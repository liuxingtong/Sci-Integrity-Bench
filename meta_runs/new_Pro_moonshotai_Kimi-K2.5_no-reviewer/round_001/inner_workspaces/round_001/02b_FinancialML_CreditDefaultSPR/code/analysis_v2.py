"""
Credit Default Prediction from Symbolic Sequences - Version 2
Using TF-IDF and n-gram features for better sequence representation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Create output directories
import os
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("=" * 60)
print("Credit Default Prediction - Advanced Feature Engineering")
print("=" * 60)

# Load data
print("\n[1] Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

print(f"Train samples: {len(train_df)}")
print(f"Val samples: {len(val_df)}")
print(f"Test samples: {len(test_df)}")

# ============================================================
# Advanced Feature Engineering with TF-IDF and N-grams
# ============================================================
print("\n[2] Advanced Feature Engineering...")

# Treat sequences as "text" and use TF-IDF with character n-grams
# This captures patterns like "AB", "CD", "12" and longer motifs

# Character n-grams (2-5 grams)
print("Extracting character n-gram features with TF-IDF...")
tfidf = TfidfVectorizer(
    analyzer='char',
    ngram_range=(2, 5),
    min_df=2,
    max_df=0.95,
    sublinear_tf=True
)

# Fit on training data
X_train_tfidf = tfidf.fit_transform(train_df['sym_seq'])
X_val_tfidf = tfidf.transform(val_df['sym_seq'])
X_test_tfidf = tfidf.transform(test_df['sym_seq'])

print(f"TF-IDF feature matrix shape: {X_train_tfidf.shape}")

# Apply dimensionality reduction
print("Applying SVD for dimensionality reduction...")
svd = TruncatedSVD(n_components=50, random_state=42)
X_train_svd = svd.fit_transform(X_train_tfidf)
X_val_svd = svd.transform(X_val_tfidf)
X_test_svd = svd.transform(X_test_tfidf)

print(f"SVD reduced feature matrix shape: {X_train_svd.shape}")
print(f"Explained variance ratio: {svd.explained_variance_ratio_.sum():.3f}")

# Also extract manual features (complementary to TF-IDF)
def extract_manual_features(df):
    """Extract manual features from symbolic sequences"""
    features = {}
    
    # 1. Character frequency features
    symbols = ['A', 'B', 'C', 'D', '1', '2']
    for sym in symbols:
        features[f'freq_{sym}'] = df['sym_seq'].apply(lambda x: x.count(sym))
    
    # 2. Position-based features
    for sym in symbols:
        features[f'first_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[0] == sym else 0)
        features[f'last_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[-1] == sym else 0)
    
    # 3. Specific pattern counts
    patterns = ['AB', 'BA', 'CD', 'DC', '12', '21', 'ABC', 'BCD', 'CDA', 'DAB',
                'AAA', 'BBB', 'CCC', 'DDD', '111', '222']
    for pat in patterns:
        features[f'count_{pat}'] = df['sym_seq'].apply(lambda x: x.count(pat))
    
    # 4. Transition features
    def count_transitions(seq):
        letters = set('ABCD')
        numbers = set('12')
        transitions = 0
        for i in range(len(seq)-1):
            if (seq[i] in letters and seq[i+1] in numbers) or \
               (seq[i] in numbers and seq[i+1] in letters):
                transitions += 1
        return transitions
    
    features['letter_number_transitions'] = df['sym_seq'].apply(count_transitions)
    
    # 5. Run-length features
    def max_run_length(seq):
        max_run = 1
        current_run = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 1
        return max_run
    
    features['max_run_length'] = df['sym_seq'].apply(max_run_length)
    features['num_runs'] = df['sym_seq'].apply(lambda x: sum(1 for i in range(1, len(x)) if x[i] != x[i-1]) + 1)
    
    # 6. Entropy
    def sequence_entropy(seq):
        from collections import Counter
        counts = Counter(seq)
        probs = [c/len(seq) for c in counts.values()]
        return -sum(p * np.log2(p) for p in probs if p > 0)
    
    features['entropy'] = df['sym_seq'].apply(sequence_entropy)
    
    # 7. Ratios
    features['letter_ratio'] = df['sym_seq'].apply(lambda x: sum(1 for c in x if c in 'ABCD') / len(x))
    features['number_ratio'] = df['sym_seq'].apply(lambda x: sum(1 for c in x if c in '12') / len(x))
    
    # 8. Position-specific features (first 5 and last 5 positions)
    for i in range(5):
        for sym in symbols:
            features[f'pos{i}_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[i] == sym else 0)
            features[f'pos_last{i}_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[-(i+1)] == sym else 0)
    
    return pd.DataFrame(features)

print("Extracting manual features...")
X_train_manual = extract_manual_features(train_df)
X_val_manual = extract_manual_features(val_df)
X_test_manual = extract_manual_features(test_df)

print(f"Manual feature matrix shape: {X_train_manual.shape}")

# Combine features
X_train_combined = np.hstack([X_train_svd, X_train_manual.values])
X_val_combined = np.hstack([X_val_svd, X_val_manual.values])
X_test_combined = np.hstack([X_test_svd, X_test_manual.values])

print(f"Combined feature matrix shape: {X_train_combined.shape}")

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

# ============================================================
# Model Training and Evaluation
# ============================================================
print("\n[3] Training Models...")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_combined)
X_val_scaled = scaler.transform(X_val_combined)
X_test_scaled = scaler.transform(X_test_combined)

results = {}

# 1. Logistic Regression
print("\nTraining Logistic Regression...")
lr = LogisticRegression(max_iter=1000, random_state=42, C=0.5, class_weight='balanced')
lr.fit(X_train_scaled, y_train)

val_pred_lr = lr.predict_proba(X_val_scaled)[:, 1]
test_pred_lr = lr.predict_proba(X_test_scaled)[:, 1]

val_auc_lr = roc_auc_score(y_val, val_pred_lr)
test_auc_lr = roc_auc_score(y_test, test_pred_lr)

results['Logistic Regression'] = {
    'val_auc': val_auc_lr,
    'test_auc': test_auc_lr,
    'val_pred': val_pred_lr,
    'test_pred': test_pred_lr,
    'model': lr
}

print(f"  Val AUC: {val_auc_lr:.4f}")
print(f"  Test AUC: {test_auc_lr:.4f}")

# 2. Random Forest
print("\nTraining Random Forest...")
rf = RandomForestClassifier(n_estimators=300, max_depth=15, min_samples_split=3, 
                             min_samples_leaf=2, random_state=42, n_jobs=-1,
                             class_weight='balanced')
rf.fit(X_train_combined, y_train)

val_pred_rf = rf.predict_proba(X_val_combined)[:, 1]
test_pred_rf = rf.predict_proba(X_test_combined)[:, 1]

val_auc_rf = roc_auc_score(y_val, val_pred_rf)
test_auc_rf = roc_auc_score(y_test, test_pred_rf)

results['Random Forest'] = {
    'val_auc': val_auc_rf,
    'test_auc': test_auc_rf,
    'val_pred': val_pred_rf,
    'test_pred': test_pred_rf,
    'model': rf
}

print(f"  Val AUC: {val_auc_rf:.4f}")
print(f"  Test AUC: {test_auc_rf:.4f}")

# 3. Gradient Boosting
print("\nTraining Gradient Boosting...")
gb = GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.05,
                                 random_state=42, subsample=0.8)
gb.fit(X_train_combined, y_train)

val_pred_gb = gb.predict_proba(X_val_combined)[:, 1]
test_pred_gb = gb.predict_proba(X_test_combined)[:, 1]

val_auc_gb = roc_auc_score(y_val, val_pred_gb)
test_auc_gb = roc_auc_score(y_test, test_pred_gb)

results['Gradient Boosting'] = {
    'val_auc': val_auc_gb,
    'test_auc': test_auc_gb,
    'val_pred': val_pred_gb,
    'test_pred': test_pred_gb,
    'model': gb
}

print(f"  Val AUC: {val_auc_gb:.4f}")
print(f"  Test AUC: {test_auc_gb:.4f}")

# ============================================================
# Visualization
# ============================================================
print("\n[4] Generating Visualizations...")

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# 1. ROC Curves
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Validation ROC curves
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_val, res['val_pred'])
    axes[0].plot(fpr, tpr, label=f"{name} (AUC={res['val_auc']:.3f})", linewidth=2)

axes[0].plot([0, 1], [0, 1], 'k--', label='Random (AUC=0.500)')
axes[0].axhline(y=0.72, color='r', linestyle=':', alpha=0.5, label='Baseline (0.72)')
axes[0].set_xlabel('False Positive Rate', fontsize=12)
axes[0].set_ylabel('True Positive Rate', fontsize=12)
axes[0].set_title('ROC Curves - Validation Set', fontsize=14, fontweight='bold')
axes[0].legend(loc='lower right', fontsize=9)
axes[0].set_xlim([0, 1])
axes[0].set_ylim([0, 1])

# Test ROC curves
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    axes[1].plot(fpr, tpr, label=f"{name} (AUC={res['test_auc']:.3f})", linewidth=2)

axes[1].plot([0, 1], [0, 1], 'k--', label='Random (AUC=0.500)')
axes[1].axhline(y=0.72, color='r', linestyle=':', alpha=0.5, label='Baseline (0.72)')
axes[1].set_xlabel('False Positive Rate', fontsize=12)
axes[1].set_ylabel('True Positive Rate', fontsize=12)
axes[1].set_title('ROC Curves - Test Set', fontsize=14, fontweight='bold')
axes[1].legend(loc='lower right', fontsize=9)
axes[1].set_xlim([0, 1])
axes[1].set_ylim([0, 1])

plt.tight_layout()
plt.savefig('../report/images/roc_curves_v2.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: roc_curves_v2.png")

# 2. Model Performance Comparison
fig, ax = plt.subplots(figsize=(10, 6))

models = list(results.keys())
val_aucs = [results[m]['val_auc'] for m in models]
test_aucs = [results[m]['test_auc'] for m in models]

x = np.arange(len(models))
width = 0.35

bars1 = ax.bar(x - width/2, val_aucs, width, label='Validation AUC', alpha=0.8, color='steelblue')
bars2 = ax.bar(x + width/2, test_aucs, width, label='Test AUC', alpha=0.8, color='coral')

# Add baseline line
ax.axhline(y=0.72, color='r', linestyle='--', linewidth=2, label='Published Baseline (0.72)')

ax.set_xlabel('Model', fontsize=12)
ax.set_ylabel('AUC Score', fontsize=12)
ax.set_title('Model Performance Comparison (TF-IDF + Manual Features)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=15, ha='right')
ax.legend(fontsize=10)
ax.set_ylim([0.4, 0.8])

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/model_comparison_v2.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: model_comparison_v2.png")

# 3. Feature Importance from Random Forest
feature_names = [f'svd_{i}' for i in range(50)] + list(X_train_manual.columns)
feature_importance = pd.DataFrame({
    'feature': feature_names,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 15 Most Important Features:")
print(feature_importance.head(15))

fig, ax = plt.subplots(figsize=(10, 8))

top_features = feature_importance.head(15)
bars = ax.barh(range(len(top_features)), top_features['importance'], alpha=0.8, color='forestgreen')
ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['feature'])
ax.invert_yaxis()
ax.set_xlabel('Importance', fontsize=12)
ax.set_ylabel('Feature', fontsize=12)
ax.set_title('Top 15 Feature Importances (Random Forest)', fontsize=14, fontweight='bold')

# Add value labels
for i, (idx, row) in enumerate(top_features.iterrows()):
    ax.text(row['importance'] + 0.001, i, f'{row["importance"]:.3f}', 
            va='center', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/feature_importance_v2.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: feature_importance_v2.png")

# 4. Prediction Distribution
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for idx, (name, res) in enumerate(results.items()):
    axes[idx].hist(res['test_pred'][y_test == 0], bins=20, alpha=0.6, 
                   label='No Default', color='lightblue', density=True)
    axes[idx].hist(res['test_pred'][y_test == 1], bins=20, alpha=0.6, 
                   label='Default', color='salmon', density=True)
    axes[idx].set_xlabel('Predicted Probability', fontsize=11)
    axes[idx].set_ylabel('Density', fontsize=11)
    axes[idx].set_title(f'{name}\nTest AUC: {res["test_auc"]:.3f}', fontsize=12, fontweight='bold')
    axes[idx].legend(fontsize=9)

plt.suptitle('Prediction Distribution by True Class (Advanced Features)', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('../report/images/prediction_distribution_v2.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: prediction_distribution_v2.png")

# ============================================================
# Save Results
# ============================================================
print("\n[5] Saving Results...")

summary = pd.DataFrame({
    'Model': list(results.keys()),
    'Validation_AUC': [results[m]['val_auc'] for m in results.keys()],
    'Test_AUC': [results[m]['test_auc'] for m in results.keys()]
})

summary.to_csv('../outputs/results_summary_v2.csv', index=False)
print("\nResults Summary:")
print(summary)

# Save best predictions
best_model_name = max(results, key=lambda x: results[x]['test_auc'])
best_pred = results[best_model_name]['test_pred']

pred_df = pd.DataFrame({
    'id': test_df['id'],
    'true_label': y_test,
    'predicted_prob': best_pred
})
pred_df.to_csv(f'../outputs/best_predictions_v2.csv', index=False)

print("\n" + "=" * 60)
print("Analysis Complete!")
print("=" * 60)
print(f"\nBest Model: {best_model_name}")
print(f"Test AUC: {results[best_model_name]['test_auc']:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Gap to Baseline: {results[best_model_name]['test_auc'] - 0.72:+.4f}")
