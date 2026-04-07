import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Set style for better visualizations
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load the data
print("Loading sensor data...")
df = pd.read_csv('../data/sensor_panel_timeseries.csv')

# Convert timestamp to datetime
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

print(f"Data loaded: {len(df)} rows")
print(f"Time range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Assets: {df['asset_id'].unique()}")
print(f"Zones: {df['zone'].unique()}")
print(f"\nData columns: {df.columns.tolist()}")

# 1. Data validation and overview
print("\n" + "="*60)
print("1. DATA VALIDATION AND OVERVIEW")
print("="*60)

# Check for missing values
missing_values = df.isnull().sum()
print(f"\nMissing values per column:")
print(missing_values[missing_values > 0] if missing_values.sum() > 0 else "No missing values")

# Check quality flag distribution
print(f"\nQuality flag distribution:")
print(df['quality_flag'].value_counts())

# Calculate effective sampling cadence
time_diffs = df.groupby(['asset_id', 'zone'])['timestamp_utc'].diff().dropna()
if len(time_diffs) > 0:
    avg_cadence = time_diffs.mean()
    print(f"\nAverage sampling cadence: {avg_cadence}")
    print(f"Most common cadence: {time_diffs.mode().iloc[0] if len(time_diffs.mode()) > 0 else 'N/A'}")

# 2. Vibration analysis by asset and zone
print("\n" + "="*60)
print("2. VIBRATION ANALYSIS BY ASSET AND ZONE")
print("="*60)

# Calculate summary statistics by asset and zone
vibration_stats = df.groupby(['asset_id', 'zone'])['vibration_rms_mm_s'].agg([
    'count', 'mean', 'std', 'min', 'max',
    lambda x: np.percentile(x, 95),  # 95th percentile
    lambda x: np.percentile(x, 5)    # 5th percentile
]).round(3)

vibration_stats.columns = ['count', 'mean', 'std', 'min', 'max', 'p95', 'p5']
print("\nVibration RMS (mm/s) statistics by asset and zone:")
print(vibration_stats)

# Save statistics to CSV
vibration_stats.to_csv('../outputs/vibration_stats_by_asset_zone.csv')
print("\nSaved vibration statistics to outputs/vibration_stats_by_asset_zone.csv")

# 3. Identify assets/zones above typical behavior
print("\n" + "="*60)
print("3. IDENTIFYING ASSETS/ZONES ABOVE TYPICAL BEHAVIOR")
print("="*60)

# Calculate fleet-wide benchmarks
fleet_mean_vibration = df['vibration_rms_mm_s'].mean()
fleet_std_vibration = df['vibration_rms_mm_s'].std()
fleet_p95_vibration = np.percentile(df['vibration_rms_mm_s'], 95)

print(f"\nFleet-wide vibration benchmarks:")
print(f"  Mean: {fleet_mean_vibration:.3f} mm/s")
print(f"  Std: {fleet_std_vibration:.3f} mm/s")
print(f"  95th percentile: {fleet_p95_vibration:.3f} mm/s")

# Identify outliers (above 95th percentile)
outlier_threshold = fleet_p95_vibration
high_vibration_assets = df[df['vibration_rms_mm_s'] > outlier_threshold]

print(f"\nAssets with vibration above {outlier_threshold:.3f} mm/s (95th percentile):")
print(f"  Count: {len(high_vibration_assets)} records ({len(high_vibration_assets)/len(df)*100:.1f}% of total)")

if len(high_vibration_assets) > 0:
    outlier_summary = high_vibration_assets.groupby(['asset_id', 'zone']).size().reset_index(name='count')
    outlier_summary = outlier_summary.sort_values('count', ascending=False)
    print("\nBreakdown by asset and zone:")
    print(outlier_summary)
    
    # Save outlier summary
    outlier_summary.to_csv('../outputs/high_vibration_assets.csv', index=False)
    print("\nSaved high vibration assets summary to outputs/high_vibration_assets.csv")

# 4. Time evolution analysis
print("\n" + "="*60)
print("4. TIME EVOLUTION ANALYSIS")
print("="*60)

# Add date features for time analysis
df['date'] = df['timestamp_utc'].dt.date
df['week'] = df['timestamp_utc'].dt.isocalendar().week

# Calculate daily averages for trend analysis
daily_vibration = df.groupby(['asset_id', 'zone', 'date'])['vibration_rms_mm_s'].mean().reset_index()
weekly_vibration = df.groupby(['asset_id', 'zone', 'week'])['vibration_rms_mm_s'].mean().reset_index()

print(f"\nCalculated daily and weekly vibration trends")
print(f"Daily records: {len(daily_vibration)}")
print(f"Weekly records: {len(weekly_vibration)}")

# 5. Correlation analysis with other parameters
print("\n" + "="*60)
print("5. CORRELATION ANALYSIS")
print("="*60)

# Calculate correlation matrix for numerical variables
numerical_cols = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
correlation_matrix = df[numerical_cols].corr()

print("\nCorrelation matrix:")
print(correlation_matrix.round(3))

# Save correlation matrix
correlation_matrix.to_csv('../outputs/correlation_matrix.csv')
print("\nSaved correlation matrix to outputs/correlation_matrix.csv")

# 6. Generate visualizations
print("\n" + "="*60)
print("6. GENERATING VISUALIZATIONS")
print("="*60)

# Figure 1: Vibration distribution by asset
plt.figure(figsize=(12, 6))
sns.boxplot(x='asset_id', y='vibration_rms_mm_s', data=df)
plt.axhline(y=fleet_p95_vibration, color='r', linestyle='--', alpha=0.7, label=f'95th percentile ({fleet_p95_vibration:.2f} mm/s)')
plt.title('Vibration RMS Distribution by Asset', fontsize=14, fontweight='bold')
plt.xlabel('Asset ID', fontsize=12)
plt.ylabel('Vibration RMS (mm/s)', fontsize=12)
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/vibration_by_asset.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/vibration_by_asset.png")
plt.close()

# Figure 2: Vibration by zone
plt.figure(figsize=(10, 6))
sns.boxplot(x='zone', y='vibration_rms_mm_s', data=df)
plt.title('Vibration RMS Distribution by Zone', fontsize=14, fontweight='bold')
plt.xlabel('Zone', fontsize=12)
plt.ylabel('Vibration RMS (mm/s)', fontsize=12)
plt.tight_layout()
plt.savefig('../report/images/vibration_by_zone.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/vibration_by_zone.png")
plt.close()

# Figure 3: Time series for ASSET_004 (problem asset)
asset_004_data = df[df['asset_id'] == 'ASSET_004']
if len(asset_004_data) > 0:
    plt.figure(figsize=(14, 8))
    
    for zone in asset_004_data['zone'].unique():
        zone_data = asset_004_data[asset_004_data['zone'] == zone]
        # Resample to daily average for cleaner plot
        zone_daily = zone_data.set_index('timestamp_utc').resample('D')['vibration_rms_mm_s'].mean()
        plt.plot(zone_daily.index, zone_daily.values, label=zone, linewidth=2)
    
    plt.title('ASSET_004: Vibration RMS Trend Over Time', fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Vibration RMS (mm/s)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('../report/images/asset_004_trend.png', dpi=300, bbox_inches='tight')
    print("Saved: report/images/asset_004_trend.png")
    plt.close()

# Figure 4: Correlation heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8})
plt.title('Correlation Matrix: Sensor Parameters', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('../report/images/correlation_heatmap.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/correlation_heatmap.png")
plt.close()

# Figure 5: Vibration vs Temperature scatter
plt.figure(figsize=(10, 6))
scatter = plt.scatter(df['bearing_temp_c'], df['vibration_rms_mm_s'], 
                      c=df['load_pct'], alpha=0.6, cmap='viridis', s=20)
plt.colorbar(scatter, label='Load (%)')
plt.title('Vibration vs Bearing Temperature (colored by Load)', fontsize=14, fontweight='bold')
plt.xlabel('Bearing Temperature (°C)', fontsize=12)
plt.ylabel('Vibration RMS (mm/s)', fontsize=12)
plt.tight_layout()
plt.savefig('../report/images/vibration_vs_temperature.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/vibration_vs_temperature.png")
plt.close()

# Figure 6: Weekly vibration trends for all assets
plt.figure(figsize=(14, 8))
for asset in df['asset_id'].unique()[:3]:  # Plot first 3 assets for clarity
    asset_data = df[df['asset_id'] == asset]
    weekly_avg = asset_data.groupby('week')['vibration_rms_mm_s'].mean()
    plt.plot(weekly_avg.index, weekly_avg.values, 'o-', label=asset, linewidth=2, markersize=6)

plt.title('Weekly Average Vibration Trends', fontsize=14, fontweight='bold')
plt.xlabel('Week Number', fontsize=12)
plt.ylabel('Average Vibration RMS (mm/s)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/weekly_trends.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/weekly_trends.png")
plt.close()

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print(f"\nGenerated {6} figures in report/images/")
print(f"Saved {3} data files in outputs/")
print("\nNext: Generate maintenance recommendations based on analysis.")
