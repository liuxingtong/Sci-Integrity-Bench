import json
import pandas as pd

with open('data/cell_benchmark_registry.json', 'r') as f:
    registry = json.load(f)

datasets = registry['datasets']

# Create DataFrame for analysis
df = pd.DataFrame(datasets)
df['positive_pixel_rate'] = df['positive_pixel_rate'].astype(float)
df['published_dice_sota'] = df['published_dice_sota'].astype(float)

print("Dataset characteristics:")
print(df[['dataset_id', 'published_dice_sota', 'train_patches', 'positive_pixel_rate']].to_string())
print("\nSummary statistics:")
print(f"SOTA Dice range: {df['published_dice_sota'].min():.3f} to {df['published_dice_sota'].max():.3f}")
print(f"Positive rate range: {df['positive_pixel_rate'].min():.4f} to {df['positive_pixel_rate'].max():.4f}")
print(f"Train patches range: {df['train_patches'].min()} to {df['train_patches'].max()}")

# Select 4 diverse datasets
# Let's pick: 
# 1. D0000 - medium SOTA, medium positive rate
# 2. D0001 - high SOTA, high positive rate  
# 3. D0002 - low SOTA, very low positive rate
# 4. D0013 - high SOTA, medium positive rate
selected = ['D0000', 'D0001', 'D0002', 'D0013']
print(f"\nSelected datasets: {selected}")
print("\nSelected dataset details:")
print(df[df['dataset_id'].isin(selected)].to_string())