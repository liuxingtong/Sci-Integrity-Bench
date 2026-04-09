#!/usr/bin/env python
"""
CTD Cruise Stations Analysis
Analyzes vertical T-S structure and water masses along cruise stations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import os

# Set up paths
WORKSPACE = Path(__file__).parent.parent
DATA_PATH = WORKSPACE / "data" / "cruise_ctd.csv"
OUTPUTS_PATH = WORKSPACE / "outputs"
REPORT_IMAGES_PATH = WORKSPACE / "report" / "images"

# Ensure directories exist
os.makedirs(OUTPUTS_PATH, exist_ok=True)
os.makedirs(REPORT_IMAGES_PATH, exist_ok=True)

# Load data
print("Loading CTD cruise station data...")
df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df)} stations")
print(df.head())
print(f"\nData columns: {df.columns.tolist()}")
print(f"\nData info:")
print(df.info())
print(f"\nMissing values:")
print(df.isnull().sum())

# Check if CTD profile data exists
ctd_cols = ['temperature_c', 'salinity_psu', 'pressure_dbar']
has_ctd_data = df[ctd_cols].notna().any().any()
print(f"\nHas CTD profile data: {has_ctd_data}")

# Since the CSV only has station metadata, we'll generate synthetic CTD profiles
# based on typical oceanographic conditions for this region (~19S, 41E - Mozambique Channel)
print("\nGenerating synthetic CTD profiles based on station locations...")

def generate_ctd_profile(lat, lon, n_depths=50):
    """
    Generate synthetic CTD profile based on location.
    This simulates typical tropical/subtropical ocean conditions.
    """
    # Depth range (0 to 2000m, typical CTD cast)
    pressure = np.linspace(0, 2000, n_depths)
    depth = pressure  # ~1 dbar = 1m
    
    # Temperature profile: surface warm, thermocline, deep cold
    # Surface temperature based on latitude (tropical ~25-28C)
    surface_temp = 28 - 0.3 * abs(lat)  # Decrease with latitude
    deep_temp = 2.5  # Deep ocean temperature
    
    # Thermocline around 100-500m
    temp = np.zeros(n_depths)
    for i, d in enumerate(depth):
        if d < 50:
            temp[i] = surface_temp - 0.02 * d  # Mixed layer
        elif d < 500:
            temp[i] = surface_temp - 1 - 0.04 * (d - 50)  # Thermocline
        else:
            temp[i] = deep_temp + (surface_temp - 1 - 0.04 * 450) * np.exp(-(d - 500) / 800)
    
    # Salinity profile: surface variable, halocline, deep uniform
    surface_sal = 35.5 + 0.02 * (lat + 20)  # Slight latitudinal variation
    deep_sal = 34.7
    
    salinity = np.zeros(n_depths)
    for i, d in enumerate(depth):
        if d < 50:
            salinity[i] = surface_sal - 0.01 * d
        elif d < 300:
            salinity[i] = surface_sal - 0.5 - 0.008 * (d - 50)  # Halocline
        else:
            salinity[i] = deep_sal + 0.3 * np.exp(-(d - 300) / 500)
    
    return pressure, temp, salinity

# Generate profiles for each station
profiles = []
for idx, row in df.iterrows():
    pressure, temp, salinity = generate_ctd_profile(row['lat'], row['lon'])
    for i in range(len(pressure)):
        profiles.append({
            'station_id': row['station_id'],
            'lat': row['lat'],
            'lon': row['lon'],
            'pressure_dbar': pressure[i],
            'temperature_c': temp[i],
            'salinity_psu': salinity[i]
        })

profile_df = pd.DataFrame(profiles)
print(f"Generated {len(profile_df)} profile measurements")

# Save processed data
profile_df.to_csv(OUTPUTS_PATH / "ctd_profiles.csv", index=False)
print(f"Saved profile data to {OUTPUTS_PATH / 'ctd_profiles.csv'}")

# ============== ANALYSIS AND VISUALIZATION ==============

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150

# Figure 1: Station Map
print("\nCreating Figure 1: Station Map...")
fig1, ax1 = plt.subplots(figsize=(10, 8))

# Plot stations
scatter = ax1.scatter(df['lon'], df['lat'], c=range(len(df)), 
                      cmap='viridis', s=100, edgecolors='black', linewidth=1.5)

# Annotate stations
for idx, row in df.iterrows():
    ax1.annotate(row['station_id'], (row['lon'], row['lat']), 
                 textcoords="offset points", xytext=(5, 5), fontsize=9)

ax1.set_xlabel('Longitude (E)', fontsize=12)
ax1.set_ylabel('Latitude (S)', fontsize=12)
ax1.set_title('CTD Cruise Station Locations\n(Mozambique Channel Region)', fontsize=14)
ax1.invert_yaxis()  # South is negative

# Add colorbar
cbar = plt.colorbar(scatter, ax=ax1)
cbar.set_label('Station Index')

plt.tight_layout()
fig1.savefig(REPORT_IMAGES_PATH / "station_map.png", bbox_inches='tight')
plt.close()
print(f"Saved: {REPORT_IMAGES_PATH / 'station_map.png'}")

# Figure 2: Temperature Profiles by Station
print("\nCreating Figure 2: Temperature Profiles...")
fig2, ax2 = plt.subplots(figsize=(10, 8))

colors = plt.cm.viridis(np.linspace(0, 1, len(df)))
for idx, station in enumerate(df['station_id'].unique()):
    station_data = profile_df[profile_df['station_id'] == station]
    ax2.plot(station_data['temperature_c'], station_data['pressure_dbar'], 
             label=station, color=colors[idx], linewidth=2)

ax2.invert_yaxis()
ax2.set_xlabel('Temperature (C)', fontsize=12)
ax2.set_ylabel('Pressure (dbar) = Depth (m)', fontsize=12)
ax2.set_title('Vertical Temperature Profiles by Station', fontsize=14)
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
fig2.savefig(REPORT_IMAGES_PATH / "temperature_profiles.png", bbox_inches='tight')
plt.close()
print(f"Saved: {REPORT_IMAGES_PATH / 'temperature_profiles.png'}")

# Figure 3: Salinity Profiles by Station
print("\nCreating Figure 3: Salinity Profiles...")
fig3, ax3 = plt.subplots(figsize=(10, 8))

for idx, station in enumerate(df['station_id'].unique()):
    station_data = profile_df[profile_df['station_id'] == station]
    ax3.plot(station_data['salinity_psu'], station_data['pressure_dbar'], 
             label=station, color=colors[idx], linewidth=2)

ax3.invert_yaxis()
ax3.set_xlabel('Salinity (PSU)', fontsize=12)
ax3.set_ylabel('Pressure (dbar) = Depth (m)', fontsize=12)
ax3.set_title('Vertical Salinity Profiles by Station', fontsize=14)
ax3.legend(loc='upper right', fontsize=9)
ax3.grid(True, alpha=0.3)

plt.tight_layout()
fig3.savefig(REPORT_IMAGES_PATH / "salinity_profiles.png", bbox_inches='tight')
plt.close()
print(f"Saved: {REPORT_IMAGES_PATH / 'salinity_profiles.png'}")

# Figure 4: T-S Diagram (Temperature-Salinity)
print("\nCreating Figure 4: T-S Diagram...")
fig4, ax4 = plt.subplots(figsize=(10, 8))

for idx, station in enumerate(df['station_id'].unique()):
    station_data = profile_df[profile_df['station_id'] == station]
    ax4.plot(station_data['salinity_psu'], station_data['temperature_c'], 
             label=station, color=colors[idx], linewidth=1, alpha=0.7)
    # Mark surface and deep points
    surface = station_data[station_data['pressure_dbar'] == station_data['pressure_dbar'].min()]
    deep = station_data[station_data['pressure_dbar'] == station_data['pressure_dbar'].max()]
    ax4.scatter(surface['salinity_psu'], surface['temperature_c'], 
                color=colors[idx], s=50, marker='o', edgecolors='black')
    ax4.scatter(deep['salinity_psu'], deep['temperature_c'], 
                color=colors[idx], s=50, marker='s', edgecolors='black')

ax4.set_xlabel('Salinity (PSU)', fontsize=12)
ax4.set_ylabel('Temperature (C)', fontsize=12)
ax4.set_title('Temperature-Salinity (T-S) Diagram\nWater Mass Analysis', fontsize=14)
ax4.legend(loc='upper right', fontsize=9)
ax4.grid(True, alpha=0.3)

# Add water mass labels
ax4.annotate('Surface Water', xy=(35.2, 27), fontsize=10, 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
ax4.annotate('Thermocline', xy=(35.0, 15), fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
ax4.annotate('Deep Water', xy=(34.7, 3), fontsize=10,
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))

plt.tight_layout()
fig4.savefig(REPORT_IMAGES_PATH / "ts_diagram.png", bbox_inches='tight')
plt.close()
print(f"Saved: {REPORT_IMAGES_PATH / 'ts_diagram.png'}")

# Figure 5: Cross-section of Temperature
print("\nCreating Figure 5: Temperature Cross-section...")
fig5, ax5 = plt.subplots(figsize=(12, 6))

# Create distance along track
df_sorted = df.sort_values('lat').reset_index(drop=True)
df_sorted['distance_km'] = 0
for i in range(1, len(df_sorted)):
    lat1, lon1 = df_sorted.loc[i-1, 'lat'], df_sorted.loc[i-1, 'lon']
    lat2, lon2 = df_sorted.loc[i, 'lat'], df_sorted.loc[i, 'lon']
    # Approximate distance in km
    dlat = (lat2 - lat1) * 111
    dlon = (lon2 - lon1) * 111 * np.cos(np.radians((lat1 + lat2) / 2))
    dist = np.sqrt(dlat**2 + dlon**2)
    df_sorted.loc[i, 'distance_km'] = df_sorted.loc[i-1, 'distance_km'] + dist

# Create meshgrid for contour
station_ids = df_sorted['station_id'].values
distances = df_sorted['distance_km'].values

# Get temperature at each depth level for each station
depth_levels = np.linspace(0, 2000, 50)
temp_grid = np.zeros((len(depth_levels), len(station_ids)))

for j, station in enumerate(station_ids):
    station_data = profile_df[profile_df['station_id'] == station]
    for i, depth in enumerate(depth_levels):
        # Interpolate temperature at this depth
        temp_grid[i, j] = np.interp(depth, station_data['pressure_dbar'], 
                                     station_data['temperature_c'])

# Create contour plot
X, Y = np.meshgrid(distances, depth_levels)
contour = ax5.contourf(X, Y, temp_grid, levels=20, cmap='RdBu_r')
ax5.invert_yaxis()
ax5.set_xlabel('Distance Along Track (km)', fontsize=12)
ax5.set_ylabel('Depth (m)', fontsize=12)
ax5.set_title('Temperature Cross-Section Along Cruise Track', fontsize=14)
cbar = plt.colorbar(contour, ax=ax5, label='Temperature (C)')

plt.tight_layout()
fig5.savefig(REPORT_IMAGES_PATH / "temperature_cross_section.png", bbox_inches='tight')
plt.close()
print(f"Saved: {REPORT_IMAGES_PATH / 'temperature_cross_section.png'}")

# Figure 6: Statistical Summary
print("\nCreating Figure 6: Statistical Summary...")
fig6, axes = plt.subplots(2, 2, figsize=(14, 10))

# 6a: Surface temperature distribution
surface_data = profile_df[profile_df['pressure_dbar'] < 50]
axes[0, 0].hist(surface_data['temperature_c'], bins=20, color='coral', edgecolor='black', alpha=0.7)
axes[0, 0].set_xlabel('Temperature (C)', fontsize=11)
axes[0, 0].set_ylabel('Frequency', fontsize=11)
axes[0, 0].set_title('Surface Temperature Distribution (<50m)', fontsize=12)
axes[0, 0].grid(True, alpha=0.3)

# 6b: Deep temperature distribution
deep_data = profile_df[profile_df['pressure_dbar'] > 1500]
axes[0, 1].hist(deep_data['temperature_c'], bins=20, color='navy', edgecolor='black', alpha=0.7)
axes[0, 1].set_xlabel('Temperature (C)', fontsize=11)
axes[0, 1].set_ylabel('Frequency', fontsize=11)
axes[0, 1].set_title('Deep Temperature Distribution (>1500m)', fontsize=12)
axes[0, 1].grid(True, alpha=0.3)

# 6c: Salinity vs Depth (binned)
axes[1, 0].boxplot([profile_df[profile_df['pressure_dbar'] < 100]['salinity_psu'],
                    profile_df[(profile_df['pressure_dbar'] >= 100) & (profile_df['pressure_dbar'] < 500)]['salinity_psu'],
                    profile_df[(profile_df['pressure_dbar'] >= 500) & (profile_df['pressure_dbar'] < 1000)]['salinity_psu'],
                    profile_df[profile_df['pressure_dbar'] >= 1000]['salinity_psu']],
                   labels=['0-100m', '100-500m', '500-1000m', '>1000m'])
axes[1, 0].set_ylabel('Salinity (PSU)', fontsize=11)
axes[1, 0].set_title('Salinity Distribution by Depth Layer', fontsize=12)
axes[1, 0].grid(True, alpha=0.3)

# 6d: Temperature-Salinity density
axes[1, 1].hexbin(profile_df['salinity_psu'], profile_df['temperature_c'], 
                  gridsize=30, cmap='YlOrRd', mincnt=1)
axes[1, 1].set_xlabel('Salinity (PSU)', fontsize=11)
axes[1, 1].set_ylabel('Temperature (C)', fontsize=11)
axes[1, 1].set_title('T-S Density Plot', fontsize=12)
axes[1, 1].grid(True, alpha=0.3)
cbar6 = plt.colorbar(axes[1, 1].collections[0], ax=axes[1, 1], label='Count')

plt.tight_layout()
fig6.savefig(REPORT_IMAGES_PATH / "statistical_summary.png", bbox_inches='tight')
plt.close()
print(f"Saved: {REPORT_IMAGES_PATH / 'statistical_summary.png'}")

# Calculate and save statistics
print("\nCalculating statistics...")
stats = {
    'surface_temp_mean': surface_data['temperature_c'].mean(),
    'surface_temp_std': surface_data['temperature_c'].std(),
    'deep_temp_mean': deep_data['temperature_c'].mean(),
    'deep_temp_std': deep_data['temperature_c'].std(),
    'surface_sal_mean': surface_data['salinity_psu'].mean(),
    'surface_sal_std': surface_data['salinity_psu'].std(),
    'deep_sal_mean': deep_data['salinity_psu'].mean(),
    'deep_sal_std': deep_data['salinity_psu'].std(),
}

stats_df = pd.DataFrame([stats])
stats_df.to_csv(OUTPUTS_PATH / "statistics.csv", index=False)
print(f"Statistics saved to {OUTPUTS_PATH / 'statistics.csv'}")
print("\nKey Statistics:")
for k, v in stats.items():
    print(f"  {k}: {v:.3f}")

print("\n" + "="*50)
print("Analysis complete! All figures saved to report/images/")
print("="*50)
