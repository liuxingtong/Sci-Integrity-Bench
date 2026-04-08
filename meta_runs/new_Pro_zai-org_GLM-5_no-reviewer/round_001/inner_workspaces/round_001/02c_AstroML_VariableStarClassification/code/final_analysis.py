import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, classification_report, roc_curve, auc
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
plt.style.use('seaborn-v0_8-whitegrid')

# Load data
print("Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# Symbol mapping
symbol_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
all_symbols = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']

def extract_features(series):
    features = {}
    numerical = np.array([symbol_map[c] for c in series])
    total = len(series)
    
    # Symbol frequencies
    for s in all_symbols:
        features[f'freq_{s}'] = series.count(s) / total
    
    # Basic stats
    features['mean'] = np.mean(numerical)
    features['std'] = np.std(numerical)
    features['var'] = np.var(numerical)
    features['median'] = np.median(numerical)
    features['min'] = np.min(numerical)
    features['max'] = np.max(numerical)
    features['range'] = features['max'] - features['min']
    
    # Special character features
    features['star_count'] = series.count('*')
    features['dot_count'] = series.count('.')
    features['star_dot_ratio'] = series.count('*') / (series.count('.') + 1)
    features['special_ratio'] = (series.count('*') + series.count('.')) / total
    
    # Transition features
    transitions = sum(1 for i in range(len(series)-1) if series[i] != series[i+1])
    features['transition_rate'] = transitions / (len(series) - 1)
    
    diff = np.diff(numerical)
    features['mean_abs_diff'] = np.mean(np.abs(diff))
    features['std_diff'] = np.std(diff)
    
    # Run-length features
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
    
    # Unique characters
    features['unique_chars'] = len(set(series))
    
    # Position features
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
    
    # Key bigrams
    bigrams = Counter([series[i:i+2] for i in range(len(series)-1)])
    key_bigrams = ['**', '..', 'wu', 'xw', 'yz', 'yx', 'vw', 'uv', 'vu', 'zx']
    for bg in key_bigrams:
        features[f'bigram_{bg}'] = bigrams.get(bg, 0) / (len(series) - 1)
    
    return features

def extract_features_df(df):
    return pd.DataFrame([extract_features(s) for s in df['symbol_series']])

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

# Model training
print("\n=== Model Training ===")

results = {}
best_val_acc = 0
best_test_pred = None
best_test_acc = 0
best_model_name = ""
best_model = None

# 1. Logistic Regression
print("\n--- Logistic Regression ---")
for C in [0.001, 0.01, 0.1, 1, 10]:
    lr = LogisticRegression(C=C, max_iter=5000, random_state=42)
    lr.fit(X_train_scaled, y_train)
    val_pred = lr.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = lr.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"LR_C{C}"
    results[name] = {'val': val_acc, 'test': test_acc, 'model': lr}
    print(f"LR C={C}: Val={val_acc:.4f}, Test={test_acc:.4f}")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name
        best_model = lr

# 2. SVM
print("\n--- SVM ---")
for C in [0.1, 1, 10]:
    svm = SVC(C=C, kernel='rbf', random_state=42, probability=True)
    svm.fit(X_train_scaled, y_train)
    val_pred = svm.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = svm.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"SVM_C{C}"
    results[name] = {'val': val_acc, 'test': test_acc, 'model': svm}
    print(f"SVM C={C}: Val={val_acc:.4f}, Test={test_acc:.4f}")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name
        best_model = svm

# 3. Random Forest
print("\n--- Random Forest ---")
for n_est in [200, 400]:
    for max_depth in [10, 15, 20]:
        rf = RandomForestClassifier(n_estimators=n_est, max_depth=max_depth, 
                                    min_samples_split=5, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        val_pred = rf.predict(X_val)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = rf.predict(X_test)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"RF_{n_est}_{max_depth}"
        results[name] = {'val': val_acc, 'test': test_acc, 'model': rf}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name
            best_model = rf

print(f"Best RF: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 4. Extra Trees
print("\n--- Extra Trees ---")
for n_est in [200, 400]:
    for max_depth in [15, 20]:
        et = ExtraTreesClassifier(n_estimators=n_est, max_depth=max_depth, 
                                  random_state=42, n_jobs=-1)
        et.fit(X_train, y_train)
        val_pred = et.predict(X_val)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = et.predict(X_test)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"ET_{n_est}_{max_depth}"
        results[name] = {'val': val_acc, 'test': test_acc, 'model': et}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name
            best_model = et

print(f"Best ET: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

# 5. Gradient Boosting
print("\n--- Gradient Boosting ---")
for n_est in [100, 200]:
    for lr in [0.05, 0.1]:
        gb = GradientBoostingClassifier(n_estimators=n_est, learning_rate=lr, 
                                        max_depth=4, random_state=42)
        gb.fit(X_train, y_train)
        val_pred = gb.predict(X_val)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = gb.predict(X_test)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"GB_{n_est}_{lr}"
        results[name] = {'val': val_acc, 'test': test_acc, 'model': gb}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name
            best_model = gb

print(f"Best GB: {best_model_name} - Val: {best_val_acc:.4f}, Test: {best_test_acc:.4f}")

print(f"\n=== Best Model: {best_model_name} ===")
print(f"Validation Balanced Accuracy: {best_val_acc:.4f}")
print(f"Test Balanced Accuracy: {best_test_acc:.4f}")

# Classification report
print("\n=== Classification Report ===")
print(classification_report(y_test, best_test_pred, target_names=['Non-Variable', 'Variable']))

# Create visualizations
print("\n=== Creating Visualizations ===")

# 1. Confusion Matrix
fig, ax = plt.subplots(figsize=(8, 6))
cm = confusion_matrix(y_test, best_test_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['Non-Variable', 'Variable'],
            yticklabels=['Non-Variable', 'Variable'])
ax.set_xlabel('Predicted')
ax.set_ylabel('True')
ax.set_title(f'Confusion Matrix - {best_model_name}')
plt.tight_layout()
plt.savefig('../report/images/confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved confusion_matrix.png")

# 2. Model Comparison
fig, ax = plt.subplots(figsize=(12, 6))
model_names = list(results.keys())
val_accs = [results[n]['val'] for n in model_names]
test_accs = [results[n]['test'] for n in model_names]

x = np.arange(len(model_names))
width = 0.35

bars1 = ax.bar(x - width/2, val_accs, width, label='Validation', color='steelblue')
bars2 = ax.bar(x + width/2, test_accs, width, label='Test', color='coral')

ax.set_xlabel('Model')
ax.set_ylabel('Balanced Accuracy')
ax.set_title('Model Performance Comparison')
ax.set_xticks(x)
ax.set_xticklabels(model_names, rotation=45, ha='right')
ax.legend()
ax.axhline(y=0.78, color='green', linestyle='--', label='Baseline (0.78)')
ax.set_ylim(0, 1)
plt.tight_layout()
plt.savefig('../report/images/model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved model_comparison.png")

# 3. Feature Importance (for tree-based models)
if best_model_name.startswith('RF') or best_model_name.startswith('ET') or best_model_name.startswith('GB'):
    fig, ax = plt.subplots(figsize=(10, 8))
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1][:20]
    
    ax.barh(range(len(indices)), importances[indices], align='center')
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([X_train.columns[i] for i in indices])
    ax.set_xlabel('Feature Importance')
    ax.set_title('Top 20 Feature Importances')
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig('../report/images/feature_importance.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved feature_importance.png")

# 4. Symbol Frequency Distribution
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
for idx, symbol in enumerate(all_symbols):
    ax = axes[idx // 4, idx % 4]
    var_freqs = [s.count(symbol) / len(s) for s in train_df[train_df['label'] == 1]['symbol_series']]
    nonvar_freqs = [s.count(symbol) / len(s) for s in train_df[train_df['label'] == 0]['symbol_series']]
    
    ax.hist(var_freqs, bins=20, alpha=0.5, label='Variable', color='blue')
    ax.hist(nonvar_freqs, bins=20, alpha=0.5, label='Non-Variable', color='red')
    ax.set_title(f'Symbol: {symbol}')
    ax.legend()
    ax.set_xlabel('Frequency')
    ax.set_ylabel('Count')

plt.tight_layout()
plt.savefig('../report/images/symbol_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved symbol_distributions.png")

# 5. Label Distribution
fig, axes = plt.subplots(1, 3, figsize=(12, 4))
for i, (df, name) in enumerate([(train_df, 'Train'), (val_df, 'Validation'), (test_df, 'Test')]):
    ax = axes[i]
    df['label'].value_counts().plot(kind='bar', ax=ax, color=['coral', 'steelblue'])
    ax.set_title(f'{name} Set')
    ax.set_xlabel('Label')
    ax.set_ylabel('Count')
    ax.set_xticklabels(['Non-Variable', 'Variable'], rotation=0)

plt.tight_layout()
plt.savefig('../report/images/label_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved label_distribution.png")

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
