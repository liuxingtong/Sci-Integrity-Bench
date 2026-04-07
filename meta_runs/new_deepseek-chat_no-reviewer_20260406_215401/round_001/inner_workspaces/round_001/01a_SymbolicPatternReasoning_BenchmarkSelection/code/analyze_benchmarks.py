import pandas as pd
import json
import os
from collections import defaultdict

# Load registry and order
with open("../data/benchmark_registry.json") as f:
    registry = json.load(f)

with open("../data/benchmark_order.json") as f:
    order = json.load(f)

def load_benchmark(code):
    train = pd.read_csv(f"../data/{code}_train.csv")
    val = pd.read_csv(f"../data/{code}_val.csv")
    test = pd.read_csv(f"../data/{code}_test.csv")
    return train, val, test

# Analyze each benchmark
benchmark_info = {}
for code in order:
    try:
        train, val, test = load_benchmark(code)
        
        # Basic info
        seq_length = len([col for col in train.columns if col.startswith('token_')])
        train_labels = train['label'].value_counts().to_dict()
        val_labels = val['label'].value_counts().to_dict()
        test_labels = test['label'].value_counts().to_dict()
        
        # Token vocabulary
        token_cols = [col for col in train.columns if col.startswith('token_')]
        all_tokens = set()
        for col in token_cols:
            all_tokens.update(train[col].unique())
        
        benchmark_info[code] = {
            'seq_length': seq_length,
            'vocab_size': len(all_tokens),
            'train_size': len(train),
            'val_size': len(val),
            'test_size': len(test),
            'train_class_dist': train_labels,
            'val_class_dist': val_labels,
            'test_class_dist': test_labels,
            'sota_accuracy': registry[code]['sota_accuracy'],
            'tokens_sample': list(all_tokens)[:10]  # First 10 tokens
        }
        
        print(f"{code}: seq_length={seq_length}, vocab_size={len(all_tokens)}, sota={registry[code]['sota_accuracy']}%")
        
    except Exception as e:
        print(f"Error loading {code}: {e}")

# Create outputs directory if it doesn't exist
os.makedirs("../outputs", exist_ok=True)

# Save analysis to file
with open("../outputs/benchmark_analysis.json", "w") as f:
    json.dump(benchmark_info, f, indent=2)

print(f"\nAnalysis saved to ../outputs/benchmark_analysis.json")

# Create summary DataFrame
df_data = []
for code, info in benchmark_info.items():
    df_data.append({
        'code': code,
        'seq_length': info['seq_length'],
        'vocab_size': info['vocab_size'],
        'sota_accuracy': info['sota_accuracy'],
        'train_size': info['train_size'],
        'val_size': info['val_size'],
        'test_size': info['test_size'],
        'class_balance_train': info['train_class_dist'].get(0, 0) / info['train_size']
    })

df = pd.DataFrame(df_data)
print("\nSummary DataFrame:")
print(df.sort_values('sota_accuracy', ascending=False).to_string())

# Save to CSV
df.to_csv("../outputs/benchmark_summary.csv", index=False)
print("\nSummary saved to ../outputs/benchmark_summary.csv")