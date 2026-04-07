import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import balanced_accuracy_score, classification_report, confusion_matrix, roc_curve, auc, precision_recall_curve
from sklearn.feature_selection import SelectKBest, f_classif, RFE
import os
import joblib

# Set up paths
output_dir = '../outputs'
report_img_dir = '../report/images'

# Create image directory if needed
os.makedirs(report_img_dir, exist_ok=True)

# Load improved features
train_features = pd.read_csv(os.path.join(output_dir, 'train_features_improved.csv'))
val_features = pd.read_csv(os.path.join(output_dir, 'val_features_improved.csv'))
test_features = pd.read_csv(os.path.join(output_dir, 'test_features_improved.csv'))

print("=== Data Overview ===")
print(f"Training features shape: {train_features.shape}")
print(f"Validation features shape: {val_features.shape}")
print(f"Test features shape: {test_features.shape}")

# Prepare features and labels
def prepare_data(df):
    # Drop non-feature columns
    feature_cols = [col for col in df.columns if col not in ['object_id', 'label']]
    X = df[feature_cols].values
    y = df['label'].values
    return X, y, feature_cols

X_train, y_train, feature_cols = prepare_data(train_features)
X_val, y_val, _ = prepare_data(val_features)
X_test, y_test, _ = prepare_data(test_features)

print(f"\nNumber of features: {len(feature_cols)}")
print(f"Feature examples: {feature_cols[:10]}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Feature selection with more features
print("\n=== Feature Selection ===")
k_features = min(40, len(feature_cols))
selector = SelectKBest(f_classif, k=k_features)
X_train_selected = selector.fit_transform(X_train_scaled, y_train)
X_val_selected = selector.transform(X_val_scaled)
X_test_selected = selector.transform(X_test_scaled)

# Get selected feature names
selected_mask = selector.get_support()
selected_features = [feature_cols[i] for i in range(len(feature_cols)) if selected_mask[i]]
print(f"Selected {len(selected_features)} features")
print("Top 20 selected features:")
for i, feat in enumerate(selected_features[:20]):
    print(f"  {i+1:2d}. {feat}")

# Initialize classifiers with potential hyperparameters
classifiers = {
    'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, class_weight='balanced'),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42),
    'SVM': SVC(kernel='rbf', C=1.0, probability=True, random_state=42, class_weight='balanced'),
    'Logistic Regression': LogisticRegression(random_state=42, class_weight='balanced', max_iter=1000, C=0.1),
    'AdaBoost': AdaBoostClassifier(n_estimators=100, random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(50, 25), max_iter=1000, random_state=42)
}

# Train and evaluate models
results = {}
for name, clf in classifiers.items():
    print(f"\n=== Training {name} ===")
    
    # Train on selected features
    clf.fit(X_train_selected, y_train)
    
    # Predict on validation set
    y_val_pred = clf.predict(X_val_selected)
    y_val_prob = clf.predict_proba(X_val_selected)[:, 1] if hasattr(clf, 'predict_proba') else None
    
    # Calculate metrics
    val_accuracy = balanced_accuracy_score(y_val, y_val_pred)
    
    # Cross-validation on training set
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(clf, X_train_selected, y_train, cv=cv, scoring='balanced_accuracy')
    
    print(f"Validation balanced accuracy: {val_accuracy:.4f}")
    print(f"Cross-validation mean accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Store results
    results[name] = {
        'model': clf,
        'val_accuracy': val_accuracy,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'y_val_pred': y_val_pred,
        'y_val_prob': y_val_prob
    }

# Find best model
best_model_name = max(results, key=lambda x: results[x]['val_accuracy'])
best_model = results[best_model_name]['model']
print(f"\n=== Best Model: {best_model_name} ===")
print(f"Validation balanced accuracy: {results[best_model_name]['val_accuracy']:.4f}")

# Evaluate on test set
print("\n=== Test Set Evaluation ===")
y_test_pred = best_model.predict(X_test_selected)
y_test_prob = best_model.predict_proba(X_test_selected)[:, 1] if hasattr(best_model, 'predict_proba') else None

test_accuracy = balanced_accuracy_score(y_test, y_test_pred)
print(f"Test balanced accuracy: {test_accuracy:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_test_pred))

# Confusion matrix
cm = confusion_matrix(y_test, y_test_pred)
print("Confusion Matrix:")
print(cm)

# Calculate precision, recall, F1
TN, FP, FN, TP = cm.ravel()
precision = TP / (TP + FP) if (TP + FP) > 0 else 0
recall = TP / (TP + FN) if (TP + FN) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
print(f"\nPrecision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1-Score: {f1:.4f}")

# Feature importance for tree-based models
if hasattr(best_model, 'feature_importances_'):
    print("\n=== Feature Importance ===")
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print("Top 20 most important features:")
    for i in range(min(20, len(selected_features))):
        print(f"{i+1:2d}. {selected_features[indices[i]]}: {importances[indices[i]]:.4f}")
    
    # Plot feature importance
    plt.figure(figsize=(10, 6))
    top_n = min(15, len(selected_features))
    plt.barh(range(top_n), importances[indices[:top_n]][::-1])
    plt.yticks(range(top_n), [selected_features[indices[i]] for i in range(top_n-1, -1, -1)])
    plt.xlabel('Feature Importance')
    plt.title(f'Top {top_n} Features - {best_model_name}')
    plt.tight_layout()
    plt.savefig(os.path.join(report_img_dir, 'feature_importance.png'), dpi=150)
    plt.close()

# Plot confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Non-variable', 'Variable'],
            yticklabels=['Non-variable', 'Variable'])
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title(f'Confusion Matrix - {best_model_name}\nTest Accuracy: {test_accuracy:.4f}')
plt.tight_layout()
plt.savefig(os.path.join(report_img_dir, 'confusion_matrix.png'), dpi=150)
plt.close()

# Plot model comparison
plt.figure(figsize=(10, 6))
models = list(results.keys())
val_accs = [results[m]['val_accuracy'] for m in models]
cv_accs = [results[m]['cv_mean'] for m in models]

x = np.arange(len(models))
width = 0.35

plt.bar(x - width/2, val_accs, width, label='Validation Accuracy', color='skyblue')
plt.bar(x + width/2, cv_accs, width, label='CV Mean Accuracy', color='lightcoral')

plt.xlabel('Model')
plt.ylabel('Balanced Accuracy')
plt.title('Model Performance Comparison')
plt.xticks(x, models, rotation=45, ha='right')
plt.legend()
plt.ylim([0.4, 0.8])
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(report_img_dir, 'model_comparison.png'), dpi=150)
plt.close()

# Save model and results
print("\n=== Saving Results ===")
joblib.dump(best_model, os.path.join(output_dir, 'best_model_improved.pkl'))
joblib.dump(scaler, os.path.join(output_dir, 'scaler_improved.pkl'))
joblib.dump(selector, os.path.join(output_dir, 'selector_improved.pkl'))

# Save results to CSV
results_df = pd.DataFrame({
    'Model': list(results.keys()),
    'Validation Accuracy': [results[name]['val_accuracy'] for name in results.keys()],
    'CV Mean Accuracy': [results[name]['cv_mean'] for name in results.keys()],
    'CV Std': [results[name]['cv_std'] for name in results.keys()]
})
results_df = results_df.sort_values('Validation Accuracy', ascending=False)
results_df.to_csv(os.path.join(output_dir, 'model_results_improved.csv'), index=False)
print("\nModel Results:")
print(results_df)

print("\nImproved modeling complete!")
