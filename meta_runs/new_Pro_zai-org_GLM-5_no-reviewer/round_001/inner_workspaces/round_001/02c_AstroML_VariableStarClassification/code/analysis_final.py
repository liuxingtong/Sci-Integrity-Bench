import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, classification_report, roc_curve, auc
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from scipy.sparse import hstack, csr_matrix
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

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# Symbol mapping
symbol_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}
all_symbols = ['*', '.', 'u', 'v', 'w', 'x', 'y', 'z']

# Feature extraction
def extract_all_features(series):
    features = {}
    numerical = np.array([symbol_map[c] for c in series])
    total = len(series)
    
    # 1. Symbol frequencies
    for s in all_symbols:
        features[f'freq_{s}'] = series.count(s) / total
    
    # 2. Statistical features
    features['mean'] = np.mean(numerical)
    features['std'] = np.std(numerical)
    features['var'] = np.var(numerical)
    features['median'] = np.median(numerical)
    features['min'] = np.min(numerical)
    features['max'] = np.max(numerical)
    features['range'] = features['max'] - features['min']
    features['skew'] = pd.Series(numerical).skew()
    features['kurtosis'] = pd.Series(numerical).kurtosis()
    
    # 3. Special character features
    features['star_count'] = series.count('*')
    features['dot_count'] = series.count('.')
    features['star_ratio'] = features['star_count'] / total
    features['dot_ratio'] = features['dot_count'] / total
    features['star_dot_ratio'] = features['star_count'] / (features['dot_count'] + 1)
    features['special_ratio'] = (features['star_count'] + features['dot_count']) / total
    
    # 4. Transition features
    transitions = sum(1 for i in range(len(series)-1) if series[i] != series[i+1])
    features['transition_rate'] = transitions / (len(series) - 1)
    
    diff = np.diff(numerical)
    features['mean_abs_diff'] = np.mean(np.abs(diff))
    features['std_diff'] = np.std(diff)
    features['max_abs_diff'] = np.max(np.abs(diff))
    features['positive_diffs'] = np.sum(diff > 0)
    features['negative_diffs'] = np.sum(diff < 0)
    features['zero_diffs'] = np.sum(diff == 0)
    
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
    features['mean_run'] = np.mean(run_lengths)
    features['max_run'] = max(run_lengths)
    features['std_run'] = np.std(run_lengths)
    
    # Star and dot runs
    star_runs = [r[1] for r in runs if r[0] == '*']
    dot_runs = [r[1] for r in runs if r[0] == '.']
    features['max_star_run'] = max(star_runs) if star_runs else 0
    features['max_dot_run'] = max(dot_runs) if dot_runs else 0
    features['mean_star_run'] = np.mean(star_runs) if star_runs else 0
    features['mean_dot_run'] = np.mean(dot_runs) if dot_runs else 0
    
    # 6. Entropy
    probs = [c/total for c in Counter(series).values()]
    features['entropy'] = -sum(p * np.log2(p) for p in probs if p > 0)
    
    # 7. Unique characters
    features['unique_chars'] = len(set(series))
    
    # 8. Position features
    n = len(series)
    for i in range(4):
        start = i * n // 4
        end = (i + 1) * n // 4
        segment = series[start:end]
        features[f'q{i+1}_star'] = segment.count('*') / len(segment)
        features[f'q{i+1}_dot'] = segment.count('.') / len(segment)
        features[f'q{i+1}_mean'] = np.mean([symbol_map[c] for c in segment])
        features[f'q{i+1}_std'] = np.std([symbol_map[c] for c in segment])
    
    # 9. Trend
    x = np.arange(len(numerical))
    features['trend'] = np.polyfit(x, numerical, 1)[0]
    
    # 10. Autocorrelation
    features['autocorr_1'] = np.corrcoef(numerical[:-1], numerical[1:])[0, 1] if len(numerical) > 1 else 0
    features['autocorr_2'] = np.corrcoef(numerical[:-2], numerical[2:])[0, 1] if len(numerical) > 2 else 0
    features['autocorr_3'] = np.corrcoef(numerical[:-3], numerical[3:])[0, 1] if len(numerical) > 3 else 0
    
    # 11. Peaks and valleys
    peaks = sum(1 for i in range(1, len(numerical)-1) if numerical[i] > numerical[i-1] and numerical[i] > numerical[i+1])
    valleys = sum(1 for i in range(1, len(numerical)-1) if numerical[i] < numerical[i-1] and numerical[i] < numerical[i+1])
    features['peaks'] = peaks
    features['valleys'] = valleys
    features['peaks_valleys_ratio'] = peaks / (valleys + 1)
    
    # 12. Energy
    features['energy'] = np.sum(numerical ** 2)
    
    # 13. Zero crossings
    centered = numerical - np.mean(numerical)
    features['zero_crossings'] = sum(1 for i in range(len(centered)-1) if centered[i] * centered[i+1] < 0)
    
    # 14. Coefficient of variation
    features['cv'] = features['std'] / features['mean'] if features['mean'] > 0 else 0
    
    # 15. Key discriminative bigrams
    bigrams = Counter([series[i:i+2] for i in range(len(series)-1)])
    key_bigrams = ['**', '..', 'wu', 'xw', 'yz', 'yx', 'vw', 'uv', 'vu', 'zx', 'zy', '.*', '*.', 'uw', 'wx']
    for bg in key_bigrams:
        features[f'bigram_{bg}'] = bigrams.get(bg, 0) / (len(series) - 1)
    
    # 16. Trigrams
    trigrams = Counter([series[i:i+3] for i in range(len(series)-2)])
    for tg in ['***', '...', '*.*', '.*.', 'zyx', 'xyz', 'uvw', 'vuw']:
        features[f'trigram_{tg}'] = trigrams.get(tg, 0) / (len(series) - 2)
    
    return features

def extract_features_df(df):
    return pd.DataFrame([extract_all_features(s) for s in df['symbol_series']])

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

# N-gram features
print("\n=== N-gram Features ===")
vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 5), lowercase=False, max_features=2000)
X_train_ngram = vectorizer.fit_transform(train_df['symbol_series'])
X_val_ngram = vectorizer.transform(val_df['symbol_series'])
X_test_ngram = vectorizer.transform(test_df['symbol_series'])

print(f"N-gram shape: {X_train_ngram.shape}")

# Combine features
X_train_combined = hstack([csr_matrix(X_train_scaled), X_train_ngram])
X_val_combined = hstack([csr_matrix(X_val_scaled), X_val_ngram])
X_test_combined = hstack([csr_matrix(X_test_scaled), X_test_ngram])

print(f"Combined shape: {X_train_combined.shape}")

# Model training
print("\n=== Model Training ===")

results = {}
best_val_acc = 0
best_test_pred = None
best_test_acc = 0
best_model_name = ""

# Test different feature sets
feature_sets = [
    ('extracted', X_train_scaled, X_val_scaled, X_test_scaled),
    ('ngram', X_train_ngram, X_val_ngram, X_test_ngram),
    ('combined', X_train_combined, X_val_combined, X_test_combined),
]

for feat_name, X_tr, X_va, X_te in feature_sets:
    print(f"\n--- Feature Set: {feat_name} ---")
    
    # Random Forest
    for n_est in [300, 500]:
        for max_depth in [15, 20, None]:
            rf = RandomForestClassifier(n_estimators=n_est, max_depth=max_depth, 
                                        min_samples_split=3, random_state=42, n_jobs=-1)
            rf.fit(X_tr, y_train)
            val_pred = rf.predict(X_va)
            val_acc = balanced_accuracy_score(y_val, val_pred)
            test_pred = rf.predict(X_te)
            test_acc = balanced_accuracy_score(y_test, test_pred)
            
            name = f"RF_{feat_name}_{n_est}_{max_depth}"
            results[name] = {'val': val_acc, 'test': test_acc}
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_test_pred = test_pred
                best_test_acc = test_acc
                best_model_name = name
    
    print(f"Best RF on {feat_name}: Val={max([results[n]['val'] for n in results if f'RF_{feat_name}' in n]):.4f}")
    
    # Extra Trees
    for n_est in [300, 500]:
        et = ExtraTreesClassifier(n_estimators=n_est, max_depth=20, random_state=42, n_jobs=-1)
        et.fit(X_tr, y_train)
        val_pred = et.predict(X_va)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = et.predict(X_te)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"ET_{feat_name}_{n_est}"
        results[name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name
    
    # Logistic Regression
    for C in [0.01, 0.1, 1, 10]:
        lr = LogisticRegression(C=C, max_iter=3000, random_state=42)
        lr.fit(X_tr, y_train)
        val_pred = lr.predict(X_va)
        val_acc = balanced_accuracy_score(y_val, val_pred)
        test_pred = lr.predict(X_te)
        test_acc = balanced_accuracy_score(y_test, test_pred)
        
        name = f"LR_{feat_name}_{C}"
        results[name] = {'val': val_acc, 'test': test_acc}
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_test_pred = test_pred
            best_test_acc = test_acc
            best_model_name = name

# SVM on extracted features
print("\n--- SVM on extracted features ---")
for C in [0.1, 1, 10, 100]:
    svm = SVC(C=C, kernel='rbf', random_state=42)
    svm.fit(X_train_scaled, y_train)
    val_pred = svm.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = svm.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"SVM_{C}"
    results[name] = {'val': val_acc, 'test': test_acc}
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name

# MLP
print("\n--- MLP ---")
for hidden in [(100,), (200,), (100, 50), (200, 100), (300, 150)]:
    mlp = MLPClassifier(hidden_layer_sizes=hidden, max_iter=2000, random_state=42, early_stopping=True)
    mlp.fit(X_train_scaled, y_train)
    val_pred = mlp.predict(X_val_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = mlp.predict(X_test_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    name = f"MLP_{hidden}"
    results[name] = {'val': val_acc, 'test': test_acc}
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_test_pred = test_pred
        best_test_acc = test_acc
        best_model_name = name

print(f"\n=== Best Model: {best_model_name} ===")
print(f"Validation Balanced Accuracy: {best_val_acc:.4f}")
print(f"Test Balanced Accuracy: {best_test_acc:.4f}")

# Classification report
print("\n=== Classification Report ===")
print(classification_report(y_test, best_test_pred, target_names=['Non-Variable', 'Variable']))

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
