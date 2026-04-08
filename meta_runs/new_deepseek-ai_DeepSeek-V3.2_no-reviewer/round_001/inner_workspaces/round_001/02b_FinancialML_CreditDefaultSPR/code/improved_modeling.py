import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import roc_auc_score, classification_report, roc_curve, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, StackingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
import pickle
warnings.filterwarnings('ignore')

# Load alternative features
train_features = pd.read_csv('../outputs/train_features_alt.csv')
val_features = pd.read_csv('../outputs/val_features_alt.csv')
test_features = pd.read_csv('../outputs/test_features_alt.csv')

train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

y_train = train['default_flag'].values
y_val = val['default_flag'].values
y_test = test['default_flag'].values

print("=== Improved Modeling with Alternative Features ===")
print(f"Training samples: {len(train_features)}")
print(f"Number of features: {train_features.shape[1]}")

# Handle missing values (replace -1 with NaN then fill)
train_features = train_features.replace(-1, np.nan)
val_features = val_features.replace(-1, np.nan)
test_features = test_features.replace(-1, np.nan)

# Fill missing values with column means
for col in train_features.columns:
    col_mean = train_features[col].mean()
    train_features[col].fillna(col_mean, inplace=True)
    val_features[col].fillna(col_mean, inplace=True)
    test_features[col].fillna(col_mean, inplace=True)

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(train_features)
X_val_scaled = scaler.transform(val_features)
X_test_scaled = scaler.transform(test_features)

# Try different feature selection methods
print("\n--- Feature Selection ---")

# Method 1: SelectKBest
selector_kbest = SelectKBest(f_classif, k=20)
X_train_kbest = selector_kbest.fit_transform(X_train_scaled, y_train)
X_val_kbest = selector_kbest.transform(X_val_scaled)
X_test_kbest = selector_kbest.transform(X_test_scaled)
print(f"KBest selected {X_train_kbest.shape[1]} features")

# Method 2: PCA for dimensionality reduction
pca = PCA(n_components=0.95)  # Keep 95% variance
X_train_pca = pca.fit_transform(X_train_scaled)
X_val_pca = pca.transform(X_val_scaled)
X_test_pca = pca.transform(X_test_scaled)
print(f"PCA reduced to {X_train_pca.shape[1]} components (95% variance)")

# Define base models
base_models = [
    ('lr', LogisticRegression(max_iter=1000, random_state=42, C=0.1)),
    ('rf', RandomForestClassifier(n_estimators=200, random_state=42, max_depth=5)),
    ('gb', GradientBoostingClassifier(n_estimators=200, random_state=42, max_depth=3, learning_rate=0.1)),
    ('svm', SVC(probability=True, random_state=42, C=1.0, kernel='rbf')),
    ('mlp', MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42, alpha=0.01))
]

# Try different feature sets
feature_sets = {
    'KBest_20': (X_train_kbest, X_val_kbest, X_test_kbest),
    'PCA': (X_train_pca, X_val_pca, X_test_pca),
    'All_Features': (X_train_scaled, X_val_scaled, X_test_scaled)
}

results = {}
best_overall_auc = 0
best_model_info = {}

for feat_name, (X_train_f, X_val_f, X_test_f) in feature_sets.items():
    print(f"\n--- Testing with {feat_name} features ---")
    
    for model_name, model in base_models:
        # Train model
        model.fit(X_train_f, y_train)
        
        # Predict on validation
        y_val_pred = model.predict_proba(X_val_f)[:, 1]
        val_auc = roc_auc_score(y_val, y_val_pred)
        
        # Cross-validation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(model, X_train_f, y_train, 
                                     cv=cv, scoring='roc_auc', n_jobs=-1)
        
        print(f"  {model_name}: Val AUC={val_auc:.4f}, CV AUC={cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
        
        # Store results
        key = f"{feat_name}_{model_name}"
        results[key] = {
            'model': model,
            'feat_name': feat_name,
            'model_name': model_name,
            'val_auc': val_auc,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
        
        # Track best
        if val_auc > best_overall_auc:
            best_overall_auc = val_auc
            best_model_info = {
                'key': key,
                'model': model,
                'feat_name': feat_name,
                'model_name': model_name,
                'X_train': X_train_f,
                'X_val': X_val_f,
                'X_test': X_test_f
            }

print(f"\n=== Best Model: {best_model_info['key']} with Validation AUC: {best_overall_auc:.4f} ===")

# Try ensemble methods with best feature set
print("\n--- Trying Ensemble Methods ---")
best_feat_set = best_model_info['feat_name']
X_train_best, X_val_best, X_test_best = feature_sets[best_feat_set]

# Voting classifier
voting_clf = VotingClassifier(
    estimators=[('lr', LogisticRegression(max_iter=1000, random_state=42)),
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=100, random_state=42))],
    voting='soft'
)
voting_clf.fit(X_train_best, y_train)
y_val_voting = voting_clf.predict_proba(X_val_best)[:, 1]
val_auc_voting = roc_auc_score(y_val, y_val_voting)
print(f"Voting Classifier Val AUC: {val_auc_voting:.4f}")

# Stacking classifier
stacking_clf = StackingClassifier(
    estimators=[('lr', LogisticRegression(max_iter=1000, random_state=42)),
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=100, random_state=42))],
    final_estimator=LogisticRegression(),
    cv=5
)
stacking_clf.fit(X_train_best, y_train)
y_val_stacking = stacking_clf.predict_proba(X_val_best)[:, 1]
val_auc_stacking = roc_auc_score(y_val, y_val_stacking)
print(f"Stacking Classifier Val AUC: {val_auc_stacking:.4f}")

# Use best ensemble if better
if val_auc_voting > best_overall_auc:
    best_overall_auc = val_auc_voting
    best_model_info['model'] = voting_clf
    best_model_info['model_name'] = 'VotingEnsemble'
    print(f"New best: Voting Ensemble with AUC {val_auc_voting:.4f}")

if val_auc_stacking > best_overall_auc:
    best_overall_auc = val_auc_stacking
    best_model_info['model'] = stacking_clf
    best_model_info['model_name'] = 'StackingEnsemble'
    print(f"New best: Stacking Ensemble with AUC {val_auc_stacking:.4f}")

# Evaluate best model on test set
print(f"\n--- Evaluating Best Model on Test Set ---")
best_model = best_model_info['model']
X_test_best = feature_sets[best_model_info['feat_name']][2]

y_test_pred = best_model.predict_proba(X_test_best)[:, 1]
test_auc = roc_auc_score(y_test, y_test_pred)
print(f"Test AUC: {test_auc:.4f}")

# Compare with baseline
baseline_auc = 0.72
print(f"Baseline AUC: {baseline_auc:.4f}")
print(f"Difference from baseline: {test_auc - baseline_auc:.4f}")

# Save best model
os.makedirs('../outputs/models', exist_ok=True)
model_filename = f"best_model_{best_model_info['model_name']}_{best_model_info['feat_name']}.pkl"
with open(f'../outputs/models/{model_filename}', 'wb') as f:
    pickle.dump(best_model, f)

# Save predictions
predictions_df = pd.DataFrame({
    'id': test['id'],
    'true_label': y_test,
    'predicted_prob': y_test_pred,
    'predicted_label': (y_test_pred > 0.5).astype(int)
})
predictions_df.to_csv('../outputs/test_predictions_improved.csv', index=False)

# Create visualizations
os.makedirs('../report/images', exist_ok=True)

# 1. Top performing models comparison
plt.figure(figsize=(12, 6))
top_results = sorted([(k, v['val_auc']) for k, v in results.items()], 
                     key=lambda x: x[1], reverse=True)[:10]
top_names = [x[0] for x in top_results]
top_aucs = [x[1] for x in top_results]

bars = plt.barh(range(len(top_names)), top_aucs, color='lightgreen')
plt.axvline(x=baseline_auc, color='red', linestyle='--', label=f'Baseline AUC={baseline_auc}')
plt.axvline(x=test_auc, color='blue', linestyle='--', label=f'Best Test AUC={test_auc:.4f}')
plt.xlabel('Validation AUC')
plt.title('Top 10 Model Configurations')
plt.yticks(range(len(top_names)), top_names)
plt.legend()
plt.xlim(0.3, 0.8)

# Add value labels
for i, (bar, auc) in enumerate(zip(bars, top_aucs)):
    width = bar.get_width()
    plt.text(width + 0.01, i, f'{auc:.3f}', va='center')

plt.tight_layout()
plt.savefig('../report/images/top_models_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. ROC curve comparison for top 3 models
top_3_keys = [x[0] for x in top_results[:3]]
plt.figure(figsize=(10, 8))

# Add best model test ROC
fpr_test, tpr_test, _ = roc_curve(y_test, y_test_pred)
plt.plot(fpr_test, tpr_test, label=f'Best Model ({best_model_info["model_name"]}) Test AUC={test_auc:.3f}', 
         linewidth=3, color='black')

# Add top 3 validation ROCs
colors = ['red', 'green', 'blue']
for i, key in enumerate(top_3_keys):
    model_data = results[key]
    X_val_f = feature_sets[model_data['feat_name']][1]
    y_val_pred = model_data['model'].predict_proba(X_val_f)[:, 1]
    fpr, tpr, _ = roc_curve(y_val, y_val_pred)
    plt.plot(fpr, tpr, label=f'{key} Val AUC={model_data["val_auc"]:.3f}', 
             linewidth=2, alpha=0.7, color=colors[i])

plt.plot([0, 1], [0, 1], 'k--', label='Random (AUC = 0.5)')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curves Comparison')
plt.legend(loc='lower right')
plt.grid(True, alpha=0.3)
plt.savefig('../report/images/roc_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Feature importance for tree-based models if applicable
if hasattr(best_model, 'feature_importances_'):
    plt.figure(figsize=(12, 8))
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1][:15]
    
    # Get feature names
    if best_model_info['feat_name'] == 'KBest_20':
        selected_indices = selector_kbest.get_support(indices=True)
        feature_names = train_features.columns[selected_indices]
        plt.barh(range(15), importances[indices[:15]], align='center')
        plt.yticks(range(15), [feature_names[i] for i in indices[:15]])
    else:
        plt.barh(range(15), importances[indices[:15]], align='center')
        plt.yticks(range(15), [f'Feature {i}' for i in indices[:15]])
    
    plt.xlabel('Feature Importance')
    plt.title('Top 15 Feature Importances')
    plt.tight_layout()
    plt.savefig('../report/images/feature_importance_improved.png', dpi=300, bbox_inches='tight')
    plt.close()

print("\nVisualizations saved to report/images/")

# Save detailed results
with open('../outputs/improved_model_results.txt', 'w') as f:
    f.write("Improved Model Results\n")
    f.write("="*50 + "\n\n")
    f.write(f"Best Model: {best_model_info['model_name']}\n")
    f.write(f"Feature Set: {best_model_info['feat_name']}\n")
    f.write(f"Validation AUC: {best_overall_auc:.4f}\n")
    f.write(f"Test AUC: {test_auc:.4f}\n")
    f.write(f"Baseline AUC: {baseline_auc:.4f}\n")
    f.write(f"Difference: {test_auc - baseline_auc:.4f}\n\n")
    
    f.write("All Results:\n")
    for key in sorted(results.keys()):
        f.write(f"{key}: Val AUC={results[key]['val_auc']:.4f}, "
                f"CV AUC={results[key]['cv_mean']:.4f} (+/- {results[key]['cv_std']*2:.4f})\n")

print("\n=== Improved Modeling Complete ===")