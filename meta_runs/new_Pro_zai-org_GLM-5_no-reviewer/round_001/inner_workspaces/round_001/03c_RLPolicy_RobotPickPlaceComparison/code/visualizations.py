import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read data
df = pd.read_csv('data/pick_place_metrics.csv')

# Create figure directory
os.makedirs('report/images', exist_ok=True)

# Define metric categories
lower_is_better = ['cycle_time_s', 'collision_count', 'energy_kwh', 'line_stop_events', 
                   'safety_intervention_rate', 'edge_case_fail_rate']
higher_is_better = ['success_rate', 'human_rating_1_5']

# Pivot data
pivot_sim = df.pivot(index='metric', columns='arm', values='simulation')
pivot_real = df.pivot(index='metric', columns='arm', values='real_world')

# Calculate percentage changes
pct_change_sim = ((pivot_sim['pi_new'] - pivot_sim['pi_base']) / pivot_sim['pi_base'] * 100)
pct_change_real = ((pivot_real['pi_new'] - pivot_real['pi_base']) / pivot_real['pi_base'] * 100)

# Figure 1: Grouped bar chart for all metrics
fig, axes = plt.subplots(2, 4, figsize=(16, 10))
axes = axes.flatten()

metrics = df['metric'].unique()
colors = {'pi_base': '#3498db', 'pi_new': '#e74c3c'}

for idx, metric in enumerate(metrics):
    ax = axes[idx]
    metric_data = df[df['metric'] == metric]
    
    x = np.arange(2)
    width = 0.35
    
    bars1 = ax.bar(x - width/2, [metric_data[metric_data['arm']=='pi_base']['simulation'].values[0],
                                   metric_data[metric_data['arm']=='pi_base']['real_world'].values[0]],
                   width, label='pi_base', color=colors['pi_base'], alpha=0.8)
    bars2 = ax.bar(x + width/2, [metric_data[metric_data['arm']=='pi_new']['simulation'].values[0],
                                   metric_data[metric_data['arm']=='pi_new']['real_world'].values[0]],
                   width, label='pi_new', color=colors['pi_new'], alpha=0.8)
    
    ax.set_ylabel('Value')
    ax.set_title(metric.replace('_', ' ').title(), fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['Simulation', 'Real World'])
    ax.legend(loc='best', fontsize=8)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=7)
    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=7)

plt.suptitle('Policy Comparison: pi_base vs pi_new\nAcross All Metrics', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('report/images/metric_comparison_bars.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure 1 saved: metric_comparison_bars.png")

# Figure 2: Percentage change heatmap
fig, ax = plt.subplots(figsize=(10, 8))

change_df = pd.DataFrame({
    'Simulation (%)': pct_change_sim,
    'Real World (%)': pct_change_real
})

# Add direction indicator
change_df['Direction'] = ['Lower is Better' if m in lower_is_better else 'Higher is Better' 
                          for m in change_df.index]

# Create heatmap data
heatmap_data = change_df[['Simulation (%)', 'Real World (%)']].values

# Create custom colormap (red for worse, green for better)
cmap = sns.diverging_palette(10, 130, s=80, l=55, as_cmap=True)

# Create annotations with direction
annot = []
for i, metric in enumerate(change_df.index):
    direction = '↓' if metric in lower_is_better else '↑'
    row = [f'{heatmap_data[i, 0]:.1f}% {direction}', f'{heatmap_data[i, 1]:.1f}% {direction}']
    annot.append(row)

sns.heatmap(heatmap_data, annot=annot, fmt='', cmap=cmap, center=0,
            xticklabels=['Simulation', 'Real World'],
            yticklabels=[m.replace('_', ' ').title() for m in change_df.index],
            ax=ax, cbar_kws={'label': 'Percentage Change (%)'})

ax.set_title('Percentage Change: pi_new vs pi_base\n(Green = Improvement, Red = Degradation)', 
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/percentage_change_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure 2 saved: percentage_change_heatmap.png")

# Figure 3: Radar chart for performance profile
def normalize_metric(value, metric, all_values):
    """Normalize metric to 0-1 scale, handling direction"""
    min_val = min(all_values)
    max_val = max(all_values)
    if max_val == min_val:
        return 0.5
    normalized = (value - min_val) / (max_val - min_val)
    # If lower is better, invert
    if metric in lower_is_better:
        normalized = 1 - normalized
    return normalized

# Prepare radar data
metrics_list = list(df['metric'].unique())
angles = np.linspace(0, 2 * np.pi, len(metrics_list), endpoint=False).tolist()
angles += angles[:1]  # Complete the circle

fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

for policy in ['pi_base', 'pi_new']:
    values = []
    for metric in metrics_list:
        policy_data = df[(df['metric'] == metric) & (df['arm'] == policy)]
        all_metric_values = df[df['metric'] == metric]['real_world'].values
        norm_val = normalize_metric(policy_data['real_world'].values[0], metric, all_metric_values)
        values.append(norm_val)
    values += values[:1]
    
    ax.plot(angles, values, 'o-', linewidth=2, label=policy)
    ax.fill(angles, values, alpha=0.25)

ax.set_xticks(angles[:-1])
ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics_list], fontsize=9)
ax.set_ylim(0, 1)
ax.set_title('Performance Profile (Real World)\n(Higher = Better Performance)', 
             fontsize=12, fontweight='bold', y=1.1)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

plt.tight_layout()
plt.savefig('report/images/radar_chart.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure 3 saved: radar_chart.png")

# Figure 4: Sim-to-Real Gap Analysis
fig, ax = plt.subplots(figsize=(12, 6))

gap_base = pivot_sim['pi_base'] - pivot_real['pi_base']
gap_new = pivot_sim['pi_new'] - pivot_real['pi_new']

x = np.arange(len(metrics_list))
width = 0.35

bars1 = ax.bar(x - width/2, gap_base, width, label='pi_base', color='#3498db', alpha=0.8)
bars2 = ax.bar(x + width/2, gap_new, width, label='pi_new', color='#e74c3c', alpha=0.8)

ax.set_ylabel('Gap (Simulation - Real World)', fontsize=11)
ax.set_xlabel('Metric', fontsize=11)
ax.set_title('Sim-to-Real Gap Analysis\n(Positive = Simulation overestimates performance)', 
             fontsize=12, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics_list], rotation=45, ha='right')
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.legend()

plt.tight_layout()
plt.savefig('report/images/sim_real_gap.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure 4 saved: sim_real_gap.png")

# Figure 5: Trade-off visualization
fig, ax = plt.subplots(figsize=(10, 8))

# Categorize metrics
improved_metrics = ['success_rate', 'cycle_time_s', 'collision_count', 'energy_kwh', 'human_rating_1_5']
degraded_metrics = ['line_stop_events', 'safety_intervention_rate', 'edge_case_fail_rate']

# Create scatter plot
for i, metric in enumerate(metrics_list):
    sim_change = pct_change_sim[metric]
    real_change = pct_change_real[metric]
    
    color = 'green' if metric in improved_metrics else 'red'
    marker = 'o' if metric in improved_metrics else 's'
    
    ax.scatter(sim_change, real_change, s=200, c=color, marker=marker, alpha=0.7, edgecolors='black')
    ax.annotate(metric.replace('_', '\n'), (sim_change, real_change), 
                textcoords="offset points", xytext=(10, 5), ha='left', fontsize=8)

ax.axhline(y=0, color='gray', linestyle='--', linewidth=1)
ax.axvline(x=0, color='gray', linestyle='--', linewidth=1)

ax.set_xlabel('Simulation % Change', fontsize=11)
ax.set_ylabel('Real World % Change', fontsize=11)
ax.set_title('Trade-off Analysis: pi_new vs pi_base\n(Green = Improved, Red = Degraded)', 
             fontsize=12, fontweight='bold')

# Add quadrant labels
ax.text(100, 100, 'Worse in Both', fontsize=10, ha='center', color='red', alpha=0.5)
ax.text(-50, 100, 'Better Sim, Worse Real', fontsize=10, ha='center', color='orange', alpha=0.5)
ax.text(100, -50, 'Worse Sim, Better Real', fontsize=10, ha='center', color='orange', alpha=0.5)
ax.text(-50, -50, 'Better in Both', fontsize=10, ha='center', color='green', alpha=0.5)

plt.tight_layout()
plt.savefig('report/images/tradeoff_analysis.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure 5 saved: tradeoff_analysis.png")

# Figure 6: Summary comparison chart
fig, ax = plt.subplots(figsize=(12, 6))

# Create a summary showing improvement/degradation
summary_data = []
for metric in metrics_list:
    real_change = pct_change_real[metric]
    direction = 'lower_better' if metric in lower_is_better else 'higher_better'
    
    # Determine if improved or degraded
    if direction == 'lower_better':
        improved = real_change < 0
    else:
        improved = real_change > 0
    
    summary_data.append({
        'metric': metric.replace('_', ' ').title(),
        'change': abs(real_change),
        'status': 'Improved' if improved else 'Degraded',
        'direction': direction
    })

summary_df = pd.DataFrame(summary_data)
summary_df = summary_df.sort_values('change', ascending=True)

colors = {'Improved': '#27ae60', 'Degraded': '#e74c3c'}

bars = ax.barh(summary_df['metric'], summary_df['change'], 
               color=[colors[s] for s in summary_df['status']], alpha=0.8)

# Add value labels
for bar, status, change in zip(bars, summary_df['status'], summary_df['change']):
    width = bar.get_width()
    label = f'{change:.1f}%'
    ax.text(width + 1, bar.get_y() + bar.get_height()/2, label,
            ha='left', va='center', fontsize=9, fontweight='bold')

ax.set_xlabel('Absolute Percentage Change (%)', fontsize=11)
ax.set_title('Real World Performance Change: pi_new vs pi_base\n(Green = Improved, Red = Degraded)', 
             fontsize=12, fontweight='bold')
ax.set_xlim(0, max(summary_df['change']) * 1.3)

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#27ae60', alpha=0.8, label='Improved'),
                   Patch(facecolor='#e74c3c', alpha=0.8, label='Degraded')]
ax.legend(handles=legend_elements, loc='lower right')

plt.tight_layout()
plt.savefig('report/images/summary_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure 6 saved: summary_comparison.png")

print("\nAll visualizations completed successfully!")
