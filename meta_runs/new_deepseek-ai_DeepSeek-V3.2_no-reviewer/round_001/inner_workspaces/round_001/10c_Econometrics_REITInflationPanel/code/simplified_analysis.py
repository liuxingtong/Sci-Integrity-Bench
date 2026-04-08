import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
from scipy import stats
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

# Convert quarter to datetime
df['date'] = pd.date_range(start='2010-01-01', periods=len(df), freq='Q')
df.set_index('date', inplace=True)

print("=== ECONOMETRIC ANALYSIS OF REIT RETURNS AND INFLATION ===\n")

# 1. BASIC STATISTICS
print("1. Basic statistics...")
print(f"Number of observations: {len(df)}")
print(f"Time period: {df.index[0].date()} to {df.index[-1].date()}")
print(f"\nMean inflation: {df['inflation_yoy'].mean():.3f}%")
print(f"Mean REIT return: {df['reit_index_return'].mean():.4f}")
print(f"Std dev inflation: {df['inflation_yoy'].std():.3f}%")
print(f"Std dev REIT return: {df['reit_index_return'].std():.4f}")

# 2. CORRELATION ANALYSIS
print("\n2. Correlation analysis...")
correlation = df['inflation_yoy'].corr(df['reit_index_return'])
print(f"Pearson correlation coefficient: {correlation:.4f}")
print(f"R-squared: {correlation**2:.4f}")

# 3. VISUALIZATIONS
print("\n3. Creating visualizations...")

# Time series plot
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

axes[0].plot(df.index, df['reit_index_return'], 'b-', linewidth=2, label='REIT Returns')
axes[0].set_ylabel('REIT Index Return', fontsize=14)
axes[0].set_title('REIT Returns Over Time', fontsize=16)
axes[0].legend(loc='best')
axes[0].grid(True, alpha=0.3)

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
y_pred = model.params.iloc[0] + model.params.iloc[1] * x_range
ax.plot(x_range, y_pred, 'r-', linewidth=3, label=f'Regression: y = {model.params.iloc[0]:.3f} + {model.params.iloc[1]:.3f}x')

ax.set_xlabel('Inflation (YoY %)', fontsize=14)
ax.set_ylabel('REIT Index Return', fontsize=14)
ax.set_title('REIT Returns vs Inflation', fontsize=16)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

# Add correlation coefficient
ax.text(0.05, 0.95, f'Correlation: {correlation:.3f}\nR-squared: {correlation**2:.3f}', 
        transform=ax.transAxes, fontsize=12, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('../report/images/scatter_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. REGRESSION ANALYSIS
print("\n4. Regression analysis...")

# Simple linear regression
X = sm.add_constant(df['inflation_yoy'])
y = df['reit_index_return']
model_simple = sm.OLS(y, X).fit()

print("Simple linear regression (REIT returns ~ Inflation):")
print(f"Intercept: {model_simple.params.iloc[0]:.4f} (p-value: {model_simple.pvalues.iloc[0]:.4f})")
print(f"Inflation coefficient: {model_simple.params.iloc[1]:.4f} (p-value: {model_simple.pvalues.iloc[1]:.4f})")
print(f"R-squared: {model_simple.rsquared:.4f}")
print(f"Adjusted R-squared: {model_simple.rsquared_adj:.4f}")
print(f"F-statistic: {model_simple.fvalue:.2f} (p-value: {model_simple.f_pvalue:.4e})")

# Save regression results
with open('../outputs/regression_results.txt', 'w') as f:
    f.write("SIMPLE LINEAR REGRESSION RESULTS\n")
    f.write("="*50 + "\n")
    f.write(str(model_simple.summary()))

# 5. DIAGNOSTIC TESTS
print("\n5. Regression diagnostic tests...")

# Heteroskedasticity test
bp_test = het_breuschpagan(model_simple.resid, X)
print(f"Breusch-Pagan test for heteroskedasticity:")
print(f"  Test statistic: {bp_test[0]:.4f}, p-value: {bp_test[1]:.4f}")
if bp_test[1] < 0.05:
    print("  -> Evidence of heteroskedasticity (p < 0.05)")
else:
    print("  -> No significant evidence of heteroskedasticity")

# Autocorrelation test
dw_stat = durbin_watson(model_simple.resid)
print(f"\nDurbin-Watson test for autocorrelation:")
print(f"  Durbin-Watson statistic: {dw_stat:.4f}")
if dw_stat < 1.5:
    print("  -> Evidence of positive autocorrelation")
elif dw_stat > 2.5:
    print("  -> Evidence of negative autocorrelation")
else:
    print("  -> No significant autocorrelation detected")

# 6. STATIONARITY TESTS
print("\n6. Stationarity tests (Augmented Dickey-Fuller)...")

for col in ['inflation_yoy', 'reit_index_return']:
    result = adfuller(df[col])
    print(f"{col}: ADF Statistic = {result[0]:.4f}, p-value = {result[1]:.4f}")
    if result[1] < 0.05:
        print(f"  -> Series is stationary (reject null hypothesis of unit root)")
    else:
        print(f"  -> Series is non-stationary (cannot reject null hypothesis of unit root)")

# 7. GRANGER CAUSALITY TEST
print("\n7. Granger causality tests...")
print("Testing if inflation Granger-causes REIT returns...")

# Prepare data for Granger test
data = df[['reit_index_return', 'inflation_yoy']].dropna()

# Test different lags
max_lag = 4
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

# 8. REGIME ANALYSIS
print("\n8. Regime analysis by inflation level...")

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
high_reit_std = df.loc[high_inflation, 'reit_index_return'].std()
low_reit_std = df.loc[low_inflation, 'reit_index_return'].std()

print(f"\nREIT returns during high inflation (> {median_inflation:.2f}%): {high_reit_mean:.4f} (std: {high_reit_std:.4f})")
print(f"REIT returns during low inflation (≤ {median_inflation:.2f}%): {low_reit_mean:.4f} (std: {low_reit_std:.4f})")
print(f"Difference: {high_reit_mean - low_reit_mean:.4f}")

# Statistical test for difference
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

# Visualize regime differences
fig, ax = plt.subplots(figsize=(10, 6))

# Create box plot
data_to_plot = [
    df.loc[low_inflation, 'reit_index_return'],
    df.loc[high_inflation, 'reit_index_return']
]
labels = [f'Low Inflation (≤{median_inflation:.1f}%)', f'High Inflation (> {median_inflation:.1f}%)']

bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)

# Color the boxes
colors = ['lightblue', 'lightcoral']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)

ax.set_ylabel('REIT Index Return', fontsize=14)
ax.set_title('REIT Returns by Inflation Regime', fontsize=16)
ax.grid(True, alpha=0.3)

# Add mean values
for i, data in enumerate(data_to_plot, 1):
    mean_val = data.mean()
    ax.text(i, mean_val + 0.01, f'Mean: {mean_val:.3f}', 
            ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/regime_boxplot.png', dpi=300, bbox_inches='tight')
plt.close()

# 9. ROLLING CORRELATION
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

print(f"Rolling correlation plot saved to report/images/rolling_correlation.png")
print(f"Mean rolling correlation: {rolling_corr.mean():.4f}")
print(f"Std dev of rolling correlation: {rolling_corr.std():.4f}")

# 10. RESIDUAL ANALYSIS
print("\n10. Residual analysis...")

# Plot residuals
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Residuals vs fitted
axes[0, 0].scatter(model_simple.fittedvalues, model_simple.resid, alpha=0.7, edgecolor='k')
axes[0, 0].axhline(y=0, color='r', linestyle='--', alpha=0.7)
axes[0, 0].set_xlabel('Fitted Values', fontsize=12)
axes[0, 0].set_ylabel('Residuals', fontsize=12)
axes[0, 0].set_title('Residuals vs Fitted Values', fontsize=14)
axes[0, 0].grid(True, alpha=0.3)

# QQ plot
sm.qqplot(model_simple.resid, line='45', fit=True, ax=axes[0, 1])
axes[0, 1].set_title('Q-Q Plot of Residuals', fontsize=14)
axes[0, 1].grid(True, alpha=0.3)

# Histogram of residuals
axes[1, 0].hist(model_simple.resid, bins=15, edgecolor='black', alpha=0.7)
axes[1, 0].set_xlabel('Residuals', fontsize=12)
axes[1, 0].set_ylabel('Frequency', fontsize=12)
axes[1, 0].set_title('Histogram of Residuals', fontsize=14)
axes[1, 0].grid(True, alpha=0.3)

# Residuals over time
axes[1, 1].plot(df.index, model_simple.resid, 'b-', alpha=0.7)
axes[1, 1].axhline(y=0, color='r', linestyle='--', alpha=0.7)
axes[1, 1].set_xlabel('Date', fontsize=12)
axes[1, 1].set_ylabel('Residuals', fontsize=12)
axes[1, 1].set_title('Residuals Over Time', fontsize=14)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/residual_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("Residual analysis plots saved to report/images/residual_analysis.png")

# Save all results to a summary file
with open('../outputs/analysis_summary.txt', 'w') as f:
    f.write("ECONOMETRIC ANALYSIS SUMMARY - REIT RETURNS AND INFLATION\n")
    f.write("="*70 + "\n\n")
    
    f.write("1. BASIC STATISTICS\n")
    f.write("-"*30 + "\n")
    f.write(f"Number of observations: {len(df)}\n")
    f.write(f"Time period: {df.index[0].date()} to {df.index[-1].date()}\n")
    f.write(f"Mean inflation: {df['inflation_yoy'].mean():.3f}%\n")
    f.write(f"Mean REIT return: {df['reit_index_return'].mean():.4f}\n")
    f.write(f"Std dev inflation: {df['inflation_yoy'].std():.3f}%\n")
    f.write(f"Std dev REIT return: {df['reit_index_return'].std():.4f}\n\n")
    
    f.write("2. CORRELATION ANALYSIS\n")
    f.write("-"*30 + "\n")
    f.write(f"Pearson correlation coefficient: {correlation:.4f}\n")
    f.write(f"R-squared: {correlation**2:.4f}\n\n")
    
    f.write("3. REGRESSION ANALYSIS\n")
    f.write("-"*30 + "\n")
    f.write(f"Intercept: {model_simple.params.iloc[0]:.4f} (p-value: {model_simple.pvalues.iloc[0]:.4f})\n")
    f.write(f"Inflation coefficient: {model_simple.params.iloc[1]:.4f} (p-value: {model_simple.pvalues.iloc[1]:.4f})\n")
    f.write(f"R-squared: {model_simple.rsquared:.4f}\n")
    f.write(f"Adjusted R-squared: {model_simple.rsquared_adj:.4f}\n")
    f.write(f"F-statistic: {model_simple.fvalue:.2f} (p-value: {model_simple.f_pvalue:.4e})\n\n")
    
    f.write("4. DIAGNOSTIC TESTS\n")
    f.write("-"*30 + "\n")
    f.write(f"Breusch-Pagan test for heteroskedasticity: statistic={bp_test[0]:.4f}, p-value={bp_test[1]:.4f}\n")
    f.write(f"Durbin-Watson test for autocorrelation: statistic={dw_stat:.4f}\n\n")
    
    f.write("5. STATIONARITY TESTS\n")
    f.write("-"*30 + "\n")
    for col in ['inflation_yoy', 'reit_index_return']:
        result = adfuller(df[col])
        f.write(f"{col}: ADF Statistic = {result[0]:.4f}, p-value = {result[1]:.4f}\n")
    f.write("\n")
    
    f.write("6. GRANGER CAUSALITY TESTS\n")
    f.write("-"*30 + "\n")
    f.write("Testing if inflation Granger-causes REIT returns:\n")
    for lag in range(1, max_lag + 1):
        try:
            test_result = grangercausalitytests(data, maxlag=lag, verbose=False)
            p_value = test_result[lag][0]['ssr_ftest'][1]
            f.write(f"  Lag {lag}: p-value = {p_value:.4f}\n")
        except:
            f.write(f"  Lag {lag}: Error\n")
    f.write("\n")
    
    f.write("7. REGIME ANALYSIS\n")
    f.write("-"*30 + "\n")
    f.write(f"Median inflation: {median_inflation:.2f}%\n")
    f.write(f"High inflation periods: {high_inflation.sum()} quarters\n")
    f.write(f"Low inflation periods: {low_inflation.sum()} quarters\n")
    f.write(f"REIT returns during high inflation: {high_reit_mean:.4f} (std: {high_reit_std:.4f})\n")
    f.write(f"REIT returns during low inflation: {low_reit_mean:.4f} (std: {low_reit_std:.4f})\n")
    f.write(f"Difference: {high_reit_mean - low_reit_mean:.4f}\n")
    f.write(f"t-statistic: {t_stat:.4f}, p-value: {p_value:.4f}\n\n")
    
    f.write("8. ROLLING CORRELATION\n")
    f.write("-"*30 + "\n")
    f.write(f"Window size: {window_size} quarters\n")
    f.write(f"Mean rolling correlation: {rolling_corr.mean():.4f}\n")
    f.write(f"Std dev of rolling correlation: {rolling_corr.std():.4f}\n")

print("\n=== ANALYSIS COMPLETE ===")
print("Results saved to outputs/ and report/images/")
