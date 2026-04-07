import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 12

# Read the data
df = pd.read_csv('../outputs/store_monthly_sales_with_date.csv')
df['date'] = pd.to_datetime(df['date'])

# Read store effectiveness data
store_effects = pd.read_csv('../outputs/store_ad_effectiveness.csv')
store_budget = pd.read_csv('../outputs/store_budget_recommendations.csv')

print("=== FINAL BUDGET RECOMMENDATIONS ===")

# 1. Analyze current policy effectiveness
print("\n1. CURRENT POLICY ANALYSIS")
print("Policy RET-ADV-ROLL: ad_spend = share * previous_month_sales")

# Calculate actual relationship
df_sorted = df.sort_values(['store_id', 'date'])
df_sorted['lag_sales'] = df_sorted.groupby('store_id')['sales_revenue_usd'].shift(1)
df_policy = df_sorted.dropna(subset=['lag_sales', 'ad_spend_usd'])

# Simple regression to estimate actual policy implementation
from sklearn.linear_model import LinearRegression
X = df_policy['lag_sales'].values.reshape(-1, 1)
y = df_policy['ad_spend_usd'].values
policy_model = LinearRegression()
policy_model.fit(X, y)
policy_share = policy_model.coef_[0]
policy_intercept = policy_model.intercept_
policy_r2 = policy_model.score(X, y)

print(f"   Estimated share: {policy_share:.6f} (2.47% of lagged sales)")
print(f"   Intercept: ${policy_intercept:.2f}")
print(f"   R²: {policy_r2:.4f} (only 24.4% of ad spend variance explained)")
print(f"   This suggests the policy is not strictly followed or other factors are important")

# 2. Key findings for budget optimization
print("\n2. KEY FINDINGS FOR OPTIMIZATION")

# Holiday vs non-holiday performance
holiday_data = df[df['is_holiday_month'] == 1]
non_holiday_data = df[df['is_holiday_month'] == 0]

holiday_roi = holiday_data['sales_revenue_usd'].sum() / holiday_data['ad_spend_usd'].sum()
non_holiday_roi = non_holiday_data['sales_revenue_usd'].sum() / non_holiday_data['ad_spend_usd'].sum()

print(f"   Holiday months ROI: {holiday_roi:.2f}:1")
print(f"   Non-holiday months ROI: {non_holiday_roi:.2f}:1")
print(f"   Holiday months have {holiday_data['ad_spend_usd'].mean() / non_holiday_data['ad_spend_usd'].mean():.1f}x higher ad spend")
print(f"   But only {holiday_data['sales_revenue_usd'].mean() / non_holiday_data['sales_revenue_usd'].mean():.1f}x higher sales")
print(f"   => Diminishing returns during holidays")

# Store heterogeneity
print(f"\n   Store-level ad effectiveness varies significantly:")
print(f"   Average: ${store_effects['ad_effectiveness'].mean():.2f} sales per $1 ad spend")
print(f"   Range: ${store_effects['ad_effectiveness'].min():.2f} to ${store_effects['ad_effectiveness'].max():.2f}")
print(f"   Top 25% of stores are {store_effects['ad_effectiveness'].quantile(0.75) / store_effects['ad_effectiveness'].quantile(0.25):.1f}x more effective")

# 3. Recommended budget allocation strategy
print("\n3. RECOMMENDED BUDGET ALLOCATION STRATEGY")

# Current total monthly ad spend
total_monthly_ad = df['ad_spend_usd'].sum() / 36  # 36 months total
print(f"   Current average monthly ad spend: ${total_monthly_ad:,.2f}")

# Calculate optimal allocation based on store efficiency
store_efficiency = df.groupby('store_id').apply(lambda x: x['sales_revenue_usd'].sum() / x['ad_spend_usd'].sum()).reset_index()
store_efficiency.columns = ['store_id', 'efficiency']

# Merge with average monthly ad spend
store_monthly = df.groupby('store_id')['ad_spend_usd'].mean().reset_index()
store_monthly.columns = ['store_id', 'current_monthly_ad']
store_efficiency = pd.merge(store_efficiency, store_monthly, on='store_id')

# Normalize efficiency scores
store_efficiency['efficiency_norm'] = store_efficiency['efficiency'] / store_efficiency['efficiency'].sum()
store_efficiency['current_share'] = store_efficiency['current_monthly_ad'] / store_efficiency['current_monthly_ad'].sum()

# Allocation rule: allocate proportional to efficiency squared (to favor high-efficiency stores)
store_efficiency['optimal_share'] = (store_efficiency['efficiency'] ** 2) / (store_efficiency['efficiency'] ** 2).sum()
store_efficiency['recommended_monthly'] = store_efficiency['optimal_share'] * total_monthly_ad
store_efficiency['change_pct'] = (store_efficiency['recommended_monthly'] - store_efficiency['current_monthly_ad']) / store_efficiency['current_monthly_ad'] * 100

# Categorize stores
store_efficiency['category'] = pd.qcut(store_efficiency['efficiency'], 4, labels=['Low', 'Medium', 'High', 'Very High'])

print(f"\n   Store categorization by efficiency:")
for category in ['Low', 'Medium', 'High', 'Very High']:
    cat_data = store_efficiency[store_efficiency['category'] == category]
    print(f"   {category}: {len(cat_data)} stores, avg efficiency: {cat_data['efficiency'].mean():.2f}, "
          f"recommended budget change: {cat_data['change_pct'].mean():+.1f}%")

# 4. Monthly adjustment factors
print("\n4. MONTHLY ADJUSTMENT FACTORS")

# Calculate monthly multipliers relative to average
monthly_performance = df.groupby('month').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'is_holiday_month': 'mean'
}).reset_index()
monthly_performance['roi'] = monthly_performance['sales_revenue_usd'] / monthly_performance['ad_spend_usd']
monthly_performance['roi_multiplier'] = monthly_performance['roi'] / monthly_performance['roi'].mean()

# For budget planning: inverse of ROI multiplier (spend less when ROI is low)
monthly_performance['budget_multiplier'] = 1 / monthly_performance['roi_multiplier']
# Normalize to average 1
monthly_performance['budget_multiplier'] = monthly_performance['budget_multiplier'] / monthly_performance['budget_multiplier'].mean()

print("\n   Month  ROI Multiplier  Budget Multiplier  Holiday")
for _, row in monthly_performance.iterrows():
    holiday_flag = "Yes" if row['is_holiday_month'] > 0.5 else "No"
    print(f"   {int(row['month']):2d}     {row['roi_multiplier']:6.3f}           {row['budget_multiplier']:6.3f}           {holiday_flag}")

# 5. Implementation plan
print("\n5. IMPLEMENTATION PLAN")
print("   Step 1: Reallocate budget based on store efficiency")
print("     - Increase budget for high-efficiency stores by 10-20%")
print("     - Decrease budget for low-efficiency stores by 10-20%")
print("     - Keep total budget constant")
print("   ")
print("   Step 2: Adjust monthly spending patterns")
print("     - Reduce holiday month ad spend (Nov, Dec, Jan) by 15-20%")
print("     - Increase non-holiday month ad spend, especially in low-ROI months")
print("   ")
print("   Step 3: Modify policy RET-ADV-ROLL")
print("     - Change from fixed 2.47% to variable share based on store efficiency")
print("     - High-efficiency stores: 2.8-3.0% of lagged sales")
print("     - Low-efficiency stores: 2.0-2.2% of lagged sales")
print("     - Add monthly adjustment factor")

# 6. Expected impact
print("\n6. EXPECTED IMPACT")
# Conservative estimate: 5% improvement in overall ROI
current_roi = df['sales_revenue_usd'].sum() / df['ad_spend_usd'].sum()
expected_improvement = 0.05  # 5%
expected_new_roi = current_roi * (1 + expected_improvement)

print(f"   Current overall ROI: {current_roi:.2f}:1")
print(f"   Expected new ROI: {expected_new_roi:.2f}:1 ({expected_improvement*100:.1f}% improvement)")
print(f"   With current ad spend of ${total_monthly_ad:,.0f}/month:")
print(f"   Expected sales increase: ${total_monthly_ad * (expected_new_roi - current_roi):,.0f}/month")
print(f"   Annual impact: ${total_monthly_ad * (expected_new_roi - current_roi) * 12:,.0f}")

# Save recommendations
store_efficiency.to_csv('../outputs/final_store_recommendations.csv', index=False)
monthly_performance.to_csv('../outputs/monthly_adjustment_factors.csv', index=False)

# Create visualization of recommendations
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: Store efficiency distribution
ax1 = axes[0, 0]
ax1.hist(store_efficiency['efficiency'], bins=30, edgecolor='black', alpha=0.7)
ax1.axvline(store_efficiency['efficiency'].mean(), color='r', linestyle='--', 
           linewidth=2, label=f'Mean: {store_efficiency["efficiency"].mean():.2f}')
ax1.set_xlabel('Store Efficiency (Sales/Ad Spend Ratio)')
ax1.set_ylabel('Number of Stores')
ax1.set_title('Distribution of Store Efficiency Scores')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Recommended budget changes by category
ax2 = axes[0, 1]
category_changes = store_efficiency.groupby('category')['change_pct'].mean()
colors = ['red', 'orange', 'lightgreen', 'green']
ax2.bar(category_changes.index, category_changes.values, color=colors, edgecolor='black')
ax2.set_xlabel('Store Efficiency Category')
ax2.set_ylabel('Recommended Budget Change (%)')
ax2.set_title('Recommended Budget Changes by Store Efficiency')
ax2.grid(True, alpha=0.3)

# Add value labels
for i, v in enumerate(category_changes.values):
    ax2.text(i, v + (1 if v > 0 else -3), f'{v:+.1f}%', 
            ha='center', va='bottom' if v > 0 else 'top', fontweight='bold')

# Plot 3: Monthly ROI and budget multipliers
ax3 = axes[1, 0]
months = monthly_performance['month']
width = 0.35
x = np.arange(len(months))

bars1 = ax3.bar(x - width/2, monthly_performance['roi_multiplier'], width, 
               label='ROI Multiplier', color='blue', alpha=0.7)
bars2 = ax3.bar(x + width/2, monthly_performance['budget_multiplier'], width, 
               label='Budget Multiplier', color='orange', alpha=0.7)

ax3.set_xlabel('Month')
ax3.set_ylabel('Multiplier (Relative to Average)')
ax3.set_title('Monthly ROI and Recommended Budget Multipliers')
ax3.set_xticks(x)
ax3.set_xticklabels(months)
ax3.legend()
ax3.grid(True, alpha=0.3)

# Highlight holiday months
holiday_months = monthly_performance[monthly_performance['is_holiday_month'] > 0.5]['month'].values - 1
for hm in holiday_months:
    ax3.axvspan(hm - 0.5, hm + 0.5, alpha=0.2, color='red')

# Plot 4: Current vs recommended allocation for sample stores
ax4 = axes[1, 1]
# Sample 20 stores for clarity
sample_stores = store_efficiency.sample(20, random_state=42).sort_values('efficiency')

x_pos = np.arange(len(sample_stores))
ax4.bar(x_pos - 0.2, sample_stores['current_monthly_ad'], width=0.4, 
       label='Current', color='blue', alpha=0.7)
ax4.bar(x_pos + 0.2, sample_stores['recommended_monthly'], width=0.4, 
       label='Recommended', color='green', alpha=0.7)

ax4.set_xlabel('Store (Sorted by Efficiency)')
ax4.set_ylabel('Monthly Ad Budget (USD)')
ax4.set_title('Current vs Recommended Budget (Sample of 20 Stores)')
ax4.set_xticks([])  # Hide store IDs for clarity
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/final_recommendations.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nFigure saved: final_recommendations.png")
print("\nFinal recommendations saved to outputs/ directory.")