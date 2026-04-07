import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load data
ctd_path = '../outputs/synthetic_ctd_profiles.csv'
ctd_df = pd.read_csv(ctd_path)

# Recreate water_mass classification (same as in part1)
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

# Calculate mean profiles for visualization
mean_temp_by_depth = ctd_df.groupby('pressure_dbar')['temperature_c'].mean()
mean_sal_by_depth = ctd_df.groupby('pressure_dbar')['salinity_psu'].mean()
std_temp_by_depth = ctd_df.groupby('pressure_dbar')['temperature_c'].std()
std_sal_by_depth = ctd_df.groupby('pressure_dbar')['salinity_psu'].std()

print("Generating visualizations...")

# Figure 1: Vertical profiles for all stations
fig1, axes1 = plt.subplots(1, 2, figsize=(14, 10))

# Temperature profiles
for station in ctd_df['station_id'].unique():
    station_data = ctd_df[ctd_df['station_id'] == station]
    axes1[0].plot(station_data['temperature_c'], station_data['pressure_dbar'], 
                  linewidth=1.5, alpha=0.7, label=station)

axes1[0].invert_yaxis()
axes1[0].set_xlabel('Temperature (°C)', fontsize=12)
axes1[0].set_ylabel('Pressure (dbar)', fontsize=12)
axes1[0].set_title('Temperature Profiles - All Stations', fontsize=14, fontweight='bold')
axes1[0].legend(loc='best', fontsize=9)
axes1[0].grid(True, alpha=0.3)

# Salinity profiles
for station in ctd_df['station_id'].unique():
    station_data = ctd_df[ctd_df['station_id'] == station]
    axes1[1].plot(station_data['salinity_psu'], station_data['pressure_dbar'], 
                  linewidth=1.5, alpha=0.7, label=station)

axes1[1].invert_yaxis()
axes1[1].set_xlabel('Salinity (psu)', fontsize=12)
axes1[1].set_ylabel('Pressure (dbar)', fontsize=12)
axes1[1].set_title('Salinity Profiles - All Stations', fontsize=14, fontweight='bold')
axes1[1].legend(loc='best', fontsize=9)
axes1[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/all_stations_profiles.png', dpi=300, bbox_inches='tight')
plt.close(fig1)
print("  - All stations profiles saved to report/images/all_stations_profiles.png")

# Figure 2: T-S diagrams colored by station
fig2, axes2 = plt.subplots(1, 2, figsize=(16, 8))

# T-S diagram with station colors
stations = ctd_df['station_id'].unique()
colors = plt.cm.tab10(np.linspace(0, 1, len(stations)))

for i, station in enumerate(stations):
    station_data = ctd_df[ctd_df['station_id'] == station]
    axes2[0].scatter(station_data['salinity_psu'], station_data['temperature_c'], 
                     c=[colors[i]], s=15, alpha=0.6, label=station, edgecolors='none')

axes2[0].set_xlabel('Salinity (psu)', fontsize=12)
axes2[0].set_ylabel('Temperature (°C)', fontsize=12)
axes2[0].set_title('T-S Diagram by Station', fontsize=14, fontweight='bold')
axes2[0].legend(loc='best', fontsize=9)
axes2[0].grid(True, alpha=0.3)

# T-S diagram colored by pressure
scatter = axes2[1].scatter(ctd_df['salinity_psu'], ctd_df['temperature_c'], 
                           c=ctd_df['pressure_dbar'], cmap='viridis', 
                           s=15, alpha=0.7, edgecolors='none')
axes2[1].set_xlabel('Salinity (psu)', fontsize=12)
axes2[1].set_ylabel('Temperature (°C)', fontsize=12)
axes2[1].set_title('T-S Diagram by Pressure', fontsize=14, fontweight='bold')
axes2[1].grid(True, alpha=0.3)
plt.colorbar(scatter, ax=axes2[1], label='Pressure (dbar)')

plt.tight_layout()
plt.savefig('../report/images/ts_diagrams.png', dpi=300, bbox_inches='tight')
plt.close(fig2)
print("  - T-S diagrams saved to report/images/ts_diagrams.png")

# Figure 3: Water mass distribution
fig3, axes3 = plt.subplots(1, 2, figsize=(14, 7))

# Water mass T-S diagram
water_masses = ctd_df['water_mass'].unique()
colors_wm = plt.cm.Set2(np.linspace(0, 1, len(water_masses)))

for i, wm in enumerate(water_masses):
    wm_data = ctd_df[ctd_df['water_mass'] == wm]
    axes3[0].scatter(wm_data['salinity_psu'], wm_data['temperature_c'], 
                     c=[colors_wm[i]], s=15, alpha=0.7, label=wm, edgecolors='none')

axes3[0].set_xlabel('Salinity (psu)', fontsize=12)
axes3[0].set_ylabel('Temperature (°C)', fontsize=12)
axes3[0].set_title('Water Masses in T-S Space', fontsize=14, fontweight='bold')
axes3[0].legend(loc='best', fontsize=9)
axes3[0].grid(True, alpha=0.3)

# Water mass vertical distribution
# Create a stacked bar chart of water mass proportion by depth range
depth_bins = [0, 100, 300, 1000, 2000]
depth_labels = ['0-100m', '100-300m', '300-1000m', '1000-2000m']
ctd_df['depth_bin'] = pd.cut(ctd_df['pressure_dbar'], bins=depth_bins, labels=depth_labels)

wm_by_depth = pd.crosstab(ctd_df['depth_bin'], ctd_df['water_mass'], normalize='index')
wm_by_depth.plot(kind='bar', stacked=True, ax=axes3[1], colormap='Set2')
axes3[1].set_xlabel('Depth Range', fontsize=12)
axes3[1].set_ylabel('Proportion', fontsize=12)
axes3[1].set_title('Water Mass Distribution by Depth', fontsize=14, fontweight='bold')
axes3[1].legend(loc='upper right', fontsize=9)
axes3[1].grid(True, alpha=0.3, axis='y')
axes3[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('../report/images/water_mass_analysis.png', dpi=300, bbox_inches='tight')
plt.close(fig3)
print("  - Water mass analysis saved to report/images/water_mass_analysis.png")

# Figure 4: Spatial distribution of surface properties
fig4, axes4 = plt.subplots(1, 2, figsize=(14, 7))

# Get surface data (0-50m)
surface_data = ctd_df[ctd_df['pressure_dbar'] <= 50].groupby('station_id').agg({
    'lat': 'first', 'lon': 'first', 'temperature_c': 'mean', 'salinity_psu': 'mean'
}).reset_index()

# Surface temperature map
sc1 = axes4[0].scatter(surface_data['lon'], surface_data['lat'], 
                       c=surface_data['temperature_c'], cmap='RdYlBu_r', 
                       s=200, edgecolors='black', linewidth=1.5)
for i, row in surface_data.iterrows():
    axes4[0].text(row['lon']+0.05, row['lat']+0.05, f"{row['temperature_c']:.1f}°C", 
                  fontsize=9, fontweight='bold')
axes4[0].set_xlabel('Longitude (°E)', fontsize=12)
axes4[0].set_ylabel('Latitude (°S)', fontsize=12)
axes4[0].set_title('Surface Temperature Distribution', fontsize=14, fontweight='bold')
axes4[0].grid(True, alpha=0.3)
plt.colorbar(sc1, ax=axes4[0], label='Temperature (°C)')

# Surface salinity map
sc2 = axes4[1].scatter(surface_data['lon'], surface_data['lat'], 
                       c=surface_data['salinity_psu'], cmap='Blues', 
                       s=200, edgecolors='black', linewidth=1.5)
for i, row in surface_data.iterrows():
    axes4[1].text(row['lon']+0.05, row['lat']+0.05, f"{row['salinity_psu']:.2f}", 
                  fontsize=9, fontweight='bold')
axes4[1].set_xlabel('Longitude (°E)', fontsize=12)
axes4[1].set_ylabel('Latitude (°S)', fontsize=12)
axes4[1].set_title('Surface Salinity Distribution', fontsize=14, fontweight='bold')
axes4[1].grid(True, alpha=0.3)
plt.colorbar(sc2, ax=axes4[1], label='Salinity (psu)')

plt.tight_layout()
plt.savefig('../report/images/surface_properties.png', dpi=300, bbox_inches='tight')
plt.close(fig4)
print("  - Surface properties map saved to report/images/surface_properties.png")

# Figure 5: Mean vertical profiles with variability
fig5, axes5 = plt.subplots(1, 2, figsize=(14, 10))

# Mean temperature profile with standard deviation
axes5[0].plot(mean_temp_by_depth.values, mean_temp_by_depth.index, 'r-', linewidth=3, label='Mean')
axes5[0].fill_betweenx(mean_temp_by_depth.index, 
                       mean_temp_by_depth.values - std_temp_by_depth.values,
                       mean_temp_by_depth.values + std_temp_by_depth.values,
                       alpha=0.3, color='red', label='±1 SD')
axes5[0].invert_yaxis()
axes5[0].set_xlabel('Temperature (°C)', fontsize=12)
axes5[0].set_ylabel('Pressure (dbar)', fontsize=12)
axes5[0].set_title('Mean Temperature Profile with Variability', fontsize=14, fontweight='bold')
axes5[0].legend(loc='best', fontsize=10)
axes5[0].grid(True, alpha=0.3)

# Mean salinity profile with standard deviation
axes5[1].plot(mean_sal_by_depth.values, mean_sal_by_depth.index, 'b-', linewidth=3, label='Mean')
axes5[1].fill_betweenx(mean_sal_by_depth.index,
                       mean_sal_by_depth.values - std_sal_by_depth.values,
                       mean_sal_by_depth.values + std_sal_by_depth.values,
                       alpha=0.3, color='blue', label='±1 SD')
axes5[1].invert_yaxis()
axes5[1].set_xlabel('Salinity (psu)', fontsize=12)
axes5[1].set_ylabel('Pressure (dbar)', fontsize=12)
axes5[1].set_title('Mean Salinity Profile with Variability', fontsize=14, fontweight='bold')
axes5[1].legend(loc='best', fontsize=10)
axes5[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/mean_profiles_variability.png', dpi=300, bbox_inches='tight')
plt.close(fig5)
print("  - Mean profiles with variability saved to report/images/mean_profiles_variability.png")

print("\nAll visualizations generated successfully!")