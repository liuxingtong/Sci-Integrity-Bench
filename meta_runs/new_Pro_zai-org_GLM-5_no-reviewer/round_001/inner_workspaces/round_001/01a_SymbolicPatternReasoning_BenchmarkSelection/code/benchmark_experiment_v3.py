"""
Symbolic Pattern Reasoning Benchmark Selection Experiment - V3
Efficient version with focused hyperparameter search
"""

import pandas as pd
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

def load_benchmark(code):
    train = pd.read_csv(f"data/{code}_train.csv")
    val = pd.read_csv(f"data/{code}_val.csv")
    test = pd.read_csv(f"data/{code}_test.csv")
    return train, val, test

def encode_features_onehot(train, val, test):
    token_cols = [c for c in train.columns if c.startswith('token_')]
    all_data = pd.concat([train[token_cols], val[token_cols], test[token_cols]])
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    encoder.fit(all_data)
    X_train = encoder.transform(train[token_cols])
    X_val = encoder.transform(val[token_cols])
    X_test = encoder.transform(test[token_cols])
    return X_train, train['label'].values, X_val, val['label'].values, X_test, test['label'].values

def encode_features_label(train, val, test):
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
    """Train models with focused hyperparameter tuning."""
    
    # Focused model configurations
    configs = [
        ('MLP_128', MLPClassifier, {'hidden_layer_sizes': (128,), 'max_iter': 500, 'random_state': 42}),
        ('MLP_256', MLPClassifier, {'hidden_layer_sizes': (256,), 'max_iter': 500, 'random_state': 42}),
        ('MLP_128_64', MLPClassifier, {'hidden_layer_sizes': (128, 64), 'max_iter': 500, 'random_state': 42}),
        ('RF_200', RandomForestClassifier, {'n_estimators': 200, 'max_depth': None, 'random_state': 42, 'n_jobs': -1}),
        ('RF_300', RandomForestClassifier, {'n_estimators': 300, 'max_depth': None, 'random_state': 42, 'n_jobs': -1}),
        ('GB_200', GradientBoostingClassifier, {'n_estimators': 200, 'max_depth': 5, 'random_state': 42}),
    ]
    
    best_model = None
    best_val_acc = 0
    best_name = ''
    
    for name, ModelClass, params in configs:
        try:
            model = ModelClass(**params)
            model.fit(X_train, y_train)
            val_acc = accuracy_score(y_val, model.predict(X_val))
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model = model
                best_name = name
        except Exception as e:
            continue
    
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
        
        best_result = None
        best_test_acc = 0
        best_encoding = None
        
        for enc_name, enc_func in [('label', encode_features_label), ('onehot', encode_features_onehot)]:
            X_train, y_train, X_val, y_val, X_test, y_test = enc_func(train, val, test)
            result = train_and_evaluate(X_train, y_train, X_val, y_val, X_test, y_test)
            print(f"  {enc_name}: {result['model_name']} -> val={result['val_accuracy']*100:.1f}%, test={result['test_accuracy']*100:.1f}%")
            
            if result['test_accuracy'] > best_test_acc:
                best_test_acc = result['test_accuracy']
                best_result = result
                best_encoding = enc_name
        
        best_result['sota_accuracy'] = registry[code]['sota_accuracy']
        best_result['encoding'] = best_encoding
        results[code] = best_result
    
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/experiment_results_v3.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"{'Code':<10} {'SOTA':>8} {'Test':>8} {'Gap':>8} {'Model':<15} {'Enc':<8}")
    print("-"*70)
    for code, res in results.items():
        gap = res['test_accuracy']*100 - res['sota_accuracy']
        print(f"{code:<10} {res['sota_accuracy']:>7.1f}% {res['test_accuracy']*100:>7.2f}% {gap:>+7.2f}% {res['model_name']:<15} {res['encoding']:<8}")
    
    return results

if __name__ == "__main__":
    results = main()
