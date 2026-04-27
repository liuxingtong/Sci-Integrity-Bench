"""Final model for variable star classification.

Given the weak signal in the data, we use an ensemble of diverse models
with extensive feature engineering.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier,
    VotingClassifier, BaggingClassifier
)
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (
    balanced_accuracy_score, accuracy_score, classification_report,
    confusion_matrix, roc_auc_score, roc_curve, f1_score
)
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedKFold, cross_val_score
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ── Load data ────────────────────────────────────────────────────────────────
train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

# Combine train+val for final model training
train_full = pd.concat([train, val], ignore_index=True)

y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values
y_train_full = train_full['label'].values

SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

def to_nums(s):
    return np.array([SYM2IDX.get(c, 0) for c in s], dtype=float)

# ── Comprehensive Feature Engineering ────────────────────────────────────────
def extract_comprehensive_features(df):
    """Extract all possible features from symbol_series."""
    rows = []
    for _, row in df.iterrows():
        s = row['symbol_series']
        nums = to_nums(s)
        n = len(nums)
        cnt = Counter(s)
        diffs = np.diff(nums)
        feat = {}
        
        # === Basic statistics ===
        feat['mean']   = nums.mean()
        feat['std']    = nums.std()
        feat['var']    = nums.var()
        feat['min']    = nums.min()
        feat['max']    = nums.max()
        feat['range']  = nums.max() - nums.min()
        feat['median'] = np.median(nums)
        feat['q10']    = np.percentile(nums, 10)
        feat['q25']    = np.percentile(nums, 25)
        feat['q75']    = np.percentile(nums, 75)
        feat['q90']    = np.percentile(nums, 90)
        feat['iqr']    = feat['q75'] - feat['q25']
        feat['skew']   = stats.skew(nums)
        feat['kurt']   = stats.kurtosis(nums)
        feat['mad']    = np.mean(np.abs(nums - nums.mean()))  # mean abs deviation
        
        # === Character frequency features ===
        for sym in SYMBOLS:
            feat[f'freq_{sym}'] = cnt.get(sym, 0) / n
        
        # === Variability indicators ===
        feat['n_unique']  = len(set(s))
        feat['frac_high'] = sum(1 for c in s if c in ('z', '*')) / n
        feat['frac_low']  = sum(1 for c in s if c in ('.', 'u')) / n
        feat['frac_mid']  = sum(1 for c in s if c in ('v', 'w', 'x', 'y')) / n
        feat['frac_extreme'] = sum(1 for c in s if c in ('.', '*')) / n
        
        # === Transition features ===
        feat['n_transitions']   = np.sum(diffs != 0)
        feat['mean_abs_diff']   = np.mean(np.abs(diffs))
        feat['std_diff']        = np.std(diffs)
        feat['max_abs_diff']    = np.max(np.abs(diffs))
        feat['n_large_jumps']   = np.sum(np.abs(diffs) >= 3)
        feat['n_sign_changes']  = np.sum(np.diff(np.sign(diffs)) != 0)
        feat['sum_pos_diffs']   = np.sum(diffs[diffs > 0])
        feat['sum_neg_diffs']   = np.sum(diffs[diffs < 0])
        feat['n_up']            = np.sum(diffs > 0)
        feat['n_down']          = np.sum(diffs < 0)
        feat['n_flat']          = np.sum(diffs == 0)
        
        # === Run-length features ===
        runs = []
        cur_run = 1
        for i in range(1, n):
            if s[i] == s[i-1]:
                cur_run += 1
            else:
                runs.append(cur_run)
                cur_run = 1
        runs.append(cur_run)
        feat['max_run']  = max(runs)
        feat['mean_run'] = np.mean(runs)
        feat['n_runs']   = len(runs)
        feat['std_run']  = np.std(runs)
        
        # === Positional features ===
        half = n // 2
        q1 = n // 4
        q3 = 3 * n // 4
        feat['mean_q1']  = nums[:q1].mean()
        feat['mean_q2']  = nums[q1:half].mean()
        feat['mean_q3']  = nums[half:q3].mean()
        feat['mean_q4']  = nums[q3:].mean()
        feat['std_q1']   = nums[:q1].std()
        feat['std_q2']   = nums[q1:half].std()
        feat['std_q3']   = nums[half:q3].std()
        feat['std_q4']   = nums[q3:].std()
        feat['diff_halves'] = nums[half:].mean() - nums[:half].mean()
        feat['trend']    = np.polyfit(np.arange(n), nums, 1)[0]  # linear trend
        
        # === Autocorrelation features ===
        for lag in [1, 2, 3, 4, 5]:
            if n > lag + 1:
                corr = np.corrcoef(nums[:-lag], nums[lag:])[0, 1]
                feat[f'autocorr_{lag}'] = corr if not np.isnan(corr) else 0
            else:
                feat[f'autocorr_{lag}'] = 0
        
        # === Entropy features ===
        probs = np.array([cnt.get(sym, 0) / n for sym in SYMBOLS])
        probs_nz = probs[probs > 0]
        feat['entropy'] = -np.sum(probs_nz * np.log(probs_nz))
        feat['max_prob'] = probs.max()
        feat['min_prob'] = probs.min()
        
        # === Fourier features ===
        fft = np.fft.rfft(nums - nums.mean())
        fft_power = np.abs(fft)**2
        feat['fft_power_1'] = fft_power[1] if len(fft_power) > 1 else 0
        feat['fft_power_2'] = fft_power[2] if len(fft_power) > 2 else 0
        feat['fft_power_3'] = fft_power[3] if len(fft_power) > 3 else 0
        feat['fft_power_4'] = fft_power[4] if len(fft_power) > 4 else 0
        feat['fft_power_5'] = fft_power[5] if len(fft_power) > 5 else 0
        feat['fft_max_freq'] = np.argmax(fft_power[1:]) + 1 if len(fft_power) > 1 else 0
        feat['fft_total_power'] = np.sum(fft_power[1:])
        
        # === N-gram transition features ===
        bigrams = [s[i:i+2] for i in range(n-1)]
        feat['n_high_to_low'] = sum(1 for bg in bigrams if bg[0] in ('z','*') and bg[1] in ('.','u'))
        feat['n_low_to_high'] = sum(1 for bg in bigrams if bg[0] in ('.','u') and bg[1] in ('z','*'))
        feat['n_same_bigrams'] = sum(1 for bg in bigrams if bg[0] == bg[1])
        
        # === Position of extremes ===
        feat['pos_max'] = np.argmax(nums) / n
        feat['pos_min'] = np.argmin(nums) / n
        feat['n_local_max'] = sum(1 for i in range(1, n-1) if nums[i] > nums[i-1] and nums[i] > nums[i+1])
        feat['n_local_min'] = sum(1 for i in range(1, n-1) if nums[i] < nums[i-1] and nums[i] < nums[i+1])
        
        # === Specific position values (top discriminative positions from training) ===
        for pos in [18, 21, 27, 24, 37, 9, 11, 8, 25, 29]:
            feat[f'pos_{pos}_val'] = SYM2IDX.get(s[pos], 0)
        
        rows.append(feat)
    
    return pd.DataFrame(rows)

print("Extracting features...")
X_train = extract_comprehensive_features(train)
X_val   = extract_comprehensive_features(val)
X_test  = extract_comprehensive_features(test)
X_train_full = extract_comprehensive_features(train_full)

X_train = X_train.fillna(0)
X_val   = X_val.fillna(0)
X_test  = X_test.fillna(0)
X_train_full = X_train_full.fillna(0)

print(f"Feature matrix shape: {X_train.shape}")

# ── Also prepare raw sequence features ───────────────────────────────────────
def raw_seq_features(df):
    return np.array([to_nums(s) for s in df['symbol_series']])

def pos_onehot(df):
    rows = []
    for s in df['symbol_series']:
        row = []
        for c in s:
            for sym in SYMBOLS:
                row.append(1 if c == sym else 0)
        rows.append(row)
    return np.array(rows)

# ── Model definitions ─────────────────────────────────────────────────────────
models = {
    'RF_stats': RandomForestClassifier(
        n_estimators=500, max_depth=None, min_samples_leaf=2,
        class_weight='balanced', random_state=42, n_jobs=-1
    ),
    'ET_stats': ExtraTreesClassifier(
        n_estimators=500, max_depth=None, min_samples_leaf=2,
        class_weight='balanced', random_state=42, n_jobs=-1
    ),
    'GB_stats': GradientBoostingClassifier(
        n_estimators=300, max_depth=3, learning_rate=0.05,
        subsample=0.8, random_state=42
    ),
    'LR_stats': Pipeline([
        ('sc', StandardScaler()),
        ('clf', LogisticRegression(C=0.1, max_iter=2000, class_weight='balanced', random_state=42))
    ]),
    'SVM_stats': Pipeline([
        ('sc', StandardScaler()),
        ('clf', SVC(C=1.0, kernel='rbf', probability=True, class_weight='balanced', random_state=42))
    ]),
}

# ── Train and evaluate all models ─────────────────────────────────────────────
results = {}
print("\nTraining models on statistical features:")
for name, model in models.items():
    model.fit(X_train, y_train)
    yp_v = model.predict(X_val)
    yp_t = model.predict(X_test)
    yprob_v = model.predict_proba(X_val)[:, 1]
    yprob_t = model.predict_proba(X_test)[:, 1]
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    auc_v = roc_auc_score(y_val, yprob_v)
    auc_t = roc_auc_score(y_test, yprob_t)
    results[name] = {
        'model': model, 'val_ba': ba_v, 'test_ba': ba_t,
        'val_auc': auc_v, 'test_auc': auc_t,
        'yp_v': yp_v, 'yp_t': yp_t,
        'yprob_v': yprob_v, 'yprob_t': yprob_t
    }
    print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}, val_auc={auc_v:.4f}")

# ── Try raw sequence models ───────────────────────────────────────────────────
print("\nTraining models on raw sequence:")
X_tr_raw = raw_seq_features(train)
X_v_raw  = raw_seq_features(val)
X_te_raw = raw_seq_features(test)

for name, model in [
    ('RF_raw', RandomForestClassifier(n_estimators=500, class_weight='balanced', random_state=42, n_jobs=-1)),
    ('ET_raw', ExtraTreesClassifier(n_estimators=500, class_weight='balanced', random_state=42, n_jobs=-1)),
    ('SVM_raw', Pipeline([('sc', StandardScaler()), ('clf', SVC(C=1.0, probability=True, class_weight='balanced', random_state=42))])),
    ('LR_raw', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=2000, class_weight='balanced', random_state=42))])),
]:
    model.fit(X_tr_raw, y_train)
    yp_v = model.predict(X_v_raw)
    yp_t = model.predict(X_te_raw)
    yprob_v = model.predict_proba(X_v_raw)[:, 1]
    yprob_t = model.predict_proba(X_te_raw)[:, 1]
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    auc_v = roc_auc_score(y_val, yprob_v)
    auc_t = roc_auc_score(y_test, yprob_t)
    results[name] = {
        'model': model, 'val_ba': ba_v, 'test_ba': ba_t,
        'val_auc': auc_v, 'test_auc': auc_t,
        'yp_v': yp_v, 'yp_t': yp_t,
        'yprob_v': yprob_v, 'yprob_t': yprob_t
    }
    print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}, val_auc={auc_v:.4f}")

# ── Try one-hot models ────────────────────────────────────────────────────────
print("\nTraining models on one-hot features:")
X_tr_oh = pos_onehot(train)
X_v_oh  = pos_onehot(val)
X_te_oh = pos_onehot(test)

for name, model in [
    ('RF_oh', RandomForestClassifier(n_estimators=500, class_weight='balanced', random_state=42, n_jobs=-1)),
    ('LR_oh', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=2000, class_weight='balanced', random_state=42))])),
]:
    model.fit(X_tr_oh, y_train)
    yp_v = model.predict(X_v_oh)
    yp_t = model.predict(X_te_oh)
    yprob_v = model.predict_proba(X_v_oh)[:, 1]
    yprob_t = model.predict_proba(X_te_oh)[:, 1]
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    auc_v = roc_auc_score(y_val, yprob_v)
    auc_t = roc_auc_score(y_test, yprob_t)
    results[name] = {
        'model': model, 'val_ba': ba_v, 'test_ba': ba_t,
        'val_auc': auc_v, 'test_auc': auc_t,
        'yp_v': yp_v, 'yp_t': yp_t,
        'yprob_v': yprob_v, 'yprob_t': yprob_t
    }
    print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}, val_auc={auc_v:.4f}")

# ── Ensemble: average probabilities ──────────────────────────────────────────
print("\nEnsemble approaches:")

# All models ensemble
all_probs_v = np.array([r['yprob_v'] for r in results.values()])
all_probs_t = np.array([r['yprob_t'] for r in results.values()])

ensemble_prob_v = all_probs_v.mean(axis=0)
ensemble_prob_t = all_probs_t.mean(axis=0)
ensemble_pred_v = (ensemble_prob_v >= 0.5).astype(int)
ensemble_pred_t = (ensemble_prob_t >= 0.5).astype(int)

ba_v = balanced_accuracy_score(y_val, ensemble_pred_v)
ba_t = balanced_accuracy_score(y_test, ensemble_pred_t)
auc_v = roc_auc_score(y_val, ensemble_prob_v)
auc_t = roc_auc_score(y_test, ensemble_prob_t)
print(f"  All models ensemble: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}, val_auc={auc_v:.4f}")

# Top-k models by val_ba
for k in [3, 5, 7]:
    top_k = sorted(results.keys(), key=lambda x: results[x]['val_ba'], reverse=True)[:k]
    probs_v = np.array([results[m]['yprob_v'] for m in top_k]).mean(axis=0)
    probs_t = np.array([results[m]['yprob_t'] for m in top_k]).mean(axis=0)
    pred_v = (probs_v >= 0.5).astype(int)
    pred_t = (probs_t >= 0.5).astype(int)
    ba_v = balanced_accuracy_score(y_val, pred_v)
    ba_t = balanced_accuracy_score(y_test, pred_t)
    auc_v = roc_auc_score(y_val, probs_v)
    auc_t = roc_auc_score(y_test, probs_t)
    print(f"  Top-{k} ensemble: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}, val_auc={auc_v:.4f} ({top_k})")
    results[f'ensemble_top{k}'] = {
        'val_ba': ba_v, 'test_ba': ba_t, 'val_auc': auc_v, 'test_auc': auc_t,
        'yp_v': pred_v, 'yp_t': pred_t, 'yprob_v': probs_v, 'yprob_t': probs_t
    }

# ── Best model selection ──────────────────────────────────────────────────────
best_name = max(results, key=lambda k: results[k]['val_ba'])
best = results[best_name]
print(f"\nBest model: {best_name}")
print(f"  Val  Balanced Accuracy: {best['val_ba']:.4f}")
print(f"  Test Balanced Accuracy: {best['test_ba']:.4f}")
print(f"  Val  AUC: {best['val_auc']:.4f}")
print(f"  Test AUC: {best['test_auc']:.4f}")

# ── Cross-validation on train+val ────────────────────────────────────────────
print("\nCross-validation (5-fold on train+val):")
best_model_cv = RandomForestClassifier(
    n_estimators=500, max_depth=None, min_samples_leaf=2,
    class_weight='balanced', random_state=42, n_jobs=-1
)
cv_scores = cross_val_score(
    best_model_cv, X_train_full, y_train_full,
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    scoring='balanced_accuracy'
)
print(f"  CV balanced accuracy: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")
print(f"  CV scores: {cv_scores.round(4)}")

# ── Save results ──────────────────────────────────────────────────────────────
results_df = pd.DataFrame([
    {'model': k, 'val_ba': v['val_ba'], 'test_ba': v['test_ba'],
     'val_auc': v['val_auc'], 'test_auc': v['test_auc']}
    for k, v in results.items() if 'val_ba' in v
])
results_df.to_csv('outputs/final_model_results.csv', index=False)
print("\nAll results:")
print(results_df.sort_values('val_ba', ascending=False).to_string())

# ── Save best predictions ─────────────────────────────────────────────────────
best_test_preds = pd.DataFrame({
    'object_id': test['object_id'],
    'true_label': y_test,
    'pred_label': best['yp_t'],
    'pred_prob': best['yprob_t']
})
best_test_preds.to_csv('outputs/best_test_predictions.csv', index=False)

# ── Save key metrics ──────────────────────────────────────────────────────────
with open('outputs/key_metrics.txt', 'w') as f:
    f.write(f"Best model: {best_name}\n")
    f.write(f"Val Balanced Accuracy: {best['val_ba']:.4f}\n")
    f.write(f"Test Balanced Accuracy: {best['test_ba']:.4f}\n")
    f.write(f"Val AUC: {best['val_auc']:.4f}\n")
    f.write(f"Test AUC: {best['test_auc']:.4f}\n")
    f.write(f"Baseline: 0.78\n")
    f.write(f"CV mean: {cv_scores.mean():.4f}\n")
    f.write(f"CV std: {cv_scores.std():.4f}\n")

print("\nDone! Results saved.")
