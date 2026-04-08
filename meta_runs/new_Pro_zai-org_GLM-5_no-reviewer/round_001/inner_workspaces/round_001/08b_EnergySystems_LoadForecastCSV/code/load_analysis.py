import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

print("="*60)
print("POWER SYSTEMS LOAD FORECASTING ANALYSIS")
print("="*60)

# =============================================================================
# 1. DATA LOADING AND PREPROCESSING
# =============================================================================
print("\n[1] Loading and preprocessing data...")

df = pd.read_csv('data/load_15min.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df = df.set_index('timestamp_utc')
df = df.sort_index()

print(f"Data shape: {df.shape}")
print(f"Date range: {df.index.min()} to {df.index.max()}")
print(f"Total duration: {(df.index.max() - df.index.min()).days} days")
print(f"\nLoad statistics:")
print(df['load_mw'].describe())

# Check for missing values
missing = df['load_mw'].isnull().sum()
print(f"\nMissing values: {missing}")

# =============================================================================
# 2. TIME SERIES DECOMPOSITION AND FEATURE ENGINEERING
# =============================================================================
print("\n[2] Feature engineering and time series decomposition...")

# Add temporal features
df['hour'] = df.index.hour
df['day_of_week'] = df.index.dayofweek
df['day_name'] = df.index.day_name()
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

# Calculate rolling statistics
df['rolling_mean_24h'] = df['load_mw'].rolling(window=96, min_periods=1).mean()  # 24 hours = 96 intervals
df['rolling_std_24h'] = df['load_mw'].rolling(window=96, min_periods=1).std()

# Daily statistics
daily_stats = df.groupby(df.index.date).agg({
    'load_mw': ['mean', 'max', 'min', 'std']
}).reset_index()
daily_stats.columns = ['date', 'daily_mean', 'daily_max', 'daily_min', 'daily_std']
daily_stats['date'] = pd.to_datetime(daily_stats['date'])
daily_stats['daily_range'] = daily_stats['daily_max'] - daily_stats['daily_min']

print(f"\nDaily statistics summary:")
print(daily_stats.describe())

# =============================================================================
# 3. HOURLY AND DAILY PATTERN ANALYSIS
# =============================================================================
print("\n[3] Analyzing hourly and daily patterns...")

# Hourly average load
hourly_avg = df.groupby('hour')['load_mw'].agg(['mean', 'std', 'min', 'max'])
print(f"\nHourly average load pattern:")
print(hourly_avg['mean'].round(2))

# Day of week analysis
dow_avg = df.groupby('day_of_week')['load_mw'].agg(['mean', 'std'])
dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
print(f"\nDay of week average load:")
for i, name in enumerate(dow_names):
    print(f"  {name}: {dow_avg.loc[i, 'mean']:.2f} MW (±{dow_avg.loc[i, 'std']:.2f})")

# Peak load analysis
peak_load = df['load_mw'].max()
peak_time = df['load_mw'].idxmax()
min_load = df['load_mw'].min()
min_time = df['load_mw'].idxmin()

print(f"\nPeak load: {peak_load:.2f} MW at {peak_time}")
print(f"Minimum load: {min_load:.2f} MW at {min_time}")
print(f"Load factor: {df['load_mw'].mean() / peak_load * 100:.1f}%")

# =============================================================================
# 4. LOAD FORECASTING MODEL
# =============================================================================
print("\n[4] Building load forecasting model...")

# Simple time series forecasting using seasonal decomposition approach
# Since we have limited data (7 days), we'll use pattern-based forecasting

# Calculate average weekly pattern
weekly_pattern = df.groupby(['day_of_week', 'hour'])['load_mw'].mean().reset_index()
weekly_pattern_pivot = weekly_pattern.pivot(index='hour', columns='day_of_week', values='load_mw')
weekly_pattern_pivot.columns = dow_names

# Calculate overall statistics for forecasting
overall_mean = df['load_mw'].mean()
overall_std = df['load_mw'].std()

# Generate forecast for next 7 days
last_date = df.index.max()
forecast_dates = pd.date_range(
    start=last_date + timedelta(minutes=15),
    periods=7*24*4,  # 7 days, 24 hours, 4 intervals per hour
    freq='15min'
)

# Create forecast dataframe
forecast_df = pd.DataFrame(index=forecast_dates)
forecast_df['hour'] = forecast_df.index.hour
forecast_df['day_of_week'] = forecast_df.index.dayofweek

# Use historical pattern for forecast
forecast_values = []
for idx, row in forecast_df.iterrows():
    dow = row['day_of_week']
    hour = row['hour']
    # Get pattern value
    pattern_value = weekly_pattern_pivot.loc[hour, dow_names[dow]]
    forecast_values.append(pattern_value)

forecast_df['forecast_mw'] = forecast_values

# Add confidence intervals (based on historical variability)
hourly_std = df.groupby('hour')['load_mw'].std()
forecast_df['forecast_lower'] = forecast_df.apply(
    lambda x: x['forecast_mw'] - 1.96 * hourly_std[x['hour']], axis=1
)
forecast_df['forecast_upper'] = forecast_df.apply(
    lambda x: x['forecast_mw'] + 1.96 * hourly_std[x['hour']], axis=1
)

print(f"\nForecast generated for {len(forecast_df)} intervals (7 days)")
print(f"Forecast period: {forecast_df.index.min()} to {forecast_df.index.max()}")
print(f"\nForecast statistics:")
print(forecast_df['forecast_mw'].describe())

# =============================================================================
# 5. ANNUAL LOAD PROJECTION
# =============================================================================
print("\n[5] Annual load projection...")

# Project annual energy consumption
# Based on the weekly pattern, extrapolate to annual figures
days_in_year = 365

# Calculate average daily energy
daily_energy = df.groupby(df.index.date)['load_mw'].sum() * 0.25  # MW * 0.25 hours = MWh
avg_daily_energy = daily_energy.mean()

# Annual projection
annual_energy_projection = avg_daily_energy * days_in_year

# Peak demand projection (considering seasonal variations - assume 10% higher in summer)
projected_annual_peak = peak_load * 1.10  # Conservative estimate with seasonal factor

# Calculate reliability metrics
load_factor = df['load_mw'].mean() / peak_load
capacity_factor = load_factor  # Simplified assumption

print(f"\nAnnual Load Projection:")
print(f"  Average daily energy: {avg_daily_energy:.2f} MWh")
print(f"  Projected annual energy: {annual_energy_projection:.2f} MWh ({annual_energy_projection/1000:.2f} GWh)")
print(f"  Observed peak demand: {peak_load:.2f} MW")
print(f"  Projected annual peak (with seasonal factor): {projected_annual_peak:.2f} MW")
print(f"  Load factor: {load_factor*100:.1f}%")

# =============================================================================
# 6. RELIABILITY ANALYSIS
# =============================================================================
print("\n[6] Reliability analysis...")

# Calculate reserve margin requirements
# Assuming a planning reserve margin of 15%
required_capacity = projected_annual_peak * 1.15

# Load duration curve data
load_sorted = df['load_mw'].sort_values(ascending=False).reset_index(drop=True).to_frame(name='load_mw')
load_sorted['percentage_time'] = (load_sorted.index + 1) / len(load_sorted) * 100

# Calculate time above certain thresholds
threshold_90 = peak_load * 0.90
threshold_80 = peak_load * 0.80
time_above_90 = (df['load_mw'] > threshold_90).sum() / len(df) * 100
time_above_80 = (df['load_mw'] > threshold_80).sum() / len(df) * 100

print(f"\nReliability Metrics:")
print(f"  Required capacity (15% reserve margin): {required_capacity:.2f} MW")
print(f"  Time above 90% of peak: {time_above_90:.1f}%")
print(f"  Time above 80% of peak: {time_above_80:.1f}%")

# Variability analysis
coef_variation = overall_std / overall_mean * 100
print(f"  Coefficient of variation: {coef_variation:.1f}%")

# =============================================================================
# 7. SAVE RESULTS
# =============================================================================
print("\n[7] Saving results...")

# Save daily statistics
daily_stats.to_csv('outputs/daily_statistics.csv', index=False)

# Save hourly pattern
hourly_avg.to_csv('outputs/hourly_pattern.csv')

# Save forecast
forecast_df[['forecast_mw', 'forecast_lower', 'forecast_upper']].to_csv('outputs/weekly_forecast.csv')

# Save load duration curve data
load_sorted.to_csv('outputs/load_duration_curve.csv', index=False)

# Save summary statistics
summary = {
    'metric': [
        'total_observations', 'mean_load_mw', 'std_load_mw', 'min_load_mw', 'max_load_mw',
        'peak_datetime', 'load_factor_pct', 'annual_energy_gwh', 'projected_peak_mw',
        'required_capacity_mw', 'coef_variation_pct', 'time_above_90pct_peak', 'time_above_80pct_peak'
    ],
    'value': [
        len(df), round(overall_mean, 2), round(overall_std, 2), round(min_load, 2), round(peak_load, 2),
        str(peak_time), round(load_factor*100, 1), round(annual_energy_projection/1000, 2),
        round(projected_annual_peak, 2), round(required_capacity, 2), round(coef_variation, 1),
        round(time_above_90, 1), round(time_above_80, 1)
    ]
}
pd.DataFrame(summary).to_csv('outputs/summary_statistics.csv', index=False)

print("Results saved to outputs/")

# =============================================================================
# 8. GENERATE FIGURES
# =============================================================================
print("\n[8] Generating figures...")

# Figure 1: Load Time Series
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df.index, df['load_mw'], color='steelblue', linewidth=0.8, alpha=0.8)
ax.axhline(y=overall_mean, color='red', linestyle='--', linewidth=1.5, label=f'Mean: {overall_mean:.1f} MW')
ax.axhline(y=peak_load, color='darkred', linestyle=':', linewidth=1.5, label=f'Peak: {peak_load:.1f} MW')
ax.set_xlabel('Date/Time')
ax.set_ylabel('Load (MW)')
ax.set_title('15-Minute Interval Load Time Series')
ax.legend(loc='upper right')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
ax.xaxis.set_major_locator(mdates.DayLocator())
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/fig1_load_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig1_load_timeseries.png")

# Figure 2: Hourly Load Pattern
fig, ax = plt.subplots(figsize=(10, 6))
hours = hourly_avg.index
ax.fill_between(hours, hourly_avg['min'], hourly_avg['max'], alpha=0.3, color='steelblue', label='Min-Max Range')
ax.fill_between(hours, hourly_avg['mean'] - hourly_avg['std'], hourly_avg['mean'] + hourly_avg['std'], 
                 alpha=0.5, color='steelblue', label='±1 Std Dev')
ax.plot(hours, hourly_avg['mean'], color='darkblue', linewidth=2.5, marker='o', markersize=5, label='Mean Load')
ax.set_xlabel('Hour of Day')
ax.set_ylabel('Load (MW)')
ax.set_title('Average Hourly Load Pattern with Variability')
ax.set_xticks(range(0, 24, 2))
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/fig2_hourly_pattern.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig2_hourly_pattern.png")

# Figure 3: Day of Week Comparison
fig, ax = plt.subplots(figsize=(10, 6))
colors = plt.cm.Set2(np.linspace(0, 1, 7))
for i, name in enumerate(dow_names):
    daily_data = df[df['day_of_week'] == i].groupby('hour')['load_mw'].mean()
    ax.plot(daily_data.index, daily_data.values, color=colors[i], linewidth=1.5, label=name, alpha=0.8)
ax.set_xlabel('Hour of Day')
ax.set_ylabel('Load (MW)')
ax.set_title('Average Hourly Load by Day of Week')
ax.set_xticks(range(0, 24, 2))
ax.legend(loc='upper left', ncol=2)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/fig3_daily_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig3_daily_comparison.png")

# Figure 4: Load Duration Curve
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(load_sorted['percentage_time'], load_sorted['load_mw'], color='darkgreen', linewidth=2)
ax.axhline(y=peak_load, color='red', linestyle='--', linewidth=1, alpha=0.7, label=f'Peak: {peak_load:.1f} MW')
ax.axhline(y=overall_mean, color='blue', linestyle='--', linewidth=1, alpha=0.7, label=f'Mean: {overall_mean:.1f} MW')
ax.fill_between(load_sorted['percentage_time'], load_sorted['load_mw'], alpha=0.3, color='green')
ax.set_xlabel('Percentage of Time (%)')
ax.set_ylabel('Load (MW)')
ax.set_title('Load Duration Curve')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 100)
plt.tight_layout()
plt.savefig('report/images/fig4_load_duration_curve.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig4_load_duration_curve.png")

# Figure 5: Weekly Forecast
fig, ax = plt.subplots(figsize=(14, 5))
# Plot historical data (last 3 days)
historical_start = df.index.max() - timedelta(days=3)
historical_data = df[df.index >= historical_start]
ax.plot(historical_data.index, historical_data['load_mw'], color='steelblue', linewidth=1, label='Historical Load')

# Plot forecast
ax.plot(forecast_df.index, forecast_df['forecast_mw'], color='darkorange', linewidth=1.5, label='Forecast')
ax.fill_between(forecast_df.index, forecast_df['forecast_lower'], forecast_df['forecast_upper'], 
                alpha=0.3, color='orange', label='95% Confidence Interval')
ax.axvline(x=df.index.max(), color='gray', linestyle='--', linewidth=1, alpha=0.7, label='Forecast Start')
ax.set_xlabel('Date/Time')
ax.set_ylabel('Load (MW)')
ax.set_title('7-Day Load Forecast with Confidence Intervals')
ax.legend(loc='upper right')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
ax.xaxis.set_major_locator(mdates.DayLocator())
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/fig5_weekly_forecast.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig5_weekly_forecast.png")

# Figure 6: Daily Statistics
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Daily mean
axes[0, 0].bar(daily_stats['date'], daily_stats['daily_mean'], color='steelblue', alpha=0.7)
axes[0, 0].axhline(y=daily_stats['daily_mean'].mean(), color='red', linestyle='--', label='Overall Mean')
axes[0, 0].set_xlabel('Date')
axes[0, 0].set_ylabel('Load (MW)')
axes[0, 0].set_title('Daily Average Load')
axes[0, 0].legend()
axes[0, 0].tick_params(axis='x', rotation=45)

# Daily peak
axes[0, 1].bar(daily_stats['date'], daily_stats['daily_max'], color='darkred', alpha=0.7)
axes[0, 1].set_xlabel('Date')
axes[0, 1].set_ylabel('Load (MW)')
axes[0, 1].set_title('Daily Peak Load')
axes[0, 1].tick_params(axis='x', rotation=45)

# Daily range
axes[1, 0].bar(daily_stats['date'], daily_stats['daily_range'], color='green', alpha=0.7)
axes[1, 0].set_xlabel('Date')
axes[1, 0].set_ylabel('Load (MW)')
axes[1, 0].set_title('Daily Load Range (Peak - Min)')
axes[1, 0].tick_params(axis='x', rotation=45)

# Daily variability
axes[1, 1].bar(daily_stats['date'], daily_stats['daily_std'], color='purple', alpha=0.7)
axes[1, 1].set_xlabel('Date')
axes[1, 1].set_ylabel('Load (MW)')
axes[1, 1].set_title('Daily Load Standard Deviation')
axes[1, 1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('report/images/fig6_daily_statistics.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig6_daily_statistics.png")

# Figure 7: Distribution Analysis
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Histogram
axes[0].hist(df['load_mw'], bins=50, color='steelblue', alpha=0.7, edgecolor='white')
axes[0].axvline(x=overall_mean, color='red', linestyle='--', linewidth=2, label=f'Mean: {overall_mean:.1f} MW')
axes[0].axvline(x=overall_mean + overall_std, color='orange', linestyle=':', linewidth=1.5, label=f'±1 Std: {overall_std:.1f} MW')
axes[0].axvline(x=overall_mean - overall_std, color='orange', linestyle=':', linewidth=1.5)
axes[0].set_xlabel('Load (MW)')
axes[0].set_ylabel('Frequency')
axes[0].set_title('Load Distribution')
axes[0].legend()

# Box plot by hour
hourly_data = [df[df['hour'] == h]['load_mw'].values for h in range(24)]
bp = axes[1].boxplot(hourly_data, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('steelblue')
    patch.set_alpha(0.6)
axes[1].set_xlabel('Hour of Day')
axes[1].set_ylabel('Load (MW)')
axes[1].set_title('Load Distribution by Hour')
axes[1].set_xticks(range(1, 25, 2))
axes[1].set_xticklabels(range(0, 24, 2))

plt.tight_layout()
plt.savefig('report/images/fig7_distribution_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: fig7_distribution_analysis.png")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print(f"\nAll figures saved to report/images/")
print(f"All data saved to outputs/")
