#!/usr/bin/env python3
"""
Credit Default Prediction from Symbolic Sequences
Feature engineering + ML classification with AUC evaluation
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
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

# Feature engineering from symbolic sequences
def extract_features(sym_seq):
    """Extract features from symbolic sequence"""
    features = {}
    seq = str(sym_seq)
    
    # Basic stats
    features['length'] = len(seq)
    
    # Character counts
    for char in ['A', 'B', 'C', 'D', '1', '2']:
        features[f'count_{char}'] = seq.count(char)
        features[f'ratio_{char}'] = seq.count(char) / len(seq) if len(seq) > 0 else 0
    
    # Group ratios (letters vs numbers)
    letter_count = sum(seq.count(c) for c in ['A', 'B', 'C', 'D'])
    num_count = sum(seq.count(c) for c in ['1', '2'])
    features['letter_ratio'] = letter_count / len(seq) if len(seq) > 0 else 0
    features['num_ratio'] = num_count / len(seq) if len(seq) > 0 else 0
    
    # Bigram features
    bigrams = [seq[i:i+2] for i in range(len(seq)-1)]
    for bg in ['AA', 'AB', 'AC', 'AD', 'BA', 'BB', 'BC', 'BD', 
               'CA', 'CB', 'CC', 'CD', 'DA', 'DB', 'DC', 'DD',
               '11', '12', '21', '22', 'A1', 'A2', 'B1', 'B2',
               'C1', 'C2', 'D1', 'D2', '1A', '1B', '1C', '1D',
               '2A', '2B', '2C', '2D']:
        features[f'bigram_{bg}'] = bigrams.count(bg) / len(bigrams) if len(bigrams) > 0 else 0
    
    # Trigram features (selected)
    trigrams = [seq[i:i+3] for i in range(len(seq)-2)]
    for tg in ['AAA', 'BBB', 'CCC', 'DDD', '111', '222', 'ABC', 'BCD', 'CDA', 'DAB']:
        features[f'trigram_{tg}'] = trigrams.count(tg) / len(trigrams) if len(trigrams) > 0 else 0
    
    # Position-based features
    if len(seq) > 0:
        features['first_char_A'] = 1 if seq[0] == 'A' else 0
        features['first_char_B'] = 1 if seq[0] == 'B' else 0
        features['first_char_C'] = 1 if seq[0] == 'C' else 0
        features['first_char_D'] = 1 if seq[0] == 'D' else 0
        features['first_char_1'] = 1 if seq[0] == '1' else 0
        features['first_char_2'] = 1 if seq[0] == '2' else 0
        
        features['last_char_A'] = 1 if seq[-1] == 'A' else 0
        features['last_char_B'] = 1 if seq[-1] == 'B' else 0
        features['last_char_C'] = 1 if seq[-1] == 'C' else 0
        features['last_char_D'] = 1 if seq[-1] == 'D' else 0
        features['last_char_1'] = 1 if seq[-1] == '1' else 0
        features['last_char_2'] = 1 if seq[-1] == '2' else 0
    
    # Entropy-like feature
    unique_chars = len(set(seq))
    features['unique_chars'] = unique_chars
    
    # Runs (consecutive same characters)
    runs = 1
    for i in range(1, len(seq)):
        if seq[i] != seq[i-1]:
            runs += 1
    features['num_runs'] = runs
    features['avg_run_length'] = len(seq) / runs if runs > 0 else 0
    
    return features

print("\nExtracting features...")
train_features = train_df['sym_seq'].apply(extract_features).apply(pd.Series)
val_features = val_df['sym_seq'].apply(extract_features).apply(pd.Series)
test_features = test_df['sym_seq'].apply(extract_features).apply(pd.Series)

X_train = train_features.values
y_train = train_df['default_flag'].values
X_val = val_features.values
y_val = val_df['default_flag'].values
X_test = test_features.values
y_test = test_df['default_flag'].values

print(f"Feature dimension: {X_train.shape[1]}")

# Train multiple models and evaluate
models = {
    'RandomForest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
    'GradientBoosting': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42),
    'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42)
}

results = {}
print("\nTraining and evaluating models...")
for name, model in models.items():
    model.fit(X_train, y_train)
    
    # Predictions
    train_pred = model.predict_proba(X_train)[:, 1]
    val_pred = model.predict_proba(X_val)[:, 1]
    test_pred = model.predict_proba(X_test)[:, 1]
    
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

# Feature importance (for tree-based models)
if hasattr(best_model, 'feature_importances_'):
    feature_names = train_features.columns.tolist()
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 important features:")
    print(importance_df.head(10))
    
    # Save feature importance
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
if hasattr(best_model, 'feature_importances_'):
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
