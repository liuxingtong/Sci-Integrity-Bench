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

# Deep analysis - look at specific patterns
print("\n" + "="*60)
print("Deep Pattern Analysis")
print("="*60)

# Check if there's a pattern in the first/last characters
print("\nFirst character distribution:")
for label in [0, 1]:
    subset = train[train['label'] == label]['symbol_series']
    first_chars = [s[0] for s in subset]
    counts = Counter(first_chars)
    total = len(first_chars)
    print(f"Label {label}: {dict((k, f'{v/total*100:.1f}%') for k, v in sorted(counts.items()))}")

print("\nLast character distribution:")
for label in [0, 1]:
    subset = train[train['label'] == label]['symbol_series']
    last_chars = [s[-1] for s in subset]
    counts = Counter(last_chars)
    total = len(last_chars)
    print(f"Label {label}: {dict((k, f'{v/total*100:.1f}%') for k, v in sorted(counts.items()))}")

# Check for specific substrings
print("\nSubstring analysis:")
substrings = ['**', '..', 'uu', 'vv', 'ww', 'xx', 'yy', 'zz', '.*', '*.', 'u*', '*u', 'v*', '*v']
for sub in substrings:
    for label in [0, 1]:
        subset = train[train['label'] == label]['symbol_series']
        count = sum(1 for s in subset if sub in s)
        print(f"'{sub}' in label {label}: {count}/{len(subset)} ({count/len(subset)*100:.1f}%)")
    print()

def extract_pattern_features(symbol_series):
    """Extract pattern-based features"""
    features = []
    
    for s in symbol_series:
        feat = {}
        
        # Convert to numeric
        char_values = np.array([CHAR_TO_IDX[c] for c in s])
        
        # First and last characters
        feat['first_char'] = CHAR_TO_IDX[s[0]]
        feat['last_char'] = CHAR_TO_IDX[s[-1]]
        
        # Character frequencies
        char_counts = Counter(s)
        for c in CHARS:
            feat[f'freq_{c}'] = char_counts.get(c, 0) / len(s)
        
        # Substring presence
        substrings = ['**', '..', 'uu', 'vv', 'ww', 'xx', 'yy', 'zz', 
                      '.*', '*.', 'u*', '*u', 'v*', '*v', 'w*', '*w',
                      'x*', '*x', 'y*', '*y', 'z*', '*z',
                      '.u', 'u.', '.v', 'v.', '.w', 'w.', '.x', 'x.', '.y', 'y.', '.z', 'z.']
        for sub in substrings:
            feat[f'has_{sub}'] = 1 if sub in s else 0
            feat[f'count_{sub}'] = s.count(sub)
        
        # Position features
        for i in range(40):
            feat[f'pos_{i}'] = CHAR_TO_IDX[s[i]]
        
        # Statistical features
        feat['mean'] = np.mean(char_values)
        feat['std'] = np.std(char_values)
        feat['min'] = np.min(char_values)
        feat['max'] = np.max(char_values)
        feat['range'] = feat['max'] - feat['min']
        
        # Differences
        diffs = np.diff(char_values)
        feat['diff_mean'] = np.mean(diffs)
        feat['diff_std'] = np.std(diffs)
        feat['diff_abs_mean'] = np.mean(np.abs(diffs))
        
        # Autocorrelation
        for lag in [1, 2, 3, 5, 10]:
            if len(char_values) > lag:
                corr = np.corrcoef(char_values[:-lag], char_values[lag:])[0, 1]
                feat[f'autocorr_{lag}'] = corr if not np.isnan(corr) else 0
        
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
        feat['mean_run'] = np.mean(runs)
        feat['max_run'] = np.max(runs)
        
        # Entropy
        probs = [char_counts.get(c, 0) / len(s) for c in CHARS]
        probs = [p for p in probs if p > 0]
        feat['entropy'] = -sum(p * np.log2(p) for p in probs)
        
        # FFT
        fft_vals = np.abs(np.fft.fft(char_values))
        fft_vals = fft_vals[:len(fft_vals)//2]
        feat['fft_max'] = np.max(fft_vals)
        feat['fft_mean'] = np.mean(fft_vals)
        if len(fft_vals) > 1:
            feat['dominant_freq'] = np.argmax(fft_vals[1:]) + 1
        else:
            feat['dominant_freq'] = 0
        
        features.append(feat)
    
    return pd.DataFrame(features)

# Extract features
print("\nExtracting features...")
X_train = extract_pattern_features(train['symbol_series'])
X_val = extract_pattern_features(val['symbol_series'])
X_test = extract_pattern_features(test['symbol_series'])

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
    'Random Forest': RandomForestClassifier(n_estimators=500, max_depth=15, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=500, max_depth=6, learning_rate=0.05, random_state=42),
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
