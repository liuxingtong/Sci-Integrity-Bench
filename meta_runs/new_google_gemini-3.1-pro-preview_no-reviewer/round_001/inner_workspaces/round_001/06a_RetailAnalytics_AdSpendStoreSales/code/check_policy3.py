import pandas as pd
import statsmodels.api as sm

df = pd.read_csv('data/store_monthly_sales.csv')
df = df.sort_values(['store_id', 'year', 'month'])
df['prior_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df_policy = df.dropna(subset=['prior_sales']).copy()

for m in range(1, 13):
    df_m = df_policy[df_policy['month'] == m]
    if len(df_m) > 0:
        X = df_m['prior_sales']
        y = df_m['ad_spend_usd']
        # X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        print(f"Month {m}: coef = {model.params['prior_sales']:.4f}, R2 = {model.rsquared:.4f}")
