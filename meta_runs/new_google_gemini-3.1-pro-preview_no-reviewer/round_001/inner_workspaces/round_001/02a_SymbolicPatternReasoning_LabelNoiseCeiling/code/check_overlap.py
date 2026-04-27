import pandas as pd

train = pd.read_csv('data/spr_bench_train.csv')
val = pd.read_csv('data/spr_bench_val.csv')
test = pd.read_csv('data/spr_bench_test.csv')

feature_cols = [c for c in train.columns if c.startswith('token_')]

train['seq'] = train[feature_cols].apply(lambda x: ' '.join(x), axis=1)
val['seq'] = val[feature_cols].apply(lambda x: ' '.join(x), axis=1)
test['seq'] = test[feature_cols].apply(lambda x: ' '.join(x), axis=1)

train_seqs = set(train['seq'])
val_seqs = set(val['seq'])
test_seqs = set(test['seq'])

print(f"Train sequences: {len(train_seqs)}")
print(f"Val sequences: {len(val_seqs)}")
print(f"Test sequences: {len(test_seqs)}")

print(f"Overlap Train-Val: {len(train_seqs.intersection(val_seqs))}")
print(f"Overlap Train-Test: {len(train_seqs.intersection(test_seqs))}")
print(f"Overlap Val-Test: {len(val_seqs.intersection(test_seqs))}")
