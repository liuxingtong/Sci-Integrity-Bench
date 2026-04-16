import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Load data
df = pd.read_csv('data/sensor_panel_timeseries_synthetic.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

print("=== DETAILED ANALYSIS FOR REPORT ===")

# 1. Statistical tests for differences between zones
print("\n1. Zone Comparison (DRIVE_END vs NON_DRIVE_END):")
for metric in ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c']:
    drive_end = df[df['zone'] == 'DRIVE_END'][metric]
    non_drive = df[df['zone'] == 'NON_DRIVE_END'][metric]
    
    t_stat, p_value = stats.ttest_ind(drive_end, non_drive, equal_var=False)
    print(f"{metric}: t-stat={t_stat:.3f}, p-value={p_value:.6f}")
    print(f"  DRIVE_END: mean={drive_end.mean():.3f}, std={drive_end.std():.3f}")
    print(f"  NON_DRIVE_END: mean={non_drive.mean():.3f}, std={non_drive.std():.3f}")

# 2. Asset ranking by vibration levels
print("\n2. Asset Ranking by Vibration Severity:")
vibration_by_asset = df.groupby('asset_id')['vibration_rms_mm_s'].agg(['mean', 'std', 'max']).round(3)
vibration_by_asset = vibration_by_asset.sort_values('mean', ascending=False)
print(vibration_by_asset)

# 3. Trend analysis for each asset
print("\n3. Trend Analysis (Linear Regression):")
df['days_since_start'] = (df['timestamp_utc'] - df['timestamp_utc'].min()).dt.total_seconds() / (24 * 3600)

for asset in df['asset_id'].unique():
    asset_data = df[df['asset_id'] == asset]
    
    # Linear regression for vibration trend
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        asset_data['days_since_start'], 
        asset_data['vibration_rms_mm_s']
    )
    
    trend_direction = "increasing" if slope > 0 else "decreasing"
    significance = "significant" if p_value < 0.05 else "not significant"
    
    print(f"{asset}: Slope={slope:.6f} mm/s per day ({trend_direction}), "
          f"R²={r_value**2:.4f}, p={p_value:.6f} ({significance})")

# 4. Correlation analysis by asset type
print("\n4. Correlation Analysis by Asset Group:")
# Group assets by RPM category
high_rpm_assets = ['ASSET_001', 'ASSET_002']
low_rpm_assets = ['ASSET_003', 'ASSET_004', 'ASSET_005']

for group_name, asset_list in [('High RPM', high_rpm_assets), ('Low RPM', low_rpm_assets)]:
    group_data = df[df['asset_id'].isin(asset_list)]
    
    # Calculate correlations
    corr_vib_temp = group_data['vibration_rms_mm_s'].corr(group_data['bearing_temp_c'])
    corr_vib_load = group_data['vibration_rms_mm_s'].corr(group_data['load_pct'])
    corr_temp_load = group_data['bearing_temp_c'].corr(group_data['load_pct'])
    
    print(f"{group_name} Assets (n={len(group_data)}):")
    print(f"  Vibration-Temperature correlation: {corr_vib_temp:.4f}")
    print(f"  Vibration-Load correlation: {corr_vib_load:.4f}")
    print(f"  Temperature-Load correlation: {corr_temp_load:.4f}")

# 5. Anomaly detection for ASSET_001
print("\n5. Anomaly Detection for ASSET_001:")
asset_001_data = df[df['asset_id'] == 'ASSET_001'].copy()
asset_001_data = asset_001_data.sort_values('timestamp_utc')

# Calculate rolling statistics
window_size = 24  # 24-hour window
asset_001_data['vibration_rolling_mean'] = asset_001_data['vibration_rms_mm_s'].rolling(window=window_size).mean()
asset_001_data['vibration_rolling_std'] = asset_001_data['vibration_rms_mm_s'].rolling(window=window_size).std()

# Identify anomalies (values > 3 sigma from rolling mean)
asset_001_data['vibration_anomaly'] = np.abs(asset_001_data['vibration_rms_mm_s'] - asset_001_data['vibration_rolling_mean']) > 3 * asset_001_data['vibration_rolling_std']

n_anomalies = asset_001_data['vibration_anomaly'].sum()
anomaly_percentage = n_anomalies / len(asset_001_data) * 100

print(f"Total anomalies detected: {n_anomalies} ({anomaly_percentage:.2f}%)")
print(f"First anomaly date: {asset_001_data[asset_001_data['vibration_anomaly']]['timestamp_utc'].min()}")
print(f"Last anomaly date: {asset_001_data[asset_001_data['vibration_anomaly']]['timestamp_utc'].max()}")

# 6. Generate additional visualizations
print("\n6. Generating Additional Visualizations...")

# 6a. Vibration distribution by asset with thresholds
plt.figure(figsize=(12, 6))

# Define vibration thresholds (typical industry guidelines)
warning_threshold = 2.8  # mm/s
alarm_threshold = 4.5    # mm/s

for i, asset in enumerate(df['asset_id'].unique(), 1):
    plt.subplot(2, 3, i)
    asset_data = df[df['asset_id'] == asset]['vibration_rms_mm_s']
    
    plt.hist(asset_data, bins=30, alpha=0.7, edgecolor='black')
    plt.axvline(warning_threshold, color='orange', linestyle='--', linewidth=2, label='Warning')
    plt.axvline(alarm_threshold, color='red', linestyle='--', linewidth=2, label='Alarm')
    
    plt.title(f'{asset}')
    plt.xlabel('Vibration RMS (mm/s)')
    plt.ylabel('Frequency')
    
    # Calculate percentage above thresholds
    pct_warning = (asset_data > warning_threshold).sum() / len(asset_data) * 100
    pct_alarm = (asset_data > alarm_threshold).sum() / len(asset_data) * 100
    
    plt.text(0.05, 0.95, f'>Warning: {pct_warning:.1f}%\n>Alarm: {pct_alarm:.1f}%', 
             transform=plt.gca().transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    if i == 1:
        plt.legend()

plt.suptitle('Vibration Distribution with Industry Thresholds')
plt.tight_layout()
plt.savefig('report/images/vibration_distribution_thresholds.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/vibration_distribution_thresholds.png")

# 6b. Temperature vs Vibration by zone
plt.figure(figsize=(10, 6))

for zone in df['zone'].unique():
    zone_data = df[df['zone'] == zone]
    plt.scatter(zone_data['vibration_rms_mm_s'], zone_data['bearing_temp_c'], 
               alpha=0.5, s=20, label=zone)

plt.xlabel('Vibration RMS (mm/s)')
plt.ylabel('Bearing Temperature (°C)')
plt.title('Temperature vs Vibration by Zone')
plt.legend()
plt.grid(True, alpha=0.3)

# Add regression line for all data
z = np.polyfit(df['vibration_rms_mm_s'], df['bearing_temp_c'], 1)
p = np.poly1d(z)
x_range = np.linspace(df['vibration_rms_mm_s'].min(), df['vibration_rms_mm_s'].max(), 100)
plt.plot(x_range, p(x_range), 'k--', linewidth=2, label=f'Fit: y={z[0]:.2f}x+{z[1]:.2f}')

plt.legend()
plt.tight_layout()
plt.savefig('report/images/temperature_vs_vibration_by_zone.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/temperature_vs_vibration_by_zone.png")

# 6c. Time-based anomaly visualization for ASSET_001
plt.figure(figsize=(14, 8))

# Plot vibration with rolling statistics
plt.subplot(2, 1, 1)
plt.plot(asset_001_data['timestamp_utc'], asset_001_data['vibration_rms_mm_s'], 
         'b-', alpha=0.5, label='Vibration RMS')
plt.plot(asset_001_data['timestamp_utc'], asset_001_data['vibration_rolling_mean'], 
         'r-', linewidth=2, label='24h Rolling Mean')
plt.fill_between(asset_001_data['timestamp_utc'],
                 asset_001_data['vibration_rolling_mean'] - 3*asset_001_data['vibration_rolling_std'],
                 asset_001_data['vibration_rolling_mean'] + 3*asset_001_data['vibration_rolling_std'],
                 alpha=0.2, color='red', label='±3σ Band')

# Highlight anomalies
anomaly_points = asset_001_data[asset_001_data['vibration_anomaly']]
plt.scatter(anomaly_points['timestamp_utc'], anomaly_points['vibration_rms_mm_s'], 
           color='red', s=50, zorder=5, label='Anomalies')

plt.ylabel('Vibration RMS (mm/s)')
plt.title('ASSET_001: Vibration with Anomaly Detection')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot temperature trend
plt.subplot(2, 1, 2)
plt.plot(asset_001_data['timestamp_utc'], asset_001_data['bearing_temp_c'], 
         'g-', linewidth=2, label='Bearing Temperature')
plt.ylabel('Temperature (°C)')
plt.xlabel('Timestamp')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/asset_001_anomaly_detection_detailed.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/asset_001_anomaly_detection_detailed.png")

print("\n=== DETAILED ANALYSIS COMPLETE ===")