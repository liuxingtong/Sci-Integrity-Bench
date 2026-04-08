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

# Read processed data
df = pd.read_csv('../outputs/processed_data.csv')
print("Data loaded. Shape:", df.shape)

# Create lagged variables for panel analysis
df = df.sort_values(['store_id', 'date'])

# Create lagged sales (prior month sales for each store)
df['lag_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)

# Create lagged ad spend
df['lag_ad_spend'] = df.groupby('store_id')['ad_spend_usd'].shift(1)

# Calculate the actual ad-to-sales ratio from previous month
df['actual_ad_to_sales_ratio'] = df['lag_ad_spend'] / df['lag_sales']

# Remove rows with NaN due to lagging
df_clean = df.dropna(subset=['lag_sales', 'lag_ad_spend']).copy()
print("Data after creating lags:", df_clean.shape)

# 1. Analyze current policy: ad spend as share of prior-month sales
# Calculate what the fixed share would be based on historical data
current_ratio = df_clean['ad_spend_usd'].sum() / df_clean['lag_sales'].sum()
print(f"\nCurrent implied ad-to-sales ratio: {current_ratio:.4f} ({current_ratio*100:.2f}%)")

# Calculate store-specific ratios
store_ratios = df_clean.groupby('store_id').apply(
    lambda x: x['ad_spend_usd'].sum() / x['lag_sales'].sum()
).reset_index()
store_ratios.columns = ['store_id', 'store_ad_to_sales_ratio']
print(f"\nStore-level ad-to-sales ratios:")
print(f"Mean: {store_ratios['store_ad_to_sales_ratio'].mean():.4f}")
print(f"Std: {store_ratios['store_ad_to_sales_ratio'].std():.4f}")
print(f"Min: {store_ratios['store_ad_to_sales_ratio'].min():.4f}")
print(f"Max: {store_ratios['store_ad_to_sales_ratio'].max():.4f}")

# 2. Analyze effectiveness of ad spend
# Calculate return on ad spend (ROAS)
df_clean['roas'] = (df_clean['sales_revenue_usd'] - df_clean['lag_sales']) / df_clean['ad_spend_usd']

# Remove extreme outliers for ROAS
roas_q1 = df_clean['roas'].quantile(0.01)
roas_q99 = df_clean['roas'].quantile(0.99)
df_clean_filtered = df_clean[(df_clean['roas'] >= roas_q1) & (df_clean['roas'] <= roas_q99)].copy()

print(f"\nReturn on Ad Spend (ROAS) statistics:")
print(f"Mean ROAS: {df_clean_filtered['roas'].mean():.2f} (each $1 ad generates ${df_clean_filtered['roas'].mean():.2f} in incremental sales)")
print(f"Median ROAS: {df_clean_filtered['roas'].median():.2f}")
print(f"Std ROAS: {df_clean_filtered['roas'].std():.2f}")

# 3. Build predictive models for sales
print("\nBuilding predictive models for sales...")

# Prepare features for modeling
model_df = df_clean.copy()

# Create additional features
model_df['month_sin'] = np.sin(2 * np.pi * model_df['month'] / 12)
model_df['month_cos'] = np.cos(2 * np.pi * model_df['month'] / 12)
model_df['population_density'] = model_df['local_population'] / 1000
model_df['traffic_per_pop'] = model_df['foot_traffic'] / model_df['local_population']

# Define features and target
features = ['lag_sales', 'lag_ad_spend', 'is_holiday_month', 
            'foot_traffic', 'local_population', 'competitor_count',
            'month_sin', 'month_cos', 'population_density', 'traffic_per_pop']

X = model_df[features]
y = model_df['sales_revenue_usd']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Training set: {X_train.shape}, Test set: {X_test.shape}")

# Train Random Forest model
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)

y_pred = rf_model.predict(X_test)
rf_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
rf_r2 = r2_score(y_test, y_pred)

print(f"\nRandom Forest Model Performance:")
print(f"RMSE: ${rf_rmse:,.2f}")
print(f"R²: {rf_r2:.4f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nFeature Importance:")
print(feature_importance.to_string(index=False))

# 4. Panel regression model
print("\n\nPanel Regression Analysis...")

# Fixed effects model
model_df['store_factor'] = pd.Categorical(model_df['store_id'])
model_df['time_factor'] = pd.Categorical(model_df['date'])

# Simple OLS with store fixed effects
formula = 'sales_revenue_usd ~ ad_spend_usd + lag_sales + is_holiday_month + foot_traffic + competitor_count + C(store_factor)'
fe_model = smf.ols(formula=formula, data=model_df).fit()
print(fe_model.summary().tables[1])

# Extract ad spend coefficient
ad_coef = fe_model.params.get('ad_spend_usd', 0)
print(f"\nAd spend coefficient: {ad_coef:.4f}")
print(f"Interpretation: Each $1 in ad spend generates ${ad_coef:.2f} in additional sales")

# 5. Budget optimization simulation
print("\n\nBudget Optimization Simulation...")

# Calculate optimal ad spend based on marginal returns
# Assuming diminishing returns: sales = α + β*log(ad_spend)
model_df['log_ad_spend'] = np.log1p(model_df['ad_spend_usd'])

log_model = smf.ols('sales_revenue_usd ~ log_ad_spend + lag_sales + is_holiday_month + foot_traffic + C(store_factor)', 
                    data=model_df).fit()
log_ad_coef = log_model.params.get('log_ad_spend', 0)
print(f"Log model ad coefficient: {log_ad_coef:.2f}")

# Simulate different budget allocation strategies
# Strategy 1: Current policy (fixed % of prior sales)
# Strategy 2: Equal allocation
# Strategy 3: Performance-based allocation

# Get last month's data for each store
last_month_data = model_df.sort_values(['store_id', 'date']).groupby('store_id').tail(1)

# Current policy simulation
current_budget = last_month_data['sales_revenue_usd'].sum() * current_ratio
print(f"\nCurrent policy budget (based on last month sales): ${current_budget:,.2f}")

# Equal allocation
equal_budget_per_store = current_budget / len(last_month_data)
print(f"Equal allocation: ${equal_budget_per_store:,.2f} per store")

# Performance-based allocation (based on historical ROAS)
store_performance = df_clean.groupby('store_id')['roas'].mean().reset_index()
store_performance.columns = ['store_id', 'avg_roas']

# Merge with last month data
budget_df = last_month_data.merge(store_performance, on='store_id', how='left')
budget_df['avg_roas'].fillna(budget_df['avg_roas'].mean(), inplace=True)

# Allocate budget proportional to ROAS
budget_df['performance_weight'] = budget_df['avg_roas'] / budget_df['avg_roas'].sum()
budget_df['performance_budget'] = budget_df['performance_weight'] * current_budget

print(f"\nPerformance-based allocation range: ${budget_df['performance_budget'].min():,.2f} to ${budget_df['performance_budget'].max():,.2f}")
print(f"Performance-based allocation std: ${budget_df['performance_budget'].std():,.2f}")

# 6. Create visualizations
os.makedirs('../report/images', exist_ok=True)

# Plot 1: Store-level ad-to-sales ratios
plt.figure(figsize=(12, 6))
plt.hist(store_ratios['store_ad_to_sales_ratio'], bins=30, edgecolor='black', alpha=0.7)
plt.axvline(store_ratios['store_ad_to_sales_ratio'].mean(), color='red', 
            linestyle='--', linewidth=2, label=f'Mean: {store_ratios["store_ad_to_sales_ratio"].mean():.4f}')
plt.xlabel('Ad-to-Sales Ratio (Ad Spend / Prior Month Sales)')
plt.ylabel('Number of Stores')
plt.title('Distribution of Store-Level Ad-to-Sales Ratios')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('../report/images/store_ad_ratios.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: ROAS distribution
plt.figure(figsize=(12, 6))
plt.hist(df_clean_filtered['roas'], bins=50, edgecolor='black', alpha=0.7)
plt.axvline(df_clean_filtered['roas'].mean(), color='red', 
            linestyle='--', linewidth=2, label=f'Mean ROAS: {df_clean_filtered["roas"].mean():.2f}')
plt.xlabel('Return on Ad Spend (Incremental Sales per $1 Ad Spend)')
plt.ylabel('Frequency')
plt.title('Distribution of Return on Ad Spend (ROAS)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('../report/images/roas_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Feature importance
plt.figure(figsize=(10, 6))
plt.barh(feature_importance['feature'], feature_importance['importance'])
plt.xlabel('Importance')
plt.title('Random Forest Feature Importance for Sales Prediction')
plt.gca().invert_yaxis()
plt.grid(True, alpha=0.3, axis='x')
plt.savefig('../report/images/feature_importance.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 4: Ad spend vs incremental sales
plt.figure(figsize=(10, 6))
plt.scatter(df_clean_filtered['ad_spend_usd'], 
            df_clean_filtered['sales_revenue_usd'] - df_clean_filtered['lag_sales'],
            alpha=0.5, s=20)
plt.xlabel('Ad Spend (USD)')
plt.ylabel('Incremental Sales (Current - Prior Month)')
plt.title('Ad Spend vs Incremental Sales')
plt.grid(True, alpha=0.3)

# Add trend line
z = np.polyfit(df_clean_filtered['ad_spend_usd'], 
               df_clean_filtered['sales_revenue_usd'] - df_clean_filtered['lag_sales'], 1)
p = np.poly1d(z)
plt.plot(df_clean_filtered['ad_spend_usd'], p(df_clean_filtered['ad_spend_usd']), 
         "r--", linewidth=2, label=f'Trend: y = {z[0]:.2f}x + {z[1]:.2f}')
plt.legend()
plt.savefig('../report/images/ad_vs_incremental.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 5: Monthly seasonality
monthly_pattern = model_df.groupby('month').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'is_holiday_month': 'mean'
}).reset_index()

fig, ax1 = plt.subplots(figsize=(12, 6))

color = 'tab:blue'
ax1.set_xlabel('Month')
ax1.set_ylabel('Average Sales Revenue (USD)', color=color)
ax1.plot(monthly_pattern['month'], monthly_pattern['sales_revenue_usd'], 
         marker='o', linewidth=2, color=color, label='Sales')
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_xticks(range(1, 13))

ax2 = ax1.twinx()
color = 'tab:orange'
ax2.set_ylabel('Average Ad Spend (USD)', color=color)
ax2.plot(monthly_pattern['month'], monthly_pattern['ad_spend_usd'], 
         marker='s', linewidth=2, color=color, label='Ad Spend')
ax2.tick_params(axis='y', labelcolor=color)

plt.title('Monthly Seasonality: Sales and Ad Spend Patterns')
fig.tight_layout()
plt.savefig('../report/images/monthly_seasonality.png', dpi=300, bbox_inches='tight')
plt.close()

# Save key results to CSV
results = {
    'current_ad_to_sales_ratio': current_ratio,
    'mean_store_ratio': store_ratios['store_ad_to_sales_ratio'].mean(),
    'std_store_ratio': store_ratios['store_ad_to_sales_ratio'].std(),
    'mean_roas': df_clean_filtered['roas'].mean(),
    'median_roas': df_clean_filtered['roas'].median(),
    'rf_rmse': rf_rmse,
    'rf_r2': rf_r2,
    'fe_ad_coefficient': ad_coef,
    'log_ad_coefficient': log_ad_coef,
    'current_budget': current_budget
}

results_df = pd.DataFrame([results])
results_df.to_csv('../outputs/key_results.csv', index=False)

# Save store-level recommendations
store_recommendations = budget_df[['store_id', 'sales_revenue_usd', 'avg_roas', 
                                   'performance_weight', 'performance_budget']].copy()
store_recommendations['current_policy_budget'] = store_recommendations['sales_revenue_usd'] * current_ratio
store_recommendations['budget_change_pct'] = (store_recommendations['performance_budget'] - 
                                              store_recommendations['current_policy_budget']) / store_recommendations['current_policy_budget'] * 100

store_recommendations.to_csv('../outputs/store_recommendations.csv', index=False)

print("\nAnalysis completed. Results saved to outputs/")
print("Visualizations saved to report/images/")
