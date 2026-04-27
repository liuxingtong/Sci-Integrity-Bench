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

# ============================================================
# 1. DATA PREPARATION
# ============================================================

# Based on column analysis, identify key variables
# The data has: date/quarter column, REIT returns, inflation, and other macro vars

# Try to parse date column
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
elif 'quarter' in df.columns:
    df = df.sort_values('quarter').reset_index(drop=True)
elif 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)

# Identify REIT return column(s)
reit_cols = [c for c in df.columns if 'reit' in c.lower()]
infl_cols = [c for c in df.columns if 'infl' in c.lower() or 'cpi' in c.lower() or 'pce' in c.lower()]

print(f'REIT columns: {reit_cols}')
print(f'Inflation columns: {infl_cols}')
print(f'\nAll columns: {df.columns.tolist()}')
print(f'\nHead:\n{df.head(10)}')
print(f'\nDescribe:\n{df.describe()}')

# Save summary stats
df.describe().to_csv('outputs/summary_stats.csv')

print('\nData preparation complete!')
