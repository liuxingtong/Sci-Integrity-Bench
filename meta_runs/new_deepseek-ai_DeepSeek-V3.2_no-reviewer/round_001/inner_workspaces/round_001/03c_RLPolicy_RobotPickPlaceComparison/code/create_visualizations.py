import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib import rcParams

# Set up better visualization settings
rcParams['figure.figsize'] = [12, 8]
rcParams['font.size'] = 12
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
df = pd.read_csv("../data/pick_place_metrics.csv")

# Create output directory for images
os.makedirs("../report/images", exist_ok=True)

# 1. Bar plot comparing policies across all metrics (simulation)
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Policy Comparison: pi_base vs pi_new', fontsize=16, fontweight='bold')

# Prepare data for grouped bar chart
metrics = df['metric'].unique()
x = np.arange(len(metrics))
width = 0.35

# Simulation values
sim_base = df[df['arm'] == 'pi_base'].set_index('metric')['simulation'].reindex(metrics)
sim_new = df[df['arm'] == 'pi_new'].set_index('metric')['simulation'].reindex(metrics)

ax1 = axes[0, 0]
ax1.bar(x - width/2, sim_base, width, label='pi_base', alpha=0.8)
ax1.bar(x + width/2, sim_new, width, label='pi_new', alpha=0.8)
ax1.set_xlabel('Metric')
ax1.set_ylabel('Value')
ax1.set_title('Simulation Performance')
ax1.set_xticks(x)
ax1.set_xticklabels(metrics, rotation=45, ha='right')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Real-world values
real_base = df[df['arm'] == 'pi_base'].set_index('metric')['real_world'].reindex(metrics)
real_new = df[df['arm'] == 'pi_new'].set_index('metric')['real_world'].reindex(metrics)

ax2 = axes[0, 1]
ax2.bar(x - width/2, real_base, width, label='pi_base', alpha=0.8)
ax2.bar(x + width/2, real_new, width, label='pi_new', alpha=0.8)
ax2.set_xlabel('Metric')
ax2.set_ylabel('Value')
ax2.set_title('Real-World Performance')
ax2.set_xticks(x)
ax2.set_xticklabels(metrics, rotation=45, ha='right')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 2. Difference plot (pi_new - pi_base)
ax3 = axes[1, 0]
diff_sim = sim_new - sim_base
diff_real = real_new - real_base

ax3.bar(x - width/2, diff_sim, width, label='Simulation', alpha=0.8)
ax3.bar(x + width/2, diff_real, width, label='Real-World', alpha=0.8)
ax3.set_xlabel('Metric')
ax3.set_ylabel('Difference (pi_new - pi_base)')
ax3.set_title('Performance Differences')
ax3.set_xticks(x)
ax3.set_xticklabels(metrics, rotation=45, ha='right')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

# 3. Simulation vs Real-world correlation
ax4 = axes[1, 1]
# Normalize metrics for better visualization
normalized_sim = (sim_new - sim_base) / (sim_base + 1e-10) * 100
normalized_real = (real_new - real_base) / (real_base + 1e-10) * 100

ax4.scatter(normalized_sim, normalized_real, s=100, alpha=0.7)
ax4.set_xlabel('Percentage Change in Simulation (%)')
ax4.set_ylabel('Percentage Change in Real-World (%)')
ax4.set_title('Simulation vs Real-World Correlation')
ax4.grid(True, alpha=0.3)
ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax4.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

# Add metric labels to points
for i, metric in enumerate(metrics):
    ax4.annotate(metric, (normalized_sim[i], normalized_real[i]), 
                 xytext=(5, 5), textcoords='offset points', fontsize=9)

# Add diagonal line for perfect correlation
lims = [
    np.min([ax4.get_xlim(), ax4.get_ylim()]),
    np.max([ax4.get_xlim(), ax4.get_ylim()]),
]
ax4.plot(lims, lims, 'k--', alpha=0.5, linewidth=1)
ax4.set_xlim(lims)
ax4.set_ylim(lims)

plt.tight_layout()
plt.savefig('../report/images/policy_comparison_overview.png', dpi=300, bbox_inches='tight')
plt.close()

print("Overview visualization saved.")

# 3. Create separate detailed plots for each metric category
# Categorize metrics
positive_metrics = ['success_rate', 'human_rating_1_5']  # Higher is better
negative_metrics = ['cycle_time_s', 'collision_count', 'energy_kwh', 
                    'line_stop_events', 'safety_intervention_rate', 'edge_case_fail_rate']  # Lower is better

# Positive metrics plot
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Metrics Where Higher Values Are Better', fontsize=14, fontweight='bold')

for idx, metric in enumerate(positive_metrics):
    metric_data = df[df['metric'] == metric]
    ax = axes[idx]
    
    x_pos = [0, 1]
    sim_vals = metric_data['simulation'].values
    real_vals = metric_data['real_world'].values
    
    ax.bar([x - 0.2 for x in x_pos], sim_vals, width=0.4, label='Simulation', alpha=0.8)
    ax.bar([x + 0.2 for x in x_pos], real_vals, width=0.4, label='Real-World', alpha=0.8)
    
    ax.set_xlabel('Policy')
    ax.set_ylabel('Value')
    ax.set_title(f'{metric.replace("_", " ").title()}')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(['pi_base', 'pi_new'])
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/positive_metrics.png', dpi=300, bbox_inches='tight')
plt.close()

# Negative metrics plot (lower is better)
fig, axes = plt.subplots(3, 2, figsize=(14, 12))
fig.suptitle('Metrics Where Lower Values Are Better', fontsize=14, fontweight='bold')

axes = axes.flatten()
for idx, metric in enumerate(negative_metrics):
    metric_data = df[df['metric'] == metric]
    ax = axes[idx]
    
    x_pos = [0, 1]
    sim_vals = metric_data['simulation'].values
    real_vals = metric_data['real_world'].values
    
    ax.bar([x - 0.2 for x in x_pos], sim_vals, width=0.4, label='Simulation', alpha=0.8)
    ax.bar([x + 0.2 for x in x_pos], real_vals, width=0.4, label='Real-World', alpha=0.8)
    
    ax.set_xlabel('Policy')
    ax.set_ylabel('Value')
    ax.set_title(f'{metric.replace("_", " ").title()}')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(['pi_base', 'pi_new'])
    ax.legend()
    ax.grid(True, alpha=0.3)

# Remove empty subplot if needed
if len(negative_metrics) < len(axes):
    for i in range(len(negative_metrics), len(axes)):
        fig.delaxes(axes[i])

plt.tight_layout()
plt.savefig('../report/images/negative_metrics.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Create a radar chart for comprehensive comparison
from math import pi

# Normalize data for radar chart (0-1 scale)
def normalize_series(series, higher_better=True):
    if higher_better:
        return (series - series.min()) / (series.max() - series.min() + 1e-10)
    else:
        # For metrics where lower is better, invert the normalization
        return 1 - (series - series.min()) / (series.max() - series.min() + 1e-10)

# Prepare data for radar chart
categories = list(metrics)
N = len(categories)

# Normalize each metric appropriately
sim_base_norm = []
sim_new_norm = []
real_base_norm = []
real_new_norm = []

for metric in categories:
    metric_data = df[df['metric'] == metric]
    
    # Determine if higher is better
    higher_better = metric in positive_metrics
    
    # Normalize simulation values
    sim_series = metric_data.set_index('arm')['simulation']
    sim_base_norm.append(normalize_series(pd.Series([sim_series['pi_base']]), higher_better).iloc[0])
    sim_new_norm.append(normalize_series(pd.Series([sim_series['pi_new']]), higher_better).iloc[0])
    
    # Normalize real-world values
    real_series = metric_data.set_index('arm')['real_world']
    real_base_norm.append(normalize_series(pd.Series([real_series['pi_base']]), higher_better).iloc[0])
    real_new_norm.append(normalize_series(pd.Series([real_series['pi_new']]), higher_better).iloc[0])

# Complete the circle
sim_base_norm += sim_base_norm[:1]
sim_new_norm += sim_new_norm[:1]
real_base_norm += real_base_norm[:1]
real_new_norm += real_new_norm[:1]

# Create radar chart
angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, polar=True)

ax.plot(angles, sim_base_norm, 'o-', linewidth=2, label='pi_base (Sim)')
ax.fill(angles, sim_base_norm, alpha=0.25)
ax.plot(angles, sim_new_norm, 'o-', linewidth=2, label='pi_new (Sim)')
ax.fill(angles, sim_new_norm, alpha=0.25)
ax.plot(angles, real_base_norm, 's-', linewidth=2, label='pi_base (Real)')
ax.plot(angles, real_new_norm, 's-', linewidth=2, label='pi_new (Real)')

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories)
ax.set_ylim(0, 1)
ax.set_title('Normalized Performance Comparison (Radar Chart)', size=15, y=1.1)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
ax.grid(True)

plt.tight_layout()
plt.savefig('../report/images/radar_chart_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 5. Create a summary table visualization
fig, ax = plt.subplots(figsize=(12, 8))
ax.axis('tight')
ax.axis('off')

# Prepare summary data
summary_data = []
for metric in metrics:
    metric_data = df[df['metric'] == metric]
    sim_base = metric_data[metric_data['arm'] == 'pi_base']['simulation'].values[0]
    sim_new = metric_data[metric_data['arm'] == 'pi_new']['simulation'].values[0]
    real_base = metric_data[metric_data['arm'] == 'pi_base']['real_world'].values[0]
    real_new = metric_data[metric_data['arm'] == 'pi_new']['real_world'].values[0]
    
    sim_diff = sim_new - sim_base
    real_diff = real_new - real_base
    
    # Determine if pi_new is better
    higher_better = metric in positive_metrics
    sim_better = (sim_diff > 0) if higher_better else (sim_diff < 0)
    real_better = (real_diff > 0) if higher_better else (real_diff < 0)
    
    summary_data.append([
        metric.replace('_', ' ').title(),
        f'{sim_base:.3f}',
        f'{sim_new:.3f}',
        f'{sim_diff:+.3f}',
        '✓' if sim_better else '✗',
        f'{real_base:.3f}',
        f'{real_new:.3f}',
        f'{real_diff:+.3f}',
        '✓' if real_better else '✗'
    ])

# Create table
table = ax.table(cellText=summary_data,
                 colLabels=['Metric', 'Sim Base', 'Sim New', 'Δ Sim', 'Better?', 
                           'Real Base', 'Real New', 'Δ Real', 'Better?'],
                 cellLoc='center',
                 loc='center',
                 colWidths=[0.15, 0.08, 0.08, 0.08, 0.06, 0.08, 0.08, 0.08, 0.06])

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.5)

# Color code the 'Better?' cells
for i in range(1, len(summary_data) + 1):
    # Simulation better cell
    if summary_data[i-1][4] == '✓':
        table[(i, 4)].set_facecolor('#90EE90')  # Light green
    else:
        table[(i, 4)].set_facecolor('#FFB6C1')  # Light red
    
    # Real-world better cell
    if summary_data[i-1][8] == '✓':
        table[(i, 8)].set_facecolor('#90EE90')  # Light green
    else:
        table[(i, 8)].set_facecolor('#FFB6C1')  # Light red

plt.title('Policy Performance Summary Table', fontsize=14, fontweight='bold', pad=20)
plt.savefig('../report/images/summary_table.png', dpi=300, bbox_inches='tight')
plt.close()

print("All visualizations created and saved to report/images/")