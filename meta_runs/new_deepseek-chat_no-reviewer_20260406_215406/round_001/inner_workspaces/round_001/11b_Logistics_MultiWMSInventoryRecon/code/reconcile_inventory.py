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

# Standardize column names
alpha_standard = alpha_df.copy()
alpha_standard.columns = ['sku', 'quantity', 'warehouse', 'timestamp']

beta_standard = beta_df.copy()
beta_standard.columns = ['sku', 'quantity', 'warehouse', 'timestamp']

# Convert timestamps to datetime
alpha_standard['timestamp'] = pd.to_datetime(alpha_standard['timestamp'])
beta_standard['timestamp'] = pd.to_datetime(beta_standard['timestamp'])

print("\n=== After Standardization ===")
print("Alpha WMS:")
print(alpha_standard)
print("\nBeta WMS:")
print(beta_standard)

# Check if timestamps are in same timezone
print("\n=== Timezone Analysis ===")
print(f"Alpha timestamp timezone info: {alpha_standard['timestamp'].dt.tz}")
print(f"Beta timestamp timezone info: {beta_standard['timestamp'].dt.tz}")

# Convert both to UTC for comparison
alpha_standard['timestamp_utc'] = alpha_standard['timestamp'].dt.tz_convert(None)  # Already UTC
beta_standard['timestamp_utc'] = beta_standard['timestamp'].dt.tz_localize(None)  # Assume local is same as UTC for comparison

# Extract date for grouping
alpha_standard['date'] = alpha_standard['timestamp_utc'].dt.date
beta_standard['date'] = beta_standard['timestamp_utc'].dt.date

print("\n=== Date Extraction ===")
print("Alpha dates:", alpha_standard['date'].unique())
print("Beta dates:", beta_standard['date'].unique())

# Create a combined dataset for reconciliation
# We'll join on sku, warehouse, and date
combined = pd.merge(
    alpha_standard,
    beta_standard,
    on=['sku', 'warehouse', 'date'],
    how='outer',
    suffixes=('_alpha', '_beta')
)

print("\n=== Combined Dataset for Reconciliation ===")
print(combined)

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
print(combined[['sku', 'warehouse', 'date', 'quantity_alpha', 'quantity_beta', 'quantity_diff', 'match_status']])

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

# 3. Inventory Value Metrics (assuming all items have equal value for simplicity)
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

# Save reconciliation results to outputs
combined.to_csv('outputs/reconciliation_results.csv', index=False)
print("\n=== Output Saved ===")
print("Reconciliation results saved to: outputs/reconciliation_results.csv")

# Generate visualizations
plt.style.use('seaborn-v0_8')

# Figure 1: Reconciliation Status
fig1, ax1 = plt.subplots(figsize=(10, 6))
match_counts = combined['match_status'].value_counts()
colors = ['#2ecc71', '#e74c3c', '#f39c12', '#3498db']
ax1.bar(match_counts.index, match_counts.values, color=colors[:len(match_counts)])
ax1.set_title('Inventory Reconciliation Status', fontsize=16, fontweight='bold')
ax1.set_xlabel('Status', fontsize=12)
ax1.set_ylabel('Count', fontsize=12)
ax1.tick_params(axis='x', rotation=45)
for i, v in enumerate(match_counts.values):
    ax1.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/reconciliation_status.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: Quantity Comparison
fig2, ax2 = plt.subplots(figsize=(12, 8))

# Prepare data for scatter plot
plot_data = combined.copy()
plot_data = plot_data[plot_data['quantity_alpha'] > 0]
plot_data = plot_data[plot_data['quantity_beta'] > 0]

if len(plot_data) > 0:
    ax2.scatter(plot_data['quantity_alpha'], plot_data['quantity_beta'], 
                alpha=0.7, s=100, edgecolors='black')
    
    # Add perfect match line
    max_val = max(plot_data[['quantity_alpha', 'quantity_beta']].max().max(), 1)
    ax2.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='Perfect Match')
    
    ax2.set_title('Quantity Comparison: Alpha vs Beta WMS', fontsize=16, fontweight='bold')
    ax2.set_xlabel('Alpha WMS Quantity', fontsize=12)
    ax2.set_ylabel('Beta WMS Quantity', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
else:
    ax2.text(0.5, 0.5, 'No overlapping records with\nquantities in both systems', 
             ha='center', va='center', fontsize=14, transform=ax2.transAxes)
    ax2.set_title('Quantity Comparison: Alpha vs Beta WMS', fontsize=16, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/quantity_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 3: Inventory Totals Comparison
fig3, ax3 = plt.subplots(figsize=(8, 6))
systems = ['Alpha WMS', 'Beta WMS']
totals = [total_inventory_alpha, total_inventory_beta]
colors = ['#3498db', '#e74c3c']

bars = ax3.bar(systems, totals, color=colors, alpha=0.8)
ax3.set_title('Total Inventory by WMS System', fontsize=16, fontweight='bold')
ax3.set_ylabel('Total Quantity (units)', fontsize=12)

# Add value labels on bars
for bar, total in zip(bars, totals):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
             f'{total:.0f}', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/total_inventory_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n=== Visualizations Generated ===")
print("1. reconciliation_status.png - Reconciliation status breakdown")
print("2. quantity_comparison.png - Scatter plot of quantity comparisons")
print("3. total_inventory_comparison.png - Bar chart of total inventory")
