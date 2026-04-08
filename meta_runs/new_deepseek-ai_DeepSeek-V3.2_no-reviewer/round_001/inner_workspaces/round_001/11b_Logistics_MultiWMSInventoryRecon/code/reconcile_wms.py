import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timezone, timedelta
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("=== WMS Inventory Reconciliation Analysis ===")
print("Loading and preprocessing data...")

# Load the data
df_alpha = pd.read_csv('../data/wms_alpha.csv')
df_beta = pd.read_csv('../data/wms_beta.csv')

print(f"\nAlpha (WMS A) records: {len(df_alpha)}")
print(f"Beta (WMS B) records: {len(df_beta)}")

# Standardize column names for easier comparison
df_alpha_std = df_alpha.copy()
df_alpha_std.columns = ['sku', 'quantity', 'warehouse', 'timestamp']

# Convert alpha timestamp to datetime (it has timezone info)
df_alpha_std['timestamp'] = pd.to_datetime(df_alpha_std['timestamp'])

# Standardize beta data
df_beta_std = df_beta.copy()
df_beta_std.columns = ['sku', 'quantity', 'warehouse', 'timestamp']

# Convert beta timestamp to datetime (assume local time, no timezone)
df_beta_std['timestamp'] = pd.to_datetime(df_beta_std['timestamp'])

# Standardize warehouse names
# Alpha uses 'WH1', Beta uses 'Warehouse-01' - likely the same warehouse
df_alpha_std['warehouse'] = df_alpha_std['warehouse'].str.upper()
df_beta_std['warehouse'] = df_beta_std['warehouse'].str.upper()

print("\n=== Data Overview ===")
print("\nAlpha (standardized):")
print(df_alpha_std)
print(f"\nDate range: {df_alpha_std['timestamp'].min()} to {df_alpha_std['timestamp'].max()}")

print("\nBeta (standardized):")
print(df_beta_std)
print(f"\nDate range: {df_beta_std['timestamp'].min()} to {df_beta_std['timestamp'].max()}")

# Check for timezone differences
print("\n=== Timezone Analysis ===")
print(f"Alpha timestamps have timezone: {'+00' in str(df_alpha['as_of_utc'].iloc[0])}")
print(f"Beta timestamps have timezone: {'+' in str(df_beta['timestamp_local'].iloc[0])}")

# Assuming Alpha is UTC and Beta is local time (maybe UTC+8 based on 08:00 time)
# Let's convert both to UTC for comparison
# Beta timestamp shows 08:00 which might be local time (e.g., UTC+8)
# For reconciliation, we need to align timestamps

# Create a combined dataset for analysis
df_alpha_std['source'] = 'WMS Alpha'
df_beta_std['source'] = 'WMS Beta'

combined = pd.concat([df_alpha_std, df_beta_std], ignore_index=True)

print("\n=== Combined Data ===")
print(combined)

# Save combined data
combined.to_csv('../outputs/combined_wms_data.csv', index=False)
print("\nSaved combined data to outputs/combined_wms_data.csv")

# Analyze discrepancies
print("\n=== Discrepancy Analysis ===")

# Group by SKU and warehouse to compare quantities
sku_analysis = combined.groupby(['sku', 'warehouse', 'source']).agg({
    'quantity': ['count', 'mean', 'min', 'max', 'std']
}).round(2)

print("\nQuantity analysis by SKU, Warehouse, and Source:")
print(sku_analysis)

# Save analysis results
with open('../outputs/sku_analysis.txt', 'w') as f:
    f.write(str(sku_analysis))

# Check for exact matches on same date
# Extract date part for comparison
df_alpha_std['date'] = df_alpha_std['timestamp'].dt.date
df_beta_std['date'] = df_beta_std['timestamp'].dt.date

print("\n=== Date-based Comparison ===")
print("Alpha dates:", df_alpha_std['date'].unique())
print("Beta dates:", df_beta_std['date'].unique())

# Find overlapping dates
alpha_dates = set(df_alpha_std['date'])
beta_dates = set(df_beta_std['date'])
overlap_dates = alpha_dates.intersection(beta_dates)
print(f"\nOverlapping dates: {overlap_dates}")

# For overlapping dates, compare quantities
if overlap_dates:
    for date in overlap_dates:
        alpha_qty = df_alpha_std[df_alpha_std['date'] == date]['quantity'].values
        beta_qty = df_beta_std[df_beta_std['date'] == date]['quantity'].values
        print(f"\nDate {date}:")
        print(f"  Alpha quantity: {alpha_qty}")
        print(f"  Beta quantity: {beta_qty}")
        if len(alpha_qty) > 0 and len(beta_qty) > 0:
            diff = alpha_qty[0] - beta_qty[0]
            print(f"  Difference (Alpha - Beta): {diff}")
            if diff == 0:
                print("  ✓ MATCH")
            else:
                print(f"  ✗ MISMATCH: {abs(diff)} units")
else:
    print("\nNo overlapping dates found for direct comparison.")
    print("Note: Beta has data for 2026-03-01 at 08:00 local time")
    print("      Alpha has data for 2026-03-01 at 00:00 UTC")
    print("      If Beta is UTC+8, these represent the same point in time!")

print("\n=== Summary Statistics ===")
total_alpha_qty = df_alpha_std['quantity'].sum()
total_beta_qty = df_beta_std['quantity'].sum()

print(f"Total quantity in Alpha: {total_alpha_qty}")
print(f"Total quantity in Beta: {total_beta_qty}")
print(f"Absolute difference: {abs(total_alpha_qty - total_beta_qty)}")
print(f"Relative difference: {abs(total_alpha_qty - total_beta_qty) / max(total_alpha_qty, total_beta_qty) * 100:.2f}%")

# Calculate KPIs for management
print("\n=== Key Performance Indicators (KPIs) ===")

# 1. Data completeness
alpha_records = len(df_alpha_std)
beta_records = len(df_beta_std)
total_expected = max(alpha_records, beta_records) * 2  # Assuming both should have same coverage
completeness_alpha = alpha_records / total_expected * 100 if total_expected > 0 else 0
completeness_beta = beta_records / total_expected * 100 if total_expected > 0 else 0

print(f"1. Data Completeness:")
print(f"   - WMS Alpha: {completeness_alpha:.1f}% ({alpha_records} records)")
print(f"   - WMS Beta: {completeness_beta:.1f}% ({beta_records} records)")

# 2. Reconciliation rate (matching records)
if overlap_dates:
    matching = 0
    total_comparable = 0
    for date in overlap_dates:
        alpha_qty = df_alpha_std[df_alpha_std['date'] == date]['quantity'].values
        beta_qty = df_beta_std[df_beta_std['date'] == date]['quantity'].values
        if len(alpha_qty) > 0 and len(beta_qty) > 0:
            total_comparable += 1
            if alpha_qty[0] == beta_qty[0]:
                matching += 1
    reconciliation_rate = matching / total_comparable * 100 if total_comparable > 0 else 0
    print(f"2. Reconciliation Rate: {reconciliation_rate:.1f}% ({matching}/{total_comparable} records match)")
else:
    print(f"2. Reconciliation Rate: Cannot calculate - no overlapping dates")

# 3. Data consistency (variance within each system)
alpha_variance = df_alpha_std['quantity'].std() if len(df_alpha_std) > 1 else 0
beta_variance = df_beta_std['quantity'].std() if len(df_beta_std) > 1 else 0

print(f"3. Data Consistency (standard deviation):")
print(f"   - WMS Alpha: {alpha_variance:.2f}")
print(f"   - WMS Beta: {beta_variance:.2f}")

# 4. Timeliness (most recent data)
most_recent_alpha = df_alpha_std['timestamp'].max()
most_recent_beta = df_beta_std['timestamp'].max()
print(f"4. Timeliness (most recent record):")
print(f"   - WMS Alpha: {most_recent_alpha}")
print(f"   - WMS Beta: {most_recent_beta}")

# Save KPIs to file
kpis = {
    'total_alpha_qty': total_alpha_qty,
    'total_beta_qty': total_beta_qty,
    'absolute_difference': abs(total_alpha_qty - total_beta_qty),
    'relative_difference_pct': abs(total_alpha_qty - total_beta_qty) / max(total_alpha_qty, total_beta_qty) * 100,
    'completeness_alpha_pct': completeness_alpha,
    'completeness_beta_pct': completeness_beta,
    'alpha_variance': alpha_variance,
    'beta_variance': beta_variance,
    'most_recent_alpha': str(most_recent_alpha),
    'most_recent_beta': str(most_recent_beta)
}

# Convert numpy types to Python native types for JSON serialization
for key, value in kpis.items():
    if hasattr(value, 'item'):  # numpy types
        kpis[key] = value.item()
    elif pd.isna(value):  # Handle NaN
        kpis[key] = None

import json
with open('../outputs/kpis.json', 'w') as f:
    json.dump(kpis, f, indent=2, default=str)

print("\nSaved KPIs to outputs/kpis.json")
