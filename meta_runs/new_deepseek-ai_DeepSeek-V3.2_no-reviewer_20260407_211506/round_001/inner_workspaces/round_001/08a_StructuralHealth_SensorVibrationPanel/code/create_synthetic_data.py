import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create synthetic data for demonstration
np.random.seed(42)

# Parameters
n_assets = 5
n_zones_per_asset = 3
n_readings_per_zone = 100

assets = [f'ASSET_{i:03d}' for i in range(1, n_assets + 1)]
zones = ['BEARING_A', 'BEARING_B', 'ROTOR']

# Generate timestamps (hourly readings over 30 days)
start_time = datetime(2024, 1, 1, 0, 0, 0)
timestamps = []
for i in range(n_readings_per_zone):
    timestamps.append(start_time + timedelta(hours=i))

# Create DataFrame
records = []
for asset in assets:
    for zone in zones:
        # Base values with some asset/zone specific characteristics
        if zone == 'BEARING_A':
            base_vibration = 2.5 + np.random.normal(0, 0.5)
            base_temp = 65 + np.random.normal(0, 5)
        elif zone == 'BEARING_B':
            base_vibration = 2.8 + np.random.normal(0, 0.6)
            base_temp = 70 + np.random.normal(0, 6)
        else:  # ROTOR
            base_vibration = 3.2 + np.random.normal(0, 0.7)
            base_temp = 75 + np.random.normal(0, 7)
        
        # Add asset-specific variation
        asset_factor = 1.0 + (int(asset.split('_')[1]) - 3) * 0.1
        
        for i, ts in enumerate(timestamps):
            # Time-based trends (some assets degrade over time)
            time_factor = 1.0 + 0.001 * i if asset in ['ASSET_001', 'ASSET_003'] else 1.0
            
            # Generate correlated values
            vibration_rms = base_vibration * asset_factor * time_factor + np.random.normal(0, 0.3)
            vibration_rms = max(0.5, vibration_rms)  # Ensure positive
            
            # Peak acceleration typically 3-5x RMS
            peak_accel = vibration_rms * (3.5 + np.random.normal(0, 0.5))
            
            # Temperature correlated with vibration and load
            temp = base_temp * asset_factor + 0.1 * vibration_rms + np.random.normal(0, 2)
            
            # RPM and load (operational parameters)
            rpm = 1800 + np.random.normal(0, 50)
            load_pct = 75 + np.random.normal(0, 10)
            
            # Quality flag (mostly good, some warnings)
            quality = 'GOOD'
            if vibration_rms > 5.0:
                quality = 'WARNING'
            elif temp > 85:
                quality = 'WARNING'
            elif np.random.random() < 0.02:  # 2% random errors
                quality = 'ERROR'
            
            records.append({
                'timestamp_utc': ts.isoformat(),
                'asset_id': asset,
                'zone': zone,
                'vibration_rms_mm_s': round(vibration_rms, 3),
                'peak_accel_g': round(peak_accel, 3),
                'bearing_temp_c': round(temp, 1),
                'rpm': round(rpm, 1),
                'load_pct': round(load_pct, 1),
                'quality_flag': quality
            })

# Create DataFrame
df = pd.DataFrame(records)

# Save to outputs directory
output_path = 'outputs/synthetic_sensor_data.csv'
df.to_csv(output_path, index=False)
print(f'Synthetic data saved to {output_path}')
print(f'Shape: {df.shape}')
print(f'Time range: {df["timestamp_utc"].min()} to {df["timestamp_utc"].max()}')
print(f'Assets: {df["asset_id"].unique().tolist()}')
print(f'Zones: {df["zone"].unique().tolist()}')