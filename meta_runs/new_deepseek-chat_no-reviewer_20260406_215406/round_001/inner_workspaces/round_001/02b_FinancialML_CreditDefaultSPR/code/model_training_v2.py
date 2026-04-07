import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score, roc_curve, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Load processed data
with open('../outputs/X_train_v2.pkl', 'rb') as f:
    X_train = pickle.load(f)
with open('../outputs/X_val_v2.pkl', 'rb') as f:
    X_val = pickle.load(f)
with open('../outputs/X_test_v2.pkl', 'rb') as f:
    X_test = pickle.load(f)
    
with open('../outputs/y_train.pkl', 'rb') as f:
    y_train = pickle.load(f)
with open('../outputs/y_val.pkl', 'rb') as f:
    y_val = pickle.load(f)
with open('../outputs/y_test.pkl', 'rb') as f:
    y_test = pickle.load(f)

with open('../outputs/feature_names_v2.pkl', 'rb') as f:
    feature_names = pickle.load(f)

print("Data shapes:")
print(f"X_train: {X_train.shape}, y_train: {y_train.shape}")
print(f"X_val: {X_val.shape}, y_val: {y_val.shape}")
print(f"X_test: {X_test.shape}, y_test: {y_test.shape}")
print(f"Number of features: {X_train.shape[1]}")

# Try feature selection
print("\nPerforming feature selection...")
selector = SelectKBest(score_func=f_classif, k=20)
X_train_selected = selector.fit_transform(X_train, y_train)
X_val_selected = selector.transform(X_val)
X_test_selected = selector.transform(X_test)

# Get selected feature indices and names
selected_indices = selector.get_support(indices=True)
selected_features = [feature_names[i] for i in selected_indices]
print(f"Selected {len(selected_features)} features:")
for i, feat in enumerate(selected_features[:10]):
    print(f"  {i+1}. {feat}")
if len(selected_features) > 10:
    print(f"  ... and {len(selected_features)-10} more")

# Define models to try
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),
    'Random Forest': RandomForestClassifier(n_estimators=200, random_state=42, class_weight='balanced'),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, random_state=42),
    'SVM': SVC(probability=True, random_state=42, class_weight='balanced'),
    'Neural Network': MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42)
}

# Train and evaluate models with selected features
results = []
predictions = {}

print("\nTraining models with selected features...")
for name, model in models.items():
    print(f"\nTraining {name}...")
    
    # Train model
    model.fit(X_train_selected, y_train)
    
    # Predict on validation set
    y_val_pred = model.predict(X_val_selected)
    y_val_prob = model.predict_proba(X_val_selected)[:, 1]
    
    # Calculate metrics
    auc = roc_auc_score(y_val, y_val_prob)
    accuracy = accuracy_score(y_val, y_val_pred)
    precision = precision_score(y_val, y_val_pred)
    recall = recall_score(y_val, y_val_pred)
    f1 = f1_score(y_val, y_val_pred)
    
    print(f"  Validation AUC: {auc:.4f}")
    print(f"  Validation Accuracy: {accuracy:.4f}")
    print(f"  Validation F1: {f1:.4f}")
    
    # Store results
    results.append({
        'Model': name,
        'AUC': auc,
        'Accuracy': accuracy,
        'Precision': precision,
        'Recall': recall,
        'F1': f1
    })
    
    # Store predictions for best model selection
    predictions[name] = {
        'model': model,
        'y_val_prob': y_val_prob,
        'y_val_pred': y_val_pred,
        'X_train_selected': X_train_selected,
        'X_val_selected': X_val_selected,
        'X_test_selected': X_test_selected
    }

# Convert results to DataFrame
results_df = pd.DataFrame(results)
print("\n" + "="*60)
print("Validation Set Performance (with feature selection):")
print("="*60)
print(results_df.to_string(index=False))

# Find best model based on AUC
best_model_name = results_df.loc[results_df['AUC'].idxmax(), 'Model']
best_auc = results_df.loc[results_df['AUC'].idxmax(), 'AUC']
print(f"\nBest model: {best_model_name} (AUC: {best_auc:.4f})")

# Evaluate best model on test set
best_model_info = predictions[best_model_name]
best_model = best_model_info['model']
X_test_selected_best = best_model_info['X_test_selected']

# Predict on test set
y_test_pred = best_model.predict(X_test_selected_best)
y_test_prob = best_model.predict_proba(X_test_selected_best)[:, 1]

test_auc = roc_auc_score(y_test, y_test_prob)
test_accuracy = accuracy_score(y_test, y_test_pred)
test_precision = precision_score(y_test, y_test_pred)
test_recall = recall_score(y_test, y_test_pred)
test_f1 = f1_score(y_test, y_test_pred)

print("\n" + "="*60)
print(f"Test Set Performance ({best_model_name}):")
print("="*60)
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

# Save the best model and selector
with open('../outputs/best_model_v2.pkl', 'wb') as f:
    pickle.dump(best_model, f)
with open('../outputs/feature_selector.pkl', 'wb') as f:
    pickle.dump(selector, f)
with open('../outputs/selected_features.pkl', 'wb') as f:
    pickle.dump(selected_features, f)

print("\nBest model and selector saved to outputs/")

# Create visualizations
os.makedirs('../report/images', exist_ok=True)

# Plot 1: Model comparison
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

metrics = ['AUC', 'Accuracy', 'F1', 'Precision']
for idx, metric in enumerate(metrics):
    ax = axes[idx]
    bars = ax.bar(results_df['Model'], results_df[metric], color='skyblue')
    ax.set_title(f'{metric} Comparison (Feature Selection)')
    ax.set_ylabel(metric)
    ax.set_xticklabels(results_df['Model'], rotation=45, ha='right')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.3f}', ha='center', va='bottom', fontsize=9)
    
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/model_comparison_v2.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: ROC curve for best model
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
ax.set_title(f'ROC Curve - {best_model_name} (Feature Selection)')
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/roc_curve_v2.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Feature importance for tree-based models
if best_model_name in ['Random Forest', 'Gradient Boosting']:
    fig, ax = plt.subplots(figsize=(12, 8))
    
    if best_model_name == 'Random Forest':
        importances = best_model.feature_importances_
    else:  # Gradient Boosting
        importances = best_model.feature_importances_
    
    # Sort features by importance
    indices = np.argsort(importances)[::-1]
    top_n = min(15, len(selected_features))
    
    # Get top features
    top_features = [selected_features[i] for i in indices[:top_n]]
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
    plt.savefig('../report/images/feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nTop 5 most important features from {best_model_name}:")
    for i in range(min(5, len(top_features))):
        print(f"  {i+1}. {top_features[i]}: {top_importances[i]:.4f}")

print("\nVisualizations saved to report/images/")
