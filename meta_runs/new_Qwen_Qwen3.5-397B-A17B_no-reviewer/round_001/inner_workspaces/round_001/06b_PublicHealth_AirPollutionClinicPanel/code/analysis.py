#!/usr/bin/env python3
"""
Air Pollution and Respiratory Health Panel Analysis
Analyzes the relationship between PM2.5 and respiratory clinic visits
with controls for heating, flu, and school holidays.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import os

# Ensure output directories exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/daily_panel.csv')
print(f"Data shape: {df.shape}")
print(f"\nColumn names: {df.columns.tolist()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nSummary statistics:\n{df.describe()}")
print(f"\nMissing values:\n{df.isnull().sum()}")

# ============================================
# 1. Data Overview and Descriptive Statistics
# ============================================

# Create correlation matrix
plt.figure(figsize=(10, 8))
corr_cols = ['pm25', 'respiratory_visits', 'heating_degree_day', 'flu_index']
corr_matrix = df[corr_cols].corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.3f', 
            square=True, linewidths=0.5)
plt.title('Correlation Matrix: Air Pollution, Health, and Covariates', fontsize=14)
plt.tight_layout()
plt.savefig('report/images/correlation_matrix.png', dpi=150)
plt.close()
print("Saved: report/images/correlation_matrix.png")

# ============================================
# 2. Time Series Visualization
# ============================================

fig, axes = plt.subplots(5, 1, figsize=(14, 12), sharex=True)

# PM2.5 time series
axes[0].plot(df['day_index'], df['pm25'], color='darkred', linewidth=1.5)
axes[0].axhline(df['pm25'].mean(), color='red', linestyle='--', alpha=0.7, label=f"Mean: {df['pm25'].mean():.1f}")
axes[0].axhline(35, color='orange', linestyle=':', alpha=0.7, label='WHO Guideline (35 ug/m3)')
axes[0].set_ylabel('PM2.5 (ug/m3)')
axes[0].set_title('Daily PM2.5 Concentration', fontsize=12)
axes[0].legend(loc='upper right', fontsize=9)
axes[0].grid(alpha=0.3)

# Respiratory visits
axes[1].plot(df['day_index'], df['respiratory_visits'], color='darkblue', linewidth=1.5)
axes[1].axhline(df['respiratory_visits'].mean(), color='blue', linestyle='--', alpha=0.7, 
                label=f"Mean: {df['respiratory_visits'].mean():.1f}")
axes[1].set_ylabel('Visits')
axes[1].set_title('Daily Respiratory Clinic Visits', fontsize=12)
axes[1].legend(loc='upper right', fontsize=9)
axes[1].grid(alpha=0.3)

# Heating degree day
axes[2].plot(df['day_index'], df['heating_degree_day'], color='darkgreen', linewidth=1.5)
axes[2].axhline(df['heating_degree_day'].mean(), color='green', linestyle='--', alpha=0.7,
                label=f"Mean: {df['heating_degree_day'].mean():.1f}")
axes[2].set_ylabel('HDD')
axes[2].set_title('Heating Degree Days', fontsize=12)
axes[2].legend(loc='upper right', fontsize=9)
axes[2].grid(alpha=0.3)

# Flu index
axes[3].plot(df['day_index'], df['flu_index'], color='purple', linewidth=1.5)
axes[3].axhline(df['flu_index'].mean(), color='purple', linestyle='--', alpha=0.7,
                label=f"Mean: {df['flu_index'].mean():.3f}")
axes[3].set_ylabel('Flu Index')
axes[3].set_title('Flu Activity Index', fontsize=12)
axes[3].legend(loc='upper right', fontsize=9)
axes[3].grid(alpha=0.3)

# School holiday indicator
axes[4].fill_between(df['day_index'], df['school_holiday'], alpha=0.3, color='orange', 
                     where=df['school_holiday']==1, label='School Holiday')
axes[4].set_ylabel('Holiday')
axes[4].set_title('School Holiday Indicator', fontsize=12)
axes[4].set_ylim(-0.1, 1.1)
axes[4].set_yticks([0, 1])
axes[4].set_yticklabels(['No', 'Yes'])
axes[4].legend(loc='upper right', fontsize=9)
axes[4].grid(alpha=0.3)

axes[4].set_xlabel('Day Index')
plt.tight_layout()
plt.savefig('report/images/time_series.png', dpi=150)
plt.close()
print("Saved: report/images/time_series.png")

# ============================================
# 3. Scatter Plots with Regression Lines
# ============================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# PM2.5 vs Respiratory visits
axes[0, 0].scatter(df['pm25'], df['respiratory_visits'], alpha=0.6, s=50, color='darkred', edgecolors='black')
z = np.polyfit(df['pm25'], df['respiratory_visits'], 1)
p = np.poly1d(z)
axes[0, 0].plot(df['pm25'].sort_values(), p(df['pm25'].sort_values()), "r--", linewidth=2, 
                label=f'y = {z[0]:.2f}x + {z[1]:.1f}')
axes[0, 0].set_xlabel('PM2.5 (ug/m3)')
axes[0, 0].set_ylabel('Respiratory Visits')
axes[0, 0].set_title('PM2.5 vs Respiratory Clinic Visits', fontsize=12)
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)

# Heating degree day vs Respiratory visits
axes[0, 1].scatter(df['heating_degree_day'], df['respiratory_visits'], alpha=0.6, s=50, 
                   color='darkgreen', edgecolors='black')
z = np.polyfit(df['heating_degree_day'], df['respiratory_visits'], 1)
p = np.poly1d(z)
axes[0, 1].plot(df['heating_degree_day'].sort_values(), p(df['heating_degree_day'].sort_values()), 
                "g--", linewidth=2, label=f'y = {z[0]:.2f}x + {z[1]:.1f}')
axes[0, 1].set_xlabel('Heating Degree Days')
axes[0, 1].set_ylabel('Respiratory Visits')
axes[0, 1].set_title('Heating Degree Days vs Respiratory Visits', fontsize=12)
axes[0, 1].legend()
axes[0, 1].grid(alpha=0.3)

# Flu index vs Respiratory visits
axes[1, 0].scatter(df['flu_index'], df['respiratory_visits'], alpha=0.6, s=50, 
                   color='purple', edgecolors='black')
z = np.polyfit(df['flu_index'], df['respiratory_visits'], 1)
p = np.poly1d(z)
axes[1, 0].plot(df['flu_index'].sort_values(), p(df['flu_index'].sort_values()), 
                "m--", linewidth=2, label=f'y = {z[0]:.2f}x + {z[1]:.1f}')
axes[1, 0].set_xlabel('Flu Index')
axes[1, 0].set_ylabel('Respiratory Visits')
axes[1, 0].set_title('Flu Index vs Respiratory Visits', fontsize=12)
axes[1, 0].legend()
axes[1, 0].grid(alpha=0.3)

# PM2.5 by school holiday status
holiday_means = df.groupby('school_holiday')['respiratory_visits'].mean()
holiday_stds = df.groupby('school_holiday')['respiratory_visits'].std()
holiday_counts = df.groupby('school_holiday')['respiratory_visits'].count()

axes[1, 1].bar(['No Holiday', 'Holiday'], holiday_means, 
               yerr=[holiday_stds[0]/np.sqrt(holiday_counts[0]), 
                     holiday_stds[1]/np.sqrt(holiday_counts[1])],
               color=['steelblue', 'orange'], alpha=0.7, capsize=5)
axes[1, 1].set_ylabel('Mean Respiratory Visits')
axes[1, 1].set_title('Respiratory Visits by School Holiday Status', fontsize=12)
axes[1, 1].grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/scatter_plots.png', dpi=150)
plt.close()
print("Saved: report/images/scatter_plots.png")

# ============================================
# 4. Statistical Analysis - Regression Models
# ============================================

print("\n" + "="*60)
print("REGRESSION ANALYSIS RESULTS")
print("="*60)

# Model 1: Simple linear regression (PM2.5 only)
X1 = sm.add_constant(df['pm25'])
y = df['respiratory_visits']
model1 = sm.OLS(y, X1).fit()
print("\n--- Model 1: PM2.5 Only ---")
print(model1.summary())

# Model 2: Multiple regression with all covariates
X2 = df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']]
X2 = sm.add_constant(X2)
model2 = sm.OLS(y, X2).fit()
print("\n--- Model 2: Full Model (All Covariates) ---")
print(model2.summary())

# Model 3: Without school holiday (for comparison)
X3 = df[['pm25', 'heating_degree_day', 'flu_index']]
X3 = sm.add_constant(X3)
model3 = sm.OLS(y, X3).fit()
print("\n--- Model 3: Without School Holiday ---")
print(model3.summary())

# Save regression results to file
with open('outputs/regression_results.txt', 'w') as f:
    f.write("REGRESSION ANALYSIS RESULTS\n")
    f.write("="*60 + "\n\n")
    f.write("Model 1: PM2.5 Only\n")
    f.write(model1.summary().as_text() + "\n\n")
    f.write("Model 2: Full Model (All Covariates)\n")
    f.write(model2.summary().as_text() + "\n\n")
    f.write("Model 3: Without School Holiday\n")
    f.write(model3.summary().as_text() + "\n")
print("\nSaved: outputs/regression_results.txt")

# ============================================
# 5. Residual Diagnostics
# ============================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Residuals vs Fitted
axes[0, 0].scatter(model2.fittedvalues, model2.resid, alpha=0.6, color='darkblue', edgecolors='black')
axes[0, 0].axhline(0, color='red', linestyle='--')
axes[0, 0].set_xlabel('Fitted Values')
axes[0, 0].set_ylabel('Residuals')
axes[0, 0].set_title('Residuals vs Fitted Values', fontsize=12)
axes[0, 0].grid(alpha=0.3)

# Q-Q plot
sm.qqplot(model2.resid, line='45', fit=True, ax=axes[0, 1])
axes[0, 1].set_title('Q-Q Plot of Residuals', fontsize=12)

# Histogram of residuals
axes[1, 0].hist(model2.resid, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
axes[1, 0].axvline(model2.resid.mean(), color='red', linestyle='--', linewidth=2, 
                   label=f"Mean: {model2.resid.mean():.2f}")
axes[1, 0].set_xlabel('Residuals')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].set_title('Histogram of Residuals', fontsize=12)
axes[1, 0].legend()
axes[1, 0].grid(alpha=0.3, axis='y')

# Residuals over time
axes[1, 1].plot(df['day_index'], model2.resid, color='darkgreen', linewidth=1)
axes[1, 1].axhline(0, color='red', linestyle='--')
axes[1, 1].set_xlabel('Day Index')
axes[1, 1].set_ylabel('Residuals')
axes[1, 1].set_title('Residuals Over Time', fontsize=12)
axes[1, 1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/residual_diagnostics.png', dpi=150)
plt.close()
print("Saved: report/images/residual_diagnostics.png")

# ============================================
# 6. Policy-Relevant Visualization
# ============================================

# Create a policy impact visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# PM2.5 distribution with WHO guidelines
axes[0].hist(df['pm25'], bins=20, color='darkred', edgecolor='black', alpha=0.7)
axes[0].axvline(35, color='orange', linestyle='--', linewidth=2, label='WHO 24h Guideline (35 ug/m3)')
axes[0].axvline(15, color='green', linestyle='--', linewidth=2, label='WHO Annual Guideline (15 ug/m3)')
axes[0].axvline(df['pm25'].mean(), color='blue', linestyle='-', linewidth=2, 
                label=f"Study Mean: {df['pm25'].mean():.1f} ug/m3")
axes[0].set_xlabel('PM2.5 Concentration (ug/m3)')
axes[0].set_ylabel('Frequency (Days)')
axes[0].set_title('Distribution of Daily PM2.5 Levels', fontsize=12)
axes[0].legend(fontsize=9)
axes[0].grid(alpha=0.3, axis='y')

# Estimated health impact
pm25_coef = model2.params['pm25']
pm25_ci = model2.conf_int().loc['pm25']

# Calculate avoided visits for different PM2.5 reduction scenarios
reduction_scenarios = [5, 10, 15, 20]  # ug/m3 reduction
avoided_visits = [r * pm25_coef * len(df) for r in reduction_scenarios]

axes[1].bar([f"-{r} ug/m3" for r in reduction_scenarios], avoided_visits, 
            color='forestgreen', alpha=0.7, edgecolor='black')
axes[1].set_xlabel('PM2.5 Reduction Scenario')
axes[1].set_ylabel('Estimated Avoided Respiratory Visits')
axes[1].set_title(f'Estimated Health Benefits of PM2.5 Reduction\n(Coefficient: {pm25_coef:.3f} visits/ug/m3)', 
                  fontsize=12)
axes[1].grid(alpha=0.3, axis='y')

# Add value labels on bars
for i, v in enumerate(avoided_visits):
    axes[1].text(i, v + max(avoided_visits)*0.02, f'{v:.0f}', ha='center', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/policy_impact.png', dpi=150)
plt.close()
print("Saved: report/images/policy_impact.png")

# ============================================
# 7. Summary Statistics Table
# ============================================

summary_stats = df.describe().round(2)
summary_stats.loc['median'] = df.median().round(2)
summary_stats = summary_stats.reindex(['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max'])

with open('outputs/summary_statistics.txt', 'w') as f:
    f.write("SUMMARY STATISTICS\n")
    f.write("="*60 + "\n\n")
    f.write(summary_stats.to_string())
print("\nSaved: outputs/summary_statistics.txt")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print(f"\nKey Findings:")
print(f"- PM2.5 coefficient (full model): {pm25_coef:.4f} (95% CI: {pm25_ci[0]:.4f} to {pm25_ci[1]:.4f})")
print(f"- R-squared (full model): {model2.rsquared:.4f}")
print(f"- Mean PM2.5: {df['pm25'].mean():.2f} ug/m3")
print(f"- Mean respiratory visits: {df['respiratory_visits'].mean():.1f}")
print(f"\nAll figures saved to report/images/")
print(f"Regression results saved to outputs/regression_results.txt")
