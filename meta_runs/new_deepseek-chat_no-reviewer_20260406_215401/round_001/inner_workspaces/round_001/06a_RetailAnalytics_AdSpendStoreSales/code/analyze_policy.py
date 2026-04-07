import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data with date
df = pd.read_csv('../outputs/store_monthly_sales_with_date.csv')
# Convert date column to datetime
df['date'] = pd.to_datetime(df['date'])
print("Data loaded. Shape:", df.shape)

# 1. Analyze current policy: RET-ADV-ROLL
# Policy ties each store's month-m online ad budget to a fixed share of prior-month same-store sales
# Let's calculate what the current fixed share might be

# Create lagged sales (prior month same-store sales)
df = df.sort_values(['store_id', 'date'])
df['sales_lag1'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)

# Calculate actual ad spend as percentage of lagged sales
df['ad_share_actual'] = df['ad_spend_usd'] / df['sales_lag1']

# Remove rows where lagged sales is NaN (first month for each store)
df_clean = df.dropna(subset=['sales_lag1', 'ad_share_actual']).copy()

print("\n=== Current Policy Analysis ===")
print(f"Rows with lagged sales data: {len(df_clean)} (out of {len(df)} total)")
print("\nAd spend as share of prior month sales:")
print(df_clean['ad_share_actual'].describe())

# Check if there's a consistent fixed share
print("\nAverage ad share by store:")
store_shares = df_clean.groupby('store_id')['ad_share_actual'].mean()
print(store_shares.describe())

# 2. Visualize the relationship between ad spend and sales
print("\n=== Relationship Analysis ===")

# Calculate correlation
correlation = df_clean['ad_spend_usd'].corr(df_clean['sales_revenue_usd'])
print(f"Correlation between ad spend and sales: {correlation:.4f}")

# Calculate correlation with lagged ad spend (effect of previous month's ad spend on current sales)
df_clean['ad_spend_lag1'] = df_clean.groupby('store_id')['ad_spend_usd'].shift(1)
correlation_lag = df_clean['ad_spend_lag1'].corr(df_clean['sales_revenue_usd'])
print(f"Correlation between lagged ad spend (t-1) and sales (t): {correlation_lag:.4f}")

# 3. Create visualizations
print("\n=== Creating Visualizations ===")

# Create report/images directory if it doesn't exist
os.makedirs('../report/images', exist_ok=True)

# Figure 1: Distribution of ad share across stores
plt.figure(figsize=(10, 6))
plt.hist(store_shares, bins=30, edgecolor='black', alpha=0.7)
plt.xlabel('Average Ad Spend as Share of Prior Month Sales')
plt.ylabel('Number of Stores')
plt.title('Distribution of Ad Spend Policy Across Stores')
plt.axvline(store_shares.mean(), color='red', linestyle='--', label=f'Mean: {store_shares.mean():.4f}')
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/ad_share_distribution.png', dpi=300)
plt.close()

# Figure 2: Ad spend vs sales scatter plot (sample of stores)
sample_stores = df_clean['store_id'].sample(5, random_state=42)
df_sample = df_clean[df_clean['store_id'].isin(sample_stores)]

plt.figure(figsize=(10, 6))
for store in sample_stores:
    store_data = df_sample[df_sample['store_id'] == store]
    plt.scatter(store_data['ad_spend_usd'], store_data['sales_revenue_usd'], 
                alpha=0.6, label=f'Store {store}')
plt.xlabel('Ad Spend (USD)')
plt.ylabel('Sales Revenue (USD)')
plt.title('Ad Spend vs Sales Revenue (Sample of 5 Stores)')
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/ad_vs_sales_scatter.png', dpi=300)
plt.close()

# Figure 3: Time series of ad spend and sales for a sample store
store_id_example = 1
df_store1 = df_clean[df_clean['store_id'] == store_id_example].sort_values('date')

fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:blue'
ax1.set_xlabel('Date')
ax1.set_ylabel('Sales Revenue (USD)', color=color)
ax1.plot(df_store1['date'], df_store1['sales_revenue_usd'], color=color, label='Sales')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Ad Spend (USD)', color=color)
ax2.plot(df_store1['date'], df_store1['ad_spend_usd'], color=color, linestyle='--', label='Ad Spend')
ax2.tick_params(axis='y', labelcolor=color)

plt.title(f'Time Series of Sales and Ad Spend for Store {store_id_example}')
fig.tight_layout()
plt.savefig('../report/images/time_series_example.png', dpi=300)
plt.close()

# Figure 4: Monthly patterns (aggregate across all stores)
df_clean['month_name'] = df_clean['date'].dt.month_name()
monthly_agg = df_clean.groupby(['month', 'month_name']).agg({
    'ad_spend_usd': 'mean',
    'sales_revenue_usd': 'mean',
    'is_holiday_month': 'mean'
}).reset_index()
monthly_agg = monthly_agg.sort_values('month')

fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:blue'
ax1.set_xlabel('Month')
ax1.set_ylabel('Average Sales Revenue (USD)', color=color)
ax1.plot(monthly_agg['month_name'], monthly_agg['sales_revenue_usd'], 
         color=color, marker='o', label='Sales')
ax1.tick_params(axis='y', labelcolor=color)
plt.xticks(rotation=45)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Average Ad Spend (USD)', color=color)
ax2.plot(monthly_agg['month_name'], monthly_agg['ad_spend_usd'], 
         color=color, marker='s', linestyle='--', label='Ad Spend')
ax2.tick_params(axis='y', labelcolor=color)

# Add holiday months shading
for i, row in monthly_agg.iterrows():
    if row['is_holiday_month'] > 0.5:  # Majority of observations are holiday months
        ax1.axvspan(i-0.5, i+0.5, alpha=0.2, color='gold', label='Holiday Month' if i==0 else '')

plt.title('Monthly Patterns: Average Sales and Ad Spend Across All Stores')
fig.tight_layout()
plt.savefig('../report/images/monthly_patterns.png', dpi=300)
plt.close()

print("\nVisualizations saved to ../report/images/")

# 4. Model ad effectiveness
print("\n=== Modeling Ad Effectiveness ===")

# Prepare data for modeling
df_model = df_clean.copy()

# Create additional features
df_model['ad_spend_lag1'] = df_model.groupby('store_id')['ad_spend_usd'].shift(1)
df_model['ad_spend_lag2'] = df_model.groupby('store_id')['ad_spend_usd'].shift(2)
df_model['sales_lag2'] = df_model.groupby('store_id')['sales_revenue_usd'].shift(2)
df_model['month_sin'] = np.sin(2 * np.pi * df_model['month'] / 12)
df_model['month_cos'] = np.cos(2 * np.pi * df_model['month'] / 12)

# Drop rows with NaN in features
df_model = df_model.dropna(subset=['ad_spend_lag1', 'ad_spend_lag2', 'sales_lag2'])

print(f"Rows available for modeling: {len(df_model)}")

# Define features and target
features = ['ad_spend_usd', 'ad_spend_lag1', 'ad_spend_lag2', 
            'sales_lag1', 'sales_lag2', 'is_holiday_month',
            'foot_traffic', 'local_population', 'competitor_count',
            'month_sin', 'month_cos']

X = df_model[features]
y = df_model['sales_revenue_usd']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest model
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)

y_pred = rf.predict(X_test)

# Calculate metrics
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

print(f"\nRandom Forest Model Performance:")
print(f"RMSE: {rmse:.2f}")
print(f"R²: {r2:.4f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

print("\nFeature Importance:")
print(feature_importance.to_string(index=False))

# Figure 5: Feature importance plot
plt.figure(figsize=(10, 6))
plt.barh(feature_importance['feature'], feature_importance['importance'])
plt.xlabel('Importance')
plt.title('Feature Importance for Sales Prediction')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('../report/images/feature_importance.png', dpi=300)
plt.close()

# 5. Estimate optimal ad spend
print("\n=== Optimal Ad Spend Analysis ===")

# Simple marginal ROI calculation
# We'll estimate the marginal effect of ad spend on sales using the model
# Create a baseline prediction and then increase ad spend

# Use a sample of stores for optimization demonstration
sample_stores_opt = df_model['store_id'].unique()[:10]  # First 10 stores
df_opt_results = []

for store_id in sample_stores_opt:
    store_data = df_model[df_model['store_id'] == store_id].iloc[-1:]  # Most recent observation
    if len(store_data) == 0:
        continue
    
    # Baseline prediction
    X_base = store_data[features].copy()
    baseline_sales = rf.predict(X_base)[0]
    baseline_ad = float(store_data['ad_spend_usd'])
    
    # Calculate marginal effect by increasing ad spend by 10%
    X_test_increase = X_base.copy()
    X_test_increase['ad_spend_usd'] = baseline_ad * 1.1
    increased_sales = rf.predict(X_test_increase)[0]
    
    # Calculate marginal ROI
    ad_increase = baseline_ad * 0.1
    sales_increase = increased_sales - baseline_sales
    marginal_roi = sales_increase / ad_increase if ad_increase > 0 else 0
    
    df_opt_results.append({
        'store_id': store_id,
        'baseline_ad': baseline_ad,
        'baseline_sales': baseline_sales,
        'marginal_roi': marginal_roi,
        'current_ad_share': float(store_data['ad_share_actual'])
    })

df_opt = pd.DataFrame(df_opt_results)
print("\nMarginal ROI for sample stores (10% ad spend increase):")
print(df_opt[['store_id', 'baseline_ad', 'marginal_roi', 'current_ad_share']].to_string(index=False))

# Save optimization results
df_opt.to_csv('../outputs/optimal_ad_analysis.csv', index=False)
print("\nOptimization results saved to ../outputs/optimal_ad_analysis.csv")

print("\n=== Analysis Complete ===")