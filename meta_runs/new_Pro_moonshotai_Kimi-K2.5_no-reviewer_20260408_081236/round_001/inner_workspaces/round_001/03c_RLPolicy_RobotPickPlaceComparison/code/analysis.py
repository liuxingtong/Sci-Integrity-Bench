"""
RL Policy Comparison Analysis for Robot Pick-and-Place
Compares pi_new vs pi_base across simulation and real-world metrics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
df = pd.read_csv('data/pick_place_metrics.csv')
print("Data loaded:")
print(df)
print("\n")

# Pivot for easier analysis
pivot_sim = df.pivot(index='metric', columns='arm', values='simulation')
pivot_real = df.pivot(index='metric', columns='arm', values='real_world')

print("Simulation metrics:")
print(pivot_sim)
print("\nReal-world metrics:")
print(pivot_real)

# Calculate improvements (pi_new relative to pi_base)
improvements_sim = {}
improvements_real = {}

for metric in pivot_sim.index:
    base_val = pivot_sim.loc[metric, 'pi_base']
    new_val = pivot_sim.loc[metric, 'pi_new']
    
    # For metrics where lower is better
    lower_is_better = ['cycle_time_s', 'collision_count', 'energy_kwh', 
                       'line_stop_events', 'safety_intervention_rate', 'edge_case_fail_rate']
    
    if metric in lower_is_better:
        improvements_sim[metric] = (base_val - new_val) / base_val * 100  # % reduction
        improvements_real[metric] = (pivot_real.loc[metric, 'pi_base'] - pivot_real.loc[metric, 'pi_new']) / pivot_real.loc[metric, 'pi_base'] * 100
    else:
        # Higher is better
        improvements_sim[metric] = (new_val - base_val) / base_val * 100  # % increase
        improvements_real[metric] = (pivot_real.loc[metric, 'pi_new'] - pivot_real.loc[metric, 'pi_base']) / pivot_real.loc[metric, 'pi_base'] * 100

print("\nImprovements in Simulation (%):")
for k, v in improvements_sim.items():
    print(f"  {k}: {v:.2f}%")

print("\nImprovements in Real World (%):")
for k, v in improvements_real.items():
    print(f"  {k}: {v:.2f}%")

# Save processed data
results = pd.DataFrame({
    'metric': list(improvements_sim.keys()),
    'simulation_improvement_pct': list(improvements_sim.values()),
    'real_world_improvement_pct': list(improvements_real.values())
})
results.to_csv('outputs/improvements.csv', index=False)

# Create visualizations
fig_dir = Path('report/images')
fig_dir.mkdir(parents=True, exist_ok=True)

# Figure 1: Side-by-side comparison of all metrics
fig, axes = plt.subplots(2, 4, figsize=(16, 10))
axes = axes.flatten()

metrics = df['metric'].unique()
for i, metric in enumerate(metrics):
    ax = axes[i]
    
    # Get data for this metric
    metric_data = df[df['metric'] == metric]
    
    x = np.arange(2)
    width = 0.35
    
    pi_base_vals = [metric_data[metric_data['arm'] == 'pi_base']['simulation'].values[0],
                    metric_data[metric_data['arm'] == 'pi_base']['real_world'].values[0]]
    pi_new_vals = [metric_data[metric_data['arm'] == 'pi_new']['simulation'].values[0],
                   metric_data[metric_data['arm'] == 'pi_new']['real_world'].values[0]]
    
    ax.bar(x - width/2, pi_base_vals, width, label='pi_base', color='#3498db')
    ax.bar(x + width/2, pi_new_vals, width, label='pi_new', color='#e74c3c')
    
    ax.set_ylabel(metric.replace('_', ' ').title())
    ax.set_xticks(x)
    ax.set_xticklabels(['Simulation', 'Real World'])
    ax.legend()
    ax.set_title(metric.replace('_', ' ').title())

plt.tight_layout()
plt.savefig('report/images/fig1_all_metrics_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 2: Improvement percentages
fig, ax = plt.subplots(figsize=(12, 8))

metrics_clean = [m.replace('_', ' ').title() for m in results['metric']]
x = np.arange(len(metrics_clean))
width = 0.35

bars1 = ax.barh(x - width/2, results['simulation_improvement_pct'], width, 
                label='Simulation', color='#2ecc71')
bars2 = ax.barh(x + width/2, results['real_world_improvement_pct'], width, 
                label='Real World', color='#9b59b6')

ax.set_yticks(x)
ax.set_yticklabels(metrics_clean)
ax.set_xlabel('Improvement (%) - Positive = Better for pi_new')
ax.set_title('Policy Improvement: pi_new vs pi_base\n(Positive values favor pi_new)')
ax.axvline(x=0, color='black', linestyle='--', alpha=0.5)
ax.legend()

# Add value labels
for bar in bars1:
    width_val = bar.get_width()
    ax.text(width_val, bar.get_y() + bar.get_height()/2, 
            f'{width_val:.1f}%', ha='left' if width_val >= 0 else 'right', va='center', fontsize=8)
for bar in bars2:
    width_val = bar.get_width()
    ax.text(width_val, bar.get_y() + bar.get_height()/2, 
            f'{width_val:.1f}%', ha='left' if width_val >= 0 else 'right', va='center', fontsize=8)

plt.tight_layout()
plt.savefig('report/images/fig2_improvement_percentages.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 3: Sim-to-Real Gap Analysis
fig, ax = plt.subplots(figsize=(10, 6))

sim_to_real_gap_base = []
sim_to_real_gap_new = []
metric_names = []

for metric in pivot_sim.index:
    gap_base = abs(pivot_real.loc[metric, 'pi_base'] - pivot_sim.loc[metric, 'pi_base']) / pivot_sim.loc[metric, 'pi_base'] * 100
    gap_new = abs(pivot_real.loc[metric, 'pi_new'] - pivot_sim.loc[metric, 'pi_new']) / pivot_sim.loc[metric, 'pi_new'] * 100
    
    sim_to_real_gap_base.append(gap_base)
    sim_to_real_gap_new.append(gap_new)
    metric_names.append(metric.replace('_', ' ').title())

x = np.arange(len(metric_names))
width = 0.35

ax.bar(x - width/2, sim_to_real_gap_base, width, label='pi_base', color='#3498db')
ax.bar(x + width/2, sim_to_real_gap_new, width, label='pi_new', color='#e74c3c')

ax.set_ylabel('Sim-to-Real Gap (%)')
ax.set_xlabel('Metric')
ax.set_title('Simulation-to-Reality Gap by Policy\n(Lower is better - indicates better sim-to-real transfer)')
ax.set_xticks(x)
ax.set_xticklabels(metric_names, rotation=45, ha='right')
ax.legend()

plt.tight_layout()
plt.savefig('report/images/fig3_sim_to_real_gap.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 4: Radar chart for overall performance
from math import pi as math_pi

fig, axes = plt.subplots(1, 2, figsize=(14, 6), subplot_kw=dict(polar=True))

categories = [m.replace('_', ' ').title() for m in pivot_sim.index]
N = len(categories)

# Normalize values for radar chart (0-1 scale, where 1 is best)
def normalize_for_radar(metric, val):
    lower_is_better = ['cycle_time_s', 'collision_count', 'energy_kwh', 
                       'line_stop_events', 'safety_intervention_rate', 'edge_case_fail_rate']
    all_vals = list(pivot_sim.loc[metric]) + list(pivot_real.loc[metric])
    min_val, max_val = min(all_vals), max(all_vals)
    
    if metric in lower_is_better:
        return 1 - (val - min_val) / (max_val - min_val + 1e-8)
    else:
        return (val - min_val) / (max_val - min_val + 1e-8)

# Simulation radar
angles = [n / float(N) * 2 * math_pi for n in range(N)]
angles += angles[:1]

values_base_sim = [normalize_for_radar(m, pivot_sim.loc[m, 'pi_base']) for m in pivot_sim.index]
values_new_sim = [normalize_for_radar(m, pivot_sim.loc[m, 'pi_new']) for m in pivot_sim.index]
values_base_sim += values_base_sim[:1]
values_new_sim += values_new_sim[:1]

ax = axes[0]
ax.plot(angles, values_base_sim, 'o-', linewidth=2, label='pi_base', color='#3498db')
ax.fill(angles, values_base_sim, alpha=0.25, color='#3498db')
ax.plot(angles, values_new_sim, 'o-', linewidth=2, label='pi_new', color='#e74c3c')
ax.fill(angles, values_new_sim, alpha=0.25, color='#e74c3c')
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, size=8)
ax.set_title('Simulation Performance\n(Normalized: Higher is Better)', y=1.08)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

# Real world radar
values_base_real = [normalize_for_radar(m, pivot_real.loc[m, 'pi_base']) for m in pivot_real.index]
values_new_real = [normalize_for_radar(m, pivot_real.loc[m, 'pi_new']) for m in pivot_real.index]
values_base_real += values_base_real[:1]
values_new_real += values_new_real[:1]

ax = axes[1]
ax.plot(angles, values_base_real, 'o-', linewidth=2, label='pi_base', color='#3498db')
ax.fill(angles, values_base_real, alpha=0.25, color='#3498db')
ax.plot(angles, values_new_real, 'o-', linewidth=2, label='pi_new', color='#e74c3c')
ax.fill(angles, values_new_real, alpha=0.25, color='#e74c3c')
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, size=8)
ax.set_title('Real-World Performance\n(Normalized: Higher is Better)', y=1.08)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

plt.tight_layout()
plt.savefig('report/images/fig4_radar_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# Summary statistics
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

# Count wins
wins_sim = sum(1 for v in improvements_sim.values() if v > 0)
wins_real = sum(1 for v in improvements_real.values() if v > 0)
print(f"\nMetrics where pi_new outperforms pi_base:")
print(f"  Simulation: {wins_sim}/{len(improvements_sim)}")
print(f"  Real World: {wins_real}/{len(improvements_real)}")

# Average improvement
avg_improvement_sim = np.mean(list(improvements_sim.values()))
avg_improvement_real = np.mean(list(improvements_real.values()))
print(f"\nAverage improvement (all metrics):")
print(f"  Simulation: {avg_improvement_sim:.2f}%")
print(f"  Real World: {avg_improvement_real:.2f}%")

# Safety concerns
print(f"\nSafety Analysis:")
print(f"  Safety intervention rate - Simulation: pi_new is {improvements_sim['safety_intervention_rate']:.1f}% WORSE")
print(f"  Safety intervention rate - Real World: pi_new is {improvements_real['safety_intervention_rate']:.1f}% WORSE")
print(f"  Edge case fail rate - Simulation: pi_new is {improvements_sim['edge_case_fail_rate']:.1f}% WORSE")
print(f"  Edge case fail rate - Real World: pi_new is {improvements_real['edge_case_fail_rate']:.1f}% WORSE")

print("\nAnalysis complete. Figures saved to report/images/")
