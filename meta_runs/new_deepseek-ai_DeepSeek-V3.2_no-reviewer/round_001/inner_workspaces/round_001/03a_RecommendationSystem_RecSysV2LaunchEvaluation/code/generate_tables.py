import pandas as pd
import numpy as np

# Load data
offline_df = pd.read_csv('data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('data/online_ab_test_metrics.csv')

# Create formatted tables for the report
print("Creating formatted tables for report...")

# Table 1: Offline metrics comparison
offline_table = offline_df.copy()
offline_table['Improvement'] = offline_table['relative_change_pct'].apply(lambda x: '✓' if x > 0 else '✗')
offline_table['Magnitude'] = offline_table['relative_change_pct'].apply(lambda x: 'Large' if abs(x) > 20 else 'Medium' if abs(x) > 5 else 'Small')
offline_table['Business Impact'] = offline_table['metric'].apply(lambda x: 'High' if x in ['Precision@10', 'NDCG@10'] else 'Medium' if x == 'Recall@50' else 'Critical')

print("\nTable 1: Offline Evaluation Metrics")
print("=" * 80)
print(f"{'Metric':<20} {'v1':<10} {'v2':<10} {'Δ%':<10} {'Better?':<10} {'Magnitude':<12} {'Business Impact'}")
print("-" * 80)
for idx, row in offline_table.iterrows():
    print(f"{row['metric']:<20} {row['recsys_v1']:<10.3f} {row['recsys_v2']:<10.3f} {row['relative_change_pct']:<10.1f} {row['Improvement']:<10} {row['Magnitude']:<12} {row['Business Impact']}")

# Table 2: Online A/B test metrics
online_table = online_df.copy()
online_table['Improvement'] = online_table['relative_change_pct'].apply(lambda x: '✓' if x > 0 else '✗')
online_table['Magnitude'] = online_table['relative_change_pct'].apply(lambda x: 'Critical' if abs(x) > 100 else 'Large' if abs(x) > 20 else 'Medium' if abs(x) > 5 else 'Small')
online_table['Business Criticality'] = online_table['metric'].apply(lambda x: 'Critical' if x == 'Complaint_rate' else 'High' if x == 'CTR' else 'Medium')

print("\n\nTable 2: Online A/B Test Metrics (14-day, 10% traffic)")
print("=" * 80)
print(f"{'Metric':<20} {'v1 (%)':<10} {'v2 (%)':<10} {'Δ%':<10} {'Better?':<10} {'Magnitude':<12} {'Criticality'}")
print("-" * 80)
for idx, row in online_table.iterrows():
    print(f"{row['metric']:<20} {row['recsys_v1_pct']:<10.2f} {row['recsys_v2_pct']:<10.2f} {row['relative_change_pct']:<10.1f} {row['Improvement']:<10} {row['Magnitude']:<12} {row['Business Criticality']}")

# Table 3: Weighted decision matrix
print("\n\nTable 3: Weighted Decision Matrix for Launch Recommendation")
print("=" * 80)
print(f"{'Metric':<20} {'Category':<15} {'Weight':<10} {'Score':<10} {'Weighted Score':<15} {'Recommendation'}")
print("-" * 80)

# Define weights based on business importance
weights = {
    'Precision@10': 0.15,
    'NDCG@10': 0.15,
    'Recall@50': 0.10,
    'Coverage_catalog': 0.20,
    'CTR': 0.15,
    'Retention_D1': 0.10,
    'Retention_D7': 0.05,
    'Complaint_rate': 0.10
}

# Normalize scores (scale to -1 to 1)
normalized_scores = {}
total_weighted_score = 0

for idx, row in offline_df.iterrows():
    metric = row['metric']
    # Normalize relative change to -1 to 1 scale
    # Assuming max reasonable change is ±50%
    normalized = min(max(row['relative_change_pct'] / 50, -1), 1)
    weighted = normalized * weights[metric]
    normalized_scores[metric] = normalized
    total_weighted_score += weighted
    rec = 'LAUNCH' if normalized > 0 else 'HOLD'
    print(f"{metric:<20} {'Offline':<15} {weights[metric]:<10.2f} {normalized:<10.2f} {weighted:<15.3f} {rec}")

for idx, row in online_df.iterrows():
    metric = row['metric']
    # Special handling for complaint rate (negative is bad)
    if metric == 'Complaint_rate':
        normalized = -min(max(row['relative_change_pct'] / 200, -1), 1)  # Negative because increase is bad
    else:
        normalized = min(max(row['relative_change_pct'] / 50, -1), 1)
    weighted = normalized * weights[metric]
    normalized_scores[metric] = normalized
    total_weighted_score += weighted
    rec = 'LAUNCH' if normalized > 0 else 'HOLD'
    print(f"{metric:<20} {'Online':<15} {weights[metric]:<10.2f} {normalized:<10.2f} {weighted:<15.3f} {rec}")

print("-" * 80)
print(f"{'TOTAL':<20} {'':<15} {'1.00':<10} {'':<10} {total_weighted_score:<15.3f} {'LAUNCH' if total_weighted_score > 0 else 'DO NOT LAUNCH'}")

print("\n\nFinal Recommendation:")
if total_weighted_score > 0:
    print(f"Weighted score: {total_weighted_score:.3f} > 0 → RECOMMEND LAUNCH RecSys v2")
else:
    print(f"Weighted score: {total_weighted_score:.3f} < 0 → RECOMMEND DO NOT LAUNCH RecSys v2")

# Save tables to CSV for reference
offline_table.to_csv('outputs/offline_table_formatted.csv', index=False)
online_table.to_csv('outputs/online_table_formatted.csv', index=False)

print("\nTables saved to outputs/ directory.")
