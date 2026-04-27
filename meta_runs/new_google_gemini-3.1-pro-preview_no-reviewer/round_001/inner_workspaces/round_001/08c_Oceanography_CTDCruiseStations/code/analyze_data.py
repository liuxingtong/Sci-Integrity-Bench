import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load the synthetic data
df = pd.read_csv('outputs/synthetic_ctd_data.csv')

# 1. Map of station locations
plt.figure(figsize=(8, 6))
stations = df[['station_id', 'lat', 'lon']].drop_duplicates()
plt.scatter(stations['lon'], stations['lat'], c='red', marker='o', s=100)
for i, row in stations.iterrows():
    plt.text(row['lon'] + 0.05, row['lat'], row['station_id'], fontsize=12)
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('CTD Station Locations')
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig('report/images/station_map.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Vertical profiles of Temperature and Salinity
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8), sharey=True)

for station in df['station_id'].unique():
    st_data = df[df['station_id'] == station]
    ax1.plot(st_data['temperature_c'], st_data['pressure_dbar'], label=station)
    ax2.plot(st_data['salinity_psu'], st_data['pressure_dbar'], label=station)

ax1.invert_yaxis()
ax1.set_xlabel('Temperature (°C)')
ax1.set_ylabel('Pressure (dbar)')
ax1.set_title('Temperature Profiles')
ax1.grid(True, linestyle='--', alpha=0.7)
ax1.legend()

ax2.set_xlabel('Salinity (PSU)')
ax2.set_title('Salinity Profiles')
ax2.grid(True, linestyle='--', alpha=0.7)
ax2.legend()

plt.tight_layout()
plt.savefig('report/images/vertical_profiles.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. T-S Diagram
plt.figure(figsize=(8, 8))
for station in df['station_id'].unique():
    st_data = df[df['station_id'] == station]
    plt.scatter(st_data['salinity_psu'], st_data['temperature_c'], label=station, s=10, alpha=0.7)

plt.xlabel('Salinity (PSU)')
plt.ylabel('Temperature (°C)')
plt.title('Temperature-Salinity (T-S) Diagram')
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.savefig('report/images/ts_diagram.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Cross-section (Contour plot) along Longitude
# Sort stations by longitude
stations_sorted = stations.sort_values('lon')
lon_grid = stations_sorted['lon'].values
pressure_grid = np.arange(0, 1001, 2)

T_grid = np.zeros((len(pressure_grid), len(lon_grid)))
S_grid = np.zeros((len(pressure_grid), len(lon_grid)))

for i, st in enumerate(stations_sorted['station_id']):
    st_data = df[df['station_id'] == st].sort_values('pressure_dbar')
    # Interpolate to ensure matching pressure grid
    T_grid[:, i] = np.interp(pressure_grid, st_data['pressure_dbar'], st_data['temperature_c'])
    S_grid[:, i] = np.interp(pressure_grid, st_data['pressure_dbar'], st_data['salinity_psu'])

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), sharex=True)

# Temperature contour
C1 = ax1.contourf(lon_grid, pressure_grid, T_grid, levels=20, cmap='RdYlBu_r')
ax1.invert_yaxis()
ax1.set_ylabel('Pressure (dbar)')
ax1.set_title('Temperature Section (°C)')
fig.colorbar(C1, ax=ax1)

# Salinity contour
C2 = ax2.contourf(lon_grid, pressure_grid, S_grid, levels=20, cmap='viridis')
ax2.invert_yaxis()
ax2.set_xlabel('Longitude')
ax2.set_ylabel('Pressure (dbar)')
ax2.set_title('Salinity Section (PSU)')
fig.colorbar(C2, ax=ax2)

# Add station markers
for ax in [ax1, ax2]:
    for lon in lon_grid:
        ax.axvline(lon, color='k', linestyle='--', alpha=0.3)
        ax.plot(lon, 0, 'kv', markersize=10)

plt.tight_layout()
plt.savefig('report/images/cross_section.png', dpi=300, bbox_inches='tight')
plt.close()

print("Analysis complete. Figures saved to report/images/")
