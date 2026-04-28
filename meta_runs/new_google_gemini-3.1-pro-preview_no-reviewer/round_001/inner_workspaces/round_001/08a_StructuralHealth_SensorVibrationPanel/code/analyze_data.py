import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create output directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/sensor_panel_timeseries.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

# Filter out BAD quality data for analysis
df_clean = df[df['quality_flag'] == 'GOOD'].copy()

# 1. Summary Statistics
obs_start = df['timestamp_utc'].min()
obs_end = df['timestamp_utc'].min()
assets = df['asset_id'].unique()
zones = df['zone'].unique()

# Calculate sampling interval
df_sorted = df.sort_values(['asset_id', 'zone', 'timestamp_utc'])
df_sorted['time_diff'] = df_sorted.groupby(['asset_id', 'zone'])['timestamp_utc'].diff()
sampling_interval = df_sorted['time_diff'].mode()[0]

summary = {
    'Observation Start': df['timestamp_utc'].min(),
    'Observation End': df['timestamp_utc'].max(),
    'Assets': list(assets),
    'Zones': list(zones),
    'Sampling Interval': sampling_interval,
    'Total Records': len(df),
    'Good Quality Records': len(df_clean)
}

with open('outputs/summary.txt', 'w') as f:
    for k, v in summary.items():
        f.write(f'{k}: {v}\n')

# 2. Vibration Evolution over Time
plt.figure(figsize=(14, 8))
sns.lineplot(data=df_clean, x='timestamp_utc', y='vibration_rms_mm_s', hue='asset_id', style='zone')
plt.title('Vibration RMS Evolution Over Time')
plt.xlabel('Time')
plt.ylabel('Vibration RMS (mm/s)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/vibration_over_time.png')
plt.close()

# Boxplot for comparison across assets and zones
plt.figure(figsize=(10, 6))
sns.boxplot(data=df_clean, x='asset_id', y='vibration_rms_mm_s', hue='zone')
plt.title('Vibration RMS Comparison Across Assets and Zones')
plt.xlabel('Asset ID')
plt.ylabel('Vibration RMS (mm/s)')
plt.tight_layout()
plt.savefig('report/images/vibration_boxplot.png')
plt.close()

# 3. Relationships among variables
# Correlation matrix
corr_cols = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
corr_matrix = df_clean[corr_cols].corr()

plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
plt.title('Correlation Matrix of Sensor Variables')
plt.tight_layout()
plt.savefig('report/images/correlation_matrix.png')
plt.close()

# Scatter plot: Vibration vs Bearing Temp
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df_clean, x='vibration_rms_mm_s', y='bearing_temp_c', hue='asset_id', style='zone', alpha=0.6)
plt.title('Bearing Temperature vs Vibration RMS')
plt.xlabel('Vibration RMS (mm/s)')
plt.ylabel('Bearing Temperature (°C)')
plt.tight_layout()
plt.savefig('report/images/vib_vs_temp.png')
plt.close()

# Scatter plot: Load vs Vibration
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df_clean, x='load_pct', y='vibration_rms_mm_s', hue='asset_id', style='zone', alpha=0.6)
plt.title('Vibration RMS vs Load Percentage')
plt.xlabel('Load (%)')
plt.ylabel('Vibration RMS (mm/s)')
plt.tight_layout()
plt.savefig('report/images/load_vs_vib.png')
plt.close()

print('Analysis complete. Outputs saved.')
