import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load the data
data_path = '../data/island_species.csv'
df = pd.read_csv(data_path)

print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nData info:")
print(df.info())
print("\nSummary statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())

# Create output directory if it doesn't exist
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Save basic statistics to file
with open('../outputs/data_summary.txt', 'w') as f:
    f.write(f"Data shape: {df.shape}\n\n")
    f.write(f"Summary statistics:\n{df.describe().to_string()}\n\n")
    f.write(f"Missing values:\n{df.isnull().sum().to_string()}\n")

print("\nData exploration complete. Summary saved to outputs/data_summary.txt")