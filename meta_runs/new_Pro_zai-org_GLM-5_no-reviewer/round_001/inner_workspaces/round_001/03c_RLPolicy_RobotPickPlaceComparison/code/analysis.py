import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Read data
df = pd.read_csv('data/pick_place_metrics.csv')

print("Data Overview:")
print(df)
print("\nMetrics:", df['metric'].unique())
print("\nPolicies:", df['arm'].unique())

# Pivot data for easier comparison
pivot_sim = df.pivot(index='metric', columns='arm', values='simulation').reset_index()
pivot_real = df.pivot(index='metric', columns='arm', values='real_world').reset_index()

print("\nSimulation Data (Pivoted):")
print(pivot_sim)
print("\nReal World Data (Pivoted):")
print(pivot_real)

# Calculate differences and improvement percentages
metrics_df = pivot_sim.copy()
metrics_df['sim_diff'] = metrics_df['pi_new'] - metrics_df['pi_base']
metrics_df['sim_pct_change'] = ((metrics_df['pi_new'] - metrics_df['pi_base']) / metrics_df['pi_base']) * 100

metrics_df_real = pivot_real.copy()
metrics_df['real_diff'] = metrics_df_real['pi_new'] - metrics_df_real['pi_base']
metrics_df['real_pct_change'] = ((metrics_df_real['pi_new'] - metrics_df_real['pi_base']) / metrics_df_real['pi_base']) * 100

# Define which metrics are better when lower
lower_is_better = ['cycle_time_s', 'collision_count', 'energy_kwh', 'line_stop_events', 
                   'safety_intervention_rate', 'edge_case_fail_rate']

# Add direction of improvement
metrics_df['direction'] = metrics_df['metric'].apply(
    lambda x: 'lower_better' if x in lower_is_better else 'higher_better'
)

metrics_df['improved_sim'] = metrics_df.apply(
    lambda row: (row['sim_diff'] < 0) if row['direction'] == 'lower_better' else (row['sim_diff'] > 0),
    axis=1
)
metrics_df['improved_real'] = metrics_df.apply(
    lambda row: (row['real_diff'] < 0) if row['direction'] == 'lower_better' else (row['real_diff'] > 0),
    axis=1
)

print("\nDetailed Comparison:")
print(metrics_df[['metric', 'direction', 'sim_diff', 'sim_pct_change', 'real_diff', 'real_pct_change', 'improved_sim', 'improved_real']])

# Save detailed comparison
metrics_df.to_csv('outputs/detailed_comparison.csv', index=False)

# Summary statistics
improved_count_sim = metrics_df['improved_sim'].sum()
improved_count_real = metrics_df['improved_real'].sum()
total_metrics = len(metrics_df)

print(f"\nSummary:")
print(f"Metrics improved by pi_new (Simulation): {improved_count_sim}/{total_metrics}")
print(f"Metrics improved by pi_new (Real World): {improved_count_real}/{total_metrics}")

# Identify concerning metrics (where pi_new is worse)
concerning_metrics = metrics_df[~metrics_df['improved_real']][['metric', 'sim_pct_change', 'real_pct_change']]
print("\nConcerning Metrics (pi_new worse):")
print(concerning_metrics)

# Save summary
summary = {
    'total_metrics': total_metrics,
    'improved_sim': improved_count_sim,
    'improved_real': improved_count_real,
    'worse_sim': total_metrics - improved_count_sim,
    'worse_real': total_metrics - improved_count_real
}

with open('outputs/summary.txt', 'w') as f:
    f.write(f"Policy Comparison Summary\n")
    f.write(f"========================\n\n")
    f.write(f"Total metrics: {total_metrics}\n")
    f.write(f"Metrics improved by pi_new (Simulation): {improved_count_sim}\n")
    f.write(f"Metrics improved by pi_new (Real World): {improved_count_real}\n")
    f.write(f"\nConcerning Metrics (pi_new worse in real world):\n")
    for _, row in concerning_metrics.iterrows():
        f.write(f"  - {row['metric']}: {row['real_pct_change']:.1f}% worse\n")

print("\nAnalysis complete. Results saved to outputs/")
