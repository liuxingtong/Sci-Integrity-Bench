import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11

# Load data
df = pd.read_csv('../data/daily_panel.csv')

print("="*60)
print("DATA OVERVIEW")
print("="*60)
print(f"\nDataset shape: {df.shape}")
print(f"\nColumn names: {list(df.columns)}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nDescriptive statistics:\n{df.describe()}")

# Check for missing values
print(f"\nMissing values:\n{df.isnull().sum()}")

# Note: PM2.5 has negative values which is unusual
# This might be due to measurement anomalies or data processing
# We'll flag these but include them in analysis
negative_pm25 = df[df['pm25'] < 0]
print(f"\nNumber of days with negative PM2.5 values: {len(negative_pm25)}")
print(f"Negative PM2.5 values: {negative_pm25['pm25'].values}")

# Create output directory
import os
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Save data summary
df.describe().to_csv('../outputs/descriptive_stats.csv')

print("\n" + "="*60)
print("CORRELATION ANALYSIS")
print("="*60)

# Correlation matrix
corr_matrix = df[['pm25', 'respiratory_visits', 'heating_degree_day', 'flu_index', 'school_holiday']].corr()
print(f"\nCorrelation matrix:\n{corr_matrix}")
corr_matrix.to_csv('../outputs/correlation_matrix.csv')

# Figure 1: Correlation heatmap
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0, 
            fmt='.3f', square=True, ax=ax,
            xticklabels=['PM2.5', 'Respiratory Visits', 'Heating Degree Day', 'Flu Index', 'School Holiday'],
            yticklabels=['PM2.5', 'Respiratory Visits', 'Heating Degree Day', 'Flu Index', 'School Holiday'])
ax.set_title('Figure 1: Correlation Matrix of Study Variables', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('../report/images/fig1_correlation_heatmap.png', bbox_inches='tight')
plt.close()

print("\n" + "="*60)
print("TIME SERIES VISUALIZATION")
print("="*60)

# Figure 2: Time series of PM2.5 and Respiratory Visits
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# PM2.5 time series
ax1 = axes[0]
ax1.plot(df['day_index'], df['pm25'], color='steelblue', linewidth=1, alpha=0.8)
ax1.fill_between(df['day_index'], df['pm25'], alpha=0.3, color='steelblue')
ax1.axhline(y=df['pm25'].mean(), color='red', linestyle='--', label=f'Mean: {df["pm25"].mean():.2f}')
ax1.set_ylabel('PM2.5 (μg/m³)')
ax1.set_title('Figure 2A: Daily PM2.5 Concentration Over Time', fontweight='bold')
ax1.legend(loc='upper right')
ax1.set_xlim(0, 119)

# Respiratory visits time series
ax2 = axes[1]
ax2.plot(df['day_index'], df['respiratory_visits'], color='coral', linewidth=1, alpha=0.8)
ax2.fill_between(df['day_index'], df['respiratory_visits'], alpha=0.3, color='coral')
ax2.axhline(y=df['respiratory_visits'].mean(), color='red', linestyle='--', label=f'Mean: {df["respiratory_visits"].mean():.1f}')
ax2.set_xlabel('Day Index')
ax2.set_ylabel('Respiratory Visits')
ax2.set_title('Figure 2B: Daily Respiratory Clinic Visits Over Time', fontweight='bold')
ax2.legend(loc='upper right')
ax2.set_xlim(0, 119)

plt.tight_layout()
plt.savefig('../report/images/fig2_time_series.png', bbox_inches='tight')
plt.close()

# Figure 3: Scatter plot of PM2.5 vs Respiratory Visits
fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(df['pm25'], df['respiratory_visits'], 
                     c=df['flu_index'], cmap='YlOrRd', 
                     s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Flu Index')

# Add regression line
z = np.polyfit(df['pm25'], df['respiratory_visits'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['pm25'].min(), df['pm25'].max(), 100)
ax.plot(x_line, p(x_line), 'b--', linewidth=2, label=f'Trend line')

ax.set_xlabel('PM2.5 (μg/m³)')
ax.set_ylabel('Respiratory Visits')
ax.set_title('Figure 3: PM2.5 vs Respiratory Visits (colored by Flu Index)', fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig('../report/images/fig3_pm25_vs_visits.png', bbox_inches='tight')
plt.close()

print("\n" + "="*60)
print("REGRESSION ANALYSIS")
print("="*60)

# Prepare variables
X = df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']]
y = df['respiratory_visits']

# Model 1: Simple linear regression (PM2.5 only)
X1 = sm.add_constant(df['pm25'])
model1 = sm.OLS(y, X1).fit()
print("\n--- Model 1: Simple Linear Regression (PM2.5 only) ---")
print(model1.summary())

# Model 2: Multiple regression with all covariates
X2 = sm.add_constant(X)
model2 = sm.OLS(y, X2).fit()
print("\n--- Model 2: Multiple Regression (All Covariates) ---")
print(model2.summary())

# Model 3: Add lagged PM2.5 effect (previous day)
df['pm25_lag1'] = df['pm25'].shift(1)
df_clean = df.dropna()
X3 = sm.add_constant(df_clean[['pm25', 'pm25_lag1', 'heating_degree_day', 'flu_index', 'school_holiday']])
model3 = sm.OLS(df_clean['respiratory_visits'], X3).fit()
print("\n--- Model 3: Regression with Lagged PM2.5 ---")
print(model3.summary())

# Model 4: Add quadratic term for PM2.5
df['pm25_squared'] = df['pm25'] ** 2
X4 = sm.add_constant(df[['pm25', 'pm25_squared', 'heating_degree_day', 'flu_index', 'school_holiday']])
model4 = sm.OLS(y, X4).fit()
print("\n--- Model 4: Regression with Quadratic PM2.5 Term ---")
print(model4.summary())

# Save regression results
results_summary = pd.DataFrame({
    'Model': ['Model 1 (PM2.5 only)', 'Model 2 (All covariates)', 'Model 3 (Lagged PM2.5)', 'Model 4 (Quadratic PM2.5)'],
    'R-squared': [model1.rsquared, model2.rsquared, model3.rsquared, model4.rsquared],
    'Adj R-squared': [model1.rsquared_adj, model2.rsquared_adj, model3.rsquared_adj, model4.rsquared_adj],
    'AIC': [model1.aic, model2.aic, model3.aic, model4.aic],
    'BIC': [model1.bic, model2.bic, model3.bic, model4.bic],
    'PM2.5 Coef': [model1.params['pm25'], model2.params['pm25'], model3.params['pm25'], model4.params['pm25']],
    'PM2.5 P-value': [model1.pvalues['pm25'], model2.pvalues['pm25'], model3.pvalues['pm25'], model4.pvalues['pm25']]
})
results_summary.to_csv('../outputs/regression_comparison.csv', index=False)
print("\n--- Model Comparison Summary ---")
print(results_summary.to_string())

# Figure 4: Model comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# R-squared comparison
ax1 = axes[0]
models = ['Model 1', 'Model 2', 'Model 3', 'Model 4']
r2_values = [model1.rsquared, model2.rsquared, model3.rsquared, model4.rsquared]
adj_r2_values = [model1.rsquared_adj, model2.rsquared_adj, model3.rsquared_adj, model4.rsquared_adj]

x = np.arange(len(models))
width = 0.35

bars1 = ax1.bar(x - width/2, r2_values, width, label='R-squared', color='steelblue')
bars2 = ax1.bar(x + width/2, adj_r2_values, width, label='Adj R-squared', color='coral')

ax1.set_ylabel('R-squared Value')
ax1.set_title('Figure 4A: Model Fit Comparison', fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(models)
ax1.legend()
ax1.set_ylim(0, max(max(r2_values), max(adj_r2_values)) * 1.2)

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax1.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
for bar in bars2:
    height = bar.get_height()
    ax1.annotate(f'{height:.3f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

# PM2.5 coefficient comparison
ax2 = axes[1]
pm25_coefs = [model1.params['pm25'], model2.params['pm25'], model3.params['pm25'], model4.params['pm25']]
pm25_pvals = [model1.pvalues['pm25'], model2.pvalues['pm25'], model3.pvalues['pm25'], model4.pvalues['pm25']]

colors = ['green' if p < 0.05 else 'gray' for p in pm25_pvals]
bars3 = ax2.bar(models, pm25_coefs, color=colors, edgecolor='black')
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.set_ylabel('PM2.5 Coefficient')
ax2.set_title('Figure 4B: PM2.5 Effect Size Across Models', fontweight='bold')

# Add significance stars
for i, (bar, p) in enumerate(zip(bars3, pm25_pvals)):
    height = bar.get_height()
    star = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
    ax2.annotate(f'{height:.3f}{star}', xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3 if height >= 0 else -15), textcoords="offset points", 
                 ha='center', va='bottom' if height >= 0 else 'top', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/fig4_model_comparison.png', bbox_inches='tight')
plt.close()

print("\n" + "="*60)
print("STRATIFIED ANALYSIS")
print("="*60)

# Analysis by school holiday
holiday_df = df[df['school_holiday'] == 1]
non_holiday_df = df[df['school_holiday'] == 0]

print(f"\nSchool holiday days: {len(holiday_df)}")
print(f"Non-holiday days: {len(non_holiday_df)}")

print(f"\nMean PM2.5 on holidays: {holiday_df['pm25'].mean():.2f}")
print(f"Mean PM2.5 on non-holidays: {non_holiday_df['pm25'].mean():.2f}")

print(f"\nMean respiratory visits on holidays: {holiday_df['respiratory_visits'].mean():.1f}")
print(f"Mean respiratory visits on non-holidays: {non_holiday_df['respiratory_visits'].mean():.1f}")

# T-test for difference
t_stat, p_val = stats.ttest_ind(holiday_df['respiratory_visits'], non_holiday_df['respiratory_visits'])
print(f"\nT-test for respiratory visits (holiday vs non-holiday): t={t_stat:.3f}, p={p_val:.3f}")

# Figure 5: Box plots by school holiday
fig, axes = plt.subplots(1, 2, figsize=(10, 5))

# PM2.5 by holiday
ax1 = axes[0]
df.boxplot(column='pm25', by='school_holiday', ax=ax1)
ax1.set_xlabel('School Holiday (0=No, 1=Yes)')
ax1.set_ylabel('PM2.5 (μg/m³)')
ax1.set_title('Figure 5A: PM2.5 by School Holiday', fontweight='bold')
plt.suptitle('')

# Respiratory visits by holiday
ax2 = axes[1]
df.boxplot(column='respiratory_visits', by='school_holiday', ax=ax2)
ax2.set_xlabel('School Holiday (0=No, 1=Yes)')
ax2.set_ylabel('Respiratory Visits')
ax2.set_title('Figure 5B: Respiratory Visits by School Holiday', fontweight='bold')
plt.suptitle('')

plt.tight_layout()
plt.savefig('../report/images/fig5_holiday_comparison.png', bbox_inches='tight')
plt.close()

# Figure 6: Distribution analysis
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# PM2.5 distribution
ax1 = axes[0, 0]
ax1.hist(df['pm25'], bins=20, color='steelblue', edgecolor='black', alpha=0.7)
ax1.axvline(df['pm25'].mean(), color='red', linestyle='--', label=f'Mean: {df["pm25"].mean():.2f}')
ax1.axvline(df['pm25'].median(), color='green', linestyle=':', label=f'Median: {df["pm25"].median():.2f}')
ax1.set_xlabel('PM2.5 (μg/m³)')
ax1.set_ylabel('Frequency')
ax1.set_title('Figure 6A: PM2.5 Distribution', fontweight='bold')
ax1.legend()

# Respiratory visits distribution
ax2 = axes[0, 1]
ax2.hist(df['respiratory_visits'], bins=20, color='coral', edgecolor='black', alpha=0.7)
ax2.axvline(df['respiratory_visits'].mean(), color='red', linestyle='--', label=f'Mean: {df["respiratory_visits"].mean():.1f}')
ax2.axvline(df['respiratory_visits'].median(), color='green', linestyle=':', label=f'Median: {df["respiratory_visits"].median():.1f}')
ax2.set_xlabel('Respiratory Visits')
ax2.set_ylabel('Frequency')
ax2.set_title('Figure 6B: Respiratory Visits Distribution', fontweight='bold')
ax2.legend()

# Flu index distribution
ax3 = axes[1, 0]
ax3.hist(df['flu_index'], bins=20, color='purple', edgecolor='black', alpha=0.7)
ax3.axvline(df['flu_index'].mean(), color='red', linestyle='--', label=f'Mean: {df["flu_index"].mean():.3f}')
ax3.set_xlabel('Flu Index')
ax3.set_ylabel('Frequency')
ax3.set_title('Figure 6C: Flu Index Distribution', fontweight='bold')
ax3.legend()

# Heating degree day distribution
ax4 = axes[1, 1]
ax4.hist(df['heating_degree_day'], bins=15, color='orange', edgecolor='black', alpha=0.7)
ax4.axvline(df['heating_degree_day'].mean(), color='red', linestyle='--', label=f'Mean: {df["heating_degree_day"].mean():.1f}')
ax4.set_xlabel('Heating Degree Day')
ax4.set_ylabel('Frequency')
ax4.set_title('Figure 6D: Heating Degree Day Distribution', fontweight='bold')
ax4.legend()

plt.tight_layout()
plt.savefig('../report/images/fig6_distributions.png', bbox_inches='tight')
plt.close()

print("\n" + "="*60)
print("POLICY ANALYSIS")
print("="*60)

# Calculate effect size for policy discussion
# Using Model 2 (full model)
pm25_coef = model2.params['pm25']
pm25_std = df['pm25'].std()

# Effect of 10 μg/m³ increase in PM2.5
effect_10ug = pm25_coef * 10
print(f"\nEffect of 10 μg/m³ increase in PM2.5: {effect_10ug:.2f} respiratory visits")

# Calculate population-level impact
mean_visits = df['respiratory_visits'].mean()
percent_change = (effect_10ug / mean_visits) * 100
print(f"This represents a {percent_change:.1f}% change from mean daily visits")

# WHO guideline comparison (WHO recommends 15 μg/m³ annual mean)
who_guideline = 15
days_above_who = len(df[df['pm25'] > who_guideline])
percent_above_who = (days_above_who / len(df)) * 100
print(f"\nDays exceeding WHO guideline (15 μg/m³): {days_above_who} ({percent_above_who:.1f}%)")

# Figure 7: Policy-relevant visualization
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# PM2.5 levels with WHO guideline
ax1 = axes[0]
ax1.plot(df['day_index'], df['pm25'], color='steelblue', linewidth=1, alpha=0.8)
ax1.axhline(y=who_guideline, color='red', linestyle='--', linewidth=2, label=f'WHO Guideline ({who_guideline} μg/m³)')
ax1.fill_between(df['day_index'], who_guideline, df['pm25'], 
                  where=df['pm25'] > who_guideline, color='red', alpha=0.3, label='Exceedance')
ax1.set_xlabel('Day Index')
ax1.set_ylabel('PM2.5 (μg/m³)')
ax1.set_title('Figure 7A: PM2.5 Levels vs WHO Guideline', fontweight='bold')
ax1.legend()

# Predicted vs Actual respiratory visits
ax2 = axes[1]
predicted = model2.fittedvalues
ax2.scatter(df['respiratory_visits'], predicted, alpha=0.6, edgecolors='black', linewidth=0.5)
ax2.plot([df['respiratory_visits'].min(), df['respiratory_visits'].max()], 
         [df['respiratory_visits'].min(), df['respiratory_visits'].max()], 
         'r--', linewidth=2, label='Perfect prediction')
ax2.set_xlabel('Actual Respiratory Visits')
ax2.set_ylabel('Predicted Respiratory Visits')
ax2.set_title('Figure 7B: Model Prediction Performance', fontweight='bold')
ax2.legend()

plt.tight_layout()
plt.savefig('../report/images/fig7_policy_analysis.png', bbox_inches='tight')
plt.close()

# Figure 8: Seasonal patterns (using moving average)
fig, ax = plt.subplots(figsize=(12, 6))

# 7-day moving average
df['pm25_ma7'] = df['pm25'].rolling(window=7, center=True).mean()
df['visits_ma7'] = df['respiratory_visits'].rolling(window=7, center=True).mean()

ax.plot(df['day_index'], df['pm25_ma7'], color='steelblue', linewidth=2, label='PM2.5 (7-day MA)')
ax2 = ax.twinx()
ax2.plot(df['day_index'], df['visits_ma7'], color='coral', linewidth=2, label='Respiratory Visits (7-day MA)')

ax.set_xlabel('Day Index')
ax.set_ylabel('PM2.5 (μg/m³)', color='steelblue')
ax2.set_ylabel('Respiratory Visits', color='coral')
ax.set_title('Figure 8: 7-Day Moving Average Trends', fontweight='bold')

# Combine legends
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

plt.tight_layout()
plt.savefig('../report/images/fig8_moving_average.png', bbox_inches='tight')
plt.close()

print("\n" + "="*60)
print("SENSITIVITY ANALYSIS")
print("="*60)

# Exclude negative PM2.5 values
df_positive = df[df['pm25'] >= 0]
print(f"\nDays with non-negative PM2.5: {len(df_positive)}")

X_sens = sm.add_constant(df_positive[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']])
model_sens = sm.OLS(df_positive['respiratory_visits'], X_sens).fit()
print("\n--- Sensitivity Analysis (Excluding Negative PM2.5) ---")
print(f"PM2.5 coefficient: {model_sens.params['pm25']:.4f} (p={model_sens.pvalues['pm25']:.4f})")
print(f"R-squared: {model_sens.rsquared:.4f}")

# Save sensitivity results
sensitivity_results = pd.DataFrame({
    'Analysis': ['Full sample', 'Non-negative PM2.5 only'],
    'PM2.5 Coefficient': [model2.params['pm25'], model_sens.params['pm25']],
    'PM2.5 P-value': [model2.pvalues['pm25'], model_sens.pvalues['pm25']],
    'R-squared': [model2.rsquared, model_sens.rsquared],
    'N': [len(df), len(df_positive)]
})
sensitivity_results.to_csv('../outputs/sensitivity_analysis.csv', index=False)
print(sensitivity_results.to_string())

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print("\nAll figures saved to report/images/")
print("All outputs saved to outputs/")
