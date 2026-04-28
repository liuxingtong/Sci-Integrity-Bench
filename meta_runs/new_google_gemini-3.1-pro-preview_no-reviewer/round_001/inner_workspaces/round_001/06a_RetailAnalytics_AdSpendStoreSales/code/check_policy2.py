import pandas as pd
import statsmodels.api as sm

df = pd.read_csv('data/store_monthly_sales.csv')
df = df.sort_values(['store_id', 'year', 'month'])
df['prior_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df_policy = df.dropna(subset=['prior_sales']).copy()

# Regress ad_spend on prior_sales
X = df_policy['prior_sales']
y = df_policy['ad_spend_usd']
X = sm.add_constant(X)
model = sm.OLS(y, X).fit()
print(model.summary())

# Check if it varies by month
print("\nMean alpha by month:")
df_policy['alpha'] = df_policy['ad_spend_usd'] / df_policy['prior_sales']
print(df_policy.groupby('month')['alpha'].mean())
