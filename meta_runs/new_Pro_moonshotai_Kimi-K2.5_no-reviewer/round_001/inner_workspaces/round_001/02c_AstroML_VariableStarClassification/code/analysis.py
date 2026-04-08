"""
Variable Star Classification using Symbolic Series Features
AstroML Time-Domain Survey Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
import re
from collections import Counter
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

print(f"Train size: {len(train_df)}")
print(f"Val size: {len(val_df)}")
print(f"Test size: {len(test_df)}")

# Check class distribution
print("\nClass distribution:")
print("Train:", train_df['label'].value_counts().to_dict())
print("Val:", val_df['label'].value_counts().to_dict())
print("Test:", test_df['label'].value_counts().to_dict())

# Feature extraction from symbolic series
def extract_symbol_features(series):
    """Extract features from symbolic series string"""
    features = {}
    
    # Basic length features
    features['length'] = len(series)
    
    # Character frequency features
    char_counts = Counter(series)
    for char in ['u', 'v', 'w', 'x', 'y', 'z', '*', '.']:
        features[f'count_{char}'] = char_counts.get(char, 0)
        features[f'freq_{char}'] = char_counts.get(char, 0) / len(series) if len(series) > 0 else 0
    
    # Symbol diversity
    features['unique_symbols'] = len(set(series))
    features['symbol_diversity'] = len(set(series)) / len(series) if len(series) > 0 else 0
    
    # Run-length features (consecutive identical symbols)
    runs = []
    current_run = 1
    for i in range(1, len(series)):
        if series[i] == series[i-1]:
            current_run += 1
        else:
            runs.append(current_run)
            current_run = 1
    runs.append(current_run)
    
    features['num_runs'] = len(runs)
    features['mean_run_length'] = np.mean(runs) if runs else 0
    features['max_run_length'] = max(runs) if runs else 0
    features['std_run_length'] = np.std(runs) if runs else 0
    
    # Special symbol patterns
    features['num_asterisks'] = series.count('*')
    features['num_dots'] = series.count('.')
    features['asterisk_ratio'] = features['num_asterisks'] / len(series) if len(series) > 0 else 0
    
    # Transition features (changes between symbol types)
    transitions = 0
    for i in range(1, len(series)):
        if series[i] != series[i-1]:
            transitions += 1
    features['transitions'] = transitions
    features['transition_rate'] = transitions / len(series) if len(series) > 0 else 0
    
    # Pattern features - count specific patterns
    features['double_asterisk'] = series.count('**')
    features['triple_asterisk'] = series.count('***')
    
    # Position-based features (first and last symbols)
    features['starts_with_asterisk'] = 1 if series[0] == '*' else 0 if len(series) > 0 else 0
    features['ends_with_asterisk'] = 1 if series[-1] == '*' else 0 if len(series) > 0 else 0
    
    return features

# Extract features for all datasets
print("\nExtracting features...")

train_features = train_df['symbol_series'].apply(extract_symbol_features)
val_features = val_df['symbol_series'].apply(extract_symbol_features)
test_features = test_df['symbol_series'].apply(extract_symbol_features)

# Convert to DataFrames
X_train = pd.DataFrame(train_features.tolist())
X_val = pd.DataFrame(val_features.tolist())
X_test = pd.DataFrame(test_features.tolist())

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values

print(f"Feature matrix shape: {X_train.shape}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Train multiple models
print("\nTraining models...")

models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42),
    'SVM': SVC(kernel='rbf', probability=True, random_state=42)
}

results = {}

for name, model in models.items():
    print(f"\nTraining {name}...")
    
    if name == 'Logistic Regression' or name == 'SVM':
        model.fit(X_train_scaled, y_train)
        val_pred = model.predict(X_val_scaled)
        val_proba = model.predict_proba(X_val_scaled)[:, 1]
        test_pred = model.predict(X_test_scaled)
        test_proba = model.predict_proba(X_test_scaled)[:, 1]
    else:
        model.fit(X_train, y_train)
        val_pred = model.predict(X_val)
        val_proba = model.predict_proba(X_val)[:, 1]
        test_pred = model.predict(X_test)
        test_proba = model.predict_proba(X_test)[:, 1]
    
    val_bal_acc = balanced_accuracy_score(y_val, val_pred)
    test_bal_acc = balanced_accuracy_score(y_test, test_pred)
    val_auc = roc_auc_score(y_val, val_proba)
    test_auc = roc_auc_score(y_test, test_proba)
    
    results[name] = {
        'val_bal_acc': val_bal_acc,
        'test_bal_acc': test_bal_acc,
        'val_auc': val_auc,
        'test_auc': test_auc,
        'val_pred': val_pred,
        'test_pred': test_pred,
        'val_proba': val_proba,
        'test_proba': test_proba,
        'model': model
    }
    
    print(f"  Val Balanced Accuracy: {val_bal_acc:.4f}")
    print(f"  Test Balanced Accuracy: {test_bal_acc:.4f}")
    print(f"  Val AUC: {val_auc:.4f}")
    print(f"  Test AUC: {test_auc:.4f}")

# Find best model
best_model_name = max(results, key=lambda x: results[x]['test_bal_acc'])
print(f"\nBest model: {best_model_name}")
print(f"Test Balanced Accuracy: {results[best_model_name]['test_bal_acc']:.4f}")

# Save results
print("\nSaving results...")

# Create results summary
results_summary = []
for name, res in results.items():
    results_summary.append({
        'Model': name,
        'Val_Balanced_Accuracy': res['val_bal_acc'],
        'Test_Balanced_Accuracy': res['test_bal_acc'],
        'Val_AUC': res['val_auc'],
        'Test_AUC': res['test_auc']
    })

results_df = pd.DataFrame(results_summary)
results_df.to_csv('outputs/model_comparison.csv', index=False)
print("Results saved to outputs/model_comparison.csv")

# Generate visualizations
print("\nGenerating visualizations...")

# Figure 1: Model Comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Balanced Accuracy comparison
models_list = list(results.keys())
val_accs = [results[m]['val_bal_acc'] for m in models_list]
test_accs = [results[m]['test_bal_acc'] for m in models_list]

x = np.arange(len(models_list))
width = 0.35

axes[0].bar(x - width/2, val_accs, width, label='Validation', alpha=0.8)
axes[0].bar(x + width/2, test_accs, width, label='Test', alpha=0.8)
axes[0].set_ylabel('Balanced Accuracy')
axes[0].set_title('Model Performance Comparison')
axes[0].set_xticks(x)
axes[0].set_xticklabels(models_list, rotation=45, ha='right')
axes[0].legend()
axes[0].axhline(y=0.78, color='r', linestyle='--', label='Baseline (0.78)')
axes[0].set_ylim([0.5, 1.0])

# AUC comparison
val_aucs = [results[m]['val_auc'] for m in models_list]
test_aucs = [results[m]['test_auc'] for m in models_list]

axes[1].bar(x - width/2, val_aucs, width, label='Validation', alpha=0.8)
axes[1].bar(x + width/2, test_aucs, width, label='Test', alpha=0.8)
axes[1].set_ylabel('AUC Score')
axes[1].set_title('AUC Score Comparison')
axes[1].set_xticks(x)
axes[1].set_xticklabels(models_list, rotation=45, ha='right')
axes[1].legend()
axes[1].set_ylim([0.5, 1.0])

plt.tight_layout()
plt.savefig('report/images/model_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: ROC Curves
plt.figure(figsize=(10, 8))
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res['test_proba'])
    plt.plot(fpr, tpr, label=f"{name} (AUC = {res['test_auc']:.3f})", linewidth=2)

plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curves - Test Set')
plt.legend(loc='lower right')
plt.grid(True, alpha=0.3)
plt.savefig('report/images/roc_curves.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 3: Confusion Matrix for Best Model
best_model = results[best_model_name]
cm = confusion_matrix(y_test, best_model['test_pred'])

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Non-Variable', 'Variable'],
            yticklabels=['Non-Variable', 'Variable'])
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title(f'Confusion Matrix - {best_model_name}')
plt.savefig('report/images/confusion_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 4: Feature Importance (for tree-based models)
if hasattr(results['Random Forest']['model'], 'feature_importances_'):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Random Forest
    rf_importance = results['Random Forest']['model'].feature_importances_
    rf_indices = np.argsort(rf_importance)[-15:]  # Top 15 features
    axes[0].barh(range(len(rf_indices)), rf_importance[rf_indices])
    axes[0].set_yticks(range(len(rf_indices)))
    axes[0].set_yticklabels([X_train.columns[i] for i in rf_indices])
    axes[0].set_xlabel('Feature Importance')
    axes[0].set_title('Random Forest - Top 15 Features')
    
    # Gradient Boosting
    gb_importance = results['Gradient Boosting']['model'].feature_importances_
    gb_indices = np.argsort(gb_importance)[-15:]  # Top 15 features
    axes[1].barh(range(len(gb_indices)), gb_importance[gb_indices])
    axes[1].set_yticks(range(len(gb_indices)))
    axes[1].set_yticklabels([X_train.columns[i] for i in gb_indices])
    axes[1].set_xlabel('Feature Importance')
    axes[1].set_title('Gradient Boosting - Top 15 Features')
    
    plt.tight_layout()
    plt.savefig('report/images/feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()

# Figure 5: Data Distribution Analysis
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Symbol frequency by class
symbol_cols = ['freq_u', 'freq_v', 'freq_w', 'freq_x', 'freq_y', 'freq_z', 'freq_*', 'freq_.']
symbol_means_var = X_train[y_train == 1][symbol_cols].mean()
symbol_means_nonvar = X_train[y_train == 0][symbol_cols].mean()

x_pos = np.arange(len(symbol_cols))
axes[0, 0].bar(x_pos - 0.2, symbol_means_nonvar, 0.4, label='Non-Variable', alpha=0.8)
axes[0, 0].bar(x_pos + 0.2, symbol_means_var, 0.4, label='Variable', alpha=0.8)
axes[0, 0].set_xticks(x_pos)
axes[0, 0].set_xticklabels(['u', 'v', 'w', 'x', 'y', 'z', '*', '.'])
axes[0, 0].set_ylabel('Mean Frequency')
axes[0, 0].set_title('Symbol Frequency by Class')
axes[0, 0].legend()

# Length distribution
axes[0, 1].hist(X_train[y_train == 0]['length'], bins=20, alpha=0.5, label='Non-Variable', density=True)
axes[0, 1].hist(X_train[y_train == 1]['length'], bins=20, alpha=0.5, label='Variable', density=True)
axes[0, 1].set_xlabel('Series Length')
axes[0, 1].set_ylabel('Density')
axes[0, 1].set_title('Distribution of Series Length')
axes[0, 1].legend()

# Asterisk ratio
axes[1, 0].hist(X_train[y_train == 0]['asterisk_ratio'], bins=20, alpha=0.5, label='Non-Variable', density=True)
axes[1, 0].hist(X_train[y_train == 1]['asterisk_ratio'], bins=20, alpha=0.5, label='Variable', density=True)
axes[1, 0].set_xlabel('Asterisk Ratio')
axes[1, 0].set_ylabel('Density')
axes[1, 0].set_title('Distribution of Asterisk Ratio')
axes[1, 0].legend()

# Transition rate
axes[1, 1].hist(X_train[y_train == 0]['transition_rate'], bins=20, alpha=0.5, label='Non-Variable', density=True)
axes[1, 1].hist(X_train[y_train == 1]['transition_rate'], bins=20, alpha=0.5, label='Variable', density=True)
axes[1, 1].set_xlabel('Transition Rate')
axes[1, 1].set_ylabel('Density')
axes[1, 1].set_title('Distribution of Transition Rate')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('report/images/data_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# Save classification report for best model
report = classification_report(y_test, best_model['test_pred'], 
                               target_names=['Non-Variable', 'Variable'])
with open('outputs/classification_report.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test Balanced Accuracy: {best_model['test_bal_acc']:.4f}\n")
    f.write(f"Test AUC: {best_model['test_auc']:.4f}\n\n")
    f.write(report)

print("\nClassification report saved to outputs/classification_report.txt")

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test_df['object_id'],
    'true_label': y_test,
    'predicted_label': best_model['test_pred'],
    'probability': best_model['test_proba']
})
predictions_df.to_csv('outputs/test_predictions.csv', index=False)
print("Predictions saved to outputs/test_predictions.csv")

print("\nAnalysis complete!")
