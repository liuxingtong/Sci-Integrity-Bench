#!/usr/bin/env python3
"""
Retail Analytics: Ad Spend & Store Sales Analysis
Policy RET-ADV-ROLL: Monthly online ad budget = fixed share of prior-month same-store sales
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print('Loading data...')
df = pd.read_csv('data/store_monthly_sales.csv')
print(f'Shape: {df.shape}')
print(f'Columns: {df.columns.tolist()}')
print(f'Dtypes:\n{df.dtypes}')
print(f'\nFirst 5 rows:\n{df.head()}')
print(f'\nDescribe:\n{df.describe()}')
print(f'\nMissing values:\n{df.isnull().sum()}')

# Save basic info
with open('outputs/data_summary.txt', 'w') as f:
    f.write(f'Shape: {df.shape}\n')
    f.write(f'Columns: {df.columns.tolist()}\n')
    f.write(f'Dtypes:\n{df.dtypes}\n')
    f.write(f'\nFirst 5 rows:\n{df.head().to_string()}\n')
    f.write(f'\nDescribe:\n{df.describe().to_string()}\n')
    f.write(f'\nMissing values:\n{df.isnull().sum().to_string()}\n')

print('\nData loaded and summary saved.')
