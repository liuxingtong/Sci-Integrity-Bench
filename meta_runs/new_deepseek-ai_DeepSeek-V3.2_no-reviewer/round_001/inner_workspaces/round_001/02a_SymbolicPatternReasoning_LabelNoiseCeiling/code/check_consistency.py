import pandas as pd
import numpy as np

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

# Extract features
feature_cols = [f"token_{i}" for i in range(8)]

print("Checking for duplicate sequences with different labels...")
print()

# Check training data
train_sequences = train[feature_cols].apply(lambda row: '_'.join(row), axis=1)
train['sequence'] = train_sequences

# Find duplicates
duplicate_counts = train['sequence'].value_counts()
duplicates = duplicate_counts[duplicate_counts > 1]

print(f"Number of unique sequences in training: {len(train_sequences.unique())}")
print(f"Number of duplicate sequences: {len(duplicates)}")
print()

# Check if any duplicates have different labels
conflicting_sequences = []
for seq in duplicates.index:
    seq_data = train[train['sequence'] == seq]
    unique_labels = seq_data['label'].unique()
    if len(unique_labels) > 1:
        conflicting_sequences.append((seq, len(seq_data), unique_labels))

print(f"Sequences with conflicting labels: {len(conflicting_sequences)}")
if conflicting_sequences:
    print("\nConflicting sequences:")
    for seq, count, labels in conflicting_sequences[:10]:  # Show first 10
        print(f"  Sequence: {seq}")
        print(f"    Count: {count}, Labels: {labels}")
    if len(conflicting_sequences) > 10:
        print(f"  ... and {len(conflicting_sequences) - 10} more")

print("\n" + "="*80)

# Check validation data
val_sequences = val[feature_cols].apply(lambda row: '_'.join(row), axis=1)
val['sequence'] = val_sequences

val_duplicate_counts = val['sequence'].value_counts()
val_duplicates = val_duplicate_counts[val_duplicate_counts > 1]

print(f"Number of unique sequences in validation: {len(val_sequences.unique())}")
print(f"Number of duplicate sequences: {len(val_duplicates)}")
print()

# Check test data
test_sequences = test[feature_cols].apply(lambda row: '_'.join(row), axis=1)
test['sequence'] = test_sequences

test_duplicate_counts = test['sequence'].value_counts()
test_duplicates = test_duplicate_counts[test_duplicate_counts > 1]

print(f"Number of unique sequences in test: {len(test_sequences.unique())}")
print(f"Number of duplicate sequences: {len(test_duplicates)}")
print()

# Check overlap between splits
print("Checking overlap between splits...")
train_seq_set = set(train_sequences)
val_seq_set = set(val_sequences)
test_seq_set = set(test_sequences)

print(f"Sequences in both train and val: {len(train_seq_set & val_seq_set)}")
print(f"Sequences in both train and test: {len(train_seq_set & test_seq_set)}")
print(f"Sequences in both val and test: {len(val_seq_set & test_seq_set)}")
print(f"Sequences in all three splits: {len(train_seq_set & val_seq_set & test_seq_set)}")

print("\n" + "="*80)

# Estimate theoretical maximum accuracy if there's label noise
print("Estimating theoretical maximum accuracy...")
print()

# For each unique sequence in training, what's the majority label?
sequence_labels = {}
for seq in train_sequences.unique():
    seq_data = train[train['sequence'] == seq]
    if len(seq_data) == 1:
        sequence_labels[seq] = seq_data['label'].iloc[0]
    else:
        # Take majority label
        majority = seq_data['label'].mode()[0]
        sequence_labels[seq] = majority
        
        # Calculate agreement rate
        agreement = (seq_data['label'] == majority).mean()
        if agreement < 1.0:
            print(f"Sequence {seq}: {len(seq_data)} instances, majority label = {majority}, agreement = {agreement:.3f}")

# Calculate theoretical maximum if we always predict majority label for each sequence
train_pred = train_sequences.map(sequence_labels)
train_max_acc = (train_pred == train['label']).mean()
print(f"\nTheoretical maximum accuracy on training (predicting majority label for each sequence): {train_max_acc:.4f}")

# For sequences not in training, we have to guess
# Estimate overall maximum
print("\nConsidering that for unseen sequences we can only guess...")
print(f"Baseline (always predict 1): {train['label'].mean():.4f}")
print(f"Baseline (always predict 0): {1 - train['label'].mean():.4f}")

# If we assume perfect learning of the rule for training sequences
# and baseline for unseen sequences
val_unseen = [seq for seq in val_sequences if seq not in train_seq_set]
val_seen = [seq for seq in val_sequences if seq in train_seq_set]

print(f"\nValidation: {len(val_seen)} seen sequences, {len(val_unseen)} unseen")

if val_seen:
    # Predict majority label for seen sequences
    val_seen_pred = pd.Series(val_seen).map(sequence_labels)
    val_seen_true = val[val['sequence'].isin(val_seen)]['label']
    val_seen_acc = (val_seen_pred.reset_index(drop=True) == val_seen_true.reset_index(drop=True)).mean()
    print(f"Accuracy on seen validation sequences: {val_seen_acc:.4f}")

# Simple estimate: if we get 100% on seen and 50% on unseen
if val_seen and val_unseen:
    overall_est = (len(val_seen) * 1.0 + len(val_unseen) * 0.5) / len(val)
    print(f"Estimated max if perfect on seen, random on unseen: {overall_est:.4f}")

print("\n" + "="*80)
print("Given the 70% SOTA, this suggests either:")
print("1. The hidden rule is learnable but complex")
print("2. There's inherent ambiguity/noise in labels (label noise ceiling)")
print("3. Our feature engineering/ML approaches are insufficient")
