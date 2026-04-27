import pandas as pd

df = pd.read_csv('data/load_15min.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
missing = df[df['load_mw'].isnull()]
print(missing)
