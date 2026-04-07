import pandas as pd
import numpy as np

# Examine FDLOT benchmark (hardest of our selection)
code = 'FDLOT'
train = pd.read_csv(f"../data/{code}_train.csv")
val = pd.read_csv(f"../data/{code}_val.csv")

print(f"Analyzing {code} benchmark")
print(f"Train shape: {train.shape}")

# Get token columns
token_cols = [col for col in train.columns if col.startswith('token_')]

# Look at examples from each class
print("\nExamples from class 0:")
class0 = train[train['label'] == 0].head(3)
for idx, row in class0.iterrows():
    tokens = [row[col] for col in token_cols]
    print(f"  {tokens}")

print("\nExamples from class 1:")
class1 = train[train['label'] == 1].head(3)
for idx, row in class1.iterrows():
    tokens = [row[col] for col in token_cols]
    print(f"  {tokens}")

# Try to find simple patterns
print("\n\nLooking for simple patterns...")

# Check if label depends on first token
print("\nFirst token distribution by class:")
first_token_by_class = train.groupby('label')['token_0'].value_counts(normalize=True)
print(first_token_by_class)

# Check if label depends on majority shape
print("\n\nExtracting shape and color counts...")
# Add shape and color columns
for i, col in enumerate(token_cols):
    train[f'{col}_shape'] = train[col].str[0]
    train[f'{col}_color'] = train[col].str[1]

# Count shapes in each sequence
shapes = ['C', 'S', 'T', 'D']
for shape in shapes:
    shape_cols = [f'{col}_shape' for col in token_cols]
    train[f'count_{shape}'] = (train[shape_cols] == shape).sum(axis=1)

# Check if count of a particular shape predicts label
print("\nMean shape counts by class:")
for shape in shapes:
    mean_count_0 = train[train['label'] == 0][f'count_{shape}'].mean()
    mean_count_1 = train[train['label'] == 1][f'count_{shape}'].mean()
    print(f"  {shape}: Class 0 = {mean_count_0:.2f}, Class 1 = {mean_count_1:.2f}")

# Check colors
colors = ['r', 'g', 'b', 'y']
for color in colors:
    color_cols = [f'{col}_color' for col in token_cols]
    train[f'count_{color}'] = (train[color_cols] == color).sum(axis=1)

print("\nMean color counts by class:")
for color in colors:
    mean_count_0 = train[train['label'] == 0][f'count_{color}'].mean()
    mean_count_1 = train[train['label'] == 1][f'count_{color}'].mean()
    print(f"  {color}: Class 0 = {mean_count_0:.2f}, Class 1 = {mean_count_1:.2f}")