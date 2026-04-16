import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan, het_white
from statsmodels.stats.outliers_influence import variance_inflation_factor
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
data_path = '../data/reit_macro_quarterly.csv'
df = pd.read_csv(data_path)

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("=== ADVANCED ECONOMETRIC ANALYSIS ===\n")

# 1. Check for heteroscedasticity
print("1. HETEROSCEDASTICITY TESTS")
X = sm.add_constant(df['inflation_yoy'])
y = df['reit_index_return']
model = sm.OLS(y, X).fit()

# Breusch-Pagan test
bp_test = het_breuschpagan(model.resid, model.model.exog)
print(f"Breusch-Pagan test:")
print(f"  LM statistic: {bp_test[0]:.4f}")
print(f"  p-value: {bp_test[1]:.4f}")
print(f"  Significant heteroscedasticity at 5% level: {bp_test[1] < 0.05}")

# White test
white_test = het_white(model.resid, model.model.exog)
print(f"\nWhite test:")
print(f"  LM statistic: {white_test[0]:.4f}")
print(f"  p-value: {white_test[1]:.4f}")
print(f"  Significant heteroscedasticity at 5% level: {white_test[1] < 0.05}")

# 2. Check for multicollinearity (for models with multiple predictors)
print("\n2. MULTICOLLINEARITY CHECK (for quadratic model)")
df['inflation_sq'] = df['inflation_yoy'] ** 2
X_quad = df[['inflation_yoy', 'inflation_sq']]
X_quad_const = sm.add_constant(X_quad)

# Calculate VIF
vif_data = pd.DataFrame()
vif_data["Variable"] = X_quad_const.columns
vif_data["VIF"] = [variance_inflation_factor(X_quad_const.values, i) for i in range(X_quad_const.shape[1])]
print(vif_data)
print("\nVIF > 10 indicates high multicollinearity.")

# 3. Robust standard errors
print("\n3. ROBUST STANDARD ERRORS")
model_robust = sm.OLS(y, X).fit(cov_type='HC3')
print("Model with robust (HC3) standard errors:")
print(model_robust.summary())

# Save robust results
with open('../outputs/robust_regression_results.txt', 'w') as f:
    f.write(str(model_robust.summary()))

# 4. Quantile regression to understand different parts of the distribution
print("\n4. QUANTILE REGRESSION ANALYSIS")
import statsmodels.regression.quantile_regression as qr

quantiles = [0.25, 0.5, 0.75]
quantile_results = {}

fig, ax = plt.subplots(figsize=(10, 6))

# Scatter plot
ax.scatter(df['inflation_yoy'], df['reit_index_return'], alpha=0.6, label='Data')

# OLS line for comparison
ax.plot(df['inflation_yoy'], model.fittedvalues, 'r-', linewidth=2, label='OLS (Mean)')

colors = ['green', 'blue', 'purple']
for i, q in enumerate(quantiles):
    quant_model = qr.QuantReg(y, X).fit(q=q)
    quantile_results[q] = quant_model
    
    ax.plot(df['inflation_yoy'], quant_model.fittedvalues, 
            '--', linewidth=2, color=colors[i], 
            label=f'Quantile {q}')
    
    print(f"\nQuantile {q} regression:")
    print(f"  Intercept: {quant_model.params['const']:.4f}")
    print(f"  Slope: {quant_model.params['inflation_yoy']:.4f}")
    print(f"  Pseudo R-squared: {quant_model.prsquared:.4f}")

ax.set_title('Quantile Regression: REIT Returns vs Inflation', fontsize=14)
ax.set_xlabel('Inflation (Year-over-Year, %)', fontsize=12)
ax.set_ylabel('REIT Index Return', fontsize=12)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/quantile_regression.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nQuantile regression plot saved.")

# 5. Structural break analysis (Chow test)
print("\n5. STRUCTURAL BREAK ANALYSIS")
# Sort by inflation to check if relationship changes at different inflation levels
df_sorted = df.sort_values('inflation_yoy').reset_index(drop=True)

# Test for structural break at median inflation
break_point = len(df_sorted) // 2

# Split data
low_inf = df_sorted.iloc[:break_point]
high_inf = df_sorted.iloc[break_point:]

# Run separate regressions
X_low = sm.add_constant(low_inf['inflation_yoy'])
y_low = low_inf['reit_index_return']
model_low = sm.OLS(y_low, X_low).fit()

X_high = sm.add_constant(high_inf['inflation_yoy'])
y_high = high_inf['reit_index_return']
model_high = sm.OLS(y_high, X_high).fit()

# Pooled regression
X_pool = sm.add_constant(df_sorted['inflation_yoy'])
y_pool = df_sorted['reit_index_return']
model_pool = sm.OLS(y_pool, X_pool).fit()

# Calculate Chow test statistic manually
ssr_pool = model_pool.ssr
ssr_low = model_low.ssr
ssr_high = model_high.ssr
ssr_combined = ssr_low + ssr_high

n = len(df_sorted)
k = 2  # parameters (intercept + slope)
n1 = len(low_inf)
n2 = len(high_inf)

chow_stat = ((ssr_pool - ssr_combined) / k) / (ssr_combined / (n - 2*k))

# F-distribution critical value
from scipy.stats import f
critical_value = f.ppf(0.95, k, n - 2*k)
p_value = 1 - f.cdf(chow_stat, k, n - 2*k)

print(f"Chow test for structural break at median inflation:")
print(f"  Chow statistic: {chow_stat:.4f}")
print(f"  Critical value (5%): {critical_value:.4f}")
print(f"  p-value: {p_value:.4f}")
print(f"  Structural break detected at 5% level: {chow_stat > critical_value}")

# 6. Plot the relationship in different regimes
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Low inflation regime
axes[0].scatter(low_inf['inflation_yoy'], low_inf['reit_index_return'], alpha=0.7)
x_low_range = np.linspace(low_inf['inflation_yoy'].min(), low_inf['inflation_yoy'].max(), 100)
y_low_pred = model_low.params['const'] + model_low.params['inflation_yoy'] * x_low_range
axes[0].plot(x_low_range, y_low_pred, 'r-', linewidth=2)
axes[0].set_title(f'Low Inflation Regime (n={len(low_inf)})', fontsize=13)
axes[0].set_xlabel('Inflation (%)', fontsize=11)
axes[0].set_ylabel('REIT Return', fontsize=11)
axes[0].grid(True, alpha=0.3)
axes[0].text(0.05, 0.95, f'Slope: {model_low.params["inflation_yoy"]:.3f}\nR²: {model_low.rsquared:.3f}',
             transform=axes[0].transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# High inflation regime
axes[1].scatter(high_inf['inflation_yoy'], high_inf['reit_index_return'], alpha=0.7)
x_high_range = np.linspace(high_inf['inflation_yoy'].min(), high_inf['inflation_yoy'].max(), 100)
y_high_pred = model_high.params['const'] + model_high.params['inflation_yoy'] * x_high_range
axes[1].plot(x_high_range, y_high_pred, 'r-', linewidth=2)
axes[1].set_title(f'High Inflation Regime (n={len(high_inf)})', fontsize=13)
axes[1].set_xlabel('Inflation (%)', fontsize=11)
axes[1].set_ylabel('REIT Return', fontsize=11)
axes[1].grid(True, alpha=0.3)
axes[1].text(0.05, 0.95, f'Slope: {model_high.params["inflation_yoy"]:.3f}\nR²: {model_high.rsquared:.3f}',
             transform=axes[1].transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('../report/images/structural_break_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nStructural break analysis plot saved.")

# 7. Calculate economic significance
print("\n6. ECONOMIC SIGNIFICANCE")
# From the robust model
slope = model_robust.params['inflation_yoy']
slope_se = model_robust.bse['inflation_yoy']

print(f"A 1 percentage point increase in inflation is associated with:")
print(f"  {slope:.4f} increase in REIT index return")
print(f"  95% Confidence Interval: [{slope - 1.96*slope_se:.4f}, {slope + 1.96*slope_se:.4f}]")

# Calculate percentage change relative to mean REIT return
mean_reit = df['reit_index_return'].mean()
print(f"\nRelative to mean REIT return of {mean_reit:.4f}:")
print(f"  A 1% inflation increase corresponds to {100*slope/mean_reit:.2f}% of mean REIT return")

# Simulate impact of different inflation scenarios
print(f"\nPredicted REIT returns for different inflation scenarios:")
inflation_scenarios = [1.0, 2.0, 3.0, 4.0]
for inf in inflation_scenarios:
    pred_return = model_robust.params['const'] + model_robust.params['inflation_yoy'] * inf
    print(f"  Inflation at {inf}%: Predicted REIT return = {pred_return:.4f}")

print("\n=== ADVANCED ANALYSIS COMPLETE ===")