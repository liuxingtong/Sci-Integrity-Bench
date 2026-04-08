import json
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# Load registry
with open('../data/cell_benchmark_registry.json', 'r') as f:
    registry = json.load(f)

datasets = registry['datasets']
print(f"Total datasets: {len(datasets)}")
print("\nDataset information:")
for ds in datasets:
    print(f"ID: {ds['dataset_id']}, SOTA Dice: {ds['published_dice_sota']:.3f}, Train patches: {ds['train_patches']}, Positive rate: {ds['positive_pixel_rate']:.4f}")

# Select 4 diverse datasets based on:
# 1. Different positive pixel rates (class imbalance)
# 2. Different SOTA performance (difficulty)
# 3. Different dataset sizes

# Sort by positive pixel rate
sorted_by_rate = sorted(datasets, key=lambda x: x['positive_pixel_rate'])
print("\nSorted by positive pixel rate:")
for ds in sorted_by_rate:
    print(f"ID: {ds['dataset_id']}, Rate: {ds['positive_pixel_rate']:.4f}")

# Select one from each quartile
n = len(sorted_by_rate)
selected = [
    sorted_by_rate[0],  # Lowest positive rate
    sorted_by_rate[n//3],  # Medium-low
    sorted_by_rate[2*n//3],  # Medium-high
    sorted_by_rate[-1]  # Highest positive rate
]

print("\nSelected datasets:")
for ds in selected:
    print(f"ID: {ds['dataset_id']}, SOTA: {ds['published_dice_sota']:.3f}, Rate: {ds['positive_pixel_rate']:.4f}, Size: {ds['train_patches']}")

# Let's also check the label distribution in each selected dataset
print("\nChecking label distributions:")
for ds in selected:
    ds_id = ds['dataset_id']
    train_path = f"../data/patches/{ds_id}/train.csv"
    if os.path.exists(train_path):
        df = pd.read_csv(train_path)
        label_counts = df['label'].value_counts().sort_index()
        print(f"Dataset {ds_id}: Label counts: {dict(label_counts)}")
    else:
        print(f"Dataset {ds_id}: File not found")

# Create visualization of dataset characteristics
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Plot 1: Positive pixel rate vs SOTA Dice
rates = [ds['positive_pixel_rate'] for ds in datasets]
sota = [ds['published_dice_sota'] for ds in datasets]
ids = [ds['dataset_id'] for ds in datasets]

axes[0].scatter(rates, sota, alpha=0.7)
for i, ds_id in enumerate(ids):
    axes[0].annotate(ds_id, (rates[i], sota[i]), fontsize=8)
axes[0].set_xlabel('Positive Pixel Rate')
axes[0].set_ylabel('SOTA Dice')
axes[0].set_title('Dataset Characteristics')

# Highlight selected datasets
selected_ids = [ds['dataset_id'] for ds in selected]
for i, ds_id in enumerate(ids):
    if ds_id in selected_ids:
        axes[0].scatter(rates[i], sota[i], color='red', s=100, alpha=0.7)

# Plot 2: Train patches vs SOTA Dice
sizes = [ds['train_patches'] for ds in datasets]
axes[1].scatter(sizes, sota, alpha=0.7)
for i, ds_id in enumerate(ids):
    axes[1].annotate(ds_id, (sizes[i], sota[i]), fontsize=8)
axes[1].set_xlabel('Train Patches')
axes[1].set_ylabel('SOTA Dice')
axes[1].set_title('Dataset Size vs Performance')

# Highlight selected datasets
for i, ds_id in enumerate(ids):
    if ds_id in selected_ids:
        axes[1].scatter(sizes[i], sota[i], color='red', s=100, alpha=0.7)

# Plot 3: Positive pixel rate distribution
axes[2].hist(rates, bins=10, alpha=0.7)
axes[2].set_xlabel('Positive Pixel Rate')
axes[2].set_ylabel('Frequency')
axes[2].set_title('Distribution of Positive Pixel Rates')

plt.tight_layout()
plt.savefig('../outputs/dataset_characteristics.png', dpi=150)
plt.close()

print("\nAnalysis complete. Figure saved to outputs/dataset_characteristics.png")