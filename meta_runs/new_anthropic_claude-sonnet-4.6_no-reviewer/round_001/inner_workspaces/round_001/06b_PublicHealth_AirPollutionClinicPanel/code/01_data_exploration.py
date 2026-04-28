#!/usr/bin/env python3
"""
Data Exploration for Air Pollution and Health Panel Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')

# Load data
df = pd.read_csv('data/daily_panel.csv')
print("Dataset shape:", df.shape)
print("\nColumn names:", df.columns.tolist())
print("\nData types:")
print(df.dtypes)
print("\nFirst 5 rows:")
print(df.head())
print("\nDescriptive statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())

# Save summary to outputs
with open('outputs/data_summary.txt', 'w') as f:
    f.write("Dataset shape: {}\n".format(df.shape))
    f.write("\nColumn names: {}\n".format(df.columns.tolist()))
    f.write("\nData types:\n{}\n".format(df.dtypes))
    f.write("\nDescriptive statistics:\n{}\n".format(df.describe()))
    f.write("\nMissing values:\n{}\n".format(df.isnull().sum()))

print("\nData exploration complete. Summary saved to outputs/data_summary.txt")
