import pandas as pd

train_df = pd.read_csv('data/train.csv')
lengths = train_df['symbol_series'].apply(len)
print(f'Sequence lengths: min={lengths.min()}, max={lengths.max()}, mean={lengths.mean()}')

print('Field ID distribution:')
print(train_df['field_id'].value_counts())
