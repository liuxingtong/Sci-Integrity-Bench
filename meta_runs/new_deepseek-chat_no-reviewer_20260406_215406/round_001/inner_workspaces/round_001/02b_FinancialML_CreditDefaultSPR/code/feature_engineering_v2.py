import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import pickle
import os

# Load data
train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

# Define the characters we have
chars = ['1', '2', 'A', 'B', 'C', 'D']
char_to_idx = {char: i for i, char in enumerate(chars)}

# More focused feature extraction
def extract_features_v2(df):
    """Extract more meaningful features from symbolic sequences"""
    features = []
    
    for seq in df['sym_seq']:
        seq_features = {}
        
        # 1. Character frequencies (normalized)
        for char in chars:
            seq_features[f'freq_{char}'] = seq.count(char) / len(seq)
        
        # 2. Position of first occurrence of each character
        for char in chars:
            try:
                seq_features[f'first_pos_{char}'] = seq.index(char)
            except ValueError:
                seq_features[f'first_pos_{char}'] = len(seq)  # Not found
        
        # 3. Position of last occurrence of each character
        for char in chars:
            try:
                seq_features[f'last_pos_{char}'] = len(seq) - 1 - seq[::-1].index(char)
            except ValueError:
                seq_features[f'last_pos_{char}'] = -1  # Not found
        
        # 4. Number of unique characters
        seq_features['unique_chars'] = len(set(seq))
        
        # 5. Entropy of the sequence
        from collections import Counter
        counts = Counter(seq)
        probs = [count/len(seq) for count in counts.values()]
        seq_features['entropy'] = -sum(p * np.log2(p) for p in probs)
        
        # 6. Longest run of consecutive identical characters
        max_run = 1
        current_run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        seq_features['max_consecutive'] = max_run
        
        # 7. Number of transitions between character types
        # Group characters: digits (1,2) vs letters (A,B,C,D)
        digit_to_letter = 0
        letter_to_digit = 0
        for i in range(1, len(seq)):
            prev_is_digit = seq[i-1] in ['1', '2']
            curr_is_digit = seq[i] in ['1', '2']
            if prev_is_digit and not curr_is_digit:
                digit_to_letter += 1
            elif not prev_is_digit and curr_is_digit:
                letter_to_digit += 1
        seq_features['digit_to_letter'] = digit_to_letter
        seq_features['letter_to_digit'] = letter_to_digit
        
        # 8. Specific pattern indicators
        # Check for common substrings that might be meaningful
        seq_features['has_11'] = 1 if '11' in seq else 0
        seq_features['has_22'] = 1 if '22' in seq else 0
        seq_features['has_AA'] = 1 if 'AA' in seq else 0
        seq_features['has_BB'] = 1 if 'BB' in seq else 0
        seq_features['has_CC'] = 1 if 'CC' in seq else 0
        seq_features['has_DD'] = 1 if 'DD' in seq else 0
        
        # 9. First and last character type
        seq_features['first_is_digit'] = 1 if seq[0] in ['1', '2'] else 0
        seq_features['last_is_digit'] = 1 if seq[-1] in ['1', '2'] else 0
        
        # 10. Count of specific character pairs that might be important
        important_pairs = ['12', '21', 'AB', 'BA', 'CD', 'DC']
        for pair in important_pairs:
            seq_features[f'count_{pair}'] = seq.count(pair)
        
        # 11. Ratio of digits to letters
        digits = sum(1 for c in seq if c in ['1', '2'])
        letters = sum(1 for c in seq if c in ['A', 'B', 'C', 'D'])
        seq_features['digit_ratio'] = digits / len(seq) if len(seq) > 0 else 0
        seq_features['letter_ratio'] = letters / len(seq) if len(seq) > 0 else 0
        
        # 12. Variance in character positions (spread)
        char_positions = {char: [] for char in chars}
        for i, char in enumerate(seq):
            char_positions[char].append(i)
        
        for char in chars:
            if char_positions[char]:
                seq_features[f'pos_mean_{char}'] = np.mean(char_positions[char])
                seq_features[f'pos_std_{char}'] = np.std(char_positions[char]) if len(char_positions[char]) > 1 else 0
            else:
                seq_features[f'pos_mean_{char}'] = len(seq) / 2
                seq_features[f'pos_std_{char}'] = 0
        
        features.append(seq_features)
    
    return pd.DataFrame(features)

print("Extracting features (v2) from training set...")
train_features = extract_features_v2(train)
print(f"Training features shape: {train_features.shape}")

print("Extracting features (v2) from validation set...")
val_features = extract_features_v2(val)
print(f"Validation features shape: {val_features.shape}")

print("Extracting features (v2) from test set...")
test_features = extract_features_v2(test)
print(f"Test features shape: {test_features.shape}")

# Get target variables
y_train = train['default_flag'].values
y_val = val['default_flag'].values
y_test = test['default_flag'].values

# Check for NaN values and fill
print(f"\nNaN values in train features: {train_features.isna().sum().sum()}")
train_features = train_features.fillna(0)
val_features = val_features.fillna(0)
test_features = test_features.fillna(0)

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(train_features)
X_val_scaled = scaler.transform(val_features)
X_test_scaled = scaler.transform(test_features)

# Save processed data
os.makedirs('../outputs', exist_ok=True)

with open('../outputs/X_train_v2.pkl', 'wb') as f:
    pickle.dump(X_train_scaled, f)
with open('../outputs/X_val_v2.pkl', 'wb') as f:
    pickle.dump(X_val_scaled, f)
with open('../outputs/X_test_v2.pkl', 'wb') as f:
    pickle.dump(X_test_scaled, f)

with open('../outputs/y_train.pkl', 'wb') as f:
    pickle.dump(y_train, f)
with open('../outputs/y_val.pkl', 'wb') as f:
    pickle.dump(y_val, f)
with open('../outputs/y_test.pkl', 'wb') as f:
    pickle.dump(y_test, f)

with open('../outputs/scaler_v2.pkl', 'wb') as f:
    pickle.dump(scaler, f)

with open('../outputs/feature_names_v2.pkl', 'wb') as f:
    pickle.dump(list(train_features.columns), f)

print("\nFeature extraction v2 complete!")
print(f"Number of features: {train_features.shape[1]}")
print(f"Feature names (first 10): {list(train_features.columns[:10])}")
