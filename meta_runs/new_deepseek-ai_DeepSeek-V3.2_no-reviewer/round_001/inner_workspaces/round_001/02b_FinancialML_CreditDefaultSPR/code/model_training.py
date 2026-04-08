import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import roc_auc_score, classification_report, roc_curve, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.feature_selection import SelectKBest, f_classif
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
import pickle
warnings.filterwarnings('ignore')

# Load features and targets
train_features = pd.read_csv('../outputs/train_features.csv')
val_features = pd.read_csv('../outputs/val_features.csv')
test_features = pd.read_csv('../outputs/test_features.csv')

train = pd.read_csv('../data/train.csv')
val = pd.read_csv('../data/val.csv')
test = pd.read_csv('../data/test.csv')

y_train = train['default_flag'].values
y_val = val['default_flag'].values
y_test = test['default_flag'].values

print("=== Model Training ===")
print(f"Training samples: {len(train_features)}")
print(f"Validation samples: {len(val_features)}")
print(f"Test samples: {len(test_features)}")
print(f"Number of features: {train_features.shape[1]}")

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(train_features)
X_val_scaled = scaler.transform(val_features)
X_test_scaled = scaler.transform(test_features)

# Save scaler for later use
os.makedirs('../outputs/models', exist_ok=True)
with open('../outputs/models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

# Feature selection (optional, can help with overfitting)
selector = SelectKBest(f_classif, k=30)
X_train_selected = selector.fit_transform(X_train_scaled, y_train)
X_val_selected = selector.transform(X_val_scaled)
X_test_selected = selector.transform(X_test_scaled)

print(f"\nSelected {X_train_selected.shape[1]} best features")

# Define models to try
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
    'SVM': SVC(probability=True, random_state=42),
    'Neural Network': MLPClassifier(hidden_layer_sizes=(50, 25), max_iter=1000, random_state=42)
}

# Train and evaluate models
results = {}
best_model = None
best_auc = 0
best_model_name = ""

for name, model in models.items():
    print(f"\n--- Training {name} ---")
    
    # Use selected features for all models
    model.fit(X_train_selected, y_train)
    
    # Predict on validation set
    y_val_pred = model.predict_proba(X_val_selected)[:, 1]
    val_auc = roc_auc_score(y_val, y_val_pred)
    
    # Cross-validation on training set
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_selected, y_train, 
                                 cv=cv, scoring='roc_auc', n_jobs=-1)
    
    print(f"Validation AUC: {val_auc:.4f}")
    print(f"CV AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Store results
    results[name] = {
        'model': model,
        'val_auc': val_auc,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'y_val_pred': y_val_pred
    }
    
    # Track best model
    if val_auc > best_auc:
        best_auc = val_auc
        best_model = model
        best_model_name = name

print(f"\n=== Best Model: {best_model_name} with Validation AUC: {best_auc:.4f} ===")

# Evaluate best model on test set
print(f"\n--- Evaluating Best Model on Test Set ---")
y_test_pred = best_model.predict_proba(X_test_selected)[:, 1]
test_auc = roc_auc_score(y_test, y_test_pred)
print(f"Test AUC: {test_auc:.4f}")

# Compare with baseline
baseline_auc = 0.72
print(f"Baseline AUC: {baseline_auc:.4f}")
print(f"Improvement over baseline: {test_auc - baseline_auc:.4f}")

# Save best model
with open(f'../outputs/models/best_model_{best_model_name.replace(" ", "_")}.pkl', 'wb') as f:
    pickle.dump(best_model, f)

# Save predictions
predictions_df = pd.DataFrame({
    'id': test['id'],
    'true_label': y_test,
    'predicted_prob': y_test_pred,
    'predicted_label': (y_test_pred > 0.5).astype(int)
})
predictions_df.to_csv('../outputs/test_predictions.csv', index=False)

# Create visualizations
os.makedirs('../report/images', exist_ok=True)

# 1. Model comparison bar chart
plt.figure(figsize=(10, 6))
model_names = list(results.keys())
val_aucs = [results[name]['val_auc'] for name in model_names]

bars = plt.bar(model_names, val_aucs, color='skyblue')
plt.axhline(y=baseline_auc, color='red', linestyle='--', label=f'Baseline AUC={baseline_auc}')
plt.axhline(y=test_auc, color='green', linestyle='--', label=f'Best Test AUC={test_auc:.4f}')
plt.xlabel('Model')
plt.ylabel('Validation AUC')
plt.title('Model Performance Comparison')
plt.ylim(0.5, 1.0)
plt.xticks(rotation=45)
plt.legend()

# Add value labels on bars
for bar, auc in zip(bars, val_aucs):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
             f'{auc:.3f}', ha='center', va='bottom')

plt.tight_layout()
plt.savefig('../report/images/model_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. ROC curve for best model
plt.figure(figsize=(8, 6))
fpr, tpr, _ = roc_curve(y_test, y_test_pred)
plt.plot(fpr, tpr, label=f'{best_model_name} (AUC = {test_auc:.3f})', linewidth=2)
plt.plot([0, 1], [0, 1], 'k--', label='Random (AUC = 0.5)')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title(f'ROC Curve - {best_model_name}')
plt.legend(loc='lower right')
plt.grid(True, alpha=0.3)
plt.savefig('../report/images/roc_curve.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Feature importance for tree-based models
if hasattr(best_model, 'feature_importances_'):
    plt.figure(figsize=(12, 8))
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1][:20]  # Top 20 features
    
    # Get feature names (use original feature names)
    feature_names = train_features.columns[selector.get_support(indices=True)]
    
    plt.barh(range(len(indices[:20])), importances[indices[:20]], align='center')
    plt.yticks(range(len(indices[:20])), [feature_names[i] for i in indices[:20]])
    plt.xlabel('Feature Importance')
    plt.title('Top 20 Feature Importances')
    plt.tight_layout()
    plt.savefig('../report/images/feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()

# 4. Confusion matrix
plt.figure(figsize=(8, 6))
y_pred_labels = (y_test_pred > 0.5).astype(int)
cm = confusion_matrix(y_test, y_pred_labels)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['No Default', 'Default'],
            yticklabels=['No Default', 'Default'])
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.savefig('../report/images/confusion_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualizations saved to report/images/")

# Save results summary
with open('../outputs/model_results_summary.txt', 'w') as f:
    f.write("Model Results Summary\n")
    f.write("="*50 + "\n\n")
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Validation AUC: {best_auc:.4f}\n")
    f.write(f"Test AUC: {test_auc:.4f}\n")
    f.write(f"Baseline AUC: {baseline_auc:.4f}\n")
    f.write(f"Improvement: {test_auc - baseline_auc:.4f}\n\n")
    
    f.write("All Models:\n")
    for name in results:
        f.write(f"  {name}: Val AUC={results[name]['val_auc']:.4f}, "
                f"CV AUC={results[name]['cv_mean']:.4f} (+/- {results[name]['cv_std']*2:.4f})\n")

print("\n=== Training Complete ===")