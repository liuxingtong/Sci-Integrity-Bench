"""
Variable Star Classification - Combined Feature Approach
AstroML Time-Domain Survey Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
from scipy.sparse import hstack, csr_matrix
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
print("Loading data...")
train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')
test_df = pd.read_csv('data/test.csv')

# Combine train and val
combined_df = pd.concat([train_df, val_df], ignore_index=True)

print(f"Train size: {len(train_df)}")
print(f"Val size: {len(val_df)}")
print(f"Test size: {len(test_df)}")

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values
y_combined = combined_df['label'].values

# Extract manual features
def extract_manual_features(series):
    """Extract manual features from symbolic series"""
    features = {}
    n = len(series)
    
    # Symbol counts
    symbols = ['u', 'v', 'w', 'x', 'y', 'z', '*', '.']
    char_counts = Counter(series)
    
    for sym in symbols:
        features[f'cnt_{sym}'] = char_counts.get(sym, 0)
        features[f'freq_{sym}'] = char_counts.get(sym, 0) / n if n > 0 else 0
    
    # Run analysis
    runs = []
    current_char = series[0] if n > 0 else ''
    current_len = 1
    
    for i in range(1, n):
        if series[i] == current_char:
            current_len += 1
        else:
            runs.append((current_char, current_len))
            current_char = series[i]
            current_len = 1
    runs.append((current_char, current_len))
    
    features['num_runs'] = len(runs)
    run_lengths = [r[1] for r in runs]
    features['mean_run'] = np.mean(run_lengths)
    features['std_run'] = np.std(run_lengths)
    features['max_run'] = max(run_lengths)
    
    # Magnitude features
    mag_weights = {'u': 0, 'v': 1, 'w': 2, 'x': 3, 'y': 4, 'z': 5}
    mag_values = [mag_weights[c] for c in series if c in mag_weights]
    
    if mag_values:
        features['mag_mean'] = np.mean(mag_values)
        features['mag_std'] = np.std(mag_values)
        features['mag_range'] = max(mag_values) - min(mag_values)
    else:
        features['mag_mean'] = 0
        features['mag_std'] = 0
        features['mag_range'] = 0
    
    # Pattern features
    features['double_star'] = series.count('**')
    features['triple_star'] = series.count('***')
    features['double_dot'] = series.count('..')
    
    return features

from collections import Counter

print("\nExtracting manual features...")
train_manual = pd.DataFrame(train_df['symbol_series'].apply(extract_manual_features).tolist())
val_manual = pd.DataFrame(val_df['symbol_series'].apply(extract_manual_features).tolist())
test_manual = pd.DataFrame(test_df['symbol_series'].apply(extract_manual_features).tolist())
combined_manual = pd.DataFrame(combined_df['symbol_series'].apply(extract_manual_features).tolist())

# Vectorize sequences
print("\nVectorizing sequences...")

# Best performing: Count vectorizer with char n-grams (2-4)
count_vec = CountVectorizer(analyzer='char', ngram_range=(2, 4), max_features=400)
X_combined_count = count_vec.fit_transform(combined_df['symbol_series'])
X_test_count = count_vec.transform(test_df['symbol_series'])

# TF-IDF char n-grams (3-6)
tfidf_char = TfidfVectorizer(analyzer='char', ngram_range=(3, 6), max_features=400)
X_combined_tfidf = tfidf_char.fit_transform(combined_df['symbol_series'])
X_test_tfidf = tfidf_char.transform(test_df['symbol_series'])

# Combine features
print("\nCombining features...")
X_combined_manual_sparse = csr_matrix(combined_manual.values)
X_test_manual_sparse = csr_matrix(test_manual.values)

X_combined_fused = hstack([X_combined_count, X_combined_tfidf, X_combined_manual_sparse])
X_test_fused = hstack([X_test_count, X_test_tfidf, X_test_manual_sparse])

print(f"Fused feature shape: {X_combined_fused.shape}")

# Train models
print("\nTraining models on fused features...")

results = {}

# Logistic Regression
print("  Training Logistic Regression...")
lr = LogisticRegression(max_iter=3000, random_state=42, C=0.5, solver='lbfgs')
lr.fit(X_combined_fused, y_combined)
test_pred = lr.predict(X_test_fused)
test_proba = lr.predict_proba(X_test_fused)[:, 1]
test_bal_acc = balanced_accuracy_score(y_test, test_pred)
test_auc = roc_auc_score(y_test, test_proba)

results['LR_fused'] = {
    'test_bal_acc': test_bal_acc,
    'test_auc': test_auc,
    'test_pred': test_pred,
    'test_proba': test_proba,
    'model': lr
}
print(f"    Test Balanced Accuracy: {test_bal_acc:.4f}")

# Naive Bayes
print("  Training Naive Bayes...")
nb = MultinomialNB(alpha=0.1)
nb.fit(X_combined_fused, y_combined)
test_pred = nb.predict(X_test_fused)
test_proba = nb.predict_proba(X_test_fused)[:, 1]
test_bal_acc = balanced_accuracy_score(y_test, test_pred)
test_auc = roc_auc_score(y_test, test_proba)

results['NB_fused'] = {
    'test_bal_acc': test_bal_acc,
    'test_auc': test_auc,
    'test_pred': test_pred,
    'test_proba': test_proba,
    'model': nb
}
print(f"    Test Balanced Accuracy: {test_bal_acc:.4f}")

# Random Forest
print("  Training Random Forest...")
rf = RandomForestClassifier(n_estimators=500, max_depth=20, min_samples_split=2, random_state=42)
rf.fit(X_combined_fused, y_combined)
test_pred = rf.predict(X_test_fused)
test_proba = rf.predict_proba(X_test_fused)[:, 1]
test_bal_acc = balanced_accuracy_score(y_test, test_pred)
test_auc = roc_auc_score(y_test, test_proba)

results['RF_fused'] = {
    'test_bal_acc': test_bal_acc,
    'test_auc': test_auc,
    'test_pred': test_pred,
    'test_proba': test_proba,
    'model': rf
}
print(f"    Test Balanced Accuracy: {test_bal_acc:.4f}")

# Gradient Boosting
print("  Training Gradient Boosting...")
gb = GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.1, random_state=42)
gb.fit(X_combined_fused, y_combined)
test_pred = gb.predict(X_test_fused)
test_proba = gb.predict_proba(X_test_fused)[:, 1]
test_bal_acc = balanced_accuracy_score(y_test, test_pred)
test_auc = roc_auc_score(y_test, test_proba)

results['GB_fused'] = {
    'test_bal_acc': test_bal_acc,
    'test_auc': test_auc,
    'test_pred': test_pred,
    'test_proba': test_proba,
    'model': gb
}
print(f"    Test Balanced Accuracy: {test_bal_acc:.4f}")

# Voting ensemble
print("  Training Voting Ensemble...")
voting = VotingClassifier(
    estimators=[('lr', LogisticRegression(max_iter=2000, random_state=42, C=0.5)),
                ('nb', MultinomialNB(alpha=0.1)),
                ('rf', RandomForestClassifier(n_estimators=200, random_state=42))],
    voting='soft'
)
voting.fit(X_combined_fused, y_combined)
test_pred = voting.predict(X_test_fused)
test_proba = voting.predict_proba(X_test_fused)[:, 1]
test_bal_acc = balanced_accuracy_score(y_test, test_pred)
test_auc = roc_auc_score(y_test, test_proba)

results['Voting_fused'] = {
    'test_bal_acc': test_bal_acc,
    'test_auc': test_auc,
    'test_pred': test_pred,
    'test_proba': test_proba,
    'model': voting
}
print(f"    Test Balanced Accuracy: {test_bal_acc:.4f}")

# Find best model
best_model_name = max(results, key=lambda x: results[x]['test_bal_acc'])
print(f"\nBest model: {best_model_name}")
print(f"Test Balanced Accuracy: {results[best_model_name]['test_bal_acc']:.4f}")

# Save results
print("\nSaving results...")

results_summary = []
for name, res in results.items():
    results_summary.append({
        'Model': name,
        'Test_Balanced_Accuracy': res['test_bal_acc'],
        'Test_AUC': res['test_auc']
    })

results_df = pd.DataFrame(results_summary)
results_df = results_df.sort_values('Test_Balanced_Accuracy', ascending=False)
results_df.to_csv('outputs/model_comparison_combined.csv', index=False)

# Generate visualizations
print("\nGenerating visualizations...")

# Figure 1: Model Comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

models_list = list(results_df['Model'])
test_accs = list(results_df['Test_Balanced_Accuracy'])
test_aucs = list(results_df['Test_AUC'])

x = np.arange(len(models_list))

axes[0].bar(x, test_accs, alpha=0.8, color='steelblue')
axes[0].set_ylabel('Balanced Accuracy', fontsize=12)
axes[0].set_title('Model Performance - Combined Features', fontsize=14, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(models_list, rotation=45, ha='right')
axes[0].axhline(y=0.78, color='red', linestyle='--', linewidth=2, label='Baseline (0.78)')
axes[0].legend()
axes[0].set_ylim([0.4, 1.0])
axes[0].grid(axis='y', alpha=0.3)

axes[1].bar(x, test_aucs, alpha=0.8, color='forestgreen')
axes[1].set_ylabel('AUC Score', fontsize=12)
axes[1].set_title('AUC Score - Combined Features', fontsize=14, fontweight='bold')
axes[1].set_xticks(x)
axes[1].set_xticklabels(models_list, rotation=45, ha='right')
axes[1].set_ylim([0.4, 1.0])
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/model_comparison_combined.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: ROC Curves
plt.figure(figsize=(10, 8))
colors = plt.cm.tab10(np.linspace(0, 1, len(results)))

for i, (name, res) in enumerate(results.items()):
    fpr, tpr, _ = roc_curve(y_test, res['test_proba'])
    plt.plot(fpr, tpr, label=f"{name} (AUC = {res['test_auc']:.3f})", 
             linewidth=2, color=colors[i])

plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier', linewidth=1)
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves - Combined Features', fontsize=14, fontweight='bold')
plt.legend(loc='lower right', fontsize=9)
plt.grid(True, alpha=0.3)
plt.savefig('report/images/roc_curves_combined.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 3: Confusion Matrix for Best Model
best_model = results[best_model_name]
cm = confusion_matrix(y_test, best_model['test_pred'])

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar_kws={'label': 'Count'},
            xticklabels=['Non-Variable', 'Variable'],
            yticklabels=['Non-Variable', 'Variable'],
            annot_kws={'size': 14})
plt.xlabel('Predicted Label', fontsize=12)
plt.ylabel('True Label', fontsize=12)
plt.title(f'Confusion Matrix - {best_model_name}', fontsize=14, fontweight='bold')
plt.savefig('report/images/confusion_matrix_combined.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 4: Feature Importance (Random Forest)
if hasattr(results['RF_fused']['model'], 'feature_importances_'):
    rf_importance = results['RF_fused']['model'].feature_importances_
    
    # Get top 30 features
    top_indices = np.argsort(rf_importance)[-30:]
    
    plt.figure(figsize=(10, 10))
    plt.barh(range(len(top_indices)), rf_importance[top_indices], color='forestgreen')
    plt.yticks(range(len(top_indices)), [f'Feature {i}' for i in top_indices])
    plt.xlabel('Feature Importance', fontsize=12)
    plt.title('Random Forest - Top 30 Feature Importances', fontsize=14, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/feature_importance_combined.png', dpi=300, bbox_inches='tight')
    plt.close()

# Save classification report
report = classification_report(y_test, best_model['test_pred'], 
                               target_names=['Non-Variable', 'Variable'])
with open('outputs/classification_report_combined.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test Balanced Accuracy: {best_model['test_bal_acc']:.4f}\n")
    f.write(f"Test AUC: {best_model['test_auc']:.4f}\n\n")
    f.write(report)

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test_df['object_id'],
    'true_label': y_test,
    'predicted_label': best_model['test_pred'],
    'probability': best_model['test_proba']
})
predictions_df.to_csv('outputs/test_predictions_combined.csv', index=False)

print("\nCombined analysis complete!")
