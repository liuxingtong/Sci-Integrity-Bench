"""Deep exploration of the symbol_series encoding."""
import pandas as pd
import numpy as np
from collections import Counter
from sklearn.metrics import balanced_accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

def to_nums(s, mapping=SYM2IDX):
    return np.array([mapping.get(c, 0) for c in s], dtype=float)

# ── Key insight: maybe the symbols are NOT ordered as I assumed ──────────────
# In AstroML, the SDSS stripe 82 dataset uses a specific encoding
# Let's try all possible orderings of the 8 symbols
# Actually, let's look at what makes sense physically:
# . = missing data (NaN)
# u, v, w, x, y, z = SDSS filter bands (but that doesn't make sense for a time series)
# OR: the symbols represent discretized magnitude bins

# Let's check if the data might be from the AstroML book's variable star dataset
# which uses RR Lyrae stars from SDSS Stripe 82
# The features might be: u, g, r, i, z magnitudes at different epochs
# But here we have 40 time steps with 8 symbols

# Let's try: what if '.' and '*' are special (missing/outlier) and u-z are ordered?
# Or what if the ordering is alphabetical: . < * < u < v < w < x < y < z
# (ASCII: . = 46, * = 42, u = 117, v = 118, w = 119, x = 120, y = 121, z = 122)

ASCII_ORDER = {c: ord(c) for c in SYMBOLS}
print('ASCII values:', {c: ord(c) for c in SYMBOLS})

# Try ASCII ordering
ASCII_MAP = {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

# Let's try all 8! orderings... too many. Let's try a few sensible ones
mappings = {
    'original': {'.': 0, 'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6, '*': 7},
    'star_low': {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7},
    'star_high': {'.': 0, 'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6, '*': 7},
    'dot_star_low': {'*': 0, '.': 0, 'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6},
    'ascii': {'*': 0, '.': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7},
    'reverse': {'*': 7, 'z': 6, 'y': 5, 'x': 4, 'w': 3, 'v': 2, 'u': 1, '.': 0},
    'dot_missing': {'.': -1, 'u': 0, 'v': 1, 'w': 2, 'x': 3, 'y': 4, 'z': 5, '*': 6},
    'star_missing': {'*': -1, '.': 0, 'u': 1, 'v': 2, 'w': 3, 'x': 4, 'y': 5, 'z': 6},
}

print('\nTesting different symbol orderings:')
for mname, mapping in mappings.items():
    X_tr = np.array([to_nums(s, mapping) for s in train['symbol_series']])
    X_v = np.array([to_nums(s, mapping) for s in val['symbol_series']])
    X_te = np.array([to_nums(s, mapping) for s in test['symbol_series']])
    
    # Compute std for each series
    tr_stds = X_tr.std(axis=1)
    v_stds = X_v.std(axis=1)
    te_stds = X_te.std(axis=1)
    
    # Check if std separates classes
    var_std = tr_stds[train['label'].values == 1].mean()
    non_std = tr_stds[train['label'].values == 0].mean()
    
    # Simple threshold classifier
    threshold = (var_std + non_std) / 2
    pred_v = (v_stds > threshold).astype(int)
    ba_v = balanced_accuracy_score(val['label'].values, pred_v)
    
    clf = Pipeline([('sc', StandardScaler()), 
                    ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])
    clf.fit(X_tr, train['label'].values)
    yp_v = clf.predict(X_v)
    yp_t = clf.predict(X_te)
    ba_v_lr = balanced_accuracy_score(val['label'].values, yp_v)
    ba_t_lr = balanced_accuracy_score(test['label'].values, yp_t)
    
    print(f'  {mname}: var_std={var_std:.3f}, non_std={non_std:.3f}, thresh_ba={ba_v:.3f}, LR_val={ba_v_lr:.3f}, LR_test={ba_t_lr:.3f}')

# ── Maybe the data is from a specific AstroML example ────────────────────────
import os
print('\nRelated work files:')
if os.path.exists('related_work'):
    for f in os.listdir('related_work'):
        print(f'  {f}')
else:
    print('  No related_work directory found')

# ── Try treating the series as a Markov chain ─────────────────────────────────
print('\nMarkov chain transition matrix analysis:')

def get_transition_matrix(series_list, mapping=SYM2IDX):
    n_states = len(SYMBOLS)
    trans = np.zeros((n_states, n_states))
    for s in series_list:
        for i in range(len(s)-1):
            from_idx = list(SYMBOLS).index(s[i]) if s[i] in SYMBOLS else 0
            to_idx = list(SYMBOLS).index(s[i+1]) if s[i+1] in SYMBOLS else 0
            trans[from_idx, to_idx] += 1
    # Normalize
    row_sums = trans.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    return trans / row_sums

var_trans = get_transition_matrix(train[train['label']==1]['symbol_series'].tolist())
non_trans = get_transition_matrix(train[train['label']==0]['symbol_series'].tolist())

print('Variable transition matrix:')
print(pd.DataFrame(var_trans, index=SYMBOLS, columns=SYMBOLS).round(3))
print('Non-variable transition matrix:')
print(pd.DataFrame(non_trans, index=SYMBOLS, columns=SYMBOLS).round(3))
print('Difference:')
print(pd.DataFrame(var_trans - non_trans, index=SYMBOLS, columns=SYMBOLS).round(3))

# ── Use Markov chain log-likelihood as a feature ──────────────────────────────
def markov_loglik(s, trans_matrix):
    ll = 0
    for i in range(len(s)-1):
        from_idx = SYMBOLS.index(s[i]) if s[i] in SYMBOLS else 0
        to_idx = SYMBOLS.index(s[i+1]) if s[i+1] in SYMBOLS else 0
        p = trans_matrix[from_idx, to_idx]
        ll += np.log(p + 1e-10)
    return ll

print('\nMarkov log-likelihood features:')
for split_name, df, y in [('train', train, train['label'].values), ('val', val, val['label'].values)]:
    ll_var = [markov_loglik(s, var_trans) for s in df['symbol_series']]
    ll_non = [markov_loglik(s, non_trans) for s in df['symbol_series']]
    ll_diff = np.array(ll_var) - np.array(ll_non)
    pred = (ll_diff > 0).astype(int)
    ba = balanced_accuracy_score(y, pred)
    print(f'  {split_name}: Markov LLR ba={ba:.4f}')

# Test set
ll_var_te = [markov_loglik(s, var_trans) for s in test['symbol_series']]
ll_non_te = [markov_loglik(s, non_trans) for s in test['symbol_series']]
ll_diff_te = np.array(ll_var_te) - np.array(ll_non_te)
pred_te = (ll_diff_te > 0).astype(int)
ba_te = balanced_accuracy_score(test['label'].values, pred_te)
print(f'  test: Markov LLR ba={ba_te:.4f}')

# ── Try combining Markov features with other features ─────────────────────────
print('\nCombined Markov + stats features:')

def markov_features(df, var_trans, non_trans):
    feats = []
    for s in df['symbol_series']:
        ll_v = markov_loglik(s, var_trans)
        ll_n = markov_loglik(s, non_trans)
        feats.append([ll_v, ll_n, ll_v - ll_n])
    return np.array(feats)

X_tr_mk = markov_features(train, var_trans, non_trans)
X_v_mk  = markov_features(val, var_trans, non_trans)
X_te_mk = markov_features(test, var_trans, non_trans)

clf = LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42)
clf.fit(X_tr_mk, train['label'].values)
yp_v = clf.predict(X_v_mk)
yp_t = clf.predict(X_te_mk)
print(f'  Markov only LR: val_ba={balanced_accuracy_score(val["label"].values, yp_v):.4f}, test_ba={balanced_accuracy_score(test["label"].values, yp_t):.4f}')

# ── Check if there's any pattern in the data at all ──────────────────────────
print('\nChecking data integrity:')
print(f'  Train series unique: {train["symbol_series"].nunique()} / {len(train)}')
print(f'  Val series unique: {val["symbol_series"].nunique()} / {len(val)}')
print(f'  Test series unique: {test["symbol_series"].nunique()} / {len(test)}')

# Check for duplicates across splits
train_set = set(train['symbol_series'])
val_set = set(val['symbol_series'])
test_set = set(test['symbol_series'])
print(f'  Train-Val overlap: {len(train_set & val_set)}')
print(f'  Train-Test overlap: {len(train_set & test_set)}')
print(f'  Val-Test overlap: {len(val_set & test_set)}')

# Check if same series appears with different labels
all_data = pd.concat([train, val, test])
dupes = all_data[all_data.duplicated('symbol_series', keep=False)]
if len(dupes) > 0:
    print(f'  Duplicate series: {len(dupes)}')
    print(dupes[['symbol_series', 'label']].head(10))
else:
    print('  No duplicate series found')
