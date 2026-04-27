import pandas as pd
import numpy as np
from itertools import combinations

train = pd.read_csv('data/spr_bench_train.csv')
val   = pd.read_csv('data/spr_bench_val.csv')
test  = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

# Split tokens into shape and color
for df in [train, val, test]:
    for col in feature_cols:
        df[col + '_shape'] = df[col].str[0]
        df[col + '_color'] = df[col].str[1]

shape_cols = [c + '_shape' for c in feature_cols]
color_cols = [c + '_color' for c in feature_cols]

print('=== Exploring potential hidden rules ===')

# Rule 1: Count of each shape
shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']

for df, name in [(train, 'train'), (val, 'val')]:
    print(f'\n--- {name} ---')
    for shape in shapes:
        count_col = f'count_{shape}'
        df[count_col] = df[shape_cols].apply(lambda row: (row == shape).sum(), axis=1)
    for color in colors:
        count_col = f'count_{color}'
        df[count_col] = df[color_cols].apply(lambda row: (row == color).sum(), axis=1)

# Check if any single count predicts label
print('\n=== Shape count correlations with label ===')
for shape in shapes:
    col = f'count_{shape}'
    corr = train[col].corr(train['label'])
    print(f'  count_{shape}: corr={corr:.4f}')
    # Check if majority rule works
    for thresh in range(0, 9):
        pred = (train[col] >= thresh).astype(int)
        acc = (pred == train['label']).mean()
        if acc > 0.55:
            print(f'    count_{shape} >= {thresh}: train_acc={acc:.4f}')

print('\n=== Color count correlations with label ===')
for color in colors:
    col = f'count_{color}'
    corr = train[col].corr(train['label'])
    print(f'  count_{color}: corr={corr:.4f}')
    for thresh in range(0, 9):
        pred = (train[col] >= thresh).astype(int)
        acc = (pred == train['label']).mean()
        if acc > 0.55:
            print(f'    count_{color} >= {thresh}: train_acc={acc:.4f}')

# Rule 2: Majority shape/color
print('\n=== Majority shape/color rules ===')
train['majority_shape'] = train[shape_cols].apply(lambda row: row.mode()[0] if len(row.mode()) > 0 else 'X', axis=1)
train['majority_color'] = train[color_cols].apply(lambda row: row.mode()[0] if len(row.mode()) > 0 else 'X', axis=1)

for shape in shapes:
    acc = (train['majority_shape'] == shape).astype(int).corr(train['label'])
    print(f'  majority_shape=={shape}: corr={acc:.4f}')

for color in colors:
    acc = (train['majority_color'] == color).astype(int).corr(train['label'])
    print(f'  majority_color=={color}: corr={acc:.4f}')

# Rule 3: Specific token at specific position
print('\n=== Specific token at position rules ===')
for col in feature_cols:
    for token in train[col].unique():
        pred = (train[col] == token).astype(int)
        acc = (pred == train['label']).mean()
        if acc > 0.58:
            print(f'  {col}=={token}: train_acc={acc:.4f}')

# Rule 4: Consecutive same shape/color
print('\n=== Consecutive same shape/color ===')
def has_consecutive_shape(row, n=2):
    shapes_seq = [row[c] for c in shape_cols]
    for i in range(len(shapes_seq) - n + 1):
        if len(set(shapes_seq[i:i+n])) == 1:
            return 1
    return 0

def has_consecutive_color(row, n=2):
    colors_seq = [row[c] for c in color_cols]
    for i in range(len(colors_seq) - n + 1):
        if len(set(colors_seq[i:i+n])) == 1:
            return 1
    return 0

for n in [2, 3, 4]:
    pred_shape = train.apply(lambda row: has_consecutive_shape(row, n), axis=1)
    pred_color = train.apply(lambda row: has_consecutive_color(row, n), axis=1)
    acc_s = (pred_shape == train['label']).mean()
    acc_c = (pred_color == train['label']).mean()
    print(f'  consecutive_shape(n={n}): train_acc={acc_s:.4f}')
    print(f'  consecutive_color(n={n}): train_acc={acc_c:.4f}')

# Rule 5: All same shape or all same color
print('\n=== All same shape/color ===')
pred_all_shape = train.apply(lambda row: 1 if len(set(row[c] for c in shape_cols)) == 1 else 0, axis=1)
pred_all_color = train.apply(lambda row: 1 if len(set(row[c] for c in color_cols)) == 1 else 0, axis=1)
print(f'  all_same_shape: train_acc={(pred_all_shape == train["label"]).mean():.4f}')
print(f'  all_same_color: train_acc={(pred_all_color == train["label"]).mean():.4f}')

# Rule 6: Alternating pattern
print('\n=== Alternating patterns ===')
def is_alternating_shape(row):
    shapes_seq = [row[c] for c in shape_cols]
    for i in range(0, len(shapes_seq)-2, 2):
        if shapes_seq[i] != shapes_seq[i+2]:
            return 0
    return 1

pred_alt = train.apply(is_alternating_shape, axis=1)
print(f'  alternating_shape: train_acc={(pred_alt == train["label"]).mean():.4f}')

# Rule 7: Unique shapes count
print('\n=== Unique shape/color count ===')
train['n_unique_shapes'] = train.apply(lambda row: len(set(row[c] for c in shape_cols)), axis=1)
train['n_unique_colors'] = train.apply(lambda row: len(set(row[c] for c in color_cols)), axis=1)

for col in ['n_unique_shapes', 'n_unique_colors']:
    corr = train[col].corr(train['label'])
    print(f'  {col}: corr={corr:.4f}')
    for val_thresh in train[col].unique():
        pred = (train[col] == val_thresh).astype(int)
        acc = (pred == train['label']).mean()
        if acc > 0.55:
            print(f'    {col}=={val_thresh}: train_acc={acc:.4f}')

# Rule 8: Specific shape at first/last position
print('\n=== First/last token rules ===')
for shape in shapes:
    pred_first = (train['token_0_shape'] == shape).astype(int)
    pred_last  = (train['token_7_shape'] == shape).astype(int)
    acc_f = (pred_first == train['label']).mean()
    acc_l = (pred_last  == train['label']).mean()
    if acc_f > 0.55 or acc_l > 0.55:
        print(f'  first_shape=={shape}: {acc_f:.4f}, last_shape=={shape}: {acc_l:.4f}')

for color in colors:
    pred_first = (train['token_0_color'] == color).astype(int)
    pred_last  = (train['token_7_color'] == color).astype(int)
    acc_f = (pred_first == train['label']).mean()
    acc_l = (pred_last  == train['label']).mean()
    if acc_f > 0.55 or acc_l > 0.55:
        print(f'  first_color=={color}: {acc_f:.4f}, last_color=={color}: {acc_l:.4f}')

# Rule 9: Parity of shape counts
print('\n=== Parity rules ===')
for shape in shapes:
    col = f'count_{shape}'
    pred_even = (train[col] % 2 == 0).astype(int)
    pred_odd  = (train[col] % 2 == 1).astype(int)
    acc_e = (pred_even == train['label']).mean()
    acc_o = (pred_odd  == train['label']).mean()
    if acc_e > 0.55 or acc_o > 0.55:
        print(f'  count_{shape} even: {acc_e:.4f}, odd: {acc_o:.4f}')

for color in colors:
    col = f'count_{color}'
    pred_even = (train[col] % 2 == 0).astype(int)
    pred_odd  = (train[col] % 2 == 1).astype(int)
    acc_e = (pred_even == train['label']).mean()
    acc_o = (pred_odd  == train['label']).mean()
    if acc_e > 0.55 or acc_o > 0.55:
        print(f'  count_{color} even: {acc_e:.4f}, odd: {acc_o:.4f}')

print('\nDone exploring rules.')
