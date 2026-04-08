import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

# Load data
train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

y_train = train['default_flag'].values
y_val = val['default_flag'].values
y_test = test['default_flag'].values

print("=== Sequence Modeling Approach ===")
print(f"Training samples: {len(train)}")

# Approach 1: Character n-grams
print("\n--- Character N-grams ---")

# Try different n-gram ranges
ngram_ranges = [(1, 1), (1, 2), (1, 3), (2, 3), (3, 3)]
results_ngrams = {}

for ngram_range in ngram_ranges:
    print(f"\nN-gram range: {ngram_range}")
    
    # Create n-gram features
    vectorizer = CountVectorizer(analyzer='char', ngram_range=ngram_range)
    X_train_ngrams = vectorizer.fit_transform(train['sym_seq'])
    X_val_ngrams = vectorizer.transform(val['sym_seq'])
    X_test_ngrams = vectorizer.transform(test['sym_seq'])
    
    print(f"  Number of n-gram features: {X_train_ngrams.shape[1]}")
    
    # Train logistic regression
    model = LogisticRegression(max_iter=1000, random_state=42, C=0.1)
    model.fit(X_train_ngrams, y_train)
    
    # Predict on validation
    y_val_pred = model.predict_proba(X_val_ngrams)[:, 1]
    val_auc = roc_auc_score(y_val, y_val_pred)
    
    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_ngrams, y_train, 
                                 cv=cv, scoring='roc_auc', n_jobs=-1)
    
    print(f"  Validation AUC: {val_auc:.4f}")
    print(f"  CV AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    
    # Store results
    results_ngrams[ngram_range] = {
        'vectorizer': vectorizer,
        'model': model,
        'val_auc': val_auc,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'n_features': X_train_ngrams.shape[1]
    }

# Find best n-gram range
best_ngram_range = max(results_ngrams, key=lambda x: results_ngrams[x]['val_auc'])
best_ngram_result = results_ngrams[best_ngram_range]
print(f"\nBest n-gram range: {best_ngram_range} with Validation AUC: {best_ngram_result['val_auc']:.4f}")

# Evaluate best n-gram model on test
X_test_best_ngrams = results_ngrams[best_ngram_range]['vectorizer'].transform(test['sym_seq'])
y_test_pred_ngrams = results_ngrams[best_ngram_range]['model'].predict_proba(X_test_best_ngrams)[:, 1]
test_auc_ngrams = roc_auc_score(y_test, y_test_pred_ngrams)
print(f"Test AUC with best n-grams: {test_auc_ngrams:.4f}")

# Approach 2: TF-IDF on n-grams
print("\n--- TF-IDF on N-grams ---")

# Use best n-gram range from previous step
tfidf_vectorizer = TfidfVectorizer(analyzer='char', ngram_range=best_ngram_range)
X_train_tfidf = tfidf_vectorizer.fit_transform(train['sym_seq'])
X_val_tfidf = tfidf_vectorizer.transform(val['sym_seq'])
X_test_tfidf = tfidf_vectorizer.transform(test['sym_seq'])

print(f"Number of TF-IDF features: {X_train_tfidf.shape[1]}")

# Train logistic regression with TF-IDF
model_tfidf = LogisticRegression(max_iter=1000, random_state=42, C=0.1)
model_tfidf.fit(X_train_tfidf, y_train)

y_val_pred_tfidf = model_tfidf.predict_proba(X_val_tfidf)[:, 1]
val_auc_tfidf = roc_auc_score(y_val, y_val_pred_tfidf)

cv_scores_tfidf = cross_val_score(model_tfidf, X_train_tfidf, y_train, 
                                   cv=5, scoring='roc_auc', n_jobs=-1)

print(f"Validation AUC with TF-IDF: {val_auc_tfidf:.4f}")
print(f"CV AUC: {cv_scores_tfidf.mean():.4f} (+/- {cv_scores_tfidf.std()*2:.4f})")

# Evaluate TF-IDF on test
y_test_pred_tfidf = model_tfidf.predict_proba(X_test_tfidf)[:, 1]
test_auc_tfidf = roc_auc_score(y_test, y_test_pred_tfidf)
print(f"Test AUC with TF-IDF: {test_auc_tfidf:.4f}")

# Approach 3: Position-specific one-hot encoding
print("\n--- Position-Specific Encoding ---")

# Create position-specific one-hot encoding (20 positions × 6 symbols = 120 features)
def position_one_hot(sequences):
    n_samples = len(sequences)
    n_features = 20 * 6  # 20 positions × 6 symbols
    X = np.zeros((n_samples, n_features))
    
    symbol_to_idx = {'1': 0, '2': 1, 'A': 2, 'B': 3, 'C': 4, 'D': 5}
    
    for i, seq in enumerate(sequences):
        for pos, symbol in enumerate(seq):
            feature_idx = pos * 6 + symbol_to_idx[symbol]
            X[i, feature_idx] = 1
    
    return X

X_train_pos = position_one_hot(train['sym_seq'])
X_val_pos = position_one_hot(val['sym_seq'])
X_test_pos = position_one_hot(test['sym_seq'])

print(f"Position encoding features: {X_train_pos.shape[1]}")

# Train model on position encoding
model_pos = LogisticRegression(max_iter=1000, random_state=42, C=0.01)
model_pos.fit(X_train_pos, y_train)

y_val_pred_pos = model_pos.predict_proba(X_val_pos)[:, 1]
val_auc_pos = roc_auc_score(y_val, y_val_pred_pos)

cv_scores_pos = cross_val_score(model_pos, X_train_pos, y_train, 
                                 cv=5, scoring='roc_auc', n_jobs=-1)

print(f"Validation AUC with position encoding: {val_auc_pos:.4f}")
print(f"CV AUC: {cv_scores_pos.mean():.4f} (+/- {cv_scores_pos.std()*2:.4f})")

# Evaluate position encoding on test
y_test_pred_pos = model_pos.predict_proba(X_test_pos)[:, 1]
test_auc_pos = roc_auc_score(y_test, y_test_pred_pos)
print(f"Test AUC with position encoding: {test_auc_pos:.4f}")

# Compare all approaches
baseline_auc = 0.72
print(f"\n=== Summary ===")
print(f"Baseline AUC: {baseline_auc:.4f}")
print(f"Best n-grams ({best_ngram_range}): Test AUC = {test_auc_ngrams:.4f} (Δ = {test_auc_ngrams - baseline_auc:.4f})")
print(f"TF-IDF: Test AUC = {test_auc_tfidf:.4f} (Δ = {test_auc_tfidf - baseline_auc:.4f})")
print(f"Position encoding: Test AUC = {test_auc_pos:.4f} (Δ = {test_auc_pos - baseline_auc:.4f})")

# Create visualization
os.makedirs('../report/images', exist_ok=True)

plt.figure(figsize=(10, 6))
methods = ['N-grams', 'TF-IDF', 'Position Encoding']
test_aucs = [test_auc_ngrams, test_auc_tfidf, test_auc_pos]
val_aucs = [best_ngram_result['val_auc'], val_auc_tfidf, val_auc_pos]

x = np.arange(len(methods))
width = 0.35

bars1 = plt.bar(x - width/2, val_aucs, width, label='Validation AUC', color='skyblue')
bars2 = plt.bar(x + width/2, test_aucs, width, label='Test AUC', color='lightgreen')
plt.axhline(y=baseline_auc, color='red', linestyle='--', label=f'Baseline AUC={baseline_auc}')

plt.xlabel('Method')
plt.ylabel('AUC')
plt.title('Sequence Modeling Approaches')
plt.xticks(x, methods)
plt.legend()
plt.ylim(0.3, 0.8)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                 f'{height:.3f}', ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('../report/images/sequence_methods_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualization saved to report/images/sequence_methods_comparison.png")

# Save results
with open('../outputs/sequence_modeling_results.txt', 'w') as f:
    f.write("Sequence Modeling Results\n")
    f.write("="*50 + "\n\n")
    f.write(f"Baseline AUC: {baseline_auc:.4f}\n\n")
    
    f.write("N-gram Results:\n")
    for ngram_range, result in results_ngrams.items():
        f.write(f"  {ngram_range}: Val AUC={result['val_auc']:.4f}, "
                f"CV AUC={result['cv_mean']:.4f}, Features={result['n_features']}\n")
    
    f.write(f"\nBest n-gram range: {best_ngram_range}\n")
    f.write(f"Test AUC with best n-grams: {test_auc_ngrams:.4f}\n")
    f.write(f"Difference from baseline: {test_auc_ngrams - baseline_auc:.4f}\n\n")
    
    f.write(f"TF-IDF Results:\n")
    f.write(f"  Validation AUC: {val_auc_tfidf:.4f}\n")
    f.write(f"  Test AUC: {test_auc_tfidf:.4f}\n")
    f.write(f"  Difference from baseline: {test_auc_tfidf - baseline_auc:.4f}\n\n")
    
    f.write(f"Position Encoding Results:\n")
    f.write(f"  Validation AUC: {val_auc_pos:.4f}\n")
    f.write(f"  Test AUC: {test_auc_pos:.4f}\n")
    f.write(f"  Difference from baseline: {test_auc_pos - baseline_auc:.4f}\n")

print("\n=== Sequence Modeling Complete ===")