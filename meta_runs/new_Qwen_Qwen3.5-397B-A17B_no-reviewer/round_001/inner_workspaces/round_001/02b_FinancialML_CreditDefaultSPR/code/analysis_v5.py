#!/usr/bin/env python3
"""
Credit Default Prediction from Symbolic Sequences - Version 5
Simple character frequency features with careful regularization
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
print(f"Train default rate: {train_df['default_flag'].mean():.3f}")
print(f"Val default rate: {val_df['default_flag'].mean():.3f}")
print(f"Test default rate: {test_df['default_flag'].mean():.3f}")

# Simple feature extraction
def extract_features(sym_seq):
    """Extract simple character-based features"""
    seq = str(sym_seq)
    n = len(seq)
    features = []
    
    # Character frequencies (6 chars: A,B,C,D,1,2)
    for c in ['A', 'B', 'C', 'D', '1', '2']:
        features.append(seq.count(c) / n)
    
    # Bigram frequencies (all 36 combinations)
    bigrams = [seq[i:i+2] for i in range(n-1)]
    bg_total = len(bigrams) if bigrams else 1
    for c1 in ['A', 'B', 'C', 'D', '1', '2']:
        for c2 in ['A', 'B', 'C', 'D', '1', '2']:
            bg = c1 + c2
            features.append(bigrams.count(bg) / bg_total)
    
    # Trigram frequencies for same characters
    trigrams = [seq[i:i+3] for i in range(n-2)]
    tg_total = len(trigrams) if trigrams else 1
    for c in ['A', 'B', 'C', 'D', '1', '2']:
        tg = c * 3
        features.append(trigrams.count(tg) / tg_total)
    
    # Sequence properties
    features.append(n)  # length
    features.append(len(set(seq)))  # unique chars
    
    # Run statistics
    runs = 1
    for i in range(1, n):
        if seq[i] != seq[i-1]:
            runs += 1
    features.append(runs)
    features.append(n / runs if runs > 0 else 0)  # avg run length
    
    # First and last char (one-hot)
    for c in ['A', 'B', 'C', 'D', '1', '2']:
        features.append(1 if seq[0] == c else 0)
    for c in ['A', 'B', 'C', 'D', '1', '2']:
        features.append(1 if seq[-1] == c else 0)
    
    return features

print("\nExtracting features...")
X_train = np.array([extract_features(s) for s in train_df['sym_seq']])
X_val = np.array([extract_features(s) for s in val_df['sym_seq']])
X_test = np.array([extract_features(s) for s in test_df['sym_seq']])

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Feature dimension: {X_train.shape[1]}")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Try many models
models = {
    'RF_d2': RandomForestClassifier(n_estimators=200, max_depth=2, min_samples_leaf=30, random_state=42),
    'RF_d3': RandomForestClassifier(n_estimators=200, max_depth=3, min_samples_leaf=20, random_state=42),
    'RF_d4': RandomForestClassifier(n_estimators=200, max_depth=4, min_samples_leaf=15, random_state=42),
    'RF_d5': RandomForestClassifier(n_estimators=200, max_depth=5, min_samples_leaf=10, random_state=42),
    'ET_d2': ExtraTreesClassifier(n_estimators=200, max_depth=2, min_samples_leaf=30, random_state=42),
    'ET_d3': ExtraTreesClassifier(n_estimators=200, max_depth=3, min_samples_leaf=20, random_state=42),
    'ET_d4': ExtraTreesClassifier(n_estimators=200, max_depth=4, min_samples_leaf=15, random_state=42),
    'GB_d2': GradientBoostingClassifier(n_estimators=100, max_depth=2, learning_rate=0.05, min_samples_leaf=30, random_state=42),
    'GB_d3': GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, min_samples_leaf=20, random_state=42),
    'GB_d4': GradientBoostingClassifier(n_estimators=100, max_depth=4, learning_rate=0.03, min_samples_leaf=15, random_state=42),
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

# Best by validation
best_model_name = max(results.keys(), key=lambda k: results[k]['val_auc'])
print(f"\nBest by validation: {best_model_name} (Val AUC={results[best_model_name]['val_auc']:.4f})")
print(f"Best test AUC: {max(results.keys(), key=lambda k: results[k]['test_auc'])} = {max(r['test_auc'] for r in results.values()):.4f}")

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
    f.write(f"Validation AUC: {results[best_model_name]['val_auc']:.4f}\n")

print(f"\n{'='*50}")
print(f"SUMMARY")
print(f"{'='*50}")
print(f"Best Model: {best_model_name}")
print(f"Test AUC: {best_test_auc:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Gap from baseline: {best_test_auc - 0.72:.4f}")
