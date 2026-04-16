#!/usr/bin/env python3
"""
Energy Systems Load Forecast Analysis
Analyzes 15-minute load data for annual load forecast and reliability assessment.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# Paths
DATA_PATH = 'data/load_15min.csv'
OUTPUT_DIR = 'outputs'
FIGURES_DIR = 'report/images'

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# Load data
print("Loading data...")
df = pd.read_csv(DATA_PATH)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df = df.set_index('timestamp_utc')

print(f"Data shape: {df.shape}")
print(f"Date range: {df.index.min()} to {df.index.max()}")
print(f"Missing values: {df['load_mw'].isna().sum()}")

# Handle missing values - interpolate
df['load_mw'] = df['load_mw'].interpolate(method='linear')
print(f"After interpolation, missing values: {df['load_mw'].isna().sum()}")

# Add time features
df['hour'] = df.index.hour
df['day_of_week'] = df.index.dayofweek
df['day_of_year'] = df.index.dayofyear
df['month'] = df.index.month

# Basic statistics
print("\n=== Basic Statistics ===")
print(df['load_mw'].describe())

# Calculate key metrics
mean_load = df['load_mw'].mean()
std_load = df['load_mw'].std()
min_load = df['load_mw'].min()
max_load = df['load_mw'].max()
median_load = df['load_mw'].median()

print(f"\nMean Load: {mean_load:.2f} MW")
print(f"Std Dev: {std_load:.2f} MW")
print(f"Min Load: {min_load:.2f} MW")
print(f"Max Load: {max_load:.2f} MW")

# Figure 1: Time Series Overview
print("\nGenerating Figure 1...")
fig1, ax1 = plt.subplots(figsize=(14, 5))
ax1.plot(df.index, df['load_mw'], linewidth=0.5, color='steelblue')
ax1.axhline(y=mean_load, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_load:.1f} MW')
ax1.axhline(y=max_load, color='green', linestyle=':', linewidth=2, label=f'Max: {max_load:.1f} MW')
ax1.axhline(y=min_load, color='orange', linestyle=':', linewidth=2, label=f'Min: {min_load:.1f} MW')
ax1.set_xlabel('Date')
ax1.set_ylabel('Load (MW)')
ax1.set_title('15-Minute Load Time Series')
ax1.legend(loc='upper right')
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}/figure1_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 2: Daily Load Profile
print("Generating Figure 2...")
fig2, ax2 = plt.subplots(figsize=(12, 6))
hourly_stats = df.groupby('hour')['load_mw'].agg(['mean', 'std'])
ax2.fill_between(hourly_stats.index, 
                 hourly_stats['mean'] - hourly_stats['std'],
                 hourly_stats['mean'] + hourly_stats['std'],
                 alpha=0.3, color='steelblue')
ax2.plot(hourly_stats.index, hourly_stats['mean'], 'o-', linewidth=2, color='steelblue')
ax2.set_xlabel('Hour of Day')
ax2.set_ylabel('Load (MW)')
ax2.set_title('Average Daily Load Profile')
ax2.set_xticks(range(0, 24, 2))
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}/figure2_daily_profile.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 3: Weekly Pattern
print("Generating Figure 3...")
fig3, ax3 = plt.subplots(figsize=(10, 6))
dow_stats = df.groupby('day_of_week')['load_mw'].agg(['mean', 'std'])
dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
ax3.bar(dow_stats.index, dow_stats['mean'], yerr=dow_stats['std'],
        capsize=5, color='steelblue', alpha=0.7)
ax3.set_xlabel('Day of Week')
ax3.set_ylabel('Load (MW)')
ax3.set_title('Average Load by Day of Week')
ax3.set_xticks(range(7))
ax3.set_xticklabels(dow_names)
ax3.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}/figure3_weekly_pattern.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 4: Load Distribution
print("Generating Figure 4...")
fig4, ax4 = plt.subplots(figsize=(10, 6))
ax4.hist(df['load_mw'], bins=50, color='steelblue', edgecolor='navy', alpha=0.7)
ax4.axvline(x=mean_load, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_load:.1f}')
ax4.axvline(x=median_load, color='green', linestyle='--', linewidth=2, label=f'Median: {median_load:.1f}')
ax4.set_xlabel('Load (MW)')
ax4.set_ylabel('Frequency')
ax4.set_title('Distribution of Load Values')
ax4.legend()
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}/figure4_distribution.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 5: Load Duration Curve
print("Generating Figure 5...")
fig5, ax5 = plt.subplots(figsize=(10, 6))
load_sorted = df['load_mw'].sort_values(ascending=False).reset_index(drop=True)
percent_time = np.arange(1, len(load_sorted) + 1) / len(load_sorted) * 100
ax5.plot(percent_time, load_sorted.values, linewidth=2, color='steelblue')
ax5.axhline(y=max_load, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Peak: {max_load:.1f} MW')
ax5.axhline(y=mean_load, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Mean: {mean_load:.1f} MW')
ax5.set_xlabel('Percentage of Time (%)')
ax5.set_ylabel('Load (MW)')
ax5.set_title('Load Duration Curve')
ax5.legend()
ax5.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}/figure5_duration_curve.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 6: Monthly Pattern
print("Generating Figure 6...")
fig6, ax6 = plt.subplots(figsize=(12, 6))
monthly_stats = df.groupby('month')['load_mw'].agg(['mean', 'min', 'max'])
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
x = np.arange(len(monthly_stats))
width = 0.25
ax6.bar(x - width, monthly_stats['min'], width, label='Min', color='lightblue')
ax6.bar(x, monthly_stats['mean'], width, label='Mean', color='steelblue')
ax6.bar(x + width, monthly_stats['max'], width, label='Max', color='navy')
ax6.set_xlabel('Month')
ax6.set_ylabel('Load (MW)')
ax6.set_title('Monthly Load Statistics')
ax6.set_xticks(x)
ax6.set_xticklabels([month_names[i-1] for i in monthly_stats.index])
ax6.legend()
ax6.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}/figure6_monthly.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 7: Ramp Rates
print("Generating Figure 7...")
df['ramp_rate'] = df['load_mw'].diff() * 4  # MW per hour
ramp_data = df['ramp_rate'].dropna()
max_ramp_up = ramp_data.max()
max_ramp_down = ramp_data.min()
fig7, ax7 = plt.subplots(figsize=(10, 6))
ax7.hist(ramp_data, bins=50, color='coral', edgecolor='darkred', alpha=0.7)
ax7.axvline(x=0, color='black', linestyle='-', linewidth=1)
ax7.axvline(x=max_ramp_up, color='green', linestyle='--', linewidth=2, label=f'Max Up: {max_ramp_up:.1f} MW/h')
ax7.axvline(x=max_ramp_down, color='red', linestyle='--', linewidth=2, label=f'Max Down: {max_ramp_down:.1f} MW/h')
ax7.set_xlabel('Ramp Rate (MW/hour)')
ax7.set_ylabel('Frequency')
ax7.set_title('Distribution of Load Ramp Rates')
ax7.legend()
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}/figure7_ramp_rates.png', dpi=150, bbox_inches='tight')
plt.close()

# Annual Forecast Calculations
intervals_per_day = 96
days_in_year = 365
total_intervals_year = intervals_per_day * days_in_year
energy_per_interval = mean_load * 0.25  # MWh
annual_energy_estimate = energy_per_interval * total_intervals_year
load_factor = mean_load / max_load
peak_load = max_load
peak_time = df['load_mw'].idxmax()
reserve_margin = 0.15
required_capacity = peak_load * (1 + reserve_margin)

# Threshold analysis
threshold_90 = np.percentile(df['load_mw'], 90)
threshold_95 = np.percentile(df['load_mw'], 95)
threshold_99 = np.percentile(df['load_mw'], 99)
total_intervals = len(df)

# Save summary
summary = f"""Energy Systems Load Forecast Analysis - Summary
================================================

Data Overview:
- Period: {df.index.min()} to {df.index.max()}
- Total intervals: {total_intervals}
- Missing values filled: {df['load_mw'].isna().sum()}

Load Statistics:
- Mean Load: {mean_load:.2f} MW
- Std Dev: {std_load:.2f} MW
- Min Load: {min_load:.2f} MW
- Max Load: {max_load:.2f} MW
- Median Load: {median_load:.2f} MW

Annual Forecast:
- Estimated Annual Energy: {annual_energy_estimate/1000:.2f} GWh
- Peak Load: {peak_load:.2f} MW (at {peak_time})
- Load Factor: {load_factor:.3f} ({load_factor*100:.1f}%)
- Required Capacity (15% reserve): {required_capacity:.2f} MW

Reliability Metrics:
- 90th percentile: {threshold_90:.2f} MW
- 95th percentile: {threshold_95:.2f} MW
- 99th percentile: {threshold_99:.2f} MW
- Max Ramp Up: {max_ramp_up:.2f} MW/hour
- Max Ramp Down: {max_ramp_down:.2f} MW/hour
"""

with open(f'{OUTPUT_DIR}/summary.txt', 'w') as f:
    f.write(summary)

print(summary)
print("\n=== Analysis Complete ===")
