"""
Energy Systems Load Forecast Analysis
Annual Load Forecast with Reliability-Oriented Commentary
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Create output directories
import os
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("="*60)
print("ENERGY SYSTEMS LOAD FORECAST ANALYSIS")
print("="*60)

# =============================================================================
# 1. DATA LOADING AND PREPROCESSING
# =============================================================================
print("\n[1] DATA LOADING AND PREPROCESSING")
print("-"*40)

# Load data
df = pd.read_csv('../data/load_15min.csv')
print(f"Raw data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

# Parse timestamps
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df = df.set_index('timestamp_utc')

# Handle missing values
df['load_mw'] = pd.to_numeric(df['load_mw'], errors='coerce')
missing_count = df['load_mw'].isna().sum()
print(f"Missing values: {missing_count} ({100*missing_count/len(df):.2f}%)")

# Interpolate missing values using linear interpolation
df['load_mw'] = df['load_mw'].interpolate(method='linear')
df['load_mw'] = df['load_mw'].fillna(method='bfill').fillna(method='ffill')

print(f"Data range: {df.index.min()} to {df.index.max()}")
print(f"Total records: {len(df)}")

# =============================================================================
# 2. EXPLORATORY DATA ANALYSIS
# =============================================================================
print("\n[2] EXPLORATORY DATA ANALYSIS")
print("-"*40)

# Basic statistics
print(f"\nLoad Statistics (MW):")
print(f"  Mean: {df['load_mw'].mean():.2f}")
print(f"  Std:  {df['load_mw'].std():.2f}")
print(f"  Min:  {df['load_mw'].min():.2f}")
print(f"  Max:  {df['load_mw'].max():.2f}")
print(f"  Range: {df['load_mw'].max() - df['load_mw'].min():.2f}")

# Add time features
df['hour'] = df.index.hour
df['day_of_week'] = df.index.dayofweek
df['day_name'] = df.index.day_name()
df['date'] = df.index.date
df['is_weekend'] = df['day_of_week'].isin([5, 6])

# Calculate peak and off-peak statistics
peak_hours = df[df['hour'].isin([9, 10, 11, 12, 13, 14, 15, 16, 17, 18])]
off_peak_hours = df[~df['hour'].isin([9, 10, 11, 12, 13, 14, 15, 16, 17, 18])]

print(f"\nPeak Hours (09:00-18:00):")
print(f"  Mean Load: {peak_hours['load_mw'].mean():.2f} MW")
print(f"  Max Load:  {peak_hours['load_mw'].max():.2f} MW")

print(f"\nOff-Peak Hours:")
print(f"  Mean Load: {off_peak_hours['load_mw'].mean():.2f} MW")
print(f"  Min Load:  {off_peak_hours['load_mw'].min():.2f} MW")

# =============================================================================
# 3. VISUALIZATION - TIME SERIES OVERVIEW
# =============================================================================
print("\n[3] GENERATING VISUALIZATIONS")
print("-"*40)

# Figure 1: Full Time Series
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df.index, df['load_mw'], color='steelblue', linewidth=0.8, alpha=0.8)
ax.set_xlabel('Time')
ax.set_ylabel('Load (MW)')
ax.set_title('15-Minute Load Time Series (January 2026)')
ax.axhline(y=df['load_mw'].mean(), color='red', linestyle='--', label=f'Mean: {df["load_mw"].mean():.1f} MW', alpha=0.7)
ax.legend(loc='upper right')
plt.tight_layout()
plt.savefig('../report/images/fig1_time_series.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig1_time_series.png")

# Figure 2: Daily Load Profile (Hourly Average)
hourly_avg = df.groupby('hour')['load_mw'].agg(['mean', 'std', 'min', 'max'])

fig, ax = plt.subplots(figsize=(12, 6))
ax.fill_between(hourly_avg.index, hourly_avg['min'], hourly_avg['max'], 
                 alpha=0.3, color='steelblue', label='Min-Max Range')
ax.fill_between(hourly_avg.index, 
                 hourly_avg['mean'] - hourly_avg['std'], 
                 hourly_avg['mean'] + hourly_avg['std'],
                 alpha=0.5, color='steelblue', label='±1 Std Dev')
ax.plot(hourly_avg.index, hourly_avg['mean'], color='darkblue', linewidth=2.5, label='Mean Load')
ax.set_xlabel('Hour of Day')
ax.set_ylabel('Load (MW)')
ax.set_title('Daily Load Profile with Variability Bands')
ax.set_xticks(range(24))
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/fig2_daily_profile.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig2_daily_profile.png")

# Figure 3: Day-of-Week Comparison
daily_avg = df.groupby('day_of_week')['load_mw'].agg(['mean', 'std'])
day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(daily_avg.index, daily_avg['mean'], color='steelblue', 
              yerr=daily_avg['std'], capsize=5, alpha=0.8)
ax.set_xlabel('Day of Week')
ax.set_ylabel('Average Load (MW)')
ax.set_title('Average Load by Day of Week')
ax.set_xticks(range(7))
ax.set_xticklabels(day_names)
ax.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/fig3_day_of_week.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig3_day_of_week.png")

# Figure 4: Heatmap - Hour vs Day of Week
pivot_data = df.pivot_table(values='load_mw', index='hour', columns='day_of_week', aggfunc='mean')
pivot_data.columns = day_names

fig, ax = plt.subplots(figsize=(12, 8))
sns.heatmap(pivot_data, cmap='YlOrRd', annot=True, fmt='.1f', 
            ax=ax, cbar_kws={'label': 'Load (MW)'})
ax.set_xlabel('Day of Week')
ax.set_ylabel('Hour of Day')
ax.set_title('Load Heatmap: Hour vs Day of Week')
plt.tight_layout()
plt.savefig('../report/images/fig4_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig4_heatmap.png")

# =============================================================================
# 4. LOAD DURATION CURVE (Reliability Analysis)
# =============================================================================
print("\n[4] RELIABILITY ANALYSIS")
print("-"*40)

# Load Duration Curve
sorted_load = df['load_mw'].sort_values(ascending=False).reset_index(drop=True)
sorted_load_pct = sorted_load / sorted_load.max() * 100
cumulative_pct = np.arange(1, len(sorted_load) + 1) / len(sorted_load) * 100

# Calculate key percentiles
percentiles = [95, 90, 85, 80, 75, 50]
print("\nLoad Duration Curve Statistics:")
for p in percentiles:
    load_at_pct = np.percentile(df['load_mw'], 100 - p)
    print(f"  {p}% of time load >= {load_at_pct:.2f} MW")

# Capacity margin analysis (assuming hypothetical capacity)
assumed_capacity = df['load_mw'].max() * 1.15  # 15% reserve margin
capacity_margin = assumed_capacity - df['load_mw']
min_margin = capacity_margin.min()
avg_margin = capacity_margin.mean()

print(f"\nCapacity Margin Analysis (Assumed Capacity: {assumed_capacity:.2f} MW):")
print(f"  Minimum Margin: {min_margin:.2f} MW ({100*min_margin/assumed_capacity:.1f}%)")
print(f"  Average Margin: {avg_margin:.2f} MW ({100*avg_margin/assumed_capacity:.1f}%)")

# Figure 5: Load Duration Curve
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(cumulative_pct, sorted_load, color='darkred', linewidth=2)
ax.fill_between(cumulative_pct, 0, sorted_load, alpha=0.3, color='darkred')
ax.axhline(y=df['load_mw'].quantile(0.95), color='blue', linestyle='--', 
           label=f'95th Percentile: {df["load_mw"].quantile(0.95):.1f} MW')
ax.axhline(y=df['load_mw'].mean(), color='green', linestyle='--', 
           label=f'Mean: {df["load_mw"].mean():.1f} MW')
ax.axhline(y=assumed_capacity, color='orange', linestyle='-', linewidth=2,
           label=f'Assumed Capacity: {assumed_capacity:.1f} MW')
ax.set_xlabel('Percentage of Time (%)')
ax.set_ylabel('Load (MW)')
ax.set_title('Load Duration Curve')
ax.legend(loc='upper right')
ax.set_xlim(0, 100)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/fig5_load_duration.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig5_load_duration.png")

# =============================================================================
# 5. ANNUAL LOAD FORECAST
# =============================================================================
print("\n[5] ANNUAL LOAD FORECAST")
print("-"*40)

# Calculate daily statistics
daily_stats = df.groupby('date').agg({
    'load_mw': ['mean', 'max', 'min', 'std']
}).reset_index()
daily_stats.columns = ['date', 'mean_load', 'peak_load', 'min_load', 'std_load']
daily_stats['date'] = pd.to_datetime(daily_stats['date'])
daily_stats['day_of_week'] = daily_stats['date'].dt.dayofweek

# Estimate annual energy (GWh)
# Using available data to extrapolate
total_energy_mwh = df['load_mw'].sum() * 0.25  # 15-min intervals = 0.25 hours
days_in_data = (df.index.max() - df.index.min()).days + 1
avg_daily_energy = total_energy_mwh / days_in_data

# Annual projection
annual_energy_gwh = avg_daily_energy * 365 / 1000

print(f"\nEnergy Estimation:")
print(f"  Days in sample: {days_in_data}")
print(f"  Total energy in sample: {total_energy_mwh:.2f} MWh")
print(f"  Average daily energy: {avg_daily_energy:.2f} MWh")
print(f"  Projected annual energy: {annual_energy_gwh:.2f} GWh")

# Peak load analysis
peak_load = df['load_mw'].max()
peak_time = df['load_mw'].idxmax()
print(f"\nPeak Load Analysis:")
print(f"  System Peak: {peak_load:.2f} MW")
print(f"  Peak Time: {peak_time}")

# Annual peak forecast with growth factor (typical 1-3% annual growth)
growth_scenarios = [0.01, 0.02, 0.03]
print(f"\nAnnual Peak Forecast (with growth scenarios):")
for g in growth_scenarios:
    forecasted_peak = peak_load * (1 + g)
    print(f"  {g*100:.0f}% growth: {forecasted_peak:.2f} MW")

# Figure 6: Daily Peak and Average Load
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(daily_stats['date'], daily_stats['peak_load'], 'o-', color='red', 
        markersize=6, label='Daily Peak', alpha=0.7)
ax.plot(daily_stats['date'], daily_stats['mean_load'], 's-', color='blue', 
        markersize=6, label='Daily Average', alpha=0.7)
ax.fill_between(daily_stats['date'], daily_stats['min_load'], daily_stats['peak_load'],
                 alpha=0.2, color='gray', label='Daily Range')
ax.set_xlabel('Date')
ax.set_ylabel('Load (MW)')
ax.set_title('Daily Load Statistics')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('../report/images/fig6_daily_stats.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig6_daily_stats.png")

# =============================================================================
# 6. FORECAST MODEL - SEASONAL DECOMPOSITION
# =============================================================================
print("\n[6] TIME SERIES DECOMPOSITION")
print("-"*40)

# Resample to hourly for decomposition
df_hourly = df['load_mw'].resample('H').mean()

from statsmodels.tsa.seasonal import seasonal_decompose

# Perform decomposition (daily seasonality = 24 hours)
decomposition = seasonal_decompose(df_hourly, model='additive', period=24)

# Figure 7: Seasonal Decomposition
fig, axes = plt.subplots(4, 1, figsize=(14, 10))

decomposition.observed.plot(ax=axes[0], color='steelblue')
axes[0].set_ylabel('Observed')
axes[0].set_title('Time Series Decomposition (Hourly Data)')

decomposition.trend.plot(ax=axes[1], color='darkblue')
axes[1].set_ylabel('Trend')

decomposition.seasonal.plot(ax=axes[2], color='green')
axes[2].set_ylabel('Seasonal')

decomposition.resid.plot(ax=axes[3], color='red', alpha=0.7)
axes[3].set_ylabel('Residual')
axes[3].set_xlabel('Time')

for ax in axes:
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/fig7_decomposition.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig7_decomposition.png")

# =============================================================================
# 7. RELIABILITY METRICS
# =============================================================================
print("\n[7] RELIABILITY METRICS")
print("-"*40)

# Loss of Load Probability (simplified)
# Assuming capacity at peak + reserve margin
reserve_margins = [0.10, 0.15, 0.20]
print("\nReliability Assessment:")
for rm in reserve_margins:
    capacity = peak_load * (1 + rm)
    hours_above = (df['load_mw'] > capacity).sum() * 0.25
    lolp = hours_above / (len(df) * 0.25) * 100
    print(f"  Reserve Margin {rm*100:.0f}% (Capacity: {capacity:.1f} MW): LOLP = {lolp:.4f}%")

# Load factor
load_factor = df['load_mw'].mean() / df['load_mw'].max()
print(f"\nLoad Factor: {load_factor:.3f} ({load_factor*100:.1f}%)")

# Diversity factor (hourly peaks vs system peak)
hourly_peaks = df.groupby('hour')['load_mw'].max()
diversity_factor = hourly_peaks.sum() / (peak_load * 24)
print(f"Diversity Factor: {diversity_factor:.3f}")

# Figure 8: Distribution Analysis
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
axes[0].hist(df['load_mw'], bins=50, color='steelblue', edgecolor='white', alpha=0.7)
axes[0].axvline(df['load_mw'].mean(), color='red', linestyle='--', label=f'Mean: {df["load_mw"].mean():.1f}')
axes[0].axvline(df['load_mw'].median(), color='green', linestyle='--', label=f'Median: {df["load_mw"].median():.1f}')
axes[0].set_xlabel('Load (MW)')
axes[0].set_ylabel('Frequency')
axes[0].set_title('Load Distribution')
axes[0].legend()

# Box plot by hour
df.boxplot(column='load_mw', by='hour', ax=axes[1])
axes[1].set_xlabel('Hour of Day')
axes[1].set_ylabel('Load (MW)')
axes[1].set_title('Load Distribution by Hour')
plt.suptitle('')

plt.tight_layout()
plt.savefig('../report/images/fig8_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig8_distribution.png")

# =============================================================================
# 8. SAVE RESULTS
# =============================================================================
print("\n[8] SAVING RESULTS")
print("-"*40)

# Save summary statistics
summary = {
    'Metric': ['Mean Load (MW)', 'Peak Load (MW)', 'Min Load (MW)', 'Std Dev (MW)',
               'Load Factor', 'Projected Annual Energy (GWh)', 'Days Analyzed'],
    'Value': [f"{df['load_mw'].mean():.2f}", f"{df['load_mw'].max():.2f}", 
              f"{df['load_mw'].min():.2f}", f"{df['load_mw'].std():.2f}",
              f"{load_factor:.3f}", f"{annual_energy_gwh:.2f}", str(days_in_data)]
}
summary_df = pd.DataFrame(summary)
summary_df.to_csv('../outputs/summary_statistics.csv', index=False)
print("  Saved: summary_statistics.csv")

# Save hourly profile
hourly_avg.to_csv('../outputs/hourly_profile.csv')
print("  Saved: hourly_profile.csv")

# Save daily statistics
daily_stats.to_csv('../outputs/daily_statistics.csv', index=False)
print("  Saved: daily_statistics.csv")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print(f"\nAll figures saved to: report/images/")
print(f"All outputs saved to: outputs/")