import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# Parameters for synthetic data
n_assets = 8
zones = ['A', 'B', 'C', 'D']
n_days = 30
readings_per_day = 24  # hourly readings

# Generate timestamps
start_date = datetime(2024, 1, 1)
timestamps = []
for day in range(n_days):
    for hour in range(readings_per_day):
        timestamps.append(start_date + timedelta(days=day, hours=hour))

# Generate asset IDs
asset_ids = [f'ASSET_{i:03d}' for i in range(1, n_assets + 1)]

# Create DataFrame
rows = []
for ts in timestamps:
    for asset_id in asset_ids:
        # Assign zone based on asset
        zone = zones[int(asset_id[-1]) % len(zones)]
        
        # Base values with some variation
        base_vibration = 2.5 + np.random.normal(0, 0.5)
        
        # Add time-based patterns (higher vibration during working hours)
        hour_of_day = ts.hour
        if 8 <= hour_of_day <= 18:  # Working hours
            vibration_factor = 1.5
        else:
            vibration_factor = 0.8
        
        # Add asset-specific patterns (some assets have higher vibration)
        asset_factor = 1.0
        if asset_id in ['ASSET_003', 'ASSET_007']:
            asset_factor = 2.0  # Problematic assets
        
        # Add some random spikes
        spike = 1.0
        if np.random.random() < 0.05:  # 5% chance of spike
            spike = np.random.uniform(3.0, 8.0)
        
        vibration_rms = max(0.1, base_vibration * vibration_factor * asset_factor * spike)
        
        # Peak acceleration is typically 1.5-3x RMS
        peak_accel = vibration_rms * np.random.uniform(1.5, 3.0)
        
        # Bearing temperature correlates with vibration and time
        base_temp = 65.0
        temp_increase = (vibration_rms - 2.5) * 5  # 5°C per unit vibration above baseline
        hour_effect = 0 if hour_of_day < 8 else (hour_of_day - 8) * 0.5  # Warmer during day
        bearing_temp = base_temp + temp_increase + hour_effect + np.random.normal(0, 2)
        
        # RPM varies by asset and time
        base_rpm = 1200
        rpm_variation = np.random.normal(0, 50)
        rpm = base_rpm + rpm_variation
        
        # Load percentage
        if hour_of_day < 8:
            load_pct = np.random.uniform(20, 40)
        elif hour_of_day < 16:
            load_pct = np.random.uniform(70, 90)
        else:
            load_pct = np.random.uniform(40, 60)
        
        # Quality flag (mostly good, some issues)
        quality_flag = 'GOOD'
        if np.random.random() < 0.02:  # 2% bad quality
            quality_flag = 'CHECK'
        
        rows.append({
            'timestamp_utc': ts.isoformat(),
            'asset_id': asset_id,
            'zone': zone,
            'vibration_rms_mm_s': round(vibration_rms, 3),
            'peak_accel_g': round(peak_accel, 3),
            'bearing_temp_c': round(bearing_temp, 1),
            'rpm': round(rpm),
            'load_pct': round(load_pct, 1),
            'quality_flag': quality_flag
        })

# Create DataFrame
df = pd.DataFrame(rows)

# Save to CSV
output_path = '../data/sensor_panel_timeseries_synthetic.csv'
df.to_csv(output_path, index=False)
print(f"Generated synthetic data with {len(df)} rows")
print(f"Saved to {output_path}")
print("\nFirst few rows:")
print(df.head())
print("\nData shape:", df.shape)
