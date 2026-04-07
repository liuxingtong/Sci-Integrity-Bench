"""
Symbolic Pattern Reasoning Benchmark Selection Experiment

This script:
1. Selects 4 benchmarks with diverse SOTA accuracies
2. Trains models on each benchmark independently
3. Tunes hyperparameters on validation set
4. Reports test accuracy vs SOTA
"""

import pandas as pd
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
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

def encode_features(train, val, test):
    """Encode categorical tokens as integers."""
    # Get token columns
    token_cols = [c for c in train.columns if c.startswith('token_')]
    
    # Fit label encoders on training data
    encoders = {}
    for col in token_cols:
        le = LabelEncoder()
        # Fit on all unique values across all splits
        all_values = pd.concat([train[col], val[col], test[col]]).astype(str).unique()
        le.fit(all_values)
        encoders[col] = le
    
    # Transform data
    def transform(df):
        encoded = pd.DataFrame()
        for col in token_cols:
            encoded[col] = encoders[col].transform(df[col].astype(str))
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
    results = {}
    
    # Model configurations to try
    models = {
        'RandomForest': [
            {'n_estimators': 50, 'max_depth': 5, 'random_state': 42},
            {'n_estimators': 100, 'max_depth': 10, 'random_state': 42},
            {'n_estimators': 200, 'max_depth': 15, 'random_state': 42},
            {'n_estimators': 100, 'max_depth': None, 'random_state': 42},
        ],
        'GradientBoosting': [
            {'n_estimators': 50, 'max_depth': 3, 'learning_rate': 0.1, 'random_state': 42},
            {'n_estimators': 100, 'max_depth': 5, 'learning_rate': 0.1, 'random_state': 42},
            {'n_estimators': 200, 'max_depth': 5, 'learning_rate': 0.05, 'random_state': 42},
        ],
        'LogisticRegression': [
            {'max_iter': 1000, 'C': 0.1, 'random_state': 42},
            {'max_iter': 1000, 'C': 1.0, 'random_state': 42},
            {'max_iter': 1000, 'C': 10.0, 'random_state': 42},
        ]
    }
    
    best_model = None
    best_val_acc = 0
    best_model_name = ''
    best_params = {}
    
    for model_name, param_list in models.items():
        for params in param_list:
            if model_name == 'RandomForest':
                model = RandomForestClassifier(**params)
            elif model_name == 'GradientBoosting':
                model = GradientBoostingClassifier(**params)
            elif model_name == 'LogisticRegression':
                model = LogisticRegression(**params)
            
            # Train on training set
            model.fit(X_train, y_train)
            
            # Evaluate on validation set
            val_pred = model.predict(X_val)
            val_acc = accuracy_score(y_val, val_pred)
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model = model
                best_model_name = model_name
                best_params = params
    
    # Evaluate best model on test set
    test_pred = best_model.predict(X_test)
    test_acc = accuracy_score(y_test, test_pred)
    
    return {
        'model_name': best_model_name,
        'params': best_params,
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
    # Sort by SOTA accuracy
    sorted_benchmarks = sorted(registry.items(), key=lambda x: x[1]['sota_accuracy'])
    
    # Select: 1 low, 1 medium-low, 1 medium-high, 1 high
    n = len(sorted_benchmarks)
    selected_codes = [
        sorted_benchmarks[1][0],   # Low (2nd lowest) - FDLOT or similar
        sorted_benchmarks[n//3][0],  # Medium-low
        sorted_benchmarks[2*n//3][0],  # Medium-high
        sorted_benchmarks[-1][0],  # Highest
    ]
    
    print("Selected benchmarks:")
    for code in selected_codes:
        print(f"  {code}: SOTA = {registry[code]['sota_accuracy']}%")
    
    # Run experiments
    results = {}
    for code in selected_codes:
        print(f"\nProcessing {code}...")
        
        # Load data
        train, val, test = load_benchmark(code)
        
        # Encode features
        X_train, y_train, X_val, y_val, X_test, y_test = encode_features(train, val, test)
        
        # Train and evaluate
        result = train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test)
        result['sota_accuracy'] = registry[code]['sota_accuracy']
        result['train_size'] = len(train)
        result['val_size'] = len(val)
        result['test_size'] = len(test)
        result['n_tokens'] = X_train.shape[1]
        
        results[code] = result
        
        print(f"  Model: {result['model_name']}")
        print(f"  Val Accuracy: {result['val_accuracy']*100:.2f}%")
        print(f"  Test Accuracy: {result['test_accuracy']*100:.2f}%")
        print(f"  SOTA: {result['sota_accuracy']}%")
        print(f"  Gap: {(result['test_accuracy']*100 - result['sota_accuracy']):.2f}%")
    
    # Save results
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/experiment_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"{'Code':<10} {'SOTA':>8} {'Test':>8} {'Gap':>8} {'Model':<20}")
    print("-"*60)
    for code, res in results.items():
        gap = res['test_accuracy']*100 - res['sota_accuracy']
        print(f"{code:<10} {res['sota_accuracy']:>7.1f}% {res['test_accuracy']*100:>7.2f}% {gap:>+7.2f}% {res['model_name']:<20}")
    
    return results

if __name__ == "__main__":
    results = main()
