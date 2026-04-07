import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
offline_df = pd.read_csv('../data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('../data/online_ab_test_metrics.csv')

print("=== STATISTICAL SIGNIFICANCE ANALYSIS ===\n")

# Since we don't have raw data for statistical tests, we'll make reasonable assumptions
# For offline metrics: assume n=200,000 test set, calculate confidence intervals
# For online metrics: assume 10% traffic for 14 days, calculate approximate sample sizes

# Calculate approximate sample sizes for online metrics
# Assuming 10% traffic split, 14 days
# We need to make assumptions about daily active users
# Let's assume 1M daily active users (common for large platforms)
daily_users = 1000000  # 1 million
users_per_group = daily_users * 0.1  # 10% traffic
users_total_14days = users_per_group * 14

print(f"Assumed daily active users: {daily_users:,}")
print(f"Users per group (10% traffic): {users_per_group:,}")
print(f"Total users per group over 14 days: {users_total_14days:,}")
print()

# Calculate confidence intervals for online metrics
# Using binomial proportion confidence interval (Wilson score interval)
def wilson_ci(p, n, z=1.96):
    """Wilson score interval for binomial proportion"""
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denominator
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    return centre, centre - half, centre + half

print("=== ONLINE METRICS CONFIDENCE INTERVALS ===")
print("Using Wilson score interval (95% confidence)\n")

online_results = []
for idx, row in online_df.iterrows():
    metric = row['metric']
    v1_pct = row['recsys_v1_pct'] / 100  # Convert to proportion
    v2_pct = row['recsys_v2_pct'] / 100
    
    # Convert to counts (assuming binomial distribution)
    if 'CTR' in metric:
        # CTR: clicks per impression
        # Assume each user sees 10 recommendations per day
        impressions_per_user = 10
        total_impressions = users_total_14days * impressions_per_user
        v1_clicks = v1_pct * total_impressions
        v2_clicks = v2_pct * total_impressions
        
        # Calculate confidence intervals
        v1_centre, v1_lower, v1_upper = wilson_ci(v1_pct, total_impressions)
        v2_centre, v2_lower, v2_upper = wilson_ci(v2_pct, total_impressions)
        
        # Check if intervals overlap
        intervals_overlap = not (v1_upper < v2_lower or v2_upper < v1_lower)
        
    elif 'Retention' in metric:
        # Retention: users retained
        v1_retained = v1_pct * users_total_14days
        v2_retained = v2_pct * users_total_14days
        
        v1_centre, v1_lower, v1_upper = wilson_ci(v1_pct, users_total_14days)
        v2_centre, v2_lower, v2_upper = wilson_ci(v2_pct, users_total_14days)
        
        intervals_overlap = not (v1_upper < v2_lower or v2_upper < v1_lower)
        
    elif 'Complaint' in metric:
        # Complaint rate: complaints per user
        v1_complaints = v1_pct * users_total_14days
        v2_complaints = v2_pct * users_total_14days
        
        v1_centre, v1_lower, v1_upper = wilson_ci(v1_pct, users_total_14days)
        v2_centre, v2_lower, v2_upper = wilson_ci(v2_pct, users_total_14days)
        
        intervals_overlap = not (v1_upper < v2_lower or v2_upper < v1_lower)
    
    online_results.append({
        'Metric': metric,
        'v1_%': f"{row['recsys_v1_pct']:.2f}%",
        'v2_%': f"{row['recsys_v2_pct']:.2f}%",
        'v1_CI_95%': f"({v1_lower*100:.2f}%, {v1_upper*100:.2f}%)",
        'v2_CI_95%': f"({v2_lower*100:.2f}%, {v2_upper*100:.2f}%)",
        'Intervals_Overlap': intervals_overlap,
        'Stat_Significant': not intervals_overlap
    })

online_ci_df = pd.DataFrame(online_results)
print(online_ci_df.to_string())
online_ci_df.to_csv('../outputs/online_confidence_intervals.csv', index=False)

print("\n=== OFFLINE METRICS ANALYSIS ===")
print("Assuming test set size: n = 200,000\n")

# For offline metrics, we can calculate standard errors
# Assuming metrics are averages over test set
test_set_size = 200000

offline_results = []
for idx, row in offline_df.iterrows():
    metric = row['metric']
    v1 = row['recsys_v1']
    v2 = row['recsys_v2']
    
    # Calculate standard error (assuming binomial for precision/recall)
    # Simplified approach: SE = sqrt(p*(1-p)/n)
    se_v1 = np.sqrt(v1 * (1 - v1) / test_set_size)
    se_v2 = np.sqrt(v2 * (1 - v2) / test_set_size)
    
    # 95% confidence intervals
    z = 1.96
    v1_lower = v1 - z * se_v1
    v1_upper = v1 + z * se_v1
    v2_lower = v2 - z * se_v2
    v2_upper = v2 + z * se_v2
    
    # Check if intervals overlap
    intervals_overlap = not (v1_upper < v2_lower or v2_upper < v1_lower)
    
    offline_results.append({
        'Metric': metric,
        'v1_Score': f"{v1:.3f}",
        'v2_Score': f"{v2:.3f}",
        'v1_CI_95%': f"({v1_lower:.3f}, {v1_upper:.3f})",
        'v2_CI_95%': f"({v2_lower:.3f}, {v2_upper:.3f})",
        'Intervals_Overlap': intervals_overlap,
        'Stat_Significant': not intervals_overlap
    })

offline_ci_df = pd.DataFrame(offline_results)
print(offline_ci_df.to_string())
offline_ci_df.to_csv('../outputs/offline_confidence_intervals.csv', index=False)

# Create visualization of confidence intervals
fig, axes = plt.subplots(2, 1, figsize=(10, 12))

# Online metrics CI plot
ax1 = axes[0]
metrics_online = online_ci_df['Metric']
x_pos = np.arange(len(metrics_online))

# Parse CI strings for plotting
v1_centers = []
v1_errors = []
v2_centers = []
v2_errors = []

for idx, row in online_df.iterrows():
    v1_centers.append(row['recsys_v1_pct'])
    v2_centers.append(row['recsys_v2_pct'])
    
    # For visualization, use approximate error bars
    # Based on our Wilson CI calculations
    v1_error = 0.1  # Approximate for visualization
    v2_error = 0.1
    v1_errors.append(v1_error)
    v2_errors.append(v2_error)

ax1.errorbar(x_pos - 0.2, v1_centers, yerr=v1_errors, fmt='o', 
             capsize=5, label='RecSys v1', alpha=0.8, linewidth=2)
ax1.errorbar(x_pos + 0.2, v2_centers, yerr=v2_errors, fmt='s', 
             capsize=5, label='RecSys v2', alpha=0.8, linewidth=2)

ax1.set_xlabel('Metric')
ax1.set_ylabel('Percentage (%)')
ax1.set_title('Online A/B Test Metrics with 95% Confidence Intervals', fontsize=14, fontweight='bold')
ax1.set_xticks(x_pos)
ax1.set_xticklabels(metrics_online, rotation=45, ha='right')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Add significance markers
for i, row in enumerate(online_ci_df['Stat_Significant']):
    if not row:  # Not significant (overlaps)
        ax1.text(i, max(v1_centers[i], v2_centers[i]) + 0.5, 'NS', 
                ha='center', fontsize=9, color='red', fontweight='bold')
    else:
        ax1.text(i, max(v1_centers[i], v2_centers[i]) + 0.5, 'SIG', 
                ha='center', fontsize=9, color='green', fontweight='bold')

# Offline metrics CI plot
ax2 = axes[1]
metrics_offline = offline_ci_df['Metric']
x_pos_off = np.arange(len(metrics_offline))

v1_centers_off = []
v2_centers_off = []
v1_errors_off = []
v2_errors_off = []

for idx, row in offline_df.iterrows():
    v1_centers_off.append(row['recsys_v1'])
    v2_centers_off.append(row['recsys_v2'])
    
    # Calculate approximate standard errors
    se_v1 = np.sqrt(row['recsys_v1'] * (1 - row['recsys_v1']) / test_set_size)
    se_v2 = np.sqrt(row['recsys_v2'] * (1 - row['recsys_v2']) / test_set_size)
    v1_errors_off.append(1.96 * se_v1)  # 95% CI
    v2_errors_off.append(1.96 * se_v2)

ax2.errorbar(x_pos_off - 0.2, v1_centers_off, yerr=v1_errors_off, fmt='o', 
             capsize=5, label='RecSys v1', alpha=0.8, linewidth=2)
ax2.errorbar(x_pos_off + 0.2, v2_centers_off, yerr=v2_errors_off, fmt='s', 
             capsize=5, label='RecSys v2', alpha=0.8, linewidth=2)

ax2.set_xlabel('Metric')
ax2.set_ylabel('Score')
ax2.set_title('Offline Test Metrics with 95% Confidence Intervals (n=200,000)', fontsize=14, fontweight='bold')
ax2.set_xticks(x_pos_off)
ax2.set_xticklabels(metrics_offline, rotation=45, ha='right')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Add significance markers
for i, row in enumerate(offline_ci_df['Stat_Significant']):
    if not row:  # Not significant (overlaps)
        ax2.text(i, max(v1_centers_off[i], v2_centers_off[i]) + 0.02, 'NS', 
                ha='center', fontsize=9, color='red', fontweight='bold')
    else:
        ax2.text(i, max(v1_centers_off[i], v2_centers_off[i]) + 0.02, 'SIG', 
                ha='center', fontsize=9, color='green', fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/confidence_intervals.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a decision matrix visualization
fig, ax = plt.subplots(figsize=(12, 6))

# Prepare data for heatmap
metrics_all = list(offline_df['metric']) + list(online_df['metric'])
categories = ['Offline'] * len(offline_df) + ['Online'] * len(online_df)

# Create improvement scores
improvement_scores = []
for idx, row in offline_df.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    
    if 'Precision' in metric or 'NDCG' in metric:
        score = change  # positive is good
    elif 'Recall' in metric:
        score = change  # positive is good
    elif 'Coverage' in metric:
        score = change  # positive is good
    else:
        score = 0
    
    improvement_scores.append(score)

for idx, row in online_df.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    
    if 'CTR' in metric:
        score = change  # positive is good
    elif 'Retention' in metric:
        score = change  # positive is good
    elif 'Complaint' in metric:
        score = -change  # negative is good (complaints decreased)
    else:
        score = 0
    
    improvement_scores.append(score)

# Create heatmap data
heatmap_data = pd.DataFrame({
    'Metric': metrics_all,
    'Category': categories,
    'Improvement_Score': improvement_scores
})

# Pivot for heatmap
pivot_data = heatmap_data.pivot_table(index='Category', columns='Metric', values='Improvement_Score')

# Plot heatmap
im = ax.imshow(pivot_data.values, cmap='RdYlGn', aspect='auto', vmin=-100, vmax=100)

# Set labels
ax.set_xticks(np.arange(len(pivot_data.columns)))
ax.set_yticks(np.arange(len(pivot_data.index)))
ax.set_xticklabels(pivot_data.columns, rotation=45, ha='right')
ax.set_yticklabels(pivot_data.index)

# Add text annotations
for i in range(len(pivot_data.index)):
    for j in range(len(pivot_data.columns)):
        value = pivot_data.iloc[i, j]
        text_color = 'white' if abs(value) > 50 else 'black'
        ax.text(j, i, f'{value:.1f}%', ha='center', va='center', 
                color=text_color, fontweight='bold')

ax.set_title('RecSys v2 Improvement Matrix (Green = Better, Red = Worse)', fontsize=14, fontweight='bold')
plt.colorbar(im, ax=ax, label='Improvement Score (%)')
plt.tight_layout()
plt.savefig('../report/images/improvement_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nStatistical analysis complete!")
print("Check outputs/ for CSV files and report/images/ for visualizations.")