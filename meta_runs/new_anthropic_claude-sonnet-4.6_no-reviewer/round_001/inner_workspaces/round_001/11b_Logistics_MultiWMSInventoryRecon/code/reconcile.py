#!/usr/bin/env python3
"""
WMS Inventory Reconciliation Analysis
Reconciles wms_alpha.csv and wms_beta.csv and summarizes KPIs for management.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from datetime import datetime, timezone
import json
import os
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# 0. Setup
# ─────────────────────────────────────────────
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("=" * 60)
print("WMS INVENTORY RECONCILIATION ANALYSIS")
print("=" * 60)

# ─────────────────────────────────────────────
# 1. Load Raw Data
# ─────────────────────────────────────────────
alpha_raw = pd.read_csv('data/wms_alpha.csv')
beta_raw  = pd.read_csv('data/wms_beta.csv')

print("\n[Alpha WMS] Raw data:")
print(alpha_raw.to_string())
print(f"Shape: {alpha_raw.shape}")

print("\n[Beta WMS] Raw data:")
print(beta_raw.to_string())
print(f"Shape: {beta_raw.shape}")

# ─────────────────────────────────────────────
# 2. Normalize / Standardize
# ─────────────────────────────────────────────

# --- Alpha: rename columns to canonical names ---
alpha = alpha_raw.rename(columns={
    'sku':       'SKU',
    'qty':       'Quantity',
    'warehouse': 'Site_raw',
    'as_of_utc': 'Timestamp_raw'
}).copy()

# Parse timestamps (UTC-aware)
alpha['Timestamp_utc'] = pd.to_datetime(alpha['Timestamp_raw'], utc=True)

# Warehouse code normalisation map (Alpha codes → canonical)
WH_MAP_ALPHA = {
    'WH1': 'Warehouse-01',
    'WH2': 'Warehouse-02',
    'WH3': 'Warehouse-03',
}
alpha['Site'] = alpha['Site_raw'].map(WH_MAP_ALPHA).fillna(alpha['Site_raw'])
alpha['Source'] = 'Alpha'

# --- Beta: rename columns to canonical names ---
beta = beta_raw.rename(columns={
    'SKU':             'SKU',
    'Quantity':        'Quantity',
    'Site':            'Site',
    'timestamp_local': 'Timestamp_raw'
}).copy()

# Parse timestamps (assume local = UTC+8 for this warehouse, convert to UTC)
beta['Timestamp_utc'] = pd.to_datetime(beta['Timestamp_raw']).dt.tz_localize('Asia/Shanghai').dt.tz_convert('UTC')
beta['Source'] = 'Beta'

print("\n[Alpha] Normalized:")
print(alpha[['SKU','Quantity','Site','Timestamp_utc','Source']].to_string())

print("\n[Beta] Normalized:")
print(beta[['SKU','Quantity','Site','Timestamp_utc','Source']].to_string())

# ─────────────────────────────────────────────
# 3. Deduplication within each system
# ─────────────────────────────────────────────
# For each (SKU, Site) keep the LATEST snapshot
alpha_latest = (
    alpha.sort_values('Timestamp_utc')
         .groupby(['SKU','Site'], as_index=False)
         .last()
         [['SKU','Site','Quantity','Timestamp_utc','Source']]
)

beta_latest = (
    beta.sort_values('Timestamp_utc')
        .groupby(['SKU','Site'], as_index=False)
        .last()
        [['SKU','Site','Quantity','Timestamp_utc','Source']]
)

print("\n[Alpha] Latest snapshot per (SKU, Site):")
print(alpha_latest.to_string())

print("\n[Beta] Latest snapshot per (SKU, Site):")
print(beta_latest.to_string())

# ─────────────────────────────────────────────
# 4. Merge for Reconciliation
# ─────────────────────────────────────────────
recon = pd.merge(
    alpha_latest[['SKU','Site','Quantity','Timestamp_utc']].rename(
        columns={'Quantity':'Qty_Alpha','Timestamp_utc':'Ts_Alpha'}),
    beta_latest[['SKU','Site','Quantity','Timestamp_utc']].rename(
        columns={'Quantity':'Qty_Beta','Timestamp_utc':'Ts_Beta'}),
    on=['SKU','Site'],
    how='outer'
)

# Fill NaN quantities with 0 for arithmetic
recon['Qty_Alpha'] = recon['Qty_Alpha'].fillna(0)
recon['Qty_Beta']  = recon['Qty_Beta'].fillna(0)

# Discrepancy: Beta minus Alpha (positive = Beta has more)
recon['Discrepancy']     = recon['Qty_Beta'] - recon['Qty_Alpha']
recon['Abs_Discrepancy'] = recon['Discrepancy'].abs()
recon['Pct_Discrepancy'] = np.where(
    recon['Qty_Alpha'] != 0,
    (recon['Discrepancy'] / recon['Qty_Alpha']) * 100,
    np.nan
)

# Status classification
def classify(row):
    if row['Qty_Alpha'] == 0 and row['Qty_Beta'] > 0:
        return 'Alpha-Only Missing'
    elif row['Qty_Beta'] == 0 and row['Qty_Alpha'] > 0:
        return 'Beta-Only Missing'
    elif row['Discrepancy'] == 0:
        return 'Matched'
    elif abs(row['Discrepancy']) / max(row['Qty_Alpha'], row['Qty_Beta']) <= 0.01:
        return 'Within Tolerance (≤1%)'
    else:
        return 'Discrepancy'

recon['Status'] = recon.apply(classify, axis=1)

print("\n[Reconciliation Table]:")
print(recon.to_string())

# ─────────────────────────────────────────────
# 5. KPI Computation
# ─────────────────────────────────────────────
total_skus_alpha = alpha_latest['SKU'].nunique()
total_skus_beta  = beta_latest['SKU'].nunique()
total_records_alpha = len(alpha_raw)
total_records_beta  = len(beta_raw)
total_recon_rows = len(recon)

matched_rows   = (recon['Status'] == 'Matched').sum()
discrepancy_rows = (recon['Status'] == 'Discrepancy').sum()
alpha_missing  = (recon['Status'] == 'Alpha-Only Missing').sum()
beta_missing   = (recon['Status'] == 'Beta-Only Missing').sum()
tolerance_rows = (recon['Status'] == 'Within Tolerance (≤1%)').sum()

match_rate = matched_rows / total_recon_rows * 100 if total_recon_rows > 0 else 0

total_qty_alpha = recon['Qty_Alpha'].sum()
total_qty_beta  = recon['Qty_Beta'].sum()
total_discrepancy_qty = recon['Discrepancy'].sum()
total_abs_discrepancy = recon['Abs_Discrepancy'].sum()

kpis = {
    'Total Raw Records (Alpha)':       total_records_alpha,
    'Total Raw Records (Beta)':        total_records_beta,
    'Unique SKU-Site Pairs (Alpha)':   len(alpha_latest),
    'Unique SKU-Site Pairs (Beta)':    len(beta_latest),
    'Total Reconciliation Rows':       total_recon_rows,
    'Matched (Exact)':                 int(matched_rows),
    'Within Tolerance (≤1%)':          int(tolerance_rows),
    'Discrepancy':                     int(discrepancy_rows),
    'Alpha-Only Missing in Beta':      int(alpha_missing),
    'Beta-Only Missing in Alpha':      int(beta_missing),
    'Match Rate (%)':                  round(match_rate, 2),
    'Total Qty Alpha':                 float(total_qty_alpha),
    'Total Qty Beta':                  float(total_qty_beta),
    'Net Discrepancy (Beta-Alpha)':    float(total_discrepancy_qty),
    'Total Absolute Discrepancy':      float(total_abs_discrepancy),
}

print("\n[KPIs]:")
for k, v in kpis.items():
    print(f"  {k}: {v}")

# Save KPIs
with open('outputs/kpis.json', 'w') as f:
    json.dump(kpis, f, indent=2)

# Save reconciliation table
recon.to_csv('outputs/reconciliation_table.csv', index=False)

# ─────────────────────────────────────────────
# 6. Figures
# ─────────────────────────────────────────────

# Color palette
COLORS = {
    'Matched':                 '#2ecc71',
    'Within Tolerance (≤1%)':  '#f39c12',
    'Discrepancy':             '#e74c3c',
    'Alpha-Only Missing':      '#9b59b6',
    'Beta-Only Missing':       '#3498db',
}

# ── Figure 1: Status Distribution Pie Chart ──
status_counts = recon['Status'].value_counts()
fig1, ax1 = plt.subplots(figsize=(7, 5))
colors_pie = [COLORS.get(s, '#95a5a6') for s in status_counts.index]
wedges, texts, autotexts = ax1.pie(
    status_counts.values,
    labels=status_counts.index,
    autopct='%1.1f%%',
    colors=colors_pie,
    startangle=140,
    pctdistance=0.75,
    wedgeprops=dict(edgecolor='white', linewidth=1.5)
)
for t in texts:
    t.set_fontsize(10)
for at in autotexts:
    at.set_fontsize(9)
    at.set_fontweight('bold')
ax1.set_title('Reconciliation Status Distribution\n(SKU-Site Pairs)', fontsize=13, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig('report/images/fig1_status_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_status_distribution.png")

# ── Figure 2: Alpha vs Beta Quantity Comparison (Bar) ──
fig2, ax2 = plt.subplots(figsize=(8, 5))
recon_sorted = recon.sort_values('SKU').reset_index(drop=True)
x = np.arange(len(recon_sorted))
width = 0.35
bars_a = ax2.bar(x - width/2, recon_sorted['Qty_Alpha'], width, label='Alpha WMS', color='#3498db', edgecolor='white')
bars_b = ax2.bar(x + width/2, recon_sorted['Qty_Beta'],  width, label='Beta WMS',  color='#e67e22', edgecolor='white')
ax2.set_xlabel('SKU – Site', fontsize=11)
ax2.set_ylabel('Quantity (units)', fontsize=11)
ax2.set_title('Inventory Quantity: Alpha vs Beta WMS\n(Latest Snapshot per SKU-Site)', fontsize=13, fontweight='bold')
labels = [f"{r['SKU']}\n{r['Site']}" for _, r in recon_sorted.iterrows()]
ax2.set_xticks(x)
ax2.set_xticklabels(labels, fontsize=9)
ax2.legend(fontsize=10)
ax2.yaxis.grid(True, linestyle='--', alpha=0.6)
ax2.set_axisbelow(True)
# Annotate bars
for bar in bars_a:
    h = bar.get_height()
    if h > 0:
        ax2.text(bar.get_x() + bar.get_width()/2, h + 0.1, f'{h:.0f}', ha='center', va='bottom', fontsize=8)
for bar in bars_b:
    h = bar.get_height()
    if h > 0:
        ax2.text(bar.get_x() + bar.get_width()/2, h + 0.1, f'{h:.0f}', ha='center', va='bottom', fontsize=8)
plt.tight_layout()
plt.savefig('report/images/fig2_qty_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_qty_comparison.png")

# ── Figure 3: Discrepancy Waterfall / Bar ──
fig3, ax3 = plt.subplots(figsize=(8, 5))
bar_colors = ['#2ecc71' if d == 0 else ('#e74c3c' if d < 0 else '#e67e22')
              for d in recon_sorted['Discrepancy']]
bars3 = ax3.bar(x, recon_sorted['Discrepancy'], color=bar_colors, edgecolor='white', width=0.5)
ax3.axhline(0, color='black', linewidth=0.8, linestyle='--')
ax3.set_xlabel('SKU – Site', fontsize=11)
ax3.set_ylabel('Discrepancy (Beta − Alpha)', fontsize=11)
ax3.set_title('Inventory Discrepancy per SKU-Site\n(Beta WMS minus Alpha WMS)', fontsize=13, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(labels, fontsize=9)
ax3.yaxis.grid(True, linestyle='--', alpha=0.6)
ax3.set_axisbelow(True)
for bar, val in zip(bars3, recon_sorted['Discrepancy']):
    ax3.text(bar.get_x() + bar.get_width()/2,
             val + (0.05 if val >= 0 else -0.15),
             f'{val:+.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
# Legend
patch_pos = mpatches.Patch(color='#e67e22', label='Beta > Alpha')
patch_neg = mpatches.Patch(color='#e74c3c', label='Beta < Alpha')
patch_zero = mpatches.Patch(color='#2ecc71', label='Matched')
ax3.legend(handles=[patch_pos, patch_neg, patch_zero], fontsize=9)
plt.tight_layout()
plt.savefig('report/images/fig3_discrepancy.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_discrepancy.png")

# ── Figure 4: KPI Summary Dashboard ──
fig4, axes = plt.subplots(1, 3, figsize=(12, 4))
fig4.suptitle('WMS Reconciliation KPI Dashboard', fontsize=14, fontweight='bold', y=1.02)

# Panel A: Record counts
ax_a = axes[0]
categories = ['Alpha\nRaw Records', 'Beta\nRaw Records', 'Alpha\nSKU-Sites', 'Beta\nSKU-Sites']
values = [total_records_alpha, total_records_beta, len(alpha_latest), len(beta_latest)]
bars_a2 = ax_a.bar(categories, values, color=['#3498db','#e67e22','#2980b9','#d35400'], edgecolor='white')
ax_a.set_title('Data Volume', fontsize=11, fontweight='bold')
ax_a.set_ylabel('Count')
ax_a.yaxis.grid(True, linestyle='--', alpha=0.5)
ax_a.set_axisbelow(True)
for bar in bars_a2:
    ax_a.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
              str(int(bar.get_height())), ha='center', va='bottom', fontsize=9)

# Panel B: Match rate gauge (horizontal bar)
ax_b = axes[1]
ax_b.barh(['Match Rate'], [match_rate], color='#2ecc71', height=0.4)
ax_b.barh(['Match Rate'], [100 - match_rate], left=[match_rate], color='#e74c3c', height=0.4)
ax_b.set_xlim(0, 100)
ax_b.set_xlabel('Percentage (%)')
ax_b.set_title(f'Match Rate: {match_rate:.1f}%', fontsize=11, fontweight='bold')
ax_b.axvline(100, color='gray', linestyle='--', linewidth=0.8)
ax_b.text(match_rate / 2, 0, f'{match_rate:.1f}%', ha='center', va='center',
          fontsize=12, fontweight='bold', color='white')
if match_rate < 100:
    ax_b.text(match_rate + (100 - match_rate) / 2, 0, f'{100-match_rate:.1f}%',
              ha='center', va='center', fontsize=10, fontweight='bold', color='white')

# Panel C: Quantity totals
ax_c = axes[2]
qty_cats = ['Total Qty\nAlpha', 'Total Qty\nBeta', 'Net\nDiscrepancy']
qty_vals = [total_qty_alpha, total_qty_beta, abs(total_discrepancy_qty)]
qty_colors = ['#3498db', '#e67e22', '#e74c3c' if total_discrepancy_qty != 0 else '#2ecc71']
bars_c = ax_c.bar(qty_cats, qty_vals, color=qty_colors, edgecolor='white')
ax_c.set_title('Quantity Summary', fontsize=11, fontweight='bold')
ax_c.set_ylabel('Units')
ax_c.yaxis.grid(True, linestyle='--', alpha=0.5)
ax_c.set_axisbelow(True)
for bar, val in zip(bars_c, qty_vals):
    ax_c.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
              f'{val:.0f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/fig4_kpi_dashboard.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig4_kpi_dashboard.png")

# ── Figure 5: Timeline of snapshots ──
fig5, ax5 = plt.subplots(figsize=(10, 4))

# Combine all snapshots
alpha_all = alpha[['SKU','Site','Quantity','Timestamp_utc','Source']].copy()
beta_all  = beta[['SKU','Site','Quantity','Timestamp_utc','Source']].copy()
all_snaps = pd.concat([alpha_all, beta_all], ignore_index=True)
all_snaps = all_snaps.sort_values('Timestamp_utc')

for src, grp in all_snaps.groupby('Source'):
    color = '#3498db' if src == 'Alpha' else '#e67e22'
    marker = 'o' if src == 'Alpha' else 's'
    for _, row in grp.iterrows():
        label_str = f"{row['SKU']} @ {row['Site']}"
        ax5.scatter(row['Timestamp_utc'], row['Quantity'],
                    color=color, marker=marker, s=120, zorder=5)
        ax5.annotate(f"{src}\n{label_str}\nQty={row['Quantity']:.0f}",
                     (row['Timestamp_utc'], row['Quantity']),
                     textcoords='offset points', xytext=(0, 12),
                     ha='center', fontsize=7.5,
                     arrowprops=dict(arrowstyle='->', color='gray', lw=0.8))

alpha_patch = mpatches.Patch(color='#3498db', label='Alpha WMS')
beta_patch  = mpatches.Patch(color='#e67e22', label='Beta WMS')
ax5.legend(handles=[alpha_patch, beta_patch], fontsize=10)
ax5.set_xlabel('Timestamp (UTC)', fontsize=11)
ax5.set_ylabel('Quantity (units)', fontsize=11)
ax5.set_title('Inventory Snapshot Timeline\n(All Records, Both WMS Systems)', fontsize=13, fontweight='bold')
ax5.yaxis.grid(True, linestyle='--', alpha=0.5)
ax5.set_axisbelow(True)
plt.tight_layout()
plt.savefig('report/images/fig5_timeline.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig5_timeline.png")

print("\n=" * 60)
print("Analysis complete. All outputs saved.")
print("=" * 60)
