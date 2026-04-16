import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read and prepare data
data_path = '../data/load_15min.csv'
df = pd.read_csv(data_path)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df.set_index('timestamp_utc', inplace=True)

# Impute missing values using forward fill then backward fill
df['load_mw'] = df['load_mw'].fillna(method='ffill').fillna(method='bfill')

# Extract time features
df['hour'] = df.index.hour
df['minute'] = df.index.minute
df['day_of_week'] = df.index.dayofweek
df['day_name'] = df.index.day_name()
df['date'] = df.index.date

print("=== RELIABILITY ANALYSIS ===\n")

# ====== BASIC STATISTICS ======
print("1. BASIC LOAD STATISTICS")
print("=" * 50)
print(f"Total observations: {len(df)}")
print(f"Time period: {df.index.min()} to {df.index.max()}")
print(f"Duration: {(df.index.max() - df.index.min()).days} days")
print(f"\nLoad Statistics (MW):")
print(f"  Mean: {df['load_mw'].mean():.2f}")
print(f"  Median: {df['load_mw'].median():.2f}")
print(f"  Std Dev: {df['load_mw'].std():.2f}")
print(f"  Minimum: {df['load_mw'].min():.2f}")
print(f"  Maximum: {df['load_mw'].max():.2f}")
print(f"  Range: {df['load_mw'].max() - df['load_mw'].min():.2f}")

# ====== RELIABILITY METRICS ======
print("\n2. RELIABILITY METRICS")
print("=" * 50)

# Load Factor = Average Load / Peak Load
load_factor = df['load_mw'].mean() / df['load_mw'].max() * 100
print(f"Load Factor: {load_factor:.1f}%")

# Peak-to-Average Ratio
peak_to_avg = df['load_mw'].max() / df['load_mw'].mean()
print(f"Peak-to-Average Ratio: {peak_to_avg:.2f}")

# Daily peak statistics
daily_peaks = df.groupby('date')['load_mw'].max()
daily_means = df.groupby('date')['load_mw'].mean()
daily_mins = df.groupby('date')['load_mw'].min()

print(f"\nDaily Peak Statistics:")
print(f"  Average daily peak: {daily_peaks.mean():.2f} MW")
print(f"  Maximum daily peak: {daily_peaks.max():.2f} MW")
print(f"  Minimum daily peak: {daily_peaks.min():.2f} MW")
print(f"  Std of daily peaks: {daily_peaks.std():.2f} MW")

# ====== LOAD DURATION ANALYSIS ======
print("\n3. LOAD DURATION ANALYSIS")
print("=" * 50)

# Sort load values in descending order
sorted_load = np.sort(df['load_mw'])[::-1]

# Calculate percentiles
percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
percentile_values = np.percentile(df['load_mw'], percentiles)

print("Load Percentiles (MW):")
for p, val in zip(percentiles, percentile_values):
    print(f"  {p}th percentile: {val:.2f}")

# Time above certain thresholds
thresholds = [110, 115, 120, 125, 130]
print("\nTime Above Thresholds:")
for thresh in thresholds:
    time_above = (df['load_mw'] > thresh).sum() / len(df) * 100
    print(f"  Above {thresh} MW: {time_above:.1f}% of time")

# ====== DAILY AND WEEKLY PATTERNS ======
print("\n4. SEASONAL PATTERNS")
print("=" * 50)

# Hourly averages
hourly_avg = df.groupby('hour')['load_mw'].mean()
hourly_std = df.groupby('hour')['load_mw'].std()

print("\nHourly Load Pattern (Average ± Std Dev):")
for hour in range(24):
    print(f"  {hour:02d}:00 - {hourly_avg[hour]:.2f} ± {hourly_std[hour]:.2f} MW")

# Day of week averages
dow_avg = df.groupby('day_name')['load_mw'].mean()
dow_std = df.groupby('day_name')['load_mw'].std()

print("\nDay-of-Week Load Pattern:")
for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
    if day in dow_avg.index:
        print(f"  {day[:3]}: {dow_avg[day]:.2f} ± {dow_std[day]:.2f} MW")

# ====== ANNUAL FORECAST (SIMPLIFIED) ======
print("\n5. ANNUAL FORECAST PROJECTION")
print("=" * 50)

# Based on one week of data, we can project annual patterns
# Assumptions:
# 1. Weekly pattern repeats throughout the year
# 2. Seasonal variations are not captured (need more data)
# 3. Growth trend is not captured (need historical data)

# Calculate weekly statistics
weekly_avg = df['load_mw'].mean()
weekly_peak = df['load_mw'].max()
weekly_min = df['load_mw'].min()

# For annual forecast, we assume similar patterns
# Conservative estimate: use observed weekly pattern
annual_avg = weekly_avg  # Assuming no growth
annual_peak = weekly_peak * 1.1  # 10% margin for annual peak
annual_min = weekly_min

print(f"\nBased on one week of data (conservative estimates):")
print(f"  Projected annual average load: {annual_avg:.2f} MW")
print(f"  Projected annual peak load: {annual_peak:.2f} MW (+10% margin)")
print(f"  Projected annual minimum load: {annual_min:.2f} MW")
print(f"  Projected load factor: {annual_avg/annual_peak*100:.1f}%")

# Calculate capacity requirements
# Assuming 15% reserve margin for reliability
required_capacity = annual_peak * 1.15
print(f"\nCapacity Planning (15% reserve margin):")
print(f"  Required capacity: {required_capacity:.2f} MW")
print(f"  Reserve margin: {required_capacity - annual_peak:.2f} MW")

# ====== VISUALIZATIONS ======
print("\n6. GENERATING VISUALIZATIONS...")

# 1. Load Duration Curve
plt.figure(figsize=(12, 6))
plt.plot(sorted_load, 'b-', linewidth=2)
plt.title('Load Duration Curve')
plt.xlabel('Number of Intervals (sorted by load)')
plt.ylabel('Load (MW)')
plt.grid(True, alpha=0.3)

# Add percentile markers
for p, val in zip([10, 50, 90], np.percentile(df['load_mw'], [10, 50, 90])):
    plt.axhline(y=val, color='r', linestyle='--', alpha=0.5)
    plt.text(0, val, f' {p}th: {val:.1f} MW', verticalalignment='bottom')

plt.tight_layout()
plt.savefig('../report/images/load_duration_curve.png', dpi=300)
plt.close()

# 2. Hourly load profile with confidence intervals
plt.figure(figsize=(12, 6))
plt.errorbar(hourly_avg.index, hourly_avg.values, 
             yerr=hourly_std.values, 
             fmt='o-', linewidth=2, capsize=5)
plt.title('Average Hourly Load Profile with Standard Deviation')
plt.xlabel('Hour of Day')
plt.ylabel('Load (MW)')
plt.xticks(range(0, 24, 2))
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/hourly_profile.png', dpi=300)
plt.close()

# 3. Boxplot by day of week
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
plt.figure(figsize=(12, 6))
box_data = [df[df['day_name'] == day]['load_mw'].values for day in day_order]
plt.boxplot(box_data, labels=[day[:3] for day in day_order])
plt.title('Load Distribution by Day of Week')
plt.xlabel('Day of Week')
plt.ylabel('Load (MW)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/dow_boxplot.png', dpi=300)
plt.close()

# 4. Time series with peak identification
plt.figure(figsize=(14, 6))
plt.plot(df.index, df['load_mw'], 'b-', alpha=0.7, linewidth=1)

# Identify peaks (local maxima)
from scipy.signal import find_peaks
peaks, _ = find_peaks(df['load_mw'], height=120, distance=4)  # distance=4 = 1 hour
plt.plot(df.index[peaks], df['load_mw'].iloc[peaks], 'ro', 
         markersize=8, label=f'Peaks (>120 MW, {len(peaks)} found)')

plt.title('Load Time Series with Peak Identification')
plt.xlabel('Timestamp')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/peak_identification.png', dpi=300)
plt.close()

# 5. Reliability dashboard
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Subplot 1: Histogram with thresholds
axes[0, 0].hist(df['load_mw'], bins=30, edgecolor='black', alpha=0.7)
for thresh in [115, 125]:
    axes[0, 0].axvline(x=thresh, color='r', linestyle='--', alpha=0.7)
    axes[0, 0].text(thresh, axes[0, 0].get_ylim()[1]*0.9, f' {thresh} MW', 
                   rotation=90, verticalalignment='top')
axes[0, 0].set_title('Load Distribution with Reliability Thresholds')
axes[0, 0].set_xlabel('Load (MW)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].grid(True, alpha=0.3)

# Subplot 2: Daily peaks
daily_dates = [pd.Timestamp(date) for date in daily_peaks.index]
axes[0, 1].bar(daily_dates, daily_peaks.values, width=0.8, alpha=0.7)
axes[0, 1].axhline(y=daily_peaks.mean(), color='r', linestyle='--', label=f'Mean: {daily_peaks.mean():.1f} MW')
axes[0, 1].set_title('Daily Peak Loads')
axes[0, 1].set_xlabel('Date')
axes[0, 1].set_ylabel('Peak Load (MW)')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)
plt.setp(axes[0, 1].xaxis.get_majorticklabels(), rotation=45)

# Subplot 3: Time above thresholds
threshold_percentages = [(df['load_mw'] > thresh).sum() / len(df) * 100 for thresh in thresholds]
axes[1, 0].bar(range(len(thresholds)), threshold_percentages, alpha=0.7)
axes[1, 0].set_title('Percentage of Time Above Load Thresholds')
axes[1, 0].set_xlabel('Threshold (MW)')
axes[1, 0].set_ylabel('Time Above Threshold (%)')
axes[1, 0].set_xticks(range(len(thresholds)))
axes[1, 0].set_xticklabels(thresholds)
for i, pct in enumerate(threshold_percentages):
    axes[1, 0].text(i, pct + 1, f'{pct:.1f}%', ha='center')
axes[1, 0].grid(True, alpha=0.3)

# Subplot 4: Load factor and peak-to-average
metrics = ['Load Factor', 'Peak-to-Average']
values = [load_factor, peak_to_avg]
colors = ['green', 'orange']
axes[1, 1].bar(metrics, values, color=colors, alpha=0.7)
axes[1, 1].set_title('Key Reliability Metrics')
axes[1, 1].set_ylabel('Value')
for i, (metric, value) in enumerate(zip(metrics, values)):
    if metric == 'Load Factor':
        axes[1, 1].text(i, value + 2, f'{value:.1f}%', ha='center')
    else:
        axes[1, 1].text(i, value + 0.05, f'{value:.2f}', ha='center')
axes[1, 1].grid(True, alpha=0.3)

plt.suptitle('Reliability Analysis Dashboard', fontsize=16)
plt.tight_layout()
plt.savefig('../report/images/reliability_dashboard.png', dpi=300)
plt.close()

print("Visualizations saved to report/images/")

# ====== SAVE RESULTS ======
# Save reliability metrics
reliability_metrics = pd.DataFrame({
    'metric': ['mean_load', 'peak_load', 'min_load', 'load_factor', 'peak_to_avg', 
               'daily_peak_mean', 'daily_peak_max', 'daily_peak_min',
               'required_capacity', 'reserve_margin'],
    'value': [df['load_mw'].mean(), df['load_mw'].max(), df['load_mw'].min(),
              load_factor, peak_to_avg, daily_peaks.mean(), daily_peaks.max(),
              daily_peaks.min(), required_capacity, required_capacity - annual_peak],
    'unit': ['MW', 'MW', 'MW', '%', 'ratio', 'MW', 'MW', 'MW', 'MW', 'MW']
})
reliability_metrics.to_csv('../outputs/reliability_metrics.csv', index=False)

# Save percentile data
percentile_df = pd.DataFrame({
    'percentile': percentiles,
    'load_mw': percentile_values
})
percentile_df.to_csv('../outputs/load_percentiles.csv', index=False)

# Save hourly profile
hourly_profile_df = pd.DataFrame({
    'hour': hourly_avg.index,
    'mean_load': hourly_avg.values,
    'std_load': hourly_std.values
})
hourly_profile_df.to_csv('../outputs/hourly_profile.csv', index=False)

print("\nResults saved to outputs/ directory")
print("\n=== ANALYSIS COMPLETE ===")