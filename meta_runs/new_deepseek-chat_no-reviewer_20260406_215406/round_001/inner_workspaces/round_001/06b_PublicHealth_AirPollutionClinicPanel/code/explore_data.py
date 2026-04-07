import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load the data
df = pd.read_csv('data/daily_panel.csv')

print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nBasic statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())

# Check unique values for categorical variables
print("\nUnique values for school_holiday:")
print(df['school_holiday'].value_counts())

# Check for negative PM2.5 values (seems odd)
print("\nRows with negative PM2.5:")
print(df[df['pm25'] < 0])
print(f"Number of negative PM2.5 values: {len(df[df['pm25'] < 0])}")

# Create output directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Save basic info to outputs
with open('outputs/data_summary.txt', 'w') as f:
    f.write(f"Data shape: {df.shape}\n")
    f.write(f"\nData types:\n{df.dtypes}\n")
    f.write(f"\nMissing values:\n{df.isnull().sum()}\n")
    f.write(f"\nBasic statistics:\n{df.describe()}\n")

print("\nExploration complete. Summary saved to outputs/data_summary.txt")