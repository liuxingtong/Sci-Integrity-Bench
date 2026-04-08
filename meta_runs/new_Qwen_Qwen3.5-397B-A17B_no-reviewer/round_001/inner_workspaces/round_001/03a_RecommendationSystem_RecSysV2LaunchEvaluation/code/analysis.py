import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Ensure output directories exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
offline_df = pd.read_csv('data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('data/online_ab_test_metrics.csv')

print("=== Offline Evaluation Metrics ===")
print(offline_df)
print("\n=== Online A/B Test Metrics ===")
print(online_df)

# Create comprehensive visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('RecSys V2 vs V1: Comprehensive Evaluation', fontsize=14, fontweight='bold')

# Plot 1: Offline Metrics Comparison (bar chart)
ax1 = axes[0, 0]
metrics_offline = offline_df['metric'].tolist()
v1_offline = offline_df['recsys_v1'].tolist()
v2_offline = offline_df['recsys_v2'].tolist()
x = np.arange(len(metrics_offline))
width = 0.35

bars1 = ax1.bar(x - width/2, v1_offline, width, label='RecSys V1', color='#3498db', alpha=0.8)
bars2 = ax1.bar(x + width/2, v2_offline, width, label='RecSys V2', color='#e74c3c', alpha=0.8)

ax1.set_ylabel('Score')
ax1.set_title('Offline Evaluation Metrics', fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(metrics_offline, rotation=15, ha='right')
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax1.annotate(f'{height:.3f}',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8)
for bar in bars2:
    height = bar.get_height()
    ax1.annotate(f'{height:.3f}',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8)

# Plot 2: Offline Relative Change (bar chart)
ax2 = axes[0, 1]
changes_offline = offline_df['relative_change_pct'].tolist()
colors = ['#27ae60' if c > 0 else '#c0392b' for c in changes_offline]
bars = ax2.bar(metrics_offline, changes_offline, color=colors, alpha=0.8)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.set_ylabel('Relative Change (%)')
ax2.set_title('Offline: V2 vs V1 Relative Change', fontweight='bold')
ax2.set_xticklabels(metrics_offline, rotation=15, ha='right')
ax2.grid(axis='y', alpha=0.3)

# Add value labels
for bar, change in zip(bars, changes_offline):
    height = bar.get_height()
    ax2.annotate(f'{change:.1f}%',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3 if height > 0 else -15), textcoords="offset points",
                 ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

# Plot 3: Online Metrics Comparison (bar chart)
ax3 = axes[1, 0]
metrics_online = online_df['metric'].tolist()
v1_online = online_df['recsys_v1_pct'].tolist()
v2_online = online_df['recsys_v2_pct'].tolist()
x = np.arange(len(metrics_online))

bars1 = ax3.bar(x - width/2, v1_online, width, label='RecSys V1', color='#3498db', alpha=0.8)
bars2 = ax3.bar(x + width/2, v2_online, width, label='RecSys V2', color='#e74c3c', alpha=0.8)

ax3.set_ylabel('Percentage Points (%)')
ax3.set_title('Online A/B Test Metrics (14-day)', fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(metrics_online, rotation=15, ha='right')
ax3.legend()
ax3.grid(axis='y', alpha=0.3)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax3.annotate(f'{height:.2f}',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8)
for bar in bars2:
    height = bar.get_height()
    ax3.annotate(f'{height:.2f}',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8)

# Plot 4: Online Relative Change (bar chart)
ax4 = axes[1, 1]
changes_online = online_df['relative_change_pct'].tolist()
colors = ['#27ae60' if c > 0 else '#c0392b' for c in changes_online]
bars = ax4.bar(metrics_online, changes_online, color=colors, alpha=0.8)
ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax4.set_ylabel('Relative Change (%)')
ax4.set_title('Online: V2 vs V1 Relative Change', fontweight='bold')
ax4.set_xticklabels(metrics_online, rotation=15, ha='right')
ax4.grid(axis='y', alpha=0.3)

# Add value labels
for bar, change in zip(bars, changes_online):
    height = bar.get_height()
    ax4.annotate(f'{change:.1f}%',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3 if height > 0 else -15), textcoords="offset points",
                 ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/evaluation_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: report/images/evaluation_comparison.png")

# Create trade-off analysis plot
fig2, ax = plt.subplots(figsize=(10, 8))

# Key metrics for trade-off analysis
key_metrics = {
    'Precision@10': (offline_df[offline_df['metric']=='Precision@10']['relative_change_pct'].values[0], 'offline', 'green'),
    'NDCG@10': (offline_df[offline_df['metric']=='NDCG@10']['relative_change_pct'].values[0], 'offline', 'green'),
    'Recall@50': (offline_df[offline_df['metric']=='Recall@50']['relative_change_pct'].values[0], 'offline', 'red'),
    'Coverage': (offline_df[offline_df['metric']=='Coverage_catalog']['relative_change_pct'].values[0], 'offline', 'red'),
    'CTR': (online_df[online_df['metric']=='CTR']['relative_change_pct'].values[0], 'online', 'green'),
    'D1 Retention': (online_df[online_df['metric']=='Retention_D1']['relative_change_pct'].values[0], 'online', 'green'),
    'D7 Retention': (online_df[online_df['metric']=='Retention_D7']['relative_change_pct'].values[0], 'online', 'red'),
    'Complaint Rate': (online_df[online_df['metric']=='Complaint_rate']['relative_change_pct'].values[0], 'online', 'red')
}

metrics_names = list(key_metrics.keys())
changes = [v[0] for v in key_metrics.values()]
categories = [v[1] for v in key_metrics.values()]
colors_map = []
for name, (change, cat, color) in key_metrics.items():
    if color == 'green':
        colors_map.append('#27ae60')
    else:
        colors_map.append('#c0392b')

x = np.arange(len(metrics_names))
bars = ax.bar(x, changes, color=colors_map, alpha=0.8)
ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax.set_ylabel('Relative Change (%)', fontsize=12)
ax.set_title('RecSys V2 vs V1: Trade-off Analysis Across All Metrics', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(metrics_names, rotation=45, ha='right')
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add legend for positive/negative
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#27ae60', label='Positive Change (Favorable)'),
                   Patch(facecolor='#c0392b', label='Negative Change (Concerning)')]
ax.legend(handles=legend_elements, loc='upper right')

# Add value labels
for bar, change in zip(bars, changes):
    height = bar.get_height()
    ax.annotate(f'{change:+.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height > 0 else -15), textcoords="offset points",
                ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/tradeoff_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/tradeoff_analysis.png")

# Summary statistics
print("\n=== SUMMARY STATISTICS ===")
print("\nOffline Metrics (n=200,000 held-out test set):")
for _, row in offline_df.iterrows():
    print(f"  {row['metric']}: V1={row['recsys_v1']:.4f}, V2={row['recsys_v2']:.4f}, Change={row['relative_change_pct']:+.1f}%")

print("\nOnline Metrics (14-day A/B test, 10% traffic per arm):")
for _, row in online_df.iterrows():
    print(f"  {row['metric']}: V1={row['recsys_v1_pct']:.2f}%, V2={row['recsys_v2_pct']:.2f}%, Change={row['relative_change_pct']:+.1f}%")

print("\nAnalysis complete!")
