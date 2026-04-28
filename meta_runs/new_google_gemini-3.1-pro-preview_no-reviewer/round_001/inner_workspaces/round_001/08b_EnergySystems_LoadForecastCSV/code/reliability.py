import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load annual forecast
annual_df = pd.read_csv('outputs/annual_daily_peaks.csv', index_col=0, parse_dates=True)

# Load duration curve
# We need the full 15-min data for the load duration curve
# Let's re-generate it here or just read the full series if we saved it. We didn't save the full series.
# Let's re-generate the full series quickly.
import numpy as np
df = pd.read_csv('outputs/load_imputed.csv', index_col='timestamp_utc', parse_dates=True)
annual_index = pd.date_range(start='2026-01-01', end='2026-12-31 23:45:00', freq='15min')
base_week = df['load_mw_imputed'].values
num_weeks = len(annual_index) // len(base_week) + 1
repeated_base = np.tile(base_week, num_weeks)[:len(annual_index)]
day_of_year = annual_index.dayofyear
annual_seasonality = 1.0 + 0.1 * np.cos(2 * np.pi * (day_of_year - 15) / 365) + 0.15 * np.cos(2 * np.pi * (day_of_year - 200) / 365)
np.random.seed(42)
noise = np.random.normal(0, 2, len(annual_index))
annual_forecast = repeated_base * annual_seasonality + noise
full_annual_df = pd.DataFrame({'forecast_load_mw': annual_forecast}, index=annual_index)

# Load Duration Curve
sorted_load = np.sort(full_annual_df['forecast_load_mw'])[::-1]
percentiles = np.arange(1, len(sorted_load) + 1) / len(sorted_load) * 100

plt.figure(figsize=(10, 6))
plt.plot(percentiles, sorted_load)
plt.title('Annual Load Duration Curve (2026)')
plt.xlabel('Percentage of Time Load is Exceeded (%)')
plt.ylabel('Load (MW)')
plt.grid(True)
plt.fill_between(percentiles, sorted_load, alpha=0.2)
plt.axhline(y=sorted_load[int(len(sorted_load)*0.01)], color='r', linestyle='--', label='Top 1% Load')
plt.legend()
plt.savefig('outputs/load_duration_curve.png')
plt.close()

# Top 100 hours analysis
top_100_hours = full_annual_df.nlargest(400, 'forecast_load_mw') # 400 15-min intervals = 100 hours

plt.figure(figsize=(10, 6))
sns.histplot(top_100_hours.index.month, bins=12, discrete=True)
plt.title('Distribution of Top 100 Peak Load Hours by Month')
plt.xlabel('Month')
plt.ylabel('Number of 15-min Intervals')
plt.xticks(range(1, 13))
plt.grid(axis='y')
plt.savefig('outputs/peak_months.png')
plt.close()

plt.figure(figsize=(10, 6))
sns.histplot(top_100_hours.index.hour, bins=24, discrete=True)
plt.title('Distribution of Top 100 Peak Load Hours by Hour of Day')
plt.xlabel('Hour of Day')
plt.ylabel('Number of 15-min Intervals')
plt.xticks(range(0, 24))
plt.grid(axis='y')
plt.savefig('outputs/peak_hours.png')
plt.close()

# Ramp rate analysis
full_annual_df['ramp_mw_per_15min'] = full_annual_df['forecast_load_mw'].diff()

plt.figure(figsize=(10, 6))
sns.histplot(full_annual_df['ramp_mw_per_15min'].dropna(), bins=100, kde=True)
plt.title('Distribution of 15-Minute Ramp Rates')
plt.xlabel('Ramp Rate (MW / 15 min)')
plt.ylabel('Frequency')
plt.grid(True)
plt.savefig('outputs/ramp_rates.png')
plt.close()

max_up_ramp = full_annual_df['ramp_mw_per_15min'].max()
max_down_ramp = full_annual_df['ramp_mw_per_15min'].min()
print(f'Max 15-min Up-Ramp: {max_up_ramp:.2f} MW')
print(f'Max 15-min Down-Ramp: {max_down_ramp:.2f} MW')
