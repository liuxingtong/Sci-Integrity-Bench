import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
data_path = "../data/flame_pressure_series.csv"
df = pd.read_csv(data_path)

print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nData info:")
print(df.info())
print("\nDescriptive statistics:")
print(df.describe())

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Create output directory if it doesn't exist
os.makedirs("../outputs", exist_ok=True)
os.makedirs("../report/images", exist_ok=True)

# Basic scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(df['pressure_kPa'], df['flame_speed_cm_s'], alpha=0.7, s=50)
plt.xlabel('Pressure (kPa)')
plt.ylabel('Flame Speed (cm/s)')
plt.title('Flame Speed vs Chamber Pressure')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/scatter_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# Check for the jump in data
print("\nLooking for data patterns:")
# Calculate differences between consecutive flame speeds
df['flame_speed_diff'] = df['flame_speed_cm_s'].diff()
print("\nLargest positive jumps in flame speed:")
print(df.nlargest(5, 'flame_speed_diff')[['pressure_kPa', 'flame_speed_cm_s', 'flame_speed_diff']])

print("\nData saved to outputs and images created.")