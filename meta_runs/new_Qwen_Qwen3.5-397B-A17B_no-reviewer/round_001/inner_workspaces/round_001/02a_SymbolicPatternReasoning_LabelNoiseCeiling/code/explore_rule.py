import pandas as pd
import numpy as np
from collections import Counter

np.random.seed(42)

print("Loading data...")
train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"Number of tokens per sequence: {len(feature_cols)}")

# Let's look at specific examples
print("\n=== Sample positive examples (label=1) ===")
positive_samples = train[train['label'] == 1].head(10)
for idx, row in positive_samples.iterrows():
    tokens = [row[col] for col in feature_cols]
    print(f"  {tokens}")

print("\n=== Sample negative examples (label=0) ===")
negative_samples = train[train['label'] == 0].head(10)
for idx, row in negative_samples.iterrows():
    tokens = [row[col] for col in feature_cols]
    print(f"  {tokens}")

# Check for patterns based on specific positions
print("\n=== Checking position-based patterns ===")

# Maybe the rule is about specific tokens at specific positions?
for col in feature_cols:
    for token in train[col].unique():
        mask = train[col] == token
        if mask.sum() >= 50:
            mean_label = train.loc[mask, 'label'].mean()
            if mean_label > 0.65 or mean_label < 0.35:
                print(f"STRONG: {col}={token}: mean={mean_label:.3f}, n={mask.sum()}")

# Check for patterns involving pairs of positions
print("\n=== Checking pair-based patterns ===")
for i in range(len(feature_cols)):
    for j in range(i+1, len(feature_cols)):
        col_i, col_j = feature_cols[i], feature_cols[j]
        # Check if same token at both positions
        same_token = train[col_i] == train[col_j]
        if same_token.sum() >= 50:
            mean_label = train.loc[same_token, 'label'].mean()
            if mean_label > 0.65 or mean_label < 0.35:
                print(f"STRONG: {col_i}=={col_j}: mean={mean_label:.3f}, n={same_token.sum()}")
        
        # Check if same shape at both positions
        same_shape = train[col_i].str[0] == train[col_j].str[0]
        if same_shape.sum() >= 100:
            mean_label = train.loc[same_shape, 'label'].mean()
            if mean_label > 0.60 or mean_label < 0.40:
                print(f"MODERATE: {col_i}[shape]=={col_j}[shape]: mean={mean_label:.3f}, n={same_shape.sum()}")
        
        # Check if same color at both positions
        same_color = train[col_i].str[1] == train[col_j].str[1]
        if same_color.sum() >= 100:
            mean_label = train.loc[same_color, 'label'].mean()
            if mean_label > 0.60 or mean_label < 0.40:
                print(f"MODERATE: {col_i}[color]=={col_j}[color]: mean={mean_label:.3f}, n={same_color.sum()}")

# Check for majority-based rules
print("\n=== Checking majority-based patterns ===")

def get_majority_shape(row):
    shapes = [row[col][0] for col in feature_cols]
    return Counter(shapes).most_common(1)[0]

def get_majority_color(row):
    colors = [row[col][1] for col in feature_cols]
    return Counter(colors).most_common(1)[0]

train['maj_shape'] = train.apply(get_majority_shape, axis=1)
train['maj_color'] = train.apply(get_majority_color, axis=1)

train['maj_shape_char'] = train['maj_shape'].apply(lambda x: x[0])
train['maj_shape_count'] = train['maj_shape'].apply(lambda x: x[1])
train['maj_color_char'] = train['maj_color'].apply(lambda x: x[0])
train['maj_color_count'] = train['maj_color'].apply(lambda x: x[1])

print("Majority shape distribution:")
print(train.groupby('maj_shape_char')['label'].agg(['mean', 'count']))

print("\nMajority color distribution:")
print(train.groupby('maj_color_char')['label'].agg(['mean', 'count']))

print("\nMajority shape count distribution:")
print(train.groupby('maj_shape_count')['label'].agg(['mean', 'count']))

print("\nMajority color count distribution:")
print(train.groupby('maj_color_count')['label'].agg(['mean', 'count']))

# Check for specific pattern: maybe it's about having a majority shape with count >= some threshold
print("\n=== Checking combined patterns ===")
for shape in ['T', 'S', 'C', 'D']:
    for threshold in [3, 4, 5]:
        mask = train['maj_shape_count'] >= threshold
        shape_mask = train['maj_shape_char'] == shape
        combined = mask & shape_mask
        if combined.sum() >= 30:
            mean_label = train.loc[combined, 'label'].mean()
            print(f"Shape {shape} count>={threshold}: mean={mean_label:.3f}, n={combined.sum()}")

# Check for pattern: specific shape at first AND last position
print("\n=== Checking first/last position patterns ===")
for shape in ['T', 'S', 'C', 'D']:
    mask = (train[feature_cols[0]].str[0] == shape) & (train[feature_cols[-1]].str[0] == shape)
    if mask.sum() >= 30:
        mean_label = train.loc[mask, 'label'].mean()
        print(f"First&Last shape={shape}: mean={mean_label:.3f}, n={mask.sum()}")

for color in ['r', 'g', 'b', 'y']:
    mask = (train[feature_cols[0]].str[1] == color) & (train[feature_cols[-1]].str[1] == color)
    if mask.sum() >= 30:
        mean_label = train.loc[mask, 'label'].mean()
        print(f"First&Last color={color}: mean={mean_label:.3f}, n={mask.sum()}")

# Check for pattern: token_0 shape == token_7 shape
print("\n=== Checking symmetric patterns ===")
for i in range(4):  # Check symmetric positions
    j = 7 - i
    col_i, col_j = feature_cols[i], feature_cols[j]
    
    same_shape = train[col_i].str[0] == train[col_j].str[0]
    mean_label = train.loc[same_shape, 'label'].mean()
    print(f"Symmetric [{i},{j}] same shape: mean={mean_label:.3f}, n={same_shape.sum()}")
    
    same_color = train[col_i].str[1] == train[col_j].str[1]
    mean_label = train.loc[same_color, 'label'].mean()
    print(f"Symmetric [{i},{j}] same color: mean={mean_label:.3f}, n={same_color.sum()}")

# Check for XOR-like patterns
print("\n=== Checking XOR patterns ===")
# Maybe the rule is: label = 1 if (condition_A XOR condition_B)

# Condition A: majority shape is T or S
# Condition B: majority color is r or b
cond_A = train['maj_shape_char'].isin(['T', 'S'])
cond_B = train['maj_color_char'].isin(['r', 'b'])
xor_mask = cond_A != cond_B  # XOR
mean_label = train.loc[xor_mask, 'label'].mean()
print(f"XOR(maj_shape in [T,S], maj_color in [r,b]): mean={mean_label:.3f}, n={xor_mask.sum()}")

# Try different XOR combinations
for shape_set in [['T', 'S'], ['T', 'C'], ['T', 'D'], ['S', 'C'], ['S', 'D'], ['C', 'D']]:
    for color_set in [['r', 'g'], ['r', 'b'], ['r', 'y'], ['g', 'b'], ['g', 'y'], ['b', 'y']]:
        cond_A = train['maj_shape_char'].isin(shape_set)
        cond_B = train['maj_color_char'].isin(color_set)
        xor_mask = cond_A != cond_B
        if xor_mask.sum() >= 200:
            mean_label = train.loc[xor_mask, 'label'].mean()
            if mean_label > 0.65 or mean_label < 0.35:
                print(f"XOR(maj_shape in {shape_set}, maj_color in {color_set}): mean={mean_label:.3f}, n={xor_mask.sum()}")
