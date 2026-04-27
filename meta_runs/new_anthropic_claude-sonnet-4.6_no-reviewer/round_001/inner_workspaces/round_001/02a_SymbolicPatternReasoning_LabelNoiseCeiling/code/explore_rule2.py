import pandas as pd
import numpy as np
from itertools import combinations, product

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

# Check for duplicate sequences with different labels (label noise)
print('=== Checking for label noise / duplicate sequences ===')
train_seq = train[feature_cols].apply(lambda row: tuple(row), axis=1)
val_seq   = val[feature_cols].apply(lambda row: tuple(row), axis=1)
test_seq  = test[feature_cols].apply(lambda row: tuple(row), axis=1)

# Within train
train_dup = train.groupby(feature_cols)['label'].agg(['mean', 'count', 'std'])
train_dup_conflict = train_dup[train_dup['std'] > 0]
print(f'Train: {len(train_dup_conflict)} unique sequences with conflicting labels out of {len(train_dup)} unique sequences')
print(f'Train: total sequences={len(train)}, unique={len(train_dup)}')

# Check noise level
if len(train_dup_conflict) > 0:
    print(f'Conflicting sequences: {len(train_dup_conflict)}')
    print(train_dup_conflict.head(10))

# Check if test sequences appear in train
train_seq_set = set(map(tuple, train[feature_cols].values))
test_in_train = sum(1 for seq in test[feature_cols].values if tuple(seq) in train_seq_set)
print(f'\nTest sequences found in train: {test_in_train}/{len(test)}')

# Rule: XOR / parity of specific features
print('\n=== XOR/parity of shape counts ===')
for s1, s2 in combinations(shapes, 2):
    c1 = train[shape_cols].apply(lambda row: (row == s1).sum(), axis=1)
    c2 = train[shape_cols].apply(lambda row: (row == s2).sum(), axis=1)
    pred = ((c1 + c2) % 2).astype(int)
    acc = (pred == train['label']).mean()
    if acc > 0.55:
        print(f'  (count_{s1}+count_{s2}) % 2: train_acc={acc:.4f}')

# Rule: specific shape appears at even/odd positions
print('\n=== Shape at even/odd positions ===')
even_shape_cols = [shape_cols[i] for i in range(0, len(shape_cols), 2)]
odd_shape_cols  = [shape_cols[i] for i in range(1, len(shape_cols), 2)]

for shape in shapes:
    pred_even = train[even_shape_cols].apply(lambda row: (row == shape).any(), axis=1).astype(int)
    pred_odd  = train[odd_shape_cols].apply(lambda row: (row == shape).any(), axis=1).astype(int)
    acc_e = (pred_even == train['label']).mean()
    acc_o = (pred_odd  == train['label']).mean()
    if acc_e > 0.55 or acc_o > 0.55:
        print(f'  {shape} in even positions: {acc_e:.4f}, odd positions: {acc_o:.4f}')

# Rule: specific color appears at even/odd positions
even_color_cols = [color_cols[i] for i in range(0, len(color_cols), 2)]
odd_color_cols  = [color_cols[i] for i in range(1, len(color_cols), 2)]

for color in colors:
    pred_even = train[even_color_cols].apply(lambda row: (row == color).any(), axis=1).astype(int)
    pred_odd  = train[odd_color_cols].apply(lambda row: (row == color).any(), axis=1).astype(int)
    acc_e = (pred_even == train['label']).mean()
    acc_o = (pred_odd  == train['label']).mean()
    if acc_e > 0.55 or acc_o > 0.55:
        print(f'  {color} in even positions: {acc_e:.4f}, odd positions: {acc_o:.4f}')

# Rule: specific token pair at adjacent positions
print('\n=== Adjacent token pair rules ===')
all_tokens = [s+c for s in shapes for c in colors]
for i in range(len(feature_cols)-1):
    for t1 in all_tokens:
        for t2 in all_tokens:
            pred = ((train[feature_cols[i]] == t1) & (train[feature_cols[i+1]] == t2)).astype(int)
            if pred.sum() > 20:  # enough samples
                acc = (pred == train['label']).mean()
                if acc > 0.65:
                    print(f'  pos{i}=={t1} AND pos{i+1}=={t2}: train_acc={acc:.4f}, n={pred.sum()}')

# Rule: count of specific token
print('\n=== Specific token count rules ===')
for token in all_tokens:
    count = train[feature_cols].apply(lambda row: (row == token).sum(), axis=1)
    corr = count.corr(train['label'])
    if abs(corr) > 0.05:
        print(f'  count({token}): corr={corr:.4f}')
    for thresh in range(1, 5):
        pred = (count >= thresh).astype(int)
        acc = (pred == train['label']).mean()
        if acc > 0.58:
            print(f'  count({token}) >= {thresh}: train_acc={acc:.4f}')

# Rule: sum of shape indices
print('\n=== Shape index sum rules ===')
shape_idx = {'T': 0, 'S': 1, 'C': 2, 'D': 3}
color_idx = {'r': 0, 'g': 1, 'b': 2, 'y': 3}

train['shape_sum'] = train[shape_cols].apply(lambda row: sum(shape_idx[s] for s in row), axis=1)
train['color_sum'] = train[color_cols].apply(lambda row: sum(color_idx[c] for c in row), axis=1)

for col in ['shape_sum', 'color_sum']:
    corr = train[col].corr(train['label'])
    print(f'  {col}: corr={corr:.4f}')
    for mod in [2, 3, 4]:
        pred = (train[col] % mod == 0).astype(int)
        acc = (pred == train['label']).mean()
        if acc > 0.55:
            print(f'    {col} % {mod} == 0: train_acc={acc:.4f}')

# Rule: first shape == last shape
print('\n=== First == Last rules ===')
pred = (train['token_0_shape'] == train['token_7_shape']).astype(int)
print(f'  first_shape == last_shape: train_acc={(pred == train["label"]).mean():.4f}')
pred = (train['token_0_color'] == train['token_7_color']).astype(int)
print(f'  first_color == last_color: train_acc={(pred == train["label"]).mean():.4f}')
pred = (train['token_0'] == train['token_7']).astype(int)
print(f'  first_token == last_token: train_acc={(pred == train["label"]).mean():.4f}')

# Rule: palindrome
print('\n=== Palindrome rules ===')
def is_palindrome(row):
    seq = [row[c] for c in feature_cols]
    return 1 if seq == seq[::-1] else 0

pred = train.apply(is_palindrome, axis=1)
print(f'  palindrome: train_acc={(pred == train["label"]).mean():.4f}, n_palindromes={pred.sum()}')

# Rule: sorted sequence
print('\n=== Sorted sequence rules ===')
def is_sorted_shapes(row):
    seq = [shape_idx[row[c]] for c in shape_cols]
    return 1 if seq == sorted(seq) else 0

pred = train.apply(is_sorted_shapes, axis=1)
print(f'  sorted_shapes: train_acc={(pred == train["label"]).mean():.4f}')

# Rule: specific shape appears exactly N times
print('\n=== Exact count rules ===')
for shape in shapes:
    counts = train[shape_cols].apply(lambda row: (row == shape).sum(), axis=1)
    for n in range(0, 9):
        pred = (counts == n).astype(int)
        if pred.sum() > 30:
            acc = (pred == train['label']).mean()
            if acc > 0.58:
                print(f'  count_{shape}=={n}: train_acc={acc:.4f}, n={pred.sum()}')

for color in colors:
    counts = train[color_cols].apply(lambda row: (row == color).sum(), axis=1)
    for n in range(0, 9):
        pred = (counts == n).astype(int)
        if pred.sum() > 30:
            acc = (pred == train['label']).mean()
            if acc > 0.58:
                print(f'  count_{color}=={n}: train_acc={acc:.4f}, n={pred.sum()}')

print('\nDone.')
