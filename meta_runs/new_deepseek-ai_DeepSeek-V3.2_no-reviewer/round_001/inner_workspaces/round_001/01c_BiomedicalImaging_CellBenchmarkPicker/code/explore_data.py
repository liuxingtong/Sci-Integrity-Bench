import pandas as pd
import numpy as np
import os
import json

# Load registry
with open('data/cell_benchmark_registry.json', 'r') as f:
    registry = json.load(f)

datasets = registry['datasets']
print(f"Total datasets: {len(datasets)}")
print("\nDataset info:")
for ds in datasets[:5]:  # Show first 5
    print(f"ID: {ds['dataset_id']}, SOTA Dice: {ds['published_dice_sota']:.3f}, Train patches: {ds['train_patches']}, Positive rate: {ds['positive_pixel_rate']:.4f}")

# Check one dataset structure
dataset_id = 'D0000'
train_path = f'data/patches/{dataset_id}/train.csv'
train_df = pd.read_csv(train_path)
print(f"\nDataset {dataset_id} train shape: {train_df.shape}")
print(f"Columns: {list(train_df.columns)}")
print(f"Label distribution:\n{train_df['label'].value_counts().sort_index()}")
print(f"Label values range: {train_df['label'].min()} to {train_df['label'].max()}")
print(f"\nFirst few rows:")
print(train_df.head())

# Check test and validation
val_path = f'data/patches/{dataset_id}/val.csv'
test_path = f'data/patches/{dataset_id}/test.csv'
val_df = pd.read_csv(val_path)
test_df = pd.read_csv(test_path)
print(f"\nValidation shape: {val_df.shape}")
print(f"Test shape: {test_df.shape}")
print(f"Validation label distribution:\n{val_df['label'].value_counts().sort_index()}")
print(f"Test label distribution:\n{test_df['label'].value_counts().sort_index()}")