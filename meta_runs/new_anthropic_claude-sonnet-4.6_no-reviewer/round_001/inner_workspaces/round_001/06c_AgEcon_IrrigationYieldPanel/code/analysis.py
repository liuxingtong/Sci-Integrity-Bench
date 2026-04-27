#!/usr/bin/env python3
"""
Irrigation Impact Analysis
Field-Year Panel Data Analysis
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
print('Loading data...')
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

# Save overview to file
with open('outputs/data_overview.txt', 'w') as f:
    f.write('=== DATA OVERVIEW ===\n')
    f.write(f'Shape: {df.shape}\n')
    f.write(f'\nColumns: {df.columns.tolist()}\n')
    f.write('\nData Types:\n')
    f.write(str(df.dtypes) + '\n')
    f.write('\nFirst 5 rows:\n')
    f.write(str(df.head()) + '\n')
    f.write('\nBasic Statistics:\n')
    f.write(str(df.describe()) + '\n')
    f.write('\nMissing Values:\n')
    f.write(str(df.isnull().sum()) + '\n')
    f.write('\nUnique values per column:\n')
    for col in df.columns:
        f.write(f'{col}: {df[col].nunique()} unique values\n')
        if df[col].nunique() < 20:
            f.write(f'  Values: {sorted(df[col].unique())}\n')

print('Data overview saved to outputs/data_overview.txt')
print('Script completed successfully!')
