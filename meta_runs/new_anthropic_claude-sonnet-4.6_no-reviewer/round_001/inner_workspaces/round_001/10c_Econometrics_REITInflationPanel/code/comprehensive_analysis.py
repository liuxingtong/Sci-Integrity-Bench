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

# Save basic info
with open('outputs/data_info.txt', 'w') as f:
    f.write(f'Shape: {df.shape}\n')
    f.write(f'Columns: {df.columns.tolist()}\n')
    f.write(f'Dtypes:\n{df.dtypes}\n\n')
    f.write(f'Head:\n{df.head(10)}\n\n')
    f.write(f'Describe:\n{df.describe()}\n')
    f.write(f'Missing:\n{df.isnull().sum()}\n')

print('Data info saved!')
