"""
REIT and Inflation Association Analysis
Econometric study of the relationship between REIT index returns and inflation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
df = pd.read_csv('data/reit_macro_quarterly.csv')
print("=" * 60)
print("REIT-INFLATION ASSOCIATION ANALYSIS")
print("=" * 60)
print(f"\nDataset: {len(df)} quarterly observations")
print(f"Variables: inflation_yoy, reit_index_return")
print("\n" + "=" * 60)

# ============================================================================
# 1. DESCRIPTIVE STATISTICS
# ============================================================================
print("\n1. DESCRIPTIVE STATISTICS")
print("-" * 60)

desc_stats = df[['inflation_yoy', 'reit_index_return']].describe()
print(desc_stats.round(4))

# Additional statistics
print("\nAdditional Statistics:")
for col in ['inflation_yoy', 'reit_index_return']:
    data = df[col]
    print(f"\n{col}:")
    print(f"  Skewness: {stats.skew(data):.4f}")
    print(f"  Kurtosis: {stats.kurtosis(data):.4f}")
    print(f"  Jarque-Bera (normality): {stats.jarque_bera(data)[1]:.4f} (p-value)")

# Save descriptive stats
desc_stats.to_csv('outputs/descriptive_statistics.csv')

# ============================================================================
# 2. VISUALIZATION: TIME SERIES PLOT
# ============================================================================
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Inflation time series
axes[0].plot(df['quarter'], df['inflation_yoy'], 'b-', linewidth=2, marker='o', markersize=4)
axes[0].axhline(y=df['inflation_yoy'].mean(), color='r', linestyle='--', alpha=0.7, label=f'Mean: {df["inflation_yoy"].mean():.2f}%')
axes[0].set_ylabel('Inflation (YoY %)', fontsize=12)
axes[0].set_title('Quarterly Inflation Rate', fontsize=14, fontweight='bold')
axes[0].legend(loc='upper right')
axes[0].grid(True, alpha=0.3)

# REIT returns time series
axes[1].plot(df['quarter'], df['reit_index_return'], 'g-', linewidth=2, marker='s', markersize=4)
axes[1].axhline(y=df['reit_index_return'].mean(), color='r', linestyle='--', alpha=0.7, label=f'Mean: {df["reit_index_return"].mean():.2f}%')
axes[1].set_xlabel('Quarter', fontsize=12)
axes[1].set_ylabel('REIT Index Return (%)', fontsize=12)
axes[1].set_title('Quarterly REIT Index Returns', fontsize=14, fontweight='bold')
axes[1].legend(loc='upper right')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/time_series_plot.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nSaved: report/images/time_series_plot.png")

# ============================================================================
# 3. SCATTER PLOT WITH REGRESSION LINE
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 8))

# Scatter plot
ax.scatter(df['inflation_yoy'], df['reit_index_return'], alpha=0.7, s=100, edgecolors='black', linewidth=1)

# Regression line
z = np.polyfit(df['inflation_yoy'], df['reit_index_return'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['inflation_yoy'].min(), df['inflation_yoy'].max(), 100)
ax.plot(x_line, p(x_line), "r--", linewidth=2, label=f'Linear fit: y={z[0]:.4f}x+{z[1]:.4f}')

# Labels and formatting
ax.set_xlabel('Inflation (YoY %)', fontsize=12)
ax.set_ylabel('REIT Index Return (%)', fontsize=12)
ax.set_title('REIT Returns vs. Inflation: Association Analysis', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3)

# Add correlation text
corr = df['inflation_yoy'].corr(df['reit_index_return'])
ax.text(0.05, 0.95, f'Pearson r = {corr:.4f}', transform=ax.transAxes, 
        fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/scatter_regression.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/scatter_regression.png")

# ============================================================================
# 4. CORRELATION ANALYSIS
# ============================================================================
print("\n2. CORRELATION ANALYSIS")
print("-" * 60)

# Pearson correlation
pearson_r, pearson_p = stats.pearsonr(df['inflation_yoy'], df['reit_index_return'])
print(f"Pearson Correlation: r = {pearson_r:.4f}, p-value = {pearson_p:.4f}")

# Spearman correlation (rank-based, robust to outliers)
spearman_r, spearman_p = stats.spearmanr(df['inflation_yoy'], df['reit_index_return'])
print(f"Spearman Correlation: ρ = {spearman_r:.4f}, p-value = {spearman_p:.4f}")

# Kendall's tau
kendall_tau, kendall_p = stats.kendalltau(df['inflation_yoy'], df['reit_index_return'])
print(f"Kendall's Tau: τ = {kendall_tau:.4f}, p-value = {kendall_p:.4f}")

# Save correlation results
corr_results = pd.DataFrame({
    'Method': ['Pearson', 'Spearman', 'Kendall'],
    'Coefficient': [pearson_r, spearman_r, kendall_tau],
    'P-value': [pearson_p, spearman_p, kendall_p]
})
corr_results.to_csv('outputs/correlation_analysis.csv', index=False)

# ============================================================================
# 5. ORDINARY LEAST SQUARES REGRESSION
# ============================================================================
print("\n3. OLS REGRESSION ANALYSIS")
print("-" * 60)

# Model 1: Simple linear regression
X = sm.add_constant(df['inflation_yoy'])
y = df['reit_index_return']

model_ols = sm.OLS(y, X).fit()
print(model_ols.summary())

# Save regression results
with open('outputs/ols_regression_summary.txt', 'w') as f:
    f.write(model_ols.summary().as_text())

# Extract key statistics
print("\nKey Regression Statistics:")
print(f"  R-squared: {model_ols.rsquared:.4f}")
print(f"  Adjusted R-squared: {model_ols.rsquared_adj:.4f}")
print(f"  F-statistic: {model_ols.fvalue:.4f} (p={model_ols.f_pvalue:.4f})")
print(f"  Inflation coefficient: {model_ols.params['inflation_yoy']:.4f} (p={model_ols.pvalues['inflation_yoy']:.4f})")
print(f"  Intercept: {model_ols.params['const']:.4f}")

# ============================================================================
# 6. DIAGNOSTIC TESTS
# ============================================================================
print("\n4. DIAGNOSTIC TESTS")
print("-" * 60)

# Durbin-Watson test for autocorrelation
dw_stat = durbin_watson(model_ols.resid)
print(f"Durbin-Watson statistic: {dw_stat:.4f}")
if dw_stat < 1.5:
    print("  -> Evidence of positive autocorrelation")
elif dw_stat > 2.5:
    print("  -> Evidence of negative autocorrelation")
else:
    print("  -> No significant autocorrelation detected")

# Breusch-Pagan test for heteroskedasticity
bp_test = het_breuschpagan(model_ols.resid, X)
print(f"\nBreusch-Pagan test (heteroskedasticity):")
print(f"  LM statistic: {bp_test[0]:.4f}, p-value: {bp_test[1]:.4f}")
if bp_test[1] < 0.05:
    print("  -> Heteroskedasticity detected")
else:
    print("  -> No significant heteroskedasticity")

# Ljung-Box test for autocorrelation in residuals
lb_test = acorr_ljungbox(model_ols.resid, lags=4, return_df=True)
print(f"\nLjung-Box test (residual autocorrelation):")
print(lb_test.head())

# Save residuals
df['residuals'] = model_ols.resid
df['fitted'] = model_ols.fittedvalues
df.to_csv('outputs/regression_data_with_residuals.csv', index=False)

# ============================================================================
# 7. RESIDUAL ANALYSIS PLOTS
# ============================================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Residuals vs Fitted
axes[0, 0].scatter(df['fitted'], df['residuals'], alpha=0.7, edgecolors='black')
axes[0, 0].axhline(y=0, color='r', linestyle='--')
axes[0, 0].set_xlabel('Fitted Values')
axes[0, 0].set_ylabel('Residuals')
axes[0, 0].set_title('Residuals vs Fitted')
axes[0, 0].grid(True, alpha=0.3)

# Q-Q plot
stats.probplot(df['residuals'], dist="norm", plot=axes[0, 1])
axes[0, 1].set_title('Q-Q Plot (Normality)')
axes[0, 1].grid(True, alpha=0.3)

# Histogram of residuals
axes[1, 0].hist(df['residuals'], bins=15, edgecolor='black', alpha=0.7, density=True)
axes[1, 0].set_xlabel('Residuals')
axes[1, 0].set_ylabel('Density')
axes[1, 0].set_title('Distribution of Residuals')
# Add normal curve
x_norm = np.linspace(df['residuals'].min(), df['residuals'].max(), 100)
y_norm = stats.norm.pdf(x_norm, df['residuals'].mean(), df['residuals'].std())
axes[1, 0].plot(x_norm, y_norm, 'r-', linewidth=2, label='Normal')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Residuals over time
axes[1, 1].plot(df['quarter'], df['residuals'], 'b-', marker='o', markersize=4)
axes[1, 1].axhline(y=0, color='r', linestyle='--')
axes[1, 1].set_xlabel('Quarter')
axes[1, 1].set_ylabel('Residuals')
axes[1, 1].set_title('Residuals Over Time')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/residual_diagnostics.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nSaved: report/images/residual_diagnostics.png")

# ============================================================================
# 8. DISTRIBUTION ANALYSIS
# ============================================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Inflation distribution
axes[0].hist(df['inflation_yoy'], bins=15, edgecolor='black', alpha=0.7, color='steelblue')
axes[0].axvline(df['inflation_yoy'].mean(), color='r', linestyle='--', linewidth=2, label=f'Mean: {df["inflation_yoy"].mean():.2f}')
axes[0].set_xlabel('Inflation (YoY %)')
axes[0].set_ylabel('Frequency')
axes[0].set_title('Distribution of Inflation')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# REIT returns distribution
axes[1].hist(df['reit_index_return'], bins=15, edgecolor='black', alpha=0.7, color='forestgreen')
axes[1].axvline(df['reit_index_return'].mean(), color='r', linestyle='--', linewidth=2, label=f'Mean: {df["reit_index_return"].mean():.2f}')
axes[1].set_xlabel('REIT Index Return (%)')
axes[1].set_ylabel('Frequency')
axes[1].set_title('Distribution of REIT Returns')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/distribution_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/distribution_analysis.png")

# ============================================================================
# 9. ROLLING CORRELATION ANALYSIS
# ============================================================================
print("\n5. ROLLING CORRELATION ANALYSIS")
print("-" * 60)

window = 8  # 8-quarter rolling window
df['rolling_corr'] = df['inflation_yoy'].rolling(window=window).corr(df['reit_index_return'])

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['quarter'], df['rolling_corr'], 'b-', linewidth=2, marker='o', markersize=4)
ax.axhline(y=0, color='r', linestyle='--', alpha=0.7)
ax.axhline(y=pearson_r, color='g', linestyle='--', alpha=0.7, label=f'Full-sample r = {pearson_r:.3f}')
ax.set_xlabel('Quarter', fontsize=12)
ax.set_ylabel('Rolling Correlation (8-quarter window)', fontsize=12)
ax.set_title('Time-Varying Correlation: REIT Returns vs. Inflation', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/rolling_correlation.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/rolling_correlation.png")

print(f"\nRolling correlation statistics:")
print(f"  Mean: {df['rolling_corr'].mean():.4f}")
print(f"  Std: {df['rolling_corr'].std():.4f}")
print(f"  Min: {df['rolling_corr'].min():.4f}")
print(f"  Max: {df['rolling_corr'].max():.4f}")

# ============================================================================
# 10. SUMMARY OUTPUT
# ============================================================================
print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)

# Create summary table
summary = {
    'Metric': [
        'Sample Size (quarters)',
        'Mean Inflation (%)',
        'Mean REIT Return (%)',
        'Pearson Correlation',
        'Correlation p-value',
        'R-squared',
        'Inflation Beta',
        'Beta p-value',
        'Durbin-Watson'
    ],
    'Value': [
        len(df),
        f"{df['inflation_yoy'].mean():.3f}",
        f"{df['reit_index_return'].mean():.3f}",
        f"{pearson_r:.4f}",
        f"{pearson_p:.4f}",
        f"{model_ols.rsquared:.4f}",
        f"{model_ols.params['inflation_yoy']:.4f}",
        f"{model_ols.pvalues['inflation_yoy']:.4f}",
        f"{dw_stat:.4f}"
    ]
}
summary_df = pd.DataFrame(summary)
summary_df.to_csv('outputs/analysis_summary.csv', index=False)
print("\nSummary saved to outputs/analysis_summary.csv")
print("\nAll figures saved to report/images/")
