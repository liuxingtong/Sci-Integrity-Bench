import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data/sensor_panel_timeseries.csv')
print('Shape:', df.shape)
print('\nColumns:', df.columns.tolist())
print('\nDtypes:')
print(df.dtypes)
print('\nFirst 5 rows:')
print(df.head())
print('\nDescribe:')
print(df.describe())
print('\nUnique assets:', df['asset_id'].unique() if 'asset_id' in df.columns else 'N/A')
print('\nUnique zones:', df['zone'].unique() if 'zone' in df.columns else 'N/A')
if 'quality_flag' in df.columns:
    print('\nQuality flags:', df['quality_flag'].value_counts())
if 'timestamp_utc' in df.columns:
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
    print('\nTime range:', df['timestamp_utc'].min(), 'to', df['timestamp_utc'].max())
    print('Duration:', df['timestamp_utc'].max() - df['timestamp_utc'].min())
