import pandas as pd
import numpy as np
import os

# Load the data
df = pd.read_csv('data/sensor_panel_timeseries.csv')
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print("\nFirst 5 rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nBasic statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())
print("\nUnique assets:")
print(df['asset_id'].unique())
print(f"Number of unique assets: {df['asset_id'].nunique()}")
print("\nUnique zones:")
print(df['zone'].unique())
print(f"Number of unique zones: {df['zone'].nunique()}")
print("\nTimestamp range:")
print(f"Min: {df['timestamp_utc'].min()}")
print(f"Max: {df['timestamp_utc'].max()}")

# Check sampling cadence
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df_sorted = df.sort_values('timestamp_utc')
time_diffs = df_sorted['timestamp_utc'].diff().dropna()
print(f"\nTime differences (seconds):")
print(f"Min: {time_diffs.min().total_seconds()} sec")
print(f"Max: {time_diffs.max().total_seconds()} sec")
print(f"Mean: {time_diffs.mean().total_seconds()} sec")
print(f"Median: {time_diffs.median().total_seconds()} sec")

# Check quality flag distribution
print("\nQuality flag distribution:")
print(df['quality_flag'].value_counts())