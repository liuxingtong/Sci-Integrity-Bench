import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Create output directories if they don't exist
os.makedirs('report/images', exist_ok=True)

# Load data
offline_df = pd.read_csv('data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('data/online_ab_test_metrics.csv')

# --- Plot Offline Metrics ---
# Separate metrics by scale
offline_0_1 = offline_df[offline_df['metric'].isin(['Sensitivity_critical_ESI12', 'Specificity_non_urgent', 'AUROC_acuity_score', 'Mean_absolute_calibration_error'])].copy()
offline_pct = offline_df[offline_df['metric'] == 'Disposition_agreement_with_attending_pct'].copy()

# Plot 0-1 metrics
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(offline_0_1))
width = 0.35

rects1 = ax.bar(x - width/2, offline_0_1['triage_a'], width, label='TriageAssist-A', color='skyblue')
rects2 = ax.bar(x + width/2, offline_0_1['triage_b'], width, label='TriageAssist-B', color='salmon')

ax.set_ylabel('Score')
ax.set_title('Offline Evaluation Metrics (0-1 Scale)')
ax.set_xticks(x)
ax.set_xticklabels(offline_0_1['metric'], rotation=15, ha='right')
ax.legend()

fig.tight_layout()
plt.savefig('report/images/offline_metrics_0_1.png')
plt.close()

# Plot percentage metrics
fig, ax = plt.subplots(figsize=(6, 6))
x = np.arange(len(offline_pct))
width = 0.35

rects1 = ax.bar(x - width/2, offline_pct['triage_a'], width, label='TriageAssist-A', color='skyblue')
rects2 = ax.bar(x + width/2, offline_pct['triage_b'], width, label='TriageAssist-B', color='salmon')

ax.set_ylabel('Percentage (%)')
ax.set_title('Offline Evaluation Metrics (Percentage)')
ax.set_xticks(x)
ax.set_xticklabels(offline_pct['metric'], rotation=0)
ax.legend()

fig.tight_layout()
plt.savefig('report/images/offline_metrics_pct.png')
plt.close()

# --- Plot Online Metrics ---
# Separate metrics by scale
online_min = online_df[online_df['metric'] == 'Median_time_to_physician_min'].copy()
online_pct = online_df[online_df['metric'] != 'Median_time_to_physician_min'].copy()

# Plot minutes metrics
fig, ax = plt.subplots(figsize=(6, 6))
x = np.arange(len(online_min))
width = 0.35

rects1 = ax.bar(x - width/2, online_min['triage_a_pct'], width, label='TriageAssist-A', color='skyblue')
rects2 = ax.bar(x + width/2, online_min['triage_b_pct'], width, label='TriageAssist-B', color='salmon')

ax.set_ylabel('Minutes')
ax.set_title('Online A/B Test Metrics (Time)')
ax.set_xticks(x)
ax.set_xticklabels(online_min['metric'], rotation=0)
ax.legend()

fig.tight_layout()
plt.savefig('report/images/online_metrics_min.png')
plt.close()

# Plot percentage metrics
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(online_pct))
width = 0.35

rects1 = ax.bar(x - width/2, online_pct['triage_a_pct'], width, label='TriageAssist-A', color='skyblue')
rects2 = ax.bar(x + width/2, online_pct['triage_b_pct'], width, label='TriageAssist-B', color='salmon')

ax.set_ylabel('Percentage (%)')
ax.set_title('Online A/B Test Metrics (Percentage)')
ax.set_xticks(x)
ax.set_xticklabels(online_pct['metric'], rotation=15, ha='right')
ax.legend()

fig.tight_layout()
plt.savefig('report/images/online_metrics_pct.png')
plt.close()

# --- Plot Relative Changes ---
# Combine relative changes
offline_rel = offline_df[['metric', 'relative_change_pct']].copy()
offline_rel['source'] = 'Offline'
online_rel = online_df[['metric', 'relative_change_pct']].copy()
online_rel['source'] = 'Online'

combined_rel = pd.concat([offline_rel, online_rel])

# Sort by relative change
combined_rel = combined_rel.sort_values('relative_change_pct')

fig, ax = plt.subplots(figsize=(12, 8))
colors = ['green' if x < 0 else 'red' for x in combined_rel['relative_change_pct']]
# Note: 'better' direction depends on the metric. 
# Let's color code based on clinical context.
# Better if negative: Mean_absolute_calibration_error, Median_time_to_physician_min, LWBS_rate_pct, Unscheduled_return_72h_pct, Clinician_override_pct, Patient_complaint_rate_pct
# Better if positive: Sensitivity_critical_ESI12, Specificity_non_urgent, AUROC_acuity_score, Disposition_agreement_with_attending_pct

def get_color(row):
    metric = row['metric']
    val = row['relative_change_pct']
    if metric in ['Sensitivity_critical_ESI12', 'Specificity_non_urgent', 'AUROC_acuity_score', 'Disposition_agreement_with_attending_pct']:
        return 'green' if val > 0 else 'red'
    else:
        return 'green' if val < 0 else 'red'

colors = combined_rel.apply(get_color, axis=1)

ax.barh(combined_rel['metric'], combined_rel['relative_change_pct'], color=colors)
ax.set_xlabel('Relative Change (%)')
ax.set_title('Relative Change from TriageAssist-A to TriageAssist-B\n(Green = Improvement, Red = Degradation)')
ax.axvline(0, color='black', linewidth=0.8)

fig.tight_layout()
plt.savefig('report/images/relative_changes.png')
plt.close()

print("Analysis complete. Images saved to report/images/")
