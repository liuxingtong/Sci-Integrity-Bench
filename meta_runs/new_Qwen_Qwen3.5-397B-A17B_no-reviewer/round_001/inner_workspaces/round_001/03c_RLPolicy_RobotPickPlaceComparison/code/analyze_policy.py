import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Read data
df = pd.read_csv('data/pick_place_metrics.csv')

# Create output directories if not exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Pivot data for easier analysis
df_pivot = df.pivot(index='metric', columns='arm', values=['simulation', 'real_world'])

print("=== Data Overview ===")
print(df)
print("\n=== Pivoted Data ===")
print(df_pivot)

# Metrics interpretation
metrics_better_higher = ['success_rate', 'human_rating_1_5']
metrics_better_lower = ['cycle_time_s', 'collision_count', 'energy_kwh', 
                        'line_stop_events', 'safety_intervention_rate', 'edge_case_fail_rate']

# Calculate improvement percentages (pi_new vs pi_base)
improvements = {}
for metric in df['metric'].unique():
    base_sim = df[(df['arm']=='pi_base') & (df['metric']==metric)]['simulation'].values[0]
    new_sim = df[(df['arm']=='pi_new') & (df['metric']==metric)]['simulation'].values[0]
    base_real = df[(df['arm']=='pi_base') & (df['metric']==metric)]['real_world'].values[0]
    new_real = df[(df['arm']=='pi_new') & (df['metric']==metric)]['real_world'].values[0]
    
    if metric in metrics_better_higher:
        imp_sim = (new_sim - base_sim) / base_sim * 100
        imp_real = (new_real - base_real) / base_real * 100
    else:
        imp_sim = (base_sim - new_sim) / base_sim * 100
        imp_real = (base_real - new_real) / base_real * 100
    
    improvements[metric] = {'simulation': imp_sim, 'real_world': imp_real}

print("\n=== Improvement Analysis (pi_new vs pi_base, % better) ===")
for metric, imp in improvements.items():
    print(f"{metric}: Sim={imp['simulation']:.2f}%, Real={imp['real_world']:.2f}%")

# Figure 1: Bar chart comparing pi_base vs pi_new for all metrics
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

metrics_list = df['metric'].unique()
for i, metric in enumerate(metrics_list):
    ax = axes[i]
    base_sim = df[(df['arm']=='pi_base') & (df['metric']==metric)]['simulation'].values[0]
    new_sim = df[(df['arm']=='pi_new') & (df['metric']==metric)]['simulation'].values[0]
    base_real = df[(df['arm']=='pi_base') & (df['metric']==metric)]['real_world'].values[0]
    new_real = df[(df['arm']=='pi_new') & (df['metric']==metric)]['real_world'].values[0]
    
    x = np.arange(2)
    width = 0.35
    
    bars1 = ax.bar(x - width/2, [base_sim, base_real], width, label='pi_base', color='#1f77b4')
    bars2 = ax.bar(x + width/2, [new_sim, new_real], width, label='pi_new', color='#ff7f0e')
    
    ax.set_ylabel('Value')
    ax.set_title(metric.replace('_', ' '))
    ax.set_xticks(x)
    ax.set_xticklabels(['Simulation', 'Real World'])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/metrics_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/metrics_comparison.png")

# Figure 2: Improvement percentage plot
fig, ax = plt.subplots(figsize=(12, 6))

metric_names = [m.replace('_', ' ') for m in improvements.keys()]
x = np.arange(len(metric_names))
width = 0.35

sim_imps = [improvements[m]['simulation'] for m in improvements.keys()]
real_imps = [improvements[m]['real_world'] for m in improvements.keys()]

bars1 = ax.bar(x - width/2, sim_imps, width, label='Simulation', color='#2ca02c')
bars2 = ax.bar(x + width/2, real_imps, width, label='Real World', color='#d62728')

ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.set_ylabel('Improvement (%)')
ax.set_title('pi_new vs pi_base: Improvement by Metric (Positive = pi_new is better)')
ax.set_xticks(x)
ax.set_xticklabels(metric_names, rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/improvement_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/improvement_analysis.png")

# Figure 3: Radar chart for overall comparison
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

metrics_for_radar = ['success_rate', 'cycle_time_s', 'collision_count', 'energy_kwh', 
                     'safety_intervention_rate', 'edge_case_fail_rate', 'human_rating_1_5']
n = len(metrics_for_radar)
angles = [i * 2 * np.pi / n for i in range(n)]
angles += angles[:1]

def get_radar_values(arm, env):
    values = []
    for metric in metrics_for_radar:
        val = df[(df['arm']==arm) & (df['metric']==metric)][env].values[0]
        max_val = df[df['metric']==metric][env].max()
        if metric in metrics_better_higher:
            norm_val = val / max_val
        else:
            norm_val = 1 - (val / max_val)
        values.append(norm_val)
    values += values[:1]
    return values

base_sim_vals = get_radar_values('pi_base', 'simulation')
new_sim_vals = get_radar_values('pi_new', 'simulation')

ax.plot(angles, base_sim_vals, 'o-', linewidth=2, label='pi_base', color='#1f77b4', alpha=0.7)
ax.fill(angles, base_sim_vals, alpha=0.15, color='#1f77b4')
ax.plot(angles, new_sim_vals, 'o-', linewidth=2, label='pi_new', color='#ff7f0e', alpha=0.7)
ax.fill(angles, new_sim_vals, alpha=0.15, color='#ff7f0e')

ax.set_xticks(angles[:-1])
ax.set_xticklabels([m.replace('_', '\n') for m in metrics_for_radar], size=9)
ax.set_ylim(0, 1.1)
ax.set_title('Policy Comparison Radar Chart (Normalized)', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
ax.grid(True)

plt.tight_layout()
plt.savefig('report/images/radar_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/radar_comparison.png")

# Figure 4: Sim vs Real gap analysis
fig, ax = plt.subplots(figsize=(10, 6))

metric_names = [m.replace('_', ' ') for m in metrics_list]
x = np.arange(len(metric_names))
width = 0.35

gap_base = []
gap_new = []
for metric in metrics_list:
    base_sim = df[(df['arm']=='pi_base') & (df['metric']==metric)]['simulation'].values[0]
    base_real = df[(df['arm']=='pi_base') & (df['metric']==metric)]['real_world'].values[0]
    new_sim = df[(df['arm']=='pi_new') & (df['metric']==metric)]['simulation'].values[0]
    new_real = df[(df['arm']=='pi_new') & (df['metric']==metric)]['real_world'].values[0]
    
    gap_b = abs(base_sim - base_real) / base_sim * 100 if base_sim != 0 else 0
    gap_n = abs(new_sim - new_real) / new_sim * 100 if new_sim != 0 else 0
    gap_base.append(gap_b)
    gap_new.append(gap_n)

bars1 = ax.bar(x - width/2, gap_base, width, label='pi_base Gap', color='#1f77b4')
bars2 = ax.bar(x + width/2, gap_new, width, label='pi_new Gap', color='#ff7f0e')

ax.set_ylabel('Sim-Real Gap (%)')
ax.set_title('Simulation to Real-World Performance Gap by Metric')
ax.set_xticks(x)
ax.set_xticklabels(metric_names, rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/sim_real_gap.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/sim_real_gap.png")

print("\n=== Analysis Complete ===")
