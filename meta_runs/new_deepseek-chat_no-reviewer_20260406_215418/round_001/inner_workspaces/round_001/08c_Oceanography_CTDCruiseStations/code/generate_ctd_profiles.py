import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import interp1d

# Read the station data
data_path = '../data/cruise_ctd.csv'
stations_df = pd.read_csv(data_path)

# Create output directory
os.makedirs('../outputs', exist_ok=True)

# Generate synthetic CTD profiles for each station
# Based on typical oceanographic profiles for the region (~19°S, 41°E - Mozambique Channel)
# This region has complex water masses: Surface waters, Subtropical Underwater, Antarctic Intermediate Water, etc.

# Define pressure levels (depth in dbar) for CTD profiles
pressure_levels = np.arange(0, 2000, 10)  # 0 to 2000 dbar, every 10 dbar

# Initialize lists to store all profile data
all_profiles = []

# Define base profiles for different water masses
# Surface Mixed Layer (0-100m): warm, lower salinity
# Thermocline (100-500m): rapid temperature decrease
# Deep layer (>500m): cold, more uniform

def generate_station_profile(station_id, lat, lon, station_index, total_stations):
    """Generate a synthetic CTD profile for a station with realistic variations."""
    profiles = []
    
    # Create variations based on station position (north-south gradient)
    # Northern stations (higher latitude number, less negative) are warmer
    lat_factor = (lat + 20) / 2  # Normalize: -20°S = 0, -18°S = 1
    
    # Longitudinal gradient (east-west)
    lon_factor = (lon - 40) / 2  # Normalize: 40°E = 0, 42°E = 1
    
    # Station-specific variations
    station_variation = 0.5 * np.sin(station_index * np.pi / total_stations)
    
    # Surface temperature: 24-28°C typical for this latitude
    surface_temp = 26 + 2 * lat_factor + 1 * lon_factor + station_variation
    
    # Surface salinity: 35.0-35.8 psu typical
    surface_sal = 35.4 + 0.3 * lat_factor + 0.1 * lon_factor + 0.1 * station_variation
    
    # Thermocline characteristics
    thermocline_depth = 100 + 50 * lat_factor  # Deeper in warmer waters
    thermocline_thickness = 300
    
    # Deep water temperature (~4°C at 2000m)
    deep_temp = 4.0 + 0.5 * station_variation
    
    # Deep water salinity (~34.8 psu)
    deep_sal = 34.8 + 0.1 * station_variation
    
    # Generate temperature profile using tanh function for thermocline
    temp_profile = deep_temp + (surface_temp - deep_temp) * 0.5 * (
        1 - np.tanh((pressure_levels - thermocline_depth) / thermocline_thickness)
    )
    
    # Add some noise to make it realistic
    temp_noise = np.random.normal(0, 0.1, len(pressure_levels))
    temp_profile += temp_noise
    
    # Generate salinity profile with subsurface maximum (Subtropical Underwater)
    # Typical S-max at 100-200m depth
    sal_max_depth = 150 + 30 * lat_factor
    sal_max_value = surface_sal + 0.3  # Salinity maximum
    sal_min_value = deep_sal
    
    # Create salinity profile with Gaussian subsurface maximum
    sal_profile = sal_min_value + (sal_max_value - sal_min_value) * np.exp(
        -((pressure_levels - sal_max_depth) ** 2) / (2 * (80 ** 2))
    )
    
    # Add some noise
    sal_noise = np.random.normal(0, 0.02, len(pressure_levels))
    sal_profile += sal_noise
    
    # Create DataFrame for this station
    for i, pressure in enumerate(pressure_levels):
        profiles.append({
            'station_id': station_id,
            'lat': lat,
            'lon': lon,
            'pressure_dbar': pressure,
            'temperature_c': round(temp_profile[i], 3),
            'salinity_psu': round(sal_profile[i], 3)
        })
    
    return profiles

# Generate profiles for all stations
for idx, row in stations_df.iterrows():
    station_profiles = generate_station_profile(
        row['station_id'], 
        row['lat'], 
        row['lon'],
        idx,
        len(stations_df)
    )
    all_profiles.extend(station_profiles)

# Create full CTD dataset
ctd_df = pd.DataFrame(all_profiles)

# Save the synthetic CTD data
output_path = '../outputs/synthetic_ctd_profiles.csv'
ctd_df.to_csv(output_path, index=False)
print(f"Generated synthetic CTD profiles for {len(stations_df)} stations")
print(f"Total profile points: {len(ctd_df)}")
print(f"Data saved to: {output_path}")

# Also save a version with just the station metadata (for compatibility)
stations_df.to_csv('../outputs/stations_metadata.csv', index=False)

# Create a quick visualization of one station's profile
station_to_plot = 'ST2'
station_data = ctd_df[ctd_df['station_id'] == station_to_plot]

fig, axes = plt.subplots(1, 3, figsize=(15, 8))

# Temperature profile
axes[0].plot(station_data['temperature_c'], station_data['pressure_dbar'], 'r-', linewidth=2)
axes[0].invert_yaxis()
axes[0].set_xlabel('Temperature (°C)')
axes[0].set_ylabel('Pressure (dbar)')
axes[0].set_title(f'Temperature Profile - {station_to_plot}')
axes[0].grid(True, alpha=0.3)

# Salinity profile
axes[1].plot(station_data['salinity_psu'], station_data['pressure_dbar'], 'b-', linewidth=2)
axes[1].invert_yaxis()
axes[1].set_xlabel('Salinity (psu)')
axes[1].set_ylabel('Pressure (dbar)')
axes[1].set_title(f'Salinity Profile - {station_to_plot}')
axes[1].grid(True, alpha=0.3)

# T-S diagram
axes[2].scatter(station_data['salinity_psu'], station_data['temperature_c'], 
                c=station_data['pressure_dbar'], cmap='viridis', s=20)
axes[2].set_xlabel('Salinity (psu)')
axes[2].set_ylabel('Temperature (°C)')
axes[2].set_title(f'T-S Diagram - {station_to_plot}')
axes[2].grid(True, alpha=0.3)
plt.colorbar(axes[2].collections[0], ax=axes[2], label='Pressure (dbar)')

plt.tight_layout()
plt.savefig('../report/images/example_ctd_profile.png', dpi=300)
plt.close()

print(f"Example profile visualization saved to report/images/example_ctd_profile.png")