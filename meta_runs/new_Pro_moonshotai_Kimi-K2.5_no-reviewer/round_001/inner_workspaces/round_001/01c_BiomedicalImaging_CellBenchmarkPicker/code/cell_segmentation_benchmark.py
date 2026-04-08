"""
Cell-Patch Segmentation Benchmark Analysis
Trains MLP baselines on tabular patch features for cell segmentation.
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load registry
with open('data/cell_benchmark_registry.json', 'r') as f:
    registry = json.load(f)

print("=" * 60)
print("CELL-PATCH SEGMENTATION BENCHMARK")
print("=" * 60)

# Select 4 diverse datasets based on positive pixel rate and difficulty
# D0001: High positive rate (0.765), high SOTA (0.862)
# D0002: Very low positive rate (0.0202), low SOTA (0.581) - challenging
# D0007: Medium positive rate (0.5115), high SOTA (0.833)
# D0013: Medium-high positive rate (0.5923), highest SOTA (0.862)

SELECTED_DATASETS = ['D0001', 'D0002', 'D0007', 'D0013']

print(f"\nSelected datasets: {SELECTED_DATASETS}")
print("\nDataset characteristics:")
for ds in SELECTED_DATASETS:
    info = next(d for d in registry['datasets'] if d['dataset_id'] == ds)
    print(f"  {ds}: train_patches={info['train_patches']}, "
          f"positive_rate={info['positive_pixel_rate']:.4f}, "
          f"SOTA={info['published_dice_sota']:.3f}")

# Function to compute Dice-like score from classification
# Since we have 4 classes (0-3) representing foreground fraction buckets,
# we compute a weighted Dice-like metric
def compute_dice_proxy(y_true, y_pred, num_classes=4):
    """
    Compute a Dice-like score treating this as a multi-class segmentation problem.
    We compute the average Dice across all class pairs.
    """
    # Convert to one-hot
    y_true_oh = np.eye(num_classes)[y_true]
    y_pred_oh = np.eye(num_classes)[y_pred]
    
    dice_scores = []
    for c in range(num_classes):
        tp = np.sum((y_true == c) & (y_pred == c))
        fp = np.sum((y_true != c) & (y_pred == c))
        fn = np.sum((y_true == c) & (y_pred != c))
        
        if tp + fp + fn == 0:
            dice = 1.0  # Perfect match if no samples of this class
        else:
            dice = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0
        dice_scores.append(dice)
    
    return np.mean(dice_scores)

# Function to compute foreground-weighted Dice (emphasizing positive classes)
def compute_weighted_dice(y_true, y_pred):
    """
    Compute weighted Dice emphasizing higher foreground classes (1,2,3).
    """
    weights = {0: 0.1, 1: 0.3, 2: 0.3, 3: 0.3}  # Weight background less
    
    dice_scores = []
    for c in range(4):
        tp = np.sum((y_true == c) & (y_pred == c))
        fp = np.sum((y_true != c) & (y_pred == c))
        fn = np.sum((y_true == c) & (y_pred != c))
        
        if tp + fp + fn == 0:
            dice = 1.0
        else:
            dice = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0
        dice_scores.append(dice * weights[c])
    
    return sum(dice_scores) / sum(weights.values())

# Store results
results = {}
all_predictions = {}

print("\n" + "=" * 60)
print("TRAINING AND EVALUATION")
print("=" * 60)

for dataset_id in SELECTED_DATASETS:
    print(f"\n{'-' * 50}")
    print(f"Dataset: {dataset_id}")
    print(f"{'-' * 50}")
    
    # Load data
    train_df = pd.read_csv(f'data/patches/{dataset_id}/train.csv')
    val_df = pd.read_csv(f'data/patches/{dataset_id}/val.csv')
    test_df = pd.read_csv(f'data/patches/{dataset_id}/test.csv')
    
    # Extract features and labels
    feature_cols = [f'feat_{i}' for i in range(32)]
    X_train = train_df[feature_cols].values
    y_train = train_df['label'].values
    X_val = val_df[feature_cols].values
    y_val = val_df['label'].values
    X_test = test_df[feature_cols].values
    y_test = test_df['label'].values
    
    print(f"Train samples: {len(X_train)}, Val samples: {len(X_val)}, Test samples: {len(X_test)}")
    print(f"Label distribution (train): {dict(zip(*np.unique(y_train, return_counts=True)))}")
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Train MLP classifier
    # Architecture: 32 -> 64 -> 32 -> 4 (similar to a small U-Net bottleneck)
    mlp = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        solver='adam',
        alpha=0.001,
        batch_size=32,
        learning_rate_init=0.001,
        max_iter=500,
        early_stopping=True,
        validation_fraction=0.1,
        n_iter_no_change=20,
        random_state=42
    )
    
    print("Training MLP...")
    mlp.fit(X_train_scaled, y_train)
    
    # Evaluate on all sets
    y_train_pred = mlp.predict(X_train_scaled)
    y_val_pred = mlp.predict(X_val_scaled)
    y_test_pred = mlp.predict(X_test_scaled)
    
    # Compute metrics
    train_acc = accuracy_score(y_train, y_train_pred)
    val_acc = accuracy_score(y_val, y_val_pred)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    train_dice = compute_dice_proxy(y_train, y_train_pred)
    val_dice = compute_dice_proxy(y_val, y_val_pred)
    test_dice = compute_dice_proxy(y_test, y_test_pred)
    
    train_wdice = compute_weighted_dice(y_train, y_train_pred)
    val_wdice = compute_weighted_dice(y_val, y_val_pred)
    test_wdice = compute_weighted_dice(y_test, y_test_pred)
    
    # Get SOTA for comparison
    sota = next(d for d in registry['datasets'] if d['dataset_id'] == dataset_id)['published_dice_sota']
    
    results[dataset_id] = {
        'train_acc': train_acc,
        'val_acc': val_acc,
        'test_acc': test_acc,
        'train_dice': train_dice,
        'val_dice': val_dice,
        'test_dice': test_dice,
        'train_wdice': train_wdice,
        'val_wdice': val_wdice,
        'test_wdice': test_wdice,
        'sota': sota,
        'n_iterations': mlp.n_iter_
    }
    
    all_predictions[dataset_id] = {
        'y_true': y_test,
        'y_pred': y_test_pred
    }
    
    print(f"\nResults for {dataset_id}:")
    print(f"  Training iterations: {mlp.n_iter_}")
    print(f"  Train Accuracy: {train_acc:.4f}")
    print(f"  Val Accuracy:   {val_acc:.4f}")
    print(f"  Test Accuracy:  {test_acc:.4f}")
    print(f"  Train Dice:     {train_dice:.4f}")
    print(f"  Val Dice:       {val_dice:.4f}")
    print(f"  Test Dice:      {test_dice:.4f} (SOTA: {sota:.3f})")
    print(f"  Weighted Dice:  {test_wdice:.4f}")

# Save results
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

summary_df = pd.DataFrame(results).T
print("\n", summary_df[['test_acc', 'test_dice', 'test_wdice', 'sota']])

# Save to CSV
summary_df.to_csv('outputs/results_summary.csv')
print("\nResults saved to outputs/results_summary.csv")

# Create visualizations
print("\nGenerating figures...")

# Figure 1: Dice scores comparison
fig, ax = plt.subplots(figsize=(10, 6))
datasets = list(results.keys())
test_dices = [results[d]['test_dice'] for d in datasets]
sotas = [results[d]['sota'] for d in datasets]

x = np.arange(len(datasets))
width = 0.35

bars1 = ax.bar(x - width/2, test_dices, width, label='MLP Baseline', color='steelblue', edgecolor='black')
bars2 = ax.bar(x + width/2, sotas, width, label='Published SOTA', color='coral', edgecolor='black', alpha=0.8)

ax.set_xlabel('Dataset', fontsize=12)
ax.set_ylabel('Dice Score', fontsize=12)
ax.set_title('Test Dice Scores: MLP Baseline vs Published SOTA', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(datasets)
ax.legend()
ax.set_ylim(0, 1.0)
ax.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/figure1_dice_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/figure1_dice_comparison.png")

# Figure 2: Confusion matrices
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

for idx, dataset_id in enumerate(SELECTED_DATASETS):
    y_true = all_predictions[dataset_id]['y_true']
    y_pred = all_predictions[dataset_id]['y_pred']
    
    cm = confusion_matrix(y_true, y_pred)
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                xticklabels=[0, 1, 2, 3], yticklabels=[0, 1, 2, 3],
                cbar_kws={'label': 'Count'})
    axes[idx].set_title(f'{dataset_id} - Confusion Matrix', fontweight='bold')
    axes[idx].set_xlabel('Predicted Label')
    axes[idx].set_ylabel('True Label')

plt.tight_layout()
plt.savefig('report/images/figure2_confusion_matrices.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/figure2_confusion_matrices.png")

# Figure 3: Performance metrics across datasets
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

metrics = ['test_acc', 'test_dice', 'test_wdice']
metric_names = ['Accuracy', 'Dice Score', 'Weighted Dice']

for idx, (metric, name) in enumerate(zip(metrics, metric_names)):
    values = [results[d][metric] for d in datasets]
    axes[idx].bar(datasets, values, color='steelblue', edgecolor='black')
    axes[idx].set_title(name, fontweight='bold')
    axes[idx].set_ylabel('Score')
    axes[idx].set_ylim(0, 1.0)
    axes[idx].grid(axis='y', alpha=0.3)
    
    # Add value labels
    for i, v in enumerate(values):
        axes[idx].text(i, v + 0.02, f'{v:.3f}', ha='center', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/figure3_performance_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/figure3_performance_metrics.png")

# Figure 4: Gap to SOTA analysis
fig, ax = plt.subplots(figsize=(10, 6))
gaps = [results[d]['sota'] - results[d]['test_dice'] for d in datasets]
colors = ['green' if g < 0.1 else 'orange' if g < 0.2 else 'red' for g in gaps]

bars = ax.bar(datasets, gaps, color=colors, edgecolor='black', alpha=0.7)
ax.set_xlabel('Dataset', fontsize=12)
ax.set_ylabel('Gap to SOTA (SOTA - Our Dice)', fontsize=12)
ax.set_title('Performance Gap to Published SOTA', fontsize=14, fontweight='bold')
ax.axhline(y=0.1, color='orange', linestyle='--', alpha=0.5, label='10% gap')
ax.axhline(y=0.2, color='red', linestyle='--', alpha=0.5, label='20% gap')
ax.legend()
ax.grid(axis='y', alpha=0.3)

for bar, gap in zip(bars, gaps):
    height = bar.get_height()
    ax.annotate(f'{gap:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/figure4_sota_gap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/figure4_sota_gap.png")

# Figure 5: Dataset characteristics vs performance
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Get dataset info
dataset_info = {d['dataset_id']: d for d in registry['datasets']}
positive_rates = [dataset_info[d]['positive_pixel_rate'] for d in datasets]
train_sizes = [dataset_info[d]['train_patches'] for d in datasets]
test_dices = [results[d]['test_dice'] for d in datasets]

# Plot 1: Positive rate vs Dice
axes[0].scatter(positive_rates, test_dices, s=200, c='steelblue', edgecolors='black', alpha=0.7)
for i, d in enumerate(datasets):
    axes[0].annotate(d, (positive_rates[i], test_dices[i]), 
                     xytext=(5, 5), textcoords='offset points', fontsize=10)
axes[0].set_xlabel('Positive Pixel Rate', fontsize=12)
axes[0].set_ylabel('Test Dice Score', fontsize=12)
axes[0].set_title('Performance vs Class Balance', fontsize=13, fontweight='bold')
axes[0].grid(alpha=0.3)

# Plot 2: Training size vs Dice
axes[1].scatter(train_sizes, test_dices, s=200, c='coral', edgecolors='black', alpha=0.7)
for i, d in enumerate(datasets):
    axes[1].annotate(d, (train_sizes[i], test_dices[i]), 
                     xytext=(5, 5), textcoords='offset points', fontsize=10)
axes[1].set_xlabel('Training Set Size', fontsize=12)
axes[1].set_ylabel('Test Dice Score', fontsize=12)
axes[1].set_title('Performance vs Training Data Size', fontsize=13, fontweight='bold')
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure5_characteristics_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/figure5_characteristics_analysis.png")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)

# Print final summary
print("\nFinal Test Dice Scores:")
for d in datasets:
    sota = results[d]['sota']
    dice = results[d]['test_dice']
    gap = sota - dice
    print(f"  {d}: {dice:.4f} (SOTA: {sota:.3f}, gap: {gap:.3f})")
