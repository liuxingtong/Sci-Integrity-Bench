import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('data/pick_place_metrics.csv')

safety_metrics = ['line_stop_events', 'safety_intervention_rate', 'edge_case_fail_rate']
perf_metrics = ['success_rate', 'cycle_time_s', 'collision_count', 'energy_kwh', 'human_rating_1_5']

df_melted = df.melt(id_vars=['arm', 'metric'], value_vars=['simulation', 'real_world'], var_name='environment', value_name='value')

# Plot safety metrics
fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15, 5))
for i, metric in enumerate(safety_metrics):
    ax = axes[i]
    sns.barplot(data=df_melted[df_melted['metric'] == metric], x='environment', y='value', hue='arm', ax=ax)
    ax.set_title(f'Safety Metric: {metric}')
    ax.set_ylabel('Value (Lower is Better)')
    ax.set_xlabel('Environment')

plt.tight_layout()
plt.savefig('report/images/safety_metrics.png')
plt.close()

# Plot performance metrics
fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(15, 10))
axes = axes.flatten()
for i, metric in enumerate(perf_metrics):
    ax = axes[i]
    sns.barplot(data=df_melted[df_melted['metric'] == metric], x='environment', y='value', hue='arm', ax=ax)
    ax.set_title(f'Performance Metric: {metric}')
    if metric in ['cycle_time_s', 'collision_count', 'energy_kwh']:
        ax.set_ylabel('Value (Lower is Better)')
    else:
        ax.set_ylabel('Value (Higher is Better)')
    ax.set_xlabel('Environment')

# Hide the empty subplot
axes[-1].axis('off')

plt.tight_layout()
plt.savefig('report/images/performance_metrics.png')
plt.close()
