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
image_dir = '../report/images/'

# Create directory if it doesn't exist
os.makedirs(image_dir, exist_ok=True)

# Set plot style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

# Read the data
df = pd.read_csv(data_path)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df['date'] = df['timestamp_utc'].dt.date
df['hour'] = df['timestamp_utc'].dt.hour
df['day_of_week'] = df['timestamp_utc'].dt.dayofweek

# 1. Time series of vibration severity
print("Creating time series plot...")
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Daily average vibration
daily_avg = df.groupby('date')['vibration_rms_mm_s'].mean()
axes[0, 0].plot(daily_avg.index, daily_avg.values, linewidth=2)
axes[0, 0].set_title('Daily Average Vibration RMS (mm/s)', fontsize=14, fontweight='bold')
axes[0, 0].set_xlabel('Date')
axes[0, 0].set_ylabel('Vibration RMS (mm/s)')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].tick_params(axis='x', rotation=45)

# Hourly pattern
hourly_avg = df.groupby('hour')['vibration_rms_mm_s'].mean()
axes[0, 1].bar(hourly_avg.index, hourly_avg.values, alpha=0.7)
axes[0, 1].set_title('Hourly Pattern of Vibration RMS', fontsize=14, fontweight='bold')
axes[0, 1].set_xlabel('Hour of Day')
axes[0, 1].set_ylabel('Average Vibration RMS (mm/s)')
axes[0, 1].grid(True, alpha=0.3)

# Vibration by asset
asset_avg = df.groupby('asset_id')['vibration_rms_mm_s'].mean().sort_values()
axes[1, 0].bar(range(len(asset_avg)), asset_avg.values, alpha=0.7)
axes[1, 0].set_title('Average Vibration RMS by Asset', fontsize=14, fontweight='bold')
axes[1, 0].set_xlabel('Asset ID')
axes[1, 0].set_ylabel('Average Vibration RMS (mm/s)')
axes[1, 0].set_xticks(range(len(asset_avg)))
axes[1, 0].set_xticklabels(asset_avg.index, rotation=45)
axes[1, 0].grid(True, alpha=0.3)

# Highlight problematic assets
for i, (asset, value) in enumerate(asset_avg.items()):
    if asset in ['ASSET_003', 'ASSET_007']:
        axes[1, 0].bar(i, value, color='red', alpha=0.7)

# Vibration by zone
zone_avg = df.groupby('zone')['vibration_rms_mm_s'].mean().sort_values()
axes[1, 1].bar(range(len(zone_avg)), zone_avg.values, alpha=0.7)
axes[1, 1].set_title('Average Vibration RMS by Zone', fontsize=14, fontweight='bold')
axes[1, 1].set_xlabel('Zone')
axes[1, 1].set_ylabel('Average Vibration RMS (mm/s)')
axes[1, 1].set_xticks(range(len(zone_avg)))
axes[1, 1].set_xticklabels(zone_avg.index)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(image_dir, 'vibration_analysis_overview.png'), dpi=300, bbox_inches='tight')
plt.close()

# 2. Correlation heatmap
print("Creating correlation heatmap...")
correlation_matrix = df[['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']].corr()

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(correlation_matrix, cmap='coolwarm', vmin=-1, vmax=1)

# Add text annotations
for i in range(len(correlation_matrix.columns)):
    for j in range(len(correlation_matrix.columns)):
        text = ax.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                       ha='center', va='center', color='black', fontsize=11)

ax.set_xticks(range(len(correlation_matrix.columns)))
ax.set_yticks(range(len(correlation_matrix.columns)))
ax.set_xticklabels(correlation_matrix.columns, rotation=45, ha='right')
ax.set_yticklabels(correlation_matrix.columns)
ax.set_title('Correlation Matrix of Sensor Parameters', fontsize=14, fontweight='bold')

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax)
cbar.ax.set_ylabel('Correlation Coefficient', rotation=-90, va='bottom')

plt.tight_layout()
plt.savefig(os.path.join(image_dir, 'correlation_heatmap.png'), dpi=300, bbox_inches='tight')
plt.close()

# 3. Scatter plots for key relationships
print("Creating scatter plots...")
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Vibration vs Bearing Temperature
axes[0, 0].scatter(df['vibration_rms_mm_s'], df['bearing_temp_c'], alpha=0.5, s=10)
axes[0, 0].set_title('Vibration RMS vs Bearing Temperature', fontsize=14, fontweight='bold')
axes[0, 0].set_xlabel('Vibration RMS (mm/s)')
axes[0, 0].set_ylabel('Bearing Temperature (°C)')
axes[0, 0].grid(True, alpha=0.3)

# Add trend line
z = np.polyfit(df['vibration_rms_mm_s'], df['bearing_temp_c'], 1)
p = np.poly1d(z)
x_range = np.linspace(df['vibration_rms_mm_s'].min(), df['vibration_rms_mm_s'].max(), 100)
axes[0, 0].plot(x_range, p(x_range), 'r-', linewidth=2, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
axes[0, 0].legend()

# Vibration vs Load Percentage
axes[0, 1].scatter(df['load_pct'], df['vibration_rms_mm_s'], alpha=0.5, s=10)
axes[0, 1].set_title('Vibration RMS vs Load Percentage', fontsize=14, fontweight='bold')
axes[0, 1].set_xlabel('Load Percentage (%)')
axes[0, 1].set_ylabel('Vibration RMS (mm/s)')
axes[0, 1].grid(True, alpha=0.3)

# Vibration vs RPM
axes[1, 0].scatter(df['rpm'], df['vibration_rms_mm_s'], alpha=0.5, s=10)
axes[1, 0].set_title('Vibration RMS vs RPM', fontsize=14, fontweight='bold')
axes[1, 0].set_xlabel('RPM')
axes[1, 0].set_ylabel('Vibration RMS (mm/s)')
axes[1, 0].grid(True, alpha=0.3)

# Peak Acceleration vs Vibration RMS
axes[1, 1].scatter(df['vibration_rms_mm_s'], df['peak_accel_g'], alpha=0.5, s=10)
axes[1, 1].set_title('Peak Acceleration vs Vibration RMS', fontsize=14, fontweight='bold')
axes[1, 1].set_xlabel('Vibration RMS (mm/s)')
axes[1, 1].set_ylabel('Peak Acceleration (g)')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(image_dir, 'scatter_relationships.png'), dpi=300, bbox_inches='tight')
plt.close()

# 4. Time series for problematic assets
print("Creating time series for problematic assets...")
problem_assets = ['ASSET_003', 'ASSET_007']

fig, axes = plt.subplots(2, 1, figsize=(16, 10))

for i, asset in enumerate(problem_assets):
    asset_data = df[df['asset_id'] == asset].copy()
    asset_data = asset_data.sort_values('timestamp_utc')
    
    # Resample to daily for cleaner plot
    asset_data_daily = asset_data.set_index('timestamp_utc').resample('D').agg({
        'vibration_rms_mm_s': 'mean',
        'bearing_temp_c': 'mean',
        'load_pct': 'mean'
    }).reset_index()
    
    ax = axes[i]
    ax.plot(asset_data_daily['timestamp_utc'], asset_data_daily['vibration_rms_mm_s'], 
            label='Vibration RMS', linewidth=2, color='blue')
    ax.set_ylabel('Vibration RMS (mm/s)', color='blue')
    ax.tick_params(axis='y', labelcolor='blue')
    ax.set_title(f'{asset} - Vibration and Temperature Trend', fontsize=14, fontweight='bold')
    
    # Add temperature on secondary axis
    ax2 = ax.twinx()
    ax2.plot(asset_data_daily['timestamp_utc'], asset_data_daily['bearing_temp_c'], 
             label='Bearing Temperature', linewidth=2, color='red', linestyle='--')
    ax2.set_ylabel('Bearing Temperature (°C)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.tight_layout()
plt.savefig(os.path.join(image_dir, 'problem_assets_timeseries.png'), dpi=300, bbox_inches='tight')
plt.close()

# 5. Distribution plots
print("Creating distribution plots...")
fig, axes = plt.subplots(2, 3, figsize=(18, 10))

# Vibration distribution
axes[0, 0].hist(df['vibration_rms_mm_s'], bins=50, alpha=0.7, edgecolor='black')
axes[0, 0].set_title('Distribution of Vibration RMS', fontsize=14, fontweight='bold')
axes[0, 0].set_xlabel('Vibration RMS (mm/s)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].grid(True, alpha=0.3)

# Peak acceleration distribution
axes[0, 1].hist(df['peak_accel_g'], bins=50, alpha=0.7, edgecolor='black')
axes[0, 1].set_title('Distribution of Peak Acceleration', fontsize=14, fontweight='bold')
axes[0, 1].set_xlabel('Peak Acceleration (g)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].grid(True, alpha=0.3)

# Bearing temperature distribution
axes[0, 2].hist(df['bearing_temp_c'], bins=50, alpha=0.7, edgecolor='black')
axes[0, 2].set_title('Distribution of Bearing Temperature', fontsize=14, fontweight='bold')
axes[0, 2].set_xlabel('Bearing Temperature (°C)')
axes[0, 2].set_ylabel('Frequency')
axes[0, 2].grid(True, alpha=0.3)

# Load percentage distribution
axes[1, 0].hist(df['load_pct'], bins=50, alpha=0.7, edgecolor='black')
axes[1, 0].set_title('Distribution of Load Percentage', fontsize=14, fontweight='bold')
axes[1, 0].set_xlabel('Load Percentage (%)')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].grid(True, alpha=0.3)

# RPM distribution
axes[1, 1].hist(df['rpm'], bins=50, alpha=0.7, edgecolor='black')
axes[1, 1].set_title('Distribution of RPM', fontsize=14, fontweight='bold')
axes[1, 1].set_xlabel('RPM')
axes[1, 1].set_ylabel('Frequency')
axes[1, 1].grid(True, alpha=0.3)

# Quality flag distribution
quality_counts = df['quality_flag'].value_counts()
axes[1, 2].bar(quality_counts.index, quality_counts.values, alpha=0.7, edgecolor='black')
axes[1, 2].set_title('Distribution of Quality Flags', fontsize=14, fontweight='bold')
axes[1, 2].set_xlabel('Quality Flag')
axes[1, 2].set_ylabel('Count')
axes[1, 2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(image_dir, 'parameter_distributions.png'), dpi=300, bbox_inches='tight')
plt.close()

print("All visualizations created successfully!")
