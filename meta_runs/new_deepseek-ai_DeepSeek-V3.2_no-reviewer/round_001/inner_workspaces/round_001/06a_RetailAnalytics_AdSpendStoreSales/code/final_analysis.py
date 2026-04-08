import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("=== Retail Analytics: Ad Spend Budget Planning ===\n")

# Read and prepare data
df = pd.read_csv('../data/store_monthly_sales.csv')
print(f"Dataset shape: {df.shape}")
print(f"Stores: {df['store_id'].nunique()}, Months per store: {len(df)/df['store_id'].nunique():.0f}")

# Create date column
df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')
df = df.sort_values(['store_id', 'date'])

# Create lagged sales for policy analysis
df['lag_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df_clean = df.dropna(subset=['lag_sales']).copy()

# 1. Analyze current RET-ADV-ROLL policy
current_ratio = df_clean['ad_spend_usd'].sum() / df_clean['lag_sales'].sum()
print(f"\n1. CURRENT POLICY ANALYSIS")
print(f"Current ad-to-sales ratio: {current_ratio:.4f} ({current_ratio*100:.2f}%)")
print(f"Interpretation: Stores spend {current_ratio*100:.2f}% of prior month's sales on advertising")

# Calculate store-level ratios
store_ratios = df_clean.groupby('store_id').apply(
    lambda x: x['ad_spend_usd'].sum() / x['lag_sales'].sum(), include_groups=False
).reset_index(name='ad_ratio')

print(f"Store-level ratio statistics:")
print(f"  Mean: {store_ratios['ad_ratio'].mean():.4f}")
print(f"  Std: {store_ratios['ad_ratio'].std():.4f}")
print(f"  Min: {store_ratios['ad_ratio'].min():.4f}")
print(f"  Max: {store_ratios['ad_ratio'].max():.4f}")

# 2. Analyze ad effectiveness
print(f"\n2. AD EFFECTIVENESS ANALYSIS")

# Calculate monthly incremental sales (simplified)
df_clean['sales_growth'] = df_clean['sales_revenue_usd'] - df_clean['lag_sales']
df_clean['ad_effectiveness'] = df_clean['sales_growth'] / df_clean['ad_spend_usd']

# Remove extreme outliers
def filter_outliers(series):
    q1 = series.quantile(0.05)
    q3 = series.quantile(0.95)
    return series[(series >= q1) & (series <= q3)]

effectiveness_filtered = filter_outliers(df_clean['ad_effectiveness'])
print(f"Ad effectiveness (sales growth per $1 ad spend):")
print(f"  Mean: {effectiveness_filtered.mean():.2f}")
print(f"  Median: {effectiveness_filtered.median():.2f}")
print(f"  Positive effectiveness: {(effectiveness_filtered > 0).sum() / len(effectiveness_filtered)*100:.1f}% of months")

# Store-level effectiveness
store_effectiveness = df_clean.groupby('store_id')['ad_effectiveness'].apply(
    lambda x: filter_outliers(x).mean(), include_groups=False
).reset_index(name='avg_effectiveness')

print(f"\nStore-level effectiveness:")
print(f"  Best store: Store {store_effectiveness['avg_effectiveness'].idxmax()+1} ({store_effectiveness['avg_effectiveness'].max():.2f})")
print(f"  Worst store: Store {store_effectiveness['avg_effectiveness'].idxmin()+1} ({store_effectiveness['avg_effectiveness'].min():.2f})")
print(f"  Stores with positive effectiveness: {(store_effectiveness['avg_effectiveness'] > 0).sum()} out of {len(store_effectiveness)}")

# 3. Seasonal patterns
print(f"\n3. SEASONALITY ANALYSIS")

monthly_pattern = df_clean.groupby('month').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'is_holiday_month': 'mean',
    'foot_traffic': 'mean'
}).reset_index()

monthly_pattern['sales_seasonality'] = monthly_pattern['sales_revenue_usd'] / monthly_pattern['sales_revenue_usd'].mean()
monthly_pattern['ad_seasonality'] = monthly_pattern['ad_spend_usd'] / monthly_pattern['ad_spend_usd'].mean()

print("Monthly patterns (1.0 = average):")
for _, row in monthly_pattern.iterrows():
    holiday = "*HOLIDAY*" if row['is_holiday_month'] > 0.5 else ""
    print(f"  Month {row['month']:2.0f}: Sales {row['sales_seasonality']:.3f}, Ad Spend {row['ad_seasonality']:.3f} {holiday}")

# 4. Store clustering for budget allocation
print(f"\n4. STORE CLUSTERING FOR BUDGET ALLOCATION")

# Calculate store characteristics
store_stats = df_clean.groupby('store_id').agg({
    'sales_revenue_usd': ['mean', 'std'],
    'ad_spend_usd': 'mean',
    'foot_traffic': 'mean',
    'local_population': 'mean',
    'competitor_count': 'mean',
    'ad_effectiveness': lambda x: filter_outliers(x).mean()
}).round(2)

store_stats.columns = ['_'.join(col).strip() for col in store_stats.columns.values]
store_stats = store_stats.reset_index()

# Rename columns - handle the lambda column name
rename_dict = {
    'sales_revenue_usd_mean': 'avg_sales',
    'sales_revenue_usd_std': 'sales_std',
    'ad_spend_usd_mean': 'avg_ad_spend',
    'foot_traffic_mean': 'avg_traffic',
    'local_population_mean': 'avg_population',
    'competitor_count_mean': 'avg_competitors'
}

# Find the ad_effectiveness column (might have different name)
for col in store_stats.columns:
    if 'ad_effectiveness' in col:
        rename_dict[col] = 'ad_effectiveness'
        break

store_stats.rename(columns=rename_dict, inplace=True)

# Ensure ad_effectiveness column exists
if 'ad_effectiveness' not in store_stats.columns:
    # Calculate it directly
    store_effectiveness_calc = df_clean.groupby('store_id')['ad_effectiveness'].apply(
        lambda x: filter_outliers(x).mean(), include_groups=False
    ).reset_index(name='ad_effectiveness')
    store_stats = store_stats.merge(store_effectiveness_calc, on='store_id')

# Classify stores into tiers
store_stats['sales_rank'] = store_stats['avg_sales'].rank(pct=True)
store_stats['effectiveness_rank'] = store_stats['ad_effectiveness'].rank(pct=True)

# Create store segments
conditions = [
    (store_stats['sales_rank'] >= 0.7) & (store_stats['effectiveness_rank'] >= 0.7),
    (store_stats['sales_rank'] >= 0.7) & (store_stats['effectiveness_rank'] < 0.7),
    (store_stats['sales_rank'] < 0.7) & (store_stats['effectiveness_rank'] >= 0.7),
    (store_stats['sales_rank'] < 0.7) & (store_stats['effectiveness_rank'] < 0.7)
]
choices = ['High Potential', 'Large but Inefficient', 'Small but Efficient', 'Low Priority']
store_stats['segment'] = np.select(conditions, choices, default='Other')

segment_counts = store_stats['segment'].value_counts()
print("Store segments:")
for segment, count in segment_counts.items():
    print(f"  {segment}: {count} stores ({count/len(store_stats)*100:.1f}%)")

# 5. Budget recommendation strategies
print(f"\n5. BUDGET RECOMMENDATION STRATEGIES")

# Get latest month data for each store
latest_data = df_clean.sort_values(['store_id', 'date']).groupby('store_id').tail(1)
budget_df = latest_data.merge(store_stats[['store_id', 'segment', 'ad_effectiveness', 'sales_rank', 'effectiveness_rank']], 
                              on='store_id')

# Current policy budget
budget_df['current_budget'] = budget_df['lag_sales'] * current_ratio
total_current_budget = budget_df['current_budget'].sum()
print(f"Total monthly budget under current policy: ${total_current_budget:,.2f}")

# Strategy A: Segment-based allocation
segment_multipliers = {
    'High Potential': 1.5,      # Increase budget
    'Large but Inefficient': 0.8, # Reduce budget
    'Small but Efficient': 1.2,   # Slightly increase
    'Low Priority': 0.7          # Reduce budget
}

budget_df['segment_multiplier'] = budget_df['segment'].map(segment_multipliers)
budget_df['segment_budget'] = budget_df['current_budget'] * budget_df['segment_multiplier']

# Normalize to keep total budget same
segment_total = budget_df['segment_budget'].sum()
budget_df['segment_budget'] = budget_df['segment_budget'] * (total_current_budget / segment_total)

# Strategy B: Performance-weighted allocation
budget_df['performance_weight'] = budget_df['ad_effectiveness'].clip(lower=0)
budget_df['performance_weight'] = budget_df['performance_weight'] / budget_df['performance_weight'].sum()
budget_df['performance_budget'] = budget_df['performance_weight'] * total_current_budget

# Strategy C: Hybrid (50% current, 50% performance)
budget_df['hybrid_budget'] = 0.5 * budget_df['current_budget'] + 0.5 * budget_df['performance_budget']

print(f"\nBudget allocation strategies (monthly total: ${total_current_budget:,.2f}):")
print(f"  Current: Fixed {current_ratio*100:.2f}% of prior month sales")
print(f"  Segment-based: Adjusts based on store potential/performance")
print(f"  Performance-based: Allocates based on ad effectiveness")
print(f"  Hybrid: 50% current + 50% performance")

# Calculate changes
budget_df['segment_change_pct'] = (budget_df['segment_budget'] - budget_df['current_budget']) / budget_df['current_budget'] * 100
budget_df['performance_change_pct'] = (budget_df['performance_budget'] - budget_df['current_budget']) / budget_df['current_budget'] * 100
budget_df['hybrid_change_pct'] = (budget_df['hybrid_budget'] - budget_df['current_budget']) / budget_df['current_budget'] * 100

print(f"\nAverage budget changes:")
print(f"  Segment-based: {budget_df['segment_change_pct'].mean():.1f}%")
print(f"  Performance-based: {budget_df['performance_change_pct'].mean():.1f}%")
print(f"  Hybrid: {budget_df['hybrid_change_pct'].mean():.1f}%")

# 6. Monthly budget plan
print(f"\n6. MONTHLY BUDGET PLAN FOR NEXT YEAR")

monthly_budget = pd.DataFrame()
for month in range(1, 13):
    seasonality = monthly_pattern[monthly_pattern['month'] == month]['ad_seasonality'].values[0]
    month_data = budget_df.copy()
    month_data['month'] = month
    month_data['monthly_budget'] = month_data['hybrid_budget'] * seasonality
    monthly_budget = pd.concat([monthly_budget, month_data])

# Calculate annual totals
annual_total = monthly_budget['monthly_budget'].sum()
monthly_avg = monthly_budget.groupby('month')['monthly_budget'].sum().mean()

print(f"Annual advertising budget: ${annual_total:,.2f}")
print(f"Average monthly budget: ${monthly_avg:,.2f}")
print(f"\nMonthly budget distribution:")
monthly_totals = monthly_budget.groupby('month')['monthly_budget'].sum()
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
    segment_data = store_stats[store_stats['segment'] == segment]
    plt.scatter(segment_data['sales_rank'], segment_data['effectiveness_rank'], 
                label=segment, color=colors[segment], alpha=0.7, s=50)

plt.xlabel('Sales Rank (Percentile)')
plt.ylabel('Ad Effectiveness Rank (Percentile)')
plt.title('Store Segmentation for Budget Allocation')
plt.axhline(y=0.7, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=0.7, color='gray', linestyle='--', alpha=0.5)
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('../report/images/store_segmentation.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Monthly seasonality
fig, ax1 = plt.subplots(figsize=(12, 6))

months = monthly_pattern['month']
ax1.bar(months - 0.2, monthly_pattern['sales_seasonality'], width=0.4, 
        label='Sales Seasonality', alpha=0.7)
ax1.bar(months + 0.2, monthly_pattern['ad_seasonality'], width=0.4,
        label='Ad Spend Seasonality', alpha=0.7)

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
plt.savefig('../report/images/monthly_seasonality_detailed.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Budget allocation comparison
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

# Current vs Segment budget
axes[0].scatter(budget_df['current_budget'], budget_df['segment_budget'], alpha=0.6)
axes[0].plot([budget_df['current_budget'].min(), budget_df['current_budget'].max()],
             [budget_df['current_budget'].min(), budget_df['current_budget'].max()], 
             'r--', label='No Change')
axes[0].set_xlabel('Current Budget ($)')
axes[0].set_ylabel('Segment-Based Budget ($)')
axes[0].set_title('Segment-Based Allocation')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Current vs Performance budget
axes[1].scatter(budget_df['current_budget'], budget_df['performance_budget'], alpha=0.6)
axes[1].plot([budget_df['current_budget'].min(), budget_df['current_budget'].max()],
             [budget_df['current_budget'].min(), budget_df['current_budget'].max()], 
             'r--', label='No Change')
axes[1].set_xlabel('Current Budget ($)')
axes[1].set_ylabel('Performance-Based Budget ($)')
axes[1].set_title('Performance-Based Allocation')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# Budget changes by segment
segment_changes = budget_df.groupby('segment')['segment_change_pct'].mean()
axes[2].bar(segment_changes.index, segment_changes.values, 
            color=[colors.get(s, 'gray') for s in segment_changes.index])
axes[2].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[2].set_xlabel('Store Segment')
axes[2].set_ylabel('Average Budget Change (%)')
axes[2].set_title('Budget Changes by Store Segment')
axes[2].tick_params(axis='x', rotation=45)
axes[2].grid(True, alpha=0.3, axis='y')

# Monthly budget distribution
axes[3].bar(monthly_totals.index, monthly_totals.values, 
            color=['red' if m in [1, 11, 12] else 'blue' for m in monthly_totals.index])
axes[3].set_xlabel('Month')
axes[3].set_ylabel('Total Monthly Budget ($)')
axes[3].set_title('Monthly Budget Distribution (Red = Holiday Months)')
axes[3].set_xticks(range(1, 13))
axes[3].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../report/images/budget_allocation_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# 8. Save outputs
print(f"\n8. SAVING OUTPUTS...")

# Save store recommendations
store_recommendations = budget_df[[
    'store_id', 'segment', 'ad_effectiveness', 'sales_rank', 'effectiveness_rank',
    'current_budget', 'segment_budget', 'performance_budget', 'hybrid_budget',
    'segment_change_pct', 'performance_change_pct', 'hybrid_change_pct'
]].copy()

store_recommendations.to_csv('../outputs/store_budget_recommendations.csv', index=False)

# Save monthly plan
monthly_plan_summary = monthly_budget.groupby('month').agg({
    'monthly_budget': 'sum',
    'store_id': 'count'
}).reset_index()
monthly_plan_summary.rename(columns={'store_id': 'store_count'}, inplace=True)
monthly_plan_summary.to_csv('../outputs/monthly_budget_plan_summary.csv', index=False)

# Save detailed monthly plan (first 3 months as example)
monthly_budget_sample = monthly_budget[monthly_budget['month'].isin([1, 2, 3])][
    ['store_id', 'month', 'monthly_budget']
].sort_values(['month', 'store_id'])
monthly_budget_sample.to_csv('../outputs/monthly_budget_sample.csv', index=False)

# Save key metrics
key_metrics = {
    'current_ad_ratio': current_ratio,
    'total_monthly_budget': total_current_budget,
    'annual_budget': annual_total,
    'avg_monthly_budget': monthly_avg,
    'stores_high_potential': (store_stats['segment'] == 'High Potential').sum(),
    'stores_low_priority': (store_stats['segment'] == 'Low Priority').sum(),
    'avg_ad_effectiveness': effectiveness_filtered.mean(),
    'pct_positive_effectiveness': (effectiveness_filtered > 0).sum() / len(effectiveness_filtered) * 100
}

metrics_df = pd.DataFrame([key_metrics])
metrics_df.to_csv('../outputs/key_metrics.csv', index=False)

print(f"\n=== ANALYSIS COMPLETE ===")
print(f"Outputs saved to: outputs/")
print(f"Visualizations saved to: report/images/")
print(f"\nKey Recommendations:")
print(f"1. Use hybrid budget allocation (50% current policy + 50% performance-based)")
print(f"2. Allocate ${monthly_avg:,.0f} monthly on average")
print(f"3. Focus on {segment_counts['High Potential']} High Potential stores")
print(f"4. Adjust monthly budgets for seasonality (higher in holiday months)")
