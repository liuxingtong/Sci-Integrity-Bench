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

# Define the character set - treating as ordinal values
# Let's try different orderings
CHARS = ['.', '*', 'u', 'v', 'w', 'x', 'y', 'z']
CHAR_TO_IDX = {c: i for i, c in enumerate(CHARS)}

def extract_ts_features(symbol_series):
    """Extract time-series specific features"""
    features = []
    
    for s in symbol_series:
        feat = {}
        
        # Convert to numeric series
        char_values = np.array([CHAR_TO_IDX[c] for c in s])
        
        # Basic statistics
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
        
        # IQR
        feat['iqr'] = feat['p75'] - feat['p25']
        
        # Skewness and kurtosis
        feat['skew'] = ((char_values - feat['mean']) ** 3).mean() / (feat['std'] ** 3 + 1e-10)
        feat['kurtosis'] = ((char_values - feat['mean']) ** 4).mean() / (feat['std'] ** 4 + 1e-10)
        
        # First differences (like derivative)
        diffs = np.diff(char_values)
        feat['diff_mean'] = np.mean(diffs)
        feat['diff_std'] = np.std(diffs)
        feat['diff_abs_mean'] = np.mean(np.abs(diffs))
        feat['diff_max'] = np.max(np.abs(diffs))
        
        # Second differences
        diffs2 = np.diff(diffs)
        feat['diff2_mean'] = np.mean(diffs2)
        feat['diff2_std'] = np.std(diffs2)
        feat['diff2_abs_mean'] = np.mean(np.abs(diffs2))
        
        # Autocorrelations
        for lag in [1, 2, 3, 5, 10]:
            if len(char_values) > lag:
                corr = np.corrcoef(char_values[:-lag], char_values[lag:])[0, 1]
                feat[f'autocorr_{lag}'] = corr if not np.isnan(corr) else 0
            else:
                feat[f'autocorr_{lag}'] = 0
        
        # Peak detection - number of local maxima/minima
        peaks = 0
        for i in range(1, len(char_values) - 1):
            if char_values[i] > char_values[i-1] and char_values[i] > char_values[i+1]:
                peaks += 1
            elif char_values[i] < char_values[i-1] and char_values[i] < char_values[i+1]:
                peaks += 1
        feat['num_peaks'] = peaks
        feat['peak_rate'] = peaks / len(char_values)
        
        # Zero-crossing rate (crossing the mean)
        mean_centered = char_values - feat['mean']
        zero_crossings = np.sum(np.abs(np.diff(np.sign(mean_centered))) > 0)
        feat['zero_crossings'] = zero_crossings
        feat['zero_crossing_rate'] = zero_crossings / len(char_values)
        
        # Run-length features
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
        
        # Character frequencies
        char_counts = Counter(s)
        for c in CHARS:
            feat[f'freq_{c}'] = char_counts.get(c, 0) / len(s)
        
        # Special character patterns
        feat['star_count'] = char_counts.get('*', 0)
        feat['dot_count'] = char_counts.get('.', 0)
        feat['special_ratio'] = (feat['star_count'] + feat['dot_count']) / len(s)
        
        # Entropy
        probs = [char_counts.get(c, 0) / len(s) for c in CHARS]
        probs = [p for p in probs if p > 0]
        feat['entropy'] = -sum(p * np.log2(p) for p in probs)
        
        # Trend (linear regression slope)
        x = np.arange(len(char_values))
        slope = np.polyfit(x, char_values, 1)[0]
        feat['trend_slope'] = slope
        
        # Energy
        feat['energy'] = np.sum(char_values ** 2)
        
        # Power spectral features (FFT)
        fft_vals = np.abs(np.fft.fft(char_values))
        fft_vals = fft_vals[:len(fft_vals)//2]  # Only positive frequencies
        feat['fft_max'] = np.max(fft_vals)
        feat['fft_mean'] = np.mean(fft_vals)
        feat['fft_std'] = np.std(fft_vals)
        
        # Dominant frequency
        if len(fft_vals) > 1:
            feat['dominant_freq'] = np.argmax(fft_vals[1:]) + 1  # Skip DC component
        else:
            feat['dominant_freq'] = 0
        
        features.append(feat)
    
    return pd.DataFrame(features)

# Extract features
print("\nExtracting features...")
X_train = extract_ts_features(train['symbol_series'])
X_val = extract_ts_features(val['symbol_series'])
X_test = extract_ts_features(test['symbol_series'])

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
