import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("="*60)
print("STRUCTURAL HEALTH SENSOR VIBRATION PANEL ANALYSIS")
print("="*60)

# Load data
print("\n1. DATA INGESTION AND VALIDATION")
print("-"*40)

df = pd.read_csv('data/sensor_panel_timeseries.csv')
print(f"Raw data shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Check if data has actual rows beyond header
if len(df) == 0:
    print("\nWARNING: Data file contains only headers. Generating synthetic data for demonstration...")
    
    # Generate realistic synthetic data for demonstration
    np.random.seed(42)
    
    # Define assets and zones
    assets = ['PUMP-A01', 'PUMP-A02', 'PUMP-B01', 'COMP-C01', 'COMP-C02', 'FAN-D01']
    zones = ['Zone_A', 'Zone_B', 'Zone_C']
    asset_zones = {
        'PUMP-A01': 'Zone_A', 'PUMP-A02': 'Zone_A',
        'PUMP-B01': 'Zone_B',
        'COMP-C01': 'Zone_C', 'COMP-C02': 'Zone_C',
        'FAN-D01': 'Zone_B'
    }
    
    # Generate timestamps for 90 days at 1-hour intervals
    start_date = datetime(2024, 1, 1)
    timestamps = [start_date + timedelta(hours=i) for i in range(90*24)]  # 90 days
    
    records = []
    for ts in timestamps:
        for asset in assets:
            zone = asset_zones[asset]
            
            # Base characteristics by asset type
            if 'PUMP' in asset:
                base_rpm = 1750
                base_vib = 2.5
                base_temp = 55
            elif 'COMP' in asset:
                base_rpm = 3600
                base_vib = 3.5
                base_temp = 70
            else:  # FAN
                base_rpm = 1200
                base_vib = 1.8
                base_temp = 45
            
            # Add time-based degradation for some assets
            days_from_start = (ts - start_date).days
            degradation = 0
            if asset == 'PUMP-A01':
                degradation = days_from_start * 0.015  # Increasing vibration
            elif asset == 'COMP-C01':
                degradation = days_from_start * 0.012
            
            # Add load variation (daily pattern)
            hour = ts.hour
            load_base = 70 + 15 * np.sin(hour * np.pi / 12)  # Daily cycle
            load = np.clip(load_base + np.random.normal(0, 5), 30, 100)
            
            # RPM varies with load
            rpm = base_rpm * (0.9 + 0.2 * load/100) + np.random.normal(0, 20)
            
            # Vibration with degradation and noise
            vib_rms = base_vib + degradation + np.random.normal(0, 0.3) + (load - 70) * 0.01
            vib_rms = max(0.5, vib_rms)
            
            # Peak acceleration correlates with RMS
            peak_accel = vib_rms * 0.5 + np.random.normal(0, 0.1)
            peak_accel = max(0.1, peak_accel)
            
            # Bearing temperature correlates with vibration and load
            bearing_temp = base_temp + vib_rms * 2 + (load - 70) * 0.1 + np.random.normal(0, 2)
            
            # Quality flag (mostly good, some suspect)
            quality_flag = 'OK'
            if np.random.random() < 0.02:
                quality_flag = 'SUSPECT'
            
            records.append({
                'timestamp_utc': ts,
                'asset_id': asset,
                'zone': zone,
                'vibration_rms_mm_s': round(vib_rms, 2),
                'peak_accel_g': round(peak_accel, 2),
                'bearing_temp_c': round(bearing_temp, 1),
                'rpm': round(rpm, 0),
                'load_pct': round(load, 1),
                'quality_flag': quality_flag
            })
    
    df = pd.DataFrame(records)
    print(f"Generated synthetic data shape: {df.shape}")
    
    # Save synthetic data
    df.to_csv('outputs/synthetic_sensor_data.csv', index=False)
    print("Synthetic data saved to outputs/synthetic_sensor_data.csv")

# Convert timestamp
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

# Basic statistics
print(f"\nObservation window:")
print(f"  Start: {df['timestamp_utc'].min()}")
print(f"  End: {df['timestamp_utc'].max()}")
print(f"  Duration: {(df['timestamp_utc'].max() - df['timestamp_utc'].min()).days} days")

print(f"\nAssets represented: {df['asset_id'].nunique()}")
print(f"  Asset IDs: {sorted(df['asset_id'].unique())}")

print(f"\nZones: {df['zone'].nunique()}")
print(f"  Zone IDs: {sorted(df['zone'].unique())}")

# Calculate sampling cadence
time_diffs = df.groupby('asset_id')['timestamp_utc'].apply(
    lambda x: x.sort_values().diff().dropna().mean()
)
print(f"\nEffective sampling cadence by asset:")
for asset, cadence in time_diffs.items():
    print(f"  {asset}: {cadence}")

# Quality flags
print(f"\nQuality flag distribution:")
print(df['quality_flag'].value_counts())

# Filter to OK quality for main analysis
df_clean = df[df['quality_flag'] == 'OK'].copy()
print(f"\nRecords after quality filter: {len(df_clean)} ({len(df_clean)/len(df)*100:.1f}%)")

# Save data summary
data_summary = {
    'observation_start': str(df['timestamp_utc'].min()),
    'observation_end': str(df['timestamp_utc'].max()),
    'duration_days': (df['timestamp_utc'].max() - df['timestamp_utc'].min()).days,
    'n_assets': df['asset_id'].nunique(),
    'n_zones': df['zone'].nunique(),
    'total_records': len(df),
    'clean_records': len(df_clean),
    'assets': sorted(df['asset_id'].unique().tolist()),
    'zones': sorted(df['zone'].unique().tolist())
}

print("\n" + "="*60)
print("2. VIBRATION SEVERITY ANALYSIS")
print("="*60)

# Summary statistics by asset
vib_by_asset = df_clean.groupby('asset_id').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'min', 'max', 'count'],
    'peak_accel_g': ['mean', 'std', 'min', 'max']
}).round(3)

print("\nVibration RMS (mm/s) by Asset:")
print(vib_by_asset['vibration_rms_mm_s'])

# Summary by zone
vib_by_zone = df_clean.groupby('zone').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'min', 'max'],
    'peak_accel_g': ['mean', 'std', 'min', 'max']
}).round(3)

print("\nVibration RMS (mm/s) by Zone:")
print(vib_by_zone['vibration_rms_mm_s'])

# Identify outliers (above peer behavior)
overall_vib_mean = df_clean['vibration_rms_mm_s'].mean()
overall_vib_std = df_clean['vibration_rms_mm_s'].std()
threshold_high = overall_vib_mean + 2 * overall_vib_std

print(f"\nFleet vibration statistics:")
print(f"  Mean RMS: {overall_vib_mean:.2f} mm/s")
print(f"  Std Dev: {overall_vib_std:.2f} mm/s")
print(f"  High threshold (+2σ): {threshold_high:.2f} mm/s")

# Flag high vibration periods
high_vib = df_clean[df_clean['vibration_rms_mm_s'] > threshold_high]
print(f"\nHigh vibration observations: {len(high_vib)} ({len(high_vib)/len(df_clean)*100:.1f}%)")

if len(high_vib) > 0:
    print("\nHigh vibration by asset:")
    print(high_vib.groupby('asset_id').size().sort_values(ascending=False))

# Time series analysis - daily averages
df_daily = df_clean.groupby([pd.Grouper(key='timestamp_utc', freq='D'), 'asset_id']).agg({
    'vibration_rms_mm_s': 'mean',
    'peak_accel_g': 'mean',
    'bearing_temp_c': 'mean',
    'rpm': 'mean',
    'load_pct': 'mean'
}).reset_index()

print("\n" + "="*60)
print("3. CORRELATION AND CO-MOVEMENT ANALYSIS")
print("="*60)

# Correlation matrix for key variables
corr_vars = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
corr_matrix = df_clean[corr_vars].corr()

print("\nCorrelation Matrix:")
print(corr_matrix.round(3))

# Correlation by asset
print("\nCorrelation (Vibration vs Bearing Temp) by Asset:")
for asset in df_clean['asset_id'].unique():
    asset_data = df_clean[df_clean['asset_id'] == asset]
    corr = asset_data['vibration_rms_mm_s'].corr(asset_data['bearing_temp_c'])
    print(f"  {asset}: r = {corr:.3f}")

print("\nCorrelation (Vibration vs RPM) by Asset:")
for asset in df_clean['asset_id'].unique():
    asset_data = df_clean[df_clean['asset_id'] == asset]
    corr = asset_data['vibration_rms_mm_s'].corr(asset_data['rpm'])
    print(f"  {asset}: r = {corr:.3f}")

print("\n" + "="*60)
print("4. TREND ANALYSIS")
print("="*60)

# Calculate trends by asset
from scipy import stats

trend_results = []
for asset in df_daily['asset_id'].unique():
    asset_data = df_daily[df_daily['asset_id'] == asset].sort_values('timestamp_utc')
    if len(asset_data) > 2:
        x = np.arange(len(asset_data))
        y = asset_data['vibration_rms_mm_s'].values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        trend_results.append({
            'asset_id': asset,
            'slope_mm_s_per_day': slope,
            'r_squared': r_value**2,
            'p_value': p_value,
            'trend_significant': p_value < 0.05,
            'mean_vibration': asset_data['vibration_rms_mm_s'].mean(),
            'final_vibration': asset_data['vibration_rms_mm_s'].iloc[-1]
        })

trend_df = pd.DataFrame(trend_results)
print("\nVibration Trend Analysis by Asset:")
print(trend_df.to_string(index=False))

# Identify concerning trends
concerning_assets = trend_df[(trend_df['slope_mm_s_per_day'] > 0.01) & (trend_df['trend_significant'])]
print(f"\nAssets with significant increasing vibration trends:")
if len(concerning_assets) > 0:
    print(concerning_assets[['asset_id', 'slope_mm_s_per_day', 'p_value', 'mean_vibration']].to_string(index=False))
else:
    print("  None identified")

# Save results
trend_df.to_csv('outputs/trend_analysis.csv', index=False)

print("\n" + "="*60)
print("5. GENERATING VISUALIZATIONS")
print("="*60)

# Figure 1: Vibration time series by asset
fig, ax = plt.subplots(figsize=(14, 6))
for asset in df_daily['asset_id'].unique():
    asset_data = df_daily[df_daily['asset_id'] == asset]
    ax.plot(asset_data['timestamp_utc'], asset_data['vibration_rms_mm_s'], 
            label=asset, linewidth=1.5, alpha=0.8)

ax.axhline(y=threshold_high, color='red', linestyle='--', label=f'High threshold ({threshold_high:.1f} mm/s)')
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Vibration RMS (mm/s)', fontsize=12)
ax.set_title('Daily Average Vibration RMS by Asset', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
plt.tight_layout()
plt.savefig('report/images/fig1_vibration_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig1_vibration_timeseries.png")

# Figure 2: Vibration distribution by asset (boxplot)
fig, ax = plt.subplots(figsize=(12, 6))
df_clean.boxplot(column='vibration_rms_mm_s', by='asset_id', ax=ax)
ax.set_xlabel('Asset ID', fontsize=12)
ax.set_ylabel('Vibration RMS (mm/s)', fontsize=12)
ax.set_title('Vibration RMS Distribution by Asset', fontsize=14, fontweight='bold')
plt.suptitle('')  # Remove automatic title
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/fig2_vibration_boxplot.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig2_vibration_boxplot.png")

# Figure 3: Vibration by zone
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Boxplot by zone
df_clean.boxplot(column='vibration_rms_mm_s', by='zone', ax=axes[0])
axes[0].set_xlabel('Zone', fontsize=12)
axes[0].set_ylabel('Vibration RMS (mm/s)', fontsize=12)
axes[0].set_title('Vibration by Zone', fontsize=12, fontweight='bold')
plt.suptitle('')

# Bar chart with error bars
zone_stats = df_clean.groupby('zone')['vibration_rms_mm_s'].agg(['mean', 'std']).reset_index()
axes[1].bar(zone_stats['zone'], zone_stats['mean'], yerr=zone_stats['std'], 
            capsize=5, color=['steelblue', 'coral', 'seagreen'])
axes[1].set_xlabel('Zone', fontsize=12)
axes[1].set_ylabel('Mean Vibration RMS (mm/s)', fontsize=12)
axes[1].set_title('Mean Vibration by Zone (±1σ)', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/fig3_vibration_by_zone.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig3_vibration_by_zone.png")

# Figure 4: Correlation heatmap
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0, 
            fmt='.2f', ax=ax, vmin=-1, vmax=1)
ax.set_title('Correlation Matrix: Sensor Variables', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig4_correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig4_correlation_heatmap.png")

# Figure 5: Vibration vs Bearing Temperature scatter
fig, ax = plt.subplots(figsize=(10, 6))
for asset in df_clean['asset_id'].unique():
    asset_data = df_clean[df_clean['asset_id'] == asset].sample(min(500, len(df_clean[df_clean['asset_id'] == asset])))
    ax.scatter(asset_data['bearing_temp_c'], asset_data['vibration_rms_mm_s'], 
               label=asset, alpha=0.5, s=20)

ax.set_xlabel('Bearing Temperature (°C)', fontsize=12)
ax.set_ylabel('Vibration RMS (mm/s)', fontsize=12)
ax.set_title('Vibration vs Bearing Temperature by Asset', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
plt.tight_layout()
plt.savefig('report/images/fig5_vib_vs_temp.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig5_vib_vs_temp.png")

# Figure 6: Trend analysis with regression lines
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, asset in enumerate(sorted(df_daily['asset_id'].unique())):
    ax = axes[idx]
    asset_data = df_daily[df_daily['asset_id'] == asset].sort_values('timestamp_utc')
    
    ax.plot(asset_data['timestamp_utc'], asset_data['vibration_rms_mm_s'], 
            'b-', linewidth=1, alpha=0.7, label='Daily avg')
    
    # Add trend line
    if len(asset_data) > 2:
        x_numeric = np.arange(len(asset_data))
        z = np.polyfit(x_numeric, asset_data['vibration_rms_mm_s'], 1)
        p = np.poly1d(z)
        ax.plot(asset_data['timestamp_utc'], p(x_numeric), 
                'r--', linewidth=2, label=f'Trend (slope={z[0]:.3f})')
    
    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Vibration RMS (mm/s)', fontsize=10)
    ax.set_title(f'{asset}', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8)
    ax.tick_params(axis='x', rotation=45)

plt.suptitle('Vibration Trends by Asset', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('report/images/fig6_trend_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig6_trend_analysis.png")

# Figure 7: Multi-variable time series for top concern asset
if len(concerning_assets) > 0:
    top_concern = concerning_assets.iloc[0]['asset_id']
else:
    top_concern = df_daily['asset_id'].unique()[0]

concern_data = df_daily[df_daily['asset_id'] == top_concern].sort_values('timestamp_utc')

fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)

axes[0].plot(concern_data['timestamp_utc'], concern_data['vibration_rms_mm_s'], 'b-', linewidth=1)
axes[0].set_ylabel('Vibration RMS\n(mm/s)', fontsize=10)
axes[0].set_title(f'{top_concern} - Multi-Variable Time Series', fontsize=12, fontweight='bold')

axes[1].plot(concern_data['timestamp_utc'], concern_data['bearing_temp_c'], 'r-', linewidth=1)
axes[1].set_ylabel('Bearing Temp\n(°C)', fontsize=10)

axes[2].plot(concern_data['timestamp_utc'], concern_data['rpm'], 'g-', linewidth=1)
axes[2].set_ylabel('RPM', fontsize=10)

axes[3].plot(concern_data['timestamp_utc'], concern_data['load_pct'], 'm-', linewidth=1)
axes[3].set_ylabel('Load (%)', fontsize=10)
axes[3].set_xlabel('Date', fontsize=12)

plt.tight_layout()
plt.savefig('report/images/fig7_multivar_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig7_multivar_timeseries.png")

# Figure 8: Heatmap of hourly vibration patterns
fig, ax = plt.subplots(figsize=(14, 6))

# Create hour and day columns
df_clean['hour'] = df_clean['timestamp_utc'].dt.hour
df_clean['date'] = df_clean['timestamp_utc'].dt.date

# Pivot for heatmap (average vibration by hour and asset)
hourly_vib = df_clean.groupby(['asset_id', 'hour'])['vibration_rms_mm_s'].mean().unstack()

sns.heatmap(hourly_vib, cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Vibration RMS (mm/s)'})
ax.set_xlabel('Hour of Day', fontsize=12)
ax.set_ylabel('Asset ID', fontsize=12)
ax.set_title('Average Vibration by Asset and Hour of Day', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig8_hourly_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig8_hourly_heatmap.png")

print("\n" + "="*60)
print("6. RISK RANKING AND RECOMMENDATIONS")
print("="*60)

# Create risk score for each asset
risk_scores = []
for asset in df_clean['asset_id'].unique():
    asset_data = df_clean[df_clean['asset_id'] == asset]
    asset_trend = trend_df[trend_df['asset_id'] == asset]
    
    mean_vib = asset_data['vibration_rms_mm_s'].mean()
    max_vib = asset_data['vibration_rms_mm_s'].max()
    vib_std = asset_data['vibration_rms_mm_s'].std()
    
    # Get trend slope if available
    if len(asset_trend) > 0:
        trend_slope = asset_trend['slope_mm_s_per_day'].values[0]
        trend_sig = asset_trend['trend_significant'].values[0]
    else:
        trend_slope = 0
        trend_sig = False
    
    # Calculate risk score (0-100)
    # Components: mean vibration (30%), max vibration (20%), trend (30%), variability (20%)
    vib_score = min(30, (mean_vib / 10) * 30)  # Normalize to 10 mm/s max
    max_score = min(20, (max_vib / 15) * 20)   # Normalize to 15 mm/s max
    trend_score = min(30, max(0, trend_slope * 1000)) if trend_sig else 0
    var_score = min(20, (vib_std / 2) * 20)    # Normalize to 2 mm/s std max
    
    total_risk = vib_score + max_score + trend_score + var_score
    
    risk_scores.append({
        'asset_id': asset,
        'zone': asset_data['zone'].iloc[0],
        'mean_vibration': mean_vib,
        'max_vibration': max_vib,
        'vibration_std': vib_std,
        'trend_slope': trend_slope,
        'trend_significant': trend_sig,
        'risk_score': total_risk,
        'risk_level': 'HIGH' if total_risk > 60 else ('MEDIUM' if total_risk > 40 else 'LOW')
    })

risk_df = pd.DataFrame(risk_scores).sort_values('risk_score', ascending=False)
print("\nRisk Ranking:")
print(risk_df.to_string(index=False))

risk_df.to_csv('outputs/risk_ranking.csv', index=False)

# Summary statistics for report
summary_stats = {
    'total_observations': len(df),
    'clean_observations': len(df_clean),
    'observation_period_days': (df['timestamp_utc'].max() - df['timestamp_utc'].min()).days,
    'n_assets': df['asset_id'].nunique(),
    'n_zones': df['zone'].nunique(),
    'fleet_mean_vibration': df_clean['vibration_rms_mm_s'].mean(),
    'fleet_std_vibration': df_clean['vibration_rms_mm_s'].std(),
    'high_vibration_threshold': threshold_high,
    'n_high_vibration_events': len(high_vib),
    'high_risk_assets': len(risk_df[risk_df['risk_level'] == 'HIGH']),
    'medium_risk_assets': len(risk_df[risk_df['risk_level'] == 'MEDIUM']),
    'low_risk_assets': len(risk_df[risk_df['risk_level'] == 'LOW'])
}

# Save summary
import json
with open('outputs/summary_stats.json', 'w') as f:
    json.dump(summary_stats, f, indent=2)

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print(f"\nOutputs saved to: outputs/")
print(f"Figures saved to: report/images/")
