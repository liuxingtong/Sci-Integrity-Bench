#!/usr/bin/env python3
"""
Analyze patterns in the symbolic data more carefully.
"""

import pandas as pd
import numpy as np
from collections import Counter

# Look at ZOBKB in detail - highest SOTA
print("="*60)
print("ZOBKB Analysis (SOTA: 95.2%)")
print("="*60)

train = pd.read_csv('data/ZOBKB_train.csv')
test = pd.read_csv('data/ZOBKB_test.csv')

print(f"\nTrain shape: {train.shape}")
print(f"\nFirst 20 rows with label=1:")
print(train[train['label']==1].head(20).to_string())

print(f"\nFirst 20 rows with label=0:")
print(train[train['label']==0].head(20).to_string())

# Check for patterns
feature_cols = [c for c in train.columns if c != 'label']

# Check if certain token positions correlate with label
print("\nToken value distributions by label:")
for col in feature_cols:
    print(f"\n{col}:")
    for label in [0, 1]:
        vals = train[train['label']==label][col].value_counts().head(5)
        print(f"  Label {label}: {dict(vals)}")

# Check for repeated tokens
print("\n\nChecking for repeated tokens in sequences:")
for label in [0, 1]:
    subset = train[train['label']==label]
    repeat_counts = []
    for idx, row in subset.iterrows():
        tokens = [row[c] for c in feature_cols]
        counts = Counter(tokens)
        max_repeat = max(counts.values())
        repeat_counts.append(max_repeat)
    print(f"Label {label}: avg max repeat = {np.mean(repeat_counts):.2f}")

# Check first vs last token
print("\n\nFirst token vs Last token match:")
for label in [0, 1]:
    subset = train[train['label']==label]
    matches = (subset['token_0'] == subset['token_5']).sum()
    print(f"Label {label}: first==last in {matches}/{len(subset)} cases ({100*matches/len(subset):.1f}%)")
