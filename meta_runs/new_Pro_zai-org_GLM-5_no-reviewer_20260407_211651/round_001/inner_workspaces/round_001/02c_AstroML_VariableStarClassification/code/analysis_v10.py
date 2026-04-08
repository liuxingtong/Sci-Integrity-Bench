import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier, VotingClassifier
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

# Define the character set - try different orderings
# Maybe the characters represent magnitude levels
# Let's try: . = gap, * = peak, and u-z = magnitude levels
CHARS = ['.', '*', 'u', 'v', 'w', 'x', 'y', 'z']
CHAR_TO_IDX = {c: i for i, c in enumerate(CHARS)}

# Alternative ordering - treating u-z as ordinal magnitude levels
# u = dimmest, z = brightest
CHARS_ORDINAL = ['.', '*', 'u', 'v', 'w', 'x', 'y', 'z']
CHAR_TO_ORDINAL = {c: i-2 for i, c in enumerate(CHARS_ORDINAL)}  # -2 to center around 0

def extract_variability_features(symbol_series):
    """Extract features specifically designed for variability detection"""
    features = []
    
    for s in symbol_series:
        feat = {}
        
        # Convert to numeric (ordinal encoding)
        char_values = np.array([CHAR_TO_IDX[c] for c in s])
        
        # Character frequencies
        char_counts = Counter(s)
        for c in CHARS:
            feat[f'freq_{c}'] = char_counts.get(c, 0) / len(s)
        
        # Variability-specific features
        # 1. Amplitude (range of values)
        feat['amplitude'] = np.max(char_values) - np.min(char_values)
        
        # 2. Standard deviation (variability measure)
        feat['std'] = np.std(char_values)
        
        # 3. Mean absolute deviation
        feat['mad'] = np.mean(np.abs(char_values - np.mean(char_values)))
        
        # 4. Coefficient of variation
        feat['cv'] = feat['std'] / (np.mean(char_values) + 1e-10)
        
        # 5. Peak-to-peak variation
        feat['peak_to_peak'] = np.max(char_values) - np.min(char_values)
        
        # 6. Number of direction changes (variability indicator)
        direction_changes = 0
        for i in range(2, len(char_values)):
            if (char_values[i] > char_values[i-1] and char_values[i-1] < char_values[i-2]) or \
               (char_values[i] < char_values[i-1] and char_values[i-1] > char_values[i-2]):
                direction_changes += 1
        feat['direction_changes'] = direction_changes / (len(char_values) - 2)
        
        # 7. Autocorrelation at different lags (periodicity indicator)
        for lag in [1, 2, 3, 4, 5, 10, 15, 20]:
            if len(char_values) > lag:
                corr = np.corrcoef(char_values[:-lag], char_values[lag:])[0, 1]
                feat[f'autocorr_{lag}'] = corr if not np.isnan(corr) else 0
        
        # 8. Run-length statistics (smoothness)
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
        
        # 9. Consecutive same-character pairs
        for c in CHARS:
            count = 0
            for i in range(len(s)-1):
                if s[i] == c and s[i+1] == c:
                    count += 1
            feat[f'consec_{c}'] = count / (len(s)-1)
        
        # 10. Special character patterns
        star_positions = [i for i in range(len(s)) if s[i] == '*']
        dot_positions = [i for i in range(len(s)) if s[i] == '.']
        
        feat['star_count'] = len(star_positions)
        feat['dot_count'] = len(dot_positions)
        
        if len(star_positions) > 1:
            feat['star_spacing_mean'] = np.mean(np.diff(star_positions))
            feat['star_spacing_std'] = np.std(np.diff(star_positions))
        else:
            feat['star_spacing_mean'] = 0
            feat['star_spacing_std'] = 0
        
        if len(dot_positions) > 1:
            feat['dot_spacing_mean'] = np.mean(np.diff(dot_positions))
            feat['dot_spacing_std'] = np.std(np.diff(dot_positions))
        else:
            feat['dot_spacing_mean'] = 0
            feat['dot_spacing_std'] = 0
        
        # 11. FFT features (periodicity)
        fft_vals = np.abs(np.fft.fft(char_values - np.mean(char_values)))
        fft_vals = fft_vals[:len(fft_vals)//2]
        
        feat['fft_max'] = np.max(fft_vals)
        feat['fft_mean'] = np.mean(fft_vals)
        feat['fft_std'] = np.std(fft_vals)
        
        if len(fft_vals) > 1:
            # Dominant frequency (excluding DC)
            feat['dominant_freq'] = np.argmax(fft_vals[1:]) + 1
            # Power at dominant frequency
            feat['dominant_power'] = fft_vals[feat['dominant_freq']]
        else:
            feat['dominant_freq'] = 0
            feat['dominant_power'] = 0
        
        # 12. Entropy
        probs = [char_counts.get(c, 0) / len(s) for c in CHARS]
        probs = [p for p in probs if p > 0]
        feat['entropy'] = -sum(p * np.log2(p) for p in probs)
        
        # 13. Trend
        x = np.arange(len(char_values))
        slope = np.polyfit(x, char_values, 1)[0]
        feat['trend_slope'] = slope
        
        # 14. Differences
        diffs = np.diff(char_values)
        feat['diff_mean'] = np.mean(diffs)
        feat['diff_std'] = np.std(diffs)
        feat['diff_abs_mean'] = np.mean(np.abs(diffs))
        
        # 15. Position-weighted features
        positions = np.arange(len(s)) / (len(s) - 1)
        for c in CHARS:
            c_positions = [positions[i] for i in range(len(s)) if s[i] == c]
            if c_positions:
                feat[f'mean_pos_{c}'] = np.mean(c_positions)
                feat[f'std_pos_{c}'] = np.std(c_positions)
            else:
                feat[f'mean_pos_{c}'] = 0.5
                feat[f'std_pos_{c}'] = 0
        
        features.append(feat)
    
    return pd.DataFrame(features)

# Extract features
print("\nExtracting features...")
X_train = extract_variability_features(train['symbol_series'])
X_val = extract_variability_features(val['symbol_series'])
X_test = extract_variability_features(test['symbol_series'])

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
