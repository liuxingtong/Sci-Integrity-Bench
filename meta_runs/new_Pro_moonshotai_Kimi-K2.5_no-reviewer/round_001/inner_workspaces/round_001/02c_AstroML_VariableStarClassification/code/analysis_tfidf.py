"""
Variable Star Classification - TF-IDF Approach
AstroML Time-Domain Survey Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.model_selection import cross_val_score, StratifiedKFold
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

# Try different vectorization approaches
print("\nVectorizing sequences...")

# 1. Character n-grams (2-5)
print("  - Character n-grams (2-5)...")
tfidf_char = TfidfVectorizer(analyzer='char', ngram_range=(2, 5), max_features=500)
X_combined_char = tfidf_char.fit_transform(combined_df['symbol_series'])
X_test_char = tfidf_char.transform(test_df['symbol_series'])

# 2. Character n-grams (3-6)
print("  - Character n-grams (3-6)...")
tfidf_char2 = TfidfVectorizer(analyzer='char', ngram_range=(3, 6), max_features=500)
X_combined_char2 = tfidf_char2.fit_transform(combined_df['symbol_series'])
X_test_char2 = tfidf_char2.transform(test_df['symbol_series'])

# 3. Word n-grams (treat runs as words)
print("  - Word n-grams...")
def segment_runs(series):
    """Segment series into runs"""
    if len(series) == 0:
        return ""
    runs = []
    current_run = series[0]
    for char in series[1:]:
        if char == current_run[0]:
            current_run += char
        else:
            runs.append(current_run)
            current_run = char
    runs.append(current_run)
    return ' '.join(runs)

combined_segmented = combined_df['symbol_series'].apply(segment_runs)
test_segmented = test_df['symbol_series'].apply(segment_runs)

tfidf_word = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), max_features=300)
X_combined_word = tfidf_word.fit_transform(combined_segmented)
X_test_word = tfidf_word.transform(test_segmented)

# 4. Count vectorizer (raw counts)
print("  - Count vectorizer...")
count_vec = CountVectorizer(analyzer='char', ngram_range=(2, 4), max_features=300)
X_combined_count = count_vec.fit_transform(combined_df['symbol_series'])
X_test_count = count_vec.transform(test_df['symbol_series'])

print(f"Char n-gram (2-5) shape: {X_combined_char.shape}")
print(f"Char n-gram (3-6) shape: {X_combined_char2.shape}")
print(f"Word n-gram shape: {X_combined_word.shape}")
print(f"Count shape: {X_combined_count.shape}")

# Train models on different representations
print("\nTraining models...")

results = {}

representations = {
    'char_2-5': (X_combined_char, X_test_char),
    'char_3-6': (X_combined_char2, X_test_char2),
    'word': (X_combined_word, X_test_word),
    'count': (X_combined_count, X_test_count)
}

for rep_name, (X_combined, X_test) in representations.items():
    print(f"\n--- Representation: {rep_name} ---")
    
    # Naive Bayes (works well with count data)
    print("  Training Naive Bayes...")
    nb = MultinomialNB()
    nb.fit(X_combined, y_combined)
    test_pred = nb.predict(X_test)
    test_proba = nb.predict_proba(X_test)[:, 1]
    test_bal_acc = balanced_accuracy_score(y_test, test_pred)
    test_auc = roc_auc_score(y_test, test_proba)
    
    results[f'NB_{rep_name}'] = {
        'test_bal_acc': test_bal_acc,
        'test_auc': test_auc,
        'test_pred': test_pred,
        'test_proba': test_proba,
        'model': nb
    }
    print(f"    Test Balanced Accuracy: {test_bal_acc:.4f}")
    
    # Logistic Regression
    print("  Training Logistic Regression...")
    lr = LogisticRegression(max_iter=2000, random_state=42, C=1.0)
    lr.fit(X_combined, y_combined)
    test_pred = lr.predict(X_test)
    test_proba = lr.predict_proba(X_test)[:, 1]
    test_bal_acc = balanced_accuracy_score(y_test, test_pred)
    test_auc = roc_auc_score(y_test, test_proba)
    
    results[f'LR_{rep_name}'] = {
        'test_bal_acc': test_bal_acc,
        'test_auc': test_auc,
        'test_pred': test_pred,
        'test_proba': test_proba,
        'model': lr
    }
    print(f"    Test Balanced Accuracy: {test_bal_acc:.4f}")
    
    # Random Forest
    print("  Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=300, max_depth=15, random_state=42)
    rf.fit(X_combined, y_combined)
    test_pred = rf.predict(X_test)
    test_proba = rf.predict_proba(X_test)[:, 1]
    test_bal_acc = balanced_accuracy_score(y_test, test_pred)
    test_auc = roc_auc_score(y_test, test_proba)
    
    results[f'RF_{rep_name}'] = {
        'test_bal_acc': test_bal_acc,
        'test_auc': test_auc,
        'test_pred': test_pred,
        'test_proba': test_proba,
        'model': rf
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
results_df.to_csv('outputs/model_comparison_tfidf.csv', index=False)

# Generate visualizations
print("\nGenerating visualizations...")

# Figure 1: Model Comparison
fig, ax = plt.subplots(1, 1, figsize=(14, 8))

models_list = list(results_df['Model'])
test_accs = list(results_df['Test_Balanced_Accuracy'])
test_aucs = list(results_df['Test_AUC'])

x = np.arange(len(models_list))
width = 0.35

ax.barh(x, test_accs, height=0.4, label='Balanced Accuracy', alpha=0.8, color='steelblue')
ax.barh(x + width, test_aucs, height=0.4, label='AUC', alpha=0.8, color='coral')
ax.set_xlabel('Score', fontsize=12)
ax.set_ylabel('Model', fontsize=12)
ax.set_title('Model Performance - TF-IDF Features', fontsize=14, fontweight='bold')
ax.set_yticks(x + width/2)
ax.set_yticklabels(models_list, fontsize=9)
ax.legend()
ax.axvline(x=0.78, color='red', linestyle='--', linewidth=2, label='Baseline (0.78)')
ax.set_xlim([0.3, 1.0])
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/model_comparison_tfidf.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: ROC Curves for top models
plt.figure(figsize=(10, 8))

top_models = results_df.head(6)['Model'].tolist()
colors = plt.cm.tab10(np.linspace(0, 1, len(top_models)))

for i, name in enumerate(top_models):
    res = results[name]
    fpr, tpr, _ = roc_curve(y_test, res['test_proba'])
    plt.plot(fpr, tpr, label=f"{name} (AUC = {res['test_auc']:.3f})", 
             linewidth=2, color=colors[i])

plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier', linewidth=1)
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves - Top Models', fontsize=14, fontweight='bold')
plt.legend(loc='lower right', fontsize=9)
plt.grid(True, alpha=0.3)
plt.savefig('report/images/roc_curves_tfidf.png', dpi=300, bbox_inches='tight')
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
plt.savefig('report/images/confusion_matrix_tfidf.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 4: Performance by representation
rep_performance = {}
for rep in ['char_2-5', 'char_3-6', 'word', 'count']:
    rep_models = [m for m in results.keys() if m.endswith(rep)]
    rep_scores = [results[m]['test_bal_acc'] for m in rep_models]
    rep_performance[rep] = max(rep_scores)

plt.figure(figsize=(10, 6))
reps = list(rep_performance.keys())
scores = list(rep_performance.values())
bars = plt.bar(reps, scores, alpha=0.8, color=['steelblue', 'forestgreen', 'coral', 'purple'])
plt.ylabel('Best Balanced Accuracy', fontsize=12)
plt.xlabel('Representation', fontsize=12)
plt.title('Best Performance by Representation Type', fontsize=14, fontweight='bold')
plt.axhline(y=0.78, color='red', linestyle='--', linewidth=2, label='Baseline (0.78)')
plt.legend()
plt.ylim([0.4, 1.0])
plt.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bar, score in zip(bars, scores):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
             f'{score:.3f}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/rep_comparison_tfidf.png', dpi=300, bbox_inches='tight')
plt.close()

# Save classification report
report = classification_report(y_test, best_model['test_pred'], 
                               target_names=['Non-Variable', 'Variable'])
with open('outputs/classification_report_tfidf.txt', 'w') as f:
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
predictions_df.to_csv('outputs/test_predictions_tfidf.csv', index=False)

print("\nTF-IDF analysis complete!")
