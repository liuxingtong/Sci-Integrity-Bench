import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import roc_auc_score, classification_report, roc_curve
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Load data
train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

# Define symbols
symbols = ['1', '2', 'A', 'B', 'C', 'D']

# Feature engineering functions
def extract_features(df):
    """Extract features from symbolic sequences"""
    features = pd.DataFrame(index=df.index)
    
    # 1. Symbol frequencies
    for sym in symbols:
        features[f'freq_{sym}'] = df['sym_seq'].apply(lambda x: x.count(sym))
    
    # 2. Normalized frequencies (proportions)
    total_chars = df['sym_seq'].apply(len)
    for sym in symbols:
        features[f'prop_{sym}'] = features[f'freq_{sym}'] / total_chars
    
    # 3. Position-specific features (first, last, middle)
    features['first_symbol'] = df['sym_seq'].apply(lambda x: x[0])
    features['last_symbol'] = df['sym_seq'].apply(lambda x: x[-1])
    features['middle_symbol'] = df['sym_seq'].apply(lambda x: x[10])  # 20 chars, middle is index 10
    
    # Convert categorical position features to one-hot
    for pos_feat in ['first_symbol', 'last_symbol', 'middle_symbol']:
        dummies = pd.get_dummies(features[pos_feat], prefix=pos_feat)
        features = pd.concat([features, dummies], axis=1)
    
    # Drop original categorical columns
    features = features.drop(['first_symbol', 'last_symbol', 'middle_symbol'], axis=1)
    
    # 4. Transition features (bigrams)
    # Count transitions between symbols
    transition_pairs = []
    for i in range(len(symbols)):
        for j in range(len(symbols)):
            transition_pairs.append(f'{symbols[i]}{symbols[j]}')
    
    for pair in transition_pairs:
        features[f'trans_{pair}'] = df['sym_seq'].apply(lambda x: x.count(pair))
    
    # 5. Sequence complexity features
    # Unique symbols count
    features['unique_symbols'] = df['sym_seq'].apply(lambda x: len(set(x)))
    
    # Longest run of same symbol
    def longest_run(seq):
        max_run = 1
        current_run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        return max_run
    
    features['longest_run'] = df['sym_seq'].apply(longest_run)
    
    # 6. Symbol diversity (entropy-like measure)
    def symbol_entropy(seq):
        from collections import Counter
        import math
        counts = Counter(seq)
        total = len(seq)
        entropy = 0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p) if p > 0 else 0
        return entropy
    
    features['symbol_entropy'] = df['sym_seq'].apply(symbol_entropy)
    
    # 7. Position of first occurrence of each symbol
    for sym in symbols:
        features[f'first_pos_{sym}'] = df['sym_seq'].apply(lambda x: x.find(sym) if sym in x else -1)
    
    # 8. Count of digit symbols vs letter symbols
    features['digit_count'] = df['sym_seq'].apply(lambda x: sum(1 for c in x if c in ['1', '2']))
    features['letter_count'] = df['sym_seq'].apply(lambda x: sum(1 for c in x if c in ['A', 'B', 'C', 'D']))
    features['digit_prop'] = features['digit_count'] / total_chars
    features['letter_prop'] = features['letter_count'] / total_chars
    
    return features

# Extract features for all datasets
print("Extracting features...")
train_features = extract_features(train)
val_features = extract_features(val)
test_features = extract_features(test)

print(f"Train features shape: {train_features.shape}")
print(f"Validation features shape: {val_features.shape}")
print(f"Test features shape: {test_features.shape}")

# Get target variables
y_train = train['default_flag'].values
y_val = val['default_flag'].values
y_test = test['default_flag'].values

# Save features
os.makedirs('../outputs', exist_ok=True)
train_features.to_csv('../outputs/train_features.csv', index=False)
val_features.to_csv('../outputs/val_features.csv', index=False)
test_features.to_csv('../outputs/test_features.csv', index=False)

print("\nFeature extraction complete!")
print(f"Number of features: {train_features.shape[1]}")

# Show some example features
print("\nFirst few feature rows:")
print(train_features.head())

# Check for any missing values
print(f"\nMissing values in train: {train_features.isnull().sum().sum()}")
print(f"Missing values in val: {val_features.isnull().sum().sum()}")
print(f"Missing values in test: {test_features.isnull().sum().sum()}")