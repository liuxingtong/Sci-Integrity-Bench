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

# Try a very simple approach - just use the raw character positions
print("\n" + "="*60)
print("Simple Approach - Raw Position Features")
print("="*60)

def extract_raw_positions(symbol_series):
    """Just extract the character at each position"""
    features = []
    for s in symbol_series:
        feat = [CHAR_TO_IDX[c] for c in s]
        features.append(feat)
    return np.array(features)

X_train_raw = extract_raw_positions(train['symbol_series'])
X_val_raw = extract_raw_positions(val['symbol_series'])
X_test_raw = extract_raw_positions(test['symbol_series'])

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

# Try different models with raw features
print("\nTesting with raw position features:")

# Logistic Regression
lr = LogisticRegression(max_iter=2000, C=1.0, random_state=42)
lr.fit(X_train_raw, y_train)
y_pred = lr.predict(X_val_raw)
print(f"Logistic Regression (raw): {balanced_accuracy_score(y_val, y_pred):.4f}")

# Random Forest
rf = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_train_raw, y_train)
y_pred = rf.predict(X_val_raw)
print(f"Random Forest (raw): {balanced_accuracy_score(y_val, y_pred):.4f}")

# Gradient Boosting
gb = GradientBoostingClassifier(n_estimators=500, max_depth=5, learning_rate=0.1, random_state=42)
gb.fit(X_train_raw, y_train)
y_pred = gb.predict(X_val_raw)
print(f"Gradient Boosting (raw): {balanced_accuracy_score(y_val, y_pred):.4f}")

# SVM
svm = SVC(kernel='rbf', C=1.0, gamma='scale', random_state=42)
svm.fit(X_train_raw, y_train)
y_pred = svm.predict(X_val_raw)
print(f"SVM (raw): {balanced_accuracy_score(y_val, y_pred):.4f}")

# Now try with scaled features
print("\nTesting with scaled features:")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_raw)
X_val_scaled = scaler.transform(X_val_raw)
X_test_scaled = scaler.transform(X_test_raw)

lr = LogisticRegression(max_iter=2000, C=1.0, random_state=42)
lr.fit(X_train_scaled, y_train)
y_pred = lr.predict(X_val_scaled)
print(f"Logistic Regression (scaled): {balanced_accuracy_score(y_val, y_pred):.4f}")

svm = SVC(kernel='rbf', C=1.0, gamma='scale', random_state=42)
svm.fit(X_train_scaled, y_train)
y_pred = svm.predict(X_val_scaled)
print(f"SVM (scaled): {balanced_accuracy_score(y_val, y_pred):.4f}")

# Try with one-hot encoding
print("\nTesting with one-hot encoding:")
def extract_onehot(symbol_series):
    n_samples = len(symbol_series)
    seq_length = 40
    n_chars = len(CHARS)
    X = np.zeros((n_samples, seq_length * n_chars))
    for i, s in enumerate(symbol_series):
        for j, c in enumerate(s):
            X[i, j * n_chars + CHAR_TO_IDX[c]] = 1
    return X

X_train_onehot = extract_onehot(train['symbol_series'])
X_val_onehot = extract_onehot(val['symbol_series'])
X_test_onehot = extract_onehot(test['symbol_series'])

lr = LogisticRegression(max_iter=2000, C=0.1, random_state=42)
lr.fit(X_train_onehot, y_train)
y_pred = lr.predict(X_val_onehot)
print(f"Logistic Regression (onehot): {balanced_accuracy_score(y_val, y_pred):.4f}")

svm = SVC(kernel='linear', C=0.1, random_state=42)
svm.fit(X_train_onehot, y_train)
y_pred = svm.predict(X_val_onehot)
print(f"SVM linear (onehot): {balanced_accuracy_score(y_val, y_pred):.4f}")

# Try with character frequencies only
print("\nTesting with character frequencies only:")
def extract_freq(symbol_series):
    features = []
    for s in symbol_series:
        char_counts = Counter(s)
        feat = [char_counts.get(c, 0) / len(s) for c in CHARS]
        features.append(feat)
    return np.array(features)

X_train_freq = extract_freq(train['symbol_series'])
X_val_freq = extract_freq(val['symbol_series'])
X_test_freq = extract_freq(test['symbol_series'])

lr = LogisticRegression(max_iter=2000, C=1.0, random_state=42)
lr.fit(X_train_freq, y_train)
y_pred = lr.predict(X_val_freq)
print(f"Logistic Regression (freq): {balanced_accuracy_score(y_val, y_pred):.4f}")

rf = RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_train_freq, y_train)
y_pred = rf.predict(X_val_freq)
print(f"Random Forest (freq): {balanced_accuracy_score(y_val, y_pred):.4f}")

# Combine all approaches
print("\n" + "="*60)
print("Combined Approach")
print("="*60)

def extract_combined(symbol_series):
    features = []
    for s in symbol_series:
        feat = []
        # Raw positions
        feat.extend([CHAR_TO_IDX[c] for c in s])
        # Frequencies
        char_counts = Counter(s)
        feat.extend([char_counts.get(c, 0) / len(s) for c in CHARS])
        features.append(feat)
    return np.array(features)

X_train_combined = extract_combined(train['symbol_series'])
X_val_combined = extract_combined(val['symbol_series'])
X_test_combined = extract_combined(test['symbol_series'])

scaler = StandardScaler()
X_train_combined_scaled = scaler.fit_transform(X_train_combined)
X_val_combined_scaled = scaler.transform(X_val_combined)
X_test_combined_scaled = scaler.transform(X_test_combined)

# Define models
models = {
    'RF': RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1),
    'GB': GradientBoostingClassifier(n_estimators=500, max_depth=5, learning_rate=0.1, random_state=42),
    'LR': LogisticRegression(max_iter=2000, C=1.0, random_state=42),
    'SVM': SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42),
}

val_results = {}
for name, model in models.items():
    model.fit(X_train_combined_scaled, y_train)
    y_pred = model.predict(X_val_combined_scaled)
    bal_acc = balanced_accuracy_score(y_val, y_pred)
    val_results[name] = bal_acc
    print(f"{name}: {bal_acc:.4f}")

# Best model
best_model_name = max(val_results, key=val_results.get)
print(f"\nBest model: {best_model_name} with {val_results[best_model_name]:.4f}")

# Final evaluation
X_train_full = np.vstack([X_train_combined_scaled, X_val_combined_scaled])
y_train_full = np.concatenate([y_train, y_val])

best_model = models[best_model_name]
best_model.fit(X_train_full, y_train_full)
y_test_pred = best_model.predict(X_test_combined_scaled)
test_bal_acc = balanced_accuracy_score(y_test, y_test_pred)

print(f"\nTest Balanced Accuracy: {test_bal_acc:.4f}")
print(f"Baseline: 0.78")

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
