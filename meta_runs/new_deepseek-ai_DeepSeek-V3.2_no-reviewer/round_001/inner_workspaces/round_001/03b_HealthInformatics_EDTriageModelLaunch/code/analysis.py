import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats

# Set style for better visualizations
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("Loading data...")
# Load offline evaluation data
offline_df = pd.read_csv('../data/offline_evaluation_metrics.csv')
print("Offline evaluation data:")
print(offline_df)
print("\n")

# Load online A/B test data
online_df = pd.read_csv('../data/online_ab_test_metrics.csv')
print("Online A/B test data:")
print(online_df)
print("\n")

# Data exploration
offline_df['improvement_direction'] = offline_df['relative_change_pct'].apply(
    lambda x: 'Improvement' if x > 0 else 'Worsening'
)

online_df['improvement_direction'] = online_df['relative_change_pct'].apply(
    lambda x: 'Improvement' if x < 0 else 'Worsening'  # Negative is better for most online metrics
)

print("Offline metrics summary:")
print(offline_df.describe())
print("\n")

print("Online metrics summary:")
print(online_df.describe())
print("\n")

# Create visualizations
# 1. Offline metrics comparison
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Offline Evaluation: TriageAssist-A vs TriageAssist-B', fontsize=16, fontweight='bold')

# Bar plot for sensitivity and specificity
ax1 = axes[0, 0]
metrics_to_plot = ['Sensitivity_critical_ESI12', 'Specificity_non_urgent']
for metric in metrics_to_plot:
    row = offline_df[offline_df['metric'] == metric]
    if not row.empty:
        ax1.bar([f"{metric}_A", f"{metric}_B"], 
                [row['triage_a'].values[0], row['triage_b'].values[0]],
                alpha=0.7, label=metric.replace('_', ' '))
ax1.set_ylabel('Score')
ax1.set_title('Sensitivity & Specificity Comparison')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Bar plot for AUROC and calibration error
ax2 = axes[0, 1]
metrics_to_plot = ['AUROC_acuity_score', 'Mean_absolute_calibration_error']
for metric in metrics_to_plot:
    row = offline_df[offline_df['metric'] == metric]
    if not row.empty:
        ax2.bar([f"{metric}_A", f"{metric}_B"], 
                [row['triage_a'].values[0], row['triage_b'].values[0]],
                alpha=0.7, label=metric.replace('_', ' '))
ax2.set_ylabel('Score')
ax2.set_title('AUROC & Calibration Error Comparison')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Bar plot for disposition agreement
ax3 = axes[1, 0]
row = offline_df[offline_df['metric'] == 'Disposition_agreement_with_attending_pct']
if not row.empty:
    ax3.bar(['TriageAssist-A', 'TriageAssist-B'], 
            [row['triage_a'].values[0], row['triage_b'].values[0]],
            color=['blue', 'orange'], alpha=0.7)
    ax3.set_ylabel('Agreement (%)')
    ax3.set_title('Disposition Agreement with Attending')
    ax3.grid(True, alpha=0.3)

# Relative change plot for all offline metrics
ax4 = axes[1, 1]
offline_df_sorted = offline_df.sort_values('relative_change_pct', ascending=False)
colors = ['green' if x > 0 else 'red' for x in offline_df_sorted['relative_change_pct']]
ax4.barh(offline_df_sorted['metric'].str.replace('_', ' '), 
         offline_df_sorted['relative_change_pct'], 
         color=colors, alpha=0.7)
ax4.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
ax4.set_xlabel('Relative Change (%)')
ax4.set_title('Relative Change from A to B (Positive = Better)')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/offline_metrics_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Online metrics comparison
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Online Pilot (14-day): TriageAssist-A vs TriageAssist-B', fontsize=16, fontweight='bold')

# Time to physician comparison
ax1 = axes[0, 0]
row = online_df[online_df['metric'] == 'Median_time_to_physician_min']
if not row.empty:
    ax1.bar(['TriageAssist-A', 'TriageAssist-B'], 
            [row['triage_a_pct'].values[0], row['triage_b_pct'].values[0]],
            color=['blue', 'orange'], alpha=0.7)
    ax1.set_ylabel('Minutes')
    ax1.set_title('Median Time to Physician')
    ax1.grid(True, alpha=0.3)

# LWBS rate comparison
ax2 = axes[0, 1]
row = online_df[online_df['metric'] == 'LWBS_rate_pct']
if not row.empty:
    ax2.bar(['TriageAssist-A', 'TriageAssist-B'], 
            [row['triage_a_pct'].values[0], row['triage_b_pct'].values[0]],
            color=['blue', 'orange'], alpha=0.7)
    ax2.set_ylabel('Rate (%)')
    ax2.set_title('Left Without Being Seen (LWBS) Rate')
    ax2.grid(True, alpha=0.3)

# Unscheduled returns comparison
ax3 = axes[1, 0]
row = online_df[online_df['metric'] == 'Unscheduled_return_72h_pct']
if not row.empty:
    ax3.bar(['TriageAssist-A', 'TriageAssist-B'], 
            [row['triage_a_pct'].values[0], row['triage_b_pct'].values[0]],
            color=['blue', 'orange'], alpha=0.7)
    ax3.set_ylabel('Rate (%)')
    ax3.set_title('Unscheduled Return within 72h')
    ax3.grid(True, alpha=0.3)

# Relative change plot for all online metrics
ax4 = axes[1, 1]
online_df_sorted = online_df.sort_values('relative_change_pct', ascending=True)  # Negative is better for most
# For visualization, we'll invert the sign for metrics where negative is better
def get_visual_change(row):
    metric = row['metric']
    change = row['relative_change_pct']
    # For time to physician, negative change is better (less time)
    if metric == 'Median_time_to_physician_min':
        return -change  # Invert so positive is better
    # For rates (LWBS, returns, overrides, complaints), negative change is better (lower rates)
    else:
        return -change  # Invert so positive is better

online_df_sorted['visual_change'] = online_df_sorted.apply(get_visual_change, axis=1)
online_df_sorted = online_df_sorted.sort_values('visual_change', ascending=False)
colors = ['green' if x > 0 else 'red' for x in online_df_sorted['visual_change']]
ax4.barh(online_df_sorted['metric'].str.replace('_', ' '), 
         online_df_sorted['visual_change'], 
         color=colors, alpha=0.7)
ax4.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
ax4.set_xlabel('Relative Change (Positive = Better)')
ax4.set_title('Relative Change from A to B (Adjusted for Clinical Benefit)')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/online_metrics_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Combined assessment visualization
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Overall Assessment: TriageAssist-B vs TriageAssist-A', fontsize=16, fontweight='bold')

# Offline metrics summary
ax1 = axes[0]
offline_improvements = offline_df[offline_df['relative_change_pct'] > 0]
offline_worsening = offline_df[offline_df['relative_change_pct'] <= 0]
ax1.bar(['Improvements', 'Worsening'], 
        [len(offline_improvements), len(offline_worsening)],
        color=['green', 'red'], alpha=0.7)
ax1.set_ylabel('Number of Metrics')
ax1.set_title('Offline Evaluation: Metric Changes')
ax1.text(0, len(offline_improvements) + 0.1, f'{len(offline_improvements)}', 
         ha='center', va='bottom', fontweight='bold')
ax1.text(1, len(offline_worsening) + 0.1, f'{len(offline_worsening)}', 
         ha='center', va='bottom', fontweight='bold')
ax1.grid(True, alpha=0.3)

# Online metrics summary (adjusted for clinical benefit)
ax2 = axes[1]
online_df['is_improvement'] = online_df.apply(
    lambda row: True if (row['metric'] == 'Median_time_to_physician_min' and row['relative_change_pct'] < 0) 
                   or (row['metric'] != 'Median_time_to_physician_min' and row['relative_change_pct'] < 0) else False,
    axis=1
)
online_improvements = online_df[online_df['is_improvement']]
online_worsening = online_df[~online_df['is_improvement']]
ax2.bar(['Improvements', 'Worsening'], 
        [len(online_improvements), len(online_worsening)],
        color=['green', 'red'], alpha=0.7)
ax2.set_ylabel('Number of Metrics')
ax2.set_title('Online Pilot: Metric Changes (Clinically Adjusted)')
ax2.text(0, len(online_improvements) + 0.1, f'{len(online_improvements)}', 
         ha='center', va='bottom', fontweight='bold')
ax2.text(1, len(online_worsening) + 0.1, f'{len(online_worsening)}', 
         ha='center', va='bottom', fontweight='bold')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/overall_assessment.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Radar chart for comprehensive comparison
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, polar=True)

# Prepare data for radar chart
offline_metrics = offline_df['metric'].tolist()
online_metrics = online_df['metric'].tolist()

# Normalize values for radar chart (0-1 scale)
def normalize_series(series, higher_better=True):
    if higher_better:
        return (series - series.min()) / (series.max() - series.min())
    else:
        # For metrics where lower is better, invert the normalization
        return 1 - ((series - series.min()) / (series.max() - series.min()))

# Create radar chart data
offline_a_normalized = []
offline_b_normalized = []
for metric in offline_metrics:
    row = offline_df[offline_df['metric'] == metric]
    if not row.empty:
        # Determine if higher is better for this metric
        higher_better = metric not in ['Mean_absolute_calibration_error']
        offline_a_normalized.append(normalize_series(pd.Series([row['triage_a'].values[0]]), higher_better)[0])
        offline_b_normalized.append(normalize_series(pd.Series([row['triage_b'].values[0]]), higher_better)[0])

# Convert to numpy arrays and close the polygon
theta = np.linspace(0, 2 * np.pi, len(offline_metrics), endpoint=False)
theta = np.concatenate((theta, [theta[0]]))
offline_a_normalized = np.concatenate((offline_a_normalized, [offline_a_normalized[0]]))
offline_b_normalized = np.concatenate((offline_b_normalized, [offline_b_normalized[0]]))

# Plot
ax.plot(theta, offline_a_normalized, 'o-', linewidth=2, label='TriageAssist-A', color='blue')
ax.fill(theta, offline_a_normalized, alpha=0.25, color='blue')
ax.plot(theta, offline_b_normalized, 'o-', linewidth=2, label='TriageAssist-B', color='orange')
ax.fill(theta, offline_b_normalized, alpha=0.25, color='orange')

# Set labels
ax.set_xticks(theta[:-1])
ax.set_xticklabels([m.replace('_', '\n') for m in offline_metrics], fontsize=9)
ax.set_ylim(0, 1)
ax.set_title('Offline Metrics Comparison (Normalized)', fontsize=14, fontweight='bold')
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

plt.tight_layout()
plt.savefig('report/images/radar_chart_offline.png', dpi=300, bbox_inches='tight')
plt.close()

# Calculate overall scores
def calculate_overall_score(df, metric_weights=None):
    """Calculate overall score for a model"""
    if metric_weights is None:
        metric_weights = {metric: 1 for metric in df['metric']}
    
    total_weight = 0
    weighted_sum = 0
    
    for _, row in df.iterrows():
        metric = row['metric']
        weight = metric_weights.get(metric, 1)
        
        # For offline metrics, use the raw values
        if 'triage_a' in row:
            value = row['triage_a']
        elif 'triage_a_pct' in row:
            value = row['triage_a_pct']
        else:
            continue
            
        weighted_sum += value * weight
        total_weight += weight
    
    return weighted_sum / total_weight if total_weight > 0 else 0

# Calculate scores
offline_score_a = calculate_overall_score(offline_df)
# Create a copy for B scores
offline_df_b = offline_df.copy()
offline_df_b['triage_a'] = offline_df_b['triage_b']
offline_score_b = calculate_overall_score(offline_df_b)

print(f"Overall Offline Score - TriageAssist-A: {offline_score_a:.3f}")
print(f"Overall Offline Score - TriageAssist-B: {offline_score_b:.3f}")
print(f"Offline Score Change: {(offline_score_b - offline_score_a):.3f} ({(offline_score_b - offline_score_a)/offline_score_a*100:.1f}%)")

# Save summary statistics
offline_summary = offline_df.describe()
online_summary = online_df.describe()

offline_summary.to_csv('outputs/offline_summary_stats.csv')
online_summary.to_csv('outputs/online_summary_stats.csv')

print("\nAnalysis complete. Figures saved to report/images/")
