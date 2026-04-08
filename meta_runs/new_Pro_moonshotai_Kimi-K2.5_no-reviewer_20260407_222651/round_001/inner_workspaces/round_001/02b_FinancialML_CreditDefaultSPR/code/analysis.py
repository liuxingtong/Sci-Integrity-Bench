"""
Credit Default Prediction from Symbolic Sequences
Financial ML Research Task
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix, classification_report
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load data
print("Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

print(f"Train size: {len(train_df)}")
print(f"Val size: {len(val_df)}")
print(f"Test size: {len(test_df)}")

# Check class distribution
print("\nClass distribution:")
print(f"Train - Default rate: {train_df['default_flag'].mean():.3f}")
print(f"Val - Default rate: {val_df['default_flag'].mean():.3f}")
print(f"Test - Default rate: {test_df['default_flag'].mean():.3f}")

# Feature engineering from symbolic sequences
def extract_features(df):
    """Extract features from symbolic sequences"""
    features = pd.DataFrame()
    features['id'] = df['id']
    
    # Basic sequence statistics
    features['seq_length'] = df['sym_seq'].str.len()
    
    # Character frequency features
    for char in ['A', 'B', 'C', 'D', '1', '2']:
        features[f'count_{char}'] = df['sym_seq'].str.count(char)
        features[f'freq_{char}'] = features[f'count_{char}'] / features['seq_length']
    
    # Position-based features
    features['first_char'] = df['sym_seq'].str[0]
    features['last_char'] = df['sym_seq'].str[-1]
    
    # N-gram features (bigrams and trigrams)
    def get_ngrams(seq, n):
        return [seq[i:i+n] for i in range(len(seq)-n+1)]
    
    # Most common bigrams
    all_bigrams = []
    for seq in df['sym_seq']:
        all_bigrams.extend(get_ngrams(seq, 2))
    bigram_counts = Counter(all_bigrams)
    top_bigrams = [bg for bg, _ in bigram_counts.most_common(20)]
    
    for bg in top_bigrams:
        features[f'bigram_{bg}'] = df['sym_seq'].str.count(bg)
    
    # Transition features (count of specific patterns)
    features['trans_letter_to_digit'] = df['sym_seq'].str.count(r'[ABCD][12]')
    features['trans_digit_to_letter'] = df['sym_seq'].str.count(r'[12][ABCD]')
    features['trans_same_letter'] = df['sym_seq'].str.count(r'([ABCD])\1')
    features['trans_same_digit'] = df['sym_seq'].str.count(r'([12])\1')
    
    # Run-length features
    def max_consecutive(seq, char_set):
        max_run = 0
        current_run = 0
        for c in seq:
            if c in char_set:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 0
        return max_run
    
    features['max_consec_letters'] = df['sym_seq'].apply(lambda x: max_consecutive(x, 'ABCD'))
    features['max_consec_digits'] = df['sym_seq'].apply(lambda x: max_consecutive(x, '12'))
    
    # Entropy-like features (diversity)
    features['unique_chars'] = df['sym_seq'].apply(lambda x: len(set(x)))
    
    # Specific pattern features
    features['count_1A'] = df['sym_seq'].str.count('1A')
    features['count_2B'] = df['sym_seq'].str.count('2B')
    features['count_1C'] = df['sym_seq'].str.count('1C')
    features['count_2D'] = df['sym_seq'].str.count('2D')
    
    return features

print("\nExtracting features...")
train_features = extract_features(train_df)
val_features = extract_features(val_df)
test_features = extract_features(test_df)

# Encode categorical features
for col in ['first_char', 'last_char']:
    for char in ['A', 'B', 'C', 'D', '1', '2']:
        train_features[f'{col}_{char}'] = (train_features[col] == char).astype(int)
        val_features[f'{col}_{char}'] = (val_features[col] == char).astype(int)
        test_features[f'{col}_{char}'] = (test_features[col] == char).astype(int)
    train_features = train_features.drop(col, axis=1)
    val_features = val_features.drop(col, axis=1)
    test_features = test_features.drop(col, axis=1)

# Align features across datasets
common_cols = list(set(train_features.columns) & set(val_features.columns) & set(test_features.columns))
common_cols = [c for c in common_cols if c != 'id']

X_train = train_features[common_cols].values
X_val = val_features[common_cols].values
X_test = test_features[common_cols].values

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Feature matrix shape: {X_train.shape}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Train models
print("\nTraining models...")

results = {}

# 1. Logistic Regression
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train_scaled, y_train)
val_pred_lr = lr.predict_proba(X_val_scaled)[:, 1]
test_pred_lr = lr.predict_proba(X_test_scaled)[:, 1]
results['Logistic Regression'] = {
    'val_auc': roc_auc_score(y_val, val_pred_lr),
    'test_auc': roc_auc_score(y_test, test_pred_lr),
    'val_pred': val_pred_lr,
    'test_pred': test_pred_lr
}

# 2. Random Forest
rf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
val_pred_rf = rf.predict_proba(X_val)[:, 1]
test_pred_rf = rf.predict_proba(X_test)[:, 1]
results['Random Forest'] = {
    'val_auc': roc_auc_score(y_val, val_pred_rf),
    'test_auc': roc_auc_score(y_test, test_pred_rf),
    'val_pred': val_pred_rf,
    'test_pred': test_pred_rf
}

# 3. Gradient Boosting
gb = GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42)
gb.fit(X_train, y_train)
val_pred_gb = gb.predict_proba(X_val)[:, 1]
test_pred_gb = gb.predict_proba(X_test)[:, 1]
results['Gradient Boosting'] = {
    'val_auc': roc_auc_score(y_val, val_pred_gb),
    'test_auc': roc_auc_score(y_test, test_pred_gb),
    'val_pred': val_pred_gb,
    'test_pred': test_pred_gb
}

# Print results
print("\n" + "="*50)
print("RESULTS SUMMARY")
print("="*50)
print(f"{'Model':<20} {'Val AUC':<12} {'Test AUC':<12}")
print("-"*50)
for model_name, res in results.items():
    print(f"{model_name:<20} {res['val_auc']:.4f}       {res['test_auc']:.4f}")
print("="*50)

# Best model
best_model = max(results.items(), key=lambda x: x[1]['val_auc'])
print(f"\nBest model: {best_model[0]} (Val AUC: {best_model[1]['val_auc']:.4f})")

# Save results
results_df = pd.DataFrame({
    'Model': list(results.keys()),
    'Val_AUC': [r['val_auc'] for r in results.values()],
    'Test_AUC': [r['test_auc'] for r in results.values()]
})
results_df.to_csv('../outputs/model_results.csv', index=False)

# Feature importance (from best model)
if best_model[0] == 'Random Forest':
    importances = rf.feature_importances_
elif best_model[0] == 'Gradient Boosting':
    importances = gb.feature_importances_
else:
    importances = np.abs(lr.coef_[0])

feature_importance_df = pd.DataFrame({
    'feature': common_cols,
    'importance': importances
}).sort_values('importance', ascending=False)
feature_importance_df.to_csv('../outputs/feature_importance.csv', index=False)

print(f"\nTop 10 important features:")
print(feature_importance_df.head(10))

# Generate visualizations
print("\nGenerating visualizations...")

# 1. Model comparison bar chart
plt.figure(figsize=(10, 6))
models = list(results.keys())
val_aucs = [results[m]['val_auc'] for m in models]
test_aucs = [results[m]['test_auc'] for m in models]

x = np.arange(len(models))
width = 0.35

plt.bar(x - width/2, val_aucs, width, label='Validation AUC', color='steelblue')
plt.bar(x + width/2, test_aucs, width, label='Test AUC', color='coral')

plt.axhline(y=0.72, color='red', linestyle='--', label='Baseline AUC = 0.72')
plt.xlabel('Model', fontsize=12)
plt.ylabel('AUC Score', fontsize=12)
plt.title('Model Performance Comparison', fontsize=14, fontweight='bold')
plt.xticks(x, models, rotation=15)
plt.legend()
plt.ylim(0.6, 0.85)
plt.tight_layout()
plt.savefig('../report/images/model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# 2. ROC Curves
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
plt.savefig('report/images/roc_curves.png', dpi=150, bbox_inches='tight')
plt.close()

# 3. Feature importance plot
plt.figure(figsize=(10, 8))
top_features = feature_importance_df.head(15)
plt.barh(range(len(top_features)), top_features['importance'], color='teal')
plt.yticks(range(len(top_features)), top_features['feature'])
plt.xlabel('Importance', fontsize=12)
plt.title('Top 15 Feature Importances', fontsize=14, fontweight='bold')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('report/images/feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()

# 4. Prediction distribution
plt.figure(figsize=(12, 4))

plt.subplot(1, 3, 1)
plt.hist(train_df['default_flag'], bins=[-0.5, 0.5, 1.5], alpha=0.7, color='steelblue', edgecolor='black')
plt.xticks([0, 1])
plt.xlabel('Default Flag')
plt.ylabel('Count')
plt.title('Training Set\nClass Distribution')

plt.subplot(1, 3, 2)
best_test_pred = best_model[1]['test_pred']
plt.hist(best_test_pred[y_test == 0], bins=20, alpha=0.5, label='No Default', color='green')
plt.hist(best_test_pred[y_test == 1], bins=20, alpha=0.5, label='Default', color='red')
plt.xlabel('Predicted Probability')
plt.ylabel('Count')
plt.title(f'Test Set\nPrediction Distribution\n({best_model[0]})')
plt.legend()

plt.subplot(1, 3, 3)
# Confusion matrix
cm = confusion_matrix(y_test, (best_test_pred > 0.5).astype(int))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix\n(Test Set)')

plt.tight_layout()
plt.savefig('report/images/prediction_analysis.png', dpi=150, bbox_inches='tight')
plt.close()

# 5. Sequence length analysis
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
train_df['seq_length'] = train_df['sym_seq'].str.len()
default_by_length = train_df.groupby('seq_length')['default_flag'].agg(['mean', 'count'])
plt.plot(default_by_length.index, default_by_length['mean'], marker='o', color='steelblue')
plt.xlabel('Sequence Length')
plt.ylabel('Default Rate')
plt.title('Default Rate by Sequence Length')
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
plt.bar(default_by_length.index, default_by_length['count'], color='coral', alpha=0.7)
plt.xlabel('Sequence Length')
plt.ylabel('Count')
plt.title('Distribution of Sequence Lengths')

plt.tight_layout()
plt.savefig('report/images/sequence_analysis.png', dpi=150, bbox_inches='tight')
plt.close()

# Save predictions
predictions_df = pd.DataFrame({
    'id': test_df['id'],
    'true_label': y_test,
    'predicted_prob': best_test_pred,
    'predicted_label': (best_test_pred > 0.5).astype(int)
})
predictions_df.to_csv('outputs/test_predictions.csv', index=False)

print("\nAnalysis complete!")
print(f"Best model Test AUC: {best_model[1]['test_auc']:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Improvement: {best_model[1]['test_auc'] - 0.72:.4f}")
