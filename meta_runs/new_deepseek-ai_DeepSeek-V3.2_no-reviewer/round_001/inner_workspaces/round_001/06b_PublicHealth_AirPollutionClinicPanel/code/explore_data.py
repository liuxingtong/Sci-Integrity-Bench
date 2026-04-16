import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load the data
data_path = '../data/daily_panel.csv'
df = pd.read_csv(data_path)

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
print("\nUnique values in school_holiday:", df['school_holiday'].unique())
print("Count of school holidays:", df['school_holiday'].sum())

# Create output directory if it doesn't exist
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Save basic summary to outputs
summary_path = '../outputs/data_summary.txt'
with open(summary_path, 'w') as f:
    f.write(f"Data shape: {df.shape}\n\n")
    f.write(f"Columns: {list(df.columns)}\n\n")
    f.write(f"Data types:\n{df.dtypes}\n\n")
    f.write(f"Basic statistics:\n{df.describe()}\n\n")
    f.write(f"Missing values:\n{df.isnull().sum()}\n\n")
    f.write(f"School holiday distribution:\n{df['school_holiday'].value_counts()}\n")

print(f"\nSummary saved to {summary_path}")