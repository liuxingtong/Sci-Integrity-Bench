import pandas as pd
import os
import json
from collections import Counter

# Load registry
with open('../data/registry.json', 'r') as f:
    registry = json.load(f)

benchmarks = registry['benchmarks']
print(f"Total benchmarks: {len(benchmarks)}")
print("\nSelected benchmarks:")
selected_codes = ['KWP', 'HLP', 'ZTE', 'ZAX', 'CWR']
selected = [b for b in benchmarks if b['code'] in selected_codes]
for b in selected:
    print(f"  {b['code']}: script_family={b['script_family']}, dev_bleu={b['dev_bleu']}, test_size={b['test_size']}")

# Explore data for each selected benchmark
for code in selected_codes:
    print(f"\n--- {code} ---")
    train_path = f"../data/corpora/{code}/train.csv"
    val_path = f"../data/corpora/{code}/val.csv"
    test_path = f"../data/corpora/{code}/test.csv"
    
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)
    
    print(f"Train samples: {len(train_df)}")
    print(f"Val samples: {len(val_df)}")
    print(f"Test samples: {len(test_df)}")
    
    # Check first few samples
    print("\nFirst train sample:")
    print(f"  Source: {train_df['source'].iloc[0]}")
    print(f"  Target: {train_df['target'].iloc[0]}")
    
    # Analyze character patterns
    source_len = train_df['source'].apply(len)
    target_len = train_df['target'].apply(len)
    print(f"  Avg source length: {source_len.mean():.1f}")
    print(f"  Avg target length: {target_len.mean():.1f}")
    
    # Check if pattern is consistent
    sample_source = train_df['source'].iloc[0]
    sample_target = train_df['target'].iloc[0]
    # Remove spaces from target to compare with source
    target_no_spaces = sample_target.replace(' ', '')
    print(f"  Source == Target (no spaces)? {sample_source == target_no_spaces}")
