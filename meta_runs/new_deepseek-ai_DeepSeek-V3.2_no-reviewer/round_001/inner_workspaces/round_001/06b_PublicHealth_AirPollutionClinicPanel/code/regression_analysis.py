import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
data_path = '../data/daily_panel.csv'
df = pd.read_csv(data_path)

print("=== Regression Analysis ===")
print(f"Dataset: {len(df)} daily observations")

# Create output directory
os.makedirs('../outputs', exist_ok=True)

# 1. Simple linear regression: PM2.5 on respiratory visits
print("\n1. Simple Linear Regression: Respiratory Visits ~ PM2.5")
X_simple = sm.add_constant(df['pm25'])
y = df['respiratory_visits']
model_simple = sm.OLS(y, X_simple).fit()
print(model_simple.summary())

# 2. Multiple regression with all covariates
print("\n2. Multiple Regression with All Covariates")
X_multi = sm.add_constant(df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']])
model_multi = sm.OLS(y, X_multi).fit()
print(model_multi.summary())

# 3. Check for non-linear relationship (quadratic term for PM2.5)
print("\n3. Model with Quadratic PM2.5 Term")
df['pm25_sq'] = df['pm25'] ** 2
X_quad = sm.add_constant(df[['pm25', 'pm25_sq', 'heating_degree_day', 'flu_index', 'school_holiday']])
model_quad = sm.OLS(y, X_quad).fit()
print(model_quad.summary())

# 4. Model with interaction between PM2.5 and heating degree days
print("\n4. Model with PM2.5 * Heating Interaction")
df['pm25_hdd_interaction'] = df['pm25'] * df['heating_degree_day']
X_interact = sm.add_constant(df[['pm25', 'heating_degree_day', 'pm25_hdd_interaction', 
                                  'flu_index', 'school_holiday']])
model_interact = sm.OLS(y, X_interact).fit()
print(model_interact.summary())

# 5. Compare models using AIC/BIC
print("\n5. Model Comparison (AIC/BIC)")
models = {
    'Simple': model_simple,
    'Multi': model_multi,
    'Quadratic': model_quad,
    'Interaction': model_interact
}

comparison_df = pd.DataFrame({
    'Model': list(models.keys()),
    'AIC': [m.aic for m in models.values()],
    'BIC': [m.bic for m in models.values()],
    'R-squared': [m.rsquared for m in models.values()],
    'Adj. R-squared': [m.rsquared_adj for m in models.values()]
})

print(comparison_df)

# 6. Diagnostic plots for the best model (based on AIC)
best_model_name = comparison_df.loc[comparison_df['AIC'].idxmin(), 'Model']
best_model = models[best_model_name]
print(f"\n6. Best model based on AIC: {best_model_name}")

# Create diagnostic plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle(f'Diagnostic Plots for {best_model_name} Model', fontsize=16, y=1.02)

# Residuals vs Fitted
fitted_values = best_model.fittedvalues
residuals = best_model.resid
axes[0, 0].scatter(fitted_values, residuals, alpha=0.6)
axes[0, 0].axhline(y=0, color='r', linestyle='--', alpha=0.3)
axes[0, 0].set_xlabel('Fitted Values')
axes[0, 0].set_ylabel('Residuals')
axes[0, 0].set_title('Residuals vs Fitted')

# Q-Q plot
sm.qqplot(residuals, line='45', ax=axes[0, 1])
axes[0, 1].set_title('Q-Q Plot')

# Histogram of residuals
axes[1, 0].hist(residuals, bins=20, edgecolor='black', alpha=0.7)
axes[1, 0].set_xlabel('Residuals')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].set_title('Distribution of Residuals')

# Residuals vs PM2.5
axes[1, 1].scatter(df['pm25'], residuals, alpha=0.6)
axes[1, 1].axhline(y=0, color='r', linestyle='--', alpha=0.3)
axes[1, 1].set_xlabel('PM2.5 (μg/m³)')
axes[1, 1].set_ylabel('Residuals')
axes[1, 1].set_title('Residuals vs PM2.5')

plt.tight_layout()
plt.savefig('../report/images/diagnostic_plots.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"\nSaved diagnostic plots to ../report/images/diagnostic_plots.png")

# 7. Calculate marginal effects
print("\n7. Marginal Effects Analysis")
print("From the best model:")
print(best_model.summary())

# Calculate expected increase in respiratory visits per 10 μg/m³ increase in PM2.5
if 'pm25' in best_model.params:
    pm25_coef = best_model.params['pm25']
    pm25_se = best_model.bse['pm25']
    increase_per_10 = pm25_coef * 10
    se_per_10 = pm25_se * 10
    
    # 95% confidence interval
    ci_lower = (pm25_coef - 1.96 * pm25_se) * 10
    ci_upper = (pm25_coef + 1.96 * pm25_se) * 10
    
    print(f"\nExpected increase in respiratory visits per 10 μg/m³ PM2.5 increase:")
    print(f"  Point estimate: {increase_per_10:.2f} visits")
    print(f"  95% CI: [{ci_lower:.2f}, {ci_upper:.2f}] visits")
    print(f"  Relative increase: {(increase_per_10 / y.mean() * 100):.1f}% of mean daily visits")

# 8. Save regression results to file
results_path = '../outputs/regression_results.txt'
with open(results_path, 'w') as f:
    f.write("=== REGRESSION ANALYSIS RESULTS ===\n\n")
    
    f.write("1. SIMPLE LINEAR REGRESSION (Respiratory Visits ~ PM2.5)\n")
    f.write(str(model_simple.summary()))
    f.write("\n\n")
    
    f.write("2. MULTIPLE REGRESSION WITH ALL COVARIATES\n")
    f.write(str(model_multi.summary()))
    f.write("\n\n")
    
    f.write("3. MODEL WITH QUADRATIC PM2.5 TERM\n")
    f.write(str(model_quad.summary()))
    f.write("\n\n")
    
    f.write("4. MODEL WITH PM2.5 * HEATING INTERACTION\n")
    f.write(str(model_interact.summary()))
    f.write("\n\n")
    
    f.write("5. MODEL COMPARISON\n")
    f.write(comparison_df.to_string())
    f.write("\n\n")
    
    f.write(f"6. BEST MODEL: {best_model_name}\n")
    f.write(str(best_model.summary()))
    f.write("\n\n")
    
    if 'pm25' in best_model.params:
        f.write("7. MARGINAL EFFECTS\n")
        f.write(f"Expected increase in respiratory visits per 10 μg/m³ PM2.5 increase:\n")
        f.write(f"  Point estimate: {increase_per_10:.2f} visits\n")
        f.write(f"  95% CI: [{ci_lower:.2f}, {ci_upper:.2f}] visits\n")
        f.write(f"  Relative increase: {(increase_per_10 / y.mean() * 100):.1f}% of mean daily visits\n")

print(f"\nSaved regression results to {results_path}")

# 9. Create visualization of predicted vs actual
plt.figure(figsize=(10, 6))
plt.scatter(df['pm25'], y, alpha=0.5, label='Actual', color='blue')

# Sort for smooth line
sorted_idx = np.argsort(df['pm25'])
pm25_sorted = df['pm25'].iloc[sorted_idx]

# Predict using best model
if best_model_name == 'Simple':
    X_pred = sm.add_constant(pm25_sorted)
    y_pred = best_model.predict(X_pred)
elif best_model_name == 'Multi':
    # Need to create proper X matrix with mean values for other covariates
    X_pred = pd.DataFrame({
        'const': 1,
        'pm25': pm25_sorted,
        'heating_degree_day': df['heating_degree_day'].mean(),
        'flu_index': df['flu_index'].mean(),
        'school_holiday': 0
    })
    y_pred = best_model.predict(X_pred)
else:
    # For other models, use average values for other variables
    X_pred = pd.DataFrame({
        'const': 1,
        'pm25': pm25_sorted,
        'heating_degree_day': df['heating_degree_day'].mean(),
        'flu_index': df['flu_index'].mean(),
        'school_holiday': 0
    })
    # Add model-specific terms
    if 'pm25_sq' in best_model.params:
        X_pred['pm25_sq'] = pm25_sorted ** 2
    if 'pm25_hdd_interaction' in best_model.params:
        X_pred['pm25_hdd_interaction'] = pm25_sorted * df['heating_degree_day'].mean()
    
    y_pred = best_model.predict(X_pred)

plt.plot(pm25_sorted, y_pred, color='red', linewidth=2, label='Predicted (best model)')
plt.xlabel('PM2.5 (μg/m³)')
plt.ylabel('Respiratory Visits')
plt.title('PM2.5 vs Respiratory Visits with Best-Fit Line')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/pm25_vs_visits_fit.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nSaved PM2.5 vs visits fit plot to ../report/images/pm25_vs_visits_fit.png")

print("\n=== Regression Analysis Complete ===")