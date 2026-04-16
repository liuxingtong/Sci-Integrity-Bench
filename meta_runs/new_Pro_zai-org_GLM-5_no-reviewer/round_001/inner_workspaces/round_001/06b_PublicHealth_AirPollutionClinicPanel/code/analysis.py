import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.gam.api import GLMGam, BSplines
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
import os
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
df = pd.read_csv('../data/daily_panel.csv')
print("Data Shape:", df.shape)
print("\nData Summary:")
print(df.describe())

# Save data summary
df.describe().to_csv('../outputs/data_summary.csv')

# ============================================
# 1. Data Overview and Visualization
# ============================================

# Figure 1: Time series of PM2.5 and Respiratory Visits
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

axes[0].plot(df['day_index'], df['pm25'], color='#e74c3c', linewidth=1.5, alpha=0.8)
axes[0].fill_between(df['day_index'], df['pm25'], alpha=0.3, color='#e74c3c')
axes[0].set_ylabel('PM2.5 (μg/m³)', fontsize=12)
axes[0].set_title('Daily PM2.5 Concentration Over Time', fontsize=14, fontweight='bold')
axes[0].axhline(y=12, color='red', linestyle='--', label='WHO Annual Guideline (12 μg/m³)', alpha=0.7)
axes[0].axhline(y=35, color='darkred', linestyle='--', label='WHO 24-hour Guideline (35 μg/m³)', alpha=0.7)
axes[0].legend(loc='upper right', fontsize=9)

axes[1].plot(df['day_index'], df['respiratory_visits'], color='#3498db', linewidth=1.5, alpha=0.8)
axes[1].fill_between(df['day_index'], df['respiratory_visits'], alpha=0.3, color='#3498db')
axes[1].set_ylabel('Respiratory Visits', fontsize=12)
axes[1].set_xlabel('Day Index', fontsize=12)
axes[1].set_title('Daily Respiratory Clinic Visits Over Time', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/fig1_time_series.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 1 saved: Time series")

# Figure 2: Distribution plots
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# PM2.5 distribution
axes[0, 0].hist(df['pm25'], bins=25, color='#e74c3c', edgecolor='white', alpha=0.7)
axes[0, 0].axvline(df['pm25'].mean(), color='black', linestyle='--', label=f'Mean: {df["pm25"].mean():.1f}')
axes[0, 0].set_xlabel('PM2.5 (μg/m³)', fontsize=11)
axes[0, 0].set_ylabel('Frequency', fontsize=11)
axes[0, 0].set_title('PM2.5 Distribution', fontsize=12, fontweight='bold')
axes[0, 0].legend()

# Respiratory visits distribution
axes[0, 1].hist(df['respiratory_visits'], bins=25, color='#3498db', edgecolor='white', alpha=0.7)
axes[0, 1].axvline(df['respiratory_visits'].mean(), color='black', linestyle='--', label=f'Mean: {df["respiratory_visits"].mean():.1f}')
axes[0, 1].set_xlabel('Respiratory Visits', fontsize=11)
axes[0, 1].set_ylabel('Frequency', fontsize=11)
axes[0, 1].set_title('Respiratory Visits Distribution', fontsize=12, fontweight='bold')
axes[0, 1].legend()

# Flu index distribution
axes[0, 2].hist(df['flu_index'], bins=25, color='#2ecc71', edgecolor='white', alpha=0.7)
axes[0, 2].axvline(df['flu_index'].mean(), color='black', linestyle='--', label=f'Mean: {df["flu_index"].mean():.2f}')
axes[0, 2].set_xlabel('Flu Index', fontsize=11)
axes[0, 2].set_ylabel('Frequency', fontsize=11)
axes[0, 2].set_title('Flu Index Distribution', fontsize=12, fontweight='bold')
axes[0, 2].legend()

# Heating degree day distribution
axes[1, 0].hist(df['heating_degree_day'], bins=15, color='#9b59b6', edgecolor='white', alpha=0.7)
axes[1, 0].axvline(df['heating_degree_day'].mean(), color='black', linestyle='--', label=f'Mean: {df["heating_degree_day"].mean():.1f}')
axes[1, 0].set_xlabel('Heating Degree Day', fontsize=11)
axes[1, 0].set_ylabel('Frequency', fontsize=11)
axes[1, 0].set_title('Heating Degree Day Distribution', fontsize=12, fontweight='bold')
axes[1, 0].legend()

# School holiday counts
holiday_counts = df['school_holiday'].value_counts()
axes[1, 1].bar(['Non-Holiday', 'Holiday'], [holiday_counts.get(0, 0), holiday_counts.get(1, 0)], 
              color=['#3498db', '#e74c3c'], edgecolor='white')
axes[1, 1].set_ylabel('Count', fontsize=11)
axes[1, 1].set_title('School Holiday Distribution', fontsize=12, fontweight='bold')
for i, v in enumerate([holiday_counts.get(0, 0), holiday_counts.get(1, 0)]):
    axes[1, 1].text(i, v + 1, str(v), ha='center', fontsize=11)

# Correlation heatmap
corr_matrix = df[['pm25', 'respiratory_visits', 'heating_degree_day', 'flu_index']].corr()
sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0, ax=axes[1, 2], 
            fmt='.3f', square=True, linewidths=0.5)
axes[1, 2].set_title('Correlation Matrix', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/fig2_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: Distributions")

# ============================================
# 2. Correlation Analysis
# ============================================

# Scatter plot: PM2.5 vs Respiratory Visits
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Simple scatter
axes[0].scatter(df['pm25'], df['respiratory_visits'], alpha=0.6, c='#3498db', edgecolor='white', s=60)
z = np.polyfit(df['pm25'], df['respiratory_visits'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['pm25'].min(), df['pm25'].max(), 100)
axes[0].plot(x_line, p(x_line), 'r-', linewidth=2, label=f'Trend line')
axes[0].set_xlabel('PM2.5 (μg/m³)', fontsize=12)
axes[0].set_ylabel('Respiratory Visits', fontsize=12)
axes[0].set_title('PM2.5 vs Respiratory Visits', fontsize=13, fontweight='bold')

# Calculate correlation
r, p_val = stats.pearsonr(df['pm25'], df['respiratory_visits'])
axes[0].text(0.05, 0.95, f'r = {r:.3f}\np = {p_val:.4f}', transform=axes[0].transAxes, 
             fontsize=11, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
axes[0].legend()

# Scatter colored by flu index
scatter = axes[1].scatter(df['pm25'], df['respiratory_visits'], c=df['flu_index'], 
                          cmap='YlOrRd', alpha=0.7, edgecolor='white', s=60)
plt.colorbar(scatter, ax=axes[1], label='Flu Index')
axes[1].set_xlabel('PM2.5 (μg/m³)', fontsize=12)
axes[1].set_ylabel('Respiratory Visits', fontsize=12)
axes[1].set_title('PM2.5 vs Respiratory Visits (colored by Flu Index)', fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/fig3_scatter_correlation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved: Scatter correlation")

# ============================================
# 3. Regression Analysis
# ============================================

# Prepare data for regression
X = df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']]
X = sm.add_constant(X)
y = df['respiratory_visits']

# OLS Regression
model_ols = sm.OLS(y, X).fit()
print("\n" + "="*60)
print("OLS REGRESSION RESULTS")
print("="*60)
print(model_ols.summary())

# Save regression results
with open('../outputs/regression_results.txt', 'w') as f:
    f.write(str(model_ols.summary()))

# Extract key results for report
results_dict = {
    'Variable': model_ols.params.index,
    'Coefficient': model_ols.params.values,
    'Std Error': model_ols.bse.values,
    't-value': model_ols.tvalues.values,
    'p-value': model_ols.pvalues.values,
    'CI_lower': model_ols.conf_int()[0].values,
    'CI_upper': model_ols.conf_int()[1].values
}
results_df = pd.DataFrame(results_dict)
results_df.to_csv('../outputs/regression_coefficients.csv', index=False)

# Figure 4: Coefficient plot
fig, ax = plt.subplots(figsize=(10, 6))

# Exclude constant for cleaner plot
coef_vars = ['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']
coefs = [model_ols.params[var] for var in coef_vars]
errors = [1.96 * model_ols.bse[var] for var in coef_vars]

colors = ['#e74c3c' if model_ols.pvalues[var] < 0.05 else '#95a5a6' for var in coef_vars]

y_pos = range(len(coef_vars))
ax.barh(y_pos, coefs, xerr=errors, align='center', alpha=0.7, color=colors, edgecolor='black')
ax.set_yticks(y_pos)
ax.set_yticklabels(['PM2.5', 'Heating Degree Day', 'Flu Index', 'School Holiday'])
ax.axvline(0, color='black', linewidth=1)
ax.set_xlabel('Coefficient (Effect on Respiratory Visits)', fontsize=12)
ax.set_title('Regression Coefficients with 95% CI\n(Red = Significant at p<0.05)', fontsize=13, fontweight='bold')

# Add coefficient values
for i, (coef, err) in enumerate(zip(coefs, errors)):
    ax.text(coef + 2 if coef > 0 else coef - 15, i, f'{coef:.2f}', va='center', fontsize=10)

plt.tight_layout()
plt.savefig('../report/images/fig4_coefficient_plot.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved: Coefficient plot")

# ============================================
# 4. Lagged Effects Analysis
# ============================================

# Create lagged PM2.5 variables
df['pm25_lag1'] = df['pm25'].shift(1)
df['pm25_lag2'] = df['pm25'].shift(2)
df['pm25_lag3'] = df['pm25'].shift(3)
df['pm25_lag7'] = df['pm25'].shift(7)
df['pm25_ma3'] = df['pm25'].rolling(window=3).mean()
df['pm25_ma7'] = df['pm25'].rolling(window=7).mean()

# Lagged regression
df_lag = df.dropna()
X_lag = df_lag[['pm25', 'pm25_lag1', 'pm25_lag2', 'pm25_lag3', 'heating_degree_day', 'flu_index', 'school_holiday']]
X_lag = sm.add_constant(X_lag)
y_lag = df_lag['respiratory_visits']

model_lag = sm.OLS(y_lag, X_lag).fit()
print("\n" + "="*60)
print("LAGGED REGRESSION RESULTS")
print("="*60)
print(model_lag.summary())

# Figure 5: Lagged effects
fig, ax = plt.subplots(figsize=(10, 6))

lag_vars = ['pm25', 'pm25_lag1', 'pm25_lag2', 'pm25_lag3']
lag_labels = ['Day 0', 'Day 1', 'Day 2', 'Day 3']
lag_coefs = [model_lag.params[var] for var in lag_vars]
lag_errors = [1.96 * model_lag.bse[var] for var in lag_vars]
lag_pvals = [model_lag.pvalues[var] for var in lag_vars]

colors = ['#e74c3c' if p < 0.05 else '#95a5a6' for p in lag_pvals]

ax.bar(lag_labels, lag_coefs, yerr=lag_errors, color=colors, alpha=0.7, edgecolor='black', capsize=5)
ax.axhline(0, color='black', linewidth=1)
ax.set_xlabel('Lag Days', fontsize=12)
ax.set_ylabel('Coefficient (Effect on Respiratory Visits)', fontsize=12)
ax.set_title('PM2.5 Lagged Effects on Respiratory Visits\n(Red = Significant at p<0.05)', fontsize=13, fontweight='bold')

for i, (coef, p) in enumerate(zip(lag_coefs, lag_pvals)):
    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
    ax.text(i, coef + 1.5, f'{coef:.2f}{sig}', ha='center', fontsize=10)

plt.tight_layout()
plt.savefig('../report/images/fig5_lagged_effects.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 5 saved: Lagged effects")

# ============================================
# 5. Stratified Analysis
# ============================================

# Analysis by season (heating vs non-heating)
df['heating_season'] = (df['heating_degree_day'] >= df['heating_degree_day'].median()).astype(int)

# Figure 6: PM2.5 effect by heating season
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Heating season
for i, (season, label) in enumerate([(1, 'High Heating Season'), (0, 'Low Heating Season')]):
    subset = df[df['heating_season'] == season]
    axes[i].scatter(subset['pm25'], subset['respiratory_visits'], alpha=0.6, 
                   c='#e74c3c' if season == 1 else '#3498db', edgecolor='white', s=60)
    
    # Fit line
    z = np.polyfit(subset['pm25'], subset['respiratory_visits'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(subset['pm25'].min(), subset['pm25'].max(), 100)
    axes[i].plot(x_line, p(x_line), 'k-', linewidth=2)
    
    r, p_val = stats.pearsonr(subset['pm25'], subset['respiratory_visits'])
    axes[i].set_xlabel('PM2.5 (μg/m³)', fontsize=12)
    axes[i].set_ylabel('Respiratory Visits', fontsize=12)
    axes[i].set_title(f'{label}\nr = {r:.3f}, p = {p_val:.4f}', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/fig6_stratified_heating.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 6 saved: Stratified by heating season")

# ============================================
# 6. School Holiday Effect
# ============================================

# Figure 7: Holiday comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Box plot
holiday_data = [df[df['school_holiday'] == 0]['respiratory_visits'], 
                df[df['school_holiday'] == 1]['respiratory_visits']]
bp = axes[0].boxplot(holiday_data, labels=['Non-Holiday', 'Holiday'], patch_artist=True)
bp['boxes'][0].set_facecolor('#3498db')
bp['boxes'][1].set_facecolor('#e74c3c')
axes[0].set_ylabel('Respiratory Visits', fontsize=12)
axes[0].set_title('Respiratory Visits: Holiday vs Non-Holiday', fontsize=12, fontweight='bold')

# T-test
t_stat, t_pval = stats.ttest_ind(df[df['school_holiday'] == 0]['respiratory_visits'],
                                  df[df['school_holiday'] == 1]['respiratory_visits'])
axes[0].text(0.5, 0.95, f't = {t_stat:.2f}, p = {t_pval:.4f}', transform=axes[0].transAxes,
             fontsize=11, ha='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# PM2.5 by holiday
pm25_holiday = [df[df['school_holiday'] == 0]['pm25'], 
                df[df['school_holiday'] == 1]['pm25']]
bp2 = axes[1].boxplot(pm25_holiday, labels=['Non-Holiday', 'Holiday'], patch_artist=True)
bp2['boxes'][0].set_facecolor('#3498db')
bp2['boxes'][1].set_facecolor('#e74c3c')
axes[1].set_ylabel('PM2.5 (μg/m³)', fontsize=12)
axes[1].set_title('PM2.5 Levels: Holiday vs Non-Holiday', fontsize=12, fontweight='bold')

t_stat2, t_pval2 = stats.ttest_ind(df[df['school_holiday'] == 0]['pm25'],
                                   df[df['school_holiday'] == 1]['pm25'])
axes[1].text(0.5, 0.95, f't = {t_stat2:.2f}, p = {t_pval2:.4f}', transform=axes[1].transAxes,
             fontsize=11, ha='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('../report/images/fig7_holiday_effect.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 7 saved: Holiday effect")

# ============================================
# 7. Dose-Response Analysis
# ============================================

# Create PM2.5 categories
df['pm25_category'] = pd.cut(df['pm25'], bins=[-1, 5, 10, 15, 20, 100], 
                              labels=['Very Low (0-5)', 'Low (5-10)', 'Medium (10-15)', 
                                     'High (15-20)', 'Very High (>20)'])

# Figure 8: Dose-response
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Mean visits by PM2.5 category
pm25_means = df.groupby('pm25_category')['respiratory_visits'].agg(['mean', 'std', 'count']).reset_index()
axes[0].bar(range(len(pm25_means)), pm25_means['mean'], yerr=pm25_means['std']/np.sqrt(pm25_means['count']),
           color=['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#8e44ad'], alpha=0.7, edgecolor='black', capsize=5)
axes[0].set_xticks(range(len(pm25_means)))
axes[0].set_xticklabels(pm25_means['pm25_category'], rotation=15, ha='right')
axes[0].set_ylabel('Mean Respiratory Visits', fontsize=12)
axes[0].set_xlabel('PM2.5 Category', fontsize=12)
axes[0].set_title('Mean Respiratory Visits by PM2.5 Level', fontsize=12, fontweight='bold')

# Trend with confidence interval
from scipy.stats import binned_statistic
bin_means, bin_edges, _ = binned_statistic(df['pm25'], df['respiratory_visits'], statistic='mean', bins=10)
bin_std, _, _ = binned_statistic(df['pm25'], df['respiratory_visits'], statistic='std', bins=10)
bin_count, _, _ = binned_statistic(df['pm25'], df['respiratory_visits'], statistic='count', bins=10)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

axes[1].errorbar(bin_centers, bin_means, yerr=bin_std/np.sqrt(bin_count), fmt='o-', 
                color='#e74c3c', capsize=5, linewidth=2, markersize=8)
axes[1].set_xlabel('PM2.5 (μg/m³)', fontsize=12)
axes[1].set_ylabel('Mean Respiratory Visits', fontsize=12)
axes[1].set_title('Dose-Response Relationship', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/fig8_dose_response.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 8 saved: Dose-response")

# ============================================
# 8. Model Diagnostics
# ============================================

# Figure 9: Residual diagnostics
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Residuals vs Fitted
fitted = model_ols.fittedvalues
residuals = model_ols.resid
axes[0, 0].scatter(fitted, residuals, alpha=0.6, c='#3498db', edgecolor='white')
axes[0, 0].axhline(0, color='red', linestyle='--', linewidth=2)
axes[0, 0].set_xlabel('Fitted Values', fontsize=11)
axes[0, 0].set_ylabel('Residuals', fontsize=11)
axes[0, 0].set_title('Residuals vs Fitted', fontsize=12, fontweight='bold')

# Q-Q plot
stats.probplot(residuals, dist="norm", plot=axes[0, 1])
axes[0, 1].set_title('Normal Q-Q Plot', fontsize=12, fontweight='bold')

# Histogram of residuals
axes[1, 0].hist(residuals, bins=20, color='#3498db', edgecolor='white', alpha=0.7, density=True)
x_range = np.linspace(residuals.min(), residuals.max(), 100)
axes[1, 0].plot(x_range, stats.norm.pdf(x_range, residuals.mean(), residuals.std()), 'r-', linewidth=2)
axes[1, 0].set_xlabel('Residuals', fontsize=11)
axes[1, 0].set_ylabel('Density', fontsize=11)
axes[1, 0].set_title('Residual Distribution', fontsize=12, fontweight='bold')

# Scale-Location plot
standardized_residuals = residuals / residuals.std()
axes[1, 1].scatter(fitted, np.sqrt(np.abs(standardized_residuals)), alpha=0.6, c='#3498db', edgecolor='white')
axes[1, 1].set_xlabel('Fitted Values', fontsize=11)
axes[1, 1].set_ylabel('√|Standardized Residuals|', fontsize=11)
axes[1, 1].set_title('Scale-Location Plot', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/fig9_diagnostics.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 9 saved: Model diagnostics")

# ============================================
# 9. Policy-Relevant Statistics
# ============================================

# Calculate excess visits attributable to PM2.5
mean_pm25 = df['pm25'].mean()
baseline_pm25 = 12  # WHO annual guideline
pm25_effect = model_ols.params['pm25']

excess_visits = pm25_effect * (mean_pm25 - baseline_pm25)
percent_increase = (excess_visits / df['respiratory_visits'].mean()) * 100

print("\n" + "="*60)
print("POLICY-RELEVANT STATISTICS")
print("="*60)
print(f"Mean PM2.5: {mean_pm25:.2f} μg/m³")
print(f"WHO Guideline: {baseline_pm25} μg/m³")
print(f"PM2.5 coefficient: {pm25_effect:.3f} visits per μg/m³")
print(f"Excess visits (vs WHO guideline): {excess_visits:.2f} per day")
print(f"Percent increase: {percent_increase:.1f}%")

# Save policy stats
policy_stats = {
    'Metric': ['Mean PM2.5 (μg/m³)', 'WHO Guideline (μg/m³)', 'PM2.5 Effect (visits/μg/m³)', 
               'Excess Daily Visits', 'Percent Increase (%)', 'R-squared', 'Sample Size'],
    'Value': [mean_pm25, baseline_pm25, pm25_effect, excess_visits, percent_increase, 
              model_ols.rsquared, len(df)]
}
policy_df = pd.DataFrame(policy_stats)
policy_df.to_csv('../outputs/policy_statistics.csv', index=False)

# ============================================
# 10. Sensitivity Analysis
# ============================================

# Model without flu index
X_no_flu = df[['pm25', 'heating_degree_day', 'school_holiday']]
X_no_flu = sm.add_constant(X_no_flu)
model_no_flu = sm.OLS(y, X_no_flu).fit()

# Model with moving average PM2.5
df_ma = df.dropna(subset=['pm25_ma7'])
X_ma = df_ma[['pm25_ma7', 'heating_degree_day', 'flu_index', 'school_holiday']]
X_ma = sm.add_constant(X_ma)
y_ma = df_ma['respiratory_visits']
model_ma = sm.OLS(y_ma, X_ma).fit()

print("\n" + "="*60)
print("SENSITIVITY ANALYSIS")
print("="*60)
print(f"Main model PM2.5 coef: {model_ols.params['pm25']:.3f} (p={model_ols.pvalues['pm25']:.4f})")
print(f"Without flu index: {model_no_flu.params['pm25']:.3f} (p={model_no_flu.pvalues['pm25']:.4f})")
print(f"7-day MA PM2.5: {model_ma.params['pm25_ma7']:.3f} (p={model_ma.pvalues['pm25_ma7']:.4f})")

# Save sensitivity results
sensitivity_df = pd.DataFrame({
    'Model': ['Main (daily PM2.5)', 'Without flu index', '7-day moving average PM2.5'],
    'PM2.5_Coefficient': [model_ols.params['pm25'], model_no_flu.params['pm25'], model_ma.params['pm25_ma7']],
    'PM2.5_pvalue': [model_ols.pvalues['pm25'], model_no_flu.pvalues['pm25'], model_ma.pvalues['pm25_ma7']],
    'R_squared': [model_ols.rsquared, model_no_flu.rsquared, model_ma.rsquared]
})
sensitivity_df.to_csv('../outputs/sensitivity_analysis.csv', index=False)

# Figure 10: Sensitivity comparison
fig, ax = plt.subplots(figsize=(10, 6))

models = ['Main Model\n(daily PM2.5)', 'Without\nFlu Index', '7-day Moving\nAverage PM2.5']
coefs = [model_ols.params['pm25'], model_no_flu.params['pm25'], model_ma.params['pm25_ma7']]
errors = [1.96*model_ols.bse['pm25'], 1.96*model_no_flu.bse['pm25'], 1.96*model_ma.bse['pm25_ma7']]

ax.bar(models, coefs, yerr=errors, color=['#3498db', '#2ecc71', '#e74c3c'], alpha=0.7, 
       edgecolor='black', capsize=10)
ax.axhline(0, color='black', linewidth=1)
ax.set_ylabel('PM2.5 Coefficient', fontsize=12)
ax.set_title('Sensitivity Analysis: PM2.5 Effect Across Model Specifications', fontsize=13, fontweight='bold')

for i, (c, e) in enumerate(zip(coefs, errors)):
    ax.text(i, c + e + 0.1, f'{c:.2f}', ha='center', fontsize=11)

plt.tight_layout()
plt.savefig('../report/images/fig10_sensitivity.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 10 saved: Sensitivity analysis")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print("All figures saved to report/images/")
print("All outputs saved to outputs/")