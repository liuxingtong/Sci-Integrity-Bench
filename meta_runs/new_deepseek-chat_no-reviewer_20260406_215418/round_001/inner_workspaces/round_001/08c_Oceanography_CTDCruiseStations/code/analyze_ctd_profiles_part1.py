import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('husl')

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load the synthetic CTD data
ctd_path = '../outputs/synthetic_ctd_profiles.csv'
ctd_df = pd.read_csv(ctd_path)

print("CTD Data Overview:")
print(f"Shape: {ctd_df.shape}")
print(f"Stations: {ctd_df['station_id'].unique()}")
print(f"Pressure range: {ctd_df['pressure_dbar'].min()} to {ctd_df['pressure_dbar'].max()} dbar")
print(f"Temperature range: {ctd_df['temperature_c'].min():.2f} to {ctd_df['temperature_c'].max():.2f} °C")
print(f"Salinity range: {ctd_df['salinity_psu'].min():.2f} to {ctd_df['salinity_psu'].max():.2f} psu")
print("\n")

# 1. Vertical structure analysis
print("1. Vertical Structure Analysis:")

# Calculate mean profiles
pressure_levels = sorted(ctd_df['pressure_dbar'].unique())
mean_temp_by_depth = ctd_df.groupby('pressure_dbar')['temperature_c'].mean()
mean_sal_by_depth = ctd_df.groupby('pressure_dbar')['salinity_psu'].mean()
std_temp_by_depth = ctd_df.groupby('pressure_dbar')['temperature_c'].std()
std_sal_by_depth = ctd_df.groupby('pressure_dbar')['salinity_psu'].std()

print(f"Surface (0-50m) mean temperature: {mean_temp_by_depth[mean_temp_by_depth.index <= 50].mean():.2f} ± {std_temp_by_depth[std_temp_by_depth.index <= 50].mean():.2f} °C")
print(f"Surface (0-50m) mean salinity: {mean_sal_by_depth[mean_sal_by_depth.index <= 50].mean():.2f} ± {std_sal_by_depth[std_sal_by_depth.index <= 50].mean():.2f} psu")
print(f"Thermocline (100-500m) mean temperature gradient: {(mean_temp_by_depth[500] - mean_temp_by_depth[100])/400:.3f} °C/dbar")
print(f"Deep water (>1000m) mean temperature: {mean_temp_by_depth[mean_temp_by_depth.index >= 1000].mean():.2f} °C")
print(f"Deep water (>1000m) mean salinity: {mean_sal_by_depth[mean_sal_by_depth.index >= 1000].mean():.2f} psu")

# 2. Water mass analysis using T-S diagrams
print("\n2. Water Mass Analysis:")

# Calculate density (sigma-theta) using simplified equation of state
# Simplified formula: sigma_theta = density - 1000 kg/m³
# Using approximate formula for demonstration
ctd_df['density_sigma_theta'] = (1028 - 0.1 * ctd_df['temperature_c'] + 0.8 * (ctd_df['salinity_psu'] - 35))

# Identify water masses based on T-S characteristics
# Define water mass boundaries (simplified)
def classify_water_mass(temp, sal, pressure):
    if pressure <= 100:
        return 'Surface Water'
    elif pressure <= 300 and sal > 35.5:
        return 'Subtropical Underwater'
    elif pressure <= 1000 and temp < 10:
        return 'Antarctic Intermediate Water'
    elif pressure > 1000:
        return 'Deep Water'
    else:
        return 'Thermocline Water'

ctd_df['water_mass'] = ctd_df.apply(
    lambda row: classify_water_mass(row['temperature_c'], row['salinity_psu'], row['pressure_dbar']), 
    axis=1
)

water_mass_counts = ctd_df['water_mass'].value_counts()
print("Water mass distribution:")
for wm, count in water_mass_counts.items():
    percentage = 100 * count / len(ctd_df)
    print(f"  {wm}: {count} points ({percentage:.1f}%)")

# 3. Spatial variability analysis
print("\n3. Spatial Variability Analysis:")

# Calculate station statistics
station_stats = ctd_df.groupby('station_id').agg({
    'lat': 'first',
    'lon': 'first',
    'temperature_c': ['mean', 'std', 'min', 'max'],
    'salinity_psu': ['mean', 'std', 'min', 'max'],
    'density_sigma_theta': 'mean'
}).round(3)

station_stats.columns = ['lat', 'lon', 'temp_mean', 'temp_std', 'temp_min', 'temp_max',
                         'sal_mean', 'sal_std', 'sal_min', 'sal_max', 'density_mean']

print("Station statistics:")
print(station_stats)

# Save station statistics
station_stats.to_csv('../outputs/station_statistics.csv')
print("\nStation statistics saved to outputs/station_statistics.csv")

print("\nPart 1 analysis complete.")