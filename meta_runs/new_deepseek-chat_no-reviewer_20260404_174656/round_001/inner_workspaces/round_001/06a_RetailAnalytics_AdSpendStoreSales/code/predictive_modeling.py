import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 12

# Read the data
df = pd.read_csv('../outputs/store_monthly_sales_with_date.csv')
df['date'] = pd.to_datetime(df['date'])

# Create lagged variables for time series analysis
df = df.sort_values(['store_id', 'date'])
df['lag_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df['lag_ad_spend'] = df.groupby('store_id')['ad_spend_usd'].shift(1)
df['lag_foot_traffic'] = df.groupby('store_id')['foot_traffic'].shift(1)

# Create interaction terms and additional features
df['ad_intensity'] = df['ad_spend_usd'] / df['local_population']  # Ad spend per capita
df['competition_intensity'] = df['competitor_count'] / (df['local_population'] / 10000)  # Competitors per 10k people
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

# Drop rows with missing lagged values
df_model = df.dropna(subset=['lag_sales', 'lag_ad_spend', 'lag_foot_traffic']).copy()

print("=== PREDICTIVE MODELING FOR SALES ===")
print(f"Observations for modeling: {len(df_model)}")

# Define features and target
features = ['ad_spend_usd', 'lag_sales', 'lag_ad_spend', 'lag_foot_traffic',
            'foot_traffic', 'local_population', 'competitor_count',
            'is_holiday_month', 'month_sin', 'month_cos', 'ad_intensity',
            'competition_intensity']

X = df_model[features]
y = df_model['sales_revenue_usd']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Training set: {len(X_train)} observations")
print(f"Test set: {len(X_test)} observations")

# 1. Random Forest model
print("\n=== RANDOM FOREST MODEL ===")
rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)

y_pred_rf = rf_model.predict(X_test)
rf_mse = mean_squared_error(y_test, y_pred_rf)
rf_r2 = r2_score(y_test, y_pred_rf)

print(f"Random Forest R²: {rf_r2:.4f}")
print(f"Random Forest RMSE: ${np.sqrt(rf_mse):,.2f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 10 most important features:")
print(feature_importance.head(10))

# 2. Linear regression for interpretability
print("\n=== LINEAR REGRESSION MODEL ===")
# Scale features for linear regression
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Add constant for statsmodels
X_train_sm = sm.add_constant(X_train_scaled)
X_test_sm = sm.add_constant(X_test_scaled)

# Fit OLS model
ols_model = sm.OLS(y_train, X_train_sm).fit()
y_pred_ols = ols_model.predict(X_test_sm)
ols_r2 = r2_score(y_test, y_pred_ols)
ols_mse = mean_squared_error(y_test, y_pred_ols)

print(f"OLS R²: {ols_r2:.4f}")
print(f"OLS RMSE: ${np.sqrt(ols_mse):,.2f}")
print("\nOLS Model Summary:")
print(ols_model.summary().tables[1])

# 3. Calculate marginal returns to ad spend
print("\n=== MARGINAL RETURNS TO AD SPEND ===")
# Use the OLS coefficients to estimate marginal effect
# The coefficient for ad_spend_usd is in standardized units, need to convert back
ad_spend_idx = features.index('ad_spend_usd')
ad_spend_coef = ols_model.params[ad_spend_idx + 1]  # +1 for constant

# Get standard deviation of ad_spend for conversion
ad_spend_std = X_train['ad_spend_usd'].std()
sales_std = y_train.std()

# Marginal effect: dy/dx = coefficient * (std_y / std_x)
marginal_effect = ad_spend_coef * (sales_std / ad_spend_std)
print(f"Marginal return to ad spend: ${marginal_effect:.2f} increase in sales per $1 increase in ad spend")
print(f"This implies an ROI of approximately {marginal_effect:.2f}:1")

# 4. Store-level heterogeneity analysis
print("\n=== STORE-LEVEL HETEROGENEITY ===")
# Estimate store-specific ad effectiveness
store_effects = []
for store_id in df_model['store_id'].unique()[:50]:  # Sample 50 stores for speed
    store_data = df_model[df_model['store_id'] == store_id]
    if len(store_data) > 20:
        X_store = store_data[['ad_spend_usd', 'lag_sales', 'is_holiday_month']]
        X_store = sm.add_constant(X_store)
        y_store = store_data['sales_revenue_usd']
        
        try:
            model_store = sm.OLS(y_store, X_store).fit()
            ad_coef = model_store.params['ad_spend_usd']
            store_effects.append({
                'store_id': store_id,
                'ad_effectiveness': ad_coef,
                'r2': model_store.rsquared,
                'avg_sales': store_data['sales_revenue_usd'].mean(),
                'avg_ad_spend': store_data['ad_spend_usd'].mean()
            })
        except:
            continue

store_effects_df = pd.DataFrame(store_effects)
print(f"Analyzed {len(store_effects_df)} stores")
print(f"Average ad effectiveness: ${store_effects_df['ad_effectiveness'].mean():.2f} sales per $1 ad spend")
print(f"Range: ${store_effects_df['ad_effectiveness'].min():.2f} to ${store_effects_df['ad_effectiveness'].max():.2f}")
print(f"Std dev: ${store_effects_df['ad_effectiveness'].std():.2f}")

# Save store effects for budget allocation
store_effects_df.to_csv('../outputs/store_ad_effectiveness.csv', index=False)

# 5. Optimization: Find optimal ad spend allocation
print("\n=== AD SPEND OPTIMIZATION ===")
# Simple optimization: allocate based on marginal returns
# Assume total budget is fixed at current level
current_total_ad = df_model['ad_spend_usd'].sum()
print(f"Current total monthly ad spend: ${current_total_ad:,.2f}")

# Calculate store efficiency scores
store_stats = df_model.groupby('store_id').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean'
}).reset_index()
store_stats['sales_to_ad_ratio'] = store_stats['sales_revenue_usd'] / store_stats['ad_spend_usd']
store_stats['efficiency_score'] = store_stats['sales_to_ad_ratio'] / store_stats['sales_to_ad_ratio'].max()

# Simple allocation rule: allocate more to efficient stores
store_stats['optimal_share'] = store_stats['efficiency_score'] / store_stats['efficiency_score'].sum()
store_stats['current_share'] = store_stats['ad_spend_usd'] / store_stats['ad_spend_usd'].sum()
store_stats['recommended_ad'] = store_stats['optimal_share'] * current_total_ad
store_stats['change'] = store_stats['recommended_ad'] - store_stats['ad_spend_usd']
store_stats['pct_change'] = (store_stats['change'] / store_stats['ad_spend_usd']) * 100

print("\nBudget reallocation summary:")
print(f"Stores with increased budget: {(store_stats['change'] > 0).sum()}")
print(f"Stores with decreased budget: {(store_stats['change'] < 0).sum()}")
print(f"Maximum increase: {store_stats['pct_change'].max():.1f}%")
print(f"Maximum decrease: {store_stats['pct_change'].min():.1f}%")
print(f"Average change: {store_stats['pct_change'].mean():.1f}%")

# Save optimization results
store_stats.to_csv('../outputs/store_budget_recommendations.csv', index=False)

print("\n=== MODEL VALIDATION ===")
# Cross-validation for Random Forest
cv_scores = cross_val_score(rf_model, X, y, cv=5, scoring='r2')
print(f"Random Forest 5-fold CV R²: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

# Create visualization of predictions vs actual
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: Predictions vs Actual for Random Forest
ax1 = axes[0]
ax1.scatter(y_test / 1000, y_pred_rf / 1000, alpha=0.5, s=20)
ax1.plot([y_test.min()/1000, y_test.max()/1000], [y_test.min()/1000, y_test.max()/1000], 
        'r--', linewidth=2, label='Perfect Prediction')
ax1.set_xlabel('Actual Sales (Thousands USD)')
ax1.set_ylabel('Predicted Sales (Thousands USD)')
ax1.set_title(f'Random Forest Predictions vs Actual (R² = {rf_r2:.3f})')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Feature importance
ax2 = axes[1]
top_features = feature_importance.head(10)
ax2.barh(range(len(top_features)), top_features['importance'])
ax2.set_yticks(range(len(top_features)))
ax2.set_yticklabels(top_features['feature'])
ax2.set_xlabel('Feature Importance')
ax2.set_title('Top 10 Feature Importances (Random Forest)')
ax2.invert_yaxis()  # Most important at top
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/model_performance.png', dpi=300, bbox_inches='tight')
plt.close()

print("Figure saved: model_performance.png")
print("\nModeling complete. Results saved to outputs/ directory.")