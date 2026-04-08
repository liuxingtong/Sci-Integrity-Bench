import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('../data/reit_macro_quarterly.csv')
print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nData info:")
print(df.info())
print("\nDescriptive statistics:")
print(df.describe())

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Save basic stats to file
with open('outputs/basic_stats.txt', 'w') as f:
    f.write(f"Data shape: {df.shape}\n")
    f.write(f"\nDescriptive statistics:\n{df.describe().to_string()}\n")
    f.write(f"\nMissing values:\n{df.isnull().sum().to_string()}\n")

print("\nBasic exploration complete. Results saved to outputs/basic_stats.txt")