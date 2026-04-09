import pandas as pd
import numpy as np
from collections import Counter
from itertools import combinations

np.random.seed(42)

print("Loading data...")
train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"Number of tokens per sequence: {len(feature_cols)}")

# Combine all data for analysis
all_data = pd.concat([train, val, test], ignore_index=True)
print(f"Total samples: {len(all_data)}")

# Look for exact duplicate sequences with different labels
print("\n=== Checking for label noise (same sequence, different labels) ===")
df_temp = all_data.copy()
df_temp['seq_key'] = df_temp[feature_cols].apply(lambda x: tuple(x), axis=1)
seq_counts = df_temp.groupby('seq_key').agg({'label': ['count', 'mean', 'std']})
seq_counts.columns = ['count', 'mean', 'std']
multi_label_seqs = seq_counts[seq_counts['count'] > 1]
print(f"Sequences appearing multiple times: {len(multi_label_seqs)}")
if len(multi_label_seqs) > 0:
    print(multi_label_seqs.head(20))

# Check std > 0 means different labels for same sequence
noisy_seqs = seq_counts[seq_counts['std'] > 0]
print(f"\nSequences with conflicting labels (potential noise): {len(noisy_seqs)}")
if len(noisy_seqs) > 0:
    print(noisy_seqs.head(10))

# Let's look at the structure more carefully
print("\n=== Analyzing token distributions ===")
for col in feature_cols:
    token_dist = all_data[col].value_counts()
    print(f"\n{col} distribution (top 5):")
    print(token_dist.head())

shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']

# Check for patterns based on shape sequences
print("\n=== Analyzing shape sequences ===")
all_data['shape_seq'] = all_data.apply(lambda row: tuple(row[col][0] for col in feature_cols), axis=1)
shape_seq_stats = all_data.groupby('shape_seq')['label'].agg(['mean', 'count'])
extreme_shapes = shape_seq_stats[(shape_seq_stats['count'] >= 20) & ((shape_seq_stats['mean'] > 0.7) | (shape_seq_stats['mean'] < 0.3))]
if len(extreme_shapes) > 0:
    print("Shape sequences with extreme label bias:")
    print(extreme_shapes.head(20))
else:
    print("No shape sequences with extreme bias found.")

# Check for patterns based on color sequences
print("\n=== Analyzing color sequences ===")
all_data['color_seq'] = all_data.apply(lambda row: tuple(row[col][1] for col in feature_cols), axis=1)
color_seq_stats = all_data.groupby('color_seq')['label'].agg(['mean', 'count'])
extreme_colors = color_seq_stats[(color_seq_stats['count'] >= 20) & ((color_seq_stats['mean'] > 0.7) | (color_seq_stats['mean'] < 0.3))]
if len(extreme_colors) > 0:
    print("Color sequences with extreme label bias:")
    print(extreme_colors.head(20))
else:
    print("No color sequences with extreme bias found.")

# Check for specific patterns: maybe it's about having certain shapes in certain positions
print("\n=== Checking complex patterns ===")

# Pattern: Does having T in position 0 AND S in position 1 predict label?
for s0 in shapes:
    for s1 in shapes:
        mask = (all_data[feature_cols[0]].str[0] == s0) & (all_data[feature_cols[1]].str[0] == s1)
        if mask.sum() >= 50:
            mean_label = all_data.loc[mask, 'label'].mean()
            if mean_label > 0.6 or mean_label < 0.4:
                print(f"Shape[0]={s0} AND Shape[1]={s1}: mean={mean_label:.3f}, n={mask.sum()}")

# Check for patterns: majority shape with specific count
print("\n=== Checking majority patterns with thresholds ===")
for shape in shapes:
    for count_threshold in [3, 4, 5]:
        def check_pattern(row, s=shape, thresh=count_threshold):
            shape_counts = Counter(row[col][0] for col in feature_cols)
            return shape_counts.get(s, 0) >= thresh
        
        mask = all_data.apply(check_pattern, axis=1)
        if mask.sum() >= 50:
            mean_label = all_data.loc[mask, 'label'].mean()
            if mean_label > 0.6 or mean_label < 0.4:
                print(f"Shape {shape} count>={count_threshold}: mean={mean_label:.3f}, n={mask.sum()}")

# Check for XOR-like patterns between shape and color majority
print("\n=== Checking XOR patterns ===")
for shape_group in [['T', 'S'], ['T', 'C'], ['T', 'D'], ['S', 'C'], ['S', 'D'], ['C', 'D'], ['T'], ['S'], ['C'], ['D']]:
    for color_group in [['r', 'g'], ['r', 'b'], ['r', 'y'], ['g', 'b'], ['g', 'y'], ['b', 'y'], ['r'], ['g'], ['b'], ['y']]:
        def get_maj_shape(row):
            return Counter(row[col][0] for col in feature_cols).most_common(1)[0][0]
        def get_maj_color(row):
            return Counter(row[col][1] for col in feature_cols).most_common(1)[0][0]
        
        all_data['maj_s'] = all_data.apply(get_maj_shape, axis=1)
        all_data['maj_c'] = all_data.apply(get_maj_color, axis=1)
        
        cond_A = all_data['maj_s'].isin(shape_group)
        cond_B = all_data['maj_c'].isin(color_group)
        
        # XOR
        xor_mask = cond_A != cond_B
        if xor_mask.sum() >= 200:
            mean_label = all_data.loc[xor_mask, 'label'].mean()
            if mean_label > 0.65 or mean_label < 0.35:
                print(f"XOR(shape in {shape_group}, color in {color_group}): mean={mean_label:.3f}, n={xor_mask.sum()}")
        
        # AND
        and_mask = cond_A & cond_B
        if and_mask.sum() >= 200:
            mean_label = all_data.loc[and_mask, 'label'].mean()
            if mean_label > 0.65 or mean_label < 0.35:
                print(f"AND(shape in {shape_group}, color in {color_group}): mean={mean_label:.3f}, n={and_mask.sum()}")
        
        # OR
        or_mask = cond_A | cond_B
        if or_mask.sum() >= 200:
            mean_label = all_data.loc[or_mask, 'label'].mean()
            if mean_label > 0.65 or mean_label < 0.35:
                print(f"OR(shape in {shape_group}, color in {color_group}): mean={mean_label:.3f}, n={or_mask.sum()}")

# Check for pattern: count of specific shape-color combinations
print("\n=== Checking shape-color count patterns ===")
for shape in shapes:
    for color in colors:
        def count_sc(row, s=shape, c=color):
            return sum(1 for col in feature_cols if row[col][0] == s and row[col][1] == c)
        
        all_data[f'count_{shape}{color}'] = all_data.apply(count_sc, axis=1)
        for threshold in [2, 3, 4]:
            mask = all_data[f'count_{shape}{color}'] >= threshold
            if mask.sum() >= 50:
                mean_label = all_data.loc[mask, 'label'].mean()
                if mean_label > 0.6 or mean_label < 0.4:
                    print(f"Count({shape}{color})>={threshold}: mean={mean_label:.3f}, n={mask.sum()}")

# Check for pattern: is the first token's shape the same as the last token's shape?
print("\n=== Checking first-last patterns ===")
for shape in shapes:
    mask = (all_data[feature_cols[0]].str[0] == shape) & (all_data[feature_cols[-1]].str[0] == shape)
    if mask.sum() >= 100:
        mean_label = all_data.loc[mask, 'label'].mean()
        print(f"First&Last shape={shape}: mean={mean_label:.3f}, n={mask.sum()}")

for color in colors:
    mask = (all_data[feature_cols[0]].str[1] == color) & (all_data[feature_cols[-1]].str[1] == color)
    if mask.sum() >= 100:
        mean_label = all_data.loc[mask, 'label'].mean()
        print(f"First&Last color={color}: mean={mean_label:.3f}, n={mask.sum()}")

# Check for pattern: number of unique shapes/colors
print("\n=== Checking uniqueness patterns ===")
def count_unique_shapes(row):
    return len(set(row[col][0] for col in feature_cols))
def count_unique_colors(row):
    return len(set(row[col][1] for col in feature_cols))

all_data['unique_shapes'] = all_data.apply(count_unique_shapes, axis=1)
all_data['unique_colors'] = all_data.apply(count_unique_colors, axis=1)

print("Unique shapes vs label:")
print(all_data.groupby('unique_shapes')['label'].agg(['mean', 'count']))

print("\nUnique colors vs label:")
print(all_data.groupby('unique_colors')['label'].agg(['mean', 'count']))
