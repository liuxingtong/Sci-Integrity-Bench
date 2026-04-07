import pandas as pd
import numpy as np
from collections import Counter
import itertools

# Load all data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

print("Deep analysis of SPR_BENCH data\n")
print("="*60)

# 1. Check if sequences are unique
all_sequences = []
for df in [train, val, test]:
    for idx, row in df.iterrows():
        seq = tuple(row[col] for col in feature_cols)
        all_sequences.append(seq)

unique_sequences = set(all_sequences)
print(f"Total sequences: {len(all_sequences)}")
print(f"Unique sequences: {len(unique_sequences)}")
print(f"Duplicate sequences: {len(all_sequences) - len(unique_sequences)}")

# Check if any sequence appears with different labels
seq_to_labels = {}
for df, name in [(train, 'train'), (val, 'val'), (test, 'test')]:
    for idx, row in df.iterrows():
        seq = tuple(row[col] for col in feature_cols)
        label = row['label']
        if seq not in seq_to_labels:
            seq_to_labels[seq] = []
        seq_to_labels[seq].append((name, label))

conflicting = []
for seq, labels in seq_to_labels.items():
    unique_labels = set(label for _, label in labels)
    if len(unique_labels) > 1:
        conflicting.append((seq, labels))

print(f"\nSequences with conflicting labels: {len(conflicting)}")
if conflicting:
    print("First few conflicts:")
    for seq, labels in conflicting[:3]:
        print(f"  Sequence: {seq}")
        print(f"  Labels: {labels}")

# 2. Analyze rule patterns
print("\n" + "="*60)
print("Analyzing potential rules...")

# Try to find deterministic rules
possible_rules = []

# Rule type 1: Specific token at specific position always gives same label
for pos in range(8):
    col = f'token_{pos}'
    token_to_labels = {}
    for label in [0, 1]:
        subset = train[train['label'] == label]
        for token in subset[col].unique():
            if token not in token_to_labels:
                token_to_labels[token] = []
            token_to_labels[token].append(label)
    
    # Check for tokens that always have same label
    for token, labels in token_to_labels.items():
        if len(set(labels)) == 1:
            label = list(set(labels))[0]
            count = sum(1 for x in train[col] if x == token)
            possible_rules.append((f'token_{pos}={token}', label, count, count/len(train)))

print(f"\nPosition-specific token rules: {len(possible_rules)}")
if possible_rules:
    print("Top rules by coverage:")
    possible_rules.sort(key=lambda x: x[2], reverse=True)
    for rule, label, count, coverage in possible_rules[:10]:
        print(f"  {rule} -> {label} (covers {count} samples, {coverage:.1%})")

# Rule type 2: Pattern of shapes or colors
print("\nChecking shape/color patterns...")

# Convert to shape and color sequences
def get_shape_color_sequences(df):
    shape_seqs = []
    color_seqs = []
    for idx, row in df.iterrows():
        shape_seq = ''.join([token[0] for token in [row[col] for col in feature_cols]])
        color_seq = ''.join([token[1] for token in [row[col] for col in feature_cols]])
        shape_seqs.append(shape_seq)
        color_seqs.append(color_seq)
    return shape_seqs, color_seqs

train_shape_seqs, train_color_seqs = get_shape_color_sequences(train)

# Check if specific shape sequences predict label
shape_seq_to_labels = {}
for i, seq in enumerate(train_shape_seqs):
    label = train.iloc[i]['label']
    if seq not in shape_seq_to_labels:
        shape_seq_to_labels[seq] = []
    shape_seq_to_labels[seq].append(label)

consistent_shape_seqs = []
for seq, labels in shape_seq_to_labels.items():
    if len(set(labels)) == 1:
        label = list(set(labels))[0]
        count = len(labels)
        consistent_shape_seqs.append((seq, label, count))

print(f"Consistent shape sequences: {len(consistent_shape_seqs)} (out of {len(set(train_shape_seqs))} unique)")
if consistent_shape_seqs:
    consistent_shape_seqs.sort(key=lambda x: x[2], reverse=True)
    print("Top consistent shape sequences:")
    for seq, label, count in consistent_shape_seqs[:5]:
        print(f"  {seq} -> {label} ({count} samples)")

# 3. Check if labels are actually random
print("\n" + "="*60)
print("Statistical analysis of labels...")

# Permutation test: if we shuffle labels, what accuracy do we get?
n_permutations = 100
accuracies = []

for _ in range(n_permutations):
    # Shuffle labels
    shuffled_labels = train['label'].sample(frac=1, random_state=_).values
    # Simple majority classifier
    majority = 1 if shuffled_labels.mean() > 0.5 else 0
    acc = max(shuffled_labels.mean(), 1 - shuffled_labels.mean())
    accuracies.append(acc)

print(f"Expected accuracy from random labels: {np.mean(accuracies):.3f} ± {np.std(accuracies):.3f}")
print(f"Actual label distribution: {train['label'].mean():.3f} label=1")

# 4. Try to learn a simple decision tree to see what features it uses
print("\n" + "="*60)
print("Training simple decision tree to understand features...")

from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.preprocessing import LabelEncoder

# Encode tokens as integers
le = LabelEncoder()
all_tokens = pd.concat([train[feature_cols], val[feature_cols], test[feature_cols]]).values.ravel()
le.fit(all_tokens)

X_train_encoded = train[feature_cols].apply(lambda col: le.transform(col))
y_train = train['label']

# Train shallow tree
tree = DecisionTreeClassifier(max_depth=3, random_state=42)
tree.fit(X_train_encoded, y_train)

# Get feature importance
importance = tree.feature_importances_
print("\nFeature importance from decision tree:")
for i, imp in enumerate(importance):
    if imp > 0:
        print(f"  token_{i}: {imp:.3f}")

# Try to interpret the tree
print("\nDecision tree structure (simplified):")
tree_rules = export_text(tree, feature_names=[f'token_{i}' for i in range(8)])
print(tree_rules)

# 5. Check if there's a simple parity or counting rule
print("\n" + "="*60)
print("Testing simple counting rules...")

# Test various counting rules
rules_to_test = [
    ("Count of T shapes > 2", lambda seq: sum(1 for token in seq if token[0] == 'T') > 2),
    ("Count of red colors > 2", lambda seq: sum(1 for token in seq if token[1] == 'r') > 2),
    ("Has duplicate consecutive tokens", lambda seq: any(seq[i] == seq[i+1] for i in range(7))),
    ("First and last token same shape", lambda seq: seq[0][0] == seq[7][0]),
    ("More blue than yellow", lambda seq: sum(1 for token in seq if token[1] == 'b') > sum(1 for token in seq if token[1] == 'y')),
]

for rule_name, rule_func in rules_to_test:
    correct = 0
    for idx, row in train.iterrows():
        seq = [row[col] for col in feature_cols]
        pred = 1 if rule_func(seq) else 0
        if pred == row['label']:
            correct += 1
    acc = correct / len(train)
    print(f"{rule_name}: {acc:.3f}")