#!/usr/bin/env python3
import pandas as pd
import numpy as np
import sys

print('Starting data exploration...', flush=True)

try:
    df = pd.read_csv('data/reit_macro_quarterly.csv')
    print(f'Shape: {df.shape}', flush=True)
    print(f'Columns: {df.columns.tolist()}', flush=True)
    print(f'Dtypes:\n{df.dtypes}', flush=True)
    print(f'Head:\n{df.head(20)}', flush=True)
    print(f'Describe:\n{df.describe()}', flush=True)
    print(f'Missing values:\n{df.isnull().sum()}', flush=True)
except Exception as e:
    print(f'Error: {e}', flush=True)
    sys.exit(1)

print('Done!', flush=True)
