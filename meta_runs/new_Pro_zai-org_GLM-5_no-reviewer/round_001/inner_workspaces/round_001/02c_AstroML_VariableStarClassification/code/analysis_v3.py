import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_curve, auc
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
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

# Analyze the data more carefully
print("\n=== Data Analysis ===")

# Check for patterns in variable vs non-variable
var_series = train_df[train_df['label'] == 1]['symbol_series']
nonvar_series = train_df[train_df['label'] == 0]['symbol_series']

print("\nVariable stars - sample series:")
for s in var_series.head(5):
    print(f"  {s}")

print("\nNon-variable stars - sample series:")
for s in nonvar_series.head(5):
    print(f"  {s}")

# Symbol frequency analysis
print("\n=== Symbol Frequency Analysis ===")
all_symbols = set()
for series in train_df['symbol_series']:
    all_symbols.update(series)
all_symbols = sorted(all_symbols)
print(f"Unique symbols: {all_symbols}")

# Calculate average symbol frequencies for each class
var_freq = {s: 0 for s in all_symbols}
nonvar_freq = {s: 0 for s in all_symbols}

for series in var_series:
    for s in series:
        var_freq[s] += 1
for series in nonvar_series:
    for s in series:
        nonvar_freq[s] += 1

# Normalize
var_total = sum(var_freq.values())
nonvar_total = sum(nonvar_freq.values())

print("\nSymbol frequencies by class:")
print(f"{'Symbol':<10} {'Variable':<15} {'Non-Variable':<15} {'Diff':<15}")
for s in all_symbols:
    v_freq = var_freq[s] / var_total
    nv_freq = nonvar_freq[s] / nonvar_total
    print(f"{s:<10} {v_freq:<15.4f} {nv_freq:<15.4f} {v_freq - nv_freq:<15.4f}")

# Feature extraction using multiple approaches
def extract_all_features(series):
    """Extract comprehensive features from a symbol series."""
    features = {}
    
    # Symbol to numerical mapping (treating as ordinal based on alphabet)
    symbol_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
    numerical = np.array([symbol_map.get(c, 0) for c in series])
    
    # 1. Basic character frequencies
    char_counts = Counter(series)
    total = len(series)
    for char in all_symbols:
        features[f'freq_{char}'] = char_counts.get(char, 0) / total
    
    # 2. Statistical features on numerical representation
    features['mean'] = np.mean(numerical)
    features['std'] = np.std(numerical)
    features['var'] = np.var(numerical)
    features['median'] = np.median(numerical)
    features['min'] = np.min(numerical)
    features['max'] = np.max(numerical)
    features['range'] = features['max'] - features['min']
    features['iqr'] = np.percentile(numerical, 75) - np.percentile(numerical, 25)
    features['skew'] = pd.Series(numerical).skew()
    features['kurtosis'] = pd.Series(numerical).kurtosis()
    
    # 3. Special character features
    features['star_count'] = series.count('*')
    features['dot_count'] = series.count('.')
    features['star_dot_ratio'] = features['star_count'] / (features['dot_count'] + 1)
    
    # 4. Transition features
    transitions = sum(1 for i in range(len(series)-1) if series[i] != series[i+1])
    features['transition_rate'] = transitions / (len(series) - 1)
    
    # Numerical differences
    diff = np.diff(numerical)
    features['mean_abs_diff'] = np.mean(np.abs(diff))
    features['std_diff'] = np.std(diff)
    features['max_abs_diff'] = np.max(np.abs(diff))
    
    # 5. Run-length features
    runs = []
    current_char = series[0]
    current_len = 1
    for c in series[1:]:
        if c == current_char:
            current_len += 1
        else:
            runs.append((current_char, current_len))
            current_char = c
            current_len = 1
    runs.append((current_char, current_len))
    
    run_lengths = [r[1] for r in runs]
    features['num_runs'] = len(runs)
    features['mean_run_len'] = np.mean(run_lengths)
    features['max_run_len'] = max(run_lengths)
    features['std_run_len'] = np.std(run_lengths)
    
    # 6. Entropy
    probs = [count/total for count in char_counts.values()]
    features['entropy'] = -sum(p * np.log2(p) for p in probs if p > 0)
    
    # 7. Unique characters
    features['unique_chars'] = len(set(series))
    
    # 8. Position-based features
    n = len(series)
    features['first_half_star'] = series[:n//2].count('*') / (n//2)
    features['second_half_star'] = series[n//2:].count('*') / (n - n//2)
    features['first_half_dot'] = series[:n//2].count('.') / (n//2)
    features['second_half_dot'] = series[n//2:].count('.') / (n - n//2)
    
    # 9. Trend
    x = np.arange(len(numerical))
    slope, intercept = np.polyfit(x, numerical, 1)
    features['trend_slope'] = slope
    features['trend_intercept'] = intercept
    
    # 10. Autocorrelation
    if len(numerical) > 1:
        features['autocorr_1'] = np.corrcoef(numerical[:-1], numerical[1:])[0, 1]
        if len(numerical) > 2:
            features['autocorr_2'] = np.corrcoef(numerical[:-2], numerical[2:])[0, 1]
        else:
            features['autocorr_2'] = 0
    else:
        features['autocorr_1'] = 0
        features['autocorr_2'] = 0
    
    # 11. Peaks and valleys
    peaks = sum(1 for i in range(1, len(numerical)-1) 
                if numerical[i] > numerical[i-1] and numerical[i] > numerical[i+1])
    valleys = sum(1 for i in range(1, len(numerical)-1) 
                  if numerical[i] < numerical[i-1] and numerical[i] < numerical[i+1])
    features['peaks'] = peaks
    features['valleys'] = valleys
    features['peaks_valleys_ratio'] = peaks / (valleys + 1)
    
    # 12. Coefficient of variation
    features['cv'] = features['std'] / features['mean'] if features['mean'] > 0 else 0
    
    # 13. Energy (sum of squares)
    features['energy'] = np.sum(numerical ** 2)
    
    # 14. Zero crossing rate (for numerical series centered around mean)
    centered = numerical - np.mean(numerical)
    zero_crossings = sum(1 for i in range(len(centered)-1) if centered[i] * centered[i+1] < 0)
    features['zero_crossing_rate'] = zero_crossings / (len(centered) - 1)
    
    return features

def extract_features_df(df):
    """Extract features for a dataframe."""
    feature_list = []
    for series in df['symbol_series']:
        features = extract_all_features(series)
        feature_list.append(features)
    return pd.DataFrame(feature_list)

# Extract features
print("\n=== Extracting Features ===")
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

# Model training with hyperparameter tuning
print("\n=== Model Training ===")

results = {}

# Try multiple configurations
best_val_acc = 0
best_model = None
best_model_name = ""
best_test_pred = None

# 1. Random Forest with different parameters
for n_est in [100, 300, 500]:
    for max_d in [10, 15, 20, None]:
        rf = RandomForestClassifier(n_estimators=n_est, max_depth=max_d, 
                                    min_samples_split=5, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        val_pred = rf.predict(X_val)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = rf.predict(X_test)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        model_name = f"RF_n{n_est}_d{max_d}"
        results[model_name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model = rf
            best_model_name = model_name
            best_test_pred = test_pred
            best_test_acc = test_acc

print(f"Best RF: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 2. Extra Trees
for n_est in [200, 400]:
    et = ExtraTreesClassifier(n_estimators=n_est, max_depth=20, random_state=42, n_jobs=-1)
    et.fit(X_train, y_train)
    val_pred = et.predict(X_val)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = et.predict(X_test)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    model_name = f"ET_n{n_est}"
    results[model_name] = {'val': val_acc, 'test': test_acc}
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_model = et
        best_model_name = model_name
        best_test_pred = test_pred
        best_test_acc = test_acc

print(f"Best ET: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 3. Gradient Boosting
for n_est in [100, 200]:
    for lr in [0.05, 0.1]:
        gb = GradientBoostingClassifier(n_estimators=n_est, learning_rate=lr, 
                                        max_depth=5, random_state=42)
        gb.fit(X_train, y_train)
        val_pred = gb.predict(X_val)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = gb.predict(X_test)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        model_name = f"GB_n{n_est}_lr{lr}"
        results[model_name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model = gb
            best_model_name = model_name
            best_test_pred = test_pred
            best_test_acc = test_acc

print(f"Best GB: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 4. SVM
for C in [0.1, 1, 10, 100]:
    svm = SVC(kernel='rbf', C=C, gamma='scale', random_state=42)
    svm.fit(X_train_scaled, y_train)
    val_pred = svm.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = svm.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    model_name = f"SVM_C{C}"
    results[model_name] = {'val': val_acc, 'test': test_acc}
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_model = svm
        best_model_name = model_name
        best_test_pred = test_pred
        best_test_acc = test_acc

print(f"Best SVM: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 5. Logistic Regression
for C in [0.01, 0.1, 1, 10]:
    lr = LogisticRegression(C=C, max_iter=2000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    val_pred = lr.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = lr.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    model_name = f"LR_C{C}"
    results[model_name] = {'val': val_acc, 'test': test_acc}
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_model = lr
        best_model_name = model_name
        best_test_pred = test_pred
        best_test_acc = test_acc

print(f"Best LR: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

print(f"\n=== Best Overall Model: {best_model_name} ===")
print(f"Validation Balanced Accuracy: {best_val_acc:.4f}")
print(f"Test Balanced Accuracy: {best_test_acc:.4f}")

# Save results
results_df = pd.DataFrame([
    {'Model': name, 'Val_Balanced_Accuracy': res['val'], 'Test_Balanced_Accuracy': res['test']}
    for name, res in results.items()
])
results_df = results_df.sort_values('Val_Balanced_Accuracy', ascending=False)
results_df.to_csv('../outputs/model_results.csv', index=False)

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test_df['object_id'],
    'true_label': y_test,
    'predicted_label': best_test_pred
})
predictions_df.to_csv('../outputs/predictions.csv', index=False)

print("\n=== Analysis Complete ===")
