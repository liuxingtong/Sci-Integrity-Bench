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
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

print(f"Train samples: {len(train_df)}")
print(f"Val samples: {len(val_df)}")
print(f"Test samples: {len(test_df)}")

# Data overview
print("\n=== Data Overview ===")
print(f"\nTrain label distribution:")
print(train_df['label'].value_counts())
print(f"\nValidation label distribution:")
print(val_df['label'].value_counts())
print(f"\nTest label distribution:")
print(test_df['label'].value_counts())

# Analyze symbol_series
print("\n=== Symbol Series Analysis ===")
all_symbols = set()
for series in train_df['symbol_series']:
    all_symbols.update(series)
print(f"Unique symbols: {sorted(all_symbols)}")
print(f"Number of unique symbols: {len(all_symbols)}")

# Check series lengths
lengths = train_df['symbol_series'].apply(len)
print(f"Series length - min: {lengths.min()}, max: {lengths.max()}, mean: {lengths.mean():.2f}")

# Feature extraction functions
def extract_features(series):
    """Extract features from a symbol series."""
    features = {}
    
    # 1. Character frequencies
    char_counts = Counter(series)
    total_chars = len(series)
    for char in sorted(all_symbols):
        features[f'freq_{char}'] = char_counts.get(char, 0) / total_chars
    
    # 2. Special character counts
    features['star_count'] = series.count('*')
    features['dot_count'] = series.count('.')
    
    # 3. Transition features
    transitions = 0
    for i in range(len(series) - 1):
        if series[i] != series[i+1]:
            transitions += 1
    features['transition_rate'] = transitions / (len(series) - 1) if len(series) > 1 else 0
    
    # 4. Consecutive patterns
    max_consecutive = 1
    current_consecutive = 1
    for i in range(len(series) - 1):
        if series[i] == series[i+1]:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 1
    features['max_consecutive'] = max_consecutive
    
    # 5. Entropy
    probs = [count/total_chars for count in char_counts.values()]
    entropy = -sum(p * np.log2(p) for p in probs if p > 0)
    features['entropy'] = entropy
    
    # 6. N-gram features (bigrams)
    bigrams = [series[i:i+2] for i in range(len(series)-1)]
    bigram_counts = Counter(bigrams)
    # Most common bigrams
    for bg, count in bigram_counts.most_common(10):
        features[f'bigram_{bg}'] = count / len(bigrams) if bigrams else 0
    
    # 7. Position-based features
    if len(series) >= 10:
        features['first_10_star'] = series[:10].count('*')
        features['last_10_star'] = series[-10:].count('*')
        features['first_10_dot'] = series[:10].count('.')
        features['last_10_dot'] = series[-10:].count('.')
    else:
        features['first_10_star'] = series.count('*')
        features['last_10_star'] = series.count('*')
        features['first_10_dot'] = series.count('.')
        features['last_10_dot'] = series.count('.')
    
    # 8. Variability indicator (range of characters)
    features['unique_chars'] = len(set(series))
    
    # 9. Alphabet vs special character ratio
    alphabet_chars = sum(1 for c in series if c.isalpha())
    features['alphabet_ratio'] = alphabet_chars / total_chars
    
    return features

# Extract features for all datasets
print("\n=== Extracting Features ===")

# First, get all unique symbols from all datasets
all_symbols = set()
for df in [train_df, val_df, test_df]:
    for series in df['symbol_series']:
        all_symbols.update(series)
all_symbols = sorted(all_symbols)
print(f"All unique symbols across datasets: {all_symbols}")

def extract_features_df(df):
    """Extract features for a dataframe."""
    feature_list = []
    for series in df['symbol_series']:
        features = extract_features(series)
        feature_list.append(features)
    return pd.DataFrame(feature_list)

X_train = extract_features_df(train_df)
X_val = extract_features_df(val_df)
X_test = extract_features_df(test_df)

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values

print(f"Feature matrix shape: {X_train.shape}")
print(f"Features: {list(X_train.columns[:20])}...")

# Handle any missing columns (ensure all datasets have same features)
all_features = set(X_train.columns) | set(X_val.columns) | set(X_test.columns)
for feat in all_features:
    for X in [X_train, X_val, X_test]:
        if feat not in X.columns:
            X[feat] = 0

# Sort columns to ensure consistency
X_train = X_train.reindex(sorted(X_train.columns), axis=1)
X_val = X_val.reindex(sorted(X_val.columns), axis=1)
X_test = X_test.reindex(sorted(X_test.columns), axis=1)

# Fill any NaN values with 0
X_train = X_train.fillna(0)
X_val = X_val.fillna(0)
X_test = X_test.fillna(0)

print(f"Checking for NaN values - Train: {X_train.isna().sum().sum()}, Val: {X_val.isna().sum().sum()}, Test: {X_test.isna().sum().sum()}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

print(f"\nScaled feature matrix shape: {X_train_scaled.shape}")

# Model training and evaluation
print("\n=== Model Training ===")

results = {}

# 1. Random Forest
print("\nTraining Random Forest...")
rf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
rf_val_pred = rf.predict(X_val)
rf_val_acc = balanced_accuracy_score(y_val, rf_val_pred)
rf_test_pred = rf.predict(X_test)
rf_test_acc = balanced_accuracy_score(y_test, rf_test_pred)
results['Random Forest'] = {'val': rf_val_acc, 'test': rf_test_acc, 'model': rf}
print(f"Random Forest - Val Balanced Accuracy: {rf_val_acc:.4f}, Test Balanced Accuracy: {rf_test_acc:.4f}")

# 2. Gradient Boosting
print("\nTraining Gradient Boosting...")
gb = GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42)
gb.fit(X_train, y_train)
gb_val_pred = gb.predict(X_val)
gb_val_acc = balanced_accuracy_score(y_val, gb_val_pred)
gb_test_pred = gb.predict(X_test)
gb_test_acc = balanced_accuracy_score(y_test, gb_test_pred)
results['Gradient Boosting'] = {'val': gb_val_acc, 'test': gb_test_acc, 'model': gb}
print(f"Gradient Boosting - Val Balanced Accuracy: {gb_val_acc:.4f}, Test Balanced Accuracy: {gb_test_acc:.4f}")

# 3. Logistic Regression
print("\nTraining Logistic Regression...")
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train_scaled, y_train)
lr_val_pred = lr.predict(X_val_scaled)
lr_val_acc = balanced_accuracy_score(y_val, lr_val_pred)
lr_test_pred = lr.predict(X_test_scaled)
lr_test_acc = balanced_accuracy_score(y_test, lr_test_pred)
results['Logistic Regression'] = {'val': lr_val_acc, 'test': lr_test_acc, 'model': lr}
print(f"Logistic Regression - Val Balanced Accuracy: {lr_val_acc:.4f}, Test Balanced Accuracy: {lr_test_acc:.4f}")

# 4. SVM
print("\nTraining SVM...")
svm = SVC(kernel='rbf', random_state=42)
svm.fit(X_train_scaled, y_train)
svm_val_pred = svm.predict(X_val_scaled)
svm_val_acc = balanced_accuracy_score(y_val, svm_val_pred)
svm_test_pred = svm.predict(X_test_scaled)
svm_test_acc = balanced_accuracy_score(y_test, svm_test_pred)
results['SVM'] = {'val': svm_val_acc, 'test': svm_test_acc, 'model': svm}
print(f"SVM - Val Balanced Accuracy: {svm_val_acc:.4f}, Test Balanced Accuracy: {svm_test_acc:.4f}")

# Select best model
best_model_name = max(results, key=lambda x: results[x]['val'])
best_result = results[best_model_name]
print(f"\n=== Best Model: {best_model_name} ===")
print(f"Validation Balanced Accuracy: {best_result['val']:.4f}")
print(f"Test Balanced Accuracy: {best_result['test']:.4f}")

# Detailed evaluation on test set
print("\n=== Detailed Test Set Evaluation ===")
if best_model_name in ['Logistic Regression', 'SVM']:
    test_pred = best_result['model'].predict(X_test_scaled)
else:
    test_pred = best_result['model'].predict(X_test)

print("\nClassification Report:")
print(classification_report(y_test, test_pred, target_names=['Non-Variable', 'Variable']))

# Save results
results_df = pd.DataFrame({
    'Model': list(results.keys()),
    'Val_Balanced_Accuracy': [results[m]['val'] for m in results],
    'Test_Balanced_Accuracy': [results[m]['test'] for m in results]
})
results_df.to_csv('../outputs/model_results.csv', index=False)
print("\nResults saved to outputs/model_results.csv")

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test_df['object_id'],
    'true_label': y_test,
    'predicted_label': test_pred
})
predictions_df.to_csv('../outputs/predictions.csv', index=False)
print("Predictions saved to outputs/predictions.csv")

print("\n=== Analysis Complete ===")
