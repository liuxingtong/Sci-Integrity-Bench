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

with open("../data/benchmark_order.json") as f:
    order = json.load(f)

summary = []
for code in order:
    train, val, test = load_benchmark(code)
    token_cols = [c for c in train.columns if c.startswith('token_')]
    seq_len = len(token_cols)
    # estimate vocabulary size across all positions
    vocab = set()
    for col in token_cols:
        vocab.update(train[col].unique())
    vocab_size = len(vocab)
    label_dist_train = train['label'].value_counts().to_dict()
    label_dist_test = test['label'].value_counts().to_dict()
    summary.append({
        'code': code,
        'sota': registry[code]['sota_accuracy'],
        'seq_len': seq_len,
        'vocab_size': vocab_size,
        'train_size': registry[code]['train_size'],
        'val_size': registry[code]['val_size'],
        'test_size': registry[code]['test_size'],
        'label_0_train': label_dist_train.get(0, 0),
        'label_1_train': label_dist_train.get(1, 0),
        'label_0_test': label_dist_test.get(0, 0),
        'label_1_test': label_dist_test.get(1, 0),
    })

df = pd.DataFrame(summary)
print(df.to_string(index=False))

# Save to CSV for reference
df.to_csv('../outputs/benchmark_summary.csv', index=False)
print("\nSaved to ../outputs/benchmark_summary.csv")