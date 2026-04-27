import pandas as pd

df = pd.read_csv('data/load_15min.csv')
print(df.head())
print(df.tail())
print(df.info())
print(df.describe())
