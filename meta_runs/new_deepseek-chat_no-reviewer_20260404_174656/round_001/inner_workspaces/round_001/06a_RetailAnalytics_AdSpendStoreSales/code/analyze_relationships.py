import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

# Read the data with date column
df = pd.read_csv('../outputs/store_monthly_sales_with_date.csv')
df['date'] = pd.to_datetime(df['date'])

print("=== DATA OVERVIEW ===")
print(f"Total observations: {len(df)}")
print(f"Time period: {df['date'].min()} to {df['date'].max()}")
print(f"Number of stores: {df['store_id'].nunique()}")

# Calculate key metrics
print("\n=== KEY METRICS ===")
total_sales = df['sales_revenue_usd'].sum()
total_ad_spend = df['ad_spend_usd'].sum()
overall_roi = (total_sales - total_ad_spend) / total_ad_spend
print(f"Total sales revenue: ${total_sales:,.2f}")
print(f"Total ad spend: ${total_ad_spend:,.2f}")
print(f"Overall ROI (simplified): {overall_roi:.2f} or {overall_roi*100:.1f}%")

# Calculate store-level averages
store_stats = df.groupby('store_id').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'foot_traffic': 'mean',
    'local_population': 'mean',
    'competitor_count': 'mean'
}).reset_index()
store_stats['sales_to_ad_ratio'] = store_stats['sales_revenue_usd'] / store_stats['ad_spend_usd']

print("\n=== STORE-LEVEL STATISTICS ===")
print(f"Average monthly sales per store: ${store_stats['sales_revenue_usd'].mean():,.2f}")
print(f"Average monthly ad spend per store: ${store_stats['ad_spend_usd'].mean():,.2f}")
print(f"Average sales-to-ad ratio: {store_stats['sales_to_ad_ratio'].mean():.2f}")
print(f"Range of sales-to-ad ratios: {store_stats['sales_to_ad_ratio'].min():.2f} to {store_stats['sales_to_ad_ratio'].max():.2f}")

# Time series analysis
print("\n=== TIME SERIES ANALYSIS ===")
monthly_agg = df.groupby('date').agg({
    'sales_revenue_usd': 'sum',
    'ad_spend_usd': 'sum',
    'foot_traffic': 'sum',
    'is_holiday_month': 'mean'
}).reset_index()
monthly_agg['roi'] = monthly_agg['sales_revenue_usd'] / monthly_agg['ad_spend_usd']

print(f"Average monthly ROI (aggregate): {monthly_agg['roi'].mean():.2f}")
print(f"Holiday months ROI: {monthly_agg[monthly_agg['is_holiday_month'] > 0.5]['roi'].mean():.2f}")
print(f"Non-holiday months ROI: {monthly_agg[monthly_agg['is_holiday_month'] <= 0.5]['roi'].mean():.2f}")

# Create lagged variables for policy analysis
df = df.sort_values(['store_id', 'date'])
df['lag_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df['lag_ad_spend'] = df.groupby('store_id')['ad_spend_usd'].shift(1)

# Calculate the policy relationship: ad_spend = share * lag_sales
# We need to estimate the share parameter from the data
df_policy = df.dropna(subset=['lag_sales', 'ad_spend_usd'])

# Simple linear regression to estimate policy share
X = df_policy['lag_sales'].values.reshape(-1, 1)
y = df_policy['ad_spend_usd'].values
model = LinearRegression()
model.fit(X, y)
policy_share = model.coef_[0]
print(f"\n=== POLICY ANALYSIS ===")
print(f"Estimated policy share (ad_spend = share * lag_sales): {policy_share:.6f}")
print(f"Intercept: {model.intercept_:.2f}")
print(f"R-squared: {model.score(X, y):.4f}")

# Check if policy is consistent across stores
store_shares = []
for store_id in df['store_id'].unique():
    store_data = df[df['store_id'] == store_id].dropna(subset=['lag_sales', 'ad_spend_usd'])
    if len(store_data) > 10:  # Need enough data
        X_store = store_data['lag_sales'].values.reshape(-1, 1)
        y_store = store_data['ad_spend_usd'].values
        model_store = LinearRegression()
        model_store.fit(X_store, y_store)
        store_shares.append({
            'store_id': store_id,
            'share': model_store.coef_[0],
            'r2': model_store.score(X_store, y_store)
        })

store_shares_df = pd.DataFrame(store_shares)
print(f"\nStore-level policy share statistics:")
print(f"Mean share: {store_shares_df['share'].mean():.6f}")
print(f"Std of shares: {store_shares_df['share'].std():.6f}")
print(f"Min share: {store_shares_df['share'].min():.6f}")
print(f"Max share: {store_shares_df['share'].max():.6f}")

# Save store shares for later use
store_shares_df.to_csv('../outputs/store_policy_shares.csv', index=False)

print("\nAnalysis complete. Data saved to outputs/store_policy_shares.csv")