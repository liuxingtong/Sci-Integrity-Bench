import pandas as pd
import numpy as np
from collections import Counter
import itertools
from scipy import stats
import os

# Set up paths
data_dir = '../data'
output_dir = '../outputs'

# Load data
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))
val_df = pd.read_csv(os.path.join(data_dir, 'val.csv'))
test_df = pd.read_csv(os.path.join(data_dir, 'test.csv'))

# Define symbols
symbols = ['*', 'v', 'w', 'z', 'y', 'u', '.', 'x']
symbol_to_num = {sym: i for i, sym in enumerate(symbols)}

# New feature extraction functions
def extract_sequential_features(series):
    """Extract features that capture sequential patterns"""
    features = {}
    
    # Convert to numeric sequence
    num_seq = [symbol_to_num[ch] for ch in series]
    
    # Statistical features on numeric sequence
    features['seq_mean'] = np.mean(num_seq)
    features['seq_std'] = np.std(num_seq)
    features['seq_skew'] = stats.skew(num_seq)
    features['seq_kurtosis'] = stats.kurtosis(num_seq)
    
    # Autocorrelation features
    autocorr_lags = [1, 2, 3, 5, 10]
    for lag in autocorr_lags:
        if lag < len(num_seq):
            corr = np.corrcoef(num_seq[:-lag], num_seq[lag:])[0, 1]
            features[f'autocorr_{lag}'] = corr if not np.isnan(corr) else 0
    
    # Run length encoding features
    runs = []
    current_run = 1
    for i in range(1, len(series)):
        if series[i] == series[i-1]:
            current_run += 1
        else:
            runs.append(current_run)
            current_run = 1
    runs.append(current_run)
    
    if runs:
        features['max_run_length'] = max(runs)
        features['mean_run_length'] = np.mean(runs)
        features['run_std'] = np.std(runs)
    else:
        features['max_run_length'] = 0
        features['mean_run_length'] = 0
        features['run_std'] = 0
    
    # Pattern complexity: number of unique substrings of length 3
    substrings_3 = set()
    for i in range(len(series) - 2):
        substrings_3.add(series[i:i+3])
    features['unique_substrings_3'] = len(substrings_3)
    
    # Symbol change rate
    changes = 0
    for i in range(1, len(series)):
        if series[i] != series[i-1]:
            changes += 1
    features['change_rate'] = changes / (len(series) - 1)
    
    return features

def extract_positional_features(series):
    """Extract features based on symbol positions"""
    features = {}
    
    # First and last symbols
    features['first_symbol'] = symbol_to_num[series[0]]
    features['last_symbol'] = symbol_to_num[series[-1]]
    
    # Symbol distribution in first/last halves
    half = len(series) // 2
    first_half = series[:half]
    second_half = series[half:]
    
    for sym in symbols:
        features[f'first_half_freq_{sym}'] = first_half.count(sym) / half
        features[f'second_half_freq_{sym}'] = second_half.count(sym) / half
        
        # Difference between halves
        features[f'half_diff_{sym}'] = features[f'first_half_freq_{sym}'] - features[f'second_half_freq_{sym}']
    
    # Quarter-based features
    quarter = len(series) // 4
    for i in range(4):
        quarter_seq = series[i*quarter:(i+1)*quarter]
        for sym in symbols:
            features[f'q{i+1}_freq_{sym}'] = quarter_seq.count(sym) / quarter
    
    return features

def extract_pattern_features(series):
    """Extract specific pattern features"""
    features = {}
    
    # Count specific patterns that might be meaningful
    patterns = {
        'peak_pattern': '*v*',  # Possible peak pattern
        'valley_pattern': 'v*v',  # Possible valley pattern
        'constant_pattern': '***',  # Constant brightness
        'oscillating_pattern': 'v*w*v'  # Oscillation
    }
    
    for pattern_name, pattern in patterns.items():
        count = 0
        for i in range(len(series) - len(pattern) + 1):
            if series[i:i+len(pattern)] == pattern:
                count += 1
        features[f'pattern_{pattern_name}'] = count / (len(series) - len(pattern) + 1)
    
    # Count transitions between specific symbol groups
    # Group symbols: bright (*), medium (v,w,x), dim (y,z,u,.)
    bright = {'*'}
    medium = {'v', 'w', 'x'}
    dim = {'y', 'z', 'u', '.'}
    
    def get_group(sym):
        if sym in bright:
            return 'bright'
        elif sym in medium:
            return 'medium'
        else:
            return 'dim'
    
    group_transitions = []
    for i in range(len(series) - 1):
        group1 = get_group(series[i])
        group2 = get_group(series[i+1])
        group_transitions.append(f"{group1}_{group2}")
    
    transition_counts = Counter(group_transitions)
    total_transitions = len(group_transitions)
    
    for transition in ['bright_bright', 'bright_medium', 'bright_dim', 
                       'medium_bright', 'medium_medium', 'medium_dim',
                       'dim_bright', 'dim_medium', 'dim_dim']:
        count = transition_counts.get(transition, 0)
        features[f'group_trans_{transition}'] = count / total_transitions
    
    return features

def extract_all_improved_features(df):
    """Extract all improved features"""
    all_features = []
    
    for idx, row in df.iterrows():
        series = row['symbol_series']
        features = {}
        
        # Add different feature types
        features.update(extract_sequential_features(series))
        features.update(extract_positional_features(series))
        features.update(extract_pattern_features(series))
        
        # Add basic frequency features (simplified)
        total_len = len(series)
        for sym in symbols:
            features[f'freq_{sym}'] = series.count(sym) / total_len
        
        # Add field_id as categorical feature
        features['field_id'] = int(row['field_id'][3:])  # Convert fldX to X
        
        # Add label
        features['label'] = row['label']
        features['object_id'] = row['object_id']
        
        all_features.append(features)
    
    return pd.DataFrame(all_features)

print("Extracting improved features from training set...")
train_features_improved = extract_all_improved_features(train_df)
print(f"Training features shape: {train_features_improved.shape}")

print("Extracting improved features from validation set...")
val_features_improved = extract_all_improved_features(val_df)
print(f"Validation features shape: {val_features_improved.shape}")

print("Extracting improved features from test set...")
test_features_improved = extract_all_improved_features(test_df)
print(f"Test features shape: {test_features_improved.shape}")

# Save features
print("\nSaving improved features...")
train_features_improved.to_csv(os.path.join(output_dir, 'train_features_improved.csv'), index=False)
val_features_improved.to_csv(os.path.join(output_dir, 'val_features_improved.csv'), index=False)
test_features_improved.to_csv(os.path.join(output_dir, 'test_features_improved.csv'), index=False)

print("\nImproved feature extraction complete!")
print("\nFeature columns:")
print(list(train_features_improved.columns[:20]))
print(f"... and {len(train_features_improved.columns) - 20} more")
