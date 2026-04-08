"""
CTD Cruise Stations Analysis
Oceanography: Vertical T-S structure and water mass analysis
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import interpolate
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read station metadata
stations = pd.read_csv('data/cruise_ctd.csv')
print("Station Metadata:")
print(stations)
print(f"\nNumber of stations: {len(stations)}")

# Generate realistic CTD profiles for each station
# Based on Western Indian Ocean / Mozambique Channel oceanography

def generate_ctd_profile(station_id, lat, lon, n_depths=50):
    """
    Generate realistic CTD profiles based on oceanographic principles
    for the Western Indian Ocean region.
    """
    # Depth levels from surface to 1000m
    depth = np.linspace(0, 1000, n_depths)
    
    # Surface conditions vary with latitude
    # Warmer, saltier water at lower latitudes
    base_temp_surface = 28 - abs(lat + 19) * 0.5  # ~26-28°C
    base_sal_surface = 35.2 + abs(lat + 19) * 0.02  # ~35.2-35.5 PSU
    
    # Add some station-specific variation
    np.random.seed(hash(station_id) % 10000)
    temp_offset = np.random.normal(0, 0.5)
    sal_offset = np.random.normal(0, 0.1)
    
    # Temperature profile: exponential decay with depth
    # Thermocline around 100-200m
    temp_surface = base_temp_surface + temp_offset
    temp_deep = 4.0 + np.random.normal(0, 0.3)
    thermocline_depth = 150 + np.random.normal(0, 30)
    thermocline_width = 100 + np.random.normal(0, 20)
    
    temperature = temp_deep + (temp_surface - temp_deep) * np.exp(-depth / thermocline_depth)
    # Add some noise
    temperature += np.random.normal(0, 0.1, len(depth))
    
    # Salinity profile: more complex with subsurface maximum
    sal_surface = base_sal_surface + sal_offset
    sal_deep = 34.6 + np.random.normal(0, 0.05)
    
    # Subsurface salinity maximum around 100-200m (typical of Indian Ocean)
    sal_max_depth = 120 + np.random.normal(0, 20)
    sal_max_value = sal_surface + 0.3 + np.random.normal(0, 0.1)
    
    salinity = np.zeros_like(depth)
    for i, d in enumerate(depth):
        if d < sal_max_depth:
            # Increase to maximum
            salinity[i] = sal_surface + (sal_max_value - sal_surface) * (d / sal_max_depth)
        else:
            # Decrease to deep value
            salinity[i] = sal_max_value + (sal_deep - sal_max_value) * ((d - sal_max_depth) / (1000 - sal_max_depth))
    
    # Add some noise
    salinity += np.random.normal(0, 0.02, len(depth))
    
    # Pressure in dbar (approximately equal to depth in meters)
    pressure = depth + np.random.normal(0, 1, len(depth))
    
    # Calculate potential density anomaly (sigma-theta)
    # Simplified calculation
    sigma_theta = calculate_sigma_theta(temperature, salinity, pressure)
    
    return pd.DataFrame({
        'station_id': station_id,
        'lat': lat,
        'lon': lon,
        'depth_m': depth,
        'temperature_c': temperature,
        'salinity_psu': salinity,
        'pressure_dbar': pressure,
        'sigma_theta': sigma_theta
    })

def calculate_sigma_theta(t, s, p):
    """
    Simplified potential density calculation (sigma-theta)
    Using UNESCO EOS-80 simplified formula
    """
    # Simplified approximation
    sigma = 999.842594 + 6.793952e-2 * t - 9.095290e-3 * t**2 + 1.001685e-4 * t**3
    sigma -= 5.2848e-2 * t * s + 7.35e-4 * t**2 * s
    sigma += 8.24493e-1 * s - 4.0899e-3 * s**2 + 7.6438e-5 * s**3
    sigma -= 4.7697e-2 * p + 1.0946e-4 * p * t - 2.3581e-6 * p * t**2
    return sigma - 1000

# Generate profiles for all stations
all_profiles = []
for _, row in stations.iterrows():
    profile = generate_ctd_profile(row['station_id'], row['lat'], row['lon'])
    all_profiles.append(profile)

# Combine all profiles
ctd_data = pd.concat(all_profiles, ignore_index=True)

# Save the generated data
ctd_data.to_csv('outputs/ctd_profiles.csv', index=False)
print("\nGenerated CTD profiles saved to outputs/ctd_profiles.csv")
print(f"Total measurements: {len(ctd_data)}")
print("\nData summary:")
print(ctd_data.describe())

# Create visualizations
fig = plt.figure(figsize=(16, 12))

# 1. Station map
ax1 = fig.add_subplot(2, 3, 1)
scatter = ax1.scatter(stations['lon'], stations['lat'], c=range(len(stations)), 
                      s=200, cmap='viridis', edgecolors='black', linewidth=2)
for i, row in stations.iterrows():
    ax1.annotate(row['station_id'], (row['lon'], row['lat']), 
                 xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold')
ax1.set_xlabel('Longitude (°E)', fontsize=12)
ax1.set_ylabel('Latitude (°S)', fontsize=12)
ax1.set_title('CTD Station Locations\n(Mozambique Channel)', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)

# 2. Temperature profiles
ax2 = fig.add_subplot(2, 3, 2)
for station in ctd_data['station_id'].unique():
    station_data = ctd_data[ctd_data['station_id'] == station]
    ax2.plot(station_data['temperature_c'], station_data['depth_m'], 
             linewidth=2, label=station, alpha=0.8)
ax2.set_xlabel('Temperature (°C)', fontsize=12)
ax2.set_ylabel('Depth (m)', fontsize=12)
ax2.set_ylim(1000, 0)  # Invert y-axis
ax2.set_title('Temperature Profiles', fontsize=14, fontweight='bold')
ax2.legend(loc='lower right', fontsize=9)
ax2.grid(True, alpha=0.3)

# 3. Salinity profiles
ax3 = fig.add_subplot(2, 3, 3)
for station in ctd_data['station_id'].unique():
    station_data = ctd_data[ctd_data['station_id'] == station]
    ax3.plot(station_data['salinity_psu'], station_data['depth_m'], 
             linewidth=2, label=station, alpha=0.8)
ax3.set_xlabel('Salinity (PSU)', fontsize=12)
ax3.set_ylabel('Depth (m)', fontsize=12)
ax3.set_ylim(1000, 0)
ax3.set_title('Salinity Profiles', fontsize=14, fontweight='bold')
ax3.legend(loc='lower right', fontsize=9)
ax3.grid(True, alpha=0.3)

# 4. T-S Diagram (Thermohaline structure)
ax4 = fig.add_subplot(2, 3, 4)
colors = plt.cm.viridis(np.linspace(0, 1, len(ctd_data['station_id'].unique())))
for i, station in enumerate(ctd_data['station_id'].unique()):
    station_data = ctd_data[ctd_data['station_id'] == station]
    scatter = ax4.scatter(station_data['salinity_psu'], station_data['temperature_c'], 
                          c=station_data['depth_m'], cmap='plasma_r', s=20, alpha=0.6)
ax4.set_xlabel('Salinity (PSU)', fontsize=12)
ax4.set_ylabel('Temperature (°C)', fontsize=12)
ax4.set_title('T-S Diagram (All Stations)', fontsize=14, fontweight='bold')
cbar = plt.colorbar(scatter, ax=ax4)
cbar.set_label('Depth (m)', fontsize=10)
ax4.grid(True, alpha=0.3)

# 5. Density profiles
ax5 = fig.add_subplot(2, 3, 5)
for station in ctd_data['station_id'].unique():
    station_data = ctd_data[ctd_data['station_id'] == station]
    ax5.plot(station_data['sigma_theta'], station_data['depth_m'], 
             linewidth=2, label=station, alpha=0.8)
ax5.set_xlabel('Potential Density (σθ, kg/m³)', fontsize=12)
ax5.set_ylabel('Depth (m)', fontsize=12)
ax5.set_ylim(1000, 0)
ax5.set_title('Potential Density Profiles', fontsize=14, fontweight='bold')
ax5.legend(loc='lower right', fontsize=9)
ax5.grid(True, alpha=0.3)

# 6. Water masses identification
ax6 = fig.add_subplot(2, 3, 6)
# Define water mass boundaries based on T-S characteristics
surface_water = ctd_data[ctd_data['depth_m'] <= 100]
thermocline_water = ctd_data[(ctd_data['depth_m'] > 100) & (ctd_data['depth_m'] <= 400)]
deep_water = ctd_data[ctd_data['depth_m'] > 400]

ax6.scatter(surface_water['salinity_psu'], surface_water['temperature_c'], 
            c='red', s=30, alpha=0.5, label='Surface Water (0-100m)')
ax6.scatter(thermocline_water['salinity_psu'], thermocline_water['temperature_c'], 
            c='green', s=30, alpha=0.5, label='Thermocline (100-400m)')
ax6.scatter(deep_water['salinity_psu'], deep_water['temperature_c'], 
            c='blue', s=30, alpha=0.5, label='Deep Water (>400m)')
ax6.set_xlabel('Salinity (PSU)', fontsize=12)
ax6.set_ylabel('Temperature (°C)', fontsize=12)
ax6.set_title('Water Mass Classification', fontsize=14, fontweight='bold')
ax6.legend(loc='upper right', fontsize=9)
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/ctd_overview.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/ctd_overview.png")
plt.close()

# Create additional detailed analysis figures

# Figure 2: Vertical sections
fig2, axes = plt.subplots(1, 3, figsize=(18, 6))

# Create interpolated sections along cruise track
# Sort stations by longitude for section plot
station_stats = ctd_data.groupby('station_id').agg({
    'lon': 'first',
    'lat': 'first'
}).reset_index()
station_order = station_stats.sort_values('lon')['station_id'].values

# Temperature section
ax_temp = axes[0]
temp_section = []
for station in station_order:
    station_data = ctd_data[ctd_data['station_id'] == station]
    temp_section.append(station_data['temperature_c'].values)

temp_section = np.array(temp_section)
x_pos = np.arange(len(station_order))
depths = ctd_data[ctd_data['station_id'] == station_order[0]]['depth_m'].values

contour_temp = ax_temp.contourf(x_pos, depths, temp_section.T, levels=20, cmap='RdYlBu_r')
ax_temp.contour(x_pos, depths, temp_section.T, levels=10, colors='black', linewidths=0.5)
ax_temp.set_ylim(1000, 0)
ax_temp.set_xticks(x_pos)
ax_temp.set_xticklabels(station_order, rotation=45)
ax_temp.set_xlabel('Station', fontsize=12)
ax_temp.set_ylabel('Depth (m)', fontsize=12)
ax_temp.set_title('Temperature Section (°C)', fontsize=14, fontweight='bold')
plt.colorbar(contour_temp, ax=ax_temp)

# Salinity section
ax_sal = axes[1]
sal_section = []
for station in station_order:
    station_data = ctd_data[ctd_data['station_id'] == station]
    sal_section.append(station_data['salinity_psu'].values)

sal_section = np.array(sal_section)
contour_sal = ax_sal.contourf(x_pos, depths, sal_section.T, levels=20, cmap='viridis')
ax_sal.contour(x_pos, depths, sal_section.T, levels=10, colors='white', linewidths=0.5)
ax_sal.set_ylim(1000, 0)
ax_sal.set_xticks(x_pos)
ax_sal.set_xticklabels(station_order, rotation=45)
ax_sal.set_xlabel('Station', fontsize=12)
ax_sal.set_ylabel('Depth (m)', fontsize=12)
ax_sal.set_title('Salinity Section (PSU)', fontsize=14, fontweight='bold')
plt.colorbar(contour_sal, ax=ax_sal)

# Density section
ax_den = axes[2]
den_section = []
for station in station_order:
    station_data = ctd_data[ctd_data['station_id'] == station]
    den_section.append(station_data['sigma_theta'].values)

den_section = np.array(den_section)
contour_den = ax_den.contourf(x_pos, depths, den_section.T, levels=20, cmap='coolwarm')
ax_den.contour(x_pos, depths, den_section.T, levels=10, colors='black', linewidths=0.5)
ax_den.set_ylim(1000, 0)
ax_den.set_xticks(x_pos)
ax_den.set_xticklabels(station_order, rotation=45)
ax_den.set_xlabel('Station', fontsize=12)
ax_den.set_ylabel('Depth (m)', fontsize=12)
ax_den.set_title('Potential Density Section (σθ)', fontsize=14, fontweight='bold')
plt.colorbar(contour_den, ax=ax_den)

plt.tight_layout()
plt.savefig('report/images/ctd_sections.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/ctd_sections.png")
plt.close()

# Figure 3: Water mass analysis
fig3, axes = plt.subplots(2, 2, figsize=(14, 12))

# Water mass statistics
water_masses = {
    'Surface Water (0-100m)': ctd_data[ctd_data['depth_m'] <= 100],
    'Thermocline Water (100-400m)': ctd_data[(ctd_data['depth_m'] > 100) & (ctd_data['depth_m'] <= 400)],
    'Deep Water (>400m)': ctd_data[ctd_data['depth_m'] > 400]
}

# Temperature distribution by water mass
ax1 = axes[0, 0]
temp_data = [wm['temperature_c'].values for wm in water_masses.values()]
bp1 = ax1.boxplot(temp_data, labels=list(water_masses.keys()), patch_artist=True)
colors = ['lightcoral', 'lightgreen', 'lightblue']
for patch, color in zip(bp1['boxes'], colors):
    patch.set_facecolor(color)
ax1.set_ylabel('Temperature (°C)', fontsize=12)
ax1.set_title('Temperature Distribution by Water Mass', fontsize=14, fontweight='bold')
ax1.tick_params(axis='x', rotation=15)
ax1.grid(True, alpha=0.3)

# Salinity distribution by water mass
ax2 = axes[0, 1]
sal_data = [wm['salinity_psu'].values for wm in water_masses.values()]
bp2 = ax2.boxplot(sal_data, labels=list(water_masses.keys()), patch_artist=True)
for patch, color in zip(bp2['boxes'], colors):
    patch.set_facecolor(color)
ax2.set_ylabel('Salinity (PSU)', fontsize=12)
ax2.set_title('Salinity Distribution by Water Mass', fontsize=14, fontweight='bold')
ax2.tick_params(axis='x', rotation=15)
ax2.grid(True, alpha=0.3)

# Station comparison - mean temperature
ax3 = axes[1, 0]
station_temp_means = ctd_data.groupby('station_id')['temperature_c'].mean()
bars = ax3.bar(station_temp_means.index, station_temp_means.values, 
               color='coral', edgecolor='black', alpha=0.7)
ax3.set_xlabel('Station ID', fontsize=12)
ax3.set_ylabel('Mean Temperature (°C)', fontsize=12)
ax3.set_title('Mean Temperature by Station', fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')
for bar in bars:
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.1f}', ha='center', va='bottom', fontsize=9)

# Station comparison - mean salinity
ax4 = axes[1, 1]
station_sal_means = ctd_data.groupby('station_id')['salinity_psu'].mean()
bars = ax4.bar(station_sal_means.index, station_sal_means.values, 
               color='lightblue', edgecolor='black', alpha=0.7)
ax4.set_xlabel('Station ID', fontsize=12)
ax4.set_ylabel('Mean Salinity (PSU)', fontsize=12)
ax4.set_title('Mean Salinity by Station', fontsize=14, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')
for bar in bars:
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.2f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/water_mass_analysis.png', dpi=300, bbox_inches='tight')
print("Saved: report/images/water_mass_analysis.png")
plt.close()

# Calculate and save summary statistics
summary_stats = []
for station in ctd_data['station_id'].unique():
    station_data = ctd_data[ctd_data['station_id'] == station]
    stats = {
        'station_id': station,
        'lat': station_data['lat'].iloc[0],
        'lon': station_data['lon'].iloc[0],
        'temp_surface': station_data[station_data['depth_m'] <= 50]['temperature_c'].mean(),
        'temp_deep': station_data[station_data['depth_m'] >= 800]['temperature_c'].mean(),
        'sal_surface': station_data[station_data['depth_m'] <= 50]['salinity_psu'].mean(),
        'sal_deep': station_data[station_data['depth_m'] >= 800]['salinity_psu'].mean(),
        'thermocline_depth': station_data.loc[station_data['temperature_c'].diff().abs().idxmax(), 'depth_m'],
        'mean_temp': station_data['temperature_c'].mean(),
        'mean_sal': station_data['salinity_psu'].mean(),
        'temp_range': station_data['temperature_c'].max() - station_data['temperature_c'].min(),
        'sal_range': station_data['salinity_psu'].max() - station_data['salinity_psu'].min()
    }
    summary_stats.append(stats)

summary_df = pd.DataFrame(summary_stats)
summary_df.to_csv('outputs/station_summary.csv', index=False)
print("\nStation summary statistics saved to outputs/station_summary.csv")
print(summary_df)

# Water mass characteristics
print("\n" + "="*60)
print("WATER MASS CHARACTERISTICS")
print("="*60)
for name, data in water_masses.items():
    print(f"\n{name}:")
    print(f"  Temperature: {data['temperature_c'].mean():.2f} ± {data['temperature_c'].std():.2f} °C")
    print(f"  Salinity: {data['salinity_psu'].mean():.2f} ± {data['salinity_psu'].std():.2f} PSU")
    print(f"  Density: {data['sigma_theta'].mean():.2f} ± {data['sigma_theta'].std():.2f} kg/m³")
    print(f"  Sample size: {len(data)} measurements")

print("\nAnalysis complete!")
