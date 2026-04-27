import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Use the generated data since the provided one is empty
data_path = 'outputs/sensor_panel_timeseries.csv'
df = pd.read_csv(data_path)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

# 1. Data Overview
print("--- Data Overview ---")
print(f"Observation Window: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Assets Represented: {', '.join(df['asset_id'].unique())}")
print(f"Zones Represented: {', '.join(df['zone'].unique())}")

# Calculate sampling interval
time_diffs = df.groupby(['asset_id', 'zone'])['timestamp_utc'].diff().dropna()
sampling_interval = time_diffs.mode()[0]
print(f"Implied Sampling Interval: {sampling_interval}")

# 2. Evolution of Vibration over Time
plt.figure(figsize=(14, 8))
sns.lineplot(data=df, x='timestamp_utc', y='vibration_rms_mm_s', hue='asset_id', style='zone')
plt.title('Vibration RMS Evolution over Time')
plt.xlabel('Time')
plt.ylabel('Vibration RMS (mm/s)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/vibration_over_time.png')
plt.close()

# 3. Comparison across Assets and Zones
plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='asset_id', y='vibration_rms_mm_s', hue='zone')
plt.title('Vibration RMS Distribution by Asset and Zone')
plt.xlabel('Asset ID')
plt.ylabel('Vibration RMS (mm/s)')
plt.tight_layout()
plt.savefig('report/images/vibration_boxplot.png')
plt.close()

# 4. Relationships among Variables
# Pairplot for a subset to see relationships
vars_to_plot = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
plt.figure(figsize=(12, 10))
sns.pairplot(df[vars_to_plot + ['asset_id']], hue='asset_id', diag_kind='kde', plot_kws={'alpha': 0.5})
plt.suptitle('Relationships among Telemetry Variables', y=1.02)
plt.tight_layout()
plt.savefig('report/images/pairplot.png')
plt.close()

# Correlation heatmap
plt.figure(figsize=(8, 6))
corr = df[vars_to_plot].corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt='.2f')
plt.title('Correlation Heatmap of Telemetry Variables')
plt.tight_layout()
plt.savefig('report/images/correlation_heatmap.png')
plt.close()

# 5. Quality Flags Analysis
plt.figure(figsize=(10, 6))
sns.countplot(data=df, x='asset_id', hue='quality_flag')
plt.title('Quality Flags Distribution by Asset')
plt.xlabel('Asset ID')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig('report/images/quality_flags.png')
plt.close()

print("\nAnalysis complete. Images saved to report/images/")
