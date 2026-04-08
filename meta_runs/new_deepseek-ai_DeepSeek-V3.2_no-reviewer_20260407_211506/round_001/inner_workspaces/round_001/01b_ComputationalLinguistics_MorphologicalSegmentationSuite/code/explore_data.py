import pandas as pd
import os
import json
from collections import Counter

# Read registry
with open('../data/registry.json', 'r') as f:
    registry = json.load(f)

benchmarks = registry['benchmarks']
print(f"Total benchmarks: {len(benchmarks)}")

# Select 5 benchmarks
selected_codes = ['KWP', 'HLP', 'ZTE', 'ZAX', 'CWR']
selected_benchmarks = [b for b in benchmarks if b['code'] in selected_codes]

print("\nSelected benchmarks:")
for b in selected_benchmarks:
    print(f"  {b['code']}: script_family={b['script_family']}, dev_bleu={b['dev_bleu']}, test_size={b['test_size']}")

# Analyze data for each selected benchmark
for code in selected_codes:
    print(f"\n--- Analyzing {code} ---")
    
    train_path = f'../data/corpora/{code}/train.csv'
    val_path = f'../data/corpora/{code}/val.csv'
    test_path = f'../data/corpora/{code}/test.csv'
    
    # Check file sizes
    for split, path in [('train', train_path), ('val', val_path), ('test', test_path)]:
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"  {split}: {len(df)} samples")
            
            # Show first few examples
            if split == 'train':
                print(f"    First example:")
                print(f"      Source: '{df.iloc[0]['source']}'")
                print(f"      Target: '{df.iloc[0]['target']}'")
                
                # Character statistics
                source_chars = list(df.iloc[0]['source'])
                target_tokens = df.iloc[0]['target'].split()
                print(f"      Source length: {len(source_chars)} chars")
                print(f"      Target tokens: {len(target_tokens)} tokens")
                
                # Check if it's character segmentation
                reconstructed = ''.join(target_tokens)
                if reconstructed == df.iloc[0]['source']:
                    print(f"      Task appears to be character-level segmentation")
                else:
                    print(f"      Task is NOT simple character-level segmentation")
                    print(f"      Reconstructed: '{reconstructed}'")
                    print(f"      Original: '{df.iloc[0]['source']}'")
