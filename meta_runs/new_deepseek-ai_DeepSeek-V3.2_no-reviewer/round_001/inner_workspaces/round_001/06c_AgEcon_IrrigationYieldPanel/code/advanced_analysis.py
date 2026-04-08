import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from linearmodels import PanelOLS
from linearmodels import RandomEffects
from linearmodels import PooledOLS
import warnings
warnings.filterwarnings('ignore')
import os
import scipy.stats as stats

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
data_path = '../data/field_year_panel.csv'
df = pd.read_csv(data_path)

print("=== ADVANCED ECONOMETRIC ANALYSIS: IRRIGATION PROGRAM EVALUATION ===")
print(f"Dataset contains {len(df)} plot-year observations")
print()

# Since we have plot_id but only one observation per plot, we can't do true panel analysis
# But we can explore heterogeneity and potential biases

# 1. Check for heteroskedasticity
print("1. HETEROSKEDASTICITY DIAGNOSTICS")
# Run initial regression
X = df[['irrigation_m3', 'fertilizer_kg', 'rainfall_mm', 'groundwater_quota_enforcement']]
X = sm.add_constant(X)
Y = df['yield_t_ha']
model = sm.OLS(Y, X).fit()

# Breusch-Pagan test for heteroskedasticity
from statsmodels.stats.diagnostic import het_breuschpagan
bp_test = het_breuschpagan(model.resid, X)
print(f"Breusch-Pagan test: LM={bp_test[0]:.3f}, p-value={bp_test[1]:.3f}")
print(f"F-statistic: {bp_test[2]:.3f}, p-value={bp_test[3]:.3f}")
if bp_test[1] < 0.05:
    print("-> Evidence of heteroskedasticity (use robust standard errors)")
else:
    print("-> No strong evidence of heteroskedasticity")
print()

# 2. Robust regression with heteroskedasticity-consistent standard errors
print("2. ROBUST REGRESSION WITH HETEROSKEDASTICITY-CONSISTENT STANDARD ERRORS")
model_robust = sm.OLS(Y, X).fit(cov_type='HC3')
print(model_robust.summary().tables[1])
print()

# Save robust results
with open('../outputs/robust_regression.txt', 'w') as f:
    f.write(str(model_robust.summary()))

# 3. Instrumental Variables approach (if we had instruments)
# Since we don't have instruments, we'll do a sensitivity analysis
print("3. SENSITIVITY ANALYSIS: QUANTILE REGRESSION")
print("Quantile regression at different yield levels (25th, 50th, 75th percentiles)")

quantiles = [0.25, 0.5, 0.75]
quantile_results = []

for q in quantiles:
    quant_model = sm.QuantReg(Y, X).fit(q=q)
    quantile_results.append({
        'quantile': q,
        'irrigation_coef': quant_model.params['irrigation_m3'],
        'quota_coef': quant_model.params['groundwater_quota_enforcement'],
        'rainfall_coef': quant_model.params['rainfall_mm'],
        'pseudo_r2': quant_model.prsquared
    })

quantile_df = pd.DataFrame(quantile_results)
print(quantile_df.round(4))
print()

# Save quantile results
quantile_df.to_csv('../outputs/quantile_regression_results.csv', index=False)

# 4. Non-linear relationships exploration
print("4. NON-LINEAR RELATIONSHIPS EXPLORATION")
print("Testing quadratic effects of irrigation and rainfall")

df['irrigation_sq'] = df['irrigation_m3'] ** 2
df['rainfall_sq'] = df['rainfall_mm'] ** 2

X_nonlinear = df[['irrigation_m3', 'irrigation_sq', 'fertilizer_kg', 
                  'rainfall_mm', 'rainfall_sq', 'groundwater_quota_enforcement']]
X_nonlinear = sm.add_constant(X_nonlinear)
model_nonlinear = sm.OLS(Y, X_nonlinear).fit()
print(model_nonlinear.summary().tables[1])
print()

# Save nonlinear results
with open('../outputs/nonlinear_regression.txt', 'w') as f:
    f.write(str(model_nonlinear.summary()))

# 5. Optimal irrigation level calculation
print("5. OPTIMAL IRRIGATION LEVEL CALCULATION")
# From quadratic model: yield = β0 + β1*irrigation + β2*irrigation² + ...
# Optimal irrigation where derivative = 0: β1 + 2β2*irrigation = 0
beta1 = model_nonlinear.params['irrigation_m3']
beta2 = model_nonlinear.params['irrigation_sq']

if beta2 < 0:  # Concave function
    optimal_irrigation = -beta1 / (2 * beta2)
    print(f"Optimal irrigation level (from quadratic model): {optimal_irrigation:.1f} m³")
    print(f"Mean irrigation in data: {df['irrigation_m3'].mean():.1f} m³")
    print(f"Median irrigation in data: {df['irrigation_m3'].median():.1f} m³")
    
    # Check if optimal is within data range
    if df['irrigation_m3'].min() <= optimal_irrigation <= df['irrigation_m3'].max():
        print("Optimal irrigation is within observed range")
    else:
        print("Optimal irrigation is outside observed range")
else:
    print("Quadratic term not negative, no interior optimum")
print()

# 6. Treatment effects analysis using propensity score matching (simplified)
print("6. TREATMENT EFFECTS ANALYSIS")
print("Comparing high vs low groundwater quota enforcement as 'treatment'")

# Define treatment: high quota enforcement (top tercile)
threshold = df['groundwater_quota_enforcement'].quantile(0.67)
df['high_quota_treatment'] = (df['groundwater_quota_enforcement'] >= threshold).astype(int)

# Balance check
balance_vars = ['irrigation_m3', 'fertilizer_kg', 'rainfall_mm']
balance_results = []

for var in balance_vars:
    treated_mean = df[df['high_quota_treatment'] == 1][var].mean()
    control_mean = df[df['high_quota_treatment'] == 0][var].mean()
    t_stat, p_val = stats.ttest_ind(
        df[df['high_quota_treatment'] == 1][var],
        df[df['high_quota_treatment'] == 0][var],
        equal_var=False
    )
    balance_results.append({
        'variable': var,
        'treated_mean': treated_mean,
        'control_mean': control_mean,
        'difference': treated_mean - control_mean,
        't_stat': t_stat,
        'p_value': p_val
    })

balance_df = pd.DataFrame(balance_results)
print("Balance check (high vs low quota enforcement):")
print(balance_df.round(3))
print()

# Simple difference in means
ate = df[df['high_quota_treatment'] == 1]['yield_t_ha'].mean() - \
      df[df['high_quota_treatment'] == 0]['yield_t_ha'].mean()
print(f"Average Treatment Effect (ATE) of high quota enforcement: {ate:.3f} t/ha")

# Regression adjustment
X_treatment = df[['high_quota_treatment', 'irrigation_m3', 'fertilizer_kg', 'rainfall_mm']]
X_treatment = sm.add_constant(X_treatment)
model_treatment = sm.OLS(Y, X_treatment).fit()
print(f"\nRegression-adjusted treatment effect: {model_treatment.params['high_quota_treatment']:.3f} t/ha")
print(f"(p-value: {model_treatment.pvalues['high_quota_treatment']:.3f})")
print()

# Save treatment analysis results
balance_df.to_csv('../outputs/treatment_balance_check.csv', index=False)
with open('../outputs/treatment_effects.txt', 'w') as f:
    f.write(f"Average Treatment Effect (ATE): {ate:.3f}\n")
    f.write(f"Regression-adjusted effect: {model_treatment.params['high_quota_treatment']:.3f}\n")
    f.write(f"p-value: {model_treatment.pvalues['high_quota_treatment']:.3f}\n")

# 7. Visualization of key results
print("7. CREATING ADVANCED VISUALIZATIONS...")

# Create figure for quantile regression results
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Quantile Regression: Irrigation Effects at Different Yield Levels', fontsize=16)

# Plot irrigation coefficients across quantiles
axes[0].bar(['25th', '50th', '75th'], 
            [quantile_results[0]['irrigation_coef'], 
             quantile_results[1]['irrigation_coef'], 
             quantile_results[2]['irrigation_coef']])
axes[0].set_ylabel('Irrigation Coefficient')
axes[0].set_title('Effect of Irrigation by Yield Quantile')
axes[0].axhline(y=0, color='r', linestyle='-', alpha=0.3)

# Plot quota enforcement coefficients across quantiles
axes[1].bar(['25th', '50th', '75th'], 
            [quantile_results[0]['quota_coef'], 
             quantile_results[1]['quota_coef'], 
             quantile_results[2]['quota_coef']])
axes[1].set_ylabel('Quota Enforcement Coefficient')
axes[1].set_title('Effect of Quota Enforcement by Yield Quantile')
axes[1].axhline(y=0, color='r', linestyle='-', alpha=0.3)

# Plot rainfall coefficients across quantiles
axes[2].bar(['25th', '50th', '75th'], 
            [quantile_results[0]['rainfall_coef'], 
             quantile_results[1]['rainfall_coef'], 
             quantile_results[2]['rainfall_coef']])
axes[2].set_ylabel('Rainfall Coefficient')
axes[2].set_title('Effect of Rainfall by Yield Quantile')
axes[2].axhline(y=0, color='r', linestyle='-', alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/quantile_regression_results.png', dpi=300, bbox_inches='tight')
print("Saved: ../report/images/quantile_regression_results.png")

# Plot quadratic relationship
plt.figure(figsize=(10, 6))
# Sort by irrigation for smooth curve
df_sorted = df.sort_values('irrigation_m3')
# Predict using quadratic model
X_pred = pd.DataFrame({
    'const': 1,
    'irrigation_m3': df_sorted['irrigation_m3'],
    'irrigation_sq': df_sorted['irrigation_m3'] ** 2,
    'fertilizer_kg': df_sorted['fertilizer_kg'].median(),
    'rainfall_mm': df_sorted['rainfall_mm'].median(),
    'rainfall_sq': (df_sorted['rainfall_mm'].median()) ** 2,
    'groundwater_quota_enforcement': df_sorted['groundwater_quota_enforcement'].median()
})
y_pred = model_nonlinear.predict(X_pred)

plt.scatter(df['irrigation_m3'], df['yield_t_ha'], alpha=0.6, label='Observed data')
plt.plot(df_sorted['irrigation_m3'], y_pred, 'r-', linewidth=2.5, label='Quadratic fit')
if beta2 < 0:
    plt.axvline(x=optimal_irrigation, color='g', linestyle='--', 
                label=f'Optimal irrigation: {optimal_irrigation:.0f} m³')
plt.xlabel('Irrigation (m³)')
plt.ylabel('Yield (t/ha)')
plt.title('Non-linear Relationship: Yield vs Irrigation (Quadratic Model)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/quadratic_irrigation_relationship.png', dpi=300, bbox_inches='tight')
print("Saved: ../report/images/quadratic_irrigation_relationship.png")

# Treatment effects visualization
plt.figure(figsize=(10, 6))
treatment_groups = df.groupby('high_quota_treatment')['yield_t_ha']
positions = [0, 1]
plt.boxplot([treatment_groups.get_group(0), treatment_groups.get_group(1)], 
            positions=positions, widths=0.6)
plt.xticks(positions, ['Low Quota Enforcement', 'High Quota Enforcement'])
plt.ylabel('Yield (t/ha)')
plt.title('Treatment Effects: Yield by Groundwater Quota Enforcement Level')
plt.axhline(y=df['yield_t_ha'].mean(), color='r', linestyle='--', alpha=0.5, label='Overall mean')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/treatment_effects_boxplot.png', dpi=300, bbox_inches='tight')
print("Saved: ../report/images/treatment_effects_boxplot.png")

# 8. Policy simulation
print("\n8. POLICY SIMULATION")
print("Simulating impact of increasing groundwater quota enforcement by 25%")

current_mean_quota = df['groundwater_quota_enforcement'].mean()
new_quota = current_mean_quota * 1.25
# Cap at maximum of 1
new_quota = min(new_quota, 1.0)

# Predict yields with new quota level
X_current = pd.DataFrame({
    'const': [1],
    'irrigation_m3': [df['irrigation_m3'].mean()],
    'fertilizer_kg': [df['fertilizer_kg'].mean()],
    'rainfall_mm': [df['rainfall_mm'].mean()],
    'groundwater_quota_enforcement': [current_mean_quota]
})

X_new = pd.DataFrame({
    'const': [1],
    'irrigation_m3': [df['irrigation_m3'].mean()],
    'fertilizer_kg': [df['fertilizer_kg'].mean()],
    'rainfall_mm': [df['rainfall_mm'].mean()],
    'groundwater_quota_enforcement': [new_quota]
})

yield_current = model.predict(X_current)[0]
yield_new = model.predict(X_new)[0]
yield_change = yield_new - yield_current
percent_change = (yield_change / yield_current) * 100

print(f"Current mean quota enforcement: {current_mean_quota:.3f}")
print(f"New quota enforcement (25% increase): {new_quota:.3f}")
print(f"Predicted yield change: {yield_change:.3f} t/ha ({percent_change:.1f}%)")
print(f"From {yield_current:.3f} to {yield_new:.3f} t/ha")

# Save policy simulation results
with open('../outputs/policy_simulation.txt', 'w') as f:
    f.write(f"Policy: Increase groundwater quota enforcement by 25%\n")
    f.write(f"Current mean: {current_mean_quota:.3f}\n")
    f.write(f"New level: {new_quota:.3f}\n")
    f.write(f"Predicted yield change: {yield_change:.3f} t/ha\n")
    f.write(f"Percentage change: {percent_change:.1f}%\n")
    f.write(f"From {yield_current:.3f} to {yield_new:.3f} t/ha\n")

print("\n=== ADVANCED ANALYSIS COMPLETE ===")
print("All outputs saved to outputs/ and report/images/ directories.")