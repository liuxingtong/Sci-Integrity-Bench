import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['savefig.dpi'] = 150

# Load data
df = pd.read_csv('data/store_monthly_sales.csv')

# Create derived variables
df = df.sort_values(['store_id', 'year', 'month'])
df['prior_month_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df['implied_ad_ratio'] = df['ad_spend_usd'] / df['prior_month_sales']
df['month_name'] = df['month'].map({
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
})

# ============================================================
# Figure 1: Monthly Ad Spend and Sales Trends
# ============================================================
print("Creating Figure 1: Monthly Ad Spend and Sales Trends...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1a: Average monthly ad spend
monthly_ad = df.groupby('month')['ad_spend_usd'].mean()
ax1 = axes[0, 0]
bars = ax1.bar(monthly_ad.index, monthly_ad.values, color='steelblue', edgecolor='navy', alpha=0.8)
ax1.set_xlabel('Month')
ax1.set_ylabel('Average Ad Spend (USD)')
ax1.set_title('Average Monthly Ad Spend', fontsize=12, fontweight='bold')
ax1.set_xticks(range(1, 13))
ax1.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])
for bar, val in zip(bars, monthly_ad.values):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200, 
             f'${val/1000:.1f}K', ha='center', va='bottom', fontsize=8)

# 1b: Average monthly sales
monthly_sales = df.groupby('month')['sales_revenue_usd'].mean()
ax2 = axes[0, 1]
bars = ax2.bar(monthly_sales.index, monthly_sales.values, color='coral', edgecolor='darkred', alpha=0.8)
ax2.set_xlabel('Month')
ax2.set_ylabel('Average Sales Revenue (USD)')
ax2.set_title('Average Monthly Sales Revenue', fontsize=12, fontweight='bold')
ax2.set_xticks(range(1, 13))
ax2.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])
for bar, val in zip(bars, monthly_sales.values):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5000, 
             f'${val/1000:.0f}K', ha='center', va='bottom', fontsize=8)

# 1c: Ad spend by year and month
ax3 = axes[1, 0]
for year in [1, 2, 3]:
    year_data = df[df['year'] == year].groupby('month')['ad_spend_usd'].mean()
    ax3.plot(year_data.index, year_data.values, marker='o', label=f'Year {year}', linewidth=2)
ax3.set_xlabel('Month')
ax3.set_ylabel('Average Ad Spend (USD)')
ax3.set_title('Ad Spend Trends by Year', fontsize=12, fontweight='bold')
ax3.legend()
ax3.set_xticks(range(1, 13))
ax3.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])

# 1d: Sales by year and month
ax4 = axes[1, 1]
for year in [1, 2, 3]:
    year_data = df[df['year'] == year].groupby('month')['sales_revenue_usd'].mean()
    ax4.plot(year_data.index, year_data.values, marker='s', label=f'Year {year}', linewidth=2)
ax4.set_xlabel('Month')
ax4.set_ylabel('Average Sales Revenue (USD)')
ax4.set_title('Sales Revenue Trends by Year', fontsize=12, fontweight='bold')
ax4.legend()
ax4.set_xticks(range(1, 13))
ax4.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])

plt.tight_layout()
plt.savefig('report/images/fig1_monthly_trends.png', bbox_inches='tight', dpi=150)
plt.close()
print("  Saved: fig1_monthly_trends.png")

# ============================================================
# Figure 2: Ad Spend vs Sales Relationship
# ============================================================
print("Creating Figure 2: Ad Spend vs Sales Relationship...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 2a: Scatter plot with regression line
ax1 = axes[0, 0]
sample_df = df.sample(n=min(1000, len(df)), random_state=42)
slope, intercept, r_value, p_value, std_err = stats.linregress(sample_df['ad_spend_usd'], sample_df['sales_revenue_usd'])
ax1.scatter(sample_df['ad_spend_usd'], sample_df['sales_revenue_usd'], alpha=0.5, s=20, c='steelblue')
x_line = np.linspace(sample_df['ad_spend_usd'].min(), sample_df['ad_spend_usd'].max(), 100)
ax1.plot(x_line, intercept + slope * x_line, 'r-', linewidth=2, label=f'R² = {r_value**2:.3f}')
ax1.set_xlabel('Ad Spend (USD)')
ax1.set_ylabel('Sales Revenue (USD)')
ax1.set_title('Ad Spend vs Sales Revenue', fontsize=12, fontweight='bold')
ax1.legend()

# 2b: Holiday vs Non-Holiday comparison
ax2 = axes[0, 1]
holiday_data = df[df['is_holiday_month'] == 1]['ad_spend_usd']
non_holiday_data = df[df['is_holiday_month'] == 0]['ad_spend_usd']
bp = ax2.boxplot([non_holiday_data, holiday_data], labels=['Non-Holiday', 'Holiday'], patch_artist=True)
bp['boxes'][0].set_facecolor('lightblue')
bp['boxes'][1].set_facecolor('lightcoral')
ax2.set_ylabel('Ad Spend (USD)')
ax2.set_title('Ad Spend: Holiday vs Non-Holiday Months', fontsize=12, fontweight='bold')

# 2c: ROAS distribution by store
ax3 = axes[1, 0]
store_roas = df.groupby('store_id').agg({'ad_spend_usd': 'sum', 'sales_revenue_usd': 'sum'})
store_roas['ROAS'] = store_roas['sales_revenue_usd'] / store_roas['ad_spend_usd']
ax3.hist(store_roas['ROAS'], bins=30, color='steelblue', edgecolor='navy', alpha=0.8)
ax3.axvline(store_roas['ROAS'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {store_roas["ROAS"].mean():.2f}')
ax3.axvline(store_roas['ROAS'].median(), color='green', linestyle=':', linewidth=2, label=f'Median: {store_roas["ROAS"].median():.2f}')
ax3.set_xlabel('ROAS (Sales / Ad Spend)')
ax3.set_ylabel('Number of Stores')
ax3.set_title('Distribution of Return on Ad Spend (ROAS)', fontsize=12, fontweight='bold')
ax3.legend()

# 2d: Correlation heatmap
ax4 = axes[1, 1]
corr_vars = ['ad_spend_usd', 'sales_revenue_usd', 'foot_traffic', 'local_population', 'competitor_count']
corr_matrix = df[corr_vars].corr()
sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='RdBu_r', center=0, ax=ax4, 
            xticklabels=['Ad Spend', 'Sales', 'Traffic', 'Population', 'Competitors'],
            yticklabels=['Ad Spend', 'Sales', 'Traffic', 'Population', 'Competitors'])
ax4.set_title('Correlation Matrix', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/fig2_ad_sales_relationship.png', bbox_inches='tight', dpi=150)
plt.close()
print("  Saved: fig2_ad_sales_relationship.png")

# ============================================================
# Figure 3: Policy RET-ADV-ROLL Analysis
# ============================================================
print("Creating Figure 3: Policy RET-ADV-ROLL Analysis...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 3a: Implied ad ratio by month
valid_df = df.dropna(subset=['implied_ad_ratio'])
monthly_ratio = valid_df.groupby('month')['implied_ad_ratio'].mean()
ax1 = axes[0, 0]
colors = ['coral' if m in [1, 11, 12] else 'steelblue' for m in monthly_ratio.index]
bars = ax1.bar(monthly_ratio.index, monthly_ratio.values * 100, color=colors, edgecolor='navy', alpha=0.8)
ax1.set_xlabel('Month')
ax1.set_ylabel('Ad Ratio (% of Prior Month Sales)')
ax1.set_title('Policy Parameter: Ad Spend as % of Prior Month Sales', fontsize=12, fontweight='bold')
ax1.set_xticks(range(1, 13))
ax1.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])
ax1.axhline(y=2.8, color='red', linestyle='--', linewidth=1.5, label='Overall Mean (2.8%)')
ax1.legend()

# 3b: Distribution of ad ratios
ax2 = axes[0, 1]
holiday_ratios = valid_df[valid_df['is_holiday_month'] == 1]['implied_ad_ratio'] * 100
non_holiday_ratios = valid_df[valid_df['is_holiday_month'] == 0]['implied_ad_ratio'] * 100
ax2.hist(non_holiday_ratios, bins=40, alpha=0.7, label='Non-Holiday', color='steelblue', edgecolor='navy')
ax2.hist(holiday_ratios, bins=40, alpha=0.7, label='Holiday', color='coral', edgecolor='darkred')
ax2.set_xlabel('Ad Ratio (% of Prior Month Sales)')
ax2.set_ylabel('Frequency')
ax2.set_title('Distribution of Ad Ratios: Holiday vs Non-Holiday', fontsize=12, fontweight='bold')
ax2.legend()

# 3c: Recommended budget ratios
ax3 = axes[1, 0]
recommended_ratios = {
    'Jan': 3.72, 'Feb': 0.94, 'Mar': 2.15, 'Apr': 2.15, 'May': 2.16, 'Jun': 2.16,
    'Jul': 2.20, 'Aug': 2.14, 'Sep': 2.19, 'Oct': 2.15, 'Nov': 8.27, 'Dec': 3.70
}
months = list(recommended_ratios.keys())
ratios = list(recommended_ratios.values())
colors = ['coral' if m in ['Jan', 'Nov', 'Dec'] else 'steelblue' for m in months]
bars = ax3.bar(months, ratios, color=colors, edgecolor='navy', alpha=0.8)
ax3.set_xlabel('Month')
ax3.set_ylabel('Recommended Ad Ratio (%)')
ax3.set_title('Recommended Monthly Ad Budget Ratios', fontsize=12, fontweight='bold')
for bar, val in zip(bars, ratios):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
             f'{val:.1f}%', ha='center', va='bottom', fontsize=9)

# 3d: Budget allocation pie chart
ax4 = axes[1, 1]
monthly_budget = df.groupby('month')['ad_spend_usd'].sum()
holiday_budget = monthly_budget.loc[[1, 11, 12]].sum()
non_holiday_budget = monthly_budget.loc[list(set(range(1, 13)) - {1, 11, 12})].sum()
sizes = [non_holiday_budget, holiday_budget]
labels = [f'Non-Holiday\n${non_holiday_budget/1e6:.1f}M', f'Holiday\n${holiday_budget/1e6:.1f}M']
colors = ['steelblue', 'coral']
explode = (0, 0.05)
ax4.pie(sizes, labels=labels, colors=colors, explode=explode, autopct='%1.1f%%', 
        startangle=90, textprops={'fontsize': 11})
ax4.set_title('Annual Budget Allocation: Holiday vs Non-Holiday', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/fig3_policy_analysis.png', bbox_inches='tight', dpi=150)
plt.close()
print("  Saved: fig3_policy_analysis.png")

# ============================================================
# Figure 4: Store Performance Analysis
# ============================================================
print("Creating Figure 4: Store Performance Analysis...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 4a: Store ROAS distribution
ax1 = axes[0, 0]
store_perf = df.groupby('store_id').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'foot_traffic': 'mean',
    'competitor_count': 'mean'
}).reset_index()
store_perf['ROAS'] = store_perf['sales_revenue_usd'] / store_perf['ad_spend_usd']
ax1.scatter(store_perf['ad_spend_usd'], store_perf['ROAS'], alpha=0.6, c='steelblue', s=50)
ax1.set_xlabel('Average Ad Spend (USD)')
ax1.set_ylabel('ROAS')
ax1.set_title('Store ROAS vs Average Ad Spend', fontsize=12, fontweight='bold')

# 4b: Sales vs Traffic by store
ax2 = axes[0, 1]
sc = ax2.scatter(store_perf['foot_traffic'], store_perf['sales_revenue_usd'], 
                 c=store_perf['competitor_count'], cmap='RdYlBu_r', alpha=0.6, s=50)
plt.colorbar(sc, ax=ax2, label='Competitor Count')
ax2.set_xlabel('Average Foot Traffic')
ax2.set_ylabel('Average Sales Revenue (USD)')
ax2.set_title('Store Sales vs Traffic (colored by Competitors)', fontsize=12, fontweight='bold')

# 4c: Top and bottom performers
ax3 = axes[1, 0]
top_10 = store_perf.nlargest(10, 'ROAS')
bottom_10 = store_perf.nsmallest(10, 'ROAS')
combined = pd.concat([top_10, bottom_10])
colors = ['green' if i < 10 else 'red' for i in range(20)]
bars = ax3.barh(range(20), combined['ROAS'], color=colors, alpha=0.7)
ax3.set_yticks(range(20))
ax3.set_yticklabels([f"Store {int(s)}" for s in combined['store_id']], fontsize=8)
ax3.set_xlabel('ROAS')
ax3.set_title('Top 10 (Green) and Bottom 10 (Red) Stores by ROAS', fontsize=12, fontweight='bold')
ax3.axvline(x=store_perf['ROAS'].mean(), color='black', linestyle='--', linewidth=1.5, label='Mean')
ax3.legend()

# 4d: Performance by competitor count
ax4 = axes[1, 1]
comp_perf = store_perf.groupby(pd.cut(store_perf['competitor_count'], bins=[0, 3, 5, 8])).agg({
    'ROAS': 'mean',
    'sales_revenue_usd': 'mean',
    'store_id': 'count'
}).reset_index()
comp_perf.columns = ['Competitor Range', 'Avg ROAS', 'Avg Sales', 'Store Count']
x_pos = range(len(comp_perf))
bars = ax4.bar(x_pos, comp_perf['Avg ROAS'], color='steelblue', edgecolor='navy', alpha=0.8)
ax4.set_xticks(x_pos)
ax4.set_xticklabels(['Low (2-3)', 'Medium (4-5)', 'High (6-8)'])
ax4.set_xlabel('Competitor Count Range')
ax4.set_ylabel('Average ROAS')
ax4.set_title('ROAS by Competitor Intensity', fontsize=12, fontweight='bold')
for bar, val in zip(bars, comp_perf['Avg ROAS']):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
             f'{val:.2f}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/fig4_store_performance.png', bbox_inches='tight', dpi=150)
plt.close()
print("  Saved: fig4_store_performance.png")

# ============================================================
# Figure 5: Year-over-Year Comparison
# ============================================================
print("Creating Figure 5: Year-over-Year Comparison...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 5a: Total ad spend by year
ax1 = axes[0, 0]
yearly_ad = df.groupby('year')['ad_spend_usd'].sum() / 1e6
bars = ax1.bar(yearly_ad.index, yearly_ad.values, color='steelblue', edgecolor='navy', alpha=0.8)
ax1.set_xlabel('Year')
ax1.set_ylabel('Total Ad Spend (Million USD)')
ax1.set_title('Total Annual Ad Spend', fontsize=12, fontweight='bold')
for bar, val in zip(bars, yearly_ad.values):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
             f'${val:.2f}M', ha='center', va='bottom', fontsize=10)

# 5b: Total sales by year
ax2 = axes[0, 1]
yearly_sales = df.groupby('year')['sales_revenue_usd'].sum() / 1e6
bars = ax2.bar(yearly_sales.index, yearly_sales.values, color='coral', edgecolor='darkred', alpha=0.8)
ax2.set_xlabel('Year')
ax2.set_ylabel('Total Sales Revenue (Million USD)')
ax2.set_title('Total Annual Sales Revenue', fontsize=12, fontweight='bold')
for bar, val in zip(bars, yearly_sales.values):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
             f'${val:.1f}M', ha='center', va='bottom', fontsize=10)

# 5c: ROAS by year
ax3 = axes[1, 0]
yearly_roas = yearly_sales / yearly_ad
bars = ax3.bar(yearly_roas.index, yearly_roas.values, color='green', edgecolor='darkgreen', alpha=0.8)
ax3.set_xlabel('Year')
ax3.set_ylabel('ROAS')
ax3.set_title('Return on Ad Spend by Year', fontsize=12, fontweight='bold')
ax3.axhline(y=yearly_roas.mean(), color='red', linestyle='--', linewidth=1.5, label=f'Mean: {yearly_roas.mean():.2f}')
ax3.legend()
for bar, val in zip(bars, yearly_roas.values):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
             f'{val:.2f}', ha='center', va='bottom', fontsize=10)

# 5d: Monthly trends across years
ax4 = axes[1, 1]
for year in [1, 2, 3]:
    monthly_sales = df[df['year'] == year].groupby('month')['sales_revenue_usd'].mean() / 1000
    ax4.plot(monthly_sales.index, monthly_sales.values, marker='o', label=f'Year {year}', linewidth=2)
ax4.set_xlabel('Month')
ax4.set_ylabel('Average Sales (Thousand USD)')
ax4.set_title('Monthly Sales Trends by Year', fontsize=12, fontweight='bold')
ax4.legend()
ax4.set_xticks(range(1, 13))
ax4.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])

plt.tight_layout()
plt.savefig('report/images/fig5_yearly_comparison.png', bbox_inches='tight', dpi=150)
plt.close()
print("  Saved: fig5_yearly_comparison.png")

# ============================================================
# Figure 6: Budget Planning Summary
# ============================================================
print("Creating Figure 6: Budget Planning Summary...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 6a: Recommended monthly budget allocation
ax1 = axes[0, 0]
monthly_budget = df.groupby('month').agg({
    'ad_spend_usd': 'mean',
    'sales_revenue_usd': 'mean'
})
monthly_budget['recommended_pct'] = [3.72, 0.94, 2.15, 2.15, 2.16, 2.16, 2.20, 2.14, 2.19, 2.15, 8.27, 3.70]

x = np.arange(12)
width = 0.35
bars1 = ax1.bar(x - width/2, monthly_budget['ad_spend_usd']/1000, width, label='Current Avg Ad Spend', color='steelblue', alpha=0.8)
bars2 = ax1.bar(x + width/2, monthly_budget['sales_revenue_usd']/1000 * monthly_budget['recommended_pct']/100, width, 
                label='Recommended Budget', color='coral', alpha=0.8)
ax1.set_xlabel('Month')
ax1.set_ylabel('Budget (Thousand USD)')
ax1.set_title('Current vs Recommended Monthly Ad Budget', fontsize=12, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])
ax1.legend()

# 6b: Budget efficiency by month
ax2 = axes[0, 1]
monthly_budget['efficiency'] = monthly_budget['sales_revenue_usd'] / monthly_budget['ad_spend_usd']
bars = ax2.bar(range(1, 13), monthly_budget['efficiency'], color='green', edgecolor='darkgreen', alpha=0.8)
ax2.axhline(y=monthly_budget['efficiency'].mean(), color='red', linestyle='--', linewidth=1.5, label='Mean')
ax2.set_xlabel('Month')
ax2.set_ylabel('Sales per Ad Dollar')
ax2.set_title('Ad Spend Efficiency by Month', fontsize=12, fontweight='bold')
ax2.set_xticks(range(1, 13))
ax2.set_xticklabels(['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'])
ax2.legend()

# 6c: Traffic vs Ad Spend
ax3 = axes[1, 0]
ax3.scatter(df['foot_traffic'], df['ad_spend_usd'], alpha=0.3, s=20, c='steelblue')
z = np.polyfit(df['foot_traffic'], df['ad_spend_usd'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['foot_traffic'].min(), df['foot_traffic'].max(), 100)
ax3.plot(x_line, p(x_line), 'r-', linewidth=2, label='Trend Line')
ax3.set_xlabel('Foot Traffic')
ax3.set_ylabel('Ad Spend (USD)')
ax3.set_title('Ad Spend vs Foot Traffic', fontsize=12, fontweight='bold')
ax3.legend()

# 6d: Summary statistics table
ax4 = axes[1, 1]
ax4.axis('off')
summary_text = """
BUDGET PLANNING SUMMARY
========================

Key Metrics:
• Total Annual Ad Budget: ~$20.2M
• Total Annual Sales: ~$720M
• Overall ROAS: 35.7x

Recommended Ad Ratios:
• Holiday Months (Jan, Nov, Dec): 3.7% - 8.3%
• Non-Holiday Months: 0.9% - 2.2%

Policy RET-ADV-ROLL Parameters:
• Mean Ratio: 2.8% of prior month sales
• Holiday Premium: 2.7x higher ratio

Budget Allocation:
• Holiday Period: 56% of annual budget
• Non-Holiday Period: 44% of annual budget

Store Performance:
• High Performers: ROAS > 36.0
• Medium Performers: ROAS 35.0-36.0
• Low Performers: ROAS < 35.0
"""
ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, fontsize=11, 
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))

plt.tight_layout()
plt.savefig('report/images/fig6_budget_planning.png', bbox_inches='tight', dpi=150)
plt.close()
print("  Saved: fig6_budget_planning.png")

print("\n" + "="*70)
print("All visualizations created successfully!")
print("="*70)
