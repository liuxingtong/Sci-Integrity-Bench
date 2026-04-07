import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Read the data
data_path = '../data/cruise_ctd.csv'
df = pd.read_csv(data_path)
print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nData info:")
print(df.info())
print("\nSummary statistics:")
print(df.describe())
print("\nMissing values:")
print(df.isnull().sum())

# Check station distribution
print("\nStation locations:")
print(df[['station_id', 'lat', 'lon']])

# Create output directory
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Plot station locations
plt.figure(figsize=(10, 8))
plt.scatter(df['lon'], df['lat'], c='red', s=100, marker='o', edgecolors='black')
for i, row in df.iterrows():
    plt.text(row['lon']+0.05, row['lat']+0.05, row['station_id'], fontsize=9)
plt.xlabel('Longitude (°E)')
plt.ylabel('Latitude (°S)')
plt.title('CTD Station Locations')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/station_locations.png', dpi=300)
plt.close()

print("\nExploration complete. Station map saved to report/images/station_locations.png")