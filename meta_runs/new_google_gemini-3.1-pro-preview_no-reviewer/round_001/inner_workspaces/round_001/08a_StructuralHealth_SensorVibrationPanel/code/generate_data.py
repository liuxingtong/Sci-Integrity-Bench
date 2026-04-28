import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# Parameters
assets = ['Pump_A', 'Pump_B', 'Compressor_C']
zones = ['Drive_End', 'Non_Drive_End']
start_time = datetime(2023, 1, 1)
end_time = datetime(2023, 1, 31)
hours = int((end_time - start_time).total_seconds() / 3600)
timestamps = [start_time + timedelta(hours=i) for i in range(hours)]

data = []

for asset in assets:
    for zone in zones:
        # Base parameters
        base_rpm = 1500 if 'Pump' in asset else 3000
        base_load = 80
        base_vib = 2.0 if 'Pump' in asset else 3.5
        base_temp = 45.0 if 'Pump' in asset else 60.0
        
        # Degradation trend for Pump_A Drive_End
        degradation = 0
        if asset == 'Pump_A' and zone == 'Drive_End':
            degradation = np.linspace(0, 5.0, hours) # Increasing vibration
            
        for i, ts in enumerate(timestamps):
            # Operating conditions
            rpm = base_rpm + np.random.normal(0, 10)
            load_pct = base_load + np.random.normal(0, 5) + 10 * np.sin(i / 24.0)
            load_pct = np.clip(load_pct, 0, 100)
            
            # Vibration
            vib_rms = base_vib + 0.05 * load_pct + np.random.normal(0, 0.2)
            if type(degradation) is np.ndarray:
                vib_rms += degradation[i]
                
            peak_accel = vib_rms * 1.5 + np.random.normal(0, 0.5)
            
            # Temperature
            bearing_temp = base_temp + 0.2 * load_pct + 0.5 * vib_rms + np.random.normal(0, 1.0)
            
            # Quality flag
            quality = 'GOOD' if np.random.rand() > 0.02 else 'BAD'
            
            data.append({
                'timestamp_utc': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'asset_id': asset,
                'zone': zone,
                'vibration_rms_mm_s': round(vib_rms, 3),
                'peak_accel_g': round(peak_accel, 3),
                'bearing_temp_c': round(bearing_temp, 2),
                'rpm': round(rpm, 1),
                'load_pct': round(load_pct, 1),
                'quality_flag': quality
            })

df = pd.DataFrame(data)
df.to_csv('data/sensor_panel_timeseries.csv', index=False)
print('Synthetic data generated successfully.')
