"""
Symbolic Pattern Reasoning Benchmark Selection Experiment - V4
Fast version with minimal hyperparameter search
"""

import pandas as pd
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

def load_benchmark(code):
    train = pd.read_csv(f"data/{code}_train.csv")
    val = pd.read_csv(f"data/{code}_val.csv")
    test = pd.read_csv(f"data/{code}_test.csv")
    return train, val, test

def encode_features(train, val, test):
    token_cols = [c for c in train.columns if c.startswith('token_')]
    encoders = {}
    for col in token_cols:
        le = LabelEncoder()
        all_values = pd.concat([train[col], val[col], test[col]]).astype(str).unique()
        le.fit(all_values)
        encoders[col] = le
    
    def transform(df):
        return np.column_stack([encoders[col].transform(df[col].astype(str)) for col in token_cols])
    
    return transform(train), train['label'].values, transform(val), val['label'].values, transform(test), test['label'].values

def train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test):
    """Train models with minimal hyperparameter tuning."""
    
    configs = [
        ('RF', RandomForestClassifier, {'n_estimators': 100, 'random_state': 42, 'n_jobs': -1}),
        ('GB', GradientBoostingClassifier, {'n_estimators': 100, 'random_state': 42}),
        ('MLP', MLPClassifier, {'hidden_layer_sizes': (64,), 'max_iter': 300, 'random_state': 42}),
    ]
    
    best_model = None
    best_val_acc = 0
    best_name = ''
    
    for name, ModelClass, params in configs:
        model = ModelClass(**params)
        model.fit(X_train, y_train)
        val_acc = accuracy_score(y_val, model.predict(X_val))
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model = model
            best_name = name
    
    test_acc = accuracy_score(y_test, best_model.predict(X_test))
    return {'model_name': best_name, 'val_accuracy': best_val_acc, 'test_accuracy': test_acc}

def main():
    with open("data/benchmark_registry.json") as f:
        registry = json.load(f)
    
    # Select 4 benchmarks with diverse SOTA accuracies
    sorted_benchmarks = sorted(registry.items(), key=lambda x: x[1]['sota_accuracy'])
    n = len(sorted_benchmarks)
    selected_codes = [
        sorted_benchmarks[1][0],   # Low
        sorted_benchmarks[n//3][0],  # Medium-low
        sorted_benchmarks[2*n//3][0],  # Medium-high
        sorted_benchmarks[-1][0],  # Highest
    ]
    
    print("Selected benchmarks:")
    for code in selected_codes:
        print(f"  {code}: SOTA = {registry[code]['sota_accuracy']}%")
    
    results = {}
    
    for code in selected_codes:
        print(f"\nProcessing {code}...")
        train, val, test = load_benchmark(code)
        X_train, y_train, X_val, y_val, X_test, y_test = encode_features(train, val, test)
        
        result = train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test)
        result['sota_accuracy'] = registry[code]['sota_accuracy']
        results[code] = result
        
        print(f"  Model: {result['model_name']}")
        print(f"  Val: {result['val_accuracy']*100:.1f}%, Test: {result['test_accuracy']*100:.1f}%")
        print(f"  SOTA: {result['sota_accuracy']}%, Gap: {(result['test_accuracy']*100 - result['sota_accuracy']):.1f}%")
    
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/experiment_results_v4.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"{'Code':<10} {'SOTA':>8} {'Test':>8} {'Gap':>8} {'Model':<10}")
    print("-"*60)
    for code, res in results.items():
        gap = res['test_accuracy']*100 - res['sota_accuracy']
        print(f"{code:<10} {res['sota_accuracy']:>7.1f}% {res['test_accuracy']*100:>7.2f}% {gap:>+7.2f}% {res['model_name']:<10}")
    
    return results

if __name__ == "__main__":
    results = main()
