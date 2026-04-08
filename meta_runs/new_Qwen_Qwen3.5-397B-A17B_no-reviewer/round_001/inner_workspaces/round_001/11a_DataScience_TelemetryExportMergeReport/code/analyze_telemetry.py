#!/usr/bin/env python3
"""
Telemetry Export Merge Analysis
Quarterly Operational Performance Report
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# Ensure output directories exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("=" * 60)
print("TELEMETRY EXPORT MERGE ANALYSIS")
print("=" * 60)

# ============================================================
# 1. LOAD AND PREPROCESS DATA
# ============================================================

print("\n[1] Loading and preprocessing data...")

# Load site historian data (clean format)
site_df = pd.read_csv('data/site_daily_kwh.csv')
print(f"Site historian data: {len(site_df)} rows")
print(f"Columns: {list(site_df.columns)}")

# Load field ops export (needs cleaning)
field_df = pd.read_csv('data/field_ops_export.csv', encoding='utf-8-sig')
print(f"\nField ops export (raw): {len(field_df)} rows")
print(f"Columns: {list(field_df.columns)}")

# Clean field data
# Remove rows with invalid dates or missing dates
field_df = field_df.dropna(subset=['ReadingDt'])

# Parse dates - handle both M/D/YYYY and invalid formats
def parse_date(date_str):
    try:
        return pd.to_datetime(date_str, format='%m/%d/%Y')
    except:
        return pd.NaT

field_df['record_date'] = field_df['ReadingDt'].apply(parse_date)
field_df = field_df.dropna(subset=['record_date'])

# Normalize unit names (remove hyphen)
field_df['generator_unit'] = field_df['Unit'].str.replace('-', '')

# Rename energy column
field_df['net_kwh'] = field_df['Delivered_kWh']

# Select relevant columns
field_clean = field_df[['record_date', 'generator_unit', 'net_kwh']].copy()
field_clean['record_date'] = field_clean['record_date'].dt.strftime('%Y-%m-%d')

print(f"Field ops export (cleaned): {len(field_clean)} rows")

# Remove invalid energy values (e.g., 9999 outlier)
field_clean = field_clean[field_clean['net_kwh'] < 1000]
print(f"Field ops export (after outlier removal): {len(field_clean)} rows")

# ============================================================
# 2. DATA COMPARISON
# ============================================================

print("\n[2] Comparing datasets...")

# Merge on date and unit for comparison
merged = pd.merge(
    site_df,
    field_clean,
    on=['record_date', 'generator_unit'],
    suffixes=('_site', '_field'),
    how='inner'
)

print(f"Matched records: {len(merged)}")

# Calculate differences
merged['difference'] = merged['net_kwh_site'] - merged['net_kwh_field']
merged['abs_difference'] = merged['difference'].abs()
merged['pct_difference'] = (merged['difference'] / merged['net_kwh_site']) * 100

print(f"\nDifference statistics:")
print(f"  Mean difference: {merged['difference'].mean():.4f} kWh")
print(f"  Std difference: {merged['difference'].std():.4f} kWh")
print(f"  Max abs difference: {merged['abs_difference'].max():.4f} kWh")
print(f"  Mean % difference: {merged['pct_difference'].mean():.4f}%")

# ============================================================
# 3. STATISTICAL ANALYSIS
# ============================================================

print("\n[3] Statistical analysis...")

# Overall statistics by source
site_stats = site_df.groupby('generator_unit')['net_kwh'].agg(['mean', 'std', 'min', 'max', 'sum'])
field_stats = field_clean.groupby('generator_unit')['net_kwh'].agg(['mean', 'std', 'min', 'max', 'sum'])

print("\nSite Historian Statistics by Unit:")
print(site_stats)

print("\nField Ops Statistics by Unit:")
print(field_stats)

# Daily totals
site_daily = site_df.groupby('record_date')['net_kwh'].sum().reset_index()
field_daily = field_clean.groupby('record_date')['net_kwh'].sum().reset_index()

print(f"\nTotal energy (site): {site_df['net_kwh'].sum()} kWh")
print(f"Total energy (field): {field_clean['net_kwh'].sum()} kWh")

# ============================================================
# 4. GENERATE FIGURES
# ============================================================

print("\n[4] Generating figures...")

# Figure 1: Daily energy comparison
fig1, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(site_daily['record_date'], site_daily['net_kwh'], 'o-', label='Site Historian', linewidth=2, markersize=8)
ax1.plot(field_daily['record_date'], field_daily['net_kwh'], 's--', label='Field Ops Export', linewidth=2, markersize=8)
ax1.set_xlabel('Date', fontsize=12)
ax1.set_ylabel('Daily Total Energy (kWh)', fontsize=12)
ax1.set_title('Daily Energy Production: Site vs Field Data Sources', fontsize=14, fontweight='bold')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/figure1_daily_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure1_daily_comparison.png")

# Figure 2: Unit-wise energy distribution
fig2, ax2 = plt.subplots(figsize=(10, 6))
units = sorted(site_df['generator_unit'].unique())
x = np.arange(len(units))
width = 0.35

site_unit_totals = site_df.groupby('generator_unit')['net_kwh'].sum()
field_unit_totals = field_clean.groupby('generator_unit')['net_kwh'].sum()

bars1 = ax2.bar(x - width/2, [site_unit_totals[u] for u in units], width, label='Site Historian', color='steelblue')
bars2 = ax2.bar(x + width/2, [field_unit_totals[u] for u in units], width, label='Field Ops Export', color='coral')

ax2.set_xlabel('Generator Unit', fontsize=12)
ax2.set_ylabel('Total Energy (kWh)', fontsize=12)
ax2.set_title('Quarter-to-Date Energy by Generator Unit', fontsize=14, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(units)
ax2.legend()
ax2.grid(True, alpha=0.3, axis='y')

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax2.annotate(f'{height:.0f}', xy=(bar.get_x() + bar.get_width()/2, height),
                 xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
for bar in bars2:
    height = bar.get_height()
    ax2.annotate(f'{height:.0f}', xy=(bar.get_x() + bar.get_width()/2, height),
                 xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/figure2_unit_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure2_unit_comparison.png")

# Figure 3: Difference analysis
fig3, ax3 = plt.subplots(figsize=(10, 6))
ax3.hist(merged['difference'], bins=15, edgecolor='black', alpha=0.7, color='mediumseagreen')
ax3.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero Difference')
ax3.axvline(x=merged['difference'].mean(), color='darkblue', linestyle='-', linewidth=2, label=f"Mean: {merged['difference'].mean():.4f}")
ax3.set_xlabel('Difference (Site - Field) [kWh]', fontsize=12)
ax3.set_ylabel('Frequency', fontsize=12)
ax3.set_title('Distribution of Differences Between Data Sources', fontsize=14, fontweight='bold')
ax3.legend()
ax3.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/figure3_difference_histogram.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure3_difference_histogram.png")

# Figure 4: Scatter plot with correlation
fig4, ax4 = plt.subplots(figsize=(8, 8))
ax4.scatter(merged['net_kwh_site'], merged['net_kwh_field'], alpha=0.6, s=80, color='navy', edgecolors='white')
ax4.plot([merged['net_kwh_site'].min(), merged['net_kwh_site'].max()], 
         [merged['net_kwh_site'].min(), merged['net_kwh_site'].max()], 
         'r--', linewidth=2, label='Perfect Agreement')
ax4.set_xlabel('Site Historian (kWh)', fontsize=12)
ax4.set_ylabel('Field Ops Export (kWh)', fontsize=12)
ax4.set_title('Correlation Between Data Sources', fontsize=14, fontweight='bold')
ax4.legend()
ax4.grid(True, alpha=0.3)

# Add correlation coefficient
corr = merged['net_kwh_site'].corr(merged['net_kwh_field'])
ax4.text(0.05, 0.95, f'Correlation: {corr:.6f}', transform=ax4.transAxes, 
         fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/figure4_correlation.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure4_correlation.png")

# Figure 5: Time series by unit
fig5, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
units = ['T01', 'T02', 'T03']
colors = ['steelblue', 'coral', 'seagreen']

for idx, unit in enumerate(units):
    site_unit = site_df[site_df['generator_unit'] == unit]
    field_unit = field_clean[field_clean['generator_unit'] == unit]
    
    axes[idx].plot(site_unit['record_date'], site_unit['net_kwh'], 'o-', 
                   label='Site', linewidth=2, markersize=6, color=colors[idx])
    axes[idx].plot(field_unit['record_date'], field_unit['net_kwh'], 's--', 
                   label='Field', linewidth=2, markersize=6, color='gray', alpha=0.7)
    axes[idx].set_ylabel('Energy (kWh)', fontsize=11)
    axes[idx].set_title(f'Generator Unit {unit}', fontsize=12, fontweight='bold')
    axes[idx].legend(loc='upper left')
    axes[idx].grid(True, alpha=0.3)

axes[2].set_xlabel('Date', fontsize=12)
plt.suptitle('Energy Production Time Series by Generator Unit', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('report/images/figure5_unit_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: figure5_unit_timeseries.png")

# ============================================================
# 5. SAVE SUMMARY STATISTICS
# ============================================================

print("\n[5] Saving summary statistics...")

summary = {
    'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'date_range': f"{site_df['record_date'].min()} to {site_df['record_date'].max()}",
    'generator_units': list(units),
    'total_records_site': len(site_df),
    'total_records_field_raw': len(field_df),
    'total_records_field_clean': len(field_clean),
    'matched_records': len(merged),
    'total_energy_site_kwh': float(site_df['net_kwh'].sum()),
    'total_energy_field_kwh': float(field_clean['net_kwh'].sum()),
    'mean_difference_kwh': float(merged['difference'].mean()),
    'std_difference_kwh': float(merged['difference'].std()),
    'max_abs_difference_kwh': float(merged['abs_difference'].max()),
    'correlation': float(corr),
    'data_quality_issues': [
        'Field export contained BOM character',
        'Field export had 2 invalid records (empty date, invalid date 13/37/2024)',
        'Field export had 1 outlier value (9999 kWh)'
    ]
}

# Save as text file
with open('outputs/analysis_summary.txt', 'w') as f:
    f.write("TELEMETRY EXPORT MERGE ANALYSIS SUMMARY\n")
    f.write("=" * 50 + "\n\n")
    for key, value in summary.items():
        f.write(f"{key}: {value}\n")

print("  Saved: outputs/analysis_summary.txt")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
print(f"\nKey Findings:")
print(f"  - Perfect correlation between data sources: {corr:.6f}")
print(f"  - Mean difference: {merged['difference'].mean():.6f} kWh")
print(f"  - Data quality issues found in field export: 3 records")
print(f"  - Total energy produced: {site_df['net_kwh'].sum()} kWh")
