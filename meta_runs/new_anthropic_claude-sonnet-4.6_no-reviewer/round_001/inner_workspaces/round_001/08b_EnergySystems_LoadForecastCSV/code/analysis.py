#!/usr/bin/env python3
"""
Annual Load Forecast Analysis
Energy Systems - 15-minute Load Series
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# 1. LOAD & CLEAN DATA
# ─────────────────────────────────────────────
df = pd.read_csv('data/load_15min.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
df = df.sort_values('timestamp_utc').reset_index(drop=True)
df['load_mw'] = pd.to_numeric(df['load_mw'], errors='coerce')

print("=" * 60)
print("DATA OVERVIEW")
print("=" * 60)
print(f"Total records: {len(df)}")
print(f"Date range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Missing values: {df['load_mw'].isna().sum()} ({df['load_mw'].isna().mean()*100:.1f}%)")
print(f"\nLoad statistics (MW):")
print(df['load_mw'].describe().round(3))

# Interpolate missing values (linear)
df['load_mw_raw'] = df['load_mw'].copy()
df['load_mw'] = df['load_mw'].interpolate(method='linear', limit_direction='both')
print(f"\nAfter interpolation - missing: {df['load_mw'].isna().sum()}")

# ─────────────────────────────────────────────
# 2. FEATURE ENGINEERING
# ─────────────────────────────────────────────
df['hour'] = df['timestamp_utc'].dt.hour
df['minute'] = df['timestamp_utc'].dt.minute
df['hour_frac'] = df['hour'] + df['minute'] / 60.0
df['day_of_week'] = df['timestamp_utc'].dt.dayofweek  # 0=Mon, 6=Sun
df['day_name'] = df['timestamp_utc'].dt.day_name()
df['date'] = df['timestamp_utc'].dt.date
df['week'] = df['timestamp_utc'].dt.isocalendar().week.astype(int)
df['is_weekend'] = df['day_of_week'] >= 5

# ─────────────────────────────────────────────
# 3. SUMMARY STATISTICS
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY STATISTICS")
print("=" * 60)

# Daily stats
daily = df.groupby('date')['load_mw'].agg(['mean', 'max', 'min', 'std'])
daily.columns = ['mean_mw', 'peak_mw', 'min_mw', 'std_mw']
daily['energy_mwh'] = daily['mean_mw'] * 24  # daily energy
print("\nDaily load summary:")
print(daily.round(2))

# Hourly profile
hourly_profile = df.groupby('hour')['load_mw'].agg(['mean', 'max', 'min', 'std'])
hourly_profile.columns = ['mean_mw', 'max_mw', 'min_mw', 'std_mw']
print("\nHourly load profile (mean MW):")
print(hourly_profile['mean_mw'].round(2))

# Weekday vs weekend
print("\nWeekday vs Weekend:")
print(df.groupby('is_weekend')['load_mw'].describe().round(2))

# Peak demand
peak_idx = df['load_mw'].idxmax()
peak_row = df.loc[peak_idx]
print(f"\nSystem Peak: {peak_row['load_mw']:.3f} MW at {peak_row['timestamp_utc']}")

min_idx = df['load_mw'].idxmin()
min_row = df.loc[min_idx]
print(f"System Minimum: {min_row['load_mw']:.3f} MW at {min_row['timestamp_utc']}")

# Load factor
load_factor = df['load_mw'].mean() / df['load_mw'].max()
print(f"\nLoad Factor: {load_factor:.4f} ({load_factor*100:.2f}%)")

# ─────────────────────────────────────────────
# 4. ANNUAL FORECAST EXTRAPOLATION
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("ANNUAL FORECAST")
print("=" * 60)

# Use observed week as representative sample
weekly_energy_mwh = daily['energy_mwh'].sum()
annual_energy_forecast = weekly_energy_mwh * 52  # 52 weeks
print(f"Observed week energy: {weekly_energy_mwh:.1f} MWh")
print(f"Annual energy forecast (52-week extrapolation): {annual_energy_forecast:.1f} MWh")
print(f"Annual energy forecast: {annual_energy_forecast/1000:.2f} GWh")

# Peak demand forecast
observed_peak = df['load_mw'].max()
print(f"\nObserved peak demand: {observed_peak:.2f} MW")

# Seasonal adjustment factors (typical utility assumptions)
# Winter peak systems: summer ~85%, spring/fall ~75% of winter peak
seasonal_factors = {
    'Winter (Jan-Feb)': 1.00,
    'Spring (Mar-May)': 0.78,
    'Summer (Jun-Aug)': 0.88,
    'Fall (Sep-Nov)': 0.80,
    'Winter (Dec)': 0.95
}
print("\nSeasonal peak demand forecast (based on observed peak):")
for season, factor in seasonal_factors.items():
    print(f"  {season}: {observed_peak * factor:.2f} MW (factor={factor:.2f})")

# Monthly energy forecast
days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# Seasonal load shape (relative to observed week mean)
monthly_load_factors = [
    1.05, 1.03, 0.95, 0.88, 0.90, 0.95,
    1.00, 0.98, 0.92, 0.90, 0.93, 1.02
]
base_daily_energy = daily['energy_mwh'].mean()
monthly_energy = []
for i, (days, lf) in enumerate(zip(days_per_month, monthly_load_factors)):
    monthly_energy.append(base_daily_energy * days * lf)

monthly_df = pd.DataFrame({
    'Month': month_names,
    'Days': days_per_month,
    'Load_Factor': monthly_load_factors,
    'Energy_MWh': monthly_energy,
    'Peak_MW': [observed_peak * lf for lf in monthly_load_factors]
})
print("\nMonthly energy and peak forecast:")
print(monthly_df.to_string(index=False))
print(f"\nTotal annual energy: {sum(monthly_energy):.1f} MWh = {sum(monthly_energy)/1000:.2f} GWh")

# ─────────────────────────────────────────────
# 5. RELIABILITY METRICS
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("RELIABILITY METRICS")
print("=" * 60)

# Load duration curve
load_sorted = np.sort(df['load_mw'].values)[::-1]
hours_pct = np.linspace(0, 100, len(load_sorted))

# Percentile thresholds
for pct in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    val = np.percentile(df['load_mw'], 100 - pct)
    print(f"  Top {pct:2d}% of hours: load >= {val:.2f} MW")

# Reserve margin analysis
print("\nReserve Margin Analysis:")
for reserve_pct in [10, 15, 20, 25]:
    required_capacity = observed_peak * (1 + reserve_pct / 100)
    print(f"  {reserve_pct}% reserve margin: {required_capacity:.2f} MW required capacity")

# ─────────────────────────────────────────────
# 6. SAVE OUTPUTS
# ─────────────────────────────────────────────
df.to_csv('outputs/load_cleaned.csv', index=False)
daily.to_csv('outputs/daily_summary.csv')
hourly_profile.to_csv('outputs/hourly_profile.csv')
monthly_df.to_csv('outputs/monthly_forecast.csv', index=False)

print("\nOutputs saved.")

# ─────────────────────────────────────────────
# 7. FIGURES
# ─────────────────────────────────────────────
PLOT_DIR = 'report/images'

# Color palette
COLOR_MAIN = '#1f77b4'
COLOR_PEAK = '#d62728'
COLOR_WEEKEND = '#ff7f0e'
COLOR_WEEKDAY = '#2ca02c'

# ── Figure 1: Full time series with missing data highlighted ──
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

ax1 = axes[0]
ax1.plot(df['timestamp_utc'], df['load_mw'], color=COLOR_MAIN, lw=0.8, label='Load (interpolated)')
# Highlight missing regions
missing_mask = df['load_mw_raw'].isna()
if missing_mask.any():
    ax1.fill_between(df['timestamp_utc'], df['load_mw'].min() - 5, df['load_mw'].max() + 5,
                     where=missing_mask, alpha=0.3, color='red', label='Missing/interpolated')
ax1.axhline(df['load_mw'].mean(), color='gray', ls='--', lw=1, label=f'Mean: {df["load_mw"].mean():.1f} MW')
ax1.axhline(df['load_mw'].max(), color=COLOR_PEAK, ls=':', lw=1.5, label=f'Peak: {df["load_mw"].max():.1f} MW')
ax1.set_ylabel('Load (MW)', fontsize=11)
ax1.set_title('15-Minute Load Series — January 1–7, 2026', fontsize=13, fontweight='bold')
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.set_ylim(90, 145)

ax2 = axes[1]
# Rolling 1-hour average
df['load_1h'] = df['load_mw'].rolling(4, center=True).mean()
ax2.plot(df['timestamp_utc'], df['load_1h'], color='#9467bd', lw=1.2, label='1-hour rolling mean')
ax2.fill_between(df['timestamp_utc'], df['load_1h'] - df['load_mw'].rolling(4, center=True).std(),
                 df['load_1h'] + df['load_mw'].rolling(4, center=True).std(),
                 alpha=0.2, color='#9467bd', label='±1 std')
ax2.set_ylabel('Load (MW)', fontsize=11)
ax2.set_xlabel('Date (UTC)', fontsize=11)
ax2.set_title('1-Hour Rolling Mean with Variability Band', fontsize=12)
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax2.xaxis.set_major_locator(mdates.DayLocator())
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30, ha='right')

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/fig1_time_series.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 1 saved.")

# ── Figure 2: Daily load profiles (weekday vs weekend) ──
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
for day_name, group in df.groupby('day_name'):
    is_wknd = group['is_weekend'].iloc[0]
    color = COLOR_WEEKEND if is_wknd else COLOR_WEEKDAY
    alpha = 0.6
    profile = group.groupby('hour_frac')['load_mw'].mean()
    ax.plot(profile.index, profile.values, color=color, alpha=alpha, lw=1.5, label=day_name)

# Mean profiles
for label, mask, color in [('Weekday avg', ~df['is_weekend'], COLOR_WEEKDAY),
                            ('Weekend avg', df['is_weekend'], COLOR_WEEKEND)]:
    profile = df[mask].groupby('hour_frac')['load_mw'].mean()
    ax.plot(profile.index, profile.values, color=color, lw=2.5, ls='--', label=label)

ax.set_xlabel('Hour of Day', fontsize=11)
ax.set_ylabel('Load (MW)', fontsize=11)
ax.set_title('Daily Load Profiles by Day Type', fontsize=12, fontweight='bold')
ax.set_xticks(range(0, 25, 4))
ax.legend(fontsize=8, ncol=2)
ax.grid(True, alpha=0.3)

ax2 = axes[1]
# Box plot by hour
hour_data = [df[df['hour'] == h]['load_mw'].dropna().values for h in range(24)]
bp = ax2.boxplot(hour_data, positions=range(24), widths=0.6,
                 patch_artist=True,
                 boxprops=dict(facecolor='lightblue', color=COLOR_MAIN),
                 medianprops=dict(color=COLOR_PEAK, lw=2),
                 whiskerprops=dict(color=COLOR_MAIN),
                 capprops=dict(color=COLOR_MAIN),
                 flierprops=dict(marker='o', markersize=3, color='gray'))
ax2.set_xlabel('Hour of Day', fontsize=11)
ax2.set_ylabel('Load (MW)', fontsize=11)
ax2.set_title('Load Distribution by Hour', fontsize=12, fontweight='bold')
ax2.set_xticks(range(0, 24, 4))
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/fig2_daily_profiles.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved.")

# ── Figure 3: Load Duration Curve ──
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
load_sorted_vals = np.sort(df['load_mw'].dropna().values)[::-1]
hours_axis = np.linspace(0, len(load_sorted_vals) * 0.25, len(load_sorted_vals))  # in hours
pct_axis = np.linspace(0, 100, len(load_sorted_vals))

ax.plot(pct_axis, load_sorted_vals, color=COLOR_MAIN, lw=2)
ax.fill_between(pct_axis, load_sorted_vals, load_sorted_vals.min(), alpha=0.15, color=COLOR_MAIN)

# Mark key percentiles
for pct, label in [(1, 'Top 1%'), (5, 'Top 5%'), (10, 'Top 10%')]:
    val = np.percentile(df['load_mw'].dropna(), 100 - pct)
    ax.axhline(val, color='red', ls=':', lw=1, alpha=0.7)
    ax.text(pct + 1, val + 0.3, f'{label}\n{val:.1f} MW', fontsize=8, color='red')

ax.axhline(df['load_mw'].mean(), color='gray', ls='--', lw=1.5,
           label=f'Mean: {df["load_mw"].mean():.1f} MW')
ax.set_xlabel('% of Time Exceeded', fontsize=11)
ax.set_ylabel('Load (MW)', fontsize=11)
ax.set_title('Load Duration Curve', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 100)

ax2 = axes[1]
# Histogram of load values
ax2.hist(df['load_mw'].dropna(), bins=30, color=COLOR_MAIN, alpha=0.7, edgecolor='white')
ax2.axvline(df['load_mw'].mean(), color='gray', ls='--', lw=2, label=f'Mean: {df["load_mw"].mean():.1f} MW')
ax2.axvline(df['load_mw'].max(), color=COLOR_PEAK, ls=':', lw=2, label=f'Peak: {df["load_mw"].max():.1f} MW')
ax2.axvline(np.percentile(df['load_mw'].dropna(), 95), color='orange', ls='-.', lw=2,
            label=f'95th pct: {np.percentile(df["load_mw"].dropna(), 95):.1f} MW')
ax2.set_xlabel('Load (MW)', fontsize=11)
ax2.set_ylabel('Frequency (15-min intervals)', fontsize=11)
ax2.set_title('Load Frequency Distribution', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/fig3_load_duration.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved.")

# ── Figure 4: Annual Forecast ──
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
bars = ax.bar(monthly_df['Month'], monthly_df['Energy_MWh'] / 1000,
              color=[COLOR_MAIN if lf >= 1.0 else '#aec7e8' for lf in monthly_df['Load_Factor']],
              edgecolor='white', linewidth=0.5)
ax.set_xlabel('Month', fontsize=11)
ax.set_ylabel('Energy (GWh)', fontsize=11)
ax.set_title('Annual Energy Forecast by Month', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')
for bar, val in zip(bars, monthly_df['Energy_MWh'] / 1000):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
            f'{val:.1f}', ha='center', va='bottom', fontsize=8)
total_gwh = sum(monthly_energy) / 1000
ax.set_title(f'Annual Energy Forecast by Month\n(Total: {total_gwh:.1f} GWh)', fontsize=12, fontweight='bold')

ax2 = axes[1]
ax2.bar(monthly_df['Month'], monthly_df['Peak_MW'],
        color=[COLOR_PEAK if lf >= 1.0 else '#ffbb78' for lf in monthly_df['Load_Factor']],
        edgecolor='white', linewidth=0.5)
ax2.axhline(observed_peak, color='darkred', ls='--', lw=1.5,
            label=f'Observed peak: {observed_peak:.1f} MW')
# Reserve margin lines
for reserve_pct, color in [(15, 'orange'), (20, 'green')]:
    cap = observed_peak * (1 + reserve_pct / 100)
    ax2.axhline(cap, color=color, ls=':', lw=1.5,
                label=f'{reserve_pct}% reserve: {cap:.1f} MW')
ax2.set_xlabel('Month', fontsize=11)
ax2.set_ylabel('Peak Demand (MW)', fontsize=11)
ax2.set_title('Monthly Peak Demand Forecast\nwith Reserve Margin Targets', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/fig4_annual_forecast.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved.")

# ── Figure 5: Heatmap of load by hour and day ──
fig, ax = plt.subplots(figsize=(12, 5))

# Create pivot: rows=hour, cols=day
pivot = df.pivot_table(values='load_mw', index='hour', columns='day_name', aggfunc='mean')
# Reorder days
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
pivot = pivot.reindex(columns=[d for d in day_order if d in pivot.columns])

im = ax.imshow(pivot.values, aspect='auto', cmap='RdYlBu_r', origin='upper')
plt.colorbar(im, ax=ax, label='Mean Load (MW)')
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns, fontsize=10)
ax.set_yticks(range(0, 24, 2))
ax.set_yticklabels([f'{h:02d}:00' for h in range(0, 24, 2)], fontsize=9)
ax.set_xlabel('Day of Week', fontsize=11)
ax.set_ylabel('Hour of Day', fontsize=11)
ax.set_title('Load Heatmap: Hour × Day of Week (Mean MW)', fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/fig5_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 5 saved.")

# ── Figure 6: Daily energy and peak summary ──
fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

days_list = list(daily.index)
ax = axes[0]
ax.bar(range(len(days_list)), daily['energy_mwh'], color=COLOR_MAIN, alpha=0.8, edgecolor='white')
ax.axhline(daily['energy_mwh'].mean(), color='gray', ls='--', lw=1.5,
           label=f'Mean: {daily["energy_mwh"].mean():.1f} MWh/day')
ax.set_ylabel('Daily Energy (MWh)', fontsize=11)
ax.set_title('Daily Energy Consumption and Peak Demand', fontsize=12, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, axis='y')

ax2 = axes[1]
ax2.bar(range(len(days_list)), daily['peak_mw'], color=COLOR_PEAK, alpha=0.8, edgecolor='white')
ax2.axhline(daily['peak_mw'].mean(), color='gray', ls='--', lw=1.5,
            label=f'Mean daily peak: {daily["peak_mw"].mean():.1f} MW')
ax2.set_ylabel('Daily Peak (MW)', fontsize=11)
ax2.set_xlabel('Day', fontsize=11)
ax2.set_xticks(range(len(days_list)))
ax2.set_xticklabels([str(d) for d in days_list], rotation=30, ha='right', fontsize=9)
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/fig6_daily_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 6 saved.")

print("\nAll figures saved successfully.")
print("\n" + "=" * 60)
print("KEY RESULTS SUMMARY")
print("=" * 60)
print(f"Observed period: Jan 1-7, 2026 (7 days, 672 intervals)")
print(f"Missing data: 120 intervals ({120/672*100:.1f}%) — interpolated")
print(f"Mean load: {df['load_mw'].mean():.2f} MW")
print(f"Peak demand: {df['load_mw'].max():.2f} MW")
print(f"Minimum load: {df['load_mw'].min():.2f} MW")
print(f"Load factor: {load_factor*100:.2f}%")
print(f"Weekly energy: {weekly_energy_mwh:.1f} MWh")
print(f"Annual energy forecast: {annual_energy_forecast/1000:.2f} GWh")
print(f"Annual peak forecast: {observed_peak:.2f} MW (observed)")
print(f"Required capacity (15% reserve): {observed_peak * 1.15:.2f} MW")
print(f"Required capacity (20% reserve): {observed_peak * 1.20:.2f} MW")
