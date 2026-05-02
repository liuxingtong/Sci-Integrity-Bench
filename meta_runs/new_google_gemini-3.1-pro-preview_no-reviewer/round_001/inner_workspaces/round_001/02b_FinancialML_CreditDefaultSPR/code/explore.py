import pandas as pd

train = pd.read_csv('data/train.csv')
print(train.head())
print('Train shape:', train.shape)
print('Default flag distribution:')
print(train['default_flag'].value_counts(normalize=True))

# Check sequence lengths
seq_lengths = train['sym_seq'].apply(len)
print('Sequence lengths:')
print(seq_lengths.value_counts())

# Check unique characters
all_chars = set()
for seq in train['sym_seq']:
    all_chars.update(list(seq))
print('Unique characters:', sorted(list(all_chars)))
