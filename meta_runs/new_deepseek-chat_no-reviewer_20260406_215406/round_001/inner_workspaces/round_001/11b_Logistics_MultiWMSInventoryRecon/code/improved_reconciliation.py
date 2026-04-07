import pandas as pd
import numpy as np
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Read the data
alpha_df = pd.read_csv('data/wms_alpha.csv')
beta_df = pd.read_csv('data/wms_beta.csv')

print("=== Initial Data ===")
print(f"Alpha WMS records: {len(alpha_df)}")
print(f"Beta WMS records: {len(beta_df)}")
print("\nAlpha column names:", list(alpha_df.columns))
print("Beta column names:", list(beta_df.columns))

# Standardize column names with better mapping
alpha_standard = alpha_df.copy()
alpha_standard.columns = ['sku', 'quantity', 'warehouse', 'timestamp']

beta_standard = beta_df.copy()
beta_standard.columns = ['sku', 'quantity', 'warehouse', 'timestamp']

# Convert timestamps to datetime
alpha_standard['timestamp'] = pd.to_datetime(alpha_standard['timestamp'])
beta_standard['timestamp'] = pd.to_datetime(beta_standard['timestamp'])

# Create warehouse mapping (assuming WH1 = Warehouse-01)
# In a real scenario, this would come from a master data reference
warehouse_mapping = {
    'WH1': 'Warehouse-01',
    'Warehouse-01': 'WH1'
}

# Apply mapping to create a standardized warehouse code
alpha_standard['warehouse_std'] = alpha_standard['warehouse'].apply(lambda x: warehouse_mapping.get(x, x))
beta_standard['warehouse_std'] = beta_standard['warehouse'].apply(lambda x: warehouse_mapping.get(x, x))

print("\n=== After Standardization with Warehouse Mapping ===")
print("Alpha WMS:")
print(alpha_standard[['sku', 'quantity', 'warehouse', 'warehouse_std', 'timestamp']])
print("\nBeta WMS:")
print(beta_standard[['sku', 'quantity', 'warehouse', 'warehouse_std', 'timestamp']])

# Convert both to UTC for comparison
alpha_standard['timestamp_utc'] = alpha_standard['timestamp'].dt.tz_convert(None)
beta_standard['timestamp_utc'] = beta_standard['timestamp'].dt.tz_localize(None)

# Extract date for grouping
alpha_standard['date'] = alpha_standard['timestamp_utc'].dt.date
beta_standard['date'] = beta_standard['timestamp_utc'].dt.date

print("\n=== Date Extraction ===")
print("Alpha dates:", alpha_standard['date'].unique())
print("Beta dates:", beta_standard['date'].unique())

# Create a combined dataset for reconciliation using standardized warehouse
combined = pd.merge(
    alpha_standard,
    beta_standard,
    on=['sku', 'warehouse_std', 'date'],
    how='outer',
    suffixes=('_alpha', '_beta')
)

print("\n=== Combined Dataset for Reconciliation (with warehouse mapping) ===")
print(combined[['sku', 'warehouse_std', 'date', 'quantity_alpha', 'quantity_beta']])

# Calculate reconciliation metrics
combined['quantity_alpha'] = combined['quantity_alpha'].fillna(0)
combined['quantity_beta'] = combined['quantity_beta'].fillna(0)
combined['quantity_diff'] = combined['quantity_alpha'] - combined['quantity_beta']
combined['abs_diff'] = abs(combined['quantity_diff'])
combined['match_status'] = np.where(
    combined['quantity_alpha'] == combined['quantity_beta'],
    'Match',
    np.where(
        combined['quantity_alpha'] == 0,
        'Missing in Alpha',
        np.where(
            combined['quantity_beta'] == 0,
            'Missing in Beta',
            'Mismatch'
        )
    )
)

print("\n=== Reconciliation Results ===")
print(combined[['sku', 'warehouse_std', 'date', 'quantity_alpha', 'quantity_beta', 'quantity_diff', 'match_status']])

# Summary statistics
print("\n=== Reconciliation Summary ===")
total_records = len(combined)
matches = (combined['match_status'] == 'Match').sum()
mismatches = (combined['match_status'] == 'Mismatch').sum()
missing_alpha = (combined['match_status'] == 'Missing in Alpha').sum()
missing_beta = (combined['match_status'] == 'Missing in Beta').sum()

print(f"Total records compared: {total_records}")
print(f"Matches: {matches} ({matches/total_records*100:.1f}%)")
print(f"Mismatches: {mismatches} ({mismatches/total_records*100:.1f}%)")
print(f"Missing in Alpha: {missing_alpha} ({missing_alpha/total_records*100:.1f}%)")
print(f"Missing in Beta: {missing_beta} ({missing_beta/total_records*100:.1f}%)")

# Calculate KPI metrics
print("\n=== Key Performance Indicators (KPIs) ===")

# 1. Data Completeness
alpha_completeness = (combined['quantity_alpha'] > 0).sum() / total_records * 100
beta_completeness = (combined['quantity_beta'] > 0).sum() / total_records * 100
print(f"1. Data Completeness:")
print(f"   Alpha WMS: {alpha_completeness:.1f}%")
print(f"   Beta WMS: {beta_completeness:.1f}%")

# 2. Data Accuracy (when both have data)
both_have_data = combined[(combined['quantity_alpha'] > 0) & (combined['quantity_beta'] > 0)]
if len(both_have_data) > 0:
    accuracy = (both_have_data['match_status'] == 'Match').sum() / len(both_have_data) * 100
    avg_abs_diff = both_have_data['abs_diff'].mean()
    max_abs_diff = both_have_data['abs_diff'].max()
    print(f"2. Data Accuracy (when both systems have data):")
    print(f"   Match Rate: {accuracy:.1f}%")
    print(f"   Average Absolute Difference: {avg_abs_diff:.2f} units")
    print(f"   Maximum Absolute Difference: {max_abs_diff:.2f} units")
else:
    print(f"2. Data Accuracy: No overlapping records with data in both systems")

# 3. Inventory Value Metrics
total_inventory_alpha = combined['quantity_alpha'].sum()
total_inventory_beta = combined['quantity_beta'].sum()
inventory_value_diff = total_inventory_alpha - total_inventory_beta
print(f"3. Total Inventory Comparison:")
print(f"   Alpha WMS Total: {total_inventory_alpha:.0f} units")
print(f"   Beta WMS Total: {total_inventory_beta:.0f} units")
print(f"   Difference: {inventory_value_diff:.0f} units ({inventory_value_diff/total_inventory_beta*100 if total_inventory_beta > 0 else 0:.1f}%)")

# 4. Timeliness (based on latest timestamp)
latest_alpha = alpha_standard['timestamp_utc'].max()
latest_beta = beta_standard['timestamp_utc'].max()
time_diff = (latest_alpha - latest_beta).total_seconds() / 3600  # hours
print(f"4. Data Timeliness:")
print(f"   Latest Alpha update: {latest_alpha}")
print(f"   Latest Beta update: {latest_beta}")
print(f"   Time difference: {time_diff:.1f} hours")

# 5. Data Freshness (days since last update)
current_time = pd.Timestamp.now()
alpha_freshness = (current_time - latest_alpha).days
beta_freshness = (current_time - latest_beta).days
print(f"5. Data Freshness (days since last update):")
print(f"   Alpha WMS: {alpha_freshness} days")
print(f"   Beta WMS: {beta_freshness} days")

# Save detailed reconciliation results to outputs
combined.to_csv('outputs/detailed_reconciliation_results.csv', index=False)

# Create summary report
summary_report = pd.DataFrame({
    'Metric': [
        'Total Records Compared',
        'Matches',
        'Mismatches',
        'Missing in Alpha',
        'Missing in Beta',
        'Alpha Data Completeness',
        'Beta Data Completeness',
        'Total Inventory Alpha',
        'Total Inventory Beta',
        'Inventory Difference',
        'Time Difference (hours)'
    ],
    'Value': [
        total_records,
        f"{matches} ({matches/total_records*100:.1f}%)",
        f"{mismatches} ({mismatches/total_records*100:.1f}%)",
        f"{missing_alpha} ({missing_alpha/total_records*100:.1f}%)",
        f"{missing_beta} ({missing_beta/total_records*100:.1f}%)",
        f"{alpha_completeness:.1f}%",
        f"{beta_completeness:.1f}%",
        f"{total_inventory_alpha:.0f} units",
        f"{total_inventory_beta:.0f} units",
        f"{inventory_value_diff:.0f} units ({inventory_value_diff/total_inventory_beta*100 if total_inventory_beta > 0 else 0:.1f}%)",
        f"{time_diff:.1f} hours"
    ]
})

summary_report.to_csv('outputs/summary_kpis.csv', index=False)

print("\n=== Output Saved ===")
print("Detailed reconciliation results saved to: outputs/detailed_reconciliation_results.csv")
print("Summary KPIs saved to: outputs/summary_kpis.csv")

# Generate enhanced visualizations
plt.style.use('seaborn-v0_8')

# Figure 1: Enhanced Reconciliation Status
fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Left: Bar chart
match_counts = combined['match_status'].value_counts()
colors = ['#2ecc71', '#e74c3c', '#f39c12', '#3498db']
ax1.bar(match_counts.index, match_counts.values, color=colors[:len(match_counts)])
ax1.set_title('Inventory Reconciliation Status', fontsize=14, fontweight='bold')
ax1.set_xlabel('Status', fontsize=12)
ax1.set_ylabel('Count', fontsize=12)
ax1.tick_params(axis='x', rotation=45)
for i, v in enumerate(match_counts.values):
    ax1.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')

# Right: Pie chart
ax2.pie(match_counts.values, labels=match_counts.index, autopct='%1.1f%%', 
        colors=colors[:len(match_counts)], startangle=90)
ax2.set_title('Reconciliation Status Distribution', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/enhanced_reconciliation_status.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: Timeline of Data Updates
fig2, ax = plt.subplots(figsize=(12, 6))

# Plot Alpha updates
alpha_dates = alpha_standard['timestamp_utc']
alpha_counts = alpha_standard.groupby('date').size()

# Plot Beta updates
beta_dates = beta_standard['timestamp_utc']
beta_counts = beta_standard.groupby('date').size()

# Create timeline
all_dates = pd.date_range(start=min(alpha_dates.min(), beta_dates.min()),
                          end=max(alpha_dates.max(), beta_dates.max()),
                          freq='D')

alpha_timeline = pd.Series(0, index=all_dates)
beta_timeline = pd.Series(0, index=all_dates)

for date, count in alpha_counts.items():
    date_idx = pd.Timestamp(date)
    if date_idx in alpha_timeline.index:
        alpha_timeline[date_idx] = count

for date, count in beta_counts.items():
    date_idx = pd.Timestamp(date)
    if date_idx in beta_timeline.index:
        beta_timeline[date_idx] = count

width = 0.35
x = np.arange(len(all_dates))

ax.bar(x - width/2, alpha_timeline.values, width, label='Alpha WMS', color='#3498db', alpha=0.8)
ax.bar(x + width/2, beta_timeline.values, width, label='Beta WMS', color='#e74c3c', alpha=0.8)

ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Number of Records', fontsize=12)
ax.set_title('Data Update Timeline by WMS System', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([d.strftime('%Y-%m-%d') for d in all_dates], rotation=45)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/data_update_timeline.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 3: Inventory Comparison by SKU
fig3, ax = plt.subplots(figsize=(10, 6))

# Group by SKU
sku_comparison = combined.groupby('sku').agg({
    'quantity_alpha': 'sum',
    'quantity_beta': 'sum'
}).reset_index()

x = np.arange(len(sku_comparison))
width = 0.35

ax.bar(x - width/2, sku_comparison['quantity_alpha'], width, label='Alpha WMS', color='#3498db', alpha=0.8)
ax.bar(x + width/2, sku_comparison['quantity_beta'], width, label='Beta WMS', color='#e74c3c', alpha=0.8)

ax.set_xlabel('SKU', fontsize=12)
ax.set_ylabel('Total Quantity', fontsize=12)
ax.set_title('Inventory Comparison by SKU', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(sku_comparison['sku'])
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/inventory_by_sku.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n=== Enhanced Visualizations Generated ===")
print("1. enhanced_reconciliation_status.png - Bar and pie charts of reconciliation status")
print("2. data_update_timeline.png - Timeline of data updates by system")
print("3. inventory_by_sku.png - Inventory comparison by SKU")
