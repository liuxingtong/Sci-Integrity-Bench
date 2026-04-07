import pandas as pd
import numpy as np

# Load processed data
df = pd.read_csv('../outputs/processed_load_data.csv', index_col='timestamp_utc', parse_dates=True)

# Prepare data for forecasting
load_series = df['load_mw']

# Split data: use first 6 days for training, last day for testing
train_size = int(len(load_series) * 6/7)  # 6 days
train = load_series[:train_size]
test = load_series[train_size:]

# Create forecasts
# 1. Naive forecast (repeat same day from previous week)
naive_forecast = train[-96:].values

# 2. Average day forecast
daily_profile = train.groupby(train.index.hour * 4 + train.index.minute // 15).mean()
average_forecast = daily_profile.values

# 3. Persistence forecast (last value)
persistence_forecast = np.full(len(test), train.iloc[-1])

# Create results dataframe
results = pd.DataFrame({
    'timestamp': test.index,
    'actual': test.values,
    'naive_forecast': naive_forecast,
    'average_day_forecast': average_forecast,
    'persistence_forecast': persistence_forecast
})

# Save to CSV
results.to_csv('../outputs/forecast_results.csv', index=False)
print("Forecast results saved to outputs/forecast_results.csv")
print(f"Results shape: {results.shape}")
