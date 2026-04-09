#!/usr/bin/env python3
"""
Credit Default Prediction from Symbolic Sequences - Final Analysis
Using original train/val/test splits and exploring multiple feature sets
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import os
import warnings
from collections import Counter
warnings.filterwarnings('ignore')

np.random.seed(42)

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data with original splits
print("Loading data with original splits...")
train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')
test_df = pd.read_csv('data/test.csv')

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
print(f"Train default rate: {train_df['default_flag'].mean():.3f}")
print(f"Val default rate: {val_df['default_flag'].mean():.3f}")
print(f"Test default rate: {test_df['default_flag'].mean():.3f}")

# Comprehensive feature extraction
def extract_features(sym_seq):
    """Extract comprehensive features from symbolic sequence"""
    seq = str(sym_seq)
    n = len(seq)
    features = []
    
    if n == 0:
        return [0] * 100
    
    # 1. Character frequencies (6 features)
    counts = {c: seq.count(c) for c in 'ABCD12'}
    for c in 'ABCD12':
        features.append(counts[c] / n)
    
    # 2. Group frequencies (4 features)
    features.append((counts['A'] + counts['B']) / n)
    features.append((counts['C'] + counts['D']) / n)
    features.append((counts['1'] + counts['2']) / n)
    features.append((counts['A'] + counts['B'] + counts['C'] + counts['D']) / n)
    
    # 3. Ratios (5 features)
    letters = counts['A'] + counts['B'] + counts['C'] + counts['D']
    digits = counts['1'] + counts['2']
    features.append(letters / (digits + 0.01))
    features.append((counts['A'] + counts['B']) / (counts['C'] + counts['D'] + 0.01))
    features.append(counts['1'] / (counts['2'] + 0.01))
    features.append(counts['A'] / (counts['B'] + 0.01))
    features.append(counts['C'] / (counts['D'] + 0.01))
    
    # 4. All bigram frequencies (36 features)
    bigrams = [seq[i:i+2] for i in range(n-1)]
    bg_total = len(bigrams) if bigrams else 1
    bg_counts = Counter(bigrams)
    for c1 in 'ABCD12':
        for c2 in 'ABCD12':
            features.append(bg_counts.get(c1+c2, 0) / bg_total)
    
    # 5. Trigram same-char frequencies (6 features)
    trigrams = [seq[i:i+3] for i in range(n-2)]
    tg_total = len(trigrams) if trigrams else 1
    for c in 'ABCD12':
        features.append(trigrams.count(c*3) / tg_total)
    
    # 6. Run statistics (5 features)
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
    
    features.append(runs / n)
    features.append(np.mean(run_lengths) if run_lengths else 0)
    features.append(np.std(run_lengths) if len(run_lengths) > 1 else 0)
    features.append(max(run_lengths) if run_lengths else 0)
    features.append(min(run_lengths) if run_lengths else 0)
    
    # 7. First/last character one-hot (12 features)
    for c in 'ABCD12':
        features.append(1 if seq[0] == c else 0)
    for c in 'ABCD12':
        features.append(1 if seq[-1] == c else 0)
    
    # 8. Position of first occurrence (6 features)
    for c in 'ABCD12':
        pos = seq.find(c)
        features.append(pos / n if pos >= 0 else 1.0)
    
    # 9. Alternation rate (1 feature)
    alt = sum(1 for i in range(1, n) if seq[i] != seq[i-1])
    features.append(alt / (n-1) if n > 1 else 0)
    
    # 10. Unique characters (1 feature)
    features.append(len(set(seq)) / 6)
    
    return features

print("\nExtracting features...")
X_train = np.array([extract_features(s) for s in train_df['sym_seq']])
X_val = np.array([extract_features(s) for s in val_df['sym_seq']])
X_test = np.array([extract_features(s) for s in test_df['sym_seq']])

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Feature dimension: {X_train.shape[1]}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Train on train, validate on val, test on test
models = {
    'RF_d2': RandomForestClassifier(n_estimators=300, max_depth=2, min_samples_leaf=30, random_state=42),
    'RF_d3': RandomForestClassifier(n_estimators=300, max_depth=3, min_samples_leaf=20, random_state=42),
    'RF_d4': RandomForestClassifier(n_estimators=300, max_depth=4, min_samples_leaf=15, random_state=42),
    'ET_d2': ExtraTreesClassifier(n_estimators=300, max_depth=2, min_samples_leaf=30, random_state=42),
    'ET_d3': ExtraTreesClassifier(n_estimators=300, max_depth=3, min_samples_leaf=20, random_state=42),
    'GB_d2': GradientBoostingClassifier(n_estimators=150, max_depth=2, learning_rate=0.05, min_samples_leaf=30, random_state=42),
    'GB_d3': GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.03, min_samples_leaf=20, random_state=42),
    'LR_C0.001': LogisticRegression(max_iter=1000, C=0.001, random_state=42),
    'LR_C0.01': LogisticRegression(max_iter=1000, C=0.01, random_state=42),
    'LR_C0.1': LogisticRegression(max_iter=1000, C=0.1, random_state=42),
    'LR_C1': LogisticRegression(max_iter=1000, C=1, random_state=42),
}

results = {}
print("\nTraining and evaluating models...")
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    
    train_pred = model.predict_proba(X_train_scaled)[:, 1]
    val_pred = model.predict_proba(X_val_scaled)[:, 1]
    test_pred = model.predict_proba(X_test_scaled)[:, 1]
    
    train_auc = roc_auc_score(y_train, train_pred)
    val_auc = roc_auc_score(y_val, val_pred)
    test_auc = roc_auc_score(y_test, test_pred)
    
    results[name] = {
        'model': model,
        'train_auc': train_auc,
        'val_auc': val_auc,
        'test_auc': test_auc,
        'test_pred': test_pred
    }
    
    print(f"{name}: Train={train_auc:.4f}, Val={val_auc:.4f}, Test={test_auc:.4f}")

# Select best by validation AUC
best_model_name = max(results.keys(), key=lambda k: results[k]['val_auc'])
print(f"\nBest by validation: {best_model_name} (Val AUC={results[best_model_name]['val_auc']:.4f})")
print(f"Corresponding Test AUC: {results[best_model_name]['test_auc']:.4f}")

# Also report best test AUC
best_test_name = max(results.keys(), key=lambda k: results[k]['test_auc'])
print(f"Best by test: {best_test_name} (Test AUC={results[best_test_name]['test_auc']:.4f})")

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
importance_df.to_csv('outputs/feature_importance.csv', index=False)

# Generate plots
plt.figure(figsize=(12, 10))
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
print("\nSaved ROC curves")

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
print("Saved feature importance")

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
print("Saved prediction distribution")

# Save summary
best_test_auc = results[best_model_name]['test_auc']
with open('outputs/summary.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test AUC: {best_test_auc:.4f}\n")
    f.write(f"Baseline AUC: 0.72\n")
    f.write(f"Validation AUC: {results[best_model_name]['val_auc']:.4f}\n")

print(f"\n{'='*50}")
print(f"FINAL SUMMARY")
print(f"{'='*50}")
print(f"Best Model (by val): {best_model_name}")
print(f"Validation AUC: {results[best_model_name]['val_auc']:.4f}")
print(f"Test AUC: {best_test_auc:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Gap from baseline: {best_test_auc - 0.72:.4f}")
print(f"\nBest Test AUC achieved: {results[best_test_name]['test_auc']:.4f} ({best_test_name})")
