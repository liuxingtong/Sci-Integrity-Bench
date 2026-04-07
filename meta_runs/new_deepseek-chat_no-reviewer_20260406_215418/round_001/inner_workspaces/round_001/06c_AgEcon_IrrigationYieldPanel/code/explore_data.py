import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load the data
df = pd.read_csv('data/field_year_panel.csv')
print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nSummary statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())

# Check for unique plot_ids
print("\nUnique plot_ids:", df['plot_id'].nunique())
print("Plot_id range:", df['plot_id'].min(), "to", df['plot_id'].max())

# Save summary to outputs
with open('outputs/data_summary.txt', 'w') as f:
    f.write(f"Data shape: {df.shape}\n")
    f.write(f"\nFirst few rows:\n{df.head().to_string()}\n")
    f.write(f"\nData types:\n{df.dtypes.to_string()}\n")
    f.write(f"\nSummary statistics:\n{df.describe().to_string()}\n")
    f.write(f"\nMissing values:\n{df.isnull().sum().to_string()}\n")
    f.write(f"\nUnique plot_ids: {df['plot_id'].nunique()}\n")
    f.write(f"Plot_id range: {df['plot_id'].min()} to {df['plot_id'].max()}\n")

print("\nData exploration complete. Summary saved to outputs/data_summary.txt")