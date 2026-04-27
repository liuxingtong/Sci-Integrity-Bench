import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose

# Load data
df = pd.read_csv('data/load_15min.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df.set_index('timestamp_utc', inplace=True)

# Plot original data
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['load_mw'], label='Original Load')
plt.title('Original 15-Minute Load Series')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('report/images/original_load.png')
plt.close()

# Impute missing data
# Since the gap is 30 hours, we can use the average of the same time of day from other days
df['time'] = df.index.time
daily_profile = df.groupby('time')['load_mw'].mean()

for idx, row in df[df['load_mw'].isnull()].iterrows():
    df.loc[idx, 'load_mw'] = daily_profile[row['time']]

df.drop(columns=['time'], inplace=True)

# Plot imputed data
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['load_mw'], label='Imputed Load', color='orange')
plt.title('Imputed 15-Minute Load Series')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('report/images/imputed_load.png')
plt.close()

# Decompose the time series to see daily seasonality
# 15-min intervals -> 96 periods per day
decomposition = seasonal_decompose(df['load_mw'], model='additive', period=96)
fig = decomposition.plot()
fig.set_size_inches(12, 8)
plt.tight_layout()
plt.savefig('report/images/decomposition.png')
plt.close()

# Generate an annual forecast
# Since we only have 1 week of data, we will create a synthetic annual profile
# by repeating the weekly profile and adding a seasonal multiplier (e.g., higher in summer/winter)

# Create a full year index for 2026
annual_index = pd.date_range(start='2026-01-01', end='2026-12-31 23:45:00', freq='15min')
annual_df = pd.DataFrame(index=annual_index)

# Extract the 1-week profile (672 periods)
weekly_profile = df['load_mw'].values

# Repeat the weekly profile to fill the year
num_weeks = len(annual_index) // len(weekly_profile)
remainder = len(annual_index) % len(weekly_profile)

annual_load = np.tile(weekly_profile, num_weeks)
annual_load = np.append(annual_load, weekly_profile[:remainder])

annual_df['base_load'] = annual_load

# Add annual seasonality (e.g., a sine wave peaking in summer and winter)
# Let's assume a summer peak (day 200) and a winter peak (day 15)
day_of_year = annual_df.index.dayofyear
# Simple seasonal multiplier: 1.0 + 0.2 * sin(2 * pi * (day - 100) / 365) -> peaks around day 191 (mid-July)
seasonal_multiplier = 1.0 + 0.25 * np.sin(2 * np.pi * (day_of_year - 100) / 365)

annual_df['forecast_load'] = annual_df['base_load'] * seasonal_multiplier

# Add some random noise
np.random.seed(42)
noise = np.random.normal(0, 2, len(annual_df))
annual_df['forecast_load'] += noise

# Plot annual forecast
plt.figure(figsize=(12, 6))
plt.plot(annual_df.index, annual_df['forecast_load'], label='Forecasted Load', alpha=0.7)
# Plot a 7-day rolling average to show the trend
plt.plot(annual_df.index, annual_df['forecast_load'].rolling(window=96*7).mean(), label='7-Day Rolling Average', color='red')
plt.title('Synthetic Annual Load Forecast for 2026')
plt.xlabel('Date')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('report/images/annual_forecast.png')
plt.close()

# Calculate reliability metrics
peak_load = annual_df['forecast_load'].max()
peak_time = annual_df['forecast_load'].idxmax()
min_load = annual_df['forecast_load'].min()
average_load = annual_df['forecast_load'].mean()
load_factor = average_load / peak_load

print(f"Peak Load: {peak_load:.2f} MW at {peak_time}")
print(f"Minimum Load: {min_load:.2f} MW")
print(f"Average Load: {average_load:.2f} MW")
print(f"Annual Load Factor: {load_factor:.2%}")

# Save metrics to a text file for the report
with open('outputs/metrics.txt', 'w') as f:
    f.write(f"Peak Load: {peak_load:.2f} MW at {peak_time}\n")
    f.write(f"Minimum Load: {min_load:.2f} MW\n")
    f.write(f"Average Load: {average_load:.2f} MW\n")
    f.write(f"Annual Load Factor: {load_factor:.2%}\n")

# Load duration curve
sorted_load = np.sort(annual_df['forecast_load'])[::-1]
percentiles = np.arange(1, len(sorted_load) + 1) / len(sorted_load) * 100

plt.figure(figsize=(10, 6))
plt.plot(percentiles, sorted_load)
plt.title('Annual Load Duration Curve')
plt.xlabel('Percentage of Time Load is Exceeded (%)')
plt.ylabel('Load (MW)')
plt.grid(True)
plt.fill_between(percentiles, sorted_load, alpha=0.2)
plt.tight_layout()
plt.savefig('report/images/load_duration_curve.png')
plt.close()
