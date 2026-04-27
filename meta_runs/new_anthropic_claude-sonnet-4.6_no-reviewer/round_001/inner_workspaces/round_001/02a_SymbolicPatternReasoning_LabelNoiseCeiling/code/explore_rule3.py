import pandas as pd
import numpy as np
from itertools import combinations, product
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

train = pd.read_csv('data/spr_bench_train.csv')
val   = pd.read_csv('data/spr_bench_val.csv')
test  = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

for df in [train, val, test]:
    for col in feature_cols:
        df[col + '_shape'] = df[col].str[0]
        df[col + '_color'] = df[col].str[1]

shape_cols = [c + '_shape' for c in feature_cols]
color_cols = [c + '_color' for c in feature_cols]
shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']
all_tokens = [s+c for s in shapes for c in colors]

# Build rich feature set
def build_features(df):
    feats = {}
    
    # Count of each shape
    for shape in shapes:
        feats[f'count_{shape}'] = df[shape_cols].apply(lambda row: (row == shape).sum(), axis=1)
    
    # Count of each color
    for color in colors:
        feats[f'count_{color}'] = df[color_cols].apply(lambda row: (row == color).sum(), axis=1)
    
    # Count of each token
    for token in all_tokens:
        feats[f'count_{token}'] = df[feature_cols].apply(lambda row: (row == token).sum(), axis=1)
    
    # Parity of each shape count
    for shape in shapes:
        feats[f'parity_{shape}'] = feats[f'count_{shape}'] % 2
    
    # Parity of each color count
    for color in colors:
        feats[f'parity_{color}'] = feats[f'count_{color}'] % 2
    
    # Parity of each token count
    for token in all_tokens:
        feats[f'parity_{token}'] = feats[f'count_{token}'] % 2
    
    # Shape at each position (ordinal)
    shape_idx = {'T': 0, 'S': 1, 'C': 2, 'D': 3}
    color_idx = {'r': 0, 'g': 1, 'b': 2, 'y': 3}
    for col in shape_cols:
        feats[col + '_idx'] = df[col].map(shape_idx)
    for col in color_cols:
        feats[col + '_idx'] = df[col].map(color_idx)
    
    # Sum and parity of shape/color indices
    feats['shape_sum'] = sum(feats[col + '_idx'] for col in shape_cols)
    feats['color_sum'] = sum(feats[col + '_idx'] for col in color_cols)
    feats['shape_sum_parity'] = feats['shape_sum'] % 2
    feats['color_sum_parity'] = feats['color_sum'] % 2
    feats['total_sum'] = feats['shape_sum'] + feats['color_sum']
    feats['total_sum_parity'] = feats['total_sum'] % 2
    
    # XOR of shape indices
    shape_xor = feats[shape_cols[0] + '_idx'].copy()
    for col in shape_cols[1:]:
        shape_xor = shape_xor ^ feats[col + '_idx']
    feats['shape_xor'] = shape_xor
    
    color_xor = feats[color_cols[0] + '_idx'].copy()
    for col in color_cols[1:]:
        color_xor = color_xor ^ feats[col + '_idx']
    feats['color_xor'] = color_xor
    
    # Number of unique shapes/colors
    feats['n_unique_shapes'] = df.apply(lambda row: len(set(row[c] for c in shape_cols)), axis=1)
    feats['n_unique_colors'] = df.apply(lambda row: len(set(row[c] for c in color_cols)), axis=1)
    feats['n_unique_tokens'] = df.apply(lambda row: len(set(row[c] for c in feature_cols)), axis=1)
    
    # Bigram counts (shape pairs)
    for i in range(len(shape_cols)-1):
        for s1 in shapes:
            for s2 in shapes:
                key = f'bigram_shape_{i}_{s1}{s2}'
                feats[key] = ((df[shape_cols[i]] == s1) & (df[shape_cols[i+1]] == s2)).astype(int)
    
    # Bigram counts (color pairs)
    for i in range(len(color_cols)-1):
        for c1 in colors:
            for c2 in colors:
                key = f'bigram_color_{i}_{c1}{c2}'
                feats[key] = ((df[color_cols[i]] == c1) & (df[color_cols[i+1]] == c2)).astype(int)
    
    return pd.DataFrame(feats)

print('Building features...')
X_train = build_features(train)
X_val   = build_features(val)
X_test  = build_features(test)
y_train = train['label'].values
y_val   = val['label'].values
y_test  = test['label'].values

print(f'Feature matrix shape: {X_train.shape}')

# Try deep decision tree to find the rule
print('\n=== Deep Decision Tree ===')
for depth in [3, 5, 8, 10, 15, 20, None]:
    dt = DecisionTreeClassifier(max_depth=depth, random_state=42)
    dt.fit(X_train, y_train)
    tr_acc = accuracy_score(y_train, dt.predict(X_train))
    va_acc = accuracy_score(y_val,   dt.predict(X_val))
    te_acc = accuracy_score(y_test,  dt.predict(X_test))
    print(f'  depth={depth}: train={tr_acc:.4f}, val={va_acc:.4f}, test={te_acc:.4f}')

# Random Forest with rich features
print('\n=== Random Forest with rich features ===')
for n_est in [100, 500]:
    rf = RandomForestClassifier(n_estimators=n_est, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    tr_acc = accuracy_score(y_train, rf.predict(X_train))
    va_acc = accuracy_score(y_val,   rf.predict(X_val))
    te_acc = accuracy_score(y_test,  rf.predict(X_test))
    print(f'  n_est={n_est}: train={tr_acc:.4f}, val={va_acc:.4f}, test={te_acc:.4f}')

# Top features from RF
rf500 = RandomForestClassifier(n_estimators=500, random_state=42, n_jobs=-1)
rf500.fit(X_train, y_train)
importances = pd.Series(rf500.feature_importances_, index=X_train.columns)
top_feats = importances.nlargest(20)
print('\nTop 20 features by importance:')
for feat, imp in top_feats.items():
    print(f'  {feat}: {imp:.6f}')

# Check if parity features alone can predict
print('\n=== Parity features only ===')
parity_cols = [c for c in X_train.columns if 'parity' in c]
dt_parity = DecisionTreeClassifier(max_depth=10, random_state=42)
dt_parity.fit(X_train[parity_cols], y_train)
tr_acc = accuracy_score(y_train, dt_parity.predict(X_train[parity_cols]))
va_acc = accuracy_score(y_val,   dt_parity.predict(X_val[parity_cols]))
te_acc = accuracy_score(y_test,  dt_parity.predict(X_test[parity_cols]))
print(f'  DT on parity features: train={tr_acc:.4f}, val={va_acc:.4f}, test={te_acc:.4f}')

# Check if count features alone can predict
print('\n=== Count features only ===')
count_cols = [c for c in X_train.columns if c.startswith('count_')]
dt_count = DecisionTreeClassifier(max_depth=10, random_state=42)
dt_count.fit(X_train[count_cols], y_train)
tr_acc = accuracy_score(y_train, dt_count.predict(X_train[count_cols]))
va_acc = accuracy_score(y_val,   dt_count.predict(X_val[count_cols]))
te_acc = accuracy_score(y_test,  dt_count.predict(X_test[count_cols]))
print(f'  DT on count features: train={tr_acc:.4f}, val={va_acc:.4f}, test={te_acc:.4f}')

# Investigate label noise ceiling
print('\n=== Label Noise Ceiling Analysis ===')
# If labels are noisy, the theoretical max accuracy is limited
# Check if same input sequences appear in train+val with different labels
all_data = pd.concat([train, val, test], ignore_index=True)
all_data['split'] = ['train']*len(train) + ['val']*len(val) + ['test']*len(test)

# Group by sequence
seq_groups = all_data.groupby(feature_cols)['label'].agg(['mean', 'count', 'std'])
seq_groups_conflict = seq_groups[seq_groups['std'] > 0]
print(f'Total unique sequences: {len(seq_groups)}')
print(f'Sequences with conflicting labels across splits: {len(seq_groups_conflict)}')

# Check if the label distribution is truly random
print('\n=== Checking if labels are random ===')
# If labels are random noise, no model can do better than ~50%
# Check mutual information between features and labels
from sklearn.feature_selection import mutual_info_classif
mi = mutual_info_classif(X_train, y_train, random_state=42)
mi_series = pd.Series(mi, index=X_train.columns)
top_mi = mi_series.nlargest(20)
print('Top 20 features by mutual information:')
for feat, mi_val in top_mi.items():
    print(f'  {feat}: {mi_val:.6f}')

print(f'\nMax MI: {mi.max():.6f}')
print(f'Mean MI: {mi.mean():.6f}')
print(f'Sum MI: {mi.sum():.6f}')

print('\nDone.')
