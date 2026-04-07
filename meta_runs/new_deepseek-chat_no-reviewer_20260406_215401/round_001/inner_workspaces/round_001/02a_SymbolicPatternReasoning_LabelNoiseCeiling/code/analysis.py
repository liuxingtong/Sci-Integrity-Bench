import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create outputs directory
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

print("Data shapes:")
print(f"Train: {train.shape}")
print(f"Val: {val.shape}")
print(f"Test: {test.shape}")

# Prepare features and labels
feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train = train[feature_cols]
y_train = train['label']
X_val = val[feature_cols]
y_val = val['label']
X_test = test[feature_cols]
y_test = test['label']

print(f"\nFeature columns: {feature_cols}")
print(f"Unique tokens in train: {len(pd.unique(X_train.values.ravel()))}")

# Encode tokens: each token is a categorical feature with 16 possible values
# We'll use one-hot encoding for each position
# First, let's create a mapping for all tokens
all_tokens = pd.concat([X_train, X_val, X_test]).values.ravel()
unique_tokens = pd.unique(all_tokens)
token_to_idx = {token: i for i, token in enumerate(unique_tokens)}
print(f"Total unique tokens across all splits: {len(unique_tokens)}")

# Function to encode data
def encode_data(df, token_to_idx):
    """Convert token sequences to one-hot encoded features."""
    n_samples = df.shape[0]
    n_positions = df.shape[1]
    n_tokens = len(token_to_idx)
    
    # Create empty array
    encoded = np.zeros((n_samples, n_positions * n_tokens))
    
    # Fill with one-hot encoding
    for i in range(n_positions):
        col = df.iloc[:, i]
        for j, token in enumerate(col):
            if token in token_to_idx:
                idx = token_to_idx[token]
                encoded[j, i * n_tokens + idx] = 1
    
    return encoded

# Encode all splits
X_train_encoded = encode_data(X_train, token_to_idx)
X_val_encoded = encode_data(X_val, token_to_idx)
X_test_encoded = encode_data(X_test, token_to_idx)

print(f"\nEncoded feature dimensions: {X_train_encoded.shape}")
print(f"(samples × features: {X_train_encoded.shape[0]} × {X_train_encoded.shape[1]})")

# Train and evaluate models
models = {
    'LogisticRegression': LogisticRegression(max_iter=1000, random_state=42),
    'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
    'SVM': SVC(kernel='rbf', random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42)
}

results = []

for name, model in models.items():
    print(f"\n--- Training {name} ---")
    
    # Train
    model.fit(X_train_encoded, y_train)
    
    # Predict
    y_train_pred = model.predict(X_train_encoded)
    y_val_pred = model.predict(X_val_encoded)
    y_test_pred = model.predict(X_test_encoded)
    
    # Calculate accuracies
    train_acc = accuracy_score(y_train, y_train_pred)
    val_acc = accuracy_score(y_val, y_val_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    print(f"Train accuracy: {train_acc:.4f}")
    print(f"Val accuracy: {val_acc:.4f}")
    print(f"Test accuracy: {test_acc:.4f}")
    
    results.append({
        'Model': name,
        'Train Accuracy': train_acc,
        'Validation Accuracy': val_acc,
        'Test Accuracy': test_acc
    })

# Convert results to DataFrame
results_df = pd.DataFrame(results)
print("\n" + "="*50)
print("SUMMARY OF RESULTS")
print("="*50)
print(results_df.to_string(index=False))

# Save results
results_df.to_csv('../outputs/model_results.csv', index=False)
print("\nResults saved to outputs/model_results.csv")

# Compare with SOTA (70%)
sota_acc = 0.70
print(f"\nSOTA Reference Accuracy: {sota_acc:.2%}")
print("Models achieving or exceeding SOTA:")
for _, row in results_df.iterrows():
    if row['Test Accuracy'] >= sota_acc:
        print(f"  - {row['Model']}: {row['Test Accuracy']:.2%}")
    else:
        print(f"  - {row['Model']}: {row['Test Accuracy']:.2%} (below SOTA)")

# Create visualization
plt.figure(figsize=(10, 6))
ax = sns.barplot(data=results_df.melt(id_vars=['Model'], 
                                       value_vars=['Train Accuracy', 'Validation Accuracy', 'Test Accuracy'],
                                       var_name='Split', value_name='Accuracy'),
                 x='Model', y='Accuracy', hue='Split')
plt.axhline(y=sota_acc, color='r', linestyle='--', label=f'SOTA ({sota_acc:.0%})')
plt.title('Model Performance on SPR_BENCH')
plt.ylabel('Accuracy')
plt.ylim(0, 1.0)
plt.legend(loc='lower right')
plt.tight_layout()
plt.savefig('../report/images/model_performance.png', dpi=300)
print("\nFigure saved to report/images/model_performance.png")

# Also create a simpler comparison chart
plt.figure(figsize=(8, 5))
ax = sns.barplot(data=results_df, x='Model', y='Test Accuracy')
plt.axhline(y=sota_acc, color='r', linestyle='--', label=f'SOTA ({sota_acc:.0%})')
plt.title('Test Accuracy vs SOTA (70%)')
plt.ylabel('Test Accuracy')
plt.ylim(0, 1.0)
for i, v in enumerate(results_df['Test Accuracy']):
    ax.text(i, v + 0.01, f'{v:.2%}', ha='center')
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/test_vs_sota.png', dpi=300)
print("Figure saved to report/images/test_vs_sota.png")