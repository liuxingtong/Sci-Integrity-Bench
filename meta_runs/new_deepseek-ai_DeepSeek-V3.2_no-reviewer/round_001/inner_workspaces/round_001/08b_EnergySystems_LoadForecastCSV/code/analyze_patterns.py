import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
import os

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Load data
df = pd.read_csv('data/load_15min.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df.set_index('timestamp_utc', inplace=True)

# Create time-based features
df['hour'] = df.index.hour
df['minute'] = df.index.minute
df['day_of_week'] = df.index.dayofweek  # Monday=0, Sunday=6
df['day_of_month'] = df.index.day
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

# 1. Plot the full time series
plt.figure(figsize=(14, 6))
plt.plot(df.index, df['load_mw'], linewidth=1)
plt.title('15-Minute Load Time Series (7 Days)', fontsize=14)
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/full_timeseries.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Plot daily patterns
plt.figure(figsize=(14, 6))
for day in range(7):
    day_data = df[df['day_of_week'] == day]
    plt.plot(day_data.index, day_data['load_mw'], label=f'Day {day}', alpha=0.7, linewidth=1)
plt.title('Load Patterns by Day of Week', fontsize=14)
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend(title='Day of Week (0=Monday)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/daily_patterns.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Box plot by hour
plt.figure(figsize=(14, 6))
df['hour_str'] = df['hour'].astype(str).str.zfill(2) + ':00'
box_data = [df[df['hour'] == h]['load_mw'].values for h in range(24)]
plt.boxplot(box_data, labels=[f'{h:02d}:00' for h in range(24)])
plt.title('Load Distribution by Hour of Day', fontsize=14)
plt.xlabel('Hour of Day')
plt.ylabel('Load (MW)')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/hourly_boxplot.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Average daily profile
avg_hourly = df.groupby('hour')['load_mw'].mean()
std_hourly = df.groupby('hour')['load_mw'].std()

plt.figure(figsize=(14, 6))
plt.plot(avg_hourly.index, avg_hourly.values, 'b-', linewidth=2, label='Mean')
plt.fill_between(avg_hourly.index, 
                 avg_hourly.values - std_hourly.values, 
                 avg_hourly.values + std_hourly.values, 
                 alpha=0.2, color='b', label='±1 Std Dev')
plt.title('Average Daily Load Profile with Variability', fontsize=14)
plt.xlabel('Hour of Day')
plt.ylabel('Load (MW)')
plt.xticks(range(0, 24, 2))
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('report/images/avg_daily_profile.png', dpi=300, bbox_inches='tight')
plt.close()

# 5. Weekend vs weekday comparison
weekday_avg = df[df['is_weekend'] == 0].groupby('hour')['load_mw'].mean()
weekend_avg = df[df['is_weekend'] == 1].groupby('hour')['load_mw'].mean()

plt.figure(figsize=(14, 6))
plt.plot(weekday_avg.index, weekday_avg.values, 'b-', linewidth=2, label='Weekday (Mon-Fri)')
plt.plot(weekend_avg.index, weekend_avg.values, 'r-', linewidth=2, label='Weekend (Sat-Sun)')
plt.title('Weekday vs Weekend Load Profiles', fontsize=14)
plt.xlabel('Hour of Day')
plt.ylabel('Load (MW)')
plt.xticks(range(0, 24, 2))
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('report/images/weekday_weekend_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 6. Time series decomposition (assuming daily seasonality)
# Resample to hourly for cleaner decomposition
hourly_df = df['load_mw'].resample('H').mean()
# Additive decomposition
decomposition = seasonal_decompose(hourly_df, model='additive', period=24)

fig, axes = plt.subplots(4, 1, figsize=(14, 10))
axes[0].plot(decomposition.observed)
axes[0].set_ylabel('Observed')
axes[0].set_title('Time Series Decomposition (Hourly Data)')

axes[1].plot(decomposition.trend)
axes[1].set_ylabel('Trend')

axes[2].plot(decomposition.seasonal)
axes[2].set_ylabel('Seasonal')

axes[3].plot(decomposition.resid)
axes[3].set_ylabel('Residual')
axes[3].set_xlabel('Time')

plt.tight_layout()
plt.savefig('report/images/decomposition.png', dpi=300, bbox_inches='tight')
plt.close()

# 7. Autocorrelation analysis
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

fig, axes = plt.subplots(2, 1, figsize=(14, 8))
plot_acf(df['load_mw'], lags=96, ax=axes[0])  # 24 hours * 4 intervals = 96 lags
axes[0].set_title('Autocorrelation Function (ACF)')
axes[0].set_xlabel('Lag (15-min intervals)')
axes[0].set_ylabel('ACF')

plot_pacf(df['load_mw'], lags=48, ax=axes[1])  # 12 hours * 4 intervals = 48 lags
axes[1].set_title('Partial Autocorrelation Function (PACF)')
axes[1].set_xlabel('Lag (15-min intervals)')
axes[1].set_ylabel('PACF')

plt.tight_layout()
plt.savefig('report/images/autocorrelation.png', dpi=300, bbox_inches='tight')
plt.close()

# Save summary statistics
summary_stats = pd.DataFrame({
    'statistic': ['mean', 'std', 'min', '25%', '50%', '75%', 'max'],
    'value': [
        df['load_mw'].mean(),
        df['load_mw'].std(),
        df['load_mw'].min(),
        df['load_mw'].quantile(0.25),
        df['load_mw'].median(),
        df['load_mw'].quantile(0.75),
        df['load_mw'].max()
    ]
})
summary_stats.to_csv('outputs/summary_statistics.csv', index=False)

# Calculate peak load statistics
peak_load = df['load_mw'].max()
peak_time = df['load_mw'].idxmax()
min_load = df['load_mw'].min()
min_time = df['load_mw'].idxmin()

peak_stats = pd.DataFrame({
    'metric': ['peak_load_mw', 'peak_time', 'min_load_mw', 'min_time', 'load_factor'],
    'value': [
        peak_load,
        peak_time,
        min_load,
        min_time,
        df['load_mw'].mean() / peak_load  # Load factor
    ]
})
peak_stats.to_csv('outputs/peak_statistics.csv', index=False)

print("Analysis complete. Figures saved to report/images/")
