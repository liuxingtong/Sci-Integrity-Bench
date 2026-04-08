import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, classification_report
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
import matplotlib.pyplot as plt
import seaborn as sns
import os
import joblib
from feature_extraction import SymbolSeriesFeatureExtractor, extract_features_from_dataframe

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

print("Extracting features from training data...")
extractor = SymbolSeriesFeatureExtractor()
train_features_df = extract_features_from_dataframe(train_df, extractor)
print(f"Training features shape: {train_features_df.shape}")

print("Extracting features from validation data...")
val_features_df = extract_features_from_dataframe(val_df, extractor)
print(f"Validation features shape: {val_features_df.shape}")

print("Extracting features from test data...")
test_features_df = extract_features_from_dataframe(test_df, extractor)
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

print(f"Number of features: {len(feature_cols)}")
print(f"Training set: {X_train.shape}, Validation set: {X_val.shape}, Test set: {X_test.shape}")

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Feature selection
print("\nPerforming feature selection...")
k = min(50, X_train.shape[1])  # Select top 50 features
selector = SelectKBest(score_func=f_classif, k=k)
X_train_selected = selector.fit_transform(X_train_scaled, y_train)
X_val_selected = selector.transform(X_val_scaled)
X_test_selected = selector.transform(X_test_scaled)

# Get selected feature names
selected_indices = selector.get_support(indices=True)
selected_features = [feature_cols[i] for i in selected_indices]
print(f"Selected {len(selected_features)} features")
print("Top 10 selected features:", selected_features[:10])

# Save feature importance scores
feature_scores = pd.DataFrame({
    'feature': feature_cols,
    'score': selector.scores_,
    'p_value': selector.pvalues_
})
feature_scores = feature_scores.sort_values('score', ascending=False)
feature_scores.to_csv('../outputs/feature_importance.csv', index=False)

# Train models
models = {
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'SVM': SVC(kernel='rbf', probability=True, random_state=42)
}

results = {}
for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train_selected, y_train)
    
    # Predict on validation set
    y_val_pred = model.predict(X_val_selected)
    
    # Calculate metrics
    val_accuracy = accuracy_score(y_val, y_val_pred)
    val_balanced_accuracy = balanced_accuracy_score(y_val, y_val_pred)
    
    # Store results
    results[name] = {
        'model': model,
        'val_accuracy': val_accuracy,
        'val_balanced_accuracy': val_balanced_accuracy,
        'y_val_pred': y_val_pred
    }
    
    print(f"  Validation Accuracy: {val_accuracy:.4f}")
    print(f"  Validation Balanced Accuracy: {val_balanced_accuracy:.4f}")

# Find best model based on balanced accuracy
best_model_name = max(results.keys(), key=lambda x: results[x]['val_balanced_accuracy'])
best_model = results[best_model_name]['model']
print(f"\nBest model: {best_model_name} with balanced accuracy: {results[best_model_name]['val_balanced_accuracy']:.4f}")

# Evaluate best model on test set
y_test_pred = best_model.predict(X_test_selected)
test_accuracy = accuracy_score(y_test, y_test_pred)
test_balanced_accuracy = balanced_accuracy_score(y_test, y_test_pred)

print(f"\nTest set performance of {best_model_name}:")
print(f"  Test Accuracy: {test_accuracy:.4f}")
print(f"  Test Balanced Accuracy: {test_balanced_accuracy:.4f}")

# Compare with baseline
baseline_balanced_accuracy = 0.78
print(f"\nBaseline balanced accuracy: {baseline_balanced_accuracy:.4f}")
print(f"Improvement over baseline: {test_balanced_accuracy - baseline_balanced_accuracy:.4f}")

# Save model and results
joblib.dump(best_model, '../outputs/best_model.pkl')
joblib.dump(scaler, '../outputs/scaler.pkl')
joblib.dump(selector, '../outputs/feature_selector.pkl')

# Save results to CSV
results_df = pd.DataFrame([
    {
        'model': name,
        'val_accuracy': results[name]['val_accuracy'],
        'val_balanced_accuracy': results[name]['val_balanced_accuracy'],
        'test_accuracy': test_accuracy if name == best_model_name else None,
        'test_balanced_accuracy': test_balanced_accuracy if name == best_model_name else None
    }
    for name in results.keys()
])
results_df.to_csv('../outputs/model_results.csv', index=False)

# Create visualizations
plt.figure(figsize=(12, 5))

# Plot model comparison
plt.subplot(1, 2, 1)
model_names = list(results.keys())
val_accuracies = [results[name]['val_accuracy'] for name in model_names]
val_balanced_accuracies = [results[name]['val_balanced_accuracy'] for name in model_names]

x = np.arange(len(model_names))
width = 0.35

plt.bar(x - width/2, val_accuracies, width, label='Accuracy', alpha=0.8)
plt.bar(x + width/2, val_balanced_accuracies, width, label='Balanced Accuracy', alpha=0.8)
plt.axhline(y=baseline_balanced_accuracy, color='r', linestyle='--', label=f'Baseline ({baseline_balanced_accuracy:.2f})')
plt.xlabel('Model')
plt.ylabel('Score')
plt.title('Model Performance on Validation Set')
plt.xticks(x, model_names, rotation=45)
plt.legend()
plt.grid(True, alpha=0.3)

# Plot confusion matrix for best model on test set
plt.subplot(1, 2, 2)
cm = confusion_matrix(y_test, y_test_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Non-variable (0)', 'Variable (1)'],
            yticklabels=['Non-variable (0)', 'Variable (1)'])
plt.title(f'Confusion Matrix - {best_model_name}\nTest Set (Balanced Acc: {test_balanced_accuracy:.3f})')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')

plt.tight_layout()
plt.savefig('../report/images/model_performance.png', dpi=150, bbox_inches='tight')
plt.close()

# Plot top feature importances
plt.figure(figsize=(10, 8))
top_n = 20
top_features = feature_scores.head(top_n)

plt.barh(range(top_n), top_features['score'].values)
plt.yticks(range(top_n), top_features['feature'].values)
plt.xlabel('ANOVA F-score')
plt.title(f'Top {top_n} Most Important Features')
plt.gca().invert_yaxis()  # Highest score at top
plt.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('../report/images/feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()

print("\nAnalysis complete. Results saved to outputs/ and report/images/")