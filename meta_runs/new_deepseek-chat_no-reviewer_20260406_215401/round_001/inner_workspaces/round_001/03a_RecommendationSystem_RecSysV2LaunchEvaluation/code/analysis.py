import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats

# Set style for better visualizations
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("Loading data...")
# Load offline evaluation metrics
offline_df = pd.read_csv('../data/offline_evaluation_metrics.csv')
print("Offline metrics:")
print(offline_df)
print("\n")

# Load online A/B test metrics
online_df = pd.read_csv('../data/online_ab_test_metrics.csv')
print("Online A/B test metrics:")
print(online_df)
print("\n")

# Basic statistics
offline_stats = offline_df.describe()
online_stats = online_df.describe()

print("Offline metrics statistics:")
print(offline_stats)
print("\nOnline metrics statistics:")
print(online_stats)

# Save statistics to files
offline_stats.to_csv('outputs/offline_stats.csv')
online_stats.to_csv('outputs/online_stats.csv')

# Create visualizations
# 1. Offline metrics comparison
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Offline Evaluation: RecSys v1 vs v2', fontsize=16, fontweight='bold')

# Bar plot for offline metrics
ax1 = axes[0, 0]
metrics = offline_df['metric']
x = np.arange(len(metrics))
width = 0.35

bars1 = ax1.bar(x - width/2, offline_df['recsys_v1'], width, label='RecSys v1', alpha=0.8)
bars2 = ax1.bar(x + width/2, offline_df['recsys_v2'], width, label='RecSys v2', alpha=0.8)

ax1.set_xlabel('Metric')
ax1.set_ylabel('Score')
ax1.set_title('Offline Metric Scores')
ax1.set_xticks(x)
ax1.set_xticklabels(metrics, rotation=45, ha='right')
ax1.legend()

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

# Relative change plot
ax2 = axes[0, 1]
colors = ['green' if x > 0 else 'red' for x in offline_df['relative_change_pct']]
bars = ax2.bar(metrics, offline_df['relative_change_pct'], color=colors, alpha=0.7)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.set_xlabel('Metric')
ax2.set_ylabel('Relative Change (%)')
ax2.set_title('Relative Change: v2 vs v1 (%)')
ax2.set_xticklabels(metrics, rotation=45, ha='right')

# Add value labels
for bar in bars:
    height = bar.get_height()
    ax2.annotate(f'{height:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height > 0 else -10),
                textcoords="offset points",
                ha='center', va='bottom' if height > 0 else 'top', fontsize=9)

# 2. Online metrics comparison
ax3 = axes[1, 0]
metrics_online = online_df['metric']
x_online = np.arange(len(metrics_online))

bars3 = ax3.bar(x_online - width/2, online_df['recsys_v1_pct'], width, label='RecSys v1', alpha=0.8)
bars4 = ax3.bar(x_online + width/2, online_df['recsys_v2_pct'], width, label='RecSys v2', alpha=0.8)

ax3.set_xlabel('Metric')
ax3.set_ylabel('Percentage (%)')
ax3.set_title('Online A/B Test Metrics')
ax3.set_xticks(x_online)
ax3.set_xticklabels(metrics_online, rotation=45, ha='right')
ax3.legend()

# Add value labels
for bars in [bars3, bars4]:
    for bar in bars:
        height = bar.get_height()
        ax3.annotate(f'{height:.2f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

# Online relative change plot
ax4 = axes[1, 1]
colors_online = ['green' if x > 0 else 'red' for x in online_df['relative_change_pct']]
bars_online = ax4.bar(metrics_online, online_df['relative_change_pct'], color=colors_online, alpha=0.7)
ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax4.set_xlabel('Metric')
ax4.set_ylabel('Relative Change (%)')
ax4.set_title('Online Relative Change: v2 vs v1 (%)')
ax4.set_xticklabels(metrics_online, rotation=45, ha='right')

# Add value labels
for bar in bars_online:
    height = bar.get_height()
    ax4.annotate(f'{height:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3 if height > 0 else -10),
                textcoords="offset points",
                ha='center', va='bottom' if height > 0 else 'top', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/comparison_metrics.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nSaved comparison metrics figure to report/images/comparison_metrics.png")

# Create a radar chart for comprehensive comparison
fig = plt.figure(figsize=(12, 10))

# Normalize data for radar chart
def normalize_data(data, is_percentage=False):
    """Normalize data to 0-1 range for radar chart"""
    if is_percentage:
        # For percentages, we might want different normalization
        return data / 100
    else:
        # For scores between 0-1
        return data

# Prepare data for radar chart
offline_v1_norm = normalize_data(offline_df['recsys_v1'].values, False)
offline_v2_norm = normalize_data(offline_df['recsys_v2'].values, False)
online_v1_norm = normalize_data(online_df['recsys_v1_pct'].values, True)
online_v2_norm = normalize_data(online_df['recsys_v2_pct'].values, True)

# Combine metrics for radar chart
all_metrics = list(offline_df['metric']) + list(online_df['metric'])
all_v1 = list(offline_v1_norm) + list(online_v1_norm)
all_v2 = list(offline_v2_norm) + list(online_v2_norm)

# Number of variables
N = len(all_metrics)

# What will be the angle of each axis in the plot
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]  # Close the loop

# Initialise the spider plot
ax = plt.subplot(111, polar=True)

# Draw one axe per variable and add labels
plt.xticks(angles[:-1], all_metrics, size=10)

# Plot data
all_v1 += all_v1[:1]
all_v2 += all_v2[:1]

ax.plot(angles, all_v1, linewidth=2, linestyle='solid', label='RecSys v1', color='blue')
ax.fill(angles, all_v1, 'blue', alpha=0.1)

ax.plot(angles, all_v2, linewidth=2, linestyle='solid', label='RecSys v2', color='orange')
ax.fill(angles, all_v2, 'orange', alpha=0.1)

# Add legend
plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
plt.title('Comprehensive Comparison: RecSys v1 vs v2 (Normalized)', size=15, y=1.1)

plt.savefig('report/images/radar_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("Saved radar comparison figure to report/images/radar_comparison.png")

# Create a summary table for decision making
summary_data = []
for idx, row in offline_df.iterrows():
    summary_data.append({
        'metric': row['metric'],
        'type': 'offline',
        'v1_value': row['recsys_v1'],
        'v2_value': row['recsys_v2'],
        'relative_change_pct': row['relative_change_pct'],
        'improvement': 'positive' if row['relative_change_pct'] > 0 else 'negative',
        'magnitude': abs(row['relative_change_pct'])
    })

for idx, row in online_df.iterrows():
    summary_data.append({
        'metric': row['metric'],
        'type': 'online',
        'v1_value': row['recsys_v1_pct'],
        'v2_value': row['recsys_v2_pct'],
        'relative_change_pct': row['relative_change_pct'],
        'improvement': 'positive' if row['relative_change_pct'] > 0 else 'negative',
        'magnitude': abs(row['relative_change_pct'])
    })

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv('outputs/summary_metrics.csv', index=False)

print("\nSummary metrics saved to outputs/summary_metrics.csv")
print("\n" + "="*80)
print("SUMMARY OF FINDINGS:")
print("="*80)

# Calculate overall improvement scores
# Weight different metrics based on business importance
# For offline: Precision and NDCG are most important
# For online: CTR and Retention are most important, Complaint rate is critical

offline_improvement = (
    offline_df.loc[offline_df['metric'] == 'Precision@10', 'relative_change_pct'].values[0] * 0.4 +
    offline_df.loc[offline_df['metric'] == 'NDCG@10', 'relative_change_pct'].values[0] * 0.4 +
    offline_df.loc[offline_df['metric'] == 'Recall@50', 'relative_change_pct'].values[0] * 0.1 +
    offline_df.loc[offline_df['metric'] == 'Coverage_catalog', 'relative_change_pct'].values[0] * 0.1
)

online_improvement = (
    online_df.loc[online_df['metric'] == 'CTR', 'relative_change_pct'].values[0] * 0.3 +
    online_df.loc[online_df['metric'] == 'Retention_D1', 'relative_change_pct'].values[0] * 0.2 +
    online_df.loc[online_df['metric'] == 'Retention_D7', 'relative_change_pct'].values[0] * 0.2 -
    online_df.loc[online_df['metric'] == 'Complaint_rate', 'relative_change_pct'].values[0] * 0.3  # Negative weight for complaints
)

print(f"\nWeighted Offline Improvement Score: {offline_improvement:.2f}%")
print(f"Weighted Online Improvement Score: {online_improvement:.2f}%")

# Overall score (weighted average)
overall_score = offline_improvement * 0.4 + online_improvement * 0.6
print(f"\nOverall Weighted Score: {overall_score:.2f}%")

# Decision logic
if overall_score > 5:
    recommendation = "LAUNCH RecSys v2"
    reasoning = "Significant overall improvement across key metrics"
elif overall_score > 0:
    recommendation = "CONSIDER launching RecSys v2 with monitoring"
    reasoning = "Moderate improvement but some trade-offs need monitoring"
else:
    recommendation = "DO NOT LAUNCH RecSys v2"
    reasoning = "Overall performance degradation or unacceptable trade-offs"

print(f"\nRECOMMENDATION: {recommendation}")
print(f"REASONING: {reasoning}")

# Create a decision matrix visualization
fig, ax = plt.subplots(figsize=(10, 6))

# Prepare data for decision matrix
metrics_list = list(offline_df['metric']) + list(online_df['metric'])
changes = list(offline_df['relative_change_pct']) + list(online_df['relative_change_pct'])
metric_types = ['offline'] * len(offline_df) + ['online'] * len(online_df)

# Create scatter plot
colors = ['blue' if t == 'offline' else 'green' for t in metric_types]
sizes = [100 + abs(c) * 5 for c in changes]  # Size based on magnitude

scatter = ax.scatter(range(len(metrics_list)), changes, c=colors, s=sizes, alpha=0.6, edgecolors='black')

# Add horizontal line at y=0
ax.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='No Change')

# Add labels
for i, (metric, change) in enumerate(zip(metrics_list, changes)):
    ax.annotate(metric, (i, change), xytext=(0, 10 if change > 0 else -15),
                textcoords='offset points', ha='center', fontsize=9,
                arrowprops=dict(arrowstyle='->', lw=0.5, alpha=0.5))

ax.set_xlabel('Metrics')
ax.set_ylabel('Relative Change (%)')
ax.set_title('Decision Matrix: Metric Changes for RecSys v2 vs v1')
ax.set_xticks([])  # Remove x-ticks since we're using annotations

# Add legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Offline Metrics',
           markerfacecolor='blue', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Online Metrics',
           markerfacecolor='green', markersize=10),
    Line2D([0], [0], color='red', linestyle='--', label='No Change')
]
ax.legend(handles=legend_elements, loc='upper right')

plt.tight_layout()
plt.savefig('report/images/decision_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nSaved decision matrix to report/images/decision_matrix.png")
print("\nAnalysis complete!")