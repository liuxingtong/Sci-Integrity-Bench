"""
Public Health Air Pollution Clinic Panel Analysis
=================================================
Research Question: How does ambient PM2.5 exposure affect daily respiratory clinic visits?

This analysis examines the relationship between PM2.5 levels and respiratory healthcare
utilization while controlling for heating-related factors, flu activity, and school holidays.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10

# Load data
print("Loading data...")
df = pd.read_csv('data/daily_panel.csv')
print(f"Dataset shape: {df.shape}")
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nData summary:\n{df.describe()}")

# Data quality check
print("\n" + "="*60)
print("DATA QUALITY CHECK")
print("="*60)
print(f"Missing values:\n{df.isnull().sum()}")
print(f"\nDuplicated rows: {df.duplicated().sum()}")

# Create output directories
import os
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# ============================================================================
# EXPLORATORY DATA ANALYSIS
# ============================================================================

print("\n" + "="*60)
print("EXPLORATORY DATA ANALYSIS")
print("="*60)

# Correlation matrix
corr_matrix = df.corr()
print("\nCorrelation Matrix:")
print(corr_matrix.round(3))

# Save correlation matrix
corr_matrix.to_csv('outputs/correlation_matrix.csv')

# Basic statistics by PM2.5 quartiles
df['pm25_quartile'] = pd.qcut(df['pm25'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'])
quartile_stats = df.groupby('pm25_quartile')['respiratory_visits'].agg(['mean', 'std', 'count'])
print("\nRespiratory visits by PM2.5 quartile:")
print(quartile_stats)
quartile_stats.to_csv('outputs/quartile_stats.csv')

# ============================================================================
# VISUALIZATION 1: Time Series Plot
# ============================================================================

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# PM2.5 time series
axes[0].plot(df['day_index'], df['pm25'], color='#d62728', linewidth=1.5, label='PM2.5')
axes[0].axhline(y=df['pm25'].mean(), color='#d62728', linestyle='--', alpha=0.7, label=f'Mean: {df["pm25"].mean():.1f}')
axes[0].set_ylabel('PM2.5 (μg/m³)', fontsize=11)
axes[0].set_title('Daily PM2.5 Concentration', fontsize=12, fontweight='bold')
axes[0].legend(loc='upper right')
axes[0].fill_between(df['day_index'], df['pm25'], alpha=0.3, color='#d62728')

# Respiratory visits time series
axes[1].plot(df['day_index'], df['respiratory_visits'], color='#1f77b4', linewidth=1.5, label='Respiratory Visits')
axes[1].axhline(y=df['respiratory_visits'].mean(), color='#1f77b4', linestyle='--', alpha=0.7, label=f'Mean: {df["respiratory_visits"].mean():.1f}')
axes[1].set_ylabel('Respiratory Visits', fontsize=11)
axes[1].set_title('Daily Respiratory Clinic Visits', fontsize=12, fontweight='bold')
axes[1].legend(loc='upper right')
axes[1].fill_between(df['day_index'], df['respiratory_visits'], alpha=0.3, color='#1f77b4')

# Covariates
ax2 = axes[2]
ax2.plot(df['day_index'], df['heating_degree_day'], color='#ff7f0e', linewidth=1.5, label='Heating Degree Days', alpha=0.8)
ax2.plot(df['day_index'], df['flu_index']*10, color='#2ca02c', linewidth=1.5, label='Flu Index (×10)', alpha=0.8)
school_holidays = df[df['school_holiday'] == 1]['day_index']
for day in school_holidays:
    ax2.axvline(x=day, color='gray', alpha=0.3, linestyle='-', linewidth=0.5)
ax2.set_ylabel('Covariate Values', fontsize=11)
ax2.set_xlabel('Day Index', fontsize=11)
ax2.set_title('Covariates: Heating Degree Days, Flu Index, and School Holidays (gray lines)', fontsize=12, fontweight='bold')
ax2.legend(loc='upper right')

plt.tight_layout()
plt.savefig('report/images/fig1_time_series.png', bbox_inches='tight', facecolor='white')
plt.close()
print("\nSaved: report/images/fig1_time_series.png")

# ============================================================================
# VISUALIZATION 2: Scatter Plot with Regression Line
# ============================================================================

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# PM2.5 vs Respiratory Visits
axes[0].scatter(df['pm25'], df['respiratory_visits'], alpha=0.6, s=50, color='#1f77b4', edgecolors='white', linewidth=0.5)
z = np.polyfit(df['pm25'], df['respiratory_visits'], 1)
p = np.poly1d(z)
axes[0].plot(df['pm25'].sort_values(), p(df['pm25'].sort_values()), "r--", linewidth=2, label=f'Linear fit: y={z[0]:.2f}x+{z[1]:.1f}')
axes[0].set_xlabel('PM2.5 (μg/m³)', fontsize=11)
axes[0].set_ylabel('Respiratory Visits', fontsize=11)
axes[0].set_title('PM2.5 vs Respiratory Visits', fontsize=12, fontweight='bold')
axes[0].legend()

# Add correlation coefficient
corr_coef = df['pm25'].corr(df['respiratory_visits'])
axes[0].annotate(f'r = {corr_coef:.3f}', xy=(0.05, 0.95), xycoords='axes fraction', 
                 fontsize=11, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Box plot by quartiles
df.boxplot(column='respiratory_visits', by='pm25_quartile', ax=axes[1])
axes[1].set_xlabel('PM2.5 Quartile', fontsize=11)
axes[1].set_ylabel('Respiratory Visits', fontsize=11)
axes[1].set_title('Respiratory Visits by PM2.5 Quartile', fontsize=12, fontweight='bold')
plt.suptitle('')  # Remove default title

plt.tight_layout()
plt.savefig('report/images/fig2_scatter_boxplot.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: report/images/fig2_scatter_boxplot.png")

# ============================================================================
# VISUALIZATION 3: Correlation Heatmap
# ============================================================================

fig, ax = plt.subplots(figsize=(10, 8))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
            square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)
ax.set_title('Correlation Matrix of Variables', fontsize=13, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('report/images/fig3_correlation_heatmap.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: report/images/fig3_correlation_heatmap.png")

# ============================================================================
# STATISTICAL MODELING
# ============================================================================

print("\n" + "="*60)
print("STATISTICAL MODELING")
print("="*60)

# Model 1: Simple OLS (PM2.5 only)
print("\n--- Model 1: Simple OLS (PM2.5 only) ---")
X1 = sm.add_constant(df['pm25'])
y = df['respiratory_visits']
model1 = sm.OLS(y, X1).fit()
print(model1.summary())

# Save model results
with open('outputs/model1_summary.txt', 'w') as f:
    f.write(model1.summary().as_text())

# Model 2: Multiple Regression (with all covariates)
print("\n--- Model 2: Multiple Regression (with covariates) ---")
X2 = df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']]
X2 = sm.add_constant(X2)
model2 = sm.OLS(y, X2).fit()
print(model2.summary())

with open('outputs/model2_summary.txt', 'w') as f:
    f.write(model2.summary().as_text())

# Model 3: Multiple Regression with interaction
print("\n--- Model 3: Multiple Regression with PM2.5 × Heating interaction ---")
df['pm25_heating_interact'] = df['pm25'] * df['heating_degree_day']
X3 = df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday', 'pm25_heating_interact']]
X3 = sm.add_constant(X3)
model3 = sm.OLS(y, X3).fit()
print(model3.summary())

with open('outputs/model3_summary.txt', 'w') as f:
    f.write(model3.summary().as_text())

# Model comparison
print("\n--- Model Comparison ---")
comparison = pd.DataFrame({
    'Model': ['Model 1 (PM2.5 only)', 'Model 2 (Full)', 'Model 3 (With Interaction)'],
    'R-squared': [model1.rsquared, model2.rsquared, model3.rsquared],
    'Adj. R-squared': [model1.rsquared_adj, model2.rsquared_adj, model3.rsquared_adj],
    'AIC': [model1.aic, model2.aic, model3.aic],
    'BIC': [model1.bic, model2.bic, model3.bic]
})
print(comparison)
comparison.to_csv('outputs/model_comparison.csv', index=False)

# ============================================================================
# VISUALIZATION 4: Regression Results
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Coefficient comparison
coef_data = pd.DataFrame({
    'Variable': ['PM2.5', 'Heating Degree Day', 'Flu Index', 'School Holiday'],
    'Model 1': [model1.params['pm25'], np.nan, np.nan, np.nan],
    'Model 2': [model2.params['pm25'], model2.params['heating_degree_day'], 
                model2.params['flu_index'], model2.params['school_holiday']]
})

x = np.arange(len(coef_data))
width = 0.35
axes[0, 0].bar(x - width/2, coef_data['Model 1'], width, label='Model 1 (PM2.5 only)', alpha=0.8)
axes[0, 0].bar(x + width/2, coef_data['Model 2'], width, label='Model 2 (Full)', alpha=0.8)
axes[0, 0].set_ylabel('Coefficient', fontsize=11)
axes[0, 0].set_title('Coefficient Comparison Across Models', fontsize=12, fontweight='bold')
axes[0, 0].set_xticks(x)
axes[0, 0].set_xticklabels(coef_data['Variable'], rotation=15, ha='right')
axes[0, 0].legend()
axes[0, 0].axhline(y=0, color='black', linestyle='-', linewidth=0.5)

# Residuals vs Fitted (Model 2)
axes[0, 1].scatter(model2.fittedvalues, model2.resid, alpha=0.6, edgecolors='white', linewidth=0.5)
axes[0, 1].axhline(y=0, color='red', linestyle='--', linewidth=1.5)
axes[0, 1].set_xlabel('Fitted Values', fontsize=11)
axes[0, 1].set_ylabel('Residuals', fontsize=11)
axes[0, 1].set_title('Residuals vs Fitted (Model 2)', fontsize=12, fontweight='bold')

# Q-Q plot
stats.probplot(model2.resid, dist="norm", plot=axes[1, 0])
axes[1, 0].set_title('Q-Q Plot of Residuals (Model 2)', fontsize=12, fontweight='bold')

# Partial regression plot for PM2.5
from statsmodels.graphics.regressionplots import plot_partregress_grid
# Create partial regression plot manually
residuals_y = sm.OLS(y, sm.add_constant(df[['heating_degree_day', 'flu_index', 'school_holiday']])).fit().resid
residuals_x = sm.OLS(df['pm25'], sm.add_constant(df[['heating_degree_day', 'flu_index', 'school_holiday']])).fit().resid
axes[1, 1].scatter(residuals_x, residuals_y, alpha=0.6, edgecolors='white', linewidth=0.5)
z = np.polyfit(residuals_x, residuals_y, 1)
p = np.poly1d(z)
axes[1, 1].plot(residuals_x.sort_values(), p(residuals_x.sort_values()), "r--", linewidth=2)
axes[1, 1].set_xlabel('PM2.5 (partialled out)', fontsize=11)
axes[1, 1].set_ylabel('Respiratory Visits (partialled out)', fontsize=11)
axes[1, 1].set_title('Partial Regression Plot: PM2.5 Effect', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/fig4_regression_diagnostics.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: report/images/fig4_regression_diagnostics.png")

# ============================================================================
# VISUALIZATION 5: Policy-Relevant Analysis
# ============================================================================

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Dose-response curve
pm25_range = np.linspace(df['pm25'].min(), df['pm25'].max(), 100)
# Predict using mean values of other covariates
mean_heating = df['heating_degree_day'].mean()
mean_flu = df['flu_index'].mean()
mean_school = df['school_holiday'].mean()

predicted_visits = (model2.params['const'] + 
                   model2.params['pm25'] * pm25_range + 
                   model2.params['heating_degree_day'] * mean_heating +
                   model2.params['flu_index'] * mean_flu +
                   model2.params['school_holiday'] * mean_school)

axes[0].plot(pm25_range, predicted_visits, 'b-', linewidth=2.5, label='Predicted visits')
axes[0].fill_between(pm25_range, predicted_visits - 1.96*model2.resid.std(), 
                     predicted_visits + 1.96*model2.resid.std(), alpha=0.2, color='blue')
axes[0].scatter(df['pm25'], df['respiratory_visits'], alpha=0.4, s=40, color='gray', label='Observed data')
axes[0].set_xlabel('PM2.5 (μg/m³)', fontsize=11)
axes[0].set_ylabel('Predicted Respiratory Visits', fontsize=11)
axes[0].set_title('Dose-Response: PM2.5 and Respiratory Visits', fontsize=12, fontweight='bold')
axes[0].legend()

# WHO guideline reference (annual: 5 μg/m³, 24-hour: 15 μg/m³)
axes[0].axvline(x=15, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='WHO 24h guideline (15)')
axes[0].axvline(x=5, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='WHO annual (5)')

# Effect size interpretation
pm25_increase = 10  # 10 μg/m³ increase
effect_size = model2.params['pm25'] * pm25_increase
ci_lower = model2.conf_int().loc['pm25', 0] * pm25_increase
ci_upper = model2.conf_int().loc['pm25', 1] * pm25_increase

axes[1].bar(['Effect Size'], [effect_size], color='#d62728', alpha=0.7, 
            yerr=[[effect_size - ci_lower], [ci_upper - effect_size]], capsize=10)
axes[1].set_ylabel('Additional Respiratory Visits', fontsize=11)
axes[1].set_title(f'Effect of {pm25_increase} μg/m³ PM2.5 Increase', fontsize=12, fontweight='bold')
axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
axes[1].text(0, effect_size/2, f'{effect_size:.2f}\n[{ci_lower:.2f}, {ci_upper:.2f}]', 
             ha='center', va='center', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/fig5_policy_analysis.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: report/images/fig5_policy_analysis.png")

# ============================================================================
# ADDITIONAL ANALYSIS: Lag Effects
# ============================================================================

print("\n" + "="*60)
print("LAG EFFECT ANALYSIS")
print("="*60)

# Create lagged variables
df['pm25_lag1'] = df['pm25'].shift(1)
df['pm25_lag2'] = df['pm25'].shift(2)
df['pm25_lag3'] = df['pm25'].shift(3)

# Lag model (excluding first 3 rows with NaN)
df_lag = df.dropna()
X_lag = df_lag[['pm25', 'pm25_lag1', 'pm25_lag2', 'pm25_lag3', 
                'heating_degree_day', 'flu_index', 'school_holiday']]
X_lag = sm.add_constant(X_lag)
y_lag = df_lag['respiratory_visits']

model_lag = sm.OLS(y_lag, X_lag).fit()
print("\n--- Lag Model: PM2.5 Current and Lagged Effects ---")
print(model_lag.summary())

with open('outputs/model_lag_summary.txt', 'w') as f:
    f.write(model_lag.summary().as_text())

# Lag effect visualization
fig, ax = plt.subplots(figsize=(10, 6))
lags = ['Current (t)', 'Lag 1 (t-1)', 'Lag 2 (t-2)', 'Lag 3 (t-3)']
coeffs = [model_lag.params['pm25'], model_lag.params['pm25_lag1'], 
          model_lag.params['pm25_lag2'], model_lag.params['pm25_lag3']]
ci_lower = [model_lag.conf_int().loc['pm25', 0], model_lag.conf_int().loc['pm25_lag1', 0],
            model_lag.conf_int().loc['pm25_lag2', 0], model_lag.conf_int().loc['pm25_lag3', 0]]
ci_upper = [model_lag.conf_int().loc['pm25', 1], model_lag.conf_int().loc['pm25_lag1', 1],
            model_lag.conf_int().loc['pm25_lag2', 1], model_lag.conf_int().loc['pm25_lag3', 1]]

errors = [[c - l for c, l in zip(coeffs, ci_lower)], [u - c for c, u in zip(coeffs, ci_upper)]]
ax.errorbar(lags, coeffs, yerr=errors, fmt='o-', capsize=8, capthick=2, linewidth=2, markersize=10, color='#2ca02c')
ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax.set_ylabel('Coefficient (Visits per μg/m³)', fontsize=11)
ax.set_xlabel('PM2.5 Exposure Timing', fontsize=11)
ax.set_title('PM2.5 Effect on Respiratory Visits: Current vs. Lagged Exposure', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig6_lag_effects.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved: report/images/fig6_lag_effects.png")

# ============================================================================
# SUMMARY STATISTICS FOR REPORT
# ============================================================================

print("\n" + "="*60)
print("SUMMARY STATISTICS FOR REPORT")
print("="*60)

summary_stats = pd.DataFrame({
    'Variable': ['PM2.5 (μg/m³)', 'Respiratory Visits', 'Heating Degree Days', 'Flu Index', 'School Holiday (%)'],
    'Mean': [df['pm25'].mean(), df['respiratory_visits'].mean(), df['heating_degree_day'].mean(), 
             df['flu_index'].mean(), df['school_holiday'].mean()*100],
    'Std': [df['pm25'].std(), df['respiratory_visits'].std(), df['heating_degree_day'].std(), 
            df['flu_index'].std(), df['school_holiday'].std()*100],
    'Min': [df['pm25'].min(), df['respiratory_visits'].min(), df['heating_degree_day'].min(), 
            df['flu_index'].min(), df['school_holiday'].min()*100],
    'Max': [df['pm25'].max(), df['respiratory_visits'].max(), df['heating_degree_day'].max(), 
            df['flu_index'].max(), df['school_holiday'].max()*100]
})
print(summary_stats)
summary_stats.to_csv('outputs/summary_statistics.csv', index=False)

# Key findings
print("\n" + "="*60)
print("KEY FINDINGS")
print("="*60)
print(f"\n1. PM2.5-Respiratory Visit Correlation: {df['pm25'].corr(df['respiratory_visits']):.4f}")
print(f"2. Model 2 (Full) R-squared: {model2.rsquared:.4f}")
print(f"3. PM2.5 Coefficient (Model 2): {model2.params['pm25']:.4f} (p={model2.pvalues['pm25']:.4f})")
print(f"4. Effect of 10 μg/m³ PM2.5 increase: {model2.params['pm25']*10:.2f} additional visits")
print(f"5. 95% CI for 10 μg/m³ effect: [{model2.conf_int().loc['pm25', 0]*10:.2f}, {model2.conf_int().loc['pm25', 1]*10:.2f}]")

# Save key findings
with open('outputs/key_findings.txt', 'w') as f:
    f.write("KEY FINDINGS\n")
    f.write("="*60 + "\n\n")
    f.write(f"1. PM2.5-Respiratory Visit Correlation: {df['pm25'].corr(df['respiratory_visits']):.4f}\n")
    f.write(f"2. Model 2 (Full) R-squared: {model2.rsquared:.4f}\n")
    f.write(f"3. PM2.5 Coefficient (Model 2): {model2.params['pm25']:.4f} (p={model2.pvalues['pm25']:.4f})\n")
    f.write(f"4. Effect of 10 μg/m³ PM2.5 increase: {model2.params['pm25']*10:.2f} additional visits\n")
    f.write(f"5. 95% CI for 10 μg/m³ effect: [{model2.conf_int().loc['pm25', 0]*10:.2f}, {model2.conf_int().loc['pm25', 1]*10:.2f}]\n")
    f.write(f"6. Flu Index Coefficient: {model2.params['flu_index']:.2f} (p={model2.pvalues['flu_index']:.4f})\n")
    f.write(f"7. Heating Degree Day Coefficient: {model2.params['heating_degree_day']:.2f} (p={model2.pvalues['heating_degree_day']:.4f})\n")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
