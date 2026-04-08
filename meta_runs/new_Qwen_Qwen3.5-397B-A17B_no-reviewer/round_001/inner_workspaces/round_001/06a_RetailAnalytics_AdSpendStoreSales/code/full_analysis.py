import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
df = pd.read_csv('data/store_monthly_sales.csv')

print("=== COMPREHENSIVE RETAIL ANALYTICS ANALYSIS ===")
print(f"Dataset: {df.shape[0]} observations, {df.shape[1]} features")
print(f"Stores: {df['store_id'].nunique()}, Years: {df['year'].nunique()}")

# ============================================================
# 1. DATA EXPLORATION
# ============================================================

# Create figure for data overview
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# 1.1 Ad Spend Distribution
axes[0, 0].hist(df['ad_spend_usd'], bins=50, edgecolor='black', alpha=0.7)
axes[0, 0].set_xlabel('Ad Spend (USD)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Distribution of Ad Spend')
axes[0, 0].axvline(df['ad_spend_usd'].mean(), color='red', linestyle='--', label=f'Mean: ${df["ad_spend_usd"].mean():.0f}')
axes[0, 0].legend()

# 1.2 Sales Revenue Distribution
axes[0, 1].hist(df['sales_revenue_usd'], bins=50, edgecolor='black', alpha=0.7, color='green')
axes[0, 1].set_xlabel('Sales Revenue (USD)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Distribution of Sales Revenue')
axes[0, 1].axvline(df['sales_revenue_usd'].mean(), color='red', linestyle='--', label=f'Mean: ${df["sales_revenue_usd"].mean():.0f}')
axes[0, 1].legend()

# 1.3 Ad Spend vs Sales Revenue Scatter
axes[0, 2].scatter(df['ad_spend_usd'], df['sales_revenue_usd'], alpha=0.3, s=10)
axes[0, 2].set_xlabel('Ad Spend (USD)')
axes[0, 2].set_ylabel('Sales Revenue (USD)')
axes[0, 2].set_title('Ad Spend vs Sales Revenue')

# Calculate correlation
ad_sales_corr = df['ad_spend_usd'].corr(df['sales_revenue_usd'])
axes[0, 2].text(0.05, 0.95, f'Correlation: {ad_sales_corr:.3f}', transform=axes[0, 2].transAxes, 
                fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 1.4 Holiday vs Non-Holiday Ad Spend
holiday_ad = df[df['is_holiday_month'] == 1]['ad_spend_usd']
non_holiday_ad = df[df['is_holiday_month'] == 0]['ad_spend_usd']
axes[1, 0].boxplot([holiday_ad, non_holiday_ad], labels=['Holiday', 'Non-Holiday'])
axes[1, 0].set_ylabel('Ad Spend (USD)')
axes[1, 0].set_title('Ad Spend: Holiday vs Non-Holiday Months')

# 1.5 Holiday vs Non-Holiday Sales
holiday_sales = df[df['is_holiday_month'] == 1]['sales_revenue_usd']
non_holiday_sales = df[df['is_holiday_month'] == 0]['sales_revenue_usd']
axes[1, 1].boxplot([holiday_sales, non_holiday_sales], labels=['Holiday', 'Non-Holiday'])
axes[1, 1].set_ylabel('Sales Revenue (USD)')
axes[1, 1].set_title('Sales Revenue: Holiday vs Non-Holiday Months')

# 1.6 Monthly patterns
monthly_ad = df.groupby('month')['ad_spend_usd'].mean()
monthly_sales = df.groupby('month')['sales_revenue_usd'].mean()
ax = axes[1, 2]
ax.plot(monthly_ad.index, monthly_ad.values, 'o-', label='Ad Spend', linewidth=2)
ax2 = ax.twinx()
ax2.plot(monthly_sales.index, monthly_sales.values, 's-', color='green', label='Sales', linewidth=2)
ax.set_xlabel('Month')
ax.set_ylabel('Ad Spend (USD)', color='blue')
ax2.set_ylabel('Sales Revenue (USD)', color='green')
ax.set_title('Monthly Patterns (Average)')
ax.legend(loc='upper left')
ax2.legend(loc='upper right')

plt.tight_layout()
plt.savefig('report/images/data_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/data_overview.png")

# ============================================================
# 2. AD SPEND TO SALES RATIO ANALYSIS (Policy RET-ADV-ROLL)
# ============================================================

# Calculate ad spend as percentage of sales
df['ad_to_sales_ratio'] = df['ad_spend_usd'] / df['sales_revenue_usd'] * 100

print(f"\n=== AD SPEND TO SALES RATIO ===")
print(f"Mean ratio: {df['ad_to_sales_ratio'].mean():.2f}%")
print(f"Median ratio: {df['ad_to_sales_ratio'].median():.2f}%")
print(f"Std ratio: {df['ad_to_sales_ratio'].std():.2f}%")

# Create figure for ratio analysis
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 2.1 Distribution of Ad-to-Sales Ratio
axes[0, 0].hist(df['ad_to_sales_ratio'], bins=50, edgecolor='black', alpha=0.7, color='orange')
axes[0, 0].set_xlabel('Ad Spend / Sales Ratio (%)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Distribution of Ad-to-Sales Ratio')
axes[0, 0].axvline(df['ad_to_sales_ratio'].mean(), color='red', linestyle='--', label=f'Mean: {df["ad_to_sales_ratio"].mean():.2f}%')
axes[0, 0].legend()

# 2.2 Ratio by Holiday vs Non-Holiday
holiday_ratio = df[df['is_holiday_month'] == 1]['ad_to_sales_ratio']
non_holiday_ratio = df[df['is_holiday_month'] == 0]['ad_to_sales_ratio']
axes[0, 1].boxplot([holiday_ratio, non_holiday_ratio], labels=['Holiday', 'Non-Holiday'])
axes[0, 1].set_ylabel('Ad/Sales Ratio (%)')
axes[0, 1].set_title('Ad-to-Sales Ratio: Holiday vs Non-Holiday')

# 2.3 Ratio over time (by year)
yearly_ratio = df.groupby('year')['ad_to_sales_ratio'].mean()
axes[1, 0].bar(yearly_ratio.index, yearly_ratio.values, color='skyblue', edgecolor='black')
axes[1, 0].set_xlabel('Year')
axes[1, 0].set_ylabel('Ad/Sales Ratio (%)')
axes[1, 0].set_title('Average Ad-to-Sales Ratio by Year')
for i, v in enumerate(yearly_ratio.values):
    axes[1, 0].text(i+1, v+0.1, f'{v:.2f}%', ha='center')

# 2.4 Ratio by store (sample of 20 stores)
sample_stores = df['store_id'].unique()[:20]
store_ratio = df[df['store_id'].isin(sample_stores)].groupby('store_id')['ad_to_sales_ratio'].mean()
axes[1, 1].bar(store_ratio.index, store_ratio.values, color='lightgreen', edgecolor='black')
axes[1, 1].set_xlabel('Store ID')
axes[1, 1].set_ylabel('Ad/Sales Ratio (%)')
axes[1, 1].set_title('Average Ad-to-Sales Ratio by Store (Sample)')
axes[1, 1].axhline(df['ad_to_sales_ratio'].mean(), color='red', linestyle='--', label='Overall Mean')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('report/images/ratio_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/ratio_analysis.png")

# ============================================================
# 3. LAGGED ANALYSIS - Policy RET-ADV-ROLL Implementation
# ============================================================

# Sort by store, year, month
df = df.sort_values(['store_id', 'year', 'month']).reset_index(drop=True)

# Create lagged sales (prior month same-store sales)
df['prev_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df['prev_ad_spend'] = df.groupby('store_id')['ad_spend_usd'].shift(1)

# Calculate what the policy would suggest: ad budget as fixed share of prior month sales
# Let's use the mean ratio as the policy parameter
policy_ratio = df['ad_to_sales_ratio'].mean() / 100  # Convert to decimal
df['policy_ad_spend'] = df['prev_sales'] * policy_ratio

# Drop rows with NaN (first month of each store)
df_lagged = df.dropna(subset=['prev_sales']).copy()

print(f"\n=== LAGGED ANALYSIS (Policy RET-ADV-ROLL) ===")
print(f"Policy ratio (ad spend as % of prior sales): {policy_ratio*100:.2f}%")
print(f"Observations after lagging: {len(df_lagged)}")

# Compare actual vs policy-suggested ad spend
print(f"\nActual Ad Spend vs Policy-Suggested:")
print(f"  Actual mean: ${df_lagged['ad_spend_usd'].mean():.2f}")
print(f"  Policy mean: ${df_lagged['policy_ad_spend'].mean():.2f}")
print(f"  Correlation: {df_lagged['ad_spend_usd'].corr(df_lagged['policy_ad_spend']):.3f}")

# Create figure for lagged analysis
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 3.1 Current Ad Spend vs Prior Sales
axes[0, 0].scatter(df_lagged['prev_sales'], df_lagged['ad_spend_usd'], alpha=0.3, s=10)
axes[0, 0].set_xlabel('Prior Month Sales (USD)')
axes[0, 0].set_ylabel('Current Ad Spend (USD)')
axes[0, 0].set_title('Current Ad Spend vs Prior Month Sales')
prior_sales_corr = df_lagged['prev_sales'].corr(df_lagged['ad_spend_usd'])
axes[0, 0].text(0.05, 0.95, f'Correlation: {prior_sales_corr:.3f}', transform=axes[0, 0].transAxes,
                fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 3.2 Current Sales vs Prior Ad Spend
axes[0, 1].scatter(df_lagged['prev_ad_spend'], df_lagged['sales_revenue_usd'], alpha=0.3, s=10, color='green')
axes[0, 1].set_xlabel('Prior Month Ad Spend (USD)')
axes[0, 1].set_ylabel('Current Sales Revenue (USD)')
axes[0, 1].set_title('Current Sales vs Prior Month Ad Spend')
prior_ad_corr = df_lagged['prev_ad_spend'].corr(df_lagged['sales_revenue_usd'])
axes[0, 1].text(0.05, 0.95, f'Correlation: {prior_ad_corr:.3f}', transform=axes[0, 1].transAxes,
                fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 3.3 Actual vs Policy Ad Spend Comparison
axes[1, 0].scatter(df_lagged['policy_ad_spend'], df_lagged['ad_spend_usd'], alpha=0.3, s=10)
axes[1, 0].plot([df_lagged['policy_ad_spend'].min(), df_lagged['policy_ad_spend'].max()],
                [df_lagged['policy_ad_spend'].min(), df_lagged['policy_ad_spend'].max()], 'r--', label='Perfect Match')
axes[1, 0].set_xlabel('Policy-Suggested Ad Spend (USD)')
axes[1, 0].set_ylabel('Actual Ad Spend (USD)')
axes[1, 0].set_title('Actual vs Policy-Suggested Ad Spend')
axes[1, 0].legend()

# 3.4 Difference between Actual and Policy
axes[1, 1].hist(df_lagged['ad_spend_usd'] - df_lagged['policy_ad_spend'], bins=50, edgecolor='black', alpha=0.7, color='purple')
axes[1, 1].set_xlabel('Difference (Actual - Policy) USD')
axes[1, 1].set_ylabel('Frequency')
axes[1, 1].set_title('Deviation from Policy-Suggested Ad Spend')
axes[1, 1].axvline(0, color='red', linestyle='--', label='Policy Target')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('report/images/lagged_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/lagged_analysis.png")

# ============================================================
# 4. PREDICTIVE MODELING
# ============================================================

print(f"\n=== PREDICTIVE MODELING ===")

# Prepare features for modeling
feature_cols = ['ad_spend_usd', 'is_holiday_month', 'foot_traffic', 'local_population', 'competitor_count']
X = df_lagged[feature_cols].copy()
y = df_lagged['sales_revenue_usd']

# Add lagged features
X['prev_sales'] = df_lagged['prev_sales']
X['prev_ad_spend'] = df_lagged['prev_ad_spend']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Model 1: Linear Regression
lr = LinearRegression()
lr.fit(X_train_scaled, y_train)
y_pred_lr = lr.predict(X_test_scaled)
lr_r2 = r2_score(y_test, y_pred_lr)
lr_rmse = np.sqrt(mean_squared_error(y_test, y_pred_lr))
lr_mae = mean_absolute_error(y_test, y_pred_lr)

print(f"\nLinear Regression:")
print(f"  R²: {lr_r2:.4f}")
print(f"  RMSE: ${lr_rmse:,.2f}")
print(f"  MAE: ${lr_mae:,.2f}")

# Model 2: Random Forest
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)
rf_r2 = r2_score(y_test, y_pred_rf)
rf_rmse = np.sqrt(mean_squared_error(y_test, y_pred_rf))
rf_mae = mean_absolute_error(y_test, y_pred_rf)

print(f"\nRandom Forest:")
print(f"  R²: {rf_r2:.4f}")
print(f"  RMSE: ${rf_rmse:,.2f}")
print(f"  MAE: ${rf_mae:,.2f}")

# Model 3: Gradient Boosting
gb = GradientBoostingRegressor(n_estimators=100, random_state=42)
gb.fit(X_train, y_train)
y_pred_gb = gb.predict(X_test)
gb_r2 = r2_score(y_test, y_pred_gb)
gb_rmse = np.sqrt(mean_squared_error(y_test, y_pred_gb))
gb_mae = mean_absolute_error(y_test, y_pred_gb)

print(f"\nGradient Boosting:")
print(f"  R²: {gb_r2:.4f}")
print(f"  RMSE: ${gb_rmse:,.2f}")
print(f"  MAE: ${gb_mae:,.2f}")

# Feature importance from Random Forest
feature_importance = pd.DataFrame({
    'Feature': feature_cols + ['prev_sales', 'prev_ad_spend'],
    'Importance': rf.feature_importances_
}).sort_values('Importance', ascending=False)

print(f"\nFeature Importance (Random Forest):")
print(feature_importance)

# Create figure for model results
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 4.1 Model Comparison
models = ['Linear Reg', 'Random Forest', 'Gradient Boosting']
r2_scores = [lr_r2, rf_r2, gb_r2]
rmse_scores = [lr_rmse, rf_rmse, gb_rmse]

axes[0, 0].bar(models, r2_scores, color=['blue', 'green', 'orange'], edgecolor='black')
axes[0, 0].set_ylabel('R² Score')
axes[0, 0].set_title('Model Comparison: R² Score')
axes[0, 0].set_ylim(0, 1)
for i, v in enumerate(r2_scores):
    axes[0, 0].text(i, v+0.01, f'{v:.3f}', ha='center')

# 4.2 RMSE Comparison
axes[0, 1].bar(models, rmse_scores, color=['blue', 'green', 'orange'], edgecolor='black')
axes[0, 1].set_ylabel('RMSE (USD)')
axes[0, 1].set_title('Model Comparison: RMSE')
for i, v in enumerate(rmse_scores):
    axes[0, 1].text(i, v+1000, f'${v:,.0f}', ha='center', rotation=45)

# 4.3 Feature Importance
axes[1, 0].barh(feature_importance['Feature'], feature_importance['Importance'], color='steelblue')
axes[1, 0].set_xlabel('Importance')
axes[1, 0].set_title('Feature Importance (Random Forest)')
axes[1, 0].invert_yaxis()

# 4.4 Predicted vs Actual (Best Model - Random Forest)
axes[1, 1].scatter(y_test, y_pred_rf, alpha=0.3, s=10)
axes[1, 1].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', label='Perfect Prediction')
axes[1, 1].set_xlabel('Actual Sales (USD)')
axes[1, 1].set_ylabel('Predicted Sales (USD)')
axes[1, 1].set_title(f'Random Forest: Predicted vs Actual (R²={rf_r2:.3f})')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('report/images/model_results.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/model_results.png")

# ============================================================
# 5. BUDGET RECOMMENDATIONS
# ============================================================

print(f"\n=== BUDGET RECOMMENDATIONS ===")

# Calculate recommended ad spend based on policy for next period
# Using the most recent sales data per store
latest_data = df.sort_values(['store_id', 'year', 'month']).groupby('store_id').last().reset_index()

# Policy-based recommendation
latest_data['recommended_ad_spend'] = latest_data['sales_revenue_usd'] * policy_ratio

print(f"Policy-based budget recommendation (using {policy_ratio*100:.2f}% of prior sales):")
print(f"  Total recommended ad spend: ${latest_data['recommended_ad_spend'].sum():,.2f}")
print(f"  Average per store: ${latest_data['recommended_ad_spend'].mean():,.2f}")

# Create figure for budget recommendations
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 5.1 Recommended vs Actual (last period)
axes[0, 0].scatter(latest_data['ad_spend_usd'], latest_data['recommended_ad_spend'], alpha=0.5, s=20)
axes[0, 0].plot([latest_data['ad_spend_usd'].min(), latest_data['ad_spend_usd'].max()],
                [latest_data['ad_spend_usd'].min(), latest_data['ad_spend_usd'].max()], 'r--', label='Current = Recommended')
axes[0, 0].set_xlabel('Current Ad Spend (USD)')
axes[0, 0].set_ylabel('Recommended Ad Spend (USD)')
axes[0, 0].set_title('Current vs Policy-Recommended Ad Spend')
axes[0, 0].legend()

# 5.2 Distribution of Recommended Ad Spend
axes[0, 1].hist(latest_data['recommended_ad_spend'], bins=30, edgecolor='black', alpha=0.7, color='teal')
axes[0, 1].set_xlabel('Recommended Ad Spend (USD)')
axes[0, 1].set_ylabel('Number of Stores')
axes[0, 1].set_title('Distribution of Recommended Ad Spend')
axes[0, 1].axvline(latest_data['recommended_ad_spend'].mean(), color='red', linestyle='--', 
                   label=f'Mean: ${latest_data["recommended_ad_spend"].mean():,.0f}')
axes[0, 1].legend()

# 5.3 ROI Analysis: Sales per Ad Dollar
df['sales_per_ad_dollar'] = df['sales_revenue_usd'] / df['ad_spend_usd']
roi_by_store = df.groupby('store_id')['sales_per_ad_dollar'].mean().sort_values(ascending=False)

# Top and bottom 10 stores
top_stores = roi_by_store.head(10)
bottom_stores = roi_by_store.tail(10)

axes[1, 0].barh(range(10), top_stores.values, color='green')
axes[1, 0].set_yticks(range(10))
axes[1, 0].set_yticklabels([f'Store {int(s)}' for s in top_stores.index])
axes[1, 0].set_xlabel('Sales per Ad Dollar')
axes[1, 0].set_title('Top 10 Stores by ROI')

axes[1, 1].barh(range(10), bottom_stores.values, color='red')
axes[1, 1].set_yticks(range(10))
axes[1, 1].set_yticklabels([f'Store {int(s)}' for s in bottom_stores.index])
axes[1, 1].set_xlabel('Sales per Ad Dollar')
axes[1, 1].set_title('Bottom 10 Stores by ROI')

plt.tight_layout()
plt.savefig('report/images/budget_recommendations.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/budget_recommendations.png")

# ============================================================
# 6. SAVE SUMMARY STATISTICS
# ============================================================

summary_stats = {
    'total_observations': len(df),
    'num_stores': df['store_id'].nunique(),
    'num_years': df['year'].nunique(),
    'avg_ad_spend': df['ad_spend_usd'].mean(),
    'avg_sales': df['sales_revenue_usd'].mean(),
    'ad_sales_correlation': df['ad_spend_usd'].corr(df['sales_revenue_usd']),
    'avg_ad_to_sales_ratio': df['ad_to_sales_ratio'].mean(),
    'policy_ratio': policy_ratio * 100,
    'best_model': 'Random Forest',
    'best_model_r2': rf_r2,
    'total_recommended_budget': latest_data['recommended_ad_spend'].sum(),
    'avg_recommended_per_store': latest_data['recommended_ad_spend'].mean()
}

# Save summary
with open('outputs/summary_stats.txt', 'w') as f:
    for key, value in summary_stats.items():
        if isinstance(value, float):
            f.write(f"{key}: {value:.4f}\n")
        else:
            f.write(f"{key}: {value}\n")

print(f"\nSummary statistics saved to outputs/summary_stats.txt")

# Save feature importance
feature_importance.to_csv('outputs/feature_importance.csv', index=False)
print("Feature importance saved to outputs/feature_importance.csv")

# Save budget recommendations
budget_rec = latest_data[['store_id', 'sales_revenue_usd', 'ad_spend_usd', 'recommended_ad_spend']].copy()
budget_rec['change_needed'] = budget_rec['recommended_ad_spend'] - budget_rec['ad_spend_usd']
budget_rec.to_csv('outputs/budget_recommendations.csv', index=False)
print("Budget recommendations saved to outputs/budget_recommendations.csv")

print("\n=== ANALYSIS COMPLETE ===")
