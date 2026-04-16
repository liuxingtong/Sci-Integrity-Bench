import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
data_path = '../data/daily_panel.csv'
df = pd.read_csv(data_path)

print("=== Initial Data Analysis ===")
print(f"Dataset covers {len(df)} days")
print(f"PM2.5 range: {df['pm25'].min():.2f} to {df['pm25'].max():.2f} μg/m³")
print(f"Respiratory visits range: {df['respiratory_visits'].min()} to {df['respiratory_visits'].max()}")
print(f"Heating degree days range: {df['heating_degree_day'].min()} to {df['heating_degree_day'].max()}")
print(f"Flu index range: {df['flu_index'].min():.3f} to {df['flu_index'].max():.3f}")
print(f"School holidays: {df['school_holiday'].sum()} days out of {len(df)}")

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# 1. Time series plots
fig, axes = plt.subplots(3, 2, figsize=(14, 12))
fig.suptitle('Time Series of Daily Variables', fontsize=16, y=1.02)

# PM2.5 over time
axes[0, 0].plot(df['day_index'], df['pm25'], color='red', linewidth=1.5)
axes[0, 0].set_title('PM2.5 Concentration (μg/m³)')
axes[0, 0].set_xlabel('Day Index')
axes[0, 0].set_ylabel('PM2.5')
axes[0, 0].fill_between(df['day_index'], 0, df['pm25'], alpha=0.3, color='red')

# Respiratory visits over time
axes[0, 1].plot(df['day_index'], df['respiratory_visits'], color='blue', linewidth=1.5)
axes[0, 1].set_title('Respiratory Visits')
axes[0, 1].set_xlabel('Day Index')
axes[0, 1].set_ylabel('Visits')
axes[0, 1].fill_between(df['day_index'], 0, df['respiratory_visits'], alpha=0.3, color='blue')

# Heating degree days
axes[1, 0].plot(df['day_index'], df['heating_degree_day'], color='orange', linewidth=1.5)
axes[1, 0].set_title('Heating Degree Days')
axes[1, 0].set_xlabel('Day Index')
axes[1, 0].set_ylabel('HDD')

# Flu index
axes[1, 1].plot(df['day_index'], df['flu_index'], color='green', linewidth=1.5)
axes[1, 1].set_title('Flu Index')
axes[1, 1].set_xlabel('Day Index')
axes[1, 1].set_ylabel('Flu Index')

# School holidays (as markers)
school_days = df[df['school_holiday'] == 1]
axes[2, 0].scatter(school_days['day_index'], school_days['respiratory_visits'], 
                   color='purple', s=100, alpha=0.7, label='School Holiday')
axes[2, 0].plot(df['day_index'], df['respiratory_visits'], color='blue', alpha=0.3, linewidth=1)
axes[2, 0].set_title('Respiratory Visits with School Holidays')
axes[2, 0].set_xlabel('Day Index')
axes[2, 0].set_ylabel('Visits')
axes[2, 0].legend()

# Scatter: PM2.5 vs Respiratory visits
axes[2, 1].scatter(df['pm25'], df['respiratory_visits'], alpha=0.6, color='darkred')
axes[2, 1].set_title('PM2.5 vs Respiratory Visits')
axes[2, 1].set_xlabel('PM2.5 (μg/m³)')
axes[2, 1].set_ylabel('Respiratory Visits')

# Add trend line
z = np.polyfit(df['pm25'], df['respiratory_visits'], 1)
p = np.poly1d(z)
axes[2, 1].plot(df['pm25'], p(df['pm25']), "r--", alpha=0.8, 
                label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
axes[2, 1].legend()

plt.tight_layout()
plt.savefig('../report/images/time_series_plots.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nSaved time series plots to ../report/images/time_series_plots.png")

# 2. Correlation matrix
corr_matrix = df.corr()
print("\n=== Correlation Matrix ===")
print(corr_matrix)

# Visualize correlation matrix
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
            square=True, linewidths=1, cbar_kws={"shrink": 0.8})
plt.title('Correlation Matrix of Variables', fontsize=16)
plt.tight_layout()
plt.savefig('../report/images/correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nSaved correlation matrix to ../report/images/correlation_matrix.png")

# 3. Distribution plots
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Distribution of Variables', fontsize=16, y=1.02)

# PM2.5 distribution
axes[0, 0].hist(df['pm25'], bins=20, edgecolor='black', alpha=0.7, color='red')
axes[0, 0].set_title('PM2.5 Distribution')
axes[0, 0].set_xlabel('PM2.5 (μg/m³)')
axes[0, 0].set_ylabel('Frequency')

# Respiratory visits distribution
axes[0, 1].hist(df['respiratory_visits'], bins=20, edgecolor='black', alpha=0.7, color='blue')
axes[0, 1].set_title('Respiratory Visits Distribution')
axes[0, 1].set_xlabel('Visits')
axes[0, 1].set_ylabel('Frequency')

# Heating degree days distribution
axes[0, 2].hist(df['heating_degree_day'], bins=15, edgecolor='black', alpha=0.7, color='orange')
axes[0, 2].set_title('Heating Degree Days Distribution')
axes[0, 2].set_xlabel('HDD')
axes[0, 2].set_ylabel('Frequency')

# Flu index distribution
axes[1, 0].hist(df['flu_index'], bins=20, edgecolor='black', alpha=0.7, color='green')
axes[1, 0].set_title('Flu Index Distribution')
axes[1, 0].set_xlabel('Flu Index')
axes[1, 0].set_ylabel('Frequency')

# School holiday distribution
school_counts = df['school_holiday'].value_counts()
axes[1, 1].bar(['No Holiday', 'Holiday'], school_counts.values, 
               color=['gray', 'purple'], alpha=0.7, edgecolor='black')
axes[1, 1].set_title('School Holiday Distribution')
axes[1, 1].set_ylabel('Count')

# Boxplot: Respiratory visits by school holiday
axes[1, 2].boxplot([df[df['school_holiday']==0]['respiratory_visits'],
                    df[df['school_holiday']==1]['respiratory_visits']],
                   labels=['No Holiday', 'Holiday'])
axes[1, 2].set_title('Respiratory Visits by School Holiday')
axes[1, 2].set_ylabel('Visits')

plt.tight_layout()
plt.savefig('../report/images/distribution_plots.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nSaved distribution plots to ../report/images/distribution_plots.png")

# 4. Save correlation results to file
corr_results_path = '../outputs/correlation_results.txt'
with open(corr_results_path, 'w') as f:
    f.write("=== Correlation Analysis ===\n\n")
    f.write("Correlation Matrix:\n")
    f.write(corr_matrix.to_string())
    f.write("\n\n")
    
    # Specific correlations of interest
    f.write("Key Correlations:\n")
    f.write(f"PM2.5 vs Respiratory visits: {corr_matrix.loc['pm25', 'respiratory_visits']:.4f}\n")
    f.write(f"PM2.5 vs Heating degree days: {corr_matrix.loc['pm25', 'heating_degree_day']:.4f}\n")
    f.write(f"PM2.5 vs Flu index: {corr_matrix.loc['pm25', 'flu_index']:.4f}\n")
    f.write(f"Respiratory visits vs Heating degree days: {corr_matrix.loc['respiratory_visits', 'heating_degree_day']:.4f}\n")
    f.write(f"Respiratory visits vs Flu index: {corr_matrix.loc['respiratory_visits', 'flu_index']:.4f}\n")
    f.write(f"Respiratory visits vs School holiday: {corr_matrix.loc['respiratory_visits', 'school_holiday']:.4f}\n")

print(f"\nSaved correlation results to {corr_results_path}")

print("\n=== Analysis Complete ===")