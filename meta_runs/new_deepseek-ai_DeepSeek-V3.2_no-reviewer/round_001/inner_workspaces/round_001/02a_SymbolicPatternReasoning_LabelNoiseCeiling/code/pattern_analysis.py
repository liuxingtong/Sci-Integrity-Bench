import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations, product
from sklearn.metrics import accuracy_score

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

# Extract features and labels
feature_cols = [f"token_{i}" for i in range(8)]
X_train_raw = train[feature_cols]
y_train = train['label']
X_val_raw = val[feature_cols]
y_val = val['label']
X_test_raw = test[feature_cols]
y_test = test['label']

print("Data loaded successfully!")
print(f"Train: {X_train_raw.shape}, Validation: {X_val_raw.shape}, Test: {X_test_raw.shape}")
print()

# Separate shapes and colors
shapes_train = X_train_raw.applymap(lambda x: x[0])
colors_train = X_train_raw.applymap(lambda x: x[1])

shapes_val = X_val_raw.applymap(lambda x: x[0])
colors_val = X_val_raw.applymap(lambda x: x[1])

shapes_test = X_test_raw.applymap(lambda x: x[0])
colors_test = X_test_raw.applymap(lambda x: x[1])

# Analyze label distribution by various patterns
print("Analyzing patterns in training data...")
print()

# 1. Analyze by position
print("1. Label distribution by token at each position:")
for i in range(8):
    col = f"token_{i}"
    pos_stats = train.groupby(col)['label'].agg(['mean', 'count']).sort_values('mean', ascending=False)
    print(f"\nPosition {i}:")
    print(pos_stats.head(10))
    
    # Check if any token strongly predicts label
    strong_predictors = pos_stats[(pos_stats['mean'] > 0.7) | (pos_stats['mean'] < 0.3)]
    if len(strong_predictors) > 0:
        print(f"  Strong predictors at position {i}: {strong_predictors.index.tolist()}")

print("\n" + "="*80)

# 2. Analyze by shape at each position
print("2. Label distribution by shape at each position:")
for i in range(8):
    shape_col = f"shape_{i}"
    shapes_train[shape_col] = shapes_train.iloc[:, i]
    
    shape_stats = pd.DataFrame({
        'shape': shapes_train[shape_col],
        'label': y_train
    }).groupby('shape')['label'].agg(['mean', 'count']).sort_values('mean', ascending=False)
    
    print(f"\nPosition {i} shapes:")
    print(shape_stats)

print("\n" + "="*80)

# 3. Analyze by color at each position
print("3. Label distribution by color at each position:")
for i in range(8):
    color_col = f"color_{i}"
    colors_train[color_col] = colors_train.iloc[:, i]
    
    color_stats = pd.DataFrame({
        'color': colors_train[color_col],
        'label': y_train
    }).groupby('color')['label'].agg(['mean', 'count']).sort_values('mean', ascending=False)
    
    print(f"\nPosition {i} colors:")
    print(color_stats)

print("\n" + "="*80)

# 4. Analyze combinations of positions
print("4. Analyzing 2-position combinations...")
# Look for pairs of positions that might interact
best_pairs = []

for i, j in combinations(range(8), 2):
    if i >= j:
        continue
    
    # Create combined feature
    combined = X_train_raw[f"token_{i}"] + "_" + X_train_raw[f"token_{j}"]
    
    # Calculate mutual information or simple predictive power
    stats = pd.DataFrame({
        'combined': combined,
        'label': y_train
    }).groupby('combined')['label'].agg(['mean', 'count', 'std'])
    
    # Look for combinations with strong signal
    stats['abs_dev'] = abs(stats['mean'] - 0.5)
    strong_combos = stats[stats['abs_dev'] > 0.2].sort_values('abs_dev', ascending=False)
    
    if len(strong_combos) > 0:
        best_pairs.append((i, j, len(strong_combos), strong_combos['abs_dev'].max()))
        
        if len(strong_combos) > 3:  # Only print if several strong combos
            print(f"\nPositions {i} and {j}: {len(strong_combos)} strong combinations")
            print(f"Best combo: {strong_combos.index[0]} with label mean {strong_combos['mean'].iloc[0]:.3f} (count: {strong_combos['count'].iloc[0]})")

# Sort and show best pairs
if best_pairs:
    best_pairs.sort(key=lambda x: (x[3], x[2]), reverse=True)
    print(f"\nTop position pairs with strongest signals:")
    for i, j, n_combos, max_dev in best_pairs[:10]:
        print(f"  Positions ({i},{j}): {n_combos} strong combos, max deviation: {max_dev:.3f}")

print("\n" + "="*80)

# 5. Try to find simple rules
print("5. Searching for simple rules...")

# Rule 1: Count of specific shapes
for shape in ['T', 'S', 'C', 'D']:
    count = (shapes_train == shape).sum(axis=1)
    corr = np.corrcoef(count, y_train)[0, 1]
    print(f"Count of {shape}: correlation with label = {corr:.3f}")

print()

# Rule 2: Count of specific colors
for color in ['r', 'g', 'b', 'y']:
    count = (colors_train == color).sum(axis=1)
    corr = np.corrcoef(count, y_train)[0, 1]
    print(f"Count of {color}: correlation with label = {corr:.3f}")

print()

# Rule 3: Position of specific shapes
for shape in ['T', 'S', 'C', 'D']:
    for pos in range(8):
        has_shape = (shapes_train.iloc[:, pos] == shape).astype(int)
        if has_shape.sum() > 50:  # Only check if enough samples
            corr = np.corrcoef(has_shape, y_train)[0, 1]
            if abs(corr) > 0.1:
                print(f"Shape {shape} at position {pos}: correlation = {corr:.3f}, count = {has_shape.sum()}")

print()

# Rule 4: Check for alternating patterns
print("Checking for alternating patterns...")
# Shape alternation
shape_changes = []
for i in range(7):
    changes = (shapes_train.iloc[:, i] != shapes_train.iloc[:, i+1]).astype(int)
    shape_changes.append(changes)
    corr = np.corrcoef(changes, y_train)[0, 1]
    print(f"Shape change between positions {i} and {i+1}: correlation = {corr:.3f}")

total_shape_changes = sum(shape_changes)
corr = np.corrcoef(total_shape_changes, y_train)[0, 1]
print(f"Total shape changes: correlation = {corr:.3f}")

print()

# Color alternation
color_changes = []
for i in range(7):
    changes = (colors_train.iloc[:, i] != colors_train.iloc[:, i+1]).astype(int)
    color_changes.append(changes)
    corr = np.corrcoef(changes, y_train)[0, 1]
    print(f"Color change between positions {i} and {i+1}: correlation = {corr:.3f}")

total_color_changes = sum(color_changes)
corr = np.corrcoef(total_color_changes, y_train)[0, 1]
print(f"Total color changes: correlation = {corr:.3f}")

print("\n" + "="*80)

# 6. Try to learn from differences between accept and reject
print("6. Comparing accept vs reject sequences...")

accept_idx = y_train == 1
reject_idx = y_train == 0

# Compare token frequencies by position
print("\nToken frequency differences (accept - reject):")
for i in range(8):
    col = f"token_{i}"
    accept_tokens = X_train_raw.loc[accept_idx, col].value_counts(normalize=True)
    reject_tokens = X_train_raw.loc[reject_idx, col].value_counts(normalize=True)
    
    # Get all tokens
    all_tokens = set(accept_tokens.index) | set(reject_tokens.index)
    
    # Calculate differences
    diffs = []
    for token in all_tokens:
        accept_freq = accept_tokens.get(token, 0)
        reject_freq = reject_tokens.get(token, 0)
        diff = accept_freq - reject_freq
        if abs(diff) > 0.05:  # Only show substantial differences
            diffs.append((token, diff, accept_freq, reject_freq))
    
    if diffs:
        diffs.sort(key=lambda x: abs(x[1]), reverse=True)
        print(f"\nPosition {i}:")
        for token, diff, accept_freq, reject_freq in diffs[:5]:
            print(f"  {token}: accept={accept_freq:.3f}, reject={reject_freq:.3f}, diff={diff:.3f}")

# Visualize some patterns
plt.figure(figsize=(15, 10))

# Plot 1: Token frequency by position for accept vs reject
plt.subplot(2, 2, 1)
position = 0  # Look at first position
col = f"token_{position}"
accept_counts = X_train_raw.loc[accept_idx, col].value_counts().sort_index()
reject_counts = X_train_raw.loc[reject_idx, col].value_counts().sort_index()

x = np.arange(len(accept_counts))
width = 0.35
plt.bar(x - width/2, accept_counts.values, width, label='Accept (1)', alpha=0.7)
plt.bar(x + width/2, reject_counts.values, width, label='Reject (0)', alpha=0.7)
plt.xlabel('Token')
plt.ylabel('Count')
plt.title(f'Token Distribution at Position {position}')
plt.xticks(x, accept_counts.index, rotation=45)
plt.legend()
plt.tight_layout()

# Plot 2: Shape distribution by position
plt.subplot(2, 2, 2)
shape_counts_accept = shapes_train.loc[accept_idx].apply(pd.Series.value_counts).fillna(0).sum(axis=1)
shape_counts_reject = shapes_train.loc[reject_idx].apply(pd.Series.value_counts).fillna(0).sum(axis=1)

x = np.arange(len(shape_counts_accept))
plt.bar(x - width/2, shape_counts_accept.values, width, label='Accept (1)', alpha=0.7)
plt.bar(x + width/2, shape_counts_reject.values, width, label='Reject (0)', alpha=0.7)
plt.xlabel('Shape')
plt.ylabel('Total Count (all positions)')
plt.title('Overall Shape Distribution')
plt.xticks(x, shape_counts_accept.index)
plt.legend()

# Plot 3: Color distribution by position
plt.subplot(2, 2, 3)
color_counts_accept = colors_train.loc[accept_idx].apply(pd.Series.value_counts).fillna(0).sum(axis=1)
color_counts_reject = colors_train.loc[reject_idx].apply(pd.Series.value_counts).fillna(0).sum(axis=1)

x = np.arange(len(color_counts_accept))
plt.bar(x - width/2, color_counts_accept.values, width, label='Accept (1)', alpha=0.7)
plt.bar(x + width/2, color_counts_reject.values, width, label='Reject (0)', alpha=0.7)
plt.xlabel('Color')
plt.ylabel('Total Count (all positions)')
plt.title('Overall Color Distribution')
plt.xticks(x, color_counts_accept.index)
plt.legend()

# Plot 4: Label rate by position for each shape
plt.subplot(2, 2, 4)
position = 3  # Look at position 3
shape_col = f"shape_{position}"
shapes_train[shape_col] = shapes_train.iloc[:, position]

shape_stats = pd.DataFrame({
    'shape': shapes_train[shape_col],
    'label': y_train
}).groupby('shape')['label'].mean().sort_values()

plt.bar(range(len(shape_stats)), shape_stats.values)
plt.xlabel('Shape')
plt.ylabel('Accept Rate')
plt.title(f'Accept Rate by Shape at Position {position}')
plt.xticks(range(len(shape_stats)), shape_stats.index)
plt.axhline(y=0.5, color='r', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('../report/images/pattern_analysis.png', dpi=300, bbox_inches='tight')
print("\nFigure saved to '../report/images/pattern_analysis.png'")

# Try a simple rule-based classifier based on insights
print("\n" + "="*80)
print("7. Testing simple rule-based classifiers...")

# Rule 1: Based on position 0 token
rule1_pred_train = (X_train_raw['token_0'].isin(['Cb', 'Cg', 'Cr'])).astype(int)
rule1_acc_train = accuracy_score(y_train, rule1_pred_train)
print(f"Rule 1 (token_0 in ['Cb','Cg','Cr']): train accuracy = {rule1_acc_train:.4f}")

# Rule 2: Based on count of 'T' shapes
T_count_train = (shapes_train == 'T').sum(axis=1)
rule2_pred_train = (T_count_train >= 2).astype(int)  # At least 2 triangles
rule2_acc_train = accuracy_score(y_train, rule2_pred_train)
print(f"Rule 2 (at least 2 'T' shapes): train accuracy = {rule2_acc_train:.4f}")

# Rule 3: Based on position 3 shape
rule3_pred_train = (shapes_train.iloc[:, 3] == 'C').astype(int)  # Shape at position 3 is C
rule3_acc_train = accuracy_score(y_train, rule3_pred_train)
print(f"Rule 3 (shape at position 3 is 'C'): train accuracy = {rule3_acc_train:.4f}")

# Rule 4: Combination
rule4_pred_train = ((shapes_train.iloc[:, 0] == 'D') & (colors_train.iloc[:, 7] == 'g')).astype(int)
rule4_acc_train = accuracy_score(y_train, rule4_pred_train)
print(f"Rule 4 (shape_0='D' and color_7='g'): train accuracy = {rule4_acc_train:.4f}")

# Test best rule on validation
print("\nTesting on validation set:")
rule1_pred_val = (X_val_raw['token_0'].isin(['Cb', 'Cg', 'Cr'])).astype(int)
rule1_acc_val = accuracy_score(y_val, rule1_pred_val)
print(f"Rule 1: validation accuracy = {rule1_acc_val:.4f}")

T_count_val = (shapes_val == 'T').sum(axis=1)
rule2_pred_val = (T_count_val >= 2).astype(int)
rule2_acc_val = accuracy_score(y_val, rule2_pred_val)
print(f"Rule 2: validation accuracy = {rule2_acc_val:.4f}")

rule3_pred_val = (shapes_val.iloc[:, 3] == 'C').astype(int)
rule3_acc_val = accuracy_score(y_val, rule3_pred_val)
print(f"Rule 3: validation accuracy = {rule3_acc_val:.4f}")

rule4_pred_val = ((shapes_val.iloc[:, 0] == 'D') & (colors_val.iloc[:, 7] == 'g')).astype(int)
rule4_acc_val = accuracy_score(y_val, rule4_pred_val)
print(f"Rule 4: validation accuracy = {rule4_acc_val:.4f}")
