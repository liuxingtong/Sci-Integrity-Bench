import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score, StratifiedKFold
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load data
print("Loading data...")
train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

print(f"Train size: {len(train)}, Val size: {len(val)}, Test size: {len(test)}")

# Define the character set
CHARS = ['.', '*', 'u', 'v', 'w', 'x', 'y', 'z']
CHAR_TO_IDX = {c: i for i, c in enumerate(CHARS)}

def extract_raw_features(symbol_series):
    """Extract raw ordinal features - just the character at each position"""
    features = []
    
    for s in symbol_series:
        feat = [CHAR_TO_IDX[c] for c in s]
        features.append(feat)
    
    return np.array(features)

def extract_onehot_features(symbol_series):
    """One-hot encode each position"""
    n_samples = len(symbol_series)
    seq_length = 40
    n_chars = len(CHARS)
    
    X = np.zeros((n_samples, seq_length * n_chars))
    
    for i, s in enumerate(symbol_series):
        for j, c in enumerate(s):
            X[i, j * n_chars + CHAR_TO_IDX[c]] = 1
    
    return X

# Extract features
print("\nExtracting features...")
X_train_raw = extract_raw_features(train['symbol_series'])
X_val_raw = extract_raw_features(val['symbol_series'])
X_test_raw = extract_raw_features(test['symbol_series'])

X_train_onehot = extract_onehot_features(train['symbol_series'])
X_val_onehot = extract_onehot_features(val['symbol_series'])
X_test_onehot = extract_onehot_features(test['symbol_series'])

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Raw features shape: {X_train_raw.shape}")
print(f"One-hot features shape: {X_train_onehot.shape}")

# Scale raw features
scaler = StandardScaler()
X_train_raw_scaled = scaler.fit_transform(X_train_raw)
X_val_raw_scaled = scaler.transform(X_val_raw)
X_test_raw_scaled = scaler.transform(X_test_raw)

# Combine train and val for final training
X_train_full_raw = np.vstack([X_train_raw_scaled, X_val_raw_scaled])
X_train_full_onehot = np.vstack([X_train_onehot, X_val_onehot])
y_train_full = np.concatenate([y_train, y_val])

# Define models
models_raw = {
    'RF (raw)': RandomForestClassifier(n_estimators=300, max_depth=10, random_state=42, n_jobs=-1),
    'GB (raw)': GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42),
    'LR (raw)': LogisticRegression(max_iter=2000, C=1.0, random_state=42),
    'SVM (raw)': SVC(kernel='rbf', C=1.0, probability=True, random_state=42),
}

models_onehot = {
    'LR (onehot)': LogisticRegression(max_iter=2000, C=0.1, random_state=42),
    'SVM (onehot)': SVC(kernel='rbf', C=0.1, probability=True, random_state=42),
}

# Train and evaluate on validation set
print("\n" + "="*60)
print("Model Comparison on Validation Set")
print("="*60)

val_results = {}

for name, model in models_raw.items():
    model.fit(X_train_raw_scaled, y_train)
    y_pred = model.predict(X_val_raw_scaled)
    bal_acc = balanced_accuracy_score(y_val, y_pred)
    val_results[name] = bal_acc
    print(f"{name}: Balanced Accuracy = {bal_acc:.4f}")

for name, model in models_onehot.items():
    model.fit(X_train_onehot, y_train)
    y_pred = model.predict(X_val_onehot)
    bal_acc = balanced_accuracy_score(y_val, y_pred)
    val_results[name] = bal_acc
    print(f"{name}: Balanced Accuracy = {bal_acc:.4f}")

# Find best model
best_model_name = max(val_results, key=val_results.get)
print(f"\nBest model on validation: {best_model_name} with {val_results[best_model_name]:.4f}")

# Train best model on combined train+val and evaluate on test
print("\n" + "="*60)
print("Final Evaluation on Test Set")
print("="*60)

if 'raw' in best_model_name:
    best_model = models_raw[best_model_name]
    best_model.fit(X_train_full_raw, y_train_full)
    y_test_pred = best_model.predict(X_test_raw_scaled)
elif 'onehot' in best_model_name:
    best_model = models_onehot[best_model_name]
    best_model.fit(X_train_full_onehot, y_train_full)
    y_test_pred = best_model.predict(X_test_onehot)

test_bal_acc = balanced_accuracy_score(y_test, y_test_pred)

print(f"\nTest Balanced Accuracy: {test_bal_acc:.4f}")
print(f"Baseline: 0.78")
print(f"Improvement: {test_bal_acc - 0.78:.4f}")

print("\nClassification Report:")
print(classification_report(y_test, y_test_pred, target_names=['Non-variable', 'Variable']))

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test['object_id'],
    'true_label': y_test,
    'predicted_label': y_test_pred
})
predictions_df.to_csv('outputs/predictions.csv', index=False)

print("\nAnalysis complete!")
