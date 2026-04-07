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

# Feature extraction based on pattern analysis insights
def extract_features_v3(df):
    """Extract features focusing on patterns found in analysis"""
    features = []
    
    for seq in df['sym_seq']:
        seq_features = {}
        
        # 1. Character frequencies
        for char in chars:
            seq_features[f'freq_{char}'] = seq.count(char) / len(seq)
        
        # 2. Position-specific features for key positions identified
        key_positions = [1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 14, 17, 18, 19]
        for pos in key_positions:
            for char in chars:
                seq_features[f'pos{pos}_{char}'] = 1 if seq[pos] == char else 0
        
        # 3. Important bigrams from analysis
        important_bigrams = ['21', '11', 'DC', 'BD', 'CD', '1C', '22', 'CA', 'C2', '2C', 'BC']
        for bigram in important_bigrams:
            seq_features[f'bigram_{bigram}'] = seq.count(bigram)
        
        # 4. Position of specific characters (from analysis)
        # Position where 'D' appears (tends to be later in non-defaults)
        d_positions = [i for i, char in enumerate(seq) if char == 'D']
        seq_features['d_mean_pos'] = np.mean(d_positions) if d_positions else len(seq)/2
        seq_features['d_first_pos'] = d_positions[0] if d_positions else len(seq)
        
        # Position where '2' appears (tends to be earlier in defaults)
        two_positions = [i for i, char in enumerate(seq) if char == '2']
        seq_features['two_mean_pos'] = np.mean(two_positions) if two_positions else len(seq)/2
        seq_features['two_first_pos'] = two_positions[0] if two_positions else len(seq)
        
        # 5. Pattern indicators from analysis
        seq_features['pos9_is_D'] = 1 if seq[9] == 'D' else 0
        seq_features['pos7_is_B'] = 1 if seq[7] == 'B' else 0
        seq_features['pos5_is_C'] = 1 if seq[5] == 'C' else 0
        seq_features['pos1_is_B'] = 1 if seq[1] == 'B' else 0
        seq_features['pos19_is_1'] = 1 if seq[19] == '1' else 0
        
        # 6. Transition patterns
        # Count transitions from digit to digit, letter to letter, etc.
        digit_to_digit = 0
        letter_to_letter = 0
        digit_to_letter = 0
        letter_to_digit = 0
        
        for i in range(1, len(seq)):
            prev = seq[i-1]
            curr = seq[i]
            prev_is_digit = prev in ['1', '2']
            curr_is_digit = curr in ['1', '2']
            
            if prev_is_digit and curr_is_digit:
                digit_to_digit += 1
            elif not prev_is_digit and not curr_is_digit:
                letter_to_letter += 1
            elif prev_is_digit and not curr_is_digit:
                digit_to_letter += 1
            else:
                letter_to_digit += 1
        
        seq_features['digit_to_digit'] = digit_to_digit
        seq_features['letter_to_letter'] = letter_to_letter
        seq_features['digit_to_letter'] = digit_to_letter
        seq_features['letter_to_digit'] = letter_to_digit
        
        # 7. Run length statistics
        runs = []
        current_char = seq[0]
        current_run = 1
        
        for i in range(1, len(seq)):
            if seq[i] == current_char:
                current_run += 1
            else:
                runs.append(current_run)
                current_char = seq[i]
                current_run = 1
        runs.append(current_run)
        
        seq_features['max_run'] = max(runs) if runs else 1
        seq_features['mean_run'] = np.mean(runs) if runs else 1
        seq_features['run_entropy'] = -sum((r/len(seq)) * np.log2(r/len(seq)) for r in runs)
        
        # 8. First and last character
        seq_features['first_char'] = chars.index(seq[0]) if seq[0] in chars else -1
        seq_features['last_char'] = chars.index(seq[-1]) if seq[-1] in chars else -1
        
        features.append(seq_features)
    
    return pd.DataFrame(features)

print("Extracting features (v3) from training set...")
train_features = extract_features_v3(train)
print(f"Training features shape: {train_features.shape}")

print("Extracting features (v3) from validation set...")
val_features = extract_features_v3(val)
print(f"Validation features shape: {val_features.shape}")

print("Extracting features (v3) from test set...")
test_features = extract_features_v3(test)
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

with open('../outputs/X_train_v3.pkl', 'wb') as f:
    pickle.dump(X_train_scaled, f)
with open('../outputs/X_val_v3.pkl', 'wb') as f:
    pickle.dump(X_val_scaled, f)
with open('../outputs/X_test_v3.pkl', 'wb') as f:
    pickle.dump(X_test_scaled, f)

with open('../outputs/feature_names_v3.pkl', 'wb') as f:
    pickle.dump(list(train_features.columns), f)

print("\nFeature extraction v3 complete!")
print(f"Number of features: {train_features.shape[1]}")
print(f"Feature names (first 10): {list(train_features.columns[:10])}")
