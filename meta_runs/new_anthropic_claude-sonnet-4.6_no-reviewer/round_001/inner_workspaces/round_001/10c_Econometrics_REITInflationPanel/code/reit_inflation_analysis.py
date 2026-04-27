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
print(f'\nHead:\n{df.head()}')

# ============================================================
# 1. DATA PREPARATION
# ============================================================

# Identify date/time column
date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower() or 'quarter' in c.lower() or 'year' in c.lower() or 'period' in c.lower()]
print(f'\nPotential date columns: {date_cols}')

# Identify REIT return columns
reit_cols = [c for c in df.columns if 'reit' in c.lower() or 'return' in c.lower() or 'ret' in c.lower()]
print(f'Potential REIT columns: {reit_cols}')

# Identify inflation columns
infl_cols = [c for c in df.columns if 'infl' in c.lower() or 'cpi' in c.lower() or 'pce' in c.lower() or 'price' in c.lower()]
print(f'Potential inflation columns: {infl_cols}')

# Identify other macro columns
macro_cols = [c for c in df.columns if c not in date_cols + reit_cols + infl_cols]
print(f'Other macro columns: {macro_cols}')

# Save column analysis
with open('outputs/column_analysis.txt', 'w') as f:
    f.write(f'Shape: {df.shape}\n')
    f.write(f'All columns: {df.columns.tolist()}\n\n')
    f.write(f'Date columns: {date_cols}\n')
    f.write(f'REIT columns: {reit_cols}\n')
    f.write(f'Inflation columns: {infl_cols}\n')
    f.write(f'Other macro columns: {macro_cols}\n\n')
    f.write(f'Head:\n{df.head(20)}\n\n')
    f.write(f'Describe:\n{df.describe()}\n')

print('\nColumn analysis saved!')
print('\nFull describe:')
print(df.describe())
