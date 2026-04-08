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

# Focus on frequency-based features since they showed promise
def extract_freq_features(symbol_series):
    """Extract frequency-based features"""
    features = []
    for s in symbol_series:
        feat = []
        char_counts = Counter(s)
        
        # Overall frequencies
        for c in CHARS:
            feat.append(char_counts.get(c, 0) / len(s))
        
        # Quarter-based frequencies
        for q in range(4):
            start = q * 10
            end = (q + 1) * 10
            quarter = s[start:end]
            q_counts = Counter(quarter)
            for c in CHARS:
                feat.append(q_counts.get(c, 0) / 10)
        
        # Half-based frequencies
        first_half = s[:20]
        second_half = s[20:]
        for half in [first_half, second_half]:
            h_counts = Counter(half)
            for c in CHARS:
                feat.append(h_counts.get(c, 0) / 20)
        
        # Frequency differences between halves
        first_counts = Counter(first_half)
        second_counts = Counter(second_half)
        for c in CHARS:
            diff = (second_counts.get(c, 0) - first_counts.get(c, 0)) / 20
            feat.append(diff)
        
        features.append(feat)
    return np.array(features)

X_train_freq = extract_freq_features(train['symbol_series'])
X_val_freq = extract_freq_features(val['symbol_series'])
X_test_freq = extract_freq_features(test['symbol_series'])

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Frequency features shape: {X_train_freq.shape}")

# Try different models with frequency features
print("\n" + "="*60)
print("Model Comparison with Frequency Features")
print("="*60)

models = {
    'RF_d5': RandomForestClassifier(n_estimators=500, max_depth=5, random_state=42, n_jobs=-1),
    'RF_d10': RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1),
    'RF_d15': RandomForestClassifier(n_estimators=500, max_depth=15, random_state=42, n_jobs=-1),
    'RF_d20': RandomForestClassifier(n_estimators=500, max_depth=20, random_state=42, n_jobs=-1),
    'GB_d3': GradientBoostingClassifier(n_estimators=500, max_depth=3, learning_rate=0.1, random_state=42),
    'GB_d5': GradientBoostingClassifier(n_estimators=500, max_depth=5, learning_rate=0.1, random_state=42),
    'LR': LogisticRegression(max_iter=2000, C=1.0, random_state=42),
    'SVM': SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42),
}

val_results = {}
for name, model in models.items():
    model.fit(X_train_freq, y_train)
    y_pred = model.predict(X_val_freq)
    bal_acc = balanced_accuracy_score(y_val, y_pred)
    val_results[name] = bal_acc
    print(f"{name}: {bal_acc:.4f}")

# Best model
best_model_name = max(val_results, key=val_results.get)
print(f"\nBest model: {best_model_name} with {val_results[best_model_name]:.4f}")

# Final evaluation
X_train_full = np.vstack([X_train_freq, X_val_freq])
y_train_full = np.concatenate([y_train, y_val])

best_model = models[best_model_name]
best_model.fit(X_train_full, y_train_full)
y_test_pred = best_model.predict(X_test_freq)
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
