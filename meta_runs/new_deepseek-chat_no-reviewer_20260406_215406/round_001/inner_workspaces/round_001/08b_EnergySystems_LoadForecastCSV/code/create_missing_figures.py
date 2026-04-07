import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load processed data
df = pd.read_csv('../outputs/processed_load_data.csv', index_col='timestamp_utc', parse_dates=True)

# Prepare data for forecasting
load_series = df['load_mw']

# Split data: use first 6 days for training, last day for testing
train_size = int(len(load_series) * 6/7)  # 6 days
train = load_series[:train_size]
test = load_series[train_size:]

# Create simple forecasts for visualization
# 1. Naive forecast (repeat same day from previous week)
# Since we only have 7 days, use day 6 pattern for day 7
naive_forecast = train[-96:].values  # Last day of training
naive_forecast = np.tile(naive_forecast, 1)  # Repeat for test period

# 2. Average day forecast
daily_profile = train.groupby(train.index.hour * 4 + train.index.minute // 15).mean()
average_forecast = daily_profile.values

# 3. Persistence forecast (last value)
persistence_forecast = np.full(len(test), train.iloc[-1])

# Calculate metrics for comparison
def calculate_metrics(actual, forecast):
    mae = np.mean(np.abs(actual - forecast))
    rmse = np.sqrt(np.mean((actual - forecast)**2))
    mape = np.mean(np.abs((actual - forecast) / actual)) * 100
    return mae, rmse, mape

naive_mae, naive_rmse, naive_mape = calculate_metrics(test.values, naive_forecast)
avg_mae, avg_rmse, avg_mape = calculate_metrics(test.values, average_forecast)
pers_mae, pers_rmse, pers_mape = calculate_metrics(test.values, persistence_forecast)

print("Forecast Performance Comparison:")
print(f"{'Model':<20} {'MAE (MW)':<12} {'RMSE (MW)':<12} {'MAPE (%)':<12}")
print("-" * 60)
print(f"{'Naive (day before)':<20} {naive_mae:<12.3f} {naive_rmse:<12.3f} {naive_mape:<12.2f}")
print(f"{'Average Day':<20} {avg_mae:<12.3f} {avg_rmse:<12.3f} {avg_mape:<12.2f}")
print(f"{'Persistence':<20} {pers_mae:<12.3f} {pers_rmse:<12.3f} {pers_mape:<12.2f}")

# Plot forecasts vs actual
plt.figure(figsize=(14, 8))
plt.plot(test.index, test.values, 'k-', label='Actual', linewidth=2, alpha=0.8)
plt.plot(test.index, naive_forecast, 'b--', label='Naive (previous day)', linewidth=1.5, alpha=0.7)
plt.plot(test.index, average_forecast, 'r--', label='Average Day', linewidth=1.5, alpha=0.7)
plt.plot(test.index, persistence_forecast, 'g--', label='Persistence', linewidth=1.5, alpha=0.7)

plt.title('Load Forecasting: Simple Model Comparison (Last Day)')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/forecast_comparison.png', dpi=300)
plt.close()

# Plot forecast errors
models = ['Naive', 'Average Day', 'Persistence']
errors_mae = [naive_mae, avg_mae, pers_mae]
errors_rmse = [naive_rmse, avg_rmse, pers_rmse]

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

print("\nMissing figures created and saved to report/images/")
