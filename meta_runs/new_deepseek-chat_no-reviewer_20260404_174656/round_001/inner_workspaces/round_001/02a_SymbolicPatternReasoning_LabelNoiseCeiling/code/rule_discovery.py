import pandas as pd
import numpy as np
from itertools import combinations, product

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train = train[feature_cols]
y_train = train['label']

print("Analyzing data for rule discovery...")
print(f"Train shape: {train.shape}")

# Let's check if the rule depends on specific token patterns
# Since we have 8 positions, maybe the rule is something like:
# "If token at position X is A and token at position Y is B, then accept"

# Check all pairs of positions for conjunction rules
print("\n=== Checking conjunction rules (position X = A AND position Y = B) ===")

shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']

best_rules = []

# Check single position rules first
for pos in range(8):
    col = feature_cols[pos]
    for shape in shapes:
        for color in colors:
            token = shape + color
            mask = X_train[col] == token
            if mask.sum() > 20:  # Enough samples
                accuracy = y_train[mask].mean()
                # Check if this rule is predictive
                if abs(accuracy - 0.5) > 0.15:  # Significant deviation from random
                    rule_str = f"{col} = {token}"
                    coverage = mask.mean()
                    best_rules.append({
                        'rule': rule_str,
                        'accuracy': accuracy,
                        'coverage': coverage,
                        'type': 'single'
                    })

# Check two-position conjunction rules
print("Checking two-position rules...")
for pos1, pos2 in combinations(range(8), 2):
    col1 = feature_cols[pos1]
    col2 = feature_cols[pos2]
    
    # Sample some token combinations (full 16x16=256 is too many)
    tokens1 = X_train[col1].value_counts().head(5).index.tolist()
    tokens2 = X_train[col2].value_counts().head(5).index.tolist()
    
    for token1 in tokens1:
        for token2 in tokens2:
            mask = (X_train[col1] == token1) & (X_train[col2] == token2)
            if mask.sum() > 10:  # Enough samples
                accuracy = y_train[mask].mean()
                if abs(accuracy - 0.5) > 0.2:  # Strong deviation
                    rule_str = f"{col1} = {token1} AND {col2} = {token2}"
                    coverage = mask.mean()
                    best_rules.append({
                        'rule': rule_str,
                        'accuracy': accuracy,
                        'coverage': coverage,
                        'type': 'conjunction'
                    })

# Sort rules by predictive power (distance from 0.5)
best_rules.sort(key=lambda x: abs(x['accuracy'] - 0.5), reverse=True)

print(f"\nTop 20 most predictive rules:")
for i, rule_info in enumerate(best_rules[:20]):
    print(f"{i+1:2d}. {rule_info['rule']:40s} acc={rule_info['accuracy']:.3f}, cov={rule_info['coverage']:.3f}")

# Try to combine rules into a simple classifier
print("\n=== Building simple rule-based classifier ===")
if best_rules:
    # Use the top rule
    best_rule = best_rules[0]
    print(f"Using rule: {best_rule['rule']}")
    
    # Parse the rule
    if best_rule['type'] == 'single':
        # Parse "token_X = AB"
        parts = best_rule['rule'].split('=')
        col = parts[0].strip()
        token = parts[1].strip()
        
        # Apply to train, val, test
        train_pred = (X_train[col] == token).astype(int)
        val_pred = (val[col] == token).astype(int)
        test_pred = (test[col] == token).astype(int)
        
        # If accuracy < 0.5, flip predictions
        if best_rule['accuracy'] < 0.5:
            train_pred = 1 - train_pred
            val_pred = 1 - val_pred
            test_pred = 1 - test_pred
            
    elif best_rule['type'] == 'conjunction':
        # Parse "token_X = AB AND token_Y = CD"
        parts = best_rule['rule'].split('AND')
        part1 = parts[0].strip()
        part2 = parts[1].strip()
        
        col1, token1 = part1.split('=')
        col2, token2 = part2.split('=')
        col1 = col1.strip()
        token1 = token1.strip()
        col2 = col2.strip()
        token2 = token2.strip()
        
        # Apply to train, val, test
        train_pred = ((X_train[col1] == token1) & (X_train[col2] == token2)).astype(int)
        val_pred = ((val[col1] == token1) & (val[col2] == token2)).astype(int)
        test_pred = ((test[col1] == token1) & (test[col2] == token2)).astype(int)
        
        # If accuracy < 0.5, flip predictions
        if best_rule['accuracy'] < 0.5:
            train_pred = 1 - train_pred
            val_pred = 1 - val_pred
            test_pred = 1 - test_pred
    
    # Calculate accuracies
    from sklearn.metrics import accuracy_score
    
    train_acc = accuracy_score(y_train, train_pred)
    val_acc = accuracy_score(val['label'], val_pred)
    test_acc = accuracy_score(test['label'], test_pred)
    
    print(f"Train accuracy: {train_acc:.4f}")
    print(f"Val accuracy: {val_acc:.4f}")
    print(f"Test accuracy: {test_acc:.4f}")
    
    sota = 0.70
    print(f"\nSOTA baseline: {sota:.4f}")
    print(f"Rule-based vs SOTA: {test_acc:.4f} vs {sota:.4f}")
    
    if test_acc > sota:
        print("SUCCESS: Rule-based classifier exceeds SOTA!")
    else:
        print("Rule-based classifier does not exceed SOTA.")

# Check for more complex patterns
print("\n=== Checking for sequential patterns ===")
# Maybe the rule involves the entire sequence pattern
# Let's check if certain sequences of shapes or colors are predictive

# Convert to shapes and colors
shapes_train = X_train.applymap(lambda x: x[0])
colors_train = X_train.applymap(lambda x: x[1])

# Check shape sequences
print("Checking common shape sequences...")
shape_sequences = shapes_train.apply(lambda row: ''.join(row.values), axis=1)
top_shape_seqs = shape_sequences.value_counts().head(10)

print("Top 10 shape sequences and their label rates:")
for seq, count in top_shape_seqs.items():
    if count > 5:
        mask = shape_sequences == seq
        label_rate = y_train[mask].mean()
        print(f"  {seq}: count={count}, label rate={label_rate:.3f}")

# Check color sequences
print("\nChecking common color sequences...")
color_sequences = colors_train.apply(lambda row: ''.join(row.values), axis=1)
top_color_seqs = color_sequences.value_counts().head(10)

print("Top 10 color sequences and their label rates:")
for seq, count in top_color_seqs.items():
    if count > 5:
        mask = color_sequences == seq
        label_rate = y_train[mask].mean()
        print(f"  {seq}: count={count}, label rate={label_rate:.3f}")