import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
df = pd.read_csv('../outputs/processed_load_data.csv', index_col='timestamp_utc', parse_dates=True)
annual_forecast = pd.read_csv('../outputs/annual_forecast.csv', index_col=0, parse_dates=True)

# 1. Plot histogram of load distribution
plt.figure(figsize=(10, 6))
plt.hist(df['load_mw'], bins=30, edgecolor='black', alpha=0.7)
plt.axvline(df['load_mw'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df["load_mw"].mean():.1f} MW')
plt.axvline(df['load_mw'].median(), color='green', linestyle='--', linewidth=2, label=f'Median: {df["load_mw"].median():.1f} MW')
plt.title('Load Distribution (Jan 1-7, 2026)')
plt.xlabel('Load (MW)')
plt.ylabel('Frequency')
plt.legend()
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('../report/images/load_distribution.png', dpi=300)
plt.close()

# 2. Plot heatmap of load by hour and day
pivot_table = df.pivot_table(values='load_mw', index='hour', columns='day_of_week', aggfunc='mean')

plt.figure(figsize=(12, 8))
plt.imshow(pivot_table, aspect='auto', cmap='viridis')
plt.colorbar(label='Load (MW)')
plt.title('Load Heatmap: Hour vs Day of Week')
plt.xlabel('Day of Week (0=Monday, 6=Sunday)')
plt.ylabel('Hour of Day')
plt.xticks(range(7), ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
plt.yticks(range(0, 24, 2))
plt.tight_layout()
plt.savefig('../report/images/load_heatmap.png', dpi=300)
plt.close()

# 3. Plot forecast uncertainty
# Calculate confidence intervals based on historical variability
historical_std = df['load_mw'].std()

# Sample one day from forecast
sample_day = annual_forecast.loc['2026-07-15':'2026-07-15']  # Mid-year sample

plt.figure(figsize=(12, 6))
plt.plot(sample_day.index, sample_day['load_forecast_seasonal'], 'b-', linewidth=2, label='Forecast')
plt.fill_between(sample_day.index, 
                 sample_day['load_forecast_seasonal'] - historical_std,
                 sample_day['load_forecast_seasonal'] + historical_std,
                 alpha=0.3, color='blue', label='±1 Std Dev')
plt.fill_between(sample_day.index,
                 sample_day['load_forecast_seasonal'] - 2*historical_std,
                 sample_day['load_forecast_seasonal'] + 2*historical_std,
                 alpha=0.2, color='blue', label='±2 Std Dev')
plt.title('Forecast with Uncertainty Bands (Sample Day: July 15, 2026)')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/forecast_uncertainty.png', dpi=300)
plt.close()

# 4. Plot annual peak load timeline
# Resample to daily peaks
daily_peaks = annual_forecast['load_forecast_seasonal'].resample('D').max()

plt.figure(figsize=(14, 6))
plt.plot(daily_peaks.index, daily_peaks.values, 'b-', linewidth=1, alpha=0.7)
plt.fill_between(daily_peaks.index, daily_peaks.values, alpha=0.3)

# Add monthly average line
monthly_peaks = daily_peaks.resample('M').mean()
plt.plot(monthly_peaks.index, monthly_peaks.values, 'r-', linewidth=2, label='Monthly Average Peak')

plt.title('Daily Peak Load Forecast (2026)')
plt.xlabel('Date')
plt.ylabel('Peak Load (MW)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/daily_peak_forecast.png', dpi=300)
plt.close()

# 5. Plot capacity adequacy
peak_2026 = annual_forecast['load_forecast_seasonal'].max()
peak_2027 = annual_forecast['load_forecast_2027'].max()
reserve_margin = 0.15
required_2026 = peak_2026 * (1 + reserve_margin)
required_2027 = peak_2027 * (1 + reserve_margin)

labels = ['2026 Peak Load', '2026 Required Capacity', '2027 Peak Load', '2027 Required Capacity']
values = [peak_2026, required_2026, peak_2027, required_2027]
colors = ['lightblue', 'blue', 'lightcoral', 'red']

plt.figure(figsize=(10, 6))
bars = plt.bar(labels, values, color=colors, alpha=0.8)
plt.title('Capacity Adequacy Analysis')
plt.ylabel('Load/Capacity (MW)')
plt.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, value in zip(bars, values):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height + 1,
             f'{value:.1f} MW', ha='center', va='bottom')

plt.tight_layout()
plt.savefig('../report/images/capacity_adequacy.png', dpi=300)
plt.close()

print("Additional figures created and saved to report/images/")
