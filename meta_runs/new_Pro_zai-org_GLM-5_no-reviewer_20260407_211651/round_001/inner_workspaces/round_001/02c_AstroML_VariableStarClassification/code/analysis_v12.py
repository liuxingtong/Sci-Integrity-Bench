import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
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

# Try to understand the data better
print("\n" + "="*60)
print("Data Analysis")
print("="*60)

# Check if there's any correlation between field_id and label
print("\nLabel distribution by field_id:")
for field in sorted(train['field_id'].unique()):
    subset = train[train['field_id'] == field]
    print(f"{field}: {subset['label'].value_counts().to_dict()}")

# Check if the data is shuffled or ordered
print("\nFirst 10 rows of train:")
print(train.head(10)[['object_id', 'field_id', 'label']])

# Check for any obvious patterns
print("\nChecking for patterns in symbol_series...")
for label in [0, 1]:
    subset = train[train['label'] == label]['symbol_series']
    lengths = [len(s) for s in subset]
    print(f"Label {label}: mean length = {np.mean(lengths):.2f}, std = {np.std(lengths):.2f}")

def extract_all_features(symbol_series):
    """Extract all possible features"""
    features = []
    
    for s in symbol_series:
        feat = {}
        
        # Convert to numeric
        char_values = np.array([CHAR_TO_IDX[c] for c in s])
        
        # Raw position features
        for i in range(40):
            feat[f'pos_{i}'] = CHAR_TO_IDX[s[i]]
        
        # Character frequencies
        char_counts = Counter(s)
        for c in CHARS:
            feat[f'freq_{c}'] = char_counts.get(c, 0) / len(s)
        
        # Statistical features
        feat['mean'] = np.mean(char_values)
        feat['std'] = np.std(char_values)
        feat['var'] = np.var(char_values)
        feat['min'] = np.min(char_values)
        feat['max'] = np.max(char_values)
        feat['range'] = feat['max'] - feat['min']
        feat['median'] = np.median(char_values)
        
        # Percentiles
        for p in [10, 25, 75, 90]:
            feat[f'p{p}'] = np.percentile(char_values, p)
        
        feat['iqr'] = feat['p75'] - feat['p25']
        
        # Skewness and kurtosis
        feat['skew'] = ((char_values - feat['mean']) ** 3).mean() / (feat['std'] ** 3 + 1e-10)
        feat['kurtosis'] = ((char_values - feat['mean']) ** 4).mean() / (feat['std'] ** 4 + 1e-10)
        
        # Differences
        diffs = np.diff(char_values)
        feat['diff_mean'] = np.mean(diffs)
        feat['diff_std'] = np.std(diffs)
        feat['diff_abs_mean'] = np.mean(np.abs(diffs))
        feat['diff_abs_std'] = np.std(np.abs(diffs))
        feat['diff_max'] = np.max(np.abs(diffs))
        
        # Second differences
        diffs2 = np.diff(diffs)
        feat['diff2_mean'] = np.mean(diffs2)
        feat['diff2_std'] = np.std(diffs2)
        feat['diff2_abs_mean'] = np.mean(np.abs(diffs2))
        
        # Autocorrelations
        for lag in [1, 2, 3, 4, 5, 10, 15, 20]:
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
        feat['std_run'] = np.std(runs)
        
        # Entropy
        probs = [char_counts.get(c, 0) / len(s) for c in CHARS]
        probs = [p for p in probs if p > 0]
        feat['entropy'] = -sum(p * np.log2(p) for p in probs)
        
        # FFT
        fft_vals = np.abs(np.fft.fft(char_values))
        fft_vals = fft_vals[:len(fft_vals)//2]
        feat['fft_max'] = np.max(fft_vals)
        feat['fft_mean'] = np.mean(fft_vals)
        feat['fft_std'] = np.std(fft_vals)
        if len(fft_vals) > 1:
            feat['dominant_freq'] = np.argmax(fft_vals[1:]) + 1
        else:
            feat['dominant_freq'] = 0
        
        # Peak features
        peaks = 0
        valleys = 0
        for i in range(1, len(char_values) - 1):
            if char_values[i] > char_values[i-1] and char_values[i] > char_values[i+1]:
                peaks += 1
            elif char_values[i] < char_values[i-1] and char_values[i] < char_values[i+1]:
                valleys += 1
        feat['num_peaks'] = peaks
        feat['num_valleys'] = valleys
        
        # Trend
        x = np.arange(len(char_values))
        slope = np.polyfit(x, char_values, 1)[0]
        feat['trend_slope'] = slope
        
        # Energy
        feat['energy'] = np.sum(char_values ** 2)
        
        # Consecutive pairs
        for c in CHARS:
            count = 0
            for i in range(len(s)-1):
                if s[i] == c and s[i+1] == c:
                    count += 1
            feat[f'consec_{c}'] = count / (len(s)-1)
        
        features.append(feat)
    
    return pd.DataFrame(features)

# Extract features
print("\nExtracting features...")
X_train = extract_all_features(train['symbol_series'])
X_val = extract_all_features(val['symbol_series'])
X_test = extract_all_features(test['symbol_series'])

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

# Define models with extensive hyperparameter search
models = {
    'RF_d10': RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1),
    'RF_d15': RandomForestClassifier(n_estimators=500, max_depth=15, random_state=42, n_jobs=-1),
    'RF_d20': RandomForestClassifier(n_estimators=500, max_depth=20, random_state=42, n_jobs=-1),
    'GB_d5': GradientBoostingClassifier(n_estimators=500, max_depth=5, learning_rate=0.05, random_state=42),
    'GB_d6': GradientBoostingClassifier(n_estimators=500, max_depth=6, learning_rate=0.05, random_state=42),
    'GB_d8': GradientBoostingClassifier(n_estimators=500, max_depth=8, learning_rate=0.05, random_state=42),
    'SVM_C1': SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42),
    'SVM_C10': SVC(kernel='rbf', C=10.0, gamma='scale', probability=True, random_state=42),
    'SVM_C100': SVC(kernel='rbf', C=100.0, gamma='scale', probability=True, random_state=42),
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
