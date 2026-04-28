import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load data
df = pd.read_csv('data/sensor_panel_timeseries.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])

# Filter out BAD quality data for analysis
df_clean = df[df['quality_flag'] == 'GOOD'].copy()

# 2. Vibration Evolution over Time (Separate plots for clarity)
fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
for i, asset in enumerate(df_clean['asset_id'].unique()):
    asset_data = df_clean[df_clean['asset_id'] == asset]
    sns.lineplot(data=asset_data, x='timestamp_utc', y='vibration_rms_mm_s', hue='zone', ax=axes[i])
    axes[i].set_title(f'Vibration RMS Evolution - {asset}')
    axes[i].set_ylabel('Vibration RMS (mm/s)')

axes[-1].set_xlabel('Time')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/vibration_over_time_split.png')
plt.close()

# 3. Relationships among variables (Pairplot for a comprehensive view)
# Select a subset of data to avoid overplotting, or use hexbin/kde
# Let's use a pairplot colored by asset
vars_to_plot = ['vibration_rms_mm_s', 'peak_accel_g', 'bearing_temp_c', 'rpm', 'load_pct']
sns.pairplot(df_clean, vars=vars_to_plot, hue='asset_id', plot_kws={'alpha': 0.5})
plt.savefig('report/images/pairplot.png')
plt.close()

print('Additional analysis complete.')
