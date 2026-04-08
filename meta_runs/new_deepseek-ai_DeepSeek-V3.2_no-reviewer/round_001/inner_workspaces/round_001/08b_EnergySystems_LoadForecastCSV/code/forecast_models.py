import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')
import os

# Load and prepare data
df = pd.read_csv('data/load_15min.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df.set_index('timestamp_utc', inplace=True)

# Create features for ML model
df['hour'] = df.index.hour
df['minute'] = df.index.minute
df['day_of_week'] = df.index.dayofweek
df['day_of_month'] = df.index.day
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
df['sin_hour'] = np.sin(2 * np.pi * df['hour'] / 24)
df['cos_hour'] = np.cos(2 * np.pi * df['hour'] / 24)
df['sin_minute'] = np.sin(2 * np.pi * df['minute'] / 60)
df['cos_minute'] = np.cos(2 * np.pi * df['minute'] / 60)

# Split data: use first 6 days for training, last day for testing
train_end = pd.Timestamp('2026-01-06 23:45:00+00:00')
train_data = df[df.index <= train_end]
test_data = df[df.index > train_end]

print(f"Training data: {len(train_data)} samples ({train_data.index.min()} to {train_data.index.max()})")
print(f"Test data: {len(test_data)} samples ({test_data.index.min()} to {test_data.index.max()})")

# 1. Baseline models
# 1a. Mean forecast
mean_value = train_data['load_mw'].mean()
mean_forecast = pd.Series(mean_value, index=test_data.index)

# 1b. Naive forecast (last observation)
naive_value = train_data['load_mw'].iloc[-1]
naive_forecast = pd.Series(naive_value, index=test_data.index)

# 1c. Seasonal naive forecast (same time previous day)
def seasonal_naive_forecast(train_series, test_times, season_length=96):  # 96 = 24h * 4 intervals
    forecasts = []
    for t in test_times:
        # Find the same time one day ago
        idx = len(train_series) - season_length + (t.hour * 4 + t.minute // 15)
        if idx >= 0:
            forecasts.append(train_series.iloc[idx])
        else:
            # If not enough history, use the mean
            forecasts.append(train_series.mean())
    return pd.Series(forecasts, index=test_times)

snaive_forecast = seasonal_naive_forecast(train_data['load_mw'], test_data.index)

# Evaluate baseline models
baseline_results = {}
for name, forecast in [('Mean', mean_forecast), ('Naive', naive_forecast), ('Seasonal Naive', snaive_forecast)]:
    mae = mean_absolute_error(test_data['load_mw'], forecast)
    rmse = np.sqrt(mean_squared_error(test_data['load_mw'], forecast))
    mape = np.mean(np.abs((test_data['load_mw'] - forecast) / test_data['load_mw'])) * 100
    baseline_results[name] = {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}
    print(f"{name} Forecast - MAE: {mae:.2f}, RMSE: {rmse:.2f}, MAPE: {mape:.2f}%")

# 2. SARIMA model
print("\nFitting SARIMA model...")
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    
    # Use hourly data for SARIMA to reduce computational complexity
    hourly_train = train_data['load_mw'].resample('h').mean()
    hourly_test = test_data['load_mw'].resample('h').mean()
    
    # Fit SARIMA with daily seasonality (seasonal_order P=1, D=0, Q=1, s=24)
    sarima_model = SARIMAX(hourly_train, 
                          order=(1, 0, 1), 
                          seasonal_order=(1, 0, 1, 24),
                          enforce_stationarity=False,
                          enforce_invertibility=False)
    sarima_fit = sarima_model.fit(disp=False)
    print(f"SARIMA AIC: {sarima_fit.aic:.2f}")
    
    # Forecast for test period (24 hours)
    sarima_forecast_hourly = sarima_fit.forecast(steps=24)
    
    # Convert back to 15-minute intervals (simple interpolation)
    sarima_forecast = pd.Series(index=test_data.index)
    for i, time in enumerate(test_data.index):
        hour = time.floor('H')
        if hour in sarima_forecast_hourly.index:
            # Simple approach: use hourly forecast for all 15-min intervals in that hour
            sarima_forecast.loc[time] = sarima_forecast_hourly.loc[hour]
        else:
            sarima_forecast.loc[time] = np.nan
    
    # Fill any NaN values with seasonal naive
    sarima_forecast = sarima_forecast.fillna(snaive_forecast)
    
    # Evaluate SARIMA
    mae = mean_absolute_error(test_data['load_mw'], sarima_forecast)
    rmse = np.sqrt(mean_squared_error(test_data['load_mw'], sarima_forecast))
    mape = np.mean(np.abs((test_data['load_mw'] - sarima_forecast) / test_data['load_mw'])) * 100
    baseline_results['SARIMA'] = {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}
    print(f"SARIMA Forecast - MAE: {mae:.2f}, RMSE: {rmse:.2f}, MAPE: {mape:.2f}%")
    
except Exception as e:
    print(f"SARIMA failed: {e}")
    sarima_forecast = snaive_forecast.copy()
    baseline_results['SARIMA'] = baseline_results['Seasonal Naive']

# 3. LightGBM model
print("\nFitting LightGBM model...")
try:
    import lightgbm as lgb
    
    # Prepare features for LightGBM
    feature_cols = ['hour', 'minute', 'day_of_week', 'is_weekend', 
                   'sin_hour', 'cos_hour', 'sin_minute', 'cos_minute']
    
    X_train = train_data[feature_cols]
    y_train = train_data['load_mw']
    X_test = test_data[feature_cols]
    y_test = test_data['load_mw']
    
    # Create and train model
    lgb_model = lgb.LGBMRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        random_state=42,
        verbose=-1
    )
    
    lgb_model.fit(X_train, y_train)
    
    # Make predictions
    lgb_forecast = pd.Series(lgb_model.predict(X_test), index=test_data.index)
    
    # Evaluate
    mae = mean_absolute_error(y_test, lgb_forecast)
    rmse = np.sqrt(mean_squared_error(y_test, lgb_forecast))
    mape = np.mean(np.abs((y_test - lgb_forecast) / y_test)) * 100
    baseline_results['LightGBM'] = {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}
    print(f"LightGBM Forecast - MAE: {mae:.2f}, RMSE: {rmse:.2f}, MAPE: {mape:.2f}%")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': lgb_model.feature_importances_
    }).sort_values('importance', ascending=False)
    print("\nFeature importance:")
    print(feature_importance.to_string(index=False))
    feature_importance.to_csv('outputs/feature_importance.csv', index=False)
    
except Exception as e:
    print(f"LightGBM failed: {e}")
    lgb_forecast = snaive_forecast.copy()
    baseline_results['LightGBM'] = baseline_results['Seasonal Naive']

# Save baseline results
baseline_df = pd.DataFrame(baseline_results).T
baseline_df.to_csv('outputs/baseline_forecast_results.csv')
print(f"\nBaseline results saved to outputs/baseline_forecast_results.csv")

# 4. Plot forecasts vs actual
plt.figure(figsize=(14, 8))
plt.plot(test_data.index, test_data['load_mw'], 'k-', linewidth=2, label='Actual', alpha=0.8)
plt.plot(test_data.index, snaive_forecast, 'b-', linewidth=1.5, label='Seasonal Naive', alpha=0.7)
if 'SARIMA' in baseline_results:
    plt.plot(test_data.index, sarima_forecast, 'g-', linewidth=1.5, label='SARIMA', alpha=0.7)
if 'LightGBM' in baseline_results:
    plt.plot(test_data.index, lgb_forecast, 'r-', linewidth=1.5, label='LightGBM', alpha=0.7)

plt.title('Forecast Comparison (Last Day)', fontsize=14)
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/forecast_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 5. Plot forecast errors
models_to_plot = [m for m in ['Seasonal Naive', 'SARIMA', 'LightGBM'] if m in baseline_results]
error_data = []
for model in models_to_plot:
    if model == 'Seasonal Naive':
        forecast = snaive_forecast
    elif model == 'SARIMA':
        forecast = sarima_forecast
    elif model == 'LightGBM':
        forecast = lgb_forecast
    
    errors = test_data['load_mw'] - forecast
    for err in errors:
        error_data.append({'Model': model, 'Error': err})

error_df = pd.DataFrame(error_data)

plt.figure(figsize=(12, 6))
for i, model in enumerate(models_to_plot):
    model_errors = error_df[error_df['Model'] == model]['Error']
    plt.hist(model_errors, bins=20, alpha=0.5, label=model)

plt.title('Forecast Error Distribution', fontsize=14)
plt.xlabel('Forecast Error (MW)')
plt.ylabel('Frequency')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/forecast_error_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# 6. Create annual forecast projection
print("\nCreating annual forecast projection...")

# Use the best model based on MAPE
best_model_name = min(baseline_results.items(), key=lambda x: x[1]['MAPE'])[0]
print(f"Best model for annual projection: {best_model_name}")

# Generate synthetic annual data based on weekly patterns
# Create a full year of timestamps at 15-minute intervals
start_date = pd.Timestamp('2026-01-01 00:00:00')
end_date = pd.Timestamp('2026-12-31 23:45:00')
annual_timestamps = pd.date_range(start=start_date, end=end_date, freq='15min')

# Create features for the entire year
annual_df = pd.DataFrame(index=annual_timestamps)
annual_df['hour'] = annual_df.index.hour
annual_df['minute'] = annual_df.index.minute
annual_df['day_of_week'] = annual_df.index.dayofweek
annual_df['month'] = annual_df.index.month
annual_df['day_of_year'] = annual_df.index.dayofyear
annual_df['is_weekend'] = annual_df['day_of_week'].isin([5, 6]).astype(int)
annual_df['sin_hour'] = np.sin(2 * np.pi * annual_df['hour'] / 24)
annual_df['cos_hour'] = np.cos(2 * np.pi * annual_df['hour'] / 24)
annual_df['sin_minute'] = np.sin(2 * np.pi * annual_df['minute'] / 60)
annual_df['cos_minute'] = np.cos(2 * np.pi * annual_df['minute'] / 60)

# Generate base forecast using the best model
if best_model_name == 'LightGBM' and 'LightGBM' in baseline_results:
    # Use LightGBM for annual forecast
    annual_forecast = lgb_model.predict(annual_df[feature_cols])
elif best_model_name == 'SARIMA' and 'SARIMA' in baseline_results:
    # For SARIMA, we need a different approach - use seasonal patterns
    # Calculate average daily profile from training data
    avg_daily_profile = train_data.groupby(['hour', 'minute'])['load_mw'].mean().reset_index()
    # Map to annual data
    annual_forecast = annual_df.merge(avg_daily_profile, on=['hour', 'minute'], how='left')['load_mw'].values
else:
    # Use seasonal naive approach (average daily profile)
    avg_daily_profile = train_data.groupby(['hour', 'minute'])['load_mw'].mean().reset_index()
    annual_forecast = annual_df.merge(avg_daily_profile, on=['hour', 'minute'], how='left')['load_mw'].values

annual_df['base_forecast'] = annual_forecast

# Apply monthly adjustment factors (simulated - in reality would use historical data)
# For demonstration, assume 2% annual growth with seasonal variation
np.random.seed(42)
monthly_factors = {
    1: 1.00,  # January (baseline)
    2: 0.98,  # February
    3: 0.96,  # March
    4: 0.94,  # April
    5: 0.92,  # May
    6: 0.95,  # June
    7: 1.05,  # July (peak summer)
    8: 1.08,  # August (peak summer)
    9: 1.02,  # September
    10: 0.98, # October
    11: 0.96, # November
    12: 1.01  # December
}

# Apply monthly factors
annual_df['monthly_factor'] = annual_df['month'].map(monthly_factors)
annual_df['adjusted_forecast'] = annual_df['base_forecast'] * annual_df['monthly_factor']

# Apply annual growth factor (2%)
growth_factor = 1.02
annual_df['final_forecast'] = annual_df['adjusted_forecast'] * growth_factor

# Calculate annual statistics
annual_peak = annual_df['final_forecast'].max()
annual_min = annual_df['final_forecast'].min()
annual_avg = annual_df['final_forecast'].mean()
annual_energy = annual_df['final_forecast'].sum() * 0.25  # MW * 0.25h = MWh per interval
load_factor = annual_avg / annual_peak

print(f"Annual Forecast Statistics:")
print(f"  Average Load: {annual_avg:.2f} MW")
print(f"  Peak Load: {annual_peak:.2f} MW")
print(f"  Minimum Load: {annual_min:.2f} MW")
print(f"  Annual Energy: {annual_energy:,.0f} MWh")
print(f"  Load Factor: {load_factor:.3f}")

# Save annual forecast
annual_df[['final_forecast']].to_csv('outputs/annual_forecast_15min.csv')

# Resample to daily for visualization
daily_forecast = annual_df['final_forecast'].resample('D').mean()
peak_daily = annual_df['final_forecast'].resample('D').max()

plt.figure(figsize=(14, 8))
plt.plot(daily_forecast.index, daily_forecast.values, 'b-', linewidth=1, label='Daily Average')
plt.plot(peak_daily.index, peak_daily.values, 'r-', linewidth=1, alpha=0.7, label='Daily Peak')
plt.fill_between(daily_forecast.index, daily_forecast.values * 0.9, daily_forecast.values * 1.1, 
                 alpha=0.2, color='b', label='±10% Range')
plt.title('Annual Load Forecast 2026', fontsize=14)
plt.xlabel('Date')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/annual_forecast.png', dpi=300, bbox_inches='tight')
plt.close()

# Monthly summary
monthly_summary = annual_df.resample('M').agg({
    'final_forecast': ['mean', 'max', 'min', 'std']
})
monthly_summary.columns = ['monthly_avg', 'monthly_peak', 'monthly_min', 'monthly_std']
monthly_summary.to_csv('outputs/monthly_forecast_summary.csv')

print("\nForecast modeling complete.")
