import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
data_path = '../data/reit_macro_quarterly.csv'
df = pd.read_csv(data_path)
print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nSummary statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())

# Check for any patterns in quarter column
print("\nQuarter column unique values:", df['quarter'].unique()[:10])
print("Quarter range:", df['quarter'].min(), "to", df['quarter'].max())

# Create output directory if it doesn't exist
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Basic time series plot
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Plot inflation
axes[0].plot(df['quarter'], df['inflation_yoy'], marker='o', linewidth=2)
axes[0].set_title('Inflation (Year-over-Year) Over Time')
axes[0].set_xlabel('Quarter')
axes[0].set_ylabel('Inflation (%)')
axes[0].grid(True, alpha=0.3)

# Plot REIT returns
axes[1].plot(df['quarter'], df['reit_index_return'], marker='o', linewidth=2, color='green')
axes[1].set_title('REIT Index Returns Over Time')
axes[1].set_xlabel('Quarter')
axes[1].set_ylabel('REIT Return')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/time_series_plots.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nBasic exploration complete. Time series plots saved.")