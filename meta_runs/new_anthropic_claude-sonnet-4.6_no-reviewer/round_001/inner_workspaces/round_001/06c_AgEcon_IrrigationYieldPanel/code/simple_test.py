import pandas as pd
import os

os.makedirs('outputs', exist_ok=True)

df = pd.read_csv('data/field_year_panel.csv')

with open('outputs/simple_test.txt', 'w') as f:
    f.write(f'Shape: {df.shape}\n')
    f.write(f'Columns: {list(df.columns)}\n')
    f.write(str(df.head()) + '\n')
    f.write(str(df.describe()) + '\n')

print('Done!')
