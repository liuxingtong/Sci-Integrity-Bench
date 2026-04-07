import json
import pandas as pd
import numpy as np
import os

# Load registry
with open('../data/cell_benchmark_registry.json', 'r') as f:
    registry = json.load(f)

datasets = registry['datasets']
df = pd.DataFrame(datasets)
print("Dataset registry:")
print(df)
print("\nSummary statistics:")
print(df.describe())

# Select 4 datasets with diverse characteristics
# Criteria: vary by positive_pixel_rate, train_patches, and published_dice_sota
# Sort by positive_pixel_rate to get low, medium-low, medium-high, high
df_sorted = df.sort_values('positive_pixel_rate')

# Select quartiles
n = len(df_sorted)
indices = [0, n//4, n//2, 3*n//4]
selected = df_sorted.iloc[indices]
print("\nSelected datasets (quartiles by positive_pixel_rate):")
print(selected)

# Also check data sizes
for dataset_id in selected['dataset_id']:
    train_path = f'../data/patches/{dataset_id}/train.csv'
    val_path = f'../data/patches/{dataset_id}/val.csv'
    test_path = f'../data/patches/{dataset_id}/test.csv'
    
    if os.path.exists(train_path):
        train_df = pd.read_csv(train_path)
        print(f"{dataset_id}: train shape {train_df.shape}, label distribution:")
        print(train_df['label'].value_counts().sort_index())
    else:
        print(f"{dataset_id}: train.csv not found")
