import pandas as pd
import json
import os

with open('data/benchmark_order.json') as f:
    codes = json.load(f)

with open('data/benchmark_registry.json') as f:
    registry = json.load(f)

res = []
for c in codes:
    df = pd.read_csv(f'data/{c}_train.csv')
    num_tokens = df.shape[1] - 1
    vocab = set(df.drop('label', axis=1).values.flatten())
    res.append({'code': c, 'seq_len': num_tokens, 'vocab_size': len(vocab), 'sota_accuracy': registry[c]['sota_accuracy']})

res_df = pd.DataFrame(res)
print(res_df)
res_df.to_csv('outputs/benchmark_stats.csv', index=False)
