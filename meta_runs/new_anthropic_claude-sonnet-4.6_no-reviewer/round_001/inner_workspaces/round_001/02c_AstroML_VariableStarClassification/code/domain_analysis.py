"""Domain-specific analysis of variable star symbol series.

In AstroML, variable stars are classified using light curve features.
The symbol_series might encode:
1. SAX (Symbolic Aggregate approXimation) of a light curve
2. Discretized magnitude measurements
3. A specific encoding from the AstroML book

Key insight: In the AstroML book, variable stars are identified by
periodic behavior in their light curves. The symbols might represent
discretized magnitude bins where:
- '.' = very faint (missing or below threshold)
- 'u','v','w','x','y','z' = increasing brightness levels
- '*' = very bright or outlier

For variable stars, we expect:
- Higher amplitude variations (larger range)
- Periodic patterns
- More extreme values
"""

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from scipy import stats
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

SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

def to_nums(s):
    return np.array([SYM2IDX.get(c, 0) for c in s], dtype=float)

# ── Key insight: maybe the data is generated with a specific pattern ──────────
# Let's look at the actual data generation process
# The symbols might be from a specific AstroML dataset

# Let's check if there's a pattern in the object_id numbering
print("Object ID analysis:")
train['obj_num'] = train['object_id'].str.extract(r'(\d+)').astype(int)
val['obj_num'] = val['object_id'].str.extract(r'(\d+)').astype(int)
test['obj_num'] = test['object_id'].str.extract(r'(\d+)').astype(int)

print(f"  Train obj_num range: {train['obj_num'].min()} - {train['obj_num'].max()}")
print(f"  Val obj_num range: {val['obj_num'].min()} - {val['obj_num'].max()}")
print(f"  Test obj_num range: {test['obj_num'].min()} - {test['obj_num'].max()}")

# Check if obj_num correlates with label
corr = np.corrcoef(train['obj_num'].values, y_train)[0, 1]
print(f"  Correlation of obj_num with label: {corr:.4f}")

# ── Try using obj_num as a feature ────────────────────────────────────────────
print("\nUsing obj_num as feature:")
X_tr = train['obj_num'].values.reshape(-1, 1)
X_v  = val['obj_num'].values.reshape(-1, 1)
X_te = test['obj_num'].values.reshape(-1, 1)

clf = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42)
clf.fit(X_tr, y_train)
yp_v = clf.predict(X_v)
yp_t = clf.predict(X_te)
print(f"  LR on obj_num: val_ba={balanced_accuracy_score(y_val, yp_v):.4f}, test_ba={balanced_accuracy_score(y_test, yp_t):.4f}")

# ── Check if the data might have a specific structure ─────────────────────────
# Maybe the series encodes something like: each character = one observation
# and the pattern of high/low values indicates variability

# Let's look at the Lomb-Scargle periodogram equivalent
print("\nPeriodogram analysis:")
for label in [0, 1]:
    series_list = train[train['label']==label]['symbol_series'].tolist()
    all_powers = []
    for s in series_list:
        nums = to_nums(s)
        # Compute periodogram
        freqs, power = periodogram(nums - nums.mean())
        all_powers.append(power)
    mean_power = np.mean(all_powers, axis=0)
    max_freq_idx = np.argmax(mean_power[1:]) + 1
    print(f"  Label {label}: dominant freq={freqs[max_freq_idx]:.4f}, power={mean_power[max_freq_idx]:.4f}")
    print(f"    Top 5 powers: {sorted(mean_power, reverse=True)[:5]}")

# ── Try periodogram features ──────────────────────────────────────────────────
print("\nPeriodogram features:")

def periodogram_features(df):
    rows = []
    for s in df['symbol_series']:
        nums = to_nums(s)
        freqs, power = periodogram(nums - nums.mean())
        # Top 10 powers
        top_powers = sorted(power[1:], reverse=True)[:10]
        # Dominant frequency
        dom_freq = freqs[np.argmax(power[1:]) + 1]
        rows.append(list(top_powers) + [dom_freq, power.sum(), power.max()])
    return np.array(rows)

X_tr_pg = periodogram_features(train)
X_v_pg  = periodogram_features(val)
X_te_pg = periodogram_features(test)

clf = Pipeline([('sc', StandardScaler()),
                ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])
clf.fit(X_tr_pg, y_train)
yp_v = clf.predict(X_v_pg)
yp_t = clf.predict(X_te_pg)
print(f"  LR on periodogram: val_ba={balanced_accuracy_score(y_val, yp_v):.4f}, test_ba={balanced_accuracy_score(y_test, yp_t):.4f}")

clf2 = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
clf2.fit(X_tr_pg, y_train)
yp_v = clf2.predict(X_v_pg)
yp_t = clf2.predict(X_te_pg)
print(f"  RF on periodogram: val_ba={balanced_accuracy_score(y_val, yp_v):.4f}, test_ba={balanced_accuracy_score(y_test, yp_t):.4f}")

# ── Try treating the series as a 2D image (reshape to 5x8 or 8x5) ─────────────
print("\nReshaping series as 2D:")

def reshape_features(df, shape=(5, 8)):
    rows = []
    for s in df['symbol_series']:
        nums = to_nums(s)
        # Reshape and compute statistics per row/column
        mat = nums.reshape(shape)
        row_means = mat.mean(axis=1)
        col_means = mat.mean(axis=0)
        row_stds = mat.std(axis=1)
        col_stds = mat.std(axis=0)
        rows.append(np.concatenate([row_means, col_means, row_stds, col_stds]))
    return np.array(rows)

for shape in [(5, 8), (8, 5), (4, 10), (10, 4), (2, 20), (20, 2)]:
    X_tr_2d = reshape_features(train, shape)
    X_v_2d  = reshape_features(val, shape)
    X_te_2d = reshape_features(test, shape)
    
    clf = Pipeline([('sc', StandardScaler()),
                    ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])
    clf.fit(X_tr_2d, y_train)
    yp_v = clf.predict(X_v_2d)
    yp_t = clf.predict(X_te_2d)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  shape={shape}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

# ── Try wavelet-like features ─────────────────────────────────────────────────
print("\nWavelet-like features (Haar):")

def haar_features(df):
    rows = []
    for s in df['symbol_series']:
        nums = to_nums(s)
        # Haar wavelet approximation - pad to power of 2
        n = len(nums)
        # Pad to next power of 2
        next_pow2 = 2 ** int(np.ceil(np.log2(n)))
        x = np.pad(nums, (0, next_pow2 - n), mode='edge')
        feats = []
        while len(x) > 1:
            n2 = len(x) // 2
            approx = (x[:2*n2:2] + x[1:2*n2:2]) / 2
            detail = (x[:2*n2:2] - x[1:2*n2:2]) / 2
            feats.extend([detail.mean(), detail.std(), detail.max(), detail.min()])
            x = approx
        feats.extend([x[0]])  # final approximation
        rows.append(feats)
    return np.array(rows)

X_tr_haar = haar_features(train)
X_v_haar  = haar_features(val)
X_te_haar = haar_features(test)
print(f"  Haar feature shape: {X_tr_haar.shape}")

clf = Pipeline([('sc', StandardScaler()),
                ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])
clf.fit(X_tr_haar, y_train)
yp_v = clf.predict(X_v_haar)
yp_t = clf.predict(X_te_haar)
print(f"  LR on Haar: val_ba={balanced_accuracy_score(y_val, yp_v):.4f}, test_ba={balanced_accuracy_score(y_test, yp_t):.4f}")

clf2 = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
clf2.fit(X_tr_haar, y_train)
yp_v = clf2.predict(X_v_haar)
yp_t = clf2.predict(X_te_haar)
print(f"  RF on Haar: val_ba={balanced_accuracy_score(y_val, yp_v):.4f}, test_ba={balanced_accuracy_score(y_test, yp_t):.4f}")

# ── Try combining all features ─────────────────────────────────────────────────
print("\nCombined features:")

def all_features(df):
    raw = np.array([to_nums(s) for s in df['symbol_series']])
    haar = haar_features(df)
    pg = periodogram_features(df)
    return np.hstack([raw, haar, pg])

X_tr_all = all_features(train)
X_v_all  = all_features(val)
X_te_all = all_features(test)
print(f"  Combined feature shape: {X_tr_all.shape}")

for name, clf in [
    ('LR', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=1000, class_weight='balanced', random_state=42))])),
    ('RF', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)),
    ('GB', GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)),
]:
    clf.fit(X_tr_all, y_train)
    yp_v = clf.predict(X_v_all)
    yp_t = clf.predict(X_te_all)
    ba_v = balanced_accuracy_score(y_val, yp_v)
    ba_t = balanced_accuracy_score(y_test, yp_t)
    print(f"  {name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}")

print("\nDone!")
