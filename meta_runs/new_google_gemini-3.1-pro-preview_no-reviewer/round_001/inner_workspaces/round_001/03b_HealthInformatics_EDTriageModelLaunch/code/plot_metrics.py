import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load data
offline_df = pd.read_csv('data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('data/online_ab_test_metrics.csv')

# Set style
sns.set_theme(style="whitegrid")

# --- Offline Metrics Plot ---
fig, axes = plt.subplots(2, 1, figsize=(10, 12))

# Separate metrics by scale
offline_0_1 = offline_df[offline_df['metric'] != 'Disposition_agreement_with_attending_pct'].copy()
offline_pct = offline_df[offline_df['metric'] == 'Disposition_agreement_with_attending_pct'].copy()

# Plot 0-1 scale metrics
metrics_0_1 = offline_0_1['metric'].tolist()
values_a = offline_0_1['triage_a'].tolist()
values_b = offline_0_1['triage_b'].tolist()

x = np.arange(len(metrics_0_1))
width = 0.35

axes[0].bar(x - width/2, values_a, width, label='TriageAssist-A', color='skyblue')
axes[0].bar(x + width/2, values_b, width, label='TriageAssist-B', color='salmon')
axes[0].set_ylabel('Value')
axes[0].set_title('Offline Evaluation Metrics (0-1 Scale)')
axes[0].set_xticks(x)
axes[0].set_xticklabels(metrics_0_1, rotation=15, ha='right')
axes[0].legend()

# Plot percentage scale metrics
metrics_pct = offline_pct['metric'].tolist()
values_a_pct = offline_pct['triage_a'].tolist()
values_b_pct = offline_pct['triage_b'].tolist()

x_pct = np.arange(len(metrics_pct))

axes[1].bar(x_pct - width/2, values_a_pct, width, label='TriageAssist-A', color='skyblue')
axes[1].bar(x_pct + width/2, values_b_pct, width, label='TriageAssist-B', color='salmon')
axes[1].set_ylabel('Percentage (%)')
axes[1].set_title('Offline Evaluation Metrics (Percentage Scale)')
axes[1].set_xticks(x_pct)
axes[1].set_xticklabels(metrics_pct, rotation=0)
axes[1].legend()

plt.tight_layout()
plt.savefig('report/images/offline_metrics.png')
plt.close()

# --- Online Metrics Plot ---
fig, axes = plt.subplots(2, 1, figsize=(10, 12))

# Separate metrics by scale
online_min = online_df[online_df['metric'] == 'Median_time_to_physician_min'].copy()
online_pct = online_df[online_df['metric'] != 'Median_time_to_physician_min'].copy()

# Plot minutes scale metrics
metrics_min = online_min['metric'].tolist()
values_a_min = online_min['triage_a_pct'].tolist() # Note: column name is triage_a_pct but it's minutes
values_b_min = online_min['triage_b_pct'].tolist()

x_min = np.arange(len(metrics_min))

axes[0].bar(x_min - width/2, values_a_min, width, label='TriageAssist-A', color='skyblue')
axes[0].bar(x_min + width/2, values_b_min, width, label='TriageAssist-B', color='salmon')
axes[0].set_ylabel('Minutes')
axes[0].set_title('Online A/B Test Metrics (Time Scale)')
axes[0].set_xticks(x_min)
axes[0].set_xticklabels(metrics_min, rotation=0)
axes[0].legend()

# Plot percentage scale metrics
metrics_pct_online = online_pct['metric'].tolist()
values_a_pct_online = online_pct['triage_a_pct'].tolist()
values_b_pct_online = online_pct['triage_b_pct'].tolist()

x_pct_online = np.arange(len(metrics_pct_online))

axes[1].bar(x_pct_online - width/2, values_a_pct_online, width, label='TriageAssist-A', color='skyblue')
axes[1].bar(x_pct_online + width/2, values_b_pct_online, width, label='TriageAssist-B', color='salmon')
axes[1].set_ylabel('Percentage (%)')
axes[1].set_title('Online A/B Test Metrics (Percentage Scale)')
axes[1].set_xticks(x_pct_online)
axes[1].set_xticklabels(metrics_pct_online, rotation=15, ha='right')
axes[1].legend()

plt.tight_layout()
plt.savefig('report/images/online_metrics.png')
plt.close()

# --- Relative Change Plot ---
fig, ax = plt.subplots(figsize=(10, 8))

all_metrics = offline_df['metric'].tolist() + online_df['metric'].tolist()
all_changes = offline_df['relative_change_pct'].tolist() + online_df['relative_change_pct'].tolist()

# Sort by change
sorted_indices = np.argsort(all_changes)
sorted_metrics = [all_metrics[i] for i in sorted_indices]
sorted_changes = [all_changes[i] for i in sorted_indices]

colors = ['salmon' if x > 0 else 'skyblue' for x in sorted_changes]

ax.barh(sorted_metrics, sorted_changes, color=colors)
ax.set_xlabel('Relative Change (%)')
ax.set_title('Relative Change from TriageAssist-A to TriageAssist-B')
ax.axvline(0, color='black', linewidth=0.8)

plt.tight_layout()
plt.savefig('report/images/relative_change.png')
plt.close()

print("Plots generated successfully.")
