import pandas as pd
import numpy as np
import os

# Read the data
df = pd.read_csv('data/sensor_panel_timeseries.csv')

print("Data shape:", df.shape)
print("\nFirst 10 rows:")
print(df.head(10))
print("\nData types:")
print(df.dtypes)
print("\nBasic statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())
print("\nUnique assets:", df['asset_id'].unique())
print("\nUnique zones:", df['zone'].unique())
print("\nTimestamp range:")
print("Min:", df['timestamp_utc'].min())
print("Max:", df['timestamp_utc'].max())

# Check sampling frequency
if 'timestamp_utc' in df.columns:
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
    time_diff = df.groupby('asset_id')['timestamp_utc'].diff().dropna()
    print("\nTypical time intervals (seconds):")
    print(time_diff.dt.total_seconds().describe())
