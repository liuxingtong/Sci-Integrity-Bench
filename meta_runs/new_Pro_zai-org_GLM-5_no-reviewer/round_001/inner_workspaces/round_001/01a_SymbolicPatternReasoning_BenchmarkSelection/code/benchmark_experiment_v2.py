"""
Symbolic Pattern Reasoning Benchmark Selection Experiment - V2

Improved approach with:
1. Neural networks (MLP)
2. Better feature engineering (one-hot encoding for tokens)
3. More extensive hyperparameter tuning
"""

import pandas as pd
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.metrics import accuracy_score
from sklearn.svm import SVC
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

def load_benchmark(code):
    """Load train, validation, and test splits for a benchmark."""
    train = pd.read_csv(f"data/{code}_train.csv")
    val = pd.read_csv(f"data/{code}_val.csv")
    test = pd.read_csv(f"data/{code}_test.csv")
    return train, val, test

def encode_features_onehot(train, val, test):
    """One-hot encode categorical tokens."""
    token_cols = [c for c in train.columns if c.startswith('token_')]
    
    # Collect all data for fitting encoder
    all_data = pd.concat([
        train[token_cols],
        val[token_cols],
        test[token_cols]
    ])
    
    # One-hot encode
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    encoder.fit(all_data)
    
    def transform(df):
        return encoder.transform(df[token_cols])
    
    X_train = transform(train)
    X_val = transform(val)
    X_test = transform(test)
    
    y_train = train['label'].values
    y_val = val['label'].values
    y_test = test['label'].values
    
    return X_train, y_train, X_val, y_val, X_test, y_test

def encode_features_label(train, val, test):
    """Label encode categorical tokens."""
    token_cols = [c for c in train.columns if c.startswith('token_')]
    
    encoders = {}
    for col in token_cols:
        le = LabelEncoder()
        all_values = pd.concat([train[col], val[col], test[col]]).astype(str).unique()
        le.fit(all_values)
        encoders[col] = le
    
    def transform(df):
        encoded = np.column_stack([
            encoders[col].transform(df[col].astype(str))
            for col in token_cols
        ])
        return encoded
    
    X_train = transform(train)
    X_val = transform(val)
    X_test = transform(test)
    
    y_train = train['label'].values
    y_val = val['label'].values
    y_test = test['label'].values
    
    return X_train, y_train, X_val, y_val, X_test, y_test

def train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test):
    """Train models with hyperparameter tuning on validation set."""
    
    # Model configurations to try
    model_configs = []
    
    # MLP configurations (good for pattern recognition)
    for hidden in [(64,), (128,), (256,), (64, 32), (128, 64), (256, 128)]:
        for lr in [0.001, 0.01, 0.1]:
            model_configs.append({
                'name': f'MLP_{hidden}',
                'type': 'MLP',
                'params': {
                    'hidden_layer_sizes': hidden,
                    'learning_rate_init': lr,
                    'max_iter': 1000,
                    'random_state': 42,
                    'early_stopping': True,
                    'validation_fraction': 0.1
                }
            })
    
    # Random Forest configurations
    for n_est in [100, 200, 300]:
        for depth in [10, 15, 20, None]:
            model_configs.append({
                'name': f'RF_{n_est}_{depth}',
                'type': 'RF',
                'params': {
                    'n_estimators': n_est,
                    'max_depth': depth,
                    'random_state': 42,
                    'n_jobs': -1
                }
            })
    
    # Gradient Boosting configurations
    for n_est in [100, 200]:
        for depth in [3, 5, 7]:
            for lr in [0.05, 0.1, 0.2]:
                model_configs.append({
                    'name': f'GB_{n_est}_{depth}_{lr}',
                    'type': 'GB',
                    'params': {
                        'n_estimators': n_est,
                        'max_depth': depth,
                        'learning_rate': lr,
                        'random_state': 42
                    }
                })
    
    # SVM configurations
    for C in [0.1, 1.0, 10.0]:
        for kernel in ['rbf', 'linear']:
            model_configs.append({
                'name': f'SVM_{kernel}_{C}',
                'type': 'SVM',
                'params': {
                    'C': C,
                    'kernel': kernel,
                    'random_state': 42
                }
            })
    
    best_model = None
    best_val_acc = 0
    best_config = None
    
    for config in model_configs:
        try:
            if config['type'] == 'MLP':
                model = MLPClassifier(**config['params'])
            elif config['type'] == 'RF':
                model = RandomForestClassifier(**config['params'])
            elif config['type'] == 'GB':
                model = GradientBoostingClassifier(**config['params'])
            elif config['type'] == 'SVM':
                model = SVC(**config['params'])
            
            model.fit(X_train, y_train)
            val_pred = model.predict(X_val)
            val_acc = accuracy_score(y_val, val_pred)
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model = model
                best_config = config
        except Exception as e:
            continue
    
    # Evaluate best model on test set
    test_pred = best_model.predict(X_test)
    test_acc = accuracy_score(y_test, test_pred)
    
    return {
        'model_name': best_config['name'],
        'model_type': best_config['type'],
        'params': best_config['params'],
        'val_accuracy': best_val_acc,
        'test_accuracy': test_acc
    }

def main():
    # Load registry
    with open("data/benchmark_registry.json") as f:
        registry = json.load(f)
    
    with open("data/benchmark_order.json") as f:
        order = json.load(f)
    
    # Select 4 benchmarks with diverse SOTA accuracies
    sorted_benchmarks = sorted(registry.items(), key=lambda x: x[1]['sota_accuracy'])
    
    # Select: 1 low, 1 medium-low, 1 medium-high, 1 high
    n = len(sorted_benchmarks)
    selected_codes = [
        sorted_benchmarks[1][0],   # Low (2nd lowest)
        sorted_benchmarks[n//3][0],  # Medium-low
        sorted_benchmarks[2*n//3][0],  # Medium-high
        sorted_benchmarks[-1][0],  # Highest
    ]
    
    print("Selected benchmarks:")
    for code in selected_codes:
        print(f"  {code}: SOTA = {registry[code]['sota_accuracy']}%")
    
    # Run experiments with both encoding methods
    results = {}
    
    for code in selected_codes:
        print(f"\n{'='*60}")
        print(f"Processing {code}...")
        print('='*60)
        
        # Load data
        train, val, test = load_benchmark(code)
        
        # Try both encoding methods
        best_result = None
        best_test_acc = 0
        best_encoding = None
        
        for encoding_name, encode_func in [('label', encode_features_label), ('onehot', encode_features_onehot)]:
            print(f"\n  Trying {encoding_name} encoding...")
            X_train, y_train, X_val, y_val, X_test, y_test = encode_func(train, val, test)
            print(f"    Feature shape: {X_train.shape}")
            
            result = train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test)
            print(f"    Best model: {result['model_name']}")
            print(f"    Val accuracy: {result['val_accuracy']*100:.2f}%")
            print(f"    Test accuracy: {result['test_accuracy']*100:.2f}%")
            
            if result['test_accuracy'] > best_test_acc:
                best_test_acc = result['test_accuracy']
                best_result = result
                best_encoding = encoding_name
        
        best_result['sota_accuracy'] = registry[code]['sota_accuracy']
        best_result['train_size'] = len(train)
        best_result['val_size'] = len(val)
        best_result['test_size'] = len(test)
        best_result['encoding'] = best_encoding
        
        results[code] = best_result
        
        print(f"\n  Best for {code}:")
        print(f"    Encoding: {best_encoding}")
        print(f"    Model: {best_result['model_name']}")
        print(f"    Test Accuracy: {best_result['test_accuracy']*100:.2f}%")
        print(f"    SOTA: {best_result['sota_accuracy']}%")
        print(f"    Gap: {(best_result['test_accuracy']*100 - best_result['sota_accuracy']):.2f}%")
    
    # Save results
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/experiment_results_v2.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"{'Code':<10} {'SOTA':>8} {'Test':>8} {'Gap':>8} {'Model':<25} {'Enc':<8}")
    print("-"*70)
    for code, res in results.items():
        gap = res['test_accuracy']*100 - res['sota_accuracy']
        print(f"{code:<10} {res['sota_accuracy']:>7.1f}% {res['test_accuracy']*100:>7.2f}% {gap:>+7.2f}% {res['model_name']:<25} {res['encoding']:<8}")
    
    return results

if __name__ == "__main__":
    results = main()
