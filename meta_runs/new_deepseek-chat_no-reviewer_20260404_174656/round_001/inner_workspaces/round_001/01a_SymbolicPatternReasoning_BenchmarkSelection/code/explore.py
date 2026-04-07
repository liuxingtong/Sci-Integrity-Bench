import pandas as pd
import json
import os

def load_benchmark(code):
    train = pd.read_csv(f"../data/{code}_train.csv")
    val = pd.read_csv(f"../data/{code}_val.csv")
    test = pd.read_csv(f"../data/{code}_test.csv")
    return train, val, test

with open("../data/benchmark_registry.json") as f:
    registry = json.load(f)

# Select a few benchmarks to inspect
codes = ["OQMEA", "FDLOT", "ZOBKB", "DQTDY", "RHHQD", "ILULR"]
for code in codes:
    train, val, test = load_benchmark(code)
    print(f"\n--- {code} ---")
    print(f"SOTA accuracy: {registry[code]['sota_accuracy']}%")
    print(f"Train shape: {train.shape}")
    print(f"Token columns: {[c for c in train.columns if c.startswith('token_')]}")
    print(f"Sequence length: {len([c for c in train.columns if c.startswith('token_')])}")
    # Show unique tokens in first few positions
    for i in range(min(3, len([c for c in train.columns if c.startswith('token_')]))):
        col = f"token_{i}"
        uniq = train[col].unique()
        print(f"  {col}: {len(uniq)} unique tokens, sample: {uniq[:5]}")
    print(f"Label distribution (train): {train['label'].value_counts().to_dict()}")
    print(f"Label distribution (test): {test['label'].value_counts().to_dict()}")