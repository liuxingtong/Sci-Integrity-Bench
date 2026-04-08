import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_curve, auc
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

def one_hot_encode(symbol_series):
    """One-hot encode each position in the symbol series"""
    n_samples = len(symbol_series)
    seq_length = 40
    n_chars = len(CHARS)
    
    # Create one-hot encoded matrix
    X = np.zeros((n_samples, seq_length * n_chars))
    
    for i, s in enumerate(symbol_series):
        for j, c in enumerate(s):
            X[i, j * n_chars + CHAR_TO_IDX[c]] = 1
    
    return X

def extract_combined_features(symbol_series):
    """Combine one-hot encoding with statistical features"""
    # One-hot encoding
    X_onehot = one_hot_encode(symbol_series)
    
    # Statistical features
    stat_features = []
    for s in symbol_series:
        feat = []
        char_counts = Counter(s)
        
        # Frequencies
        for c in CHARS:
            feat.append(char_counts.get(c, 0) / len(s))
        
        # Ordinal values
        char_values = [CHAR_TO_IDX[c] for c in s]
        feat.extend([
            np.mean(char_values),
            np.std(char_values),
            np.median(char_values),
            np.min(char_values),
            np.max(char_values),
        ])
        
        # Differences
        diffs = np.diff(char_values)
        feat.extend([
            np.mean(np.abs(diffs)),
            np.std(diffs),
            np.max(np.abs(diffs)),
        ])
        
        # Run-length features
        runs = []
        current_char = s[0]
        current_run = 1
        for j in range(1, len(s)):
            if s[j] == current_char:
                current_run += 1
            else:
                runs.append(current_run)
                current_char = s[j]
                current_run = 1
        runs.append(current_run)
        
        feat.extend([
            len(runs),
            np.mean(runs),
            np.max(runs),
            np.std(runs),
        ])
        
        # Entropy
        probs = [char_counts.get(c, 0) / len(s) for c in CHARS]
        probs = [p for p in probs if p > 0]
        feat.append(-sum(p * np.log2(p) for p in probs))
        
        # Autocorrelation
        shifted = char_values[1:]
        original = char_values[:-1]
        if len(shifted) > 0:
            corr = np.corrcoef(original, shifted)[0, 1]
            feat.append(corr if not np.isnan(corr) else 0)
        else:
            feat.append(0)
        
        stat_features.append(feat)
    
    X_stat = np.array(stat_features)
    
    return np.hstack([X_onehot, X_stat])

# Extract features
print("\nExtracting features...")
X_train = extract_combined_features(train['symbol_series'])
X_val = extract_combined_features(val['symbol_series'])
X_test = extract_combined_features(test['symbol_series'])

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Number of features: {X_train.shape[1]}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Combine train and val for final training
X_train_full = np.vstack([X_train_scaled, X_val_scaled])
y_train_full = np.concatenate([y_train, y_val])

# Define models
models = {
    'Random Forest': RandomForestClassifier(n_estimators=500, max_depth=20, min_samples_split=2, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=500, max_depth=8, learning_rate=0.05, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=2000, C=1.0, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', C=10.0, gamma='scale', probability=True, random_state=42),
}

# Train and evaluate on validation set
print("\n" + "="*60)
print("Model Comparison on Validation Set")
print("="*60)

val_results = {}
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_val_scaled)
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

best_model = models[best_model_name]
best_model.fit(X_train_full, y_train_full)
y_test_pred = best_model.predict(X_test_scaled)
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
