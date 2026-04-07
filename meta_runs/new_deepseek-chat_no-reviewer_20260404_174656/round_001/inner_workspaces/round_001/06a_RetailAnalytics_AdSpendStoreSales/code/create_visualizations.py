import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 12

# Read the data
df = pd.read_csv('../outputs/store_monthly_sales_with_date.csv')
df['date'] = pd.to_datetime(df['date'])

# Create lagged variables
df = df.sort_values(['store_id', 'date'])
df['lag_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df['lag_ad_spend'] = df.groupby('store_id')['ad_spend_usd'].shift(1)

# Create output directory for images
os.makedirs('../report/images', exist_ok=True)

# 1. Time series of aggregate sales and ad spend
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Aggregate by month
monthly_agg = df.groupby('date').agg({
    'sales_revenue_usd': 'sum',
    'ad_spend_usd': 'sum',
    'foot_traffic': 'sum',
    'is_holiday_month': 'mean'
}).reset_index()
monthly_agg['roi'] = monthly_agg['sales_revenue_usd'] / monthly_agg['ad_spend_usd']

# Plot 1: Sales and Ad Spend over time
ax1 = axes[0, 0]
ax1.plot(monthly_agg['date'], monthly_agg['sales_revenue_usd']/1e6, 'b-', linewidth=2, label='Sales (millions USD)')
ax1.set_xlabel('Date')
ax1.set_ylabel('Sales Revenue (Millions USD)', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.set_title('Monthly Sales Revenue Over Time')
ax1.grid(True, alpha=0.3)

ax1b = ax1.twinx()
ax1b.plot(monthly_agg['date'], monthly_agg['ad_spend_usd']/1e3, 'r-', linewidth=2, label='Ad Spend (thousands USD)')
ax1b.set_ylabel('Ad Spend (Thousands USD)', color='r')
ax1b.tick_params(axis='y', labelcolor='r')

# Highlight holiday months
holiday_months = monthly_agg[monthly_agg['is_holiday_month'] > 0.5]
ax1.scatter(holiday_months['date'], holiday_months['sales_revenue_usd']/1e6, 
           color='orange', s=100, zorder=5, label='Holiday Months')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1b.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

# Plot 2: ROI over time
ax2 = axes[0, 1]
ax2.plot(monthly_agg['date'], monthly_agg['roi'], 'g-', linewidth=2)
ax2.set_xlabel('Date')
ax2.set_ylabel('ROI (Sales/Ad Spend)')
ax2.set_title('Monthly ROI Over Time')
ax2.grid(True, alpha=0.3)

# Highlight holiday months
ax2.scatter(holiday_months['date'], holiday_months['roi'], 
           color='orange', s=100, zorder=5, label='Holiday Months')
ax2.legend()

# Plot 3: Relationship between lagged sales and ad spend (policy check)
ax3 = axes[1, 0]
sample_data = df.dropna(subset=['lag_sales', 'ad_spend_usd']).sample(1000, random_state=42)
ax3.scatter(sample_data['lag_sales']/1000, sample_data['ad_spend_usd'], 
           alpha=0.5, s=20)

# Add regression line
z = np.polyfit(sample_data['lag_sales'], sample_data['ad_spend_usd'], 1)
p = np.poly1d(z)
x_range = np.linspace(sample_data['lag_sales'].min(), sample_data['lag_sales'].max(), 100)
ax3.plot(x_range/1000, p(x_range), 'r-', linewidth=3, 
        label=f'Fit: ad_spend = {z[0]:.5f}*lag_sales + {z[1]:.1f}')

ax3.set_xlabel('Previous Month Sales (Thousands USD)')
ax3.set_ylabel('Current Month Ad Spend (USD)')
ax3.set_title('Relationship: Ad Spend vs Lagged Sales (Policy RET-ADV-ROLL)')
ax3.legend()
ax3.grid(True, alpha=0.3)

# Plot 4: Distribution of store-level sales-to-ad ratios
ax4 = axes[1, 1]
store_stats = df.groupby('store_id').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean'
}).reset_index()
store_stats['sales_to_ad_ratio'] = store_stats['sales_revenue_usd'] / store_stats['ad_spend_usd']

ax4.hist(store_stats['sales_to_ad_ratio'], bins=30, edgecolor='black', alpha=0.7)
ax4.axvline(store_stats['sales_to_ad_ratio'].mean(), color='r', 
           linestyle='--', linewidth=2, 
           label=f'Mean: {store_stats["sales_to_ad_ratio"].mean():.2f}')
ax4.set_xlabel('Sales-to-Ad Ratio')
ax4.set_ylabel('Number of Stores')
ax4.set_title('Distribution of Store-Level Sales-to-Ad Ratios')
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/time_series_and_policy.png', dpi=300, bbox_inches='tight')
plt.close()

print("Figure 1 saved: time_series_and_policy.png")

# 2. Correlation heatmap
fig, ax = plt.subplots(figsize=(10, 8))

# Select numeric columns for correlation
numeric_cols = ['ad_spend_usd', 'sales_revenue_usd', 'foot_traffic', 
                'local_population', 'competitor_count', 'is_holiday_month']
corr_matrix = df[numeric_cols].corr()

# Create mask for upper triangle
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

# Plot heatmap
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='coolwarm', 
           center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
ax.set_title('Correlation Matrix of Key Variables')
plt.tight_layout()
plt.savefig('../report/images/correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

print("Figure 2 saved: correlation_heatmap.png")

# 3. Store performance segmentation
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Calculate store-level metrics
store_performance = df.groupby('store_id').agg({
    'sales_revenue_usd': ['mean', 'std'],
    'ad_spend_usd': ['mean', 'std'],
    'foot_traffic': 'mean',
    'local_population': 'mean',
    'competitor_count': 'mean'
}).reset_index()

# Flatten column names
store_performance.columns = ['store_id', 'avg_sales', 'std_sales', 
                            'avg_ad_spend', 'std_ad_spend', 
                            'avg_foot_traffic', 'avg_population', 'avg_competitors']
store_performance['sales_to_ad_ratio'] = store_performance['avg_sales'] / store_performance['avg_ad_spend']
store_performance['cv_sales'] = store_performance['std_sales'] / store_performance['avg_sales']  # Coefficient of variation

# Plot 1: Sales vs Ad Spend by store
ax1 = axes[0]
scatter = ax1.scatter(store_performance['avg_ad_spend'], store_performance['avg_sales'], 
                     c=store_performance['sales_to_ad_ratio'], cmap='viridis', 
                     s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
ax1.set_xlabel('Average Monthly Ad Spend (USD)')
ax1.set_ylabel('Average Monthly Sales (USD)')
ax1.set_title('Store Performance: Sales vs Ad Spend')
plt.colorbar(scatter, ax=ax1, label='Sales-to-Ad Ratio')
ax1.grid(True, alpha=0.3)

# Add trend line
z = np.polyfit(store_performance['avg_ad_spend'], store_performance['avg_sales'], 1)
p = np.poly1d(z)
x_range = np.linspace(store_performance['avg_ad_spend'].min(), store_performance['avg_ad_spend'].max(), 100)
ax1.plot(x_range, p(x_range), 'r--', linewidth=2, 
        label=f'Fit: slope = {z[0]:.2f}')
ax1.legend()

# Plot 2: Sales-to-Ad Ratio vs Local Population
ax2 = axes[1]
scatter2 = ax2.scatter(store_performance['avg_population'], store_performance['sales_to_ad_ratio'], 
                      c=store_performance['avg_competitors'], cmap='plasma', 
                      s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
ax2.set_xlabel('Local Population')
ax2.set_ylabel('Sales-to-Ad Ratio')
ax2.set_title('Efficiency vs Market Size')
plt.colorbar(scatter2, ax=ax2, label='Average Competitor Count')
ax2.grid(True, alpha=0.3)

# Plot 3: Sales volatility vs efficiency
ax3 = axes[2]
scatter3 = ax3.scatter(store_performance['cv_sales'], store_performance['sales_to_ad_ratio'], 
                      c=store_performance['avg_foot_traffic'], cmap='coolwarm', 
                      s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
ax3.set_xlabel('Coefficient of Variation of Sales')
ax3.set_ylabel('Sales-to-Ad Ratio')
ax3.set_title('Efficiency vs Sales Stability')
plt.colorbar(scatter3, ax=ax3, label='Average Foot Traffic')
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/store_performance_segmentation.png', dpi=300, bbox_inches='tight')
plt.close()

print("Figure 3 saved: store_performance_segmentation.png")

# 4. Holiday vs Non-holiday comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Separate holiday and non-holiday data
holiday_data = df[df['is_holiday_month'] == 1]
non_holiday_data = df[df['is_holiday_month'] == 0]

# Plot 1: Distribution of sales
ax1 = axes[0]
ax1.hist(holiday_data['sales_revenue_usd']/1000, bins=30, alpha=0.5, 
        label='Holiday Months', color='orange', edgecolor='black')
ax1.hist(non_holiday_data['sales_revenue_usd']/1000, bins=30, alpha=0.5, 
        label='Non-Holiday Months', color='blue', edgecolor='black')
ax1.set_xlabel('Sales Revenue (Thousands USD)')
ax1.set_ylabel('Frequency')
ax1.set_title('Distribution of Sales: Holiday vs Non-Holiday')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Distribution of ad spend
ax2 = axes[1]
ax2.hist(holiday_data['ad_spend_usd'], bins=30, alpha=0.5, 
        label='Holiday Months', color='orange', edgecolor='black')
ax2.hist(non_holiday_data['ad_spend_usd'], bins=30, alpha=0.5, 
        label='Non-Holiday Months', color='blue', edgecolor='black')
ax2.set_xlabel('Ad Spend (USD)')
ax2.set_ylabel('Frequency')
ax2.set_title('Distribution of Ad Spend: Holiday vs Non-Holiday')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/holiday_vs_nonholiday.png', dpi=300, bbox_inches='tight')
plt.close()

print("Figure 4 saved: holiday_vs_nonholiday.png")

# Calculate and print summary statistics for holiday vs non-holiday
print("\n=== HOLIDAY VS NON-HOLIDAY COMPARISON ===")
print(f"Holiday months: {len(holiday_data)} observations")
print(f"Non-holiday months: {len(non_holiday_data)} observations")
print(f"\nAverage sales - Holiday: ${holiday_data['sales_revenue_usd'].mean():,.2f}")
print(f"Average sales - Non-holiday: ${non_holiday_data['sales_revenue_usd'].mean():,.2f}")
print(f"Difference: ${holiday_data['sales_revenue_usd'].mean() - non_holiday_data['sales_revenue_usd'].mean():,.2f}")
print(f"\nAverage ad spend - Holiday: ${holiday_data['ad_spend_usd'].mean():,.2f}")
print(f"Average ad spend - Non-holiday: ${non_holiday_data['ad_spend_usd'].mean():,.2f}")
print(f"Difference: ${holiday_data['ad_spend_usd'].mean() - non_holiday_data['ad_spend_usd'].mean():,.2f}")
print(f"\nROI - Holiday: {holiday_data['sales_revenue_usd'].sum() / holiday_data['ad_spend_usd'].sum():.2f}")
print(f"ROI - Non-holiday: {non_holiday_data['sales_revenue_usd'].sum() / non_holiday_data['ad_spend_usd'].sum():.2f}")

print("\nAll visualizations created and saved to report/images/")