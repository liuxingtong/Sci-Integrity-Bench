import pandas as pd
import numpy as np
from collections import Counter

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]
X_train = train[feature_cols]
y_train = train['label']

print("Checking label consistency in training data...")
print(f"Training samples: {len(train)}")

# Check for duplicate sequences
print("\n=== Checking for duplicate sequences ===")

# Create string representation of each sequence
train_sequences = X_train.apply(lambda row: '-'.join(row.values), axis=1)
sequence_counts = Counter(train_sequences)

# Find sequences that appear multiple times
duplicate_sequences = {seq: count for seq, count in sequence_counts.items() if count > 1}

print(f"Number of unique sequences: {len(sequence_counts)}")
print(f"Number of sequences that appear more than once: {len(duplicate_sequences)}")

if duplicate_sequences:
    print("\nChecking label consistency for duplicate sequences:")
    inconsistent_count = 0
    total_duplicate_instances = 0
    
    for seq, count in list(duplicate_sequences.items())[:20]:  # Check first 20
        # Get indices of this sequence
        indices = train_sequences[train_sequences == seq].index.tolist()
        labels = y_train.loc[indices].values
        unique_labels = set(labels)
        
        total_duplicate_instances += count
        
        if len(unique_labels) > 1:
            inconsistent_count += 1
            print(f"  Sequence '{seq}' appears {count} times with labels {labels}")
    
    print(f"\nFound {inconsistent_count} sequences with inconsistent labels out of {len(duplicate_sequences)} duplicate sequences")
    if total_duplicate_instances > 0:
        inconsistency_rate = inconsistent_count / len(duplicate_sequences) if duplicate_sequences else 0
        print(f"Inconsistency rate among duplicate sequences: {inconsistency_rate:.3f}")
else:
    print("No duplicate sequences found.")

# Check for similar sequences (differ by 1 token)
print("\n=== Checking for similar sequences (Hamming distance <= 1) ===")
# This is computationally expensive, so let's sample
sample_size = min(500, len(train))
sample_indices = np.random.choice(len(train), sample_size, replace=False)

similar_pairs = []

for i in range(sample_size):
    idx1 = sample_indices[i]
    seq1 = X_train.iloc[idx1].values
    
    for j in range(i+1, sample_size):
        idx2 = sample_indices[j]
        seq2 = X_train.iloc[idx2].values
        
        # Calculate Hamming distance
        distance = sum(1 for a, b in zip(seq1, seq2) if a != b)
        
        if distance <= 1:  # Very similar sequences
            label1 = y_train.iloc[idx1]
            label2 = y_train.iloc[idx2]
            
            if label1 != label2:
                similar_pairs.append((idx1, idx2, distance, label1, label2))
    
    if len(similar_pairs) >= 20:
        break

print(f"Found {len(similar_pairs)} pairs of very similar sequences (distance <= 1) with different labels")
if similar_pairs:
    print("First 5 examples:")
    for i, (idx1, idx2, dist, l1, l2) in enumerate(similar_pairs[:5]):
        print(f"  Pair {i+1}: distance={dist}, labels={l1} vs {l2}")
        print(f"    Seq1: {'-'.join(X_train.iloc[idx1].values)}")
        print(f"    Seq2: {'-'.join(X_train.iloc[idx2].values)}")

# Estimate theoretical maximum accuracy (noise ceiling)
print("\n=== Estimating theoretical maximum accuracy ===")
print("If similar sequences can have different labels, there's inherent ambiguity.")
print("This sets an upper bound on achievable accuracy.")

# Simple estimate: if x% of sequences have inconsistent labels with their nearest neighbors,
# then maximum accuracy is roughly (100 - x)%

# For a rough estimate, check k-nearest neighbors in a sample
from sklearn.neighbors import NearestNeighbors
import warnings
warnings.filterwarnings('ignore')

# Convert tokens to numerical features for distance calculation
# Simple encoding: each token as integer (0-15)
all_tokens = set()
for col in feature_cols:
    all_tokens.update(X_train[col].unique())

token_list = sorted(list(all_tokens))
token_to_idx = {token: i for i, token in enumerate(token_list)}

def encode_sequence(row):
    return [token_to_idx[row[col]] for col in feature_cols]

# Encode a sample of data
sample_size = min(1000, len(train))
sample_indices = np.random.choice(len(train), sample_size, replace=False)
X_sample_encoded = np.array([encode_sequence(X_train.iloc[idx]) for idx in sample_indices])
y_sample = y_train.iloc[sample_indices].values

# Find nearest neighbors
n_neighbors = 5
nbrs = NearestNeighbors(n_neighbors=n_neighbors+1, metric='hamming').fit(X_sample_encoded)
distances, indices = nbrs.kneighbors(X_sample_encoded)

# Check label consistency with nearest neighbors
inconsistent_with_neighbors = 0

for i in range(len(X_sample_encoded)):
    # Skip the first neighbor (itself)
    neighbor_indices = indices[i][1:n_neighbors+1]
    neighbor_labels = y_sample[neighbor_indices]
    
    # Check if any neighbor has different label
    if not all(label == y_sample[i] for label in neighbor_labels):
        inconsistent_with_neighbors += 1

inconsistency_rate = inconsistent_with_neighbors / len(X_sample_encoded)
max_theoretical_acc = 1 - inconsistency_rate

print(f"Sample size: {sample_size}")
print(f"Sequences with inconsistent labels among {n_neighbors} nearest neighbors: {inconsistent_with_neighbors} ({inconsistency_rate:.3f})")
print(f"Rough estimate of maximum theoretical accuracy: {max_theoretical_acc:.3f}")
print(f"SOTA baseline: 0.700")

if max_theoretical_acc < 0.7:
    print("WARNING: Estimated maximum accuracy is below SOTA baseline!")
    print("This suggests either:")
    print("  1. My estimate is too pessimistic")
    print("  2. The SOTA result of 70% is remarkable")
    print("  3. There's something I'm missing about the data")