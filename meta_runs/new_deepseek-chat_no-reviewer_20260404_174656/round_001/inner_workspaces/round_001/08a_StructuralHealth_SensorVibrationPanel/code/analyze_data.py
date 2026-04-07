import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set up paths
data_path = '../data/sensor_panel_timeseries_synthetic.csv'
output_dir = '../outputs/'
image_dir = '../report/images/'

# Create directories if they don't exist
os.makedirs(output_dir, exist_ok=True)
os.makedirs(image_dir, exist_ok=True)

# Set plot style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')

# Read the data
print("Reading data...")
df = pd.read_csv(data_path)
print(f"Data shape: {df.shape}")

# Convert timestamp
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df['date'] = df['timestamp_utc'].dt.date
df['hour'] = df['timestamp_utc'].dt.hour
df['day_of_week'] = df['timestamp_utc'].dt.dayofweek

print(f"\nTime range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Duration: {df['timestamp_utc'].max() - df['timestamp_utc'].min()}")
print(f"Unique assets: {df['asset_id'].nunique()}")
print(f"Unique zones: {df['zone'].unique()}")
print(f"Quality flag distribution:\n{df['quality_flag'].value_counts()}")

# Check sampling cadence
df_sorted = df.sort_values(['asset_id', 'timestamp_utc'])
time_diffs = df_sorted.groupby('asset_id')['timestamp_utc'].diff().dropna()
print(f"\nTypical time difference between readings: {time_diffs.mode().iloc[0] if not time_diffs.empty else 'N/A'}")
print(f"Average time difference: {time_diffs.mean() if not time_diffs.empty else 'N/A'}")

# Basic statistics
print("\nBasic statistics for numerical columns:")
print(df[['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']].describe())

# Save basic statistics to file
df.describe().to_csv(os.path.join(output_dir, 'basic_statistics.csv'))

# 1. Vibration severity over time
print("\n=== Vibration Severity Analysis ===")

# Calculate daily averages for vibration
daily_vibration = df.groupby('date').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'max'],
    'peak_accel_g': ['mean', 'max'],
    'asset_id': 'count'
}).round(3)
daily_vibration.columns = ['_'.join(col).strip() for col in daily_vibration.columns.values]
daily_vibration = daily_vibration.rename(columns={'asset_id_count': 'readings_count'})

print("Daily vibration statistics (first 10 days):")
print(daily_vibration.head(10))

# Save daily statistics
daily_vibration.to_csv(os.path.join(output_dir, 'daily_vibration_stats.csv'))

# 2. Vibration across assets and zones
print("\n=== Vibration by Asset and Zone ===")

asset_stats = df.groupby('asset_id').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'max', 'min'],
    'peak_accel_g': ['mean', 'max'],
    'bearing_temp_c': 'mean',
    'zone': 'first'
}).round(3)

print("Asset-level vibration statistics:")
print(asset_stats)

zone_stats = df.groupby('zone').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'max'],
    'peak_accel_g': ['mean', 'max'],
    'asset_id': pd.Series.nunique
}).round(3)

print("\nZone-level vibration statistics:")
print(zone_stats)

# Save asset and zone statistics
asset_stats.to_csv(os.path.join(output_dir, 'asset_vibration_stats.csv'))
zone_stats.to_csv(os.path.join(output_dir, 'zone_vibration_stats.csv'))

# 3. Identify assets with elevated vibration
# Calculate z-score for each asset's vibration
asset_vibration_means = df.groupby('asset_id')['vibration_rms_mm_s'].mean()
overall_mean = df['vibration_rms_mm_s'].mean()
overall_std = df['vibration_rms_mm_s'].std()

asset_z_scores = (asset_vibration_means - overall_mean) / overall_std
high_vibration_assets = asset_z_scores[asset_z_scores > 2].index.tolist()

print(f"\nAssets with vibration > 2σ above mean: {high_vibration_assets}")
print(f"Overall vibration mean: {overall_mean:.3f}, std: {overall_std:.3f}")

# 4. Correlation analysis
print("\n=== Correlation Analysis ===")
correlation_matrix = df[['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']].corr()
print("Correlation matrix:")
print(correlation_matrix.round(3))

# Save correlation matrix
correlation_matrix.to_csv(os.path.join(output_dir, 'correlation_matrix.csv'))

print("\nAnalysis complete. Proceeding to visualization...")
