"""
Multi-WMS Inventory Reconciliation Analysis
============================================
This script reconciles inventory data from two WMS exports (Alpha and Beta)
and generates KPIs and visualizations for management reporting.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("=" * 60)
print("MULTI-WMS INVENTORY RECONCILIATION")
print("=" * 60)

# =============================================================================
# 1. LOAD AND EXPLORE DATA
# =============================================================================
print("\n[1] Loading WMS data...")

# Load WMS Alpha
df_alpha = pd.read_csv('data/wms_alpha.csv')
print(f"\nWMS Alpha loaded: {len(df_alpha)} records")
print("Columns:", df_alpha.columns.tolist())
print("\nSample data:")
print(df_alpha.head())

# Load WMS Beta
df_beta = pd.read_csv('data/wms_beta.csv')
print(f"\nWMS Beta loaded: {len(df_beta)} records")
print("Columns:", df_beta.columns.tolist())
print("\nSample data:")
print(df_beta.head())

# =============================================================================
# 2. DATA STANDARDIZATION
# =============================================================================
print("\n[2] Standardizing data formats...")

# Standardize column names for Alpha
df_alpha_std = df_alpha.copy()
df_alpha_std.columns = ['sku', 'qty', 'warehouse', 'timestamp']
df_alpha_std['source'] = 'Alpha'

# Standardize column names for Beta
df_beta_std = df_beta.copy()
df_beta_std.columns = ['sku', 'qty', 'warehouse', 'timestamp']
df_beta_std['source'] = 'Beta'

# Standardize warehouse names
warehouse_mapping = {
    'WH1': 'WH1',
    'Warehouse-01': 'WH1'
}
df_alpha_std['warehouse_std'] = df_alpha_std['warehouse'].map(warehouse_mapping)
df_beta_std['warehouse_std'] = df_beta_std['warehouse'].map(warehouse_mapping)

# Convert timestamps to datetime
df_alpha_std['timestamp'] = pd.to_datetime(df_alpha_std['timestamp'])
df_beta_std['timestamp'] = pd.to_datetime(df_beta_std['timestamp'])

# Convert quantities to numeric
df_alpha_std['qty'] = pd.to_numeric(df_alpha_std['qty'], errors='coerce')
df_beta_std['qty'] = pd.to_numeric(df_beta_std['qty'], errors='coerce')

print("\nStandardized Alpha data:")
print(df_alpha_std)
print("\nStandardized Beta data:")
print(df_beta_std)

# =============================================================================
# 3. INVENTORY RECONCILIATION
# =============================================================================
print("\n[3] Performing inventory reconciliation...")

# Combine both datasets
df_combined = pd.concat([df_alpha_std, df_beta_std], ignore_index=True)

# Get unique SKUs and warehouses
all_skus = df_combined['sku'].unique()
all_warehouses = df_combined['warehouse_std'].unique()

print(f"\nUnique SKUs: {all_skus.tolist()}")
print(f"Unique Warehouses: {all_warehouses.tolist()}")

# Create reconciliation summary
reconciliation_results = []

for sku in all_skus:
    for wh in all_warehouses:
        alpha_data = df_alpha_std[(df_alpha_std['sku'] == sku) & 
                                   (df_alpha_std['warehouse_std'] == wh)]
        beta_data = df_beta_std[(df_beta_std['sku'] == sku) & 
                                 (df_beta_std['warehouse_std'] == wh)]
        
        alpha_qty = alpha_data['qty'].sum() if len(alpha_data) > 0 else 0
        beta_qty = beta_data['qty'].sum() if len(beta_data) > 0 else 0
        
        # Get latest timestamps
        alpha_latest = alpha_data['timestamp'].max() if len(alpha_data) > 0 else None
        beta_latest = beta_data['timestamp'].max() if len(beta_data) > 0 else None
        
        # Determine reconciliation status
        if alpha_qty == beta_qty:
            status = 'RECONCILED'
            variance = 0
        else:
            status = 'VARIANCE'
            variance = alpha_qty - beta_qty
        
        reconciliation_results.append({
            'sku': sku,
            'warehouse': wh,
            'alpha_qty': alpha_qty,
            'beta_qty': beta_qty,
            'variance': variance,
            'variance_pct': (variance / beta_qty * 100) if beta_qty != 0 else (100 if alpha_qty > 0 else 0),
            'status': status,
            'alpha_latest_ts': alpha_latest,
            'beta_latest_ts': beta_latest,
            'alpha_records': len(alpha_data),
            'beta_records': len(beta_data)
        })

df_recon = pd.DataFrame(reconciliation_results)
print("\nReconciliation Results:")
print(df_recon.to_string())

# Save reconciliation results
df_recon.to_csv('outputs/reconciliation_summary.csv', index=False)
print("\nReconciliation summary saved to outputs/reconciliation_summary.csv")

# =============================================================================
# 4. KPI CALCULATIONS
# =============================================================================
print("\n[4] Calculating KPIs...")

# Overall reconciliation rate
total_records = len(df_recon)
reconciled_records = len(df_recon[df_recon['status'] == 'RECONCILED'])
reconciliation_rate = (reconciled_records / total_records * 100) if total_records > 0 else 0

# Total inventory values
total_alpha_qty = df_recon['alpha_qty'].sum()
total_beta_qty = df_recon['beta_qty'].sum()
total_variance = df_recon['variance'].sum()

# Variance statistics
variance_records = df_recon[df_recon['status'] == 'VARIANCE']
num_variances = len(variance_records)
avg_variance = variance_records['variance'].abs().mean() if num_variances > 0 else 0
max_variance = variance_records['variance'].abs().max() if num_variances > 0 else 0

# Data completeness
alpha_completeness = (df_recon['alpha_records'] > 0).sum() / total_records * 100
beta_completeness = (df_recon['beta_records'] > 0).sum() / total_records * 100

kpis = {
    'total_sku_warehouse_combinations': total_records,
    'reconciled_count': reconciled_records,
    'variance_count': num_variances,
    'reconciliation_rate_pct': reconciliation_rate,
    'total_alpha_qty': total_alpha_qty,
    'total_beta_qty': total_beta_qty,
    'total_variance': total_variance,
    'avg_absolute_variance': avg_variance,
    'max_absolute_variance': max_variance,
    'alpha_data_completeness_pct': alpha_completeness,
    'beta_data_completeness_pct': beta_completeness
}

print("\n" + "=" * 60)
print("KEY PERFORMANCE INDICATORS")
print("=" * 60)
for key, value in kpis.items():
    print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")

# Save KPIs
with open('outputs/kpis.txt', 'w') as f:
    for key, value in kpis.items():
        f.write(f"{key}: {value}\n")

# =============================================================================
# 5. VISUALIZATIONS
# =============================================================================
print("\n[5] Generating visualizations...")

# Figure 1: Reconciliation Status Overview
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Multi-WMS Inventory Reconciliation Dashboard', fontsize=16, fontweight='bold')

# Pie chart - Reconciliation Status
ax1 = axes[0, 0]
status_counts = df_recon['status'].value_counts()
colors = ['#2ecc71' if s == 'RECONCILED' else '#e74c3c' for s in status_counts.index]
wedges, texts, autotexts = ax1.pie(status_counts.values, labels=status_counts.index, 
                                    autopct='%1.1f%%', colors=colors, startangle=90)
ax1.set_title('Reconciliation Status Distribution', fontweight='bold')

# Bar chart - Quantity Comparison by SKU-Warehouse
ax2 = axes[0, 1]
x_pos = np.arange(len(df_recon))
width = 0.35
bars1 = ax2.bar(x_pos - width/2, df_recon['alpha_qty'], width, label='WMS Alpha', color='#3498db')
bars2 = ax2.bar(x_pos + width/2, df_recon['beta_qty'], width, label='WMS Beta', color='#e67e22')
ax2.set_xlabel('SKU-Warehouse Combination')
ax2.set_ylabel('Quantity')
ax2.set_title('Quantity Comparison: Alpha vs Beta', fontweight='bold')
ax2.set_xticks(x_pos)
ax2.set_xticklabels([f"{r['sku']}\n{r['warehouse']}" for _, r in df_recon.iterrows()], rotation=45, ha='right')
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

# Variance Analysis
ax3 = axes[1, 0]
variance_colors = ['#2ecc71' if v == 0 else '#e74c3c' for v in df_recon['variance']]
bars = ax3.bar(range(len(df_recon)), df_recon['variance'], color=variance_colors)
ax3.set_xlabel('SKU-Warehouse Combination')
ax3.set_ylabel('Variance (Alpha - Beta)')
ax3.set_title('Inventory Variance Analysis', fontweight='bold')
ax3.set_xticks(range(len(df_recon)))
ax3.set_xticklabels([f"{r['sku']}\n{r['warehouse']}" for _, r in df_recon.iterrows()], rotation=45, ha='right')
ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax3.grid(axis='y', alpha=0.3)

# KPI Summary Table
ax4 = axes[1, 1]
ax4.axis('off')
kpi_text = f"""
KEY PERFORMANCE INDICATORS

Reconciliation Rate: {reconciliation_rate:.1f}%
  - Reconciled: {reconciled_records} / {total_records}

Total Quantities:
  - Alpha: {total_alpha_qty:.0f}
  - Beta: {total_beta_qty:.0f}
  - Variance: {total_variance:.0f}

Variance Analysis:
  - Records with Variance: {num_variances}
  - Avg Absolute Variance: {avg_variance:.2f}
  - Max Absolute Variance: {max_variance:.2f}

Data Completeness:
  - Alpha: {alpha_completeness:.1f}%
  - Beta: {beta_completeness:.1f}%
"""
ax4.text(0.1, 0.5, kpi_text, transform=ax4.transAxes, fontsize=11,
         verticalalignment='center', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/reconciliation_dashboard.png', dpi=150, bbox_inches='tight')
print("Saved: report/images/reconciliation_dashboard.png")
plt.close()

# Figure 2: Detailed Variance Heatmap (if we have more data)
fig, ax = plt.subplots(figsize=(10, 6))

# Create pivot table for heatmap
pivot_data = df_recon.pivot_table(values='variance', index='sku', columns='warehouse', aggfunc='sum')
sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap='RdYlGn_r', center=0, 
            cbar_kws={'label': 'Variance (Alpha - Beta)'}, ax=ax)
ax.set_title('Inventory Variance Heatmap by SKU and Warehouse', fontweight='bold', fontsize=12)
plt.tight_layout()
plt.savefig('report/images/variance_heatmap.png', dpi=150, bbox_inches='tight')
print("Saved: report/images/variance_heatmap.png")
plt.close()

# Figure 3: Data Timeline
fig, ax = plt.subplots(figsize=(12, 6))

# Plot Alpha data points
for idx, row in df_alpha_std.iterrows():
    ax.scatter(row['timestamp'], row['qty'], s=200, c='#3498db', marker='o', 
               label='Alpha' if idx == 0 else "", zorder=5, edgecolors='white', linewidth=2)
    ax.annotate(f"{row['sku']}\n{row['warehouse_std']}", 
                (row['timestamp'], row['qty']), 
                textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)

# Plot Beta data points
for idx, row in df_beta_std.iterrows():
    ax.scatter(row['timestamp'], row['qty'], s=200, c='#e67e22', marker='s', 
               label='Beta' if idx == 0 else "", zorder=5, edgecolors='white', linewidth=2)
    ax.annotate(f"{row['sku']}\n{row['warehouse_std']}", 
                (row['timestamp'], row['qty']), 
                textcoords="offset points", xytext=(0,-20), ha='center', fontsize=9)

ax.set_xlabel('Timestamp')
ax.set_ylabel('Quantity')
ax.set_title('Inventory Data Timeline: Alpha vs Beta', fontweight='bold', fontsize=12)
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/data_timeline.png', dpi=150, bbox_inches='tight')
print("Saved: report/images/data_timeline.png")
plt.close()

# =============================================================================
# 6. GENERATE RECOMMENDATIONS
# =============================================================================
print("\n[6] Generating recommendations...")

recommendations = []

if reconciliation_rate < 100:
    recommendations.append(f"CRITICAL: {num_variances} SKU-warehouse combination(s) show inventory variance. Immediate investigation required.")
    
    for _, row in variance_records.iterrows():
        recommendations.append(f"  - {row['sku']} at {row['warehouse']}: Alpha={row['alpha_qty']}, Beta={row['beta_qty']}, Variance={row['variance']}")

if alpha_completeness < 100 or beta_completeness < 100:
    recommendations.append("WARNING: Data completeness issues detected. Some SKU-warehouse combinations missing from one or both WMS exports.")

if len(df_alpha_std) > len(df_beta_std):
    recommendations.append("NOTE: WMS Alpha has more transaction records than WMS Beta. Verify if all transactions are being captured in Beta.")
elif len(df_beta_std) > len(df_alpha_std):
    recommendations.append("NOTE: WMS Beta has more transaction records than WMS Alpha. Verify if all transactions are being captured in Alpha.")

recommendations.append("RECOMMENDATION: Implement automated daily reconciliation checks between WMS systems.")
recommendations.append("RECOMMENDATION: Standardize timestamp formats and warehouse naming conventions across systems.")

print("\nRecommendations:")
for rec in recommendations:
    print(f"  - {rec}")

# Save recommendations
with open('outputs/recommendations.txt', 'w') as f:
    for rec in recommendations:
        f.write(f"{rec}\n")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
print("\nOutput files generated:")
print("  - outputs/reconciliation_summary.csv")
print("  - outputs/kpis.txt")
print("  - outputs/recommendations.txt")
print("  - report/images/reconciliation_dashboard.png")
print("  - report/images/variance_heatmap.png")
print("  - report/images/data_timeline.png")
