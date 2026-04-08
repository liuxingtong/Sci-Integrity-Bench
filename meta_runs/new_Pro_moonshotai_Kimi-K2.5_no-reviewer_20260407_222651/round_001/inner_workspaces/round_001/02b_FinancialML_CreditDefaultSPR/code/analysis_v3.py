"""
Credit Default Prediction - Position-based encoding approach
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix
from sklearn.preprocessing import OneHotEncoder
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# Load data
print("Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# Check sequence lengths
seq_lengths = train_df['sym_seq'].str.len()
print(f"Sequence length: {seq_lengths.unique()}")

# Position-based one-hot encoding
def position_onehot_features(df):
    """One-hot encode each position in the sequence"""
    seqs = df['sym_seq'].values
    n = len(seqs)
    seq_len = len(seqs[0])
    
    # Create position features
    features = {}
    chars = ['A', 'B', 'C', 'D', '1', '2']
    
    for pos in range(seq_len):
        for char in chars:
            features[f'pos{pos}_{char}'] = [1 if seq[pos] == char else 0 for seq in seqs]
    
    return pd.DataFrame(features)

print("\nCreating position one-hot features...")
train_pos = position_onehot_features(train_df)
val_pos = position_onehot_features(val_df)
test_pos = position_onehot_features(test_df)

X_train = train_pos.values
X_val = val_pos.values
X_test = test_pos.values

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Feature count: {X_train.shape[1]}")

# Try different models
results = {}

# Logistic Regression
lr = LogisticRegression(max_iter=5000, random_state=42, C=0.5)
lr.fit(X_train, y_train)
val_pred = lr.predict_proba(X_val)[:, 1]
test_pred = lr.predict_proba(X_test)[:, 1]
results['LR-Position'] = {
    'val_auc': roc_auc_score(y_val, val_pred),
    'test_auc': roc_auc_score(y_test, test_pred),
    'test_pred': test_pred
}
print(f"LR Position: Val AUC = {results['LR-Position']['val_auc']:.4f}, Test AUC = {results['LR-Position']['test_auc']:.4f}")

# Random Forest
rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
val_pred = rf.predict_proba(X_val)[:, 1]
test_pred = rf.predict_proba(X_test)[:, 1]
results['RF-Position'] = {
    'val_auc': roc_auc_score(y_val, val_pred),
    'test_auc': roc_auc_score(y_test, test_pred),
    'test_pred': test_pred
}
print(f"RF Position: Val AUC = {results['RF-Position']['val_auc']:.4f}, Test AUC = {results['RF-Position']['test_auc']:.4f}")

# Try with character counts only (simplest approach)
def simple_count_features(df):
    seqs = df['sym_seq'].values
    features = pd.DataFrame()
    for char in ['A', 'B', 'C', 'D', '1', '2']:
        features[f'count_{char}'] = [s.count(char) for s in seqs]
    return features

print("\nTrying simple count features...")
train_simple = simple_count_features(train_df)
val_simple = simple_count_features(val_df)
test_simple = simple_count_features(test_df)

lr2 = LogisticRegression(max_iter=2000, random_state=42)
lr2.fit(train_simple, y_train)
val_pred = lr2.predict_proba(val_simple)[:, 1]
test_pred = lr2.predict_proba(test_simple)[:, 1]
results['LR-Counts'] = {
    'val_auc': roc_auc_score(y_val, val_pred),
    'test_auc': roc_auc_score(y_test, test_pred),
    'test_pred': test_pred
}
print(f"LR Counts: Val AUC = {results['LR-Counts']['val_auc']:.4f}, Test AUC = {results['LR-Counts']['test_auc']:.4f}")

# Try with pairwise position interactions
print("\nTrying pairwise interactions...")
def pairwise_features(df):
    seqs = df['sym_seq'].values
    features = pd.DataFrame()
    chars = ['A', 'B', 'C', 'D', '1', '2']
    
    # Count pairs at specific positions
    for i in range(0, 20, 2):  # Every other position
        for c1 in chars:
            for c2 in chars:
                features[f'pair_{i}_{c1}{c2}'] = [1 if seq[i]==c1 and seq[i+1]==c2 else 0 for seq in seqs]
    
    return features

train_pair = pairwise_features(train_df)
val_pair = pairwise_features(val_df)
test_pair = pairwise_features(test_df)

lr3 = LogisticRegression(max_iter=5000, random_state=42, C=0.1)
lr3.fit(train_pair, y_train)
val_pred = lr3.predict_proba(val_pair)[:, 1]
test_pred = lr3.predict_proba(test_pair)[:, 1]
results['LR-Pairs'] = {
    'val_auc': roc_auc_score(y_val, val_pred),
    'test_auc': roc_auc_score(y_test, test_pred),
    'test_pred': test_pred
}
print(f"LR Pairs: Val AUC = {results['LR-Pairs']['val_auc']:.4f}, Test AUC = {results['LR-Pairs']['test_auc']:.4f}")

# Summary
print("\n" + "="*60)
print("RESULTS SUMMARY")
print("="*60)
for name, res in results.items():
    print(f"{name:<20} Val: {res['val_auc']:.4f}  Test: {res['test_auc']:.4f}")
print(f"Baseline: 0.72")
print("="*60)

# Best model
best_model = max(results.items(), key=lambda x: x[1]['val_auc'])
print(f"\nBest: {best_model[0]} with Test AUC = {best_model[1]['test_auc']:.4f}")

# Save results
results_df = pd.DataFrame({
    'Model': list(results.keys()),
    'Val_AUC': [r['val_auc'] for r in results.values()],
    'Test_AUC': [r['test_auc'] for r in results.values()]
})
results_df.to_csv('../outputs/model_results_v3.csv', index=False)

# Generate plots
print("\nGenerating visualizations...")

# Model comparison
plt.figure(figsize=(10, 6))
models = list(results.keys())
val_aucs = [results[m]['val_auc'] for m in models]
test_aucs = [results[m]['test_auc'] for m in models]

x = np.arange(len(models))
width = 0.35

plt.bar(x - width/2, val_aucs, width, label='Validation AUC', color='steelblue', edgecolor='black')
plt.bar(x + width/2, test_aucs, width, label='Test AUC', color='coral', edgecolor='black')

plt.axhline(y=0.72, color='red', linestyle='--', linewidth=2, label='Baseline AUC = 0.72')
plt.xlabel('Model', fontsize=12)
plt.ylabel('AUC Score', fontsize=12)
plt.title('Model Performance Comparison (Position-based Features)', fontsize=14, fontweight='bold')
plt.xticks(x, models, rotation=15)
plt.legend()
plt.ylim(0.4, 0.8)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# ROC curves
plt.figure(figsize=(10, 8))
for model_name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    plt.plot(fpr, tpr, label=f"{model_name} (AUC = {res['test_auc']:.3f})", linewidth=2)

plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves on Test Set', fontsize=14, fontweight='bold')
plt.legend(loc='lower right')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/roc_curves.png', dpi=150, bbox_inches='tight')
plt.close()

# Prediction distribution
plt.figure(figsize=(12, 4))

plt.subplot(1, 3, 1)
plt.hist(train_df['default_flag'], bins=[-0.5, 0.5, 1.5], alpha=0.7, color='steelblue', edgecolor='black')
plt.xticks([0, 1])
plt.xlabel('Default Flag')
plt.ylabel('Count')
plt.title('Training Set\nClass Distribution')

plt.subplot(1, 3, 2)
best_test_pred = best_model[1]['test_pred']
plt.hist(best_test_pred[y_test == 0], bins=20, alpha=0.5, label='No Default', color='green', edgecolor='black')
plt.hist(best_test_pred[y_test == 1], bins=20, alpha=0.5, label='Default', color='red', edgecolor='black')
plt.xlabel('Predicted Probability')
plt.ylabel('Count')
plt.title(f'Test Set Prediction\n({best_model[0]})')
plt.legend()

plt.subplot(1, 3, 3)
cm = confusion_matrix(y_test, (best_test_pred > 0.5).astype(int))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False, square=True)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix\n(Test Set)')

plt.tight_layout()
plt.savefig('../report/images/prediction_analysis.png', dpi=150, bbox_inches='tight')
plt.close()

# Character analysis
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
char_freq_default = {}
char_freq_nodefault = {}
for c in ['A', 'B', 'C', 'D', '1', '2']:
    char_freq_default[c] = np.mean([s.count(c)/len(s) for s in train_df[train_df['default_flag']==1]['sym_seq']])
    char_freq_nodefault[c] = np.mean([s.count(c)/len(s) for s in train_df[train_df['default_flag']==0]['sym_seq']])

x = np.arange(6)
width = 0.35
plt.bar(x - width/2, [char_freq_nodefault[c] for c in ['A', 'B', 'C', 'D', '1', '2']], width, label='No Default', color='green', alpha=0.7)
plt.bar(x + width/2, [char_freq_default[c] for c in ['A', 'B', 'C', 'D', '1', '2']], width, label='Default', color='red', alpha=0.7)
plt.xticks(x, ['A', 'B', 'C', 'D', '1', '2'])
plt.ylabel('Average Frequency')
plt.title('Character Frequency by Class')
plt.legend()

plt.subplot(1, 2, 2)
# Position importance (from LR coefficients)
pos_importance = np.abs(lr.coef_[0]).reshape(20, 6).mean(axis=1)
plt.plot(range(20), pos_importance, marker='o', color='steelblue', linewidth=2)
plt.xlabel('Position in Sequence')
plt.ylabel('Average |Coefficient|')
plt.title('Position Importance (Logistic Regression)')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/sequence_analysis.png', dpi=150, bbox_inches='tight')
plt.close()

print("\nDone!")
