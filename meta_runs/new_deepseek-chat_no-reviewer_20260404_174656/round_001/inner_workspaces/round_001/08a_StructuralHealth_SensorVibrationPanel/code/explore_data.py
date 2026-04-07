import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set up paths
data_path = '../data/sensor_panel_timeseries.csv'

# Read the data
print("Reading data...")
df = pd.read_csv(data_path)
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print("\nFirst few rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nBasic statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())
print("\nUnique values in categorical columns:")
print(f"Unique asset_id: {df['asset_id'].nunique()}")
print(f"Unique zones: {df['zone'].unique()}")
print(f"Unique quality_flag: {df['quality_flag'].unique()}")

# Check timestamp range
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
print(f"\nTime range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Duration: {df['timestamp_utc'].max() - df['timestamp_utc'].min()}")

# Check sampling cadence
# Sort by asset and time
df_sorted = df.sort_values(['asset_id', 'timestamp_utc'])
time_diffs = df_sorted.groupby('asset_id')['timestamp_utc'].diff().dropna()
print(f"\nTypical time difference between readings: {time_diffs.mode().iloc[0] if not time_diffs.empty else 'N/A'}")
print(f"Average time difference: {time_diffs.mean() if not time_diffs.empty else 'N/A'}")
