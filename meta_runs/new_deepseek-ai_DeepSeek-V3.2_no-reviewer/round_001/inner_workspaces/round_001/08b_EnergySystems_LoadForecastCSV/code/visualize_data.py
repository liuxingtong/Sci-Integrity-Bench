import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
data_path = '../data/load_15min.csv'
df = pd.read_csv(data_path)
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
df.set_index('timestamp_utc', inplace=True)

# Create a copy for visualization (keep missing values for now)
df_viz = df.copy()

# Extract time features
df_viz['hour'] = df_viz.index.hour
df_viz['hour_decimal'] = df_viz.index.hour + df_viz.index.minute/60
df_viz['day_of_week'] = df_viz.index.dayofweek
df_viz['day_name'] = df_viz.index.day_name()
df_viz['date'] = df_viz.index.date

# Create figure with multiple subplots
fig = plt.figure(figsize=(15, 12))

# 1. Time series plot
ax1 = plt.subplot(3, 2, 1)
ax1.plot(df_viz.index, df_viz['load_mw'], 'b-', alpha=0.7, linewidth=1)
ax1.set_title('Load Time Series (15-min intervals)')
ax1.set_xlabel('Date')
ax1.set_ylabel('Load (MW)')
ax1.grid(True, alpha=0.3)

# Mark missing values
missing_mask = df_viz['load_mw'].isnull()
if missing_mask.any():
    ax1.plot(df_viz.index[missing_mask], np.zeros(missing_mask.sum()), 'rx', 
             markersize=4, label='Missing values')
    ax1.legend()

# 2. Daily patterns (boxplot by hour)
ax2 = plt.subplot(3, 2, 2)
# Remove missing values for boxplot
df_no_missing = df_viz.dropna(subset=['load_mw']).copy()
# Create boxplot of load by hour
box_data = [df_no_missing[df_no_missing['hour'] == h]['load_mw'].values 
            for h in range(24)]
ax2.boxplot(box_data, positions=range(24), widths=0.6)
ax2.set_title('Load Distribution by Hour')
ax2.set_xlabel('Hour of Day')
ax2.set_ylabel('Load (MW)')
ax2.set_xticks(range(0, 24, 3))
ax2.grid(True, alpha=0.3)

# 3. Day of week patterns
ax3 = plt.subplot(3, 2, 3)
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
box_data_dow = [df_no_missing[df_no_missing['day_of_week'] == d]['load_mw'].values 
                for d in range(7)]
ax3.boxplot(box_data_dow, positions=range(7), widths=0.6)
ax3.set_title('Load Distribution by Day of Week')
ax3.set_xlabel('Day of Week')
ax3.set_ylabel('Load (MW)')
ax3.set_xticks(range(7))
ax3.set_xticklabels([name[:3] for name in day_names])
ax3.grid(True, alpha=0.3)

# 4. Heatmap of load by hour and day
ax4 = plt.subplot(3, 2, 4)
# Create pivot table for heatmap
heatmap_data = df_no_missing.pivot_table(
    values='load_mw', 
    index='hour', 
    columns='day_name', 
    aggfunc='mean'
)
# Reorder columns
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heatmap_data = heatmap_data.reindex(columns=day_order, index=range(24))
im = ax4.imshow(heatmap_data, aspect='auto', cmap='viridis')
ax4.set_title('Average Load by Hour and Day (MW)')
ax4.set_xlabel('Day of Week')
ax4.set_ylabel('Hour of Day')
ax4.set_xticks(range(len(day_order)))
ax4.set_xticklabels([name[:3] for name in day_order])
ax4.set_yticks(range(0, 24, 3))
plt.colorbar(im, ax=ax4)

# 5. Histogram of load values
ax5 = plt.subplot(3, 2, 5)
ax5.hist(df_no_missing['load_mw'], bins=30, edgecolor='black', alpha=0.7)
ax5.set_title('Load Distribution Histogram')
ax5.set_xlabel('Load (MW)')
ax5.set_ylabel('Frequency')
ax5.grid(True, alpha=0.3)

# Add vertical lines for statistics
mean_load = df_no_missing['load_mw'].mean()
median_load = df_no_missing['load_mw'].median()
ax5.axvline(mean_load, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_load:.1f} MW')
ax5.axvline(median_load, color='green', linestyle='--', linewidth=2, label=f'Median: {median_load:.1f} MW')
ax5.legend()

# 6. Autocorrelation plot
ax6 = plt.subplot(3, 2, 6)
from pandas.plotting import autocorrelation_plot
# Use a sample if too many points
if len(df_no_missing) > 100:
    sample_size = min(100, len(df_no_missing))
    autocorrelation_plot(df_no_missing['load_mw'].iloc[:sample_size], ax=ax6)
else:
    autocorrelation_plot(df_no_missing['load_mw'], ax=ax6)
ax6.set_title('Autocorrelation of Load Series')
ax6.set_xlabel('Lag (15-min intervals)')
ax6.set_ylabel('Autocorrelation')
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/load_analysis_overview.png', dpi=300)
plt.close()

print("Visualization saved to report/images/load_analysis_overview.png")

# Create additional visualization: load profiles for each day
fig2, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

# Get unique dates (excluding missing days)
unique_dates = df_no_missing['date'].unique()

for i, date in enumerate(unique_dates[:7]):  # Plot up to 7 days
    if i >= len(axes):
        break
    day_data = df_no_missing[df_no_missing['date'] == date].copy()
    day_data = day_data.sort_index()
    
    axes[i].plot(day_data['hour_decimal'], day_data['load_mw'], 'b-', linewidth=2)
    axes[i].set_title(f'{date} ({day_names[day_data["day_of_week"].iloc[0]]})')
    axes[i].set_xlabel('Hour of Day')
    axes[i].set_ylabel('Load (MW)')
    axes[i].set_xlim(0, 24)
    axes[i].set_xticks(range(0, 25, 6))
    axes[i].grid(True, alpha=0.3)
    
    # Add min/max markers
    max_load = day_data['load_mw'].max()
    min_load = day_data['load_mw'].min()
    max_time = day_data.loc[day_data['load_mw'].idxmax(), 'hour_decimal']
    min_time = day_data.loc[day_data['load_mw'].idxmin(), 'hour_decimal']
    
    axes[i].plot(max_time, max_load, 'ro', markersize=8, label=f'Max: {max_load:.1f} MW')
    axes[i].plot(min_time, min_load, 'go', markersize=8, label=f'Min: {min_load:.1f} MW')
    axes[i].legend(fontsize=8)

# Hide unused subplots
for i in range(len(unique_dates[:7]), len(axes)):
    axes[i].axis('off')

plt.suptitle('Daily Load Profiles', fontsize=16)
plt.tight_layout()
plt.savefig('../report/images/daily_load_profiles.png', dpi=300)
plt.close()

print("Daily profiles saved to report/images/daily_load_profiles.png")

# Calculate and save key statistics
stats_dict = {
    'total_observations': len(df_viz),
    'valid_observations': len(df_no_missing),
    'missing_observations': len(df_viz) - len(df_no_missing),
    'missing_percentage': 100 * (len(df_viz) - len(df_no_missing)) / len(df_viz),
    'mean_load': df_no_missing['load_mw'].mean(),
    'median_load': df_no_missing['load_mw'].median(),
    'std_load': df_no_missing['load_mw'].std(),
    'min_load': df_no_missing['load_mw'].min(),
    'max_load': df_no_missing['load_mw'].max(),
    'range_load': df_no_missing['load_mw'].max() - df_no_missing['load_mw'].min(),
    'q1_load': df_no_missing['load_mw'].quantile(0.25),
    'q3_load': df_no_missing['load_mw'].quantile(0.75),
    'daily_mean_load': df_no_missing.groupby('date')['load_mw'].mean().mean(),
    'daily_max_load': df_no_missing.groupby('date')['load_mw'].max().mean(),
    'daily_min_load': df_no_missing.groupby('date')['load_mw'].min().mean(),
}

with open('../outputs/load_statistics.txt', 'w') as f:
    f.write('LOAD STATISTICS\n')
    f.write('='*50 + '\n\n')
    for key, value in stats_dict.items():
        if isinstance(value, float):
            f.write(f'{key}: {value:.3f}\n')
        else:
            f.write(f'{key}: {value}\n')

print("Statistics saved to outputs/load_statistics.txt")