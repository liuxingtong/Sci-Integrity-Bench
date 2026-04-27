import pandas as pd
import numpy as np
from collections import Counter

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

SYMBOLS = ['.', 'u', 'v', 'w', 'x', 'y', 'z', '*']
SYM2IDX = {s: i for i, s in enumerate(SYMBOLS)}

# Look at position 18 specifically
print('Position 18 values by class (train):')
for label in [0, 1]:
    vals = [SYM2IDX.get(s[18], 0) for s in train[train['label']==label]['symbol_series']]
    chars = [s[18] for s in train[train['label']==label]['symbol_series']]
    print(f'  Label {label}: mean={np.mean(vals):.3f}, chars={Counter(chars).most_common()}')

# Look at all positions with large differences
var_pos_means = []
non_pos_means = []
for pos in range(40):
    var_vals = [SYM2IDX.get(s[pos], 0) for s in train[train['label']==1]['symbol_series']]
    non_vals = [SYM2IDX.get(s[pos], 0) for s in train[train['label']==0]['symbol_series']]
    var_pos_means.append(np.mean(var_vals))
    non_pos_means.append(np.mean(non_vals))

diffs = np.array(var_pos_means) - np.array(non_pos_means)
print('\nTop 10 most discriminative positions:')
for pos in np.argsort(np.abs(diffs))[::-1][:10]:
    print(f'  pos {pos}: diff={diffs[pos]:.4f}, var_mean={var_pos_means[pos]:.3f}, non_mean={non_pos_means[pos]:.3f}')

# Check if these positions are consistent across val/test
print('\nValidation set position 18:')
for label in [0, 1]:
    vals = [SYM2IDX.get(s[18], 0) for s in val[val['label']==label]['symbol_series']]
    chars = [s[18] for s in val[val['label']==label]['symbol_series']]
    print(f'  Label {label}: mean={np.mean(vals):.3f}, chars={Counter(chars).most_common()}')

print('\nTest set position 18:')
for label in [0, 1]:
    vals = [SYM2IDX.get(s[18], 0) for s in test[test['label']==label]['symbol_series']]
    chars = [s[18] for s in test[test['label']==label]['symbol_series']]
    print(f'  Label {label}: mean={np.mean(vals):.3f}, chars={Counter(chars).most_common()}')

# Check position-specific char distributions
print('\nPosition 18 char distribution:')
for label in [0, 1]:
    chars = [s[18] for s in train[train['label']==label]['symbol_series']]
    total = len(chars)
    print(f'  Label {label}:')
    for c, cnt in sorted(Counter(chars).items()):
        print(f'    {repr(c)}: {cnt}/{total} = {cnt/total:.3f}')

# Check position 21 (diff=0.396)
print('\nPosition 21 char distribution:')
for label in [0, 1]:
    chars = [s[21] for s in train[train['label']==label]['symbol_series']]
    total = len(chars)
    print(f'  Label {label}:')
    for c, cnt in sorted(Counter(chars).items()):
        print(f'    {repr(c)}: {cnt}/{total} = {cnt/total:.3f}')

# Check if the pattern is consistent in val
print('\nVal position 21 char distribution:')
for label in [0, 1]:
    chars = [s[21] for s in val[val['label']==label]['symbol_series']]
    total = len(chars)
    print(f'  Label {label}:')
    for c, cnt in sorted(Counter(chars).items()):
        print(f'    {repr(c)}: {cnt}/{total} = {cnt/total:.3f}')

# Try a simple classifier using just the top positions
from sklearn.metrics import balanced_accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Use position values as features
top_positions = np.argsort(np.abs(diffs))[::-1][:20]
print(f'\nTop 20 positions: {top_positions.tolist()}')

def pos_features(df, positions):
    rows = []
    for s in df['symbol_series']:
        rows.append([SYM2IDX.get(s[p], 0) for p in positions])
    return np.array(rows)

for n_pos in [5, 10, 15, 20, 30, 40]:
    positions = np.argsort(np.abs(diffs))[::-1][:n_pos]
    X_tr = pos_features(train, positions)
    X_v = pos_features(val, positions)
    X_te = pos_features(test, positions)
    
    clf = Pipeline([('sc', StandardScaler()),
                    ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])
    clf.fit(X_tr, train['label'].values)
    yp_v = clf.predict(X_v)
    yp_t = clf.predict(X_te)
    ba_v = balanced_accuracy_score(val['label'].values, yp_v)
    ba_t = balanced_accuracy_score(test['label'].values, yp_t)
    print(f'  top {n_pos} positions: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}')

# Try using ALL positions
X_tr = pos_features(train, list(range(40)))
X_v = pos_features(val, list(range(40)))
X_te = pos_features(test, list(range(40)))

for clf_name, clf in [
    ('LR C=0.1', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=0.1, max_iter=1000, class_weight='balanced', random_state=42))])),
    ('LR C=1', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42))])),
    ('LR C=10', Pipeline([('sc', StandardScaler()), ('clf', LogisticRegression(C=10.0, max_iter=1000, class_weight='balanced', random_state=42))])),
    ('RF', RandomForestClassifier(n_estimators=500, random_state=42, class_weight='balanced')),
]:
    clf.fit(X_tr, train['label'].values)
    yp_v = clf.predict(X_v)
    yp_t = clf.predict(X_te)
    ba_v = balanced_accuracy_score(val['label'].values, yp_v)
    ba_t = balanced_accuracy_score(test['label'].values, yp_t)
    print(f'  All positions {clf_name}: val_ba={ba_v:.4f}, test_ba={ba_t:.4f}')
