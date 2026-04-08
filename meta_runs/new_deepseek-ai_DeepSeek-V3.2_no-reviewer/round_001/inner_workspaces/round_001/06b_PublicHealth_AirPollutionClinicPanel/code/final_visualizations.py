import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
df = pd.read_csv('../data/daily_panel.csv')

print("=== Generating Final Visualizations ===\n")

# 1. Distribution plots
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Distribution of Key Variables', fontsize=16, y=1.02)

# PM2.5 distribution
axes[0, 0].hist(df['pm25'], bins=20, edgecolor='black', alpha=0.7, color='red')
axes[0, 0].axvline(x=df['pm25'].mean(), color='darkred', linestyle='--', linewidth=2, label=f'Mean: {df["pm25"].mean():.1f}')
axes[0, 0].set_xlabel('PM2.5 (µg/m³)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Distribution of PM2.5')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Respiratory visits distribution
axes[0, 1].hist(df['respiratory_visits'], bins=20, edgecolor='black', alpha=0.7, color='blue')
axes[0, 1].axvline(x=df['respiratory_visits'].mean(), color='darkblue', linestyle='--', linewidth=2, label=f'Mean: {df["respiratory_visits"].mean():.1f}')
axes[0, 1].set_xlabel('Respiratory Visits')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Distribution of Respiratory Visits')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Heating degree days distribution
axes[0, 2].hist(df['heating_degree_day'], bins=20, edgecolor='black', alpha=0.7, color='orange')
axes[0, 2].axvline(x=df['heating_degree_day'].mean(), color='darkorange', linestyle='--', linewidth=2, label=f'Mean: {df["heating_degree_day"].mean():.1f}')
axes[0, 2].set_xlabel('Heating Degree Days')
axes[0, 2].set_ylabel('Frequency')
axes[0, 2].set_title('Distribution of Heating Degree Days')
axes[0, 2].legend()
axes[0, 2].grid(True, alpha=0.3)

# Flu index distribution
axes[1, 0].hist(df['flu_index'], bins=20, edgecolor='black', alpha=0.7, color='green')
axes[1, 0].axvline(x=df['flu_index'].mean(), color='darkgreen', linestyle='--', linewidth=2, label=f'Mean: {df["flu_index"].mean():.3f}')
axes[1, 0].set_xlabel('Flu Index')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].set_title('Distribution of Flu Index')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# School holiday (bar chart)
school_holiday_counts = df['school_holiday'].value_counts().sort_index()
axes[1, 1].bar(['No School Holiday', 'School Holiday'], school_holiday_counts.values, 
               alpha=0.7, color=['lightgray', 'purple'])
axes[1, 1].set_ylabel('Number of Days')
axes[1, 1].set_title('School Holiday Days')
for i, count in enumerate(school_holiday_counts.values):
    axes[1, 1].text(i, count + 1, str(count), ha='center', va='bottom', fontweight='bold')
axes[1, 1].grid(True, alpha=0.3, axis='y')

# Remove empty subplot
fig.delaxes(axes[1, 2])

plt.tight_layout()
plt.savefig('../report/images/variable_distributions.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Scatter plot matrix for key relationships
print("Creating scatter plot matrix...")
key_vars = ['pm25', 'respiratory_visits', 'heating_degree_day', 'flu_index']
scatter_df = df[key_vars]

# Create pairplot with regression lines
g = sns.pairplot(scatter_df, kind='reg', diag_kind='kde', 
                 plot_kws={'scatter_kws': {'alpha': 0.5, 's': 30}, 
                          'line_kws': {'color': 'red', 'linewidth': 1}},
                 diag_kws={'fill': True})
g.fig.suptitle('Pairwise Relationships Between Key Variables', y=1.02, fontsize=16)
plt.tight_layout()
plt.savefig('../report/images/pairplot_relationships.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Heatmap of PM2.5 and respiratory visits by heating degree days
print("Creating heatmap of PM2.5 effects by heating conditions...")

# Create bins for PM2.5 and heating degree days
df['pm25_bin'] = pd.cut(df['pm25'], bins=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
df['heating_bin'] = pd.cut(df['heating_degree_day'], bins=3, labels=['Low Heating', 'Medium Heating', 'High Heating'])

# Calculate mean respiratory visits for each combination
heatmap_data = df.groupby(['pm25_bin', 'heating_bin'])['respiratory_visits'].mean().unstack()

plt.figure(figsize=(10, 8))
sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlOrRd', 
            cbar_kws={'label': 'Mean Respiratory Visits'})
plt.title('Mean Respiratory Visits by PM2.5 Level and Heating Conditions')
plt.xlabel('Heating Degree Days')
plt.ylabel('PM2.5 Level')
plt.tight_layout()
plt.savefig('../report/images/pm25_heating_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Time series comparison with highlighted high PM2.5 days
print("Creating time series comparison plot...")

# Identify high PM2.5 days (above 75th percentile)
pm25_threshold = df['pm25'].quantile(0.75)
high_pm25_days = df[df['pm25'] > pm25_threshold]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

# PM2.5 time series
ax1.plot(df['day_index'], df['pm25'], color='red', linewidth=1.5, alpha=0.7, label='PM2.5')
ax1.scatter(high_pm25_days['day_index'], high_pm25_days['pm25'], 
           color='darkred', s=50, zorder=5, label=f'High PM2.5 (> {pm25_threshold:.1f} µg/m³)')
ax1.axhline(y=pm25_threshold, color='gray', linestyle='--', alpha=0.5, label='75th percentile')
ax1.set_ylabel('PM2.5 (µg/m³)')
ax1.set_title('PM2.5 Concentration with High Pollution Days Highlighted')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)

# Respiratory visits time series
ax2.plot(df['day_index'], df['respiratory_visits'], color='blue', linewidth=1.5, alpha=0.7, label='Respiratory Visits')
# Highlight same days as high PM2.5
ax2.scatter(high_pm25_days['day_index'], high_pm25_days['respiratory_visits'], 
           color='darkblue', s=50, zorder=5, label='Respiratory Visits on High PM2.5 Days')
ax2.set_xlabel('Day Index')
ax2.set_ylabel('Respiratory Visits')
ax2.set_title('Respiratory Visits on Corresponding Days')
ax2.legend(loc='upper right')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/time_series_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# 5. Summary statistics table for report
print("\n=== Summary Statistics for Report ===")
summary_stats = pd.DataFrame({
    'Variable': ['PM2.5', 'Respiratory Visits', 'Heating Degree Days', 'Flu Index', 'School Holiday'],
    'Mean': [df['pm25'].mean(), df['respiratory_visits'].mean(), 
             df['heating_degree_day'].mean(), df['flu_index'].mean(), 
             df['school_holiday'].mean()],
    'Std Dev': [df['pm25'].std(), df['respiratory_visits'].std(), 
                df['heating_degree_day'].std(), df['flu_index'].std(), 
                df['school_holiday'].std()],
    'Min': [df['pm25'].min(), df['respiratory_visits'].min(), 
            df['heating_degree_day'].min(), df['flu_index'].min(), 
            df['school_holiday'].min()],
    '25%': [df['pm25'].quantile(0.25), df['respiratory_visits'].quantile(0.25), 
            df['heating_degree_day'].quantile(0.25), df['flu_index'].quantile(0.25), 
            df['school_holiday'].quantile(0.25)],
    'Median': [df['pm25'].median(), df['respiratory_visits'].median(), 
               df['heating_degree_day'].median(), df['flu_index'].median(), 
               df['school_holiday'].median()],
    '75%': [df['pm25'].quantile(0.75), df['respiratory_visits'].quantile(0.75), 
            df['heating_degree_day'].quantile(0.75), df['flu_index'].quantile(0.75), 
            df['school_holiday'].quantile(0.75)],
    'Max': [df['pm25'].max(), df['respiratory_visits'].max(), 
            df['heating_degree_day'].max(), df['flu_index'].max(), 
            df['school_holiday'].max()]
})

# Save summary statistics
summary_stats.to_csv('../outputs/summary_statistics.csv', index=False)
print(summary_stats.to_string(index=False))
print("\nSummary statistics saved to outputs/summary_statistics.csv")

print("\n=== All Visualizations Generated ===")
print("Figures saved to report/images/")
