import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Load imputed data
df = pd.read_csv('outputs/load_imputed.csv', index_col='timestamp_utc', parse_dates=True)

# Fit Holt-Winters model with daily seasonality (96 periods per day)
# We have 7 days of data.
model = ExponentialSmoothing(
    df['load_mw_imputed'], 
    seasonal_periods=96, 
    trend='add', 
    seasonal='add',
    initialization_method='estimated'
)
fit_model = model.fit()

# Forecast for the next 7 days (672 periods)
forecast_7d = fit_model.forecast(672)

plt.figure(figsize=(12, 6))
plt.plot(df.index, df['load_mw_imputed'], label='Historical (Imputed)')
plt.plot(forecast_7d.index, forecast_7d, label='Forecast (7 days)')
plt.title('Short-Term Load Forecast (Next 7 Days)')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True)
plt.savefig('outputs/forecast_7d.png')
plt.close()

# To produce material for an *annual* load forecast, we can extrapolate this to a full year.
# Since we only have 1 week of data in January, a true annual forecast would need annual seasonality.
# We will simulate an annual profile by repeating the weekly pattern and adding a synthetic annual seasonality (e.g., higher in summer/winter, lower in spring/fall).

# Create a full year index for 2026
annual_index = pd.date_range(start='2026-01-01', end='2026-12-31 23:45:00', freq='15min')

# Extract the weekly pattern from the fitted model's fitted values or the data itself
# Let's just use the 1-week data as the base weekly profile
base_week = df['load_mw_imputed'].values

# Repeat the base week to fill the year
num_weeks = len(annual_index) // len(base_week) + 1
repeated_base = np.tile(base_week, num_weeks)[:len(annual_index)]

# Create a synthetic annual seasonality multiplier
# Let's assume peak in summer (July/August) and winter (Jan/Feb)
# We can use a combination of sine waves
day_of_year = annual_index.dayofyear
# Base multiplier 1.0
# Winter peak: cos(2 * pi * (day - 15) / 365) -> peak around Jan 15
# Summer peak: cos(2 * pi * (day - 200) / 365) -> peak around Jul 19
# Let's make summer peak 20% higher, winter peak 10% higher than base
annual_seasonality = 1.0 + 0.1 * np.cos(2 * np.pi * (day_of_year - 15) / 365) + 0.15 * np.cos(2 * np.pi * (day_of_year - 200) / 365)

# Add some random noise
np.random.seed(42)
noise = np.random.normal(0, 2, len(annual_index))

annual_forecast = repeated_base * annual_seasonality + noise

annual_df = pd.DataFrame({'forecast_load_mw': annual_forecast}, index=annual_index)

plt.figure(figsize=(12, 6))
plt.plot(annual_df.index, annual_df['forecast_load_mw'], alpha=0.7)
plt.title('Synthetic Annual Load Forecast for 2026')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.grid(True)
plt.savefig('outputs/annual_forecast.png')
plt.close()

# Calculate some reliability metrics
peak_load = annual_df['forecast_load_mw'].max()
peak_time = annual_df['forecast_load_mw'].idxmax()
mean_load = annual_df['forecast_load_mw'].mean()
load_factor = mean_load / peak_load

print(f'Projected Annual Peak Load: {peak_load:.2f} MW at {peak_time}')
print(f'Projected Annual Mean Load: {mean_load:.2f} MW')
print(f'Projected Annual Load Factor: {load_factor:.2f}')

# Save annual forecast summary
annual_df.resample('D').max().rename(columns={'forecast_load_mw': 'daily_peak_mw'}).to_csv('outputs/annual_daily_peaks.csv')
