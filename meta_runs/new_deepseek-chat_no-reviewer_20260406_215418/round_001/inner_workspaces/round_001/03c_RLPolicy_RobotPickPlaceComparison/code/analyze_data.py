import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
data_path = "../data/pick_place_metrics.csv"
df = pd.read_csv(data_path)
print("Data loaded successfully!")
print(f"Shape: {df.shape}")
print("\nFirst few rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nUnique metrics:")
print(df['metric'].unique())
print("\nUnique arms (policies):")
print(df['arm'].unique())

# Create a summary dataframe
df_summary = df.copy()
print("\n\nSummary statistics:")
print(df_summary.describe())

# Save summary to outputs
os.makedirs("outputs", exist_ok=True)
df_summary.to_csv("outputs/data_summary.csv", index=False)
print("\nData summary saved to outputs/data_summary.csv")
