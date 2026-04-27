import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')
print('Train shape:', train.shape)
print('Label distribution:')
print(train['label'].value_counts(normalize=True))

# Check symbol_series length
train['len'] = train['symbol_series'].apply(len)
print('Symbol series length distribution:')
print(train['len'].describe())

# Check unique characters
all_chars = set()
for s in train['symbol_series']:
    all_chars.update(list(s))
print('Unique characters:', sorted(list(all_chars)))
