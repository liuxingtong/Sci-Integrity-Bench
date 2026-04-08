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
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
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

def extract_simple_features(symbol_series):
    """Extract simpler, more interpretable features"""
    features = []
    
    for s in symbol_series:
        feat = {}
        
        # Convert to numeric
        char_values = np.array([CHAR_TO_IDX[c] for c in s])
        
        # Character frequencies
        char_counts = Counter(s)
        for c in CHARS:
            feat[f'freq_{c}'] = char_counts.get(c, 0) / len(s)
        
        # Position encoding (first 10 chars)
        for i in range(10):
            feat[f'pos_{i}'] = CHAR_TO_IDX[s[i]]
        
        # Position encoding (last 10 chars)
        for i in range(30, 40):
            feat[f'pos_{i}'] = CHAR_TO_IDX[s[i]]
        
        # Basic statistics
        feat['mean'] = np.mean(char_values)
        feat['std'] = np.std(char_values)
        feat['min'] = np.min(char_values)
        feat['max'] = np.max(char_values)
        
        # Differences
        diffs = np.diff(char_values)
        feat['diff_abs_mean'] = np.mean(np.abs(diffs))
        feat['diff_std'] = np.std(diffs)
        
        # Autocorrelation
        corr = np.corrcoef(char_values[:-1], char_values[1:])[0, 1]
        feat['autocorr_1'] = corr if not np.isnan(corr) else 0
        
        # Run-length
        runs = []
        current_val = char_values[0]
        current_run = 1
        for i in range(1, len(char_values)):
            if char_values[i] == current_val:
                current_run += 1
            else:
                runs.append(current_run)
                current_val = char_values[i]
                current_run = 1
        runs.append(current_run)
        
        feat['num_runs'] = len(runs)
        feat['max_run'] = np.max(runs)
        
        # Entropy
        probs = [char_counts.get(c, 0) / len(s) for c in CHARS]
        probs = [p for p in probs if p > 0]
        feat['entropy'] = -sum(p * np.log2(p) for p in probs)
        
        features.append(feat)
    
    return pd.DataFrame(features)

# Extract features
print("\nExtracting features...")
X_train = extract_simple_features(train['symbol_series'])
X_val = extract_simple_features(val['symbol_series'])
X_test = extract_simple_features(test['symbol_series'])

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Number of features: {X_train.shape[1]}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Try feature selection
print("\nTrying feature selection...")
selector = SelectKBest(f_classif, k=30)
X_train_selected = selector.fit_transform(X_train_scaled, y_train)
X_val_selected = selector.transform(X_val_scaled)
X_test_selected = selector.transform(X_test_scaled)

selected_features = X_train.columns[selector.get_support()].tolist()
print(f"Selected features: {selected_features}")

# Combine train and val for final training
X_train_full = np.vstack([X_train_scaled, X_val_scaled])
y_train_full = np.concatenate([y_train, y_val])

X_train_full_selected = np.vstack([X_train_selected, X_val_selected])

# Define models with different hyperparameters
models = {
    'RF (selected)': RandomForestClassifier(n_estimators=500, max_depth=15, random_state=42, n_jobs=-1),
    'RF (full)': RandomForestClassifier(n_estimators=500, max_depth=15, random_state=42, n_jobs=-1),
    'GB (selected)': GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.1, random_state=42),
    'GB (full)': GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.1, random_state=42),
    'SVM (selected)': SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42),
    'SVM (full)': SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42),
}

# Train and evaluate on validation set
print("\n" + "="*60)
print("Model Comparison on Validation Set")
print("="*60)

val_results = {}
for name, model in models.items():
    if 'selected' in name:
        model.fit(X_train_selected, y_train)
        y_pred = model.predict(X_val_selected)
    else:
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
if 'selected' in best_model_name:
    best_model.fit(X_train_full_selected, y_train_full)
    y_test_pred = best_model.predict(X_test_selected)
else:
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
