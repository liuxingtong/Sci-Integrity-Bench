"""
REIT and Inflation Econometric Analysis
=======================================
This script analyzes the relationship between REIT index returns and inflation
using quarterly data. The analysis includes descriptive statistics, correlation
analysis, regression models, and time series analysis with policy implications.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
from statsmodels.stats.diagnostic import het_breuschpagan
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
print("Loading data...")
df = pd.read_csv('data/reit_macro_quarterly.csv')
print(f"Data shape: {df.shape}")
print(df.head())
print(df.describe())

# Create time index (assuming quarterly data starting from Q1 of some year)
df['time'] = df['quarter']
df['date'] = pd.date_range(start='2014-01-01', periods=len(df), freq='Q')

# ============================================================================
# 1. DESCRIPTIVE STATISTICS AND DATA OVERVIEW
# ============================================================================
print("\n" + "="*60)
print("1. DESCRIPTIVE STATISTICS")
print("="*60)

# Basic statistics
stats_summary = df[['inflation_yoy', 'reit_index_return']].describe()
print("\nDescriptive Statistics:")
print(stats_summary)

# Additional statistics
print("\nAdditional Statistics:")
for col in ['inflation_yoy', 'reit_index_return']:
    print(f"\n{col}:")
    print(f"  Skewness: {stats.skew(df[col]):.4f}")
    print(f"  Kurtosis: {stats.kurtosis(df[col]):.4f}")
    print(f"  Standard Error: {stats.sem(df[col]):.4f}")

# ============================================================================
# 2. CORRELATION ANALYSIS
# ============================================================================
print("\n" + "="*60)
print("2. CORRELATION ANALYSIS")
print("="*60)

# Pearson correlation
corr_coef, corr_pvalue = stats.pearsonr(df['inflation_yoy'], df['reit_index_return'])
print(f"\nPearson Correlation: {corr_coef:.4f}")
print(f"P-value: {corr_pvalue:.4f}")

# Spearman correlation (rank-based, more robust)
spearman_coef, spearman_pvalue = stats.spearmanr(df['inflation_yoy'], df['reit_index_return'])
print(f"\nSpearman Correlation: {spearman_coef:.4f}")
print(f"P-value: {spearman_pvalue:.4f}")

# ============================================================================
# 3. REGRESSION ANALYSIS
# ============================================================================
print("\n" + "="*60)
print("3. REGRESSION ANALYSIS")
print("="*60)

# Model 1: Simple OLS - REIT returns on inflation
X = sm.add_constant(df['inflation_yoy'])
y = df['reit_index_return']

model1 = sm.OLS(y, X).fit()
print("\nModel 1: REIT Return = α + β × Inflation + ε")
print(model1.summary())

# Model 2: With lagged inflation (to capture delayed effects)
df['inflation_lag1'] = df['inflation_yoy'].shift(1)
df['inflation_lag2'] = df['inflation_yoy'].shift(2)
df_clean = df.dropna()

X2 = sm.add_constant(df_clean[['inflation_yoy', 'inflation_lag1', 'inflation_lag2']])
y2 = df_clean['reit_index_return']

model2 = sm.OLS(y2, X2).fit()
print("\nModel 2: REIT Return = α + β₀×Inflation + β₁×Inflation(t-1) + β₂×Inflation(t-2) + ε")
print(model2.summary())

# Model 3: Non-linear relationship (quadratic)
df['inflation_sq'] = df['inflation_yoy'] ** 2
X3 = sm.add_constant(df[['inflation_yoy', 'inflation_sq']])
y3 = df['reit_index_return']

model3 = sm.OLS(y3, X3).fit()
print("\nModel 3: REIT Return = α + β₁×Inflation + β₂×Inflation² + ε")
print(model3.summary())

# ============================================================================
# 4. TIME SERIES ANALYSIS
# ============================================================================
print("\n" + "="*60)
print("4. TIME SERIES ANALYSIS")
print("="*60)

# Unit root tests (ADF)
print("\nAugmented Dickey-Fuller Tests:")
for col in ['inflation_yoy', 'reit_index_return']:
    adf_result = adfuller(df[col])
    print(f"\n{col}:")
    print(f"  ADF Statistic: {adf_result[0]:.4f}")
    print(f"  P-value: {adf_result[1]:.4f}")
    print(f"  Critical Values: {adf_result[4]}")

# Granger causality test (if enough data)
if len(df) > 10:
    print("\nGranger Causality Test (max lag=2):")
    gc_data = df[['reit_index_return', 'inflation_yoy']].dropna()
    try:
        gc_result = grangercausalitytests(gc_data, maxlag=2, verbose=False)
        for lag in [1, 2]:
            f_stat = gc_result[lag][0]['ssr_ftest'][0]
            p_val = gc_result[lag][0]['ssr_ftest'][1]
            print(f"  Lag {lag}: F-stat={f_stat:.4f}, p-value={p_val:.4f}")
    except Exception as e:
        print(f"  Could not perform Granger causality test: {e}")

# ============================================================================
# 5. HETEROSCEDASTICITY TEST
# ============================================================================
print("\n" + "="*60)
print("5. DIAGNOSTIC TESTS")
print("="*60)

# Breusch-Pagan test for heteroscedasticity
bp_test = het_breuschpagan(model1.resid, model1.model.exog)
print("\nBreusch-Pagan Test for Heteroscedasticity:")
print(f"  LM Statistic: {bp_test[0]:.4f}")
print(f"  LM P-value: {bp_test[1]:.4f}")
print(f"  F Statistic: {bp_test[2]:.4f}")
print(f"  F P-value: {bp_test[3]:.4f}")

# ============================================================================
# 6. GENERATE FIGURES
# ============================================================================
print("\n" + "="*60)
print("6. GENERATING FIGURES")
print("="*60)

# Figure 1: Time Series Plot
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

axes[0].plot(df['date'], df['inflation_yoy'], 'b-', linewidth=2, label='Inflation (YoY %)')
axes[0].axhline(y=df['inflation_yoy'].mean(), color='b', linestyle='--', alpha=0.5, label=f'Mean: {df["inflation_yoy"].mean():.2f}%')
axes[0].set_ylabel('Inflation (%)', fontsize=12)
axes[0].set_title('Quarterly Inflation and REIT Index Returns', fontsize=14, fontweight='bold')
axes[0].legend(loc='upper right')
axes[0].grid(True, alpha=0.3)

axes[1].plot(df['date'], df['reit_index_return'], 'r-', linewidth=2, label='REIT Index Return (%)')
axes[1].axhline(y=df['reit_index_return'].mean(), color='r', linestyle='--', alpha=0.5, label=f'Mean: {df["reit_index_return"].mean():.2f}%')
axes[1].set_ylabel('REIT Return (%)', fontsize=12)
axes[1].set_xlabel('Date', fontsize=12)
axes[1].legend(loc='upper right')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure1_time_series.png', dpi=300, bbox_inches='tight')
plt.close()
print("Figure 1 saved: Time series plot")

# Figure 2: Scatter Plot with Regression Line
fig, ax = plt.subplots(figsize=(10, 8))

# Scatter plot
ax.scatter(df['inflation_yoy'], df['reit_index_return'], alpha=0.7, s=100, c='steelblue', edgecolors='black', linewidth=0.5)

# Regression line
x_range = np.linspace(df['inflation_yoy'].min(), df['inflation_yoy'].max(), 100)
y_pred = model1.params[0] + model1.params[1] * x_range
ax.plot(x_range, y_pred, 'r-', linewidth=2, label=f'OLS Fit: y = {model1.params[0]:.3f} + {model1.params[1]:.3f}x')

# Confidence interval
from statsmodels.stats.outliers_influence import summary_table
st, data, ss2 = summary_table(model1, alpha=0.05)
predict_mean_se = data[:, 2]
predict_mean_ci_low, predict_mean_ci_upp = data[:, 4:6].T
ax.fill_between(df['inflation_yoy'].sort_values(), 
                predict_mean_ci_low[np.argsort(df['inflation_yoy'])], 
                predict_mean_ci_upp[np.argsort(df['inflation_yoy'])], 
                alpha=0.2, color='red', label='95% CI')

ax.set_xlabel('Inflation (YoY %)', fontsize=12)
ax.set_ylabel('REIT Index Return (%)', fontsize=12)
ax.set_title(f'REIT Returns vs. Inflation\n(Correlation: {corr_coef:.3f}, p-value: {corr_pvalue:.3f})', fontsize=14, fontweight='bold')
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure2_scatter_regression.png', dpi=300, bbox_inches='tight')
plt.close()
print("Figure 2 saved: Scatter plot with regression")

# Figure 3: Distribution Analysis
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Inflation histogram
axes[0, 0].hist(df['inflation_yoy'], bins=15, color='skyblue', edgecolor='black', alpha=0.7)
axes[0, 0].axvline(df['inflation_yoy'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df["inflation_yoy"].mean():.2f}')
axes[0, 0].set_xlabel('Inflation (%)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Distribution of Inflation')
axes[0, 0].legend()

# REIT return histogram
axes[0, 1].hist(df['reit_index_return'], bins=15, color='lightcoral', edgecolor='black', alpha=0.7)
axes[0, 1].axvline(df['reit_index_return'].mean(), color='blue', linestyle='--', linewidth=2, label=f'Mean: {df["reit_index_return"].mean():.2f}')
axes[0, 1].set_xlabel('REIT Return (%)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Distribution of REIT Returns')
axes[0, 1].legend()

# Q-Q plot for inflation
stats.probplot(df['inflation_yoy'], dist="norm", plot=axes[1, 0])
axes[1, 0].set_title('Q-Q Plot: Inflation')
axes[1, 0].grid(True, alpha=0.3)

# Q-Q plot for REIT returns
stats.probplot(df['reit_index_return'], dist="norm", plot=axes[1, 1])
axes[1, 1].set_title('Q-Q Plot: REIT Returns')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure3_distributions.png', dpi=300, bbox_inches='tight')
plt.close()
print("Figure 3 saved: Distribution analysis")

# Figure 4: Rolling Correlation
window = 8  # 2 years of quarterly data
df['rolling_corr'] = df['inflation_yoy'].rolling(window=window).corr(df['reit_index_return'])

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['date'], df['rolling_corr'], 'g-', linewidth=2)
ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
ax.axhline(y=corr_coef, color='red', linestyle='--', alpha=0.7, label=f'Full-sample correlation: {corr_coef:.3f}')
ax.fill_between(df['date'], df['rolling_corr'], 0, alpha=0.3, color='green')
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Rolling Correlation', fontsize=12)
ax.set_title(f'Rolling {window}-Quarter Correlation: REIT Returns vs. Inflation', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure4_rolling_correlation.png', dpi=300, bbox_inches='tight')
plt.close()
print("Figure 4 saved: Rolling correlation")

# Figure 5: Residual Analysis
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Residuals vs Fitted
axes[0, 0].scatter(model1.fittedvalues, model1.resid, alpha=0.7, c='steelblue', edgecolors='black', linewidth=0.5)
axes[0, 0].axhline(y=0, color='red', linestyle='--')
axes[0, 0].set_xlabel('Fitted Values')
axes[0, 0].set_ylabel('Residuals')
axes[0, 0].set_title('Residuals vs Fitted')
axes[0, 0].grid(True, alpha=0.3)

# Residual histogram
axes[0, 1].hist(model1.resid, bins=15, color='lightgreen', edgecolor='black', alpha=0.7)
axes[0, 1].axvline(0, color='red', linestyle='--', linewidth=2)
axes[0, 1].set_xlabel('Residuals')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Distribution of Residuals')

# Q-Q plot for residuals
stats.probplot(model1.resid, dist="norm", plot=axes[1, 0])
axes[1, 0].set_title('Q-Q Plot: Residuals')
axes[1, 0].grid(True, alpha=0.3)

# Residuals over time
axes[1, 1].plot(df['date'], model1.resid, 'b-', linewidth=1)
axes[1, 1].axhline(y=0, color='red', linestyle='--')
axes[1, 1].set_xlabel('Date')
axes[1, 1].set_ylabel('Residuals')
axes[1, 1].set_title('Residuals Over Time')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure5_residual_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("Figure 5 saved: Residual analysis")

# Figure 6: Inflation Regime Analysis
# Define inflation regimes
df['inflation_regime'] = pd.cut(df['inflation_yoy'], 
                                 bins=[-np.inf, 1.5, 2.5, np.inf], 
                                 labels=['Low (<1.5%)', 'Moderate (1.5-2.5%)', 'High (>2.5%)'])

regime_stats = df.groupby('inflation_regime')['reit_index_return'].agg(['mean', 'std', 'count'])
print("\nREIT Returns by Inflation Regime:")
print(regime_stats)

fig, ax = plt.subplots(figsize=(10, 6))
regime_means = regime_stats['mean']
regime_stds = regime_stats['std']
x_pos = np.arange(len(regime_means))

bars = ax.bar(x_pos, regime_means, yerr=regime_stds, capsize=5, 
              color=['lightblue', 'orange', 'lightcoral'], edgecolor='black', alpha=0.8)
ax.set_xticks(x_pos)
ax.set_xticklabels(regime_means.index)
ax.set_ylabel('Average REIT Return (%)', fontsize=12)
ax.set_xlabel('Inflation Regime', fontsize=12)
ax.set_title('REIT Returns by Inflation Regime', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, regime_means)):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
            f'{val:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/figure6_inflation_regimes.png', dpi=300, bbox_inches='tight')
plt.close()
print("Figure 6 saved: Inflation regime analysis")

# ============================================================================
# 7. SAVE RESULTS
# ============================================================================
print("\n" + "="*60)
print("7. SAVING RESULTS")
print("="*60)

# Save model results
results = {
    'correlation_pearson': corr_coef,
    'correlation_pvalue': corr_pvalue,
    'correlation_spearman': spearman_coef,
    'model1_r2': model1.rsquared,
    'model1_adj_r2': model1.rsquared_adj,
    'model1_beta': model1.params[1],
    'model1_beta_pvalue': model1.pvalues[1],
    'model1_alpha': model1.params[0],
    'model1_alpha_pvalue': model1.pvalues[0],
    'model3_r2': model3.rsquared,
    'model3_inflation_coef': model3.params[1],
    'model3_inflation_sq_coef': model3.params[2],
}

results_df = pd.DataFrame([results])
results_df.to_csv('outputs/model_results.csv', index=False)
print("Results saved to outputs/model_results.csv")

# Save regime statistics
regime_stats.to_csv('outputs/regime_stats.csv')
print("Regime statistics saved to outputs/regime_stats.csv")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
