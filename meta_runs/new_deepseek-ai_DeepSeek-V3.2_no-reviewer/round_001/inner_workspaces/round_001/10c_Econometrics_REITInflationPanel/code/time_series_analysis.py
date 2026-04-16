import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.tsa.api as tsa
from statsmodels.tsa.stattools import adfuller
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
data_path = '../data/reit_macro_quarterly.csv'
df = pd.read_csv(data_path)

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

print("=== TIME SERIES ANALYSIS ===\n")

# 1. Check stationarity
print("1. STATIONARITY TESTS")
for col in ['inflation_yoy', 'reit_index_return']:
    result = adfuller(df[col])
    print(f"\n{col}:")
    print(f"  ADF Statistic: {result[0]:.4f}")
    print(f"  p-value: {result[1]:.4f}")
    print(f"  Stationary at 5% level: {result[1] < 0.05}")
    print(f"  Critical values:")
    for key, value in result[4].items():
        print(f"    {key}: {value:.4f}")

# 2. Time trend analysis
print("\n2. TIME TREND ANALYSIS")
# Add time trend
df['time_trend'] = np.arange(len(df))

# Model with time trend
X_trend = sm.add_constant(df[['inflation_yoy', 'time_trend']])
y = df['reit_index_return']
model_trend = sm.OLS(y, X_trend).fit()

print("Model with time trend:")
print(f"  Inflation coefficient: {model_trend.params['inflation_yoy']:.4f}")
print(f"  Inflation p-value: {model_trend.pvalues['inflation_yoy']:.4f}")
print(f"  Time trend coefficient: {model_trend.params['time_trend']:.4f}")
print(f"  Time trend p-value: {model_trend.pvalues['time_trend']:.4f}")
print(f"  R-squared: {model_trend.rsquared:.4f}")

# Compare with model without trend
X_no_trend = sm.add_constant(df['inflation_yoy'])
model_no_trend = sm.OLS(y, X_no_trend).fit()
print(f"\nModel without time trend (for comparison):")
print(f"  Inflation coefficient: {model_no_trend.params['inflation_yoy']:.4f}")
print(f"  R-squared: {model_no_trend.rsquared:.4f}")

# 3. Rolling regression to see if relationship changes over time
print("\n3. ROLLING REGRESSION ANALYSIS")
window_size = 16  # 4 years of quarterly data

rolling_slopes = []
rolling_intercepts = []
rolling_rsquared = []

for i in range(window_size, len(df)):
    window_df = df.iloc[i-window_size:i]
    X_window = sm.add_constant(window_df['inflation_yoy'])
    y_window = window_df['reit_index_return']
    model_window = sm.OLS(y_window, X_window).fit()
    
    rolling_slopes.append(model_window.params['inflation_yoy'])
    rolling_intercepts.append(model_window.params['const'])
    rolling_rsquared.append(model_window.rsquared)

# Create dataframe for rolling results
rolling_results = pd.DataFrame({
    'quarter': df['quarter'].iloc[window_size:].values,
    'slope': rolling_slopes,
    'intercept': rolling_intercepts,
    'rsquared': rolling_rsquared
})

# Plot rolling slope
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Rolling slope
axes[0, 0].plot(rolling_results['quarter'], rolling_results['slope'], marker='o', linewidth=2)
axes[0, 0].axhline(y=model_no_trend.params['inflation_yoy'], color='r', linestyle='--', 
                   label=f'Overall slope: {model_no_trend.params["inflation_yoy"]:.3f}')
axes[0, 0].set_title(f'Rolling Slope (Window = {window_size} Quarters)', fontsize=13)
axes[0, 0].set_xlabel('Quarter')
axes[0, 0].set_ylabel('Slope Coefficient')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Rolling R-squared
axes[0, 1].plot(rolling_results['quarter'], rolling_results['rsquared'], marker='o', linewidth=2, color='green')
axes[0, 1].axhline(y=model_no_trend.rsquared, color='r', linestyle='--', 
                   label=f'Overall R²: {model_no_trend.rsquared:.3f}')
axes[0, 1].set_title(f'Rolling R-squared (Window = {window_size} Quarters)', fontsize=13)
axes[0, 1].set_xlabel('Quarter')
axes[0, 1].set_ylabel('R-squared')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Rolling intercept
axes[1, 0].plot(rolling_results['quarter'], rolling_results['intercept'], marker='o', linewidth=2, color='purple')
axes[1, 0].axhline(y=model_no_trend.params['const'], color='r', linestyle='--', 
                   label=f'Overall intercept: {model_no_trend.params["const"]:.3f}')
axes[1, 0].set_title(f'Rolling Intercept (Window = {window_size} Quarters)', fontsize=13)
axes[1, 0].set_xlabel('Quarter')
axes[1, 0].set_ylabel('Intercept')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Distribution of rolling slopes
axes[1, 1].hist(rolling_results['slope'], bins=10, edgecolor='black', alpha=0.7)
axes[1, 1].axvline(x=model_no_trend.params['inflation_yoy'], color='r', linestyle='--', 
                   linewidth=2, label=f'Overall slope')
axes[1, 1].set_title('Distribution of Rolling Slopes', fontsize=13)
axes[1, 1].set_xlabel('Slope Coefficient')
axes[1, 1].set_ylabel('Frequency')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/rolling_regression.png', dpi=300, bbox_inches='tight')
plt.close()
print("Rolling regression plots saved.")

# 4. Granger causality test (simplified version)
print("\n4. GRANGER CAUSALITY ANALYSIS (Simplified)")
# Create lagged variables for Granger test
df_granger = df.copy()
for lag in [1, 2, 3, 4]:  # Up to 4 quarters
    df_granger[f'inflation_lag{lag}'] = df_granger['inflation_yoy'].shift(lag)
    df_granger[f'reit_lag{lag}'] = df_granger['reit_index_return'].shift(lag)

df_granger = df_granger.dropna().copy()

print("Testing if inflation Granger-causes REIT returns:")
for lag in [1, 2, 3, 4]:
    # Restricted model (only REIT lags)
    reit_lag_cols = [f'reit_lag{i}' for i in range(1, lag+1)]
    X_restricted = sm.add_constant(df_granger[reit_lag_cols])
    model_restricted = sm.OLS(df_granger['reit_index_return'], X_restricted).fit()
    
    # Unrestricted model (REIT lags + inflation lags)
    inflation_lag_cols = [f'inflation_lag{i}' for i in range(1, lag+1)]
    X_unrestricted = sm.add_constant(df_granger[reit_lag_cols + inflation_lag_cols])
    model_unrestricted = sm.OLS(df_granger['reit_index_return'], X_unrestricted).fit()
    
    # F-test
    ssr_restricted = model_restricted.ssr
    ssr_unrestricted = model_unrestricted.ssr
    n = len(df_granger)
    k = len(inflation_lag_cols)  # number of restrictions
    
    f_stat = ((ssr_restricted - ssr_unrestricted) / k) / (ssr_unrestricted / (n - len(X_unrestricted.columns)))
    
    # Calculate p-value
    from scipy.stats import f
    p_value = 1 - f.cdf(f_stat, k, n - len(X_unrestricted.columns))
    
    print(f"  Lag {lag}: F-stat = {f_stat:.4f}, p-value = {p_value:.4f}")
    print(f"    Significant at 5% level: {p_value < 0.05}")

# 5. Forecast evaluation
print("\n5. FORECAST EVALUATION")
# Simple out-of-sample forecast
train_size = int(len(df) * 0.7)  # 70% for training
train_df = df.iloc[:train_size]
test_df = df.iloc[train_size:]

# Train model
X_train = sm.add_constant(train_df['inflation_yoy'])
y_train = train_df['reit_index_return']
model_train = sm.OLS(y_train, X_train).fit()

# Make predictions on test set
X_test = sm.add_constant(test_df['inflation_yoy'])
y_test = test_df['reit_index_return']
y_pred = model_train.predict(X_test)

# Calculate forecast errors
forecast_errors = y_test - y_pred
mse = np.mean(forecast_errors**2)
mae = np.mean(np.abs(forecast_errors))
rmse = np.sqrt(mse)

print(f"Training sample: {len(train_df)} observations")
print(f"Test sample: {len(test_df)} observations")
print(f"\nForecast accuracy metrics:")
print(f"  Mean Squared Error (MSE): {mse:.6f}")
print(f"  Root Mean Squared Error (RMSE): {rmse:.6f}")
print(f"  Mean Absolute Error (MAE): {mae:.6f}")

# Plot actual vs predicted
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(test_df['quarter'], y_test, label='Actual', alpha=0.7, s=80)
ax.scatter(test_df['quarter'], y_pred, label='Predicted', alpha=0.7, s=80, marker='s')
ax.set_title('Out-of-Sample Forecast: Actual vs Predicted REIT Returns', fontsize=14)
ax.set_xlabel('Quarter')
ax.set_ylabel('REIT Return')
ax.legend()
ax.grid(True, alpha=0.3)

# Add error bars
for i, (actual, pred, quarter) in enumerate(zip(y_test, y_pred, test_df['quarter'])):
    ax.plot([quarter, quarter], [actual, pred], 'k-', alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/forecast_evaluation.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nForecast evaluation plot saved.")

print("\n=== TIME SERIES ANALYSIS COMPLETE ===")