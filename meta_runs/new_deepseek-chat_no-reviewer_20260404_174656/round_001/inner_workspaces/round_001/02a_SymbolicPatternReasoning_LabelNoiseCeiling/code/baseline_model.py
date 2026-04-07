import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

# Extract features and labels
feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train_raw = train[feature_cols]
y_train = train['label']
X_val_raw = val[feature_cols]
y_val = val['label']
X_test_raw = test[feature_cols]
y_test = test['label']

print("Data loaded successfully")
print(f"Train: {X_train_raw.shape}, Validation: {X_val_raw.shape}, Test: {X_test_raw.shape}")

# Simple feature engineering: one-hot encode each token position
# Since we have 16 possible tokens, we could one-hot encode each position
# But that would be 8 * 16 = 128 features
# Let's try a simpler approach first: count of each shape and color in the sequence

def extract_features(df):
    """Extract simple features from token sequences"""
    features = []
    
    for idx, row in df.iterrows():
        seq_features = []
        
        # Count shapes and colors
        shape_counts = {'T': 0, 'S': 0, 'C': 0, 'D': 0}
        color_counts = {'r': 0, 'g': 0, 'b': 0, 'y': 0}
        
        for col in feature_cols:
            token = row[col]
            shape = token[0]
            color = token[1]
            shape_counts[shape] += 1
            color_counts[color] += 1
        
        # Add shape counts
        seq_features.extend([shape_counts['T'], shape_counts['S'], shape_counts['C'], shape_counts['D']])
        # Add color counts
        seq_features.extend([color_counts['r'], color_counts['g'], color_counts['b'], color_counts['y']])
        
        # Add position-specific features (first and last token)
        first_token = row[feature_cols[0]]
        last_token = row[feature_cols[-1]]
        seq_features.append(1 if first_token[0] == 'T' else 0)  # First shape is T
        seq_features.append(1 if first_token[1] == 'r' else 0)  # First color is r
        seq_features.append(1 if last_token[0] == 'D' else 0)   # Last shape is D
        seq_features.append(1 if last_token[1] == 'y' else 0)   # Last color is y
        
        features.append(seq_features)
    
    return np.array(features)

print("\nExtracting features...")
X_train = extract_features(X_train_raw)
X_val = extract_features(X_val_raw)
X_test = extract_features(X_test_raw)

print(f"Feature shape: {X_train.shape}")
print(f"Number of features: {X_train.shape[1]}")

# Train a Random Forest classifier
print("\nTraining Random Forest classifier...")
rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)

# Evaluate
print("\nEvaluating model...")
y_train_pred = rf.predict(X_train)
y_val_pred = rf.predict(X_val)
y_test_pred = rf.predict(X_test)

train_acc = accuracy_score(y_train, y_train_pred)
val_acc = accuracy_score(y_val, y_val_pred)
test_acc = accuracy_score(y_test, y_test_pred)

print(f"Training accuracy: {train_acc:.4f}")
print(f"Validation accuracy: {val_acc:.4f}")
print(f"Test accuracy: {test_acc:.4f}")

# Compare with SOTA baseline (70%)
sota_baseline = 0.70
print(f"\nSOTA baseline: {sota_baseline:.4f}")
print(f"Our test accuracy vs SOTA: {test_acc:.4f} vs {sota_baseline:.4f}")
print(f"Difference: {test_acc - sota_baseline:.4f}")

if test_acc > sota_baseline:
    print("SUCCESS: Our model exceeds the SOTA baseline!")
else:
    print("Our model does not exceed the SOTA baseline yet.")