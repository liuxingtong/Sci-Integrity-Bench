import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
df = pd.read_csv('../data/store_monthly_sales.csv')
print("Data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())
print("\nData info:")
print(df.info())
print("\nDescriptive statistics:")
print(df.describe())

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Create a datetime column for time series analysis
df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')
df['store_id'] = df['store_id'].astype('category')

# Check unique stores and time periods
print("\nUnique stores:", df['store_id'].nunique())
print("Date range:", df['date'].min(), "to", df['date'].max())
print("Total months per store (expected 36):", df.groupby('store_id').size().unique())

# Calculate some basic metrics
df['sales_per_traffic'] = df['sales_revenue_usd'] / df['foot_traffic']
df['ad_intensity'] = df['ad_spend_usd'] / df['sales_revenue_usd']

# Save the processed data
df.to_csv('../outputs/processed_data.csv', index=False)
print("\nProcessed data saved to ../outputs/processed_data.csv")

# Create some basic visualizations
os.makedirs('../report/images', exist_ok=True)

# 1. Distribution of key variables
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

variables = ['ad_spend_usd', 'sales_revenue_usd', 'foot_traffic', 
             'local_population', 'competitor_count', 'ad_intensity']
titles = ['Ad Spend (USD)', 'Sales Revenue (USD)', 'Foot Traffic',
          'Local Population', 'Competitor Count', 'Ad Intensity (Ad/Sales)']

for i, (var, title) in enumerate(zip(variables, titles)):
    axes[i].hist(df[var].dropna(), bins=50, edgecolor='black', alpha=0.7)
    axes[i].set_title(f'Distribution of {title}')
    axes[i].set_xlabel(title)
    axes[i].set_ylabel('Frequency')

plt.tight_layout()
plt.savefig('../report/images/distributions.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Time series of average sales and ad spend
monthly_avg = df.groupby('date').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'foot_traffic': 'mean',
    'is_holiday_month': 'mean'
}).reset_index()

fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Sales over time
axes[0].plot(monthly_avg['date'], monthly_avg['sales_revenue_usd'], 
             marker='o', linewidth=2, label='Average Sales')
axes[0].set_title('Average Monthly Sales Revenue Over Time')
axes[0].set_xlabel('Date')
axes[0].set_ylabel('Sales Revenue (USD)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Ad spend over time
axes[1].plot(monthly_avg['date'], monthly_avg['ad_spend_usd'], 
             marker='s', linewidth=2, color='orange', label='Average Ad Spend')
axes[1].set_title('Average Monthly Ad Spend Over Time')
axes[1].set_xlabel('Date')
axes[1].set_ylabel('Ad Spend (USD)')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/time_series.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Scatter plot: Ad spend vs Sales
fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(df['ad_spend_usd'], df['sales_revenue_usd'], 
                     c=df['is_holiday_month'], alpha=0.6, cmap='coolwarm', s=20)
ax.set_xlabel('Ad Spend (USD)')
ax.set_ylabel('Sales Revenue (USD)')
ax.set_title('Ad Spend vs Sales Revenue (Color: Holiday Month)')
plt.colorbar(scatter, label='Holiday Month (1=Yes, 0=No)')
ax.grid(True, alpha=0.3)
plt.savefig('../report/images/ad_vs_sales.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Holiday vs non-holiday comparison
holiday_stats = df.groupby('is_holiday_month').agg({
    'sales_revenue_usd': ['mean', 'std', 'count'],
    'ad_spend_usd': ['mean', 'std'],
    'foot_traffic': ['mean', 'std']
}).round(2)

print("\nHoliday vs Non-Holiday Statistics:")
print(holiday_stats)

# Save holiday stats
df_holiday = df[df['is_holiday_month'] == 1]
df_nonholiday = df[df['is_holiday_month'] == 0]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].boxplot([df_nonholiday['sales_revenue_usd'], df_holiday['sales_revenue_usd']], 
                labels=['Non-Holiday', 'Holiday'])
axes[0].set_title('Sales Revenue: Holiday vs Non-Holiday')
axes[0].set_ylabel('Sales Revenue (USD)')
axes[0].grid(True, alpha=0.3)

axes[1].boxplot([df_nonholiday['ad_spend_usd'], df_holiday['ad_spend_usd']], 
                labels=['Non-Holiday', 'Holiday'])
axes[1].set_title('Ad Spend: Holiday vs Non-Holiday')
axes[1].set_ylabel('Ad Spend (USD)')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/holiday_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nEDA completed. Figures saved to ../report/images/")
