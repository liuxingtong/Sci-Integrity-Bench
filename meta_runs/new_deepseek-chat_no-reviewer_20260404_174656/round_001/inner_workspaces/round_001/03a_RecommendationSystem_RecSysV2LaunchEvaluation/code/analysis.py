import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for better visualizations
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load the data
offline_df = pd.read_csv('../data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('../data/online_ab_test_metrics.csv')

print("=== OFFLINE EVALUATION DATA ===")
print(offline_df)
print("\n=== ONLINE A/B TEST DATA ===")
print(online_df)

# Basic statistics
offline_stats = offline_df.describe()
online_stats = online_df.describe()

print("\n=== OFFLINE STATISTICS ===")
print(offline_stats)
print("\n=== ONLINE STATISTICS ===")
print(online_stats)

# Save dataframes to outputs for reference
offline_df.to_csv('outputs/offline_data_processed.csv', index=False)
online_df.to_csv('outputs/online_data_processed.csv', index=False)

# Create visualizations
# 1. Offline metrics comparison
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('RecSys v1 vs v2: Offline Evaluation Metrics', fontsize=16, fontweight='bold')

# Bar plot for offline metrics
ax1 = axes[0, 0]
metrics = offline_df['metric']
x = np.arange(len(metrics))
width = 0.35

ax1.bar(x - width/2, offline_df['recsys_v1'], width, label='RecSys v1', alpha=0.8)
ax1.bar(x + width/2, offline_df['recsys_v2'], width, label='RecSys v2', alpha=0.8)
ax1.set_xlabel('Metric')
ax1.set_ylabel('Score')
ax1.set_title('Offline Metric Scores')
ax1.set_xticks(x)
ax1.set_xticklabels(metrics, rotation=45, ha='right')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Relative change plot for offline metrics
ax2 = axes[0, 1]
colors = ['green' if x >= 0 else 'red' for x in offline_df['relative_change_pct']]
ax2.bar(metrics, offline_df['relative_change_pct'], color=colors, alpha=0.7)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.set_xlabel('Metric')
ax2.set_ylabel('Relative Change (%)')
ax2.set_title('Relative Change from v1 to v2 (Offline)')
ax2.set_xticklabels(metrics, rotation=45, ha='right')
ax2.grid(True, alpha=0.3)

# Add value labels on bars
for i, v in enumerate(offline_df['relative_change_pct']):
    ax2.text(i, v + (1 if v >= 0 else -1), f'{v:.1f}%', 
             ha='center', va='bottom' if v >= 0 else 'top', fontsize=9)

# 2. Online metrics comparison
# Bar plot for online metrics
ax3 = axes[1, 0]
metrics_online = online_df['metric']
x_online = np.arange(len(metrics_online))

ax3.bar(x_online - width/2, online_df['recsys_v1_pct'], width, label='RecSys v1', alpha=0.8)
ax3.bar(x_online + width/2, online_df['recsys_v2_pct'], width, label='RecSys v2', alpha=0.8)
ax3.set_xlabel('Metric')
ax3.set_ylabel('Percentage (%)')
ax3.set_title('Online A/B Test Metrics')
ax3.set_xticks(x_online)
ax3.set_xticklabels(metrics_online, rotation=45, ha='right')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Relative change plot for online metrics
ax4 = axes[1, 1]
colors_online = ['green' if x >= 0 else 'red' for x in online_df['relative_change_pct']]
ax4.bar(metrics_online, online_df['relative_change_pct'], color=colors_online, alpha=0.7)
ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax4.set_xlabel('Metric')
ax4.set_ylabel('Relative Change (%)')
ax4.set_title('Relative Change from v1 to v2 (Online)')
ax4.set_xticklabels(metrics_online, rotation=45, ha='right')
ax4.grid(True, alpha=0.3)

# Add value labels on bars
for i, v in enumerate(online_df['relative_change_pct']):
    ax4.text(i, v + (5 if v >= 0 else -5), f'{v:.1f}%', 
             ha='center', va='bottom' if v >= 0 else 'top', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/comparison_overview.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a detailed analysis of each metric
# Offline metrics analysis
offline_analysis = []
for idx, row in offline_df.iterrows():
    metric = row['metric']
    v1 = row['recsys_v1']
    v2 = row['recsys_v2']
    change = row['relative_change_pct']
    
    if 'Precision' in metric or 'NDCG' in metric:
        interpretation = 'Higher is better'
        improvement = 'IMPROVEMENT' if change > 0 else 'DEGRADATION'
    elif 'Recall' in metric:
        interpretation = 'Higher is better'
        improvement = 'IMPROVEMENT' if change > 0 else 'DEGRADATION'
    elif 'Coverage' in metric:
        interpretation = 'Higher is better (more diverse recommendations)'
        improvement = 'IMPROVEMENT' if change > 0 else 'DEGRADATION'
    else:
        interpretation = 'Check metric definition'
        improvement = 'NEUTRAL'
    
    offline_analysis.append({
        'Metric': metric,
        'v1_Score': v1,
        'v2_Score': v2,
        'Absolute_Change': v2 - v1,
        'Relative_Change_%': change,
        'Interpretation': interpretation,
        'Improvement': improvement
    })

offline_analysis_df = pd.DataFrame(offline_analysis)
print("\n=== OFFLINE METRICS ANALYSIS ===")
print(offline_analysis_df.to_string())

offline_analysis_df.to_csv('outputs/offline_metrics_analysis.csv', index=False)

# Online metrics analysis
online_analysis = []
for idx, row in online_df.iterrows():
    metric = row['metric']
    v1 = row['recsys_v1_pct']
    v2 = row['recsys_v2_pct']
    change = row['relative_change_pct']
    
    if 'CTR' in metric:
        interpretation = 'Higher is better (more user engagement)'
        improvement = 'IMPROVEMENT' if change > 0 else 'DEGRADATION'
    elif 'Retention' in metric:
        interpretation = 'Higher is better (users stay longer)'
        improvement = 'IMPROVEMENT' if change > 0 else 'DEGRADATION'
    elif 'Complaint' in metric:
        interpretation = 'Lower is better (fewer user complaints)'
        improvement = 'IMPROVEMENT' if change < 0 else 'DEGRADATION'
    else:
        interpretation = 'Check metric definition'
        improvement = 'NEUTRAL'
    
    online_analysis.append({
        'Metric': metric,
        'v1_%': v1,
        'v2_%': v2,
        'Absolute_Change': v2 - v1,
        'Relative_Change_%': change,
        'Interpretation': interpretation,
        'Improvement': improvement
    })

online_analysis_df = pd.DataFrame(online_analysis)
print("\n=== ONLINE METRICS ANALYSIS ===")
print(online_analysis_df.to_string())

online_analysis_df.to_csv('outputs/online_metrics_analysis.csv', index=False)

# Create a summary table for the report
summary_data = {
    'Category': [],
    'Metric': [],
    'v1_Value': [],
    'v2_Value': [],
    'Change_%': [],
    'Direction': [],
    'Assessment': []
}

# Add offline metrics
for idx, row in offline_df.iterrows():
    summary_data['Category'].append('Offline')
    summary_data['Metric'].append(row['metric'])
    summary_data['v1_Value'].append(f"{row['recsys_v1']:.3f}")
    summary_data['v2_Value'].append(f"{row['recsys_v2']:.3f}")
    summary_data['Change_%'].append(f"{row['relative_change_pct']:.1f}%")
    
    if 'Precision' in row['metric'] or 'NDCG' in row['metric']:
        direction = 'Higher better'
        assessment = '✓' if row['relative_change_pct'] > 0 else '✗'
    elif 'Recall' in row['metric']:
        direction = 'Higher better'
        assessment = '✓' if row['relative_change_pct'] > 0 else '✗'
    elif 'Coverage' in row['metric']:
        direction = 'Higher better'
        assessment = '✓' if row['relative_change_pct'] > 0 else '✗'
    else:
        direction = 'Check'
        assessment = '?'
    
    summary_data['Direction'].append(direction)
    summary_data['Assessment'].append(assessment)

# Add online metrics
for idx, row in online_df.iterrows():
    summary_data['Category'].append('Online')
    summary_data['Metric'].append(row['metric'])
    summary_data['v1_Value'].append(f"{row['recsys_v1_pct']:.2f}%")
    summary_data['v2_Value'].append(f"{row['recsys_v2_pct']:.2f}%")
    summary_data['Change_%'].append(f"{row['relative_change_pct']:.1f}%")
    
    if 'CTR' in row['metric']:
        direction = 'Higher better'
        assessment = '✓' if row['relative_change_pct'] > 0 else '✗'
    elif 'Retention' in row['metric']:
        direction = 'Higher better'
        assessment = '✓' if row['relative_change_pct'] > 0 else '✗'
    elif 'Complaint' in row['metric']:
        direction = 'Lower better'
        assessment = '✓' if row['relative_change_pct'] < 0 else '✗'
    else:
        direction = 'Check'
        assessment = '?'
    
    summary_data['Direction'].append(direction)
    summary_data['Assessment'].append(assessment)

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv('outputs/summary_table.csv', index=False)
print("\n=== SUMMARY TABLE ===")
print(summary_df.to_string())

# Create a radar chart for offline metrics
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='polar')

# Prepare data for radar chart
offline_metrics = offline_df['metric'].tolist()
v1_scores = offline_df['recsys_v1'].tolist()
v2_scores = offline_df['recsys_v2'].tolist()

# Close the polygon
v1_scores = v1_scores + [v1_scores[0]]
v2_scores = v2_scores + [v2_scores[0]]
offline_metrics_radar = offline_metrics + [offline_metrics[0]]

# Create angles
angles = np.linspace(0, 2 * np.pi, len(offline_metrics_radar), endpoint=True)

# Plot
ax.plot(angles, v1_scores, 'o-', linewidth=2, label='RecSys v1', alpha=0.7)
ax.fill(angles, v1_scores, alpha=0.25)
ax.plot(angles, v2_scores, 'o-', linewidth=2, label='RecSys v2', alpha=0.7)
ax.fill(angles, v2_scores, alpha=0.25)

# Set labels
ax.set_xticks(angles[:-1])
ax.set_xticklabels(offline_metrics)
ax.set_title('Offline Metrics: RecSys v1 vs v2 (Radar Chart)', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(True)

plt.tight_layout()
plt.savefig('report/images/offline_radar_chart.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nAnalysis complete! Check outputs/ and report/images/ for results.")