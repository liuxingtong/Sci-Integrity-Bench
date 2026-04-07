import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Create output directory
os.makedirs('outputs', exist_ok=True)

print("Loading data for statistical analysis...")
# Load data
offline_df = pd.read_csv('../data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('../data/online_ab_test_metrics.csv')

print("\n=== OFFLINE METRICS STATISTICAL ANALYSIS ===")
print("Assuming offline metrics are based on n=200,000 test samples")
print("We'll calculate confidence intervals for the relative changes")

# For offline metrics, we need to estimate variance
# Since we don't have raw data, we'll make reasonable assumptions
# For binary classification metrics (Precision, Recall), variance can be estimated
# For ranking metrics (NDCG), we'll use bootstrap approximation

# Let's create a function to estimate confidence intervals
def estimate_confidence_interval(metric_name, v1_value, v2_value, n=200000, metric_type='precision'):
    """Estimate 95% confidence interval for metric difference"""
    
    if metric_type == 'precision' or metric_type == 'recall':
        # For binary metrics, use binomial proportion confidence interval
        # Standard error for proportion: sqrt(p*(1-p)/n)
        se_v1 = np.sqrt(v1_value * (1 - v1_value) / n)
        se_v2 = np.sqrt(v2_value * (1 - v2_value) / n)
        
        # Standard error for difference
        se_diff = np.sqrt(se_v1**2 + se_v2**2)
        
        # Difference
        diff = v2_value - v1_value
        
        # 95% CI (z-score = 1.96)
        ci_lower = diff - 1.96 * se_diff
        ci_upper = diff + 1.96 * se_diff
        
        # Relative change CI
        rel_diff = (v2_value - v1_value) / v1_value * 100
        rel_ci_lower = ci_lower / v1_value * 100
        rel_ci_upper = ci_upper / v1_value * 100
        
    else:
        # For other metrics, use simpler approximation
        # Assume standard error of 0.01 for normalized metrics
        se = 0.01 / np.sqrt(n/1000)  # Rough approximation
        diff = v2_value - v1_value
        ci_lower = diff - 1.96 * se
        ci_upper = diff + 1.96 * se
        
        rel_diff = (v2_value - v1_value) / v1_value * 100
        rel_ci_lower = ci_lower / v1_value * 100
        rel_ci_upper = ci_upper / v1_value * 100
    
    return {
        'absolute_diff': diff,
        'absolute_ci_lower': ci_lower,
        'absolute_ci_upper': ci_upper,
        'relative_diff_pct': rel_diff,
        'relative_ci_lower_pct': rel_ci_lower,
        'relative_ci_upper_pct': rel_ci_upper,
        'significant': (ci_lower > 0 or ci_upper < 0)  # CI doesn't cross zero
    }

# Analyze offline metrics
offline_results = []
for idx, row in offline_df.iterrows():
    metric_name = row['metric']
    v1 = row['recsys_v1']
    v2 = row['recsys_v2']
    
    # Determine metric type
    if 'Precision' in metric_name or 'Recall' in metric_name:
        metric_type = 'precision'
    elif 'NDCG' in metric_name:
        metric_type = 'ndcg'
    else:
        metric_type = 'other'
    
    result = estimate_confidence_interval(metric_name, v1, v2, metric_type=metric_type)
    result['metric'] = metric_name
    result['v1'] = v1
    result['v2'] = v2
    offline_results.append(result)

offline_stats_df = pd.DataFrame(offline_results)
print("\nOffline Metrics with 95% Confidence Intervals:")
print(offline_stats_df[['metric', 'v1', 'v2', 'absolute_diff', 
                        'absolute_ci_lower', 'absolute_ci_upper', 
                        'relative_diff_pct', 'significant']].to_string())

print("\n=== ONLINE A/B TEST STATISTICAL ANALYSIS ===")
print("Assuming 14-day test with 10% traffic per arm")
print("We need to estimate sample sizes for each metric")

# For online metrics, we need to estimate statistical significance
# Let's make reasonable assumptions about sample sizes
# CTR: clicks vs impressions
# Retention: users who returned
# Complaint rate: complaints vs total users

# Estimate sample sizes (these are rough estimates)
sample_sizes = {
    'CTR': 100000,  # Impressions
    'Retention_D1': 50000,  # Users
    'Retention_D7': 50000,  # Users
    'Complaint_rate': 100000  # Users
}

online_results = []
for idx, row in online_df.iterrows():
    metric_name = row['metric']
    v1_pct = row['recsys_v1_pct'] / 100  # Convert to proportion
    v2_pct = row['recsys_v2_pct'] / 100
    
    n = sample_sizes.get(metric_name, 50000)
    
    # For proportion metrics
    se_v1 = np.sqrt(v1_pct * (1 - v1_pct) / n)
    se_v2 = np.sqrt(v2_pct * (1 - v2_pct) / n)
    
    # Standard error for difference
    se_diff = np.sqrt(se_v1**2 + se_v2**2)
    
    # Difference in proportions
    diff = v2_pct - v1_pct
    
    # 95% CI
    ci_lower = diff - 1.96 * se_diff
    ci_upper = diff + 1.96 * se_diff
    
    # Z-test for proportions
    z_score = diff / se_diff
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    # Relative change
    rel_diff = (v2_pct - v1_pct) / v1_pct * 100
    
    online_results.append({
        'metric': metric_name,
        'v1_pct': row['recsys_v1_pct'],
        'v2_pct': row['recsys_v2_pct'],
        'absolute_diff_pct': diff * 100,
        'absolute_ci_lower_pct': ci_lower * 100,
        'absolute_ci_upper_pct': ci_upper * 100,
        'relative_diff_pct': rel_diff,
        'z_score': z_score,
        'p_value': p_value,
        'significant': p_value < 0.05
    })

online_stats_df = pd.DataFrame(online_results)
print("\nOnline A/B Test Metrics with Statistical Significance:")
print(online_stats_df[['metric', 'v1_pct', 'v2_pct', 'absolute_diff_pct',
                       'p_value', 'significant']].to_string())

# Save results
offline_stats_df.to_csv('outputs/offline_statistical_analysis.csv', index=False)
online_stats_df.to_csv('outputs/online_statistical_analysis.csv', index=False)

print("\n=== COMBINED DECISION ANALYSIS ===")

# Create a decision matrix based on statistical significance and business impact
business_impact = {
    'Precision@10': 'HIGH',
    'NDCG@10': 'HIGH',
    'Recall@50': 'MEDIUM',
    'Coverage_catalog': 'MEDIUM',
    'CTR': 'HIGH',
    'Retention_D1': 'HIGH',
    'Retention_D7': 'HIGH',
    'Complaint_rate': 'CRITICAL'
}

# Combine all metrics
all_metrics = []
for idx, row in offline_stats_df.iterrows():
    all_metrics.append({
        'metric': row['metric'],
        'type': 'offline',
        'v1': row['v1'],
        'v2': row['v2'],
        'relative_change_pct': row['relative_diff_pct'],
        'significant': row['significant'],
        'business_impact': business_impact[row['metric']],
        'decision_weight': 1.0 if business_impact[row['metric']] == 'HIGH' else 
                          0.7 if business_impact[row['metric']] == 'MEDIUM' else 0.5
    })

for idx, row in online_stats_df.iterrows():
    all_metrics.append({
        'metric': row['metric'],
        'type': 'online',
        'v1': row['v1_pct'],
        'v2': row['v2_pct'],
        'relative_change_pct': row['relative_diff_pct'],
        'significant': row['significant'],
        'business_impact': business_impact[row['metric']],
        'decision_weight': 1.5 if business_impact[row['metric']] == 'CRITICAL' else
                          1.2 if business_impact[row['metric']] == 'HIGH' else 0.8
    })

decision_df = pd.DataFrame(all_metrics)

# Calculate weighted score
# Positive changes get positive weight, negative changes get negative weight
decision_df['weighted_score'] = decision_df['relative_change_pct'] * decision_df['decision_weight']

# Separate positive and negative impacts
positive_metrics = decision_df[decision_df['relative_change_pct'] > 0]
negative_metrics = decision_df[decision_df['relative_change_pct'] < 0]

print("\nPositive Improvements:")
print(positive_metrics[['metric', 'type', 'relative_change_pct', 'business_impact', 'significant']].to_string())
print(f"\nNumber of positive metrics: {len(positive_metrics)}")
print(f"Weighted positive score: {positive_metrics['weighted_score'].sum():.2f}")

print("\nNegative Regressions:")
print(negative_metrics[['metric', 'type', 'relative_change_pct', 'business_impact', 'significant']].to_string())
print(f"\nNumber of negative metrics: {len(negative_metrics)}")
print(f"Weighted negative score: {negative_metrics['weighted_score'].sum():.2f}")

overall_weighted_score = decision_df['weighted_score'].sum()
print(f"\nOverall Weighted Decision Score: {overall_weighted_score:.2f}")

# Make final recommendation
critical_negative = decision_df[(decision_df['business_impact'] == 'CRITICAL') & 
                                (decision_df['relative_change_pct'] < 0)]

if len(critical_negative) > 0:
    print("\n⚠️  CRITICAL ISSUE DETECTED: Negative change in critical metric(s)")
    for _, row in critical_negative.iterrows():
        print(f"  - {row['metric']}: {row['relative_change_pct']:.1f}% change")
    recommendation = "DO NOT LAUNCH - Critical regression detected"
elif overall_weighted_score > 10:
    recommendation = "LAUNCH - Strong overall improvement"
elif overall_weighted_score > 0:
    recommendation = "CONSIDER LAUNCHING with close monitoring"
else:
    recommendation = "DO NOT LAUNCH - Net negative impact"

print(f"\n📋 FINAL RECOMMENDATION: {recommendation}")

# Save decision matrix
decision_df.to_csv('outputs/decision_matrix_detailed.csv', index=False)

# Create visualization of decision matrix
plt.figure(figsize=(12, 8))

# Create scatter plot with size based on business impact and color based on change
size_map = {'CRITICAL': 300, 'HIGH': 200, 'MEDIUM': 100}
sizes = [size_map[row['business_impact']] for _, row in decision_df.iterrows()]
colors = ['green' if row['relative_change_pct'] > 0 else 'red' for _, row in decision_df.iterrows()]

# Plot
for i, row in decision_df.iterrows():
    plt.scatter(i, row['relative_change_pct'], 
                s=sizes[i], c=colors[i], alpha=0.6, edgecolors='black')
    plt.text(i, row['relative_change_pct'], row['metric'], 
             ha='center', va='bottom' if row['relative_change_pct'] > 0 else 'top',
             fontsize=9)

plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
plt.xlabel('Metrics')
plt.ylabel('Relative Change (%)')
plt.title('Decision Matrix: Business Impact vs. Metric Change')
plt.xticks([])

# Add legend
import matplotlib.patches as mpatches
legend_patches = [
    mpatches.Patch(color='green', label='Improvement', alpha=0.6),
    mpatches.Patch(color='red', label='Regression', alpha=0.6),
    mpatches.Circle((0,0), radius=5, color='gray', label='CRITICAL Impact', alpha=0.6),
    mpatches.Circle((0,0), radius=3.5, color='gray', label='HIGH Impact', alpha=0.6),
    mpatches.Circle((0,0), radius=2, color='gray', label='MEDIUM Impact', alpha=0.6)
]
plt.legend(handles=legend_patches, loc='upper right')

plt.tight_layout()
plt.savefig('../report/images/decision_matrix_detailed.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nSaved detailed decision matrix to report/images/decision_matrix_detailed.png")
print("\nStatistical analysis complete!")