import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("Loading and cleaning telemetry data...")

# Load site historian data
site_df = pd.read_csv('data/site_daily_kwh.csv')
print(f"Site data shape: {site_df.shape}")
print(f"Site data columns: {site_df.columns.tolist()}")
print(f"Site data date range: {site_df['record_date'].min()} to {site_df['record_date'].max()}")
print(f"Unique generator units in site data: {site_df['generator_unit'].unique()}")

# Load field operations data - note the BOM and encoding issues
field_df = pd.read_csv('data/field_ops_export.csv', encoding='utf-8-sig')
print(f"\nField data shape: {field_df.shape}")
print(f"Field data columns: {field_df.columns.tolist()}")

# Clean field data
print("\nCleaning field data...")

# Remove rows with invalid dates
initial_rows = len(field_df)

# Convert ReadingDt to datetime with error handling
field_df['ReadingDt_clean'] = pd.to_datetime(field_df['ReadingDt'], errors='coerce', format='%m/%d/%Y')

# Count invalid dates
invalid_dates = field_df['ReadingDt_clean'].isna().sum()
print(f"Rows with invalid dates: {invalid_dates}")

# Filter out rows with invalid dates
field_df_clean = field_df.dropna(subset=['ReadingDt_clean']).copy()

# Standardize unit names: remove hyphen to match site data format
field_df_clean['Unit_clean'] = field_df_clean['Unit'].str.replace('-', '')

# Rename columns to match site data
field_df_clean = field_df_clean.rename(columns={
    'ReadingDt_clean': 'record_date',
    'Unit_clean': 'generator_unit',
    'Delivered_kWh': 'net_kwh'
})

# Select only needed columns
field_df_clean = field_df_clean[['record_date', 'generator_unit', 'net_kwh']]

print(f"Field data after cleaning: {len(field_df_clean)} rows (removed {initial_rows - len(field_df_clean)} invalid rows)")
print(f"Cleaned field data date range: {field_df_clean['record_date'].min()} to {field_df_clean['record_date'].max()}")
print(f"Unique generator units in cleaned field data: {field_df_clean['generator_unit'].unique()}")

# Ensure site_df record_date is datetime
site_df['record_date'] = pd.to_datetime(site_df['record_date'])

# Merge datasets on date and unit
print("\nMerging datasets...")
merged_df = pd.merge(
    site_df,
    field_df_clean,
    on=['record_date', 'generator_unit'],
    suffixes=('_site', '_field'),
    how='outer',
    indicator=True
)

print(f"Merged data shape: {merged_df.shape}")
print(f"Merge status counts:\n{merged_df['_merge'].value_counts()}")

# Create a comparison dataframe for matched records
matched_df = merged_df[merged_df['_merge'] == 'both'].copy()
print(f"\nMatched records: {len(matched_df)} rows")

# Calculate differences between site and field measurements
matched_df['kwh_diff'] = matched_df['net_kwh_site'] - matched_df['net_kwh_field']
matched_df['abs_diff'] = matched_df['kwh_diff'].abs()
matched_df['diff_pct'] = (matched_df['kwh_diff'] / matched_df['net_kwh_site'] * 100).round(2)

print(f"\nDifference statistics:")
print(f"Mean difference: {matched_df['kwh_diff'].mean():.2f} kWh")
print(f"Max absolute difference: {matched_df['abs_diff'].max():.2f} kWh")
print(f"Min difference: {matched_df['kwh_diff'].min():.2f} kWh")
print(f"Std deviation of differences: {matched_df['kwh_diff'].std():.2f} kWh")

# Check for any mismatches
mismatch_threshold = 0.1  # 0.1 kWh tolerance
significant_mismatches = matched_df[matched_df['abs_diff'] > mismatch_threshold]
print(f"\nRows with significant mismatches (> {mismatch_threshold} kWh): {len(significant_mismatches)}")

if len(significant_mismatches) > 0:
    print("Significant mismatches:")
    print(significant_mismatches[['record_date', 'generator_unit', 'net_kwh_site', 'net_kwh_field', 'kwh_diff']])

# Save cleaned and merged data
print("\nSaving cleaned data...")
site_df.to_csv('outputs/site_data_clean.csv', index=False)
field_df_clean.to_csv('outputs/field_data_clean.csv', index=False)
matched_df.to_csv('outputs/merged_matched_data.csv', index=False)
merged_df.to_csv('outputs/merged_all_data.csv', index=False)

print("Data cleaning and merging complete!")

# ============================================================================
# PERFORM STATISTICAL ANALYSIS AND CREATE VISUALIZATIONS
# ============================================================================

print("\n" + "="*60)
print("PERFORMING STATISTICAL ANALYSIS")
print("="*60)

# Calculate daily totals across all units
daily_totals = site_df.groupby('record_date')['net_kwh'].sum().reset_index()
daily_totals.columns = ['record_date', 'total_kwh']

print(f"\nDaily total generation statistics:")
print(f"Mean daily generation: {daily_totals['total_kwh'].mean():.2f} kWh")
print(f"Max daily generation: {daily_totals['total_kwh'].max():.2f} kWh")
print(f"Min daily generation: {daily_totals['total_kwh'].min():.2f} kWh")
print(f"Total quarterly generation: {daily_totals['total_kwh'].sum():.2f} kWh")
print(f"Std deviation: {daily_totals['total_kwh'].std():.2f} kWh")

# Calculate unit-level statistics
unit_stats = site_df.groupby('generator_unit')['net_kwh'].agg([
    'mean', 'std', 'min', 'max', 'sum'
]).round(2)
unit_stats = unit_stats.rename(columns={
    'mean': 'avg_kwh',
    'std': 'std_kwh',
    'min': 'min_kwh',
    'max': 'max_kwh',
    'sum': 'total_kwh'
})

print(f"\nUnit-level statistics:")
print(unit_stats)

# Calculate coefficient of variation for each unit
unit_stats['cv_pct'] = (unit_stats['std_kwh'] / unit_stats['avg_kwh'] * 100).round(2)

print(f"\nUnit performance consistency (Coefficient of Variation):")
for unit in unit_stats.index:
    cv = unit_stats.loc[unit, 'cv_pct']
    print(f"  {unit}: {cv}% (lower is more consistent)")

# Calculate overall plant efficiency metrics
# Assuming each unit has a rated capacity (for illustration)
# In real scenario, we would have actual rated capacities
rated_capacities = {'T01': 100, 'T02': 100, 'T03': 100}  # kW
hours_per_day = 24

# Calculate capacity factor for each unit
for unit in unit_stats.index:
    rated_kwh = rated_capacities.get(unit, 100) * hours_per_day
    actual_total = unit_stats.loc[unit, 'total_kwh']
    capacity_factor = (actual_total / (rated_kwh * len(daily_totals))) * 100
    unit_stats.loc[unit, 'capacity_factor_pct'] = round(capacity_factor, 2)

print(f"\nEstimated capacity factors (assuming 100kW rated capacity, 24h operation):")
for unit in unit_stats.index:
    cf = unit_stats.loc[unit, 'capacity_factor_pct']
    print(f"  {unit}: {cf}%")

# Save unit statistics
unit_stats.to_csv('outputs/unit_statistics.csv')
daily_totals.to_csv('outputs/daily_totals.csv', index=False)

# ============================================================================
# CREATE VISUALIZATIONS
# ============================================================================

print("\n" + "="*60)
print("CREATING VISUALIZATIONS")
print("="*60)

# 1. Daily generation trend
plt.figure(figsize=(12, 6))
plt.plot(daily_totals['record_date'], daily_totals['total_kwh'], 
         marker='o', linewidth=2, markersize=8)
plt.title('Daily Total Generation - Q1 2024', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Total kWh Generated', fontsize=12)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/daily_generation_trend.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Unit-wise daily generation (stacked area)
plt.figure(figsize=(12, 6))

# Pivot data for stacked area
unit_daily = site_df.pivot(index='record_date', columns='generator_unit', values='net_kwh')

# Create stacked area plot
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
unit_daily.plot(kind='area', stacked=True, alpha=0.7, figsize=(12, 6), color=colors)
plt.title('Daily Generation by Unit - Q1 2024', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('kWh Generated', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(title='Generator Unit', loc='upper left')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/unit_daily_generation_stacked.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Unit performance comparison (bar chart)
plt.figure(figsize=(10, 6))
units = unit_stats.index
x_pos = np.arange(len(units))

# Create grouped bar chart
width = 0.35
plt.bar(x_pos - width/2, unit_stats['avg_kwh'], width, label='Average Daily', color='skyblue')
plt.bar(x_pos + width/2, unit_stats['total_kwh'], width, label='Total Quarterly', color='lightcoral')

plt.xlabel('Generator Unit', fontsize=12)
plt.ylabel('kWh', fontsize=12)
plt.title('Unit Performance Comparison - Q1 2024', fontsize=16, fontweight='bold')
plt.xticks(x_pos, units)
plt.legend()
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('report/images/unit_performance_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Data validation: Site vs Field comparison (should be perfect match)
plt.figure(figsize=(10, 6))
plt.scatter(matched_df['net_kwh_site'], matched_df['net_kwh_field'], 
            alpha=0.6, s=100, color='green')

# Add perfect match line
max_val = max(matched_df['net_kwh_site'].max(), matched_df['net_kwh_field'].max())
plt.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='Perfect Match')

plt.xlabel('Site Historian (kWh)', fontsize=12)
plt.ylabel('Field Export (kWh)', fontsize=12)
plt.title('Data Validation: Site vs Field Measurements', fontsize=16, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('report/images/data_validation_scatter.png', dpi=300, bbox_inches='tight')
plt.close()

# 5. Generation distribution by unit (box plot)
plt.figure(figsize=(10, 6))
unit_data = [site_df[site_df['generator_unit'] == unit]['net_kwh'] for unit in units]
plt.boxplot(unit_data, labels=units, patch_artist=True,
            boxprops=dict(facecolor='lightblue', color='darkblue'),
            medianprops=dict(color='red', linewidth=2))
plt.xlabel('Generator Unit', fontsize=12)
plt.ylabel('Daily kWh Generated', fontsize=12)
plt.title('Daily Generation Distribution by Unit', fontsize=16, fontweight='bold')
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('report/images/unit_generation_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# 6. Weekly pattern analysis (if we had more data)
# For this dataset, we only have 10 days, but we can still look at day-of-week pattern
site_df['day_of_week'] = site_df['record_date'].dt.day_name()
site_df['day_num'] = site_df['record_date'].dt.dayofweek

weekly_pattern = site_df.groupby(['day_num', 'day_of_week'])['net_kwh'].mean().reset_index()
weekly_pattern = weekly_pattern.sort_values('day_num')

plt.figure(figsize=(10, 6))
plt.bar(weekly_pattern['day_of_week'], weekly_pattern['net_kwh'], color='steelblue')
plt.xlabel('Day of Week', fontsize=12)
plt.ylabel('Average kWh per Unit', fontsize=12)
plt.title('Average Generation by Day of Week', fontsize=16, fontweight='bold')
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('report/images/weekly_generation_pattern.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"\nVisualizations saved to report/images/")
print(f"- daily_generation_trend.png")
print(f"- unit_daily_generation_stacked.png")
print(f"- unit_performance_comparison.png")
print(f"- data_validation_scatter.png")
print(f"- unit_generation_distribution.png")
print(f"- weekly_generation_pattern.png")

print("\nAnalysis complete!")
