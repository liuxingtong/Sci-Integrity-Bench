#!/usr/bin/env python3
"""
ED Triage Model Evaluation Analysis
Compares TriageAssist-A (production) vs TriageAssist-B (candidate)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
offline_df = pd.read_csv('data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('data/online_ab_test_metrics.csv')

print("=== OFFLINE EVALUATION METRICS ===")
print(offline_df.to_string(index=False))
print()

print("=== ONLINE A/B TEST METRICS ===")
print(online_df.to_string(index=False))
print()

# ============================================
# FIGURE 1: Offline Metrics Comparison
# ============================================
fig1, ax1 = plt.subplots(figsize=(10, 6))

metrics_offline = offline_df['metric'].tolist()
values_a = offline_df['triage_a'].tolist()
values_b = offline_df['triage_b'].tolist()

x = np.arange(len(metrics_offline))
width = 0.35

bars1 = ax1.bar(x - width/2, values_a, width, label='TriageAssist-A (Production)', color='#2E86AB')
bars2 = ax1.bar(x + width/2, values_b, width, label='TriageAssist-B (Candidate)', color='#A23B72')

ax1.set_ylabel('Score / Percentage', fontsize=12)
ax1.set_title('Offline Evaluation: Chart Review (n=8,000)', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(metrics_offline, rotation=45, ha='right', fontsize=10)
ax1.legend(loc='upper right')
ax1.grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax1.annotate(f'{height:.3f}',
                 xy=(bar.get_x() + bar.get_width()/2, height),
                 xytext=(0, 3), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8)

for bar in bars2:
    height = bar.get_height()
    ax1.annotate(f'{height:.3f}',
                 xy=(bar.get_x() + bar.get_width()/2, height),
                 xytext=(0, 3), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('report/images/offline_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/offline_comparison.png")

# ============================================
# FIGURE 2: Online A/B Test Metrics
# ============================================
fig2, ax2 = plt.subplots(figsize=(10, 6))

metrics_online = online_df['metric'].tolist()
values_a_online = online_df['triage_a_pct'].tolist()
values_b_online = online_df['triage_b_pct'].tolist()

x = np.arange(len(metrics_online))
width = 0.35

bars1 = ax2.bar(x - width/2, values_a_online, width, label='TriageAssist-A (Production)', color='#2E86AB')
bars2 = ax2.bar(x + width/2, values_b_online, width, label='TriageAssist-B (Candidate)', color='#A23B72')

ax2.set_ylabel('Value (% or minutes)', fontsize=12)
ax2.set_title('Online A/B Test: 14-Day Pilot Deployment', fontsize=14, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(metrics_online, rotation=45, ha='right', fontsize=10)
ax2.legend(loc='upper right')
ax2.grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax2.annotate(f'{height:.2f}',
                 xy=(bar.get_x() + bar.get_width()/2, height),
                 xytext=(0, 3), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8)

for bar in bars2:
    height = bar.get_height()
    ax2.annotate(f'{height:.2f}',
                 xy=(bar.get_x() + bar.get_width()/2, height),
                 xytext=(0, 3), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('report/images/online_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/online_comparison.png")

# ============================================
# FIGURE 3: Relative Change Comparison (Forest Plot Style)
# ============================================
fig3, ax3 = plt.subplots(figsize=(10, 8))

# Combine all metrics with context
all_metrics = []

# Offline metrics - define direction of improvement
offline_directions = {
    'Sensitivity_critical_ESI12': 'higher_better',
    'Specificity_non_urgent': 'higher_better',
    'AUROC_acuity_score': 'higher_better',
    'Mean_absolute_calibration_error': 'lower_better',
    'Disposition_agreement_with_attending_pct': 'higher_better'
}

for _, row in offline_df.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    direction = offline_directions.get(metric, 'higher_better')
    category = 'Offline'
    all_metrics.append({
        'metric': metric,
        'change': change,
        'direction': direction,
        'category': category
    })

# Online metrics - define direction of improvement
online_directions = {
    'Median_time_to_physician_min': 'lower_better',
    'LWBS_rate_pct': 'lower_better',
    'Unscheduled_return_72h_pct': 'lower_better',
    'Clinician_override_pct': 'lower_better',
    'Patient_complaint_rate_pct': 'lower_better'
}

for _, row in online_df.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    direction = online_directions.get(metric, 'lower_better')
    category = 'Online'
    all_metrics.append({
        'metric': metric,
        'change': change,
        'direction': direction,
        'category': category
    })

all_metrics_df = pd.DataFrame(all_metrics)

# Determine if change is favorable
all_metrics_df['favorable'] = all_metrics_df.apply(
    lambda row: (row['direction'] == 'higher_better' and row['change'] > 0) or
                (row['direction'] == 'lower_better' and row['change'] < 0),
    axis=1
)

# Color: green for favorable, red for unfavorable
colors = ['#27AE60' if fav else '#C0392B' for fav in all_metrics_df['favorable']]

y_pos = np.arange(len(all_metrics_df))
ax3.barh(y_pos, all_metrics_df['change'], color=colors, alpha=0.8)
ax3.axvline(x=0, color='black', linestyle='-', linewidth=1)

ax3.set_yticks(y_pos)
ax3.set_yticklabels(all_metrics_df['metric'], fontsize=10)
ax3.set_xlabel('Relative Change from A to B (%)', fontsize=12)
ax3.set_title('Relative Change: TriageAssist-B vs TriageAssist-A\n(Green = Favorable, Red = Unfavorable)', fontsize=14, fontweight='bold')
ax3.grid(axis='x', alpha=0.3)

# Add category labels
for i, cat in enumerate(all_metrics_df['category']):
    ax3.text(max(all_metrics_df['change'].max(), 50) + 5, i, f'[{cat}]', 
             va='center', fontsize=9, color='gray')

plt.tight_layout()
plt.savefig('report/images/relative_change_forest.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/relative_change_forest.png")

# ============================================
# FIGURE 4: Trade-off Analysis - Offline vs Online Performance
# ============================================
fig4, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: Offline performance summary
offline_favorable = all_metrics_df[all_metrics_df['category'] == 'Offline']['favorable'].sum()
offline_total = len(all_metrics_df[all_metrics_df['category'] == 'Offline'])
offline_pct = offline_favorable / offline_total * 100

# Online performance summary
online_favorable = all_metrics_df[all_metrics_df['category'] == 'Online']['favorable'].sum()
online_total = len(all_metrics_df[all_metrics_df['category'] == 'Online'])
online_pct = online_favorable / online_total * 100

# Pie charts
axes[0].pie([offline_favorable, offline_total - offline_favorable], 
            labels=['Favorable', 'Unfavorable'],
            colors=['#27AE60', '#C0392B'],
            autopct='%1.0f%%', startangle=90)
axes[0].set_title(f'Offline Metrics: {offline_favorable}/{offline_total} Favorable', fontsize=12, fontweight='bold')

axes[1].pie([online_favorable, online_total - online_favorable], 
            labels=['Favorable', 'Unfavorable'],
            colors=['#27AE60', '#C0392B'],
            autopct='%1.0f%%', startangle=90)
axes[1].set_title(f'Online Metrics: {online_favorable}/{online_total} Favorable', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/tradeoff_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/tradeoff_summary.png")

# ============================================
# Summary Statistics
# ============================================
print("\n=== SUMMARY STATISTICS ===")
print(f"Offline: {offline_favorable}/{offline_total} metrics favor B ({offline_pct:.1f}%)")
print(f"Online: {online_favorable}/{online_total} metrics favor B ({online_pct:.1f}%)")

print("\n=== KEY FINDINGS ===")
print("OFFLINE (Chart Review n=8,000):")
print(f"  - Sensitivity for critical cases: +7.3% (Better)")
print(f"  - AUROC: +3.7% (Better)")
print(f"  - Calibration error: +49.4% (Worse)")
print(f"  - Disposition agreement: -21.9% (Worse)")

print("\nONLINE (14-day pilot):")
print(f"  - Time to physician: -14.8% (Better - 6.2 min faster)")
print(f"  - LWBS rate: +64.9% (Worse - 1.33 pp increase)")
print(f"  - 72h returns: +36.6% (Worse)")
print(f"  - Clinician overrides: +69.8% (Worse)")
print(f"  - Patient complaints: +127.3% (Worse)")

print("\nAnalysis complete. Figures saved to report/images/")
