#!/usr/bin/env python3
"""
WMS Inventory Reconciliation Analysis
Reconciles wms_alpha.csv and wms_beta.csv exports and generates KPIs.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Ensure output directories exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Set style for plots
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10

# Load data
print("Loading data files...")
alpha_df = pd.read_csv('data/wms_alpha.csv')
beta_df = pd.read_csv('data/wms_beta.csv')

print(f"\nAlpha records: {len(alpha_df)}")
print(f"Beta records: {len(beta_df)}")

# Display column names
print(f"\nAlpha columns: {list(alpha_df.columns)}")
print(f"Beta columns: {list(beta_df.columns)}")

# Normalize column names for comparison
alpha_norm = alpha_df.copy()
beta_norm = beta_df.copy()

# Standardize column names
alpha_norm.columns = ['sku', 'qty', 'warehouse', 'timestamp']
beta_norm.columns = ['sku', 'qty', 'warehouse', 'timestamp']

# Normalize warehouse names
warehouse_mapping = {
    'WH1': 'WH1',
    'Warehouse-01': 'WH1',
    'WH2': 'WH2',
    'Warehouse-02': 'WH2',
}

alpha_norm['warehouse_normalized'] = alpha_norm['warehouse'].map(warehouse_mapping).fillna(alpha_norm['warehouse'])
beta_norm['warehouse_normalized'] = beta_norm['warehouse'].map(warehouse_mapping).fillna(beta_norm['warehouse'])

# Parse timestamps
alpha_norm['timestamp'] = pd.to_datetime(alpha_norm['timestamp'])
beta_norm['timestamp'] = pd.to_datetime(beta_norm['timestamp'])

# Extract date for grouping
alpha_norm['date'] = alpha_norm['timestamp'].dt.date
beta_norm['date'] = beta_norm['timestamp'].dt.date

print("\n=== Normalized Alpha Data ===")
print(alpha_norm.to_string())

print("\n=== Normalized Beta Data ===")
print(beta_norm.to_string())

# Create reconciliation key (sku + warehouse + date)
alpha_norm['recon_key'] = alpha_norm['sku'] + '_' + alpha_norm['warehouse_normalized'] + '_' + alpha_norm['date'].astype(str)
beta_norm['recon_key'] = beta_norm['sku'] + '_' + beta_norm['warehouse_normalized'] + '_' + beta_norm['date'].astype(str)

# Aggregate quantities by reconciliation key
alpha_agg = alpha_norm.groupby(['sku', 'warehouse_normalized', 'date', 'recon_key'])['qty'].sum().reset_index()
alpha_agg.columns = ['sku', 'warehouse', 'date', 'recon_key', 'qty_alpha']

beta_agg = beta_norm.groupby(['sku', 'warehouse_normalized', 'date', 'recon_key'])['qty'].sum().reset_index()
beta_agg.columns = ['sku', 'warehouse', 'date', 'recon_key', 'qty_beta']

print("\n=== Aggregated Alpha ===")
print(alpha_agg.to_string())

print("\n=== Aggregated Beta ===")
print(beta_agg.to_string())

# Full outer join for reconciliation
recon_df = pd.merge(alpha_agg, beta_agg, on=['sku', 'warehouse', 'date', 'recon_key'], how='outer')

# Fill NaN values with 0 for comparison
recon_df['qty_alpha'] = recon_df['qty_alpha'].fillna(0)
recon_df['qty_beta'] = recon_df['qty_beta'].fillna(0)

# Calculate discrepancy
recon_df['discrepancy'] = recon_df['qty_alpha'] - recon_df['qty_beta']
recon_df['discrepancy_abs'] = recon_df['discrepancy'].abs()
recon_df['match_status'] = recon_df['discrepancy'].apply(lambda x: 'MATCH' if x == 0 else 'MISMATCH')

# Identify source of mismatch
recon_df['in_alpha_only'] = (recon_df['qty_alpha'] > 0) & (recon_df['qty_beta'] == 0)
recon_df['in_beta_only'] = (recon_df['qty_alpha'] == 0) & (recon_df['qty_beta'] > 0)
recon_df['in_both'] = (recon_df['qty_alpha'] > 0) & (recon_df['qty_beta'] > 0)

print("\n=== Reconciliation Results ===")
print(recon_df.to_string())

# Calculate KPIs
total_records_alpha = len(alpha_df)
total_records_beta = len(beta_df)
total_recon_keys = len(recon_df)
matched_keys = len(recon_df[recon_df['match_status'] == 'MATCH'])
mismatched_keys = len(recon_df[recon_df['match_status'] == 'MISMATCH'])
alpha_only_keys = len(recon_df[recon_df['in_alpha_only']])
beta_only_keys = len(recon_df[recon_df['in_beta_only']])

match_rate = (matched_keys / total_recon_keys * 100) if total_recon_keys > 0 else 0
total_qty_alpha = recon_df['qty_alpha'].sum()
total_qty_beta = recon_df['qty_beta'].sum()
total_discrepancy = recon_df['discrepancy'].sum()
total_abs_discrepancy = recon_df['discrepancy_abs'].sum()

print("\n=== KPI Summary ===")
print(f"Total Alpha Records: {total_records_alpha}")
print(f"Total Beta Records: {total_records_beta}")
print(f"Total Reconciliation Keys: {total_recon_keys}")
print(f"Matched Keys: {matched_keys}")
print(f"Mismatched Keys: {mismatched_keys}")
print(f"Alpha-Only Keys: {alpha_only_keys}")
print(f"Beta-Only Keys: {beta_only_keys}")
print(f"Match Rate: {match_rate:.2f}%")
print(f"Total Qty (Alpha): {total_qty_alpha}")
print(f"Total Qty (Beta): {total_qty_beta}")
print(f"Net Discrepancy: {total_discrepancy}")
print(f"Total Absolute Discrepancy: {total_abs_discrepancy}")

# Save reconciliation results
recon_df.to_csv('outputs/reconciliation_results.csv', index=False)
print("\nReconciliation results saved to outputs/reconciliation_results.csv")

# Generate visualizations
print("\nGenerating visualizations...")

# Figure 1: Quantity Comparison Bar Chart
fig1, ax1 = plt.subplots(figsize=(10, 6))
bar_width = 0.35
x = np.arange(len(recon_df))

ax1.bar(x - bar_width/2, recon_df['qty_alpha'], bar_width, label='WMS Alpha', color='#2E86AB')
ax1.bar(x + bar_width/2, recon_df['qty_beta'], bar_width, label='WMS Beta', color='#A23B72')

ax1.set_xlabel('Reconciliation Key (SKU_Warehouse_Date)')
ax1.set_ylabel('Quantity')
ax1.set_title('WMS Inventory Quantity Comparison by Reconciliation Key')
ax1.set_xticks(x)
ax1.set_xticklabels(recon_df['recon_key'], rotation=45, ha='right')
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/quantity_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/quantity_comparison.png")

# Figure 2: Discrepancy Analysis
fig2, ax2 = plt.subplots(figsize=(10, 6))
colors = ['green' if x == 0 else 'red' for x in recon_df['discrepancy']]
ax2.bar(range(len(recon_df)), recon_df['discrepancy'], color=colors)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax2.set_xlabel('Reconciliation Key Index')
ax2.set_ylabel('Discrepancy (Alpha - Beta)')
ax2.set_title('Inventory Discrepancy Analysis (Green=Match, Red=Mismatch)')
ax2.set_xticks(range(len(recon_df)))
ax2.set_xticklabels([f'{i+1}' for i in range(len(recon_df))])
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/discrepancy_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/discrepancy_analysis.png")

# Figure 3: Match Status Pie Chart
fig3, ax3 = plt.subplots(figsize=(8, 8))
status_counts = recon_df['match_status'].value_counts()
colors_pie = ['#28a745' if x == 'MATCH' else '#dc3545' for x in status_counts.index]
ax3.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', 
        colors=colors_pie, startangle=90, explode=(0.05, 0.05) if len(status_counts) > 1 else (0,))
ax3.set_title('Reconciliation Match Status Distribution')

plt.tight_layout()
plt.savefig('report/images/match_status_pie.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/match_status_pie.png")

# Figure 4: Data Coverage Heatmap
fig4, ax4 = plt.subplots(figsize=(8, 6))

# Create coverage matrix
coverage_data = []
for idx, row in recon_df.iterrows():
    coverage_data.append({
        'Reconciliation Key': row['recon_key'],
        'WMS Alpha': 1 if row['qty_alpha'] > 0 else 0,
        'WMS Beta': 1 if row['qty_beta'] > 0 else 0
    })

coverage_df = pd.DataFrame(coverage_data)
coverage_matrix = coverage_df.set_index('Reconciliation Key')[['WMS Alpha', 'WMS Beta']].T

sns.heatmap(coverage_matrix, annot=True, cmap='Blues', fmt='.0f', ax=ax4, cbar=False)
ax4.set_title('Data Coverage Heatmap (1=Present, 0=Missing)')
ax4.set_xlabel('Reconciliation Key')
ax4.set_ylabel('WMS System')

plt.tight_layout()
plt.savefig('report/images/coverage_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/coverage_heatmap.png")

# Figure 5: Summary KPI Dashboard
fig5, ax5 = plt.subplots(figsize=(12, 8))
ax5.axis('off')

# Create KPI table
kpi_data = [
    ['Metric', 'Value'],
    ['Total Alpha Records', str(total_records_alpha)],
    ['Total Beta Records', str(total_records_beta)],
    ['Reconciliation Keys', str(total_recon_keys)],
    ['Matched Keys', f"{matched_keys} ({match_rate:.1f}%)"],
    ['Mismatched Keys', str(mismatched_keys)],
    ['Alpha-Only Keys', str(alpha_only_keys)],
    ['Beta-Only Keys', str(beta_only_keys)],
    ['Total Qty (Alpha)', str(total_qty_alpha)],
    ['Total Qty (Beta)', str(total_qty_beta)],
    ['Net Discrepancy', str(total_discrepancy)],
    ['Total Abs Discrepancy', str(total_abs_discrepancy)],
]

table = ax5.table(cellText=kpi_data, loc='center', cellLoc='center',
                  colWidths=[0.4, 0.3], bbox=[0.1, 0.1, 0.8, 0.8])
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.2, 1.5)

# Style header
for i in range(2):
    table[(0, i)].set_facecolor('#2E86AB')
    table[(0, i)].set_text_props(color='white', fontweight='bold')

# Alternate row colors
for i in range(1, len(kpi_data)):
    for j in range(2):
        if i % 2 == 0:
            table[(i, j)].set_facecolor('#f0f0f0')

ax5.set_title('WMS Inventory Reconciliation - KPI Summary Dashboard', fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('report/images/kpi_dashboard.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/kpi_dashboard.png")

print("\n=== Analysis Complete ===")
print("All visualizations saved to report/images/")
