import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import PredefinedSplit, GridSearchCV
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Selected benchmarks
selected_codes = ['ZOBKB', 'FDLOT', 'ILULR', 'XPOFG']

with open('data/benchmark_registry.json') as f:
    registry = json.load(f)

results = []

for code in selected_codes:
    print(f"Processing {code}...")
    train_df = pd.read_csv(f'data/{code}_train.csv')
    val_df = pd.read_csv(f'data/{code}_val.csv')
    test_df = pd.read_csv(f'data/{code}_test.csv')
    
    X_train_raw = train_df.drop('label', axis=1)
    y_train = train_df['label']
    
    X_val_raw = val_df.drop('label', axis=1)
    y_val = val_df['label']
    
    X_test_raw = test_df.drop('label', axis=1)
    y_test = test_df['label']
    
    # One-hot encode
    encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    X_train = encoder.fit_transform(X_train_raw)
    X_val = encoder.transform(X_val_raw)
    X_test = encoder.transform(X_test_raw)
    
    # Combine train and val for GridSearchCV
    X_cv = np.vstack((X_train, X_val))
    y_cv = np.concatenate((y_train, y_val))
    
    # Create PredefinedSplit
    # -1 for train, 0 for val
    test_fold = np.concatenate([-1 * np.ones(len(y_train)), np.zeros(len(y_val))])
    ps = PredefinedSplit(test_fold)
    
    # Model: MLPClassifier
    mlp = MLPClassifier(max_iter=1000, random_state=42)
    param_grid = {
        'hidden_layer_sizes': [(64,), (128,), (64, 64), (128, 64)],
        'alpha': [0.0001, 0.001, 0.01],
        'learning_rate_init': [0.001, 0.01]
    }
    
    grid = GridSearchCV(mlp, param_grid, cv=ps, scoring='accuracy', n_jobs=-1)
    grid.fit(X_cv, y_cv)
    
    best_model = grid.best_estimator_
    
    # Evaluate on test
    y_pred = best_model.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred) * 100
    sota_acc = registry[code]['sota_accuracy']
    
    results.append({
        'Benchmark': code,
        'Test Accuracy (%)': test_acc,
        'SOTA Accuracy (%)': sota_acc,
        'Difference': test_acc - sota_acc
    })
    print(f"{code} - Test Acc: {test_acc:.1f}%, SOTA: {sota_acc:.1f}%")

results_df = pd.DataFrame(results)
print("\nFinal Results:")
print(results_df)
results_df.to_csv('outputs/results.csv', index=False)

# Plotting
plt.figure(figsize=(10, 6))
x = np.arange(len(selected_codes))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 6))
rects1 = ax.bar(x - width/2, results_df['Test Accuracy (%)'], width, label='Our Model (MLP)')
rects2 = ax.bar(x + width/2, results_df['SOTA Accuracy (%)'], width, label='SOTA')

ax.set_ylabel('Accuracy (%)')
ax.set_title('Test Accuracy vs SOTA by Benchmark')
ax.set_xticks(x)
ax.set_xticklabels(selected_codes)
ax.legend()

ax.bar_label(rects1, fmt='%.1f', padding=3)
ax.bar_label(rects2, fmt='%.1f', padding=3)

fig.tight_layout()
plt.savefig('report/images/accuracy_comparison.png')
