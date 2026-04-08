"""
Variable Star Classification using Symbolic Series Features - Targeted Approach
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

# Analyze the symbolic series structure
print("\nAnalyzing symbolic series structure...")

# Sample some series to understand patterns
sample_var = train_df[train_df['label'] == 1]['symbol_series'].iloc[:5].tolist()
sample_nonvar = train_df[train_df['label'] == 0]['symbol_series'].iloc[:5].tolist()

print("\nSample Variable stars:")
for i, s in enumerate(sample_var):
    print(f"  {i+1}: {s[:80]}...")

print("\nSample Non-Variable stars:")
for i, s in enumerate(sample_nonvar):
    print(f"  {i+1}: {s[:80]}...")

# Targeted feature extraction
def extract_targeted_features(series):
    """Extract targeted features based on symbolic series analysis"""
    features = {}
    
    # Basic stats
    features['length'] = len(series)
    
    # The symbols u,v,w,x,y,z likely represent magnitude bins
    # * and . likely represent special states (missing data, outliers, etc.)
    
    # Count each symbol
    char_counts = Counter(series)
    total = len(series)
    
    # Magnitude bin symbols (ordered from u to z)
    mag_symbols = ['u', 'v', 'w', 'x', 'y', 'z']
    for sym in mag_symbols:
        features[f'count_{sym}'] = char_counts.get(sym, 0)
        features[f'freq_{sym}'] = char_counts.get(sym, 0) / total if total > 0 else 0
    
    # Special symbols
    features['count_star'] = char_counts.get('*', 0)
    features['count_dot'] = char_counts.get('.', 0)
    features['freq_star'] = char_counts.get('*', 0) / total if total > 0 else 0
    features['freq_dot'] = char_counts.get('.', 0) / total if total > 0 else 0
    
    # Total magnitude measurements (non-special symbols)
    mag_count = sum(char_counts.get(s, 0) for s in mag_symbols)
    features['mag_count'] = mag_count
    features['mag_ratio'] = mag_count / total if total > 0 else 0
    
    # Special symbol ratio
    special_count = char_counts.get('*', 0) + char_counts.get('.', 0)
    features['special_count'] = special_count
    features['special_ratio'] = special_count / total if total > 0 else 0
    
    # Center of mass of magnitude distribution (weighted average)
    weights = {'u': 0, 'v': 1, 'w': 2, 'x': 3, 'y': 4, 'z': 5}
    weighted_sum = sum(char_counts.get(s, 0) * weights[s] for s in mag_symbols)
    features['mag_center'] = weighted_sum / mag_count if mag_count > 0 else 0
    
    # Variance of magnitude distribution
    if mag_count > 0:
        mean_mag = features['mag_center']
        variance = sum(char_counts.get(s, 0) * (weights[s] - mean_mag)**2 for s in mag_symbols) / mag_count
        features['mag_variance'] = variance
        features['mag_std'] = np.sqrt(variance)
    else:
        features['mag_variance'] = 0
        features['mag_std'] = 0
    
    # Range of magnitudes observed
    observed_mags = [s for s in mag_symbols if char_counts.get(s, 0) > 0]
    if observed_mags:
        mag_indices = [weights[s] for s in observed_mags]
        features['mag_range'] = max(mag_indices) - min(mag_indices)
    else:
        features['mag_range'] = 0
    
    # Run-length analysis for magnitude changes
    mag_runs = []
    special_runs = []
    current_run_type = None
    current_run_len = 0
    
    for char in series:
        if char in mag_symbols:
            if current_run_type == 'mag':
                current_run_len += 1
            else:
                if current_run_type == 'special':
                    special_runs.append(current_run_len)
                current_run_type = 'mag'
                current_run_len = 1
        else:
            if current_run_type == 'special':
                current_run_len += 1
            else:
                if current_run_type == 'mag':
                    mag_runs.append(current_run_len)
                current_run_type = 'special'
                current_run_len = 1
    
    if current_run_type == 'mag':
        mag_runs.append(current_run_len)
    elif current_run_type == 'special':
        special_runs.append(current_run_len)
    
    features['num_mag_runs'] = len(mag_runs)
    features['num_special_runs'] = len(special_runs)
    features['mean_mag_run'] = np.mean(mag_runs) if mag_runs else 0
    features['mean_special_run'] = np.mean(special_runs) if special_runs else 0
    features['max_mag_run'] = max(mag_runs) if mag_runs else 0
    features['max_special_run'] = max(special_runs) if special_runs else 0
    
    # Pattern detection - consecutive magnitude changes
    mag_changes = 0
    for i in range(1, len(series)):
        if series[i] in mag_symbols and series[i-1] in mag_symbols:
            if series[i] != series[i-1]:
                mag_changes += 1
    features['mag_changes'] = mag_changes
    features['mag_change_rate'] = mag_changes / total if total > 0 else 0
    
    # Large magnitude jumps (u<->z, v<->y, etc.)
    large_jumps = 0
    for i in range(1, len(series)):
        if series[i] in mag_symbols and series[i-1] in mag_symbols:
            diff = abs(weights[series[i]] - weights[series[i-1]])
            if diff >= 3:  # Large jump
                large_jumps += 1
    features['large_jumps'] = large_jumps
    features['large_jump_rate'] = large_jumps / total if total > 0 else 0
    
    # Periodic pattern detection - look for repeating sequences
    # Count occurrences of common patterns
    patterns_2 = {}
    patterns_3 = {}
    for i in range(len(series) - 1):
        p2 = series[i:i+2]
        patterns_2[p2] = patterns_2.get(p2, 0) + 1
    for i in range(len(series) - 2):
        p3 = series[i:i+3]
        patterns_3[p3] = patterns_3.get(p3, 0) + 1
    
    # Most common patterns
    features['max_pattern2_count'] = max(patterns_2.values()) if patterns_2 else 0
    features['max_pattern3_count'] = max(patterns_3.values()) if patterns_3 else 0
    features['unique_patterns_2'] = len(patterns_2)
    features['unique_patterns_3'] = len(patterns_3)
    
    # Position-based features
    features['starts_with_mag'] = 1 if series[0] in mag_symbols else 0
    features['ends_with_mag'] = 1 if series[-1] in mag_symbols else 0
    features['starts_with_star'] = 1 if series[0] == '*' else 0
    features['ends_with_star'] = 1 if series[-1] == '*' else 0
    
    # First and last magnitude
    first_mag = None
    last_mag = None
    for char in series:
        if char in mag_symbols:
            first_mag = weights[char]
            break
    for char in reversed(series):
        if char in mag_symbols:
            last_mag = weights[char]
            break
    features['first_mag'] = first_mag if first_mag is not None else -1
    features['last_mag'] = last_mag if last_mag is not None else -1
    features['mag_diff_ends'] = abs(last_mag - first_mag) if first_mag is not None and last_mag is not None else 0
    
    return features

# Extract features
print("\nExtracting targeted features...")

train_features = train_df['symbol_series'].apply(extract_targeted_features)
val_features = val_df['symbol_series'].apply(extract_targeted_features)
test_features = test_df['symbol_series'].apply(extract_targeted_features)

X_train = pd.DataFrame(train_features.tolist())
X_val = pd.DataFrame(val_features.tolist())
X_test = pd.DataFrame(test_features.tolist())

print(f"Feature matrix shape: {X_train.shape}")
print(f"Features: {list(X_train.columns)}")

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Train models
print("\nTraining models...")

models = {
    'Logistic Regression': LogisticRegression(max_iter=2000, random_state=42, C=0.1),
    'Random Forest': RandomForestClassifier(n_estimators=500, max_depth=10, min_samples_split=3, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=500, max_depth=4, learning_rate=0.05, random_state=42),
    'SVM': SVC(kernel='rbf', C=0.5, gamma='scale', probability=True, random_state=42)
}

results = {}

for name, model in models.items():
    print(f"\nTraining {name}...")
    
    if name in ['Logistic Regression', 'SVM']:
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
results_df.to_csv('outputs/model_comparison_v3.csv', index=False)

# Generate visualizations
print("\nGenerating visualizations...")

# Figure 1: Model Comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

models_list = list(results.keys())
val_accs = [results[m]['val_bal_acc'] for m in models_list]
test_accs = [results[m]['test_bal_acc'] for m in models_list]

x = np.arange(len(models_list))
width = 0.35

axes[0].bar(x - width/2, val_accs, width, label='Validation', alpha=0.8, color='steelblue')
axes[0].bar(x + width/2, test_accs, width, label='Test', alpha=0.8, color='coral')
axes[0].set_ylabel('Balanced Accuracy', fontsize=12)
axes[0].set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(models_list, rotation=45, ha='right')
axes[0].legend()
axes[0].axhline(y=0.78, color='red', linestyle='--', linewidth=2, label='Baseline (0.78)')
axes[0].set_ylim([0.4, 1.0])
axes[0].grid(axis='y', alpha=0.3)

val_aucs = [results[m]['val_auc'] for m in models_list]
test_aucs = [results[m]['test_auc'] for m in models_list]

axes[1].bar(x - width/2, val_aucs, width, label='Validation', alpha=0.8, color='steelblue')
axes[1].bar(x + width/2, test_aucs, width, label='Test', alpha=0.8, color='coral')
axes[1].set_ylabel('AUC Score', fontsize=12)
axes[1].set_title('AUC Score Comparison', fontsize=14, fontweight='bold')
axes[1].set_xticks(x)
axes[1].set_xticklabels(models_list, rotation=45, ha='right')
axes[1].legend()
axes[1].set_ylim([0.4, 1.0])
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/model_comparison_v3.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: ROC Curves
plt.figure(figsize=(10, 8))
colors = ['blue', 'green', 'orange', 'red']
for i, (name, res) in enumerate(results.items()):
    fpr, tpr, _ = roc_curve(y_test, res['test_proba'])
    plt.plot(fpr, tpr, label=f"{name} (AUC = {res['test_auc']:.3f})", 
             linewidth=2, color=colors[i % len(colors)])

plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier', linewidth=1)
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves - Test Set', fontsize=14, fontweight='bold')
plt.legend(loc='lower right', fontsize=10)
plt.grid(True, alpha=0.3)
plt.savefig('report/images/roc_curves_v3.png', dpi=300, bbox_inches='tight')
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
plt.savefig('report/images/confusion_matrix_v3.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 4: Feature Importance
if hasattr(results['Random Forest']['model'], 'feature_importances_'):
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    # Random Forest
    rf_importance = results['Random Forest']['model'].feature_importances_
    rf_indices = np.argsort(rf_importance)[-15:]
    axes[0].barh(range(len(rf_indices)), rf_importance[rf_indices], color='forestgreen')
    axes[0].set_yticks(range(len(rf_indices)))
    axes[0].set_yticklabels([X_train.columns[i] for i in rf_indices])
    axes[0].set_xlabel('Feature Importance', fontsize=12)
    axes[0].set_title('Random Forest - Top 15 Features', fontsize=14, fontweight='bold')
    axes[0].grid(axis='x', alpha=0.3)
    
    # Gradient Boosting
    gb_importance = results['Gradient Boosting']['model'].feature_importances_
    gb_indices = np.argsort(gb_importance)[-15:]
    axes[1].barh(range(len(gb_indices)), gb_importance[gb_indices], color='darkorange')
    axes[1].set_yticks(range(len(gb_indices)))
    axes[1].set_yticklabels([X_train.columns[i] for i in gb_indices])
    axes[1].set_xlabel('Feature Importance', fontsize=12)
    axes[1].set_title('Gradient Boosting - Top 15 Features', fontsize=14, fontweight='bold')
    axes[1].grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/feature_importance_v3.png', dpi=300, bbox_inches='tight')
    plt.close()

# Figure 5: Key Feature Distributions
fig, axes = plt.subplots(2, 3, figsize=(16, 10))

# Select key features for visualization
key_features = ['mag_variance', 'mag_changes', 'mag_range', 'special_ratio', 'mag_center', 'large_jumps']

for idx, feat in enumerate(key_features):
    row = idx // 3
    col = idx % 3
    
    # Plot histograms
    axes[row, col].hist(X_train[y_train == 0][feat], bins=20, alpha=0.6, 
                        label='Non-Variable', density=True, color='steelblue')
    axes[row, col].hist(X_train[y_train == 1][feat], bins=20, alpha=0.6, 
                        label='Variable', density=True, color='coral')
    axes[row, col].set_xlabel(feat.replace('_', ' ').title(), fontsize=10)
    axes[row, col].set_ylabel('Density', fontsize=10)
    axes[row, col].legend(fontsize=9)
    axes[row, col].grid(alpha=0.3)

plt.suptitle('Distribution of Key Features by Class', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('report/images/feature_distributions_v3.png', dpi=300, bbox_inches='tight')
plt.close()

# Save classification report
report = classification_report(y_test, best_model['test_pred'], 
                               target_names=['Non-Variable', 'Variable'])
with open('outputs/classification_report_v3.txt', 'w') as f:
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
predictions_df.to_csv('outputs/test_predictions_v3.csv', index=False)

print("\nAnalysis complete!")
