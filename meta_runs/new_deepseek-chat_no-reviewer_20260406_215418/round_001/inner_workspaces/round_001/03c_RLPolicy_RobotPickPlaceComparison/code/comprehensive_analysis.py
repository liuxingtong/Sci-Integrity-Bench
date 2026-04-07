import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

# Load the data
data_path = "../data/pick_place_metrics.csv"
df = pd.read_csv(data_path)
print("Data loaded successfully!")
print(f"Shape: {df.shape}")

# Create output directories
os.makedirs("../outputs", exist_ok=True)
os.makedirs("../report/images", exist_ok=True)

# 1. Create a melted dataframe for easier plotting
df_melted = df.melt(id_vars=['arm', 'metric'], 
                    value_vars=['simulation', 'real_world'],
                    var_name='environment', 
                    value_name='value')

# 2. Calculate improvement percentages for each metric
# For metrics where higher is better (success_rate, human_rating_1_5)
# For metrics where lower is better (all others)
higher_is_better = ['success_rate', 'human_rating_1_5']

improvement_data = []
for metric in df['metric'].unique():
    for env in ['simulation', 'real_world']:
        base_val = df[(df['arm'] == 'pi_base') & (df['metric'] == metric)][env].values[0]
        new_val = df[(df['arm'] == 'pi_new') & (df['metric'] == metric)][env].values[0]
        
        if metric in higher_is_better:
            # Higher is better: improvement = (new - base) / base * 100%
            improvement = ((new_val - base_val) / base_val) * 100
        else:
            # Lower is better: improvement = (base - new) / base * 100%
            improvement = ((base_val - new_val) / base_val) * 100
        
        improvement_data.append({
            'metric': metric,
            'environment': env,
            'improvement_percent': improvement,
            'base_value': base_val,
            'new_value': new_val
        })

df_improvement = pd.DataFrame(improvement_data)

# Save improvement data
df_improvement.to_csv("../outputs/improvement_analysis.csv", index=False)
print("\nImprovement analysis saved to outputs/improvement_analysis.csv")

# 3. Create visualizations
print("\nGenerating visualizations...")

# Figure 1: Comparison of all metrics between policies in both environments
fig, axes = plt.subplots(2, 4, figsize=(20, 12))
axes = axes.flatten()

for idx, metric in enumerate(df['metric'].unique()):
    ax = axes[idx]
    metric_data = df_melted[df_melted['metric'] == metric]
    
    # Create grouped bar plot
    sns.barplot(data=metric_data, x='environment', y='value', hue='arm', ax=ax)
    ax.set_title(f'{metric.replace("_", " ").title()}')
    ax.set_xlabel('Environment')
    ax.set_ylabel('Value')
    
    # Add value labels on bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.3f', padding=3)
    
    # Adjust legend
    if idx == 0:
        ax.legend(title='Policy', loc='upper left')
    else:
        ax.get_legend().remove()

plt.suptitle('Policy Comparison Across All Metrics', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('../report/images/all_metrics_comparison.png', dpi=300, bbox_inches='tight')
print("  - Created: all_metrics_comparison.png")

# Figure 2: Improvement percentage heatmap
plt.figure(figsize=(14, 8))

# Pivot for heatmap
heatmap_data = df_improvement.pivot(index='metric', columns='environment', values='improvement_percent')

# Create custom colormap: green for positive, red for negative
cmap = sns.diverging_palette(10, 130, as_cmap=True)

sns.heatmap(heatmap_data, annot=True, fmt='.2f', cmap=cmap, 
            center=0, linewidths=1, linecolor='gray',
            cbar_kws={'label': 'Improvement % (Positive = Better)'})
plt.title('Percentage Improvement of pi_new over pi_base\n(Positive = Improvement, Negative = Regression)', 
          fontsize=14, fontweight='bold')
plt.xlabel('Environment')
plt.ylabel('Metric')
plt.tight_layout()
plt.savefig('../report/images/improvement_heatmap.png', dpi=300, bbox_inches='tight')
print("  - Created: improvement_heatmap.png")

# Figure 3: Simulation vs Real-world correlation
plt.figure(figsize=(10, 8))

# Prepare data for scatter plot
scatter_data = []
for metric in df['metric'].unique():
    for arm in ['pi_base', 'pi_new']:
        sim_val = df[(df['arm'] == arm) & (df['metric'] == metric)]['simulation'].values[0]
        real_val = df[(df['arm'] == arm) & (df['metric'] == metric)]['real_world'].values[0]
        scatter_data.append({
            'metric': metric,
            'arm': arm,
            'simulation': sim_val,
            'real_world': real_val
        })

df_scatter = pd.DataFrame(scatter_data)

# Create scatter plot
for arm, color in zip(['pi_base', 'pi_new'], ['blue', 'red']):
    arm_data = df_scatter[df_scatter['arm'] == arm]
    plt.scatter(arm_data['simulation'], arm_data['real_world'], 
                label=arm, color=color, s=100, alpha=0.7)
    
    # Add labels for each point
    for _, row in arm_data.iterrows():
        plt.annotate(row['metric'].replace('_', '\n'), 
                    (row['simulation'], row['real_world']),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha='center',
                    fontsize=8)

# Add diagonal line (perfect correlation)
min_val = min(df_scatter['simulation'].min(), df_scatter['real_world'].min())
max_val = max(df_scatter['simulation'].max(), df_scatter['real_world'].max())
plt.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='Perfect Correlation')

plt.xlabel('Simulation Value')
plt.ylabel('Real-world Value')
plt.title('Simulation vs Real-world Performance Correlation', fontsize=14, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/simulation_real_correlation.png', dpi=300, bbox_inches='tight')
print("  - Created: simulation_real_correlation.png")

# Figure 4: Overall performance summary
plt.figure(figsize=(12, 8))

# Calculate overall scores (weighted average)
# Normalize metrics first
normalized_data = []
for _, row in df.iterrows():
    metric = row['metric']
    
    # Get all values for this metric to normalize
    all_vals = df[df['metric'] == metric][['simulation', 'real_world']].values.flatten()
    min_val = all_vals.min()
    max_val = all_vals.max()
    
    # For metrics where higher is better, normalize directly
    if metric in higher_is_better:
        norm_sim = (row['simulation'] - min_val) / (max_val - min_val) if max_val != min_val else 0.5
        norm_real = (row['real_world'] - min_val) / (max_val - min_val) if max_val != min_val else 0.5
    else:
        # For metrics where lower is better, invert normalization
        norm_sim = 1 - (row['simulation'] - min_val) / (max_val - min_val) if max_val != min_val else 0.5
        norm_real = 1 - (row['real_world'] - min_val) / (max_val - min_val) if max_val != min_val else 0.5
    
    normalized_data.append({
        'arm': row['arm'],
        'metric': metric,
        'simulation_norm': norm_sim,
        'real_world_norm': norm_real
    })

df_norm = pd.DataFrame(normalized_data)

# Calculate overall scores
overall_scores = df_norm.groupby('arm')[['simulation_norm', 'real_world_norm']].mean().reset_index()
overall_scores_melted = overall_scores.melt(id_vars=['arm'], 
                                            value_vars=['simulation_norm', 'real_world_norm'],
                                            var_name='environment', 
                                            value_name='score')
overall_scores_melted['environment'] = overall_scores_melted['environment'].replace({
    'simulation_norm': 'Simulation',
    'real_world_norm': 'Real-world'
})

# Create bar plot
ax = sns.barplot(data=overall_scores_melted, x='environment', y='score', hue='arm')
plt.title('Overall Normalized Performance Scores\n(Higher is Better, All Metrics Weighted Equally)', 
          fontsize=14, fontweight='bold')
plt.xlabel('Environment')
plt.ylabel('Normalized Score (0-1)')
plt.ylim(0, 1)

# Add value labels
for container in ax.containers:
    ax.bar_label(container, fmt='%.3f', padding=3)

plt.legend(title='Policy')
plt.tight_layout()
plt.savefig('../report/images/overall_performance_scores.png', dpi=300, bbox_inches='tight')
print("  - Created: overall_performance_scores.png")

# 4. Statistical analysis
print("\n\nStatistical Analysis:")
print("=" * 50)

# Calculate mean improvement across all metrics
mean_improvement_sim = df_improvement[df_improvement['environment'] == 'simulation']['improvement_percent'].mean()
mean_improvement_real = df_improvement[df_improvement['environment'] == 'real_world']['improvement_percent'].mean()

print(f"Mean improvement in simulation: {mean_improvement_sim:.2f}%")
print(f"Mean improvement in real-world: {mean_improvement_real:.2f}%")
print()

# Count improvements vs regressions
improvements_sim = (df_improvement[df_improvement['environment'] == 'simulation']['improvement_percent'] > 0).sum()
improvements_real = (df_improvement[df_improvement['environment'] == 'real_world']['improvement_percent'] > 0).sum()

print(f"Metrics improved in simulation: {improvements_sim}/8 ({improvements_sim/8*100:.1f}%)")
print(f"Metrics improved in real-world: {improvements_real}/8 ({improvements_real/8*100:.1f}%)")
print()

# Identify key trade-offs
print("Key Trade-offs:")
print("-" * 30)
for metric in df['metric'].unique():
    sim_imp = df_improvement[(df_improvement['metric'] == metric) & 
                            (df_improvement['environment'] == 'simulation')]['improvement_percent'].values[0]
    real_imp = df_improvement[(df_improvement['metric'] == metric) & 
                             (df_improvement['environment'] == 'real_world')]['improvement_percent'].values[0]
    
    if sim_imp < -5 or real_imp < -5:  # Significant regression
        print(f"{metric}: Regression of {sim_imp:.1f}% (sim), {real_imp:.1f}% (real)")
    elif sim_imp > 10 or real_imp > 10:  # Significant improvement
        print(f"{metric}: Improvement of {sim_imp:.1f}% (sim), {real_imp:.1f}% (real)")

print("\nAnalysis complete! All outputs saved to respective directories.")