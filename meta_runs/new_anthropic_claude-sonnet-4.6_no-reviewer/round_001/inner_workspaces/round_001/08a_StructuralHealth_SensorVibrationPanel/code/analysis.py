#!/usr/bin/env python3
"""
Structural Health Sensor Vibration Panel Analysis
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("Loading data...")
df = pd.read_csv('data/sensor_panel_timeseries.csv')
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nDtypes:\n{df.dtypes}")
print(f"\nFirst 5 rows:\n{df.head()}")
print(f"\nDescribe:\n{df.describe()}")

# Parse timestamps
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df = df.sort_values('timestamp_utc')

print(f"\nTime range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Duration: {df['timestamp_utc'].max() - df['timestamp_utc'].min()}")
print(f"\nUnique assets: {df['asset_id'].unique()}")
print(f"Unique zones: {df['zone'].unique()}")
print(f"\nQuality flags:\n{df['quality_flag'].value_counts()}")

# Save summary stats
with open('outputs/summary_stats.txt', 'w') as f:
    f.write("=== SENSOR PANEL TIMESERIES SUMMARY ===\n\n")
    f.write(f"Shape: {df.shape}\n")
    f.write(f"Columns: {df.columns.tolist()}\n")
    f.write(f"\nTime range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}\n")
    f.write(f"Duration: {df['timestamp_utc'].max() - df['timestamp_utc'].min()}\n")
    f.write(f"\nUnique assets: {df['asset_id'].unique()}\n")
    f.write(f"Unique zones: {df['zone'].unique()}\n")
    f.write(f"\nQuality flags:\n{df['quality_flag'].value_counts()}\n")
    f.write(f"\nDescriptive Statistics:\n{df.describe()}\n")
    f.write(f"\nMissing values:\n{df.isnull().sum()}\n")

print("\nSummary stats saved.")

# Per-asset statistics
asset_stats = df.groupby('asset_id').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'max', 'min'],
    'peak_accel_g': ['mean', 'std', 'max'],
    'bearing_temp_c': ['mean', 'std', 'max'],
    'rpm': ['mean', 'std'],
    'load_pct': ['mean', 'std']
}).round(3)

print(f"\nPer-asset statistics:\n{asset_stats}")
asset_stats.to_csv('outputs/asset_stats.csv')

# Per-zone statistics
zone_stats = df.groupby('zone').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'max'],
    'peak_accel_g': ['mean', 'std', 'max'],
    'bearing_temp_c': ['mean', 'std', 'max'],
    'rpm': ['mean', 'std'],
    'load_pct': ['mean', 'std']
}).round(3)

print(f"\nPer-zone statistics:\n{zone_stats}")
zone_stats.to_csv('outputs/zone_stats.csv')

# Sampling interval analysis
df_sorted = df.sort_values(['asset_id', 'timestamp_utc'])
df_sorted['time_diff'] = df_sorted.groupby('asset_id')['timestamp_utc'].diff()
print(f"\nSampling intervals (seconds):")
print(df_sorted['time_diff'].dt.total_seconds().describe())

# Correlation analysis
numeric_cols = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
corr_matrix = df[numeric_cols].corr()
print(f"\nCorrelation matrix:\n{corr_matrix}")
corr_matrix.to_csv('outputs/correlation_matrix.csv')

print("\nBasic analysis complete. Starting visualization...")

# ============================================================
# FIGURE 1: Time series overview for all assets
# ============================================================
fig, axes = plt.subplots(5, 1, figsize=(14, 16), sharex=True)
fig.suptitle('Sensor Panel Time Series Overview', fontsize=16, fontweight='bold')

assets = df['asset_id'].unique()
colors = plt.cm.tab10(np.linspace(0, 1, len(assets)))

for i, asset in enumerate(assets):
    asset_df = df[df['asset_id'] == asset]
    color = colors[i]
    
    axes[0].plot(asset_df['timestamp_utc'], asset_df['vibration_rms_mm_s'], 
                 label=asset, color=color, alpha=0.7, linewidth=0.8)
    axes[1].plot(asset_df['timestamp_utc'], asset_df['peak_accel_g'], 
                 color=color, alpha=0.7, linewidth=0.8)
    axes[2].plot(asset_df['timestamp_utc'], asset_df['bearing_temp_c'], 
                 color=color, alpha=0.7, linewidth=0.8)
    axes[3].plot(asset_df['timestamp_utc'], asset_df['rpm'], 
                 color=color, alpha=0.7, linewidth=0.8)
    axes[4].plot(asset_df['timestamp_utc'], asset_df['load_pct'], 
                 color=color, alpha=0.7, linewidth=0.8)

axes[0].set_ylabel('Vibration RMS (mm/s)')
axes[1].set_ylabel('Peak Accel (g)')
axes[2].set_ylabel('Bearing Temp (°C)')
axes[3].set_ylabel('RPM')
axes[4].set_ylabel('Load (%)')
axes[4].set_xlabel('Time (UTC)')

axes[0].legend(loc='upper right', fontsize=8)
for ax in axes:
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')

plt.tight_layout()
plt.savefig('report/images/fig1_timeseries_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 1 saved.")

# ============================================================
# FIGURE 2: Vibration RMS by asset - boxplot comparison
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Vibration Comparison Across Assets', fontsize=14, fontweight='bold')

# Boxplot of vibration RMS by asset
df.boxplot(column='vibration_rms_mm_s', by='asset_id', ax=axes[0])
axes[0].set_title('Vibration RMS by Asset')
axes[0].set_xlabel('Asset ID')
axes[0].set_ylabel('Vibration RMS (mm/s)')
axes[0].tick_params(axis='x', rotation=45)

# Boxplot of peak acceleration by asset
df.boxplot(column='peak_accel_g', by='asset_id', ax=axes[1])
axes[1].set_title('Peak Acceleration by Asset')
axes[1].set_xlabel('Asset ID')
axes[1].set_ylabel('Peak Acceleration (g)')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('report/images/fig2_vibration_by_asset.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved.")

# ============================================================
# FIGURE 3: Correlation heatmap
# ============================================================
fig, ax = plt.subplots(figsize=(8, 7))
sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='RdYlGn', 
            center=0, ax=ax, square=True, linewidths=0.5)
ax.set_title('Correlation Matrix: Sensor Variables', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig3_correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved.")

# ============================================================
# FIGURE 4: Scatter plots - vibration vs other variables
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Vibration vs. Other Sensor Variables', fontsize=14, fontweight='bold')

for i, asset in enumerate(assets):
    asset_df = df[df['asset_id'] == asset]
    color = colors[i]
    
    axes[0, 0].scatter(asset_df['bearing_temp_c'], asset_df['vibration_rms_mm_s'],
                       label=asset, color=color, alpha=0.5, s=10)
    axes[0, 1].scatter(asset_df['rpm'], asset_df['vibration_rms_mm_s'],
                       color=color, alpha=0.5, s=10)
    axes[1, 0].scatter(asset_df['load_pct'], asset_df['vibration_rms_mm_s'],
                       color=color, alpha=0.5, s=10)
    axes[1, 1].scatter(asset_df['peak_accel_g'], asset_df['vibration_rms_mm_s'],
                       color=color, alpha=0.5, s=10)

axes[0, 0].set_xlabel('Bearing Temperature (°C)')
axes[0, 0].set_ylabel('Vibration RMS (mm/s)')
axes[0, 0].set_title('Vibration vs. Bearing Temperature')
axes[0, 0].legend(fontsize=7)

axes[0, 1].set_xlabel('RPM')
axes[0, 1].set_ylabel('Vibration RMS (mm/s)')
axes[0, 1].set_title('Vibration vs. RPM')

axes[1, 0].set_xlabel('Load (%)')
axes[1, 0].set_ylabel('Vibration RMS (mm/s)')
axes[1, 0].set_title('Vibration vs. Load')

axes[1, 1].set_xlabel('Peak Acceleration (g)')
axes[1, 1].set_ylabel('Vibration RMS (mm/s)')
axes[1, 1].set_title('Vibration vs. Peak Acceleration')

for ax in axes.flat:
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig4_scatter_vibration.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved.")

# ============================================================
# FIGURE 5: Zone comparison
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(15, 6))
fig.suptitle('Sensor Metrics by Zone', fontsize=14, fontweight='bold')

df.boxplot(column='vibration_rms_mm_s', by='zone', ax=axes[0])
axes[0].set_title('Vibration RMS by Zone')
axes[0].set_xlabel('Zone')
axes[0].set_ylabel('Vibration RMS (mm/s)')
axes[0].tick_params(axis='x', rotation=45)

df.boxplot(column='bearing_temp_c', by='zone', ax=axes[1])
axes[1].set_title('Bearing Temperature by Zone')
axes[1].set_xlabel('Zone')
axes[1].set_ylabel('Bearing Temperature (°C)')
axes[1].tick_params(axis='x', rotation=45)

df.boxplot(column='load_pct', by='zone', ax=axes[2])
axes[2].set_title('Load % by Zone')
axes[2].set_xlabel('Zone')
axes[2].set_ylabel('Load (%)')
axes[2].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('report/images/fig5_zone_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 5 saved.")

# ============================================================
# FIGURE 6: Vibration trend over time per asset
# ============================================================
fig, axes = plt.subplots(len(assets), 1, figsize=(14, 4*len(assets)), sharex=True)
if len(assets) == 1:
    axes = [axes]
fig.suptitle('Vibration RMS Trend per Asset', fontsize=14, fontweight='bold')

for i, asset in enumerate(assets):
    asset_df = df[df['asset_id'] == asset].copy()
    asset_df = asset_df.sort_values('timestamp_utc')
    
    # Rolling mean
    asset_df['vib_rolling'] = asset_df['vibration_rms_mm_s'].rolling(window=10, min_periods=1).mean()
    
    axes[i].plot(asset_df['timestamp_utc'], asset_df['vibration_rms_mm_s'], 
                 alpha=0.4, color='steelblue', linewidth=0.8, label='Raw')
    axes[i].plot(asset_df['timestamp_utc'], asset_df['vib_rolling'], 
                 color='red', linewidth=1.5, label='Rolling Mean (10)')
    
    # Add threshold lines (ISO 10816 guidelines for general machinery)
    axes[i].axhline(y=2.8, color='orange', linestyle='--', alpha=0.7, label='Warning (2.8 mm/s)')
    axes[i].axhline(y=7.1, color='red', linestyle='--', alpha=0.7, label='Alarm (7.1 mm/s)')
    
    axes[i].set_ylabel('Vibration RMS (mm/s)')
    axes[i].set_title(f'Asset: {asset}')
    axes[i].legend(loc='upper right', fontsize=8)
    axes[i].grid(True, alpha=0.3)
    axes[i].xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    plt.setp(axes[i].xaxis.get_majorticklabels(), rotation=30, ha='right')

axes[-1].set_xlabel('Time (UTC)')
plt.tight_layout()
plt.savefig('report/images/fig6_vibration_trend_per_asset.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 6 saved.")

# ============================================================
# FIGURE 7: Bearing temperature vs vibration with color by load
# ============================================================
fig, axes = plt.subplots(1, len(assets), figsize=(6*len(assets), 5))
if len(assets) == 1:
    axes = [axes]
fig.suptitle('Bearing Temperature vs. Vibration (colored by Load %)', fontsize=14, fontweight='bold')

for i, asset in enumerate(assets):
    asset_df = df[df['asset_id'] == asset]
    sc = axes[i].scatter(asset_df['bearing_temp_c'], asset_df['vibration_rms_mm_s'],
                         c=asset_df['load_pct'], cmap='YlOrRd', alpha=0.6, s=15)
    plt.colorbar(sc, ax=axes[i], label='Load (%)')
    axes[i].set_xlabel('Bearing Temperature (°C)')
    axes[i].set_ylabel('Vibration RMS (mm/s)')
    axes[i].set_title(f'Asset: {asset}')
    axes[i].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig7_temp_vs_vibration_load.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 7 saved.")

# ============================================================
# FIGURE 8: Quality flag analysis
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('Data Quality Analysis', fontsize=14, fontweight='bold')

# Quality flag distribution
qf_counts = df['quality_flag'].value_counts()
axes[0].bar(qf_counts.index.astype(str), qf_counts.values, color=['green', 'orange', 'red'][:len(qf_counts)])
axes[0].set_title('Quality Flag Distribution')
axes[0].set_xlabel('Quality Flag')
axes[0].set_ylabel('Count')
axes[0].grid(True, alpha=0.3, axis='y')

# Quality flag by asset
qf_by_asset = df.groupby(['asset_id', 'quality_flag']).size().unstack(fill_value=0)
qf_by_asset.plot(kind='bar', ax=axes[1], colormap='RdYlGn')
axes[1].set_title('Quality Flags by Asset')
axes[1].set_xlabel('Asset ID')
axes[1].set_ylabel('Count')
axes[1].tick_params(axis='x', rotation=45)
axes[1].legend(title='Quality Flag', fontsize=8)
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/fig8_quality_flags.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 8 saved.")

# ============================================================
# FIGURE 9: Risk ranking - composite score
# ============================================================
# Normalize metrics for risk scoring
df_clean = df[df['quality_flag'] == 1].copy() if 1 in df['quality_flag'].values else df.copy()

# Calculate z-scores for risk metrics
for col in ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c']:
    df_clean[f'{col}_z'] = stats.zscore(df_clean[col].fillna(df_clean[col].mean()))

df_clean['risk_score'] = (df_clean['vibration_rms_mm_s_z'] + 
                           df_clean['peak_accel_g_z'] + 
                           df_clean['bearing_temp_c_z']) / 3

asset_risk = df_clean.groupby('asset_id')['risk_score'].mean().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(asset_risk.index, asset_risk.values, 
              color=['red' if v > 0.5 else 'orange' if v > 0 else 'green' for v in asset_risk.values])
ax.set_title('Asset Risk Ranking (Composite Score)', fontsize=14, fontweight='bold')
ax.set_xlabel('Asset ID')
ax.set_ylabel('Mean Risk Score (Z-score composite)')
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='High Risk Threshold')
ax.grid(True, alpha=0.3, axis='y')
ax.legend()
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('report/images/fig9_risk_ranking.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 9 saved.")

# Save risk ranking
asset_risk.to_csv('outputs/asset_risk_ranking.csv')

# ============================================================
# FIGURE 10: RPM vs Vibration relationship
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6))
for i, asset in enumerate(assets):
    asset_df = df[df['asset_id'] == asset]
    ax.scatter(asset_df['rpm'], asset_df['vibration_rms_mm_s'],
               label=asset, color=colors[i], alpha=0.5, s=15)

ax.set_xlabel('RPM')
ax.set_ylabel('Vibration RMS (mm/s)')
ax.set_title('RPM vs. Vibration RMS by Asset', fontsize=14, fontweight='bold')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/fig10_rpm_vs_vibration.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 10 saved.")

print("\n=== ALL ANALYSIS COMPLETE ===")
print("Outputs saved to outputs/ and report/images/")

# Print final summary for report
print("\n=== FINAL SUMMARY ===")
print(f"Total records: {len(df)}")
print(f"Assets: {list(df['asset_id'].unique())}")
print(f"Zones: {list(df['zone'].unique())}")
print(f"Time range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"\nVibration RMS stats:")
print(df.groupby('asset_id')['vibration_rms_mm_s'].describe())
print(f"\nBearing temp stats:")
print(df.groupby('asset_id')['bearing_temp_c'].describe())
print(f"\nRisk ranking:")
print(asset_risk)
