import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
df = pd.read_csv('../data/reit_macro_quarterly.csv')

# Convert quarter to datetime (assuming quarterly frequency starting from some date)
# We'll create a time index for visualization
df['date'] = pd.date_range(start='2010-01-01', periods=len(df), freq='Q')
df.set_index('date', inplace=True)

print("=== ECONOMETRIC ANALYSIS OF REIT RETURNS AND INFLATION ===\n")

# 1. VISUALIZATION
print("1. Creating visualizations...")

# Time series plot
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Plot REIT returns
axes[0].plot(df.index, df['reit_index_return'], 'b-', linewidth=2, label='REIT Returns')
axes[0].set_ylabel('REIT Index Return', fontsize=14)
axes[0].set_title('REIT Returns Over Time', fontsize=16)
axes[0].legend(loc='best')
axes[0].grid(True, alpha=0.3)

# Plot inflation
axes[1].plot(df.index, df['inflation_yoy'], 'r-', linewidth=2, label='Inflation (YoY)')
axes[1].set_ylabel('Inflation (YoY %)', fontsize=14)
axes[1].set_title('Inflation Over Time', fontsize=16)
axes[1].legend(loc='best')
axes[1].grid(True, alpha=0.3)
axes[1].set_xlabel('Date', fontsize=14)

plt.tight_layout()
plt.savefig('../report/images/time_series.png', dpi=300, bbox_inches='tight')
plt.close()

# Scatter plot with regression line
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(df['inflation_yoy'], df['reit_index_return'], alpha=0.7, s=80, edgecolor='k')

# Add regression line
X = sm.add_constant(df['inflation_yoy'])
model = sm.OLS(df['reit_index_return'], X).fit()
x_range = np.linspace(df['inflation_yoy'].min(), df['inflation_yoy'].max(), 100)
y_pred = model.params[0] + model.params[1] * x_range
ax.plot(x_range, y_pred, 'r-', linewidth=3, label=f'Regression: y = {model.params[0]:.3f} + {model.params[1]:.3f}x')

ax.set_xlabel('Inflation (YoY %)', fontsize=14)
ax.set_ylabel('REIT Index Return', fontsize=14)
ax.set_title('REIT Returns vs Inflation', fontsize=16)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

# Add correlation coefficient
corr = df['inflation_yoy'].corr(df['reit_index_return'])
ax.text(0.05, 0.95, f'Correlation: {corr:.3f}', transform=ax.transAxes, 
        fontsize=12, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('../report/images/scatter_plot.png', dpi=300, bbox_inches='tight')
plt.close()

print("Visualizations saved to report/images/\n")

# 2. CORRELATION ANALYSIS
print("2. Correlation analysis...")
correlation = df['inflation_yoy'].corr(df['reit_index_return'])
print(f"Pearson correlation coefficient: {correlation:.4f}")

# 3. STATIONARITY TESTS (Augmented Dickey-Fuller)
print("\n3. Stationarity tests (Augmented Dickey-Fuller)...")

for col in ['inflation_yoy', 'reit_index_return']:
    result = adfuller(df[col])
    print(f"{col}: ADF Statistic = {result[0]:.4f}, p-value = {result[1]:.4f}")
    if result[1] < 0.05:
        print(f"  -> Series is stationary (reject null hypothesis of unit root)")
    else:
        print(f"  -> Series is non-stationary (cannot reject null hypothesis of unit root)")

# 4. BASIC REGRESSION ANALYSIS
print("\n4. Regression analysis...")

# Simple linear regression
X = sm.add_constant(df['inflation_yoy'])
y = df['reit_index_return']
model_simple = sm.OLS(y, X).fit()

print("Simple linear regression (REIT returns ~ Inflation):")
print(model_simple.summary())

# Save regression results
with open('../outputs/regression_results.txt', 'w') as f:
    f.write("SIMPLE LINEAR REGRESSION RESULTS\n")
    f.write("="*50 + "\n")
    f.write(str(model_simple.summary()))

# Check for heteroskedasticity
print("\nTesting for heteroskedasticity (Breusch-Pagan test)...")
bp_test = het_breuschpagan(model_simple.resid, X)
print(f"Breusch-Pagan test statistic: {bp_test[0]:.4f}")
print(f"p-value: {bp_test[1]:.4f}")
if bp_test[1] < 0.05:
    print("  -> Evidence of heteroskedasticity (p < 0.05)")
else:
    print("  -> No significant evidence of heteroskedasticity")

# Check for autocorrelation
print("\nTesting for autocorrelation (Durbin-Watson test)...")
dw_stat = durbin_watson(model_simple.resid)
print(f"Durbin-Watson statistic: {dw_stat:.4f}")
if dw_stat < 1.5:
    print("  -> Evidence of positive autocorrelation")
elif dw_stat > 2.5:
    print("  -> Evidence of negative autocorrelation")
else:
    print("  -> No significant autocorrelation detected")

# 5. GRANGER CAUSALITY TEST
print("\n5. Granger causality tests...")
print("Testing if inflation Granger-causes REIT returns...")

# Prepare data for VAR model
data = df[['reit_index_return', 'inflation_yoy']].dropna()

# Test different lags
max_lag = 4  # Maximum lag to test (quarterly data)
print(f"Testing lags 1 to {max_lag}...")

for lag in range(1, max_lag + 1):
    try:
        test_result = grangercausalitytests(data, maxlag=lag, verbose=False)
        p_value = test_result[lag][0]['ssr_ftest'][1]
        print(f"  Lag {lag}: p-value = {p_value:.4f}", end="")
        if p_value < 0.05:
            print(" -> Significant (inflation Granger-causes REIT returns)")
        else:
            print(" -> Not significant")
    except Exception as e:
        print(f"  Lag {lag}: Error - {e}")

# 6. VECTOR AUTOREGRESSION (VAR) MODEL
print("\n6. Vector Autoregression (VAR) model...")

# Determine optimal lag order
var_model = VAR(data)
lag_results = var_model.select_order(maxlags=5)
print(f"Optimal lag order (AIC): {lag_results.aic}")
print(f"Optimal lag order (BIC): {lag_results.bic}")
print(f"Optimal lag order (HQIC): {lag_results.hqic}")

# Use AIC to select lag order
selected_lag = lag_results.aic
print(f"Selected lag order (based on AIC): {selected_lag}")

# Fit VAR model
var_result = var_model.fit(selected_lag)
print("\nVAR Model Summary:")
print(var_result.summary())

# Save VAR results
with open('../outputs/var_results.txt', 'w') as f:
    f.write("VECTOR AUTOREGRESSION (VAR) MODEL RESULTS\n")
    f.write("="*50 + "\n")
    f.write(str(var_result.summary()))

# 7. IMPULSE RESPONSE ANALYSIS
print("\n7. Impulse response analysis...")

# Generate impulse response functions
irf = var_result.irf(periods=10)

# Plot impulse responses
fig = irf.plot(orth=False, figsize=(12, 8))
plt.suptitle('Impulse Response Functions', fontsize=16)
plt.tight_layout()
plt.savefig('../report/images/impulse_response.png', dpi=300, bbox_inches='tight')
plt.close()

print("Impulse response plot saved to report/images/impulse_response.png")

# 8. FORECAST ERROR VARIANCE DECOMPOSITION
print("\n8. Forecast error variance decomposition...")

fevd = var_result.fevd(periods=10)
print("\nForecast Error Variance Decomposition (10 periods ahead):")
print(fevd.summary())

# Plot FEVD
fig = fevd.plot(figsize=(10, 8))
plt.suptitle('Forecast Error Variance Decomposition', fontsize=16)
plt.tight_layout()
plt.savefig('../report/images/variance_decomposition.png', dpi=300, bbox_inches='tight')
plt.close()

print("Variance decomposition plot saved to report/images/variance_decomposition.png")

# 9. ROLLING CORRELATION ANALYSIS
print("\n9. Rolling correlation analysis...")

window_size = 8  # 2-year rolling window
rolling_corr = df['reit_index_return'].rolling(window=window_size).corr(df['inflation_yoy'])

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df.index, rolling_corr, 'g-', linewidth=2, label=f'{window_size}-quarter rolling correlation')
ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
ax.axhline(y=correlation, color='r', linestyle='--', alpha=0.5, label=f'Overall correlation: {correlation:.3f}')
ax.set_xlabel('Date', fontsize=14)
ax.set_ylabel('Rolling Correlation', fontsize=14)
ax.set_title(f'Rolling Correlation Between REIT Returns and Inflation ({window_size}-quarter window)', fontsize=16)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/rolling_correlation.png', dpi=300, bbox_inches='tight')
plt.close()

print("Rolling correlation plot saved to report/images/rolling_correlation.png")

# 10. REGIME ANALYSIS - SPLIT BY INFLATION LEVEL
print("\n10. Regime analysis by inflation level...")

# Define inflation regimes
median_inflation = df['inflation_yoy'].median()
high_inflation = df['inflation_yoy'] > median_inflation
low_inflation = df['inflation_yoy'] <= median_inflation

print(f"Median inflation: {median_inflation:.2f}%")
print(f"High inflation periods: {high_inflation.sum()} quarters")
print(f"Low inflation periods: {low_inflation.sum()} quarters")

# Compare REIT returns in different regimes
high_reit_mean = df.loc[high_inflation, 'reit_index_return'].mean()
low_reit_mean = df.loc[low_inflation, 'reit_index_return'].mean()

print(f"\nREIT returns during high inflation (> {median_inflation:.2f}%): {high_reit_mean:.4f}")
print(f"REIT returns during low inflation (≤ {median_inflation:.2f}%): {low_reit_mean:.4f}")
print(f"Difference: {high_reit_mean - low_reit_mean:.4f}")

# Statistical test for difference
from scipy import stats
t_stat, p_value = stats.ttest_ind(
    df.loc[high_inflation, 'reit_index_return'],
    df.loc[low_inflation, 'reit_index_return'],
    equal_var=False
)
print(f"t-statistic: {t_stat:.4f}, p-value: {p_value:.4f}")
if p_value < 0.05:
    print("  -> Significant difference in REIT returns between inflation regimes (p < 0.05)")
else:
    print("  -> No significant difference in REIT returns between inflation regimes")

# Save regime analysis results
with open('../outputs/regime_analysis.txt', 'w') as f:
    f.write("REGIME ANALYSIS BY INFLATION LEVEL\n")
    f.write("="*50 + "\n")
    f.write(f"Median inflation: {median_inflation:.2f}%\n")
    f.write(f"High inflation periods: {high_inflation.sum()} quarters\n")
    f.write(f"Low inflation periods: {low_inflation.sum()} quarters\n\n")
    f.write(f"REIT returns during high inflation (> {median_inflation:.2f}%): {high_reit_mean:.4f}\n")
    f.write(f"REIT returns during low inflation (≤ {median_inflation:.2f}%): {low_reit_mean:.4f}\n")
    f.write(f"Difference: {high_reit_mean - low_reit_mean:.4f}\n\n")
    f.write(f"t-statistic: {t_stat:.4f}\n")
    f.write(f"p-value: {p_value:.4f}\n")

print("\n=== ANALYSIS COMPLETE ===")
print("Results saved to outputs/ and report/images/")
