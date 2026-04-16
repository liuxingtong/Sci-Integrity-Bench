import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
data_path = '../data/load_15min.csv'
df = pd.read_csv(data_path)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df.set_index('timestamp_utc', inplace=True)

print("Original data shape:", df.shape)
print("Missing values:", df['load_mw'].isnull().sum())

# ====== STEP 1: IMPUTE MISSING VALUES ======
# Strategy: For missing entire day (Jan 2), use average of same day of week (Thursday)
# For other missing values, use linear interpolation

df_imputed = df.copy()

# First, identify the completely missing day (Jan 2, 2026)
# January 2, 2026 is a Friday (dayofweek = 4)
missing_day = pd.Timestamp('2026-01-02')
print(f"\nCompletely missing day: {missing_day.date()} (Day of week: {missing_day.day_name()})")

# Find other Fridays in the dataset to use as reference
friday_data = []
for date in pd.date_range(start=df.index.min(), end=df.index.max()):
    if date.dayofweek == 4 and date.date() != missing_day.date():  # Friday = 4
        day_data = df[df.index.date == date.date()]
        if not day_data['load_mw'].isnull().all():  # Only use if not all missing
            friday_data.append(day_data['load_mw'].values)

# Calculate average Friday profile if we have reference data
if friday_data:
    # Find the minimum length to avoid issues
    min_length = min(len(d) for d in friday_data)
    friday_data_truncated = [d[:min_length] for d in friday_data]
    avg_friday_profile = np.nanmean(friday_data_truncated, axis=0)
    
    # Impute the missing Friday
    missing_day_start = pd.Timestamp(f'{missing_day.date()} 00:00:00')
    missing_day_end = pd.Timestamp(f'{missing_day.date()} 23:45:00')
    missing_day_range = pd.date_range(start=missing_day_start, end=missing_day_end, freq='15min')
    
    # Ensure we have the right number of intervals
    n_intervals = len(missing_day_range)
    if len(avg_friday_profile) >= n_intervals:
        for i, ts in enumerate(missing_day_range):
            if i < len(avg_friday_profile):
                df_imputed.loc[ts, 'load_mw'] = avg_friday_profile[i]
    else:
        # If profile is shorter, repeat or interpolate
        for i, ts in enumerate(missing_day_range):
            idx = i % len(avg_friday_profile)
            df_imputed.loc[ts, 'load_mw'] = avg_friday_profile[idx]
    
    print(f"Imputed {n_intervals} values for {missing_day.date()} using average Friday profile")

# Now use linear interpolation for any remaining missing values
df_imputed['load_mw'] = df_imputed['load_mw'].interpolate(method='linear')

# If there are still missing values at the beginning/end, use forward/backward fill
df_imputed['load_mw'] = df_imputed['load_mw'].fillna(method='ffill').fillna(method='bfill')

print(f"Remaining missing values after imputation: {df_imputed['load_mw'].isnull().sum()}")

# ====== STEP 2: TIME SERIES DECOMPOSITION ======
# Resample to hourly for clearer seasonal patterns
df_hourly = df_imputed.resample('H').mean()

# Perform seasonal decomposition (multiplicative for load data)
# Use period = 24 for daily seasonality (hourly data)
decomposition = seasonal_decompose(df_hourly['load_mw'], model='additive', period=24)

# Plot decomposition
fig, axes = plt.subplots(4, 1, figsize=(14, 10))

axes[0].plot(decomposition.observed, label='Observed')
axes[0].legend(loc='upper left')
axes[0].set_ylabel('Load (MW)')

axes[1].plot(decomposition.trend, label='Trend')
axes[1].legend(loc='upper left')
axes[1].set_ylabel('Trend')

axes[2].plot(decomposition.seasonal, label='Seasonal')
axes[2].legend(loc='upper left')
axes[2].set_ylabel('Seasonal')

axes[3].plot(decomposition.resid, label='Residual')
axes[3].legend(loc='upper left')
axes[3].set_ylabel('Residual')
axes[3].set_xlabel('Date')

plt.suptitle('Time Series Decomposition of Hourly Load Data', fontsize=16)
plt.tight_layout()
plt.savefig('../report/images/time_series_decomposition.png', dpi=300)
plt.close()

print("\nDecomposition plot saved to report/images/time_series_decomposition.png")

# ====== STEP 3: FORECASTING MODEL ======
# For annual forecast, we'll use SARIMA model
# First, let's work with daily data for annual forecasting
df_daily = df_imputed.resample('D').agg({'load_mw': ['mean', 'max', 'min']})
df_daily.columns = ['daily_mean', 'daily_max', 'daily_min']

print("\nDaily statistics:")
print(df_daily)

# Prepare data for SARIMA (using daily mean)
ts_data = df_daily['daily_mean']

# Split into train/test (use last day for testing if we have enough data)
train_size = int(len(ts_data) * 0.8)
train = ts_data[:train_size]
test = ts_data[train_size:]

print(f"\nTraining data: {len(train)} days")
print(f"Test data: {len(test)} days")

# Fit SARIMA model
# Note: For a proper implementation, we would do parameter tuning
# For simplicity, we'll use reasonable defaults
order = (1, 1, 1)  # (p, d, q)
seasonal_order = (1, 1, 1, 7)  # (P, D, Q, s) where s=7 for weekly seasonality

model = SARIMAX(train, order=order, seasonal_order=seasonal_order)
model_fit = model.fit(disp=False)

print("\nSARIMA Model Summary:")
print(model_fit.summary())

# Forecast on test set
forecast = model_fit.get_forecast(steps=len(test))
forecast_mean = forecast.predicted_mean
forecast_ci = forecast.conf_int()

# Calculate forecast metrics
mae = mean_absolute_error(test, forecast_mean)
rmse = np.sqrt(mean_squared_error(test, forecast_mean))
mape = np.mean(np.abs((test - forecast_mean) / test)) * 100

print(f"\nForecast Metrics:")
print(f"MAE: {mae:.2f} MW")
print(f"RMSE: {rmse:.2f} MW")
print(f"MAPE: {mape:.2f}%")

# Plot forecast vs actual
plt.figure(figsize=(12, 6))
plt.plot(train.index, train, 'b-', label='Training Data')
plt.plot(test.index, test, 'g-', label='Actual Test Data')
plt.plot(test.index, forecast_mean, 'r--', label='Forecast')
plt.fill_between(test.index, 
                 forecast_ci.iloc[:, 0], 
                 forecast_ci.iloc[:, 1], 
                 color='pink', alpha=0.3, label='95% Confidence Interval')
plt.title('SARIMA Forecast vs Actual (Daily Mean Load)')
plt.xlabel('Date')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/sarima_forecast.png', dpi=300)
plt.close()

print("\nForecast plot saved to report/images/sarima_forecast.png")

# ====== STEP 4: ANNUAL FORECAST ======
# Forecast for the next year (365 days)
# First, refit model on all data
full_model = SARIMAX(ts_data, order=order, seasonal_order=seasonal_order)
full_model_fit = full_model.fit(disp=False)

# Generate forecast for next 365 days
forecast_horizon = 365
annual_forecast = full_model_fit.get_forecast(steps=forecast_horizon)
annual_forecast_mean = annual_forecast.predicted_mean
annual_forecast_ci = annual_forecast.conf_int()

# Create date index for forecast
last_date = ts_data.index[-1]
forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), 
                               periods=forecast_horizon, freq='D')

# Calculate annual statistics
annual_mean = annual_forecast_mean.mean()
annual_max = annual_forecast_mean.max()
annual_min = annual_forecast_mean.min()
annual_peak_to_mean = annual_max / annual_mean

print(f"\nAnnual Forecast Statistics (next 365 days):")
print(f"Average daily load: {annual_mean:.2f} MW")
print(f"Maximum daily load: {annual_max:.2f} MW")
print(f"Minimum daily load: {annual_min:.2f} MW")
print(f"Peak-to-average ratio: {annual_peak_to_mean:.2f}")

# Plot annual forecast
plt.figure(figsize=(14, 7))
plt.plot(ts_data.index, ts_data, 'b-', label='Historical Data (7 days)', linewidth=2)
plt.plot(forecast_dates, annual_forecast_mean, 'r-', label='Annual Forecast', linewidth=2, alpha=0.7)
plt.fill_between(forecast_dates, 
                 annual_forecast_ci.iloc[:, 0], 
                 annual_forecast_ci.iloc[:, 1], 
                 color='pink', alpha=0.3, label='95% Confidence Interval')
plt.title('Annual Load Forecast (Next 365 Days)', fontsize=16)
plt.xlabel('Date')
plt.ylabel('Daily Mean Load (MW)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/annual_forecast.png', dpi=300)
plt.close()

print("\nAnnual forecast plot saved to report/images/annual_forecast.png")

# ====== STEP 5: SAVE FORECAST RESULTS ======
# Save forecast data to CSV
forecast_df = pd.DataFrame({
    'date': forecast_dates,
    'forecast_mean': annual_forecast_mean.values,
    'forecast_lower': annual_forecast_ci.iloc[:, 0].values,
    'forecast_upper': annual_forecast_ci.iloc[:, 1].values
})
forecast_df.to_csv('../outputs/annual_forecast.csv', index=False)

# Save model metrics
metrics_df = pd.DataFrame({
    'metric': ['MAE', 'RMSE', 'MAPE'],
    'value': [mae, rmse, mape],
    'unit': ['MW', 'MW', '%']
})
metrics_df.to_csv('../outputs/forecast_metrics.csv', index=False)

# Save key annual statistics
annual_stats = pd.DataFrame({
    'statistic': ['annual_mean', 'annual_max', 'annual_min', 'peak_to_mean_ratio'],
    'value': [annual_mean, annual_max, annual_min, annual_peak_to_mean],
    'unit': ['MW', 'MW', 'MW', 'ratio']
})
annual_stats.to_csv('../outputs/annual_statistics.csv', index=False)

print("\nForecast results saved to outputs/ directory")
print("\nAnalysis complete!")