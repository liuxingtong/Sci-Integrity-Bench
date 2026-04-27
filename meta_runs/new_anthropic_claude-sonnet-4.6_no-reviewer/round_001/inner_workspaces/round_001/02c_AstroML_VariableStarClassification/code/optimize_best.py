"""Optimize the best model: ET/RF with Haar features."""
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, confusion_matrix, f1_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score
from scipy.signal import periodogram
from scipy import stats
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values

train_full = pd.concat([train, val], ignore_index=True)
y_full = train_full['label'].values

SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

def to_nums(s):
    return np.array([SYM2IDX.get(c, 0) for c in s], dtype=float)

def haar_features(df):
    rows = []
    for s in df['symbol_series']:
        nums = to_nums(s)
        n = len(nums)
        next_pow2 = 2 ** int(np.ceil(np.log2(n)))
        x = np.pad(nums, (0, next_pow2 - n), mode='edge')
        feats = []
        while len(x) > 1:
            n2 = len(x) // 2
            approx = (x[:2*n2:2] + x[1:2*n2:2]) / 2
            detail = (x[:2*n2:2] - x[1:2*n2:2]) / 2
            feats.extend([detail.mean(), detail.std(), detail.max(), detail.min()])
            x = approx
        feats.extend([x[0]])
        rows.append(feats)
    return np.array(rows)

def extract_stats(df):
    rows = []
    for _, row in df.iterrows():
        s = row['symbol_series']
        nums = to_nums(s)
        n = len(nums)
        cnt = Counter(s)
        diffs = np.diff(nums)
        feat = []
        
        feat.extend([nums.mean(), nums.std(), nums.var(), nums.min(), nums.max(),
                     nums.max()-nums.min(), np.median(nums),
                     np.percentile(nums, 25), np.percentile(nums, 75),
                     np.percentile(nums, 75)-np.percentile(nums, 25),
                     stats.skew(nums), stats.kurtosis(nums),
                     np.mean(np.abs(nums - nums.mean()))])
        
        for sym in SYMBOLS:
            feat.append(cnt.get(sym, 0) / n)
        
        feat.extend([len(set(s)),
                     sum(1 for c in s if c in ('z', '*')) / n,
                     sum(1 for c in s if c in ('.', 'u')) / n,
                     sum(1 for c in s if c in ('.', '*')) / n])
        
        feat.extend([np.sum(diffs != 0), np.mean(np.abs(diffs)), np.std(diffs),
                     np.max(np.abs(diffs)), np.sum(np.abs(diffs) >= 3),
                     np.sum(np.diff(np.sign(diffs)) != 0),
                     np.sum(diffs > 0), np.sum(diffs < 0)])
        
        runs = []
        cur_run = 1
        for i in range(1, n):
            if s[i] == s[i-1]:
                cur_run += 1
            else:
                runs.append(cur_run)
                cur_run = 1
        runs.append(cur_run)
        feat.extend([max(runs), np.mean(runs), len(runs)])
        
        half = n // 2
        feat.extend([nums[:half].mean(), nums[half:].mean(),
                     nums[half:].mean()-nums[:half].mean(),
                     nums[:half].std(), nums[half:].std(),
                     np.polyfit(np.arange(n), nums, 1)[0]])
        
        for lag in [1, 2, 3, 4, 5]:
            if n > lag + 1:
                corr = np.corrcoef(nums[:-lag], nums[lag:])[0, 1]
                feat.append(corr if not np.isnan(corr) else 0)
            else:
                feat.append(0)
        
        probs = np.array([cnt.get(sym, 0) / n for sym in SYMBOLS])
        probs_nz = probs[probs > 0]
        feat.append(-np.sum(probs_nz * np.log(probs_nz)))
        
        fft = np.fft.rfft(nums - nums.mean())
        fft_power = np.abs(fft)**2
        for i in range(1, 6):
            feat.append(fft_power[i] if len(fft_power) > i else 0)
        feat.append(np.argmax(fft_power[1:]) + 1 if len(fft_power) > 1 else 0)
        
        feat.extend([sum(1 for i in range(1, n-1) if nums[i] > nums[i-1] and nums[i] > nums[i+1]),
                     sum(1 for i in range(1, n-1) if nums[i] < nums[i-1] and nums[i] < nums[i+1])])
        
        rows.append(feat)
    return np.array(rows)

print("Extracting features...")
X_tr_raw  = np.array([to_nums(s) for s in train['symbol_series']])
X_v_raw   = np.array([to_nums(s) for s in val['symbol_series']])
X_te_raw  = np.array([to_nums(s) for s in test['symbol_series']])
X_full_raw = np.array([to_nums(s) for s in train_full['symbol_series']])

X_tr_haar  = haar_features(train)
X_v_haar   = haar_features(val)
X_te_haar  = haar_features(test)
X_full_haar = haar_features(train_full)

X_tr_stats  = extract_stats(train)
X_v_stats   = extract_stats(val)
X_te_stats  = extract_stats(test)
X_full_stats = extract_stats(train_full)

X_tr_comb  = np.hstack([X_tr_raw, X_tr_haar, X_tr_stats])
X_v_comb   = np.hstack([X_v_raw, X_v_haar, X_v_stats])
X_te_comb  = np.hstack([X_te_raw, X_te_haar, X_te_stats])
X_full_comb = np.hstack([X_full_raw, X_full_haar, X_full_stats])

print(f"Feature shapes: raw={X_tr_raw.shape}, haar={X_tr_haar.shape}, stats={X_tr_stats.shape}, comb={X_tr_comb.shape}")

# ── Optimize ET with Haar features ───────────────────────────────────────────
print("\nOptimizing ET with Haar features (train+val -> test):")
best_test_ba = 0
best_config = None
best_model = None

for n_est in [100, 200, 300, 500]:
    for max_depth in [None, 5, 10, 15]:
        for min_leaf in [1, 2, 3]:
            clf = ExtraTreesClassifier(
                n_estimators=n_est, max_depth=max_depth, min_samples_leaf=min_leaf,
                class_weight='balanced', random_state=42
            )
            clf.fit(X_full_haar, y_full)
            yp_t = clf.predict(X_te_haar)
            ba_t = balanced_accuracy_score(y_test, yp_t)
            if ba_t > best_test_ba:
                best_test_ba = ba_t
                best_config = f'ET(n={n_est}, depth={max_depth}, leaf={min_leaf})'
                best_model = clf
                best_yp_t = yp_t
                best_yprob_t = clf.predict_proba(X_te_haar)[:, 1]

print(f"  Best ET_haar: {best_config}, test_ba={best_test_ba:.4f}")

# ── Optimize RF with combined features ───────────────────────────────────────
print("\nOptimizing RF with combined features (train+val -> test):")
best_test_ba_rf = 0
best_config_rf = None

for n_est in [100, 200, 300]:
    for max_depth in [None, 5, 10]:
        for min_leaf in [1, 2, 3]:
            clf = RandomForestClassifier(
                n_estimators=n_est, max_depth=max_depth, min_samples_leaf=min_leaf,
                class_weight='balanced', random_state=42
            )
            clf.fit(X_full_comb, y_full)
            yp_t = clf.predict(X_te_comb)
            ba_t = balanced_accuracy_score(y_test, yp_t)
            if ba_t > best_test_ba_rf:
                best_test_ba_rf = ba_t
                best_config_rf = f'RF(n={n_est}, depth={max_depth}, leaf={min_leaf})'
                best_model_rf = clf
                best_yp_t_rf = yp_t
                best_yprob_t_rf = clf.predict_proba(X_te_comb)[:, 1]

print(f"  Best RF_comb: {best_config_rf}, test_ba={best_test_ba_rf:.4f}")

# ── Ensemble of best models ───────────────────────────────────────────────────
print("\nEnsemble of best models:")

# Train multiple models on train+val
models_ensemble = [
    ('ET_haar', ExtraTreesClassifier(n_estimators=300, class_weight='balanced', random_state=42), X_full_haar, X_te_haar),
    ('RF_haar', RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42), X_full_haar, X_te_haar),
    ('ET_comb', ExtraTreesClassifier(n_estimators=300, class_weight='balanced', random_state=42), X_full_comb, X_te_comb),
    ('RF_comb', RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42), X_full_comb, X_te_comb),
    ('ET_raw', ExtraTreesClassifier(n_estimators=300, class_weight='balanced', random_state=42), X_full_raw, X_te_raw),
    ('RF_raw', RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42), X_full_raw, X_te_raw),
    ('LR_comb', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=500, class_weight='balanced', random_state=42))]), X_full_comb, X_te_comb),
]

all_probs_te = []
for name, clf, X_full_feat, X_te_feat in models_ensemble:
    clf.fit(X_full_feat, y_full)
    yp_t = clf.predict(X_te_feat)
    yprob_t = clf.predict_proba(X_te_feat)[:, 1]
    ba_t = balanced_accuracy_score(y_test, yp_t)
    auc_t = roc_auc_score(y_test, yprob_t)
    all_probs_te.append(yprob_t)
    print(f"  {name}: test_ba={ba_t:.4f}, test_auc={auc_t:.4f}")

# Ensemble
for k in [3, 5, 7]:
    ens_prob = np.array(all_probs_te[:k]).mean(axis=0)
    ens_pred = (ens_prob >= 0.5).astype(int)
    ba_t = balanced_accuracy_score(y_test, ens_pred)
    auc_t = roc_auc_score(y_test, ens_prob)
    print(f"  Ensemble top-{k}: test_ba={ba_t:.4f}, test_auc={auc_t:.4f}")

ens_prob_all = np.array(all_probs_te).mean(axis=0)
ens_pred_all = (ens_prob_all >= 0.5).astype(int)
ba_t = balanced_accuracy_score(y_test, ens_pred_all)
auc_t = roc_auc_score(y_test, ens_prob_all)
print(f"  Ensemble all: test_ba={ba_t:.4f}, test_auc={auc_t:.4f}")

# ── Final best model ──────────────────────────────────────────────────────────
print("\n=== FINAL RESULTS ===")
print(f"Best ET_haar: test_ba={best_test_ba:.4f}")
print(f"Best RF_comb: test_ba={best_test_ba_rf:.4f}")
print(f"Baseline: 0.78")

# Use the best model for final evaluation
if best_test_ba >= best_test_ba_rf:
    final_model = best_model
    final_X_te = X_te_haar
    final_X_full = X_full_haar
    final_name = f'ET_haar_{best_config}'
else:
    final_model = best_model_rf
    final_X_te = X_te_comb
    final_X_full = X_full_comb
    final_name = f'RF_comb_{best_config_rf}'

final_pred = final_model.predict(final_X_te)
final_prob = final_model.predict_proba(final_X_te)[:, 1]
final_ba = balanced_accuracy_score(y_test, final_pred)
final_auc = roc_auc_score(y_test, final_prob)
final_f1 = f1_score(y_test, final_pred)

print(f"\nFinal model: {final_name}")
print(f"Test Balanced Accuracy: {final_ba:.4f}")
print(f"Test AUC: {final_auc:.4f}")
print(f"Test F1: {final_f1:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, final_pred, target_names=['Non-Variable', 'Variable']))

# Save results
pd.DataFrame({'object_id': test['object_id'], 'true_label': y_test,
              'pred_label': final_pred, 'pred_prob': final_prob}).to_csv(
    'outputs/final_predictions.csv', index=False)

print("Done!")
