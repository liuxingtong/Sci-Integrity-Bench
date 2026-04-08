import pandas as pd
import os

print("Loading data...")
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

print(f"Train shape: {train.shape}")
print(f"Validation shape: {val.shape}")
print(f"Test shape: {test.shape}")

print("\nFirst few rows of train:")
print(train.head())

print("\nColumn names:")
print(train.columns.tolist())

print("\nLabel distribution in train:")
print(train['label'].value_counts())
print(f"Train label ratio: {train['label'].mean():.3f}")

print("\nLabel distribution in validation:")
print(val['label'].value_counts())
print(f"Validation label ratio: {val['label'].mean():.3f}")

print("\nLabel distribution in test:")
print(test['label'].value_counts())
print(f"Test label ratio: {test['label'].mean():.3f}")

# Check for missing values
print("\nMissing values in train:")
print(train.isnull().sum().sum())

# Check unique tokens
feature_cols = [c for c in train.columns if c.startswith('token_')]
print(f"\nNumber of feature columns: {len(feature_cols)}")
print(f"Sequence length: {len(feature_cols)}")

# Get unique tokens
all_tokens = []
for col in feature_cols:
    all_tokens.extend(train[col].unique())
unique_tokens = set(all_tokens)
print(f"\nUnique tokens in train: {len(unique_tokens)}")
print(f"Sample tokens: {list(unique_tokens)[:10]}")

# Check if tokens are consistent format
sample_token = train[feature_cols[0]].iloc[0]
print(f"\nSample token format: '{sample_token}' (length: {len(sample_token)})")
