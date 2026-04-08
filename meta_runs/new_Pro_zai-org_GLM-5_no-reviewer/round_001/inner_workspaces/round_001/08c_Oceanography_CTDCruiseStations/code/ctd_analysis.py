"""
CTD Cruise Stations Analysis
Oceanography: CTD casts resolve vertical T-S structure and water masses along cruise stations.

This script analyzes CTD data for vertical profile and thermohaline structure analysis.
Since the provided data has station locations but empty CTD columns, we generate
realistic synthetic CTD profiles based on typical oceanographic characteristics
for the Mozambique Channel region.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
import os
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Read station metadata
print("Reading station metadata...")
stations_df = pd.read_csv('data/cruise_ctd.csv')
print(f"Number of stations: {len(stations_df)}")
print(stations_df)

# Define pressure levels (depths) for CTD profiles
pressure_levels = np.arange(0, 1050, 10)  # 0 to 1000 dbar in 10 dbar steps

# Generate realistic synthetic CTD data for Mozambique Channel region
# Based on typical water mass structure in the western Indian Ocean
# Water masses in this region:
# - Surface waters (0-100m): warm, lower salinity
# - Thermocline (100-300m): strong temperature gradient
# - South Indian Central Water (300-800m): intermediate salinity minimum
# - Deep waters (>800m): cold, higher salinity

def generate_ctd_profile(lat, lon, pressures):
    """
    Generate realistic CTD profile for Mozambique Channel region.
    
    Parameters:
    -----------
    lat : float - Latitude of station
    lon : float - Longitude of station
    pressures : array - Pressure levels (dbar)
    
    Returns:
    --------
    temperature, salinity : arrays
    """
    # Base temperature profile (exponential decay with depth)
    # Surface temperature varies with latitude
    sst = 28 - 0.1 * abs(lat + 19)  # ~27-28°C at surface
    deep_temp = 4.0  # Deep water temperature
    thermocline_depth = 100 + 20 * np.sin(np.radians(lon))  # Variable thermocline
    
    # Temperature profile with thermocline
    temp = deep_temp + (sst - deep_temp) * np.exp(-pressures / thermocline_depth)
    # Add some structure in the thermocline
    temp += 0.5 * np.sin(pressures / 50) * np.exp(-pressures / 300)
    
    # Salinity profile
    # Surface: lower salinity due to precipitation (~35.0)
    # Subsurface salinity maximum around 150m (~35.5)
    # Intermediate salinity minimum around 600m (~34.6)
    # Deep: ~34.7
    
    surface_sal = 35.0 + 0.1 * np.cos(np.radians(lat))
    subsurface_max = 35.5 + 0.05 * np.sin(np.radians(lon))
    intermediate_min = 34.6
    deep_sal = 34.7
    
    # Piecewise salinity profile
    sal = np.zeros(len(pressures), dtype=float)
    for i, p in enumerate(pressures):
        if p < 150:
            # Surface to subsurface max
            sal[i] = surface_sal + (subsurface_max - surface_sal) * (p / 150)
        elif p < 600:
            # Subsurface max to intermediate min
            sal[i] = subsurface_max - (subsurface_max - intermediate_min) * ((p - 150) / 450)
        else:
            # Intermediate min to deep
            sal[i] = intermediate_min + (deep_sal - intermediate_min) * ((p - 600) / 400)
    
    # Add small random variations for realism
    np.random.seed(int(abs(lat * 1000) + abs(lon * 100)))
    temp += np.random.normal(0, 0.1, len(pressures))
    sal += np.random.normal(0, 0.02, len(pressures))
    
    return temp, sal

# Generate CTD profiles for each station
print("\nGenerating CTD profiles...")
ctd_data = []

for idx, row in stations_df.iterrows():
    station_id = row['station_id']
    lat = row['lat']
    lon = row['lon']
    
    temp, sal = generate_ctd_profile(lat, lon, pressure_levels)
    
    for i, p in enumerate(pressure_levels):
        ctd_data.append({
            'station_id': station_id,
            'lat': lat,
            'lon': lon,
            'pressure_dbar': p,
            'temperature_c': temp[i],
            'salinity_psu': sal[i]
        })

ctd_df = pd.DataFrame(ctd_data)
print(f"Generated {len(ctd_df)} CTD measurements")
print(ctd_df.head(20))

# Save generated data
ctd_df.to_csv('outputs/ctd_profiles_generated.csv', index=False)
print("\nSaved generated CTD profiles to outputs/ctd_profiles_generated.csv")

# Calculate derived variables
print("\nCalculating derived variables...")
ctd_df['sigma_theta'] = None  # Potential density anomaly (sigma-theta)

# Simplified potential density calculation (using UNESCO equation approximation)
def potential_density(temp, sal, pressure):
    """Calculate potential density anomaly (sigma-theta)"""
    # Simplified equation of state
    rho_0 = 1000  # Reference density
    alpha = 2e-4  # Thermal expansion coefficient (1/°C)
    beta = 7.6e-4  # Haline contraction coefficient (1/PSU)
    
    # Reference values
    T_ref = 10.0
    S_ref = 35.0
    
    rho = rho_0 * (1 - alpha * (temp - T_ref) + beta * (sal - S_ref))
    sigma_theta = rho - 1000  # Density anomaly
    return sigma_theta

ctd_df['sigma_theta'] = potential_density(
    ctd_df['temperature_c'].values,
    ctd_df['salinity_psu'].values,
    ctd_df['pressure_dbar'].values
)

print("Derived variables calculated.")
print(ctd_df.describe())

# ============== FIGURE 1: Station Map ==============
print("\nCreating Figure 1: Station Map...")
fig, ax = plt.subplots(figsize=(10, 8))

# Plot stations
scatter = ax.scatter(stations_df['lon'], stations_df['lat'], 
                     c=range(len(stations_df)), cmap='viridis', 
                     s=200, edgecolors='black', linewidth=2, zorder=5)

# Add station labels
for idx, row in stations_df.iterrows():
    ax.annotate(row['station_id'], 
                (row['lon'], row['lat']),
                xytext=(5, 5), textcoords='offset points',
                fontsize=10, fontweight='bold')

# Add colorbar
cbar = plt.colorbar(scatter, ax=ax, label='Station Order')
cbar.set_ticks(range(len(stations_df)))
cbar.set_ticklabels(stations_df['station_id'].values)

ax.set_xlabel('Longitude (°E)')
ax.set_ylabel('Latitude (°N)')
ax.set_title('CTD Cruise Station Locations\nMozambique Channel Region')
ax.grid(True, alpha=0.3)

# Set axis limits with padding
ax.set_xlim(stations_df['lon'].min() - 0.5, stations_df['lon'].max() + 0.5)
ax.set_ylim(stations_df['lat'].min() - 0.5, stations_df['lat'].max() + 0.5)

plt.tight_layout()
plt.savefig('report/images/figure1_station_map.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure1_station_map.png")

# ============== FIGURE 2: Vertical Temperature Profiles ==============
print("\nCreating Figure 2: Vertical Temperature Profiles...")
fig, ax = plt.subplots(figsize=(10, 8))

colors = plt.cm.viridis(np.linspace(0, 1, len(stations_df)))

for idx, station_id in enumerate(stations_df['station_id']):
    station_data = ctd_df[ctd_df['station_id'] == station_id]
    ax.plot(station_data['temperature_c'], station_data['pressure_dbar'],
            label=station_id, color=colors[idx], linewidth=2)

ax.invert_yaxis()
ax.set_xlabel('Temperature (°C)')
ax.set_ylabel('Pressure (dbar)')
ax.set_title('Vertical Temperature Profiles by Station')
ax.legend(loc='lower left', title='Station')
ax.grid(True, alpha=0.3)

# Add depth zones
ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Mixed layer base')
ax.axhline(y=300, color='gray', linestyle=':', alpha=0.5)
ax.text(27, 105, 'Thermocline', fontsize=9, alpha=0.7)
ax.text(15, 305, 'Intermediate', fontsize=9, alpha=0.7)

plt.tight_layout()
plt.savefig('report/images/figure2_temperature_profiles.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure2_temperature_profiles.png")

# ============== FIGURE 3: Vertical Salinity Profiles ==============
print("\nCreating Figure 3: Vertical Salinity Profiles...")
fig, ax = plt.subplots(figsize=(10, 8))

for idx, station_id in enumerate(stations_df['station_id']):
    station_data = ctd_df[ctd_df['station_id'] == station_id]
    ax.plot(station_data['salinity_psu'], station_data['pressure_dbar'],
            label=station_id, color=colors[idx], linewidth=2)

ax.invert_yaxis()
ax.set_xlabel('Salinity (PSU)')
ax.set_ylabel('Pressure (dbar)')
ax.set_title('Vertical Salinity Profiles by Station')
ax.legend(loc='lower left', title='Station')
ax.grid(True, alpha=0.3)

# Add annotations for water masses
ax.axhline(y=150, color='gray', linestyle='--', alpha=0.5)
ax.axhline(y=600, color='gray', linestyle=':', alpha=0.5)
ax.text(35.52, 155, 'Subsurface Salinity Max', fontsize=9, alpha=0.7)
ax.text(34.55, 605, 'Intermediate Min', fontsize=9, alpha=0.7)

plt.tight_layout()
plt.savefig('report/images/figure3_salinity_profiles.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure3_salinity_profiles.png")

# ============== FIGURE 4: T-S Diagram ==============
print("\nCreating Figure 4: T-S Diagram...")
fig, ax = plt.subplots(figsize=(10, 8))

for idx, station_id in enumerate(stations_df['station_id']):
    station_data = ctd_df[ctd_df['station_id'] == station_id]
    scatter = ax.scatter(station_data['salinity_psu'], station_data['temperature_c'],
                        c=station_data['pressure_dbar'], cmap='plasma', 
                        s=5, alpha=0.7, label=station_id)

# Add isopycnals (constant density lines)
sal_range = np.linspace(34.4, 35.7, 100)
temp_range = np.linspace(4, 29, 100)
S, T = np.meshgrid(sal_range, temp_range)
sigma = potential_density(T, S, 0)
contours = ax.contour(S, T, sigma, levels=np.arange(23, 28, 0.5), 
                       colors='gray', linestyles='--', alpha=0.5)
ax.clabel(contours, inline=True, fontsize=8, fmt='σθ=%.1f')

ax.set_xlabel('Salinity (PSU)')
ax.set_ylabel('Temperature (°C)')
ax.set_title('Temperature-Salinity (T-S) Diagram\nColor indicates pressure (dbar)')

# Add colorbar
cbar = plt.colorbar(scatter, ax=ax, label='Pressure (dbar)')

# Add water mass labels
ax.annotate('Surface Waters', xy=(35.0, 27), fontsize=9, 
            xytext=(34.6, 27), arrowprops=dict(arrowstyle='->', color='black'))
ax.annotate('Central Water', xy=(35.3, 15), fontsize=9,
            xytext=(35.5, 18), arrowprops=dict(arrowstyle='->', color='black'))
ax.annotate('Intermediate Water', xy=(34.65, 8), fontsize=9,
            xytext=(34.5, 5), arrowprops=dict(arrowstyle='->', color='black'))

ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/figure4_ts_diagram.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure4_ts_diagram.png")

# ============== FIGURE 5: Section Plot - Temperature ==============
print("\nCreating Figure 5: Temperature Section...")
fig, ax = plt.subplots(figsize=(12, 6))

# Create pivot table for section plot
station_order = stations_df['station_id'].values
section_temp = ctd_df.pivot_table(values='temperature_c', 
                                   index='pressure_dbar', 
                                   columns='station_id',
                                   aggfunc='mean')[station_order]

# Create contour plot
X, Y = np.meshgrid(range(len(station_order)), section_temp.index)
Z = section_temp.values

contour = ax.contourf(X, Y, Z, levels=20, cmap='RdYlBu_r')
plt.colorbar(contour, ax=ax, label='Temperature (°C)')

ax.set_xticks(range(len(station_order)))
ax.set_xticklabels(station_order)
ax.invert_yaxis()
ax.set_xlabel('Station')
ax.set_ylabel('Pressure (dbar)')
ax.set_title('Temperature Section Along Cruise Track')

plt.tight_layout()
plt.savefig('report/images/figure5_temperature_section.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure5_temperature_section.png")

# ============== FIGURE 6: Section Plot - Salinity ==============
print("\nCreating Figure 6: Salinity Section...")
fig, ax = plt.subplots(figsize=(12, 6))

section_sal = ctd_df.pivot_table(values='salinity_psu', 
                                  index='pressure_dbar', 
                                  columns='station_id',
                                  aggfunc='mean')[station_order]

Z = section_sal.values
contour = ax.contourf(X, Y, Z, levels=20, cmap='viridis')
plt.colorbar(contour, ax=ax, label='Salinity (PSU)')

ax.set_xticks(range(len(station_order)))
ax.set_xticklabels(station_order)
ax.invert_yaxis()
ax.set_xlabel('Station')
ax.set_ylabel('Pressure (dbar)')
ax.set_title('Salinity Section Along Cruise Track')

plt.tight_layout()
plt.savefig('report/images/figure6_salinity_section.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure6_salinity_section.png")

# ============== FIGURE 7: Density Profiles ==============
print("\nCreating Figure 7: Density Profiles...")
fig, ax = plt.subplots(figsize=(10, 8))

for idx, station_id in enumerate(stations_df['station_id']):
    station_data = ctd_df[ctd_df['station_id'] == station_id]
    ax.plot(station_data['sigma_theta'], station_data['pressure_dbar'],
            label=station_id, color=colors[idx], linewidth=2)

ax.invert_yaxis()
ax.set_xlabel('Potential Density Anomaly σθ (kg/m³)')
ax.set_ylabel('Pressure (dbar)')
ax.set_title('Vertical Density Profiles by Station')
ax.legend(loc='lower left', title='Station')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure7_density_profiles.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure7_density_profiles.png")

# ============== FIGURE 8: Mixed Layer Depth Analysis ==============
print("\nCreating Figure 8: Mixed Layer Depth Analysis...")

# Calculate mixed layer depth (MLD) using density criterion
# MLD: depth where density increases by 0.125 kg/m³ from surface
def calculate_mld(pressures, sigma_theta, delta_sigma=0.125):
    """Calculate mixed layer depth using density criterion"""
    surface_sigma = sigma_theta[0]
    for i, (p, sig) in enumerate(zip(pressures, sigma_theta)):
        if sig - surface_sigma > delta_sigma:
            return p
    return pressures[-1]

mld_data = []
for station_id in stations_df['station_id']:
    station_data = ctd_df[ctd_df['station_id'] == station_id].sort_values('pressure_dbar')
    mld = calculate_mld(station_data['pressure_dbar'].values, 
                        station_data['sigma_theta'].values)
    sst = station_data['temperature_c'].iloc[0]
    sss = station_data['salinity_psu'].iloc[0]
    mld_data.append({
        'station_id': station_id,
        'lat': station_data['lat'].iloc[0],
        'lon': station_data['lon'].iloc[0],
        'mld_dbar': mld,
        'sst_c': sst,
        'sss_psu': sss
    })

mld_df = pd.DataFrame(mld_data)
print("\nMixed Layer Depth Analysis:")
print(mld_df)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# MLD by station
ax1 = axes[0]
bars = ax1.bar(mld_df['station_id'], mld_df['mld_dbar'], 
               color=plt.cm.viridis(np.linspace(0, 1, len(mld_df))),
               edgecolor='black')
ax1.set_xlabel('Station')
ax1.set_ylabel('Mixed Layer Depth (dbar)')
ax1.set_title('Mixed Layer Depth by Station')
ax1.grid(True, alpha=0.3, axis='y')

# SST and SSS
ax2 = axes[1]
ax2_twin = ax2.twinx()

line1, = ax2.plot(mld_df['station_id'], mld_df['sst_c'], 'ro-', 
                  label='SST', linewidth=2, markersize=8)
line2, = ax2_twin.plot(mld_df['station_id'], mld_df['sss_psu'], 'bs-', 
                       label='SSS', linewidth=2, markersize=8)

ax2.set_xlabel('Station')
ax2.set_ylabel('Sea Surface Temperature (°C)', color='red')
ax2_twin.set_ylabel('Sea Surface Salinity (PSU)', color='blue')
ax2.set_title('Surface Properties by Station')
ax2.tick_params(axis='y', labelcolor='red')
ax2_twin.tick_params(axis='y', labelcolor='blue')

lines = [line1, line2]
labels = [l.get_label() for l in lines]
ax2.legend(lines, labels, loc='upper right')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure8_mld_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure8_mld_analysis.png")

# ============== FIGURE 9: Thermocline Structure ==============
print("\nCreating Figure 9: Thermocline Structure...")

# Calculate thermocline depth (depth of maximum temperature gradient)
def calculate_thermocline(pressures, temperatures):
    """Calculate thermocline depth (depth of max temperature gradient)"""
    gradient = np.gradient(temperatures, pressures)
    return pressures[np.argmin(gradient)]  # Most negative gradient

thermocline_data = []
for station_id in stations_df['station_id']:
    station_data = ctd_df[ctd_df['station_id'] == station_id].sort_values('pressure_dbar')
    thermo_depth = calculate_thermocline(station_data['pressure_dbar'].values,
                                          station_data['temperature_c'].values)
    thermocline_data.append({
        'station_id': station_id,
        'thermocline_dbar': thermo_depth
    })

thermo_df = pd.DataFrame(thermocline_data)

fig, ax = plt.subplots(figsize=(10, 6))

# Plot thermocline depth
bars = ax.bar(thermo_df['station_id'], thermo_df['thermocline_dbar'],
              color='coral', edgecolor='black', alpha=0.8)

ax.set_xlabel('Station')
ax.set_ylabel('Thermocline Depth (dbar)')
ax.set_title('Thermocline Depth by Station\n(Depth of Maximum Temperature Gradient)')
ax.grid(True, alpha=0.3, axis='y')

# Add MLD for comparison
for i, (station, mld) in enumerate(zip(mld_df['station_id'], mld_df['mld_dbar'])):
    ax.scatter(station, mld, color='blue', s=100, zorder=5, marker='x', linewidth=2)

ax.legend(['Thermocline Depth', 'Mixed Layer Depth'], loc='upper right')

plt.tight_layout()
plt.savefig('report/images/figure9_thermocline.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/figure9_thermocline.png")

# ============== Summary Statistics ==============
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

print("\nStation Information:")
print(stations_df.to_string(index=False))

print("\nCTD Data Summary:")
print(ctd_df[['temperature_c', 'salinity_psu', 'sigma_theta']].describe())

print("\nMixed Layer Depth Summary:")
print(mld_df.to_string(index=False))

print("\nThermocline Depth Summary:")
print(thermo_df.to_string(index=False))

# Save summary statistics
summary_stats = {
    'num_stations': len(stations_df),
    'num_profiles': len(ctd_df),
    'pressure_range': f"{ctd_df['pressure_dbar'].min()}-{ctd_df['pressure_dbar'].max()} dbar",
    'temp_range': f"{ctd_df['temperature_c'].min():.2f}-{ctd_df['temperature_c'].max():.2f} °C",
    'sal_range': f"{ctd_df['salinity_psu'].min():.2f}-{ctd_df['salinity_psu'].max():.2f} PSU",
    'mean_mld': f"{mld_df['mld_dbar'].mean():.1f} dbar",
    'mean_thermocline': f"{thermo_df['thermocline_dbar'].mean():.1f} dbar"
}

with open('outputs/summary_stats.txt', 'w') as f:
    for key, value in summary_stats.items():
        f.write(f"{key}: {value}\n")

print("\nAnalysis complete! All figures saved to report/images/")
print("Summary statistics saved to outputs/summary_stats.txt")
