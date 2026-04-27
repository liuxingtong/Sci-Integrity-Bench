import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

X_train = train[feature_cols]
y_train = train['label']
X_val = val[feature_cols]
y_val = val['label']
X_test = test[feature_cols]
y_test = test['label']

# Preprocessing: One-hot encoding
encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train_encoded = encoder.fit_transform(X_train)
X_val_encoded = encoder.transform(X_val)
X_test_encoded = encoder.transform(X_test)

print(f'Encoded feature shape: {X_train_encoded.shape}')

# Models to try
models = {
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)
}

results = []

for name, model in models.items():
    print(f'Training {name}...')
    model.fit(X_train_encoded, y_train)
    
    train_acc = accuracy_score(y_train, model.predict(X_train_encoded))
    val_acc = accuracy_score(y_val, model.predict(X_val_encoded))
    test_acc = accuracy_score(y_test, model.predict(X_test_encoded))
    
    results.append({
        'Model': name,
        'Train Acc': train_acc,
        'Val Acc': val_acc,
        'Test Acc': test_acc
    })
    print(f'{name} - Train: {train_acc:.4f}, Val: {val_acc:.4f}, Test: {test_acc:.4f}')

results_df = pd.DataFrame(results)
results_df.to_csv('outputs/model_results.csv', index=False)
print(results_df)

# Plot results
plt.figure(figsize=(10, 6))
x = np.arange(len(models))
width = 0.25

plt.bar(x - width, results_df['Train Acc'], width, label='Train')
plt.bar(x, results_df['Val Acc'], width, label='Val')
plt.bar(x + width, results_df['Test Acc'], width, label='Test')

plt.axhline(y=0.70, color='r', linestyle='--', label='SOTA (70%)')

plt.ylabel('Accuracy')
plt.title('Model Accuracy Comparison')
plt.xticks(x, results_df['Model'])
plt.legend()
plt.ylim(0, 1.05)
plt.tight_layout()
plt.savefig('report/images/accuracy_comparison.png')
plt.close()
