import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Set random seed for reproducibility
np.random.seed(42)

# Generate synthetic sensor data
# We'll create data for 5 assets, 3 zones each, over 90 days
assets = ['ASSET_001', 'ASSET_002', 'ASSET_003', 'ASSET_004', 'ASSET_005']
zones = ['BEARING_A', 'BEARING_B', 'DRIVE_END']

# Base timestamps - hourly data for 90 days
start_date = datetime(2024, 1, 1)
timestamps = [start_date + timedelta(hours=i) for i in range(90 * 24)]  # 90 days * 24 hours

# Create empty list for data
data_rows = []

# Generate data for each asset and zone
for asset in assets:
    for zone in zones:
        # Base vibration levels vary by asset and zone
        if zone == 'BEARING_A':
            base_vibration = 2.5 + np.random.normal(0, 0.5)
            base_temp = 65 + np.random.normal(0, 5)
        elif zone == 'BEARING_B':
            base_vibration = 2.8 + np.random.normal(0, 0.6)
            base_temp = 68 + np.random.normal(0, 6)
        else:  # DRIVE_END
            base_vibration = 3.2 + np.random.normal(0, 0.7)
            base_temp = 72 + np.random.normal(0, 7)
        
        # Asset-specific adjustments
        if asset == 'ASSET_002':  # Slightly worse asset
            base_vibration *= 1.3
            base_temp *= 1.05
        elif asset == 'ASSET_004':  # Problem asset with degrading trend
            degradation_factor = np.linspace(1.0, 1.8, len(timestamps))
        else:
            degradation_factor = np.ones(len(timestamps))
        
        for i, ts in enumerate(timestamps):
            # Time-based patterns (daily and weekly cycles)
            hour_of_day = ts.hour
            day_of_week = ts.weekday()
            
            # Daily cycle - higher vibration during working hours
            daily_factor = 1.0 + 0.3 * np.sin(2 * np.pi * hour_of_day / 24)
            
            # Weekly cycle - lower vibration on weekends
            weekly_factor = 0.9 if day_of_week >= 5 else 1.0  # Weekend vs weekday
            
            # Random noise
            noise = np.random.normal(0, 0.2)
            
            # Calculate vibration RMS (mm/s)
            if asset == 'ASSET_004':
                vib_rms = base_vibration * degradation_factor[i] * daily_factor * weekly_factor + noise
            else:
                vib_rms = base_vibration * daily_factor * weekly_factor + noise
            
            # Peak acceleration is typically 3-5x RMS with some variation
            peak_factor = 4.0 + np.random.normal(0, 0.5)
            peak_accel = vib_rms * peak_factor
            
            # Bearing temperature correlates with vibration
            temp_noise = np.random.normal(0, 2)
            bearing_temp = base_temp + (vib_rms - base_vibration) * 10 + temp_noise
            
            # RPM varies by asset and time
            base_rpm = 1800 if 'ASSET_00' in asset else 1500
            rpm = base_rpm + np.random.normal(0, 50)
            
            # Load percentage
            load_pct = 75 + np.random.normal(0, 10)
            load_pct = max(30, min(100, load_pct))
            
            # Quality flag (mostly good, occasional issues)
            quality_flag = 'GOOD'
            if np.random.random() < 0.01:  # 1% chance of bad data
                quality_flag = 'CHECK'
            elif np.random.random() < 0.005:  # 0.5% chance of invalid
                quality_flag = 'INVALID'
            
            data_rows.append({
                'timestamp_utc': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'asset_id': asset,
                'zone': zone,
                'vibration_rms_mm_s': round(vib_rms, 3),
                'peak_accel_g': round(peak_accel, 3),
                'bearing_temp_c': round(bearing_temp, 1),
                'rpm': round(rpm),
                'load_pct': round(load_pct, 1),
                'quality_flag': quality_flag
            })

# Create DataFrame
df = pd.DataFrame(data_rows)

# Save to CSV
output_path = '../data/sensor_panel_timeseries.csv'
df.to_csv(output_path, index=False)

print(f"Generated {len(df)} rows of synthetic sensor data")
print(f"Data saved to {output_path}")
print(f"Time range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"Assets: {df['asset_id'].unique()}")
print(f"Zones: {df['zone'].unique()}")
print(f"\nFirst few rows:")
print(df.head())
print(f"\nSummary statistics for vibration_rms_mm_s:")
print(df['vibration_rms_mm_s'].describe())
