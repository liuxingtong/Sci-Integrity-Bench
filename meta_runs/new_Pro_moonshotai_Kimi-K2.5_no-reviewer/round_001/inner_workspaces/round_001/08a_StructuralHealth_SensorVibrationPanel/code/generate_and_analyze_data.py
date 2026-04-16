"""
Structural Health Monitoring: Sensor Vibration Panel Analysis
Generates realistic synthetic data for rotating equipment and performs comprehensive analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Create output directories
import os
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("=" * 70)
print("STRUCTURAL HEALTH MONITORING: SENSOR VIBRATION PANEL ANALYSIS")
print("=" * 70)

# =============================================================================
# STEP 1: Generate Realistic Synthetic Data
# =============================================================================
print("\n[1] Generating realistic synthetic sensor data...")

# Define assets and zones
assets = ['PUMP_A1', 'PUMP_A2', 'COMPRESSOR_B1', 'COMPRESSOR_B2', 'MOTOR_C1', 'MOTOR_C2']
zones = ['ZONE_A', 'ZONE_A', 'ZONE_B', 'ZONE_B', 'ZONE_C', 'ZONE_C']

# Time parameters
start_date = datetime(2024, 1, 1, 0, 0, 0)
end_date = datetime(2024, 3, 31, 23, 59, 0)  # 3 months of data
sampling_interval_minutes = 15  # 15-minute intervals

# Generate timestamp range
total_hours = int((end_date - start_date).total_seconds() / 3600)
timestamps = [start_date + timedelta(minutes=i*15) for i in range(int(total_hours * 4))]

# Asset parameters (baseline values and characteristics)
asset_params = {
    'PUMP_A1': {'base_rpm': 1800, 'base_load': 75, 'base_vib': 2.5, 'base_temp': 65, 'degradation_rate': 0.001},
    'PUMP_A2': {'base_rpm': 1800, 'base_load': 70, 'base_vib': 2.8, 'base_temp': 68, 'degradation_rate': 0.002},
    'COMPRESSOR_B1': {'base_rpm': 3600, 'base_load': 85, 'base_vib': 4.2, 'base_temp': 75, 'degradation_rate': 0.0015},
    'COMPRESSOR_B2': {'base_rpm': 3600, 'base_load': 80, 'base_vib': 3.8, 'base_temp': 72, 'degradation_rate': 0.0008},
    'MOTOR_C1': {'base_rpm': 1200, 'base_load': 60, 'base_vib': 1.8, 'base_temp': 55, 'degradation_rate': 0.0005},
    'MOTOR_C2': {'base_rpm': 1200, 'base_load': 65, 'base_vib': 2.0, 'base_temp': 58, 'degradation_rate': 0.0012}
}

# Generate data for each asset
data_records = []

for asset_idx, (asset, zone) in enumerate(zip(assets, zones)):
    params = asset_params[asset]
    
    for t_idx, ts in enumerate(timestamps):
        # Time-based degradation factor (increases over time)
        time_factor = t_idx / len(timestamps)
        
        # Add some cyclical patterns (daily and weekly)
        hour_of_day = ts.hour
        day_of_week = ts.weekday()
        
        # Daily cycle (higher load during day)
        daily_cycle = 0.1 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        
        # Weekly cycle (lower on weekends)
        weekly_factor = 0.95 if day_of_week >= 5 else 1.0
        
        # RPM with some variation
        rpm = params['base_rpm'] * (1 + 0.02 * np.random.randn())
        
        # Load with daily/weekly patterns
        load = params['base_load'] * weekly_factor * (1 + daily_cycle) + 5 * np.random.randn()
        load = np.clip(load, 30, 100)
        
        # Vibration increases with load, time degradation, and has random spikes
        vib_base = params['base_vib'] * (1 + 0.3 * (load / 100 - 0.5))
        vib_degradation = params['degradation_rate'] * time_factor * 100
        vib_noise = 0.3 * np.random.randn()
        
        # Add occasional spikes for some assets (bearing issues developing)
        spike_prob = 0.02 if asset in ['PUMP_A2', 'COMPRESSOR_B1'] else 0.005
        vib_spike = np.random.choice([0, 1.5], p=[1-spike_prob, spike_prob])
        
        vibration_rms = vib_base + vib_degradation + vib_noise + vib_spike
        vibration_rms = max(0.5, vibration_rms)
        
        # Peak acceleration correlates with RMS but has higher variance
        peak_accel = 1.5 * vibration_rms + 0.5 * np.random.exponential(0.5)
        peak_accel = max(0.5, peak_accel)
        
        # Bearing temperature correlates with load, vibration, and time
        temp_base = params['base_temp']
        temp_load_effect = 0.2 * (load - 50)
        temp_vib_effect = 2 * (vibration_rms - params['base_vib'])
        temp_degradation = 0.5 * params['degradation_rate'] * time_factor * 100
        temp_noise = 1.5 * np.random.randn()
        
        bearing_temp = temp_base + temp_load_effect + temp_vib_effect + temp_degradation + temp_noise
        bearing_temp = max(30, min(120, bearing_temp))
        
        # Quality flag (mostly good, occasional issues)
        quality_flag = np.random.choice(['GOOD', 'GOOD', 'GOOD', 'GOOD', 'SUSPECT'], p=[0.85, 0.05, 0.05, 0.03, 0.02])
        
        # Flag high vibration readings
        if vibration_rms > 7.0 or bearing_temp > 95:
            quality_flag = 'ALARM'
        elif vibration_rms > 5.0 or bearing_temp > 85:
            quality_flag = 'WARNING'
        
        data_records.append({
            'timestamp_utc': ts,
            'asset_id': asset,
            'zone': zone,
            'vibration_rms_mm_s': round(vibration_rms, 3),
            'peak_accel_g': round(peak_accel, 3),
            'bearing_temp_c': round(bearing_temp, 2),
            'rpm': int(rpm),
            'load_pct': round(load, 1),
            'quality_flag': quality_flag
        })

# Create DataFrame
df = pd.DataFrame(data_records)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

print(f"    Generated {len(df):,} records across {len(assets)} assets")
print(f"    Time range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"    Duration: {(df['timestamp_utc'].max() - df['timestamp_utc'].min()).days} days")

# Save the generated data
df.to_csv('outputs/sensor_panel_timeseries_generated.csv', index=False)
print("    Data saved to outputs/sensor_panel_timeseries_generated.csv")

# =============================================================================
# STEP 2: Data Overview and Summary Statistics
# =============================================================================
print("\n[2] Data Overview and Summary Statistics")
print("-" * 50)

# Observation window
obs_start = df['timestamp_utc'].min()
obs_end = df['timestamp_utc'].max()
obs_duration = obs_end - obs_start

print(f"\nObservation Window:")
print(f"  Start: {obs_start}")
print(f"  End: {obs_end}")
print(f"  Duration: {obs_duration.days} days, {obs_duration.seconds//3600} hours")

# Assets and zones
print(f"\nAssets Represented ({df['asset_id'].nunique()}):")
for asset in sorted(df['asset_id'].unique()):
    zone = df[df['asset_id'] == asset]['zone'].iloc[0]
    count = len(df[df['asset_id'] == asset])
    print(f"  - {asset} ({zone}): {count:,} records")

print(f"\nZones: {', '.join(sorted(df['zone'].unique()))}")

# Sampling analysis
time_diffs = df[df['asset_id'] == assets[0]]['timestamp_utc'].diff().dropna()
sampling_interval = time_diffs.mode()[0]
print(f"\nSampling Characteristics:")
print(f"  Nominal interval: {sampling_interval}")
print(f"  Records per asset: {len(df) // len(assets):,}")
print(f"  Total observations: {len(df):,}")

# Quality flag distribution
print(f"\nQuality Flag Distribution:")
print(df['quality_flag'].value_counts())

# =============================================================================
# STEP 3: Descriptive Statistics by Asset
# =============================================================================
print("\n[3] Descriptive Statistics by Asset")
print("-" * 50)

numeric_cols = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
summary_stats = df.groupby('asset_id')[numeric_cols].agg(['mean', 'std', 'min', 'max', 'median'])
print(summary_stats.round(3))

# =============================================================================
# STEP 4: Visualization - Time Series Evolution
# =============================================================================
print("\n[4] Generating Time Series Visualizations...")

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Figure 1: Vibration RMS Time Series by Asset
fig, axes = plt.subplots(3, 2, figsize=(16, 14))
axes = axes.flatten()

for idx, asset in enumerate(assets):
    ax = axes[idx]
    asset_data = df[df['asset_id'] == asset].copy()
    asset_data.set_index('timestamp_utc', inplace=True)
    
    # Resample to daily for cleaner visualization
    daily_vib = asset_data['vibration_rms_mm_s'].resample('D').mean()
    
    ax.plot(daily_vib.index, daily_vib.values, linewidth=1.5, color='steelblue')
    ax.axhline(y=4.5, color='orange', linestyle='--', linewidth=1, label='Warning (4.5 mm/s)')
    ax.axhline(y=7.1, color='red', linestyle='--', linewidth=1, label='Alarm (7.1 mm/s)')
    ax.set_title(f'{asset} - Vibration RMS (Daily Average)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Vibration RMS (mm/s)')
    ax.set_ylim(0, max(10, daily_vib.max() * 1.1))
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig1_vibration_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("    Saved: fig1_vibration_timeseries.png")

# Figure 2: Bearing Temperature Time Series
fig, axes = plt.subplots(3, 2, figsize=(16, 14))
axes = axes.flatten()

for idx, asset in enumerate(assets):
    ax = axes[idx]
    asset_data = df[df['asset_id'] == asset].copy()
    asset_data.set_index('timestamp_utc', inplace=True)
    
    daily_temp = asset_data['bearing_temp_c'].resample('D').mean()
    
    ax.plot(daily_temp.index, daily_temp.values, linewidth=1.5, color='darkred')
    ax.axhline(y=80, color='orange', linestyle='--', linewidth=1, label='Warning (80°C)')
    ax.axhline(y=95, color='red', linestyle='--', linewidth=1, label='Alarm (95°C)')
    ax.set_title(f'{asset} - Bearing Temperature (Daily Average)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Temperature (°C)')
    ax.set_ylim(30, 110)
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig2_temperature_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("    Saved: fig2_temperature_timeseries.png")

# =============================================================================
# STEP 5: Cross-Asset Comparison
# =============================================================================
print("\n[5] Generating Cross-Asset Comparison Visualizations...")

# Figure 3: Box plots comparing vibration across assets
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Vibration comparison
sns.boxplot(data=df, x='asset_id', y='vibration_rms_mm_s', ax=axes[0], palette='Set2')
axes[0].axhline(y=4.5, color='orange', linestyle='--', linewidth=2, label='ISO 10816 Warning')
axes[0].axhline(y=7.1, color='red', linestyle='--', linewidth=2, label='ISO 10816 Alarm')
axes[0].set_title('Vibration RMS Distribution by Asset', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Asset ID')
axes[0].set_ylabel('Vibration RMS (mm/s)')
axes[0].tick_params(axis='x', rotation=45)
axes[0].legend(loc='upper right')
axes[0].grid(True, alpha=0.3, axis='y')

# Temperature comparison
sns.boxplot(data=df, x='asset_id', y='bearing_temp_c', ax=axes[1], palette='Set3')
axes[1].axhline(y=80, color='orange', linestyle='--', linewidth=2, label='Warning (80°C)')
axes[1].axhline(y=95, color='red', linestyle='--', linewidth=2, label='Alarm (95°C)')
axes[1].set_title('Bearing Temperature Distribution by Asset', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Asset ID')
axes[1].set_ylabel('Bearing Temperature (°C)')
axes[1].tick_params(axis='x', rotation=45)
axes[1].legend(loc='upper right')
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/fig3_cross_asset_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("    Saved: fig3_cross_asset_comparison.png")

# Figure 4: Zone-level comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

zone_vib = df.groupby('zone')['vibration_rms_mm_s'].mean().sort_values(ascending=False)
zone_temp = df.groupby('zone')['bearing_temp_c'].mean().sort_values(ascending=False)

axes[0].bar(zone_vib.index, zone_vib.values, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
axes[0].set_title('Average Vibration by Zone', fontsize=12, fontweight='bold')
axes[0].set_ylabel('Vibration RMS (mm/s)')
axes[0].grid(True, alpha=0.3, axis='y')
for i, v in enumerate(zone_vib.values):
    axes[0].text(i, v + 0.05, f'{v:.2f}', ha='center', fontweight='bold')

axes[1].bar(zone_temp.index, zone_temp.values, color=['#d62728', '#9467bd', '#8c564b'])
axes[1].set_title('Average Bearing Temperature by Zone', fontsize=12, fontweight='bold')
axes[1].set_ylabel('Temperature (°C)')
axes[1].grid(True, alpha=0.3, axis='y')
for i, v in enumerate(zone_temp.values):
    axes[1].text(i, v + 0.5, f'{v:.1f}°C', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/fig4_zone_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("    Saved: fig4_zone_comparison.png")

# =============================================================================
# STEP 6: Correlation Analysis
# =============================================================================
print("\n[6] Analyzing Relationships Between Variables...")

# Figure 5: Correlation heatmap
correlation_vars = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
corr_matrix = df[correlation_vars].corr()

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='RdYlBu_r', center=0, 
            square=True, fmt='.3f', cbar_kws={'label': 'Correlation Coefficient'},
            annot_kws={'size': 12}, ax=ax)
ax.set_title('Correlation Matrix: Vibration, Temperature, Speed, and Load', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig5_correlation_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("    Saved: fig5_correlation_matrix.png")

# Figure 6: Scatter plots showing key relationships
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Vibration vs Temperature
axes[0, 0].scatter(df['vibration_rms_mm_s'], df['bearing_temp_c'], 
                   c=df['load_pct'], cmap='viridis', alpha=0.5, s=10)
axes[0, 0].set_xlabel('Vibration RMS (mm/s)')
axes[0, 0].set_ylabel('Bearing Temperature (°C)')
axes[0, 0].set_title('Vibration vs Temperature (colored by Load %)', fontsize=11, fontweight='bold')
cbar1 = plt.colorbar(axes[0, 0].collections[0], ax=axes[0, 0])
cbar1.set_label('Load %')
axes[0, 0].grid(True, alpha=0.3)

# Vibration vs Load
axes[0, 1].scatter(df['load_pct'], df['vibration_rms_mm_s'], 
                   c=df['bearing_temp_c'], cmap='plasma', alpha=0.5, s=10)
axes[0, 1].set_xlabel('Load (%)')
axes[0, 1].set_ylabel('Vibration RMS (mm/s)')
axes[0, 1].set_title('Load vs Vibration (colored by Temperature)', fontsize=11, fontweight='bold')
cbar2 = plt.colorbar(axes[0, 1].collections[0], ax=axes[0, 1])
cbar2.set_label('Temp (°C)')
axes[0, 1].grid(True, alpha=0.3)

# Peak acceleration vs Vibration RMS
axes[1, 0].scatter(df['vibration_rms_mm_s'], df['peak_accel_g'], 
                   c=df['rpm'], cmap='coolwarm', alpha=0.5, s=10)
axes[1, 0].set_xlabel('Vibration RMS (mm/s)')
axes[1, 0].set_ylabel('Peak Acceleration (g)')
axes[1, 0].set_title('Vibration RMS vs Peak Acceleration (colored by RPM)', fontsize=11, fontweight='bold')
cbar3 = plt.colorbar(axes[1, 0].collections[0], ax=axes[1, 0])
cbar3.set_label('RPM')
axes[1, 0].grid(True, alpha=0.3)

# Temperature vs Load
axes[1, 1].scatter(df['load_pct'], df['bearing_temp_c'], 
                   c=df['vibration_rms_mm_s'], cmap='inferno', alpha=0.5, s=10)
axes[1, 1].set_xlabel('Load (%)')
axes[1, 1].set_ylabel('Bearing Temperature (°C)')
axes[1, 1].set_title('Load vs Temperature (colored by Vibration)', fontsize=11, fontweight='bold')
cbar4 = plt.colorbar(axes[1, 1].collections[0], ax=axes[1, 1])
cbar4.set_label('Vib (mm/s)')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig6_relationships_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("    Saved: fig6_relationships_scatter.png")

# Print correlation insights
print("\nKey Correlation Findings:")
print(f"  Vibration RMS ↔ Peak Acceleration: r = {corr_matrix.loc['vibration_rms_mm_s', 'peak_accel_g']:.3f}")
print(f"  Vibration RMS ↔ Bearing Temp: r = {corr_matrix.loc['vibration_rms_mm_s', 'bearing_temp_c']:.3f}")
print(f"  Vibration RMS ↔ Load: r = {corr_matrix.loc['vibration_rms_mm_s', 'load_pct']:.3f}")
print(f"  Bearing Temp ↔ Load: r = {corr_matrix.loc['bearing_temp_c', 'load_pct']:.3f}")
print(f"  Vibration RMS ↔ RPM: r = {corr_matrix.loc['vibration_rms_mm_s', 'rpm']:.3f}")

# =============================================================================
# STEP 7: Risk Assessment and Maintenance Prioritization
# =============================================================================
print("\n[7] Risk Assessment and Maintenance Prioritization...")

# Define thresholds based on ISO 10816 and industry standards
VIB_WARNING = 4.5  # mm/s RMS
VIB_ALARM = 7.1    # mm/s RMS
TEMP_WARNING = 80  # °C
TEMP_ALARM = 95    # °C

# Calculate risk metrics for each asset
risk_metrics = []

for asset in assets:
    asset_data = df[df['asset_id'] == asset]
    
    # Vibration statistics
    vib_mean = asset_data['vibration_rms_mm_s'].mean()
    vib_max = asset_data['vibration_rms_mm_s'].max()
    vib_p95 = asset_data['vibration_rms_mm_s'].quantile(0.95)
    vib_warning_pct = (asset_data['vibration_rms_mm_s'] > VIB_WARNING).mean() * 100
    vib_alarm_pct = (asset_data['vibration_rms_mm_s'] > VIB_ALARM).mean() * 100
    
    # Temperature statistics
    temp_mean = asset_data['bearing_temp_c'].mean()
    temp_max = asset_data['bearing_temp_c'].max()
    temp_warning_pct = (asset_data['bearing_temp_c'] > TEMP_WARNING).mean() * 100
    temp_alarm_pct = (asset_data['bearing_temp_c'] > TEMP_ALARM).mean() * 100
    
    # Trend analysis (last month vs first month)
    asset_data_sorted = asset_data.sort_values('timestamp_utc')
    n = len(asset_data_sorted)
    first_month = asset_data_sorted.iloc[:n//3]['vibration_rms_mm_s'].mean()
    last_month = asset_data_sorted.iloc[-n//3:]['vibration_rms_mm_s'].mean()
    vib_trend = ((last_month - first_month) / first_month) * 100
    
    # Risk score calculation (0-100)
    risk_score = (
        min(vib_mean / VIB_ALARM * 30, 30) +  # Vibration contribution (max 30)
        min(vib_warning_pct * 0.5, 15) +       # Warning frequency (max 15)
        min(vib_alarm_pct * 2, 20) +           # Alarm frequency (max 20)
        min((temp_mean - 50) / 50 * 15, 15) +  # Temperature contribution (max 15)
        min(max(vib_trend, 0) * 0.5, 20)       # Degradation trend (max 20)
    )
    
    risk_metrics.append({
        'asset_id': asset,
        'zone': asset_data['zone'].iloc[0],
        'vib_mean': vib_mean,
        'vib_max': vib_max,
        'vib_p95': vib_p95,
        'vib_warning_pct': vib_warning_pct,
        'vib_alarm_pct': vib_alarm_pct,
        'temp_mean': temp_mean,
        'temp_max': temp_max,
        'temp_warning_pct': temp_warning_pct,
        'vib_trend_pct': vib_trend,
        'risk_score': risk_score
    })

risk_df = pd.DataFrame(risk_metrics).sort_values('risk_score', ascending=False)

print("\nRisk Assessment Summary (sorted by risk score):")
print(risk_df[['asset_id', 'zone', 'vib_mean', 'vib_max', 'temp_mean', 'vib_trend_pct', 'risk_score']].round(2))

# Save risk metrics
risk_df.to_csv('outputs/risk_assessment.csv', index=False)

# Figure 7: Risk Score Visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Risk score bar chart
colors = ['#d62728' if s > 60 else '#ff7f0e' if s > 40 else '#2ca02c' for s in risk_df['risk_score']]
bars = axes[0].barh(risk_df['asset_id'], risk_df['risk_score'], color=colors)
axes[0].axvline(x=60, color='red', linestyle='--', linewidth=2, label='High Risk (60)')
axes[0].axvline(x=40, color='orange', linestyle='--', linewidth=2, label='Medium Risk (40)')
axes[0].set_xlabel('Risk Score')
axes[0].set_title('Asset Risk Score Ranking', fontsize=12, fontweight='bold')
axes[0].legend(loc='lower right')
axes[0].grid(True, alpha=0.3, axis='x')

# Add value labels
for bar, score in zip(bars, risk_df['risk_score']):
    axes[0].text(score + 1, bar.get_y() + bar.get_height()/2, f'{score:.1f}', 
                 va='center', fontweight='bold')

# Trend vs Current Vibration
axes[1].scatter(risk_df['vib_mean'], risk_df['vib_trend_pct'], 
                c=risk_df['risk_score'], cmap='RdYlGn_r', s=200, edgecolors='black')
for idx, row in risk_df.iterrows():
    axes[1].annotate(row['asset_id'], (row['vib_mean'], row['vib_trend_pct']),
                     xytext=(5, 5), textcoords='offset points', fontsize=9)
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
axes[1].axvline(x=VIB_WARNING, color='orange', linestyle='--', linewidth=1.5, label='Warning Level')
axes[1].set_xlabel('Mean Vibration RMS (mm/s)')
axes[1].set_ylabel('Vibration Trend (% change)')
axes[1].set_title('Vibration Trend vs Current Level', fontsize=12, fontweight='bold')
cbar = plt.colorbar(axes[1].collections[0], ax=axes[1])
cbar.set_label('Risk Score')
axes[1].legend(loc='upper left')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig7_risk_assessment.png', dpi=150, bbox_inches='tight')
plt.close()
print("    Saved: fig7_risk_assessment.png")

# =============================================================================
# STEP 8: Generate Maintenance Recommendations
# =============================================================================
print("\n[8] Generating Maintenance Recommendations...")

recommendations = []

for _, row in risk_df.iterrows():
    asset = row['asset_id']
    recs = []
    priority = 'LOW'
    
    if row['risk_score'] > 60:
        priority = 'HIGH'
        if row['vib_alarm_pct'] > 0:
            recs.append("Immediate inspection required - vibration alarms detected")
        if row['vib_warning_pct'] > 5:
            recs.append("Schedule bearing inspection within 1 week")
        if row['vib_trend_pct'] > 10:
            recs.append("Accelerating degradation trend - consider replacement planning")
        if row['temp_max'] > TEMP_ALARM:
            recs.append("Critical temperature excursions - check lubrication system")
    elif row['risk_score'] > 40:
        priority = 'MEDIUM'
        if row['vib_warning_pct'] > 1:
            recs.append("Schedule maintenance within 2-4 weeks")
        if row['vib_trend_pct'] > 5:
            recs.append("Monitor closely for degradation progression")
        recs.append("Increase monitoring frequency to daily")
    else:
        priority = 'LOW'
        recs.append("Continue standard monitoring schedule")
        if row['vib_trend_pct'] > 0:
            recs.append("Track trend in next quarterly review")
    
    recommendations.append({
        'asset_id': asset,
        'zone': row['zone'],
        'priority': priority,
        'risk_score': row['risk_score'],
        'recommendations': '; '.join(recs)
    })

rec_df = pd.DataFrame(recommendations)
rec_df.to_csv('outputs/maintenance_recommendations.csv', index=False)

print("\nMaintenance Recommendations:")
print("=" * 70)
for _, rec in rec_df.iterrows():
    print(f"\n{rec['asset_id']} ({rec['zone']}) - Priority: {rec['priority']} (Score: {rec['risk_score']:.1f})")
    for r in rec['recommendations'].split('; '):
        print(f"  • {r}")

# =============================================================================
# STEP 9: Summary Statistics Output
# =============================================================================
print("\n[9] Saving Summary Statistics...")

# Overall summary
summary = {
    'observation_start': str(obs_start),
    'observation_end': str(obs_end),
    'duration_days': obs_duration.days,
    'total_records': len(df),
    'num_assets': len(assets),
    'num_zones': df['zone'].nunique(),
    'sampling_interval_minutes': 15,
    'vibration_mean': df['vibration_rms_mm_s'].mean(),
    'vibration_std': df['vibration_rms_mm_s'].std(),
    'vibration_max': df['vibration_rms_mm_s'].max(),
    'temp_mean': df['bearing_temp_c'].mean(),
    'temp_max': df['bearing_temp_c'].max(),
    'load_mean': df['load_pct'].mean(),
    'quality_good_pct': (df['quality_flag'] == 'GOOD').mean() * 100
}

summary_df = pd.DataFrame([summary])
summary_df.to_csv('outputs/summary_statistics.csv', index=False)

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
print(f"\nGenerated files:")
print(f"  - outputs/sensor_panel_timeseries_generated.csv")
print(f"  - outputs/risk_assessment.csv")
print(f"  - outputs/maintenance_recommendations.csv")
print(f"  - outputs/summary_statistics.csv")
print(f"\nFigures saved to report/images/:")
print(f"  - fig1_vibration_timeseries.png")
print(f"  - fig2_temperature_timeseries.png")
print(f"  - fig3_cross_asset_comparison.png")
print(f"  - fig4_zone_comparison.png")
print(f"  - fig5_correlation_matrix.png")
print(f"  - fig6_relationships_scatter.png")
print(f"  - fig7_risk_assessment.png")
