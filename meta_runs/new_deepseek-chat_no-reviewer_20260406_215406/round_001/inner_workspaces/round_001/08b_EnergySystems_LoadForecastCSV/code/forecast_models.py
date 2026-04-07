import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load processed data
df = pd.read_csv('../outputs/processed_load_data.csv', index_col='timestamp_utc', parse_dates=True)
print(f"Data shape: {df.shape}")

# Prepare data for forecasting
load_series = df['load_mw']

# Split data: use first 6 days for training, last day for testing
train_size = int(len(load_series) * 6/7)  # 6 days
train = load_series[:train_size]
test = load_series[train_size:]

print(f"Train size: {len(train)} ({(len(train)/len(load_series)*100):.1f}%)")
print(f"Test size: {len(test)} ({(len(test)/len(load_series)*100):.1f}%)")

# 1. Holt-Winters Exponential Smoothing model
print("\n=== Holt-Winters Exponential Smoothing ===")
# Since we have 15-min data, seasonality period = 24*4 = 96
hw_model = ExponentialSmoothing(train, 
                                seasonal_periods=96, 
                                trend='add', 
                                seasonal='add',
                                initialization_method='estimated')
hw_fit = hw_model.fit()
hw_forecast = hw_fit.forecast(len(test))

# Calculate metrics
hw_mae = mean_absolute_error(test, hw_forecast)
hw_rmse = np.sqrt(mean_squared_error(test, hw_forecast))
print(f"HW MAE: {hw_mae:.3f} MW")
print(f"HW RMSE: {hw_rmse:.3f} MW")
print(f"HW Mean Absolute Percentage Error: {(np.mean(np.abs((test - hw_forecast) / test)) * 100):.2f}%")

# 2. ARIMA model
print("\n=== ARIMA Model ===")
# Based on ACF/PACF analysis, try ARIMA(1,0,1) with seasonal components
# Differencing d=0 since series appears stationary
arima_model = ARIMA(train, order=(1, 0, 1), seasonal_order=(1, 0, 1, 96))
arima_fit = arima_model.fit()
arima_forecast = arima_fit.forecast(len(test))

# Calculate metrics
arima_mae = mean_absolute_error(test, arima_forecast)
arima_rmse = np.sqrt(mean_squared_error(test, arima_forecast))
print(f"ARIMA MAE: {arima_mae:.3f} MW")
print(f"ARIMA RMSE: {arima_rmse:.3f} MW")
print(f"ARIMA Mean Absolute Percentage Error: {(np.mean(np.abs((test - arima_forecast) / test)) * 100):.2f}%")

# 3. Machine Learning approach: Random Forest with time features
print("\n=== Random Forest Model ===")
# Create features for ML model
# We need to create features on the full dataset first, then split
df_ml = df.copy()

# Create lag features
for lag in [1, 2, 3, 4, 96]:  # 15-min, 30-min, 45-min, 1-hour, 1-day lags (192 is too large for 7 days)
    df_ml[f'lag_{lag}'] = df_ml['load_mw'].shift(lag)

# Create time-based features
df_ml['hour'] = df_ml.index.hour
df_ml['minute'] = df_ml.index.minute
df_ml['day_of_week'] = df_ml.index.dayofweek

# Drop rows with NaN from lag features
df_ml = df_ml.dropna()

# Now split the data
train_ml = df_ml.iloc[:train_size - 96]  # Subtract max lag to ensure no data leakage
test_ml = df_ml.iloc[train_size - 96:train_size + len(test)]  # Include overlap for lag features

# Further trim to get only test period predictions
test_start_idx = len(train_ml)
test_ml = test_ml.iloc[test_start_idx:]

# Prepare features and target
X_train = train_ml.drop('load_mw', axis=1)
y_train = train_ml['load_mw']
X_test = test_ml.drop('load_mw', axis=1)
y_test = test_ml['load_mw']

print(f"ML Train size: {len(X_train)}")
print(f"ML Test size: {len(X_test)}")

# Train Random Forest
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)
rf_forecast = rf_model.predict(X_test)

y_test_aligned = y_test

# Calculate metrics
rf_mae = mean_absolute_error(y_test_aligned, rf_forecast)
rf_rmse = np.sqrt(mean_squared_error(y_test_aligned, rf_forecast))
print(f"RF MAE: {rf_mae:.3f} MW")
print(f"RF RMSE: {rf_rmse:.3f} MW")
print(f"RF Mean Absolute Percentage Error: {(np.mean(np.abs((y_test_aligned - rf_forecast) / y_test_aligned)) * 100):.2f}%")

# Compare models
print("\n=== Model Comparison ===")
print(f"{'Model':<20} {'MAE (MW)':<12} {'RMSE (MW)':<12} ")
print("-" * 50)
print(f"{'Holt-Winters':<20} {hw_mae:<12.3f} {hw_rmse:<12.3f}")
print(f"{'ARIMA':<20} {arima_mae:<12.3f} {arima_rmse:<12.3f}")
print(f"{'Random Forest':<20} {rf_mae:<12.3f} {rf_rmse:<12.3f}")

# Plot forecasts vs actual
plt.figure(figsize=(14, 8))
plt.plot(test.index, test.values, 'k-', label='Actual', linewidth=2, alpha=0.8)
plt.plot(test.index, hw_forecast.values, 'b--', label='Holt-Winters', linewidth=1.5, alpha=0.7)
plt.plot(test.index, arima_forecast.values, 'r--', label='ARIMA', linewidth=1.5, alpha=0.7)
plt.plot(y_test_aligned.index, rf_forecast, 'g--', label='Random Forest', linewidth=1.5, alpha=0.7)

plt.title('Load Forecasting: Model Comparison (Last Day)')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/forecast_comparison.png', dpi=300)
plt.close()

# Plot forecast errors
models = ['Holt-Winters', 'ARIMA', 'Random Forest']
errors_mae = [hw_mae, arima_mae, rf_mae]
errors_rmse = [hw_rmse, arima_rmse, rf_rmse]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].bar(models, errors_mae, color=['blue', 'red', 'green'], alpha=0.7)
axes[0].set_title('Mean Absolute Error (MAE) by Model')
axes[0].set_ylabel('MAE (MW)')
axes[0].grid(True, alpha=0.3, axis='y')

axes[1].bar(models, errors_rmse, color=['blue', 'red', 'green'], alpha=0.7)
axes[1].set_title('Root Mean Square Error (RMSE) by Model')
axes[1].set_ylabel('RMSE (MW)')
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../report/images/forecast_errors.png', dpi=300)
plt.close()

print("\nForecast comparison complete. Figures saved to report/images/")

# Save forecast results
forecast_results = pd.DataFrame({
    'timestamp': test.index,
    'actual': test.values,
    'holt_winters': hw_forecast.values,
    'arima': arima_forecast.values
})
# Add RF forecast (aligned)
rf_results = pd.DataFrame({
    'timestamp': y_test_aligned.index,
    'random_forest': rf_forecast
})
forecast_results = forecast_results.merge(rf_results, on='timestamp', how='left')
forecast_results.to_csv('../outputs/forecast_results.csv', index=False)
print("Forecast results saved to outputs/forecast_results.csv")
