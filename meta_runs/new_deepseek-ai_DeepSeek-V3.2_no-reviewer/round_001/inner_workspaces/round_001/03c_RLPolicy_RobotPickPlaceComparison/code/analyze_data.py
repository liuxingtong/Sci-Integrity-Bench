import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for better visualizations
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
data_path = "../data/pick_place_metrics.csv"
df = pd.read_csv(data_path)
print("Data loaded successfully!")
print(f"Shape: {df.shape}")
print("\nFirst few rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nUnique arms (policies):")
print(df['arm'].unique())
print("\nUnique metrics:")
print(df['metric'].unique())
print("\nSummary statistics:")
print(df.describe())

# Create a pivot table for easier analysis
pivot_sim = df.pivot(index='metric', columns='arm', values='simulation')
pivot_real = df.pivot(index='metric', columns='arm', values='real_world')

print("\nSimulation values (pivot):")
print(pivot_sim)
print("\nReal-world values (pivot):")
print(pivot_real)

# Calculate differences between pi_new and pi_base
diff_sim = pivot_sim['pi_new'] - pivot_sim['pi_base']
diff_real = pivot_real['pi_new'] - pivot_real['pi_base']

print("\nDifferences (pi_new - pi_base) in simulation:")
print(diff_sim)
print("\nDifferences (pi_new - pi_base) in real-world:")
print(diff_real)

# Calculate percentage changes
pct_sim = (diff_sim / pivot_sim['pi_base']) * 100
pct_real = (diff_real / pivot_real['pi_base']) * 100

print("\nPercentage changes (pi_new vs pi_base) in simulation:")
print(pct_sim)
print("\nPercentage changes (pi_new vs pi_base) in real-world:")
print(pct_real)

# Save the processed data
os.makedirs("../outputs", exist_ok=True)
pivot_sim.to_csv("../outputs/simulation_pivot.csv")
pivot_real.to_csv("../outputs/real_world_pivot.csv")
pd.DataFrame({'metric': diff_sim.index, 'diff_sim': diff_sim.values, 'diff_real': diff_real.values}).to_csv("../outputs/differences.csv", index=False)

print("\nData analysis complete. Results saved to outputs/ folder.")