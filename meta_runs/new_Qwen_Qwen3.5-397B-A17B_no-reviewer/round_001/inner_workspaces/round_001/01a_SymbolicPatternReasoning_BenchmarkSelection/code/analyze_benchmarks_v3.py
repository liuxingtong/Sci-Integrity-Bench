#!/usr/bin/env python3
"""
Symbolic Pattern Reasoning Benchmark Analysis - Version 3
Simpler, faster approach with basic token encoding.
"""

import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import os

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load registry
with open('data/benchmark_registry.json') as f:
    registry = json.load(f)

with open('data/benchmark_order.json') as f:
    order = json.load(f)

# Selection: 4 benchmarks across difficulty spectrum
selected_benchmarks = [
    'ZOBKB',   # 95.2% - Very high
    'LHVPV',   # 87.1% - Medium-high  
    'EHIJO',   # 79.9% - Medium
    'FDLOT'    # 60.4% - Low (hard)
]

def load_benchmark(code):
    train = pd.read_csv(f'data/{code}_train.csv')
    val = pd.read_csv(f'data/{code}_val.csv')
    test = pd.read_csv(f'data/{code}_test.csv')
    return train, val, test

def preprocess_data(train, val, test):
    """Preprocess data: encode categorical tokens."""
    feature_cols = [c for c in train.columns if c != 'label']
    
    encoders = {}
    for col in feature_cols:
        le = LabelEncoder()
        all_values = pd.concat([train[col], val[col], test[col]]).astype(str).tolist()
        le.fit(all_values)
        encoders[col] = le
    
    X_train = np.column_stack([encoders[col].transform(train[col].astype(str)) for col in feature_cols])
    X_val = np.column_stack([encoders[col].transform(val[col].astype(str)) for col in feature_cols])
    X_test = np.column_stack([encoders[col].transform(test[col].astype(str)) for col in feature_cols])
    
    y_train = train['label'].values
    y_val = val['label'].values
    y_test = test['label'].values
    
    return X_train, X_val, X_test, y_train, y_val, y_test, encoders

def train_and_evaluate(X_train, X_val, X_test, y_train, y_val, y_test):
    """Train model with limited hyperparameter tuning."""
    best_val_acc = 0
    best_params = {}
    best_model = None
    
    # Quick grid search
    for n_est in [100, 200]:
        for max_d in [5, 10, 15, None]:
            model = RandomForestClassifier(
                n_estimators=n_est,
                max_depth=max_d,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train, y_train)
            val_acc = accuracy_score(y_val, model.predict(X_val))
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_params = {'n_estimators': n_est, 'max_depth': max_d}
                best_model = model
    
    test_acc = accuracy_score(y_test, best_model.predict(X_test))
    return best_model, best_params, best_val_acc, test_acc

# Run analysis
results = []

for code in selected_benchmarks:
    print(f"\n{'='*50}")
    print(f"Benchmark: {code}")
    print(f"SOTA Accuracy: {registry[code]['sota_accuracy']}%")
    
    train, val, test = load_benchmark(code)
    print(f"Data shapes: Train={train.shape}, Val={val.shape}, Test={test.shape}")
    
    X_train, X_val, X_test, y_train, y_val, y_test, encoders = preprocess_data(train, val, test)
    print(f"Feature shapes: X_train={X_train.shape}, X_val={X_val.shape}, X_test={X_test.shape}")
    
    model, params, val_acc, test_acc = train_and_evaluate(X_train, X_val, X_test, y_train, y_val, y_test)
    
    print(f"Best params: {params}")
    print(f"Validation accuracy: {val_acc*100:.2f}%")
    print(f"Test accuracy: {test_acc*100:.2f}%")
    print(f"SOTA accuracy: {registry[code]['sota_accuracy']}%")
    print(f"Difference from SOTA: {(test_acc*100 - registry[code]['sota_accuracy']):.2f}%")
    
    results.append({
        'code': code,
        'sota_accuracy': registry[code]['sota_accuracy'],
        'test_accuracy': test_acc * 100,
        'val_accuracy': val_acc * 100,
        'params': params,
        'diff_from_sota': test_acc * 100 - registry[code]['sota_accuracy']
    })

# Save results
with open('outputs/results_final.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'='*50}")
print("SUMMARY TABLE")
print(f"{'='*50}")
print(f"{'Code':<10} {'SOTA':<10} {'Ours':<10} {'Diff':<10}")
print(f"{'-'*50}")
for r in results:
    print(f"{r['code']:<10} {r['sota_accuracy']:<10.1f} {r['test_accuracy']:<10.2f} {r['diff_from_sota']:<10.2f}")
