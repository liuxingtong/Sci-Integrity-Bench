#!/usr/bin/env python3
import pandas as pd
import numpy as np
import sys
import os

os.makedirs('outputs', exist_ok=True)

with open('outputs/data_exploration.txt', 'w') as f:
    f.write('Starting data exploration...\n')
    
    try:
        df = pd.read_csv('data/reit_macro_quarterly.csv')
        f.write(f'Shape: {df.shape}\n')
        f.write(f'Columns: {df.columns.tolist()}\n')
        f.write(f'Dtypes:\n{df.dtypes}\n')
        f.write(f'Head:\n{df.head(20)}\n')
        f.write(f'Describe:\n{df.describe()}\n')
        f.write(f'Missing values:\n{df.isnull().sum()}\n')
    except Exception as e:
        f.write(f'Error: {e}\n')
    
    f.write('Done!\n')

print('Script completed')
