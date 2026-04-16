import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Load data
df = pd.read_csv('../data/beverage_temperature_series.csv')

# Create output directory for images
os.makedirs('report/images', exist_ok=True)

# Plot the full temperature series
plt.figure(figsize=(12, 6))
plt.plot(df['time_min'], df['temperature_c'], 'b-', linewidth=2, label='Temperature')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Cooling Over Time')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('report/images/full_temperature_series.png', dpi=150)
plt.close()

# Identify the anomaly point
anomaly_idx = df[df['time_min'] == 80].index[0]
print(f"Anomaly detected at time {df.loc[anomaly_idx, 'time_min']} min, temperature {df.loc[anomaly_idx, 'temperature_c']}°C")
print(f"Previous temperature at time 79 min: {df.loc[anomaly_idx-1, 'temperature_c']}°C")
print(f"Temperature jump: {df.loc[anomaly_idx, 'temperature_c'] - df.loc[anomaly_idx-1, 'temperature_c']:.2f}°C")

# Also check for other anomalies
temp_diff = df['temperature_c'].diff()
large_jumps = df[abs(temp_diff) > 1]
print(f"\nLarge temperature jumps (>1°C):")
print(large_jumps)

# Plot with anomaly highlighted
plt.figure(figsize=(12, 6))
plt.plot(df['time_min'], df['temperature_c'], 'b-', linewidth=2, label='Temperature')
plt.scatter(df.loc[anomaly_idx, 'time_min'], df.loc[anomaly_idx, 'temperature_c'], 
            color='red', s=100, zorder=5, label='Anomaly (time=80)')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Cooling Over Time with Anomaly Highlighted')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('report/images/temperature_with_anomaly.png', dpi=150)
plt.close()

# Check if there are multiple segments
print(f"\nData segments based on anomalies:")
# The data seems to have 3 segments: 0-79, 80-120, 121-199
segment1 = df[df['time_min'] <= 79]
segment2 = df[(df['time_min'] >= 80) & (df['time_min'] <= 120)]
segment3 = df[df['time_min'] >= 121]

print(f"Segment 1: time {segment1['time_min'].min()} to {segment1['time_min'].max()} min, {len(segment1)} points")
print(f"Segment 2: time {segment2['time_min'].min()} to {segment2['time_min'].max()} min, {len(segment2)} points")
print(f"Segment 3: time {segment3['time_min'].min()} to {segment3['time_min'].max()} min, {len(segment3)} points")

# Plot segments separately
plt.figure(figsize=(12, 6))
plt.plot(segment1['time_min'], segment1['temperature_c'], 'b-', linewidth=2, label='Segment 1 (0-79 min)')
plt.plot(segment2['time_min'], segment2['temperature_c'], 'r-', linewidth=2, label='Segment 2 (80-120 min)')
plt.plot(segment3['time_min'], segment3['temperature_c'], 'g-', linewidth=2, label='Segment 3 (121-199 min)')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Cooling - Three Segments')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('report/images/three_segments.png', dpi=150)
plt.close()