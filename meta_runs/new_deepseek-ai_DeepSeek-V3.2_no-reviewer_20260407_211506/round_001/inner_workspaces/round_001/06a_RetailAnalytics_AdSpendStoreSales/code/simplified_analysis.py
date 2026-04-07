import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("=== Retail Analytics: Ad Spend Budget Planning ===\n")

# Read and prepare data
df = pd.read_csv('../data/store_monthly_sales.csv')
print(f"Dataset shape: {df.shape}")
print(f"Stores: {df['store_id'].nunique()}, Months per store: {len(df)/df['store_id'].nunique():.0f}")

# Create date column with proper format
df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2) + '-01')
df = df.sort_values(['store_id', 'date'])

# Create lagged sales for policy analysis
df['lag_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df_clean = df.dropna(subset=['lag_sales']).copy()

# 1. Analyze current RET-ADV-ROLL policy
current_ratio = df_clean['ad_spend_usd'].sum() / df_clean['lag_sales'].sum()
print(f"\n1. CURRENT POLICY ANALYSIS")
print(f"Current ad-to-sales ratio: {current_ratio:.4f} ({current_ratio*100:.2f}%)")
print(f"Interpretation: Stores spend {current_ratio*100:.2f}% of prior month's sales on advertising")

# 2. Calculate basic effectiveness metric
df_clean['sales_growth'] = df_clean['sales_revenue_usd'] - df_clean['lag_sales']
df_clean['ad_effectiveness'] = df_clean['sales_growth'] / df_clean['ad_spend_usd']

# Filter outliers
def filter_outliers(series):
    q1 = series.quantile(0.05)
    q3 = series.quantile(0.95)
    return series[(series >= q1) & (series <= q3)]

effectiveness_filtered = filter_outliers(df_clean['ad_effectiveness'])
print(f"\n2. AD EFFECTIVENESS")
print(f"Ad effectiveness (sales growth per $1 ad spend):")
print(f"  Mean: {effectiveness_filtered.mean():.2f}")
print(f"  Median: {effectiveness_filtered.median():.2f}")
print(f"  Positive effectiveness: {(effectiveness_filtered > 0).sum() / len(effectiveness_filtered)*100:.1f}% of months")

# Store-level effectiveness
store_effectiveness = df_clean.groupby('store_id').apply(
    lambda x: filter_outliers(x['ad_effectiveness']).mean(), include_groups=False
).reset_index(name='avg_effectiveness')

# 3. Seasonal patterns
print(f"\n3. SEASONALITY ANALYSIS")

monthly_pattern = df_clean.groupby('month').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'is_holiday_month': 'mean'
}).reset_index()

monthly_pattern['sales_seasonality'] = monthly_pattern['sales_revenue_usd'] / monthly_pattern['sales_revenue_usd'].mean()
monthly_pattern['ad_seasonality'] = monthly_pattern['ad_spend_usd'] / monthly_pattern['ad_spend_usd'].mean()

print("Monthly patterns (1.0 = average):")
for _, row in monthly_pattern.iterrows():
    holiday = "*HOLIDAY*" if row['is_holiday_month'] > 0.5 else ""
    print(f"  Month {row['month']:2.0f}: Sales {row['sales_seasonality']:.3f}, Ad Spend {row['ad_seasonality']:.3f} {holiday}")

# 4. Store segmentation
print(f"\n4. STORE SEGMENTATION")

# Get store averages
store_avg = df_clean.groupby('store_id').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'foot_traffic': 'mean'
}).reset_index()

store_avg = store_avg.merge(store_effectiveness, on='store_id')
store_avg['sales_rank'] = store_avg['sales_revenue_usd'].rank(pct=True)
store_avg['effectiveness_rank'] = store_avg['avg_effectiveness'].rank(pct=True)

# Create segments
conditions = [
    (store_avg['sales_rank'] >= 0.7) & (store_avg['effectiveness_rank'] >= 0.7),
    (store_avg['sales_rank'] >= 0.7) & (store_avg['effectiveness_rank'] < 0.7),
    (store_avg['sales_rank'] < 0.7) & (store_avg['effectiveness_rank'] >= 0.7),
    (store_avg['sales_rank'] < 0.7) & (store_avg['effectiveness_rank'] < 0.7)
]
choices = ['High Potential', 'Large but Inefficient', 'Small but Efficient', 'Low Priority']
store_avg['segment'] = np.select(conditions, choices, default='Other')

segment_counts = store_avg['segment'].value_counts()
print("Store segments:")
for segment, count in segment_counts.items():
    print(f"  {segment}: {count} stores ({count/len(store_avg)*100:.1f}%)")

# 5. Budget recommendations
print(f"\n5. BUDGET RECOMMENDATIONS")

# Get latest month data
latest_data = df_clean.sort_values(['store_id', 'date']).groupby('store_id').tail(1)
budget_df = latest_data.merge(store_avg[['store_id', 'segment', 'avg_effectiveness']], on='store_id')

# Current policy budget
budget_df['current_budget'] = budget_df['lag_sales'] * current_ratio
total_current_budget = budget_df['current_budget'].sum()
print(f"Total monthly budget under current policy: ${total_current_budget:,.2f}")

# Simple performance-based allocation
# Use absolute value of effectiveness for weighting (treat all as potentially effective)
budget_df['performance_weight'] = (budget_df['avg_effectiveness'] - budget_df['avg_effectiveness'].min() + 0.1)
budget_df['performance_weight'] = budget_df['performance_weight'] / budget_df['performance_weight'].sum()
budget_df['performance_budget'] = budget_df['performance_weight'] * total_current_budget

# Hybrid allocation (70% current, 30% performance)
budget_df['hybrid_budget'] = 0.7 * budget_df['current_budget'] + 0.3 * budget_df['performance_budget']

print(f"\nRecommended allocation strategy: Hybrid (70% current policy + 30% performance-based)")
print(f"Rationale: Balances stability of current policy with performance optimization")

# 6. Monthly budget plan
print(f"\n6. MONTHLY BUDGET PLAN")

monthly_budget = pd.DataFrame()
for month in range(1, 13):
    seasonality = monthly_pattern[monthly_pattern['month'] == month]['ad_seasonality'].values[0]
    month_data = budget_df.copy()
    month_data['month'] = month
    month_data['monthly_budget'] = month_data['hybrid_budget'] * seasonality
    monthly_budget = pd.concat([monthly_budget, month_data])

# Calculate totals
annual_total = monthly_budget['monthly_budget'].sum()
monthly_totals = monthly_budget.groupby('month')['monthly_budget'].sum()

print(f"Annual advertising budget: ${annual_total:,.2f}")
print(f"Average monthly budget: ${monthly_totals.mean():,.2f}")
print(f"\nMonthly budget distribution:")
for month, total in monthly_totals.items():
    holiday = "(Holiday)" if monthly_pattern[monthly_pattern['month'] == month]['is_holiday_month'].values[0] > 0.5 else ""
    print(f"  Month {month:2.0f}: ${total:,.2f} {holiday}")

# 7. Create visualizations
print(f"\n7. GENERATING VISUALIZATIONS...")
os.makedirs('../report/images', exist_ok=True)

# Plot 1: Store segments
plt.figure(figsize=(10, 6))
colors = {'High Potential': 'green', 'Large but Inefficient': 'orange', 
          'Small but Efficient': 'blue', 'Low Priority': 'red'}

for segment in colors.keys():
    segment_data = store_avg[store_avg['segment'] == segment]
    plt.scatter(segment_data['sales_rank'], segment_data['effectiveness_rank'], 
                label=segment, color=colors[segment], alpha=0.7, s=50)

plt.xlabel('Sales Rank (Percentile)')
plt.ylabel('Ad Effectiveness Rank (Percentile)')
plt.title('Store Segmentation for Budget Allocation')
plt.axhline(y=0.7, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=0.7, color='gray', linestyle='--', alpha=0.5)
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('../report/images/store_segmentation_final.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Monthly seasonality
fig, ax1 = plt.subplots(figsize=(12, 6))

months = monthly_pattern['month']
ax1.bar(months - 0.2, monthly_pattern['sales_seasonality'], width=0.4, 
        label='Sales Seasonality', alpha=0.7, color='blue')
ax1.bar(months + 0.2, monthly_pattern['ad_seasonality'], width=0.4,
        label='Ad Spend Seasonality', alpha=0.7, color='orange')

# Highlight holiday months
holiday_months = monthly_pattern[monthly_pattern['is_holiday_month'] > 0.5]['month']
for month in holiday_months:
    ax1.axvspan(month - 0.5, month + 0.5, alpha=0.2, color='red')

ax1.set_xlabel('Month')
ax1.set_ylabel('Seasonality Factor (1.0 = Average)')
ax1.set_title('Monthly Seasonality Patterns (Red = Holiday Months)')
ax1.set_xticks(range(1, 13))
ax1.legend()
ax1.grid(True, alpha=0.3, axis='y')
plt.savefig('../report/images/monthly_seasonality_final.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Budget allocation
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Current vs Hybrid budget
axes[0].scatter(budget_df['current_budget'], budget_df['hybrid_budget'], alpha=0.6)
axes[0].plot([budget_df['current_budget'].min(), budget_df['current_budget'].max()],
             [budget_df['current_budget'].min(), budget_df['current_budget'].max()], 
             'r--', label='No Change', linewidth=2)
axes[0].set_xlabel('Current Policy Budget ($)')
axes[0].set_ylabel('Hybrid Budget ($)')
axes[0].set_title('Hybrid Allocation vs Current Policy')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Monthly budget distribution
axes[1].bar(monthly_totals.index, monthly_totals.values, 
            color=['red' if m in [1, 11, 12] else 'blue' for m in monthly_totals.index])
axes[1].set_xlabel('Month')
axes[1].set_ylabel('Total Monthly Budget ($)')
axes[1].set_title('Monthly Budget Distribution (Red = Holiday Months)')
axes[1].set_xticks(range(1, 13))
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../report/images/budget_analysis_final.png', dpi=300, bbox_inches='tight')
plt.close()

# 8. Save outputs
print(f"\n8. SAVING OUTPUTS...")

# Save store recommendations
store_recommendations = budget_df[[
    'store_id', 'segment', 'avg_effectiveness',
    'current_budget', 'hybrid_budget'
]].copy()
store_recommendations['budget_change_pct'] = (store_recommendations['hybrid_budget'] - store_recommendations['current_budget']) / store_recommendations['current_budget'] * 100

store_recommendations.to_csv('../outputs/store_recommendations_final.csv', index=False)

# Save monthly plan summary
monthly_plan_summary = monthly_budget.groupby('month').agg({
    'monthly_budget': 'sum',
    'store_id': 'count'
}).reset_index()
monthly_plan_summary.rename(columns={'store_id': 'store_count'}, inplace=True)
monthly_plan_summary.to_csv('../outputs/monthly_plan_summary_final.csv', index=False)

# Save key metrics
key_metrics = {
    'current_ad_ratio': current_ratio,
    'total_monthly_budget': total_current_budget,
    'annual_budget': annual_total,
    'avg_monthly_budget': monthly_totals.mean(),
    'stores_high_potential': (store_avg['segment'] == 'High Potential').sum(),
    'pct_positive_effectiveness': (effectiveness_filtered > 0).sum() / len(effectiveness_filtered) * 100,
    'recommended_strategy': 'Hybrid (70% current + 30% performance)'
}

metrics_df = pd.DataFrame([key_metrics])
metrics_df.to_csv('../outputs/key_metrics_final.csv', index=False)

print(f"\n=== ANALYSIS COMPLETE ===")
print(f"Outputs saved to: outputs/")
print(f"Visualizations saved to: report/images/")
print(f"\nKEY RECOMMENDATIONS:")
print(f"1. Adopt hybrid budget allocation: 70% current policy + 30% performance-based")
print(f"2. Annual budget: ${annual_total:,.0f} (${monthly_totals.mean():,.0f} monthly average)")
print(f"3. Focus investment on {segment_counts['High Potential']} High Potential stores")
print(f"4. Adjust for seasonality: Higher budgets in holiday months (Jan, Nov, Dec)")
print(f"5. Current ad-to-sales ratio of {current_ratio*100:.2f}% appears reasonable")
