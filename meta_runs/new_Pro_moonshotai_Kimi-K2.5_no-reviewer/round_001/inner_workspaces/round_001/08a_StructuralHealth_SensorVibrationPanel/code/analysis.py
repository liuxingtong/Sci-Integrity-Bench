"""
Structural Health Monitoring Analysis
Rotating Equipment Vibration and Thermal Telemetry Analysis
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10

# Load data
print("Loading sensor data...")
df = pd.read_csv('data/sensor_panel_timeseries.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df['date'] = df['timestamp_utc'].dt.date

print(f"Dataset: {len(df):,} records")
print(f"Date range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Assets: {df['asset_id'].nunique()}")
print(f"Zones: {df['zone'].nunique()}")
print(f"Sampling interval: 15 minutes")

# ============================================================================
# 1. DATA OVERVIEW AND VALIDATION
# ============================================================================
print("\n" + "="*60)
print("1. DATA OVERVIEW AND VALIDATION")
print("="*60)

# Observation window
observation_days = (df['timestamp_utc'].max() - df['timestamp_utc'].min()).days + 1
print(f"\nObservation window: {observation_days} days (Q1 2024)")

# Assets and zones
asset_summary = df.groupby(['asset_id', 'zone']).size().reset_index(name='record_count')
print(f"\nAssets by Zone:")
print(asset_summary)

# Quality flag distribution
quality_dist = df['quality_flag'].value_counts()
print(f"\nQuality Flag Distribution:")
print(quality_dist)
print(f"Data quality: {(quality_dist.get('OK', 0) / len(df) * 100):.1f}% OK")

# Sampling cadence verification
time_diffs = df.groupby('asset_id')['timestamp_utc'].diff().dt.total_seconds() / 60
print(f"\nSampling cadence: {time_diffs.mode().iloc[0]:.0f} minutes (nominal: 15 min)")

# Save data overview
overview = {
    'total_records': len(df),
    'observation_days': observation_days,
    'n_assets': df['asset_id'].nunique(),
    'n_zones': df['zone'].nunique(),
    'sampling_interval_min': 15,
    'date_start': str(df['timestamp_utc'].min()),
    'date_end': str(df['timestamp_utc'].max()),
    'quality_ok_pct': quality_dist.get('OK', 0) / len(df) * 100
}

# ============================================================================
# 2. VIBRATION SEVERITY ANALYSIS
# ============================================================================
print("\n" + "="*60)
print("2. VIBRATION SEVERITY ANALYSIS")
print("="*60)

# ISO 10816 vibration severity guidelines (mm/s RMS)
# For large machines ( > 15kW) on rigid foundations:
# Zone A (Good): < 2.8 mm/s
# Zone B (Acceptable): 2.8 - 7.1 mm/s
# Zone C (Alert): 7.1 - 18 mm/s
# Zone D (Danger): > 18 mm/s

iso_zones = {
    'Zone A (Good)': (0, 2.8),
    'Zone B (Acceptable)': (2.8, 7.1),
    'Zone C (Alert)': (7.1, 18.0),
    'Zone D (Danger)': (18.0, float('inf'))
}

def classify_iso_zone(vibration_rms):
    for zone, (low, high) in iso_zones.items():
        if low <= vibration_rms < high:
            return zone
    return 'Zone D (Danger)'

df['iso_zone'] = df['vibration_rms_mm_s'].apply(classify_iso_zone)

# Vibration statistics by asset
vib_stats = df.groupby('asset_id').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'min', 'max', 'median'],
    'peak_accel_g': ['mean', 'max'],
    'bearing_temp_c': ['mean', 'max']
}).round(3)

vib_stats.columns = ['_'.join(col).strip() for col in vib_stats.columns]
print("\nVibration Statistics by Asset:")
print(vib_stats)

# ISO zone distribution by asset
iso_dist = pd.crosstab(df['asset_id'], df['iso_zone'], normalize='index') * 100
print("\nISO 10816 Zone Distribution (% of time):")
print(iso_dist.round(1))

# Assets exceeding thresholds
alert_assets = vib_stats[vib_stats['vibration_rms_mm_s_mean'] > 7.1].index.tolist()
critical_assets = vib_stats[vib_stats['vibration_rms_mm_s_mean'] > 18.0].index.tolist()
print(f"\nAssets in Alert Zone (mean > 7.1 mm/s): {alert_assets}")
print(f"Assets in Danger Zone (mean > 18 mm/s): {critical_assets}")

# ============================================================================
# 3. TEMPORAL ANALYSIS
# ============================================================================
print("\n" + "="*60)
print("3. TEMPORAL ANALYSIS")
print("="*60)

# Daily aggregation for trend analysis
daily_stats = df.groupby(['asset_id', 'date']).agg({
    'vibration_rms_mm_s': 'mean',
    'peak_accel_g': 'mean',
    'bearing_temp_c': 'mean',
    'rpm': 'mean',
    'load_pct': 'mean'
}).reset_index()
daily_stats['date'] = pd.to_datetime(daily_stats['date'])

# Trend analysis - check for increasing vibration over time
from scipy import stats

trend_results = {}
for asset in df['asset_id'].unique():
    asset_data = daily_stats[daily_stats['asset_id'] == asset].sort_values('date')
    if len(asset_data) > 10:
        x = np.arange(len(asset_data))
        y = asset_data['vibration_rms_mm_s'].values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        trend_results[asset] = {
            'slope': slope,
            'r_squared': r_value**2,
            'p_value': p_value,
            'trend_direction': 'Increasing' if slope > 0.01 else ('Decreasing' if slope < -0.01 else 'Stable')
        }

trend_df = pd.DataFrame(trend_results).T
print("\nVibration Trend Analysis (Daily means):")
print(trend_df.round(4))

# ============================================================================
# 4. CO-MOVEMENT ANALYSIS
# ============================================================================
print("\n" + "="*60)
print("4. CO-MOVEMENT ANALYSIS")
print("="*60)

# Correlation analysis
correlation_vars = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
corr_matrix = df[correlation_vars].corr()
print("\nCorrelation Matrix (All Assets):")
print(corr_matrix.round(3))

# Correlation by asset
print("\nVibration-Temperature Correlation by Asset:")
for asset in df['asset_id'].unique():
    asset_data = df[df['asset_id'] == asset]
    corr = asset_data['vibration_rms_mm_s'].corr(asset_data['bearing_temp_c'])
    print(f"  {asset}: {corr:.3f}")

# Correlation by zone
print("\nVibration-Temperature Correlation by Zone:")
for zone in df['zone'].unique():
    zone_data = df[df['zone'] == zone]
    corr = zone_data['vibration_rms_mm_s'].corr(zone_data['bearing_temp_c'])
    print(f"  {zone}: {corr:.3f}")

# ============================================================================
# 5. ZONE AND ASSET COMPARISON
# ============================================================================
print("\n" + "="*60)
print("5. ZONE AND ASSET COMPARISON")
print("="*60)

zone_stats = df.groupby('zone').agg({
    'vibration_rms_mm_s': ['mean', 'std', 'max'],
    'bearing_temp_c': ['mean', 'max'],
    'asset_id': 'nunique'
}).round(3)
zone_stats.columns = ['_'.join(col).strip() for col in zone_stats.columns]
print("\nZone-level Statistics:")
print(zone_stats)

# ============================================================================
# 6. RISK RANKING
# ============================================================================
print("\n" + "="*60)
print("6. RISK RANKING")
print("="*60)

# Calculate risk score for each asset
risk_scores = []
for asset in df['asset_id'].unique():
    asset_data = df[df['asset_id'] == asset]
    
    # Vibration severity (40% weight)
    vib_mean = asset_data['vibration_rms_mm_s'].mean()
    vib_max = asset_data['vibration_rms_mm_s'].max()
    vib_score = min(100, (vib_mean / 18.0) * 100)  # Normalize to 18 mm/s (Zone D threshold)
    
    # Temperature severity (20% weight)
    temp_mean = asset_data['bearing_temp_c'].mean()
    temp_score = min(100, max(0, (temp_mean - 40) / 50 * 100))  # Normalize 40-90°C range
    
    # Trend severity (25% weight)
    if asset in trend_results:
        trend = trend_results[asset]
        trend_score = min(100, abs(trend['slope']) * 50) if trend['trend_direction'] == 'Increasing' else 0
    else:
        trend_score = 0
    
    # Alert frequency (15% weight)
    alert_pct = (asset_data['iso_zone'].isin(['Zone C (Alert)', 'Zone D (Danger)'])).mean() * 100
    
    # Composite risk score
    risk_score = (vib_score * 0.40) + (temp_score * 0.20) + (trend_score * 0.25) + (alert_pct * 0.15)
    
    risk_scores.append({
        'asset_id': asset,
        'zone': asset_data['zone'].iloc[0],
        'vibration_rms_mean': vib_mean,
        'vibration_rms_max': vib_max,
        'bearing_temp_mean': temp_mean,
        'trend_direction': trend_results.get(asset, {}).get('trend_direction', 'Unknown'),
        'trend_slope': trend_results.get(asset, {}).get('slope', 0),
        'alert_zone_pct': alert_pct,
        'risk_score': risk_score,
        'priority': 'Critical' if risk_score > 70 else ('High' if risk_score > 50 else ('Medium' if risk_score > 30 else 'Low'))
    })

risk_df = pd.DataFrame(risk_scores).sort_values('risk_score', ascending=False)
print("\nRisk Ranking (Quarterly Review):")
print(risk_df[['asset_id', 'zone', 'vibration_rms_mean', 'bearing_temp_mean', 
               'trend_direction', 'alert_zone_pct', 'risk_score', 'priority']].round(2))

# ============================================================================
# 7. GENERATE VISUALIZATIONS
# ============================================================================
print("\n" + "="*60)
print("7. GENERATING VISUALIZATIONS")
print("="*60)

# Figure 1: Vibration Time Series by Asset
fig, axes = plt.subplots(4, 2, figsize=(16, 20))
axes = axes.flatten()

for idx, asset in enumerate(sorted(df['asset_id'].unique())):
    ax = axes[idx]
    asset_data = df[df['asset_id'] == asset].sort_values('timestamp_utc')
    
    ax.plot(asset_data['timestamp_utc'], asset_data['vibration_rms_mm_s'], 
            alpha=0.7, linewidth=0.5, color='steelblue')
    
    # Add ISO zone thresholds
    ax.axhline(y=2.8, color='green', linestyle='--', alpha=0.5, label='Zone A/B')
    ax.axhline(y=7.1, color='orange', linestyle='--', alpha=0.5, label='Zone B/C')
    ax.axhline(y=18.0, color='red', linestyle='--', alpha=0.5, label='Zone C/D')
    
    ax.set_title(f'{asset} ({asset_data["zone"].iloc[0]})', fontsize=11, fontweight='bold')
    ax.set_ylabel('Vibration RMS (mm/s)')
    ax.set_ylim(0, max(asset_data['vibration_rms_mm_s'].max() * 1.1, 5))
    
    if idx >= 6:
        ax.set_xlabel('Date')
    
    # Add statistics text
    mean_vib = asset_data['vibration_rms_mm_s'].mean()
    max_vib = asset_data['vibration_rms_mm_s'].max()
    ax.text(0.02, 0.98, f'Mean: {mean_vib:.2f}\nMax: {max_vib:.2f}', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5), fontsize=8)

plt.suptitle('Vibration Time Series by Asset (Q1 2024)', fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig('report/images/fig1_vibration_timeseries.png', bbox_inches='tight', dpi=150)
plt.close()
print("  - Saved: fig1_vibration_timeseries.png")

# Figure 2: Zone Comparison Boxplot
fig, ax = plt.subplots(figsize=(12, 6))
zone_order = ['Zone_A', 'Zone_B', 'Zone_C', 'Zone_D']
sns.boxplot(data=df, x='zone', y='vibration_rms_mm_s', order=zone_order, ax=ax, palette='Set2')
ax.axhline(y=2.8, color='green', linestyle='--', alpha=0.7, label='Zone A/B Threshold (2.8 mm/s)')
ax.axhline(y=7.1, color='orange', linestyle='--', alpha=0.7, label='Zone B/C Threshold (7.1 mm/s)')
ax.axhline(y=18.0, color='red', linestyle='--', alpha=0.7, label='Zone C/D Threshold (18.0 mm/s)')
ax.set_xlabel('Zone', fontsize=12)
ax.set_ylabel('Vibration RMS (mm/s)', fontsize=12)
ax.set_title('Vibration Distribution by Zone', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
plt.tight_layout()
plt.savefig('report/images/fig2_zone_comparison.png', bbox_inches='tight', dpi=150)
plt.close()
print("  - Saved: fig2_zone_comparison.png")

# Figure 3: Vibration vs Temperature Scatter
fig, ax = plt.subplots(figsize=(12, 8))
for asset in df['asset_id'].unique():
    asset_data = df[df['asset_id'] == asset].sample(min(500, len(df[df['asset_id'] == asset])))
    ax.scatter(asset_data['bearing_temp_c'], asset_data['vibration_rms_mm_s'], 
               alpha=0.5, s=10, label=asset)

ax.set_xlabel('Bearing Temperature (°C)', fontsize=12)
ax.set_ylabel('Vibration RMS (mm/s)', fontsize=12)
ax.set_title('Vibration vs Bearing Temperature by Asset', fontsize=14, fontweight='bold')
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
plt.tight_layout()
plt.savefig('report/images/fig3_vib_temp_correlation.png', bbox_inches='tight', dpi=150)
plt.close()
print("  - Saved: fig3_vib_temp_correlation.png")

# Figure 4: Correlation Heatmap
fig, ax = plt.subplots(figsize=(10, 8))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.3f', cmap='RdBu_r', 
            center=0, vmin=-1, vmax=1, square=True, ax=ax,
            cbar_kws={'label': 'Correlation Coefficient'})
ax.set_title('Sensor Correlation Matrix', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig4_correlation_heatmap.png', bbox_inches='tight', dpi=150)
plt.close()
print("  - Saved: fig4_correlation_heatmap.png")

# Figure 5: Risk Score Bar Chart
fig, ax = plt.subplots(figsize=(12, 6))
colors = {'Critical': 'darkred', 'High': 'red', 'Medium': 'orange', 'Low': 'green'}
bar_colors = [colors[p] for p in risk_df['priority']]
bars = ax.barh(risk_df['asset_id'], risk_df['risk_score'], color=bar_colors)
ax.set_xlabel('Risk Score', fontsize=12)
ax.set_ylabel('Asset ID', fontsize=12)
ax.set_title('Asset Risk Ranking (Q1 2024)', fontsize=14, fontweight='bold')
ax.axvline(x=70, color='darkred', linestyle='--', alpha=0.7, label='Critical Threshold')
ax.axvline(x=50, color='red', linestyle='--', alpha=0.7, label='High Threshold')
ax.axvline(x=30, color='orange', linestyle='--', alpha=0.7, label='Medium Threshold')

# Add value labels
for i, (bar, score) in enumerate(zip(bars, risk_df['risk_score'])):
    ax.text(score + 1, i, f'{score:.1f}', va='center', fontsize=9)

# Create legend for priorities
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=colors[p], label=p) for p in ['Critical', 'High', 'Medium', 'Low']]
ax.legend(handles=legend_elements, loc='lower right')

plt.tight_layout()
plt.savefig('report/images/fig5_risk_ranking.png', bbox_inches='tight', dpi=150)
plt.close()
print("  - Saved: fig5_risk_ranking.png")

# Figure 6: Daily Trend Lines for Critical Assets
fig, ax = plt.subplots(figsize=(14, 6))
critical_assets_list = risk_df[risk_df['priority'].isin(['Critical', 'High'])]['asset_id'].tolist()

for asset in critical_assets_list:
    asset_daily = daily_stats[daily_stats['asset_id'] == asset].sort_values('date')
    ax.plot(asset_daily['date'], asset_daily['vibration_rms_mm_s'], 
            marker='o', markersize=3, linewidth=1.5, label=asset, alpha=0.8)

ax.axhline(y=7.1, color='orange', linestyle='--', alpha=0.7, label='Alert Threshold')
ax.axhline(y=18.0, color='red', linestyle='--', alpha=0.7, label='Danger Threshold')
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Daily Mean Vibration RMS (mm/s)', fontsize=12)
ax.set_title('Vibration Trends - Priority Assets', fontsize=14, fontweight='bold')
ax.legend(loc='upper left')
plt.tight_layout()
plt.savefig('report/images/fig6_trend_analysis.png', bbox_inches='tight', dpi=150)
plt.close()
print("  - Saved: fig6_trend_analysis.png")

# Figure 7: ISO Zone Distribution
fig, ax = plt.subplots(figsize=(10, 6))
iso_counts = df.groupby(['asset_id', 'iso_zone']).size().unstack(fill_value=0)
iso_counts_pct = iso_counts.div(iso_counts.sum(axis=1), axis=0) * 100
iso_counts_pct = iso_counts_pct.reindex(risk_df['asset_id'])  # Order by risk

iso_counts_pct.plot(kind='barh', stacked=True, ax=ax, 
                    color=['green', 'yellow', 'orange', 'red'],
                    alpha=0.8)
ax.set_xlabel('Percentage of Time (%)', fontsize=12)
ax.set_ylabel('Asset ID', fontsize=12)
ax.set_title('ISO 10816 Zone Distribution by Asset', fontsize=14, fontweight='bold')
ax.legend(title='ISO Zone', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('report/images/fig7_iso_distribution.png', bbox_inches='tight', dpi=150)
plt.close()
print("  - Saved: fig7_iso_distribution.png")

# ============================================================================
# 8. SAVE RESULTS
# ============================================================================
print("\n" + "="*60)
print("8. SAVING RESULTS")
print("="*60)

# Save key statistics
vib_stats.to_csv('outputs/vibration_statistics.csv')
risk_df.to_csv('outputs/risk_ranking.csv', index=False)
corr_matrix.to_csv('outputs/correlation_matrix.csv')
trend_df.to_csv('outputs/trend_analysis.csv')
iso_dist.to_csv('outputs/iso_zone_distribution.csv')

# Save summary for report
summary = {
    'observation_days': observation_days,
    'total_records': len(df),
    'n_assets': df['asset_id'].nunique(),
    'n_zones': df['zone'].nunique(),
    'critical_assets': critical_assets,
    'alert_assets': alert_assets,
    'highest_risk_asset': risk_df.iloc[0]['asset_id'],
    'highest_risk_score': risk_df.iloc[0]['risk_score'],
    'mean_vibration_fleet': df['vibration_rms_mm_s'].mean(),
    'max_vibration_fleet': df['vibration_rms_mm_s'].max(),
    'vib_temp_correlation': df['vibration_rms_mm_s'].corr(df['bearing_temp_c'])
}

import json
with open('outputs/analysis_summary.json', 'w') as f:
    json.dump(summary, f, indent=2, default=str)

print("\nAnalysis complete!")
print(f"  - Outputs saved to: outputs/")
print(f"  - Figures saved to: report/images/")
print(f"\nKey Findings:")
print(f"  - Critical Asset: {summary['highest_risk_asset']} (Risk Score: {summary['highest_risk_score']:.1f})")
print(f"  - Assets requiring immediate attention: {critical_assets}")
print(f"  - Fleet mean vibration: {summary['mean_vibration_fleet']:.2f} mm/s")
print(f"  - Vibration-Temperature correlation: {summary['vib_temp_correlation']:.3f}")
