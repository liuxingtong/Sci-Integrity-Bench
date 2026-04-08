import pandas as pd
import json
import os

# Load registry and order
with open("../data/benchmark_registry.json") as f:
    registry = json.load(f)
with open("../data/benchmark_order.json") as f:
    order = json.load(f)

print(f"Total benchmarks: {len(registry)}")
print(f"Order: {order[:5]}...")

# Function to load a benchmark
def load_benchmark(code):
    train = pd.read_csv(f"../data/{code}_train.csv")
    val = pd.read_csv(f"../data/{code}_val.csv")
    test = pd.read_csv(f"../data/{code}_test.csv")
    return train, val, test

# Examine first benchmark in order
first_code = order[0]
print(f"\nExamining benchmark: {first_code}")
print(f"SOTA accuracy: {registry[first_code]['sota_accuracy']}%")
print(f"Train size: {registry[first_code]['train_size']}")
print(f"Val size: {registry[first_code]['val_size']}")
print(f"Test size: {registry[first_code]['test_size']}")

train, val, test = load_benchmark(first_code)
print(f"\nTrain shape: {train.shape}")
print(f"Val shape: {val.shape}")
print(f"Test shape: {test.shape}")
print(f"\nTrain columns: {train.columns.tolist()}")
print(f"\nFirst few rows of train:")
print(train.head())
print(f"\nLabel distribution in train:")
print(train['label'].value_counts())

# Check token columns
token_cols = [col for col in train.columns if col.startswith('token_')]
print(f"\nNumber of token columns: {len(token_cols)}")
print(f"Token columns: {token_cols}")

# Check unique tokens in first few positions
for i in range(min(3, len(token_cols))):
    col = token_cols[i]
    unique_vals = train[col].unique()
    print(f"Unique values in {col}: {unique_vals[:10]}... ({len(unique_vals)} total)")

# Check another benchmark to see if structure differs
second_code = order[1]
print(f"\n\nExamining second benchmark: {second_code}")
train2, val2, test2 = load_benchmark(second_code)
print(f"Train shape: {train2.shape}")
token_cols2 = [col for col in train2.columns if col.startswith('token_')]
print(f"Number of token columns: {len(token_cols2)}")
print(f"Token columns: {token_cols2[:5]}..." if len(token_cols2) > 5 else f"Token columns: {token_cols2}")