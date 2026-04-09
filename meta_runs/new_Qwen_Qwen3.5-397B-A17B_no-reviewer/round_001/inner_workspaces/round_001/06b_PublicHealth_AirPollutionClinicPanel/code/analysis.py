#!/usr/bin/env python3
"""
Air Pollution and Healthcare Utilization Analysis
Analyzes the relationship between PM2.5 and respiratory clinic visits
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
df = pd.read_csv('data/daily_panel.csv')
print(f"Data shape: {df.shape}")
print(f"\nColumn names: {df.columns.tolist()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nBasic statistics:\n{df.describe()}")

# Check for missing values
print(f"\nMissing values:\n{df.isnull().sum()}")

# ============================================
# 1. Data Overview and Descriptive Statistics
# ============================================

# Create figure for data overview
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# Histogram of PM2.5
axes[0, 0].hist(df['pm25'], bins=20, edgecolor='black', alpha=0.7, color='skyblue')
axes[0, 0].set_xlabel('PM2.5 (ug/m3)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Distribution of PM2.5 Levels')
axes[0, 0].axvline(df['pm25'].mean(), color='red', linestyle='--', label=f'Mean: {df["pm25"].mean():.1f}')
axes[0, 0].legend()

# Histogram of respiratory visits
axes[0, 1].hist(df['respiratory_visits'], bins=20, edgecolor='black', alpha=0.7, color='lightcoral')
axes[0, 1].set_xlabel('Respiratory Visits')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Distribution of Respiratory Clinic Visits')
axes[0, 1].axvline(df['respiratory_visits'].mean(), color='red', linestyle='--', label=f'Mean: {df["respiratory_visits"].mean():.1f}')
axes[0, 1].legend()

# Time series of PM2.5 and respiratory visits
ax2 = fig.add_subplot(2, 3, 3)
ax2_twin = ax2.twinx()
ax2.plot(df['day_index'], df['pm25'], 'b-', label='PM2.5', alpha=0.7)
ax2_twin.plot(df['day_index'], df['respiratory_visits'], 'r-', label='Respiratory Visits', alpha=0.7)
ax2.set_xlabel('Day Index')
ax2.set_ylabel('PM2.5 (ug/m3)', color='blue')
ax2_twin.set_ylabel('Respiratory Visits', color='red')
ax2.set_title('Time Series: PM2.5 and Respiratory Visits')
ax2.legend(loc='upper left')
ax2_twin.legend(loc='upper right')

# Heating degree day distribution
axes[1, 0].hist(df['heating_degree_day'], bins=15, edgecolor='black', alpha=0.7, color='orange')
axes[1, 0].set_xlabel('Heating Degree Days')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].set_title('Distribution of Heating Degree Days')

# Flu index distribution
axes[1, 1].hist(df['flu_index'], bins=15, edgecolor='black', alpha=0.7, color='purple')
axes[1, 1].set_xlabel('Flu Index')
axes[1, 1].set_ylabel('Frequency')
axes[1, 1].set_title('Distribution of Flu Index')

# School holiday distribution
school_hol_counts = df['school_holiday'].value_counts()
axes[1, 2].bar(['No Holiday', 'Holiday'], school_hol_counts.values, color=['steelblue', 'coral'])
axes[1, 2].set_xlabel('School Holiday')
axes[1, 2].set_ylabel('Count')
axes[1, 2].set_title('School Holiday Distribution')
for i, v in enumerate(school_hol_counts.values):
    axes[1, 2].text(i, v + 1, str(v), ha='center')

plt.tight_layout()
plt.savefig('report/images/data_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: report/images/data_overview.png")

# ============================================
# 2. Correlation Analysis
# ============================================

# Calculate correlation matrix
corr_cols = ['pm25', 'respiratory_visits', 'heating_degree_day', 'flu_index', 'school_holiday']
corr_matrix = df[corr_cols].corr()

print(f"\nCorrelation Matrix:\n{corr_matrix.round(3)}")

# Create correlation heatmap
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0, fmt='.3f', 
            square=True, linewidths=0.5, ax=ax, 
            xticklabels=['PM2.5', 'Respiratory Visits', 'Heating Degree Day', 'Flu Index', 'School Holiday'],
            yticklabels=['PM2.5', 'Respiratory Visits', 'Heating Degree Day', 'Flu Index', 'School Holiday'])
ax.set_title('Correlation Matrix: Air Pollution and Healthcare Utilization', fontsize=14, pad=15)
plt.tight_layout()
plt.savefig('report/images/correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/correlation_heatmap.png")

# ============================================
# 3. Scatter Plots with Regression Lines
# ============================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# PM2.5 vs Respiratory Visits
sns.regplot(x='pm25', y='respiratory_visits', data=df, ax=axes[0, 0], 
            scatter_kws={'alpha': 0.6}, line_kws={'color': 'red'})
axes[0, 0].set_xlabel('PM2.5 (ug/m3)')
axes[0, 0].set_ylabel('Respiratory Visits')
axes[0, 0].set_title('PM2.5 vs Respiratory Clinic Visits')
# Add correlation coefficient
corr, p_val = stats.pearsonr(df['pm25'], df['respiratory_visits'])
axes[0, 0].text(0.05, 0.95, f'r = {corr:.3f}\np = {p_val:.4f}', transform=axes[0, 0].transAxes, 
                fontsize=11, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Heating Degree Day vs Respiratory Visits
sns.regplot(x='heating_degree_day', y='respiratory_visits', data=df, ax=axes[0, 1], 
            scatter_kws={'alpha': 0.6}, line_kws={'color': 'green'})
axes[0, 1].set_xlabel('Heating Degree Days')
axes[0, 1].set_ylabel('Respiratory Visits')
axes[0, 1].set_title('Heating Degree Days vs Respiratory Clinic Visits')
corr, p_val = stats.pearsonr(df['heating_degree_day'], df['respiratory_visits'])
axes[0, 1].text(0.05, 0.95, f'r = {corr:.3f}\np = {p_val:.4f}', transform=axes[0, 1].transAxes, 
                fontsize=11, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Flu Index vs Respiratory Visits
sns.regplot(x='flu_index', y='respiratory_visits', data=df, ax=axes[1, 0], 
            scatter_kws={'alpha': 0.6}, line_kws={'color': 'purple'})
axes[1, 0].set_xlabel('Flu Index')
axes[1, 0].set_ylabel('Respiratory Visits')
axes[1, 0].set_title('Flu Index vs Respiratory Clinic Visits')
corr, p_val = stats.pearsonr(df['flu_index'], df['respiratory_visits'])
axes[1, 0].text(0.05, 0.95, f'r = {corr:.3f}\np = {p_val:.4f}', transform=axes[1, 0].transAxes, 
                fontsize=11, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# PM2.5 vs Heating Degree Day (to check confounding)
sns.regplot(x='pm25', y='heating_degree_day', data=df, ax=axes[1, 1], 
            scatter_kws={'alpha': 0.6}, line_kws={'color': 'orange'})
axes[1, 1].set_xlabel('PM2.5 (ug/m3)')
axes[1, 1].set_ylabel('Heating Degree Days')
axes[1, 1].set_title('PM2.5 vs Heating Degree Days')
corr, p_val = stats.pearsonr(df['pm25'], df['heating_degree_day'])
axes[1, 1].text(0.05, 0.95, f'r = {corr:.3f}\np = {p_val:.4f}', transform=axes[1, 1].transAxes, 
                fontsize=11, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/scatter_regression.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/scatter_regression.png")

# ============================================
# 4. Multiple Linear Regression Analysis
# ============================================

# Prepare data for regression
X = df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']]
X = sm.add_constant(X)  # Add intercept
y = df['respiratory_visits']

# Fit OLS model
model = sm.OLS(y, X).fit()
print(f"\n{'='*60}")
print("MULTIPLE LINEAR REGRESSION RESULTS")
print(f"{'='*60}")
print(model.summary())

# Save regression results to file
with open('outputs/regression_results.txt', 'w') as f:
    f.write(model.summary().as_text())
print("\nSaved: outputs/regression_results.txt")

# ============================================
# 5. Effect Visualization
# ============================================

# Create effect plot showing predicted values
fig, ax = plt.subplots(figsize=(12, 7))

# Sort by PM2.5 for cleaner visualization
df_sorted = df.sort_values('pm25').reset_index(drop=True)
X_sorted = X.loc[df_sorted.index]

# Get predictions
predictions = model.predict(X_sorted)

# Plot actual vs predicted
ax.scatter(df_sorted['pm25'], df_sorted['respiratory_visits'], alpha=0.5, label='Actual', color='gray', s=50)
ax.scatter(df_sorted['pm25'], predictions, alpha=0.7, label='Predicted', color='blue', s=50)
ax.plot(df_sorted['pm25'], predictions, 'r-', linewidth=2, label='Regression Fit')
ax.set_xlabel('PM2.5 (ug/m3)')
ax.set_ylabel('Respiratory Visits')
ax.set_title('Actual vs Predicted Respiratory Visits by PM2.5 Level')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/model_fit.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/model_fit.png")

# ============================================
# 6. Residual Analysis
# ============================================

residuals = model.resid

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Residuals vs Fitted
axes[0].scatter(predictions, residuals, alpha=0.6, color='darkgreen')
axes[0].axhline(y=0, color='red', linestyle='--')
axes[0].set_xlabel('Predicted Values')
axes[0].set_ylabel('Residuals')
axes[0].set_title('Residuals vs Fitted Values')
axes[0].grid(True, alpha=0.3)

# Q-Q plot for normality
sm.qqplot(residuals, line='45', ax=axes[1])
axes[1].set_title('Q-Q Plot of Residuals')

plt.tight_layout()
plt.savefig('report/images/residual_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/residual_analysis.png")

# ============================================
# 7. PM2.5 Impact Analysis (Policy-Relevant)
# ============================================

# Categorize PM2.5 levels based on WHO guidelines
# WHO 2021: 15 ug/m3 (24-hour mean)
df['pm25_category'] = pd.cut(df['pm25'], 
                              bins=[-np.inf, 15, 25, np.inf],
                              labels=['Low (<=15)', 'Moderate (15-25)', 'High (>25)'])

fig, ax = plt.subplots(figsize=(10, 6))

# Box plot of respiratory visits by PM2.5 category
sns.boxplot(x='pm25_category', y='respiratory_visits', data=df, ax=ax, palette='viridis')
ax.set_xlabel('PM2.5 Category (ug/m3)')
ax.set_ylabel('Respiratory Visits')
ax.set_title('Respiratory Visits by PM2.5 Exposure Category')

# Add mean values
means = df.groupby('pm25_category')['respiratory_visits'].mean()
for i, cat in enumerate(['Low (<=15)', 'Moderate (15-25)', 'High (>25)']):
    if cat in means.index:
        ax.text(i, means[cat] + 2, f'Mean: {means[cat]:.1f}', ha='center', fontsize=11, 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig('report/images/pm25_category_impact.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/pm25_category_impact.png")

# ============================================
# 8. Time Series Analysis - Weekly Patterns
# ============================================

df['week'] = df['day_index'] // 7
weekly_avg = df.groupby('week')[['pm25', 'respiratory_visits']].mean()

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(weekly_avg.index, weekly_avg['pm25'], 'b-o', label='PM2.5', linewidth=2, markersize=6)
ax_twin = ax.twinx()
ax_twin.plot(weekly_avg.index, weekly_avg['respiratory_visits'], 'r-s', label='Respiratory Visits', linewidth=2, markersize=6)
ax.set_xlabel('Week')
ax.set_ylabel('PM2.5 (ug/m3)', color='blue')
ax_twin.set_ylabel('Respiratory Visits', color='red')
ax.set_title('Weekly Average: PM2.5 and Respiratory Visits')
ax.legend(loc='upper left')
ax_twin.legend(loc='upper right')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/weekly_trends.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/weekly_trends.png")

# ============================================
# 9. Save Summary Statistics
# ============================================

summary_stats = df.describe()
summary_stats.to_csv('outputs/summary_statistics.csv')
print("Saved: outputs/summary_statistics.csv")

# Save key findings
key_findings = {
    'total_days': len(df),
    'mean_pm25': float(df['pm25'].mean()),
    'std_pm25': float(df['pm25'].std()),
    'mean_respiratory_visits': float(df['respiratory_visits'].mean()),
    'std_respiratory_visits': float(df['respiratory_visits'].std()),
    'pm25_respiratory_corr': float(stats.pearsonr(df['pm25'], df['respiratory_visits'])[0]),
    'pm25_respiratory_pval': float(stats.pearsonr(df['pm25'], df['respiratory_visits'])[1]),
    'regression_pm25_coef': float(model.params['pm25']),
    'regression_pm25_pval': float(model.pvalues['pm25']),
    'r_squared': float(model.rsquared),
    'adj_r_squared': float(model.rsquared_adj)
}

import json
with open('outputs/key_findings.json', 'w') as f:
    json.dump(key_findings, f, indent=2)
print("Saved: outputs/key_findings.json")

print(f"\n{'='*60}")
print("ANALYSIS COMPLETE")
print(f"{'='*60}")
print(f"Total observations: {len(df)}")
print(f"PM2.5 mean (std): {key_findings['mean_pm25']:.2f} ({key_findings['std_pm25']:.2f})")
print(f"Respiratory visits mean (std): {key_findings['mean_respiratory_visits']:.2f} ({key_findings['std_respiratory_visits']:.2f})")
print(f"PM2.5-Respiratory correlation: {key_findings['pm25_respiratory_corr']:.3f} (p={key_findings['pm25_respiratory_pval']:.4f})")
print(f"Regression R-squared: {key_findings['r_squared']:.3f}")
print(f"PM2.5 coefficient: {key_findings['regression_pm25_coef']:.3f} (p={key_findings['regression_pm25_pval']:.4f})")
