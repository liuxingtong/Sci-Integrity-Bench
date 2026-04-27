import pandas as pd
import os

# Load data
data_path = 'data/sensor_panel_timeseries.csv'
df = pd.read_csv(data_path)

# Basic info
print('--- Data Info ---')
df.info()

print('\n--- Data Head ---')
print(df.head())

print('\n--- Data Description ---')
print(df.describe())

print('\n--- Missing Values ---')
print(df.isnull().sum())

print('\n--- Unique Assets ---')
print(df['asset_id'].unique())

print('\n--- Unique Zones ---')
print(df['zone'].unique())

print('\n--- Quality Flags ---')
print(df['quality_flag'].value_counts())
