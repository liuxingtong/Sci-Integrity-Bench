"""
SPR Benchmark: Symbolic Pattern Reasoning Classification - Version 3
Using one-hot encoding and n-gram features to capture symbolic patterns.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load data
print("Loading data...")
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"Number of positions: {len(feature_cols)}")

# Collect all unique tokens
all_tokens = set()
for df in [train, val, test]:
    for col in feature_cols:
        all_tokens.update(df[col].unique())

all_tokens = sorted(all_tokens)
print(f"Unique tokens: {all_tokens}")
token_to_idx = {token: i for i, token in enumerate(all_tokens)}
n_tokens = len(all_tokens)

def one_hot_encode(df, feature_cols, token_to_idx, n_tokens):
    """One-hot encode all token positions."""
    n_samples = len(df)
    n_positions = len(feature_cols)
    X = np.zeros((n_samples, n_positions * n_tokens))
    
    for pos_idx, col in enumerate(feature_cols):
        for sample_idx, token in enumerate(df[col]):
            token_idx = token_to_idx[token]
            X[sample_idx, pos_idx * n_tokens + token_idx] = 1
    
    return X

def extract_ngram_features(df, feature_cols, n=2):
    """Extract n-gram features from sequences."""
    n_samples = len(df)
    
    # Create sequences
    sequences = []
    for i in range(n_samples):
        seq = tuple(df.iloc[i][col] for col in feature_cols)
        sequences.append(seq)
    
    # Extract n-grams
    ngram_counts = []
    for seq in sequences:
        ngrams = [seq[i:i+n] for i in range(len(seq) - n + 1)]
        ngram_counts.append(Counter(ngrams))
    
    # Get all unique n-grams
    all_ngrams = set()
    for counts in ngram_counts:
        all_ngrams.update(counts.keys())
    all_ngrams = sorted(all_ngrams)
    ngram_to_idx = {ng: i for i, ng in enumerate(all_ngrams)}
    
    # Create feature matrix
    X = np.zeros((n_samples, len(all_ngrams)))
    for i, counts in enumerate(ngram_counts):
        for ngram, count in counts.items():
            X[i, ngram_to_idx[ngram]] = count
    
    return X, all_ngrams

def extract_shape_color_features(df, feature_cols):
    """Extract separate shape and color features."""
    n_samples = len(df)
    n_positions = len(feature_cols)
    
    # Parse shapes and colors
    SHAPES = {'T': 0, 'S': 1, 'C': 2, 'D': 3}
    COLORS = {'r': 0, 'g': 1, 'b': 2, 'y': 3}
    
    shape_onehot = np.zeros((n_samples, n_positions * 4))
    color_onehot = np.zeros((n_samples, n_positions * 4))
    
    for pos_idx, col in enumerate(feature_cols):
        for sample_idx, token in enumerate(df[col]):
            shape = token[0]
            color = token[1]
            shape_onehot[sample_idx, pos_idx * 4 + SHAPES[shape]] = 1
            color_onehot[sample_idx, pos_idx * 4 + COLORS[color]] = 1
    
    return shape_onehot, color_onehot

print("\nExtracting features...")

# One-hot encoding
X_train_oh = one_hot_encode(train, feature_cols, token_to_idx, n_tokens)
X_val_oh = one_hot_encode(val, feature_cols, token_to_idx, n_tokens)
X_test_oh = one_hot_encode(test, feature_cols, token_to_idx, n_tokens)
print(f"One-hot features: {X_train_oh.shape}")

# Bigram features
X_train_bi, bigrams = extract_ngram_features(train, feature_cols, n=2)
X_val_bi, _ = extract_ngram_features(val, feature_cols, n=2)
X_test_bi, _ = extract_ngram_features(test, feature_cols, n=2)
print(f"Bigram features: {X_train_bi.shape}")

# Shape and color one-hot
X_train_sh, X_train_co = extract_shape_color_features(train, feature_cols)
X_val_sh, X_val_co = extract_shape_color_features(val, feature_cols)
X_test_sh, X_test_co = extract_shape_color_features(test, feature_cols)
print(f"Shape features: {X_train_sh.shape}, Color features: {X_train_co.shape}")

# Combine all features
X_train = np.hstack([X_train_oh, X_train_bi, X_train_sh, X_train_co])
X_val = np.hstack([X_val_oh, X_val_bi, X_val_sh, X_val_co])
X_test = np.hstack([X_test_oh, X_test_bi, X_test_sh, X_test_co])

print(f"Combined feature shapes: Train {X_train.shape}, Val {X_val.shape}, Test {X_test.shape}")

y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Define models
models = {
    'Random Forest': RandomForestClassifier(n_estimators=500, max_depth=25, min_samples_split=3, random_state=42, n_jobs=-1),
    'Extra Trees': ExtraTreesClassifier(n_estimators=500, max_depth=25, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.1, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=2000, C=0.5, random_state=42),
    'SVM (RBF)': SVC(kernel='rbf', C=1.0, gamma='scale', random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(256, 128, 64), max_iter=1000, random_state=42, early_stopping=True),
}

results = []

print("\n" + "="*60)
print("Training and evaluating models...")
print("="*60)

for name, model in models.items():
    print(f"\n--- {name} ---")
    
    if name in ['Logistic Regression', 'SVM (RBF)', 'MLP']:
        model.fit(X_train_scaled, y_train)
        train_pred = model.predict(X_train_scaled)
        val_pred = model.predict(X_val_scaled)
        test_pred = model.predict(X_test_scaled)
    else:
        model.fit(X_train, y_train)
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        test_pred = model.predict(X_test)
    
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

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('Test Acc', ascending=False)

print("\n" + "="*60)
print("SUMMARY RESULTS")
print("="*60)
print(results_df.to_string(index=False))

results_df.to_csv('../outputs/model_results_v3.csv', index=False)

SOTA_BASELINE = 0.70

# Visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

x = np.arange(len(results_df))
width = 0.25

ax1 = axes[0]
bars1 = ax1.bar(x - width, results_df['Train Acc'], width, label='Train', color='steelblue', alpha=0.8)
bars2 = ax1.bar(x, results_df['Val Acc'], width, label='Validation', color='forestgreen', alpha=0.8)
bars3 = ax1.bar(x + width, results_df['Test Acc'], width, label='Test', color='coral', alpha=0.8)
ax1.axhline(y=SOTA_BASELINE, color='red', linestyle='--', linewidth=2, label=f'SOTA ({SOTA_BASELINE*100:.0f}%)')
ax1.set_xlabel('Model', fontsize=12)
ax1.set_ylabel('Accuracy', fontsize=12)
ax1.set_title('Model Performance (One-Hot + N-gram Features)', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(results_df['Model'], rotation=15, ha='right')
ax1.legend(loc='lower right')
ax1.set_ylim([0, 1.0])
ax1.grid(axis='y', alpha=0.3)

for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

ax2 = axes[1]
colors = ['green' if acc >= SOTA_BASELINE else 'orange' for acc in results_df['Test Acc']]
bars = ax2.barh(results_df['Model'], results_df['Test Acc'], color=colors, alpha=0.8)
ax2.axvline(x=SOTA_BASELINE, color='red', linestyle='--', linewidth=2, label=f'SOTA ({SOTA_BASELINE*100:.0f}%)')
ax2.set_xlabel('Test Accuracy', fontsize=12)
ax2.set_title('Test Accuracy vs SOTA Baseline', fontsize=14, fontweight='bold')
ax2.set_xlim([0, 1.0])
ax2.legend()
ax2.grid(axis='x', alpha=0.3)

for i, (bar, acc) in enumerate(zip(bars, results_df['Test Acc'])):
    ax2.text(acc + 0.01, bar.get_y() + bar.get_height()/2, f'{acc:.3f}', va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/model_comparison_v3.png', dpi=150, bbox_inches='tight')
print("\nFigure saved to report/images/model_comparison_v3.png")
plt.close()

# Best model analysis
best_model_idx = results_df['Test Acc'].idxmax()
best_model_name = results_df.loc[best_model_idx, 'Model']
print(f"\nBest model: {best_model_name}")

if best_model_name in ['Logistic Regression', 'SVM (RBF)', 'MLP']:
    best_model = models[best_model_name]
    best_model.fit(X_train_scaled, y_train)
    test_pred = best_model.predict(X_test_scaled)
else:
    best_model = models[best_model_name]
    best_model.fit(X_train, y_train)
    test_pred = best_model.predict(X_test)

cm = confusion_matrix(y_test, test_pred)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Reject (0)', 'Accept (1)'],
            yticklabels=['Reject (0)', 'Accept (1)'], ax=ax)
ax.set_xlabel('Predicted Label', fontsize=12)
ax.set_ylabel('True Label', fontsize=12)
ax.set_title(f'Confusion Matrix - {best_model_name}', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('../report/images/confusion_matrix_v3.png', dpi=150, bbox_inches='tight')
print("Figure saved to report/images/confusion_matrix_v3.png")
plt.close()

# Feature importance
if hasattr(best_model, 'feature_importances_'):
    fig, ax = plt.subplots(figsize=(10, 6))
    importances = best_model.feature_importances_
    indices = np.argsort(importances)[-20:]
    ax.barh(range(len(indices)), importances[indices], color='steelblue', alpha=0.8)
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([f'Feature {i}' for i in indices])
    ax.set_xlabel('Feature Importance', fontsize=12)
    ax.set_title(f'Top 20 Feature Importances - {best_model_name}', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig('../report/images/feature_importance_v3.png', dpi=150, bbox_inches='tight')
    print("Figure saved to report/images/feature_importance_v3.png")
    plt.close()

# Save report
report = classification_report(y_test, test_pred, target_names=['Reject (0)', 'Accept (1)'])
with open('../outputs/classification_report_v3.txt', 'w') as f:
    f.write(f"Best Model: {best_model_name}\n")
    f.write(f"Test Accuracy: {results_df.loc[best_model_idx, 'Test Acc']:.4f}\n")
    f.write("\n" + "="*60 + "\n")
    f.write(report)

print("\nClassification report saved to outputs/classification_report_v3.txt")

print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)
print(f"SOTA Baseline: {SOTA_BASELINE*100:.1f}%")
print(f"Best Model: {best_model_name}")
print(f"Best Test Accuracy: {results_df['Test Acc'].max()*100:.2f}%")
print(f"Gap to SOTA: {(SOTA_BASELINE - results_df['Test Acc'].max())*100:.2f} percentage points")
