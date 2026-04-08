import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("="*70)
print("WMS INVENTORY RECONCILIATION ANALYSIS")
print("="*70)

# =============================================================================
# 1. DATA LOADING AND STANDARDIZATION
# =============================================================================
print("\n1. DATA LOADING AND STANDARDIZATION")
print("-"*50)

# Read both WMS exports
wms_alpha = pd.read_csv('../data/wms_alpha.csv')
wms_beta = pd.read_csv('../data/wms_beta.csv')

print(f"\nWMS Alpha Records: {len(wms_alpha)}")
print(f"WMS Beta Records: {len(wms_beta)}")

# Standardize column names
wms_alpha_std = wms_alpha.rename(columns={
    'sku': 'SKU',
    'qty': 'Quantity',
    'warehouse': 'Warehouse',
    'as_of_utc': 'Timestamp'
})
wms_alpha_std['Source'] = 'WMS_Alpha'

wms_beta_std = wms_beta.rename(columns={
    'SKU': 'SKU',
    'Quantity': 'Quantity',
    'Site': 'Warehouse',
    'timestamp_local': 'Timestamp'
})
wms_beta_std['Source'] = 'WMS_Beta'

# =============================================================================
# 2. WAREHOUSE MAPPING
# =============================================================================
print("\n2. WAREHOUSE MAPPING")
print("-"*50)

# Create warehouse mapping based on analysis
# WH1 in Alpha appears to correspond to Warehouse-01 in Beta
warehouse_mapping = {
    'WH1': 'Warehouse-01',
    'WH2': 'Warehouse-02',
    'WH3': 'Warehouse-03',
    'Warehouse-01': 'Warehouse-01',
    'Warehouse-02': 'Warehouse-02',
    'Warehouse-03': 'Warehouse-03'
}

# Apply standardized warehouse names
wms_alpha_std['Warehouse_Std'] = wms_alpha_std['Warehouse'].map(warehouse_mapping)
wms_beta_std['Warehouse_Std'] = wms_beta_std['Warehouse'].map(warehouse_mapping)

print("\nWarehouse Mapping Applied:")
print("Alpha Warehouses:", wms_alpha_std['Warehouse'].unique().tolist())
print("Beta Warehouses:", wms_beta_std['Warehouse'].unique().tolist())
print("Standardized:", wms_alpha_std['Warehouse_Std'].unique().tolist())

# =============================================================================
# 3. TIMESTAMP NORMALIZATION
# =============================================================================
print("\n3. TIMESTAMP NORMALIZATION")
print("-"*50)

# Parse timestamps
wms_alpha_std['Timestamp_Parsed'] = pd.to_datetime(wms_alpha_std['Timestamp'], utc=True)
wms_beta_std['Timestamp_Parsed'] = pd.to_datetime(wms_beta_std['Timestamp'])

# Convert Beta to UTC (assuming local time is UTC+8 based on the 8-hour difference)
wms_beta_std['Timestamp_Parsed'] = wms_beta_std['Timestamp_Parsed'].dt.tz_localize('Asia/Shanghai').dt.tz_convert('UTC')

print("\nAlpha Timestamp Range:")
print(f"  From: {wms_alpha_std['Timestamp_Parsed'].min()}")
print(f"  To: {wms_alpha_std['Timestamp_Parsed'].max()}")

print("\nBeta Timestamp Range:")
print(f"  From: {wms_beta_std['Timestamp_Parsed'].min()}")
print(f"  To: {wms_beta_std['Timestamp_Parsed'].max()}")

# =============================================================================
# 4. INVENTORY RECONCILIATION
# =============================================================================
print("\n4. INVENTORY RECONCILIATION")
print("-"*50)

# Get latest records from each system (by SKU and Warehouse)
wms_alpha_latest = wms_alpha_std.sort_values('Timestamp_Parsed').groupby(['SKU', 'Warehouse_Std']).last().reset_index()
wms_beta_latest = wms_beta_std.sort_values('Timestamp_Parsed').groupby(['SKU', 'Warehouse_Std']).last().reset_index()

print(f"\nLatest Alpha Records: {len(wms_alpha_latest)}")
print(wms_alpha_latest[['SKU', 'Warehouse_Std', 'Quantity', 'Timestamp_Parsed']])

print(f"\nLatest Beta Records: {len(wms_beta_latest)}")
print(wms_beta_latest[['SKU', 'Warehouse_Std', 'Quantity', 'Timestamp_Parsed']])

# Merge for comparison
reconciliation = pd.merge(
    wms_alpha_latest[['SKU', 'Warehouse_Std', 'Quantity', 'Timestamp_Parsed']],
    wms_beta_latest[['SKU', 'Warehouse_Std', 'Quantity', 'Timestamp_Parsed']],
    on=['SKU', 'Warehouse_Std'],
    how='outer',
    suffixes=('_Alpha', '_Beta')
)

# Calculate discrepancies
reconciliation['Quantity_Alpha'] = reconciliation['Quantity_Alpha'].fillna(0)
reconciliation['Quantity_Beta'] = reconciliation['Quantity_Beta'].fillna(0)
reconciliation['Discrepancy'] = reconciliation['Quantity_Alpha'] - reconciliation['Quantity_Beta']
reconciliation['Discrepancy_Pct'] = np.where(
    reconciliation['Quantity_Alpha'] + reconciliation['Quantity_Beta'] > 0,
    abs(reconciliation['Discrepancy']) / ((reconciliation['Quantity_Alpha'] + reconciliation['Quantity_Beta']) / 2) * 100,
    0
)
reconciliation['Match_Status'] = reconciliation.apply(
    lambda x: 'MATCH' if x['Discrepancy'] == 0 else ('ALPHA_ONLY' if x['Quantity_Beta'] == 0 else ('BETA_ONLY' if x['Quantity_Alpha'] == 0 else 'MISMATCH')),
    axis=1
)

print("\nReconciliation Results:")
print(reconciliation.to_string())

# Save reconciliation results
reconciliation.to_csv('../outputs/reconciliation_results.csv', index=False)

# =============================================================================
# 5. KPI CALCULATION
# =============================================================================
print("\n5. KEY PERFORMANCE INDICATORS (KPIs)")
print("-"*50)

total_skus_alpha = wms_alpha_std['SKU'].nunique()
total_skus_beta = wms_beta_std['SKU'].nunique()
total_skus_combined = reconciliation['SKU'].nunique()

total_qty_alpha = wms_alpha_std['Quantity'].sum()
total_qty_beta = wms_beta_std['Quantity'].sum()

matching_records = len(reconciliation[reconciliation['Match_Status'] == 'MATCH'])
mismatch_records = len(reconciliation[reconciliation['Match_Status'] == 'MISMATCH'])
alpha_only = len(reconciliation[reconciliation['Match_Status'] == 'ALPHA_ONLY'])
beta_only = len(reconciliation[reconciliation['Match_Status'] == 'BETA_ONLY'])

match_rate = matching_records / len(reconciliation) * 100 if len(reconciliation) > 0 else 0
total_discrepancy = abs(reconciliation['Discrepancy'].sum())

kpis = {
    'Metric': [
        'Total Unique SKUs (Alpha)',
        'Total Unique SKUs (Beta)',
        'Total Unique SKUs (Combined)',
        'Total Quantity (Alpha)',
        'Total Quantity (Beta)',
        'Total Records (Alpha)',
        'Total Records (Beta)',
        'Matching Records',
        'Mismatch Records',
        'Alpha-Only Records',
        'Beta-Only Records',
        'Match Rate (%)',
        'Total Discrepancy (Units)',
        'Avg Discrepancy per SKU (%)'
    ],
    'Value': [
        total_skus_alpha,
        total_skus_beta,
        total_skus_combined,
        total_qty_alpha,
        total_qty_beta,
        len(wms_alpha_std),
        len(wms_beta_std),
        matching_records,
        mismatch_records,
        alpha_only,
        beta_only,
        round(match_rate, 2),
        total_discrepancy,
        round(reconciliation['Discrepancy_Pct'].mean(), 2)
    ]
}

kpi_df = pd.DataFrame(kpis)
print("\n" + kpi_df.to_string(index=False))
kpi_df.to_csv('../outputs/kpi_summary.csv', index=False)

# =============================================================================
# 6. VISUALIZATIONS
# =============================================================================
print("\n6. GENERATING VISUALIZATIONS")
print("-"*50)

# Figure 1: Match Status Distribution
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 1.1 Match Status Pie Chart
ax1 = axes[0, 0]
status_counts = reconciliation['Match_Status'].value_counts()
colors = {'MATCH': '#2ecc71', 'MISMATCH': '#e74c3c', 'ALPHA_ONLY': '#3498db', 'BETA_ONLY': '#9b59b6'}
if len(status_counts) > 0:
    wedges, texts, autotexts = ax1.pie(status_counts.values, labels=status_counts.index, 
                                        autopct='%1.1f%%', colors=[colors.get(x, '#95a5a6') for x in status_counts.index],
                                        explode=[0.05]*len(status_counts))
    ax1.set_title('Reconciliation Match Status Distribution', fontsize=12, fontweight='bold')

# 1.2 Quantity Comparison Bar Chart
ax2 = axes[0, 1]
x_pos = np.arange(len(reconciliation))
width = 0.35
bars1 = ax2.bar(x_pos - width/2, reconciliation['Quantity_Alpha'], width, label='WMS Alpha', color='#3498db', alpha=0.8)
bars2 = ax2.bar(x_pos + width/2, reconciliation['Quantity_Beta'], width, label='WMS Beta', color='#e74c3c', alpha=0.8)
ax2.set_xlabel('SKU-Warehouse Combination', fontsize=10)
ax2.set_ylabel('Quantity', fontsize=10)
ax2.set_title('Quantity Comparison: WMS Alpha vs WMS Beta', fontsize=12, fontweight='bold')
ax2.set_xticks(x_pos)
ax2.set_xticklabels([f"{row['SKU']}\n{row['Warehouse_Std']}" for _, row in reconciliation.iterrows()], fontsize=8)
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

# 1.3 Discrepancy Analysis
ax3 = axes[1, 0]
colors_discrepancy = ['#2ecc71' if x == 0 else '#e74c3c' for x in reconciliation['Discrepancy']]
bars = ax3.bar(range(len(reconciliation)), reconciliation['Discrepancy'], color=colors_discrepancy, alpha=0.8)
ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax3.set_xlabel('SKU-Warehouse Combination', fontsize=10)
ax3.set_ylabel('Discrepancy (Alpha - Beta)', fontsize=10)
ax3.set_title('Inventory Discrepancy by SKU-Warehouse', fontsize=12, fontweight='bold')
ax3.set_xticks(range(len(reconciliation)))
ax3.set_xticklabels([f"{row['SKU']}\n{row['Warehouse_Std']}" for _, row in reconciliation.iterrows()], fontsize=8)
ax3.grid(axis='y', alpha=0.3)

# 1.4 KPI Summary Table
ax4 = axes[1, 1]
ax4.axis('off')
table_data = [[kpi_df['Metric'].iloc[i], kpi_df['Value'].iloc[i]] for i in range(len(kpi_df))]
table = ax4.table(cellText=table_data, colLabels=['Metric', 'Value'], loc='center', cellLoc='left',
                   colWidths=[0.6, 0.3])
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1.2, 1.5)
# Color header
table[(0, 0)].set_facecolor('#3498db')
table[(0, 1)].set_facecolor('#3498db')
table[(0, 0)].set_text_props(color='white', fontweight='bold')
table[(0, 1)].set_text_props(color='white', fontweight='bold')
ax4.set_title('Key Performance Indicators Summary', fontsize=12, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('../report/images/reconciliation_dashboard.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: reconciliation_dashboard.png")

# Figure 2: Data Completeness Analysis
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 2.1 Records by Source
ax1 = axes[0]
source_data = pd.DataFrame({
    'Source': ['WMS Alpha', 'WMS Beta'],
    'Records': [len(wms_alpha_std), len(wms_beta_std)],
    'Unique SKUs': [total_skus_alpha, total_skus_beta]
})
x = np.arange(len(source_data['Source']))
width = 0.35
ax1.bar(x - width/2, source_data['Records'], width, label='Total Records', color='#3498db', alpha=0.8)
ax1.bar(x + width/2, source_data['Unique SKUs'], width, label='Unique SKUs', color='#2ecc71', alpha=0.8)
ax1.set_xlabel('Data Source', fontsize=10)
ax1.set_ylabel('Count', fontsize=10)
ax1.set_title('Data Volume by Source', fontsize=12, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(source_data['Source'])
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

# Add value labels
for i, (rec, sku) in enumerate(zip(source_data['Records'], source_data['Unique SKUs'])):
    ax1.annotate(f'{rec}', (i - width/2, rec), ha='center', va='bottom', fontsize=9)
    ax1.annotate(f'{sku}', (i + width/2, sku), ha='center', va='bottom', fontsize=9)

# 2.2 Timeline Analysis
ax2 = axes[1]
if len(wms_alpha_std) > 0:
    alpha_dates = wms_alpha_std['Timestamp_Parsed'].dt.date.value_counts().sort_index()
    ax2.bar(range(len(alpha_dates)), alpha_dates.values, label='WMS Alpha', color='#3498db', alpha=0.7, width=0.4, align='edge')
if len(wms_beta_std) > 0:
    beta_dates = wms_beta_std['Timestamp_Parsed'].dt.date.value_counts().sort_index()
    ax2.bar(range(len(beta_dates)), beta_dates.values, label='WMS Beta', color='#e74c3c', alpha=0.7, width=-0.4, align='edge')
ax2.set_xlabel('Date Index', fontsize=10)
ax2.set_ylabel('Record Count', fontsize=10)
ax2.set_title('Records Distribution Over Time', fontsize=12, fontweight='bold')
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/data_completeness.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: data_completeness.png")

# Figure 3: Detailed Discrepancy Heatmap
fig, ax = plt.subplots(figsize=(10, 6))

# Create pivot table for heatmap
if len(reconciliation) > 0:
    pivot_data = reconciliation.pivot_table(
        values='Discrepancy', 
        index='SKU', 
        columns='Warehouse_Std', 
        aggfunc='sum',
        fill_value=0
    )
    
    if not pivot_data.empty:
        sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap='RdYlGn_r', center=0, 
                    linewidths=0.5, ax=ax, cbar_kws={'label': 'Discrepancy (Alpha - Beta)'})
        ax.set_title('Inventory Discrepancy Heatmap by SKU and Warehouse', fontsize=12, fontweight='bold')
        ax.set_xlabel('Warehouse', fontsize=10)
        ax.set_ylabel('SKU', fontsize=10)

plt.tight_layout()
plt.savefig('../report/images/discrepancy_heatmap.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: discrepancy_heatmap.png")

# =============================================================================
# 7. SUMMARY STATISTICS
# =============================================================================
print("\n7. SUMMARY STATISTICS")
print("-"*50)

print("\n=== WMS Alpha Summary ===")
print(wms_alpha_std.describe())

print("\n=== WMS Beta Summary ===")
print(wms_beta_std.describe())

print("\n=== Reconciliation Summary ===")
print(reconciliation.describe())

# Save all data to outputs
wms_alpha_std.to_csv('../outputs/wms_alpha_standardized.csv', index=False)
wms_beta_std.to_csv('../outputs/wms_beta_standardized.csv', index=False)

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print("\nOutput files saved to:")
print("  - outputs/reconciliation_results.csv")
print("  - outputs/kpi_summary.csv")
print("  - outputs/wms_alpha_standardized.csv")
print("  - outputs/wms_beta_standardized.csv")
print("\nVisualization files saved to:")
print("  - report/images/reconciliation_dashboard.png")
print("  - report/images/data_completeness.png")
print("  - report/images/discrepancy_heatmap.png")