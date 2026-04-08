"""
Variable Star Classification - Advanced Feature Engineering
AstroML Time-Domain Survey Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
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

# Combine train and val for cross-validation
combined_df = pd.concat([train_df, val_df], ignore_index=True)

print(f"Train size: {len(train_df)}")
print(f"Val size: {len(val_df)}")
print(f"Test size: {len(test_df)}")
print(f"Combined size: {len(combined_df)}")

# Advanced feature extraction
def extract_advanced_features(series):
    """Extract advanced features from symbolic series"""
    features = {}
    n = len(series)
    
    # Basic length
    features['length'] = n
    
    # Symbol counts and frequencies
    symbols = ['u', 'v', 'w', 'x', 'y', 'z', '*', '.']
    char_counts = Counter(series)
    
    for sym in symbols:
        features[f'cnt_{sym}'] = char_counts.get(sym, 0)
        features[f'freq_{sym}'] = char_counts.get(sym, 0) / n if n > 0 else 0
    
    # Statistical features of symbol distribution
    counts = [char_counts.get(s, 0) for s in symbols]
    features['count_mean'] = np.mean(counts)
    features['count_std'] = np.std(counts)
    features['count_max'] = max(counts)
    features['count_min'] = min(counts)
    
    # Entropy of symbol distribution
    entropy = 0
    for c in counts:
        if c > 0:
            p = c / n
            entropy -= p * np.log2(p)
    features['entropy'] = entropy
    
    # Run-length encoding features
    runs = []
    run_chars = []
    current_char = series[0] if n > 0 else ''
    current_len = 1
    
    for i in range(1, n):
        if series[i] == current_char:
            current_len += 1
        else:
            runs.append(current_len)
            run_chars.append(current_char)
            current_char = series[i]
            current_len = 1
    runs.append(current_len)
    run_chars.append(current_char)
    
    features['num_runs'] = len(runs)
    features['mean_run'] = np.mean(runs)
    features['std_run'] = np.std(runs)
    features['max_run'] = max(runs)
    features['min_run'] = min(runs)
    
    # Run statistics by symbol type
    mag_runs = [runs[i] for i in range(len(runs)) if run_chars[i] in 'uvwxyz']
    special_runs = [runs[i] for i in range(len(runs)) if run_chars[i] in '*.']
    
    features['mag_run_mean'] = np.mean(mag_runs) if mag_runs else 0
    features['mag_run_max'] = max(mag_runs) if mag_runs else 0
    features['special_run_mean'] = np.mean(special_runs) if special_runs else 0
    features['special_run_max'] = max(special_runs) if special_runs else 0
    
    # Transition analysis
    transitions = sum(1 for i in range(1, n) if series[i] != series[i-1])
    features['transitions'] = transitions
    features['transition_rate'] = transitions / n if n > 0 else 0
    
    # Magnitude-related features (u=bright, z=faint)
    mag_weights = {'u': 0, 'v': 1, 'w': 2, 'x': 3, 'y': 4, 'z': 5}
    
    # Weighted position features
    weighted_pos = 0
    total_weight = 0
    for i, char in enumerate(series):
        if char in mag_weights:
            weighted_pos += mag_weights[char] * i
            total_weight += mag_weights[char]
    features['weighted_pos'] = weighted_pos / n if n > 0 else 0
    
    # Magnitude variance (light curve variability)
    mag_values = [mag_weights[c] for c in series if c in mag_weights]
    if mag_values:
        features['mag_mean'] = np.mean(mag_values)
        features['mag_std'] = np.std(mag_values)
        features['mag_range'] = max(mag_values) - min(mag_values)
        features['mag_min'] = min(mag_values)
        features['mag_max'] = max(mag_values)
    else:
        features['mag_mean'] = 0
        features['mag_std'] = 0
        features['mag_range'] = 0
        features['mag_min'] = 0
        features['mag_max'] = 0
    
    # Pattern features - look for periodicity indicators
    # Count repeated patterns of length 2-5
    for pattern_len in [2, 3, 4, 5]:
        patterns = {}
        for i in range(n - pattern_len + 1):
            p = series[i:i+pattern_len]
            patterns[p] = patterns.get(p, 0) + 1
        
        if patterns:
            features[f'pattern{pattern_len}_max'] = max(patterns.values())
            features[f'pattern{pattern_len}_unique'] = len(patterns)
            features[f'pattern{pattern_len}_ratio'] = max(patterns.values()) / len(patterns) if patterns else 0
    
    # Position-based features
    first_quarter = series[:n//4] if n > 0 else ''
    last_quarter = series[3*n//4:] if n > 0 else ''
    
    features['first_q_stars'] = first_quarter.count('*')
    features['last_q_stars'] = last_quarter.count('*')
    features['first_q_dots'] = first_quarter.count('.')
    features['last_q_dots'] = last_quarter.count('.')
    
    # Change detection - count direction changes in magnitude
    direction_changes = 0
    last_direction = 0  # -1: decreasing, 1: increasing, 0: unknown
    
    for i in range(1, n):
        if series[i] in mag_weights and series[i-1] in mag_weights:
            curr_mag = mag_weights[series[i]]
            prev_mag = mag_weights[series[i-1]]
            
            if curr_mag > prev_mag:
                direction = 1
            elif curr_mag < prev_mag:
                direction = -1
            else:
                continue
            
            if last_direction != 0 and direction != last_direction:
                direction_changes += 1
            last_direction = direction
    
    features['direction_changes'] = direction_changes
    features['direction_change_rate'] = direction_changes / n if n > 0 else 0
    
    # Peak detection - local maxima and minima in magnitude
    peaks = 0
    valleys = 0
    
    for i in range(1, n-1):
        if series[i] in mag_weights and series[i-1] in mag_weights and series[i+1] in mag_weights:
            curr = mag_weights[series[i]]
            prev = mag_weights[series[i-1]]
            next_val = mag_weights[series[i+1]]
            
            if curr > prev and curr > next_val:
                peaks += 1
            elif curr < prev and curr < next_val:
                valleys += 1
    
    features['peaks'] = peaks
    features['valleys'] = valleys
    features['peak_valley_ratio'] = (peaks + valleys) / n if n > 0 else 0
    
    return features

# Extract features
print("\nExtracting advanced features...")

train_features = train_df['symbol_series'].apply(extract_advanced_features)
val_features = val_df['symbol_series'].apply(extract_advanced_features)
test_features = test_df['symbol_series'].apply(extract_advanced_features)
combined_features = combined_df['symbol_series'].apply(extract_advanced_features)

X_train = pd.DataFrame(train_features.tolist())
X_val = pd.DataFrame(val_features.tolist())
X_test = pd.DataFrame(test_features.tolist())
X_combined = pd.DataFrame(combined_features.tolist())

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values
y_combined = combined_df['label'].values

print(f"Feature matrix shape: {X_train.shape}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)
X_combined_scaled = scaler.fit_transform(X_combined)

# Train models with cross-validation
print("\nTraining models with cross-validation...")

models = {
    'Logistic Regression': LogisticRegression(max_iter=2000, random_state=42, C=1.0),
    'Random Forest': RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_split=4, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.1, random_state=42),
    'SVM': SVC(kernel='rbf', C=1.0, probability=True, random_state=42),
    'KNN': KNeighborsClassifier(n_neighbors=5)
}

results = {}
cv_scores = {}

# Cross-validation on combined data
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for name, model in models.items():
    print(f"\nTraining {name}...")
    
    # Cross-validation
    if name in ['Logistic Regression', 'SVM', 'KNN']:
        cv_score = cross_val_score(model, X_combined_scaled, y_combined, cv=cv, scoring='balanced_accuracy')
        model.fit(X_combined_scaled, y_combined)
        test_pred = model.predict(X_test_scaled)
        test_proba = model.predict_proba(X_test_scaled)[:, 1]
    else:
        cv_score = cross_val_score(model, X_combined, y_combined, cv=cv, scoring='balanced_accuracy')
        model.fit(X_combined, y_combined)
        test_pred = model.predict(X_test)
        test_proba = model.predict_proba(X_test)[:, 1]
    
    test_bal_acc = balanced_accuracy_score(y_test, test_pred)
    test_auc = roc_auc_score(y_test, test_proba)
    
    results[name] = {
        'cv_mean': cv_score.mean(),
        'cv_std': cv_score.std(),
        'test_bal_acc': test_bal_acc,
        'test_auc': test_auc,
        'test_pred': test_pred,
        'test_proba': test_proba,
        'model': model
    }
    
    cv_scores[name] = cv_score
    
    print(f"  CV Balanced Accuracy: {cv_score.mean():.4f} (+/- {cv_score.std()*2:.4f})")
    print(f"  Test Balanced Accuracy: {test_bal_acc:.4f}")
    print(f"  Test AUC: {test_auc:.4f}")

# Try ensemble methods
print("\nTraining ensemble models...")

# Voting classifier
estimators = [
    ('lr', LogisticRegression(max_iter=2000, random_state=42, C=1.0)),
    ('rf', RandomForestClassifier(n_estimators=200, random_state=42)),
    ('gb', GradientBoostingClassifier(n_estimators=200, random_state=42))
]

voting_clf = VotingClassifier(estimators=estimators, voting='soft')
voting_clf.fit(X_combined_scaled, y_combined)
voting_pred = voting_clf.predict(X_test_scaled)
voting_proba = voting_clf.predict_proba(X_test_scaled)[:, 1]
voting_bal_acc = balanced_accuracy_score(y_test, voting_pred)
voting_auc = roc_auc_score(y_test, voting_proba)

results['Voting Ensemble'] = {
    'cv_mean': voting_bal_acc,  # No CV for ensemble
    'cv_std': 0,
    'test_bal_acc': voting_bal_acc,
    'test_auc': voting_auc,
    'test_pred': voting_pred,
    'test_proba': voting_proba,
    'model': voting_clf
}

print(f"  Voting Ensemble Test Balanced Accuracy: {voting_bal_acc:.4f}")
print(f"  Voting Ensemble Test AUC: {voting_auc:.4f}")

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
        'CV_Mean': res['cv_mean'],
        'CV_Std': res['cv_std'],
        'Test_Balanced_Accuracy': res['test_bal_acc'],
        'Test_AUC': res['test_auc']
    })

results_df = pd.DataFrame(results_summary)
results_df.to_csv('outputs/model_comparison_v4.csv', index=False)

# Generate visualizations
print("\nGenerating visualizations...")

# Figure 1: Model Comparison with CV
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

models_list = list(results.keys())
cv_means = [results[m]['cv_mean'] for m in models_list]
cv_stds = [results[m]['cv_std'] for m in models_list]
test_accs = [results[m]['test_bal_acc'] for m in models_list]

x = np.arange(len(models_list))
width = 0.35

# CV scores with error bars
axes[0].bar(x - width/2, cv_means, width, yerr=cv_stds, label='CV Score', alpha=0.8, 
            color='steelblue', capsize=5)
axes[0].bar(x + width/2, test_accs, width, label='Test Score', alpha=0.8, color='coral')
axes[0].set_ylabel('Balanced Accuracy', fontsize=12)
axes[0].set_title('Model Performance with Cross-Validation', fontsize=14, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(models_list, rotation=45, ha='right')
axes[0].legend()
axes[0].axhline(y=0.78, color='red', linestyle='--', linewidth=2, label='Baseline (0.78)')
axes[0].set_ylim([0.3, 1.0])
axes[0].grid(axis='y', alpha=0.3)

# AUC comparison
test_aucs = [results[m]['test_auc'] for m in models_list]
axes[1].bar(x, test_aucs, alpha=0.8, color='forestgreen')
axes[1].set_ylabel('AUC Score', fontsize=12)
axes[1].set_title('Test AUC Comparison', fontsize=14, fontweight='bold')
axes[1].set_xticks(x)
axes[1].set_xticklabels(models_list, rotation=45, ha='right')
axes[1].set_ylim([0.3, 1.0])
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/model_comparison_v4.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: Cross-validation box plot
plt.figure(figsize=(10, 6))
cv_data = [cv_scores[m] for m in models.keys() if m in cv_scores]
labels = [m for m in models.keys() if m in cv_scores]
bp = plt.boxplot(cv_data, labels=labels, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('lightblue')
plt.ylabel('Balanced Accuracy', fontsize=12)
plt.title('Cross-Validation Score Distribution (5-Fold)', fontsize=14, fontweight='bold')
plt.xticks(rotation=45, ha='right')
plt.axhline(y=0.78, color='red', linestyle='--', linewidth=2, label='Baseline (0.78)')
plt.legend()
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/cv_boxplot_v4.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 3: ROC Curves
plt.figure(figsize=(10, 8))
colors = plt.cm.tab10(np.linspace(0, 1, len(results)))
for i, (name, res) in enumerate(results.items()):
    fpr, tpr, _ = roc_curve(y_test, res['test_proba'])
    plt.plot(fpr, tpr, label=f"{name} (AUC = {res['test_auc']:.3f})", 
             linewidth=2, color=colors[i])

plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier', linewidth=1)
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.title('ROC Curves - Test Set', fontsize=14, fontweight='bold')
plt.legend(loc='lower right', fontsize=9)
plt.grid(True, alpha=0.3)
plt.savefig('report/images/roc_curves_v4.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 4: Confusion Matrix for Best Model
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
plt.savefig('report/images/confusion_matrix_v4.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 5: Feature Importance
if hasattr(results['Random Forest']['model'], 'feature_importances_'):
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    # Random Forest
    rf_importance = results['Random Forest']['model'].feature_importances_
    rf_indices = np.argsort(rf_importance)[-20:]
    axes[0].barh(range(len(rf_indices)), rf_importance[rf_indices], color='forestgreen')
    axes[0].set_yticks(range(len(rf_indices)))
    axes[0].set_yticklabels([X_train.columns[i] for i in rf_indices])
    axes[0].set_xlabel('Feature Importance', fontsize=12)
    axes[0].set_title('Random Forest - Top 20 Features', fontsize=14, fontweight='bold')
    axes[0].grid(axis='x', alpha=0.3)
    
    # Gradient Boosting
    gb_importance = results['Gradient Boosting']['model'].feature_importances_
    gb_indices = np.argsort(gb_importance)[-20:]
    axes[1].barh(range(len(gb_indices)), gb_importance[gb_indices], color='darkorange')
    axes[1].set_yticks(range(len(gb_indices)))
    axes[1].set_yticklabels([X_train.columns[i] for i in gb_indices])
    axes[1].set_xlabel('Feature Importance', fontsize=12)
    axes[1].set_title('Gradient Boosting - Top 20 Features', fontsize=14, fontweight='bold')
    axes[1].grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/feature_importance_v4.png', dpi=300, bbox_inches='tight')
    plt.close()

# Save classification report
report = classification_report(y_test, best_model['test_pred'], 
                               target_names=['Non-Variable', 'Variable'])
with open('outputs/classification_report_v4.txt', 'w') as f:
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
predictions_df.to_csv('outputs/test_predictions_v4.csv', index=False)

print("\nAnalysis complete!")
