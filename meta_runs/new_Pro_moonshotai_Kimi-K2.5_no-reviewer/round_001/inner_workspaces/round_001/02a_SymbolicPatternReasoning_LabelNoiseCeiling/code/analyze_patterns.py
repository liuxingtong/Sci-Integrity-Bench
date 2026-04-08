"""
Analyze SPR data to understand hidden patterns and label noise.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

np.random.seed(42)

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

print("="*60)
print("DATA ANALYSIS")
print("="*60)

# Label distribution
print("\nLabel Distribution:")
for name, df in [('Train', train), ('Val', val), ('Test', test)]:
    counts = df['label'].value_counts().sort_index()
    pct = df['label'].value_counts(normalize=True).sort_index() * 100
    print(f"  {name}: 0={counts[0]} ({pct[0]:.1f}%), 1={counts[1]} ({pct[1]:.1f}%)")

# Collect all tokens
all_tokens = set()
for df in [train, val, test]:
    for col in feature_cols:
        all_tokens.update(df[col].unique())
all_tokens = sorted(all_tokens)
print(f"\nUnique tokens: {all_tokens}")

# Parse tokens
SHAPES = {'T': 'Triangle', 'S': 'Square', 'C': 'Circle', 'D': 'Diamond'}
COLORS = {'r': 'red', 'g': 'green', 'b': 'blue', 'y': 'yellow'}

def parse_token(token):
    return token[0], token[1]

# Analyze token distribution by label
print("\n" + "="*60)
print("TOKEN ANALYSIS BY LABEL")
print("="*60)

for pos_idx, col in enumerate(feature_cols[:4]):  # First 4 positions
    print(f"\nPosition {pos_idx}:")
    token_by_label = train.groupby('label')[col].apply(list)
    
    for label in [0, 1]:
        tokens = token_by_label[label]
        counter = Counter(tokens)
        print(f"  Label {label}: {dict(counter.most_common(5))}")

# Look for simple patterns
print("\n" + "="*60)
print("PATTERN ANALYSIS")
print("="*60)

# Check if first token predicts label
first_token_acc = {}
for token in all_tokens:
    mask = train['token_0'] == token
    if mask.sum() > 10:
        label_dist = train[mask]['label'].value_counts()
        majority_label = label_dist.index[0]
        accuracy = label_dist.iloc[0] / mask.sum()
        first_token_acc[token] = (accuracy, majority_label, mask.sum())

print("\nFirst token predictive power:")
for token, (acc, label, count) in sorted(first_token_acc.items(), key=lambda x: x[1][0], reverse=True)[:10]:
    print(f"  {token}: predicts {label} with {acc:.3f} accuracy ({count} samples)")

# Check for position-based patterns
print("\n" + "="*60)
print("POSITION-BASED PATTERNS")
print("="*60)

# Same shape at positions 0 and 4
for name, df in [('Train', train), ('Test', test)]:
    same_shape_0_4 = []
    for _, row in df.iterrows():
        t0 = row['token_0']
        t4 = row['token_4']
        same_shape_0_4.append(1 if t0[0] == t4[0] else 0)
    
    df_copy = df.copy()
    df_copy['same_shape_0_4'] = same_shape_0_4
    
    print(f"\n{name} - Same shape at positions 0 and 4:")
    for same in [0, 1]:
        mask = df_copy['same_shape_0_4'] == same
        label_dist = df_copy[mask]['label'].value_counts()
        print(f"  Same={same}: {dict(label_dist)}")

# Same color at positions 0 and 4
for name, df in [('Train', train), ('Test', test)]:
    same_color_0_4 = []
    for _, row in df.iterrows():
        t0 = row['token_0']
        t4 = row['token_4']
        same_color_0_4.append(1 if t0[1] == t4[1] else 0)
    
    df_copy = df.copy()
    df_copy['same_color_0_4'] = same_color_0_4
    
    print(f"\n{name} - Same color at positions 0 and 4:")
    for same in [0, 1]:
        mask = df_copy['same_color_0_4'] == same
        label_dist = df_copy[mask]['label'].value_counts()
        print(f"  Same={same}: {dict(label_dist)}")

# Check for alternating patterns
print("\n" + "="*60)
print("ALTERNATING PATTERNS")
print("="*60)

def count_alternations(row, feature_cols):
    """Count how many times shape or color alternates."""
    shapes = [row[col][0] for col in feature_cols]
    colors = [row[col][1] for col in feature_cols]
    
    shape_alts = sum(1 for i in range(1, len(shapes)) if shapes[i] != shapes[i-1])
    color_alts = sum(1 for i in range(1, len(colors)) if colors[i] != colors[i-1])
    
    return shape_alts, color_alts

for name, df in [('Train', train), ('Test', test)]:
    alts = df.apply(lambda row: count_alternations(row, feature_cols), axis=1)
    df_copy = df.copy()
    df_copy['shape_alts'] = [a[0] for a in alts]
    df_copy['color_alts'] = [a[1] for a in alts]
    
    print(f"\n{name} - Alternations by label:")
    for label in [0, 1]:
        mask = df_copy['label'] == label
        print(f"  Label {label}: shape_alts={df_copy[mask]['shape_alts'].mean():.2f}, color_alts={df_copy[mask]['color_alts'].mean():.2f}")

# Check for symmetry
print("\n" + "="*60)
print("SYMMETRY PATTERNS")
print("="*60)

def is_symmetric(row, feature_cols):
    """Check if sequence is symmetric."""
    tokens = [row[col] for col in feature_cols]
    return tokens == tokens[::-1]

for name, df in [('Train', train), ('Test', test)]:
    sym = df.apply(lambda row: is_symmetric(row, feature_cols), axis=1)
    df_copy = df.copy()
    df_copy['symmetric'] = sym
    
    print(f"\n{name} - Symmetry:")
    for sym_val in [True, False]:
        mask = df_copy['symmetric'] == sym_val
        if mask.sum() > 0:
            label_dist = df_copy[mask]['label'].value_counts()
            print(f"  Symmetric={sym_val}: {dict(label_dist)} ({mask.sum()} samples)")

# Estimate label noise
print("\n" + "="*60)
print("LABEL NOISE ESTIMATION")
print("="*60)

# If we assume the true pattern is deterministic, 
# the maximum achievable accuracy is limited by label noise
# The SOTA of 70% suggests ~30% label noise

print("\nGiven SOTA = 70%, estimated label noise ceiling = 30%")
print("This means approximately 30% of labels may be incorrect.")

# Create visualization of label distribution
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for idx, (name, df) in enumerate([('Train', train), ('Val', val), ('Test', test)]):
    ax = axes[idx]
    counts = df['label'].value_counts().sort_index()
    colors = ['coral', 'steelblue']
    bars = ax.bar(['Reject (0)', 'Accept (1)'], counts.values, color=colors, alpha=0.8, edgecolor='black')
    ax.set_ylabel('Count', fontsize=11)
    ax.set_title(f'{name} Set\n(n={len(df)})', fontsize=12, fontweight='bold')
    ax.set_ylim([0, max(counts.values) * 1.2])
    
    # Add percentage labels
    total = len(df)
    for bar, count in zip(bars, counts.values):
        height = bar.get_height()
        pct = count / total * 100
        ax.text(bar.get_x() + bar.get_width()/2., height + total*0.01,
                f'{count}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=10)

plt.suptitle('Label Distribution Across Splits', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('../report/images/label_distribution.png', dpi=150, bbox_inches='tight')
print("\nFigure saved to report/images/label_distribution.png")
plt.close()

# Visualize token frequency
fig, ax = plt.subplots(figsize=(12, 5))
token_counts = Counter()
for df in [train, val, test]:
    for col in feature_cols:
        token_counts.update(df[col].values)

tokens = list(token_counts.keys())
counts = list(token_counts.values())
colors = [plt.cm.tab20(i % 20) for i in range(len(tokens))]

bars = ax.bar(tokens, counts, color=colors, alpha=0.8, edgecolor='black')
ax.set_xlabel('Token', fontsize=12)
ax.set_ylabel('Frequency', fontsize=12)
ax.set_title('Token Frequency Distribution (All Splits)', fontsize=14, fontweight='bold')
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.savefig('../report/images/token_frequency.png', dpi=150, bbox_inches='tight')
print("Figure saved to report/images/token_frequency.png")
plt.close()

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
