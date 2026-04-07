import pandas as pd
import os

print("Checking data files...")

# Check file sizes
for fname in ['spr_bench_train.csv', 'spr_bench_val.csv', 'spr_bench_test.csv']:
    path = os.path.join('..', 'data', fname)
    if os.path.exists(path):
        with open(path, 'r') as f:
            lines = f.readlines()
        print(f"{fname}: {len(lines)} lines (including header)")
    else:
        print(f"{fname}: not found")

# Load a small sample to understand structure
print("\nLoading train data...")
train = pd.read_csv('../data/spr_bench_train.csv')
print(f"Train shape: {train.shape}")
print(f"Columns: {list(train.columns)}")
print(f"\nFirst few rows:")
print(train.head())
print(f"\nLabel distribution:")
print(train['label'].value_counts())

# Check sequence length
feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"\nNumber of tokens per sequence: {len(feature_cols)}")
print(f"Token columns: {feature_cols}")

# Check unique tokens
all_tokens = []
for col in feature_cols:
    all_tokens.extend(train[col].unique())
unique_tokens = set(all_tokens)
print(f"\nUnique tokens (first 20): {list(unique_tokens)[:20]}")
print(f"Total unique tokens: {len(unique_tokens)}")