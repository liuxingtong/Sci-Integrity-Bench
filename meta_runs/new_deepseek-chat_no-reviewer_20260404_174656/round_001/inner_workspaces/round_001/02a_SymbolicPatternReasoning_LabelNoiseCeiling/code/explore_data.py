import pandas as pd
import numpy as np

# Load data
train = pd.read_csv('../data/spr_bench_train.csv')
val = pd.read_csv('../data/spr_bench_val.csv')
test = pd.read_csv('../data/spr_bench_test.csv')

print("Train shape:", train.shape)
print("Validation shape:", val.shape)
print("Test shape:", test.shape)

print("\nTrain columns:", train.columns.tolist())
print("\nFirst few rows of train:")
print(train.head())

print("\nLabel distribution in train:")
print(train['label'].value_counts())
print("Label distribution in validation:")
print(val['label'].value_counts())
print("Label distribution in test:")
print(test['label'].value_counts())

# Check for missing values
print("\nMissing values in train:", train.isnull().sum().sum())
print("Missing values in validation:", val.isnull().sum().sum())
print("Missing values in test:", test.isnull().sum().sum())

# Check unique tokens
feature_cols = [c for c in train.columns if c.startswith('token_')]
print("\nFeature columns:", feature_cols)
print("Number of tokens per sequence:", len(feature_cols))

# Get all unique tokens
all_tokens = []
for col in feature_cols:
    all_tokens.extend(train[col].unique())
    all_tokens.extend(val[col].unique())
    all_tokens.extend(test[col].unique())

unique_tokens = set(all_tokens)
print("\nUnique tokens:", unique_tokens)
print("Number of unique tokens:", len(unique_tokens))

# Check token composition
print("\nSample token breakdown:")
for token in list(unique_tokens)[:10]:
    print(f"Token '{token}': shape={token[0]}, color={token[1]}")