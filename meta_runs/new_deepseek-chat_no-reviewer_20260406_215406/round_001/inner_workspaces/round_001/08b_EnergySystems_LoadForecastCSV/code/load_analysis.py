import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
df = pd.read_csv('../data/load_15min.csv')
print(f"Data shape: {df.shape}")
print(df.head())
print(df.tail())

# Convert timestamp to datetime and set as index
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df.set_index('timestamp_utc', inplace=True)

# Check for missing values
print(f"\nMissing values: {df.isnull().sum().sum()}")

# Basic statistics
print("\nBasic statistics:")
print(df.describe())

# Create time-based features
df['hour'] = df.index.hour
df['day_of_week'] = df.index.dayofweek  # Monday=0, Sunday=6
df['day_of_month'] = df.index.day
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

# Plot the time series
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['load_mw'], linewidth=1)
plt.title('15-Minute Load Time Series (Jan 1-7, 2026)')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/time_series.png', dpi=300)
plt.close()

# Plot daily patterns
plt.figure(figsize=(12, 6))
for day in range(7):
    day_data = df[df['day_of_week'] == day]
    plt.plot(day_data.index.hour + day_data.index.minute/60, 
             day_data['load_mw'], 
             label=f'Day {day+1}', 
             alpha=0.7, 
             linewidth=1)
plt.title('Daily Load Patterns by Day of Week')
plt.xlabel('Hour of Day')
plt.ylabel('Load (MW)')
plt.legend(title='Day of Week')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/daily_patterns.png', dpi=300)
plt.close()

# Box plot by hour
plt.figure(figsize=(12, 6))
df.boxplot(column='load_mw', by='hour', grid=False)
plt.title('Load Distribution by Hour of Day')
plt.suptitle('')  # Remove default suptitle
plt.xlabel('Hour of Day')
plt.ylabel('Load (MW)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/boxplot_by_hour.png', dpi=300)
plt.close()

# Seasonal decomposition (assuming daily seasonality: 24*4 = 96 periods per day)
# Resample to hourly for clearer seasonal patterns
df_hourly = df['load_mw'].resample('H').mean()

# For seasonal decomposition, we need at least 2 full cycles
# Let's use daily seasonality (24 periods for hourly data)
decomposition = seasonal_decompose(df_hourly, model='additive', period=24)

fig, axes = plt.subplots(4, 1, figsize=(12, 10))
axes[0].plot(decomposition.observed)
axes[0].set_ylabel('Observed')
axes[0].set_title('Seasonal Decomposition of Hourly Load')

axes[1].plot(decomposition.trend)
axes[1].set_ylabel('Trend')

axes[2].plot(decomposition.seasonal)
axes[2].set_ylabel('Seasonal')

axes[3].plot(decomposition.resid)
axes[3].set_ylabel('Residual')
axes[3].set_xlabel('Time')

plt.tight_layout()
plt.savefig('../report/images/seasonal_decomposition.png', dpi=300)
plt.close()

# Calculate autocorrelation
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

fig, axes = plt.subplots(2, 1, figsize=(12, 8))
plot_acf(df['load_mw'], lags=96, ax=axes[0])  # 24 hours * 4 = 96 lags for daily seasonality
axes[0].set_title('Autocorrelation Function (ACF)')

plot_pacf(df['load_mw'], lags=48, ax=axes[1])  # 12 hours * 4 = 48 lags
axes[1].set_title('Partial Autocorrelation Function (PACF)')

plt.tight_layout()
plt.savefig('../report/images/acf_pacf.png', dpi=300)
plt.close()

print("\nAnalysis complete. Figures saved to report/images/")

# Save processed data
df.to_csv('../outputs/processed_load_data.csv')
print("Processed data saved to outputs/processed_load_data.csv")
