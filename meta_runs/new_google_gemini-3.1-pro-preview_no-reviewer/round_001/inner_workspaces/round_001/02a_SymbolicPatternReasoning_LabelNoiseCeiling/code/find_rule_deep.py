import pandas as pd
import numpy as np
from collections import Counter
import itertools

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Let's try to find the rule by looking at the differences between positive and negative examples
pos_train = train[train['label'] == 1]
neg_train = train[train['label'] == 0]

print(f"Positive examples: {len(pos_train)}")
print(f"Negative examples: {len(neg_train)}")

# Let's look at the length of the sequences
print(f"Sequence length: {len(feature_cols)}")

# Let's check for specific sub-sequences
def count_subsequences(df, length):
    subseqs = []
    for i, row in df.iterrows():
        tokens = [row[col] for col in feature_cols]
        for j in range(len(tokens) - length + 1):
            subseqs.append(tuple(tokens[j:j+length]))
    return Counter(subseqs)

pos_bigrams = count_subsequences(pos_train, 2)
neg_bigrams = count_subsequences(neg_train, 2)

print("\nTop 5 bigrams in positive examples:")
print(pos_bigrams.most_common(5))
print("Top 5 bigrams in negative examples:")
print(neg_bigrams.most_common(5))

# Let's check for specific shape sub-sequences
def count_shape_subsequences(df, length):
    subseqs = []
    for i, row in df.iterrows():
        tokens = [row[col][0] for col in feature_cols]
        for j in range(len(tokens) - length + 1):
            subseqs.append(tuple(tokens[j:j+length]))
    return Counter(subseqs)

pos_shape_bigrams = count_shape_subsequences(pos_train, 2)
neg_shape_bigrams = count_shape_subsequences(neg_train, 2)

print("\nTop 5 shape bigrams in positive examples:")
print(pos_shape_bigrams.most_common(5))
print("Top 5 shape bigrams in negative examples:")
print(neg_shape_bigrams.most_common(5))

# Let's check for specific color sub-sequences
def count_color_subsequences(df, length):
    subseqs = []
    for i, row in df.iterrows():
        tokens = [row[col][1] for col in feature_cols]
        for j in range(len(tokens) - length + 1):
            subseqs.append(tuple(tokens[j:j+length]))
    return Counter(subseqs)

pos_color_bigrams = count_color_subsequences(pos_train, 2)
neg_color_bigrams = count_color_subsequences(neg_train, 2)

print("\nTop 5 color bigrams in positive examples:")
print(pos_color_bigrams.most_common(5))
print("Top 5 color bigrams in negative examples:")
print(neg_color_bigrams.most_common(5))

# Let's check for symmetry
def is_symmetric(row):
    tokens = [row[col] for col in feature_cols]
    return tokens == tokens[::-1]

train['is_symmetric'] = train.apply(is_symmetric, axis=1)
print(f"\nSymmetric sequences: {train['is_symmetric'].sum()}")

# Let's check for shape symmetry
def is_shape_symmetric(row):
    tokens = [row[col][0] for col in feature_cols]
    return tokens == tokens[::-1]

train['is_shape_symmetric'] = train.apply(is_shape_symmetric, axis=1)
print(f"Shape symmetric sequences: {train['is_shape_symmetric'].sum()}")

# Let's check for color symmetry
def is_color_symmetric(row):
    tokens = [row[col][1] for col in feature_cols]
    return tokens == tokens[::-1]

train['is_color_symmetric'] = train.apply(is_color_symmetric, axis=1)
print(f"Color symmetric sequences: {train['is_color_symmetric'].sum()}")

# Let's check for number of unique tokens
train['num_unique_tokens'] = train[feature_cols].apply(lambda x: len(set(x)), axis=1)
print(f"\nCorrelation with num_unique_tokens: {train['label'].corr(train['num_unique_tokens']):.4f}")

# Let's check for specific token counts
for token in set(itertools.chain(*[train[col].unique() for col in feature_cols])):
    train[f'count_{token}'] = train[feature_cols].apply(lambda x: sum(1 for t in x if t == token), axis=1)
    corr = train['label'].corr(train[f'count_{token}'])
    if abs(corr) > 0.1:
        print(f"Correlation with count_{token}: {corr:.4f}")
