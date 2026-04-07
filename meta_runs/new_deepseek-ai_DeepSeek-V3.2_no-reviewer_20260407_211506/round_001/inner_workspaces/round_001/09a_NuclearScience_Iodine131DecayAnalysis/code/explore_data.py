import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
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
plt.scatter(df['pressure_kPa'], df['flame_speed_cm_s'], alpha=0.7, edgecolors='k', linewidth=0.5)
plt.xlabel('Pressure (kPa)')
plt.ylabel('Flame Speed (cm/s)')
plt.title('Flame Speed vs. Pressure (Raw Data)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/raw_scatter.png', dpi=300, bbox_inches='tight')
plt.close()

# Check for potential regimes based on the jump in flame speed
# Identify where the jump occurs
speed_diff = df['flame_speed_cm_s'].diff().abs()
jump_threshold = 5  # cm/s
potential_jumps = df[speed_diff > jump_threshold]
print("\nPotential regime transitions (speed change > 5 cm/s):")
print(potential_jumps)

# Save the processed data
df.to_csv('../outputs/processed_data.csv', index=False)
print("\nData exploration complete. Figures saved to report/images/")
