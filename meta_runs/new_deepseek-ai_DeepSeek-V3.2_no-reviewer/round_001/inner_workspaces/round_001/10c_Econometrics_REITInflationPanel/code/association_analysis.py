import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
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

print("=== ASSOCIATION ANALYSIS: REIT RETURNS AND INFLATION ===\n")

# 1. Basic correlation analysis
print("1. CORRELATION ANALYSIS")
correlation = df['inflation_yoy'].corr(df['reit_index_return'])
print(f"Pearson correlation coefficient: {correlation:.4f}")

# Test significance
corr_test = stats.pearsonr(df['inflation_yoy'], df['reit_index_return'])
print(f"Correlation p-value: {corr_test.pvalue:.6f}")
print(f"Significant at 5% level: {corr_test.pvalue < 0.05}")

# 2. Scatter plot with regression line
fig, ax = plt.subplots(figsize=(10, 6))
sns.regplot(x='inflation_yoy', y='reit_index_return', data=df, 
            scatter_kws={'s': 80, 'alpha': 0.7}, 
            line_kws={'color': 'red', 'linewidth': 2},
            ax=ax)
ax.set_title('REIT Returns vs. Inflation: Scatter Plot with Regression Line', fontsize=14)
ax.set_xlabel('Inflation (Year-over-Year, %)', fontsize=12)
ax.set_ylabel('REIT Index Return', fontsize=12)
ax.grid(True, alpha=0.3)

# Add correlation text
ax.text(0.05, 0.95, f'Correlation: {correlation:.3f}\np-value: {corr_test.pvalue:.4f}',
        transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('../report/images/scatter_regression.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nScatter plot with regression line saved.")

# 3. Simple linear regression
print("\n2. SIMPLE LINEAR REGRESSION")
X = sm.add_constant(df['inflation_yoy'])  # Add constant for intercept
y = df['reit_index_return']
model = sm.OLS(y, X).fit()
print(model.summary())

# Save regression results to file
with open('../outputs/regression_results.txt', 'w') as f:
    f.write(str(model.summary()))

# 4. Check for non-linear relationship
print("\n3. CHECKING FOR NON-LINEAR RELATIONSHIPS")
# Add squared term for inflation
df['inflation_sq'] = df['inflation_yoy'] ** 2
X_nonlinear = sm.add_constant(df[['inflation_yoy', 'inflation_sq']])
model_nonlinear = sm.OLS(y, X_nonlinear).fit()
print("Quadratic model summary:")
print(model_nonlinear.summary())

# Compare models
print(f"\nLinear model R-squared: {model.rsquared:.4f}")
print(f"Quadratic model R-squared: {model_nonlinear.rsquared:.4f}")
print(f"R-squared improvement: {model_nonlinear.rsquared - model.rsquared:.4f}")

# 5. Time series aspects
print("\n4. TIME SERIES ANALYSIS")
# Check for autocorrelation in residuals
from statsmodels.stats.stattools import durbin_watson
dw_stat = durbin_watson(model.resid)
print(f"Durbin-Watson statistic: {dw_stat:.4f}")
print("Interpretation: Values near 2 suggest no autocorrelation.")

# Plot residuals
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Residuals vs fitted
axes[0].scatter(model.fittedvalues, model.resid, alpha=0.7)
axes[0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[0].set_title('Residuals vs Fitted Values')
axes[0].set_xlabel('Fitted Values')
axes[0].set_ylabel('Residuals')
axes[0].grid(True, alpha=0.3)

# Residuals over time
axes[1].plot(df['quarter'], model.resid, marker='o', alpha=0.7)
axes[1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[1].set_title('Residuals Over Time')
axes[1].set_xlabel('Quarter')
axes[1].set_ylabel('Residuals')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/residual_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nResidual analysis plots saved.")

# 6. Lagged relationship analysis
print("\n5. LAGGED RELATIONSHIP ANALYSIS")
# Create lagged variables
df['inflation_lag1'] = df['inflation_yoy'].shift(1)
df['reit_lag1'] = df['reit_index_return'].shift(1)

# Drop first row with NaN
df_lag = df.dropna().copy()

# Model with lagged inflation
X_lag = sm.add_constant(df_lag[['inflation_lag1']])
y_lag = df_lag['reit_index_return']
model_lag = sm.OLS(y_lag, X_lag).fit()
print("\nModel with lagged inflation (t-1):")
print(f"R-squared: {model_lag.rsquared:.4f}")
print(f"Coefficient on lagged inflation: {model_lag.params['inflation_lag1']:.4f}")
print(f"p-value: {model_lag.pvalues['inflation_lag1']:.4f}")

# 7. Rolling correlation to check stability
print("\n6. ROLLING CORRELATION ANALYSIS")
window_size = 12  # 3 years of quarterly data
df['rolling_corr'] = df['inflation_yoy'].rolling(window=window_size).corr(df['reit_index_return'])

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['quarter'], df['rolling_corr'], linewidth=2, marker='o', markersize=4)
ax.axhline(y=correlation, color='r', linestyle='--', alpha=0.7, label=f'Overall correlation: {correlation:.3f}')
ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax.set_title(f'Rolling Correlation (Window = {window_size} Quarters)', fontsize=14)
ax.set_xlabel('Quarter', fontsize=12)
ax.set_ylabel('Rolling Correlation', fontsize=12)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/rolling_correlation.png', dpi=300, bbox_inches='tight')
plt.close()
print("Rolling correlation plot saved.")

# 8. Inflation regimes analysis
print("\n7. INFLATION REGIMES ANALYSIS")
# Define inflation regimes
median_inflation = df['inflation_yoy'].median()
print(f"Median inflation: {median_inflation:.3f}%")

df['high_inflation'] = df['inflation_yoy'] > median_inflation

# Compare REIT returns in high vs low inflation periods
high_inf_returns = df.loc[df['high_inflation'], 'reit_index_return']
low_inf_returns = df.loc[~df['high_inflation'], 'reit_index_return']

print(f"\nHigh inflation periods (> {median_inflation:.3f}%): {len(high_inf_returns)} observations")
print(f"Mean REIT return in high inflation: {high_inf_returns.mean():.4f}")
print(f"Std dev: {high_inf_returns.std():.4f}")

print(f"\nLow inflation periods (≤ {median_inflation:.3f}%): {len(low_inf_returns)} observations")
print(f"Mean REIT return in low inflation: {low_inf_returns.mean():.4f}")
print(f"Std dev: {low_inf_returns.std():.4f}")

# T-test for difference in means
t_stat, p_value = stats.ttest_ind(high_inf_returns, low_inf_returns, equal_var=False)
print(f"\nT-test for difference in means:")
print(f"t-statistic: {t_stat:.4f}")
print(f"p-value: {p_value:.4f}")
print(f"Significant difference at 5% level: {p_value < 0.05}")

# Box plot for visualization
fig, ax = plt.subplots(figsize=(8, 6))
df['inflation_regime'] = df['high_inflation'].map({True: f'High (> {median_inflation:.1f}%)', 
                                                    False: f'Low (≤ {median_inflation:.1f}%)'})
sns.boxplot(x='inflation_regime', y='reit_index_return', data=df, ax=ax)
ax.set_title('REIT Returns by Inflation Regime', fontsize=14)
ax.set_xlabel('Inflation Regime', fontsize=12)
ax.set_ylabel('REIT Index Return', fontsize=12)
ax.grid(True, alpha=0.3)

# Add mean markers
means = df.groupby('inflation_regime')['reit_index_return'].mean()
for i, regime in enumerate(means.index):
    ax.text(i, means[regime] + 0.01, f'Mean: {means[regime]:.3f}', 
            ha='center', va='bottom', fontsize=10, 
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

plt.tight_layout()
plt.savefig('../report/images/inflation_regimes.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nInflation regimes box plot saved.")

print("\n=== ANALYSIS COMPLETE ===")
print("All outputs saved to ../outputs/ and ../report/images/")