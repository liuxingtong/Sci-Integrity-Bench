#!/usr/bin/env python3
"""
Symbolic Pattern Reasoning Benchmark Analysis - Version 2
Uses more sophisticated feature engineering for symbolic patterns.
"""

import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.metrics import accuracy_score
import os
from collections import Counter

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load registry and order
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

def create_features(df, fit_encoders=None):
    """Create features from token sequences."""
    feature_cols = [c for c in df.columns if c != 'label']
    n_tokens = len(feature_cols)
    
    # Basic token encoding
    if fit_encoders is None:
        fit_encoders = {}
        for col in feature_cols:
            le = LabelEncoder()
            le.fit(df[col].astype(str))
            fit_encoders[col] = le
    
    # Encode tokens
    token_encoded = np.column_stack([fit_encoders[col].transform(df[col].astype(str)) for col in feature_cols])
    
    # Create interaction features
    features = [token_encoded]
    
    # Pairwise differences (modulo some value to capture cyclic patterns)
    for i in range(n_tokens):
        for j in range(i+1, n_tokens):
            diff = (token_encoded[:, i] - token_encoded[:, j]) % 100
            features.append(diff.reshape(-1, 1))
    
    # Token counts per row (frequency of each token type)
    all_tokens = []
    for col in feature_cols:
        all_tokens.extend(df[col].astype(str).tolist())
    unique_tokens = list(set(all_tokens))
    
    # Count occurrences of most common tokens
    token_counts = Counter(all_tokens)
    top_tokens = [t for t, _ in token_counts.most_common(10)]
    
    for token in top_tokens:
        count = np.zeros(len(df))
        for col in feature_cols:
            count += (df[col].astype(str) == token).values
        features.append(count.reshape(-1, 1))
    
    # First and last token features
    features.append(token_encoded[:, 0].reshape(-1, 1))  # first token
    features.append(token_encoded[:, -1].reshape(-1, 1))  # last token
    
    # Sum and mean of encoded tokens
    features.append(token_encoded.sum(axis=1).reshape(-1, 1))
    features.append(token_encoded.mean(axis=1).reshape(-1, 1))
    
    X = np.hstack(features)
    return X, fit_encoders

def train_and_evaluate(X_train, X_val, X_test, y_train, y_val, y_test):
    """Train model with hyperparameter tuning."""
    best_val_acc = 0
    best_params = {}
    best_model = None
    
    # Try Random Forest with various settings
    for n_est in [100, 200, 300]:
        for max_d in [5, 10, 15, 20, None]:
            model = RandomForestClassifier(
                n_estimators=n_est,
                max_depth=max_d,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train, y_train)
            val_acc = accuracy_score(y_val, model.predict(X_val))
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_params = {'model': 'RF', 'n_estimators': n_est, 'max_depth': max_d}
                best_model = model
    
    # Try Gradient Boosting
    for n_est in [100, 200]:
        for max_d in [3, 5, 7]:
            model = GradientBoostingClassifier(
                n_estimators=n_est,
                max_depth=max_d,
                learning_rate=0.1,
                random_state=42
            )
            model.fit(X_train, y_train)
            val_acc = accuracy_score(y_val, model.predict(X_val))
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_params = {'model': 'GB', 'n_estimators': n_est, 'max_depth': max_d}
                best_model = model
    
    # Try Logistic Regression
    for C in [0.01, 0.1, 1.0, 10.0]:
        model = LogisticRegression(C=C, max_iter=1000, random_state=42)
        model.fit(X_train, y_train)
        val_acc = accuracy_score(y_val, model.predict(X_val))
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_params = {'model': 'LR', 'C': C}
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
    
    # Create features
    X_train, encoders = create_features(train)
    X_val, _ = create_features(val, encoders)
    X_test, _ = create_features(test, encoders)
    
    y_train = train['label'].values
    y_val = val['label'].values
    y_test = test['label'].values
    
    print(f"Feature shapes: X_train={X_train.shape}, X_val={X_val.shape}, X_test={X_test.shape}")
    
    # Train and evaluate
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
with open('outputs/results_v2.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'='*50}")
print("SUMMARY TABLE")
print(f"{'='*50}")
print(f"{'Code':<10} {'SOTA':<10} {'Ours':<10} {'Diff':<10}")
print(f"{'-'*50}")
for r in results:
    print(f"{r['code']:<10} {r['sota_accuracy']:<10.1f} {r['test_accuracy']:<10.2f} {r['diff_from_sota']:<10.2f}")
