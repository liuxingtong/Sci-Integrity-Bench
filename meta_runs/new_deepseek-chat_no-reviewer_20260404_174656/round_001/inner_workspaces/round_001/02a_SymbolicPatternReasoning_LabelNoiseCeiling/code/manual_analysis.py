import pandas as pd
import numpy as np

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train = train[feature_cols]
y_train = train['label']

print("Manual analysis of patterns...")
print(f"Training samples: {len(train)}")

# Look at examples of each class
print("\n=== Examples of class 1 (accept) ===")
class1_examples = train[train['label'] == 1].head(10)
for idx, row in class1_examples.iterrows():
    tokens = [row[col] for col in feature_cols]
    print(f"{idx:4d}: {' '.join(tokens)}")

print("\n=== Examples of class 0 (reject) ===")
class0_examples = train[train['label'] == 0].head(10)
for idx, row in class0_examples.iterrows():
    tokens = [row[col] for col in feature_cols]
    print(f"{idx:4d}: {' '.join(tokens)}")

# Try to find patterns
print("\n=== Looking for patterns ===")

# Check if specific patterns appear in one class but not the other
# Look at shape sequences
print("\nShape sequences for first 5 examples of each class:")
print("Class 1:")
for idx, row in class1_examples.iterrows():
    shapes = ''.join([row[col][0] for col in feature_cols])
    print(f"  {shapes}")

print("\nClass 0:")
for idx, row in class0_examples.iterrows():
    shapes = ''.join([row[col][0] for col in feature_cols])
    print(f"  {shapes}")

# Check color sequences
print("\nColor sequences for first 5 examples of each class:")
print("Class 1:")
for idx, row in class1_examples.iterrows():
    colors = ''.join([row[col][1] for col in feature_cols])
    print(f"  {colors}")

print("\nClass 0:")
for idx, row in class0_examples.iterrows():
    colors = ''.join([row[col][1] for col in feature_cols])
    print(f"  {colors}")

# Check for positional patterns
print("\n=== Checking positional patterns ===")
print("Looking at position 0 (first token):")
pos0_class1 = class1_examples[feature_cols[0]].value_counts().head(5)
pos0_class0 = class0_examples[feature_cols[0]].value_counts().head(5)

print(f"Class 1 most common at position 0: {pos0_class1.index.tolist()}")
print(f"Class 0 most common at position 0: {pos0_class0.index.tolist()}")

# Check if there's a simple rule like "if token contains 'r' at any position"
print("\n=== Checking for simple token patterns ===")

# Check for presence of specific shapes/colors
for shape in ['T', 'S', 'C', 'D']:
    for color in ['r', 'g', 'b', 'y']:
        token = shape + color
        
        # Check if this token appears in sequences
        token_present = X_train.apply(lambda row: any(row[col] == token for col in feature_cols), axis=1)
        
        class1_with_token = y_train[token_present].mean()
        class0_with_token = 1 - class1_with_token
        
        if abs(class1_with_token - 0.5) > 0.1:
            print(f"Token {token}: class 1 rate = {class1_with_token:.3f}")

# Check for patterns in transitions
print("\n=== Checking transition patterns ===")
# Look at shape transitions
print("Common shape transitions in class 1:")
shape_transitions_class1 = []
for idx, row in class1_examples.iterrows():
    shapes = [row[col][0] for col in feature_cols]
    for i in range(len(shapes)-1):
        shape_transitions_class1.append(shapes[i] + '->' + shapes[i+1])

from collections import Counter
trans_counts_class1 = Counter(shape_transitions_class1)
print(f"Top shape transitions in class 1: {trans_counts_class1.most_common(5)}")

print("\nCommon shape transitions in class 0:")
shape_transitions_class0 = []
for idx, row in class0_examples.iterrows():
    shapes = [row[col][0] for col in feature_cols]
    for i in range(len(shapes)-1):
        shape_transitions_class0.append(shapes[i] + '->' + shapes[i+1])

trans_counts_class0 = Counter(shape_transitions_class0)
print(f"Top shape transitions in class 0: {trans_counts_class0.most_common(5)}")

# Try to guess a rule
print("\n=== Trying to guess the rule ===")
print("Based on manual inspection, some observations:")
print("1. No obvious single-token or single-position rule")
print("2. Shape and color sequences look random in both classes")
print("3. Transitions also look similar between classes")
print("4. This suggests a complex rule or noisy labels")

# Check if rule might be about relationships between positions
print("\nChecking if rule might be about position relationships:")
print("Example: 'If position 0 shape equals position 4 shape, then accept'")

rule_predictions = (X_train[feature_cols[0]].str[0] == X_train[feature_cols[4]].str[0]).astype(int)
rule_accuracy = (rule_predictions == y_train).mean()
print(f"Rule 'pos0_shape == pos4_shape': accuracy = {rule_accuracy:.3f}")

# Try a few more
rules_to_test = [
    ("pos0_shape == pos7_shape", X_train[feature_cols[0]].str[0] == X_train[feature_cols[7]].str[0]),
    ("pos0_color == pos4_color", X_train[feature_cols[0]].str[1] == X_train[feature_cols[4]].str[1]),
    ("pos1_shape == pos5_shape", X_train[feature_cols[1]].str[0] == X_train[feature_cols[5]].str[0]),
    ("pos2_color == pos6_color", X_train[feature_cols[2]].str[1] == X_train[feature_cols[6]].str[1]),
    ("count(T) > count(S)", X_train.apply(lambda row: sum(1 for col in feature_cols if row[col][0] == 'T'), axis=1) > \
                           X_train.apply(lambda row: sum(1 for col in feature_cols if row[col][0] == 'S'), axis=1)),
    ("more red than blue", X_train.apply(lambda row: sum(1 for col in feature_cols if row[col][1] == 'r'), axis=1) > \
                          X_train.apply(lambda row: sum(1 for col in feature_cols if row[col][1] == 'b'), axis=1)),
]

print("\nTesting simple rules:")
for rule_name, rule_mask in rules_to_test:
    predictions = rule_mask.astype(int)
    accuracy = (predictions == y_train).mean()
    # Also check flipped version
    flipped_accuracy = ((1 - predictions) == y_train).mean()
    best_accuracy = max(accuracy, flipped_accuracy)
    print(f"  {rule_name:30s}: accuracy = {accuracy:.3f}, flipped = {flipped_accuracy:.3f}, best = {best_accuracy:.3f}")