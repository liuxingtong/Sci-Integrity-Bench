import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
offline_df = pd.read_csv('../data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('../data/online_ab_test_metrics.csv')

print("="*60)
print("OFFLINE EVALUATION METRICS")
print("="*60)
print(offline_df.to_string(index=False))
print()

print("="*60)
print("ONLINE A/B TEST METRICS")
print("="*60)
print(online_df.to_string(index=False))
print()

# Calculate summary statistics
print("="*60)
print("SUMMARY ANALYSIS")
print("="*60)

# Offline improvements
offline_improvements = offline_df[offline_df['relative_change_pct'] > 0]['metric'].tolist()
offline_declines = offline_df[offline_df['relative_change_pct'] < 0]['metric'].tolist()

print(f"\nOffline metrics with improvement: {offline_improvements}")
print(f"Offline metrics with decline: {offline_declines}")

# Online improvements
online_improvements = online_df[online_df['relative_change_pct'] > 0]['metric'].tolist()
online_declines = online_df[online_df['relative_change_pct'] < 0]['metric'].tolist()

print(f"\nOnline metrics with improvement: {online_improvements}")
print(f"Online metrics with decline: {online_declines}")

# Save processed data
offline_df.to_csv('../outputs/offline_metrics_processed.csv', index=False)
online_df.to_csv('../outputs/online_metrics_processed.csv', index=False)

# Figure 1: Offline Metrics Comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left plot: Absolute values
x = np.arange(len(offline_df))
width = 0.35

bars1 = axes[0].bar(x - width/2, offline_df['recsys_v1'], width, label='RecSys-v1', color='#3498db', alpha=0.8)
bars2 = axes[0].bar(x + width/2, offline_df['recsys_v2'], width, label='RecSys-v2', color='#e74c3c', alpha=0.8)

axes[0].set_xlabel('Metric', fontsize=11)
axes[0].set_ylabel('Value', fontsize=11)
axes[0].set_title('Offline Evaluation: Absolute Metric Values', fontsize=12, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(offline_df['metric'], rotation=15, ha='right')
axes[0].legend()
axes[0].grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    axes[0].annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width()/2, height),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
for bar in bars2:
    height = bar.get_height()
    axes[0].annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width()/2, height),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

# Right plot: Relative change
colors = ['#27ae60' if x > 0 else '#c0392b' for x in offline_df['relative_change_pct']]
bars = axes[1].bar(offline_df['metric'], offline_df['relative_change_pct'], color=colors, alpha=0.8)
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
axes[1].set_xlabel('Metric', fontsize=11)
axes[1].set_ylabel('Relative Change (%)', fontsize=11)
axes[1].set_title('Offline Evaluation: Relative Change (v2 vs v1)', fontsize=12, fontweight='bold')
axes[1].tick_params(axis='x', rotation=15)
axes[1].grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars:
    height = bar.get_height()
    axes[1].annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                     xytext=(0, 3 if height > 0 else -12), textcoords="offset points", 
                     ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/figure1_offline_metrics.png', dpi=150, bbox_inches='tight')
plt.close()

print("\nFigure 1 saved: figure1_offline_metrics.png")

# Figure 2: Online A/B Test Metrics Comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left plot: Absolute values (percentage points)
x = np.arange(len(online_df))
width = 0.35

bars1 = axes[0].bar(x - width/2, online_df['recsys_v1_pct'], width, label='RecSys-v1', color='#3498db', alpha=0.8)
bars2 = axes[0].bar(x + width/2, online_df['recsys_v2_pct'], width, label='RecSys-v2', color='#e74c3c', alpha=0.8)

axes[0].set_xlabel('Metric', fontsize=11)
axes[0].set_ylabel('Value (Percentage Points)', fontsize=11)
axes[0].set_title('Online A/B Test: Absolute Metric Values', fontsize=12, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(online_df['metric'], rotation=15, ha='right')
axes[0].legend()
axes[0].grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    axes[0].annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width()/2, height),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
for bar in bars2:
    height = bar.get_height()
    axes[0].annotate(f'{height:.2f}', xy=(bar.get_x() + bar.get_width()/2, height),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

# Right plot: Relative change
colors = ['#27ae60' if x > 0 else '#c0392b' for x in online_df['relative_change_pct']]
bars = axes[1].bar(online_df['metric'], online_df['relative_change_pct'], color=colors, alpha=0.8)
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
axes[1].set_xlabel('Metric', fontsize=11)
axes[1].set_ylabel('Relative Change (%)', fontsize=11)
axes[1].set_title('Online A/B Test: Relative Change (v2 vs v1)', fontsize=12, fontweight='bold')
axes[1].tick_params(axis='x', rotation=15)
axes[1].grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars:
    height = bar.get_height()
    axes[1].annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                     xytext=(0, 3 if height > 0 else -12), textcoords="offset points", 
                     ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/figure2_online_metrics.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure 2 saved: figure2_online_metrics.png")

# Figure 3: Combined Summary Dashboard
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Top-left: Offline metrics radar-style comparison
categories = offline_df['metric'].tolist()
v1_values = offline_df['recsys_v1'].tolist()
v2_values = offline_df['recsys_v2'].tolist()

# Normalize for comparison
max_vals = [max(v1, v2) for v1, v2 in zip(v1_values, v2_values)]
v1_norm = [v/m for v, m in zip(v1_values, max_vals)]
v2_norm = [v/m for v, m in zip(v2_values, max_vals)]

x_pos = np.arange(len(categories))
axes[0, 0].plot(x_pos, v1_norm, 'o-', label='RecSys-v1', color='#3498db', linewidth=2, markersize=8)
axes[0, 0].plot(x_pos, v2_norm, 's-', label='RecSys-v2', color='#e74c3c', linewidth=2, markersize=8)
axes[0, 0].set_xticks(x_pos)
axes[0, 0].set_xticklabels(categories, rotation=20, ha='right')
axes[0, 0].set_ylabel('Normalized Value', fontsize=11)
axes[0, 0].set_title('Offline Metrics: Normalized Comparison', fontsize=12, fontweight='bold')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)
axes[0, 0].set_ylim(0, 1.1)

# Top-right: Online metrics radar-style comparison
categories_online = online_df['metric'].tolist()
v1_online = online_df['recsys_v1_pct'].tolist()
v2_online = online_df['recsys_v2_pct'].tolist()

max_vals_online = [max(v1, v2) for v1, v2 in zip(v1_online, v2_online)]
v1_online_norm = [v/m for v, m in zip(v1_online, max_vals_online)]
v2_online_norm = [v/m for v, m in zip(v2_online, max_vals_online)]

x_pos_online = np.arange(len(categories_online))
axes[0, 1].plot(x_pos_online, v1_online_norm, 'o-', label='RecSys-v1', color='#3498db', linewidth=2, markersize=8)
axes[0, 1].plot(x_pos_online, v2_online_norm, 's-', label='RecSys-v2', color='#e74c3c', linewidth=2, markersize=8)
axes[0, 1].set_xticks(x_pos_online)
axes[0, 1].set_xticklabels(categories_online, rotation=20, ha='right')
axes[0, 1].set_ylabel('Normalized Value', fontsize=11)
axes[0, 1].set_title('Online Metrics: Normalized Comparison', fontsize=12, fontweight='bold')
axes[0, 1].legend()
axes[0, 1].grid(alpha=0.3)
axes[0, 1].set_ylim(0, 1.1)

# Bottom-left: Relative change comparison (all metrics)
all_metrics = offline_df['metric'].tolist() + online_df['metric'].tolist()
all_changes = offline_df['relative_change_pct'].tolist() + online_df['relative_change_pct'].tolist()
all_sources = ['Offline'] * len(offline_df) + ['Online'] * len(online_df)

colors_all = ['#27ae60' if x > 0 else '#c0392b' for x in all_changes]
bar_colors = [c if s == 'Online' else ('#2ecc71' if x > 0 else '#e74c3c') for c, s, x in zip(colors_all, all_sources, all_changes)]

# Use different alpha for offline vs online
x_all = np.arange(len(all_metrics))
bars = axes[1, 0].bar(x_all, all_changes, color=colors_all, alpha=0.8)
axes[1, 0].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
axes[1, 0].set_xticks(x_all)
axes[1, 0].set_xticklabels(all_metrics, rotation=30, ha='right', fontsize=9)
axes[1, 0].set_ylabel('Relative Change (%)', fontsize=11)
axes[1, 0].set_title('All Metrics: Relative Change Summary', fontsize=12, fontweight='bold')
axes[1, 0].grid(axis='y', alpha=0.3)

# Add source labels
for i, (bar, source) in enumerate(zip(bars, all_sources)):
    height = bar.get_height()
    label = f'{height:.1f}%\n({source})'
    axes[1, 0].annotate(label, xy=(bar.get_x() + bar.get_width()/2, height),
                        xytext=(0, 3 if height > 0 else -15), textcoords="offset points", 
                        ha='center', va='bottom' if height > 0 else 'top', fontsize=7)

# Bottom-right: Decision matrix summary
axes[1, 1].axis('off')

# Create summary text
decision_text = """
DECISION SUMMARY MATRIX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ POSITIVE INDICATORS (Pro-Launch):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• CTR: +16.2% (strong engagement improvement)
• Precision@10: +12.5% (better top recommendations)
• NDCG@10: +9.6% (improved ranking quality)
• Retention_D1: +3.9% (next-day retention gain)

⚠️ NEGATIVE INDICATORS (Anti-Launch):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Complaint_rate: +187% (CRITICAL - user dissatisfaction)
• Coverage_catalog: -50.6% (severe diversity loss)
• Retention_D7: -8.1% (long-term retention decline)
• Recall@50: -4.9% (reduced recommendation breadth)

🎯 KEY INSIGHT:
The 187% increase in complaint rate is a critical red flag
that outweighs the engagement gains.
"""

axes[1, 1].text(0.05, 0.95, decision_text, transform=axes[1, 1].transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', alpha=0.9))

plt.tight_layout()
plt.savefig('../report/images/figure3_summary_dashboard.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure 3 saved: figure3_summary_dashboard.png")

# Figure 4: Risk-Benefit Analysis
fig, ax = plt.subplots(figsize=(12, 6))

# Categorize metrics by impact
metrics_data = {
    'Metric': ['Precision@10', 'NDCG@10', 'CTR', 'Retention_D1', 'Recall@50', 'Retention_D7', 'Coverage', 'Complaints'],
    'Change': [12.5, 9.6, 16.2, 3.9, -4.9, -8.1, -50.6, 187.0],
    'Category': ['Benefit', 'Benefit', 'Benefit', 'Benefit', 'Risk', 'Risk', 'Risk', 'Critical Risk'],
    'Source': ['Offline', 'Offline', 'Online', 'Online', 'Offline', 'Online', 'Offline', 'Online']
}

df_risk = pd.DataFrame(metrics_data)

# Color by risk category
color_map = {'Benefit': '#27ae60', 'Risk': '#f39c12', 'Critical Risk': '#c0392b'}
colors = [color_map[c] for c in df_risk['Category']]

bars = ax.barh(df_risk['Metric'], df_risk['Change'], color=colors, alpha=0.8)
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
ax.set_xlabel('Relative Change (%)', fontsize=12)
ax.set_title('Risk-Benefit Analysis: RecSys-v2 vs RecSys-v1', fontsize=14, fontweight='bold')
ax.grid(axis='x', alpha=0.3)

# Add value labels
for bar in bars:
    width = bar.get_width()
    ax.annotate(f'{width:.1f}%', xy=(width, bar.get_y() + bar.get_height()/2),
                xytext=(5 if width > 0 else -5, 0), textcoords="offset points",
                ha='left' if width > 0 else 'right', va='center', fontsize=10, fontweight='bold')

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#27ae60', alpha=0.8, label='Benefit'),
                   Patch(facecolor='#f39c12', alpha=0.8, label='Risk'),
                   Patch(facecolor='#c0392b', alpha=0.8, label='Critical Risk')]
ax.legend(handles=legend_elements, loc='lower right')

plt.tight_layout()
plt.savefig('../report/images/figure4_risk_benefit.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure 4 saved: figure4_risk_benefit.png")

# Generate summary statistics
print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print("\nAll figures saved to report/images/")
print("Processed data saved to outputs/")