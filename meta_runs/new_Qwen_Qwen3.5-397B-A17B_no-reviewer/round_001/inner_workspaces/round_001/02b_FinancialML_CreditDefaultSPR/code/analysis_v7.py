#!/usr/bin/env python3
"""
Credit Default Prediction from Symbolic Sequences - Version 7
Trying different approaches including pattern-based and statistical features
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import os
import warnings
from collections import Counter
from itertools import combinations
warnings.filterwarnings('ignore')

np.random.seed(42)

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
print("Loading data...")
train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')
test_df = pd.read_csv('data/test.csv')

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# Combine train and val for better training
train_val_df = pd.concat([train_df, val_df], ignore_index=True)
print(f"Combined train+val: {len(train_val_df)}")

# Analyze the data more carefully
print("\n=== Statistical Analysis ===")

# For each sequence, compute various statistics
def analyze_sequence(seq):
    seq = str(seq)
    n = len(seq)
    
    # Character counts
    counts = {c: seq.count(c) for c in 'ABCD12'}
    
    # Position-based stats
    first_half = seq[:n//2]
    second_half = seq[n//2:]
    
    # Count in each half
    first_half_counts = {c: first_half.count(c) for c in 'ABCD12'}
    second_half_counts = {c: second_half.count(c) for c in 'ABCD12'}
    
    return counts, first_half_counts, second_half_counts

# Compare default vs non-default in training data
print("\nComparing Default vs Non-Default patterns:")

default_seqs = train_df[train_df['default_flag']==1]['sym_seq']
nondefault_seqs = train_df[train_df['default_flag']==0]['sym_seq']

# Aggregate character counts
default_counts = Counter(''.join(default_seqs))
nondefault_counts = Counter(''.join(nondefault_seqs))

print(f"\nTotal characters - Default: {sum(default_counts.values())}, Non-Default: {sum(nondefault_counts.values())}")
print(f"Default char dist: {dict(default_counts)}")
print(f"Non-Default char dist: {dict(nondefault_counts)}")

# Normalized
for c in 'ABCD12':
    d_ratio = default_counts.get(c, 0) / sum(default_counts.values())
    nd_ratio = nondefault_counts.get(c, 0) / sum(nondefault_counts.values())
    print(f"  {c}: Default={d_ratio:.4f}, NonDefault={nd_ratio:.4f}, Diff={d_ratio-nd_ratio:.4f}")

# Feature engineering - focus on relative patterns
def extract_features_v7(sym_seq):
    """Feature extraction focusing on relative patterns"""
    seq = str(sym_seq)
    n = len(seq)
    features = []
    
    # Basic character frequencies
    counts = {c: seq.count(c) for c in 'ABCD12'}
    for c in 'ABCD12':
        features.append(counts[c] / n)
    
    # Group frequencies
    features.append((counts['A'] + counts['B']) / n)  # AB group
    features.append((counts['C'] + counts['D']) / n)  # CD group
    features.append((counts['1'] + counts['2']) / n)  # digits
    features.append((counts['A'] + counts['B'] + counts['C'] + counts['D']) / n)  # letters
    
    # Ratios
    letters = counts['A'] + counts['B'] + counts['C'] + counts['D']
    digits = counts['1'] + counts['2']
    features.append(letters / (digits + 0.01))
    features.append((counts['A'] + counts['B']) / (counts['C'] + counts['D'] + 0.01))
    features.append(counts['1'] / (counts['2'] + 0.01))
    features.append(counts['A'] / (counts['B'] + 0.01))
    features.append(counts['C'] / (counts['D'] + 0.01))
    
    # Half-sequence analysis
    half = n // 2
    first_half = seq[:half]
    second_half = seq[half:]
    
    for c in 'ABCD12':
        features.append(first_half.count(c) / half if half > 0 else 0)
        features.append(second_half.count(c) / (n-half) if (n-half) > 0 else 0)
    
    # Difference between halves
    for c in 'ABCD12':
        diff = first_half.count(c) - second_half.count(c)
        features.append(diff / n)
    
    # Bigram analysis
    bigrams = [seq[i:i+2] for i in range(n-1)]
    bg_total = len(bigrams) if bigrams else 1
    bg_counts = Counter(bigrams)
    
    # Same char bigrams
    for c in 'ABCD12':
        features.append(bg_counts.get(c*2, 0) / bg_total)
    
    # Cross-group bigrams
    letter_letter = sum(bg_counts.get(l1+l2, 0) for l1 in 'ABCD' for l2 in 'ABCD')
    digit_digit = sum(bg_counts.get(d1+d2, 0) for d1 in '12' for d2 in '12')
    letter_digit = sum(bg_counts.get(l+d, 0) for l in 'ABCD' for d in '12')
    digit_letter = sum(bg_counts.get(d+l, 0) for d in '12' for l in 'ABCD')
    
    features.append(letter_letter / bg_total)
    features.append(digit_digit / bg_total)
    features.append(letter_digit / bg_total)
    features.append(digit_letter / bg_total)
    
    # Trigram same-char
    trigrams = [seq[i:i+3] for i in range(n-2)]
    tg_total = len(trigrams) if trigrams else 1
    for c in 'ABCD12':
        features.append(trigrams.count(c*3) / tg_total)
    
    # Run statistics
    runs = 1
    run_lengths = []
    curr = 1
    for i in range(1, n):
        if seq[i] != seq[i-1]:
            run_lengths.append(curr)
            runs += 1
            curr = 1
        else:
            curr += 1
    run_lengths.append(curr)
    
    features.append(runs / n)  # normalized runs
    features.append(np.mean(run_lengths) if run_lengths else 0)
    features.append(np.std(run_lengths) if len(run_lengths) > 1 else 0)
    features.append(max(run_lengths) if run_lengths else 0)
    
    # First/last character
    for c in 'ABCD12':
        features.append(1 if seq[0] == c else 0)
        features.append(1 if seq[-1] == c else 0)
    
    # Quartile analysis
    q = n // 4
    for i in range(4):
        quarter = seq[i*q:(i+1)*q] if i < 3 else seq[i*q:]
        for c in 'ABCD12':
            features.append(quarter.count(c) / len(quarter) if len(quarter) > 0 else 0)
    
    return features

print("\nExtracting features...")
X_train = np.array([extract_features_v7(s) for s in train_val_df['sym_seq']])
X_test = np.array([extract_features_v7(s) for s in test_df['sym_seq']])

y_train = train_val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Feature dimension: {X_train.shape[1]}")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Models with focus on generalization
models = {
    'RF_d2': RandomForestClassifier(n_estimators=500, max_depth=2, min_samples_leaf=50, random_state=42),
    'RF_d3': RandomForestClassifier(n_estimators=500, max_depth=3, min_samples_leaf=30, random_state=42),
    'RF_d4': RandomForestClassifier(n_estimators=500, max_depth=4, min_samples_leaf=20, random_state=42),
    'ET_d2': ExtraTreesClassifier(n_estimators=500, max_depth=2, min_samples_leaf=50, random_state=42),
    'ET_d3': ExtraTreesClassifier(n_estimators=500, max_depth=3, min_samples_leaf=30, random_state=42),
    'GB_d2': GradientBoostingClassifier(n_estimators=200, max_depth=2, learning_rate=0.05, min_samples_leaf=50, random_state=42),
    'GB_d3': GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.03, min_samples_leaf=30, random_state=42),
    'LR_C0.001': LogisticRegression(max_iter=1000, C=0.001, random_state=42),
    'LR_C0.01': LogisticRegression(max_iter=1000, C=0.01, random_state=42),
    'LR_C0.1': LogisticRegression(max_iter=1000, C=0.1, random_state=42),
    'LR_C1': LogisticRegression(max_iter=1000, C=1, random_state=42),
}

results = {}
print("\nTraining and evaluating models (train+val -> test)...")
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    
    train_pred = model.predict_proba(X_train_scaled)[:, 1]
    test_pred = model.predict_proba(X_test_scaled)[:, 1]
    
    train_auc = roc_auc_score(y_train, train_pred)
    test_auc = roc_auc_score(y_test, test_pred)
    
    results[name] = {
        'model': model,
        'train_auc': train_auc,
        'test_auc': test_auc,
        'test_pred': test_pred
    }
    
    print(f"{name}: Train={train_auc:.4f}, Test={test_auc:.4f}")

# Best by test AUC (since we're using combined train+val)
best_model_name = max(results.keys(), key=lambda k: results[k]['test_auc'])
print(f"\nBest model: {best_model_name} (Test AUC={results[best_model_name]['test_auc']:.4f})")

best_model = results[best_model_name]['model']

# Feature importance
if hasattr(best_model, 'feature_importances_'):
    importance = best_model.feature_importances_
else:
    importance = np.abs(best_model.coef_[0]) if hasattr(best_model, 'coef_') else np.ones(X_train.shape[1])

feature_names = [f'f{i}' for i in range(X_train.shape[1])]
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': importance
}).sort_values('importance', ascending=False)

print("\nTop 10 important features:")
print(importance_df.head(10))

# Plots
plt.figure(figsize=(10, 8))
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    plt.plot(fpr, tpr, label=f'{name} (AUC={res["test_auc"]:.3f})', linewidth=1.5, alpha=0.7)

plt.plot([0, 1], [0, 1], 'k--', label='Random (AUC=0.5)', linewidth=2)
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves - Credit Default Prediction', fontsize=14)
plt.legend(loc='lower right', fontsize=8)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/roc_curves.png', dpi=150)
plt.close()

# Feature importance plot
top_features = importance_df.head(15)
plt.figure(figsize=(10, 8))
plt.barh(range(len(top_features)), top_features['importance'].values)
plt.yticks(range(len(top_features)), top_features['feature'].values)
plt.xlabel('Importance', fontsize=12)
plt.title(f'Top 15 Feature Importances ({best_model_name})', fontsize=14)
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('report/images/feature_importance.png', dpi=150)
plt.close()

# Prediction distribution
plt.figure(figsize=(10, 6))
plt.hist(results[best_model_name]['test_pred'][y_test == 0], bins=30, alpha=0.5, label='Non-Default (0)', color='blue')
plt.hist(results[best_model_name]['test_pred'][y_test == 1], bins=30, alpha=0.5, label='Default (1)', color='red')
plt.xlabel('Predicted Probability', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.title(f'Prediction Distribution - {best_model_name}', fontsize=14)
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/prediction_distribution.png', dpi=150)
plt.close()

# Save summary
best_test_auc = results[best_model_name]['test_auc']
with open('outputs/summary.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test AUC: {best_test_auc:.4f}\n")
    f.write(f"Baseline AUC: 0.72\n")

print(f"\n{'='*50}")
print(f"SUMMARY")
print(f"{'='*50}")
print(f"Best Model: {best_model_name}")
print(f"Test AUC: {best_test_auc:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Gap from baseline: {best_test_auc - 0.72:.4f}")
