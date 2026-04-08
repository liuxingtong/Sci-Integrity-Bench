"""
SPR Benchmark: Symbolic Pattern Reasoning Classification
Binary classification of symbolic sequences with hidden rule.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load data
print("Loading data...")
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

print(f"Train shape: {train.shape}")
print(f"Val shape: {val.shape}")
print(f"Test shape: {test.shape}")

# Extract feature columns
feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"Number of features: {len(feature_cols)}")

# Check label distribution
print("\nLabel distribution:")
print(f"Train: {train['label'].value_counts().to_dict()}")
print(f"Val: {val['label'].value_counts().to_dict()}")
print(f"Test: {test['label'].value_counts().to_dict()}")

# Feature engineering: encode tokens as categorical features
# Each token is a 2-char string (shape + color)
# We'll use one-hot encoding for all unique tokens

# Collect all unique tokens
all_tokens = set()
for df in [train, val, test]:
    for col in feature_cols:
        all_tokens.update(df[col].unique())

print(f"\nUnique tokens: {sorted(all_tokens)}")
print(f"Total unique tokens: {len(all_tokens)}")

# Create token to index mapping
token_to_idx = {token: i for i, token in enumerate(sorted(all_tokens))}

def encode_features(df, feature_cols, token_to_idx):
    """Encode features using token indices."""
    n_samples = len(df)
    n_features = len(feature_cols)
    n_tokens = len(token_to_idx)
    
    # Create one-hot encoded features
    X = np.zeros((n_samples, n_features * n_tokens))
    
    for i, col in enumerate(feature_cols):
        for j, token in enumerate(df[col]):
            token_idx = token_to_idx[token]
            X[j, i * n_tokens + token_idx] = 1
    
    return X

# Alternative: use ordinal encoding (faster, less sparse)
def encode_features_ordinal(df, feature_cols, token_to_idx):
    """Encode features using ordinal encoding."""
    X = np.zeros((len(df), len(feature_cols)))
    for i, col in enumerate(feature_cols):
        X[:, i] = df[col].map(token_to_idx).values
    return X

print("\nEncoding features...")
X_train = encode_features_ordinal(train, feature_cols, token_to_idx)
X_val = encode_features_ordinal(val, feature_cols, token_to_idx)
X_test = encode_features_ordinal(test, feature_cols, token_to_idx)

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Feature matrix shapes: Train {X_train.shape}, Val {X_val.shape}, Test {X_test.shape}")

# Scale features for models that need it
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Define models to benchmark
models = {
    'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', random_state=42),
}

# Store results
results = []

print("\n" + "="*60)
print("Training and evaluating models...")
print("="*60)

for name, model in models.items():
    print(f"\n--- {name} ---")
    
    # Use scaled data for LR and SVM
    if name in ['Logistic Regression', 'SVM (RBF)']:
        model.fit(X_train_scaled, y_train)
        train_pred = model.predict(X_train_scaled)
        val_pred = model.predict(X_val_scaled)
        test_pred = model.predict(X_test_scaled)
    else:
        model.fit(X_train, y_train)
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        test_pred = model.predict(X_test)
    
    # Calculate accuracies
    train_acc = accuracy_score(y_train, train_pred)
    val_acc = accuracy_score(y_val, val_pred)
    test_acc = accuracy_score(y_test, test_pred)
    
    print(f"Train Accuracy: {train_acc:.4f}")
    print(f"Val Accuracy:   {val_acc:.4f}")
    print(f"Test Accuracy:  {test_acc:.4f}")
    
    results.append({
        'Model': name,
        'Train Acc': train_acc,
        'Val Acc': val_acc,
        'Test Acc': test_acc
    })

# Create results DataFrame
results_df = pd.DataFrame(results)
print("\n" + "="*60)
print("SUMMARY RESULTS")
print("="*60)
print(results_df.to_string(index=False))

# Save results
results_df.to_csv('../outputs/model_results.csv', index=False)
print("\nResults saved to outputs/model_results.csv")

# SOTA baseline
SOTA_BASELINE = 0.70

# Create visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Bar chart comparing accuracies
x = np.arange(len(results_df))
width = 0.25

ax1 = axes[0]
bars1 = ax1.bar(x - width, results_df['Train Acc'], width, label='Train', color='steelblue', alpha=0.8)
bars2 = ax1.bar(x, results_df['Val Acc'], width, label='Validation', color='forestgreen', alpha=0.8)
bars3 = ax1.bar(x + width, results_df['Test Acc'], width, label='Test', color='coral', alpha=0.8)

# Add SOTA baseline line
ax1.axhline(y=SOTA_BASELINE, color='red', linestyle='--', linewidth=2, label=f'SOTA ({SOTA_BASELINE*100:.0f}%)')

ax1.set_xlabel('Model', fontsize=12)
ax1.set_ylabel('Accuracy', fontsize=12)
ax1.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(results_df['Model'], rotation=15, ha='right')
ax1.legend(loc='lower right')
ax1.set_ylim([0, 1.0])
ax1.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

# Plot 2: Test accuracy comparison with SOTA
ax2 = axes[1]
colors = ['green' if acc >= SOTA_BASELINE else 'orange' for acc in results_df['Test Acc']]
bars = ax2.barh(results_df['Model'], results_df['Test Acc'], color=colors, alpha=0.8)
ax2.axvline(x=SOTA_BASELINE, color='red', linestyle='--', linewidth=2, label=f'SOTA ({SOTA_BASELINE*100:.0f}%)')
ax2.set_xlabel('Test Accuracy', fontsize=12)
ax2.set_title('Test Accuracy vs SOTA Baseline', fontsize=14, fontweight='bold')
ax2.set_xlim([0, 1.0])
ax2.legend()
ax2.grid(axis='x', alpha=0.3)

# Add value labels
for i, (bar, acc) in enumerate(zip(bars, results_df['Test Acc'])):
    ax2.text(acc + 0.01, bar.get_y() + bar.get_height()/2, 
             f'{acc:.3f}', va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/model_comparison.png', dpi=150, bbox_inches='tight')
print("Figure saved to report/images/model_comparison.png")
plt.close()

# Create confusion matrix for best model
best_model_idx = results_df['Test Acc'].idxmax()
best_model_name = results_df.loc[best_model_idx, 'Model']
print(f"\nBest model: {best_model_name}")

# Retrain best model and get predictions
if best_model_name in ['Logistic Regression', 'SVM (RBF)']:
    best_model = models[best_model_name]
    best_model.fit(X_train_scaled, y_train)
    test_pred = best_model.predict(X_test_scaled)
else:
    best_model = models[best_model_name]
    best_model.fit(X_train, y_train)
    test_pred = best_model.predict(X_test)

# Confusion matrix
cm = confusion_matrix(y_test, test_pred)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Reject (0)', 'Accept (1)'],
            yticklabels=['Reject (0)', 'Accept (1)'],
            ax=ax)
ax.set_xlabel('Predicted Label', fontsize=12)
ax.set_ylabel('True Label', fontsize=12)
ax.set_title(f'Confusion Matrix - {best_model_name}', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('../report/images/confusion_matrix.png', dpi=150, bbox_inches='tight')
print("Figure saved to report/images/confusion_matrix.png")
plt.close()

# Feature importance for tree-based models
if hasattr(best_model, 'feature_importances_'):
    fig, ax = plt.subplots(figsize=(10, 6))
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[-20:]  # Top 20 features
    
    ax.barh(range(len(indices)), importances[indices], color='steelblue', alpha=0.8)
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([f'Token Position {i}' for i in indices])
    ax.set_xlabel('Feature Importance', fontsize=12)
    ax.set_title(f'Top 20 Feature Importances - {best_model_name}', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('../report/images/feature_importance.png', dpi=150, bbox_inches='tight')
    print("Figure saved to report/images/feature_importance.png")
    plt.close()

# Save detailed classification report
report = classification_report(y_test, test_pred, target_names=['Reject (0)', 'Accept (1)'])
with open('../outputs/classification_report.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test Accuracy: {results_df.loc[best_model_idx, 'Test Acc']:.4f}\n")
    f.write("\n" + "="*60 + "\n")
    f.write(report)

print("\nClassification report saved to outputs/classification_report.txt")

# Print final summary
print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)
print(f"SOTA Baseline: {SOTA_BASELINE*100:.1f}%")
print(f"Best Model: {best_model_name}")
print(f"Best Test Accuracy: {results_df['Test Acc'].max()*100:.2f}%")
print(f"Improvement over SOTA: {(results_df['Test Acc'].max() - SOTA_BASELINE)*100:.2f} percentage points")
