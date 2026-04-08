"""
Credit Default Prediction from Symbolic Sequences - Version 2
Using TF-IDF and advanced sequence features
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# Load data
print("Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
print(f"Default rates - Train: {train_df['default_flag'].mean():.3f}, Val: {val_df['default_flag'].mean():.3f}, Test: {test_df['default_flag'].mean():.3f}")

# Advanced feature engineering
def extract_advanced_features(df):
    """Extract comprehensive features from symbolic sequences"""
    features = pd.DataFrame()
    features['id'] = df['id']
    
    seqs = df['sym_seq'].values
    
    # Basic stats
    features['length'] = [len(s) for s in seqs]
    
    # Character counts and ratios
    chars = ['A', 'B', 'C', 'D', '1', '2']
    for c in chars:
        features[f'cnt_{c}'] = [s.count(c) for s in seqs]
        features[f'ratio_{c}'] = features[f'cnt_{c}'] / features['length']
    
    # Letter vs digit ratios
    features['letter_ratio'] = sum(features[f'ratio_{c}'] for c in ['A', 'B', 'C', 'D'])
    features['digit_ratio'] = features['ratio_1'] + features['ratio_2']
    
    # Position features
    features['first_A'] = [1 if s[0] == 'A' else 0 for s in seqs]
    features['first_B'] = [1 if s[0] == 'B' else 0 for s in seqs]
    features['first_C'] = [1 if s[0] == 'C' else 0 for s in seqs]
    features['first_D'] = [1 if s[0] == 'D' else 0 for s in seqs]
    features['first_1'] = [1 if s[0] == '1' else 0 for s in seqs]
    features['first_2'] = [1 if s[0] == '2' else 0 for s in seqs]
    
    features['last_A'] = [1 if s[-1] == 'A' else 0 for s in seqs]
    features['last_B'] = [1 if s[-1] == 'B' else 0 for s in seqs]
    features['last_C'] = [1 if s[-1] == 'C' else 0 for s in seqs]
    features['last_D'] = [1 if s[-1] == 'D' else 0 for s in seqs]
    features['last_1'] = [1 if s[-1] == '1' else 0 for s in seqs]
    features['last_2'] = [1 if s[-1] == '2' else 0 for s in seqs]
    
    # Pattern features - specific combinations
    patterns = ['1A', '1B', '1C', '1D', '2A', '2B', '2C', '2D',
                'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'D1', 'D2',
                'AA', 'BB', 'CC', 'DD', '11', '22',
                'AB', 'BC', 'CD', 'BA', 'CB', 'DC']
    
    for p in patterns:
        features[f'pat_{p}'] = [s.count(p) for s in seqs]
    
    # Run features
    def count_runs(seq):
        """Count number of runs (consecutive same characters)"""
        if len(seq) <= 1:
            return 0
        runs = 1
        for i in range(1, len(seq)):
            if seq[i] != seq[i-1]:
                runs += 1
        return runs
    
    def max_run_length(seq):
        """Find maximum run length"""
        if not seq:
            return 0
        max_run = 1
        current_run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        return max_run
    
    features['num_runs'] = [count_runs(s) for s in seqs]
    features['max_run'] = [max_run_length(s) for s in seqs]
    features['avg_run'] = features['length'] / features['num_runs']
    
    # Transition features
    features['trans_LD'] = [len(re.findall(r'[ABCD][12]', s)) for s in seqs]  # Letter to Digit
    features['trans_DL'] = [len(re.findall(r'[12][ABCD]', s)) for s in seqs]  # Digit to Letter
    features['trans_LL'] = [len(re.findall(r'[ABCD][ABCD]', s)) for s in seqs]  # Letter to Letter
    features['trans_DD'] = [len(re.findall(r'[12][12]', s)) for s in seqs]  # Digit to Digit
    
    # Entropy/diversity
    features['unique_chars'] = [len(set(s)) for s in seqs]
    
    # Specific position patterns
    for i in range(min(5, min(len(s) for s in seqs))):
        for c in chars:
            features[f'pos{i}_{c}'] = [1 if len(s) > i and s[i] == c else 0 for s in seqs]
    
    return features

print("\nExtracting features...")
train_feat = extract_advanced_features(train_df)
val_feat = extract_advanced_features(val_df)
test_feat = extract_advanced_features(test_df)

# Get feature columns (exclude id)
feature_cols = [c for c in train_feat.columns if c != 'id']

X_train = train_feat[feature_cols].values
X_val = val_feat[feature_cols].values
X_test = test_feat[feature_cols].values

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Feature count: {len(feature_cols)}")

# Also try TF-IDF on character n-grams
print("\nCreating TF-IDF features...")
tfidf = TfidfVectorizer(analyzer='char', ngram_range=(2, 4), max_features=100)
X_train_tfidf = tfidf.fit_transform(train_df['sym_seq']).toarray()
X_val_tfidf = tfidf.transform(val_df['sym_seq']).toarray()
X_test_tfidf = tfidf.transform(test_df['sym_seq']).toarray()

# Combine features
X_train_combined = np.hstack([X_train, X_train_tfidf])
X_val_combined = np.hstack([X_val, X_val_tfidf])
X_test_combined = np.hstack([X_test, X_test_tfidf])

print(f"Combined feature count: {X_train_combined.shape[1]}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_combined)
X_val_scaled = scaler.transform(X_val_combined)
X_test_scaled = scaler.transform(X_test_combined)

# Train models
print("\nTraining models...")
results = {}

# 1. Logistic Regression with regularization
for C in [0.1, 1.0, 10.0]:
    lr = LogisticRegression(C=C, max_iter=2000, random_state=42, solver='lbfgs')
    lr.fit(X_train_scaled, y_train)
    val_pred = lr.predict_proba(X_val_scaled)[:, 1]
    val_auc = roc_auc_score(y_val, val_pred)
    print(f"  LR (C={C}): Val AUC = {val_auc:.4f}")

# Best LR
lr = LogisticRegression(C=1.0, max_iter=2000, random_state=42)
lr.fit(X_train_scaled, y_train)
val_pred_lr = lr.predict_proba(X_val_scaled)[:, 1]
test_pred_lr = lr.predict_proba(X_test_scaled)[:, 1]
results['Logistic Regression'] = {
    'val_auc': roc_auc_score(y_val, val_pred_lr),
    'test_auc': roc_auc_score(y_test, test_pred_lr),
    'test_pred': test_pred_lr
}

# 2. Random Forest
rf = RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_split=5, random_state=42, n_jobs=-1)
rf.fit(X_train_combined, y_train)
val_pred_rf = rf.predict_proba(X_val_combined)[:, 1]
test_pred_rf = rf.predict_proba(X_test_combined)[:, 1]
results['Random Forest'] = {
    'val_auc': roc_auc_score(y_val, val_pred_rf),
    'test_auc': roc_auc_score(y_test, test_pred_rf),
    'test_pred': test_pred_rf
}

# 3. Gradient Boosting
gb = GradientBoostingClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42)
gb.fit(X_train_combined, y_train)
val_pred_gb = gb.predict_proba(X_val_combined)[:, 1]
test_pred_gb = gb.predict_proba(X_test_combined)[:, 1]
results['Gradient Boosting'] = {
    'val_auc': roc_auc_score(y_val, val_pred_gb),
    'test_auc': roc_auc_score(y_test, test_pred_gb),
    'test_pred': test_pred_gb
}

# Print results
print("\n" + "="*60)
print("RESULTS SUMMARY")
print("="*60)
print(f"{'Model':<25} {'Val AUC':<12} {'Test AUC':<12}")
print("-"*60)
for model_name, res in results.items():
    print(f"{model_name:<25} {res['val_auc']:.4f}       {res['test_auc']:.4f}")
print("="*60)
print(f"Baseline AUC: 0.72")

# Best model
best_model = max(results.items(), key=lambda x: x[1]['val_auc'])
print(f"\nBest model: {best_model[0]}")
print(f"  Validation AUC: {best_model[1]['val_auc']:.4f}")
print(f"  Test AUC: {best_model[1]['test_auc']:.4f}")

# Save results
results_df = pd.DataFrame({
    'Model': list(results.keys()),
    'Val_AUC': [r['val_auc'] for r in results.values()],
    'Test_AUC': [r['test_auc'] for r in results.values()]
})
results_df.to_csv('../outputs/model_results_v2.csv', index=False)

# Feature importance
if best_model[0] == 'Random Forest':
    importances = rf.feature_importances_
elif best_model[0] == 'Gradient Boosting':
    importances = gb.feature_importances_
else:
    importances = np.abs(lr.coef_[0])

all_feature_names = feature_cols + [f'tfidf_{i}' for i in range(X_train_tfidf.shape[1])]
feature_importance_df = pd.DataFrame({
    'feature': all_feature_names,
    'importance': importances
}).sort_values('importance', ascending=False)
feature_importance_df.to_csv('../outputs/feature_importance_v2.csv', index=False)

print(f"\nTop 15 important features:")
print(feature_importance_df.head(15).to_string())

# Generate visualizations
print("\nGenerating visualizations...")

# 1. Model comparison
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
plt.title('Model Performance Comparison', fontsize=14, fontweight='bold')
plt.xticks(x, models)
plt.legend()
plt.ylim(0.4, 0.8)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# 2. ROC Curves
plt.figure(figsize=(10, 8))
for model_name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    plt.plot(fpr, tpr, label=f"{model_name} (AUC = {res['test_auc']:.3f})", linewidth=2)

plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier (AUC = 0.500)')
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves on Test Set', fontsize=14, fontweight='bold')
plt.legend(loc='lower right')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/roc_curves.png', dpi=150, bbox_inches='tight')
plt.close()

# 3. Feature importance (top 20)
plt.figure(figsize=(10, 10))
top_features = feature_importance_df.head(20)
colors = plt.cm.viridis(np.linspace(0, 1, len(top_features)))
plt.barh(range(len(top_features)), top_features['importance'], color=colors)
plt.yticks(range(len(top_features)), top_features['feature'])
plt.xlabel('Importance', fontsize=12)
plt.title('Top 20 Feature Importances', fontsize=14, fontweight='bold')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('../report/images/feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()

# 4. Prediction analysis
plt.figure(figsize=(15, 4))

plt.subplot(1, 4, 1)
plt.hist(train_df['default_flag'], bins=[-0.5, 0.5, 1.5], alpha=0.7, color='steelblue', edgecolor='black')
plt.xticks([0, 1])
plt.xlabel('Default Flag')
plt.ylabel('Count')
plt.title('Training Set\nClass Distribution')

plt.subplot(1, 4, 2)
best_test_pred = best_model[1]['test_pred']
plt.hist(best_test_pred[y_test == 0], bins=20, alpha=0.5, label='No Default', color='green', edgecolor='black')
plt.hist(best_test_pred[y_test == 1], bins=20, alpha=0.5, label='Default', color='red', edgecolor='black')
plt.xlabel('Predicted Probability')
plt.ylabel('Count')
plt.title(f'Test Set Prediction\n({best_model[0]})')
plt.legend()

plt.subplot(1, 4, 3)
cm = confusion_matrix(y_test, (best_test_pred > 0.5).astype(int))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False, square=True)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix\n(Test Set)')

plt.subplot(1, 4, 4)
# Calibration plot
from sklearn.calibration import calibration_curve
prob_true, prob_pred = calibration_curve(y_test, best_test_pred, n_bins=10)
plt.plot(prob_pred, prob_true, 's-', label='Model', color='steelblue')
plt.plot([0, 1], [0, 1], 'k--', label='Perfectly calibrated')
plt.xlabel('Mean Predicted Probability')
plt.ylabel('Fraction of Positives')
plt.title('Calibration Plot')
plt.legend()

plt.tight_layout()
plt.savefig('../report/images/prediction_analysis.png', dpi=150, bbox_inches='tight')
plt.close()

# 5. Sequence analysis
plt.figure(figsize=(12, 4))

plt.subplot(1, 3, 1)
train_df['seq_length'] = train_df['sym_seq'].str.len()
default_by_length = train_df.groupby('seq_length')['default_flag'].agg(['mean', 'count'])
plt.plot(default_by_length.index, default_by_length['mean'], marker='o', color='steelblue', linewidth=2, markersize=8)
plt.xlabel('Sequence Length')
plt.ylabel('Default Rate')
plt.title('Default Rate by Sequence Length')
plt.grid(True, alpha=0.3)

plt.subplot(1, 3, 2)
plt.bar(default_by_length.index, default_by_length['count'], color='coral', alpha=0.7, edgecolor='black')
plt.xlabel('Sequence Length')
plt.ylabel('Count')
plt.title('Distribution of Sequence Lengths')

plt.subplot(1, 3, 3)
# Character frequency by default
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

plt.tight_layout()
plt.savefig('../report/images/sequence_analysis.png', dpi=150, bbox_inches='tight')
plt.close()

# Save predictions
predictions_df = pd.DataFrame({
    'id': test_df['id'],
    'true_label': y_test,
    'predicted_prob': best_test_pred,
    'predicted_label': (best_test_pred > 0.5).astype(int)
})
predictions_df.to_csv('../outputs/test_predictions_v2.csv', index=False)

print("\n" + "="*60)
print("Analysis complete!")
print(f"Best model: {best_model[0]}")
print(f"Test AUC: {best_model[1]['test_auc']:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Gap to baseline: {best_model[1]['test_auc'] - 0.72:.4f}")
print("="*60)
