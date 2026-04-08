import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os

# Load annual forecast
annual_df = pd.read_csv('outputs/annual_forecast_15min.csv', index_col=0, parse_dates=True)

# 1. Calculate reliability metrics
peak_load = annual_df['final_forecast'].max()
avg_load = annual_df['final_forecast'].mean()
min_load = annual_df['final_forecast'].min()

# Load duration curve
load_sorted = np.sort(annual_df['final_forecast'].values)[::-1]  # Descending
hours = np.arange(1, len(load_sorted) + 1) / 4  # Convert 15-min intervals to hours

plt.figure(figsize=(12, 6))
plt.plot(hours, load_sorted, 'b-', linewidth=2)
plt.axhline(y=avg_load, color='r', linestyle='--', alpha=0.7, label=f'Average ({avg_load:.1f} MW)')
plt.axhline(y=peak_load, color='g', linestyle='--', alpha=0.7, label=f'Peak ({peak_load:.1f} MW)')
plt.fill_between(hours, 0, load_sorted, alpha=0.3, color='b')
plt.title('Load Duration Curve 2026', fontsize=14)
plt.xlabel('Hours')
plt.ylabel('Load (MW)')
plt.xlim(0, 8760)  # Hours in a year
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/load_duration_curve.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Calculate capacity margin
# Assume system capacity based on peak + 20% reserve margin
system_capacity = peak_load * 1.20
capacity_margin = system_capacity - peak_load
capacity_margin_percent = (capacity_margin / system_capacity) * 100

# Hours above certain thresholds
threshold_90 = peak_load * 0.90
threshold_95 = peak_load * 0.95
hours_above_90 = (annual_df['final_forecast'] > threshold_90).sum() / 4  # Convert to hours
hours_above_95 = (annual_df['final_forecast'] > threshold_95).sum() / 4

# 3. Calculate LOLP (Loss of Load Probability)
# Simplified approach: probability that load exceeds available capacity
# Assuming normal distribution of forecast errors based on test performance
forecast_error_std = 4.16  # RMSE from mean forecast
lolp = 1 - stats.norm.cdf(system_capacity, loc=peak_load, scale=forecast_error_std)

# 4. Calculate EENS (Expected Energy Not Served)
# Simplified calculation
if lolp > 0:
    # Expected shortfall when load exceeds capacity
    expected_shortfall = forecast_error_std * stats.norm.pdf(
        (system_capacity - peak_load) / forecast_error_std
    ) - (system_capacity - peak_load) * lolp
    eens = expected_shortfall * 8760  # Hours in year
else:
    eens = 0

# 5. Create reliability summary
reliability_metrics = pd.DataFrame({
    'Metric': [
        'Peak Load (MW)',
        'Average Load (MW)',
        'Minimum Load (MW)',
        'Load Factor',
        'System Capacity (MW)',
        'Capacity Margin (MW)',
        'Capacity Margin (%)',
        'Hours > 90% of Peak',
        'Hours > 95% of Peak',
        'Loss of Load Probability (LOLP)',
        'Expected Energy Not Served (EENS, MWh)'
    ],
    'Value': [
        peak_load,
        avg_load,
        min_load,
        avg_load / peak_load,
        system_capacity,
        capacity_margin,
        capacity_margin_percent,
        hours_above_90,
        hours_above_95,
        lolp,
        eens
    ]
})

reliability_metrics.to_csv('outputs/reliability_metrics.csv', index=False)
print("Reliability metrics saved to outputs/reliability_metrics.csv")
print("\nReliability Summary:")
print(reliability_metrics.to_string(index=False))

# 6. Monthly reliability analysis
monthly_peaks = annual_df.resample('M')['final_forecast'].max()
monthly_avg = annual_df.resample('M')['final_forecast'].mean()
monthly_capacity_margin = system_capacity - monthly_peaks
monthly_capacity_margin_pct = (monthly_capacity_margin / system_capacity) * 100

monthly_reliability = pd.DataFrame({
    'Month': monthly_peaks.index.month_name(),
    'Peak Load (MW)': monthly_peaks.values,
    'Average Load (MW)': monthly_avg.values,
    'Capacity Margin (MW)': monthly_capacity_margin.values,
    'Capacity Margin (%)': monthly_capacity_margin_pct.values
})

monthly_reliability.to_csv('outputs/monthly_reliability.csv', index=False)

# Plot monthly peaks and capacity margins
fig, ax1 = plt.subplots(figsize=(14, 6))

color = 'tab:red'
ax1.set_xlabel('Month')
ax1.set_ylabel('Load (MW)', color=color)
ax1.plot(monthly_reliability['Month'], monthly_reliability['Peak Load (MW)'], 
         color=color, marker='o', linewidth=2, label='Monthly Peak')
ax1.plot(monthly_reliability['Month'], monthly_reliability['Average Load (MW)'], 
         color='orange', marker='s', linewidth=2, alpha=0.7, label='Monthly Average')
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_xticklabels(monthly_reliability['Month'], rotation=45)

ax2 = ax1.twinx()
color = 'tab:blue'
ax2.set_ylabel('Capacity Margin (%)', color=color)
ax2.plot(monthly_reliability['Month'], monthly_reliability['Capacity Margin (%)'], 
         color=color, marker='^', linestyle='--', linewidth=2, label='Capacity Margin')
ax2.tick_params(axis='y', labelcolor=color)
ax2.axhline(y=15, color='gray', linestyle=':', alpha=0.7, label='15% Target')

fig.tight_layout()
fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
plt.title('Monthly Peak Load and Capacity Margin', fontsize=14)
plt.savefig('report/images/monthly_reliability.png', dpi=300, bbox_inches='tight')
plt.close()

# 7. Create risk curves
# Simulate different capacity levels and calculate LOLP
capacity_levels = np.linspace(peak_load * 0.9, peak_load * 1.3, 50)
lolp_curve = []
eens_curve = []

for capacity in capacity_levels:
    lolp_val = 1 - stats.norm.cdf(capacity, loc=peak_load, scale=forecast_error_std)
    lolp_curve.append(lolp_val)
    
    if lolp_val > 0:
        expected_shortfall = forecast_error_std * stats.norm.pdf(
            (capacity - peak_load) / forecast_error_std
        ) - (capacity - peak_load) * lolp_val
        eens_val = expected_shortfall * 8760
    else:
        eens_val = 0
    eens_curve.append(eens_val)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.plot(capacity_levels, lolp_curve, 'b-', linewidth=2)
ax1.axvline(x=system_capacity, color='r', linestyle='--', alpha=0.7, label=f'Planned Capacity ({system_capacity:.1f} MW)')
ax1.set_xlabel('System Capacity (MW)')
ax1.set_ylabel('Loss of Load Probability (LOLP)')
ax1.set_title('LOLP vs System Capacity')
ax1.grid(True, alpha=0.3)
ax1.legend()

ax2.plot(capacity_levels, eens_curve, 'r-', linewidth=2)
ax2.axvline(x=system_capacity, color='b', linestyle='--', alpha=0.7, label=f'Planned Capacity ({system_capacity:.1f} MW)')
ax2.set_xlabel('System Capacity (MW)')
ax2.set_ylabel('Expected Energy Not Served (MWh)')
ax2.set_title('EENS vs System Capacity')
ax2.grid(True, alpha=0.3)
ax2.legend()

plt.tight_layout()
plt.savefig('report/images/risk_curves.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nReliability analysis complete.")
