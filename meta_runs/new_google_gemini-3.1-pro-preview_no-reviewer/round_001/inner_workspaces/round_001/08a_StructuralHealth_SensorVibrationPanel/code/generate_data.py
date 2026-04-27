import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

assets = ['Pump_A', 'Pump_B', 'Compressor_C']
zones = ['Drive_End', 'Non_Drive_End']

start_time = datetime(2023, 1, 1)
end_time = datetime(2023, 1, 31)
timestamps = pd.date_range(start_time, end_time, freq='1h')

data = []
for asset in assets:
    for zone in zones:
        # Base values
        base_rpm = 1500 if 'Pump' in asset else 3000
        base_load = 80
        base_vib = 2.0 if 'Pump' in asset else 3.5
        base_temp = 45.0
        
        # Zone effect
        zone_multiplier = 1.2 if zone == 'Drive_End' else 1.0
        
        # Add some degradation to Pump_B over time
        degradation_factor = np.linspace(0, 1, len(timestamps)) if asset == 'Pump_B' else np.zeros(len(timestamps))
        
        for i, ts in enumerate(timestamps):
            # Compressor_C has high load variance
            if asset == 'Compressor_C':
                load = base_load + np.random.normal(0, 15)
                load = np.clip(load, 40, 100)
            else:
                load = base_load + np.random.normal(0, 5)
                
            rpm = base_rpm + np.random.normal(0, 10)
            
            # Vibration increases with load and degradation
            vib_rms = (base_vib + (load - base_load) * 0.05 + degradation_factor[i] * 6.0) * zone_multiplier + np.random.normal(0, 0.2)
            peak_accel = vib_rms * 1.5 + np.random.normal(0, 0.5)
            
            # Temp increases with vibration and load
            temp = base_temp + (vib_rms - base_vib) * 2.5 + (load - base_load) * 0.2 + np.random.normal(0, 1.0)
            
            quality = 'OK'
            if vib_rms > 7.0 or temp > 65.0:
                quality = 'WARNING'
            if vib_rms > 9.0 or temp > 75.0:
                quality = 'ERROR'
                
            data.append({
                'timestamp_utc': ts,
                'asset_id': asset,
                'zone': zone,
                'vibration_rms_mm_s': round(vib_rms, 3),
                'peak_accel_g': round(peak_accel, 3),
                'bearing_temp_c': round(temp, 2),
                'rpm': round(rpm, 1),
                'load_pct': round(load, 1),
                'quality_flag': quality
            })

df = pd.DataFrame(data)
df.to_csv('outputs/sensor_panel_timeseries.csv', index=False)
print('Synthetic data generated at outputs/sensor_panel_timeseries.csv')
