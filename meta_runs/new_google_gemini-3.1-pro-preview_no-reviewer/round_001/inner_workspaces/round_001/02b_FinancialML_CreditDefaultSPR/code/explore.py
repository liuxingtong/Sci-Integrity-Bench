import pandas as pd
import numpy as np
from collections import Counter

train = pd.read_csv('data/train.csv')
val = pd.read_csv('data/val.csv')
test = pd.read_csv('data/test.csv')

print('Train shape:', train.shape)
print('Val shape:', val.shape)
print('Test shape:', test.shape)

print('\nTrain default_flag distribution:')
print(train['default_flag'].value_counts(normalize=True))

print('\nSequence lengths:')
print(train['sym_seq'].apply(len).describe())

all_chars = set()
for seq in train['sym_seq']:
    all_chars.update(list(seq))
print('\nUnique characters:', sorted(list(all_chars)))

# Character frequencies
char_counts = Counter()
for seq in train['sym_seq']:
    char_counts.update(list(seq))
print('\nCharacter frequencies:', char_counts)
