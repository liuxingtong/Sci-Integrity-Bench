import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# Parameters for synthetic data
n_assets = 5
n_zones_per_asset = 2
hours_of_data = 720  # 30 days of hourly data
start_time = datetime(2024, 1, 1, 0, 0, 0)

# Asset and zone names
asset_ids = [f'ASSET_{i:03d}' for i in range(1, n_assets + 1)]
zones = ['DRIVE_END', 'NON_DRIVE_END']

# Generate timestamps (hourly for 30 days)
timestamps = [start_time + timedelta(hours=i) for i in range(hours_of_data)]

# Create empty list to store all records
records = []

# Generate data for each asset and zone
for asset in asset_ids:
    for zone in zones:
        # Base values that drift over time (simulating degradation)
        time_factor = np.linspace(0, 1, hours_of_data)
        
        # Base vibration increases slightly over time for some assets
        if asset in ['ASSET_001', 'ASSET_003']:
            base_vibration = 2.0 + 0.5 * time_factor + np.random.normal(0, 0.1, hours_of_data)
        else:
            base_vibration = 1.5 + 0.1 * time_factor + np.random.normal(0, 0.05, hours_of_data)
        
        # Peak acceleration correlates with RMS vibration
        peak_accel = base_vibration * 0.8 + np.random.normal(0, 0.2, hours_of_data)
        
        # Bearing temperature depends on vibration and load
        base_temp = 65.0 + 0.3 * base_vibration + np.random.normal(0, 1.5, hours_of_data)
        
        # RPM varies by asset type
        if asset in ['ASSET_001', 'ASSET_002']:
            rpm = 1800 + np.random.normal(0, 50, hours_of_data)
        else:
            rpm = 1200 + np.random.normal(0, 30, hours_of_data)
        
        # Load percentage (0-100%)
        load_pct = 70 + 20 * np.sin(2 * np.pi * time_factor * 10) + np.random.normal(0, 5, hours_of_data)
        load_pct = np.clip(load_pct, 20, 95)
        
        # Quality flag (mostly good, occasional issues)
        quality_flag = np.random.choice(['GOOD', 'CHECK', 'BAD'], 
                                        size=hours_of_data, 
                                        p=[0.92, 0.06, 0.02])
        
        # Add some anomalies for ASSET_001 (simulating developing fault)
        if asset == 'ASSET_001' and zone == 'DRIVE_END':
            # Add increasing vibration anomaly in last third of data
            anomaly_start = int(hours_of_data * 2/3)
            base_vibration[anomaly_start:] += np.linspace(0, 2.0, hours_of_data - anomaly_start)
            peak_accel[anomaly_start:] += np.linspace(0, 1.5, hours_of_data - anomaly_start)
            base_temp[anomaly_start:] += np.linspace(0, 10, hours_of_data - anomaly_start)
            
            # Add some spike anomalies
            spike_indices = np.random.choice(range(anomaly_start, hours_of_data), 
                                            size=5, replace=False)
            base_vibration[spike_indices] += np.random.uniform(3, 5, 5)
            peak_accel[spike_indices] += np.random.uniform(2, 4, 5)
        
        # Create records for this asset-zone combination
        for i in range(hours_of_data):
            records.append({
                'timestamp_utc': timestamps[i].strftime('%Y-%m-%d %H:%M:%S'),
                'asset_id': asset,
                'zone': zone,
                'vibration_rms_mm_s': max(0.1, round(base_vibration[i], 2)),
                'peak_accel_g': max(0.1, round(peak_accel[i], 2)),
                'bearing_temp_c': round(base_temp[i], 1),
                'rpm': round(rpm[i]),
                'load_pct': round(load_pct[i], 1),
                'quality_flag': quality_flag[i]
            })

# Create DataFrame
df = pd.DataFrame(records)

# Save to CSV
df.to_csv('data/sensor_panel_timeseries_synthetic.csv', index=False)

print(f"Generated synthetic data with {len(df)} records")
print(f"Time range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Assets: {df['asset_id'].nunique()}")
print(f"Zones: {df['zone'].nunique()}")
print("\nFirst few rows:")
print(df.head())
print("\nData summary:")
print(df.describe())