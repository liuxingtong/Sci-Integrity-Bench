import pandas as pd
import numpy as np
from collections import Counter

np.random.seed(42)

print("Loading data...")
train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
shapes = ['T', 'S', 'C', 'D']
colors = ['r', 'g', 'b', 'y']
all_tokens = ['Cb', 'Cg', 'Cr', 'Cy', 'Db', 'Dg', 'Dr', 'Dy', 'Sb', 'Sg', 'Sr', 'Sy', 'Tb', 'Tg', 'Tr', 'Ty']

# Combine all data
all_data = pd.concat([train, val, test], ignore_index=True)
print(f"Total samples: {len(all_data)}")
print(f"Label distribution: {Counter(all_data['label'])}")

# Check for near-duplicate sequences
print("\n=== Checking for duplicates ===")
df_temp = all_data.copy()
df_temp['seq_key'] = df_temp[feature_cols].apply(lambda x: tuple(x), axis=1)
seq_groups = df_temp.groupby('seq_key')['label'].agg(['count', 'mean', 'std'])
print(f"Unique sequences: {len(seq_groups)}")
print(f"Total samples: {df_temp['seq_key'].count()}")

seq_with_multiple = seq_groups[seq_groups['count'] > 1]
if len(seq_with_multiple) > 0:
    print(f"Sequences appearing multiple times: {len(seq_with_multiple)}")
else:
    print("No duplicate sequences found.")

# Check for sequences that differ by only 1 token but have different labels
print("\n=== Checking for 1-token-different sequences with conflicting labels ===")
seq_list = df_temp[['seq_key', 'label']].values

conflicting_near_dup = 0
sample_size = min(500, len(seq_list))
sample_indices = np.random.choice(len(seq_list), sample_size, replace=False)

for i in sample_indices:
    seq_i, label_i = seq_list[i]
    for j in sample_indices:
        if i >= j:
            continue
        seq_j, label_j = seq_list[j]
        diff_count = sum(1 for a, b in zip(seq_i, seq_j) if a != b)
        if diff_count == 1 and label_i != label_j:
            conflicting_near_dup += 1

print(f"Found {conflicting_near_dup} near-duplicate pairs (1 token diff) with conflicting labels in sample")

# Analyze the theoretical ceiling due to potential noise
print("\n=== Estimating Label Noise Ceiling ===")

# Check: if we ignore 1 position, do we get conflicting labels?
print("\nChecking sequences that match on 7 of 8 positions:")
for ignore_pos in range(8):
    df_temp[f'sig_{ignore_pos}'] = df_temp.apply(
        lambda row: tuple(t for i, t in enumerate([row[col] for col in feature_cols]) if i != ignore_pos),
        axis=1
    )
    sig_groups = df_temp.groupby(f'sig_{ignore_pos}')['label'].agg(['count', 'std'])
    conflicting = sig_groups[sig_groups['std'] > 0]
    total_samples_in_conflicting = conflicting['count'].sum()
    print(f"  Ignoring position {ignore_pos}: {len(conflicting)} signatures with conflicts, {total_samples_in_conflicting} samples affected")
    df_temp.drop(columns=[f'sig_{ignore_pos}'], inplace=True)

# Check for patterns in the data
print("\n=== Checking for simple rules ===")

# Rule 1: Label = 1 if majority shape is T or S
train['maj_shape'] = train.apply(lambda row: Counter(row[col][0] for col in feature_cols).most_common(1)[0][0], axis=1)
rule1_train = (train['maj_shape'].isin(['T', 'S']) == train['label']).mean()
print(f"Rule: maj_shape in [T,S] -> label=1, Accuracy: {rule1_train:.4f}")

# Rule 2: Label based on first token shape
for shape in shapes:
    pred = (train[feature_cols[0]].str[0] == shape).astype(int)
    acc = (pred == train['label']).mean()
    if acc > 0.55 or acc < 0.45:
        print(f"Rule: first_shape={shape} -> label=1, Accuracy: {acc:.4f}")

# Rule 3: XOR of two conditions
print("\n=== Checking XOR rules ===")
train['maj_color'] = train.apply(lambda row: Counter(row[col][1] for col in feature_cols).most_common(1)[0][0], axis=1)

for s1 in shapes:
    for c1 in colors:
        cond_A = train['maj_shape'] == s1
        cond_B = train['maj_color'] == c1
        xor_pred = (cond_A != cond_B).astype(int)
        acc = (xor_pred == train['label']).mean()
        if acc > 0.55:
            print(f"XOR(maj_shape={s1}, maj_color={c1}): Accuracy: {acc:.4f}")

# Check token count patterns
print("\n=== Checking token count patterns ===")
for token in all_tokens:
    train[f'count_{token}'] = train.apply(lambda row, t=token: sum(1 for col in feature_cols if row[col] == t), axis=1)
    for thresh in [2, 3]:
        pred = (train[f'count_{token}'] >= thresh).astype(int)
        acc = (pred == train['label']).mean()
        if acc > 0.55 or acc < 0.45:
            print(f"Rule: count({token})>={thresh} -> label=1, Accuracy: {acc:.4f}")
    train.drop(columns=[f'count_{token}'], inplace=True)

print("\n=== Summary ===")
print("The SPR benchmark appears to have a hidden rule that is not easily captured by standard features.")
print("Models achieve ~50% accuracy, suggesting either:")
print("1. The rule is highly complex/non-linear")
print("2. There is significant label noise (hence 'LabelNoiseCeiling' in task name)")
print("3. The task requires symbolic reasoning beyond standard ML pattern recognition")
