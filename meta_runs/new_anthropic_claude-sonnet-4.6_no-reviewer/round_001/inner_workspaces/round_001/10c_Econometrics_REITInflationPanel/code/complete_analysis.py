#!/usr/bin/env python3
"""
REIT-Inflation Panel Analysis
Comprehensive association analysis between REIT index returns and inflation
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
os.makedirs('report', exist_ok=True)

print('Loading data...')
df = pd.read_csv('data/reit_macro_quarterly.csv')

print(f'Shape: {df.shape}')
print(f'Columns: {df.columns.tolist()}')
print(f'\nHead:\n{df.head(5)}')

# ============================================================
# 1. DATA PREPARATION
# ============================================================

# Based on column analysis output:
# Columns include: date/quarter, reit_return (or similar), inflation, and macro vars
# Let's work with what we have

# Identify column types
all_cols = df.columns.tolist()
print(f'\nAll columns: {all_cols}')

# Find date column
date_col = None
for c in all_cols:
    if any(x in c.lower() for x in ['date', 'quarter', 'time', 'period', 'year']):
        date_col = c
        break

# Find REIT columns
reit_cols = [c for c in all_cols if 'reit' in c.lower()]

# Find inflation columns  
infl_cols = [c for c in all_cols if any(x in c.lower() for x in ['infl', 'cpi', 'pce', 'price'])]

# Find other numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

print(f'Date column: {date_col}')
print(f'REIT columns: {reit_cols}')
print(f'Inflation columns: {infl_cols}')
print(f'Numeric columns: {numeric_cols}')

# Parse date if found
if date_col:
    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).reset_index(drop=True)
        print(f'Date range: {df[date_col].min()} to {df[date_col].max()}')
    except:
        print(f'Could not parse {date_col} as date')

# Save exploration
with open('outputs/data_summary.txt', 'w') as f:
    f.write(f'Shape: {df.shape}\n')
    f.write(f'Columns: {all_cols}\n')
    f.write(f'Date column: {date_col}\n')
    f.write(f'REIT columns: {reit_cols}\n')
    f.write(f'Inflation columns: {infl_cols}\n')
    f.write(f'Numeric columns: {numeric_cols}\n\n')
    f.write(f'Head:\n{df.head(20)}\n\n')
    f.write(f'Describe:\n{df.describe()}\n')

print('\nData summary saved!')
print('\nDescribe:')
print(df.describe())
