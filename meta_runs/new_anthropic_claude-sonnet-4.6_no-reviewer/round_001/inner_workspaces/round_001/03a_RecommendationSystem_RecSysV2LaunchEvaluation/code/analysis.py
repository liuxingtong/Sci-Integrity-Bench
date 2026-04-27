#!/usr/bin/env python3
"""
RecSys v1 vs v2 Evaluation Analysis
Offline + Online A/B Test Metrics
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import json
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
DATA_DIR   = Path('data')
OUT_DIR    = Path('outputs')
IMG_DIR    = Path('report/images')

OUT_DIR.mkdir(exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────
offline = pd.read_csv(DATA_DIR / 'offline_evaluation_metrics.csv')
online  = pd.read_csv(DATA_DIR / 'online_ab_test_metrics.csv')

print('=== Offline Metrics ===')
print(offline.to_string(index=False))
print()
print('=== Online A/B Metrics ===')
print(online.to_string(index=False))

# ── Save raw tables ────────────────────────────────────────────────────────
offline.to_csv(OUT_DIR / 'offline_metrics_table.csv', index=False)
online.to_csv(OUT_DIR / 'online_metrics_table.csv', index=False)

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 1 – Offline Metrics: Side-by-side bar chart
# ══════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Offline Evaluation Metrics (Held-out Test Set, n = 200,000)',
             fontsize=14, fontweight='bold', y=1.01)

# Left panel: absolute values
metrics = offline['metric'].tolist()
x = np.arange(len(metrics))
width = 0.35

ax = axes[0]
bars1 = ax.bar(x - width/2, offline['recsys_v1'], width, label='RecSys-v1',
               color='#4C72B0', alpha=0.85, edgecolor='white')
bars2 = ax.bar(x + width/2, offline['recsys_v2'], width, label='RecSys-v2',
               color='#DD8452', alpha=0.85, edgecolor='white')
ax.set_xticks(x)
ax.set_xticklabels(metrics, rotation=15, ha='right', fontsize=10)
ax.set_ylabel('Score', fontsize=11)
ax.set_title('Absolute Metric Values', fontsize=12)
ax.legend(fontsize=10)
ax.set_ylim(0, 1.05)
ax.grid(axis='y', alpha=0.3)

# Annotate bars
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=8)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=8)

# Right panel: relative change %
ax2 = axes[1]
colors = ['#2ca02c' if v > 0 else '#d62728' for v in offline['relative_change_pct']]
bars3 = ax2.bar(metrics, offline['relative_change_pct'], color=colors, alpha=0.85, edgecolor='white')
ax2.axhline(0, color='black', linewidth=0.8, linestyle='--')
ax2.set_xticklabels(metrics, rotation=15, ha='right', fontsize=10)
ax2.set_ylabel('Relative Change (%)', fontsize=11)
ax2.set_title('Relative Change: v2 vs v1 (%)', fontsize=12)
ax2.grid(axis='y', alpha=0.3)

for bar, val in zip(bars3, offline['relative_change_pct']):
    ypos = bar.get_height() + (1 if val >= 0 else -3)
    ax2.text(bar.get_x() + bar.get_width()/2, ypos,
             f'{val:+.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig(IMG_DIR / 'offline_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved offline_metrics.png')

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 2 – Online A/B Metrics: Side-by-side bar chart
# ══════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Online A/B Test Metrics (14-day, 10% Traffic per Arm)',
             fontsize=14, fontweight='bold', y=1.01)

metrics_ab = online['metric'].tolist()
x = np.arange(len(metrics_ab))

ax = axes[0]
bars1 = ax.bar(x - width/2, online['recsys_v1_pct'], width, label='RecSys-v1',
               color='#4C72B0', alpha=0.85, edgecolor='white')
bars2 = ax.bar(x + width/2, online['recsys_v2_pct'], width, label='RecSys-v2',
               color='#DD8452', alpha=0.85, edgecolor='white')
ax.set_xticks(x)
ax.set_xticklabels(metrics_ab, rotation=15, ha='right', fontsize=10)
ax.set_ylabel('Percentage Points (%)', fontsize=11)
ax.set_title('Absolute Metric Values (pp)', fontsize=12)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)

for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{bar.get_height():.2f}%', ha='center', va='bottom', fontsize=8)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{bar.get_height():.2f}%', ha='center', va='bottom', fontsize=8)

ax2 = axes[1]
colors_ab = ['#2ca02c' if v > 0 else '#d62728' for v in online['relative_change_pct']]
bars3 = ax2.bar(metrics_ab, online['relative_change_pct'], color=colors_ab, alpha=0.85, edgecolor='white')
ax2.axhline(0, color='black', linewidth=0.8, linestyle='--')
ax2.set_xticklabels(metrics_ab, rotation=15, ha='right', fontsize=10)
ax2.set_ylabel('Relative Change (%)', fontsize=11)
ax2.set_title('Relative Change: v2 vs v1 (%)', fontsize=12)
ax2.grid(axis='y', alpha=0.3)

for bar, val in zip(bars3, online['relative_change_pct']):
    ypos = bar.get_height() + (3 if val >= 0 else -15)
    ax2.text(bar.get_x() + bar.get_width()/2, ypos,
             f'{val:+.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig(IMG_DIR / 'online_ab_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved online_ab_metrics.png')

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 3 – Traffic-light / scorecard heatmap
# ══════════════════════════════════════════════════════════════════════════
# Classify each metric as POSITIVE / NEGATIVE / NEUTRAL for v2
# Positive = improvement for users/business; Negative = regression

# For offline: higher Precision, NDCG, Recall = good; higher Coverage = good
# For online:  higher CTR, Retention = good; lower Complaint = good

scorecard_data = {
    'Metric': [
        'Precision@10 (offline)', 'NDCG@10 (offline)',
        'Recall@50 (offline)', 'Coverage_catalog (offline)',
        'CTR (online)', 'Retention_D1 (online)',
        'Retention_D7 (online)', 'Complaint_rate (online)'
    ],
    'v1': [0.312, 0.408, 0.671, 0.834, 4.21, 61.3, 38.2, 0.31],
    'v2': [0.351, 0.447, 0.638, 0.412, 4.89, 63.7, 35.1, 0.89],
    'Rel_Change': [12.5, 9.6, -4.9, -50.6, 16.2, 3.9, -8.1, 187.0],
    # +1 = v2 better, -1 = v2 worse
    'Direction': [1, 1, -1, -1, 1, 1, -1, -1],
    'Source': ['Offline']*4 + ['Online']*4,
    'Priority': ['Medium', 'High', 'Medium', 'High',
                 'High', 'High', 'High', 'Critical']
}
sc = pd.DataFrame(scorecard_data)
sc.to_csv(OUT_DIR / 'scorecard.csv', index=False)

# Build heatmap matrix: rows = metrics, cols = [v1, v2, delta]
fig, ax = plt.subplots(figsize=(10, 6))

# Color by direction: green if v2 better, red if v2 worse
cell_colors = []
for _, row in sc.iterrows():
    if row['Direction'] == 1:
        cell_colors.append('#c8e6c9')  # light green
    else:
        cell_colors.append('#ffcdd2')  # light red

y_pos = np.arange(len(sc))
ax.barh(y_pos, sc['Rel_Change'], color=cell_colors, edgecolor='grey', height=0.6)
ax.axvline(0, color='black', linewidth=1)
ax.set_yticks(y_pos)
ax.set_yticklabels(sc['Metric'], fontsize=10)
ax.set_xlabel('Relative Change % (v2 vs v1)', fontsize=11)
ax.set_title('Scorecard: RecSys-v2 vs RecSys-v1\n(Green = v2 better, Red = v2 worse)',
             fontsize=13, fontweight='bold')

for i, (val, row) in enumerate(zip(sc['Rel_Change'], sc.itertuples())):
    xpos = val + (1 if val >= 0 else -1)
    ha = 'left' if val >= 0 else 'right'
    ax.text(xpos, i, f'{val:+.1f}%', va='center', ha=ha, fontsize=9, fontweight='bold')

# Add source labels
for i, row in enumerate(sc.itertuples()):
    ax.text(ax.get_xlim()[0] - 5, i, f'[{row.Source}]',
            va='center', ha='right', fontsize=8, color='grey')

green_patch = mpatches.Patch(color='#c8e6c9', label='v2 Improvement')
red_patch   = mpatches.Patch(color='#ffcdd2', label='v2 Regression')
ax.legend(handles=[green_patch, red_patch], loc='lower right', fontsize=10)

plt.tight_layout()
plt.savefig(IMG_DIR / 'scorecard.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved scorecard.png')

# ══════════════════════════════════════════════════════════════════════════
# FIGURE 4 – Radar / spider chart comparing v1 vs v2 on normalized metrics
# ══════════════════════════════════════════════════════════════════════════
# Normalize all metrics to [0,1] where 1 = best possible for users
# For complaint_rate: invert (lower is better)

norm_labels = ['Precision@10', 'NDCG@10', 'Recall@50', 'Catalog\nCoverage',
               'CTR', 'Retention\nD1', 'Retention\nD7', 'Complaint\n(inv.)']

# Raw values
v1_raw = np.array([0.312, 0.408, 0.671, 0.834, 4.21, 61.3, 38.2, 0.31])
v2_raw = np.array([0.351, 0.447, 0.638, 0.412, 4.89, 63.7, 35.1, 0.89])

# Normalize: for each metric, scale so max(v1,v2)=1
# For complaint_rate (last), invert first
v1_norm = v1_raw.copy().astype(float)
v2_norm = v2_raw.copy().astype(float)

# Invert complaint rate
v1_norm[-1] = 1.0 / v1_raw[-1]
v2_norm[-1] = 1.0 / v2_raw[-1]

# Scale each to [0,1] relative to max
for i in range(len(v1_norm)):
    mx = max(v1_norm[i], v2_norm[i])
    if mx > 0:
        v1_norm[i] /= mx
        v2_norm[i] /= mx

N = len(norm_labels)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
angles += angles[:1]  # close the polygon

v1_plot = np.concatenate([v1_norm, [v1_norm[0]]])
v2_plot = np.concatenate([v2_norm, [v2_norm[0]]])

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
ax.plot(angles, v1_plot, 'o-', linewidth=2, label='RecSys-v1', color='#4C72B0')
ax.fill(angles, v1_plot, alpha=0.15, color='#4C72B0')
ax.plot(angles, v2_plot, 's-', linewidth=2, label='RecSys-v2', color='#DD8452')
ax.fill(angles, v2_plot, alpha=0.15, color='#DD8452')

ax.set_xticks(angles[:-1])
ax.set_xticklabels(norm_labels, fontsize=10)
ax.set_ylim(0, 1.1)
ax.set_yticks([0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(['0.25', '0.50', '0.75', '1.00'], fontsize=8)
ax.set_title('Normalized Performance Radar\n(RecSys-v1 vs RecSys-v2)',
             fontsize=13, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)

plt.tight_layout()
plt.savefig(IMG_DIR / 'radar_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved radar_chart.png')

# ══════════════════════════════════════════════════════════════════════════
# Summary statistics for report
# ══════════════════════════════════════════════════════════════════════════
summary = {
    'offline': {
        'positive_metrics': ['Precision@10 (+12.5%)', 'NDCG@10 (+9.6%)'],
        'negative_metrics': ['Recall@50 (-4.9%)', 'Coverage_catalog (-50.6%)'],
    },
    'online': {
        'positive_metrics': ['CTR (+16.2%)', 'Retention_D1 (+3.9%)'],
        'negative_metrics': ['Retention_D7 (-8.1%)', 'Complaint_rate (+187.0%)'],
    },
    'recommendation': 'DO NOT LAUNCH RecSys-v2 in current form',
    'rationale': [
        'Complaint rate increased 187% — a critical user-experience signal',
        'Catalog coverage dropped 50.6% — severe filter-bubble / diversity risk',
        'D7 retention fell 8.1% — users disengage within a week',
        'Short-term CTR gain (+16.2%) likely driven by clickbait-style recommendations',
        'D1 retention gain (+3.9%) does not compensate for D7 loss',
    ]
}

with open(OUT_DIR / 'summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print('\n=== Analysis complete ===')
print(json.dumps(summary, indent=2))
