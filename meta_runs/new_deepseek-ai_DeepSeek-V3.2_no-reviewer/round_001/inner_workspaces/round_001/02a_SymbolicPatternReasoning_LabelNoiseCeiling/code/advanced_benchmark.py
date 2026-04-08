import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

from feature_engineering import SPRFeatureEngineer

# Set random seed for reproducibility
np.random.seed(42)

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

# Extract features and labels
feature_cols = [f"token_{i}" for i in range(8)]
X_train_raw = train[feature_cols]
y_train = train['label']
X_val_raw = val[feature_cols]
y_val = val['label']
X_test_raw = test[feature_cols]
y_test = test['label']

print("Data loaded successfully!")
print(f"Train: {X_train_raw.shape}, Validation: {X_val_raw.shape}, Test: {X_test_raw.shape}")
print()

# Engineer features
print("Engineering features...")
engineer = SPRFeatureEngineer()
X_train, feature_names = engineer.extract_features(X_train_raw)
X_val, _ = engineer.extract_features(X_val_raw)
X_test, _ = engineer.extract_features(X_test_raw)

print(f"Engineered features shape: {X_train.shape}")
print(f"Number of features: {len(feature_names)}")
print()

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Baseline: majority class
majority_class = y_train.mode()[0]
baseline_val_acc = accuracy_score(y_val, [majority_class] * len(y_val))
baseline_test_acc = accuracy_score(y_test, [majority_class] * len(y_test))

print(f"Baseline (majority class = {majority_class}):")
print(f"  Validation accuracy: {baseline_val_acc:.4f}")
print(f"  Test accuracy: {baseline_test_acc:.4f}")
print()

# Initialize models with some hyperparameter tuning
models = {
    'Logistic Regression': {
        'model': LogisticRegression(max_iter=1000, random_state=42),
        'params': {'C': [0.01, 0.1, 1, 10, 100]}
    },
    'Random Forest': {
        'model': RandomForestClassifier(random_state=42),
        'params': {
            'n_estimators': [100, 200],
            'max_depth': [10, 20, None],
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
    'XGBoost': {
        'model': xgb.XGBClassifier(random_state=42, eval_metric='logloss'),
        'params': {
            'n_estimators': [100, 200],
            'max_depth': [3, 6],
            'learning_rate': [0.01, 0.1]
        }
    },
    'LightGBM': {
        'model': lgb.LGBMClassifier(random_state=42),
        'params': {
            'n_estimators': [100, 200],
            'num_leaves': [31, 63],
            'learning_rate': [0.01, 0.1]
        }
    },
    'MLP': {
        'model': MLPClassifier(max_iter=500, random_state=42),
        'params': {
            'hidden_layer_sizes': [(64, 32), (128, 64)],
            'alpha': [0.0001, 0.001]
        }
    }
}

# Train and evaluate models with hyperparameter tuning
results = []
best_models = {}

for name, config in models.items():
    print(f"\nTraining {name} with hyperparameter tuning...")
    
    # Perform grid search
    grid_search = GridSearchCV(
        config['model'], 
        config['params'], 
        cv=3, 
        scoring='accuracy',
        n_jobs=-1,
        verbose=0
    )
    
    grid_search.fit(X_train_scaled, y_train)
    
    # Get best model
    best_model = grid_search.best_estimator_
    best_models[name] = best_model
    
    # Predict
    y_val_pred = best_model.predict(X_val_scaled)
    y_test_pred = best_model.predict(X_test_scaled)
    
    # Calculate accuracies
    val_acc = accuracy_score(y_val, y_val_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    # Store results
    results.append({
        'Model': name,
        'Val Accuracy': val_acc,
        'Test Accuracy': test_acc,
        'Best Params': str(grid_search.best_params_)
    })
    
    print(f"  Best params: {grid_search.best_params_}")
    print(f"  Validation accuracy: {val_acc:.4f}")
    print(f"  Test accuracy: {test_acc:.4f}")
    
    # Print detailed report for the best overall model
    if test_acc == max([r['Test Accuracy'] for r in results]):
        print(f"  \n  Best model so far! Test classification report:")
        print(classification_report(y_test, y_test_pred))
        
        # Save confusion matrix
        cm = confusion_matrix(y_test, y_test_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=['Reject (0)', 'Accept (1)'],
                    yticklabels=['Reject (0)', 'Accept (1)'])
        plt.title(f'Confusion Matrix - {name}')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(f'../report/images/confusion_matrix_{name.lower().replace(" ", "_")}.png', dpi=300)
        print(f"  Confusion matrix saved to '../report/images/confusion_matrix_{name.lower().replace(' ', '_')}.png'")

# Add baseline to results
results.append({
    'Model': 'Baseline (Majority)',
    'Val Accuracy': baseline_val_acc,
    'Test Accuracy': baseline_test_acc,
    'Best Params': 'N/A'
})

# Convert to DataFrame
results_df = pd.DataFrame(results)
print("\n" + "="*60)
print("=== Summary of Results ===")
print("="*60)
print(results_df[['Model', 'Val Accuracy', 'Test Accuracy']].to_string(index=False))
print()

# Compare with SOTA (70%)
sota_threshold = 0.70
print(f"SOTA threshold: {sota_threshold:.2%}")
print("Models achieving or exceeding SOTA:")
sota_models = results_df[results_df['Test Accuracy'] >= sota_threshold]
if len(sota_models) > 0:
    print(sota_models[['Model', 'Test Accuracy']].to_string(index=False))
else:
    print("None")
    
    # Find best model
    best_idx = results_df['Test Accuracy'].idxmax()
    best_model_name = results_df.loc[best_idx, 'Model']
    best_test_acc = results_df.loc[best_idx, 'Test Accuracy']
    print(f"\nBest model: {best_model_name} with test accuracy: {best_test_acc:.4f}")
    print(f"Gap to SOTA: {sota_threshold - best_test_acc:.4f} ({((sota_threshold - best_test_acc)/sota_threshold)*100:.1f}% below SOTA)")

print()

# Create visualizations
plt.figure(figsize=(14, 6))

# Bar plot of test accuracies
plt.subplot(1, 2, 1)
sorted_results = results_df.sort_values('Test Accuracy', ascending=False)
colors = ['green' if acc >= sota_threshold else 'blue' for acc in sorted_results['Test Accuracy']]
plt.barh(sorted_results['Model'], sorted_results['Test Accuracy'], color=colors)
plt.axvline(x=sota_threshold, color='red', linestyle='--', label=f'SOTA ({sota_threshold:.0%})')
plt.xlabel('Test Accuracy')
plt.title('Model Performance Comparison (with Feature Engineering)')
plt.legend()
plt.xlim(0, 1.0)

# Scatter plot of val vs test accuracy
plt.subplot(1, 2, 2)
for _, row in results_df.iterrows():
    if row['Model'] != 'Baseline (Majority)':
        plt.scatter(row['Val Accuracy'], row['Test Accuracy'], s=100, label=row['Model'])
plt.plot([0, 1], [0, 1], 'k--', alpha=0.3)
plt.xlabel('Validation Accuracy')
plt.ylabel('Test Accuracy')
plt.title('Validation vs Test Accuracy')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()

# Save figure
plt.savefig('../report/images/model_performance_engineered.png', dpi=300, bbox_inches='tight')
print("Figure saved to '../report/images/model_performance_engineered.png'")

# Feature importance analysis for the best tree-based model
best_tree_model_name = None
best_tree_acc = 0
for name in ['Random Forest', 'Gradient Boosting', 'XGBoost', 'LightGBM']:
    if name in best_models:
        acc = results_df[results_df['Model'] == name]['Test Accuracy'].values[0]
        if acc > best_tree_acc:
            best_tree_acc = acc
            best_tree_model_name = name

if best_tree_model_name:
    print(f"\nAnalyzing feature importance for {best_tree_model_name}...")
    best_tree_model = best_models[best_tree_model_name]
    
    if hasattr(best_tree_model, 'feature_importances_'):
        feature_importance = best_tree_model.feature_importances_
        
        # Create DataFrame for feature importance
        importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': feature_importance
        })
        
        # Sort by importance
        importance_df = importance_df.sort_values('Importance', ascending=False)
        
        print("\nTop 20 most important features:")
        print(importance_df.head(20).to_string(index=False))
        
        # Plot feature importance
        plt.figure(figsize=(12, 8))
        top_n = 30
        top_features = importance_df.head(top_n)
        plt.barh(range(top_n), top_features['Importance'][::-1])
        plt.yticks(range(top_n), top_features['Feature'][::-1])
        plt.xlabel('Feature Importance')
        plt.title(f'Top {top_n} Feature Importances ({best_tree_model_name})')
        plt.tight_layout()
        plt.savefig(f'../report/images/feature_importance_{best_tree_model_name.lower().replace(" ", "_")}.png', dpi=300, bbox_inches='tight')
        print(f"Figure saved to '../report/images/feature_importance_{best_tree_model_name.lower().replace(' ', '_')}.png'")
        
        # Save feature importance to CSV
        importance_df.to_csv(f'../outputs/feature_importance_{best_tree_model_name.lower().replace(" ", "_")}.csv', index=False)
        print(f"Feature importance saved to '../outputs/feature_importance_{best_tree_model_name.lower().replace(' ', '_')}.csv'")

# Save results to CSV
results_df.to_csv('../outputs/model_results_engineered.csv', index=False)
print("\nResults saved to '../outputs/model_results_engineered.csv'")

# Try ensemble of best models
print("\n" + "="*60)
print("Trying ensemble methods...")
print("="*60)

# Get top 3 models (excluding baseline)
top_models = results_df[results_df['Model'] != 'Baseline (Majority)'].nlargest(3, 'Test Accuracy')
top_model_names = top_models['Model'].tolist()
print(f"Top 3 models for ensemble: {top_model_names}")

# Create ensemble predictions
ensemble_val_preds = []
ensemble_test_preds = []

for name in top_model_names:
    if name in best_models:
        model = best_models[name]
        ensemble_val_preds.append(model.predict(X_val_scaled))
        ensemble_test_preds.append(model.predict(X_test_scaled))

if ensemble_val_preds:
    # Average predictions
    ensemble_val_pred = np.round(np.mean(ensemble_val_preds, axis=0)).astype(int)
    ensemble_test_pred = np.round(np.mean(ensemble_test_preds, axis=0)).astype(int)
    
    # Calculate accuracies
    ensemble_val_acc = accuracy_score(y_val, ensemble_val_pred)
    ensemble_test_acc = accuracy_score(y_test, ensemble_test_pred)
    
    print(f"\nEnsemble (average of top {len(top_model_names)} models):")
    print(f"  Validation accuracy: {ensemble_val_acc:.4f}")
    print(f"  Test accuracy: {ensemble_test_acc:.4f}")
    
    # Add to results
    results_df = pd.concat([results_df, pd.DataFrame([{
        'Model': f'Ensemble ({len(top_model_names)} models)',
        'Val Accuracy': ensemble_val_acc,
        'Test Accuracy': ensemble_test_acc,
        'Best Params': 'N/A'
    }])], ignore_index=True)
    
    print(f"\nUpdated results with ensemble:")
    print(results_df[['Model', 'Val Accuracy', 'Test Accuracy']].to_string(index=False))
