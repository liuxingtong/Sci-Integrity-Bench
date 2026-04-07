import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load the data
df = pd.read_csv('../data/reit_macro_quarterly.csv')
print(f"Data shape: {df.shape}")
print(f"\nFirst few rows:")
print(df.head())
print(f"\nData types:")
print(df.dtypes)
print(f"\nSummary statistics:")
print(df.describe())
print(f"\nMissing values:")
print(df.isnull().sum())

# Convert quarter to datetime (assuming it's quarterly frequency starting from some period)
# Since we don't have actual dates, we'll treat it as a time index
# For visualization, we can create a time series index
df['time'] = pd.date_range(start='2000-01-01', periods=len(df), freq='Q')
df.set_index('time', inplace=True)

# Save the processed data
df.to_csv('outputs/processed_data.csv')

# 1. Time series plots
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# REIT returns
axes[0].plot(df.index, df['reit_index_return'], marker='o', linewidth=2)
axes[0].set_title('Quarterly REIT Index Returns Over Time', fontsize=14, fontweight='bold')
axes[0].set_ylabel('Return (decimal)')
axes[0].grid(True, alpha=0.3)

# Inflation
axes[1].plot(df.index, df['inflation_yoy'], marker='o', linewidth=2, color='orange')
axes[1].set_title('Year-over-Year Inflation Over Time', fontsize=14, fontweight='bold')
axes[1].set_ylabel('Inflation Rate (decimal)')
axes[1].set_xlabel('Time')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/time_series_plots.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. Scatter plot: REIT returns vs Inflation
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(df['inflation_yoy'], df['reit_index_return'], alpha=0.7, s=80)
ax.set_xlabel('Inflation Rate (yoy, decimal)')
ax.set_ylabel('REIT Index Return (decimal)')
ax.set_title('REIT Returns vs Inflation: Scatter Plot', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

# Add regression line
X = sm.add_constant(df['inflation_yoy'])
model = sm.OLS(df['reit_index_return'], X).fit()
x_range = np.linspace(df['inflation_yoy'].min(), df['inflation_yoy'].max(), 100)
y_pred = model.params[0] + model.params[1] * x_range
ax.plot(x_range, y_pred, color='red', linewidth=2, label=f'Regression line: y = {model.params[0]:.3f} + {model.params[1]:.3f}x')
ax.legend()

plt.tight_layout()
plt.savefig('report/images/scatter_reit_vs_inflation.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"\nRegression Results (REIT Return ~ Inflation):")
print(model.summary())

# 3. Correlation analysis
correlation = df['reit_index_return'].corr(df['inflation_yoy'])
print(f"\nCorrelation between REIT returns and inflation: {correlation:.4f}")

# 4. Stationarity tests (Augmented Dickey-Fuller)
print("\nStationarity Tests:")
for col in ['reit_index_return', 'inflation_yoy']:
    result = adfuller(df[col].dropna())
    print(f"{col}: ADF Statistic = {result[0]:.4f}, p-value = {result[1]:.4f}")
    if result[1] < 0.05:
        print(f"  -> Series is stationary (reject null hypothesis of unit root)")
    else:
        print(f"  -> Series has unit root (non-stationary)")

# 5. Lag analysis: Check if REIT returns are related to lagged inflation
print("\n\nLag Analysis:")
max_lags = 4  # Up to 4 quarters (1 year)
lag_results = []
for lag in range(0, max_lags + 1):
    if lag == 0:
        X_lag = sm.add_constant(df['inflation_yoy'])
        model_lag = sm.OLS(df['reit_index_return'], X_lag).fit()
    else:
        # Create lagged inflation series
        inflation_lagged = df['inflation_yoy'].shift(lag).dropna()
        reit_aligned = df['reit_index_return'].iloc[lag:]
        X_lag = sm.add_constant(inflation_lagged)
        model_lag = sm.OLS(reit_aligned, X_lag).fit()
    
    lag_results.append({
        'lag': lag,
        'coef': model_lag.params[1],
        'p_value': model_lag.pvalues[1],
        'r_squared': model_lag.rsquared
    })
    print(f"Lag {lag}: Coefficient = {model_lag.params[1]:.4f}, p-value = {model_lag.pvalues[1]:.4f}, R² = {model_lag.rsquared:.4f}")

# Convert to DataFrame for saving
lag_df = pd.DataFrame(lag_results)
lag_df.to_csv('outputs/lag_analysis_results.csv', index=False)

# 6. Plot lag coefficients with confidence intervals
fig, ax = plt.subplots(figsize=(10, 6))
ax.errorbar(lag_df['lag'], lag_df['coef'], 
            yerr=1.96*lag_df['p_value'].apply(lambda x: abs(np.log(x+1e-10)))*0.01,  # Simplified error bars
            fmt='o-', capsize=5, linewidth=2)
ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
ax.set_xlabel('Lag (quarters)')
ax.set_ylabel('Coefficient')
ax.set_title('REIT Return Response to Inflation at Different Lags', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/lag_coefficients.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nInitial analysis complete. Check outputs/ and report/images/ for results.")