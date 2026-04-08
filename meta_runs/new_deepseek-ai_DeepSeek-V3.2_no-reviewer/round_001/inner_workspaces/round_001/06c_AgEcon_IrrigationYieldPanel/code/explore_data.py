import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
data_path = '../data/field_year_panel.csv'
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

# Check for unique plots
print("\nUnique plot_id count:", df['plot_id'].nunique())

# Create outputs directory if it doesn't exist
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Save basic statistics to file
with open('../outputs/data_summary.txt', 'w') as f:
    f.write(f"Data shape: {df.shape}\n\n")
    f.write("Summary statistics:\n")
    f.write(df.describe().to_string())
    f.write("\n\nMissing values:\n")
    f.write(df.isnull().sum().to_string())
    f.write(f"\n\nUnique plot_id count: {df['plot_id'].nunique()}")

print("\nData exploration complete. Summary saved to outputs/data_summary.txt")