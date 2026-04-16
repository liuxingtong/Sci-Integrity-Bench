import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Load the synthetic data
df = pd.read_csv('data/sensor_panel_timeseries_synthetic.csv')

# Convert timestamp to datetime
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

print("=== DATA OVERVIEW ===")
print(f"Total records: {len(df)}")
print(f"Time range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Duration: {df['timestamp_utc'].max() - df['timestamp_utc'].min()}")
print(f"Assets: {df['asset_id'].nunique()}")
print(f"Zones: {df['zone'].nunique()}")
print(f"Unique assets: {sorted(df['asset_id'].unique())}")
print(f"Unique zones: {sorted(df['zone'].unique())}")

# Check sampling frequency
print("\n=== SAMPLING ANALYSIS ===")
sampling_stats = []
for asset in df['asset_id'].unique():
    for zone in df['zone'].unique():
        subset = df[(df['asset_id'] == asset) & (df['zone'] == zone)].sort_values('timestamp_utc')
        if len(subset) > 1:
            time_diffs = subset['timestamp_utc'].diff().dropna()
            avg_interval = time_diffs.mean()
            sampling_stats.append({
                'asset': asset,
                'zone': zone,
                'n_samples': len(subset),
                'avg_interval_hours': avg_interval.total_seconds() / 3600,
                'data_coverage': len(subset) / len(df[df['asset_id'] == asset][df['zone'] == zone])
            })

sampling_df = pd.DataFrame(sampling_stats)
print(sampling_df.to_string())

# Basic statistics by asset and zone
print("\n=== DESCRIPTIVE STATISTICS BY ASSET ===")
for col in ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']:
    print(f"\n{col} by asset:")
    stats = df.groupby('asset_id')[col].agg(['mean', 'std', 'min', 'max', 'median']).round(3)
    print(stats)

print("\n=== DESCRIPTIVE STATISTICS BY ZONE ===")
for col in ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c']:
    print(f"\n{col} by zone:")
    stats = df.groupby('zone')[col].agg(['mean', 'std', 'min', 'max', 'median']).round(3)
    print(stats)

# Quality flag analysis
print("\n=== QUALITY FLAG DISTRIBUTION ===")
quality_dist = df['quality_flag'].value_counts()
print(quality_dist)
print(f"\nPercentage of GOOD records: {quality_dist.get('GOOD', 0) / len(df) * 100:.1f}%")

# Save summary statistics to file
summary_stats = df.describe()
summary_stats.to_csv('outputs/summary_statistics.csv')
print("\nSummary statistics saved to outputs/summary_statistics.csv")

# Create time series visualization for key metrics
print("\n=== GENERATING VISUALIZATIONS ===")

# 1. Time series of vibration for each asset (averaged by day)
df['date'] = df['timestamp_utc'].dt.date
vibration_by_day = df.groupby(['date', 'asset_id'])['vibration_rms_mm_s'].mean().reset_index()

plt.figure(figsize=(12, 6))
for asset in df['asset_id'].unique():
    asset_data = vibration_by_day[vibration_by_day['asset_id'] == asset]
    plt.plot(asset_data['date'], asset_data['vibration_rms_mm_s'], 
             label=asset, linewidth=2, alpha=0.8)

plt.xlabel('Date')
plt.ylabel('Vibration RMS (mm/s)')
plt.title('Daily Average Vibration RMS by Asset')
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/vibration_timeseries_by_asset.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/vibration_timeseries_by_asset.png")

# 2. Box plot of vibration by asset and zone
plt.figure(figsize=(14, 6))
sns.boxplot(x='asset_id', y='vibration_rms_mm_s', hue='zone', data=df)
plt.xlabel('Asset ID')
plt.ylabel('Vibration RMS (mm/s)')
plt.title('Vibration Distribution by Asset and Zone')
plt.legend(title='Zone')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/vibration_boxplot_by_asset_zone.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/vibration_boxplot_by_asset_zone.png")

# 3. Correlation heatmap
correlation_cols = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
corr_matrix = df[correlation_cols].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
            square=True, linewidths=1, cbar_kws={"shrink": 0.8})
plt.title('Correlation Matrix of Sensor Metrics')
plt.tight_layout()
plt.savefig('report/images/correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/correlation_heatmap.png")

# 4. Scatter plot: vibration vs bearing temperature
plt.figure(figsize=(10, 6))
scatter = plt.scatter(df['vibration_rms_mm_s'], df['bearing_temp_c'], 
                     c=df['load_pct'], alpha=0.6, cmap='viridis', s=20)
plt.colorbar(scatter, label='Load (%)')
plt.xlabel('Vibration RMS (mm/s)')
plt.ylabel('Bearing Temperature (°C)')
plt.title('Vibration vs Bearing Temperature (colored by Load)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/vibration_vs_temperature.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/vibration_vs_temperature.png")

# 5. Asset 001 anomaly detection (developing fault)
asset_001_data = df[df['asset_id'] == 'ASSET_001'].copy()
asset_001_data = asset_001_data.sort_values('timestamp_utc')

plt.figure(figsize=(14, 10))

# Subplot 1: Vibration
plt.subplot(3, 1, 1)
for zone in asset_001_data['zone'].unique():
    zone_data = asset_001_data[asset_001_data['zone'] == zone]
    plt.plot(zone_data['timestamp_utc'], zone_data['vibration_rms_mm_s'], 
             label=f'{zone} Vibration', linewidth=2)
plt.ylabel('Vibration RMS (mm/s)')
plt.title('ASSET_001: Developing Fault Indicators')
plt.legend()
plt.grid(True, alpha=0.3)

# Subplot 2: Temperature
plt.subplot(3, 1, 2)
for zone in asset_001_data['zone'].unique():
    zone_data = asset_001_data[asset_001_data['zone'] == zone]
    plt.plot(zone_data['timestamp_utc'], zone_data['bearing_temp_c'], 
             label=f'{zone} Temperature', linewidth=2)
plt.ylabel('Temperature (°C)')
plt.legend()
plt.grid(True, alpha=0.3)

# Subplot 3: Peak Acceleration
plt.subplot(3, 1, 3)
for zone in asset_001_data['zone'].unique():
    zone_data = asset_001_data[asset_001_data['zone'] == zone]
    plt.plot(zone_data['timestamp_utc'], zone_data['peak_accel_g'], 
             label=f'{zone} Peak Accel', linewidth=2)
plt.ylabel('Peak Acceleration (g)')
plt.xlabel('Timestamp')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/asset_001_anomaly_detection.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/asset_001_anomaly_detection.png")

# 6. Load vs RPM relationship
plt.figure(figsize=(10, 6))
for asset in df['asset_id'].unique()[:3]:  # Show first 3 assets for clarity
    asset_data = df[df['asset_id'] == asset]
    plt.scatter(asset_data['rpm'], asset_data['load_pct'], 
               label=asset, alpha=0.5, s=20)
plt.xlabel('RPM')
plt.ylabel('Load (%)')
plt.title('RPM vs Load Relationship by Asset')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/rpm_vs_load.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/rpm_vs_load.png")

print("\n=== ANALYSIS COMPLETE ===")