import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score
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

# Deep analysis of the symbol series
print("\n=== Deep Symbol Analysis ===")

# Check if there are any obvious patterns
var_series = train_df[train_df['label'] == 1]['symbol_series'].values
nonvar_series = train_df[train_df['label'] == 0]['symbol_series'].values

# Look at specific patterns
print("\nAnalyzing specific patterns...")

# Count specific subsequences
patterns = ['**', '..', '*.', '.*', 'zx', 'xz', 'yz', 'zy', 'xy', 'yx', 
            'uv', 'vu', 'uw', 'wu', 'vw', 'wv', 'wx', 'xw', 'yz', 'zy']

print("\nPattern frequencies by class:")
print(f"{'Pattern':<10} {'Variable':<15} {'Non-Variable':<15} {'Diff':<15}")
for pattern in patterns:
    var_count = np.mean([s.count(pattern) for s in var_series])
    nonvar_count = np.mean([s.count(pattern) for s in nonvar_series])
    print(f"{pattern:<10} {var_count:<15.4f} {nonvar_count:<15.4f} {var_count - nonvar_count:<15.4f}")

# Look at position-specific patterns
print("\n=== Position Analysis ===")
for pos in [0, 10, 20, 30, 39]:
    var_chars = [s[pos] for s in var_series]
    nonvar_chars = [s[pos] for s in nonvar_series]
    var_counter = Counter(var_chars)
    nonvar_counter = Counter(nonvar_chars)
    print(f"\nPosition {pos}:")
    for char in ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']:
        var_freq = var_counter.get(char, 0) / len(var_series)
        nonvar_freq = nonvar_counter.get(char, 0) / len(nonvar_series)
        if abs(var_freq - nonvar_freq) > 0.05:
            print(f"  {char}: Var={var_freq:.3f}, NonVar={nonvar_freq:.3f}, Diff={var_freq - nonvar_freq:.3f} ***")

# Try using the entire sequence as features
print("\n=== Sequence as Features ===")

# Map symbols to numbers
symbol_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def series_to_features(series_list):
    """Convert series to numerical features."""
    return np.array([[symbol_map[c] for c in s] for s in series_list])

X_train_seq = series_to_features(train_df['symbol_series'].tolist())
X_val_seq = series_to_features(val_df['symbol_series'].tolist())
X_test_seq = series_to_features(test_df['symbol_series'].tolist())

print(f"Sequence shape: {X_train_seq.shape}")

# Try different models on raw sequence
print("\n=== Models on Raw Sequence ===")

results = {}
best_val_acc = 0
best_test_pred = None
best_test_acc = 0
best_model_name = ""

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_seq)
X_val_scaled = scaler.transform(X_val_seq)
X_test_scaled = scaler.transform(X_test_seq)

# 1. Logistic Regression
for C in [0.001, 0.01, 0.1, 1, 10]:
    lr = LogisticRegression(C=C, max_iter=5000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    val_pred = lr.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = lr.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"LR_C{C}"
    results[name] = {'val': val_acc, 'test': test_acc}
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name

print(f"Best LR: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 2. SVM
for C in [0.01, 0.1, 1, 10, 100]:
    for kernel in ['rbf', 'linear']:
        svm = SVC(C=C, kernel=kernel, random_state=42)
        svm.fit(X_train_scaled, y_train)
        val_pred = svm.predict(X_val_scaled)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = svm.predict(X_test_scaled)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"SVM_{kernel}_C{C}"
        results[name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name

print(f"Best SVM: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 3. Random Forest
for n_est in [100, 300, 500]:
    for max_depth in [5, 10, 15, None]:
        rf = RandomForestClassifier(n_estimators=n_est, max_depth=max_depth, 
                                    random_state=42, n_jobs=-1)
        rf.fit(X_train_seq, y_train)
        val_pred = rf.predict(X_val_seq)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = rf.predict(X_test_seq)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"RF_{n_est}_{max_depth}"
        results[name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name

print(f"Best RF: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 4. Gradient Boosting
for n_est in [100, 200]:
    for lr in [0.01, 0.05, 0.1]:
        gb = GradientBoostingClassifier(n_estimators=n_est, learning_rate=lr, 
                                        max_depth=3, random_state=42)
        gb.fit(X_train_seq, y_train)
        val_pred = gb.predict(X_val_seq)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = gb.predict(X_test_seq)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"GB_{n_est}_{lr}"
        results[name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name

print(f"Best GB: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# Try with n-grams
print("\n=== N-gram Features ===")
for ngram_range in [(1, 2), (1, 3), (2, 3), (2, 4), (3, 5)]:
    vectorizer = CountVectorizer(analyzer='char', ngram_range=ngram_range, lowercase=False)
    X_train_ng = vectorizer.fit_transform(train_df['symbol_series'])
    X_val_ng = vectorizer.transform(val_df['symbol_series'])
    X_test_ng = vectorizer.transform(test_df['symbol_series'])
    
    for C in [0.1, 1, 10]:
        lr = LogisticRegression(C=C, max_iter=2000, random_state=42)
        lr.fit(X_train_ng, y_train)
        val_pred = lr.predict(X_val_ng)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = lr.predict(X_test_ng)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"LR_ng{ngram_range}_C{C}"
        results[name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name

print(f"Best overall: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

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
