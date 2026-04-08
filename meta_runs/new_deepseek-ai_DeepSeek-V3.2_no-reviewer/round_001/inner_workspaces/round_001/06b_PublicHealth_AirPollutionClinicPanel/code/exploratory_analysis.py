import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
import os

# Set style for better visualizations
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load the data
df = pd.read_csv('../data/daily_panel.csv')
print("Dataset shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nSummary statistics:")
print(df.describe())

# Check for any negative PM2.5 values (which might be measurement errors)
negative_pm25 = df[df['pm25'] < 0]
print(f"\nNumber of days with negative PM2.5: {len(negative_pm25)}")
print("These might be measurement errors or calibration issues")

# Basic time series plot
fig, axes = plt.subplots(3, 2, figsize=(14, 12))
fig.suptitle('Daily Panel Data Time Series', fontsize=16, y=1.02)

# PM2.5 over time
axes[0, 0].plot(df['day_index'], df['pm25'], color='red', linewidth=1.5)
axes[0, 0].set_title('PM2.5 Concentration Over Time')
axes[0, 0].set_xlabel('Day Index')
axes[0, 0].set_ylabel('PM2.5 (µg/m³)')
axes[0, 0].axhline(y=df['pm25'].mean(), color='gray', linestyle='--', alpha=0.7, label=f'Mean: {df["pm25"].mean():.1f}')
axes[0, 0].legend()

# Respiratory visits over time
axes[0, 1].plot(df['day_index'], df['respiratory_visits'], color='blue', linewidth=1.5)
axes[0, 1].set_title('Respiratory Visits Over Time')
axes[0, 1].set_xlabel('Day Index')
axes[0, 1].set_ylabel('Number of Visits')
axes[0, 1].axhline(y=df['respiratory_visits'].mean(), color='gray', linestyle='--', alpha=0.7, label=f'Mean: {df["respiratory_visits"].mean():.1f}')
axes[0, 1].legend()

# Heating degree days
axes[1, 0].plot(df['day_index'], df['heating_degree_day'], color='orange', linewidth=1.5)
axes[1, 0].set_title('Heating Degree Days Over Time')
axes[1, 0].set_xlabel('Day Index')
axes[1, 0].set_ylabel('Heating Degree Days')

# Flu index
axes[1, 1].plot(df['day_index'], df['flu_index'], color='green', linewidth=1.5)
axes[1, 1].set_title('Flu Index Over Time')
axes[1, 1].set_xlabel('Day Index')
axes[1, 1].set_ylabel('Flu Index')

# School holiday (binary)
axes[2, 0].scatter(df['day_index'], df['school_holiday'], color='purple', alpha=0.6, s=30)
axes[2, 0].set_title('School Holiday Indicator Over Time')
axes[2, 0].set_xlabel('Day Index')
axes[2, 0].set_ylabel('School Holiday (1=Yes, 0=No)')
axes[2, 0].set_yticks([0, 1])
axes[2, 0].set_ylim(-0.1, 1.1)

# Remove empty subplot
fig.delaxes(axes[2, 1])

plt.tight_layout()
plt.savefig('../report/images/time_series_plots.png', dpi=300, bbox_inches='tight')
plt.close()

# Correlation analysis
print("\n=== Correlation Analysis ===")
correlation_matrix = df.corr()
print("Correlation matrix:")
print(correlation_matrix)

# Visualize correlation matrix
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f', 
            square=True, linewidths=1, cbar_kws={"shrink": 0.8})
plt.title('Correlation Matrix of Variables')
plt.tight_layout()
plt.savefig('../report/images/correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

# Focus on PM2.5 and respiratory visits correlation
print("\n=== PM2.5 and Respiratory Visits Relationship ===")
corr_pm25_resp = df['pm25'].corr(df['respiratory_visits'])
print(f"Correlation between PM2.5 and respiratory visits: {corr_pm25_resp:.3f}")

# Scatter plot with regression line
plt.figure(figsize=(10, 6))
sns.regplot(x='pm25', y='respiratory_visits', data=df, scatter_kws={'alpha':0.6, 's':50}, 
            line_kws={'color': 'red', 'linewidth': 2})
plt.title('PM2.5 vs Respiratory Visits')
plt.xlabel('PM2.5 Concentration (µg/m³)')
plt.ylabel('Respiratory Visits')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/pm25_vs_respiratory_visits.png', dpi=300, bbox_inches='tight')
plt.close()

# Check for lagged effects
print("\n=== Lagged Effects Analysis ===")
max_lag = 7  # Check up to 7-day lags
lag_correlations = []
for lag in range(1, max_lag + 1):
    # Shift PM2.5 forward to see effect on future respiratory visits
    shifted_pm25 = df['pm25'].shift(lag)
    corr = shifted_pm25.corr(df['respiratory_visits'])
    lag_correlations.append((lag, corr))
    print(f"Lag {lag} days: PM2.5 correlation with respiratory visits = {corr:.3f}")

# Plot lag correlations
lags, correlations = zip(*lag_correlations)
plt.figure(figsize=(10, 6))
plt.plot(lags, correlations, 'o-', linewidth=2, markersize=8)
plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
plt.title('Correlation between PM2.5 and Respiratory Visits by Lag')
plt.xlabel('Lag (days)')
plt.ylabel('Correlation Coefficient')
plt.grid(True, alpha=0.3)
plt.xticks(range(1, max_lag + 1))
plt.tight_layout()
plt.savefig('../report/images/lag_correlations.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nExploratory analysis complete. Figures saved to ../report/images/")
