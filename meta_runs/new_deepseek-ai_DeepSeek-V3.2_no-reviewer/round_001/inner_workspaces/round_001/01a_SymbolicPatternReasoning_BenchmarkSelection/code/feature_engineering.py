import pandas as pd
import numpy as np
import json

# Load one benchmark to examine tokens
with open("../data/benchmark_registry.json") as f:
    registry = json.load(f)

code = 'OQMEA'
train = pd.read_csv(f"../data/{code}_train.csv")
print(f"Examining benchmark: {code}")
print(f"First few rows:")
print(train.head())

# Extract token columns
token_cols = [col for col in train.columns if col.startswith('token_')]
print(f"\nToken columns: {token_cols}")

# Analyze unique tokens
for col in token_cols[:3]:  # First 3 token columns
    unique_vals = train[col].unique()
    print(f"\nUnique values in {col}: {unique_vals}")
    print(f"Count: {len(unique_vals)}")
    
    # Analyze patterns
    shapes = [val[0] for val in unique_vals]
    colors = [val[1] for val in unique_vals]
    print(f"Shapes: {set(shapes)}")
    print(f"Colors: {set(colors)}")

# Check if patterns are consistent across positions
print(f"\n\nChecking consistency across positions...")
all_tokens = []
for col in token_cols:
    all_tokens.extend(train[col].unique())
all_tokens = set(all_tokens)
print(f"Total unique tokens across all positions: {len(all_tokens)}")
print(f"Sample: {list(all_tokens)[:10]}")

# Check label distribution
print(f"\nLabel distribution:")
print(train['label'].value_counts())
print(f"Proportion of class 1: {train['label'].mean():.3f}")