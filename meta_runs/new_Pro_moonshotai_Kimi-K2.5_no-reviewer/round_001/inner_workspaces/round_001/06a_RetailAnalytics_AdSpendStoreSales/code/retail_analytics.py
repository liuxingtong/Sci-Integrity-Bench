"""
Retail Analytics: Ad Spend and Store Sales Analysis
Policy RET-ADV-ROLL: Online ad budget = fixed share of prior-month same-store sales
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
print("Loading data...")
df = pd.read_csv('data/store_monthly_sales.csv')
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nMissing values:\n{df.isnull().sum()}")
print(f"\nDuplicated rows: {df.duplicated().sum()}")

# Data overview
print("\n" + "="*60)
print("DATA OVERVIEW")
print("="*60)
print(f"\nNumber of stores: {df['store_id'].nunique()}")
print(f"Number of months: {df['month'].nunique()}")
print(f"Number of years: {df['year'].nunique()}")
print(f"\nNumeric columns summary:\n{df.describe()}")

# Create date column for time series analysis (year 1,2,3 -> 2021,2022,2023)
df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1).assign(year=df['year'] + 2020))
df = df.sort_values(['store_id', 'date']).reset_index(drop=True)

# Calculate key metrics
print("\n" + "="*60)
print("KEY METRICS")
print("="*60)

# ROAS (Return on Ad Spend)
df['roas'] = df['sales_revenue_usd'] / df['ad_spend_usd']
print(f"\nROAS Statistics:")
print(f"  Mean: {df['roas'].mean():.2f}")
print(f"  Median: {df['roas'].median():.2f}")
print(f"  Std: {df['roas'].std():.2f}")

# Ad Spend as % of Sales
df['ad_spend_pct'] = (df['ad_spend_usd'] / df['sales_revenue_usd']) * 100
print(f"\nAd Spend as % of Sales:")
print(f"  Mean: {df['ad_spend_pct'].mean():.2f}%")
print(f"  Median: {df['ad_spend_pct'].median():.2f}%")

# Sales per capita
df['sales_per_capita'] = df['sales_revenue_usd'] / df['local_population']
print(f"\nSales per Capita:")
print(f"  Mean: ${df['sales_per_capita'].mean():.2f}")

# Traffic conversion rate
df['conversion_rate'] = df['sales_revenue_usd'] / df['foot_traffic']
print(f"\nRevenue per Foot Traffic:")
print(f"  Mean: ${df['conversion_rate'].mean():.2f}")

# Save processed data
df.to_csv('outputs/processed_data.csv', index=False)
print("\nProcessed data saved to outputs/processed_data.csv")

# ============================================================================
# POLICY RET-ADV-ROLL ANALYSIS
# ============================================================================
print("\n" + "="*60)
print("POLICY RET-ADV-ROLL ANALYSIS")
print("="*60)

# Create lagged sales for policy analysis
df_sorted = df.sort_values(['store_id', 'year', 'month'])
df_sorted['prior_month_sales'] = df_sorted.groupby('store_id')['sales_revenue_usd'].shift(1)

# Calculate the implied ad spend ratio (ad_spend / prior_month_sales)
df_sorted['implied_ratio'] = df_sorted['ad_spend_usd'] / df_sorted['prior_month_sales']

# Remove first month for each store (no prior month data)
df_policy = df_sorted[df_sorted['prior_month_sales'].notna()].copy()

print(f"\nPolicy Analysis (excluding first month per store):")
print(f"  Observations: {len(df_policy)}")
print(f"  Implied Ad Spend Ratio (ad_spend / prior_month_sales):")
print(f"    Mean: {df_policy['implied_ratio'].mean():.4f} ({df_policy['implied_ratio'].mean()*100:.2f}%)")
print(f"    Median: {df_policy['implied_ratio'].median():.4f} ({df_policy['implied_ratio'].median()*100:.2f}%)")
print(f"    Std: {df_policy['implied_ratio'].std():.4f}")

# Analyze by month to see seasonal patterns
monthly_policy = df_policy.groupby('month').agg({
    'implied_ratio': ['mean', 'std', 'count'],
    'ad_spend_usd': 'mean',
    'sales_revenue_usd': 'mean'
}).round(4)
print(f"\nMonthly Policy Ratios:")
print(monthly_policy)

# ============================================================================
# VISUALIZATION 1: Data Overview
# ============================================================================
print("\nGenerating Figure 1: Data Overview...")

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('Retail Analytics: Data Overview', fontsize=14, fontweight='bold')

# Sales distribution
axes[0, 0].hist(df['sales_revenue_usd'], bins=50, color='steelblue', edgecolor='white', alpha=0.7)
axes[0, 0].set_xlabel('Sales Revenue (USD)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Distribution of Sales Revenue')
axes[0, 0].axvline(df['sales_revenue_usd'].mean(), color='red', linestyle='--', label=f'Mean: ${df["sales_revenue_usd"].mean():,.0f}')
axes[0, 0].legend()

# Ad Spend distribution
axes[0, 1].hist(df['ad_spend_usd'], bins=50, color='forestgreen', edgecolor='white', alpha=0.7)
axes[0, 1].set_xlabel('Ad Spend (USD)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Distribution of Ad Spend')
axes[0, 1].axvline(df['ad_spend_usd'].mean(), color='red', linestyle='--', label=f'Mean: ${df["ad_spend_usd"].mean():,.0f}')
axes[0, 1].legend()

# ROAS distribution
axes[0, 2].hist(df['roas'], bins=50, color='coral', edgecolor='white', alpha=0.7)
axes[0, 2].set_xlabel('ROAS (Return on Ad Spend)')
axes[0, 2].set_ylabel('Frequency')
axes[0, 2].set_title('Distribution of ROAS')
axes[0, 2].axvline(df['roas'].mean(), color='red', linestyle='--', label=f'Mean: {df["roas"].mean():.2f}')
axes[0, 2].legend()

# Sales vs Ad Spend scatter
axes[1, 0].scatter(df['ad_spend_usd'], df['sales_revenue_usd'], alpha=0.5, c='steelblue', s=20)
axes[1, 0].set_xlabel('Ad Spend (USD)')
axes[1, 0].set_ylabel('Sales Revenue (USD)')
axes[1, 0].set_title('Sales vs Ad Spend Relationship')
# Add trend line
z = np.polyfit(df['ad_spend_usd'], df['sales_revenue_usd'], 1)
p = np.poly1d(z)
axes[1, 0].plot(df['ad_spend_usd'], p(df['ad_spend_usd']), "r--", alpha=0.8, label='Trend')
axes[1, 0].legend()

# Monthly seasonality
monthly_sales = df.groupby('month')['sales_revenue_usd'].mean()
axes[1, 1].bar(monthly_sales.index, monthly_sales.values, color='teal', alpha=0.7)
axes[1, 1].set_xlabel('Month')
axes[1, 1].set_ylabel('Average Sales (USD)')
axes[1, 1].set_title('Seasonal Sales Pattern')
axes[1, 1].set_xticks(range(1, 13))

# Holiday vs Non-holiday
holiday_comparison = df.groupby('is_holiday_month').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'roas': 'mean'
})
x = ['Non-Holiday', 'Holiday']
width = 0.35
x_pos = np.arange(len(x))
axes[1, 2].bar(x_pos - width/2, holiday_comparison['sales_revenue_usd']/1000, width, label='Sales (K$)', color='steelblue')
axes[1, 2].bar(x_pos + width/2, holiday_comparison['ad_spend_usd']/1000, width, label='Ad Spend (K$)', color='forestgreen')
axes[1, 2].set_ylabel('Amount (K$)')
axes[1, 2].set_title('Holiday vs Non-Holiday Performance')
axes[1, 2].set_xticks(x_pos)
axes[1, 2].set_xticklabels(x)
axes[1, 2].legend()

plt.tight_layout()
plt.savefig('report/images/figure1_data_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 1 saved.")

# ============================================================================
# VISUALIZATION 2: Policy Analysis
# ============================================================================
print("\nGenerating Figure 2: Policy RET-ADV-ROLL Analysis...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Policy RET-ADV-ROLL: Ad Budget as Share of Prior-Month Sales', fontsize=14, fontweight='bold')

# Implied ratio distribution
axes[0, 0].hist(df_policy['implied_ratio'], bins=50, color='purple', edgecolor='white', alpha=0.7)
axes[0, 0].set_xlabel('Implied Ad Spend Ratio (Ad Spend / Prior Month Sales)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Distribution of Implied Policy Ratios')
axes[0, 0].axvline(df_policy['implied_ratio'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {df_policy["implied_ratio"].mean():.4f}')
axes[0, 0].legend()

# Monthly policy ratios
monthly_ratios = df_policy.groupby('month')['implied_ratio'].mean()
axes[0, 1].plot(monthly_ratios.index, monthly_ratios.values, marker='o', linewidth=2, markersize=8, color='darkgreen')
axes[0, 1].set_xlabel('Month')
axes[0, 1].set_ylabel('Average Implied Ratio')
axes[0, 1].set_title('Monthly Policy Ratios (Seasonality)')
axes[0, 1].set_xticks(range(1, 13))
axes[0, 1].grid(True, alpha=0.3)

# Prior month sales vs current ad spend
axes[1, 0].scatter(df_policy['prior_month_sales'], df_policy['ad_spend_usd'], alpha=0.5, c='darkblue', s=20)
axes[1, 0].set_xlabel('Prior Month Sales (USD)')
axes[1, 0].set_ylabel('Current Month Ad Spend (USD)')
axes[1, 0].set_title('Policy Relationship: Prior Sales → Current Ad Spend')
# Add trend line
z = np.polyfit(df_policy['prior_month_sales'], df_policy['ad_spend_usd'], 1)
p = np.poly1d(z)
axes[1, 0].plot(df_policy['prior_month_sales'], p(df_policy['prior_month_sales']), "r--", alpha=0.8, label='Trend')
axes[1, 0].legend()

# ROAS by implied ratio bins
df_policy['ratio_bin'] = pd.cut(df_policy['implied_ratio'], bins=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
roas_by_ratio = df_policy.groupby('ratio_bin')['roas'].mean()
axes[1, 1].bar(range(len(roas_by_ratio)), roas_by_ratio.values, color='coral', alpha=0.8)
axes[1, 1].set_xlabel('Ad Spend Ratio Bin')
axes[1, 1].set_ylabel('Average ROAS')
axes[1, 1].set_title('ROAS by Ad Spend Ratio Level')
axes[1, 1].set_xticks(range(len(roas_by_ratio)))
axes[1, 1].set_xticklabels(roas_by_ratio.index, rotation=45)

plt.tight_layout()
plt.savefig('report/images/figure2_policy_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved.")

# ============================================================================
# CORRELATION ANALYSIS
# ============================================================================
print("\n" + "="*60)
print("CORRELATION ANALYSIS")
print("="*60)

corr_vars = ['ad_spend_usd', 'sales_revenue_usd', 'foot_traffic', 'local_population', 
             'competitor_count', 'roas', 'ad_spend_pct']
correlation_matrix = df[corr_vars].corr()
print("\nCorrelation Matrix:")
print(correlation_matrix.round(3))

# Generate correlation heatmap
print("\nGenerating Figure 3: Correlation Analysis...")
plt.figure(figsize=(10, 8))
mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
sns.heatmap(correlation_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', 
            center=0, square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
plt.title('Correlation Matrix: Key Variables', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/figure3_correlation_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved.")

# ============================================================================
# PREDICTIVE MODELING
# ============================================================================
print("\n" + "="*60)
print("PREDICTIVE MODELING")
print("="*60)

# Feature engineering for modeling
df_model = df.copy()

# Create lag features
df_model = df_model.sort_values(['store_id', 'year', 'month'])
df_model['sales_lag1'] = df_model.groupby('store_id')['sales_revenue_usd'].shift(1)
df_model['sales_lag2'] = df_model.groupby('store_id')['sales_revenue_usd'].shift(2)
df_model['ad_spend_lag1'] = df_model.groupby('store_id')['ad_spend_usd'].shift(1)

# Create rolling averages
df_model['sales_ma3'] = df_model.groupby('store_id')['sales_revenue_usd'].transform(
    lambda x: x.rolling(window=3, min_periods=1).mean())
df_model['ad_spend_ma3'] = df_model.groupby('store_id')['ad_spend_usd'].transform(
    lambda x: x.rolling(window=3, min_periods=1).mean())

# Month and year as cyclical features
df_model['month_sin'] = np.sin(2 * np.pi * df_model['month'] / 12)
df_model['month_cos'] = np.cos(2 * np.pi * df_model['month'] / 12)

# Remove rows with missing lag features
df_model_clean = df_model.dropna(subset=['sales_lag1', 'sales_lag2', 'ad_spend_lag1']).copy()

print(f"\nModeling dataset: {len(df_model_clean)} observations")

# Define features for sales prediction
feature_cols = ['ad_spend_usd', 'foot_traffic', 'local_population', 'competitor_count',
                'is_holiday_month', 'sales_lag1', 'sales_lag2', 'ad_spend_lag1',
                'sales_ma3', 'ad_spend_ma3', 'month_sin', 'month_cos']

X = df_model_clean[feature_cols]
y = df_model_clean['sales_revenue_usd']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"\nTraining set: {len(X_train)} observations")
print(f"Test set: {len(X_test)} observations")

# Model 1: Linear Regression
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)
lr_pred = lr_model.predict(X_test)
lr_r2 = r2_score(y_test, lr_pred)
lr_rmse = np.sqrt(mean_squared_error(y_test, lr_pred))
lr_mae = mean_absolute_error(y_test, lr_pred)

print(f"\nLinear Regression Results:")
print(f"  R²: {lr_r2:.4f}")
print(f"  RMSE: ${lr_rmse:,.2f}")
print(f"  MAE: ${lr_mae:,.2f}")

# Model 2: Ridge Regression
ridge_model = Ridge(alpha=1.0)
ridge_model.fit(X_train, y_train)
ridge_pred = ridge_model.predict(X_test)
ridge_r2 = r2_score(y_test, ridge_pred)
ridge_rmse = np.sqrt(mean_squared_error(y_test, ridge_pred))
ridge_mae = mean_absolute_error(y_test, ridge_pred)

print(f"\nRidge Regression Results:")
print(f"  R²: {ridge_r2:.4f}")
print(f"  RMSE: ${ridge_rmse:,.2f}")
print(f"  MAE: ${ridge_mae:,.2f}")

# Model 3: Random Forest
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)
rf_r2 = r2_score(y_test, rf_pred)
rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
rf_mae = mean_absolute_error(y_test, rf_pred)

print(f"\nRandom Forest Results:")
print(f"  R²: {rf_r2:.4f}")
print(f"  RMSE: ${rf_rmse:,.2f}")
print(f"  MAE: ${rf_mae:,.2f}")

# Feature importance from Random Forest
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\nTop 5 Most Important Features (Random Forest):")
print(feature_importance.head().to_string(index=False))

# Save model results
model_results = pd.DataFrame({
    'Model': ['Linear Regression', 'Ridge Regression', 'Random Forest'],
    'R2': [lr_r2, ridge_r2, rf_r2],
    'RMSE': [lr_rmse, ridge_rmse, rf_rmse],
    'MAE': [lr_mae, ridge_mae, rf_mae]
})
model_results.to_csv('outputs/model_comparison.csv', index=False)
feature_importance.to_csv('outputs/feature_importance.csv', index=False)

# ============================================================================
# VISUALIZATION 4: Model Performance
# ============================================================================
print("\nGenerating Figure 4: Model Performance...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Predictive Model Performance', fontsize=14, fontweight='bold')

# Actual vs Predicted - Random Forest (best model)
axes[0, 0].scatter(y_test, rf_pred, alpha=0.5, c='steelblue', s=20)
axes[0, 0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
axes[0, 0].set_xlabel('Actual Sales (USD)')
axes[0, 0].set_ylabel('Predicted Sales (USD)')
axes[0, 0].set_title(f'Random Forest: Actual vs Predicted (R²={rf_r2:.3f})')

# Residuals plot
residuals = y_test - rf_pred
axes[0, 1].scatter(rf_pred, residuals, alpha=0.5, c='coral', s=20)
axes[0, 1].axhline(y=0, color='red', linestyle='--')
axes[0, 1].set_xlabel('Predicted Sales (USD)')
axes[0, 1].set_ylabel('Residuals')
axes[0, 1].set_title('Residuals Plot (Random Forest)')

# Feature importance
top_features = feature_importance.head(8)
axes[1, 0].barh(top_features['feature'], top_features['importance'], color='forestgreen', alpha=0.8)
axes[1, 0].set_xlabel('Importance')
axes[1, 0].set_title('Top Feature Importance (Random Forest)')
axes[1, 0].invert_yaxis()

# Model comparison
models = ['Linear Reg', 'Ridge Reg', 'Random Forest']
r2_scores = [lr_r2, ridge_r2, rf_r2]
axes[1, 1].bar(models, r2_scores, color=['steelblue', 'coral', 'forestgreen'], alpha=0.8)
axes[1, 1].set_ylabel('R² Score')
axes[1, 1].set_title('Model Comparison (R²)')
axes[1, 1].set_ylim(0, 1)
for i, v in enumerate(r2_scores):
    axes[1, 1].text(i, v + 0.02, f'{v:.3f}', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/figure4_model_performance.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved.")

# ============================================================================
# BUDGET OPTIMIZATION ANALYSIS
# ============================================================================
print("\n" + "="*60)
print("BUDGET OPTIMIZATION ANALYSIS")
print("="*60)

# Calculate marginal ROAS by ad spend levels
df['ad_spend_quintile'] = pd.qcut(df['ad_spend_usd'], q=5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
quintile_analysis = df.groupby('ad_spend_quintile').agg({
    'ad_spend_usd': ['mean', 'min', 'max'],
    'sales_revenue_usd': 'mean',
    'roas': 'mean',
    'foot_traffic': 'mean'
}).round(2)

print("\nAd Spend Quintile Analysis:")
print(quintile_analysis)

# Calculate elasticity
df_clean = df[(df['ad_spend_usd'] > 0) & (df['sales_revenue_usd'] > 0)].copy()
log_ad_spend = np.log(df_clean['ad_spend_usd'])
log_sales = np.log(df_clean['sales_revenue_usd'])
elasticity_model = LinearRegression()
elasticity_model.fit(log_ad_spend.values.reshape(-1, 1), log_sales)
ad_elasticity = elasticity_model.coef_[0]

print(f"\nAd Spend Elasticity: {ad_elasticity:.4f}")
print(f"Interpretation: 1% increase in ad spend → {ad_elasticity:.2f}% increase in sales")

# Store-level analysis
store_performance = df.groupby('store_id').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'roas': 'mean',
    'foot_traffic': 'mean',
    'local_population': 'mean',
    'competitor_count': 'mean'
}).reset_index()

store_performance['ad_efficiency'] = store_performance['roas']
store_performance['sales_per_capita'] = store_performance['sales_revenue_usd'] / store_performance['local_population']

# Segment stores
store_performance['segment'] = pd.cut(store_performance['roas'], 
                                       bins=3, 
                                       labels=['Low ROAS', 'Medium ROAS', 'High ROAS'])

segment_summary = store_performance.groupby('segment').agg({
    'store_id': 'count',
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'roas': 'mean',
    'foot_traffic': 'mean'
}).round(2)

print(f"\nStore Segmentation by ROAS:")
print(segment_summary)

# Save segment analysis
store_performance.to_csv('outputs/store_performance.csv', index=False)
quintile_analysis.to_csv('outputs/quintile_analysis.csv')

# ============================================================================
# VISUALIZATION 5: Budget Optimization
# ============================================================================
print("\nGenerating Figure 5: Budget Optimization...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Budget Optimization Insights', fontsize=14, fontweight='bold')

# ROAS by ad spend quintile
quintile_roas = df.groupby('ad_spend_quintile')['roas'].mean()
axes[0, 0].bar(quintile_roas.index, quintile_roas.values, color='steelblue', alpha=0.8)
axes[0, 0].set_xlabel('Ad Spend Quintile')
axes[0, 0].set_ylabel('Average ROAS')
axes[0, 0].set_title('ROAS by Ad Spend Level')
for i, v in enumerate(quintile_roas.values):
    axes[0, 0].text(i, v + 0.5, f'{v:.1f}', ha='center', fontweight='bold')

# Sales vs Ad Spend with elasticity line
axes[0, 1].scatter(df_clean['ad_spend_usd'], df_clean['sales_revenue_usd'], alpha=0.3, c='gray', s=10)
# Add trend line
x_trend = np.linspace(df_clean['ad_spend_usd'].min(), df_clean['ad_spend_usd'].max(), 100)
y_trend = np.exp(elasticity_model.intercept_) * (x_trend ** ad_elasticity)
axes[0, 1].plot(x_trend, y_trend, 'r-', linewidth=2, label=f'Elasticity={ad_elasticity:.2f}')
axes[0, 1].set_xlabel('Ad Spend (USD)')
axes[0, 1].set_ylabel('Sales Revenue (USD)')
axes[0, 1].set_title('Sales vs Ad Spend (with Elasticity Curve)')
axes[0, 1].legend()

# Store segments
segment_counts = store_performance['segment'].value_counts()
colors = ['coral', 'gold', 'forestgreen']
axes[1, 0].pie(segment_counts.values, labels=segment_counts.index, autopct='%1.1f%%', 
               colors=colors, startangle=90)
axes[1, 0].set_title('Store Distribution by ROAS Segment')

# Monthly budget recommendation
monthly_stats = df.groupby('month').agg({
    'ad_spend_usd': 'mean',
    'sales_revenue_usd': 'mean',
    'roas': 'mean'
})
x = np.arange(1, 13)
width = 0.35
axes[1, 1].bar(x - width/2, monthly_stats['ad_spend_usd'], width, label='Avg Ad Spend', color='steelblue', alpha=0.8)
ax2 = axes[1, 1].twinx()
ax2.plot(x, monthly_stats['roas'], 'ro-', linewidth=2, markersize=6, label='Avg ROAS')
axes[1, 1].set_xlabel('Month')
axes[1, 1].set_ylabel('Ad Spend (USD)', color='steelblue')
ax2.set_ylabel('ROAS', color='red')
axes[1, 1].set_title('Monthly Ad Spend vs ROAS')
axes[1, 1].set_xticks(x)
axes[1, 1].legend(loc='upper left')
ax2.legend(loc='upper right')

plt.tight_layout()
plt.savefig('report/images/figure5_budget_optimization.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 5 saved.")

# ============================================================================
# BUDGET RECOMMENDATIONS
# ============================================================================
print("\n" + "="*60)
print("BUDGET RECOMMENDATIONS")
print("="*60)

# Calculate recommended budget ratios by month
monthly_recommendations = df.groupby('month').agg({
    'ad_spend_usd': ['mean', 'std'],
    'sales_revenue_usd': 'mean',
    'roas': ['mean', 'std']
}).round(4)

# Calculate optimal ad spend ratio based on ROAS
# Higher ROAS months should get proportionally more budget
avg_roas = df.groupby('month')['roas'].mean()
roas_weights = avg_roas / avg_roas.sum()

print("\nMonthly Budget Allocation Recommendations:")
print("-" * 60)
print(f"{'Month':<8} {'Avg ROAS':<12} {'Weight':<10} {'Rec. Ratio':<12}")
print("-" * 60)

monthly_budget_ratios = {}
for month in range(1, 13):
    weight = roas_weights[month]
    # Base ratio on historical performance
    base_ratio = df_policy[df_policy['month'] == month]['implied_ratio'].mean() if 'implied_ratio' in df_policy.columns else 0.025
    if pd.isna(base_ratio):
        base_ratio = df_policy['implied_ratio'].mean()
    
    # Adjust based on ROAS performance
    recommended_ratio = base_ratio * (1 + (weight - 1/12) * 2)  # Adjust up/down based on performance
    monthly_budget_ratios[month] = recommended_ratio
    print(f"{month:<8} {avg_roas[month]:<12.2f} {weight:<10.4f} {recommended_ratio:<12.4f}")

# Portfolio-level recommendations
total_historical_ad_spend = df['ad_spend_usd'].sum()
avg_monthly_ad_spend = df.groupby(['year', 'month'])['ad_spend_usd'].sum().mean()
total_stores = df['store_id'].nunique()

print(f"\n" + "="*60)
print("PORTFOLIO-LEVEL SUMMARY")
print("="*60)
print(f"Total Stores: {total_stores}")
print(f"Total Historical Ad Spend: ${total_historical_ad_spend:,.2f}")
print(f"Average Monthly Portfolio Ad Spend: ${avg_monthly_ad_spend:,.2f}")
print(f"Average Store Monthly Ad Spend: ${df['ad_spend_usd'].mean():,.2f}")
print(f"Overall Average ROAS: {df['roas'].mean():.2f}")
print(f"Ad Spend Elasticity: {ad_elasticity:.4f}")

# Save recommendations
recommendations_df = pd.DataFrame({
    'month': range(1, 13),
    'avg_roas': [avg_roas[m] for m in range(1, 13)],
    'allocation_weight': [roas_weights[m] for m in range(1, 13)],
    'recommended_ratio': [monthly_budget_ratios[m] for m in range(1, 13)]
})
recommendations_df.to_csv('outputs/budget_recommendations.csv', index=False)

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print("\nOutput files generated:")
print("  - outputs/processed_data.csv")
print("  - outputs/model_comparison.csv")
print("  - outputs/feature_importance.csv")
print("  - outputs/store_performance.csv")
print("  - outputs/quintile_analysis.csv")
print("  - outputs/budget_recommendations.csv")
print("\nFigures generated:")
print("  - report/images/figure1_data_overview.png")
print("  - report/images/figure2_policy_analysis.png")
print("  - report/images/figure3_correlation_matrix.png")
print("  - report/images/figure4_model_performance.png")
print("  - report/images/figure5_budget_optimization.png")
