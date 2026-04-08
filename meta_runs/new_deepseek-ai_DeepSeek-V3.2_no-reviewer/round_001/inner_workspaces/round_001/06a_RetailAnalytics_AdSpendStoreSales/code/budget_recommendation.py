import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read processed data
df = pd.read_csv('../outputs/processed_data.csv')
print("Data loaded. Shape:", df.shape)

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Sort by store and date
df = df.sort_values(['store_id', 'date'])

# Create lagged sales
df['lag_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)

# Remove first month for each store (no lag)
df_clean = df.dropna(subset=['lag_sales']).copy()

# Calculate year-over-year growth for better ROAS calculation
# Since we have 3 years of data, we can compare same month year-over-year
df_clean['month_year'] = df_clean['date'].dt.strftime('%m-%Y')
df_clean['prev_year_sales'] = df_clean.groupby(['store_id', 'month'])['sales_revenue_usd'].shift(12)

# Calculate YoY incremental sales
df_clean['yoy_incremental'] = df_clean['sales_revenue_usd'] - df_clean['prev_year_sales']

# Calculate YoY ROAS (only where we have prev year data)
df_yoy = df_clean.dropna(subset=['prev_year_sales']).copy()
df_yoy['yoy_roas'] = df_yoy['yoy_incremental'] / df_yoy['ad_spend_usd']

# Remove extreme outliers for YoY ROAS
yoy_roas_q1 = df_yoy['yoy_roas'].quantile(0.05)
yoy_roas_q99 = df_yoy['yoy_roas'].quantile(0.95)
df_yoy_filtered = df_yoy[(df_yoy['yoy_roas'] >= yoy_roas_q1) & (df_yoy['yoy_roas'] <= yoy_roas_q99)].copy()

print(f"\nYear-over-Year ROAS Statistics:")
print(f"Mean YoY ROAS: {df_yoy_filtered['yoy_roas'].mean():.2f}")
print(f"Median YoY ROAS: {df_yoy_filtered['yoy_roas'].median():.2f}")
print(f"Std YoY ROAS: {df_yoy_filtered['yoy_roas'].std():.2f}")
print(f"Number of observations: {len(df_yoy_filtered)}")

# Calculate store-level performance metrics
store_performance = df_yoy_filtered.groupby('store_id').agg({
    'yoy_roas': ['mean', 'std', 'count'],
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'foot_traffic': 'mean',
    'local_population': 'mean',
    'competitor_count': 'mean'
}).round(2)

store_performance.columns = ['_'.join(col).strip() for col in store_performance.columns.values]
store_performance = store_performance.reset_index()
store_performance.rename(columns={
    'yoy_roas_mean': 'avg_roas',
    'yoy_roas_std': 'roas_std',
    'yoy_roas_count': 'obs_count',
    'sales_revenue_usd_mean': 'avg_sales',
    'ad_spend_usd_mean': 'avg_ad_spend',
    'foot_traffic_mean': 'avg_traffic',
    'local_population_mean': 'avg_population',
    'competitor_count_mean': 'avg_competitors'
}, inplace=True)

print(f"\nStore performance metrics calculated for {len(store_performance)} stores")

# Calculate current policy parameters
current_ad_ratio = df_clean['ad_spend_usd'].sum() / df_clean['lag_sales'].sum()
print(f"\nCurrent ad-to-sales ratio: {current_ad_ratio:.4f} ({current_ad_ratio*100:.2f}%)")

# Get the most recent month data for each store
last_month_data = df_clean.sort_values(['store_id', 'date']).groupby('store_id').tail(1)

# Merge with performance metrics
budget_df = last_month_data.merge(store_performance[['store_id', 'avg_roas', 'roas_std', 'obs_count']], 
                                  on='store_id', how='left')

# Fill missing ROAS with overall average
overall_avg_roas = store_performance['avg_roas'].mean()
budget_df['avg_roas'].fillna(overall_avg_roas, inplace=True)
budget_df['roas_std'].fillna(store_performance['roas_std'].mean(), inplace=True)
budget_df['obs_count'].fillna(store_performance['obs_count'].median(), inplace=True)

# Calculate current policy budget for each store
budget_df['current_policy_budget'] = budget_df['lag_sales'] * current_ad_ratio

# Calculate total current budget
total_current_budget = budget_df['current_policy_budget'].sum()
print(f"Total current policy budget: ${total_current_budget:,.2f}")

# Strategy 1: Performance-weighted allocation
# Weight stores by their ROAS (higher ROAS gets more budget)
# But we need to consider risk (ROAS standard deviation)
budget_df['roas_score'] = budget_df['avg_roas'] / budget_df['roas_std'].clip(lower=0.1)
budget_df['roas_score'] = budget_df['roas_score'].clip(lower=0, upper=10)  # Cap extreme values

# Normalize scores to sum to 1
budget_df['performance_weight'] = budget_df['roas_score'] / budget_df['roas_score'].sum()
budget_df['performance_budget'] = budget_df['performance_weight'] * total_current_budget

# Strategy 2: Equal allocation (baseline)
budget_df['equal_budget'] = total_current_budget / len(budget_df)

# Strategy 3: Hybrid approach (50% performance, 50% equal)
budget_df['hybrid_budget'] = 0.5 * budget_df['performance_budget'] + 0.5 * budget_df['equal_budget']

# Strategy 4: Sales-weighted allocation (similar to current but with adjustment)
budget_df['sales_weight'] = budget_df['lag_sales'] / budget_df['lag_sales'].sum()
budget_df['sales_weighted_budget'] = budget_df['sales_weight'] * total_current_budget

# Calculate changes from current policy
budget_df['perf_change_pct'] = (budget_df['performance_budget'] - budget_df['current_policy_budget']) / budget_df['current_policy_budget'] * 100
budget_df['hybrid_change_pct'] = (budget_df['hybrid_budget'] - budget_df['current_policy_budget']) / budget_df['current_policy_budget'] * 100

print(f"\nBudget Allocation Summary:")
print(f"Current policy range: ${budget_df['current_policy_budget'].min():,.2f} to ${budget_df['current_policy_budget'].max():,.2f}")
print(f"Performance-based range: ${budget_df['performance_budget'].min():,.2f} to ${budget_df['performance_budget'].max():,.2f}")
print(f"Hybrid range: ${budget_df['hybrid_budget'].min():,.2f} to ${budget_df['hybrid_budget'].max():,.2f}")

print(f"\nAverage change from current policy:")
print(f"Performance-based: {budget_df['perf_change_pct'].mean():.1f}%")
print(f"Hybrid: {budget_df['hybrid_change_pct'].mean():.1f}%")

# Identify stores that would see largest changes
budget_df_sorted = budget_df.sort_values('perf_change_pct', ascending=False)
print(f"\nTop 5 stores with largest budget INCREASES under performance-based allocation:")
for i, row in budget_df_sorted.head().iterrows():
    print(f"Store {row['store_id']}: {row['perf_change_pct']:.1f}% change (ROAS: {row['avg_roas']:.2f})")

print(f"\nTop 5 stores with largest budget DECREASES under performance-based allocation:")
for i, row in budget_df_sorted.tail().iterrows():
    print(f"Store {row['store_id']}: {row['perf_change_pct']:.1f}% change (ROAS: {row['avg_roas']:.2f})")

# Monthly budget planning
# Create monthly allocation based on historical patterns
monthly_pattern = df_clean.groupby('month').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'is_holiday_month': 'mean'
}).reset_index()

monthly_pattern['seasonality_factor'] = monthly_pattern['ad_spend_usd'] / monthly_pattern['ad_spend_usd'].mean()

print(f"\nMonthly Seasonality Factors:")
for _, row in monthly_pattern.iterrows():
    holiday_flag = "(Holiday)" if row['is_holiday_month'] > 0.5 else ""
    print(f"Month {row['month']}: {row['seasonality_factor']:.3f} {holiday_flag}")

# Create monthly budget plan using hybrid strategy
monthly_budget_plan = pd.DataFrame()
for month in range(1, 13):
    seasonality = monthly_pattern[monthly_pattern['month'] == month]['seasonality_factor'].values[0]
    month_budget = budget_df.copy()
    month_budget['month'] = month
    month_budget['seasonality_factor'] = seasonality
    month_budget['monthly_budget'] = month_budget['hybrid_budget'] * seasonality
    
    monthly_budget_plan = pd.concat([monthly_budget_plan, month_budget])

# Calculate total annual budget by strategy
total_performance_budget = budget_df['performance_budget'].sum() * 12  # Approximate annual
total_hybrid_budget = budget_df['hybrid_budget'].sum() * 12
total_current_annual = budget_df['current_policy_budget'].sum() * 12

print(f"\nAnnual Budget Totals:")
print(f"Current policy: ${total_current_annual:,.2f}")
print(f"Performance-based: ${total_performance_budget:,.2f}")
print(f"Hybrid: ${total_hybrid_budget:,.2f}")

# Create visualizations
os.makedirs('../report/images', exist_ok=True)

# Plot 1: Store ROAS distribution
plt.figure(figsize=(12, 6))
plt.hist(store_performance['avg_roas'], bins=30, edgecolor='black', alpha=0.7)
plt.axvline(store_performance['avg_roas'].mean(), color='red', 
            linestyle='--', linewidth=2, label=f'Mean: {store_performance["avg_roas"].mean():.2f}')
plt.xlabel('Average Year-over-Year ROAS')
plt.ylabel('Number of Stores')
plt.title('Distribution of Store-Level Return on Ad Spend (ROAS)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('../report/images/store_roas_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Budget allocation comparison
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Current vs Performance budget
axes[0].scatter(budget_df['current_policy_budget'], budget_df['performance_budget'], alpha=0.6)
axes[0].plot([budget_df['current_policy_budget'].min(), budget_df['current_policy_budget'].max()],
             [budget_df['current_policy_budget'].min(), budget_df['current_policy_budget'].max()], 
             'r--', label='No Change')
axes[0].set_xlabel('Current Policy Budget ($)')
axes[0].set_ylabel('Performance-Based Budget ($)')
axes[0].set_title('Current vs Performance-Based Budget Allocation')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# ROAS vs Budget Change
axes[1].scatter(budget_df['avg_roas'], budget_df['perf_change_pct'], alpha=0.6)
axes[1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[1].set_xlabel('Average ROAS')
axes[1].set_ylabel('Budget Change (%)')
axes[1].set_title('ROAS vs Budget Change (Performance-Based)')
axes[1].grid(True, alpha=0.3)

# Monthly seasonality
axes[2].bar(monthly_pattern['month'], monthly_pattern['seasonality_factor'], 
            color=['orange' if h > 0.5 else 'blue' for h in monthly_pattern['is_holiday_month']])
axes[2].set_xlabel('Month')
axes[2].set_ylabel('Seasonality Factor')
axes[2].set_title('Monthly Ad Spend Seasonality (Orange = Holiday Months)')
axes[2].set_xticks(range(1, 13))
axes[2].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../report/images/budget_allocation_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Store clustering by performance
plt.figure(figsize=(10, 6))
plt.scatter(budget_df['avg_roas'], budget_df['roas_std'], 
            c=budget_df['perf_change_pct'], cmap='RdYlGn', 
            alpha=0.7, s=50, edgecolors='black')
plt.colorbar(label='Budget Change %')
plt.xlabel('Average ROAS')
plt.ylabel('ROAS Standard Deviation (Risk)')
plt.title('Store Performance Clustering: ROAS vs Risk (Color = Budget Change)')
plt.grid(True, alpha=0.3)
plt.savefig('../report/images/store_performance_clustering.png', dpi=300, bbox_inches='tight')
plt.close()

# Save detailed recommendations
budget_recommendations = budget_df[[
    'store_id', 'date', 'sales_revenue_usd', 'lag_sales', 'avg_roas', 'roas_std',
    'current_policy_budget', 'performance_budget', 'equal_budget', 'hybrid_budget',
    'perf_change_pct', 'hybrid_change_pct'
]].copy()

budget_recommendations.to_csv('../outputs/detailed_budget_recommendations.csv', index=False)

# Save monthly budget plan
monthly_budget_plan[['store_id', 'month', 'seasonality_factor', 'monthly_budget']].to_csv(
    '../outputs/monthly_budget_plan.csv', index=False)

# Save summary statistics
summary_stats = {
    'current_ad_ratio': current_ad_ratio,
    'overall_avg_roas': overall_avg_roas,
    'total_current_annual_budget': total_current_annual,
    'total_performance_annual_budget': total_performance_budget,
    'total_hybrid_annual_budget': total_hybrid_budget,
    'avg_budget_change_performance': budget_df['perf_change_pct'].mean(),
    'avg_budget_change_hybrid': budget_df['hybrid_change_pct'].mean(),
    'stores_with_roas_above_1': (store_performance['avg_roas'] > 1).sum(),
    'stores_with_roas_below_0': (store_performance['avg_roas'] < 0).sum()
}

summary_df = pd.DataFrame([summary_stats])
summary_df.to_csv('../outputs/summary_statistics.csv', index=False)

print("\nBudget recommendation analysis completed!")
print("Detailed recommendations saved to outputs/")
print("Visualizations saved to report/images/")
