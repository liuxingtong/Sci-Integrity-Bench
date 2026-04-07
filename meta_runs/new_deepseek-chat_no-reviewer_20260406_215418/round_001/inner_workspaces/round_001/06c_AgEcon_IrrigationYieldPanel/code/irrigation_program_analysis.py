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
df = pd.read_csv('data/field_year_panel.csv')
print("=== Irrigation Program Outcome Analysis ===")
print(f"Data shape: {df.shape}")

# 1. Define treatment: High vs Low groundwater quota enforcement
# Create binary treatment variable (High enforcement = 1)
median_enforcement = df['groundwater_quota_enforcement'].median()
df['high_enforcement'] = (df['groundwater_quota_enforcement'] > median_enforcement).astype(int)
print(f"\nMedian enforcement value: {median_enforcement:.3f}")
print(f"High enforcement plots: {df['high_enforcement'].sum()} ({df['high_enforcement'].sum()/len(df)*100:.1f}%)")
print(f"Low enforcement plots: {(df['high_enforcement'] == 0).sum()} ({100 - df['high_enforcement'].sum()/len(df)*100:.1f}%)")

# 2. Balance check: Compare characteristics of treatment and control groups
print("\n=== Balance Check: High vs Low Enforcement Groups ===")
balance_vars = ['irrigation_m3', 'fertilizer_kg', 'rainfall_mm']

balance_results = []
for var in balance_vars:
    high_group = df[df['high_enforcement'] == 1][var]
    low_group = df[df['high_enforcement'] == 0][var]
    
    t_stat, p_value = stats.ttest_ind(high_group, low_group, equal_var=False)
    
    balance_results.append({
        'Variable': var,
        'High_Mean': high_group.mean(),
        'Low_Mean': low_group.mean(),
        'Difference': high_group.mean() - low_group.mean(),
        't-statistic': t_stat,
        'p-value': p_value
    })

balance_df = pd.DataFrame(balance_results)
print(balance_df.round(4))

# Save balance check results
balance_df.to_csv('outputs/balance_check.csv', index=False)

# 3. Average Treatment Effect (ATE) - Simple comparison
print("\n=== Average Treatment Effect (Simple Comparison) ===")
yield_high = df[df['high_enforcement'] == 1]['yield_t_ha']
yield_low = df[df['high_enforcement'] == 0]['yield_t_ha']

ate_simple = yield_high.mean() - yield_low.mean()
t_stat_ate, p_value_ate = stats.ttest_ind(yield_high, yield_low, equal_var=False)

print(f"Mean yield (High enforcement): {yield_high.mean():.3f} t/ha")
print(f"Mean yield (Low enforcement): {yield_low.mean():.3f} t/ha")
print(f"ATE (Simple): {ate_simple:.3f} t/ha")
print(f"t-statistic: {t_stat_ate:.3f}, p-value: {p_value_ate:.4f}")

# 4. Regression-adjusted ATE
print("\n=== Regression-Adjusted ATE ===")
# Model with covariates
model_ate = smf.ols('yield_t_ha ~ high_enforcement + irrigation_m3 + fertilizer_kg + rainfall_mm', data=df).fit()
print(model_ate.summary().tables[1])

# Extract ATE from regression
ate_reg = model_ate.params['high_enforcement']
ate_reg_se = model_ate.bse['high_enforcement']
print(f"\nRegression-adjusted ATE: {ate_reg:.3f} t/ha (SE: {ate_reg_se:.3f})")
print(f"95% CI: [{ate_reg - 1.96*ate_reg_se:.3f}, {ate_reg + 1.96*ate_reg_se:.3f}]")

# Save regression results
with open('outputs/ate_regression_results.txt', 'w') as f:
    f.write(str(model_ate.summary()))

# 5. Heterogeneous treatment effects by rainfall levels
print("\n=== Heterogeneous Effects by Rainfall Levels ===")
# Create rainfall terciles
df['rainfall_tercile'] = pd.qcut(df['rainfall_mm'], q=3, labels=['Low', 'Medium', 'High'])

# Calculate ATE by rainfall tercile
ate_by_rainfall = []
for tercile in ['Low', 'Medium', 'High']:
    subset = df[df['rainfall_tercile'] == tercile]
    if len(subset) > 0:
        yield_high_tercile = subset[subset['high_enforcement'] == 1]['yield_t_ha']
        yield_low_tercile = subset[subset['high_enforcement'] == 0]['yield_t_ha']
        
        if len(yield_high_tercile) > 1 and len(yield_low_tercile) > 1:
            ate_tercile = yield_high_tercile.mean() - yield_low_tercile.mean()
            t_stat, p_value = stats.ttest_ind(yield_high_tercile, yield_low_tercile, equal_var=False)
            
            ate_by_rainfall.append({
                'Rainfall_Tercile': tercile,
                'N_high': len(yield_high_tercile),
                'N_low': len(yield_low_tercile),
                'Yield_high': yield_high_tercile.mean(),
                'Yield_low': yield_low_tercile.mean(),
                'ATE': ate_tercile,
                'p_value': p_value
            })

ate_rainfall_df = pd.DataFrame(ate_by_rainfall)
print(ate_rainfall_df.round(4))

# Save heterogeneous effects results
ate_rainfall_df.to_csv('outputs/heterogeneous_effects_rainfall.csv', index=False)

# 6. Irrigation water use efficiency analysis
print("\n=== Irrigation Water Use Efficiency ===")
# Calculate yield per unit irrigation water
df['water_productivity'] = df['yield_t_ha'] / df['irrigation_m3']
# Handle division by zero or very small values
df['water_productivity'] = df['water_productivity'].replace([np.inf, -np.inf], np.nan)

# Compare water productivity by enforcement
wp_high = df[df['high_enforcement'] == 1]['water_productivity'].dropna()
wp_low = df[df['high_enforcement'] == 0]['water_productivity'].dropna()

print(f"Water productivity (High enforcement): {wp_high.mean():.4f} t/ha per m3 (n={len(wp_high)})")
print(f"Water productivity (Low enforcement): {wp_low.mean():.4f} t/ha per m3 (n={len(wp_low)})")
print(f"Difference: {wp_high.mean() - wp_low.mean():.4f} t/ha per m3")

# Test for significance
if len(wp_high) > 1 and len(wp_low) > 1:
    t_stat_wp, p_value_wp = stats.ttest_ind(wp_high, wp_low, equal_var=False)
    print(f"t-statistic: {t_stat_wp:.3f}, p-value: {p_value_wp:.4f}")

# 7. Visualizations for irrigation program assessment
print("\n=== Creating Program Assessment Visualizations ===")

# Figure 1: Yield distribution by enforcement status
plt.figure(figsize=(10, 6))
sns.boxplot(x='high_enforcement', y='yield_t_ha', data=df)
plt.xlabel('Groundwater Quota Enforcement (0=Low, 1=High)')
plt.ylabel('Yield (t/ha)')
plt.title('Yield Distribution by Groundwater Quota Enforcement Status')
plt.xticks([0, 1], ['Low Enforcement', 'High Enforcement'])
plt.tight_layout()
plt.savefig('report/images/yield_by_enforcement_status.png', dpi=300, bbox_inches='tight')
print("Saved yield_by_enforcement_status.png")

# Figure 2: Relationship between enforcement and irrigation use
plt.figure(figsize=(10, 6))
plt.scatter(df['groundwater_quota_enforcement'], df['irrigation_m3'], alpha=0.7)
plt.xlabel('Groundwater Quota Enforcement')
plt.ylabel('Irrigation Water Use (m3)')
plt.title('Irrigation Water Use vs Groundwater Quota Enforcement')

# Add trend line
z = np.polyfit(df['groundwater_quota_enforcement'], df['irrigation_m3'], 1)
p = np.poly1d(z)
plt.plot(df['groundwater_quota_enforcement'], p(df['groundwater_quota_enforcement']), "r--", alpha=0.8, 
         label=f'Trend: y = {z[0]:.2f}x + {z[1]:.2f}')
plt.legend()
plt.tight_layout()
plt.savefig('report/images/irrigation_vs_enforcement.png', dpi=300, bbox_inches='tight')
print("Saved irrigation_vs_enforcement.png")

# Figure 3: Heterogeneous treatment effects by rainfall
if not ate_rainfall_df.empty:
    plt.figure(figsize=(10, 6))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for i, row in ate_rainfall_df.iterrows():
        plt.bar(i, row['ATE'], color=colors[i], alpha=0.7, 
                label=f"{row['Rainfall_Tercile']} Rainfall")
        
        # Add error bars (approximate 95% CI)
        ci_width = 1.96 * (abs(row['Yield_high'] - row['Yield_low']) / np.sqrt(row['N_high'] + row['N_low']))
        plt.errorbar(i, row['ATE'], yerr=ci_width, fmt='none', color='black', capsize=5)
    
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.xlabel('Rainfall Tercile')
    plt.ylabel('Average Treatment Effect (t/ha)')
    plt.title('Heterogeneous Treatment Effects of Groundwater Enforcement by Rainfall Level')
    plt.xticks(range(len(ate_rainfall_df)), ate_rainfall_df['Rainfall_Tercile'])
    plt.legend()
    plt.tight_layout()
    plt.savefig('report/images/heterogeneous_effects.png', dpi=300, bbox_inches='tight')
    print("Saved heterogeneous_effects.png")

# Figure 4: Water productivity by enforcement status
plt.figure(figsize=(10, 6))
wp_data = pd.DataFrame({
    'Enforcement': ['Low'] * len(wp_low) + ['High'] * len(wp_high),
    'Water_Productivity': list(wp_low) + list(wp_high)
})

sns.boxplot(x='Enforcement', y='Water_Productivity', data=wp_data)
plt.xlabel('Groundwater Quota Enforcement')
plt.ylabel('Water Productivity (t/ha per m3)')
plt.title('Water Productivity by Groundwater Quota Enforcement Status')
plt.tight_layout()
plt.savefig('report/images/water_productivity_by_enforcement.png', dpi=300, bbox_inches='tight')
print("Saved water_productivity_by_enforcement.png")

# 8. Policy simulation: What if all plots had high enforcement?
print("\n=== Policy Simulation ===")
# Predict yields under high enforcement for all plots
# Using the regression model to predict counterfactual
df_high = df.copy()
df_high['high_enforcement'] = 1  # Counterfactual: all plots have high enforcement

df_low = df.copy()
df_low['high_enforcement'] = 0  # Counterfactual: all plots have low enforcement

# Predict yields using the regression model
y_pred_high = model_ate.predict(df_high)
y_pred_low = model_ate.predict(df_low)

# Calculate expected gains
expected_gain = y_pred_high.mean() - y_pred_low.mean()
expected_percent_gain = (expected_gain / y_pred_low.mean()) * 100

print(f"Current average yield: {df['yield_t_ha'].mean():.3f} t/ha")
print(f"Predicted yield with universal high enforcement: {y_pred_high.mean():.3f} t/ha")
print(f"Predicted yield with universal low enforcement: {y_pred_low.mean():.3f} t/ha")
print(f"Expected gain from universal high enforcement: {expected_gain:.3f} t/ha ({expected_percent_gain:.1f}% increase)")

# Save policy simulation results
policy_results = pd.DataFrame({
    'Scenario': ['Current', 'Universal High Enforcement', 'Universal Low Enforcement'],
    'Predicted_Yield': [df['yield_t_ha'].mean(), y_pred_high.mean(), y_pred_low.mean()],
    'Gain_vs_Current': [0, y_pred_high.mean() - df['yield_t_ha'].mean(), y_pred_low.mean() - df['yield_t_ha'].mean()]
})
policy_results.to_csv('outputs/policy_simulation.csv', index=False)
print("\nPolicy simulation results saved to outputs/policy_simulation.csv")

print("\n=== Irrigation Program Analysis Complete ===")