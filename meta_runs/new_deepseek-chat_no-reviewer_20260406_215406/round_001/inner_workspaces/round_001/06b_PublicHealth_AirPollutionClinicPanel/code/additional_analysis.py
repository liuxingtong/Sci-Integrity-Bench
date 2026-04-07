import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
df = pd.read_csv('data/daily_panel.csv')

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("Starting additional analysis...")

# 1. Stratified analysis by heating degree days
# Create categories for heating degree days
print("\n=== Stratified Analysis by Heating Degree Days ===")
# Create terciles
hdd_terciles = pd.qcut(df['heating_degree_day'], q=3, labels=['Low', 'Medium', 'High'])
df['hdd_category'] = hdd_terciles

print("\nSummary by heating degree day category:")
for category in ['Low', 'Medium', 'High']:
    subset = df[df['hdd_category'] == category]
    print(f"\n{category} HDD (n={len(subset)}):")
    print(f"  Mean PM2.5: {subset['pm25'].mean():.2f} μg/m³")
    print(f"  Mean respiratory visits: {subset['respiratory_visits'].mean():.2f}")
    print(f"  Correlation PM2.5-visits: {subset['pm25'].corr(subset['respiratory_visits']):.3f}")

# 2. High pollution days analysis
# Define high pollution days as PM2.5 > 75th percentile
pm25_threshold = df['pm25'].quantile(0.75)
high_pollution = df['pm25'] > pm25_threshold

print(f"\n=== High Pollution Days Analysis (PM2.5 > {pm25_threshold:.2f} μg/m³) ===")
print(f"Number of high pollution days: {high_pollution.sum()} out of {len(df)} ({high_pollution.sum()/len(df)*100:.1f}%)")
print(f"\nHigh pollution days vs normal days:")
print(f"Mean respiratory visits on high pollution days: {df[high_pollution]['respiratory_visits'].mean():.1f}")
print(f"Mean respiratory visits on normal days: {df[~high_pollution]['respiratory_visits'].mean():.1f}")
print(f"Difference: {df[high_pollution]['respiratory_visits'].mean() - df[~high_pollution]['respiratory_visits'].mean():.1f} visits")

# Statistical test
t_stat, p_value = stats.ttest_ind(
    df[high_pollution]['respiratory_visits'], 
    df[~high_pollution]['respiratory_visits'],
    equal_var=False
)
print(f"T-test for difference: t={t_stat:.3f}, p={p_value:.4f}")

# 3. Sensitivity analysis: excluding negative PM2.5 values
print("\n=== Sensitivity Analysis: Excluding Negative PM2.5 Values ===")
df_positive = df[df['pm25'] >= 0].copy()
print(f"Days with non-negative PM2.5: {len(df_positive)} out of {len(df)} ({len(df_positive)/len(df)*100:.1f}%)")
print(f"Correlation PM2.5-visits (non-negative only): {df_positive['pm25'].corr(df_positive['respiratory_visits']):.3f}")
print(f"Mean PM2.5 (non-negative): {df_positive['pm25'].mean():.2f} μg/m³")
print(f"Mean visits (non-negative): {df_positive['respiratory_visits'].mean():.2f}")

# 4. Seasonal patterns (if day_index represents consecutive days)
# Let's check if there are patterns by dividing into quarters
print("\n=== Seasonal/Temporal Patterns ===")
# Divide into 4 quarters
df['quarter'] = pd.cut(df['day_index'], bins=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])

quarter_stats = []
for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
    subset = df[df['quarter'] == quarter]
    quarter_stats.append({
        'Quarter': quarter,
        'Days': len(subset),
        'Mean_PM25': subset['pm25'].mean(),
        'Mean_Visits': subset['respiratory_visits'].mean(),
        'Mean_HDD': subset['heating_degree_day'].mean(),
        'Mean_Flu': subset['flu_index'].mean()
    })

quarter_df = pd.DataFrame(quarter_stats)
print(quarter_df.to_string(index=False))
quarter_df.to_csv('outputs/quarterly_stats.csv', index=False)

# 5. Visualization: PM2.5 and visits by HDD category
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
for category in ['Low', 'Medium', 'High']:
    subset = df[df['hdd_category'] == category]
    plt.scatter(subset['pm25'], subset['respiratory_visits'], 
                alpha=0.6, s=40, label=category)

plt.xlabel('PM2.5 (μg/m³)')
plt.ylabel('Respiratory Visits')
plt.title('PM2.5 vs Visits by Heating Degree Day Category')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
# Box plot of visits by HDD category
sns.boxplot(x='hdd_category', y='respiratory_visits', data=df)
plt.xlabel('Heating Degree Day Category')
plt.ylabel('Respiratory Visits')
plt.title('Respiratory Visits Distribution by HDD Category')
plt.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/stratified_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# 6. High pollution days visualization
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Time series with high pollution days highlighted
axes[0].plot(df['day_index'], df['pm25'], color='gray', alpha=0.5, linewidth=1, label='PM2.5')
axes[0].scatter(df.loc[high_pollution, 'day_index'], 
                df.loc[high_pollution, 'pm25'], 
                color='red', s=40, label=f'High pollution (> {pm25_threshold:.1f})', zorder=5)
axes[0].set_xlabel('Day Index')
axes[0].set_ylabel('PM2.5 (μg/m³)')
axes[0].set_title('High Pollution Days in Time Series')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Visits comparison
visit_means = [df[~high_pollution]['respiratory_visits'].mean(), 
               df[high_pollution]['respiratory_visits'].mean()]
visit_stds = [df[~high_pollution]['respiratory_visits'].std(), 
              df[high_pollution]['respiratory_visits'].std()]

bars = axes[1].bar(['Normal Days', 'High Pollution Days'], visit_means, 
                   yerr=visit_stds, capsize=10, 
                   color=['lightblue', 'lightcoral'], edgecolor='black')
axes[1].set_ylabel('Mean Respiratory Visits')
axes[1].set_title('Visits on High Pollution vs Normal Days')
axes[1].grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, (mean, std) in enumerate(zip(visit_means, visit_stds)):
    axes[1].text(i, mean + std + 2, f'{mean:.1f} ± {std:.1f}', 
                 ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/high_pollution_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# 7. Quarterly trends
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Quarterly Trends in Key Variables', fontsize=16, y=1.02)

variables = ['pm25', 'respiratory_visits', 'heating_degree_day', 'flu_index']
titles = ['PM2.5', 'Respiratory Visits', 'Heating Degree Days', 'Flu Index']
colors = ['red', 'blue', 'orange', 'green']

for idx, (var, title, color) in enumerate(zip(variables, titles, colors)):
    row = idx // 2
    col = idx % 2
    
    # Calculate means by quarter
    quarter_means = df.groupby('quarter')[var].mean()
    quarter_stds = df.groupby('quarter')[var].std()
    
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    means = [quarter_means.get(q, 0) for q in quarters]
    stds = [quarter_stds.get(q, 0) for q in quarters]
    
    axes[row, col].bar(quarters, means, yerr=stds, capsize=10, 
                       color=color, alpha=0.7, edgecolor='black')
    axes[row, col].set_title(f'{title} by Quarter')
    axes[row, col].set_xlabel('Quarter')
    axes[row, col].set_ylabel(title)
    axes[row, col].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/quarterly_trends.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nAdditional analysis complete. All plots saved to report/images/")