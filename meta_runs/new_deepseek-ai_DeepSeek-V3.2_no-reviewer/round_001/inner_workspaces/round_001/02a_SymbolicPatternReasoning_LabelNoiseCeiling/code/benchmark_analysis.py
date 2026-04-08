import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

# Extract features and labels
feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train_raw = train[feature_cols]
y_train = train['label']
X_val_raw = val[feature_cols]
y_val = val['label']
X_test_raw = test[feature_cols]
y_test = test['label']

print("Data loaded successfully!")
print(f"Train: {X_train_raw.shape}, Validation: {X_val_raw.shape}, Test: {X_test_raw.shape}")
print()

# Function to preprocess data
def preprocess_data(X_raw):
    """Convert symbolic tokens to one-hot encoded features"""
    # Flatten the 8xN matrix to 1D array for one-hot encoding
    X_flat = X_raw.values.reshape(-1, 1)
    
    # Fit encoder on training data only
    if not hasattr(preprocess_data, 'encoder'):
        preprocess_data.encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        preprocess_data.encoder.fit(X_flat)
    
    # Transform
    X_encoded = preprocess_data.encoder.transform(X_flat)
    
    # Reshape back to (n_samples, 8 * n_tokens)
    n_samples = X_raw.shape[0]
    X_encoded = X_encoded.reshape(n_samples, -1)
    
    return X_encoded

# Preprocess all data
print("Preprocessing data...")
X_train = preprocess_data(X_train_raw)
X_val = preprocess_data(X_val_raw)
X_test = preprocess_data(X_test_raw)

print(f"After one-hot encoding: Train shape: {X_train.shape}")
print(f"Number of features: {X_train.shape[1]}")
print()

# Baseline: majority class
majority_class = y_train.mode()[0]
baseline_val_acc = accuracy_score(y_val, [majority_class] * len(y_val))
baseline_test_acc = accuracy_score(y_test, [majority_class] * len(y_test))

print(f"Baseline (majority class = {majority_class}):")
print(f"  Validation accuracy: {baseline_val_acc:.4f}")
print(f"  Test accuracy: {baseline_test_acc:.4f}")
print()

# Initialize models
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
    'XGBoost': xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss'),
    'LightGBM': lgb.LGBMClassifier(n_estimators=100, random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)
}

# Train and evaluate models
results = []
for name, model in models.items():
    print(f"Training {name}...")
    
    # Train
    model.fit(X_train, y_train)
    
    # Predict
    y_val_pred = model.predict(X_val)
    y_test_pred = model.predict(X_test)
    
    # Calculate accuracies
    val_acc = accuracy_score(y_val, y_val_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    # Store results
    results.append({
        'Model': name,
        'Val Accuracy': val_acc,
        'Test Accuracy': test_acc
    })
    
    print(f"  Validation accuracy: {val_acc:.4f}")
    print(f"  Test accuracy: {test_acc:.4f}")
    
    # Print classification report for the best model later
    if name == 'Random Forest':  # Just as an example
        print(f"  Test classification report for {name}:")
        print(classification_report(y_test, y_test_pred))
    print()

# Add baseline to results
results.append({
    'Model': 'Baseline (Majority)',
    'Val Accuracy': baseline_val_acc,
    'Test Accuracy': baseline_test_acc
})

# Convert to DataFrame
results_df = pd.DataFrame(results)
print("\n=== Summary of Results ===")
print(results_df.to_string(index=False))
print()

# Compare with SOTA (70%)
sota_threshold = 0.70
print(f"SOTA threshold: {sota_threshold:.2%}")
print("Models achieving or exceeding SOTA:")
sota_models = results_df[results_df['Test Accuracy'] >= sota_threshold]
if len(sota_models) > 0:
    print(sota_models.to_string(index=False))
else:
    print("None")
print()

# Create visualizations
plt.figure(figsize=(12, 6))

# Bar plot of test accuracies
plt.subplot(1, 2, 1)
sorted_results = results_df.sort_values('Test Accuracy', ascending=False)
colors = ['green' if acc >= sota_threshold else 'blue' for acc in sorted_results['Test Accuracy']]
plt.barh(sorted_results['Model'], sorted_results['Test Accuracy'], color=colors)
plt.axvline(x=sota_threshold, color='red', linestyle='--', label=f'SOTA ({sota_threshold:.0%})')
plt.xlabel('Test Accuracy')
plt.title('Model Performance Comparison')
plt.legend()
plt.xlim(0, 1.0)

# Scatter plot of val vs test accuracy
plt.subplot(1, 2, 2)
for _, row in results_df.iterrows():
    plt.scatter(row['Val Accuracy'], row['Test Accuracy'], s=100, label=row['Model'])
plt.plot([0, 1], [0, 1], 'k--', alpha=0.3)
plt.xlabel('Validation Accuracy')
plt.ylabel('Test Accuracy')
plt.title('Validation vs Test Accuracy')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()

# Save figure
plt.savefig('../report/images/model_performance.png', dpi=300, bbox_inches='tight')
print("Figure saved to '../report/images/model_performance.png'")

# Feature importance analysis for Random Forest (as an example)
rf_model = models['Random Forest']
feature_importance = rf_model.feature_importances_

# Get feature names (one-hot encoded)
feature_names = []
for i in range(8):  # 8 positions
    for token in preprocess_data.encoder.categories_[0]:
        feature_names.append(f"pos{i}_{token}")

# Create DataFrame for feature importance
importance_df = pd.DataFrame({
    'Feature': feature_names,
    'Importance': feature_importance
})

# Sort by importance
importance_df = importance_df.sort_values('Importance', ascending=False)

print("\nTop 20 most important features from Random Forest:")
print(importance_df.head(20).to_string(index=False))

# Plot feature importance
plt.figure(figsize=(10, 8))
top_n = 30
top_features = importance_df.head(top_n)
plt.barh(range(top_n), top_features['Importance'][::-1])
plt.yticks(range(top_n), top_features['Feature'][::-1])
plt.xlabel('Feature Importance')
plt.title(f'Top {top_n} Feature Importances (Random Forest)')
plt.tight_layout()
plt.savefig('../report/images/feature_importance.png', dpi=300, bbox_inches='tight')
print(f"Figure saved to '../report/images/feature_importance.png'")

# Save results to CSV
results_df.to_csv('../outputs/model_results.csv', index=False)
print("\nResults saved to '../outputs/model_results.csv'")
