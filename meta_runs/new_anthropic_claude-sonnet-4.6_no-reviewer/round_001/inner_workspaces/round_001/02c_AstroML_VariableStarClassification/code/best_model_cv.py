"""Best model using cross-validation on train+val."""
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, confusion_matrix, f1_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score
from scipy.signal import periodogram
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values

# Combine train+val for CV-based model selection
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

def periodogram_features(df):
    rows = []
    for s in df['symbol_series']:
        nums = to_nums(s)
        freqs, power = periodogram(nums - nums.mean())
        top_powers = sorted(power[1:], reverse=True)[:10]
        dom_freq = freqs[np.argmax(power[1:]) + 1]
        rows.append(list(top_powers) + [dom_freq, power.sum(), power.max()])
    return np.array(rows)

def extract_features(df):
    """Comprehensive feature extraction."""
    from collections import Counter
    from scipy import stats
    rows = []
    for _, row in df.iterrows():
        s = row['symbol_series']
        nums = to_nums(s)
        n = len(nums)
        cnt = Counter(s)
        diffs = np.diff(nums)
        feat = {}
        
        feat['mean'] = nums.mean()
        feat['std'] = nums.std()
        feat['var'] = nums.var()
        feat['min'] = nums.min()
        feat['max'] = nums.max()
        feat['range'] = nums.max() - nums.min()
        feat['median'] = np.median(nums)
        feat['q25'] = np.percentile(nums, 25)
        feat['q75'] = np.percentile(nums, 75)
        feat['iqr'] = feat['q75'] - feat['q25']
        feat['skew'] = stats.skew(nums)
        feat['kurt'] = stats.kurtosis(nums)
        feat['mad'] = np.mean(np.abs(nums - nums.mean()))
        
        for sym in SYMBOLS:
            feat[f'freq_{sym}'] = cnt.get(sym, 0) / n
        
        feat['n_unique'] = len(set(s))
        feat['frac_high'] = sum(1 for c in s if c in ('z', '*')) / n
        feat['frac_low'] = sum(1 for c in s if c in ('.', 'u')) / n
        feat['frac_extreme'] = sum(1 for c in s if c in ('.', '*')) / n
        
        feat['n_transitions'] = np.sum(diffs != 0)
        feat['mean_abs_diff'] = np.mean(np.abs(diffs))
        feat['std_diff'] = np.std(diffs)
        feat['max_abs_diff'] = np.max(np.abs(diffs))
        feat['n_large_jumps'] = np.sum(np.abs(diffs) >= 3)
        feat['n_sign_changes'] = np.sum(np.diff(np.sign(diffs)) != 0)
        feat['n_up'] = np.sum(diffs > 0)
        feat['n_down'] = np.sum(diffs < 0)
        
        runs = []
        cur_run = 1
        for i in range(1, n):
            if s[i] == s[i-1]:
                cur_run += 1
            else:
                runs.append(cur_run)
                cur_run = 1
        runs.append(cur_run)
        feat['max_run'] = max(runs)
        feat['mean_run'] = np.mean(runs)
        feat['n_runs'] = len(runs)
        
        half = n // 2
        feat['mean_first_half'] = nums[:half].mean()
        feat['mean_second_half'] = nums[half:].mean()
        feat['diff_halves'] = feat['mean_second_half'] - feat['mean_first_half']
        feat['std_first_half'] = nums[:half].std()
        feat['std_second_half'] = nums[half:].std()
        feat['trend'] = np.polyfit(np.arange(n), nums, 1)[0]
        
        for lag in [1, 2, 3, 4, 5]:
            if n > lag + 1:
                corr = np.corrcoef(nums[:-lag], nums[lag:])[0, 1]
                feat[f'autocorr_{lag}'] = corr if not np.isnan(corr) else 0
            else:
                feat[f'autocorr_{lag}'] = 0
        
        probs = np.array([cnt.get(sym, 0) / n for sym in SYMBOLS])
        probs_nz = probs[probs > 0]
        feat['entropy'] = -np.sum(probs_nz * np.log(probs_nz))
        
        fft = np.fft.rfft(nums - nums.mean())
        fft_power = np.abs(fft)**2
        for i in range(1, 6):
            feat[f'fft_power_{i}'] = fft_power[i] if len(fft_power) > i else 0
        feat['fft_max_freq'] = np.argmax(fft_power[1:]) + 1 if len(fft_power) > 1 else 0
        
        feat['n_local_max'] = sum(1 for i in range(1, n-1) if nums[i] > nums[i-1] and nums[i] > nums[i+1])
        feat['n_local_min'] = sum(1 for i in range(1, n-1) if nums[i] < nums[i-1] and nums[i] < nums[i+1])
        
        rows.append(feat)
    
    return pd.DataFrame(rows).fillna(0)

print("Extracting features...")
X_tr_stats = extract_features(train).values
X_v_stats  = extract_features(val).values
X_te_stats = extract_features(test).values
X_full_stats = extract_features(train_full).values

X_tr_raw = np.array([to_nums(s) for s in train['symbol_series']])
X_v_raw  = np.array([to_nums(s) for s in val['symbol_series']])
X_te_raw = np.array([to_nums(s) for s in test['symbol_series']])
X_full_raw = np.array([to_nums(s) for s in train_full['symbol_series']])

X_tr_haar = haar_features(train)
X_v_haar  = haar_features(val)
X_te_haar = haar_features(test)
X_full_haar = haar_features(train_full)

# Combined features
X_tr_comb = np.hstack([X_tr_raw, X_tr_stats, X_tr_haar])
X_v_comb  = np.hstack([X_v_raw, X_v_stats, X_v_haar])
X_te_comb = np.hstack([X_te_raw, X_te_stats, X_te_haar])
X_full_comb = np.hstack([X_full_raw, X_full_stats, X_full_haar])

print(f"Feature shapes: raw={X_tr_raw.shape}, stats={X_tr_stats.shape}, haar={X_tr_haar.shape}, comb={X_tr_comb.shape}")

# ── Cross-validation model selection ─────────────────────────────────────────
print("\nCross-validation model selection (5-fold on train+val):")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

models_to_test = [
    ('RF_raw_100', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42), X_full_raw),
    ('ET_raw_100', ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42), X_full_raw),
    ('RF_haar_100', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42), X_full_haar),
    ('ET_haar_100', ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42), X_full_haar),
    ('RF_comb_100', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42), X_full_comb),
    ('LR_raw', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=500, class_weight='balanced', random_state=42))]), X_full_raw),
    ('LR_comb', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=500, class_weight='balanced', random_state=42))]), X_full_comb),
    ('MLP_raw', Pipeline([('sc', StandardScaler()), ('clf', MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=200, random_state=42, alpha=0.01))]), X_full_raw),
    ('MLP_comb', Pipeline([('sc', StandardScaler()), ('clf', MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=200, random_state=42, alpha=0.01))]), X_full_comb),
]

cv_results = {}
for name, model, X in models_to_test:
    scores = cross_val_score(model, X, y_full, cv=skf, scoring='balanced_accuracy')
    cv_results[name] = {'mean': scores.mean(), 'std': scores.std(), 'scores': scores}
    print(f"  {name}: CV ba={scores.mean():.4f} +/- {scores.std():.4f}")

best_cv_name = max(cv_results, key=lambda k: cv_results[k]['mean'])
print(f"\nBest CV model: {best_cv_name} (CV ba={cv_results[best_cv_name]['mean']:.4f})")

# ── Train best model on full train+val, evaluate on test ─────────────────────
print("\nTraining best models on train+val, evaluating on test:")

final_results = {}
for name, model, X_full_feat in models_to_test:
    # Get corresponding test features
    if 'raw' in name and 'comb' not in name:
        X_te = X_te_raw
    elif 'haar' in name:
        X_te = X_te_haar
    elif 'comb' in name:
        X_te = X_te_comb
    else:
        X_te = X_te_raw
    
    model.fit(X_full_feat, y_full)
    yp_t = model.predict(X_te)
    yprob_t = model.predict_proba(X_te)[:, 1]
    ba_t = balanced_accuracy_score(y_test, yp_t)
    auc_t = roc_auc_score(y_test, yprob_t)
    final_results[name] = {'test_ba': ba_t, 'test_auc': auc_t, 'yp_t': yp_t, 'yprob_t': yprob_t}
    print(f"  {name}: test_ba={ba_t:.4f}, test_auc={auc_t:.4f}")

# ── Also train on train only, evaluate on val and test ───────────────────────
print("\nTrain-only models (val and test):")
for name, model, X_full_feat in models_to_test:
    if 'raw' in name and 'comb' not in name:
        X_tr, X_v, X_te = X_tr_raw, X_v_raw, X_te_raw
    elif 'haar' in name:
        X_tr, X_v, X_te = X_tr_haar, X_v_haar, X_te_haar
    elif 'comb' in name:
        X_tr, X_v, X_te = X_tr_comb, X_v_comb, X_te_comb
    else:
        X_tr, X_v, X_te = X_tr_raw, X_v_raw, X_te_raw
    
    model.fit(X_tr, y_train)
    yp_v = model.predict(X_v)
    yp_t = model.predict(X_te)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

print("\nDone!")
