import pandas as pd
import numpy as np
from collections import Counter
import itertools

train = pd.read_csv('data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Let's check for specific sequences or patterns
# e.g., "contains Tr followed by Cb"

def check_pattern(df, pattern_func, name):
    df[name] = df[feature_cols].apply(pattern_func, axis=1)
    corr = df['label'].corr(df[name])
    if abs(corr) > 0.1:
        print(f"Correlation with {name}: {corr:.4f}")

# Check for adjacent identical shapes/colors
def has_adjacent_same_shape(row):
    tokens = [row[col] for col in feature_cols]
    for i in range(len(tokens)-1):
        if tokens[i][0] == tokens[i+1][0]:
            return True
    return False

def has_adjacent_same_color(row):
    tokens = [row[col] for col in feature_cols]
    for i in range(len(tokens)-1):
        if tokens[i][1] == tokens[i+1][1]:
            return True
    return False

check_pattern(train, has_adjacent_same_shape, 'has_adjacent_same_shape')
check_pattern(train, has_adjacent_same_color, 'has_adjacent_same_color')

# Check for palindromes
def is_palindrome(row):
    tokens = [row[col] for col in feature_cols]
    return tokens == tokens[::-1]

check_pattern(train, is_palindrome, 'is_palindrome')

# Check for alternating patterns
def is_alternating_shape(row):
    tokens = [row[col] for col in feature_cols]
    for i in range(len(tokens)-2):
        if tokens[i][0] != tokens[i+2][0]:
            return False
    return True

check_pattern(train, is_alternating_shape, 'is_alternating_shape')

# Check for specific counts of shapes/colors
shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']

for s in shapes:
    train[f'count_{s}'] = train[feature_cols].apply(lambda x: sum(1 for t in x if t[0] == s), axis=1)
    corr = train['label'].corr(train[f'count_{s}'])
    if abs(corr) > 0.1:
        print(f"Correlation with count_{s}: {corr:.4f}")

for c in colors:
    train[f'count_{c}'] = train[feature_cols].apply(lambda x: sum(1 for t in x if t[1] == c), axis=1)
    corr = train['label'].corr(train[f'count_{c}'])
    if abs(corr) > 0.1:
        print(f"Correlation with count_{c}: {corr:.4f}")

# Check for specific combinations of counts
# e.g., count_T == count_S
for s1, s2 in itertools.combinations(shapes, 2):
    train[f'eq_{s1}_{s2}'] = train[f'count_{s1}'] == train[f'count_{s2}']
    corr = train['label'].corr(train[f'eq_{s1}_{s2}'])
    if abs(corr) > 0.1:
        print(f"Correlation with eq_{s1}_{s2}: {corr:.4f}")

for c1, c2 in itertools.combinations(colors, 2):
    train[f'eq_{c1}_{c2}'] = train[f'count_{c1}'] == train[f'count_{c2}']
    corr = train['label'].corr(train[f'eq_{c1}_{c2}'])
    if abs(corr) > 0.1:
        print(f"Correlation with eq_{c1}_{c2}: {corr:.4f}")

# Check for majority shape/color
def majority_shape(row):
    tokens = [row[col] for col in feature_cols]
    counts = Counter([t[0] for t in tokens])
    return counts.most_common(1)[0][1] > len(tokens) / 2

check_pattern(train, majority_shape, 'majority_shape')

# Check for presence of all shapes/colors
def has_all_shapes(row):
    tokens = [row[col] for col in feature_cols]
    return len(set([t[0] for t in tokens])) == 4

check_pattern(train, has_all_shapes, 'has_all_shapes')

def has_all_colors(row):
    tokens = [row[col] for col in feature_cols]
    return len(set([t[1] for t in tokens])) == 4

check_pattern(train, has_all_colors, 'has_all_colors')

# Let's look at the first and last tokens
for s in shapes:
    train[f'first_is_{s}'] = train['token_0'].str[0] == s
    corr = train['label'].corr(train[f'first_is_{s}'])
    if abs(corr) > 0.1:
        print(f"Correlation with first_is_{s}: {corr:.4f}")
        
    train[f'last_is_{s}'] = train[f'token_{len(feature_cols)-1}'].str[0] == s
    corr = train['label'].corr(train[f'last_is_{s}'])
    if abs(corr) > 0.1:
        print(f"Correlation with last_is_{s}: {corr:.4f}")
