import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_curve, auc
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')

# Load data
print("Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

print(f"Train samples: {len(train_df)}")
print(f"Val samples: {len(val_df)}")
print(f"Test samples: {len(test_df)}")

# Get all unique symbols
all_symbols = set()
for df in [train_df, val_df, test_df]:
    for series in df['symbol_series']:
        all_symbols.update(series)
all_symbols = sorted(all_symbols)
print(f"Unique symbols: {all_symbols}")

# Map symbols to numerical values (treating them as ordinal)
symbol_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def extract_comprehensive_features(series):
    """Extract comprehensive features from a symbol series."""
    features = {}
    
    # Convert to numerical
    numerical = [symbol_map.get(c, 0) for c in series]
    numerical = np.array(numerical)
    
    # 1. Basic statistics on numerical representation
    features['mean'] = np.mean(numerical)
    features['std'] = np.std(numerical)
    features['min'] = np.min(numerical)
    features['max'] = np.max(numerical)
    features['range'] = features['max'] - features['min']
    features['median'] = np.median(numerical)
    
    # 2. Character frequencies
    char_counts = Counter(series)
    total_chars = len(series)
    for char in all_symbols:
        features[f'freq_{char}'] = char_counts.get(char, 0) / total_chars
    
    # 3. Special character features
    features['star_count'] = series.count('*')
    features['dot_count'] = series.count('.')
    features['star_ratio'] = features['star_count'] / total_chars
    features['dot_ratio'] = features['dot_count'] / total_chars
    features['special_ratio'] = (features['star_count'] + features['dot_count']) / total_chars
    
    # 4. Transition features
    transitions = 0
    for i in range(len(series) - 1):
        if series[i] != series[i+1]:
            transitions += 1
    features['transition_count'] = transitions
    features['transition_rate'] = transitions / (len(series) - 1)
    
    # 5. Numerical transitions (changes in value)
    numerical_diff = np.diff(numerical)
    features['mean_diff'] = np.mean(np.abs(numerical_diff))
    features['std_diff'] = np.std(numerical_diff)
    features['positive_transitions'] = np.sum(numerical_diff > 0)
    features['negative_transitions'] = np.sum(numerical_diff < 0)
    features['zero_transitions'] = np.sum(numerical_diff == 0)
    
    # 6. Consecutive patterns
    max_consecutive = 1
    current_consecutive = 1
    for i in range(len(series) - 1):
        if series[i] == series[i+1]:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 1
    features['max_consecutive'] = max_consecutive
    
    # 7. Entropy
    probs = [count/total_chars for count in char_counts.values()]
    entropy = -sum(p * np.log2(p) for p in probs if p > 0)
    features['entropy'] = entropy
    
    # 8. Unique characters
    features['unique_chars'] = len(set(series))
    
    # 9. Position-based features (split into quarters)
    quarter = len(series) // 4
    for i, (start, end) in enumerate([(0, quarter), (quarter, 2*quarter), (2*quarter, 3*quarter), (3*quarter, len(series))]):
        segment = series[start:end]
        features[f'q{i+1}_star'] = segment.count('*') / len(segment)
        features[f'q{i+1}_dot'] = segment.count('.') / len(segment)
        features[f'q{i+1}_mean'] = np.mean([symbol_map.get(c, 0) for c in segment])
    
    # 10. Trend features
    x = np.arange(len(numerical))
    slope = np.polyfit(x, numerical, 1)[0]
    features['trend_slope'] = slope
    
    # 11. Variability measures
    features['coefficient_of_variation'] = features['std'] / features['mean'] if features['mean'] > 0 else 0
    
    # 12. Run-length encoding features
    runs = []
    current_char = series[0]
    current_length = 1
    for c in series[1:]:
        if c == current_char:
            current_length += 1
        else:
            runs.append((current_char, current_length))
            current_char = c
            current_length = 1
    runs.append((current_char, current_length))
    
    features['num_runs'] = len(runs)
    run_lengths = [r[1] for r in runs]
    features['mean_run_length'] = np.mean(run_lengths)
    features['std_run_length'] = np.std(run_lengths)
    features['max_run_length'] = max(run_lengths)
    
    # 13. Peak detection (local maxima in numerical series)
    peaks = 0
    for i in range(1, len(numerical) - 1):
        if numerical[i] > numerical[i-1] and numerical[i] > numerical[i+1]:
            peaks += 1
    features['peak_count'] = peaks
    
    # 14. Valley detection (local minima)
    valleys = 0
    for i in range(1, len(numerical) - 1):
        if numerical[i] < numerical[i-1] and numerical[i] < numerical[i+1]:
            valleys += 1
    features['valley_count'] = valleys
    
    # 15. Autocorrelation at lag 1
    if len(numerical) > 1:
        autocorr = np.corrcoef(numerical[:-1], numerical[1:])[0, 1]
        features['autocorr_lag1'] = autocorr if not np.isnan(autocorr) else 0
    else:
        features['autocorr_lag1'] = 0
    
    # 16. Bigram features (most common)
    bigrams = [series[i:i+2] for i in range(len(series)-1)]
    bigram_counts = Counter(bigrams)
    top_bigrams = ['**', '..', '*z', 'z*', 'zw', 'wz', 'xy', 'yx', 'uv', 'vu']
    for bg in top_bigrams:
        features[f'bigram_{bg}'] = bigram_counts.get(bg, 0) / len(bigrams) if bigrams else 0
    
    return features

def extract_features_df(df):
    """Extract features for a dataframe."""
    feature_list = []
    for series in df['symbol_series']:
        features = extract_comprehensive_features(series)
        feature_list.append(features)
    return pd.DataFrame(feature_list)

# Extract features
print("\n=== Extracting Comprehensive Features ===")
X_train = extract_features_df(train_df)
X_val = extract_features_df(val_df)
X_test = extract_features_df(test_df)

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values

print(f"Feature matrix shape: {X_train.shape}")

# Handle missing values
X_train = X_train.fillna(0)
X_val = X_val.fillna(0)
X_test = X_test.fillna(0)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

print(f"Scaled feature matrix shape: {X_train_scaled.shape}")

# Model training
print("\n=== Model Training ===")

results = {}

# 1. Random Forest with tuned parameters
print("\nTraining Random Forest...")
rf = RandomForestClassifier(n_estimators=500, max_depth=20, min_samples_split=5, 
                            min_samples_leaf=2, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
rf_val_pred = rf.predict(X_val)
rf_val_acc = balanced_accuracy_score(y_val, rf_val_pred)
rf_test_pred = rf.predict(X_test)
rf_test_acc = balanced_accuracy_score(y_test, rf_test_pred)
results['Random Forest'] = {'val': rf_val_acc, 'test': rf_test_acc, 'model': rf, 'predictions': rf_test_pred}
print(f"Random Forest - Val: {rf_val_acc:.4f}, Test: {rf_test_acc:.4f}")

# 2. Gradient Boosting
print("\nTraining Gradient Boosting...")
gb = GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.1, random_state=42)
gb.fit(X_train, y_train)
gb_val_pred = gb.predict(X_val)
gb_val_acc = balanced_accuracy_score(y_val, gb_val_pred)
gb_test_pred = gb.predict(X_test)
gb_test_acc = balanced_accuracy_score(y_test, gb_test_pred)
results['Gradient Boosting'] = {'val': gb_val_acc, 'test': gb_test_acc, 'model': gb, 'predictions': gb_test_pred}
print(f"Gradient Boosting - Val: {gb_val_acc:.4f}, Test: {gb_test_acc:.4f}")

# 3. Logistic Regression
print("\nTraining Logistic Regression...")
lr = LogisticRegression(max_iter=2000, C=1.0, random_state=42)
lr.fit(X_train_scaled, y_train)
lr_val_pred = lr.predict(X_val_scaled)
lr_val_acc = balanced_accuracy_score(y_val, lr_val_pred)
lr_test_pred = lr.predict(X_test_scaled)
lr_test_acc = balanced_accuracy_score(y_test, lr_test_pred)
results['Logistic Regression'] = {'val': lr_val_acc, 'test': lr_test_acc, 'model': lr, 'predictions': lr_test_pred}
print(f"Logistic Regression - Val: {lr_val_acc:.4f}, Test: {lr_test_acc:.4f}")

# 4. SVM with RBF kernel
print("\nTraining SVM...")
svm = SVC(kernel='rbf', C=10, gamma='scale', random_state=42)
svm.fit(X_train_scaled, y_train)
svm_val_pred = svm.predict(X_val_scaled)
svm_val_acc = balanced_accuracy_score(y_val, svm_val_pred)
svm_test_pred = svm.predict(X_test_scaled)
svm_test_acc = balanced_accuracy_score(y_test, svm_test_pred)
results['SVM'] = {'val': svm_val_acc, 'test': svm_test_acc, 'model': svm, 'predictions': svm_test_pred}
print(f"SVM - Val: {svm_val_acc:.4f}, Test: {svm_test_acc:.4f}")

# Select best model
best_model_name = max(results, key=lambda x: results[x]['val'])
best_result = results[best_model_name]
print(f"\n=== Best Model: {best_model_name} ===")
print(f"Validation Balanced Accuracy: {best_result['val']:.4f}")
print(f"Test Balanced Accuracy: {best_result['test']:.4f}")

# Save results
results_df = pd.DataFrame({
    'Model': list(results.keys()),
    'Val_Balanced_Accuracy': [results[m]['val'] for m in results],
    'Test_Balanced_Accuracy': [results[m]['test'] for m in results]
})
results_df.to_csv('../outputs/model_results.csv', index=False)

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test_df['object_id'],
    'true_label': y_test,
    'predicted_label': best_result['predictions']
})
predictions_df.to_csv('../outputs/predictions.csv', index=False)

# Feature importance (for tree-based models)
if best_model_name in ['Random Forest', 'Gradient Boosting']:
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': best_result['model'].feature_importances_
    }).sort_values('importance', ascending=False)
    feature_importance.to_csv('../outputs/feature_importance.csv', index=False)
    print("\nTop 20 Most Important Features:")
    print(feature_importance.head(20))

print("\n=== Analysis Complete ===")
