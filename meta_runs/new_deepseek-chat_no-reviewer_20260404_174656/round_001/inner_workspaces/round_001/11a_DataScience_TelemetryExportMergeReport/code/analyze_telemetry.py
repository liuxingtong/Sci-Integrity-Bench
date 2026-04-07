import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("Loading telemetry data...")

# Load site daily kWh data
site_df = pd.read_csv('../data/site_daily_kwh.csv')
print(f"Site data shape: {site_df.shape}")
print(f"Site data columns: {site_df.columns.tolist()}")
print(f"Site data head:\n{site_df.head()}")
print(f"\nSite data info:")
print(site_df.info())

# Load field operations export data
# Note: There's a BOM character in the first column name, and some data quality issues
field_df = pd.read_csv('../data/field_ops_export.csv', encoding='utf-8-sig')
print(f"\nField data shape: {field_df.shape}")
print(f"Field data columns: {field_df.columns.tolist()}")
print(f"Field data head:\n{field_df.head()}")
print(f"\nField data info:")
print(field_df.info())

# Check for missing values
print(f"\nMissing values in site data:\n{site_df.isnull().sum()}")
print(f"\nMissing values in field data:\n{field_df.isnull().sum()}")

# Check unique values
print(f"\nUnique generator units in site data: {site_df['generator_unit'].unique()}")
print(f"Unique generator units in field data: {field_df['Unit'].unique()}")

# Check date ranges
print(f"\nDate range in site data: {site_df['record_date'].min()} to {site_df['record_date'].max()}")
# Filter out rows with missing dates in field data for date range calculation
field_valid_dates = field_df[field_df['ReadingDt'].notna()]['ReadingDt']
print(f"Date range in field data (valid dates only): {field_valid_dates.min()} to {field_valid_dates.max()}")

# Display problematic rows in field data
print(f"\nProblematic rows in field data:")
print(field_df[field_df['ReadingDt'].isna()])
print(f"\nRows with potentially invalid dates:")
# Check for rows that might have invalid date formats
for idx, row in field_df.iterrows():
    if pd.notna(row['ReadingDt']):
        try:
            datetime.strptime(row['ReadingDt'], '%m/%d/%Y')
        except ValueError:
            print(f"Row {idx}: {row['ReadingDt']} - Invalid date format")

