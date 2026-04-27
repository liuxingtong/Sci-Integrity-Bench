import pandas as pd
import os

os.makedirs('outputs', exist_ok=True)

df = pd.read_csv('data/reit_macro_quarterly.csv')

with open('outputs/simple_test.txt', 'w') as f:
    f.write(str(df.columns.tolist()) + '\n')
    f.write(str(df.shape) + '\n')
    f.write(str(df.head(5)) + '\n')
    f.write(str(df.describe()) + '\n')
