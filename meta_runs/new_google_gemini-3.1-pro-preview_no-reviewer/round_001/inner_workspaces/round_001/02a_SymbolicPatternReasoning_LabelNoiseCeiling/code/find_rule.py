import pandas as pd
import numpy as np
from collections import Counter

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Let's look at the distribution of labels
print("Label distribution:")
print(train['label'].value_counts(normalize=True))

# Let's look at the most common tokens in positive vs negative examples
pos_train = train[train['label'] == 1]
neg_train = train[train['label'] == 0]

pos_tokens = []
for col in feature_cols:
    pos_tokens.extend(pos_train[col].tolist())
    
neg_tokens = []
for col in feature_cols:
    neg_tokens.extend(neg_train[col].tolist())

print("\nTop 5 tokens in positive examples:")
print(Counter(pos_tokens).most_common(5))

print("\nTop 5 tokens in negative examples:")
print(Counter(neg_tokens).most_common(5))

# Let's look at shapes and colors separately
pos_shapes = [t[0] for t in pos_tokens]
pos_colors = [t[1] for t in pos_tokens]
neg_shapes = [t[0] for t in neg_tokens]
neg_colors = [t[1] for t in neg_tokens]

print("\nShape distribution in positive examples:")
print(Counter(pos_shapes).most_common())
print("Shape distribution in negative examples:")
print(Counter(neg_shapes).most_common())

print("\nColor distribution in positive examples:")
print(Counter(pos_colors).most_common())
print("Color distribution in negative examples:")
print(Counter(neg_colors).most_common())

# Let's check for specific patterns, like "contains X"
for shape in ['T', 'S', 'C', 'D']:
    for color in ['r', 'g', 'b', 'y']:
        token = f"{shape}{color}"
        train[f'has_{token}'] = train[feature_cols].apply(lambda x: token in x.values, axis=1)
        corr = train['label'].corr(train[f'has_{token}'])
        if abs(corr) > 0.1:
            print(f"Correlation with has_{token}: {corr:.4f}")

# Check for "all tokens have same shape/color"
train['same_shape'] = train[feature_cols].apply(lambda x: len(set([t[0] for t in x])) == 1, axis=1)
train['same_color'] = train[feature_cols].apply(lambda x: len(set([t[1] for t in x])) == 1, axis=1)
print(f"\nCorrelation with same_shape: {train['label'].corr(train['same_shape']):.4f}")
print(f"Correlation with same_color: {train['label'].corr(train['same_color']):.4f}")

# Check for number of unique shapes/colors
train['num_unique_shapes'] = train[feature_cols].apply(lambda x: len(set([t[0] for t in x])), axis=1)
train['num_unique_colors'] = train[feature_cols].apply(lambda x: len(set([t[1] for t in x])), axis=1)
print(f"\nCorrelation with num_unique_shapes: {train['label'].corr(train['num_unique_shapes']):.4f}")
print(f"Correlation with num_unique_colors: {train['label'].corr(train['num_unique_colors']):.4f}")
