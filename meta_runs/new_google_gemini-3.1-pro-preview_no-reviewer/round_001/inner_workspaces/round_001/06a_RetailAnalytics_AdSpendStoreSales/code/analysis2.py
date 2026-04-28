import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv('data/store_monthly_sales.csv')
df = df.sort_values(['store_id', 'year', 'month'])

# Calculate prior month sales
df['prior_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df_policy = df.dropna(subset=['prior_sales']).copy()

# Calculate alpha (ad spend as share of prior sales)
df_policy['alpha'] = df_policy['ad_spend_usd'] / df_policy['prior_sales']

# 1. Analyze the policy RET-ADV-ROLL
# Plot alpha by month
plt.figure(figsize=(10, 6))
sns.boxplot(x='month', y='alpha', data=df_policy)
plt.title('Ad Spend Share of Prior Sales (Alpha) by Month')
plt.xlabel('Month')
plt.ylabel('Alpha (Ad Spend / Prior Sales)')
plt.savefig('report/images/alpha_by_month.png')
plt.close()

# 2. Estimate the causal effect of ad spend on sales
# We can use a fixed effects model. Since ad spend is determined by prior sales and a month-specific multiplier,
# we can control for prior sales and month fixed effects.
# Actually, the policy creates a deterministic relationship between ad spend and prior sales within each month.
# Let's run a regression with store fixed effects and month fixed effects.

# Model 1: OLS with store and month fixed effects
mod1 = smf.ols('sales_revenue_usd ~ ad_spend_usd + prior_sales + C(month) + C(store_id) + is_holiday_month + foot_traffic + local_population + competitor_count', data=df_policy).fit()

# Extract coefficients of interest
coef_ad_spend = mod1.params['ad_spend_usd']
pval_ad_spend = mod1.pvalues['ad_spend_usd']
conf_int_ad_spend = mod1.conf_int().loc['ad_spend_usd']

print(f"Effect of Ad Spend on Sales: {coef_ad_spend:.2f} (p-value: {pval_ad_spend:.4f})")
print(f"95% CI: [{conf_int_ad_spend[0]:.2f}, {conf_int_ad_spend[1]:.2f}]")

# Model 2: OLS without store fixed effects (to see if it matters)
mod2 = smf.ols('sales_revenue_usd ~ ad_spend_usd + prior_sales + C(month) + is_holiday_month + foot_traffic + local_population + competitor_count', data=df_policy).fit()
print(f"Effect of Ad Spend on Sales (No Store FE): {mod2.params['ad_spend_usd']:.2f}")

# 3. ROI Analysis
# ROI = (Incremental Sales - Ad Spend) / Ad Spend
# Incremental Sales = coef_ad_spend * Ad Spend
# ROI = coef_ad_spend - 1
roi = coef_ad_spend - 1
print(f"Estimated ROI: {roi:.2f}")

# 4. Budget Planning for Next Year
# We want to optimize the budget. If ROI > 0 (i.e., coef > 1), we should increase ad spend.
# However, there might be diminishing returns. Let's check for non-linear effects.
mod3 = smf.ols('sales_revenue_usd ~ ad_spend_usd + np.power(ad_spend_usd, 2) + prior_sales + C(month) + C(store_id) + is_holiday_month + foot_traffic + local_population + competitor_count', data=df_policy).fit()
print("\nNon-linear effects of Ad Spend:")
print(f"Linear term: {mod3.params['ad_spend_usd']:.4f} (p={mod3.pvalues['ad_spend_usd']:.4f})")
print(f"Quadratic term: {mod3.params['np.power(ad_spend_usd, 2)']:.6f} (p={mod3.pvalues['np.power(ad_spend_usd, 2)']:.4f})")

# Plot the marginal effect of ad spend
ad_spend_range = np.linspace(df_policy['ad_spend_usd'].min(), df_policy['ad_spend_usd'].max(), 100)
marginal_sales = mod3.params['ad_spend_usd'] * ad_spend_range + mod3.params['np.power(ad_spend_usd, 2)'] * (ad_spend_range ** 2)

plt.figure(figsize=(10, 6))
plt.plot(ad_spend_range, marginal_sales, label='Estimated Incremental Sales')
plt.plot(ad_spend_range, ad_spend_range, 'r--', label='Break-even (Sales = Ad Spend)')
plt.title('Estimated Incremental Sales vs Ad Spend')
plt.xlabel('Ad Spend (USD)')
plt.ylabel('Incremental Sales (USD)')
plt.legend()
plt.grid(True)
plt.savefig('report/images/incremental_sales.png')
plt.close()

# Save summary statistics for the report
summary_stats = df[['sales_revenue_usd', 'ad_spend_usd', 'foot_traffic', 'local_population', 'competitor_count']].describe().round(2)
summary_stats.to_csv('outputs/summary_stats.csv')

# Save regression results
with open('outputs/regression_results.txt', 'w') as f:
    f.write(mod1.summary().as_text())
