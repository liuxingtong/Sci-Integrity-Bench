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

print("Loading data...")

# Load site historian data
site_df = pd.read_csv('data/site_daily_kwh.csv')
print(f"Site data shape: {site_df.shape}")
print(f"Site data columns: {site_df.columns.tolist()}")
print(f"Site data head:\n{site_df.head()}")
print(f"\nSite data info:")
print(site_df.info())

# Load field ops data - note the BOM character and encoding issues
# First, let's read it with proper encoding
with open('data/field_ops_export.csv', 'r', encoding='utf-8-sig') as f:
    field_df = pd.read_csv(f)

print(f"\nField data shape: {field_df.shape}")
print(f"Field data columns: {field_df.columns.tolist()}")
print(f"Field data head:\n{field_df.head()}")
print(f"\nField data info:")
print(field_df.info())

# Check for problematic rows
print(f"\nField data tail:\n{field_df.tail()}")

# Check unique values in date column
print(f"\nUnique dates in field data: {field_df['ReadingDt'].unique()[:20]}")
print(f"Number of unique dates: {field_df['ReadingDt'].nunique()}")

# Check unique units
print(f"\nUnique units in site data: {site_df['generator_unit'].unique()}")
print(f"Unique units in field data: {field_df['Unit'].unique()}")

# Data cleaning
print("\n" + "="*80)
print("DATA CLEANING")
print("="*80)

# Clean site data
site_df_clean = site_df.copy()
site_df_clean['record_date'] = pd.to_datetime(site_df_clean['record_date'])
print(f"Site data date range: {site_df_clean['record_date'].min()} to {site_df_clean['record_date'].max()}")

# Clean field data
field_df_clean = field_df.copy()

# Remove rows with invalid dates
print(f"\nRemoving invalid rows from field data...")
print(f"Rows before cleaning: {len(field_df_clean)}")

# Remove rows with NaN dates
field_df_clean = field_df_clean.dropna(subset=['ReadingDt'])

# Remove rows with invalid date format (like '13/37/2024')
# We'll try to convert to datetime and keep only valid conversions
def try_parse_date(date_str):
    try:
        return pd.to_datetime(date_str, format='%m/%d/%Y')
    except:
        return pd.NaT

field_df_clean['ReadingDt_parsed'] = field_df_clean['ReadingDt'].apply(try_parse_date)
field_df_clean = field_df_clean.dropna(subset=['ReadingDt_parsed'])
field_df_clean['ReadingDt'] = field_df_clean['ReadingDt_parsed']
field_df_clean = field_df_clean.drop(columns=['ReadingDt_parsed'])

print(f"Rows after cleaning: {len(field_df_clean)}")
print(f"Field data date range: {field_df_clean['ReadingDt'].min()} to {field_df_clean['ReadingDt'].max()}")

# Standardize unit names in field data (remove hyphen)
field_df_clean['Unit'] = field_df_clean['Unit'].str.replace('-', '')
print(f"\nField data units after standardization: {field_df_clean['Unit'].unique()}")

# Rename columns for consistency
site_df_clean = site_df_clean.rename(columns={
    'record_date': 'date',
    'generator_unit': 'unit',
    'net_kwh': 'kwh'
})

field_df_clean = field_df_clean.rename(columns={
    'ReadingDt': 'date',
    'Unit': 'unit',
    'Delivered_kWh': 'kwh'
})

print(f"\nSite data columns after renaming: {site_df_clean.columns.tolist()}")
print(f"Field data columns after renaming: {field_df_clean.columns.tolist()}")

# Check for duplicates
print(f"\nChecking for duplicates...")
site_duplicates = site_df_clean.duplicated(subset=['date', 'unit']).sum()
field_duplicates = field_df_clean.duplicated(subset=['date', 'unit']).sum()
print(f"Duplicate rows in site data: {site_duplicates}")
print(f"Duplicate rows in field data: {field_duplicates}")

# Merge the datasets
print("\n" + "="*80)
print("DATA MERGING")
print("="*80)

# Merge on date and unit
merged_df = pd.merge(
    site_df_clean,
    field_df_clean,
    on=['date', 'unit'],
    suffixes=('_site', '_field'),
    how='outer',
    indicator=True
)

print(f"Merged data shape: {merged_df.shape}")
print(f"\nMerge indicator counts:")
print(merged_df['_merge'].value_counts())

# Create a comparison dataframe for matched records
matched_df = merged_df[merged_df['_merge'] == 'both'].copy()
print(f"\nMatched records: {len(matched_df)}")

# Calculate difference between site and field measurements
matched_df['kwh_diff'] = matched_df['kwh_site'] - matched_df['kwh_field']
matched_df['abs_diff'] = matched_df['kwh_diff'].abs()
matched_df['diff_pct'] = (matched_df['kwh_diff'] / matched_df['kwh_site']) * 100

print(f"\nDifference statistics:")
print(f"Mean absolute difference: {matched_df['abs_diff'].mean():.2f} kWh")
print(f"Max absolute difference: {matched_df['abs_diff'].max():.2f} kWh")
print(f"Mean percentage difference: {matched_df['diff_pct'].mean():.2f}%")
print(f"Max percentage difference: {matched_df['diff_pct'].max():.2f}%")

# Save cleaned data
site_df_clean.to_csv('outputs/site_data_clean.csv', index=False)
field_df_clean.to_csv('outputs/field_data_clean.csv', index=False)
matched_df.to_csv('outputs/matched_data.csv', index=False)
merged_df.to_csv('outputs/merged_data.csv', index=False)

print("\nCleaned data saved to outputs/ directory.")

# Additional analysis
print("\n" + "="*80)
print("ADDITIONAL ANALYSIS")
print("="*80)

# Check the pattern in the data
print("\nAnalyzing data patterns...")

# Sort by date and unit for better analysis
matched_df_sorted = matched_df.sort_values(['date', 'unit'])

# Calculate daily totals
daily_totals = matched_df_sorted.groupby('date').agg({
    'kwh_site': 'sum',
    'kwh_field': 'sum'
}).reset_index()

daily_totals['total_kwh'] = daily_totals['kwh_site']  # Same as kwh_field
print(f"\nDaily totals:\n{daily_totals}")

# Calculate unit-wise totals
unit_totals = matched_df_sorted.groupby('unit').agg({
    'kwh_site': 'sum',
    'kwh_field': 'sum'
}).reset_index()

unit_totals['total_kwh'] = unit_totals['kwh_site']
print(f"\nUnit-wise totals:\n{unit_totals}")

# Calculate statistics
print(f"\nOverall statistics:")
print(f"Total generation (all units, all days): {daily_totals['total_kwh'].sum():.0f} kWh")
print(f"Average daily generation: {daily_totals['total_kwh'].mean():.2f} kWh")
print(f"Minimum daily generation: {daily_totals['total_kwh'].min():.2f} kWh")
print(f"Maximum daily generation: {daily_totals['total_kwh'].max():.2f} kWh")
print(f"Standard deviation of daily generation: {daily_totals['total_kwh'].std():.2f} kWh")

# Check for trends
matched_df_sorted['day_num'] = (matched_df_sorted['date'] - matched_df_sorted['date'].min()).dt.days + 1

# Calculate correlation between day number and generation
correlation_by_unit = {}
for unit in matched_df_sorted['unit'].unique():
    unit_data = matched_df_sorted[matched_df_sorted['unit'] == unit]
    corr = unit_data['day_num'].corr(unit_data['kwh_site'])
    correlation_by_unit[unit] = corr
    print(f"Correlation (day vs kwh) for {unit}: {corr:.4f}")

# Create visualizations
print("\n" + "="*80)
print("CREATING VISUALIZATIONS")
print("="*80)

# 1. Daily generation trend
plt.figure(figsize=(12, 6))
for unit in matched_df_sorted['unit'].unique():
    unit_data = matched_df_sorted[matched_df_sorted['unit'] == unit]
    plt.plot(unit_data['date'], unit_data['kwh_site'], marker='o', label=f'{unit}')

plt.title('Daily Generation by Unit (Jan 1-10, 2024)', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Generation (kWh)', fontsize=12)
plt.legend(title='Generator Unit')
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('report/images/daily_generation_by_unit.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/daily_generation_by_unit.png")

# 2. Daily total generation
plt.figure(figsize=(10, 6))
plt.bar(daily_totals['date'].dt.strftime('%m/%d'), daily_totals['total_kwh'], 
        color='steelblue', edgecolor='black')
plt.title('Total Daily Generation (All Units)', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Total Generation (kWh)', fontsize=12)
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('report/images/daily_total_generation.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/daily_total_generation.png")

# 3. Unit contribution pie chart
plt.figure(figsize=(8, 8))
plt.pie(unit_totals['total_kwh'], labels=unit_totals['unit'], 
        autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99'])
plt.title('Total Generation by Unit (Jan 1-10, 2024)', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/unit_contribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/unit_contribution.png")

# 4. Data validation scatter plot (site vs field)
plt.figure(figsize=(8, 8))
plt.scatter(matched_df_sorted['kwh_site'], matched_df_sorted['kwh_field'], 
            alpha=0.6, color='green')
# Add perfect correlation line
max_val = max(matched_df_sorted['kwh_site'].max(), matched_df_sorted['kwh_field'].max())
plt.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='Perfect match')
plt.title('Data Validation: Site vs Field Measurements', fontsize=16, fontweight='bold')
plt.xlabel('Site Historian (kWh)', fontsize=12)
plt.ylabel('Field Operations (kWh)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/data_validation_scatter.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/data_validation_scatter.png")

# 5. Generation trend over time
plt.figure(figsize=(12, 6))
for unit in matched_df_sorted['unit'].unique():
    unit_data = matched_df_sorted[matched_df_sorted['unit'] == unit]
    plt.plot(unit_data['day_num'], unit_data['kwh_site'], marker='s', 
             linewidth=2, markersize=8, label=f'{unit}')

plt.title('Generation Trend Over Time (Day 1-10)', fontsize=16, fontweight='bold')
plt.xlabel('Day Number', fontsize=12)
plt.ylabel('Generation (kWh)', fontsize=12)
plt.legend(title='Generator Unit')
plt.grid(True, alpha=0.3)
plt.xticks(range(1, 11))
plt.tight_layout()
plt.savefig('report/images/generation_trend.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/generation_trend.png")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
