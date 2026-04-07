import pandas as pd
import json

# Load registry
with open("../data/benchmark_registry.json") as f:
    registry = json.load(f)

# Check a few benchmarks
benchmarks_to_check = ['FDLOT', 'WVIOP', 'XPOFG', 'OQMEA', 'AUOJZ']

for code in benchmarks_to_check:
    print(f"\n{'='*50}")
    print(f"Benchmark: {code}")
    train = pd.read_csv(f"../data/{code}_train.csv")
    
    token_cols = [col for col in train.columns if col.startswith('token_')]
    
    # Collect all unique tokens
    all_tokens = set()
    for col in token_cols:
        all_tokens.update(train[col].unique())
    
    print(f"Sequence length: {len(token_cols)}")
    print(f"Total unique tokens: {len(all_tokens)}")
    print(f"Tokens: {sorted(list(all_tokens))}")
    
    # Extract shapes and colors
    shapes = set([t[0] for t in all_tokens])
    colors = set([t[1] for t in all_tokens])
    
    print(f"Shapes: {shapes}")
    print(f"Colors: {colors}")
    
    # Check label balance
    prop_1 = train['label'].mean()
    print(f"Proportion of class 1: {prop_1:.3f}")