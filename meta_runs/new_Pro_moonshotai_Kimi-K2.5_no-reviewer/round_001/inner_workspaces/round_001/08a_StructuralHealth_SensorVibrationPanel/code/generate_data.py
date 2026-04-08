"""
Generate realistic synthetic sensor data for structural health monitoring analysis.
Simulates rotating equipment (motors, pumps, compressors) with vibration, temperature,
speed, and load telemetry.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

# Configuration
n_assets = 8
zones = ['Zone_A', 'Zone_B', 'Zone_C', 'Zone_D']
start_date = datetime(2024, 1, 1)
n_days = 90  # Quarterly data
samples_per_hour = 4  # 15-minute intervals

# Asset characteristics (some will have issues)
asset_configs = {
    'MOT-001': {'zone': 'Zone_A', 'base_rpm': 1800, 'base_load': 75, 'health': 'good'},
    'MOT-002': {'zone': 'Zone_A', 'base_rpm': 1800, 'base_load': 80, 'health': 'degrading'},  # Bearing issue
    'PMP-101': {'zone': 'Zone_B', 'base_rpm': 1200, 'base_load': 60, 'health': 'good'},
    'PMP-102': {'zone': 'Zone_B', 'base_rpm': 1200, 'base_load': 65, 'health': 'good'},
    'CMP-201': {'zone': 'Zone_C', 'base_rpm': 3600, 'base_load': 85, 'health': 'critical'},  # High vibration
    'CMP-202': {'zone': 'Zone_C', 'base_rpm': 3600, 'base_load': 82, 'health': 'good'},
    'FAN-301': {'zone': 'Zone_D', 'base_rpm': 900, 'base_load': 50, 'health': 'good'},
    'FAN-302': {'zone': 'Zone_D', 'base_rpm': 900, 'base_load': 55, 'health': 'degrading'},  # Misalignment
}

def generate_vibration_data(asset_id, config, timestamps):
    """Generate vibration data based on asset health status."""
    n = len(timestamps)
    health = config['health']
    base_rpm = config['base_rpm']
    
    # Base vibration levels (ISO 10816 guidelines for rotating machinery)
    if health == 'good':
        base_rms = 2.0 + np.random.normal(0, 0.3, n)
        base_peak = 0.3 + np.random.normal(0, 0.05, n)
    elif health == 'degrading':
        base_rms = 4.5 + np.random.normal(0, 0.8, n)
        base_peak = 0.8 + np.random.normal(0, 0.15, n)
    else:  # critical
        base_rms = 8.0 + np.random.normal(0, 1.5, n)
        base_peak = 1.5 + np.random.normal(0, 0.3, n)
    
    # Add time-based degradation for degrading assets
    if health == 'degrading':
        trend = np.linspace(0, 2.0, n)  # Increasing over time
        base_rms += trend
        base_peak += trend * 0.2
    elif health == 'critical':
        # Intermittent spikes
        spike_indices = np.random.choice(n, size=n//20, replace=False)
        base_rms[spike_indices] += np.random.uniform(3, 6, len(spike_indices))
    
    # RPM effect on vibration (higher RPM = higher vibration)
    rpm_factor = (base_rpm / 1800) ** 1.5
    base_rms *= rpm_factor
    base_peak *= rpm_factor
    
    # Add daily cycle (equipment warms up during day)
    hours = np.array([t.hour for t in timestamps])
    daily_cycle = 0.2 * np.sin(2 * np.pi * (hours - 6) / 24)
    base_rms += daily_cycle
    
    # Ensure positive values
    base_rms = np.maximum(base_rms, 0.5)
    base_peak = np.maximum(base_peak, 0.1)
    
    return base_rms, base_peak

def generate_temperature(asset_id, config, timestamps, vibration_rms):
    """Generate bearing temperature correlated with vibration."""
    n = len(timestamps)
    health = config['health']
    
    # Base temperature based on load and ambient
    base_temp = 45 + config['base_load'] * 0.3
    
    # Add correlation with vibration (higher vibration = more heat)
    temp = base_temp + vibration_rms * 1.5 + np.random.normal(0, 2, n)
    
    # Add seasonal trend
    days = np.array([(t - start_date).days for t in timestamps])
    seasonal = 5 * np.sin(2 * np.pi * days / 90)
    temp += seasonal
    
    # Degrading assets run hotter
    if health == 'degrading':
        temp += 8 + np.linspace(0, 5, n)
    elif health == 'critical':
        temp += 15 + np.random.uniform(0, 10, n)
    
    return temp

def generate_operational_data(config, timestamps):
    """Generate RPM and load data with realistic variation."""
    n = len(timestamps)
    base_rpm = config['base_rpm']
    base_load = config['base_load']
    
    # RPM varies slightly around setpoint
    rpm = base_rpm + np.random.normal(0, base_rpm * 0.02, n)
    
    # Load varies with operational demand
    load = base_load + np.random.normal(0, 8, n)
    load = np.clip(load, 20, 100)
    
    # Weekly pattern in load
    days_of_week = np.array([t.weekday() for t in timestamps])
    weekend_mask = (days_of_week >= 5)
    load[weekend_mask] *= 0.7
    
    return rpm, load

def generate_quality_flag(vibration_rms, peak_accel, temp, rpm):
    """Generate quality flags based on sensor readings."""
    flags = []
    for v, p, t, r in zip(vibration_rms, peak_accel, temp, rpm):
        if v > 10 or p > 2.0 or t > 90:
            flags.append('ALERT')
        elif v > 7 or p > 1.2 or t > 80:
            flags.append('WARNING')
        elif np.random.random() < 0.02:  # Occasional sensor issues
            flags.append('SUSPECT')
        else:
            flags.append('OK')
    return flags

# Generate timestamps
timestamps = []
current = start_date
end_date = start_date + timedelta(days=n_days)
while current < end_date:
    timestamps.append(current)
    current += timedelta(minutes=15)

# Generate data for all assets
all_data = []

for asset_id, config in asset_configs.items():
    print(f"Generating data for {asset_id}...")
    
    # Generate vibration
    vibration_rms, peak_accel = generate_vibration_data(asset_id, config, timestamps)
    
    # Generate temperature (correlated with vibration)
    bearing_temp = generate_temperature(asset_id, config, timestamps, vibration_rms)
    
    # Generate operational parameters
    rpm, load_pct = generate_operational_data(config, timestamps)
    
    # Generate quality flags
    quality_flag = generate_quality_flag(vibration_rms, peak_accel, bearing_temp, rpm)
    
    # Create DataFrame for this asset
    asset_df = pd.DataFrame({
        'timestamp_utc': timestamps,
        'asset_id': asset_id,
        'zone': config['zone'],
        'vibration_rms_mm_s': np.round(vibration_rms, 3),
        'peak_accel_g': np.round(peak_accel, 3),
        'bearing_temp_c': np.round(bearing_temp, 2),
        'rpm': np.round(rpm, 0).astype(int),
        'load_pct': np.round(load_pct, 1),
        'quality_flag': quality_flag
    })
    
    all_data.append(asset_df)

# Combine all data
df = pd.concat(all_data, ignore_index=True)

# Save to CSV
df.to_csv('data/sensor_panel_timeseries.csv', index=False)
print(f"\nGenerated {len(df)} records across {n_assets} assets")
print(f"Date range: {df['timestamp_utc'].min()} to {df['timestamp_utc'].max()}")
print(f"\nAsset summary:")
print(df.groupby('asset_id')['vibration_rms_mm_s'].agg(['mean', 'max', 'std']).round(2))
