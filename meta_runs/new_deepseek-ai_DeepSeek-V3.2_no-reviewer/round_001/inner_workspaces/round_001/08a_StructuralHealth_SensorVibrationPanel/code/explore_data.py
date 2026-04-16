import pandas as pd
import numpy as np
import os

# Load the data
df = pd.read_csv('data/sensor_panel_timeseries.csv')

print("Data shape:", df.shape)
print("\nFirst 5 rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nBasic statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())
print("\nUnique assets:", df['asset_id'].nunique())
print("Unique zones:", df['zone'].nunique())
print("\nSample of unique asset IDs:", df['asset_id'].unique()[:10])
print("Sample of unique zones:", df['zone'].unique()[:10])

# Check timestamp range
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
print("\nTimestamp range:")
print("Start:", df['timestamp_utc'].min())
print("End:", df['timestamp_utc'].max())
print("Duration:", df['timestamp_utc'].max() - df['timestamp_utc'].min())

# Check sampling frequency
print("\nSampling analysis:")
for asset in df['asset_id'].unique()[:3]:
    asset_data = df[df['asset_id'] == asset].sort_values('timestamp_utc')
    time_diffs = asset_data['timestamp_utc'].diff().dropna()
    print(f"Asset {asset}: {len(asset_data)} records")
    if len(time_diffs) > 0:
        print(f"  Average time between samples: {time_diffs.mean()}")
        print(f"  Min time between samples: {time_diffs.min()}")
        print(f"  Max time between samples: {time_diffs.max()}")