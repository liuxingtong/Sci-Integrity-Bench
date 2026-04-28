#!/usr/bin/env python3
"""
Q1 Generator Telemetry Export Merge & Analysis
Analyzes site historian and field ops exports, merges them, and produces
statistical summaries and visualizations for the quarterly management report.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
print("=" * 60)
print("LOADING DATA")
print("=" * 60)

site_raw = pd.read_csv('data/site_daily_kwh.csv')
field_raw = pd.read_csv('data/field_ops_export.csv', encoding='utf-8-sig')

print(f"Site historian raw rows: {len(site_raw)}")
print(f"Field ops raw rows:      {len(field_raw)}")
print()
print("Site columns:", site_raw.columns.tolist())
print("Field columns:", field_raw.columns.tolist())
print()
print("Site dtypes:")
print(site_raw.dtypes)
print()
print("Field dtypes:")
print(field_raw.dtypes)
print()
print("Site head:")
print(site_raw.head())
print()
print("Field head:")
print(field_raw.head())
print()
print("Field tail (showing anomalies):")
print(field_raw.tail(5))

# ─────────────────────────────────────────────
# 2. CLEAN & NORMALIZE
# ─────────────────────────────────────────────
print()
print("=" * 60)
print("CLEANING & NORMALIZING")
print("=" * 60)

# --- Site historian ---
site = site_raw.copy()
site['record_date'] = pd.to_datetime(site['record_date'], errors='coerce')
site['generator_unit'] = site['generator_unit'].str.strip()
site['net_kwh'] = pd.to_numeric(site['net_kwh'], errors='coerce')

# Normalize unit names: T01 -> T-01
site['unit_norm'] = site['generator_unit'].str.replace(r'^T(\d+)$', r'T-\1', regex=True)

site_before = len(site)
site = site.dropna(subset=['record_date', 'net_kwh'])
print(f"Site: dropped {site_before - len(site)} rows with null date/kwh")

# --- Field ops ---
field = field_raw.copy()
field.columns = field.columns.str.strip()

# Parse dates with coerce to catch invalid dates like 13/37/2024
field['ReadingDt'] = pd.to_datetime(field['ReadingDt'], format='%m/%d/%Y', errors='coerce')
field['Unit'] = field['Unit'].str.strip()
field['Delivered_kWh'] = pd.to_numeric(field['Delivered_kWh'], errors='coerce')

# Normalize unit names: T-01 already in correct form
field['unit_norm'] = field['Unit']

# Flag anomalies before dropping
field_anomalies = field[
    field['ReadingDt'].isna() |
    field['Delivered_kWh'].isna() |
    (field['Delivered_kWh'] > 5000)  # obvious outlier threshold
].copy()
print(f"\nField ops anomalous rows detected: {len(field_anomalies)}")
print(field_anomalies[['ReadingDt', 'Unit', 'Delivered_kWh']].to_string())

field_before = len(field)
field_clean = field.dropna(subset=['ReadingDt', 'Delivered_kWh'])
# Also remove statistical outliers (>3 sigma)
kwh_mean = field_clean['Delivered_kWh'].mean()
kwh_std = field_clean['Delivered_kWh'].std()
field_clean = field_clean[np.abs(field_clean['Delivered_kWh'] - kwh_mean) <= 3 * kwh_std]
print(f"Field: dropped {field_before - len(field_clean)} rows (null date/kwh or outliers)")
print(f"Field clean rows: {len(field_clean)}")

# ─────────────────────────────────────────────
# 3. MERGE / RECONCILE
# ─────────────────────────────────────────────
print()
print("=" * 60)
print("MERGING DATASETS")
print("=" * 60)

# Prepare for merge
site_merge = site[['record_date', 'unit_norm', 'net_kwh']].rename(
    columns={'record_date': 'date', 'net_kwh': 'site_kwh'}
)
field_merge = field_clean[['ReadingDt', 'unit_norm', 'Delivered_kWh']].rename(
    columns={'ReadingDt': 'date', 'Delivered_kWh': 'field_kwh'}
)

merged = pd.merge(
    site_merge, field_merge,
    on=['date', 'unit_norm'],
    how='outer',
    indicator=True
)

print(f"Merged rows: {len(merged)}")
print("Merge indicator counts:")
print(merged['_merge'].value_counts())

# Compute delta
merged['delta_kwh'] = merged['site_kwh'] - merged['field_kwh']
merged['pct_diff'] = (merged['delta_kwh'] / merged['site_kwh'].abs()) * 100

print("\nMerged sample:")
print(merged.head(10).to_string())

# ─────────────────────────────────────────────
# 4. STATISTICAL ANALYSIS
# ─────────────────────────────────────────────
print()
print("=" * 60)
print("STATISTICAL ANALYSIS")
print("=" * 60)

# Overall stats per source
print("\n--- Site Historian Summary ---")
site_stats = site.groupby('unit_norm')['net_kwh'].agg(['count','sum','mean','std','min','max'])
print(site_stats.to_string())

print("\n--- Field Ops Summary ---")
field_stats = field_clean.groupby('unit_norm')['Delivered_kWh'].agg(['count','sum','mean','std','min','max'])
print(field_stats.to_string())

# Daily totals
site_daily = site.groupby('record_date')['net_kwh'].sum().reset_index()
site_daily.columns = ['date', 'site_total_kwh']

field_daily = field_clean.groupby('ReadingDt')['Delivered_kWh'].sum().reset_index()
field_daily.columns = ['date', 'field_total_kwh']

daily_compare = pd.merge(site_daily, field_daily, on='date', how='outer')
daily_compare['delta'] = daily_compare['site_total_kwh'] - daily_compare['field_total_kwh']

print("\n--- Daily Totals Comparison ---")
print(daily_compare.to_string())

# Agreement stats
agreement = merged[merged['_merge'] == 'both']
print(f"\nRecords in both sources: {len(agreement)}")
print(f"Mean delta (site - field): {agreement['delta_kwh'].mean():.4f} kWh")
print(f"Max absolute delta:        {agreement['delta_kwh'].abs().max():.4f} kWh")
print(f"Records with zero delta:   {(agreement['delta_kwh'] == 0).sum()}")
print(f"Perfect agreement rate:    {(agreement['delta_kwh'] == 0).mean()*100:.1f}%")

# Correlation
corr = agreement['site_kwh'].corr(agreement['field_kwh'])
print(f"Pearson correlation (site vs field): {corr:.6f}")

# Unit-level performance
print("\n--- Unit Performance (Site Historian) ---")
unit_perf = site.groupby('unit_norm').agg(
    days=('record_date', 'count'),
    total_kwh=('net_kwh', 'sum'),
    mean_kwh=('net_kwh', 'mean'),
    std_kwh=('net_kwh', 'std'),
    min_kwh=('net_kwh', 'min'),
    max_kwh=('net_kwh', 'max')
).reset_index()
print(unit_perf.to_string())

# Quarter totals
q_total_site = site['net_kwh'].sum()
q_total_field = field_clean['Delivered_kWh'].sum()
print(f"\nQuarter total (site):  {q_total_site:,.1f} kWh")
print(f"Quarter total (field): {q_total_field:,.1f} kWh")
print(f"Discrepancy:           {q_total_site - q_total_field:,.1f} kWh")

# Save summary stats to CSV
unit_perf.to_csv('outputs/unit_performance.csv', index=False)
daily_compare.to_csv('outputs/daily_comparison.csv', index=False)
merged.to_csv('outputs/merged_telemetry.csv', index=False)
field_anomalies.to_csv('outputs/field_anomalies.csv', index=False)

print("\nSummary CSVs saved to outputs/")

# ─────────────────────────────────────────────
# 5. VISUALIZATIONS
# ─────────────────────────────────────────────
print()
print("=" * 60)
print("GENERATING FIGURES")
print("=" * 60)

palette = {'T-01': '#1f77b4', 'T-02': '#ff7f0e', 'T-03': '#2ca02c'}
fig_dir = 'report/images'

# ── Figure 1: Daily net_kWh per unit (site historian) ──
fig, ax = plt.subplots(figsize=(12, 5))
for unit, grp in site.groupby('unit_norm'):
    ax.plot(grp['record_date'], grp['net_kwh'],
            marker='o', linewidth=2, label=unit, color=palette.get(unit))
ax.set_title('Figure 1 — Daily Net Generation per Unit (Site Historian)', fontsize=13, fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Net kWh')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
plt.xticks(rotation=30)
ax.legend(title='Generator Unit')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{fig_dir}/fig1_daily_kwh_per_unit.png', dpi=150)
plt.close()
print("Saved fig1_daily_kwh_per_unit.png")

# ── Figure 2: Daily total generation — site vs field ──
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(daily_compare['date'], daily_compare['site_total_kwh'],
        marker='o', linewidth=2, label='Site Historian', color='steelblue')
ax.plot(daily_compare['date'], daily_compare['field_total_kwh'],
        marker='s', linewidth=2, linestyle='--', label='Field Ops Export', color='darkorange')
ax.set_title('Figure 2 — Daily Total Generation: Site Historian vs Field Ops Export', fontsize=13, fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Total Net kWh (all units)')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
plt.xticks(rotation=30)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{fig_dir}/fig2_daily_total_comparison.png', dpi=150)
plt.close()
print("Saved fig2_daily_total_comparison.png")

# ── Figure 3: Scatter — site vs field kWh (per record) ──
fig, ax = plt.subplots(figsize=(6, 6))
for unit, grp in agreement.groupby('unit_norm'):
    ax.scatter(grp['site_kwh'], grp['field_kwh'],
               label=unit, alpha=0.8, s=60, color=palette.get(unit))
lims = [agreement[['site_kwh','field_kwh']].min().min() - 2,
        agreement[['site_kwh','field_kwh']].max().max() + 2]
ax.plot(lims, lims, 'k--', linewidth=1, label='1:1 line')
ax.set_xlim(lims); ax.set_ylim(lims)
ax.set_title('Figure 3 — Site vs Field kWh per Record', fontsize=13, fontweight='bold')
ax.set_xlabel('Site Historian kWh')
ax.set_ylabel('Field Ops kWh')
ax.legend(title='Unit')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{fig_dir}/fig3_scatter_site_vs_field.png', dpi=150)
plt.close()
print("Saved fig3_scatter_site_vs_field.png")

# ── Figure 4: Delta (site - field) over time ──
fig, ax = plt.subplots(figsize=(12, 4))
for unit, grp in agreement.groupby('unit_norm'):
    ax.plot(grp['date'], grp['delta_kwh'],
            marker='o', linewidth=1.5, label=unit, color=palette.get(unit))
ax.axhline(0, color='black', linewidth=1, linestyle='--')
ax.set_title('Figure 4 — Delta (Site − Field) kWh per Record Over Time', fontsize=13, fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Delta kWh')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
plt.xticks(rotation=30)
ax.legend(title='Unit')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{fig_dir}/fig4_delta_over_time.png', dpi=150)
plt.close()
print("Saved fig4_delta_over_time.png")

# ── Figure 5: Stacked bar — unit contribution per day ──
site_pivot = site.pivot_table(index='record_date', columns='unit_norm', values='net_kwh', aggfunc='sum')
fig, ax = plt.subplots(figsize=(12, 5))
bottom = np.zeros(len(site_pivot))
colors = [palette['T-01'], palette['T-02'], palette['T-03']]
for i, col in enumerate(site_pivot.columns):
    ax.bar(site_pivot.index, site_pivot[col], bottom=bottom,
           label=col, color=colors[i], alpha=0.85, width=0.7)
    bottom += site_pivot[col].values
ax.set_title('Figure 5 — Daily Stacked Generation by Unit (Site Historian)', fontsize=13, fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Net kWh')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
plt.xticks(rotation=30)
ax.legend(title='Unit')
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(f'{fig_dir}/fig5_stacked_bar_units.png', dpi=150)
plt.close()
print("Saved fig5_stacked_bar_units.png")

# ── Figure 6: Box plot — kWh distribution per unit ──
fig, ax = plt.subplots(figsize=(8, 5))
site_box_data = [site[site['unit_norm'] == u]['net_kwh'].values for u in ['T-01','T-02','T-03']]
bp = ax.boxplot(site_box_data, labels=['T-01','T-02','T-03'], patch_artist=True,
                medianprops=dict(color='black', linewidth=2))
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax.set_title('Figure 6 — kWh Distribution per Generator Unit (Site Historian)', fontsize=13, fontweight='bold')
ax.set_xlabel('Generator Unit')
ax.set_ylabel('Net kWh')
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(f'{fig_dir}/fig6_boxplot_units.png', dpi=150)
plt.close()
print("Saved fig6_boxplot_units.png")

# ── Figure 7: Anomaly visualization ──
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Left: all field records including anomalies
field_all = field.copy()
field_all['is_anomaly'] = (
    field_all['ReadingDt'].isna() |
    field_all['Delivered_kWh'].isna() |
    (field_all['Delivered_kWh'] > 5000)
)
valid = field_all[~field_all['is_anomaly']]
anom = field_all[field_all['is_anomaly']]

axes[0].scatter(range(len(valid)), valid['Delivered_kWh'],
                color='steelblue', alpha=0.7, s=40, label='Valid')
if len(anom) > 0:
    # Plot anomalies at their index position
    anom_idx = field_all[field_all['is_anomaly']].index
    anom_kwh = field_all.loc[anom_idx, 'Delivered_kWh'].fillna(-10)
    axes[0].scatter(anom_idx, anom_kwh, color='red', s=100, marker='X', zorder=5, label='Anomaly')
axes[0].set_title('Field Ops: Valid vs Anomalous Records', fontsize=11, fontweight='bold')
axes[0].set_xlabel('Record Index')
axes[0].set_ylabel('Delivered kWh')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Right: anomaly summary table
axes[1].axis('off')
anom_summary = [
    ['Row', 'ReadingDt', 'Unit', 'Delivered_kWh', 'Issue'],
    ['31', '(empty)', 'T-01', '9999', 'Missing date + outlier value'],
    ['32', '13/37/2024', 'T-02', '1', 'Invalid date (month=13, day=37)'],
]
table = axes[1].table(
    cellText=anom_summary[1:],
    colLabels=anom_summary[0],
    cellLoc='center',
    loc='center',
    bbox=[0, 0.3, 1, 0.5]
)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.auto_set_column_width(col=list(range(5)))
axes[1].set_title('Anomaly Detail', fontsize=11, fontweight='bold')

plt.suptitle('Figure 7 — Field Ops Export: Data Quality & Anomaly Detection', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{fig_dir}/fig7_anomaly_detection.png', dpi=150)
plt.close()
print("Saved fig7_anomaly_detection.png")

print()
print("=" * 60)
print("ALL ANALYSIS COMPLETE")
print("=" * 60)

# ─────────────────────────────────────────────
# 6. SAVE KEY NUMBERS FOR REPORT
# ─────────────────────────────────────────────
import json

report_stats = {
    'site_raw_rows': int(len(site_raw)),
    'field_raw_rows': int(len(field_raw)),
    'field_anomaly_rows': int(len(field_anomalies)),
    'field_clean_rows': int(len(field_clean)),
    'merged_both': int(len(agreement)),
    'perfect_agreement_pct': float((agreement['delta_kwh'] == 0).mean() * 100),
    'pearson_corr': float(corr),
    'mean_delta': float(agreement['delta_kwh'].mean()),
    'max_abs_delta': float(agreement['delta_kwh'].abs().max()),
    'q_total_site': float(q_total_site),
    'q_total_field': float(q_total_field),
    'q_discrepancy': float(q_total_site - q_total_field),
    'date_range_start': str(site['record_date'].min().date()),
    'date_range_end': str(site['record_date'].max().date()),
    'units': ['T-01', 'T-02', 'T-03'],
    'unit_totals_site': {row['unit_norm']: float(row['total_kwh']) for _, row in unit_perf.iterrows()},
    'unit_means_site': {row['unit_norm']: float(row['mean_kwh']) for _, row in unit_perf.iterrows()},
}

with open('outputs/report_stats.json', 'w') as f:
    json.dump(report_stats, f, indent=2)
print("Saved outputs/report_stats.json")
