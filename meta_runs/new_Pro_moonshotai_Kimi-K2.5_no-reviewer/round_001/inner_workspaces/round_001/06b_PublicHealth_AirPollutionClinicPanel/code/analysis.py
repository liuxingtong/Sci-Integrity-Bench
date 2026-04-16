"""
Air Pollution and Respiratory Health Policy Analysis
=====================================================
Analysis of PM2.5 effects on respiratory clinic visits
with controls for heating, flu, and school holidays.
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

# Load data
print("Loading data...")
df = pd.read_csv('data/daily_panel.csv')
print(f"Dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nData summary:\n{df.describe()}")

# Create output directories
import os
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# ============================================================================
# 1. DATA OVERVIEW AND EXPLORATORY ANALYSIS
# ============================================================================

print("\n" + "="*60)
print("1. DATA OVERVIEW AND EXPLORATORY ANALYSIS")
print("="*60)

# Check for missing values
print(f"\nMissing values:\n{df.isnull().sum()}")

# Correlation matrix
corr_matrix = df.corr()
print(f"\nCorrelation matrix:\n{corr_matrix}")

# Create correlation heatmap
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0, 
            square=True, fmt='.3f', cbar_kws={'shrink': 0.8}, ax=ax)
ax.set_title('Correlation Matrix: Air Quality and Health Variables', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig1_correlation_matrix.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: fig1_correlation_matrix.png")

# ============================================================================
# 2. UNIVARIATE ANALYSIS - DISTRIBUTIONS
# ============================================================================

print("\n" + "="*60)
print("2. UNIVARIATE ANALYSIS")
print("="*60)

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

variables = ['pm25', 'respiratory_visits', 'heating_degree_day', 'flu_index', 'school_holiday']
titles = ['PM2.5 (μg/m³)', 'Respiratory Visits', 'Heating Degree Days', 'Flu Index', 'School Holiday']

for i, (var, title) in enumerate(zip(variables, titles)):
    ax = axes[i]
    if var == 'school_holiday':
        df[var].value_counts().plot(kind='bar', ax=ax, color='steelblue')
        ax.set_xticklabels(['No Holiday', 'Holiday'], rotation=0)
    else:
        ax.hist(df[var], bins=20, color='steelblue', edgecolor='black', alpha=0.7)
        ax.axvline(df[var].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df[var].mean():.2f}')
        ax.legend()
    ax.set_xlabel(title, fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title(f'Distribution of {title}', fontsize=12, fontweight='bold')

axes[5].axis('off')
plt.tight_layout()
plt.savefig('report/images/fig2_distributions.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: fig2_distributions.png")

# ============================================================================
# 3. BIVARIATE ANALYSIS - PM2.5 vs RESPIRATORY VISITS
# ============================================================================

print("\n" + "="*60)
print("3. BIVARIATE ANALYSIS: PM2.5 vs RESPIRATORY VISITS")
print("="*60)

# Scatter plot with regression line
fig, ax = plt.subplots(figsize=(10, 7))
scatter = ax.scatter(df['pm25'], df['respiratory_visits'], 
                     c=df['flu_index'], cmap='viridis', s=80, alpha=0.7, edgecolors='black')

# Add regression line
z = np.polyfit(df['pm25'], df['respiratory_visits'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['pm25'].min(), df['pm25'].max(), 100)
ax.plot(x_line, p(x_line), "r--", linewidth=2, label=f'Linear fit: slope={z[0]:.2f}')

cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Flu Index', fontsize=11)
ax.set_xlabel('PM2.5 Concentration (μg/m³)', fontsize=12)
ax.set_ylabel('Respiratory Clinic Visits', fontsize=12)
ax.set_title('PM2.5 vs Respiratory Visits (colored by Flu Index)', fontsize=14, fontweight='bold')
ax.legend(loc='upper left')
plt.tight_layout()
plt.savefig('report/images/fig3_pm25_vs_visits.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: fig3_pm25_vs_visits.png")

# Calculate Pearson correlation
pearson_r, pearson_p = stats.pearsonr(df['pm25'], df['respiratory_visits'])
print(f"Pearson correlation (PM2.5 vs Respiratory Visits): r={pearson_r:.4f}, p={pearson_p:.4f}")

# ============================================================================
# 4. TIME SERIES ANALYSIS
# ============================================================================

print("\n" + "="*60)
print("4. TIME SERIES ANALYSIS")
print("="*60)

fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

# PM2.5 time series
axes[0].plot(df['day_index'], df['pm25'], color='darkred', linewidth=1.5, label='PM2.5')
axes[0].axhline(df['pm25'].mean(), color='red', linestyle='--', alpha=0.7, label=f'Mean: {df["pm25"].mean():.1f}')
axes[0].fill_between(df['day_index'], df['pm25'], alpha=0.3, color='darkred')
axes[0].set_ylabel('PM2.5 (μg/m³)', fontsize=11)
axes[0].set_title('Daily PM2.5 Concentration', fontsize=12, fontweight='bold')
axes[0].legend(loc='upper right')
axes[0].grid(True, alpha=0.3)

# Respiratory visits time series
axes[1].plot(df['day_index'], df['respiratory_visits'], color='darkblue', linewidth=1.5, label='Respiratory Visits')
axes[1].axhline(df['respiratory_visits'].mean(), color='blue', linestyle='--', alpha=0.7, 
                label=f'Mean: {df["respiratory_visits"].mean():.1f}')
axes[1].fill_between(df['day_index'], df['respiratory_visits'], alpha=0.3, color='darkblue')
axes[1].set_ylabel('Visits', fontsize=11)
axes[1].set_title('Daily Respiratory Clinic Visits', fontsize=12, fontweight='bold')
axes[1].legend(loc='upper right')
axes[1].grid(True, alpha=0.3)

# Combined with heating degree days
ax2 = axes[2]
ax2.plot(df['day_index'], df['heating_degree_day'], color='orange', linewidth=1.5, label='Heating Degree Days')
ax2.set_ylabel('Heating Degree Days', fontsize=11, color='orange')
ax2.tick_params(axis='y', labelcolor='orange')
ax2.set_title('Heating Demand and Flu Index Over Time', fontsize=12, fontweight='bold')

ax3 = ax2.twinx()
ax3.plot(df['day_index'], df['flu_index'], color='green', linewidth=1.5, label='Flu Index', linestyle='--')
ax3.set_ylabel('Flu Index', fontsize=11, color='green')
ax3.tick_params(axis='y', labelcolor='green')

# Mark school holidays
holiday_days = df[df['school_holiday'] == 1]['day_index']
for day in holiday_days:
    for ax in axes:
        ax.axvline(day, color='gray', linestyle=':', alpha=0.5)

axes[2].set_xlabel('Day Index', fontsize=12)
fig.tight_layout()
plt.savefig('report/images/fig4_time_series.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: fig4_time_series.png")

# ============================================================================
# 5. REGRESSION ANALYSIS
# ============================================================================

print("\n" + "="*60)
print("5. REGRESSION ANALYSIS")
print("="*60)

# Model 1: Simple OLS - PM2.5 only
X1 = sm.add_constant(df['pm25'])
y = df['respiratory_visits']
model1 = sm.OLS(y, X1).fit()
print("\n--- Model 1: PM2.5 only ---")
print(model1.summary())

# Model 2: Multiple regression with all controls
X2 = df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']]
X2 = sm.add_constant(X2)
model2 = sm.OLS(y, X2).fit()
print("\n--- Model 2: Full Model with Controls ---")
print(model2.summary())

# Save regression results
with open('outputs/regression_results.txt', 'w') as f:
    f.write("="*70 + "\n")
    f.write("REGRESSION ANALYSIS RESULTS\n")
    f.write("="*70 + "\n\n")
    f.write("MODEL 1: PM2.5 Only\n")
    f.write("-"*70 + "\n")
    f.write(model1.summary().as_text())
    f.write("\n\n" + "="*70 + "\n\n")
    f.write("MODEL 2: Full Model with Controls\n")
    f.write("-"*70 + "\n")
    f.write(model2.summary().as_text())

print("Saved: outputs/regression_results.txt")

# ============================================================================
# 6. MODEL DIAGNOSTICS AND VALIDATION
# ============================================================================

print("\n" + "="*60)
print("6. MODEL DIAGNOSTICS")
print("="*60)

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Residuals vs Fitted
ax1 = axes[0, 0]
ax1.scatter(model2.fittedvalues, model2.resid, alpha=0.6, edgecolors='black')
ax1.axhline(y=0, color='red', linestyle='--')
ax1.set_xlabel('Fitted Values', fontsize=11)
ax1.set_ylabel('Residuals', fontsize=11)
ax1.set_title('Residuals vs Fitted', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Q-Q plot
ax2 = axes[0, 1]
stats.probplot(model2.resid, dist="norm", plot=ax2)
ax2.set_title('Normal Q-Q Plot', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)

# Histogram of residuals
ax3 = axes[1, 0]
ax3.hist(model2.resid, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
ax3.axvline(model2.resid.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {model2.resid.mean():.3f}')
ax3.set_xlabel('Residuals', fontsize=11)
ax3.set_ylabel('Frequency', fontsize=11)
ax3.set_title('Distribution of Residuals', fontsize=12, fontweight='bold')
ax3.legend()

# Scale-Location plot
ax4 = axes[1, 1]
residuals_sqrt = np.sqrt(np.abs(model2.resid))
ax4.scatter(model2.fittedvalues, residuals_sqrt, alpha=0.6, edgecolors='black')
ax4.set_xlabel('Fitted Values', fontsize=11)
ax4.set_ylabel('√|Residuals|', fontsize=11)
ax4.set_title('Scale-Location Plot', fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig5_diagnostics.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: fig5_diagnostics.png")

# Breusch-Pagan test for heteroscedasticity
bp_test = het_breuschpagan(model2.resid, model2.model.exog)
print(f"\nBreusch-Pagan test for heteroscedasticity:")
print(f"  LM Statistic: {bp_test[0]:.4f}")
print(f"  LM p-value: {bp_test[1]:.4f}")

# ============================================================================
# 7. POLICY-RELEVANT ANALYSIS
# ============================================================================

print("\n" + "="*60)
print("7. POLICY-RELEVANT ANALYSIS")
print("="*60)

# Calculate effect sizes
pm25_coef = model2.params['pm25']
pm25_ci_low = model2.conf_int()[0]['pm25']
pm25_ci_high = model2.conf_int()[1]['pm25']

print(f"\nPM2.5 Effect on Respiratory Visits:")
print(f"  Coefficient: {pm25_coef:.4f} visits per μg/m³ increase in PM2.5")
print(f"  95% CI: [{pm25_ci_low:.4f}, {pm25_ci_high:.4f}]")

# Calculate impact of 10 μg/m³ increase
effect_10 = pm25_coef * 10
effect_10_low = pm25_ci_low * 10
effect_10_high = pm25_ci_high * 10
print(f"\nImpact of 10 μg/m³ increase in PM2.5:")
print(f"  Expected increase: {effect_10:.2f} respiratory visits per day")
print(f"  95% CI: [{effect_10_low:.2f}, {effect_10_high:.2f}]")

# WHO guideline comparison (15 μg/m³ daily mean)
who_guideline = 15
days_exceeded = (df['pm25'] > who_guideline).sum()
percent_exceeded = (days_exceeded / len(df)) * 100
print(f"\nWHO Air Quality Guideline (15 μg/m³ daily mean):")
print(f"  Days exceeded: {days_exceeded} out of {len(df)} ({percent_exceeded:.1f}%)")

# PM2.5 categories analysis
def categorize_pm25(pm25):
    if pm25 <= 12:
        return 'Good (≤12)'
    elif pm25 <= 35.4:
        return 'Moderate (12.1-35.4)'
    else:
        return 'Unhealthy (>35.4)'

df['pm25_category'] = df['pm25'].apply(categorize_pm25)
category_stats = df.groupby('pm25_category')['respiratory_visits'].agg(['mean', 'std', 'count'])
print(f"\nRespiratory visits by PM2.5 category:")
print(category_stats)

# Visualization of policy thresholds
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Box plot by category
ax1 = axes[0]
category_order = ['Good (≤12)', 'Moderate (12.1-35.4)', 'Unhealthy (>35.4)']
df_plot = df.copy()
df_plot['pm25_category'] = pd.Categorical(df_plot['pm25_category'], categories=category_order, ordered=True)
sns.boxplot(data=df_plot, x='pm25_category', y='respiratory_visits', ax=ax1, palette='YlOrRd')
ax1.set_xlabel('PM2.5 Category (μg/m³)', fontsize=11)
ax1.set_ylabel('Respiratory Visits', fontsize=11)
ax1.set_title('Respiratory Visits by PM2.5 Air Quality Category', fontsize=12, fontweight='bold')
ax1.tick_params(axis='x', rotation=15)

# Dose-response curve
ax2 = axes[1]
pm25_range = np.linspace(df['pm25'].min(), df['pm25'].max(), 100)
# Predict using mean values of other covariates
mean_heating = df['heating_degree_day'].mean()
mean_flu = df['flu_index'].mean()
mean_holiday = df['school_holiday'].mean()

predicted_visits = (model2.params['const'] + 
                   model2.params['pm25'] * pm25_range + 
                   model2.params['heating_degree_day'] * mean_heating +
                   model2.params['flu_index'] * mean_flu +
                   model2.params['school_holiday'] * mean_holiday)

ax2.plot(pm25_range, predicted_visits, 'b-', linewidth=2, label='Predicted visits')
ax2.fill_between(pm25_range, 
                 predicted_visits - 1.96 * model2.bse['pm25'] * pm25_range,
                 predicted_visits + 1.96 * model2.bse['pm25'] * pm25_range,
                 alpha=0.2, color='blue', label='95% CI')
ax2.axvline(who_guideline, color='red', linestyle='--', linewidth=2, label=f'WHO Guideline ({who_guideline})')
ax2.set_xlabel('PM2.5 Concentration (μg/m³)', fontsize=11)
ax2.set_ylabel('Predicted Respiratory Visits', fontsize=11)
ax2.set_title('Dose-Response: PM2.5 and Respiratory Visits', fontsize=12, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig6_policy_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: fig6_policy_analysis.png")

# ============================================================================
# 8. SENSITIVITY ANALYSIS
# ============================================================================

print("\n" + "="*60)
print("8. SENSITIVITY ANALYSIS")
print("="*60)

# Model without flu index (potential mediator)
X3 = df[['pm25', 'heating_degree_day', 'school_holiday']]
X3 = sm.add_constant(X3)
model3 = sm.OLS(y, X3).fit()
print("\n--- Model 3: Without Flu Index ---")
print(f"PM2.5 coefficient: {model3.params['pm25']:.4f} (SE: {model3.bse['pm25']:.4f})")

# Model with PM2.5 squared (non-linearity check)
df['pm25_sq'] = df['pm25'] ** 2
X4 = df[['pm25', 'pm25_sq', 'heating_degree_day', 'flu_index', 'school_holiday']]
X4 = sm.add_constant(X4)
model4 = sm.OLS(y, X4).fit()
print("\n--- Model 4: With PM2.5 Squared (non-linearity check) ---")
print(f"PM2.5 linear term: {model4.params['pm25']:.4f} (p={model4.pvalues['pm25']:.4f})")
print(f"PM2.5 squared term: {model4.params['pm25_sq']:.4f} (p={model4.pvalues['pm25_sq']:.4f})")

# Compare model performance
print("\n--- Model Comparison ---")
models = {'Model 1 (PM2.5 only)': model1, 
          'Model 2 (Full)': model2, 
          'Model 3 (No flu)': model3,
          'Model 4 (Non-linear)': model4}
for name, model in models.items():
    print(f"{name}: R²={model.rsquared:.4f}, AIC={model.aic:.2f}, BIC={model.bic:.2f}")

# ============================================================================
# 9. SAVE RESULTS
# ============================================================================

print("\n" + "="*60)
print("9. SAVING RESULTS")
print("="*60)

# Save key statistics
results_summary = {
    'pm25_mean': df['pm25'].mean(),
    'pm25_std': df['pm25'].std(),
    'pm25_max': df['pm25'].max(),
    'visits_mean': df['respiratory_visits'].mean(),
    'visits_std': df['respiratory_visits'].std(),
    'pm25_visits_correlation': pearson_r,
    'pm25_visits_pvalue': pearson_p,
    'model2_pm25_coef': model2.params['pm25'],
    'model2_pm25_se': model2.bse['pm25'],
    'model2_pm25_pvalue': model2.pvalues['pm25'],
    'model2_r_squared': model2.rsquared,
    'model2_adj_r_squared': model2.rsquared_adj,
    'who_days_exceeded': days_exceeded,
    'who_percent_exceeded': percent_exceeded,
    'effect_per_10ug': effect_10
}

results_df = pd.DataFrame([results_summary])
results_df.to_csv('outputs/key_results.csv', index=False)
print("Saved: outputs/key_results.csv")

# Save category analysis
category_stats.to_csv('outputs/pm25_category_analysis.csv')
print("Saved: outputs/pm25_category_analysis.csv")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
