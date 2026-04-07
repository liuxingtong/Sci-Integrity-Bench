import pandas as pd
import numpy as np
from collections import Counter
import itertools
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set up paths
data_dir = '../data'
train_path = os.path.join(data_dir, 'train.csv')
val_path = os.path.join(data_dir, 'val.csv')
test_path = os.path.join(data_dir, 'test.csv')
output_dir = '../outputs'
report_img_dir = '../report/images'

# Create directories if they don't exist
os.makedirs(output_dir, exist_ok=True)
os.makedirs(report_img_dir, exist_ok=True)

# Load data
train_df = pd.read_csv(train_path)
val_df = pd.read_csv(val_path)
test_df = pd.read_csv(test_path)

# Define symbols
symbols = ['*', 'v', 'w', 'z', 'y', 'u', '.', 'x']

# Feature extraction functions
def extract_frequency_features(series):
    """Extract frequency features for each symbol"""
    features = {}
    total_len = len(series)
    
    # Individual symbol frequencies
    for sym in symbols:
        features[f'freq_{sym}'] = series.count(sym) / total_len
    
    # Basic statistics
    features['unique_symbols'] = len(set(series))
    
    # Most common symbol frequency
    counter = Counter(series)
    most_common = counter.most_common(1)[0]
    features['most_common_freq'] = most_common[1] / total_len
    features['most_common_symbol'] = symbols.index(most_common[0])  # encode as index
    
    return features

def extract_transition_features(series):
    """Extract transition probabilities between symbols"""
    features = {}
    
    # Count transitions
    transition_counts = {}
    for i in range(len(series) - 1):
        pair = (series[i], series[i+1])
        transition_counts[pair] = transition_counts.get(pair, 0) + 1
    
    # Create features for common transitions
    for sym1 in symbols:
        for sym2 in symbols:
            pair = (sym1, sym2)
            count = transition_counts.get(pair, 0)
            features[f'trans_{sym1}_{sym2}'] = count / (len(series) - 1)
    
    return features

def extract_ngram_features(series, n=2):
    """Extract n-gram frequencies"""
    features = {}
    
    # Generate all possible n-grams
    ngrams = [''.join(ngram) for ngram in itertools.product(symbols, repeat=n)]
    
    # Count n-grams in series
    ngram_counts = {}
    for i in range(len(series) - n + 1):
        ngram = series[i:i+n]
        ngram_counts[ngram] = ngram_counts.get(ngram, 0) + 1
    
    # Create features
    total_ngrams = len(series) - n + 1
    for ngram in ngrams:
        count = ngram_counts.get(ngram, 0)
        features[f'ngram_{n}_{ngram}'] = count / total_ngrams
    
    return features

def extract_complexity_features(series):
    """Extract complexity measures"""
    features = {}
    
    # Shannon entropy
    from math import log2
    counter = Counter(series)
    entropy = 0
    total = len(series)
    for count in counter.values():
        p = count / total
        if p > 0:
            entropy -= p * log2(p)
    features['entropy'] = entropy
    features['max_entropy'] = log2(len(set(series))) if len(set(series)) > 0 else 0
    features['norm_entropy'] = entropy / log2(len(symbols)) if log2(len(symbols)) > 0 else 0
    
    # Simple pattern: count of repeated symbols
    repeats = 0
    for i in range(1, len(series)):
        if series[i] == series[i-1]:
            repeats += 1
    features['repeat_fraction'] = repeats / (len(series) - 1)
    
    return features

def extract_all_features(df):
    """Extract all features for a dataframe"""
    all_features = []
    
    for idx, row in df.iterrows():
        series = row['symbol_series']
        features = {}
        
        # Add different feature types
        features.update(extract_frequency_features(series))
        features.update(extract_transition_features(series))
        features.update(extract_ngram_features(series, n=2))  # Bigrams
        features.update(extract_complexity_features(series))
        
        # Add original fields
        features['object_id'] = row['object_id']
        features['field_id'] = row['field_id']
        features['label'] = row['label']
        
        all_features.append(features)
    
    return pd.DataFrame(all_features)

print("Extracting features from training set...")
train_features = extract_all_features(train_df)
print(f"Training features shape: {train_features.shape}")

print("Extracting features from validation set...")
val_features = extract_all_features(val_df)
print(f"Validation features shape: {val_features.shape}")

print("Extracting features from test set...")
test_features = extract_all_features(test_df)
print(f"Test features shape: {test_features.shape}")

# Save features
print("\nSaving features...")
train_features.to_csv(os.path.join(output_dir, 'train_features.csv'), index=False)
val_features.to_csv(os.path.join(output_dir, 'val_features.csv'), index=False)
test_features.to_csv(os.path.join(output_dir, 'test_features.csv'), index=False)

print("\nFeature extraction complete!")
