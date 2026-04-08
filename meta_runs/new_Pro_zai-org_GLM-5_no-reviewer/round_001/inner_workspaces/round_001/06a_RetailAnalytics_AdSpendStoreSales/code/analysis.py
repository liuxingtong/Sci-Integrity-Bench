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

# Load data
df = pd.read_csv('data/store_monthly_sales.csv')

print("="*60)
print("DATA OVERVIEW")
print("="*60)
print(f"\nShape: {df.shape}")
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nMissing values:\n{df.isnull().sum()}")
print(f"\nBasic statistics:\n{df.describe()}")

# Create derived variables
df['ad_to_sales_ratio'] = df['ad_spend_usd'] / df['sales_revenue_usd']
df['sales_per_traffic'] = df['sales_revenue_usd'] / df['foot_traffic']
df['year_month'] = df['year'] * 100 + df['month']

# Create prior month sales for policy analysis
df = df.sort_values(['store_id', 'year', 'month'])
df['prior_month_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df['prior_month_ad'] = df.groupby('store_id')['ad_spend_usd'].shift(1)

# Calculate implied ad spend ratio (current ad / prior sales)
df['implied_ad_ratio'] = df['ad_spend_usd'] / df['prior_month_sales']

print("\n" + "="*60)
print("AD SPEND ANALYSIS")
print("="*60)

# Overall ad spend statistics
print(f"\nTotal Ad Spend: ${df['ad_spend_usd'].sum():,.2f}")
print(f"Total Sales Revenue: ${df['sales_revenue_usd'].sum():,.2f}")
print(f"Overall Ad-to-Sales Ratio: {df['ad_spend_usd'].sum() / df['sales_revenue_usd'].sum():.4f}")

# Monthly patterns
monthly_stats = df.groupby('month').agg({
    'ad_spend_usd': ['mean', 'std'],
    'sales_revenue_usd': ['mean', 'std'],
    'foot_traffic': ['mean', 'std']
}).round(2)
print(f"\nMonthly Statistics:\n{monthly_stats}")

# Holiday vs non-holiday
holiday_stats = df.groupby('is_holiday_month').agg({
    'ad_spend_usd': 'mean',
    'sales_revenue_usd': 'mean',
    'foot_traffic': 'mean'
}).round(2)
print(f"\nHoliday vs Non-Holiday:\n{holiday_stats}")

# Store-level statistics
store_stats = df.groupby('store_id').agg({
    'ad_spend_usd': ['mean', 'sum'],
    'sales_revenue_usd': ['mean', 'sum'],
    'foot_traffic': 'mean',
    'competitor_count': 'mean'
})
store_stats.columns = ['avg_ad_spend', 'total_ad_spend', 'avg_sales', 'total_sales', 'avg_traffic', 'avg_competitors']

print("\n" + "="*60)
print("POLICY RET-ADV-ROLL ANALYSIS")
print("="*60)

# Analyze the implied ad ratio (policy parameter)
valid_ratio = df['implied_ad_ratio'].dropna()
print(f"\nImplied Ad Ratio (Ad Spend / Prior Month Sales):")
print(f"  Mean: {valid_ratio.mean():.4f}")
print(f"  Median: {valid_ratio.median():.4f}")
print(f"  Std: {valid_ratio.std():.4f}")
print(f"  Min: {valid_ratio.min():.4f}")
print(f"  Max: {valid_ratio.max():.4f}")

# Holiday vs non-holiday ad ratios
holiday_ratios = df[df['is_holiday_month'] == 1]['implied_ad_ratio'].dropna()
non_holiday_ratios = df[df['is_holiday_month'] == 0]['implied_ad_ratio'].dropna()
print(f"\nHoliday months ad ratio: {holiday_ratios.mean():.4f}")
print(f"Non-holiday months ad ratio: {non_holiday_ratios.mean():.4f}")

# Save processed data
df.to_csv('outputs/processed_data.csv', index=False)
store_stats.to_csv('outputs/store_statistics.csv')

print("\nData saved to outputs folder.")
