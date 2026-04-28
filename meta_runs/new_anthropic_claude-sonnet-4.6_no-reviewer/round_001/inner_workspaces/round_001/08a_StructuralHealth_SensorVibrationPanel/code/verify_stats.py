import pandas as pd
import numpy as np
from scipy import stats

df = pd.read_csv('data/sensor_panel_timeseries.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

print('=== DATA VERIFICATION ===')
print(f'Shape: {df.shape}')
print(f'Assets: {sorted(df.asset_id.unique().tolist())}')
print(f'Zones: {sorted(df.zone.unique().tolist())}')
print(f'Time range: {df.timestamp_utc.min()} to {df.timestamp_utc.max()}')
print(f'Duration: {df.timestamp_utc.max() - df.timestamp_utc.min()}')
print(f'Quality flags: {df.quality_flag.value_counts().to_dict()}')
print()
print('Fleet-level stats:')
print(df[['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']].describe().round(2))
print()
print('Per-asset vibration RMS:')
print(df.groupby('asset_id')['vibration_rms_mm_s'].agg(['mean', 'std', 'max', 'min']).round(3))
print()
print('Per-asset bearing temp:')
print(df.groupby('asset_id')['bearing_temp_c'].agg(['mean', 'std', 'max', 'min']).round(2))
print()
print('Per-asset RPM:')
print(df.groupby('asset_id')['rpm'].agg(['mean', 'std']).round(1))
print()
print('Per-asset load:')
print(df.groupby('asset_id')['load_pct'].agg(['mean', 'std']).round(1))
print()

# Risk ranking
df_clean = df.copy()
for col in ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c']:
    df_clean[f'{col}_z'] = stats.zscore(df_clean[col].fillna(df_clean[col].mean()))
df_clean['risk_score'] = (df_clean['vibration_rms_mm_s_z'] + 
                           df_clean['peak_accel_g_z'] + 
                           df_clean['bearing_temp_c_z']) / 3
asset_risk = df_clean.groupby('asset_id')['risk_score'].mean().sort_values(ascending=False)
print('Risk ranking:')
print(asset_risk.round(4))

# Correlation
print()
print('Correlation matrix:')
print(df[['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']].corr().round(3))

# Sampling interval
df_sorted = df.sort_values(['asset_id', 'timestamp_utc'])
df_sorted['time_diff'] = df_sorted.groupby('asset_id')['timestamp_utc'].diff()
print()
print('Sampling interval (seconds):')
print(df_sorted['time_diff'].dt.total_seconds().describe())

with open('outputs/verification.txt', 'w') as f:
    f.write('=== DATA VERIFICATION ===\n')
    f.write(f'Shape: {df.shape}\n')
    f.write(f'Assets: {sorted(df.asset_id.unique().tolist())}\n')
    f.write(f'Zones: {sorted(df.zone.unique().tolist())}\n')
    f.write(f'Time range: {df.timestamp_utc.min()} to {df.timestamp_utc.max()}\n')
    f.write(f'Duration: {df.timestamp_utc.max() - df.timestamp_utc.min()}\n')
    f.write(f'Quality flags: {df.quality_flag.value_counts().to_dict()}\n')
    f.write('\nFleet-level stats:\n')
    f.write(df[["vibration_rms_mm_s", "peak_accel_g", "bearing_temp_c", "rpm", "load_pct"]].describe().round(2).to_string())
    f.write('\n\nPer-asset vibration RMS:\n')
    f.write(df.groupby('asset_id')['vibration_rms_mm_s'].agg(['mean', 'std', 'max', 'min']).round(3).to_string())
    f.write('\n\nPer-asset bearing temp:\n')
    f.write(df.groupby('asset_id')['bearing_temp_c'].agg(['mean', 'std', 'max', 'min']).round(2).to_string())
    f.write('\n\nRisk ranking:\n')
    f.write(asset_risk.round(4).to_string())
    f.write('\n\nCorrelation matrix:\n')
    f.write(df[["vibration_rms_mm_s", "peak_accel_g", "bearing_temp_c", "rpm", "load_pct"]].corr().round(3).to_string())
    f.write('\n\nSampling interval (seconds):\n')
    f.write(df_sorted['time_diff'].dt.total_seconds().describe().to_string())
