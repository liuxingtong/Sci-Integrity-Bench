import pandas as pd
import numpy as np
import os

# Check all result files
print("Checking all results...\n")

# List all CSV files in outputs
output_dir = '../outputs'
if os.path.exists(output_dir):
    csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
    for csv_file in csv_files:
        path = os.path.join(output_dir, csv_file)
        df = pd.read_csv(path)
        print(f"{csv_file}:")
        print(df.to_string(index=False))
        print("\n" + "-"*50 + "\n")

# Calculate label distribution
print("\nLabel distributions:")
for split_name, path in [('train', '../data/spr_bench_train.csv'), 
                         ('val', '../data/spr_bench_val.csv'), 
                         ('test', '../data/spr_bench_test.csv')]:
    df = pd.read_csv(path)
    label_dist = df['label'].value_counts(normalize=True)
    print(f"{split_name}: {len(df)} samples, label 0: {label_dist.get(0, 0):.2%}, label 1: {label_dist.get(1, 0):.2%}")

# Check if there's any simple pattern
print("\n\nChecking for simple patterns...")
train = pd.read_csv('../data/spr_bench_train.csv')
feature_cols = [c for c in train.columns if c.startswith('token_')]

# Check if label depends on specific positions
for pos in range(8):
    col = f'token_{pos}'
    # Get most common token for each label
    for label in [0, 1]:
        subset = train[train['label'] == label]
        most_common = subset[col].value_counts().index[0]
        count = subset[col].value_counts().iloc[0]
        total = len(subset)
        print(f"Label {label}, Position {pos}: Most common token = {most_common} ({count/total:.1%})")
    print()

# Check shape/color distributions by label
print("\nShape and color distributions by label:")
for label in [0, 1]:
    subset = train[train['label'] == label]
    print(f"\nLabel {label} ({len(subset)} samples):")
    
    # Count shapes
    shape_counts = {'T': 0, 'S': 0, 'C': 0, 'D': 0}
    color_counts = {'r': 0, 'g': 0, 'b': 0, 'y': 0}
    
    for _, row in subset.iterrows():
        for pos in range(8):
            token = row[f'token_{pos}']
            shape = token[0]
            color = token[1]
            shape_counts[shape] += 1
            color_counts[color] += 1
    
    total_tokens = len(subset) * 8
    print("Shapes:", {k: f'{v/total_tokens:.1%}' for k, v in shape_counts.items()})
    print("Colors:", {k: f'{v/total_tokens:.1%}' for k, v in color_counts.items()})