import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create output directory
os.makedirs('outputs', exist_ok=True)

print("=== FINAL COMPREHENSIVE ANALYSIS FOR RecSys v2 LAUNCH DECISION ===")

# Load data
offline_df = pd.read_csv('../data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('../data/online_ab_test_metrics.csv')

print("\n1. DATA OVERVIEW")
print("="*50)
print("\nOffline Evaluation Metrics (n=200,000 test samples):")
print(offline_df.to_string())
print("\nOnline A/B Test Metrics (14-day, 10% traffic per arm):")
print(online_df.to_string())

print("\n\n2. KEY METRIC INTERPRETATION")
print("="*50)

# Define which metrics should increase (good) vs decrease (good)
# For most metrics, increase is good, but for Complaint_rate, decrease is good
metric_direction = {
    'Precision@10': 'increase',
    'NDCG@10': 'increase',
    'Recall@50': 'increase',
    'Coverage_catalog': 'increase',
    'CTR': 'increase',
    'Retention_D1': 'increase',
    'Retention_D7': 'increase',
    'Complaint_rate': 'decrease'  # Lower is better
}

# Calculate actual direction of change
offline_df['desired_direction'] = offline_df['metric'].map(metric_direction)
offline_df['actual_direction'] = offline_df['relative_change_pct'].apply(lambda x: 'increase' if x > 0 else 'decrease')
offline_df['aligned'] = offline_df['desired_direction'] == offline_df['actual_direction']

online_df['desired_direction'] = online_df['metric'].map(metric_direction)
online_df['actual_direction'] = online_df['relative_change_pct'].apply(lambda x: 'increase' if x > 0 else 'decrease')
online_df['aligned'] = online_df['desired_direction'] == online_df['actual_direction']

# Fix complaint rate - increase is actually bad
complaint_mask = online_df['metric'] == 'Complaint_rate'
online_df.loc[complaint_mask, 'aligned'] = False  # 187% increase is NOT aligned with desired decrease

print("\nOffline Metrics Alignment with Desired Direction:")
print(offline_df[['metric', 'recsys_v1', 'recsys_v2', 'relative_change_pct', 
                  'desired_direction', 'actual_direction', 'aligned']].to_string())

print("\n\nOnline Metrics Alignment with Desired Direction:")
print(online_df[['metric', 'recsys_v1_pct', 'recsys_v2_pct', 'relative_change_pct',
                 'desired_direction', 'actual_direction', 'aligned']].to_string())

print("\n\n3. BUSINESS IMPACT ASSESSMENT")
print("="*50)

# Define business impact weights
business_weights = {
    'Precision@10': 0.15,  # High importance for recommendation quality
    'NDCG@10': 0.15,       # High importance for ranking quality
    'Recall@50': 0.10,     # Medium importance
    'Coverage_catalog': 0.10,  # Medium importance for diversity
    'CTR': 0.15,           # High importance for engagement
    'Retention_D1': 0.10,  # Medium-high importance
    'Retention_D7': 0.15,  # High importance for long-term retention
    'Complaint_rate': 0.10  # High importance (negative weight)
}

# Calculate weighted scores
# For metrics where increase is good: score = relative_change_pct * weight
# For complaint rate (decrease is good): score = -relative_change_pct * weight
offline_scores = []
for idx, row in offline_df.iterrows():
    metric = row['metric']
    weight = business_weights[metric]
    change = row['relative_change_pct']
    
    if metric_direction[metric] == 'increase':
        score = change * weight
    else:
        score = -change * weight
    
    offline_scores.append({
        'metric': metric,
        'weight': weight,
        'relative_change': change,
        'score': score,
        'aligned': row['aligned']
    })

offline_scores_df = pd.DataFrame(offline_scores)

online_scores = []
for idx, row in online_df.iterrows():
    metric = row['metric']
    weight = business_weights[metric]
    change = row['relative_change_pct']
    
    if metric_direction[metric] == 'increase':
        score = change * weight
    else:
        score = -change * weight  # Negative for complaint rate increase
    
    online_scores.append({
        'metric': metric,
        'weight': weight,
        'relative_change': change,
        'score': score,
        'aligned': row['aligned']
    })

online_scores_df = pd.DataFrame(online_scores)

print("\nOffline Metrics Business Impact Scores:")
print(offline_scores_df.to_string())
print(f"\nTotal Offline Score: {offline_scores_df['score'].sum():.2f}")

print("\n\nOnline Metrics Business Impact Scores:")
print(online_scores_df.to_string())
print(f"\nTotal Online Score: {online_scores_df['score'].sum():.2f}")

total_score = offline_scores_df['score'].sum() + online_scores_df['score'].sum()
print(f"\n\nTOTAL BUSINESS IMPACT SCORE: {total_score:.2f}")

print("\n\n4. RISK ASSESSMENT")
print("="*50)

# Identify critical issues
critical_issues = []

# Complaint rate increased by 187% - this is a major red flag
if online_df.loc[online_df['metric'] == 'Complaint_rate', 'relative_change_pct'].values[0] > 10:
    critical_issues.append({
        'issue': 'Complaint rate increased dramatically (+187%)',
        'severity': 'CRITICAL',
        'impact': 'User dissatisfaction, potential churn, brand damage'
    })

# Coverage dropped by 50.6% - significant reduction in catalog coverage
if offline_df.loc[offline_df['metric'] == 'Coverage_catalog', 'relative_change_pct'].values[0] < -20:
    critical_issues.append({
        'issue': 'Catalog coverage reduced by 50.6%',
        'severity': 'HIGH',
        'impact': 'Reduced diversity, potential long-tail item neglect'
    })

# D7 retention dropped by 8.1%
if online_df.loc[online_df['metric'] == 'Retention_D7', 'relative_change_pct'].values[0] < -5:
    critical_issues.append({
        'issue': '7-day retention decreased by 8.1%',
        'severity': 'HIGH',
        'impact': 'Reduced long-term user engagement and lifetime value'
    })

print("\nCritical Issues Identified:")
for issue in critical_issues:
    print(f"\n• {issue['issue']}")
    print(f"  Severity: {issue['severity']}")
    print(f"  Impact: {issue['impact']}")

print("\n\n5. TRADE-OFF ANALYSIS")
print("="*50)

print("\nRecSys v2 shows MIXED results:")
print("\nIMPROVEMENTS:")
print("- Precision@10: +12.5% (better recommendation accuracy)")
print("- NDCG@10: +9.6% (better ranking quality)")
print("- CTR: +16.2% (higher click-through rate)")
print("- D1 Retention: +3.9% (better day-1 retention)")

print("\nREGRESSIONS:")
print("- Recall@50: -4.9% (slightly lower recall)")
print("- Coverage: -50.6% (significantly reduced catalog coverage)")
print("- D7 Retention: -8.1% (worse 7-day retention)")
print("- Complaint Rate: +187% (DRAMATIC increase in user complaints)")

print("\n\n6. FINAL RECOMMENDATION")
print("="*50)

# Decision logic
if len([i for i in critical_issues if i['severity'] == 'CRITICAL']) > 0:
    recommendation = "DO NOT LAUNCH RecSys v2"
    reasoning = "Critical issue detected: 187% increase in complaint rate indicates serious user dissatisfaction that outweighs other improvements."
elif total_score < 0:
    recommendation = "DO NOT LAUNCH RecSys v2"
    reasoning = "Net negative business impact score."
elif total_score < 5:
    recommendation = "CONSIDER launching with close monitoring and rapid iteration"
    reasoning = "Slight positive impact but significant trade-offs require careful monitoring."
else:
    recommendation = "LAUNCH RecSys v2"
    reasoning = "Strong positive business impact outweighs the negatives."

# Override based on critical issue
if len([i for i in critical_issues if i['severity'] == 'CRITICAL']) > 0:
    recommendation = "DO NOT LAUNCH RecSys v2"
    reasoning = "CRITICAL: 187% increase in complaint rate is unacceptable. This indicates serious user experience issues that could damage brand reputation and cause user churn."

print(f"\nRECOMMENDATION: {recommendation}")
print(f"\nRATIONALE: {reasoning}")

print("\n\n7. ALTERNATIVE RECOMMENDATIONS")
print("="*50)
print("\nIf not launching v2 immediately, consider:")
print("1. Investigate root cause of increased complaints")
print("2. Address coverage reduction issue")
print("3. Run focused A/B tests on specific components")
print("4. Develop v2.1 with fixes before full launch")

# Create final visualization
plt.figure(figsize=(14, 8))

# Prepare data for visualization
all_metrics = pd.concat([
    offline_df[['metric', 'relative_change_pct']].assign(type='offline'),
    online_df[['metric', 'relative_change_pct']].assign(type='online')
])

# Add desired direction
all_metrics['desired_direction'] = all_metrics['metric'].map(metric_direction)
all_metrics['aligned'] = all_metrics.apply(
    lambda row: 'aligned' if (row['desired_direction'] == 'increase' and row['relative_change_pct'] > 0) or 
                             (row['desired_direction'] == 'decrease' and row['relative_change_pct'] < 0) 
                 else 'misaligned', axis=1
)

# Fix complaint rate
complaint_mask = all_metrics['metric'] == 'Complaint_rate'
all_metrics.loc[complaint_mask, 'aligned'] = 'misaligned'  # Increase is bad

# Sort by relative change
all_metrics = all_metrics.sort_values('relative_change_pct')

# Create bar plot
colors = {'aligned': 'green', 'misaligned': 'red'}
bar_colors = [colors[a] for a in all_metrics['aligned']]

bars = plt.barh(all_metrics['metric'], all_metrics['relative_change_pct'], color=bar_colors, alpha=0.7)
plt.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

# Add value labels
for bar in bars:
    width = bar.get_width()
    label_x_pos = width + (1 if width >= 0 else -1)
    plt.text(label_x_pos, bar.get_y() + bar.get_height()/2,
             f'{width:.1f}%', ha='left' if width >= 0 else 'right', va='center', fontsize=9)

plt.xlabel('Relative Change (%)')
plt.title('RecSys v2 vs v1: Metric Changes (Green=Good, Red=Bad)', fontsize=14, fontweight='bold')
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()

# Add legend
import matplotlib.patches as mpatches
legend_elements = [
    mpatches.Patch(color='green', alpha=0.7, label='Aligned with business goals'),
    mpatches.Patch(color='red', alpha=0.7, label='Misaligned with business goals')
]
plt.legend(handles=legend_elements, loc='lower right')

plt.savefig('../report/images/final_recommendation_chart.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n\nSaved final recommendation chart to report/images/final_recommendation_chart.png")

# Save final results
final_results = {
    'recommendation': recommendation,
    'reasoning': reasoning,
    'total_business_score': total_score,
    'critical_issues_count': len(critical_issues),
    'offline_score': offline_scores_df['score'].sum(),
    'online_score': online_scores_df['score'].sum()
}

import json
with open('outputs/final_recommendation.json', 'w') as f:
    json.dump(final_results, f, indent=2)

print("\n\nFinal results saved to outputs/final_recommendation.json")
print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)