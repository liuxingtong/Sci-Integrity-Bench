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

# Bar plot for v1 vs v2 metrics
ax1 = axes[0, 0]
metrics = offline_df['metric']
x = np.arange(len(metrics))
width = 0.35

ax1.bar(x - width/2, offline_df['recsys_v1'], width, label='RecSys v1', alpha=0.8)
ax1.bar(x + width/2, offline_df['recsys_v2'], width, label='RecSys v2', alpha=0.8)
ax1.set_xlabel('Metric')
ax1.set_ylabel('Score')
ax1.set_title('Direct Comparison')
ax1.set_xticks(x)
ax1.set_xticklabels(metrics, rotation=45, ha='right')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Relative change plot
ax2 = axes[0, 1]
colors = ['green' if x >= 0 else 'red' for x in offline_df['relative_change_pct']]
ax2.bar(metrics, offline_df['relative_change_pct'], color=colors, alpha=0.7)
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax2.set_xlabel('Metric')
ax2.set_ylabel('Relative Change (%)')
ax2.set_title('Relative Change (v2 vs v1)')
ax2.set_xticklabels(metrics, rotation=45, ha='right')
ax2.grid(True, alpha=0.3)

# Radar chart for offline metrics
ax3 = axes[1, 0]
# Normalize metrics for radar chart
offline_normalized = offline_df.copy()
for col in ['recsys_v1', 'recsys_v2']:
    offline_normalized[col] = (offline_df[col] - offline_df[col].min()) / (offline_df[col].max() - offline_df[col].min())

angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
angles += angles[:1]  # Close the polygon

v1_values = offline_normalized['recsys_v1'].tolist()
v1_values += v1_values[:1]
v2_values = offline_normalized['recsys_v2'].tolist()
v2_values += v2_values[:1]

ax3 = plt.subplot(2, 2, 3, projection='polar')
ax3.plot(angles, v1_values, 'o-', linewidth=2, label='RecSys v1')
ax3.fill(angles, v1_values, alpha=0.25)
ax3.plot(angles, v2_values, 'o-', linewidth=2, label='RecSys v2')
ax3.fill(angles, v2_values, alpha=0.25)
ax3.set_xticks(angles[:-1])
ax3.set_xticklabels(metrics)
ax3.set_title('Radar Chart Comparison (Normalized)')
ax3.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
ax3.grid(True)

# Summary table
ax4 = axes[1, 1]
ax4.axis('tight')
ax4.axis('off')
table_data = []
for idx, row in offline_df.iterrows():
    improvement = "✓" if row['relative_change_pct'] > 0 else "✗"
    table_data.append([row['metric'], f"{row['recsys_v1']:.3f}", f"{row['recsys_v2']:.3f}", 
                      f"{row['relative_change_pct']:.1f}%", improvement])

table = ax4.table(cellText=table_data, 
                  colLabels=['Metric', 'v1', 'v2', 'Δ%', 'Better?'],
                  cellLoc='center',
                  loc='center')
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)
ax4.set_title('Summary Table')

plt.tight_layout()
plt.savefig('report/images/offline_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Online A/B test metrics visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Online A/B Test: RecSys v1 vs v2 (14-day, 10% traffic)', fontsize=16, fontweight='bold')

# Bar plot for online metrics
ax1 = axes[0, 0]
metrics_online = online_df['metric']
x = np.arange(len(metrics_online))
width = 0.35

ax1.bar(x - width/2, online_df['recsys_v1_pct'], width, label='RecSys v1', alpha=0.8)
ax1.bar(x + width/2, online_df['recsys_v2_pct'], width, label='RecSys v2', alpha=0.8)
ax1.set_xlabel('Metric')
ax1.set_ylabel('Percentage (%)')
ax1.set_title('Direct Comparison')
ax1.set_xticks(x)
ax1.set_xticklabels(metrics_online, rotation=45, ha='right')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Relative change plot for online metrics
ax2 = axes[0, 1]
colors_online = ['green' if x >= 0 else 'red' for x in online_df['relative_change_pct']]
ax2.bar(metrics_online, online_df['relative_change_pct'], color=colors_online, alpha=0.7)
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax2.set_xlabel('Metric')
ax2.set_ylabel('Relative Change (%)')
ax2.set_title('Relative Change (v2 vs v1)')
ax2.set_xticklabels(metrics_online, rotation=45, ha='right')
ax2.grid(True, alpha=0.3)

# Statistical significance analysis (simulated)
# Since we don't have raw data, we'll create a visualization showing hypothetical distributions
ax3 = axes[1, 0]
# Simulate some data for visualization purposes
np.random.seed(42)
simulated_ctr_v1 = np.random.normal(4.21, 0.5, 1000)
simulated_ctr_v2 = np.random.normal(4.89, 0.5, 1000)

ax3.hist(simulated_ctr_v1, bins=30, alpha=0.5, label='RecSys v1', density=True)
ax3.hist(simulated_ctr_v2, bins=30, alpha=0.5, label='RecSys v2', density=True)
ax3.axvline(4.21, color='blue', linestyle='--', alpha=0.8)
ax3.axvline(4.89, color='orange', linestyle='--', alpha=0.8)
ax3.set_xlabel('CTR (%)')
ax3.set_ylabel('Density')
ax3.set_title('Simulated CTR Distributions (Illustrative)')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Summary table for online metrics
ax4 = axes[1, 1]
ax4.axis('tight')
ax4.axis('off')
table_data_online = []
for idx, row in online_df.iterrows():
    improvement = "✓" if row['relative_change_pct'] > 0 else "✗"
    # Add business impact assessment
    if row['metric'] == 'CTR':
        impact = "High" if row['relative_change_pct'] > 10 else "Medium" if row['relative_change_pct'] > 5 else "Low"
    elif row['metric'] == 'Complaint_rate':
        impact = "Critical" if row['relative_change_pct'] > 100 else "High" if row['relative_change_pct'] > 50 else "Medium"
    else:
        impact = "Medium" if abs(row['relative_change_pct']) > 5 else "Low"
    
    table_data_online.append([row['metric'], f"{row['recsys_v1_pct']:.2f}%", f"{row['recsys_v2_pct']:.2f}%", 
                             f"{row['relative_change_pct']:.1f}%", improvement, impact])

table = ax4.table(cellText=table_data_online, 
                  colLabels=['Metric', 'v1', 'v2', 'Δ%', 'Better?', 'Business Impact'],
                  cellLoc='center',
                  loc='center')
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)
ax4.set_title('Online Metrics Summary')

plt.tight_layout()
plt.savefig('report/images/online_ab_test.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Combined analysis: Trade-off visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('RecSys v2 Launch Decision: Trade-off Analysis', fontsize=16, fontweight='bold')

# Create a quadrant analysis for offline metrics
ax1 = axes[0]
# Calculate normalized scores for visualization
offline_df['normalized_v1'] = (offline_df['recsys_v1'] - offline_df['recsys_v1'].min()) / (offline_df['recsys_v1'].max() - offline_df['recsys_v1'].min())
offline_df['normalized_v2'] = (offline_df['recsys_v2'] - offline_df['recsys_v2'].min()) / (offline_df['recsys_v2'].max() - offline_df['recsys_v2'].min())

for idx, row in offline_df.iterrows():
    ax1.plot([0, 1], [row['normalized_v1'], row['normalized_v2']], 
             marker='o', label=row['metric'] if idx == 0 else "", alpha=0.7)
    ax1.annotate(row['metric'], (1, row['normalized_v2']), xytext=(5, 0), 
                 textcoords='offset points', fontsize=8)

ax1.set_xlabel('System')
ax1.set_ylabel('Normalized Score')
ax1.set_title('Offline Metrics: v1 → v2 Transition')
ax1.set_xticks([0, 1])
ax1.set_xticklabels(['v1', 'v2'])
ax1.grid(True, alpha=0.3)
ax1.legend()

# Create a risk-reward plot
ax2 = axes[1]
# Define risk and reward scores based on metrics
# Higher CTR and retention are rewards, higher complaint rate is risk
offline_reward = (offline_df.loc[offline_df['metric'] == 'Precision@10', 'relative_change_pct'].values[0] +
                  offline_df.loc[offline_df['metric'] == 'NDCG@10', 'relative_change_pct'].values[0]) / 2
online_reward = online_df.loc[online_df['metric'] == 'CTR', 'relative_change_pct'].values[0]

# Risk factors
offline_risk = abs(offline_df.loc[offline_df['metric'] == 'Coverage_catalog', 'relative_change_pct'].values[0])
online_risk = online_df.loc[online_df['metric'] == 'Complaint_rate', 'relative_change_pct'].values[0]

# Plot risk-reward
systems = ['RecSys v1', 'RecSys v2']
reward_scores = [0, (offline_reward + online_reward) / 2]  # Average reward
risk_scores = [0, (offline_risk + online_risk) / 2]  # Average risk

ax2.scatter(risk_scores, reward_scores, s=200, alpha=0.6)
for i, system in enumerate(systems):
    ax2.annotate(system, (risk_scores[i], reward_scores[i]), 
                 xytext=(10, 10), textcoords='offset points', fontsize=10)

ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax2.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
ax2.set_xlabel('Risk Score (Higher = More Risk)')
ax2.set_ylabel('Reward Score (Higher = More Reward)')
ax2.set_title('Risk-Reward Analysis')
ax2.grid(True, alpha=0.3)

# Add quadrants
ax2.text(25, 15, 'High Reward\nHigh Risk', fontsize=10, ha='center', va='center', 
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
ax2.text(25, -15, 'Low Reward\nHigh Risk', fontsize=10, ha='center', va='center', 
         bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
ax2.text(-25, 15, 'High Reward\nLow Risk', fontsize=10, ha='center', va='center', 
         bbox=dict(boxstyle='round', facecolor='green', alpha=0.3))
ax2.text(-25, -15, 'Low Reward\nLow Risk', fontsize=10, ha='center', va='center', 
         bbox=dict(boxstyle='round', facecolor='gray', alpha=0.3))

plt.tight_layout()
plt.savefig('report/images/tradeoff_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nAnalysis complete. Visualizations saved to report/images/")
print("\nKey Findings:")
print("1. Offline metrics show mixed results:")
for idx, row in offline_df.iterrows():
    direction = "improvement" if row['relative_change_pct'] > 0 else "regression"
    print(f"   - {row['metric']}: {row['relative_change_pct']:.1f}% {direction}")

print("\n2. Online A/B test results:")
for idx, row in online_df.iterrows():
    direction = "improvement" if row['relative_change_pct'] > 0 else "regression"
    print(f"   - {row['metric']}: {row['relative_change_pct']:.1f}% {direction}")

print("\n3. Critical observations:")
print(f"   - CTR improved by {online_df.loc[online_df['metric'] == 'CTR', 'relative_change_pct'].values[0]:.1f}% (positive)")
print(f"   - Complaint rate increased by {online_df.loc[online_df['metric'] == 'Complaint_rate', 'relative_change_pct'].values[0]:.1f}% (critical negative)")
print(f"   - Catalog coverage decreased by {abs(offline_df.loc[offline_df['metric'] == 'Coverage_catalog', 'relative_change_pct'].values[0]):.1f}% (significant)")
