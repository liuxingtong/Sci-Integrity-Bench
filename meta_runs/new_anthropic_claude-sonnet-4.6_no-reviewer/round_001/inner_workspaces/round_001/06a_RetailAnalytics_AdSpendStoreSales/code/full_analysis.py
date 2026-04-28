#!/usr/bin/env python3
"""
Retail Analytics: Ad Spend & Store Sales Analysis
Policy RET-ADV-ROLL: Monthly online ad budget = fixed share of prior-month same-store sales
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print('=== RETAIL ANALYTICS: AD SPEND & STORE SALES ===')
print('Loading data...')
df = pd.read_csv('data/store_monthly_sales.csv')
print(f'Shape: {df.shape}')
print(f'Columns: {df.columns.tolist()}')

# ============================================================
# 1. DATA PREPARATION
# ============================================================
print('\n--- Data Preparation ---')

# Parse date columns
if 'year' in df.columns and 'month' in df.columns:
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
elif 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month

df = df.sort_values(['store_id', 'date']).reset_index(drop=True)

print(f'Date range: {df["date"].min()} to {df["date"].max()}')
print(f'Unique stores: {df["store_id"].nunique()}')
print(f'Months per store (avg): {df.groupby("store_id").size().mean():.1f}')

# ============================================================
# 2. POLICY RET-ADV-ROLL IMPLEMENTATION
# ============================================================
print('\n--- Policy RET-ADV-ROLL Implementation ---')
# Policy: month-m ad budget = fixed_share * prior-month same-store sales
# Compute the implied share for each store-month
df = df.sort_values(['store_id', 'date'])
df['prev_month_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df['implied_share'] = df['ad_spend_usd'] / df['prev_month_sales']

# Compute the median implied share (the 'fixed share' in the policy)
median_share = df['implied_share'].median()
mean_share = df['implied_share'].mean()
print(f'Implied ad share (median): {median_share:.4f} ({median_share*100:.2f}%)')
print(f'Implied ad share (mean): {mean_share:.4f} ({mean_share*100:.2f}%)')

# ============================================================
# 3. DESCRIPTIVE STATISTICS
# ============================================================
print('\n--- Descriptive Statistics ---')
desc = df[['ad_spend_usd', 'sales_revenue_usd', 'foot_traffic', 'local_population', 'competitor_count']].describe()
print(desc)
desc.to_csv('outputs/descriptive_stats.csv')

# ============================================================
# 4. CORRELATION ANALYSIS
# ============================================================
print('\n--- Correlation Analysis ---')
corr_cols = ['ad_spend_usd', 'sales_revenue_usd', 'foot_traffic', 'local_population', 
             'competitor_count', 'is_holiday_month']
corr_matrix = df[corr_cols].corr()
print(corr_matrix)
corr_matrix.to_csv('outputs/correlation_matrix.csv')

# ============================================================
# 5. REGRESSION ANALYSIS
# ============================================================
print('\n--- Regression Analysis ---')

# Prepare features
feature_cols = ['ad_spend_usd', 'foot_traffic', 'local_population', 'competitor_count', 'is_holiday_month']
df_reg = df[feature_cols + ['sales_revenue_usd']].dropna()

X = df_reg[feature_cols].values
y = df_reg['sales_revenue_usd'].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

reg = LinearRegression()
reg.fit(X_scaled, y)
y_pred = reg.predict(X_scaled)

r2 = r2_score(y, y_pred)
rmse = np.sqrt(mean_squared_error(y, y_pred))
print(f'R²: {r2:.4f}')
print(f'RMSE: {rmse:.2f}')

coef_df = pd.DataFrame({'feature': feature_cols, 'coefficient': reg.coef_})
coef_df['abs_coef'] = coef_df['coefficient'].abs()
coef_df = coef_df.sort_values('abs_coef', ascending=False)
print('\nCoefficients (standardized):')
print(coef_df)
coef_df.to_csv('outputs/regression_coefficients.csv', index=False)

# ============================================================
# 6. AD SPEND ELASTICITY
# ============================================================
print('\n--- Ad Spend Elasticity ---')
# Log-log regression for elasticity
df_elas = df[['ad_spend_usd', 'sales_revenue_usd']].dropna()
df_elas = df_elas[(df_elas['ad_spend_usd'] > 0) & (df_elas['sales_revenue_usd'] > 0)]
log_ad = np.log(df_elas['ad_spend_usd'])
log_sales = np.log(df_elas['sales_revenue_usd'])
slope, intercept, r_value, p_value, std_err = stats.linregress(log_ad, log_sales)
print(f'Ad spend elasticity: {slope:.4f} (p={p_value:.4e})')
print(f'R² (log-log): {r_value**2:.4f}')

# ============================================================
# 7. STORE-LEVEL ANALYSIS
# ============================================================
print('\n--- Store-Level Analysis ---')
store_stats = df.groupby('store_id').agg(
    avg_ad_spend=('ad_spend_usd', 'mean'),
    avg_sales=('sales_revenue_usd', 'mean'),
    avg_traffic=('foot_traffic', 'mean'),
    total_months=('date', 'count'),
    avg_implied_share=('implied_share', 'mean')
).reset_index()
print(store_stats.describe())
store_stats.to_csv('outputs/store_level_stats.csv', index=False)

# ============================================================
# 8. MONTHLY SEASONALITY
# ============================================================
print('\n--- Monthly Seasonality ---')
monthly_avg = df.groupby('month').agg(
    avg_sales=('sales_revenue_usd', 'mean'),
    avg_ad_spend=('ad_spend_usd', 'mean'),
    avg_traffic=('foot_traffic', 'mean')
).reset_index()
print(monthly_avg)
monthly_avg.to_csv('outputs/monthly_seasonality.csv', index=False)

# ============================================================
# 9. BUDGET RECOMMENDATION (Policy RET-ADV-ROLL)
# ============================================================
print('\n--- Budget Recommendation ---')
# Use the most recent month's sales to project next year's budget
latest_month = df['date'].max()
latest_sales = df[df['date'] == latest_month].groupby('store_id')['sales_revenue_usd'].sum()

# Apply policy: next month budget = fixed_share * current_month_sales
# Use median implied share as the 'fixed share'
recommended_budget = latest_sales * median_share
total_recommended = recommended_budget.sum()
print(f'Latest month: {latest_month}')
print(f'Total recommended monthly budget (portfolio): ${total_recommended:,.2f}')
print(f'Annual budget projection: ${total_recommended * 12:,.2f}')

# Monthly budget by applying seasonality adjustment
monthly_index = monthly_avg.set_index('month')['avg_sales'] / monthly_avg['avg_sales'].mean()
annual_budget_by_month = {}
for m in range(1, 13):
    adj = monthly_index.get(m, 1.0)
    annual_budget_by_month[m] = total_recommended * adj

budget_df = pd.DataFrame(list(annual_budget_by_month.items()), columns=['month', 'recommended_budget'])
budget_df['month_name'] = pd.to_datetime(budget_df['month'], format='%m').dt.strftime('%b')
print('\nRecommended Monthly Budget (Portfolio):')
print(budget_df[['month_name', 'recommended_budget']].to_string(index=False))
budget_df.to_csv('outputs/recommended_monthly_budget.csv', index=False)

# Per-store budget
store_budget = df.groupby('store_id').apply(
    lambda x: x.nlargest(1, 'date')[['sales_revenue_usd']].values[0][0] * median_share
).reset_index()
store_budget.columns = ['store_id', 'recommended_monthly_budget']
store_budget['recommended_annual_budget'] = store_budget['recommended_monthly_budget'] * 12
store_budget.to_csv('outputs/per_store_budget.csv', index=False)
print(f'\nPer-store budget saved. Total stores: {len(store_budget)}')

print('\n=== ANALYSIS COMPLETE ===')
print('All outputs saved to outputs/ directory')
