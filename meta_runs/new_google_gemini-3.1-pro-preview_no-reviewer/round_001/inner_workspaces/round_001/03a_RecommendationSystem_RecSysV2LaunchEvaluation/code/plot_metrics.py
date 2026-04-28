import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Create directories if they don't exist
os.makedirs('report/images', exist_ok=True)

# Load data
offline_df = pd.read_csv('data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('data/online_ab_test_metrics.csv')

# Set style
sns.set_theme(style="whitegrid")

# 1. Offline Metrics Absolute Comparison
plt.figure(figsize=(10, 6))
x = np.arange(len(offline_df['metric']))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width/2, offline_df['recsys_v1'], width, label='RecSys-v1')
rects2 = ax.bar(x + width/2, offline_df['recsys_v2'], width, label='RecSys-v2')

ax.set_ylabel('Metric Value')
ax.set_title('Offline Evaluation Metrics: RecSys-v1 vs RecSys-v2')
ax.set_xticks(x)
ax.set_xticklabels(offline_df['metric'])
ax.legend()

fig.tight_layout()
plt.savefig('report/images/offline_metrics_absolute.png', dpi=300)
plt.close()

# 2. Online Metrics Absolute Comparison
plt.figure(figsize=(10, 6))
x = np.arange(len(online_df['metric']))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width/2, online_df['recsys_v1_pct'], width, label='RecSys-v1')
rects2 = ax.bar(x + width/2, online_df['recsys_v2_pct'], width, label='RecSys-v2')

ax.set_ylabel('Metric Value (%)')
ax.set_title('Online A/B Test Metrics: RecSys-v1 vs RecSys-v2')
ax.set_xticks(x)
ax.set_xticklabels(online_df['metric'])
ax.legend()

fig.tight_layout()
plt.savefig('report/images/online_metrics_absolute.png', dpi=300)
plt.close()

# 3. Relative Change Comparison (Combined)
offline_df['type'] = 'Offline'
online_df['type'] = 'Online'

combined_df = pd.concat([
    offline_df[['metric', 'relative_change_pct', 'type']],
    online_df[['metric', 'relative_change_pct', 'type']]
])

plt.figure(figsize=(12, 8))
colors = ['green' if val > 0 else 'red' for val in combined_df['relative_change_pct']]
ax = sns.barplot(x='relative_change_pct', y='metric', hue='type', data=combined_df, palette='muted')

plt.axvline(0, color='black', linewidth=1)
plt.xlabel('Relative Change (%)')
plt.ylabel('Metric')
plt.title('Relative Change in Metrics (RecSys-v2 vs RecSys-v1)')
plt.tight_layout()
plt.savefig('report/images/relative_change_combined.png', dpi=300)
plt.close()

# 4. Relative Change Comparison (Separate for better scaling)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Offline
colors_offline = ['green' if val > 0 else 'red' for val in offline_df['relative_change_pct']]
sns.barplot(x='relative_change_pct', y='metric', data=offline_df, ax=ax1, palette=colors_offline)
ax1.axvline(0, color='black', linewidth=1)
ax1.set_xlabel('Relative Change (%)')
ax1.set_ylabel('Metric')
ax1.set_title('Offline Metrics Relative Change')

# Online
colors_online = ['green' if val > 0 else 'red' for val in online_df['relative_change_pct']]
sns.barplot(x='relative_change_pct', y='metric', data=online_df, ax=ax2, palette=colors_online)
ax2.axvline(0, color='black', linewidth=1)
ax2.set_xlabel('Relative Change (%)')
ax2.set_ylabel('')
ax2.set_title('Online Metrics Relative Change')

plt.tight_layout()
plt.savefig('report/images/relative_change_separate.png', dpi=300)
plt.close()

print("Plots generated successfully.")
