import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, classification_report
from sklearn.feature_extraction.text import CountVectorizer
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# Load data
print("Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values

# Symbol mapping
symbol_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
all_symbols = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']

def extract_discriminative_features(series):
    """Extract features based on discriminative patterns found."""
    features = {}
    
    # Key discriminative patterns
    patterns = ['**', '..', 'wu', 'xw', 'yz', 'yx', 'vw', 'uv', 'vu', 'zx', 'zy']
    for p in patterns:
        features[f'count_{p}'] = series.count(p)
        features[f'ratio_{p}'] = series.count(p) / (len(series) - 1)
    
    # Special character patterns
    features['star_star_ratio'] = series.count('**') / (series.count('*') + 1)
    features['dot_dot_ratio'] = series.count('..') / (series.count('.') + 1)
    
    # Numerical representation
    numerical = np.array([symbol_map[c] for c in series])
    
    # Basic stats
    features['mean'] = np.mean(numerical)
    features['std'] = np.std(numerical)
    features['var'] = np.var(numerical)
    
    # Frequency of each symbol
    total = len(series)
    for s in all_symbols:
        features[f'freq_{s}'] = series.count(s) / total
    
    # Special ratios
    features['star_dot_ratio'] = series.count('*') / (series.count('.') + 1)
    features['special_total'] = (series.count('*') + series.count('.')) / total
    
    # Transitions
    transitions = sum(1 for i in range(len(series)-1) if series[i] != series[i+1])
    features['transition_rate'] = transitions / (len(series) - 1)
    
    # Run features
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
    features['mean_run'] = np.mean(run_lengths)
    features['max_run'] = max(run_lengths)
    
    # Entropy
    probs = [c/total for c in Counter(series).values()]
    features['entropy'] = -sum(p * np.log2(p) for p in probs if p > 0)
    
    # Unique chars
    features['unique_chars'] = len(set(series))
    
    # Position features (key positions found)
    for pos in [0, 10, 20, 30, 39]:
        features[f'pos_{pos}'] = symbol_map[series[pos]]
    
    # Quarter features
    n = len(series)
    for i in range(4):
        start = i * n // 4
        end = (i + 1) * n // 4
        segment = series[start:end]
        features[f'q{i+1}_star'] = segment.count('*') / len(segment)
        features[f'q{i+1}_dot'] = segment.count('.') / len(segment)
        features[f'q{i+1}_mean'] = np.mean([symbol_map[c] for c in segment])
    
    # Trend
    x = np.arange(len(numerical))
    features['trend'] = np.polyfit(x, numerical, 1)[0]
    
    # Autocorrelation
    features['autocorr_1'] = np.corrcoef(numerical[:-1], numerical[1:])[0, 1] if len(numerical) > 1 else 0
    
    # Peaks and valleys
    peaks = sum(1 for i in range(1, len(numerical)-1) if numerical[i] > numerical[i-1] and numerical[i] > numerical[i+1])
    valleys = sum(1 for i in range(1, len(numerical)-1) if numerical[i] < numerical[i-1] and numerical[i] < numerical[i+1])
    features['peaks'] = peaks
    features['valleys'] = valleys
    features['peaks_valleys_ratio'] = peaks / (valleys + 1)
    
    # Numerical differences
    diff = np.diff(numerical)
    features['mean_abs_diff'] = np.mean(np.abs(diff))
    features['std_diff'] = np.std(diff)
    
    # Energy
    features['energy'] = np.sum(numerical ** 2)
    
    return features

def extract_features_df(df):
    return pd.DataFrame([extract_discriminative_features(s) for s in df['symbol_series']])

print("\n=== Extracting Features ===")
X_train = extract_features_df(train_df)
X_val = extract_features_df(val_df)
X_test = extract_features_df(test_df)

print(f"Feature matrix shape: {X_train.shape}")

# Fill NaN
X_train = X_train.fillna(0)
X_val = X_val.fillna(0)
X_test = X_test.fillna(0)

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Also try n-grams
print("\n=== N-gram Features ===")
vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 5), lowercase=False, max_features=1000)
X_train_ngram = vectorizer.fit_transform(train_df['symbol_series'])
X_val_ngram = vectorizer.transform(val_df['symbol_series'])
X_test_ngram = vectorizer.transform(test_df['symbol_series'])

print(f"N-gram shape: {X_train_ngram.shape}")

# Model training
print("\n=== Model Training ===")

results = {}
best_val_acc = 0
best_test_pred = None
best_test_acc = 0
best_model_name = ""

# Test on extracted features
print("\n--- Extracted Features ---")

# 1. Random Forest
for n_est in [200, 400, 600]:
    for max_depth in [10, 15, 20, None]:
        rf = RandomForestClassifier(n_estimators=n_est, max_depth=max_depth, 
                                    min_samples_split=3, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        val_pred = rf.predict(X_val)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = rf.predict(X_test)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"RF_{n_est}_{max_depth}"
        results[name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name

print(f"Best RF: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 2. Extra Trees
for n_est in [200, 400]:
    et = ExtraTreesClassifier(n_estimators=n_est, max_depth=20, random_state=42, n_jobs=-1)
    et.fit(X_train, y_train)
    val_pred = et.predict(X_val)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = et.predict(X_test)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"ET_{n_est}"
    results[name] = {'val': val_acc, 'test': test_acc}
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name

print(f"Best ET: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 3. Gradient Boosting
for n_est in [100, 200, 300]:
    for lr in [0.05, 0.1]:
        for depth in [3, 5]:
            gb = GradientBoostingClassifier(n_estimators=n_est, learning_rate=lr, 
                                            max_depth=depth, random_state=42)
            gb.fit(X_train, y_train)
            val_pred = gb.predict(X_val)
            val_acc = balanced_accuracy_score(y_val, val_pred)
            test_pred = gb.predict(X_test)
            test_acc = balanced_accuracy_score(y_test, test_pred)
            
            name = f"GB_{n_est}_{lr}_{depth}"
            results[name] = {'val': val_acc, 'test': test_acc}
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_test_pred = test_pred
                best_test_acc = test_acc
                best_model_name = name

print(f"Best GB: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 4. SVM
for C in [0.1, 1, 10, 100]:
    for kernel in ['rbf', 'linear']:
        svm = SVC(C=C, kernel=kernel, random_state=42)
        svm.fit(X_train_scaled, y_train)
        val_pred = svm.predict(X_val_scaled)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = svm.predict(X_test_scaled)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"SVM_{kernel}_{C}"
        results[name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name

print(f"Best SVM: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 5. Logistic Regression
for C in [0.01, 0.1, 1, 10]:
    lr = LogisticRegression(C=C, max_iter=2000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    val_pred = lr.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = lr.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"LR_{C}"
    results[name] = {'val': val_acc, 'test': test_acc}
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name

print(f"Best LR: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 6. N-gram with Logistic Regression
print("\n--- N-gram Features ---")
for C in [0.01, 0.1, 1, 10]:
    lr = LogisticRegression(C=C, max_iter=2000, random_state=42)
    lr.fit(X_train_ngram, y_train)
    val_pred = lr.predict(X_val_ngram)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = lr.predict(X_test_ngram)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"LR_ngram_{C}"
    results[name] = {'val': val_acc, 'test': test_acc}
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name

print(f"Best LR_ngram: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

print(f"\n=== Best Model: {best_model_name} ===")
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
