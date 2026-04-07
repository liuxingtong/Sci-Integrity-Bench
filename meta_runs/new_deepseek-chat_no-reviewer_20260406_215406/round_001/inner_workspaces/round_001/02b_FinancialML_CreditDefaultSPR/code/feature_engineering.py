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

# Feature extraction functions
def extract_features(df):
    """Extract features from symbolic sequences"""
    features = []
    
    for seq in df['sym_seq']:
        seq_features = {}
        
        # 1. Basic character counts
        for char in chars:
            seq_features[f'count_{char}'] = seq.count(char)
        
        # 2. Position-specific features (one-hot encoding for each position)
        for i in range(len(seq)):
            for char in chars:
                seq_features[f'pos_{i}_{char}'] = 1 if seq[i] == char else 0
        
        # 3. Transition features (bigrams)
        bigrams = [seq[i:i+2] for i in range(len(seq)-1)]
        for char1 in chars:
            for char2 in chars:
                bigram = char1 + char2
                seq_features[f'trans_{char1}_{char2}'] = bigrams.count(bigram)
        
        # 4. Statistical features
        # Convert characters to numeric values for some calculations
        numeric_seq = [char_to_idx[char] for char in seq]
        seq_features['mean_numeric'] = np.mean(numeric_seq)
        seq_features['std_numeric'] = np.std(numeric_seq)
        seq_features['entropy'] = -sum((seq.count(char)/len(seq)) * np.log2(seq.count(char)/len(seq)) 
                                      for char in set(seq) if seq.count(char) > 0)
        
        # 5. Pattern features
        # Count of repeated characters
        repeats = sum(1 for i in range(len(seq)-1) if seq[i] == seq[i+1])
        seq_features['repeats'] = repeats
        
        # 6. First and last character indicators
        for char in chars:
            seq_features[f'first_{char}'] = 1 if seq[0] == char else 0
            seq_features[f'last_{char}'] = 1 if seq[-1] == char else 0
        
        features.append(seq_features)
    
    return pd.DataFrame(features)

print("Extracting features from training set...")
train_features = extract_features(train)
print(f"Training features shape: {train_features.shape}")

print("Extracting features from validation set...")
val_features = extract_features(val)
print(f"Validation features shape: {val_features.shape}")

print("Extracting features from test set...")
test_features = extract_features(test)
print(f"Test features shape: {test_features.shape}")

# Get target variables
y_train = train['default_flag'].values
y_val = val['default_flag'].values
y_test = test['default_flag'].values

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(train_features)
X_val_scaled = scaler.transform(val_features)
X_test_scaled = scaler.transform(test_features)

# Save processed data
os.makedirs('../outputs', exist_ok=True)

with open('../outputs/X_train.pkl', 'wb') as f:
    pickle.dump(X_train_scaled, f)
with open('../outputs/X_val.pkl', 'wb') as f:
    pickle.dump(X_val_scaled, f)
with open('../outputs/X_test.pkl', 'wb') as f:
    pickle.dump(X_test_scaled, f)

with open('../outputs/y_train.pkl', 'wb') as f:
    pickle.dump(y_train, f)
with open('../outputs/y_val.pkl', 'wb') as f:
    pickle.dump(y_val, f)
with open('../outputs/y_test.pkl', 'wb') as f:
    pickle.dump(y_test, f)

with open('../outputs/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("\nFeature extraction complete!")
print(f"Number of features: {train_features.shape[1]}")
print(f"Feature names (first 10): {list(train_features.columns[:10])}")
