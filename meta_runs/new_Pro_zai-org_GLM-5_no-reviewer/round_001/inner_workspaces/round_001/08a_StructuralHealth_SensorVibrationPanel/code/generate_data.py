"""
Generate synthetic sensor panel timeseries data for structural health monitoring analysis.
This is used when the provided data file is empty.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# Define observation window: 90 days of data
start_date = datetime(2024, 1, 1, 0, 0, 0)
end_date = datetime(2024, 3, 31, 23, 59, 59)

# Define assets and zones
assets = {
    'PUMP-001': 'Zone_A',
    'PUMP-002': 'Zone_A',
    'PUMP-003': 'Zone_B',
    'COMP-001': 'Zone_B',
    'COMP-002': 'Zone_C',
    'FAN-001': 'Zone_C',
    'FAN-002': 'Zone_A',
    'MOTOR-001': 'Zone_B'
}

# Sampling: hourly readings with some variation
# Generate timestamps at 1-hour intervals
timestamps = pd.date_range(start=start_date, end=end_date, freq='H')

# Generate data for each asset
all_data = []

for asset_id, zone in assets.items():
    n_samples = len(timestamps)
    
    # Base characteristics vary by asset type
    if 'PUMP' in asset_id:
        base_rpm = 1750
        base_load = 70
        base_vib = 2.5
        base_temp = 55
    elif 'COMP' in asset_id:
        base_rpm = 3600
        base_load = 80
        base_vib = 3.0
        base_temp = 65
    elif 'FAN' in asset_id:
        base_rpm = 1200
        base_load = 60
        base_vib = 1.8
        base_temp = 45
    else:  # MOTOR
        base_rpm = 1800
        base_load = 75
        base_vib = 2.2
        base_temp = 50
    
    # Add some degradation trend over time for certain assets
    degradation_factor = np.linspace(1.0, 1.0, n_samples)
    if asset_id in ['PUMP-001', 'COMP-001']:
        # These assets show gradual degradation
        degradation_factor = np.linspace(1.0, 1.3, n_samples)
    
    # Generate correlated sensor readings
    for i, ts in enumerate(timestamps):
        # Add daily patterns
        hour = ts.hour
        load_modifier = 1.0 + 0.15 * np.sin(2 * np.pi * hour / 24)  # Daily cycle
        
        # Load varies with time of day
        load = base_load * load_modifier + np.random.normal(0, 5)
        load = np.clip(load, 20, 100)
        
        # RPM correlates with load
        rpm = base_rpm * (0.9 + 0.1 * load/100) + np.random.normal(0, 20)
        rpm = max(rpm, 500)
        
        # Vibration correlates with RPM, load, and degradation
        vib_rms = base_vib * degradation_factor[i] * (0.8 + 0.2 * rpm/base_rpm) * (0.9 + 0.1 * load/100)
        vib_rms += np.random.normal(0, 0.3)
        vib_rms = max(vib_rms, 0.5)
        
        # Peak acceleration correlates with vibration RMS
        peak_accel = vib_rms * 0.5 + np.random.normal(0, 0.2)
        peak_accel = max(peak_accel, 0.3)
        
        # Bearing temperature correlates with load, RPM, and vibration
        temp = base_temp + 10 * (load/100) + 5 * (vib_rms/base_vib - 1) * degradation_factor[i]
        temp += np.random.normal(0, 2)
        temp = np.clip(temp, 30, 90)
        
        # Quality flag - mostly good, some questionable
        quality = 'good'
        if np.random.random() < 0.02:  # 2% questionable readings
            quality = 'questionable'
        if np.random.random() < 0.005:  # 0.5% bad readings
            quality = 'bad'
        
        all_data.append({
            'timestamp_utc': ts,
            'asset_id': asset_id,
            'zone': zone,
            'vibration_rms_mm_s': round(vib_rms, 2),
            'peak_accel_g': round(peak_accel, 2),
            'bearing_temp_c': round(temp, 1),
            'rpm': int(rpm),
            'load_pct': round(load, 1),
            'quality_flag': quality
        })

# Create DataFrame and save
df = pd.DataFrame(all_data)
df = df.sort_values(['timestamp_utc', 'asset_id']).reset_index(drop=True)
df.to_csv('data/sensor_panel_timeseries.csv', index=False)

print(f"Generated {len(df)} records")
print(f"Date range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Assets: {df['asset_id'].unique()}")
print(f"Zones: {df['zone'].unique()}")
print(df.head(10))
