"""
Telemetry Export Merge Analysis
Q1 2024 Generator Performance Report
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
print("Loading telemetry data...")

# Site historian data
site_df = pd.read_csv('data/site_daily_kwh.csv')
site_df['record_date'] = pd.to_datetime(site_df['record_date'])
site_df['source'] = 'Site Historian'
site_df.rename(columns={'net_kwh': 'kwh'}, inplace=True)

# Field ops export data
field_df = pd.read_csv('data/field_ops_export.csv')

# Clean field data - handle malformed entries
field_df_clean = field_df.copy()

# Remove rows with empty dates or invalid dates
field_df_clean = field_df_clean[field_df_clean['ReadingDt'].notna()]
field_df_clean = field_df_clean[field_df_clean['ReadingDt'] != '']

# Parse dates, handling errors
field_df_clean['ReadingDt'] = pd.to_datetime(field_df_clean['ReadingDt'], errors='coerce')
field_df_clean = field_df_clean[field_df_clean['ReadingDt'].notna()]

# Clean unit names (remove hyphens for consistency)
field_df_clean['Unit'] = field_df_clean['Unit'].str.replace('-', '')
field_df_clean.rename(columns={'ReadingDt': 'record_date', 'Unit': 'generator_unit', 'Delivered_kWh': 'kwh'}, inplace=True)
field_df_clean['source'] = 'Field Export'

print(f"Site historian records: {len(site_df)}")
print(f"Field export records (cleaned): {len(field_df_clean)}")

# Data quality assessment
print("\n=== DATA QUALITY ASSESSMENT ===")
print(f"Site data date range: {site_df['record_date'].min()} to {site_df['record_date'].max()}")
print(f"Field data date range: {field_df_clean['record_date'].min()} to {field_df_clean['record_date'].max()}")

# Check for duplicates and anomalies
print(f"\nSite data duplicates: {site_df.duplicated(subset=['record_date', 'generator_unit']).sum()}")
print(f"Field data duplicates: {field_df_clean.duplicated(subset=['record_date', 'generator_unit']).sum()}")

# Merge datasets for comparison
merged = pd.merge(
    site_df, 
    field_df_clean, 
    on=['record_date', 'generator_unit'], 
    suffixes=('_site', '_field'),
    how='outer',
    indicator=True
)

print(f"\nMerge summary:")
print(merged['_merge'].value_counts())

# Calculate differences where both sources exist
both_sources = merged[merged['_merge'] == 'both'].copy()
both_sources['kwh_diff'] = both_sources['kwh_site'] - both_sources['kwh_field']
both_sources['pct_diff'] = (both_sources['kwh_diff'] / both_sources['kwh_site']) * 100

print(f"\nRecords with both sources: {len(both_sources)}")
print(f"KWh difference statistics:")
print(both_sources['kwh_diff'].describe())

# Statistical Analysis
print("\n=== STATISTICAL ANALYSIS ===")

# Combined dataset for full analysis
combined = pd.concat([site_df, field_df_clean], ignore_index=True)
combined = combined.drop_duplicates(subset=['record_date', 'generator_unit'], keep='first')

print(f"\nCombined dataset: {len(combined)} records")
print(f"Date range: {combined['record_date'].min()} to {combined['record_date'].max()}")
print(f"Generator units: {combined['generator_unit'].unique()}")

# Daily totals
daily_totals = combined.groupby('record_date')['kwh'].sum().reset_index()
daily_totals['day_of_year'] = daily_totals['record_date'].dt.dayofyear

# Unit-level statistics
unit_stats = combined.groupby('generator_unit')['kwh'].agg([
    'count', 'mean', 'std', 'min', 'max', 'sum'
]).round(2)
unit_stats['capacity_factor'] = (unit_stats['mean'] / unit_stats['max'] * 100).round(2)

print("\nUnit-level statistics:")
print(unit_stats)

# Trend analysis
from scipy import stats
slope, intercept, r_value, p_value, std_err = stats.linregress(
    daily_totals['day_of_year'], daily_totals['kwh']
)

print(f"\nDaily total trend analysis:")
print(f"Slope: {slope:.4f} kWh/day")
print(f"R-squared: {r_value**2:.4f}")
print(f"P-value: {p_value:.4f}")

# Generate visualizations
print("\n=== GENERATING FIGURES ===")

# Figure 1: Daily Generation Trend
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(daily_totals['record_date'], daily_totals['kwh'], 
        marker='o', linewidth=2, markersize=6, color='#2E86AB')
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Total Daily Generation (kWh)', fontsize=12)
ax.set_title('Q1 2024 Daily Generation Trend', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

# Add trend line
trend_line = slope * daily_totals['day_of_year'] + intercept
ax.plot(daily_totals['record_date'], trend_line, '--', color='#E94F37', 
        linewidth=2, label=f'Trend (slope={slope:.2f} kWh/day)')
ax.legend()
plt.tight_layout()
plt.savefig('report/images/figure1_daily_trend.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: figure1_daily_trend.png")

# Figure 2: Unit Comparison
fig, ax = plt.subplots(figsize=(10, 6))
unit_daily = combined.pivot(index='record_date', columns='generator_unit', values='kwh')
unit_daily.plot(kind='bar', ax=ax, width=0.8)
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Net Generation (kWh)', fontsize=12)
ax.set_title('Daily Generation by Unit', fontsize=14, fontweight='bold')
ax.legend(title='Generator Unit', loc='upper left')
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
plt.savefig('report/images/figure2_unit_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: figure2_unit_comparison.png")

# Figure 3: Source Comparison (Data Validation)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Scatter plot comparison
if len(both_sources) > 0:
    axes[0].scatter(both_sources['kwh_site'], both_sources['kwh_field'], 
                   alpha=0.7, s=80, color='#2E86AB')
    max_val = max(both_sources['kwh_site'].max(), both_sources['kwh_field'].max())
    axes[0].plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Perfect Match')
    axes[0].set_xlabel('Site Historian (kWh)', fontsize=12)
    axes[0].set_ylabel('Field Export (kWh)', fontsize=12)
    axes[0].set_title('Data Source Validation', fontsize=14, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

# Difference distribution
if len(both_sources) > 0:
    axes[1].hist(both_sources['kwh_diff'], bins=10, color='#6A994E', edgecolor='black', alpha=0.7)
    axes[1].axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero Difference')
    axes[1].set_xlabel('Difference (Site - Field) kWh', fontsize=12)
    axes[1].set_ylabel('Frequency', fontsize=12)
    axes[1].set_title('Distribution of Measurement Differences', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure3_source_validation.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: figure3_source_validation.png")

# Figure 4: Performance Metrics Summary
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Unit totals
unit_totals = combined.groupby('generator_unit')['kwh'].sum()
axes[0, 0].bar(unit_totals.index, unit_totals.values, color=['#2E86AB', '#A23B72', '#F18F01'])
axes[0, 0].set_ylabel('Total Generation (kWh)', fontsize=11)
axes[0, 0].set_title('Total Generation by Unit (Q1)', fontsize=12, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3, axis='y')

# Daily average by unit
unit_avg = combined.groupby('generator_unit')['kwh'].mean()
axes[0, 1].bar(unit_avg.index, unit_avg.values, color=['#2E86AB', '#A23B72', '#F18F01'])
axes[0, 1].set_ylabel('Average Daily Generation (kWh)', fontsize=11)
axes[0, 1].set_title('Average Daily Generation by Unit', fontsize=12, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3, axis='y')

# Generation distribution
axes[1, 0].boxplot([combined[combined['generator_unit']==unit]['kwh'].values 
                    for unit in combined['generator_unit'].unique()],
                   labels=combined['generator_unit'].unique())
axes[1, 0].set_ylabel('Daily Generation (kWh)', fontsize=11)
axes[1, 0].set_title('Generation Distribution by Unit', fontsize=12, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Cumulative generation
combined_sorted = combined.sort_values('record_date')
cumulative = combined_sorted.groupby('record_date')['kwh'].sum().cumsum()
axes[1, 1].plot(cumulative.index, cumulative.values, marker='o', linewidth=2, color='#2E86AB')
axes[1, 1].set_ylabel('Cumulative Generation (kWh)', fontsize=11)
axes[1, 1].set_title('Cumulative Generation Trend', fontsize=12, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('report/images/figure4_performance_summary.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: figure4_performance_summary.png")

# Save analysis results
results = {
    'total_generation_kwh': combined['kwh'].sum(),
    'daily_average_kwh': daily_totals['kwh'].mean(),
    'daily_std_kwh': daily_totals['kwh'].std(),
    'trend_slope_kwh_per_day': slope,
    'trend_r_squared': r_value**2,
    'data_quality_match_pct': (len(both_sources) / len(site_df)) * 100,
    'unit_stats': unit_stats.to_dict(),
    'date_range': f"{combined['record_date'].min().strftime('%Y-%m-%d')} to {combined['record_date'].max().strftime('%Y-%m-%d')}"
}

# Save to CSV for reference
daily_totals.to_csv('outputs/daily_totals.csv', index=False)
unit_stats.to_csv('outputs/unit_statistics.csv')
both_sources.to_csv('outputs/source_comparison.csv', index=False)

print("\n=== ANALYSIS COMPLETE ===")
print(f"Total Q1 Generation: {results['total_generation_kwh']:.0f} kWh")
print(f"Daily Average: {results['daily_average_kwh']:.1f} ± {results['daily_std_kwh']:.1f} kWh")
print(f"Data Quality: {results['data_quality_match_pct']:.1f}% match between sources")
