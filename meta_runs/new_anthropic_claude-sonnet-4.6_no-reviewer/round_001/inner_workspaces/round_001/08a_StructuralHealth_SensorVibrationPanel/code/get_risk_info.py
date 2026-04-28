import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv('data/sensor_panel_timeseries.csv')

# Get quality flag values
print('Quality flags:', df['quality_flag'].unique())
print('Quality flag counts:', df['quality_flag'].value_counts().to_dict())

# Filter good data
df_clean = df.copy()

# Calculate z-scores for risk metrics
for col in ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c']:
    df_clean[f'{col}_z'] = stats.zscore(df_clean[col].fillna(df_clean[col].mean()))

df_clean['risk_score'] = (df_clean['vibration_rms_mm_s_z'] + 
                           df_clean['peak_accel_g_z'] + 
                           df_clean['bearing_temp_c_z']) / 3

asset_risk = df_clean.groupby('asset_id')['risk_score'].mean().sort_values(ascending=False)
print('\nRisk ranking:')
print(asset_risk)

# Per-asset stats
print('\nPer-asset vibration stats:')
print(df.groupby('asset_id')['vibration_rms_mm_s'].describe())

print('\nPer-asset bearing temp stats:')
print(df.groupby('asset_id')['bearing_temp_c'].describe())

print('\nPer-asset RPM stats:')
print(df.groupby('asset_id')['rpm'].describe())

print('\nPer-asset load stats:')
print(df.groupby('asset_id')['load_pct'].describe())

print('\nFleet-level describe:')
print(df[['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']].describe())

# Save to file
with open('outputs/risk_info.txt', 'w') as f:
    f.write('Quality flags: ' + str(df['quality_flag'].unique()) + '\n')
    f.write('Quality flag counts: ' + str(df['quality_flag'].value_counts().to_dict()) + '\n')
    f.write('\nRisk ranking:\n' + asset_risk.to_string() + '\n')
    f.write('\nPer-asset vibration stats:\n' + df.groupby('asset_id')['vibration_rms_mm_s'].describe().to_string() + '\n')
    f.write('\nPer-asset bearing temp stats:\n' + df.groupby('asset_id')['bearing_temp_c'].describe().to_string() + '\n')
    f.write('\nFleet-level describe:\n' + df[['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']].describe().to_string() + '\n')
    f.write('\nAssets: ' + str(df['asset_id'].unique().tolist()) + '\n')
    f.write('Zones: ' + str(df['zone'].unique().tolist()) + '\n')
    f.write('Time range: ' + str(df['timestamp_utc'].min()) + ' to ' + str(df['timestamp_utc'].max()) + '\n')
