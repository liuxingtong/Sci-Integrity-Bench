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

# Identify key columns
print('\nColumn info:')
for col in df.columns:
    print(f'  {col}: {df[col].dtype}, non-null: {df[col].notna().sum()}')

# Save to file for reference
with open('outputs/column_info.txt', 'w') as f:
    f.write(f'Shape: {df.shape}\n')
    f.write(f'Columns: {df.columns.tolist()}\n\n')
    f.write('Column details:\n')
    for col in df.columns:
        f.write(f'  {col}: {df[col].dtype}, non-null: {df[col].notna().sum()}\n')
    f.write(f'\nHead:\n{df.head(20)}\n')
    f.write(f'\nDescribe:\n{df.describe()}\n')

print('Done!')
