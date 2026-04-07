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

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("=== TELEMETRY DATA ANALYSIS ===")
print("Loading and cleaning data...")

# Load site daily kWh data
site_df = pd.read_csv('../data/site_daily_kwh.csv')

# Load field operations export data
field_df = pd.read_csv('../data/field_ops_export.csv', encoding='utf-8-sig')

# Clean site data
site_df['record_date'] = pd.to_datetime(site_df['record_date'])
site_df['generator_unit'] = site_df['generator_unit'].str.strip()

# Clean field data
# Remove rows with missing dates
field_clean = field_df[field_df['ReadingDt'].notna()].copy()

# Convert dates, handling invalid formats
valid_dates = []
for date_str in field_clean['ReadingDt']:
    try:
        valid_dates.append(datetime.strptime(date_str, '%m/%d/%Y'))
    except ValueError:
        # Mark invalid dates as NaT
        valid_dates.append(pd.NaT)

field_clean['ReadingDt'] = valid_dates
field_clean = field_clean[field_clean['ReadingDt'].notna()].copy()

# Clean unit names to match site data format
field_clean['Unit'] = field_clean['Unit'].str.replace('-', '')

# Rename columns for consistency
site_df_clean = site_df.rename(columns={'record_date': 'date', 'generator_unit': 'unit', 'net_kwh': 'kwh'})
field_clean = field_clean.rename(columns={'ReadingDt': 'date', 'Unit': 'unit', 'Delivered_kWh': 'kwh'})

# Convert dates to date only (remove time component)
site_df_clean['date'] = pd.to_datetime(site_df_clean['date']).dt.date
field_clean['date'] = pd.to_datetime(field_clean['date']).dt.date

print(f"\nCleaned site data shape: {site_df_clean.shape}")
print(f"Cleaned field data shape: {field_clean.shape}")
print(f"\nSite data date range: {site_df_clean['date'].min()} to {site_df_clean['date'].max()}")
print(f"Field data date range: {field_clean['date'].min()} to {field_clean['date'].max()}")
print(f"\nUnique units in site data: {sorted(site_df_clean['unit'].unique())}")
print(f"Unique units in field data: {sorted(field_clean['unit'].unique())}")

# Merge datasets on date and unit
merged_df = pd.merge(site_df_clean, field_clean, 
                     on=['date', 'unit'], 
                     suffixes=('_site', '_field'),
                     how='outer')

print(f"\nMerged data shape: {merged_df.shape}")
print(f"Merged data head:\n{merged_df.head(10)}")

# Calculate difference between site and field measurements
merged_df['kwh_diff'] = merged_df['kwh_site'] - merged_df['kwh_field']
merged_df['abs_diff'] = abs(merged_df['kwh_diff'])
merged_df['diff_pct'] = (merged_df['kwh_diff'] / merged_df['kwh_site']) * 100

# Summary statistics
print("\n=== DATA QUALITY ASSESSMENT ===")
print(f"Total records in merged data: {len(merged_df)}")
print(f"Records with both site and field measurements: {merged_df[merged_df['kwh_site'].notna() & merged_df['kwh_field'].notna()].shape[0]}")
print(f"Records with only site measurement: {merged_df[merged_df['kwh_field'].isna()].shape[0]}")
print(f"Records with only field measurement: {merged_df[merged_df['kwh_site'].isna()].shape[0]}")

# Statistics for matching records
matching_records = merged_df[merged_df['kwh_site'].notna() & merged_df['kwh_field'].notna()]
print(f"\nStatistics for matching records (n={len(matching_records)}):")
print(f"Mean absolute difference: {matching_records['abs_diff'].mean():.2f} kWh")
print(f"Max absolute difference: {matching_records['abs_diff'].max():.2f} kWh")
print(f"Mean percentage difference: {matching_records['diff_pct'].mean():.2f}%")
print(f"Percentage of records with zero difference: {(matching_records['abs_diff'] == 0).sum() / len(matching_records) * 100:.1f}%")

# Save cleaned data
merged_df.to_csv('../outputs/merged_telemetry.csv', index=False)
matching_records.to_csv('../outputs/matching_records.csv', index=False)
print("\nCleaned data saved to outputs/")
