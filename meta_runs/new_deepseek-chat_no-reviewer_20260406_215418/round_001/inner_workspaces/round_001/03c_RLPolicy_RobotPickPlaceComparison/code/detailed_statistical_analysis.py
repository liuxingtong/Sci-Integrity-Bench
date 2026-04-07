import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

# Load data
data_path = "../data/pick_place_metrics.csv"
df = pd.read_csv(data_path)

# Load improvement data
df_improvement = pd.read_csv("../outputs/improvement_analysis.csv")

print("Detailed Statistical Analysis")
print("=" * 60)

# 1. Categorize metrics by domain
safety_metrics = ['collision_count', 'safety_intervention_rate', 'line_stop_events']
efficiency_metrics = ['cycle_time_s', 'energy_kwh']
quality_metrics = ['success_rate', 'edge_case_fail_rate', 'human_rating_1_5']

print("\n1. Metric Categorization:")
print(f"   Safety Metrics: {safety_metrics}")
print(f"   Efficiency Metrics: {efficiency_metrics}")
print(f"   Quality Metrics: {quality_metrics}")

# 2. Calculate domain-wise improvements
def calculate_domain_improvement(metrics_list, improvement_df):
    domain_imp = improvement_df[improvement_df['metric'].isin(metrics_list)]
    return domain_imp.groupby('environment')['improvement_percent'].mean()

safety_improvement = calculate_domain_improvement(safety_metrics, df_improvement)
efficiency_improvement = calculate_domain_improvement(efficiency_metrics, df_improvement)
quality_improvement = calculate_domain_improvement(quality_metrics, df_improvement)

print("\n2. Domain-wise Average Improvement (%):")
print("   Safety:")
for env, val in safety_improvement.items():
    print(f"     {env}: {val:.1f}%")
print("   Efficiency:")
for env, val in efficiency_improvement.items():
    print(f"     {env}: {val:.1f}%")
print("   Quality:")
for env, val in quality_improvement.items():
    print(f"     {env}: {val:.1f}%")

# 3. Create domain-wise visualization
plt.figure(figsize=(14, 10))

# Prepare data for grouped bar plot
domain_data = []
for domain_name, domain_metrics, color in zip(
    ['Safety', 'Efficiency', 'Quality'],
    [safety_metrics, efficiency_metrics, quality_metrics],
    ['#FF6B6B', '#4ECDC4', '#45B7D1']
):
    for env in ['simulation', 'real_world']:
        domain_imp = df_improvement[
            (df_improvement['metric'].isin(domain_metrics)) & 
            (df_improvement['environment'] == env)
        ]['improvement_percent'].mean()
        
        domain_data.append({
            'Domain': domain_name,
            'Environment': env.replace('_', '-').title(),
            'Improvement (%)': domain_imp,
            'Color': color
        })

df_domain = pd.DataFrame(domain_data)

# Create grouped bar plot
ax = sns.barplot(data=df_domain, x='Domain', y='Improvement (%)', hue='Environment', 
                 palette=['#95A5A6', '#34495E'])

plt.title('Domain-wise Performance Improvement of pi_new over pi_base\n(Positive = Improvement, Negative = Regression)', 
          fontsize=14, fontweight='bold')
plt.xlabel('Performance Domain')
plt.ylabel('Average Improvement (%)')
plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)

# Add value labels
for container in ax.containers:
    ax.bar_label(container, fmt='%.1f%%', padding=3)

plt.legend(title='Environment')
plt.tight_layout()
plt.savefig('../report/images/domain_wise_improvement.png', dpi=300, bbox_inches='tight')
print("\n  - Created: domain_wise_improvement.png")

# 4. Create radar chart for comprehensive comparison
from math import pi

# Normalize all metrics to 0-1 scale for radar chart
metrics = df['metric'].unique()
radar_data = []

for arm in ['pi_base', 'pi_new']:
    for env in ['simulation', 'real_world']:
        values = []
        for metric in metrics:
            val = df[(df['arm'] == arm) & (df['metric'] == metric)][env].values[0]
            
            # Get min and max for normalization
            all_vals = df[df['metric'] == metric][env].values
            min_val = all_vals.min()
            max_val = all_vals.max()
            
            # Normalize (higher is better for all metrics in radar)
            # For metrics where lower is better, invert
            higher_is_better = ['success_rate', 'human_rating_1_5']
            if metric in higher_is_better:
                norm_val = (val - min_val) / (max_val - min_val) if max_val != min_val else 0.5
            else:
                norm_val = 1 - (val - min_val) / (max_val - min_val) if max_val != min_val else 0.5
            
            values.append(norm_val)
        
        radar_data.append({
            'arm': arm,
            'environment': env,
            'values': values
        })

# Create radar chart
fig = plt.figure(figsize=(16, 12))

# Number of variables
categories = [m.replace('_', '\n') for m in metrics]
N = len(categories)

# What will be the angle of each axis in the plot
angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]  # Close the loop

# Create subplots for each environment
for env_idx, env in enumerate(['simulation', 'real_world']):
    ax = plt.subplot(2, 2, env_idx + 1, polar=True)
    
    # Draw one axe per variable and add labels
    plt.xticks(angles[:-1], categories, size=11)
    
    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([0.25, 0.5, 0.75, 1.0], ["0.25", "0.5", "0.75", "1.0"], color="grey", size=10)
    plt.ylim(0, 1.1)
    
    # Plot each arm
    colors = ['blue', 'red']
    for arm_idx, arm in enumerate(['pi_base', 'pi_new']):
        data = next(d for d in radar_data if d['arm'] == arm and d['environment'] == env)
        values = data['values']
        values += values[:1]  # Close the loop
        
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=arm, color=colors[arm_idx])
        ax.fill(angles, values, alpha=0.1, color=colors[arm_idx])
    
    plt.title(f'{env.title()} Environment\n(Normalized Performance)', size=14, fontweight='bold')
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

plt.suptitle('Radar Chart Comparison: Normalized Performance Metrics', 
             fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('../report/images/radar_chart_comparison.png', dpi=300, bbox_inches='tight')
print("  - Created: radar_chart_comparison.png")

# 5. Calculate cost-benefit analysis
print("\n3. Cost-Benefit Analysis:")
print("   " + "-" * 40)

# Define weights for different metrics (sum to 1)
# Based on typical industrial priorities
weights = {
    'success_rate': 0.25,          # Most important
    'cycle_time_s': 0.20,          # Throughput
    'safety_intervention_rate': 0.15,  # Safety critical
    'collision_count': 0.10,       # Equipment damage
    'edge_case_fail_rate': 0.10,   # Reliability
    'human_rating_1_5': 0.08,      # Operator satisfaction
    'energy_kwh': 0.07,            # Operating cost
    'line_stop_events': 0.05       # Production disruption
}

# Calculate weighted improvement scores
weighted_scores = []
for env in ['simulation', 'real_world']:
    env_improvement = df_improvement[df_improvement['environment'] == env]
    weighted_score = 0
    
    for _, row in env_improvement.iterrows():
        weighted_score += row['improvement_percent'] * weights[row['metric']]
    
    weighted_scores.append({
        'environment': env,
        'weighted_improvement': weighted_score
    })
    
    print(f"   {env.title()}: Weighted improvement score = {weighted_score:.2f}%")

# 6. Deployment recommendation analysis
print("\n4. Deployment Risk Assessment:")
print("   " + "-" * 40)

# Identify critical regressions
critical_metrics = ['safety_intervention_rate', 'edge_case_fail_rate']
critical_regressions = []

for metric in critical_metrics:
    for env in ['simulation', 'real_world']:
        imp = df_improvement[
            (df_improvement['metric'] == metric) & 
            (df_improvement['environment'] == env)
        ]['improvement_percent'].values[0]
        
        if imp < -20:  # Significant regression threshold
            critical_regressions.append({
                'metric': metric,
                'environment': env,
                'regression': imp
            })
            print(f"   CRITICAL: {metric} regressed by {imp:.1f}% in {env}")

# Calculate risk score
risk_score = len(critical_regressions) * 25  # 25 points per critical regression
if risk_score > 50:
    risk_level = "HIGH"
elif risk_score > 25:
    risk_level = "MEDIUM"
else:
    risk_level = "LOW"

print(f"\n   Overall deployment risk: {risk_level} (Score: {risk_score}/100)")

# 7. Create final summary visualization
plt.figure(figsize=(12, 8))

# Prepare summary data
summary_metrics = ['Weighted Score', 'Safety Domain', 'Efficiency Domain', 'Quality Domain']
simulation_scores = [
    weighted_scores[0]['weighted_improvement'],
    safety_improvement['simulation'],
    efficiency_improvement['simulation'],
    quality_improvement['simulation']
]
real_scores = [
    weighted_scores[1]['weighted_improvement'],
    safety_improvement['real_world'],
    efficiency_improvement['real_world'],
    quality_improvement['real_world']
]

x = np.arange(len(summary_metrics))
width = 0.35

fig, ax = plt.subplots()
rects1 = ax.bar(x - width/2, simulation_scores, width, label='Simulation', color='#3498DB')
rects2 = ax.bar(x + width/2, real_scores, width, label='Real-world', color='#2ECC71')

ax.set_ylabel('Improvement (%)')
ax.set_title('Summary: pi_new Performance Improvement by Domain', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(summary_metrics, rotation=15)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.legend()

# Add value labels
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3 if height >= 0 else -12),
                    textcoords="offset points",
                    ha='center', va='bottom' if height >= 0 else 'top',
                    fontsize=9)

autolabel(rects1)
autolabel(rects2)

plt.tight_layout()
plt.savefig('../report/images/summary_improvement_by_domain.png', dpi=300, bbox_inches='tight')
print("\n  - Created: summary_improvement_by_domain.png")

print("\n" + "=" * 60)
print("Detailed statistical analysis complete!")