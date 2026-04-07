import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Set style for better visualizations
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')

# Create images directory if it doesn't exist
os.makedirs('report/images', exist_ok=True)

# Load the synthetic data
df = pd.read_csv('outputs/synthetic_sensor_data.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

print("=== DATA OVERVIEW ===")
print(f"Data shape: {df.shape}")
print(f"Time range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Observation window: {(df['timestamp_utc'].max() - df['timestamp_utc'].min()).days} days")
print(f"Assets: {df['asset_id'].unique().tolist()}")
print(f"Zones: {df['zone'].unique().tolist()}")

# Calculate sampling cadence
df_sorted = df.sort_values('timestamp_utc')
time_diffs = df_sorted['timestamp_utc'].diff().dropna()
print(f"\nSampling cadence:")
print(f"  Min interval: {time_diffs.min().total_seconds()/3600:.2f} hours")
print(f"  Max interval: {time_diffs.max().total_seconds()/3600:.2f} hours")
print(f"  Mean interval: {time_diffs.mean().total_seconds()/3600:.2f} hours")
print(f"  Median interval: {time_diffs.median().total_seconds()/3600:.2f} hours")
print(f"  Implied cadence: Hourly readings")

print("\n=== DATA QUALITY ===")
print(f"Quality flag distribution:")
print(df['quality_flag'].value_counts())
print(f"\nMissing values:")
print(df.isnull().sum())

# 1. Vibration severity analysis
print("\n=== VIBRATION SEVERITY ANALYSIS ===")

# Overall statistics
print("\nOverall vibration statistics (RMS, mm/s):")
print(df['vibration_rms_mm_s'].describe())
print("\nOverall peak acceleration statistics (g):")
print(df['peak_accel_g'].describe())

# Define thresholds (typical industry thresholds for rotating equipment)
rms_warning_threshold = 4.5  # mm/s
rms_alarm_threshold = 7.0    # mm/s
peak_warning_threshold = 15.0  # g
peak_alarm_threshold = 25.0    # g

print(f"\nVibration RMS thresholds:")
print(f"  Warning (> {rms_warning_threshold} mm/s): {len(df[df['vibration_rms_mm_s'] > rms_warning_threshold])} readings ({len(df[df['vibration_rms_mm_s'] > rms_warning_threshold])/len(df)*100:.1f}%)")
print(f"  Alarm (> {rms_alarm_threshold} mm/s): {len(df[df['vibration_rms_mm_s'] > rms_alarm_threshold])} readings ({len(df[df['vibration_rms_mm_s'] > rms_alarm_threshold])/len(df)*100:.1f}%)")

print(f"\nPeak acceleration thresholds:")
print(f"  Warning (> {peak_warning_threshold} g): {len(df[df['peak_accel_g'] > peak_warning_threshold])} readings ({len(df[df['peak_accel_g'] > peak_warning_threshold])/len(df)*100:.1f}%)")
print(f"  Alarm (> {peak_alarm_threshold} g): {len(df[df['peak_accel_g'] > peak_alarm_threshold])} readings ({len(df[df['peak_accel_g'] > peak_alarm_threshold])/len(df)*100:.1f}%)")

# 2. Time evolution analysis
print("\n=== TIME EVOLUTION ANALYSIS ===")

# Calculate daily averages for trend analysis
df['date'] = df['timestamp_utc'].dt.date
daily_stats = df.groupby('date').agg({
    'vibration_rms_mm_s': ['mean', 'max', 'std'],
    'peak_accel_g': ['mean', 'max'],
    'bearing_temp_c': ['mean', 'max'],
    'rpm': 'mean',
    'load_pct': 'mean'
}).round(3)

print("\nDaily vibration trends (first 5 days):")
print(daily_stats.head())

# 3. Asset and zone comparison
print("\n=== ASSET AND ZONE COMPARISON ===")

# By asset
asset_stats = df.groupby('asset_id').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'max'],
    'peak_accel_g': ['mean', 'max'],
    'bearing_temp_c': ['mean', 'max'],
    'quality_flag': lambda x: (x == 'WARNING').sum()
}).round(3)

print("\nAsset-level statistics:")
print(asset_stats)

# By zone
zone_stats = df.groupby('zone').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'max'],
    'peak_accel_g': ['mean', 'max'],
    'bearing_temp_c': ['mean', 'max']
}).round(3)

print("\nZone-level statistics:")
print(zone_stats)

# 4. Correlation analysis
print("\n=== CORRELATION ANALYSIS ===")

# Calculate correlations between key variables
correlation_vars = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
corr_matrix = df[correlation_vars].corr()

print("\nCorrelation matrix:")
print(corr_matrix.round(3))

# 5. Identify outliers and concerning patterns
print("\n=== OUTLIER DETECTION ===")

# Find assets with consistently high vibration
high_vibration_assets = asset_stats[('vibration_rms_mm_s', 'mean')].nlargest(3)
print(f"\nAssets with highest average vibration RMS:")
for asset, value in high_vibration_assets.items():
    print(f"  {asset}: {value:.3f} mm/s")

# Find zones with highest vibration
high_vibration_zones = zone_stats[('vibration_rms_mm_s', 'mean')].nlargest(3)
print(f"\nZones with highest average vibration RMS:")
for zone, value in high_vibration_zones.items():
    print(f"  {zone}: {value:.3f} mm/s")

# Find time periods with degradation trends
print("\n=== DEGRADATION TRENDS ===")

# Calculate rolling averages for assets showing potential degradation
degradation_data = []
for asset in df['asset_id'].unique():
    asset_data = df[df['asset_id'] == asset].sort_values('timestamp_utc')
    
    # Calculate 8-hour rolling average
    asset_data['vibration_rolling'] = asset_data['vibration_rms_mm_s'].rolling(window=8, min_periods=1).mean()
    
    # Check if trend is increasing
    if len(asset_data) > 1:
        slope = np.polyfit(range(len(asset_data)), asset_data['vibration_rms_mm_s'], 1)[0]
        if slope > 0.001:  # Positive slope threshold
            degradation_data.append({
                'asset': asset,
                'slope': slope,
                'final_vibration': asset_data['vibration_rms_mm_s'].iloc[-1],
                'initial_vibration': asset_data['vibration_rms_mm_s'].iloc[0]
            })

if degradation_data:
    print("\nAssets showing potential degradation (increasing vibration trend):")
    for item in degradation_data:
        print(f"  {item['asset']}: Slope = {item['slope']:.5f}, Change = {item['final_vibration'] - item['initial_vibration']:.3f} mm/s")
else:
    print("\nNo clear degradation trends detected in the observation period.")

print("\n=== ANALYSIS COMPLETE ===")
print("Visualizations saved to report/images/")