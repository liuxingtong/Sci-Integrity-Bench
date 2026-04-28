import pandas as pd
import json

df = pd.read_csv('data/sensor_panel_timeseries.csv')

info = {
    'assets': df['asset_id'].unique().tolist(),
    'zones': df['zone'].unique().tolist(),
    'shape': list(df.shape),
    'time_min': str(df['timestamp_utc'].min()),
    'time_max': str(df['timestamp_utc'].max()),
    'quality_flags': df['quality_flag'].value_counts().to_dict(),
    'describe': df.describe().to_dict()
}

with open('outputs/data_info2.json', 'w') as f:
    json.dump(info, f, indent=2, default=str)

print('Done')
