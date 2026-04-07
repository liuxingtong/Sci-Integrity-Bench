import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load processed data
df = pd.read_csv('../outputs/processed_load_data.csv', index_col='timestamp_utc', parse_dates=True)
print(f"Data shape: {df.shape}")

# Prepare data
load_series = df['load_mw']

# 1. Generate annual forecast based on weekly patterns
# We have 7 days of data, we'll use this to project for a year

# First, let's analyze weekly patterns
df['hour_of_day'] = df.index.hour + df.index.minute/60
df['day_of_week'] = df.index.dayofweek

# Calculate average daily profile
daily_profile = df.groupby('hour_of_day')['load_mw'].mean()

# Calculate day-of-week multipliers
daily_totals = df.groupby(df.index.date)['load_mw'].mean()
day_of_week_avg = df.groupby('day_of_week')['load_mw'].mean()
overall_avg = df['load_mw'].mean()
day_multipliers = day_of_week_avg / overall_avg

print("\n=== Day of Week Multipliers ===")
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
for i, day in enumerate(days):
    print(f"{day:<12}: {day_multipliers[i]:.4f}")

# 2. Create annual forecast
# Generate dates for a full year (2026)
dates_2026 = pd.date_range(start='2026-01-01', end='2026-12-31', freq='15min')
annual_forecast = pd.DataFrame(index=dates_2026)
annual_forecast['hour_of_day'] = annual_forecast.index.hour + annual_forecast.index.minute/60
annual_forecast['day_of_week'] = annual_forecast.index.dayofweek
annual_forecast['month'] = annual_forecast.index.month

# Apply daily profile
annual_forecast['base_load'] = annual_forecast['hour_of_day'].map(daily_profile)

# Apply day-of-week multipliers
annual_forecast['day_multiplier'] = annual_forecast['day_of_week'].map(day_multipliers)
annual_forecast['load_forecast'] = annual_forecast['base_load'] * annual_forecast['day_multiplier']

# 3. Add seasonal adjustment based on monthly patterns
# Calculate monthly averages from our week (January)
jan_avg = df['load_mw'].mean()

# Typical seasonal factors for electricity load (example values)
# These would normally come from historical data, but we'll use typical patterns
seasonal_factors = {
    1: 1.00,   # January (baseline)
    2: 0.98,   # February
    3: 0.95,   # March
    4: 0.92,   # April
    5: 0.90,   # May
    6: 0.92,   # June
    7: 0.95,   # July
    8: 0.98,   # August
    9: 1.00,   # September
    10: 1.02,  # October
    11: 1.05,  # November
    12: 1.08   # December
}

annual_forecast['seasonal_factor'] = annual_forecast['month'].map(seasonal_factors)
annual_forecast['load_forecast_seasonal'] = annual_forecast['load_forecast'] * annual_forecast['seasonal_factor']

# 4. Add growth factor (assuming 2% annual growth from 2026 to 2027)
# For reliability planning, we need to forecast for future years
years_ahead = 1  # Forecast for 2027
growth_rate = 0.02  # 2% annual growth
annual_forecast['load_forecast_2027'] = annual_forecast['load_forecast_seasonal'] * (1 + growth_rate)**years_ahead

# 5. Calculate key statistics for reliability planning
print("\n=== Annual Forecast Statistics ===")
print(f"Average daily load (2026): {annual_forecast['load_forecast_seasonal'].mean():.2f} MW")
print(f"Peak load (2026): {annual_forecast['load_forecast_seasonal'].max():.2f} MW")
print(f"Minimum load (2026): {annual_forecast['load_forecast_seasonal'].min():.2f} MW")
print(f"Load factor (2026): {(annual_forecast['load_forecast_seasonal'].mean() / annual_forecast['load_forecast_seasonal'].max() * 100):.1f}%")

print(f"\nAverage daily load (2027): {annual_forecast['load_forecast_2027'].mean():.2f} MW")
print(f"Peak load (2027): {annual_forecast['load_forecast_2027'].max():.2f} MW")
print(f"Growth in peak load: {((annual_forecast['load_forecast_2027'].max() / annual_forecast['load_forecast_seasonal'].max() - 1) * 100):.1f}%")

# 6. Calculate reserve margin requirements
# Typical reserve margin for reliability: 15-20%
reserve_margin = 0.15  # 15%
required_capacity_2026 = annual_forecast['load_forecast_seasonal'].max() * (1 + reserve_margin)
required_capacity_2027 = annual_forecast['load_forecast_2027'].max() * (1 + reserve_margin)

print(f"\n=== Reliability Planning ===")
print(f"Peak load 2026: {annual_forecast['load_forecast_seasonal'].max():.2f} MW")
print(f"Required capacity (15% reserve): {required_capacity_2026:.2f} MW")
print(f"Capacity deficit/surplus: {required_capacity_2026 - annual_forecast['load_forecast_seasonal'].max():.2f} MW")

print(f"\nPeak load 2027: {annual_forecast['load_forecast_2027'].max():.2f} MW")
print(f"Required capacity (15% reserve): {required_capacity_2027:.2f} MW")
print(f"Capacity deficit/surplus: {required_capacity_2027 - annual_forecast['load_forecast_2027'].max():.2f} MW")

# 7. Plot annual forecast
plt.figure(figsize=(14, 8))

# Plot one week sample
sample_week = annual_forecast.loc['2026-01-01':'2026-01-07']
plt.plot(sample_week.index, sample_week['load_forecast_seasonal'], 'b-', linewidth=1, alpha=0.7, label='Forecasted Load')

# Add actual data for comparison
plt.plot(df.index, df['load_mw'], 'r-', linewidth=1.5, alpha=0.8, label='Actual (Jan 1-7, 2026)')

plt.title('Load Forecast: One Week Sample (January 1-7, 2026)')
plt.xlabel('Time')
plt.ylabel('Load (MW)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/annual_forecast_sample.png', dpi=300)
plt.close()

# 8. Plot monthly averages
monthly_avg = annual_forecast.groupby('month')['load_forecast_seasonal'].mean()
monthly_peak = annual_forecast.groupby('month')['load_forecast_seasonal'].max()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].bar(monthly_avg.index, monthly_avg.values, alpha=0.7)
axes[0].set_title('Average Monthly Load Forecast (2026)')
axes[0].set_xlabel('Month')
axes[0].set_ylabel('Average Load (MW)')
axes[0].set_xticks(range(1, 13))
axes[0].set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
axes[0].grid(True, alpha=0.3, axis='y')

axes[1].bar(monthly_peak.index, monthly_peak.values, alpha=0.7, color='orange')
axes[1].set_title('Peak Monthly Load Forecast (2026)')
axes[1].set_xlabel('Month')
axes[1].set_ylabel('Peak Load (MW)')
axes[1].set_xticks(range(1, 13))
axes[1].set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../report/images/monthly_forecast.png', dpi=300)
plt.close()

# 9. Plot daily load duration curve
# Sort loads in descending order
sorted_loads = np.sort(annual_forecast['load_forecast_seasonal'].values)[::-1]
hours = np.arange(1, len(sorted_loads) + 1)

plt.figure(figsize=(12, 6))
plt.plot(hours, sorted_loads, 'b-', linewidth=2)
plt.fill_between(hours, 0, sorted_loads, alpha=0.3)
plt.title('Load Duration Curve (2026)')
plt.xlabel('Hours (sorted from highest to lowest load)')
plt.ylabel('Load (MW)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/load_duration_curve.png', dpi=300)
plt.close()

# 10. Calculate and plot reliability metrics
# Probability of exceeding certain load thresholds
thresholds = [120, 125, 130, 135]
print("\n=== Load Exceedance Probabilities ===")
for threshold in thresholds:
    prob = (annual_forecast['load_forecast_seasonal'] > threshold).mean() * 100
    print(f"Probability load > {threshold} MW: {prob:.2f}%")

# Save forecast results
annual_forecast[['load_forecast_seasonal', 'load_forecast_2027']].to_csv('../outputs/annual_forecast.csv')
print("\nAnnual forecast saved to outputs/annual_forecast.csv")
print("Analysis complete.")
