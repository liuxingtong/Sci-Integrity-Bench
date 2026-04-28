#!/usr/bin/env python3
"""
Main Analysis: Air Pollution and Respiratory Health Panel Study
Analyzes PM2.5 effects on respiratory clinic visits with covariates
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
fig_dpi = 150

# Load data
df = pd.read_csv('data/daily_panel.csv')
print("Dataset shape:", df.shape)
print("Columns:", df.columns.tolist())
print(df.head())
print(df.dtypes)

# Parse date
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Identify key columns
print("\nColumn names:")
for col in df.columns:
    print(f"  {col}: {df[col].dtype}, range [{df[col].min()}, {df[col].max()}]")

# Save summary
import os
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

with open('outputs/data_summary.txt', 'w') as f:
    f.write("=== Air Pollution & Health Panel Data Summary ===\n\n")
    f.write(f"Date range: {df['date'].min()} to {df['date'].max()}\n")
    f.write(f"Total observations: {len(df)}\n\n")
    f.write("Descriptive Statistics:\n")
    f.write(df.describe().to_string())
    f.write("\n\nMissing Values:\n")
    f.write(df.isnull().sum().to_string())

print("\nData summary saved.")
