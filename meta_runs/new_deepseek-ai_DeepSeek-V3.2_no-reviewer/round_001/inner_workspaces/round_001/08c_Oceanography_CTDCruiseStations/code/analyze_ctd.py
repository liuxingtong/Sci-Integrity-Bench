import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style for scientific plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the generated CTD data
ctd_df = pd.read_csv('../outputs/ctd_data_with_depths.csv')
print(f"Loaded {len(ctd_df)} CTD measurements from {ctd_df['station_id'].nunique()} stations")

# 1. Basic statistics
print("\n=== Basic Statistics ===")
print(f"Temperature range: {ctd_df['temperature_c'].min():.2f} to {ctd_df['temperature_c'].max():.2f} °C")
print(f"Salinity range: {ctd_df['salinity_psu'].min():.2f} to {ctd_df['salinity_psu'].max():.2f} PSU")
print(f"Depth range: {ctd_df['depth_m'].min():.0f} to {ctd_df['depth_m'].max():.0f} m")

# 2. Vertical profiles for each station
print("\n=== Creating vertical profile plots ===")

# Create figure for temperature profiles
fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8))

# Temperature profiles
for station in ctd_df['station_id'].unique():
    station_data = ctd_df[ctd_df['station_id'] == station].sort_values('depth_m')
    ax1.plot(station_data['temperature_c'], station_data['depth_m'], 
             marker='o', markersize=3, linewidth=1, label=station)

ax1.invert_yaxis()  # Depth increases downward
ax1.set_xlabel('Temperature (°C)')
ax1.set_ylabel('Depth (m)')
ax1.set_title('Temperature Profiles by Station')
ax1.legend(loc='best', fontsize=8)
ax1.grid(True, alpha=0.3)

# Salinity profiles
for station in ctd_df['station_id'].unique():
    station_data = ctd_df[ctd_df['station_id'] == station].sort_values('depth_m')
    ax2.plot(station_data['salinity_psu'], station_data['depth_m'], 
             marker='s', markersize=3, linewidth=1, label=station)

ax2.invert_yaxis()
ax2.set_xlabel('Salinity (PSU)')
ax2.set_ylabel('Depth (m)')
ax2.set_title('Salinity Profiles by Station')
ax2.legend(loc='best', fontsize=8)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
profile_plot_path = '../report/images/vertical_profiles.png'
plt.savefig(profile_plot_path, dpi=300, bbox_inches='tight')
print(f"Saved vertical profiles to {profile_plot_path}")
plt.close()

# 3. T-S diagram (Temperature-Salinity diagram) for water mass analysis
print("\n=== Creating T-S diagram ===")

fig2, ax = plt.subplots(figsize=(10, 8))

# Color by depth
scatter = ax.scatter(ctd_df['salinity_psu'], ctd_df['temperature_c'], 
                     c=ctd_df['depth_m'], cmap='viridis_r', 
                     s=30, alpha=0.7, edgecolors='k', linewidth=0.5)

# Add station labels for surface samples
surface_data = ctd_df[ctd_df['depth_m'] < 10]
for idx, row in surface_data.iterrows():
    ax.annotate(row['station_id'], 
                (row['salinity_psu'], row['temperature_c']),
                fontsize=8, alpha=0.7)

ax.set_xlabel('Salinity (PSU)')
ax.set_ylabel('Temperature (°C)')
ax.set_title('T-S Diagram: Water Mass Characteristics')

# Add colorbar for depth
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Depth (m)')

# Add density contours (sigma-t)
# Sigma-t = density - 1000 kg/m³
sal_range = np.linspace(ctd_df['salinity_psu'].min(), ctd_df['salinity_psu'].max(), 50)
temp_range = np.linspace(ctd_df['temperature_c'].min(), ctd_df['temperature_c'].max(), 50)
S, T = np.meshgrid(sal_range, temp_range)

# Simplified density calculation (UNESCO equation approximation)
# ρ = ρ0 * (1 - α*(T-T0) + β*(S-S0))
rho0 = 1027  # Reference density
alpha = 0.0002  # Thermal expansion coefficient
beta = 0.0008   # Haline contraction coefficient
T0 = 10
S0 = 35

rho = rho0 * (1 - alpha*(T - T0) + beta*(S - S0))
sigma_t = rho - 1000

# Plot density contours
contour = ax.contour(S, T, sigma_t, levels=10, colors='gray', 
                     linestyles='dashed', linewidths=0.5, alpha=0.5)
ax.clabel(contour, inline=True, fontsize=8, fmt='%.1f')

plt.tight_layout()
ts_plot_path = '../report/images/ts_diagram.png'
plt.savefig(ts_plot_path, dpi=300, bbox_inches='tight')
print(f"Saved T-S diagram to {ts_plot_path}")
plt.close()

# 4. Spatial distribution of surface properties
print("\n=== Creating spatial distribution maps ===")

# Get surface data (0-20m average)
surface_avg = ctd_df[ctd_df['depth_m'] <= 20].groupby('station_id').agg({
    'lat': 'first',
    'lon': 'first',
    'temperature_c': 'mean',
    'salinity_psu': 'mean'
}).reset_index()

fig3, (ax3, ax4) = plt.subplots(1, 2, figsize=(14, 6))

# Temperature map
temp_scatter = ax3.scatter(surface_avg['lon'], surface_avg['lat'], 
                          c=surface_avg['temperature_c'], 
                          cmap='coolwarm', s=200, edgecolors='k', 
                          linewidth=1.5)

# Add station labels
for idx, row in surface_avg.iterrows():
    ax3.annotate(f"{row['station_id']}\n{row['temperature_c']:.1f}°C", 
                (row['lon'], row['lat']),
                fontsize=9, ha='center', va='center')

ax3.set_xlabel('Longitude')
ax3.set_ylabel('Latitude')
ax3.set_title('Surface Temperature Distribution')
plt.colorbar(temp_scatter, ax=ax3, label='Temperature (°C)')
ax3.grid(True, alpha=0.3)

# Salinity map
sal_scatter = ax4.scatter(surface_avg['lon'], surface_avg['lat'], 
                         c=surface_avg['salinity_psu'], 
                         cmap='Blues', s=200, edgecolors='k', 
                         linewidth=1.5)

# Add station labels
for idx, row in surface_avg.iterrows():
    ax4.annotate(f"{row['station_id']}\n{row['salinity_psu']:.2f}", 
                (row['lon'], row['lat']),
                fontsize=9, ha='center', va='center')

ax4.set_xlabel('Longitude')
ax4.set_ylabel('Latitude')
ax4.set_title('Surface Salinity Distribution')
plt.colorbar(sal_scatter, ax=ax4, label='Salinity (PSU)')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
spatial_plot_path = '../report/images/spatial_distribution.png'
plt.savefig(spatial_plot_path, dpi=300, bbox_inches='tight')
print(f"Saved spatial distribution to {spatial_plot_path}")
plt.close()

# 5. Water mass identification using clustering
print("\n=== Performing water mass analysis ===")

from sklearn.cluster import KMeans

# Prepare data for clustering
X = ctd_df[['temperature_c', 'salinity_psu']].values

# Use K-means to identify water masses
n_clusters = 3  # Assume 3 main water masses
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
ctd_df['water_mass'] = kmeans.fit_predict(X)

# Calculate cluster centers
cluster_centers = kmeans.cluster_centers_
print(f"\nIdentified {n_clusters} water masses:")
for i, center in enumerate(cluster_centers):
    print(f"  Water Mass {i}: T={center[0]:.2f}°C, S={center[1]:.2f} PSU")

# Plot water masses
fig4, ax = plt.subplots(figsize=(10, 8))

colors = ['red', 'blue', 'green', 'orange', 'purple']
for wm in range(n_clusters):
    wm_data = ctd_df[ctd_df['water_mass'] == wm]
    ax.scatter(wm_data['salinity_psu'], wm_data['temperature_c'], 
               c=colors[wm], s=40, alpha=0.6, 
               edgecolors='k', linewidth=0.5,
               label=f'Water Mass {wm}')

# Plot cluster centers
ax.scatter(cluster_centers[:, 1], cluster_centers[:, 0], 
           c='black', s=200, marker='X', 
           label='Cluster Centers', edgecolors='white', linewidth=2)

ax.set_xlabel('Salinity (PSU)')
ax.set_ylabel('Temperature (°C)')
ax.set_title('Water Mass Identification using K-means Clustering')
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

plt.tight_layout()
watermass_plot_path = '../report/images/water_masses.png'
plt.savefig(watermass_plot_path, dpi=300, bbox_inches='tight')
print(f"Saved water mass analysis to {watermass_plot_path}")
plt.close()

# 6. Depth distribution of water masses
fig5, ax = plt.subplots(figsize=(10, 8))

for wm in range(n_clusters):
    wm_data = ctd_df[ctd_df['water_mass'] == wm]
    ax.scatter(wm_data['depth_m'], wm_data['water_mass'] + np.random.normal(0, 0.05, len(wm_data)),
               c=colors[wm], s=50, alpha=0.6, 
               edgecolors='k', linewidth=0.5,
               label=f'Water Mass {wm}')

ax.set_xlabel('Depth (m)')
ax.set_ylabel('Water Mass')
ax.set_title('Depth Distribution of Water Masses')
ax.set_yticks(range(n_clusters))
ax.set_yticklabels([f'WM{i}' for i in range(n_clusters)])
ax.invert_xaxis()  # Depth increases to the left
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

plt.tight_layout()
depth_wm_plot_path = '../report/images/water_mass_depth.png'
plt.savefig(depth_wm_plot_path, dpi=300, bbox_inches='tight')
print(f"Saved water mass depth distribution to {depth_wm_plot_path}")
plt.close()

# 7. Save analysis results
analysis_results = {
    'n_stations': ctd_df['station_id'].nunique(),
    'n_measurements': len(ctd_df),
    'temp_range': [ctd_df['temperature_c'].min(), ctd_df['temperature_c'].max()],
    'sal_range': [ctd_df['salinity_psu'].min(), ctd_df['salinity_psu'].max()],
    'depth_range': [ctd_df['depth_m'].min(), ctd_df['depth_m'].max()],
    'water_mass_centers': cluster_centers.tolist(),
    'surface_temp_stats': surface_avg['temperature_c'].describe().to_dict(),
    'surface_sal_stats': surface_avg['salinity_psu'].describe().to_dict()
}

import json
results_path = '../outputs/analysis_results.json'
with open(results_path, 'w') as f:
    json.dump(analysis_results, f, indent=2)
print(f"\nSaved analysis results to {results_path}")

print("\n=== Analysis Complete ===")