import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv('data/store_monthly_sales.csv')

# Sort by store and time
df = df.sort_values(['store_id', 'year', 'month'])

# Calculate prior month sales
df['prior_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)

# Check policy RET-ADV-ROLL: ad_spend_usd = alpha * prior_sales
df_policy = df.dropna(subset=['prior_sales']).copy()
df_policy['alpha'] = df_policy['ad_spend_usd'] / df_policy['prior_sales']

print("Summary of alpha (ad_spend / prior_sales):")
print(df_policy['alpha'].describe())

# Plot alpha distribution
plt.figure(figsize=(8, 5))
sns.histplot(df_policy['alpha'], bins=50, kde=True)
plt.title('Distribution of Ad Spend as Share of Prior Month Sales')
plt.xlabel('Alpha (Ad Spend / Prior Sales)')
plt.ylabel('Frequency')
plt.savefig('outputs/alpha_distribution.png')
plt.close()

# Basic EDA
print("\nBasic Statistics:")
print(df.describe())

# Correlation matrix
plt.figure(figsize=(10, 8))
sns.heatmap(df.corr(), annot=True, cmap='coolwarm', fmt='.2f')
plt.title('Correlation Matrix')
plt.savefig('outputs/correlation_matrix.png')
plt.close()

# Time series of total sales and ad spend
monthly_totals = df.groupby(['year', 'month'])[['sales_revenue_usd', 'ad_spend_usd']].sum().reset_index()
monthly_totals['time'] = monthly_totals['year'].astype(str) + '-' + monthly_totals['month'].astype(str).str.zfill(2)

fig, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(monthly_totals['time'], monthly_totals['sales_revenue_usd'], 'b-', label='Total Sales')
ax1.set_xlabel('Time')
ax1.set_ylabel('Total Sales (USD)', color='b')
ax1.tick_params('y', colors='b')
plt.xticks(rotation=45)

ax2 = ax1.twinx()
ax2.plot(monthly_totals['time'], monthly_totals['ad_spend_usd'], 'r-', label='Total Ad Spend')
ax2.set_ylabel('Total Ad Spend (USD)', color='r')
ax2.tick_params('y', colors='r')

plt.title('Total Monthly Sales and Ad Spend')
fig.tight_layout()
plt.savefig('outputs/time_series.png')
plt.close()
