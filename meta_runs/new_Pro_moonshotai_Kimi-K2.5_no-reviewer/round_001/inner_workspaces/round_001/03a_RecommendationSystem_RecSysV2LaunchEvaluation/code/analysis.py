"""
RecSys V2 Launch Evaluation Analysis
=====================================
This script analyzes offline and online metrics to recommend whether to launch RecSys-v2.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
print("Loading data...")
offline_df = pd.read_csv('data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('data/online_ab_test_metrics.csv')

print("\n=== OFFLINE EVALUATION METRICS ===")
print(offline_df.to_string(index=False))

print("\n=== ONLINE A/B TEST METRICS ===")
print(online_df.to_string(index=False))

# Save processed data
offline_df.to_csv('outputs/offline_metrics_processed.csv', index=False)
online_df.to_csv('outputs/online_metrics_processed.csv', index=False)

# Create visualization 1: Offline metrics comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Left plot: Absolute values
metrics = offline_df['metric'].values
v1_values = offline_df['recsys_v1'].values
v2_values = offline_df['recsys_v2'].values

x = np.arange(len(metrics))
width = 0.35

bars1 = axes[0].bar(x - width/2, v1_values, width, label='RecSys-v1', color='#3498db', edgecolor='black', linewidth=0.5)
bars2 = axes[0].bar(x + width/2, v2_values, width, label='RecSys-v2', color='#e74c3c', edgecolor='black', linewidth=0.5)

axes[0].set_xlabel('Metric', fontsize=11)
axes[0].set_ylabel('Score', fontsize=11)
axes[0].set_title('Offline Evaluation: Absolute Scores', fontsize=12, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(metrics, rotation=45, ha='right')
axes[0].legend(loc='upper right')
axes[0].set_ylim(0, max(max(v1_values), max(v2_values)) * 1.15)

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    axes[0].annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)
for bar in bars2:
    height = bar.get_height()
    axes[0].annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

# Right plot: Relative change
changes = offline_df['relative_change_pct'].values
colors = ['#2ecc71' if c > 0 else '#e74c3c' for c in changes]
bars3 = axes[1].bar(metrics, changes, color=colors, edgecolor='black', linewidth=0.5)
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
axes[1].set_xlabel('Metric', fontsize=11)
axes[1].set_ylabel('Relative Change (%)', fontsize=11)
axes[1].set_title('Offline Evaluation: Relative Change (v2 vs v1)', fontsize=12, fontweight='bold')
axes[1].set_xticklabels(metrics, rotation=45, ha='right')

# Add value labels
for bar in bars3:
    height = bar.get_height()
    axes[1].annotate(f'{height:+.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3 if height > 0 else -12), textcoords="offset points",
                    ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/offline_metrics_comparison.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: report/images/offline_metrics_comparison.png")

# Create visualization 2: Online A/B test metrics
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Left plot: Absolute values
metrics_online = online_df['metric'].values
v1_online = online_df['recsys_v1_pct'].values
v2_online = online_df['recsys_v2_pct'].values

x = np.arange(len(metrics_online))
bars4 = axes[0].bar(x - width/2, v1_online, width, label='RecSys-v1', color='#3498db', edgecolor='black', linewidth=0.5)
bars5 = axes[0].bar(x + width/2, v2_online, width, label='RecSys-v2', color='#e74c3c', edgecolor='black', linewidth=0.5)

axes[0].set_xlabel('Metric', fontsize=11)
axes[0].set_ylabel('Percentage (%)', fontsize=11)
axes[0].set_title('Online A/B Test: Absolute Values', fontsize=12, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(metrics_online, rotation=45, ha='right')
axes[0].legend(loc='upper right')

# Add value labels
for bar in bars4:
    height = bar.get_height()
    axes[0].annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)
for bar in bars5:
    height = bar.get_height()
    axes[0].annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

# Right plot: Relative change
changes_online = online_df['relative_change_pct'].values
colors_online = ['#2ecc71' if c > 0 else '#e74c3c' for c in changes_online]
bars6 = axes[1].bar(metrics_online, changes_online, color=colors_online, edgecolor='black', linewidth=0.5)
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
axes[1].set_xlabel('Metric', fontsize=11)
axes[1].set_ylabel('Relative Change (%)', fontsize=11)
axes[1].set_title('Online A/B Test: Relative Change (v2 vs v1)', fontsize=12, fontweight='bold')
axes[1].set_xticklabels(metrics_online, rotation=45, ha='right')

# Add value labels
for bar in bars6:
    height = bar.get_height()
    axes[1].annotate(f'{height:+.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3 if height > 0 else -12), textcoords="offset points",
                    ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/online_metrics_comparison.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: report/images/online_metrics_comparison.png")

# Create visualization 3: Comprehensive decision dashboard
fig = plt.figure(figsize=(14, 10))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.25)

# Top row: Offline metrics summary
ax1 = fig.add_subplot(gs[0, :])
metrics_short = ['P@10', 'NDCG@10', 'R@50', 'Coverage']
offline_changes = offline_df['relative_change_pct'].values
colors_offline = ['#2ecc71' if c > 0 else '#e74c3c' for c in offline_changes]

bars = ax1.barh(metrics_short, offline_changes, color=colors_offline, edgecolor='black', height=0.6)
ax1.axvline(x=0, color='black', linestyle='-', linewidth=1)
ax1.set_xlabel('Relative Change (%)', fontsize=11)
ax1.set_title('Offline Evaluation Metrics (n=200,000 held-out test)', fontsize=12, fontweight='bold')
ax1.set_xlim(-60, 20)

for i, (bar, val) in enumerate(zip(bars, offline_changes)):
    ax1.text(val + (2 if val > 0 else -2), bar.get_y() + bar.get_height()/2, 
             f'{val:+.1f}%', ha='left' if val > 0 else 'right', va='center', fontsize=10, fontweight='bold')

# Middle left: Online metrics
ax2 = fig.add_subplot(gs[1, 0])
online_changes = online_df['relative_change_pct'].values
metrics_online_short = ['CTR', 'D1 Ret.', 'D7 Ret.', 'Complaint']
colors_online = ['#2ecc71' if c > 0 else '#e74c3c' for c in online_changes]

bars2 = ax2.barh(metrics_online_short, online_changes, color=colors_online, edgecolor='black', height=0.6)
ax2.axvline(x=0, color='black', linestyle='-', linewidth=1)
ax2.set_xlabel('Relative Change (%)', fontsize=10)
ax2.set_title('Online A/B Test (14-day, 10% traffic)', fontsize=11, fontweight='bold')

for bar, val in zip(bars2, online_changes):
    ax2.text(val + (5 if val > 0 else -5), bar.get_y() + bar.get_height()/2, 
             f'{val:+.1f}%', ha='left' if val > 0 else 'right', va='center', fontsize=9)

# Middle right: Key trade-offs
ax3 = fig.add_subplot(gs[1, 1])
tradeoff_metrics = ['CTR', 'D7 Retention', 'Complaint Rate']
tradeoff_values = [16.2, -8.1, 187.0]
tradeoff_colors = ['#2ecc71', '#e74c3c', '#e74c3c']

bars3 = ax3.bar(tradeoff_metrics, tradeoff_values, color=tradeoff_colors, edgecolor='black', width=0.6)
ax3.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax3.set_ylabel('Relative Change (%)', fontsize=10)
ax3.set_title('Critical Business Metrics', fontsize=11, fontweight='bold')
ax3.set_xticklabels(tradeoff_metrics, rotation=15, ha='right')

for bar in bars3:
    height = bar.get_height()
    ax3.annotate(f'{height:+.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height > 0 else -12), textcoords="offset points",
                ha='center', va='bottom' if height > 0 else 'top', fontsize=10, fontweight='bold')

# Bottom: Summary scorecard
ax4 = fig.add_subplot(gs[2, :])
ax4.axis('off')

# Create summary table data
summary_data = [
    ['Metric Category', 'Key Finding', 'Impact'],
    ['Ranking Quality', 'P@10 +12.5%, NDCG@10 +9.6%', 'Positive'],
    ['Catalog Coverage', '-50.6%', 'Negative'],
    ['User Engagement', 'CTR +16.2%', 'Positive'],
    ['User Retention', 'D1 +3.9%, D7 -8.1%', 'Mixed/Negative'],
    ['User Satisfaction', 'Complaint rate +187%', 'Severely Negative']
]

table = ax4.table(cellText=summary_data[1:], colLabels=summary_data[0],
                  cellLoc='center', loc='center',
                  colColours=['#3498db']*3,
                  colWidths=[0.25, 0.4, 0.2])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2)

# Color code the impact column
for i in range(1, len(summary_data)):
    impact = summary_data[i][2]
    if 'Positive' in impact:
        table[(i, 2)].set_facecolor('#d5f5e3')
    elif 'Negative' in impact or 'Severely' in impact:
        table[(i, 2)].set_facecolor('#f5b7b1')
    else:
        table[(i, 2)].set_facecolor('#fef9e7')

ax4.set_title('Executive Summary: RecSys-v2 vs RecSys-v1', fontsize=12, fontweight='bold', pad=20)

plt.savefig('report/images/decision_dashboard.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: report/images/decision_dashboard.png")

# Statistical analysis summary
print("\n=== STATISTICAL ANALYSIS SUMMARY ===")

# Calculate composite scores
offline_improvements = offline_df[offline_df['relative_change_pct'] > 0]['relative_change_pct'].mean()
offline_degradations = offline_df[offline_df['relative_change_pct'] < 0]['relative_change_pct'].mean()

online_improvements = online_df[online_df['relative_change_pct'] > 0]['relative_change_pct'].mean()
online_degradations = online_df[online_df['relative_change_pct'] < 0]['relative_change_pct'].mean()

print(f"\nOffline Metrics:")
print(f"  - Average improvement (positive changes): {offline_improvements:.2f}%")
print(f"  - Average degradation (negative changes): {offline_degradations:.2f}%")

print(f"\nOnline Metrics:")
print(f"  - Average improvement (positive changes): {online_improvements:.2f}%")
print(f"  - Average degradation (negative changes): {online_degradations:.2f}%")

# Key insights
print("\n=== KEY INSIGHTS ===")
print("1. Offline metrics show improved ranking quality but severely reduced catalog coverage")
print("2. Online A/B shows strong CTR improvement (+16.2%) but concerning complaint rate increase (+187%)")
print("3. Long-term retention (D7) declined by 8.1%, suggesting user dissatisfaction")
print("4. The 50.6% drop in catalog coverage likely contributes to user complaints")

# Save analysis summary
with open('outputs/analysis_summary.txt', 'w') as f:
    f.write("RecSys V2 Launch Evaluation - Analysis Summary\n")
    f.write("=" * 60 + "\n\n")
    f.write("OFFLINE EVALUATION (n=200,000 held-out test):\n")
    f.write(offline_df.to_string(index=False))
    f.write("\n\nONLINE A/B TEST (14-day, 10% traffic per arm):\n")
    f.write(online_df.to_string(index=False))
    f.write("\n\nKEY FINDINGS:\n")
    f.write("- Ranking quality improved: P@10 +12.5%, NDCG@10 +9.6%\n")
    f.write("- Catalog coverage severely degraded: -50.6%\n")
    f.write("- CTR improved: +16.2%\n")
    f.write("- Retention mixed: D1 +3.9%, D7 -8.1%\n")
    f.write("- User complaints increased dramatically: +187%\n")

print("\nAnalysis complete! Outputs saved to outputs/ and report/images/")
