import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

df = pd.read_csv('data/load_15min.csv')
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df.set_index('timestamp_utc', inplace=True)

print(f"Data shape: {df.shape}")
print(f"Date range: {df.index.min()} to {df.index.max()}")
print(f"Load statistics:\n{df['load_mw'].describe()}")

df['hour'] = df.index.hour
df['day_of_week'] = df.index.dayofweek
df['date'] = df.index.date

fig1, ax1 = plt.subplots(figsize=(14, 5))
ax1.plot(df.index, df['load_mw'], linewidth=0.8, color='steelblue')
ax1.set_xlabel('Date/Time (UTC)')
ax1.set_ylabel('Load (MW)')
ax1.set_title('15-Minute Load Profile (Jan 1-7, 2026)')
ax1.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/load_timeseries.png', dpi=150)
plt.close()
print("Saved: load_timeseries.png")

fig2, ax2 = plt.subplots(figsize=(12, 6))
for date in df['date'].unique():
    day_data = df[df['date'] == date]
    hours = day_data['hour'] + day_data.index.minute / 60
    ax2.plot(hours, day_data['load_mw'], label=date.strftime('%Y-%m-%d'), linewidth=1.5, alpha=0.8)
ax2.set_xlabel('Hour of Day')
ax2.set_ylabel('Load (MW)')
ax2.set_title('Daily Load Profiles by Date')
ax2.legend(loc='upper right', fontsize=8)
ax2.set_xticks(range(0, 25, 2))
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/daily_profiles.png', dpi=150)
plt.close()
print("Saved: daily_profiles.png")

hourly_avg = df.groupby('hour')['load_mw'].agg(['mean', 'std'])
fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.bar(hourly_avg.index, hourly_avg['mean'], yerr=hourly_avg['std'], color='steelblue', alpha=0.7, capsize=3)
ax3.set_xlabel('Hour of Day')
ax3.set_ylabel('Average Load (MW)')
ax3.set_title('Average Hourly Load Pattern with Standard Deviation')
ax3.set_xticks(range(0, 24, 2))
ax3.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('report/images/hourly_pattern.png', dpi=150)
plt.close()
print("Saved: hourly_pattern.png")

fig4, ax4 = plt.subplots(figsize=(8, 5))
ax4.hist(df['load_mw'], bins=30, color='steelblue', edgecolor='black', alpha=0.7)
ax4.axvline(df['load_mw'].mean(), color='red', linestyle='--', linewidth=2, label=f"Mean: {df['load_mw'].mean():.2f} MW")
ax4.axvline(df['load_mw'].quantile(0.95), color='green', linestyle='--', linewidth=2, label=f"95th %ile: {df['load_mw'].quantile(0.95):.2f} MW")
ax4.set_xlabel('Load (MW)')
ax4.set_ylabel('Frequency')
ax4.set_title('Distribution of Load Values')
ax4.legend()
ax4.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/load_distribution.png', dpi=150)
plt.close()
print("Saved: load_distribution.png")

dow_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
df['dow_name'] = df['day_of_week'].map(dow_map)
dow_avg = df.groupby('dow_name')['load_mw'].mean()
dow_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
dow_avg = dow_avg.reindex(dow_order)
fig5, ax5 = plt.subplots(figsize=(10, 5))
ax5.bar(dow_avg.index, dow_avg.values, color='steelblue', alpha=0.7)
ax5.set_xlabel('Day of Week')
ax5.set_ylabel('Average Load (MW)')
ax5.set_title('Average Load by Day of Week')
ax5.set_ylim(0, dow_avg.max() * 1.1)
for i, v in enumerate(dow_avg.values):
    ax5.text(i, v + 0.5, f'{v:.1f}', ha='center', fontsize=9)
ax5.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('report/images/day_of_week.png', dpi=150)
plt.close()
print("Saved: day_of_week.png")

peak_threshold = df['load_mw'].quantile(0.9)
peak_hours = df[df['load_mw'] >= peak_threshold]
fig6, ax6 = plt.subplots(figsize=(10, 5))
ax6.scatter(peak_hours['hour'], peak_hours['load_mw'], alpha=0.6, color='red', label='Peak Load (>90th %ile)')
ax6.hist(df['hour'], bins=24, alpha=0.3, color='gray', label='All Hours', density=True)
ax6.set_xlabel('Hour of Day')
ax6.set_ylabel('Load (MW) / Density')
ax6.set_title(f'Peak Load Hours (Threshold: {peak_threshold:.1f} MW)')
ax6.legend()
ax6.set_xticks(range(0, 24, 2))
ax6.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/peak_analysis.png', dpi=150)
plt.close()
print("Saved: peak_analysis.png")

window = 96
df['ma_24h'] = df['load_mw'].rolling(window=window, min_periods=1).mean()
df['lag_24h'] = df['load_mw'].shift(window)
df['forecast_error'] = df['load_mw'] - df['lag_24h']

forecast_df = df.dropna(subset=['lag_24h'])
fig7, ax7 = plt.subplots(figsize=(12, 5))
ax7.plot(forecast_df.index, forecast_df['load_mw'], label='Actual', linewidth=1, alpha=0.8)
ax7.plot(forecast_df.index, forecast_df['lag_24h'], label='24h Lag Forecast', linewidth=1, linestyle='--', alpha=0.8)
ax7.set_xlabel('Date/Time (UTC)')
ax7.set_ylabel('Load (MW)')
ax7.set_title('Actual vs 24-Hour Lag Forecast')
ax7.legend()
ax7.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/forecast_performance.png', dpi=150)
plt.close()
print("Saved: forecast_performance.png")

mae = np.mean(np.abs(forecast_df['forecast_error']))
rmse = np.sqrt(np.mean(forecast_df['forecast_error']**2))
mape = np.mean(np.abs(forecast_df['forecast_error'] / forecast_df['load_mw'])) * 100
print(f"\nForecast Metrics (24h lag): MAE={mae:.3f} MW, RMSE={rmse:.3f} MW, MAPE={mape:.2f}%")

fig8, ax8 = plt.subplots(figsize=(8, 5))
ax8.hist(forecast_df['forecast_error'], bins=30, color='steelblue', edgecolor='black', alpha=0.7)
ax8.axvline(0, color='red', linestyle='--', linewidth=2)
ax8.set_xlabel('Forecast Error (MW)')
ax8.set_ylabel('Frequency')
ax8.set_title(f'Distribution of Forecast Errors (MAE={mae:.2f} MW, RMSE={rmse:.2f} MW)')
ax8.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/forecast_errors.png', dpi=150)
plt.close()
print("Saved: forecast_errors.png")

summary = {
    'total_records': len(df),
    'date_range_start': str(df.index.min()),
    'date_range_end': str(df.index.max()),
    'mean_load_mw': float(df['load_mw'].mean()),
    'std_load_mw': float(df['load_mw'].std()),
    'min_load_mw': float(df['load_mw'].min()),
    'max_load_mw': float(df['load_mw'].max()),
    'p95_load_mw': float(df['load_mw'].quantile(0.95)),
    'p99_load_mw': float(df['load_mw'].quantile(0.99)),
    'mae_mw': float(mae),
    'rmse_mw': float(rmse),
    'mape_percent': float(mape)
}
summary_df = pd.DataFrame([summary])
summary_df.to_csv('outputs/summary_statistics.csv', index=False)
print("\nSaved: outputs/summary_statistics.csv")
print("\n=== Analysis Complete ===")
