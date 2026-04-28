import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data/store_monthly_sales.csv')
print('Shape:', df.shape)
print('Columns:', df.columns.tolist())
print('Dtypes:')
print(df.dtypes)
print('\nFirst 5 rows:')
print(df.head())
print('\nDescribe:')
print(df.describe())
print('\nMissing values:')
print(df.isnull().sum())
print('\nUnique stores:', df['store_id'].nunique() if 'store_id' in df.columns else 'N/A')
