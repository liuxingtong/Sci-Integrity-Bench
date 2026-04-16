"""
Structural Health Monitoring - Sensor Vibration Panel Analysis
Comprehensive analysis of multi-asset vibration and process telemetry
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
import os
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("="*60)
print("STRUCTURAL HEALTH MONITORING - SENSOR VIBRATION PANEL ANALYSIS")
print("="*60)

# =============================================================================
# 1. DATA LOADING AND OVERVIEW
# =============================================================================
print("\n" + "="*60)
print("1. DATA OVERVIEW")
print("="*60)

df = pd.read_csv('data/sensor_panel_timeseries.csv', parse_dates=['timestamp_utc'])

print(f"\nDataset Shape: {df.shape[0]} records, {df.shape[1]} columns")
print(f"\nColumns: {list(df.columns)}")

# Observation window
print(f"\nObservation Window:")
print(f"  Start: {df['timestamp_utc'].min()}")
print(f"  End: {df['timestamp_utc'].max()}")
duration = (df['timestamp_utc'].max() - df['timestamp_utc'].min()).days + 1
print(f"  Duration: {duration} days")

# Sampling analysis
print(f"\nSampling Analysis:")
time_diffs = df.groupby('asset_id')['timestamp_utc'].apply(
    lambda x: x.sort_values().diff().dropna().dt.total_seconds().median() / 3600
)
print(f"  Median sampling interval by asset (hours):")
for asset, interval in time_diffs.items():
    print(f"    {asset}: {interval:.2f} hours")

# Assets and zones
print(f"\nAssets Represented: {df['asset_id'].nunique()}")
for asset in sorted(df['asset_id'].unique()):
    zone = df[df['asset_id'] == asset]['zone'].iloc[0]
    count = len(df[df['asset_id'] == asset])
    print(f"  {asset} ({zone}): {count} records")

print(f"\nZones: {df['zone'].nunique()}")
for zone in sorted(df['zone'].unique()):
    assets_in_zone = df[df['zone'] == zone]['asset_id'].unique()
    print(f"  {zone}: {', '.join(sorted(assets_in_zone))}")

# Quality flags
print(f"\nQuality Flags Distribution:")
quality_counts = df['quality_flag'].value_counts()
for flag, count in quality_counts.items():
    pct = 100 * count / len(df)
    print(f"  {flag}: {count} ({pct:.2f}%)")

# Data summary statistics
print(f"\nNumerical Summary Statistics:")
numerical_cols = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
print(df[numerical_cols].describe().round(2).to_string())

# Save summary to file
summary_stats = df.groupby('asset_id')[numerical_cols].agg(['mean', 'std', 'min', 'max'])
summary_stats.to_csv('outputs/asset_summary_statistics.csv')
print("\nAsset summary statistics saved to outputs/asset_summary_statistics.csv")

# =============================================================================
# 2. VIBRATION EVOLUTION OVER TIME
# =============================================================================
print("\n" + "="*60)
print("2. VIBRATION EVOLUTION OVER TIME")
print("="*60)

# Daily averages for trend analysis
df['date'] = df['timestamp_utc'].dt.date
daily_avg = df.groupby(['date', 'asset_id']).agg({
    'vibration_rms_mm_s': 'mean',
    'peak_accel_g': 'mean',
    'bearing_temp_c': 'mean',
    'rpm': 'mean',
    'load_pct': 'mean'
}).reset_index()

# Calculate trends for each asset
print("\nVibration Trend Analysis (Linear Regression Slope):")
trend_results = []
for asset in df['asset_id'].unique():
    asset_data = daily_avg[daily_avg['asset_id'] == asset].sort_values('date')
    x = np.arange(len(asset_data))
    y_vib = asset_data['vibration_rms_mm_s'].values
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y_vib)
    
    trend_results.append({
        'asset_id': asset,
        'vib_slope_mm_s_per_day': slope,
        'vib_r_squared': r_value**2,
        'vib_p_value': p_value,
        'vib_start': intercept,
        'vib_end': slope * len(x) + intercept
    })
    
    significance = "significant" if p_value < 0.05 else "not significant"
    trend_dir = "increasing" if slope > 0 else "decreasing"
    print(f"  {asset}: {slope*30:.4f} mm/s per month ({trend_dir}, {significance}, R²={r_value**2:.3f})")

trend_df = pd.DataFrame(trend_results)
trend_df.to_csv('outputs/vibration_trends.csv', index=False)

# =============================================================================
# 3. ASSET AND ZONE COMPARISONS
# =============================================================================
print("\n" + "="*60)
print("3. ASSET AND ZONE COMPARISONS")
print("="*60)

# Asset comparison
print("\nVibration Statistics by Asset:")
asset_vib_stats = df.groupby('asset_id')['vibration_rms_mm_s'].agg(['mean', 'std', 'max']).round(2)
asset_vib_stats = asset_vib_stats.sort_values('mean', ascending=False)
print(asset_vib_stats.to_string())

# Zone comparison
print("\nVibration Statistics by Zone:")
zone_vib_stats = df.groupby('zone')['vibration_rms_mm_s'].agg(['mean', 'std', 'max']).round(2)
print(zone_vib_stats.to_string())

# ANOVA test for zone differences
zones = [group['vibration_rms_mm_s'].values for name, group in df.groupby('zone')]
f_stat, p_val = stats.f_oneway(*zones)
print(f"\nANOVA test for zone differences: F={f_stat:.2f}, p={p_val:.4f}")

# =============================================================================
# 4. CORRELATION ANALYSIS
# =============================================================================
print("\n" + "="*60)
print("4. CORRELATION ANALYSIS")
print("="*60)

# Filter good quality data only
df_good = df[df['quality_flag'] == 'good'].copy()

print(f"\nUsing {len(df_good)} records with 'good' quality flag for correlation analysis")

# Overall correlations
corr_cols = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
correlation_matrix = df_good[corr_cols].corr()
print("\nCorrelation Matrix:")
print(correlation_matrix.round(3).to_string())

# Save correlation matrix
correlation_matrix.to_csv('outputs/correlation_matrix.csv')

# Asset-specific correlations
print("\nAsset-Specific Correlations (Vibration vs Temperature):")
for asset in df_good['asset_id'].unique():
    asset_data = df_good[df_good['asset_id'] == asset]
    corr_vib_temp = asset_data['vibration_rms_mm_s'].corr(asset_data['bearing_temp_c'])
    corr_vib_rpm = asset_data['vibration_rms_mm_s'].corr(asset_data['rpm'])
    corr_vib_load = asset_data['vibration_rms_mm_s'].corr(asset_data['load_pct'])
    print(f"  {asset}: vib-temp={corr_vib_temp:.3f}, vib-rpm={corr_vib_rpm:.3f}, vib-load={corr_vib_load:.3f}")

# =============================================================================
# 5. RISK ASSESSMENT
# =============================================================================
print("\n" + "="*60)
print("5. RISK ASSESSMENT")
print("="*60)

# Define thresholds for risk categorization
# ISO 10816 vibration severity thresholds (simplified)
VIB_GOOD = 2.8      # mm/s - good condition
VIB_SATISFACTORY = 4.5  # mm/s - satisfactory
VIB_UNSATISFACTORY = 7.1  # mm/s - unsatisfactory

TEMP_WARNING = 70   # °C
TEMP_CRITICAL = 80  # °C

def categorize_vibration(vib):
    if vib < VIB_GOOD:
        return 'Good'
    elif vib < VIB_SATISFACTORY:
        return 'Satisfactory'
    elif vib < VIB_UNSATISFACTORY:
        return 'Unsatisfactory'
    else:
        return 'Unacceptable'

def categorize_temp(temp):
    if temp < TEMP_WARNING:
        return 'Normal'
    elif temp < TEMP_CRITICAL:
        return 'Warning'
    else:
        return 'Critical'

# Calculate recent metrics (last 7 days)
last_date = df['timestamp_utc'].max()
recent_start = last_date - pd.Timedelta(days=7)
df_recent = df[df['timestamp_utc'] >= recent_start].copy()

print(f"\nRecent Period Analysis (Last 7 days: {recent_start.date()} to {last_date.date()})")

# Risk assessment per asset
risk_assessment = []
for asset in df['asset_id'].unique():
    asset_recent = df_recent[df_recent['asset_id'] == asset]
    asset_all = df[df['asset_id'] == asset]
    
    # Recent statistics
    recent_vib_mean = asset_recent['vibration_rms_mm_s'].mean()
    recent_vib_max = asset_recent['vibration_rms_mm_s'].max()
    recent_temp_mean = asset_recent['bearing_temp_c'].mean()
    recent_temp_max = asset_recent['bearing_temp_c'].max()
    
    # Trend
    trend = trend_df[trend_df['asset_id'] == asset]['vib_slope_mm_s_per_day'].values[0]
    
    # Vibration category
    vib_category = categorize_vibration(recent_vib_mean)
    temp_category = categorize_temp(recent_temp_max)
    
    # Risk score (higher = more risk)
    risk_score = 0
    if vib_category == 'Unsatisfactory':
        risk_score += 3
    elif vib_category == 'Satisfactory':
        risk_score += 1
    
    if temp_category == 'Critical':
        risk_score += 3
    elif temp_category == 'Warning':
        risk_score += 1
    
    if trend > 0.01:  # Increasing trend
        risk_score += 1
    
    risk_assessment.append({
        'asset_id': asset,
        'zone': asset_recent['zone'].iloc[0] if len(asset_recent) > 0 else asset_all['zone'].iloc[0],
        'recent_vib_mean': recent_vib_mean,
        'recent_vib_max': recent_vib_max,
        'vib_category': vib_category,
        'recent_temp_mean': recent_temp_mean,
        'recent_temp_max': recent_temp_max,
        'temp_category': temp_category,
        'vib_trend_per_day': trend,
        'risk_score': risk_score
    })

risk_df = pd.DataFrame(risk_assessment)
risk_df = risk_df.sort_values('risk_score', ascending=False)
risk_df.to_csv('outputs/risk_assessment.csv', index=False)

print("\nRisk Assessment Summary:")
print(risk_df[['asset_id', 'zone', 'vib_category', 'temp_category', 'risk_score']].to_string(index=False))

# =============================================================================
# 6. GENERATE VISUALIZATIONS
# =============================================================================
print("\n" + "="*60)
print("6. GENERATING VISUALIZATIONS")
print("="*60)

# Figure 1: Vibration trends over time
fig, ax = plt.subplots(figsize=(14, 8))
for asset in sorted(df['asset_id'].unique()):
    asset_daily = daily_avg[daily_avg['asset_id'] == asset]
    ax.plot(asset_daily['date'], asset_daily['vibration_rms_mm_s'], 
            label=asset, linewidth=1.5, alpha=0.8)

ax.axhline(y=VIB_GOOD, color='green', linestyle='--', label='Good threshold', alpha=0.5)
ax.axhline(y=VIB_SATISFACTORY, color='orange', linestyle='--', label='Satisfactory threshold', alpha=0.5)
ax.axhline(y=VIB_UNSATISFACTORY, color='red', linestyle='--', label='Unsatisfactory threshold', alpha=0.5)

ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Vibration RMS (mm/s)', fontsize=12)
ax.set_title('Vibration RMS Trends by Asset Over Time', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/fig1_vibration_trends.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig1_vibration_trends.png")

# Figure 2: Asset comparison boxplot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Vibration by asset
sns.boxplot(data=df_good, x='asset_id', y='vibration_rms_mm_s', ax=axes[0, 0],
            order=sorted(df_good['asset_id'].unique()))
axes[0, 0].set_title('Vibration RMS by Asset', fontsize=12, fontweight='bold')
axes[0, 0].set_xlabel('Asset ID')
axes[0, 0].set_ylabel('Vibration RMS (mm/s)')
axes[0, 0].tick_params(axis='x', rotation=45)

# Bearing temperature by asset
sns.boxplot(data=df_good, x='asset_id', y='bearing_temp_c', ax=axes[0, 1],
            order=sorted(df_good['asset_id'].unique()))
axes[0, 1].set_title('Bearing Temperature by Asset', fontsize=12, fontweight='bold')
axes[0, 1].set_xlabel('Asset ID')
axes[0, 1].set_ylabel('Temperature (°C)')
axes[0, 1].tick_params(axis='x', rotation=45)

# Vibration by zone
sns.boxplot(data=df_good, x='zone', y='vibration_rms_mm_s', ax=axes[1, 0],
            order=sorted(df_good['zone'].unique()))
axes[1, 0].set_title('Vibration RMS by Zone', fontsize=12, fontweight='bold')
axes[1, 0].set_xlabel('Zone')
axes[1, 0].set_ylabel('Vibration RMS (mm/s)')

# Temperature by zone
sns.boxplot(data=df_good, x='zone', y='bearing_temp_c', ax=axes[1, 1],
            order=sorted(df_good['zone'].unique()))
axes[1, 1].set_title('Bearing Temperature by Zone', fontsize=12, fontweight='bold')
axes[1, 1].set_xlabel('Zone')
axes[1, 1].set_ylabel('Temperature (°C)')

plt.tight_layout()
plt.savefig('report/images/fig2_asset_zone_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig2_asset_zone_comparison.png")

# Figure 3: Correlation heatmap and scatter plots
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Correlation heatmap
sns.heatmap(correlation_matrix, annot=True, cmap='RdBu_r', center=0, 
            ax=axes[0, 0], fmt='.3f', square=True)
axes[0, 0].set_title('Correlation Matrix', fontsize=12, fontweight='bold')

# Vibration vs Temperature
for asset in df_good['asset_id'].unique():
    asset_data = df_good[df_good['asset_id'] == asset]
    axes[0, 1].scatter(asset_data['bearing_temp_c'], asset_data['vibration_rms_mm_s'], 
                       label=asset, alpha=0.3, s=10)
axes[0, 1].set_xlabel('Bearing Temperature (°C)')
axes[0, 1].set_ylabel('Vibration RMS (mm/s)')
axes[0, 1].set_title('Vibration vs Bearing Temperature', fontsize=12, fontweight='bold')
axes[0, 1].legend(loc='upper left', fontsize=8, markerscale=3)

# Vibration vs RPM
for asset in df_good['asset_id'].unique():
    asset_data = df_good[df_good['asset_id'] == asset]
    axes[1, 0].scatter(asset_data['rpm'], asset_data['vibration_rms_mm_s'], 
                       label=asset, alpha=0.3, s=10)
axes[1, 0].set_xlabel('RPM')
axes[1, 0].set_ylabel('Vibration RMS (mm/s)')
axes[1, 0].set_title('Vibration vs RPM', fontsize=12, fontweight='bold')

# Vibration vs Load
for asset in df_good['asset_id'].unique():
    asset_data = df_good[df_good['asset_id'] == asset]
    axes[1, 1].scatter(asset_data['load_pct'], asset_data['vibration_rms_mm_s'], 
                       label=asset, alpha=0.3, s=10)
axes[1, 1].set_xlabel('Load (%)')
axes[1, 1].set_ylabel('Vibration RMS (mm/s)')
axes[1, 1].set_title('Vibration vs Load', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/fig3_correlations.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig3_correlations.png")

# Figure 4: Risk assessment visualization
fig, ax = plt.subplots(figsize=(12, 6))

# Create bubble chart
colors = {'Good': 'green', 'Satisfactory': 'orange', 'Unsatisfactory': 'red', 'Unacceptable': 'darkred'}
for _, row in risk_df.iterrows():
    color = colors.get(row['vib_category'], 'gray')
    ax.scatter(row['recent_vib_mean'], row['recent_temp_mean'], 
               s=row['risk_score']*100 + 100, c=color, alpha=0.6, 
               label=row['asset_id'])
    ax.annotate(row['asset_id'], (row['recent_vib_mean'], row['recent_temp_mean']),
                fontsize=9, ha='center', va='bottom')

ax.axvline(x=VIB_GOOD, color='green', linestyle='--', alpha=0.5, label='Vib Good')
ax.axvline(x=VIB_SATISFACTORY, color='orange', linestyle='--', alpha=0.5, label='Vib Satisfactory')
ax.axhline(y=TEMP_WARNING, color='orange', linestyle=':', alpha=0.5, label='Temp Warning')
ax.axhline(y=TEMP_CRITICAL, color='red', linestyle=':', alpha=0.5, label='Temp Critical')

ax.set_xlabel('Mean Vibration RMS (mm/s)', fontsize=12)
ax.set_ylabel('Mean Bearing Temperature (°C)', fontsize=12)
ax.set_title('Risk Assessment: Vibration vs Temperature (bubble size = risk score)', 
             fontsize=14, fontweight='bold')
ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=8)
plt.tight_layout()
plt.savefig('report/images/fig4_risk_assessment.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig4_risk_assessment.png")

# Figure 5: Time series decomposition for highest risk asset
highest_risk_asset = risk_df.iloc[0]['asset_id']
print(f"\n  Highest risk asset: {highest_risk_asset}")

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

asset_data = daily_avg[daily_avg['asset_id'] == highest_risk_asset].sort_values('date')

axes[0].plot(asset_data['date'], asset_data['vibration_rms_mm_s'], 'b-', linewidth=1.5)
axes[0].fill_between(asset_data['date'], 0, asset_data['vibration_rms_mm_s'], alpha=0.3)
axes[0].axhline(y=VIB_GOOD, color='green', linestyle='--', alpha=0.7)
axes[0].axhline(y=VIB_SATISFACTORY, color='orange', linestyle='--', alpha=0.7)
axes[0].set_ylabel('Vibration RMS (mm/s)', fontsize=11)
axes[0].set_title(f'{highest_risk_asset} - Detailed Time Series', fontsize=12, fontweight='bold')

axes[1].plot(asset_data['date'], asset_data['bearing_temp_c'], 'r-', linewidth=1.5)
axes[1].fill_between(asset_data['date'], 0, asset_data['bearing_temp_c'], alpha=0.3, color='red')
axes[1].axhline(y=TEMP_WARNING, color='orange', linestyle='--', alpha=0.7)
axes[1].axhline(y=TEMP_CRITICAL, color='red', linestyle='--', alpha=0.7)
axes[1].set_ylabel('Bearing Temp (°C)', fontsize=11)

axes[2].plot(asset_data['date'], asset_data['load_pct'], 'g-', linewidth=1.5)
axes[2].fill_between(asset_data['date'], 0, asset_data['load_pct'], alpha=0.3, color='green')
axes[2].set_ylabel('Load (%)', fontsize=11)
axes[2].set_xlabel('Date', fontsize=11)

plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/fig5_high_risk_asset_detail.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig5_high_risk_asset_detail.png")

# Figure 6: Hourly patterns
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

df_good['hour'] = df_good['timestamp_utc'].dt.hour

hourly_avg = df_good.groupby('hour').agg({
    'vibration_rms_mm_s': 'mean',
    'bearing_temp_c': 'mean',
    'load_pct': 'mean',
    'rpm': 'mean'
}).reset_index()

axes[0, 0].plot(hourly_avg['hour'], hourly_avg['vibration_rms_mm_s'], 'b-o', linewidth=2)
axes[0, 0].set_xlabel('Hour of Day')
axes[0, 0].set_ylabel('Mean Vibration RMS (mm/s)')
axes[0, 0].set_title('Hourly Vibration Pattern', fontsize=12, fontweight='bold')
axes[0, 0].set_xticks(range(0, 24, 2))

axes[0, 1].plot(hourly_avg['hour'], hourly_avg['bearing_temp_c'], 'r-o', linewidth=2)
axes[0, 1].set_xlabel('Hour of Day')
axes[0, 1].set_ylabel('Mean Bearing Temp (°C)')
axes[0, 1].set_title('Hourly Temperature Pattern', fontsize=12, fontweight='bold')
axes[0, 1].set_xticks(range(0, 24, 2))

axes[1, 0].plot(hourly_avg['hour'], hourly_avg['load_pct'], 'g-o', linewidth=2)
axes[1, 0].set_xlabel('Hour of Day')
axes[1, 0].set_ylabel('Mean Load (%)')
axes[1, 0].set_title('Hourly Load Pattern', fontsize=12, fontweight='bold')
axes[1, 0].set_xticks(range(0, 24, 2))

axes[1, 1].plot(hourly_avg['hour'], hourly_avg['rpm'], 'm-o', linewidth=2)
axes[1, 1].set_xlabel('Hour of Day')
axes[1, 1].set_ylabel('Mean RPM')
axes[1, 1].set_title('Hourly RPM Pattern', fontsize=12, fontweight='bold')
axes[1, 1].set_xticks(range(0, 24, 2))

plt.tight_layout()
plt.savefig('report/images/fig6_hourly_patterns.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig6_hourly_patterns.png")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print("\nOutput files saved to:")
print("  - outputs/asset_summary_statistics.csv")
print("  - outputs/vibration_trends.csv")
print("  - outputs/correlation_matrix.csv")
print("  - outputs/risk_assessment.csv")
print("\nFigures saved to report/images/")
