import pandas as pd

df_a = pd.read_csv('data/museum_export_a.csv')
df_b = pd.read_csv('data/museum_export_b.csv')

print('--- museum_export_a.csv ---')
print(df_a.head())
print(df_a.info())

print('\n--- museum_export_b.csv ---')
print(df_b.head())
print(df_b.info())
