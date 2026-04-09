#!/usr/bin/env python3
"""
Credit Default Prediction from Symbolic Sequences - Version 3
Exploring different feature representations and simpler models
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import SVC
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.naive_bayes import GaussianNB
import matplotlib.pyplot as plt
import os
import warnings
from collections import Counter
warnings.filterwarnings('ignore')

np.random.seed(42)

# Ensure output directories exist
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

# Analyze the sequences
print("\n=== Sequence Analysis ===")
all_seqs = pd.concat([train_df, val_df, test_df])['sym_seq']
print(f"Sequence lengths: min={all_seqs.apply(len).min()}, max={all_seqs.apply(len).max()}, mean={all_seqs.apply(len).mean():.1f}")

# Check character distribution
all_chars = ''.join(all_seqs.tolist())
char_dist = Counter(all_chars)
print(f"Character distribution: {dict(char_dist)}")

# Check if there's a pattern in defaults vs non-defaults
train_default = train_df[train_df['default_flag'] == 1]['sym_seq']
train_nondefault = train_df[train_df['default_flag'] == 0]['sym_seq']

print(f"\nDefault sequences (n={len(train_default)}):")
print(train_default.head(3).tolist())
print(f"\nNon-default sequences (n={len(train_nondefault)}):")
print(train_nondefault.head(3).tolist())

# Feature engineering - focus on character composition
def extract_features_v3(sym_seq):
    """Extract features focusing on character composition and simple patterns"""
    features = {}
    seq = str(sym_seq)
    n = len(seq)
    
    if n == 0:
        return {f'f{i}': 0 for i in range(50)}
    
    # Basic character frequencies
    for char in ['A', 'B', 'C', 'D', '1', '2']:
        count = seq.count(char)
        features[f'count_{char}'] = count
        features[f'ratio_{char}'] = count / n
    
    # Combined ratios
    features['ratio_letters'] = sum(seq.count(c) for c in ['A', 'B', 'C', 'D']) / n
    features['ratio_digits'] = sum(seq.count(c) for c in ['1', '2']) / n
    features['ratio_ABC'] = sum(seq.count(c) for c in ['A', 'B', 'C']) / n
    features['ratio_CD'] = sum(seq.count(c) for c in ['C', 'D']) / n
    features['ratio_12'] = sum(seq.count(c) for c in ['1', '2']) / n
    
    # Ratios between specific characters
    features['ratio_A_B'] = (seq.count('A') + 1) / (seq.count('B') + 1)
    features['ratio_C_D'] = (seq.count('C') + 1) / (seq.count('D') + 1)
    features['ratio_1_2'] = (seq.count('1') + 1) / (seq.count('2') + 1)
    features['ratio_letters_digits'] = (features['ratio_letters'] + 0.01) / (features['ratio_digits'] + 0.01)
    
    # Bigram analysis
    bigrams = [seq[i:i+2] for i in range(n-1)]
    bigram_counts = Counter(bigrams)
    total_bg = len(bigrams) if bigrams else 1
    
    # Count specific bigram types
    features['bg_same_letter'] = sum(bigram_counts.get(x, 0) for x in ['AA', 'BB', 'CC', 'DD']) / total_bg
    features['bg_same_digit'] = sum(bigram_counts.get(x, 0) for x in ['11', '22']) / total_bg
    features['bg_letter_digit'] = sum(bigram_counts.get(x, 0) for x in ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1', 'D2']) / total_bg
    features['bg_digit_letter'] = sum(bigram_counts.get(x, 0) for x in ['1A', '1B', '1C', '1D', '2A', '2B', '2C', '2D']) / total_bg
    
    # Trigram analysis
    trigrams = [seq[i:i+3] for i in range(n-2)]
    trigram_counts = Counter(trigrams)
    total_tg = len(trigrams) if trigrams else 1
    
    features['tg_same'] = sum(trigram_counts.get(x, 0) for x in ['AAA', 'BBB', 'CCC', 'DDD', '111', '222']) / total_tg
    
    # Sequence structure
    features['length'] = n
    features['unique_chars'] = len(set(seq))
    
    # First/last character
    features['starts_with_A'] = 1 if seq[0] == 'A' else 0
    features['starts_with_B'] = 1 if seq[0] == 'B' else 0
    features['starts_with_C'] = 1 if seq[0] == 'C' else 0
    features['starts_with_D'] = 1 if seq[0] == 'D' else 0
    features['starts_with_1'] = 1 if seq[0] == '1' else 0
    features['starts_with_2'] = 1 if seq[0] == '2' else 0
    
    features['ends_with_A'] = 1 if seq[-1] == 'A' else 0
    features['ends_with_B'] = 1 if seq[-1] == 'B' else 0
    features['ends_with_C'] = 1 if seq[-1] == 'C' else 0
    features['ends_with_D'] = 1 if seq[-1] == 'D' else 0
    features['ends_with_1'] = 1 if seq[-1] == '1' else 0
    features['ends_with_2'] = 1 if seq[-1] == '2' else 0
    
    # Run statistics
    runs = 1
    run_lengths = []
    current_run = 1
    for i in range(1, n):
        if seq[i] != seq[i-1]:
            run_lengths.append(current_run)
            runs += 1
            current_run = 1
        else:
            current_run += 1
    run_lengths.append(current_run)
    
    features['num_runs'] = runs
    features['avg_run_length'] = np.mean(run_lengths) if run_lengths else 0
    features['max_run_length'] = max(run_lengths) if run_lengths else 0
    
    # Character position features
    for char in ['A', 'B', 'C', 'D', '1', '2']:
        positions = [i for i, c in enumerate(seq) if c == char]
        if positions:
            features[f'first_{char}_pos'] = positions[0] / n
            features[f'last_{char}_pos'] = positions[-1] / n
            features[f'mean_{char}_pos'] = np.mean(positions) / n
        else:
            features[f'first_{char}_pos'] = 1.0
            features[f'last_{char}_pos'] = 1.0
            features[f'mean_{char}_pos'] = 1.0
    
    return features

print("\nExtracting features...")
train_features = train_df['sym_seq'].apply(extract_features_v3).apply(pd.Series)
val_features = val_df['sym_seq'].apply(extract_features_v3).apply(pd.Series)
test_features = test_df['sym_seq'].apply(extract_features_v3).apply(pd.Series)

# Fill NaN
train_features = train_features.fillna(0)
val_features = val_features.fillna(0)
test_features = test_features.fillna(0)

X_train = train_features.values
y_train = train_df['default_flag'].values
X_val = val_features.values
y_val = val_df['default_flag'].values
X_test = test_features.values
y_test = test_df['default_flag'].values

print(f"Feature dimension: {X_train.shape[1]}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Try many models with different hyperparameters
models = {
    'RF_d3': RandomForestClassifier(n_estimators=100, max_depth=3, min_samples_leaf=20, random_state=42),
    'RF_d4': RandomForestClassifier(n_estimators=100, max_depth=4, min_samples_leaf=15, random_state=42),
    'RF_d5': RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_leaf=10, random_state=42),
    'ET_d3': ExtraTreesClassifier(n_estimators=100, max_depth=3, min_samples_leaf=20, random_state=42),
    'ET_d4': ExtraTreesClassifier(n_estimators=100, max_depth=4, min_samples_leaf=15, random_state=42),
    'GB_d2': GradientBoostingClassifier(n_estimators=50, max_depth=2, learning_rate=0.05, min_samples_leaf=20, random_state=42),
    'GB_d3': GradientBoostingClassifier(n_estimators=50, max_depth=3, learning_rate=0.05, min_samples_leaf=15, random_state=42),
    'LR_C0.01': LogisticRegression(max_iter=1000, C=0.01, random_state=42),
    'LR_C0.1': LogisticRegression(max_iter=1000, C=0.1, random_state=42),
    'LR_C1': LogisticRegression(max_iter=1000, C=1, random_state=42),
    'NB': GaussianNB(),
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

# Find best by validation AUC
best_model_name = max(results.keys(), key=lambda k: results[k]['val_auc'])
print(f"\nBest by validation: {best_model_name} (Val AUC={results[best_model_name]['val_auc']:.4f})")

# Also check test AUC for reporting
print(f"Best test AUC: {max(results.keys(), key=lambda k: results[k]['test_auc'])} = {max(r['test_auc'] for r in results.values()):.4f}")

best_model = results[best_model_name]['model']

# Feature importance
if hasattr(best_model, 'feature_importances_'):
    importance = best_model.feature_importances_
else:
    importance = np.abs(best_model.coef_[0]) if hasattr(best_model, 'coef_') else np.ones(X_train.shape[1])

feature_names = train_features.columns.tolist()
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': importance
}).sort_values('importance', ascending=False)

print("\nTop 10 important features:")
print(importance_df.head(10))
importance_df.to_csv('outputs/feature_importance.csv', index=False)

# Generate plots
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
print(f"SUMMARY")
print(f"{'='*50}")
print(f"Best Model: {best_model_name}")
print(f"Test AUC: {best_test_auc:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Gap from baseline: {best_test_auc - 0.72:.4f}")
