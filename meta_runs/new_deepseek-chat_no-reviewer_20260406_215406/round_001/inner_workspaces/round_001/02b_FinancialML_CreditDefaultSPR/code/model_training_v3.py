import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Try to import xgboost, install if not available
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    print("XGBoost not available, installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xgboost"])
    import xgboost as xgb
    XGB_AVAILABLE = True

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score, roc_curve, confusion_matrix

# Load processed data
with open('../outputs/X_train_v3.pkl', 'rb') as f:
    X_train = pickle.load(f)
with open('../outputs/X_val_v3.pkl', 'rb') as f:
    X_val = pickle.load(f)
with open('../outputs/X_test_v3.pkl', 'rb') as f:
    X_test = pickle.load(f)
    
with open('../outputs/y_train.pkl', 'rb') as f:
    y_train = pickle.load(f)
with open('../outputs/y_val.pkl', 'rb') as f:
    y_val = pickle.load(f)
with open('../outputs/y_test.pkl', 'rb') as f:
    y_test = pickle.load(f)

print("Data shapes:")
print(f"X_train: {X_train.shape}, y_train: {y_train.shape}")
print(f"X_val: {X_val.shape}, y_val: {y_val.shape}")
print(f"X_test: {X_test.shape}, y_test: {y_test.shape}")

# Combine train and val for final training (small dataset)
X_train_full = np.vstack([X_train, X_val])
y_train_full = np.concatenate([y_train, y_val])
print(f"\nCombined training data: {X_train_full.shape}, {y_train_full.shape}")

# Define models with hyperparameter tuning
models = {}

# XGBoost with tuning
if XGB_AVAILABLE:
    xgb_model = xgb.XGBClassifier(
        random_state=42,
        eval_metric='logloss',
        use_label_encoder=False
    )
    
    xgb_params = {
        'n_estimators': [100, 200, 300],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1, 0.2],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }
    
    models['XGBoost'] = {
        'model': xgb_model,
        'params': xgb_params
    }

# Random Forest
rf_model = RandomForestClassifier(random_state=42, class_weight='balanced')
rf_params = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20],
    'min_samples_split': [2, 5, 10]
}
models['Random Forest'] = {'model': rf_model, 'params': rf_params}

# Gradient Boosting
gb_model = GradientBoostingClassifier(random_state=42)
gb_params = {
    'n_estimators': [100, 200],
    'learning_rate': [0.01, 0.1, 0.2],
    'max_depth': [3, 5, 7]
}
models['Gradient Boosting'] = {'model': gb_model, 'params': gb_params}

# Logistic Regression
lr_model = LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced')
lr_params = {
    'C': [0.01, 0.1, 1, 10],
    'penalty': ['l2']
}
models['Logistic Regression'] = {'model': lr_model, 'params': lr_params}

# Train and tune models
results = []
best_models = {}

print("\nTraining and tuning models...")
for name, model_info in models.items():
    print(f"\nTuning {name}...")
    
    # Use GridSearchCV for hyperparameter tuning
    grid_search = GridSearchCV(
        estimator=model_info['model'],
        param_grid=model_info['params'],
        cv=5,
        scoring='roc_auc',
        n_jobs=-1,
        verbose=0
    )
    
    # Fit on training data
    grid_search.fit(X_train, y_train)
    
    # Get best model
    best_model = grid_search.best_estimator_
    
    # Predict on validation set
    y_val_pred = best_model.predict(X_val)
    y_val_prob = best_model.predict_proba(X_val)[:, 1]
    
    # Calculate metrics
    auc = roc_auc_score(y_val, y_val_prob)
    accuracy = accuracy_score(y_val, y_val_pred)
    precision = precision_score(y_val, y_val_pred)
    recall = recall_score(y_val, y_val_pred)
    f1 = f1_score(y_val, y_val_pred)
    
    print(f"  Best params: {grid_search.best_params_}")
    print(f"  Validation AUC: {auc:.4f}")
    print(f"  Validation F1: {f1:.4f}")
    
    # Store results
    results.append({
        'Model': name,
        'AUC': auc,
        'Accuracy': accuracy,
        'Precision': precision,
        'Recall': recall,
        'F1': f1,
        'Best Params': str(grid_search.best_params_)
    })
    
    # Store best model
    best_models[name] = best_model

# Convert results to DataFrame
results_df = pd.DataFrame(results)
print("\n" + "="*70)
print("Validation Set Performance (with hyperparameter tuning):")
print("="*70)
print(results_df[['Model', 'AUC', 'Accuracy', 'F1', 'Best Params']].to_string(index=False))

# Find best model based on AUC
best_model_name = results_df.loc[results_df['AUC'].idxmax(), 'Model']
best_auc = results_df.loc[results_df['AUC'].idxmax(), 'AUC']
print(f"\nBest model: {best_model_name} (AUC: {best_auc:.4f})")

# Retrain best model on combined training data
print(f"\nRetraining {best_model_name} on combined training data...")
best_model = best_models[best_model_name]

# Clone and retrain on full data
from sklearn.base import clone
final_model = clone(best_model)
final_model.fit(X_train_full, y_train_full)

# Predict on test set
y_test_pred = final_model.predict(X_test)
y_test_prob = final_model.predict_proba(X_test)[:, 1]

test_auc = roc_auc_score(y_test, y_test_prob)
test_accuracy = accuracy_score(y_test, y_test_pred)
test_precision = precision_score(y_test, y_test_pred)
test_recall = recall_score(y_test, y_test_pred)
test_f1 = f1_score(y_test, y_test_pred)

print("\n" + "="*70)
print(f"Test Set Performance ({best_model_name} - final model):")
print("="*70)
print(f"AUC: {test_auc:.4f}")
print(f"Accuracy: {test_accuracy:.4f}")
print(f"Precision: {test_precision:.4f}")
print(f"Recall: {test_recall:.4f}")
print(f"F1 Score: {test_f1:.4f}")

# Compare with baseline
baseline_auc = 0.72
print(f"\nBaseline AUC: {baseline_auc:.4f}")
print(f"Our model AUC: {test_auc:.4f}")
print(f"Difference: {test_auc - baseline_auc:.4f}")

# Save the final model
with open('../outputs/final_model.pkl', 'wb') as f:
    pickle.dump(final_model, f)

print("\nFinal model saved to outputs/final_model.pkl")

# Create visualizations
os.makedirs('../report/images', exist_ok=True)

# Plot 1: Model comparison
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

metrics = ['AUC', 'Accuracy', 'F1', 'Precision']
for idx, metric in enumerate(metrics):
    ax = axes[idx]
    bars = ax.bar(results_df['Model'], results_df[metric], color='skyblue')
    ax.set_title(f'{metric} Comparison (Tuned Models)')
    ax.set_ylabel(metric)
    ax.set_xticklabels(results_df['Model'], rotation=45, ha='right')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', fontsize=9)
    
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/model_comparison_v3.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: ROC curve for final model
fig, ax = plt.subplots(figsize=(8, 6))

# Calculate ROC curve
fpr, tpr, thresholds = roc_curve(y_test, y_test_prob)

# Plot ROC curve
ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {test_auc:.3f})')
ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
ax.set_xlim([0.0, 1.0])
ax.set_ylim([0.0, 1.05])
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.set_title(f'ROC Curve - {best_model_name} (Final Model)')
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/roc_curve_final.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Feature importance for tree-based models
if hasattr(final_model, 'feature_importances_'):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    importances = final_model.feature_importances_
    
    # Load feature names
    with open('../outputs/feature_names_v3.pkl', 'rb') as f:
        feature_names = pickle.load(f)
    
    # Sort features by importance
    indices = np.argsort(importances)[::-1]
    top_n = min(20, len(feature_names))
    
    # Get top features
    top_features = [feature_names[i] for i in indices[:top_n]]
    top_importances = importances[indices[:top_n]]
    
    # Create horizontal bar chart
    y_pos = np.arange(top_n)
    ax.barh(y_pos, top_importances, align='center', color='steelblue')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top_features)
    ax.invert_yaxis()  # Most important on top
    ax.set_xlabel('Feature Importance')
    ax.set_title(f'Top {top_n} Feature Importances - {best_model_name}')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/feature_importance_final.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nTop 10 most important features from {best_model_name}:")
    for i in range(min(10, len(top_features))):
        print(f"  {i+1}. {top_features[i]}: {top_importances[i]:.4f}")

print("\nVisualizations saved to report/images/")
