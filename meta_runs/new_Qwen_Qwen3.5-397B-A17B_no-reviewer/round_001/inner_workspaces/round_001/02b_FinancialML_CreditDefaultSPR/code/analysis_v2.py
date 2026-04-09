#!/usr/bin/env python3
"""
Credit Default Prediction from Symbolic Sequences - Version 2
Improved feature engineering with n-gram TF-IDF style features
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import os
import warnings
from collections import Counter
warnings.filterwarnings('ignore')

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

# Improved feature engineering
def extract_features_v2(sym_seq):
    """Extract features from symbolic sequence - simpler, more robust"""
    features = {}
    seq = str(sym_seq)
    n = len(seq)
    
    if n == 0:
        return {f'f{i}': 0 for i in range(20)}
    
    # Character frequencies (normalized)
    for char in ['A', 'B', 'C', 'D', '1', '2']:
        features[f'freq_{char}'] = seq.count(char) / n
    
    # Letter vs digit ratio
    letters = sum(seq.count(c) for c in ['A', 'B', 'C', 'D'])
    digits = sum(seq.count(c) for c in ['1', '2'])
    features['letter_digit_ratio'] = letters / (digits + 1e-6)
    
    # All bigram frequencies
    bigrams = [seq[i:i+2] for i in range(n-1)]
    bigram_counts = Counter(bigrams)
    total_bigrams = len(bigrams) if bigrams else 1
    
    # Key bigrams that might be informative
    key_bigrams = ['AA', 'AB', 'AC', 'AD', 'BA', 'BB', 'BC', 'BD',
                   'CA', 'CB', 'CC', 'CD', 'DA', 'DB', 'DC', 'DD',
                   '11', '12', '21', '22', 'A1', 'A2', 'B1', 'B2',
                   'C1', 'C2', 'D1', 'D2', '1A', '1B', '1C', '1D',
                   '2A', '2B', '2C', '2D']
    
    for bg in key_bigrams:
        features[f'bg_{bg}'] = bigram_counts.get(bg, 0) / total_bigrams
    
    # Trigram features for common patterns
    trigrams = [seq[i:i+3] for i in range(n-2)]
    trigram_counts = Counter(trigrams)
    total_trigrams = len(trigrams) if trigrams else 1
    
    key_trigrams = ['AAA', 'BBB', 'CCC', 'DDD', '111', '222',
                    'ABC', 'BCD', 'CDA', 'DAB', 'AB1', 'CD2']
    for tg in key_trigrams:
        features[f'tg_{tg}'] = trigram_counts.get(tg, 0) / total_trigrams
    
    # Sequence statistics
    features['length'] = n
    features['unique_chars'] = len(set(seq))
    
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
    features['min_run_length'] = min(run_lengths) if run_lengths else 0
    
    # First and last character encoding
    char_to_num = {'A': 0, 'B': 1, 'C': 2, 'D': 3, '1': 4, '2': 5}
    features['first_char'] = char_to_num.get(seq[0], -1)
    features['last_char'] = char_to_num.get(seq[-1], -1)
    
    # Position of first occurrence of each character
    for char in ['A', 'B', 'C', 'D', '1', '2']:
        pos = seq.find(char)
        features[f'first_{char}_pos'] = pos / n if pos >= 0 else 1.0
    
    # Alternation rate (how often characters change)
    alternations = sum(1 for i in range(1, n) if seq[i] != seq[i-1])
    features['alternation_rate'] = alternations / (n - 1) if n > 1 else 0
    
    return features

print("\nExtracting features...")
train_features = train_df['sym_seq'].apply(extract_features_v2).apply(pd.Series)
val_features = val_df['sym_seq'].apply(extract_features_v2).apply(pd.Series)
test_features = test_df['sym_seq'].apply(extract_features_v2).apply(pd.Series)

# Fill any NaN values
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

# Train models with regularization to prevent overfitting
models = {
    'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=4, min_samples_leaf=10, random_state=42),
    'GradientBoosting': GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, min_samples_leaf=10, random_state=42),
    'LogisticRegression': LogisticRegression(max_iter=1000, C=0.1, random_state=42),
}

results = {}
print("\nTraining and evaluating models...")
for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    
    # Predictions
    train_pred = model.predict_proba(X_train_scaled)[:, 1]
    val_pred = model.predict_proba(X_val_scaled)[:, 1]
    test_pred = model.predict_proba(X_test_scaled)[:, 1]
    
    # AUC scores
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
    
    print(f"{name}: Train AUC={train_auc:.4f}, Val AUC={val_auc:.4f}, Test AUC={test_auc:.4f}")

# Select best model based on validation AUC
best_model_name = max(results.keys(), key=lambda k: results[k]['val_auc'])
best_model = results[best_model_name]['model']
print(f"\nBest model: {best_model_name}")

# Feature importance
if hasattr(best_model, 'feature_importances_'):
    feature_names = train_features.columns.tolist()
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 important features:")
    print(importance_df.head(10))
    importance_df.to_csv('outputs/feature_importance.csv', index=False)
else:
    # For logistic regression, use absolute coefficients
    coef = np.abs(best_model.coef_[0])
    feature_names = train_features.columns.tolist()
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': coef
    }).sort_values('importance', ascending=False)
    print("\nTop 10 important features (by coefficient magnitude):")
    print(importance_df.head(10))
    importance_df.to_csv('outputs/feature_importance.csv', index=False)

# Generate ROC curves
plt.figure(figsize=(10, 8))
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    plt.plot(fpr, tpr, label=f'{name} (AUC={res["test_auc"]:.4f})', linewidth=2)

plt.plot([0, 1], [0, 1], 'k--', label='Random (AUC=0.5)')
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves - Credit Default Prediction', fontsize=14)
plt.legend(loc='lower right')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/roc_curves.png', dpi=150)
plt.close()
print("\nSaved ROC curves to report/images/roc_curves.png")

# Generate feature importance plot
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
print("Saved feature importance to report/images/feature_importance.png")

# Generate prediction distribution
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
print("Saved prediction distribution to report/images/prediction_distribution.png")

# Save predictions
pred_df = pd.DataFrame({
    'id': test_df['id'],
    'actual': y_test,
    'predicted_prob': results[best_model_name]['test_pred'],
    'predicted_class': (results[best_model_name]['test_pred'] >= 0.5).astype(int)
})
pred_df.to_csv('outputs/predictions.csv', index=False)

# Summary statistics
print("\n" + "="*50)
print("SUMMARY")
print("="*50)
print(f"Best Model: {best_model_name}")
print(f"Test AUC: {results[best_model_name]['test_auc']:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Improvement over baseline: {results[best_model_name]['test_auc'] - 0.72:.4f}")

# Save summary
with open('outputs/summary.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test AUC: {results[best_model_name]['test_auc']:.4f}\n")
    f.write(f"Baseline AUC: 0.72\n")
    f.write(f"Validation AUC: {results[best_model_name]['val_auc']:.4f}\n")

print("\nAnalysis complete!")
