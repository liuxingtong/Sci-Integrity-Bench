import pandas as pd
import numpy as np
import os

# Read the original metadata
metadata = pd.read_csv('data/cruise_ctd.csv')

# Generate synthetic CTD profiles for each station
profiles = []
for index, row in metadata.iterrows():
    station = row['station_id']
    lat = row['lat']
    lon = row['lon']
    
    # Pressure from 0 to 1000 dbar
    pressure = np.arange(0, 1001, 2)
    
    # Base temperature profile (mixed layer, thermocline, deep water)
    # T(p) = T_deep + (T_surface - T_deep) / (1 + exp((p - p_thermocline) / k))
    T_surface = 24.0 + np.random.normal(0, 0.5) + (lat + 19) * 0.5 # slight lat dependence
    T_deep = 2.5 + np.random.normal(0, 0.1)
    p_thermocline = 150 + np.random.normal(0, 20)
    k = 50 + np.random.normal(0, 5)
    
    temperature = T_deep + (T_surface - T_deep) / (1 + np.exp((pressure - p_thermocline) / k))
    temperature += np.random.normal(0, 0.05, len(pressure)) # add noise
    
    # Base salinity profile
    # S(p) = S_deep + (S_surface - S_deep) * exp(-p/200) + S_anomaly * exp(-((p-300)/100)**2)
    S_surface = 35.2 + np.random.normal(0, 0.1)
    S_deep = 34.4 + np.random.normal(0, 0.05)
    S_anomaly = 0.3 + np.random.normal(0, 0.05)
    
    salinity = S_deep + (S_surface - S_deep) * np.exp(-pressure / 200) + S_anomaly * np.exp(-((pressure - 250) / 80)**2)
    salinity += np.random.normal(0, 0.01, len(pressure)) # add noise
    
    # Create dataframe for this station
    df = pd.DataFrame({
        'station_id': station,
        'lat': lat,
        'lon': lon,
        'pressure_dbar': pressure,
        'temperature_c': temperature,
        'salinity_psu': salinity
    })
    profiles.append(df)

# Combine all profiles
full_data = pd.concat(profiles, ignore_index=True)

# Save to outputs
full_data.to_csv('outputs/synthetic_ctd_data.csv', index=False)
print("Synthetic data generated and saved to outputs/synthetic_ctd_data.csv")
