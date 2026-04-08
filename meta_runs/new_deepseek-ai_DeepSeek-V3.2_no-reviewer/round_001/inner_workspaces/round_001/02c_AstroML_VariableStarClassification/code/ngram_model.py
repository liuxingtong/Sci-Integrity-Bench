import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import os
import joblib

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

# Prepare data
X_train = train_df['symbol_series'].values
y_train = train_df['label'].values

X_val = val_df['symbol_series'].values
y_val = val_df['label'].values

X_test = test_df['symbol_series'].values
y_test = test_df['label'].values

# Create n-gram features
print("\nCreating n-gram features...")

# Try different n-gram ranges
vectorizer = CountVectorizer(
    analyzer='char',
    ngram_range=(2, 4),  # Bigrams, trigrams, and 4-grams
    max_features=500  # Limit number of features
)

X_train_ngram = vectorizer.fit_transform(X_train).toarray()
X_val_ngram = vectorizer.transform(X_val).toarray()
X_test_ngram = vectorizer.transform(X_test).toarray()

print(f"N-gram feature shape: {X_train_ngram.shape}")
print(f"Number of unique n-grams: {len(vectorizer.get_feature_names_out())}")

# Get top n-grams
feature_names = vectorizer.get_feature_names_out()
print("\nSample n-gram features:", feature_names[:20])

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_ngram)
X_val_scaled = scaler.transform(X_val_ngram)
X_test_scaled = scaler.transform(X_test_ngram)

# Train models
models = {
    'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=1000, C=1, random_state=42),
    'SVM': SVC(kernel='linear', C=1, probability=True, random_state=42)
}

results = {}
for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train_scaled, y_train)
    
    # Predict on validation set
    y_val_pred = model.predict(X_val_scaled)
    
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

# Find best model
best_model_name = max(results.keys(), key=lambda x: results[x]['val_balanced_accuracy'])
best_model = results[best_model_name]['model']
print(f"\nBest model: {best_model_name} with balanced accuracy: {results[best_model_name]['val_balanced_accuracy']:.4f}")

# Evaluate on test set
y_test_pred = best_model.predict(X_test_scaled)
test_accuracy = accuracy_score(y_test, y_test_pred)
test_balanced_accuracy = balanced_accuracy_score(y_test, y_test_pred)

print(f"\nTest set performance of {best_model_name}:")
print(f"  Test Accuracy: {test_accuracy:.4f}")
print(f"  Test Balanced Accuracy: {test_balanced_accuracy:.4f}")

# Compare with baseline
baseline_balanced_accuracy = 0.78
print(f"\nBaseline balanced accuracy: {baseline_balanced_accuracy:.4f}")
print(f"Improvement over baseline: {test_balanced_accuracy - baseline_balanced_accuracy:.4f}")

# Save model and vectorizer
joblib.dump(best_model, '../outputs/best_ngram_model.pkl')
joblib.dump(vectorizer, '../outputs/ngram_vectorizer.pkl')
joblib.dump(scaler, '../outputs/ngram_scaler.pkl')

# Get feature importance for tree-based models
if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    # Save top features
    top_n = 30
    top_features = pd.DataFrame({
        'ngram': feature_names[indices[:top_n]],
        'importance': importances[indices[:top_n]]
    })
    top_features.to_csv('../outputs/top_ngram_features.csv', index=False)
    
    print(f"\nTop {top_n} n-gram features:")
    for i in range(min(top_n, len(top_features))):
        print(f"  {top_features.iloc[i]['ngram']}: {top_features.iloc[i]['importance']:.4f}")

# Create visualizations
plt.figure(figsize=(14, 10))

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
plt.title('Model Performance on Validation Set (N-gram Features)')
plt.xticks(x, model_names, rotation=45)
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(0, 1.0)

# Plot confusion matrix
plt.subplot(2, 2, 2)
cm = confusion_matrix(y_test, y_test_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Non-variable (0)', 'Variable (1)'],
            yticklabels=['Non-variable (0)', 'Variable (1)'])
plt.title(f'Confusion Matrix - {best_model_name}\nTest Set (Balanced Acc: {test_balanced_accuracy:.3f})')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')

# Plot top n-gram features
if hasattr(best_model, 'feature_importances_'):
    plt.subplot(2, 2, 3)
    top_n_viz = 15
    
    plt.barh(range(top_n_viz), top_features['importance'].values[:top_n_viz][::-1])
    plt.yticks(range(top_n_viz), top_features['ngram'].values[:top_n_viz][::-1])
    plt.xlabel('Feature Importance')
    plt.title(f'Top {top_n_viz} N-gram Features - {best_model_name}')
    plt.grid(True, alpha=0.3, axis='x')

# Plot classification report as heatmap
plt.subplot(2, 2, 4)
report = classification_report(y_test, y_test_pred, target_names=['Non-variable', 'Variable'], output_dict=True)
report_df = pd.DataFrame(report).transpose()

# Extract metrics for heatmap
metrics_df = report_df[['precision', 'recall', 'f1-score']].iloc[:2]
sns.heatmap(metrics_df, annot=True, fmt='.3f', cmap='YlOrRd', cbar_kws={'label': 'Score'})
plt.title('Classification Metrics by Class')
plt.tight_layout()

plt.savefig('../report/images/ngram_model_performance.png', dpi=150, bbox_inches='tight')
plt.close()

# Try different n-gram ranges to find optimal
print("\n" + "="*60)
print("Testing different n-gram ranges:")
print("="*60)

ngram_ranges = [(1, 1), (2, 2), (3, 3), (4, 4), (2, 3), (2, 4), (3, 5)]
ngram_results = []

for ngram_range in ngram_ranges:
    print(f"\nTesting n-gram range {ngram_range}...")
    
    vectorizer_test = CountVectorizer(
        analyzer='char',
        ngram_range=ngram_range,
        max_features=500
    )
    
    X_train_ngram_test = vectorizer_test.fit_transform(X_train).toarray()
    X_val_ngram_test = vectorizer_test.transform(X_val).toarray()
    
    # Standardize
    scaler_test = StandardScaler()
    X_train_scaled_test = scaler_test.fit_transform(X_train_ngram_test)
    X_val_scaled_test = scaler_test.transform(X_val_ngram_test)
    
    # Train simple model
    model_test = RandomForestClassifier(n_estimators=100, random_state=42)
    model_test.fit(X_train_scaled_test, y_train)
    
    y_val_pred_test = model_test.predict(X_val_scaled_test)
    val_bal_acc = balanced_accuracy_score(y_val, y_val_pred_test)
    
    ngram_results.append({
        'ngram_range': str(ngram_range),
        'n_features': X_train_ngram_test.shape[1],
        'balanced_accuracy': val_bal_acc
    })
    
    print(f"  Features: {X_train_ngram_test.shape[1]}, Balanced Accuracy: {val_bal_acc:.4f}")

# Plot n-gram range comparison
ngram_df = pd.DataFrame(ngram_results)
plt.figure(figsize=(10, 6))
plt.bar(range(len(ngram_df)), ngram_df['balanced_accuracy'])
plt.axhline(y=baseline_balanced_accuracy, color='r', linestyle='--', 
            label=f'Baseline ({baseline_balanced_accuracy:.2f})', linewidth=2)
plt.xlabel('N-gram Range')
plt.ylabel('Balanced Accuracy')
plt.title('Performance by N-gram Range (Validation Set)')
plt.xticks(range(len(ngram_df)), ngram_df['ngram_range'], rotation=45)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/ngram_range_comparison.png', dpi=150)
plt.close()

print("\nAnalysis complete. Results saved to outputs/ and report/images/")