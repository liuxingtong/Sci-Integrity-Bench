import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load the data
data_path = '../data/beverage_temperature_series.csv'
df = pd.read_csv(data_path)
print(f"Data shape: {df.shape}")
print(df.head())
print(df.tail())

# Basic statistics
print("\nBasic statistics:")
print(df.describe())

# Check for missing values
print(f"\nMissing values: {df.isnull().sum().sum()}")

# Plot the raw data
plt.figure(figsize=(12, 6))
plt.plot(df['time_min'], df['temperature_c'], 'b-', linewidth=2, label='Temperature')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Cooling Curve')
plt.grid(True, alpha=0.3)
plt.legend()

# Mark the anomalies
anomaly_times = [80, 121]
for t in anomaly_times:
    idx = df[df['time_min'] == t].index[0]
    plt.plot(df.loc[idx, 'time_min'], df.loc[idx, 'temperature_c'], 'ro', markersize=8, label=f'Anomaly at t={t}' if t == 80 else '')

plt.legend()

# Save the figure
os.makedirs('../report/images', exist_ok=True)
plt.savefig('../report/images/raw_data.png', dpi=300, bbox_inches='tight')
plt.show()

# Calculate cooling rate (derivative)
df['cooling_rate'] = -np.gradient(df['temperature_c'], df['time_min'])

# Plot cooling rate
plt.figure(figsize=(12, 6))
plt.plot(df['time_min'], df['cooling_rate'], 'g-', linewidth=2, label='Cooling Rate')
plt.xlabel('Time (minutes)')
plt.ylabel('Cooling Rate (°C/min)')
plt.title('Cooling Rate Over Time')
plt.grid(True, alpha=0.3)
plt.legend()
plt.savefig('../report/images/cooling_rate.png', dpi=300, bbox_inches='tight')
plt.show()

# Check temperature difference from ambient (assuming room temperature ~25°C)
# We'll estimate ambient temperature from the tail of the data
ambient_est = df['temperature_c'].iloc[-20:].mean()
print(f"\nEstimated ambient temperature from last 20 points: {ambient_est:.2f}°C")

# Calculate temperature difference from ambient
df['temp_diff'] = df['temperature_c'] - ambient_est

# Plot log of temperature difference
plt.figure(figsize=(12, 6))
plt.plot(df['time_min'], np.log(df['temp_diff']), 'm-', linewidth=2, label='log(T - T_ambient)')
plt.xlabel('Time (minutes)')
plt.ylabel('log(T - T_ambient)')
plt.title('Logarithm of Temperature Difference from Ambient')
plt.grid(True, alpha=0.3)
plt.legend()
plt.savefig('../report/images/log_temp_diff.png', dpi=300, bbox_inches='tight')
plt.show()