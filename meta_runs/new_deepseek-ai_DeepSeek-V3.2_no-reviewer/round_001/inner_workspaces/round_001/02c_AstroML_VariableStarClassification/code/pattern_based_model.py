import pandas as pd
import numpy as np
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

# Based on pattern analysis, define discriminative patterns
# From earlier analysis:
# Variable star patterns: 'zv.', '.*v', 'vw.', 'z.u', 'v.u', 'yv.', 'w.v', 'xvw', 'vwx', '.yy'
# Non-variable star patterns: 'u.x', '.yz', 'wu.', '*wu', 'wu*', 'uxu', 'yzv', 'u..', 'uwx', 'zv*'

variable_patterns = [
    'zv.', '.*v', 'vw.', 'z.u', 'v.u', 'yv.', 'w.v', 'xvw', 'vwx', '.yy',
    'zv', 'v.', '.v', 'wv', 'xv', 'yv', 'zv', '.*', '.y', 'vw'
]

non_variable_patterns = [
    'u.x', '.yz', 'wu.', '*wu', 'wu*', 'uxu', 'yzv', 'u..', 'uwx', 'zv*',
    'u.', '.y', 'wu', '*w', 'ux', 'yz', 'u.', 'uw', 'zv', 'wu'
]

# Also include bigrams with largest differences from earlier analysis
significant_bigrams = [
    'wu', 'y*', 'xw', 'yz', '**', '.z', 'w.', 'yu', 'zz', 'yx',
    '*z', 'yv', '..', '*v', 'vw', 'v.', 'x*', 'uz', 'uy', '*y'
]

def extract_pattern_features(sequences, patterns):
    """Extract pattern presence features"""
    features = []
    
    for seq in sequences:
        seq_features = []
        
        # Check for pattern presence
        for pattern in patterns:
            if pattern in seq:
                seq_features.append(1)
            else:
                seq_features.append(0)
        
        # Count occurrences of each pattern
        for pattern in patterns:
            count = seq.count(pattern)
            seq_features.append(count)
        
        # Pattern density (occurrences per length)
        for pattern in patterns:
            count = seq.count(pattern)
            density = count / len(seq) if len(seq) > 0 else 0
            seq_features.append(density)
        
        features.append(seq_features)
    
    return np.array(features)

# Extract features for all patterns
all_patterns = variable_patterns + non_variable_patterns + significant_bigrams
all_patterns = list(set(all_patterns))  # Remove duplicates
print(f"\nUsing {len(all_patterns)} unique patterns for feature extraction")
print("Sample patterns:", all_patterns[:20])

X_train = extract_pattern_features(train_df['symbol_series'], all_patterns)
y_train = train_df['label'].values

X_val = extract_pattern_features(val_df['symbol_series'], all_patterns)
y_val = val_df['label'].values

X_test = extract_pattern_features(test_df['symbol_series'], all_patterns)
y_test = test_df['label'].values

print(f"\nFeature matrix shape: {X_train.shape}")
print(f"Number of features per sequence: {X_train.shape[1]}")

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
    model.fit(X_train, y_train)
    
    # Predict on validation set
    y_val_pred = model.predict(X_val)
    
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
y_test_pred = best_model.predict(X_test)
test_accuracy = accuracy_score(y_test, y_test_pred)
test_balanced_accuracy = balanced_accuracy_score(y_test, y_test_pred)

print(f"\nTest set performance of {best_model_name}:")
print(f"  Test Accuracy: {test_accuracy:.4f}")
print(f"  Test Balanced Accuracy: {test_balanced_accuracy:.4f}")

# Compare with baseline
baseline_balanced_accuracy = 0.78
print(f"\nBaseline balanced accuracy: {baseline_balanced_accuracy:.4f}")
print(f"Improvement over baseline: {test_balanced_accuracy - baseline_balanced_accuracy:.4f}")

# Save model
joblib.dump(best_model, '../outputs/best_pattern_model.pkl')

# Get feature importance for tree-based models
if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    # Create feature names (3 sets: presence, count, density for each pattern)
    feature_names = []
    for pattern in all_patterns:
        feature_names.append(f"has_{pattern}")
    for pattern in all_patterns:
        feature_names.append(f"count_{pattern}")
    for pattern in all_patterns:
        feature_names.append(f"density_{pattern}")
    
    # Save top features
    top_n = 20
    top_features = pd.DataFrame({
        'feature': [feature_names[i] for i in indices[:top_n]],
        'importance': importances[indices[:top_n]]
    })
    top_features.to_csv('../outputs/top_pattern_features.csv', index=False)
    
    print(f"\nTop {top_n} pattern features:")
    for i in range(min(top_n, len(top_features))):
        print(f"  {top_features.iloc[i]['feature']}: {top_features.iloc[i]['importance']:.4f}")

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
plt.title('Model Performance on Validation Set (Pattern Features)')
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

# Plot top pattern features
if hasattr(best_model, 'feature_importances_'):
    plt.subplot(2, 2, 3)
    top_n_viz = 15
    
    plt.barh(range(top_n_viz), top_features['importance'].values[:top_n_viz][::-1])
    plt.yticks(range(top_n_viz), top_features['feature'].values[:top_n_viz][::-1])
    plt.xlabel('Feature Importance')
    plt.title(f'Top {top_n_viz} Pattern Features - {best_model_name}')
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

plt.savefig('../report/images/pattern_model_performance.png', dpi=150, bbox_inches='tight')
plt.close()

# Try a simple rule-based classifier based on pattern counts
print("\n" + "="*60)
print("Testing simple rule-based classifiers:")
print("="*60)

# Rule 1: Count variable patterns vs non-variable patterns
def rule_based_classifier(sequences, variable_patterns, non_variable_patterns):
    predictions = []
    
    for seq in sequences:
        var_count = 0
        non_var_count = 0
        
        for pattern in variable_patterns:
            var_count += seq.count(pattern)
        
        for pattern in non_variable_patterns:
            non_var_count += seq.count(pattern)
        
        # Predict based on which count is higher
        if var_count > non_var_count:
            predictions.append(1)  # Variable
        else:
            predictions.append(0)  # Non-variable
    
    return np.array(predictions)

# Test on validation set
y_val_rule = rule_based_classifier(val_df['symbol_series'], variable_patterns[:10], non_variable_patterns[:10])
val_rule_accuracy = accuracy_score(y_val, y_val_rule)
val_rule_balanced_accuracy = balanced_accuracy_score(y_val, y_val_rule)

print(f"\nSimple rule-based classifier (pattern counts):")
print(f"  Validation Accuracy: {val_rule_accuracy:.4f}")
print(f"  Validation Balanced Accuracy: {val_rule_balanced_accuracy:.4f}")

# Test on test set
y_test_rule = rule_based_classifier(test_df['symbol_series'], variable_patterns[:10], non_variable_patterns[:10])
test_rule_accuracy = accuracy_score(y_test, y_test_rule)
test_rule_balanced_accuracy = balanced_accuracy_score(y_test, y_test_rule)

print(f"  Test Accuracy: {test_rule_accuracy:.4f}")
print(f"  Test Balanced Accuracy: {test_rule_balanced_accuracy:.4f}")

print("\nAnalysis complete. Results saved to outputs/ and report/images/")