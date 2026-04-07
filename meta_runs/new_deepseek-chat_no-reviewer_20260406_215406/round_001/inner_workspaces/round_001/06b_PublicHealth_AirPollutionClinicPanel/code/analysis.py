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
df = pd.read_csv('data/daily_panel.csv')

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("Starting comprehensive analysis...")

# 1. Time series visualization
fig, axes = plt.subplots(3, 2, figsize=(14, 12))
fig.suptitle('Time Series of Daily Variables', fontsize=16, y=1.02)

# PM2.5 over time
axes[0, 0].plot(df['day_index'], df['pm25'], color='red', linewidth=1.5)
axes[0, 0].set_title('PM2.5 Concentration Over Time')
axes[0, 0].set_xlabel('Day Index')
axes[0, 0].set_ylabel('PM2.5 (μg/m³)')
axes[0, 0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)

# Respiratory visits over time
axes[0, 1].plot(df['day_index'], df['respiratory_visits'], color='blue', linewidth=1.5)
axes[0, 1].set_title('Respiratory Visits Over Time')
axes[0, 1].set_xlabel('Day Index')
axes[0, 1].set_ylabel('Number of Visits')

# Heating degree days over time
axes[1, 0].plot(df['day_index'], df['heating_degree_day'], color='orange', linewidth=1.5)
axes[1, 0].set_title('Heating Degree Days Over Time')
axes[1, 0].set_xlabel('Day Index')
axes[1, 0].set_ylabel('Heating Degree Days')

# Flu index over time
axes[1, 1].plot(df['day_index'], df['flu_index'], color='green', linewidth=1.5)
axes[1, 1].set_title('Flu Index Over Time')
axes[1, 1].set_xlabel('Day Index')
axes[1, 1].set_ylabel('Flu Index')

# School holiday indicator
axes[2, 0].scatter(df['day_index'], df['school_holiday'], color='purple', s=20)
axes[2, 0].set_title('School Holiday Indicator Over Time')
axes[2, 0].set_xlabel('Day Index')
axes[2, 0].set_ylabel('School Holiday (0/1)')
axes[2, 0].set_yticks([0, 1])
axes[2, 0].set_ylim(-0.1, 1.1)

# Remove empty subplot
fig.delaxes(axes[2, 1])

plt.tight_layout()
plt.savefig('report/images/time_series.png', dpi=300, bbox_inches='tight')
plt.close()

print("Time series plots saved.")

# 2. Correlation analysis
correlation_matrix = df.corr()
print("\nCorrelation Matrix:")
print(correlation_matrix)

# Save correlation matrix
correlation_matrix.to_csv('outputs/correlation_matrix.csv')

# Visualize correlation matrix
plt.figure(figsize=(10, 8))
heatmap = sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                      square=True, linewidths=1, cbar_kws={"shrink": 0.8})
plt.title('Correlation Matrix of Variables')
plt.tight_layout()
plt.savefig('report/images/correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

print("Correlation matrix saved.")

# 3. Scatter plots of PM2.5 vs respiratory visits with other variables as hue
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('PM2.5 vs Respiratory Visits with Covariates', fontsize=16, y=1.02)

# Basic scatter
axes[0, 0].scatter(df['pm25'], df['respiratory_visits'], alpha=0.6, s=30)
axes[0, 0].set_title('PM2.5 vs Respiratory Visits')
axes[0, 0].set_xlabel('PM2.5 (μg/m³)')
axes[0, 0].set_ylabel('Respiratory Visits')

# Add regression line for basic relationship
z = np.polyfit(df['pm25'], df['respiratory_visits'], 1)
p = np.poly1d(z)
axes[0, 0].plot(df['pm25'], p(df['pm25']), "r--", alpha=0.8, linewidth=2)

# Color by heating degree day (categorical-ish)
scatter1 = axes[0, 1].scatter(df['pm25'], df['respiratory_visits'], 
                              c=df['heating_degree_day'], alpha=0.6, s=30, cmap='viridis')
axes[0, 1].set_title('PM2.5 vs Respiratory Visits (colored by Heating Degree Day)')
axes[0, 1].set_xlabel('PM2.5 (μg/m³)')
axes[0, 1].set_ylabel('Respiratory Visits')
plt.colorbar(scatter1, ax=axes[0, 1], label='Heating Degree Day')

# Color by flu index
scatter2 = axes[1, 0].scatter(df['pm25'], df['respiratory_visits'], 
                              c=df['flu_index'], alpha=0.6, s=30, cmap='plasma')
axes[1, 0].set_title('PM2.5 vs Respiratory Visits (colored by Flu Index)')
axes[1, 0].set_xlabel('PM2.5 (μg/m³)')
axes[1, 0].set_ylabel('Respiratory Visits')
plt.colorbar(scatter2, ax=axes[1, 0], label='Flu Index')

# Different markers for school holiday
school_holiday_mask = df['school_holiday'] == 1
axes[1, 1].scatter(df.loc[~school_holiday_mask, 'pm25'], 
                   df.loc[~school_holiday_mask, 'respiratory_visits'], 
                   alpha=0.6, s=30, label='No School Holiday', color='blue')
axes[1, 1].scatter(df.loc[school_holiday_mask, 'pm25'], 
                   df.loc[school_holiday_mask, 'respiratory_visits'], 
                   alpha=0.8, s=50, marker='s', label='School Holiday', color='red')
axes[1, 1].set_title('PM2.5 vs Respiratory Visits (School Holiday)')
axes[1, 1].set_xlabel('PM2.5 (μg/m³)')
axes[1, 1].set_ylabel('Respiratory Visits')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('report/images/pm25_vs_visits_scatter.png', dpi=300, bbox_inches='tight')
plt.close()

print("Scatter plots saved.")

# 4. Distribution plots
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
fig.suptitle('Distributions of Variables', fontsize=16, y=1.02)

# PM2.5 distribution
axes[0, 0].hist(df['pm25'], bins=20, edgecolor='black', alpha=0.7, color='red')
axes[0, 0].set_title('PM2.5 Distribution')
axes[0, 0].set_xlabel('PM2.5 (μg/m³)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].axvline(x=df['pm25'].mean(), color='darkred', linestyle='--', label=f'Mean: {df["pm25"].mean():.2f}')
axes[0, 0].legend()

# Respiratory visits distribution
axes[0, 1].hist(df['respiratory_visits'], bins=20, edgecolor='black', alpha=0.7, color='blue')
axes[0, 1].set_title('Respiratory Visits Distribution')
axes[0, 1].set_xlabel('Number of Visits')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].axvline(x=df['respiratory_visits'].mean(), color='darkblue', linestyle='--', label=f'Mean: {df["respiratory_visits"].mean():.2f}')
axes[0, 1].legend()

# Heating degree day distribution
axes[0, 2].hist(df['heating_degree_day'], bins=15, edgecolor='black', alpha=0.7, color='orange')
axes[0, 2].set_title('Heating Degree Days Distribution')
axes[0, 2].set_xlabel('Heating Degree Days')
axes[0, 2].set_ylabel('Frequency')
axes[0, 2].axvline(x=df['heating_degree_day'].mean(), color='darkorange', linestyle='--', label=f'Mean: {df["heating_degree_day"].mean():.2f}')
axes[0, 2].legend()

# Flu index distribution
axes[1, 0].hist(df['flu_index'], bins=20, edgecolor='black', alpha=0.7, color='green')
axes[1, 0].set_title('Flu Index Distribution')
axes[1, 0].set_xlabel('Flu Index')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].axvline(x=df['flu_index'].mean(), color='darkgreen', linestyle='--', label=f'Mean: {df["flu_index"].mean():.3f}')
axes[1, 0].legend()

# School holiday distribution
school_holiday_counts = df['school_holiday'].value_counts()
axes[1, 1].bar(['No Holiday', 'Holiday'], school_holiday_counts.values, 
               color=['lightblue', 'lightcoral'], edgecolor='black')
axes[1, 1].set_title('School Holiday Distribution')
axes[1, 1].set_ylabel('Count')
for i, v in enumerate(school_holiday_counts.values):
    axes[1, 1].text(i, v + 1, str(v), ha='center')

# Remove empty subplot
fig.delaxes(axes[1, 2])

plt.tight_layout()
plt.savefig('report/images/distributions.png', dpi=300, bbox_inches='tight')
plt.close()

print("Distribution plots saved.")

# 5. Lag analysis for PM2.5 effect (potential delayed effects)
print("\nPerforming lag analysis...")
max_lag = 7  # Look at lags up to 7 days
lag_correlations = []

for lag in range(max_lag + 1):
    if lag == 0:
        corr = df['pm25'].corr(df['respiratory_visits'])
    else:
        # Shift PM2.5 forward (lag days before)
        shifted_pm25 = df['pm25'].shift(lag)
        # Align with respiratory visits
        aligned_df = pd.DataFrame({
            'pm25_lag': shifted_pm25,
            'respiratory_visits': df['respiratory_visits']
        }).dropna()
        corr = aligned_df['pm25_lag'].corr(aligned_df['respiratory_visits'])
    
    lag_correlations.append({
        'lag_days': lag,
        'correlation': corr,
        'abs_correlation': abs(corr)
    })

lag_df = pd.DataFrame(lag_correlations)
print("\nCorrelations at different lags:")
print(lag_df)
lag_df.to_csv('outputs/lag_correlations.csv', index=False)

# Plot lag correlations
plt.figure(figsize=(10, 6))
plt.plot(lag_df['lag_days'], lag_df['correlation'], 'o-', linewidth=2, markersize=8)
plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
plt.title('Correlation between PM2.5 (lagged) and Respiratory Visits')
plt.xlabel('Lag (days)')
plt.ylabel('Correlation Coefficient')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/lag_correlations.png', dpi=300, bbox_inches='tight')
plt.close()

print("Lag analysis complete.")

print("\nAnalysis complete. All plots saved to report/images/")