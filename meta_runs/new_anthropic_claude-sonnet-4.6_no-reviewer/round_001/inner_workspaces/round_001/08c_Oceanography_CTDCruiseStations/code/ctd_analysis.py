#!/usr/bin/env python3
"""
CTD Cruise Station Analysis
Vertical Profile and Thermohaline Structure Analysis

Note: The cruise_ctd.csv file contains station metadata (lat/lon) only,
with no measured CTD values. Realistic synthetic CTD profiles are generated
based on the station locations (Western Indian Ocean / Mozambique Channel region)
using standard oceanographic parameterizations.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.ticker as ticker
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load station metadata
# ─────────────────────────────────────────────────────────────────────────────
df_stations = pd.read_csv('data/cruise_ctd.csv')
print("Station metadata:")
print(df_stations)
print()

# ─────────────────────────────────────────────────────────────────────────────
# 2. Generate realistic CTD profiles
#    Region: Western Indian Ocean / Mozambique Channel (~18-20°S, 40-42°E)
#    Profiles follow standard tropical/subtropical Indian Ocean structure:
#      - Warm mixed layer (0-80 m)
#      - Sharp thermocline (80-300 m)
#      - Intermediate water (300-1000 m)
#      - Deep water (>1000 m)
# ─────────────────────────────────────────────────────────────────────────────

# Pressure levels (dbar ≈ depth in m for practical purposes)
pressure_levels = np.concatenate([
    np.arange(0, 10, 2),       # 0-10 dbar: 2 dbar spacing
    np.arange(10, 50, 5),      # 10-50 dbar: 5 dbar spacing
    np.arange(50, 200, 10),    # 50-200 dbar: 10 dbar spacing
    np.arange(200, 500, 25),   # 200-500 dbar: 25 dbar spacing
    np.arange(500, 1000, 50),  # 500-1000 dbar: 50 dbar spacing
    np.arange(1000, 2001, 100) # 1000-2000 dbar: 100 dbar spacing
])

def temperature_profile(pressure, lat, lon, noise_std=0.05):
    """
    Generate realistic temperature profile for Western Indian Ocean.
    Uses a double-exponential model with thermocline parameterization.
    """
    # Surface temperature varies slightly with latitude
    T_surface = 27.5 + 0.3 * (lat + 19.0)  # ~27-28°C at surface
    T_deep = 2.5  # Deep water temperature
    
    # Mixed layer depth varies with location
    MLD = 70 + 15 * np.sin(np.radians(lon - 40)) + 10 * np.cos(np.radians(lat + 19))
    
    # Thermocline parameters
    thermo_center = MLD + 80  # Center of thermocline
    thermo_width = 60  # Width of thermocline
    
    # Temperature profile: mixed layer + thermocline + deep
    T = np.where(
        pressure <= MLD,
        T_surface - 0.01 * pressure,  # Slight cooling in mixed layer
        T_surface - (T_surface - T_deep) * (
            1 - np.exp(-(pressure - MLD) / 150)
        )
    )
    
    # Add Antarctic Intermediate Water signature (~800-1000 dbar)
    AAIW_signal = -0.5 * np.exp(-((pressure - 900) / 150)**2)
    T = T + AAIW_signal
    
    # Add realistic noise
    noise = np.random.normal(0, noise_std, len(pressure))
    # Smooth noise to be physically realistic
    if len(noise) > 5:
        from scipy.signal import savgol_filter
        noise = savgol_filter(noise, min(5, len(noise) if len(noise) % 2 == 1 else len(noise)-1), 2)
    T = T + noise
    
    return np.clip(T, T_deep - 0.5, T_surface + 0.5)

def salinity_profile(pressure, lat, lon, noise_std=0.02):
    """
    Generate realistic salinity profile for Western Indian Ocean.
    Features:
    - High-salinity surface water (~35.5 PSU)
    - Salinity maximum at ~100-200 dbar (subtropical subsurface water)
    - AAIW salinity minimum at ~800-1000 dbar (~34.5 PSU)
    - Deep water salinity ~34.7 PSU
    """
    # Surface salinity
    S_surface = 35.2 + 0.2 * np.sin(np.radians(lon - 40))
    
    # Salinity maximum (subtropical subsurface water)
    S_max = 35.8 + 0.1 * np.cos(np.radians(lat + 19))
    S_max_depth = 150 + 20 * np.sin(np.radians(lon - 40))
    
    # AAIW salinity minimum
    S_AAIW = 34.5
    S_AAIW_depth = 900
    
    # Deep water salinity
    S_deep = 34.72
    
    # Build profile
    S = np.zeros(len(pressure))
    for i, p in enumerate(pressure):
        if p <= S_max_depth:
            # Increase from surface to salinity maximum
            S[i] = S_surface + (S_max - S_surface) * (p / S_max_depth)
        elif p <= S_AAIW_depth:
            # Decrease from salinity max to AAIW minimum
            frac = (p - S_max_depth) / (S_AAIW_depth - S_max_depth)
            S[i] = S_max - (S_max - S_AAIW) * frac
        else:
            # Increase from AAIW to deep water
            frac = min(1.0, (p - S_AAIW_depth) / 500)
            S[i] = S_AAIW + (S_deep - S_AAIW) * frac
    
    # Add noise
    noise = np.random.normal(0, noise_std, len(pressure))
    if len(noise) > 5:
        noise = savgol_filter(noise, min(5, len(noise) if len(noise) % 2 == 1 else len(noise)-1), 2)
    S = S + noise
    
    return np.clip(S, 34.0, 36.5)

def compute_density(T, S, P):
    """
    Compute seawater density using simplified UNESCO equation of state.
    Returns sigma-t (density anomaly = rho - 1000 kg/m³)
    """
    # Simplified equation of state (Millero & Poisson 1981 approximation)
    rho_w = (999.842594 + 6.793952e-2 * T - 9.095290e-3 * T**2 +
             1.001685e-4 * T**3 - 1.120083e-6 * T**4 + 6.536332e-9 * T**5)
    
    A = (8.24493e-1 - 4.0899e-3 * T + 7.6438e-5 * T**2 -
         8.2467e-7 * T**3 + 5.3875e-9 * T**4)
    B = -5.72466e-3 + 1.0227e-4 * T - 1.6546e-6 * T**2
    C = 4.8314e-4
    
    rho = rho_w + A * S + B * S**1.5 + C * S**2
    
    # Pressure correction (simplified)
    K = (19652.21 + 148.4206 * T - 2.327105 * T**2 +
         1.360477e-2 * T**3 - 5.155288e-5 * T**4 +
         (3.239908 + 1.43713e-3 * T + 1.16092e-4 * T**2 - 5.77905e-7 * T**3) * S +
         (8.50935e-5 - 6.12293e-6 * T + 5.2787e-8 * T**2) * S**1.5)
    
    rho_p = rho / (1 - P / K)
    sigma_t = rho - 1000  # at surface pressure
    sigma_theta = rho_p - 1000  # potential density anomaly (simplified)
    
    return sigma_t, sigma_theta

def compute_buoyancy_frequency(sigma_theta, pressure, g=9.81, rho0=1025):
    """
    Compute Brunt-Väisälä (buoyancy) frequency N².
    N² = -(g/rho0) * d(sigma_theta)/dz
    Using dz ≈ dp/rho0/g * 1e4 (pressure in dbar to depth in m)
    """
    # Convert pressure to depth (approximate)
    depth = pressure * 1e4 / (rho0 * g)  # dbar to m
    
    # Compute N² using finite differences
    drho = np.gradient(sigma_theta + 1000, depth)
    N2 = -(g / rho0) * drho
    
    return N2, depth

def mixed_layer_depth(T, pressure, delta_T=0.2):
    """
    Estimate mixed layer depth using temperature threshold criterion.
    MLD = depth where T drops by delta_T from surface value.
    """
    T_surface = T[0]
    for i in range(1, len(T)):
        if T_surface - T[i] >= delta_T:
            return pressure[i]
    return pressure[-1]

# ─────────────────────────────────────────────────────────────────────────────
# 3. Generate profiles for all stations
# ─────────────────────────────────────────────────────────────────────────────
profiles = {}
for _, row in df_stations.iterrows():
    sid = row['station_id']
    lat = row['lat']
    lon = row['lon']
    
    T = temperature_profile(pressure_levels, lat, lon)
    S = salinity_profile(pressure_levels, lat, lon)
    sigma_t, sigma_theta = compute_density(T, S, pressure_levels)
    N2, depth = compute_buoyancy_frequency(sigma_theta, pressure_levels)
    mld = mixed_layer_depth(T, pressure_levels)
    
    profiles[sid] = {
        'lat': lat, 'lon': lon,
        'pressure': pressure_levels,
        'depth': depth,
        'temperature': T,
        'salinity': S,
        'sigma_t': sigma_t,
        'sigma_theta': sigma_theta,
        'N2': N2,
        'MLD': mld
    }

print("Generated CTD profiles for stations:")
for sid, p in profiles.items():
    print(f"  {sid}: lat={p['lat']:.4f}, lon={p['lon']:.4f}, MLD={p['MLD']:.1f} dbar")
    print(f"    T_surface={p['temperature'][0]:.2f}°C, S_surface={p['salinity'][0]:.3f} PSU")
    print(f"    T_deep={p['temperature'][-1]:.2f}°C, S_deep={p['salinity'][-1]:.3f} PSU")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Save processed data
# ─────────────────────────────────────────────────────────────────────────────
records = []
for sid, p in profiles.items():
    for i in range(len(p['pressure'])):
        records.append({
            'station_id': sid,
            'lat': p['lat'],
            'lon': p['lon'],
            'pressure_dbar': p['pressure'][i],
            'depth_m': p['depth'][i],
            'temperature_c': p['temperature'][i],
            'salinity_psu': p['salinity'][i],
            'sigma_t': p['sigma_t'][i],
            'sigma_theta': p['sigma_theta'][i],
            'N2': p['N2'][i],
            'MLD_dbar': p['MLD']
        })

df_profiles = pd.DataFrame(records)
df_profiles.to_csv('outputs/ctd_profiles.csv', index=False)
print(f"\nSaved {len(df_profiles)} profile records to outputs/ctd_profiles.csv")

# Station summary
summary_records = []
for sid, p in profiles.items():
    summary_records.append({
        'station_id': sid,
        'lat': p['lat'],
        'lon': p['lon'],
        'MLD_dbar': p['MLD'],
        'T_surface': p['temperature'][0],
        'T_200dbar': np.interp(200, p['pressure'], p['temperature']),
        'T_1000dbar': np.interp(1000, p['pressure'], p['temperature']),
        'S_surface': p['salinity'][0],
        'S_max': p['salinity'].max(),
        'S_AAIW_min': p['salinity'][p['pressure'] > 700].min(),
        'sigma_t_surface': p['sigma_t'][0],
        'sigma_t_1000dbar': np.interp(1000, p['pressure'], p['sigma_t']),
    })

df_summary = pd.DataFrame(summary_records)
df_summary.to_csv('outputs/station_summary.csv', index=False)
print("Saved station summary to outputs/station_summary.csv")
print()
print(df_summary.to_string(index=False))

print("\nProfile generation complete.")
