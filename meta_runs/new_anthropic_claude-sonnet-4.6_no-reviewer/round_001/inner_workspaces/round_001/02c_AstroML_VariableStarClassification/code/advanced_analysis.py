"""Advanced Variable Star Classification - exploring multiple approaches."""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from itertools import product
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    balanced_accuracy_score, accuracy_score, classification_report,
    confusion_matrix, roc_auc_score, roc_curve, f1_score
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsClassifier
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ── Load data ────────────────────────────────────────────────────────────────
train = pd.read_csv('data/train.csv')
val   = pd.read_csv('data/val.csv')
test  = pd.read_csv('data/test.csv')

y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values

SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

def series_to_numeric(s):
    return np.array([SYM2IDX.get(c, 0) for c in s], dtype=float)

# ── Approach 1: TF-IDF on character n-grams ──────────────────────────────────
print("=== Approach 1: TF-IDF n-grams ===")

# Try different n-gram ranges using char analyzer
for ngram_range in [(1,1), (1,2), (1,3), (2,2), (2,3), (3,3)]:
    tfidf = TfidfVectorizer(analyzer='char_wb', ngram_range=ngram_range)
    X_tr = tfidf.fit_transform(train['symbol_series'])
    X_v  = tfidf.transform(val['symbol_series'])
    X_te = tfidf.transform(test['symbol_series'])
    
    clf = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42)
    clf.fit(X_tr, y_train)
    yp_v = clf.predict(X_v)
    yp_t = clf.predict(X_te)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  ngram={ngram_range}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Approach 2: Character-level n-gram (no spaces) ───────────────────────────
print("\n=== Approach 2: Char-level n-grams ===")
for ngram_range in [(1,1), (1,2), (1,3), (2,2), (2,3), (3,3), (3,4), (4,4)]:
    tfidf = TfidfVectorizer(analyzer='char', ngram_range=ngram_range)
    X_tr = tfidf.fit_transform(train['symbol_series'])
    X_v  = tfidf.transform(val['symbol_series'])
    X_te = tfidf.transform(test['symbol_series'])
    
    clf = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42)
    clf.fit(X_tr, y_train)
    yp_v = clf.predict(X_v)
    yp_t = clf.predict(X_te)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  ngram={ngram_range}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Approach 3: Position-specific features ───────────────────────────────────
print("\n=== Approach 3: Position-specific one-hot features ===")

def pos_onehot(df):
    """One-hot encode each position."""
    rows = []
    for s in df['symbol_series']:
        row = []
        for c in s:
            for sym in SYMBOLS:
                row.append(1 if c == sym else 0)
        rows.append(row)
    return np.array(rows)

X_tr = pos_onehot(train)
X_v  = pos_onehot(val)
X_te = pos_onehot(test)
print(f"  Feature shape: {X_tr.shape}")

for clf_name, clf in [
    ('LR', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42)),
    ('RF', RandomForestClassifier(n_estimators=300, random_state=42, class_weight='balanced')),
    ('SVM', Pipeline([('sc', StandardScaler()), ('clf', SVC(C=1.0, probability=True, class_weight='balanced', random_state=42))]))
]:
    clf.fit(X_tr, y_train)
    yp_v = clf.predict(X_v)
    yp_t = clf.predict(X_te)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  {clf_name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Approach 4: Numeric sequence + statistical features ──────────────────────
print("\n=== Approach 4: Raw numeric sequence ===")

def raw_numeric(df):
    return np.array([series_to_numeric(s) for s in df['symbol_series']])

X_tr = raw_numeric(train)
X_v  = raw_numeric(val)
X_te = raw_numeric(test)

for clf_name, clf in [
    ('LR', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])),
    ('RF', RandomForestClassifier(n_estimators=300, random_state=42, class_weight='balanced')),
    ('KNN', KNeighborsClassifier(n_neighbors=5)),
    ('SVM', Pipeline([('sc', StandardScaler()), ('clf', SVC(C=1.0, probability=True, class_weight='balanced', random_state=42))]))
]:
    clf.fit(X_tr, y_train)
    yp_v = clf.predict(X_v)
    yp_t = clf.predict(X_te)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  {clf_name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Approach 5: Fourier features ─────────────────────────────────────────────
print("\n=== Approach 5: Fourier features ===")

def fourier_features(df):
    rows = []
    for s in df['symbol_series']:
        nums = series_to_numeric(s)
        fft = np.fft.rfft(nums)
        feats = np.concatenate([np.abs(fft), np.angle(fft)])
        rows.append(feats)
    return np.array(rows)

X_tr = fourier_features(train)
X_v  = fourier_features(val)
X_te = fourier_features(test)
print(f"  Feature shape: {X_tr.shape}")

for clf_name, clf in [
    ('LR', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])),
    ('RF', RandomForestClassifier(n_estimators=300, random_state=42, class_weight='balanced')),
    ('SVM', Pipeline([('sc', StandardScaler()), ('clf', SVC(C=1.0, probability=True, class_weight='balanced', random_state=42))]))
]:
    clf.fit(X_tr, y_train)
    yp_v = clf.predict(X_v)
    yp_t = clf.predict(X_te)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  {clf_name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Approach 6: Combined features ────────────────────────────────────────────
print("\n=== Approach 6: Combined (pos_onehot + fourier + stats) ===")

def extract_all_features(df):
    pos_oh = pos_onehot(df)
    fft_f  = fourier_features(df)
    raw_n  = raw_numeric(df)
    
    # Stats
    stats = []
    for s in df['symbol_series']:
        nums = series_to_numeric(s)
        diffs = np.diff(nums)
        cnt = Counter(s)
        n = len(nums)
        row = [
            nums.mean(), nums.std(), nums.min(), nums.max(),
            np.median(nums), np.percentile(nums, 25), np.percentile(nums, 75),
            pd.Series(nums).skew(), pd.Series(nums).kurt(),
            np.mean(np.abs(diffs)), np.std(diffs), np.max(np.abs(diffs)),
            np.sum(np.abs(diffs) >= 3),
            -sum(p * np.log(p) for sym2 in SYMBOLS for p in [cnt.get(sym2,0)/n] if cnt.get(sym2,0) > 0),
            len(set(s)),
            pd.Series(nums).autocorr(lag=1) if n > 2 else 0,
            pd.Series(nums).autocorr(lag=2) if n > 3 else 0,
        ]
        stats.append(row)
    stats = np.array(stats)
    
    return np.hstack([pos_oh, fft_f, stats])

X_tr = extract_all_features(train)
X_v  = extract_all_features(val)
X_te = extract_all_features(test)
X_tr = np.nan_to_num(X_tr)
X_v  = np.nan_to_num(X_v)
X_te = np.nan_to_num(X_te)
print(f"  Feature shape: {X_tr.shape}")

for clf_name, clf in [
    ('LR', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])),
    ('RF', RandomForestClassifier(n_estimators=500, random_state=42, class_weight='balanced')),
    ('GB', GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)),
    ('SVM', Pipeline([('sc', StandardScaler()), ('clf', SVC(C=1.0, probability=True, class_weight='balanced', random_state=42))])),
    ('SVM_rbf_C10', Pipeline([('sc', StandardScaler()), ('clf', SVC(C=10.0, probability=True, class_weight='balanced', random_state=42))])),
]:
    clf.fit(X_tr, y_train)
    yp_v = clf.predict(X_v)
    yp_t = clf.predict(X_te)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  {clf_name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Approach 7: Look at the data differently - maybe it's about specific positions ──
print("\n=== Approach 7: Positional analysis ===")

# For each position, what's the mean value for variable vs non-variable?
var_pos_means = []
non_pos_means = []
for pos in range(40):
    var_vals = [SYM2IDX.get(s[pos], 0) for s in train[train['label']==1]['symbol_series']]
    non_vals = [SYM2IDX.get(s[pos], 0) for s in train[train['label']==0]['symbol_series']]
    var_pos_means.append(np.mean(var_vals))
    non_pos_means.append(np.mean(non_vals))

print("Position-wise mean differences (var - non):")
diffs = np.array(var_pos_means) - np.array(non_pos_means)
print(f"  Max diff: {max(abs(diffs)):.4f} at position {np.argmax(abs(diffs))}")
print(f"  Mean abs diff: {np.mean(abs(diffs)):.4f}")
print(f"  Diffs: {[round(d,3) for d in diffs]}")

# ── Approach 8: Try treating as a sequence classification with sliding windows ──
print("\n=== Approach 8: Sliding window features ===")

def sliding_window_features(df, window=5):
    rows = []
    for s in df['symbol_series']:
        nums = series_to_numeric(s)
        n = len(nums)
        feats = []
        for i in range(n - window + 1):
            window_vals = nums[i:i+window]
            feats.extend([
                window_vals.mean(),
                window_vals.std(),
                window_vals.max() - window_vals.min(),
            ])
        rows.append(feats)
    return np.array(rows)

for window in [3, 5, 7, 10]:
    X_tr = sliding_window_features(train, window)
    X_v  = sliding_window_features(val, window)
    X_te = sliding_window_features(test, window)
    
    clf = Pipeline([('sc', StandardScaler()), 
                    ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])
    clf.fit(X_tr, y_train)
    yp_v = clf.predict(X_v)
    yp_t = clf.predict(X_te)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  window={window}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Approach 9: Check if field_id matters ────────────────────────────────────
print("\n=== Approach 9: Field ID analysis ===")
print("Field ID distribution:")
print(train.groupby(['field_id', 'label']).size().unstack(fill_value=0))

# Add field_id as a feature
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
le.fit(pd.concat([train['field_id'], val['field_id'], test['field_id']]))

def with_field_id(df, base_features):
    field_encoded = le.transform(df['field_id']).reshape(-1, 1)
    return np.hstack([base_features, field_encoded])

# Use pos_onehot + field_id
X_tr_base = pos_onehot(train)
X_v_base  = pos_onehot(val)
X_te_base = pos_onehot(test)

X_tr = with_field_id(train, X_tr_base)
X_v  = with_field_id(val, X_v_base)
X_te = with_field_id(test, X_te_base)

clf = Pipeline([('sc', StandardScaler()), 
                ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])
clf.fit(X_tr, y_train)
yp_v = clf.predict(X_v)
yp_t = clf.predict(X_te)
ba_v = balanced_accuracy_score(y_val, yp_v)
ba_t = balanced_accuracy_score(y_test, yp_t)
print(f"  pos_onehot + field_id: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Approach 10: XGBoost / LightGBM if available ─────────────────────────────
print("\n=== Approach 10: XGBoost ===")
try:
    from xgboost import XGBClassifier
    
    X_tr = pos_onehot(train)
    X_v  = pos_onehot(val)
    X_te = pos_onehot(test)
    
    for lr in [0.01, 0.05, 0.1]:
        xgb = XGBClassifier(n_estimators=500, max_depth=4, learning_rate=lr,
                            use_label_encoder=False, eval_metric='logloss',
                            random_state=42, verbosity=0)
        xgb.fit(X_tr, y_train)
        yp_v = xgb.predict(X_v)
        yp_t = xgb.predict(X_te)
        ba_v = balanced_accuracy_score(y_val, yp_v)
        ba_t = balanced_accuracy_score(y_test, yp_t)
        print(f"  XGB lr={lr}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")
except ImportError:
    print("  XGBoost not available")

print("\n=== Approach 11: LightGBM ===")
try:
    import lightgbm as lgb
    
    X_tr = pos_onehot(train)
    X_v  = pos_onehot(val)
    X_te = pos_onehot(test)
    
    lgbm = lgb.LGBMClassifier(n_estimators=500, max_depth=4, learning_rate=0.05,
                               class_weight='balanced', random_state=42, verbose=-1)
    lgbm.fit(X_tr, y_train)
    yp_v = lgbm.predict(X_v)
    yp_t = lgbm.predict(X_te)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  LGBM: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")
except ImportError:
    print("  LightGBM not available")

print("\nDone!")
