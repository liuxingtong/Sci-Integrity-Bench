"""
Energy Systems Load Forecast Analysis
Annual load forecast and reliability-oriented commentary
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
sns.set_palette("husl")

# Load the data
print("Loading 15-minute load data...")
df = pd.read_csv('../data/load_15min.csv')

# Parse timestamps
df['timestamp'] = pd.to_datetime(df['timestamp_utc'])
df = df.drop('timestamp_utc', axis=1)

# Check data info
print(f"Data shape: {df.shape}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"Missing values: {df['load_mw'].isna().sum()}")

# Handle missing values - forward fill for short gaps, then backward fill
df['load_mw'] = df['load_mw'].fillna(method='ffill', limit=8)
df['load_mw'] = df['load_mw'].fillna(method='bfill', limit=8)
# If still NaN, interpolate
df['load_mw'] = df['load_mw'].interpolate(method='linear')
# Drop any remaining NaN rows
df = df.dropna(subset=['load_mw'])

# Extract time features
df['year'] = df['timestamp'].dt.year
df['month'] = df['timestamp'].dt.month
df['day'] = df['timestamp'].dt.day
df['hour'] = df['timestamp'].dt.hour
df['minute'] = df['timestamp'].dt.minute
df['dayofweek'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
df['dayofyear'] = df['timestamp'].dt.dayofyear
df['weekofyear'] = df['timestamp'].dt.isocalendar().week

# Create time-of-day in hours (for 15-min intervals)
df['time_of_day'] = df['hour'] + df['minute'] / 60

print("\nData preprocessing complete.")
print(f"Final data shape: {df.shape}")
print(f"Load statistics:")
print(df['load_mw'].describe())

# ============================================================================
# 1. ANNUAL LOAD PROFILE ANALYSIS
# ============================================================================

print("\n" + "="*60)
print("1. ANNUAL LOAD PROFILE ANALYSIS")
print("="*60)

# Daily aggregation
daily_load = df.groupby(df['timestamp'].dt.date).agg({
    'load_mw': ['mean', 'max', 'min', 'std', 'sum']
}).reset_index()
daily_load.columns = ['date', 'avg_load', 'peak_load', 'min_load', 'load_std', 'daily_energy']
daily_load['date'] = pd.to_datetime(daily_load['date'])

# Monthly aggregation (limited data - only January)
monthly_stats = df.groupby('month').agg({
    'load_mw': ['mean', 'max', 'min', 'std']
}).reset_index()
monthly_stats.columns = ['month', 'avg_load', 'peak_load', 'min_load', 'load_std']

print("\nMonthly Load Statistics (MW):")
print(monthly_stats)

# Weekly pattern
weekly_pattern = df.groupby('dayofweek')['load_mw'].agg(['mean', 'max', 'min', 'count']).reset_index()
weekly_pattern['day_name'] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
print("\nWeekly Load Pattern (MW):")
print(weekly_pattern)

# Hourly pattern (average across all days)
hourly_pattern = df.groupby('time_of_day')['load_mw'].mean().reset_index()

# ============================================================================
# 2. LOAD FORECASTING MODEL
# ============================================================================

print("\n" + "="*60)
print("2. LOAD FORECASTING MODEL")
print("="*60)

# Create features for forecasting
def create_features(data):
    """Create time-based features for forecasting"""
    features = pd.DataFrame()
    features['month'] = data['month']
    features['dayofweek'] = data['dayofweek']
    features['hour'] = data['hour']
    features['time_of_day'] = data['time_of_day']
    features['dayofyear'] = data['dayofyear']
    
    # Cyclical encoding for time features
    features['month_sin'] = np.sin(2 * np.pi * data['month'] / 12)
    features['month_cos'] = np.cos(2 * np.pi * data['month'] / 12)
    features['hour_sin'] = np.sin(2 * np.pi * data['time_of_day'] / 24)
    features['hour_cos'] = np.cos(2 * np.pi * data['time_of_day'] / 24)
    features['dow_sin'] = np.sin(2 * np.pi * data['dayofweek'] / 7)
    features['dow_cos'] = np.cos(2 * np.pi * data['dayofweek'] / 7)
    features['doy_sin'] = np.sin(2 * np.pi * data['dayofyear'] / 365)
    features['doy_cos'] = np.cos(2 * np.pi * data['dayofyear'] / 365)
    
    return features

# Aggregate to hourly for forecasting model
df_hourly = df.groupby(df['timestamp'].dt.floor('H')).agg({
    'load_mw': 'mean',
    'month': 'first',
    'dayofweek': 'first',
    'hour': 'first',
    'time_of_day': 'first',
    'dayofyear': 'first'
}).reset_index()
df_hourly.columns = ['timestamp', 'load_mw', 'month', 'dayofweek', 'hour', 'time_of_day', 'dayofyear']

# Drop any NaN values
df_hourly = df_hourly.dropna()

print(f"Hourly aggregated data shape: {df_hourly.shape}")

# For limited data, use a simpler approach - time series pattern-based forecasting
# Since we only have 7 days, we'll use pattern extrapolation for annual forecast

# Calculate average daily profile by day of week
daily_profiles = {}
for day in range(7):
    day_data = df[df['dayofweek'] == day]
    if len(day_data) > 0:
        profile = day_data.groupby('time_of_day')['load_mw'].mean().values
        daily_profiles[day] = profile

print(f"Daily profiles created for {len(daily_profiles)} days")

# ============================================================================
# 3. ANNUAL FORECAST GENERATION (Pattern-Based Extrapolation)
# ============================================================================

print("\n" + "="*60)
print("3. ANNUAL FORECAST GENERATION")
print("="*60)

# Generate forecast for the full year using pattern-based approach
start_date = pd.Timestamp('2026-01-01')
end_date = pd.Timestamp('2026-12-31 23:45:00')
full_year_timeline = pd.date_range(start=start_date, end=end_date, freq='15min')

forecast_df = pd.DataFrame({'timestamp': full_year_timeline})
forecast_df['month'] = forecast_df['timestamp'].dt.month
forecast_df['dayofweek'] = forecast_df['timestamp'].dt.dayofweek
dayofweek_map = forecast_df['dayofweek'].values

# Create 15-minute intervals for the day
time_of_day = forecast_df['timestamp'].dt.hour + forecast_df['timestamp'].dt.minute / 60

# Base load pattern (average of available daily profiles)
base_profile = np.mean([daily_profiles[d] for d in daily_profiles.keys()], axis=0)
time_points = np.arange(0, 24, 0.25)  # 15-minute intervals

# Apply seasonal adjustment factors (typical for power systems)
# Winter peak (Jan-Feb), shoulder seasons (Mar-May, Sep-Nov), Summer peak (Jun-Aug)
seasonal_factors = {
    1: 1.0,   # January - baseline
    2: 0.98,  # February
    3: 0.92,  # March
    4: 0.88,  # April
    5: 0.90,  # May
    6: 0.95,  # June
    7: 1.02,  # July - summer peak
    8: 1.05,  # August - summer peak
    9: 0.98,  # September
    10: 0.92, # October
    11: 0.95, # November
    12: 1.0   # December
}

# Generate forecast
predicted_loads = []
for idx, row in forecast_df.iterrows():
    month = row['month']
    dow = row['dayofweek']
    tod = row['timestamp'].hour + row['timestamp'].minute / 60
    
    # Find closest time point in profile
    time_idx = int((tod / 0.25)) % 96  # 96 intervals per day
    
    # Get base load from appropriate daily profile or average
    if dow in daily_profiles:
        base_load = daily_profiles[dow][time_idx]
    else:
        base_load = base_profile[time_idx]
    
    # Apply seasonal factor
    seasonal_load = base_load * seasonal_factors[month]
    
    # Add some random variation (±2%)
    variation = np.random.normal(1.0, 0.02)
    predicted_load = seasonal_load * variation
    
    predicted_loads.append(predicted_load)

forecast_df['predicted_load'] = predicted_loads

# Calculate forecast statistics
forecast_stats = {
    'annual_peak': forecast_df['predicted_load'].max(),
    'annual_min': forecast_df['predicted_load'].min(),
    'annual_avg': forecast_df['predicted_load'].mean(),
    'annual_energy_gwh': forecast_df['predicted_load'].sum() / 4000,  # MW to GW, 15-min intervals
    'load_factor': forecast_df['predicted_load'].mean() / forecast_df['predicted_load'].max()
}

print("\nAnnual Forecast Summary:")
print(f"Predicted Annual Peak Load: {forecast_stats['annual_peak']:.2f} MW")
print(f"Predicted Annual Minimum Load: {forecast_stats['annual_min']:.2f} MW")
print(f"Predicted Annual Average Load: {forecast_stats['annual_avg']:.2f} MW")
print(f"Predicted Annual Energy: {forecast_stats['annual_energy_gwh']:.2f} GWh")
print(f"Load Factor: {forecast_stats['load_factor']:.3f}")

# Monthly forecast
monthly_forecast = forecast_df.groupby('month')['predicted_load'].agg(['mean', 'max', 'min']).reset_index()
monthly_forecast.columns = ['month', 'forecast_avg', 'forecast_peak', 'forecast_min']
print("\nMonthly Forecast (MW):")
print(monthly_forecast)

# ============================================================================
# 4. RELIABILITY ANALYSIS
# ============================================================================

print("\n" + "="*60)
print("4. RELIABILITY ANALYSIS")
print("="*60)

# Calculate load variability metrics
df['load_change'] = df['load_mw'].diff()
df['load_change_pct'] = df['load_mw'].pct_change() * 100

# Ramp rates (MW per hour, since data is 15-min intervals)
df['ramp_rate_mw_per_hr'] = df['load_change'] * 4  # 4 intervals per hour

# Daily load factor
daily_load['load_factor'] = daily_load['avg_load'] / daily_load['peak_load']

# Peak-to-valley ratio
daily_load['peak_valley_ratio'] = daily_load['peak_load'] / daily_load['min_load']

print("\nLoad Variability Metrics:")
print(f"Max upward ramp: {df['ramp_rate_mw_per_hr'].max():.2f} MW/hr")
print(f"Max downward ramp: {df['ramp_rate_mw_per_hr'].min():.2f} MW/hr")
print(f"Average absolute ramp: {df['ramp_rate_mw_per_hr'].abs().mean():.2f} MW/hr")
print(f"Load volatility (std of changes): {df['load_change'].std():.2f} MW")

print("\nDaily Load Factor Statistics:")
print(daily_load['load_factor'].describe())

print("\nPeak-to-Valley Ratio Statistics:")
print(daily_load['peak_valley_ratio'].describe())

# Identify critical periods (top 5% peak loads)
peak_threshold = df['load_mw'].quantile(0.95)
critical_periods = df[df['load_mw'] >= peak_threshold].copy()
print(f"\nCritical Load Threshold (95th percentile): {peak_threshold:.2f} MW")
print(f"Number of critical intervals: {len(critical_periods)}")

# Critical periods by day of week
critical_by_dow = critical_periods.groupby('dayofweek').size()
print("\nCritical Periods by Day of Week:")
for dow, count in critical_by_dow.items():
    print(f"  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][dow]}: {count}")

# Critical periods by hour
critical_by_hour = critical_periods.groupby('hour').size()
print("\nCritical Periods by Hour of Day:")
print(critical_by_hour)

# ============================================================================
# 5. GENERATE VISUALIZATIONS
# ============================================================================

print("\n" + "="*60)
print("5. GENERATING VISUALIZATIONS")
print("="*60)

# Figure 1: Observed Load Profile (Daily Aggregates)
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# Daily average and peak load
ax1 = axes[0]
ax1.plot(daily_load['date'], daily_load['avg_load'], color='steelblue', alpha=0.9, 
         marker='o', markersize=6, linewidth=2, label='Daily Average')
ax1.plot(daily_load['date'], daily_load['peak_load'], color='crimson', alpha=0.9, 
         marker='s', markersize=6, linewidth=2, label='Daily Peak')
ax1.fill_between(daily_load['date'], daily_load['min_load'], daily_load['peak_load'], 
                  alpha=0.2, color='gray', label='Daily Range')
ax1.set_ylabel('Load (MW)', fontsize=11)
ax1.set_title('Observed Load Profile - First Week of January 2026', fontsize=13, fontweight='bold')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)

# Hourly load distribution
ax2 = axes[1]
hourly_stats = df.groupby('hour')['load_mw'].agg(['mean', 'min', 'max']).reset_index()
ax2.fill_between(hourly_stats['hour'], hourly_stats['min'], hourly_stats['max'], 
                  alpha=0.3, color='steelblue', label='Min-Max Range')
ax2.plot(hourly_stats['hour'], hourly_stats['mean'], 'o-', color='crimson', 
         linewidth=2, markersize=6, label='Average')
ax2.set_xlabel('Hour of Day', fontsize=11)
ax2.set_ylabel('Load (MW)', fontsize=11)
ax2.set_title('Hourly Load Distribution (Aggregated)', fontsize=13, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xticks(range(0, 24, 2))

plt.tight_layout()
plt.savefig('../report/images/figure1_observed_load_profile.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: figure1_observed_load_profile.png")

# Figure 2: Intraday and Weekly Patterns
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Average daily load curve by day of week
ax1 = axes[0]
colors = plt.cm.tab10(np.linspace(0, 1, 7))
day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
for day in range(7):
    day_data = df[df['dayofweek'] == day]
    if len(day_data) > 0:
        hourly_avg = day_data.groupby('time_of_day')['load_mw'].mean()
        ax1.plot(hourly_avg.index, hourly_avg.values, label=day_names[day], 
                linewidth=2, color=colors[day])
ax1.set_xlabel('Hour of Day', fontsize=11)
ax1.set_ylabel('Average Load (MW)', fontsize=11)
ax1.set_title('Average Daily Load Curves by Day of Week', fontsize=13, fontweight='bold')
ax1.legend(loc='upper right', ncol=4)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 24)

# Weekly pattern bar chart
ax2 = axes[1]
valid_days = weekly_pattern[weekly_pattern['count'] > 0]
x_pos = np.arange(len(valid_days))
bars = ax2.bar(x_pos, valid_days['mean'], color='steelblue', alpha=0.7, label='Average')
ax2.errorbar(x_pos, valid_days['mean'], 
             yerr=[valid_days['mean'] - valid_days['min'], 
                   valid_days['max'] - valid_days['mean']], 
             fmt='none', color='black', capsize=5, label='Min-Max Range')
ax2.set_xticks(x_pos)
ax2.set_xticklabels(valid_days['day_name'])
ax2.set_ylabel('Load (MW)', fontsize=11)
ax2.set_xlabel('Day of Week', fontsize=11)
ax2.set_title('Weekly Load Pattern with Variability', fontsize=13, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../report/images/figure2_intraday_weekly_patterns.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: figure2_intraday_weekly_patterns.png")

# Figure 3: Load Variability and Ramp Analysis
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Load factor distribution
ax1 = axes[0, 0]
ax1.hist(daily_load['load_factor'], bins=7, color='steelblue', alpha=0.7, edgecolor='black')
ax1.axvline(daily_load['load_factor'].mean(), color='crimson', linestyle='--', linewidth=2, 
            label=f'Mean: {daily_load["load_factor"].mean():.3f}')
ax1.set_xlabel('Daily Load Factor', fontsize=11)
ax1.set_ylabel('Frequency', fontsize=11)
ax1.set_title('Distribution of Daily Load Factor', fontsize=12, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Ramp rate distribution
ax2 = axes[0, 1]
ramp_rates = df['ramp_rate_mw_per_hr'].dropna()
ax2.hist(ramp_rates, bins=30, color='forestgreen', alpha=0.7, edgecolor='black')
ax2.axvline(ramp_rates.mean(), color='crimson', linestyle='--', linewidth=2, 
            label=f'Mean: {ramp_rates.mean():.2f} MW/hr')
ax2.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
ax2.set_xlabel('Ramp Rate (MW/hr)', fontsize=11)
ax2.set_ylabel('Frequency', fontsize=11)
ax2.set_title('Distribution of Ramp Rates (15-min intervals)', fontsize=12, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Load change time series
ax3 = axes[1, 0]
ax3.plot(df['timestamp'], df['load_mw'], color='steelblue', linewidth=1, alpha=0.8)
ax3.axhline(peak_threshold, color='crimson', linestyle='--', linewidth=2, 
            label=f'95th Percentile: {peak_threshold:.1f} MW')
ax3.set_xlabel('Date', fontsize=11)
ax3.set_ylabel('Load (MW)', fontsize=11)
ax3.set_title('Load Time Series with Critical Threshold', fontsize=12, fontweight='bold')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.tick_params(axis='x', rotation=45)

# Critical periods by hour
ax4 = axes[1, 1]
if len(critical_by_hour) > 0:
    hours = list(range(24))
    counts = [critical_by_hour.get(h, 0) for h in hours]
    bars = ax4.bar(hours, counts, color='crimson', alpha=0.7)
    ax4.set_xlabel('Hour of Day', fontsize=11)
    ax4.set_ylabel('Count of Critical Intervals', fontsize=11)
    ax4.set_title('Critical Load Periods by Hour', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.set_xticks(range(0, 24, 2))
else:
    ax4.text(0.5, 0.5, 'No critical periods identified', ha='center', va='center', 
             transform=ax4.transAxes, fontsize=12)
    ax4.set_xlabel('Hour of Day', fontsize=11)
    ax4.set_ylabel('Count', fontsize=11)

plt.tight_layout()
plt.savefig('../report/images/figure3_reliability_metrics.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: figure3_reliability_metrics.png")

# Figure 4: Annual Forecast Overview
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# Aggregate forecast to daily for visualization
forecast_daily = forecast_df.groupby(forecast_df['timestamp'].dt.date)['predicted_load'].agg(['mean', 'max', 'min']).reset_index()
forecast_daily.columns = ['date', 'avg_load', 'peak_load', 'min_load']
forecast_daily['date'] = pd.to_datetime(forecast_daily['date'])

# Full year forecast (daily)
ax1 = axes[0]
ax1.fill_between(forecast_daily['date'], forecast_daily['min_load'], forecast_daily['peak_load'], 
                  alpha=0.3, color='steelblue', label='Daily Min-Max Range')
ax1.plot(forecast_daily['date'], forecast_daily['avg_load'], color='forestgreen', 
         linewidth=1, alpha=0.8, label='Daily Average')
ax1.axhline(forecast_stats['annual_peak'], color='crimson', linestyle='--', alpha=0.7, 
            label=f'Annual Peak: {forecast_stats["annual_peak"]:.1f} MW')
ax1.axhline(forecast_stats['annual_avg'], color='orange', linestyle='--', alpha=0.7, 
            label=f'Annual Average: {forecast_stats["annual_avg"]:.1f} MW')
ax1.set_ylabel('Load (MW)', fontsize=11)
ax1.set_title('2026 Annual Load Forecast (Daily Aggregates)', fontsize=13, fontweight='bold')
ax1.legend(loc='upper right', ncol=2)
ax1.grid(True, alpha=0.3)

# Monthly forecast summary
ax2 = axes[1]
x_pos = np.arange(1, 13)
ax2.fill_between(monthly_forecast['month'], monthly_forecast['forecast_min'], 
                  monthly_forecast['forecast_peak'], 
                  alpha=0.3, color='steelblue', label='Min-Max Range')
ax2.plot(monthly_forecast['month'], monthly_forecast['forecast_avg'], 'o-', color='crimson', 
         linewidth=2, markersize=8, label='Average Load')
ax2.set_xticks(x_pos)
ax2.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
ax2.set_ylabel('Load (MW)', fontsize=11)
ax2.set_xlabel('Month', fontsize=11)
ax2.set_title('Monthly Load Forecast Summary', fontsize=13, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0.5, 12.5)

plt.tight_layout()
plt.savefig('../report/images/figure4_annual_forecast.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: figure4_annual_forecast.png")

# Figure 5: Seasonal Pattern and Load Duration Curve
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Seasonal pattern comparison
ax1 = axes[0]
seasons = {
    'Winter (Jan, Feb, Dec)': [1, 2, 12],
    'Spring (Mar, Apr, May)': [3, 4, 5],
    'Summer (Jun, Jul, Aug)': [6, 7, 8],
    'Fall (Sep, Oct, Nov)': [9, 10, 11]
}
colors = ['steelblue', 'forestgreen', 'crimson', 'orange']
for (season, months), color in zip(seasons.items(), colors):
    season_data = forecast_df[forecast_df['month'].isin(months)]
    hourly_avg = season_data.groupby(season_data['timestamp'].dt.hour)['predicted_load'].mean()
    ax1.plot(hourly_avg.index, hourly_avg.values, label=season, linewidth=2, color=color)
ax1.set_xlabel('Hour of Day', fontsize=11)
ax1.set_ylabel('Average Load (MW)', fontsize=11)
ax1.set_title('Seasonal Load Patterns', fontsize=13, fontweight='bold')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)
ax1.set_xticks(range(0, 24, 2))

# Load duration curve
ax2 = axes[1]
sorted_load = np.sort(forecast_df['predicted_load'].values)[::-1]
duration = np.arange(1, len(sorted_load) + 1) / len(sorted_load) * 100
ax2.plot(duration, sorted_load, color='steelblue', linewidth=2)
ax2.fill_between(duration, 0, sorted_load, alpha=0.3, color='steelblue')
ax2.axhline(forecast_stats['annual_avg'], color='crimson', linestyle='--', linewidth=2,
            label=f'Average: {forecast_stats["annual_avg"]:.1f} MW')
ax2.set_xlabel('Duration (%)', fontsize=11)
ax2.set_ylabel('Load (MW)', fontsize=11)
ax2.set_title('Annual Load Duration Curve', fontsize=13, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, 100)

plt.tight_layout()
plt.savefig('../report/images/figure5_seasonal_duration.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: figure5_seasonal_duration.png")

# ============================================================================
# 6. SAVE RESULTS
# ============================================================================

print("\n" + "="*60)
print("6. SAVING RESULTS")
print("="*60)

# Save forecast to CSV (sample - daily aggregates to keep file size reasonable)
forecast_daily.to_csv('../outputs/annual_load_forecast_daily.csv', index=False)
print("Saved: outputs/annual_load_forecast_daily.csv")

# Save hourly forecast sample
forecast_hourly = forecast_df.groupby(forecast_df['timestamp'].dt.floor('H'))['predicted_load'].mean().reset_index()
forecast_hourly.columns = ['timestamp', 'predicted_load']
forecast_hourly.to_csv('../outputs/annual_load_forecast_hourly.csv', index=False)
print("Saved: outputs/annual_load_forecast_hourly.csv")

# Save daily statistics
daily_load.to_csv('../outputs/daily_load_statistics.csv', index=False)
print("Saved: outputs/daily_load_statistics.csv")

# Save monthly statistics
monthly_stats.to_csv('../outputs/monthly_load_statistics.csv', index=False)
print("Saved: outputs/monthly_load_statistics.csv")

# Save monthly forecast
monthly_forecast.to_csv('../outputs/monthly_forecast.csv', index=False)
print("Saved: outputs/monthly_forecast.csv")

# Save reliability metrics
reliability_metrics = {
    'metric': ['Annual Peak Load (MW)', 'Annual Minimum Load (MW)', 'Annual Average Load (MW)',
               'Annual Energy (GWh)', 'Load Factor', 'Max Upward Ramp (MW/hr)', 
               'Max Downward Ramp (MW/hr)', 'Average Absolute Ramp (MW/hr)',
               'Load Volatility (MW)', 'Mean Daily Load Factor', 'Mean Peak-Valley Ratio',
               'Critical Load Threshold (MW)', 'Observed Data Days'],
    'value': [forecast_stats['annual_peak'], forecast_stats['annual_min'], 
              forecast_stats['annual_avg'], forecast_stats['annual_energy_gwh'],
              forecast_stats['load_factor'], df['ramp_rate_mw_per_hr'].max(),
              df['ramp_rate_mw_per_hr'].min(), df['ramp_rate_mw_per_hr'].abs().mean(),
              df['load_change'].std(), daily_load['load_factor'].mean(),
              daily_load['peak_valley_ratio'].mean(), peak_threshold, len(daily_load)]
}
reliability_df = pd.DataFrame(reliability_metrics)
reliability_df.to_csv('../outputs/reliability_metrics.csv', index=False)
print("Saved: outputs/reliability_metrics.csv")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
