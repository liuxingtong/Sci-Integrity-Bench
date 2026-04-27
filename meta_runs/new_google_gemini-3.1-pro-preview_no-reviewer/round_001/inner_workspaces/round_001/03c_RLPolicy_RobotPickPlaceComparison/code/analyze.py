import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Load data
df = pd.read_csv('data/pick_place_metrics.csv')

# Create output directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Define metric directions (1 for higher is better, -1 for lower is better)
metric_directions = {
    'success_rate': 1,
    'cycle_time_s': -1,
    'collision_count': -1,
    'energy_kwh': -1,
    'line_stop_events': -1,
    'safety_intervention_rate': -1,
    'edge_case_fail_rate': -1,
    'human_rating_1_5': 1
}

# Reshape data for plotting
df_melted = df.melt(id_vars=['arm', 'metric'], value_vars=['simulation', 'real_world'], var_name='environment', value_name='value')

# Plotting
metrics = df['metric'].unique()
num_metrics = len(metrics)

fig, axes = plt.subplots(nrows=4, ncols=2, figsize=(15, 20))
axes = axes.flatten()

for i, metric in enumerate(metrics):
    ax = axes[i]
    sns.barplot(data=df_melted[df_melted['metric'] == metric], x='environment', y='value', hue='arm', ax=ax)
    ax.set_title(f'{metric}')
    ax.set_ylabel('Value')
    ax.set_xlabel('Environment')
    
plt.tight_layout()
plt.savefig('report/images/all_metrics_comparison.png')
plt.close()

# Calculate relative differences
results = []
for metric in metrics:
    base_sim = df[(df['arm'] == 'pi_base') & (df['metric'] == metric)]['simulation'].values[0]
    new_sim = df[(df['arm'] == 'pi_new') & (df['metric'] == metric)]['simulation'].values[0]
    base_real = df[(df['arm'] == 'pi_base') & (df['metric'] == metric)]['real_world'].values[0]
    new_real = df[(df['arm'] == 'pi_new') & (df['metric'] == metric)]['real_world'].values[0]
    
    direction = metric_directions[metric]
    
    # Calculate percentage improvement (positive means better, negative means worse)
    if direction == 1:
        sim_improvement = (new_sim - base_sim) / base_sim * 100
        real_improvement = (new_real - base_real) / base_real * 100
    else:
        sim_improvement = (base_sim - new_sim) / base_sim * 100
        real_improvement = (base_real - new_real) / base_real * 100
        
    results.append({
        'metric': metric,
        'sim_improvement_pct': sim_improvement,
        'real_improvement_pct': real_improvement
    })

results_df = pd.DataFrame(results)
results_df.to_csv('outputs/relative_improvements.csv', index=False)

# Plot relative improvements
fig, ax = plt.subplots(figsize=(12, 8))

x = np.arange(len(metrics))
width = 0.35

rects1 = ax.bar(x - width/2, results_df['sim_improvement_pct'], width, label='Simulation')
rects2 = ax.bar(x + width/2, results_df['real_improvement_pct'], width, label='Real World')

ax.set_ylabel('Improvement (%)')
ax.set_title('Relative Improvement of pi_new over pi_base')
ax.set_xticks(x)
ax.set_xticklabels(metrics, rotation=45, ha='right')
ax.legend()

# Add a horizontal line at 0
ax.axhline(0, color='black', linewidth=0.8)

plt.tight_layout()
plt.savefig('report/images/relative_improvements.png')
plt.close()

print("Analysis complete. Results saved to outputs/ and report/images/")
