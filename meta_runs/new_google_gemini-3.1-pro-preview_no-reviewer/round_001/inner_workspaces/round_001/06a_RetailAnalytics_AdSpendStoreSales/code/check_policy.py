import pandas as pd

df = pd.read_csv('data/store_monthly_sales.csv')
df = df.sort_values(['store_id', 'year', 'month'])
df['prior_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df_policy = df.dropna(subset=['prior_sales']).copy()
df_policy['alpha'] = df_policy['ad_spend_usd'] / df_policy['prior_sales']

store_alphas = df_policy.groupby('store_id')['alpha'].std()
print("Standard deviation of alpha per store:")
print(store_alphas.describe())

print("\nMean alpha per store:")
print(df_policy.groupby('store_id')['alpha'].mean().describe())
