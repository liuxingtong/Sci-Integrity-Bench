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
from sklearn.model_selection import GridSearchCV, cross_val_score
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

def extract_comprehensive_features(symbol_series):
    """Extract comprehensive features for variable star classification"""
    features = []
    
    for s in symbol_series:
        feat = {}
        
        # Convert to numeric
        char_values = np.array([CHAR_TO_IDX[c] for c in s])
        
        # 1. Character frequencies
        char_counts = Counter(s)
        for c in CHARS:
            feat[f'freq_{c}'] = char_counts.get(c, 0) / len(s)
        
        # 2. Position-specific frequencies (quarters)
        for q in range(4):
            start = q * 10
            end = (q + 1) * 10
            quarter = s[start:end]
            q_counts = Counter(quarter)
            for c in CHARS:
                feat[f'q{q}_freq_{c}'] = q_counts.get(c, 0) / 10
        
        # 3. Half-based frequencies and differences
        first_half = s[:20]
        second_half = s[20:]
        first_counts = Counter(first_half)
        second_counts = Counter(second_half)
        
        for c in CHARS:
            feat[f'first_freq_{c}'] = first_counts.get(c, 0) / 20
            feat[f'second_freq_{c}'] = second_counts.get(c, 0) / 20
            feat[f'freq_diff_{c}'] = (second_counts.get(c, 0) - first_counts.get(c, 0)) / 20
        
        # 4. Statistical features
        feat['mean'] = np.mean(char_values)
        feat['std'] = np.std(char_values)
        feat['var'] = np.var(char_values)
        feat['min'] = np.min(char_values)
        feat['max'] = np.max(char_values)
        feat['range'] = feat['max'] - feat['min']
        feat['median'] = np.median(char_values)
        
        # 5. Percentiles
        for p in [10, 25, 75, 90]:
            feat[f'p{p}'] = np.percentile(char_values, p)
        feat['iqr'] = feat['p75'] - feat['p25']
        
        # 6. Differences (derivatives)
        diffs = np.diff(char_values)
        feat['diff_mean'] = np.mean(diffs)
        feat['diff_std'] = np.std(diffs)
        feat['diff_abs_mean'] = np.mean(np.abs(diffs))
        feat['diff_abs_std'] = np.std(np.abs(diffs))
        feat['diff_max'] = np.max(np.abs(diffs))
        
        # 7. Autocorrelations
        for lag in [1, 2, 3, 5, 10]:
            if len(char_values) > lag:
                corr = np.corrcoef(char_values[:-lag], char_values[lag:])[0, 1]
                feat[f'autocorr_{lag}'] = corr if not np.isnan(corr) else 0
        
        # 8. Run-length features
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
        
        # 9. Consecutive pairs
        for c in CHARS:
            count = 0
            for i in range(len(s)-1):
                if s[i] == c and s[i+1] == c:
                    count += 1
            feat[f'consec_{c}'] = count / (len(s)-1)
        
        # 10. Entropy
        probs = [char_counts.get(c, 0) / len(s) for c in CHARS]
        probs = [p for p in probs if p > 0]
        feat['entropy'] = -sum(p * np.log2(p) for p in probs)
        
        # 11. FFT features
        fft_vals = np.abs(np.fft.fft(char_values))
        fft_vals = fft_vals[:len(fft_vals)//2]
        feat['fft_max'] = np.max(fft_vals)
        feat['fft_mean'] = np.mean(fft_vals)
        feat['fft_std'] = np.std(fft_vals)
        if len(fft_vals) > 1:
            feat['dominant_freq'] = np.argmax(fft_vals[1:]) + 1
        else:
            feat['dominant_freq'] = 0
        
        # 12. Peak features
        peaks = 0
        valleys = 0
        for i in range(1, len(char_values) - 1):
            if char_values[i] > char_values[i-1] and char_values[i] > char_values[i+1]:
                peaks += 1
            elif char_values[i] < char_values[i-1] and char_values[i] < char_values[i+1]:
                valleys += 1
        feat['num_peaks'] = peaks
        feat['num_valleys'] = valleys
        
        # 13. Trend
        x = np.arange(len(char_values))
        slope = np.polyfit(x, char_values, 1)[0]
        feat['trend_slope'] = slope
        
        features.append(feat)
    
    return pd.DataFrame(features)

# Extract features
print("\nExtracting features...")
X_train = extract_comprehensive_features(train['symbol_series'])
X_val = extract_comprehensive_features(val['symbol_series'])
X_test = extract_comprehensive_features(test['symbol_series'])

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

# Define models with hyperparameter tuning
print("\n" + "="*60)
print("Model Comparison on Validation Set")
print("="*60)

models = {
    'RF_d5': RandomForestClassifier(n_estimators=500, max_depth=5, random_state=42, n_jobs=-1),
    'RF_d10': RandomForestClassifier(n_estimators=500, max_depth=10, random_state=42, n_jobs=-1),
    'RF_d15': RandomForestClassifier(n_estimators=500, max_depth=15, random_state=42, n_jobs=-1),
    'GB_d3': GradientBoostingClassifier(n_estimators=500, max_depth=3, learning_rate=0.05, random_state=42),
    'GB_d5': GradientBoostingClassifier(n_estimators=500, max_depth=5, learning_rate=0.05, random_state=42),
    'GB_d7': GradientBoostingClassifier(n_estimators=500, max_depth=7, learning_rate=0.05, random_state=42),
    'SVM_C1': SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42),
    'SVM_C10': SVC(kernel='rbf', C=10.0, gamma='scale', probability=True, random_state=42),
}

val_results = {}
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_val_scaled)
    bal_acc = balanced_accuracy_score(y_val, y_pred)
    val_results[name] = bal_acc
    print(f"{name}: {bal_acc:.4f}")

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

# Confusion matrix
cm = confusion_matrix(y_test, y_test_pred)
print("\nConfusion Matrix:")
print(cm)

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test['object_id'],
    'true_label': y_test,
    'predicted_label': y_test_pred
})
predictions_df.to_csv('outputs/predictions.csv', index=False)

# Save feature importance if applicable
if 'RF' in best_model_name or 'GB' in best_model_name:
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    feature_importance.to_csv('outputs/feature_importance.csv', index=False)
    print("\nTop 15 Most Important Features:")
    print(feature_importance.head(15).to_string(index=False))

print("\nAnalysis complete!")
