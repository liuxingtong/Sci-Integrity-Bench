#!/usr/bin/env python3
"""
Irrigation Impact Analysis - Full Analysis
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
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')

# Load data
print('Loading data...')
df = pd.read_csv('data/field_year_panel.csv')

print('Shape:', df.shape)
print('Columns:', df.columns.tolist())
print(df.head())
print(df.describe())

# Save detailed overview
with open('outputs/detailed_overview.txt', 'w') as f:
    f.write('=== FIELD-YEAR PANEL DATA OVERVIEW ===\n\n')
    f.write(f'Total observations: {len(df)}\n')
    f.write(f'Columns: {df.columns.tolist()}\n\n')
    f.write('Data Types:\n')
    f.write(str(df.dtypes) + '\n\n')
    f.write('Basic Statistics:\n')
    f.write(str(df.describe()) + '\n\n')
    f.write('Missing Values:\n')
    f.write(str(df.isnull().sum()) + '\n\n')
    f.write('Unique values per column:\n')
    for col in df.columns:
        f.write(f'{col}: {df[col].nunique()} unique values\n')
        if df[col].nunique() < 30:
            f.write(f'  Values: {sorted(df[col].dropna().unique())}\n')

print('Overview saved.')

# Identify key columns
cols = df.columns.tolist()
print('\nAll columns:', cols)

# Try to identify column types
yield_cols = [c for c in cols if 'yield' in c.lower()]
irrig_cols = [c for c in cols if 'irrig' in c.lower()]
fert_cols = [c for c in cols if 'fert' in c.lower() or 'nitrogen' in c.lower() or 'npk' in c.lower()]
rain_cols = [c for c in cols if 'rain' in c.lower() or 'precip' in c.lower()]
quota_cols = [c for c in cols if 'quota' in c.lower() or 'enforce' in c.lower() or 'gw' in c.lower() or 'ground' in c.lower()]
year_cols = [c for c in cols if 'year' in c.lower()]
field_cols = [c for c in cols if 'field' in c.lower() or 'plot' in c.lower() or 'id' in c.lower()]

print('\nYield columns:', yield_cols)
print('Irrigation columns:', irrig_cols)
print('Fertilizer columns:', fert_cols)
print('Rainfall columns:', rain_cols)
print('Quota/enforcement columns:', quota_cols)
print('Year columns:', year_cols)
print('Field/ID columns:', field_cols)

# Save column identification
with open('outputs/column_identification.txt', 'w') as f:
    f.write('Column Identification:\n')
    f.write(f'Yield columns: {yield_cols}\n')
    f.write(f'Irrigation columns: {irrig_cols}\n')
    f.write(f'Fertilizer columns: {fert_cols}\n')
    f.write(f'Rainfall columns: {rain_cols}\n')
    f.write(f'Quota/enforcement columns: {quota_cols}\n')
    f.write(f'Year columns: {year_cols}\n')
    f.write(f'Field/ID columns: {field_cols}\n')
    f.write(f'\nAll columns: {cols}\n')

print('Column identification saved.')
print('Script completed!')
