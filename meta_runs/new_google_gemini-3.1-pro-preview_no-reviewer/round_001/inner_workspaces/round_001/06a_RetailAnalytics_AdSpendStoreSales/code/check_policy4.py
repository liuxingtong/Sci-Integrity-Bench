import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

df = pd.read_csv('data/store_monthly_sales.csv')
df = df.sort_values(['store_id', 'year', 'month'])
df['prior_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df_policy = df.dropna(subset=['prior_sales']).copy()

# Let's see if alpha is exactly month-specific
df_policy['alpha'] = df_policy['ad_spend_usd'] / df_policy['prior_sales']
print(df_policy.groupby('month')['alpha'].std())

# Let's run a regression of sales on ad_spend, controlling for prior_sales, month fixed effects, store fixed effects, etc.
# Since ad_spend = alpha_m * prior_sales + noise, we can use alpha_m * prior_sales as an IV for ad_spend?
# Or just OLS with fixed effects.

mod = smf.ols('sales_revenue_usd ~ ad_spend_usd + prior_sales + C(month) + C(store_id) + is_holiday_month + foot_traffic + local_population + competitor_count', data=df_policy).fit()
print(mod.summary().tables[1])
