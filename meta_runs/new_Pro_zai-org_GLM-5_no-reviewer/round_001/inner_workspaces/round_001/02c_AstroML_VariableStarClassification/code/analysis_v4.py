import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
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

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values

# Get all unique symbols
all_symbols = set()
for df in [train_df, val_df, test_df]:
    for series in df['symbol_series']:
        all_symbols.update(series)
all_symbols = sorted(all_symbols)
print(f"Unique symbols: {all_symbols}")

# Approach 1: N-gram features using CountVectorizer
print("\n=== Approach 1: N-gram Features ===")

# Use character n-grams
vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 4), lowercase=False)
X_train_ngram = vectorizer.fit_transform(train_df['symbol_series'])
X_val_ngram = vectorizer.transform(val_df['symbol_series'])
X_test_ngram = vectorizer.transform(test_df['symbol_series'])

print(f"N-gram feature matrix shape: {X_train_ngram.shape}")

# Approach 2: TF-IDF features
print("\n=== Approach 2: TF-IDF Features ===")

tfidf = TfidfVectorizer(analyzer='char', ngram_range=(1, 4), lowercase=False)
X_train_tfidf = tfidf.fit_transform(train_df['symbol_series'])
X_val_tfidf = tfidf.transform(val_df['symbol_series'])
X_test_tfidf = tfidf.transform(test_df['symbol_series'])

print(f"TF-IDF feature matrix shape: {X_train_tfidf.shape}")

# Approach 3: One-hot encoding of each position
print("\n=== Approach 3: Position-based One-hot Encoding ===")

def one_hot_encode(series_list, symbols):
    """One-hot encode each position in the series."""
    symbol_to_idx = {s: i for i, s in enumerate(symbols)}
    n_samples = len(series_list)
    seq_len = len(series_list[0])
    n_symbols = len(symbols)
    
    encoded = np.zeros((n_samples, seq_len * n_symbols))
    for i, series in enumerate(series_list):
        for j, char in enumerate(series):
            if char in symbol_to_idx:
                encoded[i, j * n_symbols + symbol_to_idx[char]] = 1
    return encoded

X_train_oh = one_hot_encode(train_df['symbol_series'].tolist(), all_symbols)
X_val_oh = one_hot_encode(val_df['symbol_series'].tolist(), all_symbols)
X_test_oh = one_hot_encode(test_df['symbol_series'].tolist(), all_symbols)

print(f"One-hot encoded matrix shape: {X_train_oh.shape}")

# Approach 4: Numerical encoding with symbol mapping
print("\n=== Approach 4: Numerical Encoding ===")

symbol_map = {'.': 0, '*': 1, 'u': 2, 'v': 3, 'w': 4, 'x': 5, 'y': 6, 'z': 7}

def numerical_encode(series_list):
    """Convert series to numerical array."""
    return np.array([[symbol_map.get(c, 0) for c in s] for s in series_list])

X_train_num = numerical_encode(train_df['symbol_series'].tolist())
X_val_num = numerical_encode(val_df['symbol_series'].tolist())
X_test_num = numerical_encode(test_df['symbol_series'].tolist())

print(f"Numerical encoded matrix shape: {X_train_num.shape}")

# Combine all features
print("\n=== Combining Features ===")

# Statistical features
def extract_stat_features(series_list):
    features = []
    for series in series_list:
        numerical = np.array([symbol_map.get(c, 0) for c in series])
        feat = {
            'mean': np.mean(numerical),
            'std': np.std(numerical),
            'min': np.min(numerical),
            'max': np.max(numerical),
            'range': np.max(numerical) - np.min(numerical),
            'star_count': series.count('*'),
            'dot_count': series.count('.'),
            'entropy': -sum(p * np.log2(p) for p in [c/len(series) for c in Counter(series).values()] if p > 0),
            'unique_chars': len(set(series)),
            'transitions': sum(1 for i in range(len(series)-1) if series[i] != series[i+1]),
        }
        features.append(feat)
    return pd.DataFrame(features)

X_train_stat = extract_stat_features(train_df['symbol_series'].tolist())
X_val_stat = extract_stat_features(val_df['symbol_series'].tolist())
X_test_stat = extract_stat_features(test_df['symbol_series'].tolist())

# Combine: n-gram + statistical
from scipy.sparse import hstack, csr_matrix

X_train_combined = hstack([X_train_ngram, csr_matrix(X_train_stat.values)])
X_val_combined = hstack([X_val_ngram, csr_matrix(X_val_stat.values)])
X_test_combined = hstack([X_test_ngram, csr_matrix(X_test_stat.values)])

print(f"Combined feature matrix shape: {X_train_combined.shape}")

# Model training
print("\n=== Model Training ===")

results = {}
best_val_acc = 0
best_model = None
best_model_name = ""
best_test_pred = None
best_test_acc = 0

# Test different feature sets
feature_sets = [
    ('ngram', X_train_ngram, X_val_ngram, X_test_ngram),
    ('tfidf', X_train_tfidf, X_val_tfidf, X_test_tfidf),
    ('onehot', csr_matrix(X_train_oh), csr_matrix(X_val_oh), csr_matrix(X_test_oh)),
    ('numerical', csr_matrix(X_train_num), csr_matrix(X_val_num), csr_matrix(X_test_num)),
    ('combined', X_train_combined, X_val_combined, X_test_combined),
]

for feat_name, X_tr, X_va, X_te in feature_sets:
    print(f"\n--- Feature Set: {feat_name} ---")
    
    # Random Forest
    rf = RandomForestClassifier(n_estimators=300, max_depth=15, random_state=42, n_jobs=-1)
    rf.fit(X_tr, y_train)
    val_pred = rf.predict(X_va)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = rf.predict(X_te)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    model_name = f"RF_{feat_name}"
    results[model_name] = {'val': val_acc, 'test': test_acc}
    print(f"RF - Val: {val_acc:.4f}, Test: {test_acc:.4f}")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_model = rf
        best_model_name = model_name
        best_test_pred = test_pred
        best_test_acc = test_acc
    
    # Logistic Regression (for sparse matrices)
    lr = LogisticRegression(max_iter=2000, C=1.0, random_state=42)
    lr.fit(X_tr, y_train)
    val_pred = lr.predict(X_va)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = lr.predict(X_te)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    model_name = f"LR_{feat_name}"
    results[model_name] = {'val': val_acc, 'test': test_acc}
    print(f"LR - Val: {val_acc:.4f}, Test: {test_acc:.4f}")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_model = lr
        best_model_name = model_name
        best_test_pred = test_pred
        best_test_acc = test_acc

# Also try on numerical features with SVM
print("\n--- SVM on numerical features ---")
scaler = StandardScaler()
X_train_num_scaled = scaler.fit_transform(X_train_num)
X_val_num_scaled = scaler.transform(X_val_num)
X_test_num_scaled = scaler.transform(X_test_num)

for C in [0.1, 1, 10, 100]:
    svm = SVC(kernel='rbf', C=C, gamma='scale', random_state=42)
    svm.fit(X_train_num_scaled, y_train)
    val_pred = svm.predict(X_val_num_scaled)
    val_acc = balanced_accuracy_score(y_val, val_pred)
    test_pred = svm.predict(X_test_num_scaled)
    test_acc = balanced_accuracy_score(y_test, test_pred)
    
    model_name = f"SVM_num_C{C}"
    results[model_name] = {'val': val_acc, 'test': test_acc}
    print(f"SVM C={C} - Val: {val_acc:.4f}, Test: {test_acc:.4f}")
    
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_model = svm
        best_model_name = model_name
        best_test_pred = test_pred
        best_test_acc = test_acc

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
