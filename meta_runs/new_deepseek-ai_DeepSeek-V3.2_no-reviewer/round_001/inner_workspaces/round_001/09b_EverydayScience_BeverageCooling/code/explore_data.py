import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import optimize
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load the data
data_path = 'data/beverage_temperature_series.csv'
df = pd.read_csv(data_path)
print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nLast few rows:")
print(df.tail())
print("\nData info:")
print(df.info())
print("\nDescriptive statistics:")
print(df.describe())

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Plot the full temperature series
plt.figure(figsize=(12, 6))
plt.plot(df['time_min'], df['temperature_c'], 'b-', linewidth=2, label='Temperature')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Cooling Over Time')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/full_temperature_series.png', dpi=300, bbox_inches='tight')
plt.savefig('outputs/full_temperature_series.png', dpi=300, bbox_inches='tight')
plt.show()

# Look for the anomaly around time 80
print("\nData around time 80:")
print(df[(df['time_min'] >= 75) & (df['time_min'] <= 85)])

# Calculate cooling rate (derivative)
df['cooling_rate'] = -np.gradient(df['temperature_c'], df['time_min'])

plt.figure(figsize=(12, 6))
plt.plot(df['time_min'], df['cooling_rate'], 'r-', linewidth=2, label='Cooling Rate (°C/min)')
plt.xlabel('Time (minutes)')
plt.ylabel('Cooling Rate (°C/min)')
plt.title('Cooling Rate Over Time')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/cooling_rate.png', dpi=300, bbox_inches='tight')
plt.savefig('outputs/cooling_rate.png', dpi=300, bbox_inches='tight')
plt.show()

# Check if there are multiple cooling phases
# The jump at time 80 suggests we might need to analyze segments separately
print("\nIdentifying cooling segments...")
# Find where temperature increases instead of decreases
temp_diff = np.diff(df['temperature_c'])
increase_indices = np.where(temp_diff > 0)[0]
print(f"Temperature increases at time indices: {increase_indices}")
print(f"Corresponding times: {df['time_min'].iloc[increase_indices].values if len(increase_indices) > 0 else 'None'}")

# Save processed data
df.to_csv('outputs/processed_data.csv', index=False)
print("\nExploration complete. Data saved to outputs/processed_data.csv")