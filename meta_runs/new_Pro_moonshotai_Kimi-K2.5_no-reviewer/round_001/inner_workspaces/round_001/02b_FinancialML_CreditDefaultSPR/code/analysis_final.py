"""
Credit Default Prediction - Final Analysis
Ensemble approach with optimized features
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
from sklearn.model_selection import GridSearchCV
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

import os
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("=" * 60)
print("Credit Default Prediction - Final Ensemble Analysis")
print("=" * 60)

# Load data
print("\n[1] Loading data...")
train_df = pd.read_csv('../data/train.csv')
val_df = pd.read_csv('../data/val.csv')
test_df = pd.read_csv('../data/test.csv')

y_train = train_df['default_flag'].values
y_val = val_df['default_flag'].values
y_test = test_df['default_flag'].values

print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

# ============================================================
# Optimized Feature Engineering
# ============================================================
print("\n[2] Feature Engineering...")

def extract_features(df):
    """Optimized feature extraction"""
    features = {}
    
    symbols = ['A', 'B', 'C', 'D', '1', '2']
    
    # 1. Character frequencies
    for sym in symbols:
        features[f'freq_{sym}'] = df['sym_seq'].apply(lambda x: x.count(sym))
    
    # 2. First and last character
    for sym in symbols:
        features[f'first_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[0] == sym else 0)
        features[f'last_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[-1] == sym else 0)
    
    # 3. Bigram counts (all 36 combinations)
    for s1 in symbols:
        for s2 in symbols:
            bigram = s1 + s2
            features[f'bigram_{bigram}'] = df['sym_seq'].apply(lambda x: x.count(bigram))
    
    # 4. Specific patterns
    patterns = ['AB', 'BA', 'CD', 'DC', '12', '21', '1A', 'A1', '2B', 'B2']
    for pat in patterns:
        features[f'pat_{pat}'] = df['sym_seq'].apply(lambda x: x.count(pat))
    
    # 5. Run statistics
    def get_runs(seq):
        runs = []
        current = 1
        for i in range(1, len(seq)):
            if seq[i] == seq[i-1]:
                current += 1
            else:
                runs.append(current)
                current = 1
        runs.append(current)
        return runs
    
    features['max_run'] = df['sym_seq'].apply(lambda x: max(get_runs(x)))
    features['num_runs'] = df['sym_seq'].apply(lambda x: len(get_runs(x)))
    
    # 6. Entropy
    from collections import Counter
    def entropy(seq):
        counts = Counter(seq)
        probs = [c/len(seq) for c in counts.values()]
        return -sum(p * np.log2(p) for p in probs if p > 0)
    
    features['entropy'] = df['sym_seq'].apply(entropy)
    
    # 7. Ratios
    features['letter_ratio'] = df['sym_seq'].apply(lambda x: sum(1 for c in x if c in 'ABCD') / len(x))
    features['number_ratio'] = df['sym_seq'].apply(lambda x: sum(1 for c in x if c in '12') / len(x))
    
    # 8. Position-specific (first 3, last 3)
    for pos in range(3):
        for sym in symbols:
            features[f'pos{pos}_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[pos] == sym else 0)
            features[f'pos_last{pos}_{sym}'] = df['sym_seq'].apply(lambda x: 1 if x[-(pos+1)] == sym else 0)
    
    return pd.DataFrame(features)

print("Extracting manual features...")
X_train_manual = extract_features(train_df)
X_val_manual = extract_features(val_df)
X_test_manual = extract_features(test_df)

print(f"Manual features: {X_train_manual.shape[1]}")

# TF-IDF features
tfidf = TfidfVectorizer(analyzer='char', ngram_range=(2, 4), min_df=2, max_df=0.95)
X_train_tfidf = tfidf.fit_transform(train_df['sym_seq'])
X_val_tfidf = tfidf.transform(val_df['sym_seq'])
X_test_tfidf = tfidf.transform(test_df['sym_seq'])

svd = TruncatedSVD(n_components=50, random_state=42)
X_train_svd = svd.fit_transform(X_train_tfidf)
X_val_svd = svd.transform(X_val_tfidf)
X_test_svd = svd.transform(X_test_tfidf)

# Combine
X_train = np.hstack([X_train_svd, X_train_manual.values])
X_val = np.hstack([X_val_svd, X_val_manual.values])
X_test = np.hstack([X_test_svd, X_test_manual.values])

print(f"Total features: {X_train.shape[1]}")

# Scale
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_val_s = scaler.transform(X_val)
X_test_s = scaler.transform(X_test)

# ============================================================
# Model Training
# ============================================================
print("\n[3] Training Models...")

results = {}

# 1. Logistic Regression
lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42, class_weight='balanced')
lr.fit(X_train_s, y_train)
val_pred = lr.predict_proba(X_val_s)[:, 1]
test_pred = lr.predict_proba(X_test_s)[:, 1]
results['Logistic Regression'] = {
    'val_auc': roc_auc_score(y_val, val_pred),
    'test_auc': roc_auc_score(y_test, test_pred),
    'val_pred': val_pred, 'test_pred': test_pred
}
print(f"Logistic Regression - Val: {results['Logistic Regression']['val_auc']:.4f}, Test: {results['Logistic Regression']['test_auc']:.4f}")

# 2. Random Forest
rf = RandomForestClassifier(n_estimators=300, max_depth=15, random_state=42, class_weight='balanced')
rf.fit(X_train, y_train)
val_pred = rf.predict_proba(X_val)[:, 1]
test_pred = rf.predict_proba(X_test)[:, 1]
results['Random Forest'] = {
    'val_auc': roc_auc_score(y_val, val_pred),
    'test_auc': roc_auc_score(y_test, test_pred),
    'val_pred': val_pred, 'test_pred': test_pred
}
print(f"Random Forest - Val: {results['Random Forest']['val_auc']:.4f}, Test: {results['Random Forest']['test_auc']:.4f}")

# 3. Gradient Boosting
gb = GradientBoostingClassifier(n_estimators=300, max_depth=4, learning_rate=0.1, random_state=42)
gb.fit(X_train, y_train)
val_pred = gb.predict_proba(X_val)[:, 1]
test_pred = gb.predict_proba(X_test)[:, 1]
results['Gradient Boosting'] = {
    'val_auc': roc_auc_score(y_val, val_pred),
    'test_auc': roc_auc_score(y_test, test_pred),
    'val_pred': val_pred, 'test_pred': test_pred
}
print(f"Gradient Boosting - Val: {results['Gradient Boosting']['val_auc']:.4f}, Test: {results['Gradient Boosting']['test_auc']:.4f}")

# 4. SVM
svm = SVC(probability=True, C=1.0, kernel='rbf', random_state=42, class_weight='balanced')
svm.fit(X_train_s, y_train)
val_pred = svm.predict_proba(X_val_s)[:, 1]
test_pred = svm.predict_proba(X_test_s)[:, 1]
results['SVM'] = {
    'val_auc': roc_auc_score(y_val, val_pred),
    'test_auc': roc_auc_score(y_test, test_pred),
    'val_pred': val_pred, 'test_pred': test_pred
}
print(f"SVM - Val: {results['SVM']['val_auc']:.4f}, Test: {results['SVM']['test_auc']:.4f}")

# 5. KNN
knn = KNeighborsClassifier(n_neighbors=15, weights='distance')
knn.fit(X_train_s, y_train)
val_pred = knn.predict_proba(X_val_s)[:, 1]
test_pred = knn.predict_proba(X_test_s)[:, 1]
results['KNN'] = {
    'val_auc': roc_auc_score(y_val, val_pred),
    'test_auc': roc_auc_score(y_test, test_pred),
    'val_pred': val_pred, 'test_pred': test_pred
}
print(f"KNN - Val: {results['KNN']['val_auc']:.4f}, Test: {results['KNN']['test_auc']:.4f}")

# 6. Simple Ensemble (average)
print("\nCreating Ensemble...")
ensemble_val_pred = np.mean([results[m]['val_pred'] for m in results.keys()], axis=0)
ensemble_test_pred = np.mean([results[m]['test_pred'] for m in results.keys()], axis=0)
results['Ensemble (Average)'] = {
    'val_auc': roc_auc_score(y_val, ensemble_val_pred),
    'test_auc': roc_auc_score(y_test, ensemble_test_pred),
    'val_pred': ensemble_val_pred, 'test_pred': ensemble_test_pred
}
print(f"Ensemble - Val: {results['Ensemble (Average)']['val_auc']:.4f}, Test: {results['Ensemble (Average)']['test_auc']:.4f}")

# ============================================================
# Visualizations
# ============================================================
print("\n[4] Generating Visualizations...")

plt.style.use('seaborn-v0_8-whitegrid')

# ROC Curves
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_val, res['val_pred'])
    axes[0].plot(fpr, tpr, label=f"{name} (AUC={res['val_auc']:.3f})", linewidth=2)

axes[0].plot([0, 1], [0, 1], 'k--', label='Random (0.500)')
axes[0].axhline(y=0.72, color='r', linestyle=':', alpha=0.7, label='Baseline (0.72)')
axes[0].set_xlabel('False Positive Rate', fontsize=12)
axes[0].set_ylabel('True Positive Rate', fontsize=12)
axes[0].set_title('ROC Curves - Validation Set', fontsize=14, fontweight='bold')
axes[0].legend(loc='lower right', fontsize=8)
axes[0].set_xlim([0, 1])
axes[0].set_ylim([0, 1])

for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_pred'])
    axes[1].plot(fpr, tpr, label=f"{name} (AUC={res['test_auc']:.3f})", linewidth=2)

axes[1].plot([0, 1], [0, 1], 'k--', label='Random (0.500)')
axes[1].axhline(y=0.72, color='r', linestyle=':', alpha=0.7, label='Baseline (0.72)')
axes[1].set_xlabel('False Positive Rate', fontsize=12)
axes[1].set_ylabel('True Positive Rate', fontsize=12)
axes[1].set_title('ROC Curves - Test Set', fontsize=14, fontweight='bold')
axes[1].legend(loc='lower right', fontsize=8)
axes[1].set_xlim([0, 1])
axes[1].set_ylim([0, 1])

plt.tight_layout()
plt.savefig('../report/images/roc_curves_final.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: roc_curves_final.png")

# Model Comparison
fig, ax = plt.subplots(figsize=(12, 6))

models = list(results.keys())
val_aucs = [results[m]['val_auc'] for m in models]
test_aucs = [results[m]['test_auc'] for m in models]

x = np.arange(len(models))
width = 0.35

bars1 = ax.bar(x - width/2, val_aucs, width, label='Validation AUC', alpha=0.8, color='steelblue')
bars2 = ax.bar(x + width/2, test_aucs, width, label='Test AUC', alpha=0.8, color='coral')

ax.axhline(y=0.72, color='r', linestyle='--', linewidth=2, label='Baseline (0.72)')

ax.set_xlabel('Model', fontsize=12)
ax.set_ylabel('AUC Score', fontsize=12)
ax.set_title('Model Performance Comparison - Final Analysis', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(models, rotation=30, ha='right')
ax.legend(fontsize=10)
ax.set_ylim([0.35, 0.8])

for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('../report/images/model_comparison_final.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: model_comparison_final.png")

# Feature Importance
feature_names = [f'svd_{i}' for i in range(50)] + list(X_train_manual.columns)
feature_importance = pd.DataFrame({
    'feature': feature_names,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

fig, ax = plt.subplots(figsize=(10, 8))
top_features = feature_importance.head(20)
bars = ax.barh(range(len(top_features)), top_features['importance'], alpha=0.8, color='forestgreen')
ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['feature'])
ax.invert_yaxis()
ax.set_xlabel('Importance', fontsize=12)
ax.set_ylabel('Feature', fontsize=12)
ax.set_title('Top 20 Feature Importances (Random Forest)', fontsize=14, fontweight='bold')

for i, (idx, row) in enumerate(top_features.iterrows()):
    ax.text(row['importance'] + 0.0005, i, f'{row["importance"]:.3f}', 
            va='center', fontsize=8)

plt.tight_layout()
plt.savefig('../report/images/feature_importance_final.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: feature_importance_final.png")

# Prediction Distribution
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, (name, res) in enumerate(results.items()):
    if idx < 6:
        axes[idx].hist(res['test_pred'][y_test == 0], bins=20, alpha=0.6, 
                       label='No Default', color='lightblue', density=True)
        axes[idx].hist(res['test_pred'][y_test == 1], bins=20, alpha=0.6, 
                       label='Default', color='salmon', density=True)
        axes[idx].set_xlabel('Predicted Probability', fontsize=10)
        axes[idx].set_ylabel('Density', fontsize=10)
        axes[idx].set_title(f'{name}\nTest AUC: {res["test_auc"]:.3f}', fontsize=11, fontweight='bold')
        axes[idx].legend(fontsize=8)

plt.suptitle('Prediction Distribution by True Class', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('../report/images/prediction_distribution_final.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: prediction_distribution_final.png")

# ============================================================
# Save Results
# ============================================================
print("\n[5] Saving Results...")

summary = pd.DataFrame({
    'Model': list(results.keys()),
    'Validation_AUC': [results[m]['val_auc'] for m in results.keys()],
    'Test_AUC': [results[m]['test_auc'] for m in results.keys()]
})

summary.to_csv('../outputs/results_summary_final.csv', index=False)
print("\nFinal Results Summary:")
print(summary.to_string(index=False))

best_model = max(results, key=lambda x: results[x]['test_auc'])
print(f"\n{'='*60}")
print(f"Best Model: {best_model}")
print(f"Test AUC: {results[best_model]['test_auc']:.4f}")
print(f"Baseline AUC: 0.72")
print(f"Gap: {results[best_model]['test_auc'] - 0.72:+.4f}")
print(f"{'='*60}")

# Save best predictions
best_pred_df = pd.DataFrame({
    'id': test_df['id'],
    'true_label': y_test,
    'predicted_prob': results[best_model]['test_pred']
})
best_pred_df.to_csv('../outputs/final_predictions.csv', index=False)
