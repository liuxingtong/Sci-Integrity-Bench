import pandas as pd
import numpy as np

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

print('Train shape:', train.shape)
print('Val shape:', val.shape)
print('Test shape:', test.shape)

print('\nLabel distribution in train:')
print(train['label'].value_counts(normalize=True))

print('\nSymbol series length:')
print(train['symbol_series'].apply(len).describe())

# Get unique characters
chars = set()
for s in train['symbol_series']:
    chars.update(list(s))
print('\nUnique characters:', sorted(list(chars)))
