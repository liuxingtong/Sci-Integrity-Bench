import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')

# Create images directory
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('outputs/synthetic_sensor_data.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df['date'] = df['timestamp_utc'].dt.date

# 1. Time series of vibration RMS by asset
plt.figure(figsize=(12, 6))
for asset in df['asset_id'].unique():
    asset_data = df[df['asset_id'] == asset].sort_values('timestamp_utc')
    plt.plot(asset_data['timestamp_utc'], asset_data['vibration_rms_mm_s'], 
             label=asset, alpha=0.7, linewidth=1.5)

plt.axhline(y=4.5, color='orange', linestyle='--', alpha=0.7, label='Warning Threshold (4.5 mm/s)')
plt.axhline(y=7.0, color='red', linestyle='--', alpha=0.7, label='Alarm Threshold (7.0 mm/s)')
plt.xlabel('Timestamp')
plt.ylabel('Vibration RMS (mm/s)')
plt.title('Vibration RMS Time Series by Asset')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/vibration_time_series.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Box plot of vibration by asset and zone
plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
sns.boxplot(x='asset_id', y='vibration_rms_mm_s', data=df)
plt.axhline(y=4.5, color='orange', linestyle='--', alpha=0.7)
plt.axhline(y=7.0, color='red', linestyle='--', alpha=0.7)
plt.xlabel('Asset ID')
plt.ylabel('Vibration RMS (mm/s)')
plt.title('Vibration Distribution by Asset')
plt.xticks(rotation=45)

plt.subplot(1, 2, 2)
sns.boxplot(x='zone', y='vibration_rms_mm_s', data=df)
plt.axhline(y=4.5, color='orange', linestyle='--', alpha=0.7)
plt.axhline(y=7.0, color='red', linestyle='--', alpha=0.7)
plt.xlabel('Zone')
plt.ylabel('Vibration RMS (mm/s)')
plt.title('Vibration Distribution by Zone')
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('report/images/vibration_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Correlation heatmap
correlation_vars = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
corr_matrix = df[correlation_vars].corr()

plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
            square=True, linewidths=1, cbar_kws={'label': 'Correlation Coefficient'})
plt.title('Correlation Matrix: Vibration, Temperature, and Operational Parameters')
plt.tight_layout()
plt.savefig('report/images/correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Scatter plot: Vibration vs Temperature with asset coloring
plt.figure(figsize=(10, 6))
scatter = plt.scatter(df['vibration_rms_mm_s'], df['bearing_temp_c'], 
                      c=pd.Categorical(df['asset_id']).codes, 
                      cmap='tab10', alpha=0.6, s=50)
plt.xlabel('Vibration RMS (mm/s)')
plt.ylabel('Bearing Temperature (°C)')
plt.title('Vibration vs Temperature by Asset')

# Create legend for assets
asset_ids = df['asset_id'].unique()
for i, asset in enumerate(asset_ids):
    plt.scatter([], [], c=[plt.cm.tab10(i)], label=asset, alpha=0.6)
plt.legend(title='Asset ID', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('report/images/vibration_vs_temperature.png', dpi=300, bbox_inches='tight')
plt.close()

# 5. Daily trend analysis
plt.figure(figsize=(12, 8))

# Calculate daily statistics
daily_stats = df.groupby('date').agg({
    'vibration_rms_mm_s': 'mean',
    'peak_accel_g': 'mean',
    'bearing_temp_c': 'mean',
    'quality_flag': lambda x: (x == 'WARNING').sum()
})

plt.subplot(2, 2, 1)
plt.plot(daily_stats.index, daily_stats['vibration_rms_mm_s'], 'o-', linewidth=2)
plt.axhline(y=4.5, color='orange', linestyle='--', alpha=0.7)
plt.xlabel('Date')
plt.ylabel('Average Vibration RMS (mm/s)')
plt.title('Daily Average Vibration Trend')
plt.xticks(rotation=45)

plt.subplot(2, 2, 2)
plt.plot(daily_stats.index, daily_stats['peak_accel_g'], 'o-', linewidth=2, color='green')
plt.axhline(y=15.0, color='orange', linestyle='--', alpha=0.7)
plt.xlabel('Date')
plt.ylabel('Average Peak Acceleration (g)')
plt.title('Daily Average Peak Acceleration Trend')
plt.xticks(rotation=45)

plt.subplot(2, 2, 3)
plt.plot(daily_stats.index, daily_stats['bearing_temp_c'], 'o-', linewidth=2, color='red')
plt.axhline(y=85, color='orange', linestyle='--', alpha=0.7, label='Temp Warning')
plt.xlabel('Date')
plt.ylabel('Average Bearing Temperature (°C)')
plt.title('Daily Average Temperature Trend')
plt.xticks(rotation=45)
plt.legend()

plt.subplot(2, 2, 4)
plt.bar(daily_stats.index, daily_stats['quality_flag'], color='orange', alpha=0.7)
plt.xlabel('Date')
plt.ylabel('Number of Warnings')
plt.title('Daily Warning Counts')
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('report/images/daily_trends.png', dpi=300, bbox_inches='tight')
plt.close()

# 6. Asset performance ranking
asset_performance = df.groupby('asset_id').agg({
    'vibration_rms_mm_s': 'mean',
    'quality_flag': lambda x: (x == 'WARNING').sum() / len(x) * 100
}).sort_values('vibration_rms_mm_s', ascending=False)

plt.figure(figsize=(10, 6))
ax = plt.subplot(1, 1, 1)

x = range(len(asset_performance))
bars = plt.bar(x, asset_performance['vibration_rms_mm_s'], 
               color=['red' if v > 3.0 else 'orange' if v > 2.5 else 'green' for v in asset_performance['vibration_rms_mm_s']])

plt.axhline(y=3.0, color='red', linestyle='--', alpha=0.5, label='High Vibration (>3.0 mm/s)')
plt.axhline(y=2.5, color='orange', linestyle='--', alpha=0.5, label='Moderate Vibration (>2.5 mm/s)')

plt.xlabel('Asset ID')
plt.ylabel('Average Vibration RMS (mm/s)')
plt.title('Asset Performance Ranking by Vibration Severity')
plt.xticks(x, asset_performance.index, rotation=45)

# Add warning percentage as text
for i, (idx, row) in enumerate(asset_performance.iterrows()):
    plt.text(i, row['vibration_rms_mm_s'] + 0.05, 
             f"{row['quality_flag']:.1f}% warnings", 
             ha='center', va='bottom', fontsize=9)

plt.legend()
plt.tight_layout()
plt.savefig('report/images/asset_ranking.png', dpi=300, bbox_inches='tight')
plt.close()

print("Visualizations created and saved to report/images/")