import pandas as pd
import numpy as np
import json
import os
from catboost import CatBoostClassifier, Pool
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load registry
with open("../data/benchmark_registry.json") as f:
    registry = json.load(f)

# Selected benchmarks
selected_benchmarks = ['FDLOT', 'WVIOP', 'XPOFG', 'OQMEA']
print(f"Selected benchmarks: {selected_benchmarks}")

# Function to load data
def load_benchmark(code):
    train = pd.read_csv(f"../data/{code}_train.csv")
    val = pd.read_csv(f"../data/{code}_val.csv")
    test = pd.read_csv(f"../data/{code}_test.csv")
    return train, val, test

# Function to prepare data for CatBoost
def prepare_data(train_df, val_df, test_df):
    # Separate features and target
    X_train = train_df.drop('label', axis=1)
    y_train = train_df['label']
    X_val = val_df.drop('label', axis=1)
    y_val = val_df['label']
    X_test = test_df.drop('label', axis=1)
    y_test = test_df['label']
    
    # Identify categorical features (all token columns)
    cat_features = [col for col in X_train.columns if col.startswith('token_')]
    
    # Create CatBoost Pool objects for efficient training
    train_pool = Pool(X_train, y_train, cat_features=cat_features)
    val_pool = Pool(X_val, y_val, cat_features=cat_features)
    test_pool = Pool(X_test, y_test, cat_features=cat_features)
    
    return X_train, y_train, X_val, y_val, X_test, y_test, train_pool, val_pool, test_pool, cat_features

# Hyperparameter grid for tuning - simplified
param_grid = {
    'iterations': [100, 200],
    'depth': [4, 6],
    'learning_rate': [0.05, 0.1],
    'l2_leaf_reg': [3, 5]
}

# Results storage
results = []

for code in selected_benchmarks:
    print(f"\n{'='*60}")
    print(f"Training model for benchmark: {code}")
    print(f"SOTA accuracy: {registry[code]['sota_accuracy']}%")
    
    # Load data
    train_df, val_df, test_df = load_benchmark(code)
    print(f"Train shape: {train_df.shape}, Val shape: {val_df.shape}, Test shape: {test_df.shape}")
    
    # Prepare data
    X_train, y_train, X_val, y_val, X_test, y_test, train_pool, val_pool, test_pool, cat_features = prepare_data(train_df, val_df, test_df)
    print(f"Number of categorical features: {len(cat_features)}")
    
    # Simple hyperparameter tuning (grid search)
    best_val_acc = 0
    best_params = None
    best_model = None
    
    print("Performing hyperparameter tuning...")
    total_combinations = len(param_grid['iterations']) * len(param_grid['depth']) * \
                         len(param_grid['learning_rate']) * len(param_grid['l2_leaf_reg'])
    combo_count = 0
    
    for iterations in param_grid['iterations']:
        for depth in param_grid['depth']:
            for lr in param_grid['learning_rate']:
                for l2 in param_grid['l2_leaf_reg']:
                    combo_count += 1
                    if combo_count % 2 == 0:
                        print(f"  Testing combination {combo_count}/{total_combinations}...")
                    
                    model = CatBoostClassifier(
                        iterations=iterations,
                        depth=depth,
                        learning_rate=lr,
                        l2_leaf_reg=l2,
                        random_seed=42,
                        verbose=False,
                        task_type='CPU',
                        early_stopping_rounds=20
                    )
                    
                    # Train with early stopping on validation set
                    model.fit(train_pool, eval_set=val_pool, verbose=False)
                    
                    # Predict on validation set
                    y_val_pred = model.predict(val_pool)
                    val_acc = accuracy_score(y_val, y_val_pred)
                    
                    if val_acc > best_val_acc:
                        best_val_acc = val_acc
                        best_params = {'iterations': iterations, 'depth': depth, 
                                      'learning_rate': lr, 'l2_leaf_reg': l2}
                        best_model = model
    
    print(f"Best validation accuracy: {best_val_acc:.4f}")
    print(f"Best parameters: {best_params}")
    
    # Evaluate on test set
    y_test_pred = best_model.predict(test_pool)
    test_acc = accuracy_score(y_test, y_test_pred)
    print(f"Test accuracy: {test_acc:.4f}")
    
    # Compare with SOTA
    sota_acc = registry[code]['sota_accuracy'] / 100  # Convert from percentage
    diff = test_acc - sota_acc
    print(f"SOTA accuracy: {sota_acc:.4f}")
    print(f"Difference (Our - SOTA): {diff:.4f}")
    
    # Save model
    model_path = f"../outputs/models/{code}_model.cbm"
    best_model.save_model(model_path)
    print(f"Model saved to {model_path}")
    
    # Store results
    results.append({
        'benchmark': code,
        'sota_accuracy': sota_acc * 100,  # Back to percentage
        'test_accuracy': test_acc * 100,
        'val_accuracy': best_val_acc * 100,
        'difference': diff * 100,
        'sequence_length': len(cat_features),
        'train_size': len(train_df),
        'val_size': len(val_df),
        'test_size': len(test_df),
        'best_params': best_params
    })
    
    # Create feature importance plot
    feature_importance = best_model.get_feature_importance()
    feature_names = X_train.columns.tolist()
    
    plt.figure(figsize=(10, 6))
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': feature_importance
    }).sort_values('importance', ascending=True)
    
    plt.barh(range(len(importance_df)), importance_df['importance'])
    plt.yticks(range(len(importance_df)), importance_df['feature'])
    plt.xlabel('Feature Importance')
    plt.title(f'Feature Importance for {code}')
    plt.tight_layout()
    plt.savefig(f'../outputs/figures/{code}_feature_importance.png', dpi=150)
    plt.close()
    
    # Create confusion matrix
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_test, y_test_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Class 0', 'Class 1'],
                yticklabels=['Class 0', 'Class 1'])
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title(f'Confusion Matrix for {code}\nTest Accuracy: {test_acc:.4f}')
    plt.tight_layout()
    plt.savefig(f'../outputs/figures/{code}_confusion_matrix.png', dpi=150)
    plt.close()

# Save results to CSV
results_df = pd.DataFrame(results)
results_path = "../outputs/results/benchmark_results.csv"
results_df.to_csv(results_path, index=False)
print(f"\n{'='*60}")
print(f"Results saved to {results_path}")
print("\nSummary of results:")
print(results_df[['benchmark', 'sota_accuracy', 'test_accuracy', 'difference', 'sequence_length']].to_string())

# Create comparison plot
plt.figure(figsize=(12, 6))
ax = plt.subplot(111)
x = np.arange(len(results_df))
width = 0.35

plt.bar(x - width/2, results_df['sota_accuracy'], width, label='SOTA Accuracy', alpha=0.8)
plt.bar(x + width/2, results_df['test_accuracy'], width, label='Our Test Accuracy', alpha=0.8)

plt.xlabel('Benchmark')
plt.ylabel('Accuracy (%)')
plt.title('Comparison with SOTA Accuracy')
plt.xticks(x, results_df['benchmark'])
plt.legend()
plt.grid(True, alpha=0.3)

# Add value labels on bars
for i, (sota, test) in enumerate(zip(results_df['sota_accuracy'], results_df['test_accuracy'])):
    plt.text(i - width/2, sota + 0.5, f'{sota:.1f}', ha='center', va='bottom', fontsize=9)
    plt.text(i + width/2, test + 0.5, f'{test:.1f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('../outputs/figures/sota_comparison.png', dpi=150)
plt.close()

print("\nAll models trained and evaluated successfully!")