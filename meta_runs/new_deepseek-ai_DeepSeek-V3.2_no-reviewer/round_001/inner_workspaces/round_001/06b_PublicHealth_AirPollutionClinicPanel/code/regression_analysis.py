import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
df = pd.read_csv('../data/daily_panel.csv')

print("=== Regression Analysis: PM2.5 and Respiratory Visits ===\n")

# 1. Simple linear regression (unadjusted)
print("1. Simple Linear Regression (Unadjusted)")
print("   Model: respiratory_visits ~ pm25")
model_simple = smf.ols('respiratory_visits ~ pm25', data=df).fit()
print(model_simple.summary())
print(f"\n   Interpretation: Each 1 µg/m³ increase in PM2.5 is associated with ")
print(f"   {model_simple.params['pm25']:.3f} additional respiratory visits per day.")
print(f"   R-squared: {model_simple.rsquared:.3f}")

# 2. Multiple regression with all covariates
print("\n\n2. Multiple Regression with All Covariates")
print("   Model: respiratory_visits ~ pm25 + heating_degree_day + flu_index + school_holiday")
model_full = smf.ols('respiratory_visits ~ pm25 + heating_degree_day + flu_index + school_holiday', data=df).fit()
print(model_full.summary())
print(f"\n   Interpretation: After adjusting for confounders, each 1 µg/m³ increase in PM2.5")
print(f"   is associated with {model_full.params['pm25']:.3f} additional respiratory visits.")
print(f"   R-squared: {model_full.rsquared:.3f} (Adjusted: {model_full.rsquared_adj:.3f})")

# 3. Check for multicollinearity
print("\n\n3. Multicollinearity Check (Variance Inflation Factors)")
X = df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']]
X = sm.add_constant(X)  # Add constant for VIF calculation
vif_data = pd.DataFrame()
vif_data["Variable"] = X.columns
vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
print(vif_data)
print("\n   Rule of thumb: VIF > 10 indicates problematic multicollinearity")

# 4. Check for non-linear relationship
print("\n\n4. Checking for Non-linear Relationship")
print("   Adding quadratic term for PM2.5")
df['pm25_squared'] = df['pm25'] ** 2
model_quadratic = smf.ols('respiratory_visits ~ pm25 + pm25_squared + heating_degree_day + flu_index + school_holiday', data=df).fit()
print(model_quadratic.summary())

# Test if quadratic term is significant
print(f"\n   p-value for pm25_squared: {model_quadratic.pvalues['pm25_squared']:.4f}")
if model_quadratic.pvalues['pm25_squared'] < 0.05:
    print("   Quadratic term is statistically significant (p < 0.05)")
else:
    print("   Quadratic term is not statistically significant")

# 5. Model with interaction terms
print("\n\n5. Exploring Interaction Effects")
print("   Model with PM2.5 * heating_degree_day interaction")
model_interaction = smf.ols('respiratory_visits ~ pm25 * heating_degree_day + flu_index + school_holiday', data=df).fit()
print(model_interaction.summary())

# 6. Model diagnostics
print("\n\n6. Model Diagnostics")
print("   Checking residuals for the full model...")

# Calculate residuals
residuals = model_full.resid
fitted = model_full.fittedvalues

# Create diagnostic plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Regression Diagnostics: Full Model', fontsize=16, y=1.02)

# Residuals vs Fitted
axes[0, 0].scatter(fitted, residuals, alpha=0.6)
axes[0, 0].axhline(y=0, color='red', linestyle='--', alpha=0.7)
axes[0, 0].set_xlabel('Fitted Values')
axes[0, 0].set_ylabel('Residuals')
axes[0, 0].set_title('Residuals vs Fitted')
axes[0, 0].grid(True, alpha=0.3)

# Q-Q plot
sm.qqplot(residuals, line='45', fit=True, ax=axes[0, 1])
axes[0, 1].set_title('Q-Q Plot of Residuals')
axes[0, 1].grid(True, alpha=0.3)

# Histogram of residuals
axes[1, 0].hist(residuals, bins=20, edgecolor='black', alpha=0.7)
axes[1, 0].axvline(x=0, color='red', linestyle='--', alpha=0.7)
axes[1, 0].set_xlabel('Residuals')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].set_title('Distribution of Residuals')
axes[1, 0].grid(True, alpha=0.3)

# Residuals vs PM2.5
axes[1, 1].scatter(df['pm25'], residuals, alpha=0.6)
axes[1, 1].axhline(y=0, color='red', linestyle='--', alpha=0.7)
axes[1, 1].set_xlabel('PM2.5')
axes[1, 1].set_ylabel('Residuals')
axes[1, 1].set_title('Residuals vs PM2.5')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/regression_diagnostics.png', dpi=300, bbox_inches='tight')
plt.close()

# 7. Compare models
print("\n\n7. Model Comparison")
models = {
    'Simple': model_simple,
    'Full': model_full,
    'Quadratic': model_quadratic,
    'Interaction': model_interaction
}

comparison = pd.DataFrame({
    'Model': list(models.keys()),
    'R-squared': [m.rsquared for m in models.values()],
    'Adj. R-squared': [m.rsquared_adj for m in models.values()],
    'AIC': [m.aic for m in models.values()],
    'BIC': [m.bic for m in models.values()]
})

print(comparison.to_string(index=False))
print("\n   Lower AIC/BIC indicates better model fit")

# 8. Calculate effect size for policy discussion
print("\n\n8. Effect Size Calculation for Policy Discussion")
# Calculate IQR for PM2.5
pm25_iqr = df['pm25'].quantile(0.75) - df['pm25'].quantile(0.25)
print(f"   IQR of PM2.5: {pm25_iqr:.2f} µg/m³")

# Effect of IQR increase in PM2.5 on respiratory visits
effect_iqr = model_full.params['pm25'] * pm25_iqr
print(f"   Effect of IQR increase in PM2.5: {effect_iqr:.2f} additional respiratory visits per day")

# Calculate percentage increase relative to mean
mean_visits = df['respiratory_visits'].mean()
percent_increase = (effect_iqr / mean_visits) * 100
print(f"   This represents a {percent_increase:.1f}% increase relative to the mean daily visits ({mean_visits:.1f})")

# 9. Save model results for reporting
results_summary = pd.DataFrame({
    'Variable': model_full.params.index,
    'Coefficient': model_full.params.values,
    'Std Error': model_full.bse.values,
    't-value': model_full.tvalues.values,
    'p-value': model_full.pvalues.values,
    '95% CI Lower': model_full.conf_int()[0].values,
    '95% CI Upper': model_full.conf_int()[1].values
})

results_summary.to_csv('../outputs/regression_results.csv', index=False)
print("\n\nRegression results saved to outputs/regression_results.csv")

print("\n=== Regression Analysis Complete ===")
