"""
SPR_BENCH Deep Analysis
Try sequence-based approaches and analyze potential label noise
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
print("Loading data...")
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

# Extract feature columns
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Labels
y_train = train['label'].values
y_val = val['label'].values
y_test = test['label'].values

print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

# One-hot encoding for tokens
def one_hot_encode(df, feature_cols):
    """One-hot encode each token position"""
    all_tokens = ['Cb', 'Cg', 'Cr', 'Cy', 'Db', 'Dg', 'Dr', 'Dy', 
                  'Sb', 'Sg', 'Sr', 'Sy', 'Tb', 'Tg', 'Tr', 'Ty']
    token_to_idx = {t: i for i, t in enumerate(all_tokens)}
    
    n_samples = len(df)
    n_positions = len(feature_cols)
    n_tokens = len(all_tokens)
    
    # Create one-hot encoded matrix
    encoded = np.zeros((n_samples, n_positions * n_tokens))
    
    for i, col in enumerate(feature_cols):
        for j, token in enumerate(df[col]):
            if token in token_to_idx:
                encoded[j, i * n_tokens + token_to_idx[token]] = 1
    
    return encoded

print("\nCreating one-hot encoded features...")
X_train_oh = one_hot_encode(train, feature_cols)
X_val_oh = one_hot_encode(val, feature_cols)
X_test_oh = one_hot_encode(test, feature_cols)

print(f"One-hot features shape: {X_train_oh.shape}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_oh)
X_val_scaled = scaler.transform(X_val_oh)
X_test_scaled = scaler.transform(X_test_oh)

# Train models with one-hot encoding
print("\n=== Training with One-Hot Encoding ===")

models = {
    'LogReg': LogisticRegression(max_iter=2000, C=1.0, random_state=42),
    'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42),
    'GradientBoost': GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42),
    'MLP_512_256': MLPClassifier(hidden_layer_sizes=(512, 256), max_iter=1000, random_state=42),
    'MLP_512_256_128': MLPClassifier(hidden_layer_sizes=(512, 256, 128), max_iter=1000, random_state=42),
    'MLP_1024_512': MLPClassifier(hidden_layer_sizes=(1024, 512), max_iter=1000, random_state=42),
}

results = []

for name, model in models.items():
    print(f"Training {name}...", end=' ')
    model.fit(X_train_scaled, y_train)
    
    train_acc = accuracy_score(y_train, model.predict(X_train_scaled))
    val_acc = accuracy_score(y_val, model.predict(X_val_scaled))
    test_acc = accuracy_score(y_test, model.predict(X_test_scaled))
    
    print(f"Test: {test_acc:.4f}")
    
    results.append({
        'Model': name,
        'Features': 'OneHot',
        'Train Acc': train_acc,
        'Val Acc': val_acc,
        'Test Acc': test_acc
    })

# Try to find patterns by analyzing the data more carefully
print("\n=== Deep Pattern Analysis ===")

# Analyze n-gram patterns
def get_ngrams(tokens, n):
    """Get n-grams from token list"""
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

# Analyze bigram patterns by label
print("\nAnalyzing bigram patterns...")
bigram_counts = {0: {}, 1: {}}

for idx, row in train.iterrows():
    label = row['label']
    tokens = [row[col] for col in feature_cols]
    for bigram in get_ngrams(tokens, 2):
        if bigram not in bigram_counts[label]:
            bigram_counts[label][bigram] = 0
        bigram_counts[label][bigram] += 1

# Find discriminative bigrams
print("\nMost discriminative bigrams:")
all_bigrams = set(bigram_counts[0].keys()) | set(bigram_counts[1].keys())
bigram_scores = []

for bigram in all_bigrams:
    count_0 = bigram_counts[0].get(bigram, 0)
    count_1 = bigram_counts[1].get(bigram, 0)
    total = count_0 + count_1
    if total >= 10:  # Only consider bigrams appearing at least 10 times
        diff = (count_1 - count_0) / total
        bigram_scores.append((bigram, count_0, count_1, diff))

bigram_scores.sort(key=lambda x: abs(x[3]), reverse=True)

print("\nTop 10 discriminative bigrams:")
for bigram, c0, c1, diff in bigram_scores[:10]:
    print(f"  {bigram}: label0={c0}, label1={c1}, diff={diff:.3f}")

# Analyze trigram patterns
print("\nAnalyzing trigram patterns...")
trigram_counts = {0: {}, 1: {}}

for idx, row in train.iterrows():
    label = row['label']
    tokens = [row[col] for col in feature_cols]
    for trigram in get_ngrams(tokens, 3):
        if trigram not in trigram_counts[label]:
            trigram_counts[label][trigram] = 0
        trigram_counts[label][trigram] += 1

# Find discriminative trigrams
all_trigrams = set(trigram_counts[0].keys()) | set(trigram_counts[1].keys())
trigram_scores = []

for trigram in all_trigrams:
    count_0 = trigram_counts[0].get(trigram, 0)
    count_1 = trigram_counts[1].get(trigram, 0)
    total = count_0 + count_1
    if total >= 5:  # Only consider trigrams appearing at least 5 times
        diff = (count_1 - count_0) / total
        trigram_scores.append((trigram, count_0, count_1, diff))

trigram_scores.sort(key=lambda x: abs(x[3]), reverse=True)

print("\nTop 10 discriminative trigrams:")
for trigram, c0, c1, diff in trigram_scores[:10]:
    print(f"  {trigram}: label0={c0}, label1={c1}, diff={diff:.3f}")

# Check for position-specific patterns
print("\n=== Position-Specific Analysis ===")

for pos in range(len(feature_cols)):
    col = feature_cols[pos]
    print(f"\nPosition {pos} ({col}):")
    
    for label in [0, 1]:
        subset = train[train['label'] == label]
        token_counts = subset[col].value_counts()
        top_tokens = token_counts.head(3)
        print(f"  Label {label}: {top_tokens.to_dict()}")

# Analyze shape/color patterns
print("\n=== Shape/Color Pattern Analysis ===")

# Check if specific shapes/colors are more common in each label
for label in [0, 1]:
    subset = train[train['label'] == label]
    print(f"\nLabel {label}:")
    
    # Shape distribution
    shape_counts = {}
    for col in feature_cols:
        for shape in subset[col].apply(lambda x: x[0]):
            shape_counts[shape] = shape_counts.get(shape, 0) + 1
    
    total_shapes = sum(shape_counts.values())
    print(f"  Shape distribution: {dict((k, f'{v/total_shapes*100:.1f}%') for k, v in sorted(shape_counts.items()))}")
    
    # Color distribution
    color_counts = {}
    for col in feature_cols:
        for color in subset[col].apply(lambda x: x[1]):
            color_counts[color] = color_counts.get(color, 0) + 1
    
    total_colors = sum(color_counts.values())
    print(f"  Color distribution: {dict((k, f'{v/total_colors*100:.1f}%') for k, v in sorted(color_counts.items()))}")

# Estimate label noise ceiling
print("\n=== Label Noise Ceiling Estimation ===")

# Use cross-validation to estimate the noise ceiling
from sklearn.model_selection import cross_val_score

# Train a strong model and check consistency
rf = RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42)
cv_scores = cross_val_score(rf, X_train_scaled, y_train, cv=5)
print(f"5-fold CV scores: {cv_scores}")
print(f"Mean CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")

# Check if there are duplicate samples with different labels
print("\nChecking for label inconsistencies...")
train_sequences = train[feature_cols].apply(tuple, axis=1)
duplicate_check = train.groupby(train_sequences)['label'].nunique()
inconsistent = duplicate_check[duplicate_check > 1]
print(f"Sequences with inconsistent labels: {len(inconsistent)}")

if len(inconsistent) > 0:
    print("Sample inconsistent sequences:")
    for seq in inconsistent.index[:5]:
        labels = train[train_sequences == seq]['label'].values
        print(f"  {seq}: labels = {labels}")

# Create results dataframe
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('Test Acc', ascending=False)

print("\n=== Final Results Summary ===")
print(results_df.to_string(index=False))

# Save results
results_df.to_csv('../outputs/deep_model_results.csv', index=False)

# Create visualization
plt.figure(figsize=(12, 6))
colors = ['green' if acc >= 0.7 else 'coral' for acc in results_df['Test Acc']]
plt.barh(results_df['Model'], results_df['Test Acc'], color=colors, alpha=0.8)
plt.axvline(x=0.7, color='navy', linestyle='--', linewidth=2, label='SOTA (70%)')
plt.axvline(x=0.5, color='gray', linestyle=':', linewidth=1, label='Random (50%)')
plt.xlabel('Test Accuracy')
plt.title('Model Performance with One-Hot Encoding')
plt.xlim(0.4, 0.8)
plt.legend(loc='lower right')
plt.tight_layout()
plt.savefig('../report/images/onehot_model_comparison.png', dpi=150)
plt.close()
print("\nSaved onehot_model_comparison.png")

# Create summary figure
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Model comparison
ax1 = axes[0, 0]
ax1.barh(results_df['Model'], results_df['Test Acc'], color='steelblue', alpha=0.8)
ax1.axvline(x=0.7, color='red', linestyle='--', linewidth=2, label='SOTA (70%)')
ax1.set_xlabel('Test Accuracy')
ax1.set_title('Model Performance')
ax1.legend()

# Plot 2: Train vs Test
ax2 = axes[0, 1]
x = np.arange(len(results_df))
width = 0.35
ax2.bar(x - width/2, results_df['Train Acc'], width, label='Train', alpha=0.8)
ax2.bar(x + width/2, results_df['Test Acc'], width, label='Test', alpha=0.8)
ax2.axhline(y=0.7, color='red', linestyle='--', linewidth=2, label='SOTA')
ax2.set_xlabel('Model')
ax2.set_ylabel('Accuracy')
ax2.set_title('Train vs Test Accuracy')
ax2.set_xticks(x)
ax2.set_xticklabels(results_df['Model'], rotation=45, ha='right')
ax2.legend()

# Plot 3: Label distribution
ax3 = axes[1, 0]
labels = ['Train', 'Val', 'Test']
label_0 = [train['label'].sum(), val['label'].sum(), test['label'].sum()]
label_1 = [len(train) - train['label'].sum(), len(val) - val['label'].sum(), len(test) - test['label'].sum()]
x = np.arange(len(labels))
width = 0.35
ax3.bar(x - width/2, label_0, width, label='Label 0', color='coral')
ax3.bar(x + width/2, label_1, width, label='Label 1', color='steelblue')
ax3.set_xlabel('Dataset')
ax3.set_ylabel('Count')
ax3.set_title('Label Distribution')
ax3.set_xticks(x)
ax3.set_xticklabels(labels)
ax3.legend()

# Plot 4: Performance gap
ax4 = axes[1, 1]
gaps = results_df['Test Acc'].values - 0.7
colors = ['green' if g >= 0 else 'red' for g in gaps]
ax4.bar(results_df['Model'], gaps, color=colors, alpha=0.8)
ax4.axhline(y=0, color='black', linewidth=1)
ax4.set_xlabel('Model')
ax4.set_ylabel('Gap from SOTA (70%)')
ax4.set_title('Performance Gap from SOTA')
ax4.set_xticklabels(results_df['Model'], rotation=45, ha='right')

plt.tight_layout()
plt.savefig('../report/images/summary_analysis.png', dpi=150)
plt.close()
print("Saved summary_analysis.png")

print("\n=== Analysis Complete ===")