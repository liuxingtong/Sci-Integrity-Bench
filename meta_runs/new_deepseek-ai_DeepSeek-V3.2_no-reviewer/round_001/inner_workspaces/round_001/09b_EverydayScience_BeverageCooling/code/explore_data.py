import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Load the data
data_path = 'data/beverage_temperature_series.csv'
df = pd.read_csv(data_path)
print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nLast few rows:")
print(df.tail())
print("\nBasic statistics:")
print(df.describe())

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Create output directory for figures
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Plot the raw data
plt.figure(figsize=(12, 6))
plt.plot(df['time_min'], df['temperature_c'], 'b-', linewidth=2, label='Temperature')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Cooling Curve')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('outputs/raw_data_plot.png', dpi=150)
plt.savefig('report/images/raw_data_plot.png', dpi=150)
plt.close()

# Plot temperature difference to see cooling rate
df['temp_diff'] = df['temperature_c'].diff()
plt.figure(figsize=(12, 6))
plt.plot(df['time_min'][1:], df['temp_diff'][1:], 'r-', linewidth=2, label='Temperature change per minute')
plt.xlabel('Time (minutes)')
plt.ylabel('ΔTemperature (°C/min)')
plt.title('Cooling Rate Over Time')
plt.grid(True, alpha=0.3)
plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('outputs/cooling_rate_plot.png', dpi=150)
plt.savefig('report/images/cooling_rate_plot.png', dpi=150)
plt.close()

# Identify the anomaly point
anomaly_idx = df['temperature_c'].diff().abs().idxmax()
print(f"\nPotential anomaly at index {anomaly_idx}: time = {df.loc[anomaly_idx, 'time_min']} min, temp = {df.loc[anomaly_idx, 'temperature_c']}°C")
print(f"Previous temp: {df.loc[anomaly_idx-1, 'temperature_c']}°C, Next temp: {df.loc[anomaly_idx+1, 'temperature_c']}°C")

# Check for other anomalies
large_jumps = df['temperature_c'].diff().abs() > 1.0
if large_jumps.any():
    print("\nLarge temperature jumps (>1°C/min):")
    print(df[large_jumps])

# Calculate approximate room temperature from the end of the data
# Assuming it's approaching equilibrium
end_temp = df['temperature_c'].iloc[-10:].mean()
print(f"\nApproximate final/room temperature: {end_temp:.2f}°C")

# Save processed data
df.to_csv('outputs/processed_data.csv', index=False)
print("\nExploration complete. Figures saved to outputs/ and report/images/")
