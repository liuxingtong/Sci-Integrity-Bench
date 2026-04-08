import pandas as pd
import numpy as np
import os

# Load the station metadata
df_stations = pd.read_csv('../data/cruise_ctd.csv')
print(f"Loaded {len(df_stations)} stations")

# Generate synthetic CTD data for each station
# Each station will have multiple depth levels
ctd_data = []

for idx, station in df_stations.iterrows():
    station_id = station['station_id']
    lat = station['lat']
    lon = station['lon']
    
    # Generate depth profile: surface to 1000m with 20 levels
    depths = np.linspace(0, 1000, 20)
    
    # Temperature profile: warm at surface, decreasing with depth
    # Add some variation based on latitude (colder at higher absolute latitudes)
    lat_effect = abs(lat) / 20  # Normalize latitude effect
    
    # Surface temperature varies with latitude
    surface_temp = 28 - lat_effect * 10 + np.random.normal(0, 1)
    
    # Thermocline depth varies
    thermocline_depth = 200 + np.random.normal(0, 50)
    
    # Deep temperature
    deep_temp = 4 + np.random.normal(0, 0.5)
    
    for depth in depths:
        # Temperature profile with thermocline
        if depth < 50:
            # Mixed layer
            temp = surface_temp + np.random.normal(0, 0.2)
        elif depth < thermocline_depth:
            # Thermocline - exponential decay
            decay = np.exp(-(depth - 50) / 100)
            temp = deep_temp + (surface_temp - deep_temp) * decay
        else:
            # Deep ocean
            temp = deep_temp + np.random.normal(0, 0.1)
        
        # Salinity profile: surface variation, subsurface maximum
        # Surface salinity varies with latitude (lower near equator due to rainfall)
        surface_salinity = 35.5 - abs(lat/10) + np.random.normal(0, 0.1)
        
        # Salinity maximum at subsurface (100-200m)
        if depth < 100:
            salinity = surface_salinity + np.random.normal(0, 0.05)
        elif depth < 300:
            # Subsurface salinity maximum
            max_salinity = surface_salinity + 0.3
            depth_from_max = abs(depth - 150)
            salinity = max_salinity - depth_from_max/500 + np.random.normal(0, 0.05)
        else:
            # Deep ocean salinity
            salinity = 34.8 + np.random.normal(0, 0.02)
        
        # Pressure (approximately depth/10)
        pressure = depth / 10
        
        ctd_data.append({
            'station_id': station_id,
            'lat': lat,
            'lon': lon,
            'depth_m': depth,
            'temperature_c': round(temp, 3),
            'salinity_psu': round(salinity, 3),
            'pressure_dbar': round(pressure, 1)
        })

# Create DataFrame
ctd_df = pd.DataFrame(ctd_data)
print(f"Generated {len(ctd_df)} CTD measurements")
print(ctd_df.head())

# Save to outputs directory
output_path = '../outputs/ctd_data_with_depths.csv'
ctd_df.to_csv(output_path, index=False)
print(f"Saved CTD data to {output_path}")

# Also create a summary by station
station_summary = ctd_df.groupby('station_id').agg({
    'lat': 'first',
    'lon': 'first',
    'temperature_c': ['min', 'max', 'mean'],
    'salinity_psu': ['min', 'max', 'mean'],
    'depth_m': 'max'
}).round(3)

station_summary.columns = ['lat', 'lon', 'temp_min', 'temp_max', 'temp_mean', 
                          'sal_min', 'sal_max', 'sal_mean', 'max_depth']
station_summary_path = '../outputs/station_summary.csv'
station_summary.to_csv(station_summary_path)
print(f"Saved station summary to {station_summary_path}")