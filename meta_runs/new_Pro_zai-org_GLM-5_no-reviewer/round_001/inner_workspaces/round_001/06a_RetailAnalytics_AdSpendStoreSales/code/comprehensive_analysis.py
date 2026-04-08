import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11

# Load data
df = pd.read_csv('data/store_monthly_sales.csv')

# Create derived variables
df = df.sort_values(['store_id', 'year', 'month'])
df['prior_month_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df['prior_month_ad'] = df.groupby('store_id')['ad_spend_usd'].shift(1)
df['prior_month_traffic'] = df.groupby('store_id')['foot_traffic'].shift(1)
df['implied_ad_ratio'] = df['ad_spend_usd'] / df['prior_month_sales']
df['sales_growth'] = df.groupby('store_id')['sales_revenue_usd'].pct_change()
df['ad_growth'] = df.groupby('store_id')['ad_spend_usd'].pct_change()

# Create lagged variables for regression
df['ad_spend_lag1'] = df.groupby('store_id')['ad_spend_usd'].shift(1)
df['ad_spend_lag2'] = df.groupby('store_id')['ad_spend_usd'].shift(2)

# Create month dummies
df['month_name'] = df['month'].map({
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
})

print("="*70)
print("COMPREHENSIVE RETAIL ANALYTICS - AD SPEND & SALES")
print("="*70)

# ============================================================
# 1. CORRELATION ANALYSIS
# ============================================================
print("\n" + "="*70)
print("1. CORRELATION ANALYSIS")
print("="*70)

corr_vars = ['ad_spend_usd', 'sales_revenue_usd', 'foot_traffic', 
             'local_population', 'competitor_count', 'is_holiday_month']
corr_matrix = df[corr_vars].corr()
print(f"\nCorrelation Matrix:\n{corr_matrix.round(3)}")

# Save correlation matrix
corr_matrix.to_csv('outputs/correlation_matrix.csv')

# ============================================================
# 2. AD SPEND EFFECTIVENESS ANALYSIS
# ============================================================
print("\n" + "="*70)
print("2. AD SPEND EFFECTIVENESS ANALYSIS")
print("="*70)

# Calculate ROAS (Return on Ad Spend) by store
store_roas = df.groupby('store_id').agg({
    'ad_spend_usd': 'sum',
    'sales_revenue_usd': 'sum'
}).reset_index()
store_roas['ROAS'] = store_roas['sales_revenue_usd'] / store_roas['ad_spend_usd']

print(f"\nROAS Statistics:")
print(f"  Mean: {store_roas['ROAS'].mean():.2f}")
print(f"  Median: {store_roas['ROAS'].median():.2f}")
print(f"  Std: {store_roas['ROAS'].std():.2f}")
print(f"  Min: {store_roas['ROAS'].min():.2f}")
print(f"  Max: {store_roas['ROAS'].max():.2f}")

# Marginal effect of ad spend on sales
# Using regression with controls
reg_df = df.dropna(subset=['prior_month_sales', 'ad_spend_lag1'])

# Simple regression: Sales ~ Ad Spend
X_simple = reg_df[['ad_spend_usd']].values
y = reg_df['sales_revenue_usd'].values

lr_simple = LinearRegression()
lr_simple.fit(X_simple, y)
print(f"\nSimple Regression (Sales ~ Ad Spend):")
print(f"  Coefficient: {lr_simple.coef_[0]:.4f}")
print(f"  Intercept: {lr_simple.intercept_:.2f}")
print(f"  R²: {lr_simple.score(X_simple, y):.4f}")

# Multiple regression with controls
X_multi = reg_df[['ad_spend_usd', 'foot_traffic', 'local_population', 
                  'competitor_count', 'is_holiday_month', 'prior_month_sales']].values

lr_multi = LinearRegression()
lr_multi.fit(X_multi, y)
print(f"\nMultiple Regression (with controls):")
print(f"  Ad Spend Coefficient: {lr_multi.coef_[0]:.4f}")
print(f"  Foot Traffic Coefficient: {lr_multi.coef_[1]:.4f}")
print(f"  Local Population Coefficient: {lr_multi.coef_[2]:.4f}")
print(f"  Competitor Count Coefficient: {lr_multi.coef_[3]:.4f}")
print(f"  Holiday Month Coefficient: {lr_multi.coef_[4]:.2f}")
print(f"  Prior Month Sales Coefficient: {lr_multi.coef_[5]:.4f}")
print(f"  R²: {lr_multi.score(X_multi, y):.4f}")

# ============================================================
# 3. POLICY RET-ADV-ROLL ANALYSIS
# ============================================================
print("\n" + "="*70)
print("3. POLICY RET-ADV-ROLL ANALYSIS")
print("="*70)

# The policy ties ad budget to prior-month sales
# Analyze optimal ratio
valid_df = df.dropna(subset=['implied_ad_ratio'])

# Segment by holiday vs non-holiday
holiday_df = valid_df[valid_df['is_holiday_month'] == 1]
non_holiday_df = valid_df[valid_df['is_holiday_month'] == 0]

print(f"\nPolicy Parameter Analysis (Ad Spend / Prior Month Sales):")
print(f"\nHoliday Months (Nov, Dec, Jan):")
print(f"  Mean Ratio: {holiday_df['implied_ad_ratio'].mean():.4f}")
print(f"  Median Ratio: {holiday_df['implied_ad_ratio'].median():.4f}")
print(f"  Recommended Ratio: {holiday_df['implied_ad_ratio'].quantile(0.75):.4f}")

print(f"\nNon-Holiday Months:")
print(f"  Mean Ratio: {non_holiday_df['implied_ad_ratio'].mean():.4f}")
print(f"  Median Ratio: {non_holiday_df['implied_ad_ratio'].median():.4f}")
print(f"  Recommended Ratio: {non_holiday_df['implied_ad_ratio'].quantile(0.75):.4f}")

# ============================================================
# 4. MONTHLY BUDGET PLANNING
# ============================================================
print("\n" + "="*70)
print("4. MONTHLY BUDGET PLANNING RECOMMENDATIONS")
print("="*70)

# Calculate average monthly budget by month
monthly_budget = df.groupby('month').agg({
    'ad_spend_usd': ['mean', 'std', 'sum'],
    'sales_revenue_usd': ['mean', 'sum'],
    'store_id': 'count'
}).round(2)
monthly_budget.columns = ['avg_ad_spend', 'std_ad_spend', 'total_ad_spend', 
                          'avg_sales', 'total_sales', 'n_obs']
monthly_budget['recommended_ratio'] = df.groupby('month')['implied_ad_ratio'].mean().values

print(f"\nMonthly Budget Summary:")
print(monthly_budget.to_string())

# Calculate recommended budget for next year
# Based on average prior month sales and recommended ratios
avg_prior_sales_by_month = df.groupby('month')['prior_month_sales'].mean()

print(f"\nRecommended Ad Budget Ratios by Month:")
for month in range(1, 13):
    ratio = monthly_budget.loc[month, 'recommended_ratio']
    print(f"  Month {month:2d}: {ratio:.4f} ({ratio*100:.2f}% of prior month sales)")

# ============================================================
# 5. STORE-LEVEL RECOMMENDATIONS
# ============================================================
print("\n" + "="*70)
print("5. STORE-LEVEL RECOMMENDATIONS")
print("="*70)

# Segment stores by performance
store_perf = df.groupby('store_id').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'foot_traffic': 'mean',
    'competitor_count': 'mean',
    'implied_ad_ratio': 'mean'
}).reset_index()

store_perf['ROAS'] = store_perf['sales_revenue_usd'] / store_perf['ad_spend_usd']

# Classify stores
store_perf['performance'] = pd.cut(store_perf['ROAS'], 
                                    bins=[0, store_perf['ROAS'].quantile(0.33),
                                          store_perf['ROAS'].quantile(0.67), float('inf')],
                                    labels=['Low', 'Medium', 'High'])

perf_summary = store_perf.groupby('performance').agg({
    'store_id': 'count',
    'ROAS': 'mean',
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'implied_ad_ratio': 'mean'
}).round(2)

print(f"\nStore Performance Segments:")
print(perf_summary.to_string())

# Save store performance
store_perf.to_csv('outputs/store_performance.csv', index=False)

# ============================================================
# 6. YEAR-OVER-YEAR ANALYSIS
# ============================================================
print("\n" + "="*70)
print("6. YEAR-OVER-YEAR ANALYSIS")
print("="*70)

yearly_stats = df.groupby('year').agg({
    'ad_spend_usd': ['sum', 'mean'],
    'sales_revenue_usd': ['sum', 'mean'],
    'foot_traffic': 'mean'
}).round(2)
yearly_stats.columns = ['total_ad', 'avg_ad', 'total_sales', 'avg_sales', 'avg_traffic']
yearly_stats['ROAS'] = yearly_stats['total_sales'] / yearly_stats['total_ad']

print(f"\nYearly Statistics:")
print(yearly_stats.to_string())

# Year-over-year growth
print(f"\nYear-over-Year Growth:")
print(f"  Ad Spend Growth (Y2 vs Y1): {((yearly_stats.loc[2, 'total_ad'] / yearly_stats.loc[1, 'total_ad']) - 1) * 100:.2f}%")
print(f"  Ad Spend Growth (Y3 vs Y2): {((yearly_stats.loc[3, 'total_ad'] / yearly_stats.loc[2, 'total_ad']) - 1) * 100:.2f}%")
print(f"  Sales Growth (Y2 vs Y1): {((yearly_stats.loc[2, 'total_sales'] / yearly_stats.loc[1, 'total_sales']) - 1) * 100:.2f}%")
print(f"  Sales Growth (Y3 vs Y2): {((yearly_stats.loc[3, 'total_sales'] / yearly_stats.loc[2, 'total_sales']) - 1) * 100:.2f}%")

# Save yearly stats
yearly_stats.to_csv('outputs/yearly_statistics.csv')

print("\n" + "="*70)
print("Analysis complete. Generating visualizations...")
print("="*70)
