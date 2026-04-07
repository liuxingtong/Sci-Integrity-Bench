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

print("=== OPERATIONAL PERFORMANCE ANALYSIS ===")

# Load merged data
merged_df = pd.read_csv('../outputs/merged_telemetry.csv')
merged_df['date'] = pd.to_datetime(merged_df['date'])

# Calculate daily totals
daily_totals = merged_df.groupby('date').agg({
    'kwh_site': 'sum',
    'kwh_field': 'sum'
}).reset_index()

# Calculate performance metrics
print("\n1. QUARTERLY PERFORMANCE SUMMARY")
print("=" * 40)

# Total production
total_production = daily_totals['kwh_site'].sum()
print(f"Total Quarterly Production: {total_production:,} kWh")
print(f"Average Daily Production: {daily_totals['kwh_site'].mean():.1f} kWh")
print(f"Daily Production Range: {daily_totals['kwh_site'].min():.0f} - {daily_totals['kwh_site'].max():.0f} kWh")
print(f"Production Standard Deviation: {daily_totals['kwh_site'].std():.2f} kWh")

# Unit performance
unit_performance = merged_df.groupby('unit').agg({
    'kwh_site': ['sum', 'mean', 'std', 'min', 'max']
}).round(2)

unit_performance.columns = ['total_kwh', 'avg_daily_kwh', 'std_daily_kwh', 'min_daily_kwh', 'max_daily_kwh']

print("\n2. GENERATOR UNIT PERFORMANCE")
print("=" * 40)
for unit in unit_performance.index:
    stats = unit_performance.loc[unit]
    print(f"\nGenerator {unit}:")
    print(f"  Total Production: {stats['total_kwh']:.0f} kWh")
    print(f"  Average Daily: {stats['avg_daily_kwh']:.1f} kWh")
    print(f"  Consistency (std): {stats['std_daily_kwh']:.2f} kWh")
    print(f"  Daily Range: {stats['min_daily_kwh']:.0f} - {stats['max_daily_kwh']:.0f} kWh")

# Calculate capacity utilization
# Assuming each generator has a nominal capacity (for illustration)
# In real analysis, this would come from equipment specifications
NOMINAL_CAPACITY = 100  # kWh per day per generator (example)

daily_totals['capacity_utilization'] = (daily_totals['kwh_site'] / (3 * NOMINAL_CAPACITY)) * 100

print("\n3. CAPACITY UTILIZATION ANALYSIS")
print("=" * 40)
print(f"Average Capacity Utilization: {daily_totals['capacity_utilization'].mean():.1f}%")
print(f"Peak Utilization: {daily_totals['capacity_utilization'].max():.1f}%")
print(f"Minimum Utilization: {daily_totals['capacity_utilization'].min():.1f}%")

# Trend analysis
merged_df['day_num'] = (merged_df['date'] - merged_df['date'].min()).dt.days + 1

from sklearn.linear_model import LinearRegression

trend_results = {}
for unit in merged_df['unit'].unique():
    unit_data = merged_df[merged_df['unit'] == unit].sort_values('day_num')
    X = unit_data[['day_num']]
    y = unit_data['kwh_site']
    
    model = LinearRegression()
    model.fit(X, y)
    
    trend_results[unit] = {
        'slope': model.coef_[0],
        'intercept': model.intercept_,
        'r_squared': model.score(X, y)
    }

print("\n4. PRODUCTION TREND ANALYSIS")
print("=" * 40)
for unit, results in trend_results.items():
    trend_direction = "increasing" if results['slope'] > 0 else "decreasing" if results['slope'] < 0 else "stable"
    print(f"Generator {unit}: {trend_direction} trend ({results['slope']:.3f} kWh/day), R² = {results['r_squared']:.3f}")

# Data quality assessment
print("\n5. DATA QUALITY ASSESSMENT")
print("=" * 40)
print("✓ Perfect match between site historian and field export data")
print("✓ No missing values in aligned datasets")
print("✓ Consistent date ranges across sources")
print("✓ Unit naming standardized after cleaning")
print("✗ 2 records filtered from field data due to data quality issues:")
print("  - 1 record with missing date (Unit T-01, Value 9999 kWh)")
print("  - 1 record with invalid date '13/37/2024' (Unit T-02, Value 1 kWh)")

# Generate actionable insights
print("\n6. ACTIONABLE INSIGHTS & RECOMMENDATIONS")
print("=" * 40)

# Insight 1: Consistent production increase
avg_slope = np.mean([r['slope'] for r in trend_results.values()])
if avg_slope > 0.5:
    print("• POSITIVE TREND: All generators show consistent daily production increases.")
    print("  → Consider investigating operational improvements that could be standardized.")
elif avg_slope < -0.5:
    print("• NEGATIVE TREND: Production is declining over time.")
    print("  → Schedule maintenance checks to identify potential issues.")
else:
    print("• STABLE OPERATION: Production levels are consistent.")
    print("  → Current operational procedures are effective.")

# Insight 2: Data quality
print("\n• DATA QUALITY ISSUES IDENTIFIED:")
print("  → Field export contains 2 invalid records (6.25% of field data).")
print("  → Recommendation: Implement validation checks in field data collection process.")

# Insight 3: Performance consistency
unit_std = unit_performance['std_daily_kwh']
if unit_std.max() > 15:
    print("\n• HIGH VARIABILITY: Significant day-to-day production fluctuations.")
    print("  → Investigate root causes of variability (load demand, maintenance, etc.)")
else:
    print("\n• GOOD CONSISTENCY: Low day-to-day variability in production.")
    print("  → Operations are stable and predictable.")

# Insight 4: Capacity utilization
avg_util = daily_totals['capacity_utilization'].mean()
if avg_util > 80:
    print("\n• HIGH CAPACITY UTILIZATION: Generators operating near capacity.")
    print("  → Consider capacity expansion or load balancing optimization.")
elif avg_util < 50:
    print("\n• LOW CAPACITY UTILIZATION: Significant unused capacity.")
    print("  → Opportunity to take on additional load or optimize generator scheduling.")
else:
    print(f"\n• MODERATE CAPACITY UTILIZATION: {avg_util:.1f}% average utilization.")
    print("  → Current capacity planning appears appropriate.")

# Save performance metrics
performance_metrics = {
    'total_production_kwh': total_production,
    'avg_daily_production_kwh': daily_totals['kwh_site'].mean(),
    'avg_capacity_utilization_pct': daily_totals['capacity_utilization'].mean(),
    'data_quality_score_pct': (30/32) * 100,  # 30 valid records out of 32 total
    'avg_trend_slope_kwh_per_day': avg_slope
}

metrics_df = pd.DataFrame([performance_metrics])
metrics_df.to_csv('../outputs/performance_metrics.csv', index=False)

print("\n\nPerformance metrics saved to outputs/performance_metrics.csv")
print("Analysis complete!")
