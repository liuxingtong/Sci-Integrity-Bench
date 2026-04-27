import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data/field_year_panel.csv')

print('=== DATA OVERVIEW ===')
print('Shape:', df.shape)
print('\nColumns:', df.columns.tolist())
print('\nData Types:')
print(df.dtypes)
print('\nFirst 5 rows:')
print(df.head())
print('\nBasic Statistics:')
print(df.describe())
print('\nMissing Values:')
print(df.isnull().sum())
print('\nUnique values per column:')
for col in df.columns:
    print(f'{col}: {df[col].nunique()} unique values')
    if df[col].nunique() < 20:
        print(f'  Values: {sorted(df[col].unique())}')
