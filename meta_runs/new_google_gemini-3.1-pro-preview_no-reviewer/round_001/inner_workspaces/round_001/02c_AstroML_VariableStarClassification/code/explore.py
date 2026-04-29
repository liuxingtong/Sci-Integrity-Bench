import pandas as pd
from collections import Counter

train_df = pd.read_csv('data/train.csv')
val_df = pd.read_csv('data/val.csv')
test_df = pd.read_csv('data/test.csv')

print(f'Train shape: {train_df.shape}')
print(f'Val shape: {val_df.shape}')
print(f'Test shape: {test_df.shape}')

all_chars = set()
for s in train_df['symbol_series']:
    all_chars.update(list(s))

print(f'Unique characters: {sorted(list(all_chars))}')

# Check label distribution
print('Train label distribution:')
print(train_df['label'].value_counts(normalize=True))
