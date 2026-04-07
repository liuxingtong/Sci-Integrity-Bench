import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.preprocessing import StandardScaler

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
df = pd.read_csv('data/daily_panel.csv')

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("Starting statistical modeling...")

# Handle negative PM2.5 values - these might be measurement errors
# For analysis, we'll consider absolute values or treat as 0 for sensitivity
# First, let's create a version with non-negative PM2.5
# Option 1: Set negative values to 0 (assuming measurement error)
df['pm25_nonneg'] = df['pm25'].clip(lower=0)
# Option 2: Use absolute values
df['pm25_abs'] = df['pm25'].abs()

print(f"Original PM2.5 range: [{df['pm25'].min():.2f}, {df['pm25'].max():.2f}]")
print(f"Non-negative PM2.5 range: [{df['pm25_nonneg'].min():.2f}, {df['pm25_nonneg'].max():.2f}]")
print(f"Number of negative PM2.5 values: {(df['pm25'] < 0).sum()}")

# 1. Simple linear regression: PM2.5 vs respiratory visits
print("\n=== Simple Linear Regression (PM2.5 → Respiratory Visits) ===")
X_simple = sm.add_constant(df['pm25'])
model_simple = sm.OLS(df['respiratory_visits'], X_simple).fit()
print(model_simple.summary())

# Save model results
with open('outputs/model_simple_summary.txt', 'w') as f:
    f.write(str(model_simple.summary()))

# 2. Multiple regression with all covariates
print("\n=== Multiple Regression with All Covariates ===")
X_multi = sm.add_constant(df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']])
model_multi = sm.OLS(df['respiratory_visits'], X_multi).fit()
print(model_multi.summary())

with open('outputs/model_multi_summary.txt', 'w') as f:
    f.write(str(model_multi.summary()))

# 3. Multiple regression with non-negative PM2.5
print("\n=== Multiple Regression with Non-negative PM2.5 ===")
X_multi_nn = sm.add_constant(df[['pm25_nonneg', 'heating_degree_day', 'flu_index', 'school_holiday']])
model_multi_nn = sm.OLS(df['respiratory_visits'], X_multi_nn).fit()
print(model_multi_nn.summary())

with open('outputs/model_multi_nn_summary.txt', 'w') as f:
    f.write(str(model_multi_nn.summary()))

# 4. Using formula API for easier specification
print("\n=== Formula-based Models ===")

# Model with interaction terms
model_formula1 = smf.ols('respiratory_visits ~ pm25 + heating_degree_day + flu_index + school_holiday', data=df).fit()
print("\nModel 1: Main effects only")
print(model_formula1.summary())

# Model with PM2.5 * heating interaction (cold days might amplify pollution effects)
model_formula2 = smf.ols('respiratory_visits ~ pm25 * heating_degree_day + flu_index + school_holiday', data=df).fit()
print("\nModel 2: With PM2.5 * heating interaction")
print(model_formula2.summary())

# Model with PM2.5 * flu interaction (flu might increase susceptibility)
model_formula3 = smf.ols('respiratory_visits ~ pm25 * flu_index + heating_degree_day + school_holiday', data=df).fit()
print("\nModel 3: With PM2.5 * flu interaction")
print(model_formula3.summary())

# Save all formula models
with open('outputs/model_formula1_summary.txt', 'w') as f:
    f.write(str(model_formula1.summary()))

with open('outputs/model_formula2_summary.txt', 'w') as f:
    f.write(str(model_formula2.summary()))

with open('outputs/model_formula3_summary.txt', 'w') as f:
    f.write(str(model_formula3.summary()))

# 5. Model comparison
print("\n=== Model Comparison ===")
models = {
    'Simple': model_simple,
    'Multi': model_multi,
    'Multi_nn': model_multi_nn,
    'Formula1': model_formula1,
    'Formula2': model_formula2,
    'Formula3': model_formula3
}

comparison_data = []
for name, model in models.items():
    comparison_data.append({
        'Model': name,
        'R-squared': model.rsquared,
        'Adj. R-squared': model.rsquared_adj,
        'AIC': model.aic,
        'BIC': model.bic,
        'PM2.5 Coef': model.params.get('pm25', model.params.get('pm25_nonneg', np.nan)),
        'PM2.5 P-value': model.pvalues.get('pm25', model.pvalues.get('pm25_nonneg', np.nan))
    })

comparison_df = pd.DataFrame(comparison_data)
print("\nModel comparison:")
print(comparison_df.to_string(index=False))
comparison_df.to_csv('outputs/model_comparison.csv', index=False)

# 6. Visualization of model results
# Plot coefficients for the best model (multi with all covariates)
coef_df = pd.DataFrame({
    'Variable': model_multi.params.index[1:],  # Skip constant
    'Coefficient': model_multi.params[1:],
    'Std Error': model_multi.bse[1:],
    'P-value': model_multi.pvalues[1:]
})

# Add confidence intervals
coef_df['CI_lower'] = coef_df['Coefficient'] - 1.96 * coef_df['Std Error']
coef_df['CI_upper'] = coef_df['Coefficient'] + 1.96 * coef_df['Std Error']

print("\nCoefficients for multiple regression model:")
print(coef_df.to_string(index=False))
coef_df.to_csv('outputs/coefficients_multi.csv', index=False)

# Plot coefficients with confidence intervals
plt.figure(figsize=(10, 6))
y_pos = np.arange(len(coef_df))
plt.errorbar(coef_df['Coefficient'], y_pos, 
             xerr=[coef_df['Coefficient'] - coef_df['CI_lower'], coef_df['CI_upper'] - coef_df['Coefficient']],
             fmt='o', color='steelblue', ecolor='lightcoral', elinewidth=2, capsize=5, markersize=8)
plt.axvline(x=0, color='gray', linestyle='--', alpha=0.7)
plt.yticks(y_pos, coef_df['Variable'])
plt.xlabel('Coefficient Estimate (95% CI)')
plt.title('Regression Coefficients: PM2.5 and Covariates on Respiratory Visits')
plt.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('report/images/coefficients_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# 7. Predicted vs actual values
# Use the best model for predictions
df['predicted_visits'] = model_multi.predict(X_multi)

plt.figure(figsize=(10, 6))
plt.scatter(df['predicted_visits'], df['respiratory_visits'], alpha=0.6, s=40)
plt.plot([df['respiratory_visits'].min(), df['respiratory_visits'].max()], 
         [df['respiratory_visits'].min(), df['respiratory_visits'].max()], 
         'r--', alpha=0.8, label='Perfect prediction')
plt.xlabel('Predicted Respiratory Visits')
plt.ylabel('Actual Respiratory Visits')
plt.title('Model Fit: Predicted vs Actual Respiratory Visits')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/predicted_vs_actual.png', dpi=300, bbox_inches='tight')
plt.close()

# 8. Residual analysis
residuals = df['respiratory_visits'] - df['predicted_visits']

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Residual Analysis', fontsize=16, y=1.02)

# Residuals vs predicted
axes[0, 0].scatter(df['predicted_visits'], residuals, alpha=0.6, s=30)
axes[0, 0].axhline(y=0, color='gray', linestyle='--', alpha=0.7)
axes[0, 0].set_xlabel('Predicted Values')
axes[0, 0].set_ylabel('Residuals')
axes[0, 0].set_title('Residuals vs Predicted')
axes[0, 0].grid(True, alpha=0.3)

# Residuals vs PM2.5
axes[0, 1].scatter(df['pm25'], residuals, alpha=0.6, s=30)
axes[0, 1].axhline(y=0, color='gray', linestyle='--', alpha=0.7)
axes[0, 1].set_xlabel('PM2.5')
axes[0, 1].set_ylabel('Residuals')
axes[0, 1].set_title('Residuals vs PM2.5')
axes[0, 1].grid(True, alpha=0.3)

# Histogram of residuals
axes[1, 0].hist(residuals, bins=20, edgecolor='black', alpha=0.7, color='steelblue')
axes[1, 0].axvline(x=0, color='gray', linestyle='--', alpha=0.7)
axes[1, 0].set_xlabel('Residuals')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].set_title('Distribution of Residuals')
axes[1, 0].grid(True, alpha=0.3)

# Q-Q plot for normality
sm.qqplot(residuals, line='45', ax=axes[1, 1])
axes[1, 1].set_title('Q-Q Plot of Residuals')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/residual_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# 9. Calculate effect size for policy discussion
# What's the expected increase in visits per 10 μg/m³ increase in PM2.5?
pm25_coef = model_multi.params['pm25']
effect_per_10 = pm25_coef * 10
print(f"\n=== Policy-Relevant Effect Size ===")
print(f"Coefficient for PM2.5: {pm25_coef:.3f} visits per 1 μg/m³")
print(f"Expected increase in respiratory visits per 10 μg/m³ PM2.5 increase: {effect_per_10:.1f} visits")
print(f"95% CI: [{pm25_coef - 1.96*model_multi.bse['pm25']:.3f}, {pm25_coef + 1.96*model_multi.bse['pm25']:.3f}] per 1 μg/m³")

# Calculate percentage increase relative to mean
mean_visits = df['respiratory_visits'].mean()
percent_increase = (effect_per_10 / mean_visits) * 100
print(f"Percentage increase per 10 μg/m³ PM2.5: {percent_increase:.1f}% (relative to mean of {mean_visits:.1f} visits)")

# Save effect size calculations
with open('outputs/effect_size_calculations.txt', 'w') as f:
    f.write(f"PM2.5 coefficient: {pm25_coef:.3f} visits per 1 μg/m³\n")
    f.write(f"Expected increase per 10 μg/m³ PM2.5: {effect_per_10:.1f} visits\n")
    f.write(f"95% CI per 1 μg/m³: [{pm25_coef - 1.96*model_multi.bse['pm25']:.3f}, {pm25_coef + 1.96*model_multi.bse['pm25']:.3f}]\n")
    f.write(f"Percentage increase per 10 μg/m³: {percent_increase:.1f}%\n")
    f.write(f"Mean daily visits: {mean_visits:.1f}\n")

print("\nModeling complete. All results saved to outputs/ and report/images/")