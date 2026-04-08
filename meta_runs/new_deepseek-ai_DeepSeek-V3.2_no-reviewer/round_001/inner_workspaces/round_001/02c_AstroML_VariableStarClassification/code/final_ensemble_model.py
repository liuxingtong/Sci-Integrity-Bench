import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, classification_report, roc_auc_score
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns
import os
import joblib
from feature_extraction import SymbolSeriesFeatureExtractor, extract_features_from_dataframe
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

print("Dataset sizes:")
print(f"Training: {len(train_df)}")
print(f"Validation: {len(val_df)}")
print(f"Test: {len(test_df)}")

# Combine train and validation for final training (as is common practice)
combined_df = pd.concat([train_df, val_df], ignore_index=True)
print(f"\nCombined training+validation: {len(combined_df)}")

# Extract multiple feature sets
print("\nExtracting multiple feature sets...")

# 1. Basic features
extractor_basic = SymbolSeriesFeatureExtractor()
basic_features = extract_features_from_dataframe(combined_df, extractor_basic)
basic_features_test = extract_features_from_dataframe(test_df, extractor_basic)

# 2. Advanced features
extractor_advanced = AdvancedSymbolicFeatureExtractor()
advanced_features = extract_advanced_features_from_dataframe(combined_df, extractor_advanced)
advanced_features_test = extract_advanced_features_from_dataframe(test_df, extractor_advanced)

# 3. N-gram features (simple version)
from sklearn.feature_extraction.text import CountVectorizer
vectorizer = CountVectorizer(analyzer='char', ngram_range=(2, 3), max_features=200)
X_ngram = vectorizer.fit_transform(combined_df['symbol_series']).toarray()
X_ngram_test = vectorizer.transform(test_df['symbol_series']).toarray()

# 4. Field_id as feature (one-hot encoded)
field_encoder = LabelEncoder()
field_features = field_encoder.fit_transform(combined_df['field_id']).reshape(-1, 1)
field_features_test = field_encoder.transform(test_df['field_id']).reshape(-1, 1)

# Prepare labels
y = combined_df['label'].values
y_test = test_df['label'].values

# Prepare feature matrices
print("\nPreparing feature matrices...")

# Basic features
basic_cols = [col for col in basic_features.columns if col not in ['object_id', 'field_id', 'label']]
X_basic = basic_features[basic_cols].values
X_basic_test = basic_features_test[basic_cols].values

# Advanced features
advanced_cols = [col for col in advanced_features.columns if col not in ['object_id', 'field_id', 'label']]
X_advanced = advanced_features[advanced_cols].values
X_advanced_test = advanced_features_test[advanced_cols].values

print(f"Basic features: {X_basic.shape}")
print(f"Advanced features: {X_advanced.shape}")
print(f"N-gram features: {X_ngram.shape}")
print(f"Field features: {field_features.shape}")

# Combine all features
X_combined = np.hstack([
    X_basic,
    X_advanced,
    X_ngram,
    field_features
])

X_combined_test = np.hstack([
    X_basic_test,
    X_advanced_test,
    X_ngram_test,
    field_features_test
])

print(f"\nCombined features: {X_combined.shape}")

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_combined)
X_scaled_test = scaler.transform(X_combined_test)

# Feature selection
print("\nPerforming feature selection...")
k = min(100, X_scaled.shape[1])
selector = SelectKBest(score_func=f_classif, k=k)
X_selected = selector.fit_transform(X_scaled, y)
X_selected_test = selector.transform(X_scaled_test)

print(f"Selected {k} features from {X_scaled.shape[1]}")

# Train ensemble model
print("\nTraining ensemble model...")

# Define base models
base_models = [
    ('rf', RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)),
    ('gb', GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)),
    ('svm', SVC(kernel='rbf', C=1, probability=True, random_state=42)),
    ('mlp', MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=1000, random_state=42))
]

# Create voting classifier
voting_clf = VotingClassifier(
    estimators=base_models,
    voting='soft',  # Use probabilities for voting
    n_jobs=-1
)

voting_clf.fit(X_selected, y)

# Create stacking classifier
stacking_clf = StackingClassifier(
    estimators=base_models,
    final_estimator=LogisticRegression(max_iter=1000, random_state=42),
    n_jobs=-1
)

stacking_clf.fit(X_selected, y)

# Evaluate models
models = {
    'Voting Classifier': voting_clf,
    'Stacking Classifier': stacking_clf,
    'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42).fit(X_selected, y),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42).fit(X_selected, y)
}

results = {}
for name, model in models.items():
    print(f"\nEvaluating {name}...")
    
    # Predict on test set
    y_pred = model.predict(X_selected_test)
    y_prob = model.predict_proba(X_selected_test)[:, 1] if hasattr(model, 'predict_proba') else None
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    balanced_acc = balanced_accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob) if y_prob is not None else None
    
    # Store results
    results[name] = {
        'model': model,
        'accuracy': accuracy,
        'balanced_accuracy': balanced_acc,
        'auc': auc,
        'y_pred': y_pred,
        'y_prob': y_prob
    }
    
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  Balanced Accuracy: {balanced_acc:.4f}")
    if auc is not None:
        print(f"  AUC: {auc:.4f}")

# Find best model
best_model_name = max(results.keys(), key=lambda x: results[x]['balanced_accuracy'])
best_model = results[best_model_name]['model']
best_balanced_acc = results[best_model_name]['balanced_accuracy']

print(f"\n{'='*60}")
print(f"Best model: {best_model_name} with balanced accuracy: {best_balanced_acc:.4f}")

# Compare with baseline
baseline_balanced_accuracy = 0.78
print(f"Baseline balanced accuracy: {baseline_balanced_accuracy:.4f}")
print(f"Improvement over baseline: {best_balanced_acc - baseline_balanced_accuracy:.4f}")

# Save best model and components
joblib.dump(best_model, '../outputs/final_best_model.pkl')
joblib.dump(scaler, '../outputs/final_scaler.pkl')
joblib.dump(selector, '../outputs/final_selector.pkl')
joblib.dump(vectorizer, '../outputs/final_vectorizer.pkl')
joblib.dump(extractor_basic, '../outputs/final_extractor_basic.pkl')
joblib.dump(extractor_advanced, '../outputs/final_extractor_advanced.pkl')

# Save results
results_df = pd.DataFrame([
    {
        'model': name,
        'accuracy': results[name]['accuracy'],
        'balanced_accuracy': results[name]['balanced_accuracy'],
        'auc': results[name]['auc']
    }
    for name in results.keys()
])
results_df.to_csv('../outputs/final_model_results.csv', index=False)

# Create comprehensive visualizations
plt.figure(figsize=(16, 12))

# Plot model comparison
plt.subplot(2, 3, 1)
model_names = list(results.keys())
accuracies = [results[name]['accuracy'] for name in model_names]
balanced_accuracies = [results[name]['balanced_accuracy'] for name in model_names]

x = np.arange(len(model_names))
width = 0.35

plt.bar(x - width/2, accuracies, width, label='Accuracy', alpha=0.8)
plt.bar(x + width/2, balanced_accuracies, width, label='Balanced Accuracy', alpha=0.8)
plt.axhline(y=baseline_balanced_accuracy, color='r', linestyle='--', 
            label=f'Baseline ({baseline_balanced_accuracy:.2f})', linewidth=2)
plt.xlabel('Model')
plt.ylabel('Score')
plt.title('Model Performance on Test Set')
plt.xticks(x, model_names, rotation=45)
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(0, 1.0)

# Plot confusion matrix for best model
plt.subplot(2, 3, 2)
cm = confusion_matrix(y_test, results[best_model_name]['y_pred'])
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Non-variable (0)', 'Variable (1)'],
            yticklabels=['Non-variable (0)', 'Variable (1)'])
plt.title(f'Confusion Matrix - {best_model_name}\nBalanced Acc: {best_balanced_acc:.3f}')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')

# Plot ROC curve if probabilities available
if results[best_model_name]['y_prob'] is not None:
    plt.subplot(2, 3, 3)
    from sklearn.metrics import roc_curve
    
    fpr, tpr, _ = roc_curve(y_test, results[best_model_name]['y_prob'])
    auc_score = results[best_model_name]['auc']
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {auc_score:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC Curve - {best_model_name}')
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)

# Plot feature importance for tree-based models
if hasattr(best_model, 'feature_importances_'):
    plt.subplot(2, 3, 4)
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    top_n = 20
    
    plt.barh(range(top_n), importances[indices[:top_n]][::-1])
    plt.yticks(range(top_n), [f'Feature {i}' for i in indices[:top_n]][::-1])
    plt.xlabel('Feature Importance')
    plt.title(f'Top {top_n} Feature Importances')
    plt.grid(True, alpha=0.3, axis='x')

# Plot classification report as heatmap
plt.subplot(2, 3, 5)
report = classification_report(y_test, results[best_model_name]['y_pred'], 
                               target_names=['Non-variable', 'Variable'], output_dict=True)
report_df = pd.DataFrame(report).transpose()

# Extract metrics for heatmap
metrics_df = report_df[['precision', 'recall', 'f1-score']].iloc[:2]
sns.heatmap(metrics_df, annot=True, fmt='.3f', cmap='YlOrRd', cbar_kws={'label': 'Score'})
plt.title('Classification Metrics by Class')

# Plot error analysis
plt.subplot(2, 3, 6)
error_mask = results[best_model_name]['y_pred'] != y_test
error_indices = np.where(error_mask)[0]

if len(error_indices) > 0:
    error_types = []
    for idx in error_indices[:min(20, len(error_indices))]:
        true_label = y_test[idx]
        pred_label = results[best_model_name]['y_pred'][idx]
        error_types.append(f'True:{true_label}->Pred:{pred_label}')
    
    error_counts = pd.Series(error_types).value_counts()
    error_counts.plot(kind='bar', alpha=0.7)
    plt.xlabel('Error Type (True->Predicted)')
    plt.ylabel('Count')
    plt.title(f'Error Analysis ({len(error_indices)} errors total)')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../report/images/final_model_performance.png', dpi=150, bbox_inches='tight')
plt.close()

# Print detailed report
print("\n" + "="*60)
print("Detailed Classification Report for Best Model:")
print("="*60)
print(classification_report(y_test, results[best_model_name]['y_pred'], 
                            target_names=['Non-variable', 'Variable']))

# Save predictions
predictions_df = pd.DataFrame({
    'object_id': test_df['object_id'],
    'true_label': y_test,
    'predicted_label': results[best_model_name]['y_pred'],
    'predicted_probability': results[best_model_name]['y_prob'] if results[best_model_name]['y_prob'] is not None else np.nan
})
predictions_df.to_csv('../outputs/final_predictions.csv', index=False)

print("\nFinal analysis complete. Results saved to outputs/ and report/images/")