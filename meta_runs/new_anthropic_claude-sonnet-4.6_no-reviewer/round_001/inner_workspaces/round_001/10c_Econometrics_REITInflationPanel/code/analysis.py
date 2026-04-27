#!/usr/bin/env python3
"""
REIT-Inflation Panel Analysis
Association analysis between REIT index returns and inflation
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
print(f'Dtypes:\n{df.dtypes}')
print(f'Head:\n{df.head(10)}')
print(f'Describe:\n{df.describe()}')

# Save exploration results
with open('outputs/data_exploration.txt', 'w') as f:
    f.write(f'Shape: {df.shape}\n')
    f.write(f'Columns: {df.columns.tolist()}\n')
    f.write(f'Dtypes:\n{df.dtypes}\n\n')
    f.write(f'Head:\n{df.head(20)}\n\n')
    f.write(f'Describe:\n{df.describe()}\n\n')
    f.write(f'Missing values:\n{df.isnull().sum()}\n')

print('Data loaded successfully!')
