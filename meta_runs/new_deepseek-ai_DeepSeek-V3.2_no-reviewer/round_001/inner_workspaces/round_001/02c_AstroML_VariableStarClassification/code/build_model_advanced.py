import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, classification_report, roc_auc_score
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
import os
import joblib
from advanced_features import AdvancedSymbolicFeatureExtractor, extract_advanced_features_from_dataframe

# Set random seed for reproducibility
np.random.seed(42)

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
data_dir = '../data'
train_df = pd.read_csv(os.path.join(data_dir, 'train.csv'))
val_df = pd.read_csv(os.path.join(data_dir, 'val.csv'))
test_df = pd.read_csv(os.path.join(data_dir, 'test.csv'))

print("Extracting advanced features from training data...")
extractor = AdvancedSymbolicFeatureExtractor()
train_features_df = extract_advanced_features_from_dataframe(train_df, extractor)
print(f"Training features shape: {train_features_df.shape}")

print("Extracting features from validation data...")
val_features_df = extract_advanced_features_from_dataframe(val_df, extractor)
print(f"Validation features shape: {val_features_df.shape}")

print("Extracting features from test data...")
test_features_df = extract_advanced_features_from_dataframe(test_df, extractor)
print(f"Test features shape: {test_features_df.shape}")

# Separate features and labels
def prepare_features(df):
    # Drop non-feature columns
    feature_cols = [col for col in df.columns if col not in ['object_id', 'field_id', 'label']]
    X = df[feature_cols].values
    y = df['label'].values
    return X, y, feature_cols

X_train, y_train, feature_cols = prepare_features(train_features_df)
X_val, y_val, _ = prepare_features(val_features_df)
X_test, y_test, _ = prepare_features(test_features_df)

print(f"\nNumber of features: {len(feature_cols)}")
print(f"Training set: {X_train.shape}, Validation set: {X_val.shape}, Test set: {X_test.shape}")
print(f"Feature names: {feature_cols}")

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Feature selection using RFE with Random Forest
print("\nPerforming feature selection with RFE...")
from sklearn.feature_selection import RFECV

# Use a simpler model for feature selection
selector = RFECV(
    estimator=RandomForestClassifier(n_estimators=50, random_state=42),
    step=1,
    cv=5,
    scoring='balanced_accuracy',
    min_features_to_select=10,
    n_jobs=-1
)

selector.fit(X_train_scaled, y_train)
X_train_selected = selector.transform(X_train_scaled)
X_val_selected = selector.transform(X_val_scaled)
X_test_selected = selector.transform(X_test_scaled)

# Get selected feature names
selected_indices = selector.get_support(indices=True)
selected_features = [feature_cols[i] for i in selected_indices]
print(f"Selected {len(selected_features)} features")
print("Selected features:", selected_features)

# Save feature ranking
feature_ranking = pd.DataFrame({
    'feature': feature_cols,
    'ranking': selector.ranking_,
    'selected': selector.support_
})
feature_ranking = feature_ranking.sort_values('ranking')
feature_ranking.to_csv('../outputs/feature_ranking_advanced.csv', index=False)

# Train multiple models with hyperparameter tuning
models = {
    'Random Forest': {
        'model': RandomForestClassifier(random_state=42),
        'params': {
            'n_estimators': [100, 200],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5]
        }
    },
    'Gradient Boosting': {
        'model': GradientBoostingClassifier(random_state=42),
        'params': {
            'n_estimators': [100, 200],
            'learning_rate': [0.01, 0.1],
            'max_depth': [3, 5]
        }
    },
    'Logistic Regression': {
        'model': LogisticRegression(max_iter=1000, random_state=42),
        'params': {
            'C': [0.1, 1, 10],
            'penalty': ['l2']
        }
    },
    'SVM': {
        'model': SVC(probability=True, random_state=42),
        'params': {
            'C': [0.1, 1, 10],
            'gamma': ['scale', 'auto']
        }
    },
    'MLP': {
        'model': MLPClassifier(random_state=42, max_iter=1000),
        'params': {
            'hidden_layer_sizes': [(50,), (100,), (50, 50)],
            'alpha': [0.0001, 0.001]
        }
    }
}

results = {}
best_models = {}

for name, config in models.items():
    print(f"\nTraining and tuning {name}...")
    
    # Grid search with cross-validation
    grid_search = GridSearchCV(
        config['model'],
        config['params'],
        cv=5,
        scoring='balanced_accuracy',
        n_jobs=-1,
        verbose=0
    )
    
    grid_search.fit(X_train_selected, y_train)
    
    # Get best model
    best_model = grid_search.best_estimator_
    best_models[name] = best_model
    
    # Predict on validation set
    y_val_pred = best_model.predict(X_val_selected)
    y_val_prob = best_model.predict_proba(X_val_selected)[:, 1] if hasattr(best_model, 'predict_proba') else None
    
    # Calculate metrics
    val_accuracy = accuracy_score(y_val, y_val_pred)
    val_balanced_accuracy = balanced_accuracy_score(y_val, y_val_pred)
    val_auc = roc_auc_score(y_val, y_val_prob) if y_val_prob is not None else None
    
    # Store results
    results[name] = {
        'model': best_model,
        'best_params': grid_search.best_params_,
        'val_accuracy': val_accuracy,
        'val_balanced_accuracy': val_balanced_accuracy,
        'val_auc': val_auc,
        'y_val_pred': y_val_pred,
        'y_val_prob': y_val_prob
    }
    
    print(f"  Best params: {grid_search.best_params_}")
    print(f"  Validation Accuracy: {val_accuracy:.4f}")
    print(f"  Validation Balanced Accuracy: {val_balanced_accuracy:.4f}")
    if val_auc is not None:
        print(f"  Validation AUC: {val_auc:.4f}")

# Find best model based on balanced accuracy
best_model_name = max(results.keys(), key=lambda x: results[x]['val_balanced_accuracy'])
best_model = results[best_model_name]['model']
print(f"\n{'='*60}")
print(f"Best model: {best_model_name} with balanced accuracy: {results[best_model_name]['val_balanced_accuracy']:.4f}")
print(f"Best parameters: {results[best_model_name]['best_params']}")

# Evaluate best model on test set
y_test_pred = best_model.predict(X_test_selected)
y_test_prob = best_model.predict_proba(X_test_selected)[:, 1] if hasattr(best_model, 'predict_proba') else None

test_accuracy = accuracy_score(y_test, y_test_pred)
test_balanced_accuracy = balanced_accuracy_score(y_test, y_test_pred)
test_auc = roc_auc_score(y_test, y_test_prob) if y_test_prob is not None else None

print(f"\nTest set performance of {best_model_name}:")
print(f"  Test Accuracy: {test_accuracy:.4f}")
print(f"  Test Balanced Accuracy: {test_balanced_accuracy:.4f}")
if test_auc is not None:
    print(f"  Test AUC: {test_auc:.4f}")

# Compare with baseline
baseline_balanced_accuracy = 0.78
print(f"\nBaseline balanced accuracy: {baseline_balanced_accuracy:.4f}")
print(f"Improvement over baseline: {test_balanced_accuracy - baseline_balanced_accuracy:.4f}")

# Save model and results
joblib.dump(best_model, '../outputs/best_model_advanced.pkl')
joblib.dump(scaler, '../outputs/scaler_advanced.pkl')
joblib.dump(selector, '../outputs/feature_selector_advanced.pkl')
joblib.dump(extractor, '../outputs/feature_extractor_advanced.pkl')

# Save results to CSV
results_df = pd.DataFrame([
    {
        'model': name,
        'best_params': str(results[name]['best_params']),
        'val_accuracy': results[name]['val_accuracy'],
        'val_balanced_accuracy': results[name]['val_balanced_accuracy'],
        'val_auc': results[name]['val_auc'],
        'test_accuracy': test_accuracy if name == best_model_name else None,
        'test_balanced_accuracy': test_balanced_accuracy if name == best_model_name else None,
        'test_auc': test_auc if name == best_model_name else None
    }
    for name in results.keys()
])
results_df.to_csv('../outputs/model_results_advanced.csv', index=False)

# Create visualizations
plt.figure(figsize=(15, 10))

# Plot model comparison
plt.subplot(2, 2, 1)
model_names = list(results.keys())
val_accuracies = [results[name]['val_accuracy'] for name in model_names]
val_balanced_accuracies = [results[name]['val_balanced_accuracy'] for name in model_names]

x = np.arange(len(model_names))
width = 0.35

plt.bar(x - width/2, val_accuracies, width, label='Accuracy', alpha=0.8)
plt.bar(x + width/2, val_balanced_accuracies, width, label='Balanced Accuracy', alpha=0.8)
plt.axhline(y=baseline_balanced_accuracy, color='r', linestyle='--', 
            label=f'Baseline ({baseline_balanced_accuracy:.2f})', linewidth=2)
plt.xlabel('Model')
plt.ylabel('Score')
plt.title('Model Performance on Validation Set')
plt.xticks(x, model_names, rotation=45)
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(0, 1.0)

# Plot confusion matrix for best model on test set
plt.subplot(2, 2, 2)
cm = confusion_matrix(y_test, y_test_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Non-variable (0)', 'Variable (1)'],
            yticklabels=['Non-variable (0)', 'Variable (1)'])
plt.title(f'Confusion Matrix - {best_model_name}\nTest Set (Balanced Acc: {test_balanced_accuracy:.3f})')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')

# Plot feature importance for tree-based models
if hasattr(best_model, 'feature_importances_'):
    plt.subplot(2, 2, 3)
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    top_n = min(15, len(selected_features))
    
    plt.barh(range(top_n), importances[indices[:top_n]][::-1])
    plt.yticks(range(top_n), [selected_features[i] for i in indices[:top_n]][::-1])
    plt.xlabel('Feature Importance')
    plt.title(f'Top {top_n} Feature Importances - {best_model_name}')
    plt.grid(True, alpha=0.3, axis='x')

# Plot ROC curve if probabilities available
if y_test_prob is not None:
    plt.subplot(2, 2, 4)
    from sklearn.metrics import roc_curve
    
    fpr, tpr, _ = roc_curve(y_test, y_test_prob)
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {test_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC Curve - {best_model_name}')
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/model_performance_advanced.png', dpi=150, bbox_inches='tight')
plt.close()

# Create detailed classification report
print("\n" + "="*60)
print("Detailed Classification Report for Best Model:")
print("="*60)
print(classification_report(y_test, y_test_pred, target_names=['Non-variable', 'Variable']))

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test_df['object_id'],
    'true_label': y_test,
    'predicted_label': y_test_pred,
    'predicted_probability': y_test_prob if y_test_prob is not None else np.nan
})
predictions_df.to_csv('../outputs/test_predictions.csv', index=False)

print("\nAnalysis complete. Results saved to outputs/ and report/images/")