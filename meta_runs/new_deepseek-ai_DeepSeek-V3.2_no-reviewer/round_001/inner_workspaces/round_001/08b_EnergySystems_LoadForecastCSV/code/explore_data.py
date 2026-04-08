import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load the data
df = pd.read_csv('data/load_15min.csv')
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"First few rows:\n{df.head()}")
print(f"Last few rows:\n{df.tail()}")

# Convert timestamp to datetime
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
print(f"\nDate range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Time span: {df['timestamp_utc'].max() - df['timestamp_utc'].min()}")

# Check for missing values
print(f"\nMissing values:\n{df.isnull().sum()}")

# Basic statistics
print(f"\nLoad statistics:")
print(df['load_mw'].describe())

# Check data frequency
print(f"\nTime intervals (first 10):")
time_diffs = df['timestamp_utc'].diff().dropna()
print(time_diffs.head(10))
print(f"\nUnique time intervals: {time_diffs.unique()}")

# Create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Save basic info to file
with open('outputs/data_summary.txt', 'w') as f:
    f.write(f"Data shape: {df.shape}\n")
    f.write(f"Date range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}\n")
    f.write(f"Time span: {df['timestamp_utc'].max() - df['timestamp_utc'].min()}\n")
    f.write(f"\nLoad statistics:\n{df['load_mw'].describe().to_string()}\n")
