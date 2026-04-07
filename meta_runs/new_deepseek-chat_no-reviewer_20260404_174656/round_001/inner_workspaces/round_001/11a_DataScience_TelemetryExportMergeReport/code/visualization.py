import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directory
os.makedirs('../report/images', exist_ok=True)

print("Generating visualizations...")

# Load merged data
merged_df = pd.read_csv('../outputs/merged_telemetry.csv')
merged_df['date'] = pd.to_datetime(merged_df['date'])

# 1. Time series plot for each generator unit
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
units = sorted(merged_df['unit'].unique())

for idx, unit in enumerate(units):
    unit_data = merged_df[merged_df['unit'] == unit].sort_values('date')
    ax = axes[idx]
    
    ax.plot(unit_data['date'], unit_data['kwh_site'], 'o-', label='Site Historian', linewidth=2, markersize=6)
    ax.plot(unit_data['date'], unit_data['kwh_field'], 's--', label='Field Export', linewidth=2, markersize=6, alpha=0.7)
    
    ax.set_title(f'Generator {unit} - Daily kWh Production', fontsize=12, fontweight='bold')
    ax.set_ylabel('kWh', fontsize=10)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Add value labels for first and last points
    for i in [0, -1]:
        ax.text(unit_data['date'].iloc[i], unit_data['kwh_site'].iloc[i], 
                f'{unit_data["kwh_site"].iloc[i]}', 
                ha='center', va='bottom', fontsize=8)

axes[-1].set_xlabel('Date', fontsize=10)
plt.tight_layout()
plt.savefig('../report/images/time_series_by_unit.png', dpi=300, bbox_inches='tight')
print("Saved: time_series_by_unit.png")
plt.close()

# 2. Aggregate daily production (sum across all units)
daily_totals = merged_df.groupby('date').agg({
    'kwh_site': 'sum',
    'kwh_field': 'sum'
}).reset_index()

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(daily_totals['date'], daily_totals['kwh_site'], 'o-', label='Site Historian Total', linewidth=2, markersize=8)
ax.plot(daily_totals['date'], daily_totals['kwh_field'], 's--', label='Field Export Total', linewidth=2, markersize=8, alpha=0.7)

ax.set_title('Total Daily kWh Production (All Generator Units)', fontsize=14, fontweight='bold')
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Total kWh', fontsize=12)
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)

# Add value labels
for i, row in daily_totals.iterrows():
    ax.text(row['date'], row['kwh_site'], f'{row["kwh_site"]:.0f}', 
            ha='center', va='bottom', fontsize=9)

plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('../report/images/daily_total_production.png', dpi=300, bbox_inches='tight')
print("Saved: daily_total_production.png")
plt.close()

# 3. Correlation scatter plot
fig, ax = plt.subplots(figsize=(8, 8))

ax.scatter(merged_df['kwh_site'], merged_df['kwh_field'], alpha=0.7, s=80)

# Add perfect correlation line
min_val = min(merged_df['kwh_site'].min(), merged_df['kwh_field'].min())
max_val = max(merged_df['kwh_site'].max(), merged_df['kwh_field'].max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='Perfect Correlation')

ax.set_title('Site vs Field Measurements Correlation', fontsize=14, fontweight='bold')
ax.set_xlabel('Site Historian (kWh)', fontsize=12)
ax.set_ylabel('Field Export (kWh)', fontsize=12)
ax.legend()
ax.grid(True, alpha=0.3)

# Add correlation coefficient
correlation = merged_df['kwh_site'].corr(merged_df['kwh_field'])
ax.text(0.05, 0.95, f'Correlation: {correlation:.6f}', 
        transform=ax.transAxes, fontsize=12, 
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('../report/images/correlation_plot.png', dpi=300, bbox_inches='tight')
print("Saved: correlation_plot.png")
plt.close()

# 4. Statistical summary by unit
unit_stats = merged_df.groupby('unit').agg({
    'kwh_site': ['mean', 'std', 'min', 'max', 'sum'],
    'kwh_field': ['mean', 'std', 'min', 'max', 'sum']
}).round(2)

# Save unit statistics to CSV
unit_stats.to_csv('../outputs/unit_statistics.csv')
print("\nUnit Statistics:")
print(unit_stats)

# 5. Daily statistics
daily_stats = merged_df.groupby('date').agg({
    'kwh_site': ['mean', 'std', 'min', 'max', 'sum'],
    'kwh_field': ['mean', 'std', 'min', 'max', 'sum']
}).round(2)

daily_stats.to_csv('../outputs/daily_statistics.csv')
print("\nDaily statistics saved to outputs/")

# 6. Production trend analysis
merged_df['day_num'] = (merged_df['date'] - merged_df['date'].min()).dt.days + 1

# Linear regression for each unit
from sklearn.linear_model import LinearRegression

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for idx, unit in enumerate(units):
    unit_data = merged_df[merged_df['unit'] == unit].sort_values('day_num')
    X = unit_data[['day_num']]
    y = unit_data['kwh_site']
    
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    
    ax = axes[idx]
    ax.scatter(unit_data['day_num'], unit_data['kwh_site'], alpha=0.7, s=60, label='Actual')
    ax.plot(unit_data['day_num'], y_pred, 'r-', linewidth=2, label=f'Trend (slope={model.coef_[0]:.2f})')
    
    ax.set_title(f'Generator {unit} - Production Trend', fontsize=12, fontweight='bold')
    ax.set_xlabel('Day Number', fontsize=10)
    ax.set_ylabel('kWh', fontsize=10)
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/production_trends.png', dpi=300, bbox_inches='tight')
print("Saved: production_trends.png")
plt.close()

print("\nVisualization complete!")
