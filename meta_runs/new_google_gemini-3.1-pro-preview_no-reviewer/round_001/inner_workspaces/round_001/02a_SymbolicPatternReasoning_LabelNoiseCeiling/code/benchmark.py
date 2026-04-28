import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
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

# One-hot encoding
encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
X_train = encoder.fit_transform(train[feature_cols])
X_val = encoder.transform(val[feature_cols])
X_test = encoder.transform(test[feature_cols])

y_train = train['label']
y_val = val['label']
y_test = test['label']

# Define models
models = {
    'Logistic Regression (L1)': LogisticRegression(C=0.1, penalty='l1', solver='liblinear', random_state=42),
    'Logistic Regression (L2)': LogisticRegression(C=0.1, penalty='l2', random_state=42),
    'SVM (RBF)': SVC(C=1.0, kernel='rbf', random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=6, min_samples_leaf=5, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42),
    'MLP (Neural Net)': MLPClassifier(hidden_layer_sizes=(64,), alpha=1.0, max_iter=1000, random_state=42)
}

results = []

print("Benchmarking models...")
for name, model in models.items():
    print(f"Training {name}...")
    model.fit(X_train, y_train)
    
    train_acc = accuracy_score(y_train, model.predict(X_train))
    val_acc = accuracy_score(y_val, model.predict(X_val))
    test_acc = accuracy_score(y_test, model.predict(X_test))
    
    results.append({
        'Model': name,
        'Train Accuracy': train_acc,
        'Validation Accuracy': val_acc,
        'Test Accuracy': test_acc
    })

results_df = pd.DataFrame(results)
results_df.to_csv('outputs/benchmark_results.csv', index=False)
print("\nBenchmark Results:")
print(results_df.to_string(index=False))

# Plot results
plt.figure(figsize=(12, 6))
x = np.arange(len(models))
width = 0.25

plt.bar(x - width, results_df['Train Accuracy'], width, label='Train')
plt.bar(x, results_df['Validation Accuracy'], width, label='Validation')
plt.bar(x + width, results_df['Test Accuracy'], width, label='Test')

plt.axhline(y=0.70, color='r', linestyle='--', label='SOTA Baseline (70%)')
plt.axhline(y=0.50, color='gray', linestyle=':', label='Random Guessing (50%)')

plt.ylabel('Accuracy')
plt.title('Model Performance on SPR_BENCH vs SOTA')
plt.xticks(x, results_df['Model'], rotation=45, ha='right')
plt.legend(loc='upper right')
plt.ylim(0, 1.05)
plt.tight_layout()
plt.savefig('report/images/benchmark_accuracy.png', dpi=300)
plt.close()

# Also plot the train-val gap to show overfitting
plt.figure(figsize=(10, 6))
plt.plot(results_df['Model'], results_df['Train Accuracy'] - results_df['Validation Accuracy'], marker='o', linestyle='-', color='purple')
plt.ylabel('Generalization Gap (Train Acc - Val Acc)')
plt.title('Overfitting: Generalization Gap by Model')
plt.xticks(rotation=45, ha='right')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('report/images/generalization_gap.png', dpi=300)
plt.close()
