"""
Load Forecasting Analysis for Power Systems
============================================
This script performs comprehensive load forecasting analysis using 15-minute interval data.
It includes:
- Data exploration and visualization
- Time series decomposition
- Statistical analysis
- Short-term load forecasting
- Reliability metrics calculation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
print("Loading data...")
script_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.dirname(script_dir)
df = pd.read_csv(os.path.join(workspace_dir, 'data', 'load_15min.csv'))
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df.set_index('timestamp_utc', inplace=True)

print(f"Data loaded: {len(df)} records")
print(f"Date range: {df.index.min()} to {df.index.max()}")
print(f"Load range: {df['load_mw'].min():.2f} - {df['load_mw'].max():.2f} MW")

# Create time-based features
df['hour'] = df.index.hour
df['day_of_week'] = df.index.dayofweek
df['day_of_year'] = df.index.dayofyear
df['month'] = df.index.month
df['quarter'] = df.index.quarter
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
df['date'] = df.index.date

# ============================================================================
# 1. DATA OVERVIEW AND EXPLORATORY ANALYSIS
# ============================================================================

print("\n=== DATA OVERVIEW ===")
print(df['load_mw'].describe())

# Calculate basic statistics
total_records = len(df)
time_span_days = (df.index.max() - df.index.min()).days + 1
avg_load = df['load_mw'].mean()
peak_load = df['load_mw'].max()
min_load = df['load_mw'].min()
load_std = df['load_mw'].std()
cv = load_std / avg_load * 100  # Coefficient of variation

print(f"\nTime span: {time_span_days} days")
print(f"Average load: {avg_load:.2f} MW")
print(f"Peak load: {peak_load:.2f} MW")
print(f"Minimum load: {min_load:.2f} MW")
print(f"Load variability (CV): {cv:.2f}%")

# ============================================================================
# 2. TIME SERIES VISUALIZATION
# ============================================================================

print("\nGenerating time series plots...")

# Full time series
fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(df.index, df['load_mw'], linewidth=0.8, alpha=0.8, color='#2E86AB')
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Load (MW)', fontsize=12)
ax.set_title('15-Minute Load Profile (Full Dataset)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/01_full_load_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()

# Daily patterns
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Hourly pattern
hourly_avg = df.groupby('hour')['load_mw'].mean()
axes[0, 0].plot(hourly_avg.index, hourly_avg.values, marker='o', linewidth=2, markersize=6, color='#A23B72')
axes[0, 0].set_xlabel('Hour of Day', fontsize=11)
axes[0, 0].set_ylabel('Average Load (MW)', fontsize=11)
axes[0, 0].set_title('Average Load by Hour of Day', fontsize=12, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].set_xticks(range(0, 24, 2))

# Day of week pattern
dow_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
dow_avg = df.groupby('day_of_week')['load_mw'].mean()
axes[0, 1].bar(range(7), dow_avg.values, color='#F18F01', edgecolor='black', alpha=0.8)
axes[0, 1].set_xlabel('Day of Week', fontsize=11)
axes[0, 1].set_ylabel('Average Load (MW)', fontsize=11)
axes[0, 1].set_title('Average Load by Day of Week', fontsize=12, fontweight='bold')
axes[0, 1].set_xticks(range(7))
axes[0, 1].set_xticklabels(dow_labels)
axes[0, 1].grid(True, alpha=0.3, axis='y')

# Hourly boxplot by day of week
hourly_dow = df.groupby(['day_of_week', 'hour'])['load_mw'].mean().reset_index()
for dow in range(7):
    subset = hourly_dow[hourly_dow['day_of_week'] == dow]
    axes[1, 0].plot(subset['hour'], subset['load_mw'], 
                    label=dow_labels[dow], linewidth=1.5, alpha=0.8)
axes[1, 0].set_xlabel('Hour of Day', fontsize=11)
axes[1, 0].set_ylabel('Average Load (MW)', fontsize=11)
axes[1, 0].set_title('Hourly Load Patterns by Day of Week', fontsize=12, fontweight='bold')
axes[1, 0].legend(loc='upper right', fontsize=8)
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].set_xticks(range(0, 24, 2))

# Load distribution histogram
axes[1, 1].hist(df['load_mw'], bins=40, color='#C73E1D', edgecolor='black', alpha=0.7)
axes[1, 1].axvline(avg_load, color='black', linestyle='--', linewidth=2, label=f'Mean: {avg_load:.1f} MW')
axes[1, 1].axvline(peak_load, color='red', linestyle='--', linewidth=2, label=f'Peak: {peak_load:.1f} MW')
axes[1, 1].set_xlabel('Load (MW)', fontsize=11)
axes[1, 1].set_ylabel('Frequency', fontsize=11)
axes[1, 1].set_title('Load Distribution', fontsize=12, fontweight='bold')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/02_load_patterns.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================================
# 3. DAILY LOAD CURVES
# ============================================================================

print("Generating daily load curves...")

# Create daily load curves for each day
daily_data = df.groupby(['date', 'hour'])['load_mw'].mean().reset_index()
daily_pivot = daily_data.pivot(index='hour', columns='date', values='load_mw')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# All daily curves
colors = plt.cm.viridis(np.linspace(0, 1, len(daily_pivot.columns)))
for i, col in enumerate(daily_pivot.columns):
    axes[0].plot(daily_pivot.index, daily_pivot[col], alpha=0.7, 
                 color=colors[i], linewidth=1.5, label=str(col))
axes[0].plot(daily_pivot.index, daily_pivot.mean(axis=1), color='red', 
             linewidth=3, label='Average', linestyle='--')
axes[0].set_xlabel('Hour of Day', fontsize=11)
axes[0].set_ylabel('Load (MW)', fontsize=11)
axes[0].set_title('Daily Load Curves (All Days)', fontsize=12, fontweight='bold')
axes[0].legend(loc='upper left', fontsize=8)
axes[0].grid(True, alpha=0.3)
axes[0].set_xticks(range(0, 24, 2))

# Weekend vs Weekday
weekday_data = df[df['is_weekend'] == 0].groupby('hour')['load_mw'].mean()
weekend_data = df[df['is_weekend'] == 1].groupby('hour')['load_mw'].mean()

axes[1].plot(weekday_data.index, weekday_data.values, marker='o', linewidth=2, 
             label='Weekday', color='#2E86AB')
if len(weekend_data) > 0:
    axes[1].plot(weekend_data.index, weekend_data.values, marker='s', linewidth=2, 
                 label='Weekend', color='#F18F01')
axes[1].set_xlabel('Hour of Day', fontsize=11)
axes[1].set_ylabel('Load (MW)', fontsize=11)
axes[1].set_title('Weekday vs Weekend Load Patterns', fontsize=12, fontweight='bold')
axes[1].legend()
axes[1].grid(True, alpha=0.3)
axes[1].set_xticks(range(0, 24, 2))

plt.tight_layout()
plt.savefig('report/images/03_daily_load_curves.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================================
# 4. LOAD VARIABILITY AND STATISTICS
# ============================================================================

print("Calculating load variability metrics...")

# Calculate daily statistics
daily_stats = df.groupby('date').agg({
    'load_mw': ['min', 'max', 'mean', 'std']
}).reset_index()
daily_stats.columns = ['date', 'min_load', 'max_load', 'avg_load', 'std_load']
daily_stats['load_range'] = daily_stats['max_load'] - daily_stats['min_load']
daily_stats['cv'] = daily_stats['std_load'] / daily_stats['avg_load'] * 100
daily_stats['date'] = pd.to_datetime(daily_stats['date'])

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Daily peak load
axes[0, 0].plot(daily_stats['date'], daily_stats['max_load'], color='#C73E1D', 
                linewidth=2, marker='o', markersize=6)
axes[0, 0].set_xlabel('Date', fontsize=11)
axes[0, 0].set_ylabel('Peak Load (MW)', fontsize=11)
axes[0, 0].set_title('Daily Peak Load Trend', fontsize=12, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)

# Daily average load
axes[0, 1].plot(daily_stats['date'], daily_stats['avg_load'], color='#2E86AB', 
                linewidth=2, marker='o', markersize=6)
axes[0, 1].set_xlabel('Date', fontsize=11)
axes[0, 1].set_ylabel('Average Load (MW)', fontsize=11)
axes[0, 1].set_title('Daily Average Load Trend', fontsize=12, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3)

# Daily load range
axes[1, 0].plot(daily_stats['date'], daily_stats['load_range'], color='#F18F01', 
                linewidth=2, marker='o', markersize=6)
axes[1, 0].set_xlabel('Date', fontsize=11)
axes[1, 0].set_ylabel('Load Range (MW)', fontsize=11)
axes[1, 0].set_title('Daily Load Range (Max - Min)', fontsize=12, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3)

# Daily coefficient of variation
axes[1, 1].plot(daily_stats['date'], daily_stats['cv'], color='#A23B72', 
                linewidth=2, marker='o', markersize=6)
axes[1, 1].set_xlabel('Date', fontsize=11)
axes[1, 1].set_ylabel('Coefficient of Variation (%)', fontsize=11)
axes[1, 1].set_title('Daily Load Variability (CV)', fontsize=12, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/04_daily_statistics.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================================
# 5. ANNUAL LOAD FORECASTING (Based on 7-day pattern projection)
# ============================================================================

print("\nPerforming annual load forecasting...")

# Since we only have 7 days, we'll use pattern-based forecasting
# Calculate average daily profile and project for the year

# Daily average profile (15-min intervals)
daily_profile = df.groupby(df.index.time)['load_mw'].mean()

# Day-of-week patterns
dow_profiles = {}
for dow in range(7):
    dow_data = df[df['day_of_week'] == dow]
    if len(dow_data) > 0:
        dow_profiles[dow] = dow_data.groupby(dow_data.index.time)['load_mw'].mean()

# Calculate weekly statistics
weekly_avg = df['load_mw'].mean()
weekly_peak = df['load_mw'].max()
weekly_min = df['load_mw'].min()

# Project annual load based on observed patterns
# Assume 52 weeks with similar patterns
projected_annual_energy = weekly_avg * 24 * 7 * 52  # MWh
projected_annual_peak = weekly_peak * 1.05  # Add 5% margin for annual peak
projected_annual_avg = weekly_avg

print(f"\nAnnual Projection (based on 7-day sample):")
print(f"Projected Annual Energy: {projected_annual_energy/1000:.2f} GWh")
print(f"Projected Annual Peak: {projected_annual_peak:.2f} MW")
print(f"Projected Annual Average: {projected_annual_avg:.2f} MW")

# Create a synthetic annual forecast visualization
# Generate 365 days of forecast based on weekly pattern
from datetime import datetime, timedelta

start_date = datetime(2026, 1, 1)
forecast_dates = [start_date + timedelta(days=i) for i in range(365)]
forecast_dow = [d.weekday() for d in forecast_dates]

# Use average daily load for each day type
forecast_daily_avg = []
for dow in forecast_dow:
    if dow in dow_profiles:
        forecast_daily_avg.append(dow_profiles[dow].mean())
    else:
        forecast_daily_avg.append(weekly_avg)

# Add some seasonal variation (simplified sine wave for demonstration)
# In reality, this would use historical seasonal patterns
seasonal_factor = [1 + 0.1 * np.sin(2 * np.pi * i / 365) for i in range(365)]
forecast_daily_avg_seasonal = [forecast_daily_avg[i] * seasonal_factor[i] for i in range(365)]

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Annual forecast - daily average
axes[0].plot(forecast_dates[:90], forecast_daily_avg_seasonal[:90], 
             color='#2E86AB', linewidth=1.5, label='Q1 Forecast')
axes[0].plot(forecast_dates[90:180], forecast_daily_avg_seasonal[90:180], 
             color='#F18F01', linewidth=1.5, label='Q2 Forecast')
axes[0].plot(forecast_dates[180:270], forecast_daily_avg_seasonal[180:270], 
             color='#C73E1D', linewidth=1.5, label='Q3 Forecast')
axes[0].plot(forecast_dates[270:], forecast_daily_avg_seasonal[270:], 
             color='#A23B72', linewidth=1.5, label='Q4 Forecast')
axes[0].axhline(weekly_avg, color='gray', linestyle='--', linewidth=2, 
                label=f'Observed Avg: {weekly_avg:.1f} MW')
axes[0].set_xlabel('Date', fontsize=11)
axes[0].set_ylabel('Projected Daily Average Load (MW)', fontsize=11)
axes[0].set_title('Annual Load Forecast - Daily Average (Projected)', fontsize=12, fontweight='bold')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Monthly aggregation
monthly_forecast = []
month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
idx = 0
for days in days_in_month:
    monthly_forecast.append(np.mean(forecast_daily_avg_seasonal[idx:idx+days]))
    idx += days

axes[1].bar(range(1, 13), monthly_forecast, color='#2E86AB', edgecolor='black', alpha=0.8)
axes[1].axhline(weekly_avg, color='red', linestyle='--', linewidth=2, 
                label=f'Observed Avg: {weekly_avg:.1f} MW')
axes[1].set_xlabel('Month', fontsize=11)
axes[1].set_ylabel('Projected Monthly Average Load (MW)', fontsize=11)
axes[1].set_title('Annual Load Forecast - Monthly Aggregation', fontsize=12, fontweight='bold')
axes[1].set_xticks(range(1, 13))
axes[1].set_xticklabels(month_labels)
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/05_annual_forecast.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================================
# 6. INTRADAY PATTERN ANALYSIS
# ============================================================================

print("\nPerforming intraday pattern analysis...")

# 15-minute interval analysis
interval_stats = df.groupby(df.index.time)['load_mw'].agg(['mean', 'std', 'min', 'max'])

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Average load by 15-min interval
times = [t.strftime('%H:%M') for t in interval_stats.index]
axes[0].plot(range(len(times)), interval_stats['mean'], color='#2E86AB', linewidth=2)
axes[0].fill_between(range(len(times)), 
                      interval_stats['mean'] - interval_stats['std'],
                      interval_stats['mean'] + interval_stats['std'],
                      alpha=0.3, color='#2E86AB', label='±1 Std Dev')
axes[0].set_xlabel('Time of Day', fontsize=11)
axes[0].set_ylabel('Load (MW)', fontsize=11)
axes[0].set_title('Average Load by 15-Minute Interval', fontsize=12, fontweight='bold')
axes[0].set_xticks(range(0, len(times), 8))
axes[0].set_xticklabels([times[i] for i in range(0, len(times), 8)], rotation=45)
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Load variability by time of day
axes[1].plot(range(len(times)), interval_stats['std'], color='#C73E1D', linewidth=2, marker='o', markersize=3)
axes[1].set_xlabel('Time of Day', fontsize=11)
axes[1].set_ylabel('Standard Deviation (MW)', fontsize=11)
axes[1].set_title('Load Variability by 15-Minute Interval', fontsize=12, fontweight='bold')
axes[1].set_xticks(range(0, len(times), 8))
axes[1].set_xticklabels([times[i] for i in range(0, len(times), 8)], rotation=45)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/06_intraday_patterns.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================================
# 7. RELIABILITY METRICS
# ============================================================================

print("\nCalculating reliability metrics...")

# Load duration curve
sorted_load = np.sort(df['load_mw'].values)[::-1]
duration = np.arange(1, len(sorted_load) + 1) / len(sorted_load) * 100

# Calculate key percentiles
p50 = np.percentile(df['load_mw'], 50)
p90 = np.percentile(df['load_mw'], 90)
p95 = np.percentile(df['load_mw'], 95)
p99 = np.percentile(df['load_mw'], 99)

# Capacity metrics (assuming peak + 10% reserve)
required_capacity = peak_load * 1.10
capacity_factor = avg_load / required_capacity * 100
load_factor = avg_load / peak_load * 100

print(f"\nReliability Metrics:")
print(f"Load Factor: {load_factor:.2f}%")
print(f"Capacity Factor (with 10% reserve): {capacity_factor:.2f}%")
print(f"P50 Load: {p50:.2f} MW")
print(f"P90 Load: {p90:.2f} MW")
print(f"P95 Load: {p95:.2f} MW")
print(f"P99 Load: {p99:.2f} MW")

# Load duration curve visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Full load duration curve
axes[0].plot(duration, sorted_load, color='#2E86AB', linewidth=2)
axes[0].axhline(peak_load, color='red', linestyle='--', linewidth=1.5, label=f'Peak: {peak_load:.1f} MW')
axes[0].axhline(avg_load, color='green', linestyle='--', linewidth=1.5, label=f'Average: {avg_load:.1f} MW')
axes[0].axhline(p90, color='orange', linestyle='--', linewidth=1.5, label=f'P90: {p90:.1f} MW')
axes[0].set_xlabel('Duration (%)', fontsize=11)
axes[0].set_ylabel('Load (MW)', fontsize=11)
axes[0].set_title('Load Duration Curve', fontsize=12, fontweight='bold')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Zoomed view (top 20%)
top_20_idx = int(len(sorted_load) * 0.2)
axes[1].plot(duration[:top_20_idx], sorted_load[:top_20_idx], color='#C73E1D', linewidth=2)
axes[1].axhline(peak_load, color='red', linestyle='--', linewidth=1.5, label=f'Peak: {peak_load:.1f} MW')
axes[1].axhline(p95, color='orange', linestyle='--', linewidth=1.5, label=f'P95: {p95:.1f} MW')
axes[1].axhline(p99, color='purple', linestyle='--', linewidth=1.5, label=f'P99: {p99:.1f} MW')
axes[1].set_xlabel('Duration (%)', fontsize=11)
axes[1].set_ylabel('Load (MW)', fontsize=11)
axes[1].set_title('Load Duration Curve (Top 20%)', fontsize=12, fontweight='bold')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/07_load_duration_curve.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================================
# 8. FORECAST ACCURACY ASSESSMENT (Day-ahead validation)
# ============================================================================

print("\nAssessing forecast accuracy...")

# Use last day as test set for validation
test_days = 1
train_data = daily_stats.iloc[:-test_days]
test_data = daily_stats.iloc[-test_days:]

# Simple average forecast
avg_forecast = train_data['avg_load'].mean()

# Day-of-week based forecast
last_train_dow = pd.to_datetime(train_data['date'].iloc[-1]).weekday()
test_dow = pd.to_datetime(test_data['date'].iloc[0]).weekday()

# Calculate errors
actual = test_data['avg_load'].values
mae = np.abs(avg_forecast - actual[0])
mape = mae / actual[0] * 100

print(f"\nForecast Accuracy (Last day):")
print(f"Simple Average Forecast - MAE: {mae:.2f} MW, MAPE: {mape:.2f}%")

# Validation visualization
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(train_data['date'], train_data['avg_load'], 'o-', color='#2E86AB', 
        linewidth=2, markersize=6, label='Training Data')
ax.plot(test_data['date'], actual, 'o', color='green', 
        markersize=10, label='Actual')
ax.plot(test_data['date'], [avg_forecast], 's', color='#C73E1D', 
        markersize=10, label=f'Forecast: {avg_forecast:.1f} MW')
ax.axvline(test_data['date'].iloc[0], color='gray', linestyle=':', linewidth=2, alpha=0.7)
ax.set_xlabel('Date', fontsize=11)
ax.set_ylabel('Average Load (MW)', fontsize=11)
ax.set_title('Forecast Validation (Day-ahead)', fontsize=12, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/08_forecast_validation.png', dpi=150, bbox_inches='tight')
plt.close()

# ============================================================================
# 9. SUMMARY STATISTICS TABLE
# ============================================================================

print("\nGenerating summary statistics...")

# Annual summary
annual_summary = {
    'Metric': [
        'Total Records',
        'Time Span (Days)',
        'Average Load (MW)',
        'Peak Load (MW)',
        'Minimum Load (MW)',
        'Load Range (MW)',
        'Standard Deviation (MW)',
        'Coefficient of Variation (%)',
        'Load Factor (%)',
        'P90 Load (MW)',
        'P95 Load (MW)',
        'P99 Load (MW)',
        'Required Capacity (MW)*',
        'Capacity Factor (%)',
        'Projected Annual Energy (GWh)',
        'Projected Annual Peak (MW)'
    ],
    'Value': [
        f"{total_records:,}",
        f"{time_span_days}",
        f"{avg_load:.2f}",
        f"{peak_load:.2f}",
        f"{min_load:.2f}",
        f"{peak_load - min_load:.2f}",
        f"{load_std:.2f}",
        f"{cv:.2f}",
        f"{load_factor:.2f}",
        f"{p90:.2f}",
        f"{p95:.2f}",
        f"{p99:.2f}",
        f"{required_capacity:.2f}",
        f"{capacity_factor:.2f}",
        f"{projected_annual_energy/1000:.2f}",
        f"{projected_annual_peak:.2f}"
    ]
}

summary_df = pd.DataFrame(annual_summary)
summary_df.to_csv('outputs/annual_summary.csv', index=False)
print("\nSummary saved to outputs/annual_summary.csv")

# Daily summary
daily_summary = df.groupby('date').agg({
    'load_mw': ['count', 'mean', 'max', 'min', 'std']
}).round(2)
daily_summary.columns = ['Records', 'Avg_Load_MW', 'Peak_Load_MW', 'Min_Load_MW', 'Std_MW']
daily_summary.to_csv('outputs/daily_summary.csv')
print("Daily summary saved to outputs/daily_summary.csv")

# Hourly summary
hourly_summary = df.groupby('hour')['load_mw'].agg(['mean', 'max', 'min', 'std']).round(2)
hourly_summary.to_csv('outputs/hourly_summary.csv')
print("Hourly summary saved to outputs/hourly_summary.csv")

# Forecast summary
forecast_summary = pd.DataFrame({
    'Month': range(1, 13),
    'Month_Name': month_labels,
    'Projected_Avg_MW': [f"{x:.2f}" for x in monthly_forecast]
})
forecast_summary.to_csv('outputs/annual_forecast.csv', index=False)
print("Forecast saved to outputs/annual_forecast.csv")

print("\n=== ANALYSIS COMPLETE ===")
print(f"Generated 8 figures in report/images/")
print(f"Generated 4 CSV files in outputs/")
