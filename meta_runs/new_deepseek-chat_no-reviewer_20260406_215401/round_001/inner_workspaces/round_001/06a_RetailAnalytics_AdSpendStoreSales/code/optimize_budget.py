import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
df = pd.read_csv('../outputs/store_monthly_sales_with_date.csv')
df['date'] = pd.to_datetime(df['date'])

print("=== Budget Optimization for Next Year ===")
print(f"Data shape: {df.shape}")

# Prepare data for modeling
df = df.sort_values(['store_id', 'date'])

# Create features
df['sales_lag1'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df['sales_lag2'] = df.groupby('store_id')['sales_revenue_usd'].shift(2)
df['ad_spend_lag1'] = df.groupby('store_id')['ad_spend_usd'].shift(1)
df['ad_spend_lag2'] = df.groupby('store_id')['ad_spend_usd'].shift(2)
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

# Drop rows with NaN
df_model = df.dropna(subset=['sales_lag1', 'sales_lag2', 'ad_spend_lag1', 'ad_spend_lag2']).copy()

print(f"Rows available for modeling: {len(df_model)}")

# Train a model to predict sales based on ad spend and other factors
features = ['ad_spend_usd', 'ad_spend_lag1', 'ad_spend_lag2', 
            'sales_lag1', 'sales_lag2', 'is_holiday_month',
            'foot_traffic', 'local_population', 'competitor_count',
            'month_sin', 'month_cos']

X = df_model[features]
y = df_model['sales_revenue_usd']

# Train Random Forest model
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X, y)

print("\nModel trained successfully.")

# 1. Analyze current policy performance
print("\n=== Current Policy Performance ===")

# Calculate current ad share (policy RET-ADV-ROLL)
df_model['ad_share_actual'] = df_model['ad_spend_usd'] / df_model['sales_lag1']
current_ad_share = df_model['ad_share_actual'].mean()
print(f"Current policy: Ad spend = {current_ad_share:.4f} * prior month sales")
print(f"Average ad share across stores: {current_ad_share:.4f}")
print(f"Range across stores: {df_model.groupby('store_id')['ad_share_actual'].mean().min():.4f} to {df_model.groupby('store_id')['ad_share_actual'].mean().max():.4f}")

# Calculate predicted sales with current policy
current_pred_sales = rf.predict(X)
df_model['predicted_sales'] = current_pred_sales

# Calculate total ad spend and sales
total_ad_current = df_model['ad_spend_usd'].sum()
total_sales_current = df_model['sales_revenue_usd'].sum()
total_pred_sales_current = df_model['predicted_sales'].sum()

print(f"\nTotal ad spend (historical): ${total_ad_current:,.2f}")
print(f"Total sales (historical): ${total_sales_current:,.2f}")
print(f"Predicted sales (model): ${total_pred_sales_current:,.2f}")
print(f"Ad-to-sales ratio: {total_ad_current/total_sales_current:.4f}")

# 2. Estimate optimal ad spend share for each store
print("\n=== Store-Level Optimization ===")

# For each store, find optimal ad share that maximizes profit
# Assume profit = sales - ad_spend (ignoring other costs for simplicity)

store_results = []
store_ids = df_model['store_id'].unique()

for store_id in store_ids[:50]:  # Limit to 50 stores for demonstration
    store_data = df_model[df_model['store_id'] == store_id]
    if len(store_data) < 12:  # Need enough data
        continue
    
    # Use the most recent observation as baseline
    latest = store_data.iloc[-1:].copy()
    
    # Function to calculate profit for a given ad share
    def calculate_profit(ad_share):
        # Create test data with new ad spend
        test_data = latest.copy()
        test_data['ad_spend_usd'] = test_data['sales_lag1'] * ad_share
        
        # Predict sales
        X_test = test_data[features]
        predicted_sales = rf.predict(X_test)[0]
        
        # Profit = sales - ad_spend
        profit = predicted_sales - test_data['ad_spend_usd'].iloc[0]
        return -profit  # Negative for minimization
    
    # Find optimal ad share (between 0.01 and 0.1)
    try:
        result = minimize(calculate_profit, x0=[current_ad_share], 
                         bounds=[(0.01, 0.1)], method='L-BFGS-B')
        optimal_share = result.x[0]
        optimal_profit = -result.fun
        
        # Current profit
        current_profit = latest['sales_revenue_usd'].iloc[0] - latest['ad_spend_usd'].iloc[0]
        
        store_results.append({
            'store_id': store_id,
            'current_ad_share': latest['ad_share_actual'].iloc[0],
            'optimal_ad_share': optimal_share,
            'current_profit': current_profit,
            'optimal_profit': optimal_profit,
            'profit_improvement': (optimal_profit - current_profit) / current_profit * 100
        })
    except:
        continue

df_store_opt = pd.DataFrame(store_results)
print(f"Optimized {len(df_store_opt)} stores.")

print("\nStore optimization summary:")
print(df_store_opt[['store_id', 'current_ad_share', 'optimal_ad_share', 'profit_improvement']].head(10).to_string(index=False))

print(f"\nAverage current ad share: {df_store_opt['current_ad_share'].mean():.4f}")
print(f"Average optimal ad share: {df_store_opt['optimal_ad_share'].mean():.4f}")
print(f"Average profit improvement: {df_store_opt['profit_improvement'].mean():.2f}%")

# Save store optimization results
df_store_opt.to_csv('../outputs/store_level_optimization.csv', index=False)
print("\nStore optimization results saved to ../outputs/store_level_optimization.csv")

# 3. Portfolio-level optimization (fixed total budget)
print("\n=== Portfolio-Level Optimization ===")

# Total budget for next year (based on historical average)
total_budget = df_model['ad_spend_usd'].sum() / 3  # Average annual budget
print(f"\nAnnual ad budget for optimization: ${total_budget:,.2f}")

# Get store characteristics for weighting
store_chars = df_model.groupby('store_id').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'local_population': 'mean',
    'foot_traffic': 'mean',
    'competitor_count': 'mean'
}).reset_index()

# Calculate store weights based on historical sales
store_chars['weight'] = store_chars['sales_revenue_usd'] / store_chars['sales_revenue_usd'].sum()

# Simple allocation strategies:
# 1. Equal allocation
# 2. Proportional to historical sales
# 3. Proportional to population
# 4. Proportional to foot traffic
# 5. Optimal based on marginal ROI

allocations = {}
allocations['equal'] = np.ones(len(store_chars)) / len(store_chars)
allocations['sales_proportional'] = store_chars['weight'].values
allocations['population_proportional'] = store_chars['local_population'] / store_chars['local_population'].sum()
allocations['traffic_proportional'] = store_chars['foot_traffic'] / store_chars['foot_traffic'].sum()

# Calculate predicted sales for each allocation
allocation_results = []

for alloc_name, alloc_weights in allocations.items():
    # Allocate budget
    store_budgets = alloc_weights * total_budget
    
    # Estimate total sales (simplified - using average ROI)
    # Use average marginal ROI from previous analysis: ~11.0
    avg_marginal_roi = 11.0
    estimated_sales_increase = store_budgets.sum() * avg_marginal_roi
    
    # Baseline sales (historical average)
    baseline_sales = store_chars['sales_revenue_usd'].sum() * 12  # Annualize
    
    estimated_total_sales = baseline_sales + estimated_sales_increase
    
    allocation_results.append({
        'allocation_strategy': alloc_name,
        'total_budget': total_budget,
        'estimated_sales': estimated_total_sales,
        'estimated_roi': estimated_sales_increase / total_budget,
        'sales_per_dollar': estimated_total_sales / total_budget
    })

df_alloc = pd.DataFrame(allocation_results)
print("\nAllocation Strategy Comparison:")
print(df_alloc.to_string(index=False))

# 4. Monthly budget planning
print("\n=== Monthly Budget Planning ===")

# Analyze seasonal patterns
monthly_patterns = df_model.groupby('month').agg({
    'sales_revenue_usd': 'mean',
    'ad_spend_usd': 'mean',
    'is_holiday_month': 'mean',
    'foot_traffic': 'mean'
}).reset_index()

# Calculate optimal monthly allocation based on historical effectiveness
# Months with higher historical ROI should get more budget

# Calculate ROI by month (simplified)
monthly_roi = []
for month in range(1, 13):
    month_data = df_model[df_model['month'] == month]
    if len(month_data) > 0:
        # Simple ROI calculation: sales / ad_spend
        roi = month_data['sales_revenue_usd'].sum() / month_data['ad_spend_usd'].sum()
        monthly_roi.append({'month': month, 'roi': roi})

df_monthly_roi = pd.DataFrame(monthly_roi)

# Normalize ROI to get allocation weights
df_monthly_roi['weight'] = df_monthly_roi['roi'] / df_monthly_roi['roi'].sum()

print("\nMonthly ROI and Recommended Allocation:")
print(df_monthly_roi.to_string(index=False))

# Save monthly planning
df_monthly_roi.to_csv('../outputs/monthly_budget_allocation.csv', index=False)
print("\nMonthly allocation plan saved to ../outputs/monthly_budget_allocation.csv")

# 5. Create visualizations
print("\n=== Creating Optimization Visualizations ===")

# Figure 1: Current vs Optimal Ad Share by Store
plt.figure(figsize=(12, 6))
plt.scatter(df_store_opt['store_id'], df_store_opt['current_ad_share'], 
            alpha=0.7, label='Current', s=50)
plt.scatter(df_store_opt['store_id'], df_store_opt['optimal_ad_share'], 
            alpha=0.7, label='Optimal', s=50, marker='^')
plt.xlabel('Store ID')
plt.ylabel('Ad Spend Share of Prior Month Sales')
plt.title('Current vs Optimal Ad Spend Allocation by Store')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/current_vs_optimal_ad_share.png', dpi=300)
plt.close()

# Figure 2: Profit Improvement Distribution
plt.figure(figsize=(10, 6))
plt.hist(df_store_opt['profit_improvement'], bins=20, edgecolor='black', alpha=0.7)
plt.xlabel('Profit Improvement (%)')
plt.ylabel('Number of Stores')
plt.title('Distribution of Potential Profit Improvement from Optimal Ad Allocation')
plt.axvline(df_store_opt['profit_improvement'].mean(), color='red', 
            linestyle='--', label=f'Mean: {df_store_opt["profit_improvement"].mean():.1f}%')
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/profit_improvement_distribution.png', dpi=300)
plt.close()

# Figure 3: Monthly ROI Pattern
plt.figure(figsize=(10, 6))
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
plt.bar(df_monthly_roi['month'] - 1, df_monthly_roi['roi'], 
        color='skyblue', edgecolor='black')
plt.xticks(range(12), months, rotation=45)
plt.xlabel('Month')
plt.ylabel('ROI (Sales / Ad Spend)')
plt.title('Historical ROI by Month')
plt.tight_layout()
plt.savefig('../report/images/monthly_roi_pattern.png', dpi=300)
plt.close()

# Figure 4: Allocation Strategy Comparison
plt.figure(figsize=(10, 6))
strategies = df_alloc['allocation_strategy']
sales_per_dollar = df_alloc['sales_per_dollar']

bars = plt.bar(range(len(strategies)), sales_per_dollar, 
               color=['blue', 'green', 'orange', 'red'], edgecolor='black')
plt.xticks(range(len(strategies)), strategies, rotation=45)
plt.ylabel('Estimated Sales per Ad Dollar')
plt.title('Allocation Strategy Efficiency Comparison')

# Add value labels on bars
for bar, value in zip(bars, sales_per_dollar):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
             f'{value:.1f}', ha='center', va='bottom')

plt.tight_layout()
plt.savefig('../report/images/allocation_strategy_comparison.png', dpi=300)
plt.close()

print("\nOptimization visualizations saved to ../report/images/")
print("\n=== Optimization Complete ===")