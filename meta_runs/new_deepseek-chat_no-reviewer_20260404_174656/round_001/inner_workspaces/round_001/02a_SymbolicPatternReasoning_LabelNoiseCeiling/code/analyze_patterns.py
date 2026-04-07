import pandas as pd
import numpy as np
from collections import Counter

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train = train[feature_cols]
y_train = train['label']

print("Analyzing patterns in the data...")
print(f"Dataset shapes: Train={train.shape}, Val={val.shape}, Test={test.shape}")

# Let's look for simple rules
# 1. Check if label depends on presence of specific tokens
print("\n=== Checking for token presence patterns ===")

# Get all unique tokens
all_tokens = set()
for col in feature_cols:
    all_tokens.update(X_train[col].unique())

print(f"Total unique tokens: {len(all_tokens)}")

# Check correlation between token presence and label
for token in sorted(all_tokens):
    # Check if token appears in any position
    token_present = X_train.apply(lambda row: any(row[col] == token for col in feature_cols), axis=1)
    pos_rate = y_train[token_present].mean()
    neg_rate = y_train[~token_present].mean()
    
    if abs(pos_rate - neg_rate) > 0.2:  # Significant difference
        print(f"Token {token}: Present label rate={pos_rate:.3f}, Absent label rate={neg_rate:.3f}, diff={pos_rate-neg_rate:.3f}")

# 2. Check position-specific patterns
print("\n=== Checking position-specific patterns ===")
for i, col in enumerate(feature_cols):
    print(f"\nPosition {i} ({col}):")
    pos_tokens = X_train[col].unique()
    for token in sorted(pos_tokens):
        mask = X_train[col] == token
        if mask.sum() > 20:  # Only consider tokens with enough samples
            label_rate = y_train[mask].mean()
            print(f"  {token}: count={mask.sum()}, label rate={label_rate:.3f}")

# 3. Check for transitions between tokens
print("\n=== Checking transition patterns ===")
# Look at pairs of consecutive tokens
for i in range(len(feature_cols)-1):
    col1 = feature_cols[i]
    col2 = feature_cols[i+1]
    
    # Create transition strings
    transitions = X_train[col1] + '->' + X_train[col2]
    
    # Get most common transitions and their label rates
    trans_counts = Counter(transitions)
    print(f"\nTransitions from position {i} to {i+1} (top 5):")
    for trans, count in trans_counts.most_common(5):
        mask = transitions == trans
        label_rate = y_train[mask].mean()
        print(f"  {trans}: count={count}, label rate={label_rate:.3f}")

# 4. Check for repeating patterns
print("\n=== Checking for repeating tokens ===")
# Count number of unique tokens in each sequence
unique_token_counts = X_train.apply(lambda row: len(set(row.values)), axis=1)
print(f"Unique tokens per sequence stats:")
print(f"  Min: {unique_token_counts.min()}")
print(f"  Max: {unique_token_counts.max()}")
print(f"  Mean: {unique_token_counts.mean():.2f}")
print(f"  Std: {unique_token_counts.std():.2f}")

# Check correlation with label
for count in range(1, 9):
    mask = unique_token_counts == count
    if mask.sum() > 10:
        label_rate = y_train[mask].mean()
        print(f"  {count} unique tokens: count={mask.sum()}, label rate={label_rate:.3f}")

# 5. Check shape/color patterns
print("\n=== Checking shape/color patterns ===")
# Convert tokens to shapes and colors
shapes_train = X_train.applymap(lambda x: x[0])
colors_train = X_train.applymap(lambda x: x[1])

# Check if all shapes/colors are the same in a sequence
all_same_shape = shapes_train.apply(lambda row: len(set(row)) == 1, axis=1)
all_same_color = colors_train.apply(lambda row: len(set(row)) == 1, axis=1)

print(f"Sequences with all same shape: {all_same_shape.sum()} ({all_same_shape.mean():.3f})")
print(f"  Label rate when all same shape: {y_train[all_same_shape].mean():.3f}")
print(f"Sequences with all same color: {all_same_color.sum()} ({all_same_color.mean():.3f})")
print(f"  Label rate when all same color: {y_train[all_same_color].mean():.3f}")

# Check alternating patterns
print("\n=== Checking alternating patterns ===")
# Check if shape alternates
shape_alternates = []
color_alternates = []

for idx, row in shapes_train.iterrows():
    shapes = row.values
    # Check if shape alternates (e.g., T,S,T,S,... or T,T,S,S,T,T,...)
    # Simple check: count changes
    changes = sum(1 for i in range(len(shapes)-1) if shapes[i] != shapes[i+1])
    shape_alternates.append(changes)

for idx, row in colors_train.iterrows():
    colors = row.values
    changes = sum(1 for i in range(len(colors)-1) if colors[i] != colors[i+1])
    color_alternates.append(changes)

shape_alternates = pd.Series(shape_alternates)
color_alternates = pd.Series(color_alternates)

print(f"Shape changes per sequence: mean={shape_alternates.mean():.2f}, std={shape_alternates.std():.2f}")
print(f"Color changes per sequence: mean={color_alternates.mean():.2f}, std={color_alternates.std():.2f}")

# Check correlation with label
print("\nLabel rate by number of shape changes:")
for changes in range(0, 8):
    mask = shape_alternates == changes
    if mask.sum() > 10:
        label_rate = y_train[mask].mean()
        print(f"  {changes} changes: count={mask.sum()}, label rate={label_rate:.3f}")