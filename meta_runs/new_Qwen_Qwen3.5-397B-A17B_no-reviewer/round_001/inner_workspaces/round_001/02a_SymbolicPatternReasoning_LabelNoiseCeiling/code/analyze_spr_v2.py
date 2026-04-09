import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from itertools import combinations

np.random.seed(42)

print("Loading data...")
train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"Number of tokens per sequence: {len(feature_cols)}")

def parse_token(token):
    return token[0], token[1]

# Analyze patterns in the data
print("\n=== Analyzing patterns ===")

# Check if there are position-specific patterns
for col in feature_cols:
    for token in train[col].unique()[:4]:
        mask = train[col] == token
        if mask.sum() > 10:
            label_dist = train.loc[mask, 'label'].mean()
            print(f"{col}={token}: label mean = {label_dist:.3f} (n={mask.sum()})")
    break  # Just check first column

# Check for pair patterns
print("\nChecking token pair correlations...")
for i, j in [(0, 1), (0, 4), (4, 7), (0, 7)]:
    col_i, col_j = feature_cols[i], feature_cols[j]
    pair_counts = train.groupby([col_i, col_j])['label'].agg(['mean', 'count'])
    high_corr_pairs = pair_counts[pair_counts['count'] > 20].nlargest(5, 'mean')
    print(f"\nTop pairs for ({col_i}, {col_j}) by label mean:")
    print(high_corr_pairs)

# Check for shape/color patterns
print("\n=== Shape/Color Analysis ===")
shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']

# Count shapes and colors per sample
for shape in shapes:
    shape_counts = []
    labels = []
    for idx, row in train.iterrows():
        count = sum(1 for col in feature_cols if row[col][0] == shape)
        shape_counts.append(count)
        labels.append(row['label'])
    df_temp = pd.DataFrame({'count': shape_counts, 'label': labels})
    print(f"Shape {shape}: mean label by count = {df_temp.groupby('count')['label'].mean().to_dict()}")

for color in colors:
    color_counts = []
    labels = []
    for idx, row in train.iterrows():
        count = sum(1 for col in feature_cols if row[col][1] == color)
        color_counts.append(count)
        labels.append(row['label'])
    df_temp = pd.DataFrame({'count': color_counts, 'label': labels})
    print(f"Color {color}: mean label by count = {df_temp.groupby('count')['label'].mean().to_dict()}")

# Check for specific pattern: maybe it's about matching pairs
print("\n=== Checking for matching patterns ===")

def count_matching_pairs(row, feature_cols):
    """Count how many pairs of tokens match"""
    tokens = [row[col] for col in feature_cols]
    matches = 0
    for i in range(len(tokens)):
        for j in range(i+1, len(tokens)):
            if tokens[i] == tokens[j]:
                matches += 1
    return matches

train['matching_pairs'] = train.apply(lambda row: count_matching_pairs(row, feature_cols), axis=1)
print(f"Matching pairs vs label:")
print(train.groupby('matching_pairs')['label'].agg(['mean', 'count']))

# Check for shape matching
def count_shape_matches(row, feature_cols):
    shapes = [row[col][0] for col in feature_cols]
    matches = 0
    for i in range(len(shapes)):
        for j in range(i+1, len(shapes)):
            if shapes[i] == shapes[j]:
                matches += 1
    return matches

train['shape_matches'] = train.apply(lambda row: count_shape_matches(row, feature_cols), axis=1)
print(f"\nShape matches vs label:")
print(train.groupby('shape_matches')['label'].agg(['mean', 'count']))

# Check for color matching
def count_color_matches(row, feature_cols):
    colors_list = [row[col][1] for col in feature_cols]
    matches = 0
    for i in range(len(colors_list)):
        for j in range(i+1, len(colors_list)):
            if colors_list[i] == colors_list[j]:
                matches += 1
    return matches

train['color_matches'] = train.apply(lambda row: count_color_matches(row, feature_cols), axis=1)
print(f"\nColor matches vs label:")
print(train.groupby('color_matches')['label'].agg(['mean', 'count']))

# Check for specific token at specific position
print("\n=== Position-specific token analysis ===")
for col in feature_cols:
    for token in ['Tr', 'Tb', 'Cr', 'Cb', 'Sr', 'Sb', 'Dr', 'Db']:
        mask = train[col] == token
        if mask.sum() >= 10:
            mean_label = train.loc[mask, 'label'].mean()
            if mean_label > 0.6 or mean_label < 0.4:
                print(f"{col}={token}: mean label = {mean_label:.3f} (n={mask.sum()})")

# Check for adjacency patterns
print("\n=== Adjacency patterns ===")
for i in range(len(feature_cols) - 1):
    col1, col2 = feature_cols[i], feature_cols[i+1]
    # Check if same shape adjacent
    same_shape = train.apply(lambda row: row[col1][0] == row[col2][0], axis=1)
    print(f"Adjacent same shape ({col1},{col2}): label mean = {train.loc[same_shape, 'label'].mean():.3f} (n={same_shape.sum()})")
    
    # Check if same color adjacent
    same_color = train.apply(lambda row: row[col1][1] == row[col2][1], axis=1)
    print(f"Adjacent same color ({col1},{col2}): label mean = {train.loc[same_color, 'label'].mean():.3f} (n={same_color.sum()})")
