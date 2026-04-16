#!/usr/bin/env python3
"""
Econometrics Analysis: REIT Returns and Inflation Association
Quarterly panel data analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import os

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Ensure output directories exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/reit_macro_quarterly.csv')
print("Data loaded successfully")
print(f"Shape: {df.shape}")
print(df.head())

# ============================================
# 1. DESCRIPTIVE STATISTICS
# ============================================
print("\n" + "="*50)
print("DESCRIPTIVE STATISTICS")
print("="*50)

desc_stats = df[['inflation_yoy', 'reit_index_return']].describe()
print(desc_stats)

# Save descriptive stats
desc_stats.to_csv('outputs/descriptive_stats.csv')

# ============================================
# 2. CORRELATION ANALYSIS
# ============================================
print("\n" + "="*50)
print("CORRELATION ANALYSIS")
print("="*50)

corr_matrix = df[['inflation_yoy', 'reit_index_return']].corr()
print(corr_matrix)

corr_val = corr_matrix.loc['inflation_yoy', 'reit_index_return']
print(f"\nCorrelation coefficient: {corr_val:.4f}")

# Pearson correlation test
pearson_corr, pearson_p = stats.pearsonr(df['inflation_yoy'], df['reit_index_return'])
print(f"Pearson correlation: {pearson_corr:.4f}, p-value: {pearson_p:.4f}")

# Spearman correlation test
spearman_corr, spearman_p = stats.spearmanr(df['inflation_yoy'], df['reit_index_return'])
print(f"Spearman correlation: {spearman_corr:.4f}, p-value: {spearman_p:.4f}")

# Save correlation results
corr_results = pd.DataFrame({
    'method': ['Pearson', 'Spearman'],
    'correlation': [pearson_corr, spearman_corr],
    'p_value': [pearson_p, spearman_p]
})
corr_results.to_csv('outputs/correlation_results.csv', index=False)

# ============================================
# 3. REGRESSION ANALYSIS
# ============================================
print("\n" + "="*50)
print("REGRESSION ANALYSIS")
print("="*50)

# Simple OLS: REIT returns on inflation
X = sm.add_constant(df['inflation_yoy'])
y = df['reit_index_return']

model = sm.OLS(y, X).fit()
print(model.summary())

# Save regression results
with open('outputs/regression_summary.txt', 'w') as f:
    f.write(model.summary().as_text())

# ============================================
# 4. VISUALIZATION
# ============================================
print("\n" + "="*50)
print("GENERATING FIGURES")
print("="*50)

# Figure 1: Time series plot of both variables
fig1, ax1 = plt.subplots(figsize=(12, 6))
ax1_twin = ax1.twinx()

ax1.plot(df['quarter'], df['inflation_yoy'], 'b-o', label='Inflation YoY (%)', linewidth=2, markersize=4)
ax1_twin.plot(df['quarter'], df['reit_index_return'], 'r-s', label='REIT Return (%)', linewidth=2, markersize=4)

ax1.set_xlabel('Quarter', fontsize=12)
ax1.set_ylabel('Inflation YoY (%)', color='b', fontsize=12)
ax1_twin.set_ylabel('REIT Index Return (%)', color='r', fontsize=12)
ax1.set_title('Quarterly Inflation and REIT Index Returns Over Time', fontsize=14, fontweight='bold')

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1_twin.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

ax1.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/timeseries_plot.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/timeseries_plot.png")

# Figure 2: Scatter plot with regression line
fig2, ax2 = plt.subplots(figsize=(10, 8))

sns.regplot(x='inflation_yoy', y='reit_index_return', data=df, 
            scatter_kws={'s': 80, 'alpha': 0.7}, 
            line_kws={'color': 'red', 'linewidth': 2},
            ax=ax2)

ax2.set_xlabel('Inflation YoY (%)', fontsize=12)
ax2.set_ylabel('REIT Index Return (%)', fontsize=12)
ax2.set_title('Association between Inflation and REIT Returns\n' + 
              f'Pearson r = {pearson_corr:.3f} (p = {pearson_p:.4f})', 
              fontsize=14, fontweight='bold')

# Add regression equation
slope = model.params['inflation_yoy']
intercept = model.params['const']
eq_text = f'REIT Return = {intercept:.4f} + {slope:.4f} × Inflation'
ax2.text(0.05, 0.95, eq_text, transform=ax2.transAxes, fontsize=11,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/scatter_regression.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/scatter_regression.png")

# Figure 3: Distribution plots
fig3, axes = plt.subplots(1, 2, figsize=(14, 5))

sns.histplot(df['inflation_yoy'], kde=True, ax=axes[0], color='blue', alpha=0.7)
axes[0].set_xlabel('Inflation YoY (%)', fontsize=12)
axes[0].set_ylabel('Frequency', fontsize=12)
axes[0].set_title('Distribution of Inflation Rates', fontsize=14, fontweight='bold')
axes[0].axvline(df['inflation_yoy'].mean(), color='red', linestyle='--', 
                label=f'Mean: {df["inflation_yoy"].mean():.2f}%')
axes[0].legend()

sns.histplot(df['reit_index_return'], kde=True, ax=axes[1], color='green', alpha=0.7)
axes[1].set_xlabel('REIT Index Return (%)', fontsize=12)
axes[1].set_ylabel('Frequency', fontsize=12)
axes[1].set_title('Distribution of REIT Returns', fontsize=14, fontweight='bold')
axes[1].axvline(df['reit_index_return'].mean(), color='red', linestyle='--',
                label=f'Mean: {df["reit_index_return"].mean():.2f}%')
axes[1].legend()

plt.tight_layout()
plt.savefig('report/images/distribution_plots.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/distribution_plots.png")

# Figure 4: Residual analysis
fig4, axes = plt.subplots(1, 2, figsize=(14, 5))

# Residuals vs Fitted
residuals = model.resid
fitted = model.fittedvalues

axes[0].scatter(fitted, residuals, alpha=0.7, s=60, edgecolors='black')
axes[0].axhline(y=0, color='red', linestyle='--')
axes[0].set_xlabel('Fitted Values', fontsize=12)
axes[0].set_ylabel('Residuals', fontsize=12)
axes[0].set_title('Residuals vs Fitted Values', fontsize=14, fontweight='bold')
axes[0].grid(True, alpha=0.3)

# Q-Q plot
sm.qqplot(residuals, line='45', ax=axes[1])
axes[1].set_title('Q-Q Plot of Residuals', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/residual_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/residual_analysis.png")

# Figure 5: Rolling correlation (if enough data points)
fig5, ax5 = plt.subplots(figsize=(12, 6))

# Calculate rolling correlation (window=8 quarters = 2 years)
window = 8
rolling_corr = df['inflation_yoy'].rolling(window=window).corr(df['reit_index_return'])

ax5.plot(df['quarter'], rolling_corr, 'm-o', linewidth=2, markersize=4, label=f'{window}-quarter rolling correlation')
ax5.axhline(y=rolling_corr.mean(), color='blue', linestyle='--', 
            label=f'Mean rolling corr: {rolling_corr.mean():.3f}')
ax5.axhline(y=0, color='black', linestyle='-', alpha=0.3)

ax5.set_xlabel('Quarter', fontsize=12)
ax5.set_ylabel('Rolling Correlation', fontsize=12)
ax5.set_title(f'Rolling Correlation between Inflation and REIT Returns ({window}-quarter window)', 
              fontsize=14, fontweight='bold')
ax5.legend()
ax5.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/rolling_correlation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/rolling_correlation.png")

# ============================================
# 5. LAG ANALYSIS (exploratory)
# ============================================
print("\n" + "="*50)
print("LAG ANALYSIS")
print("="*50)

# Create lagged inflation variables
for lag in range(1, 5):
    df[f'inflation_lag{lag}'] = df['inflation_yoy'].shift(lag)

# Test correlations with lags
lag_results = []
for lag in range(1, 5):
    lag_col = f'inflation_lag{lag}'
    valid_data = df[[lag_col, 'reit_index_return']].dropna()
    if len(valid_data) > 10:
        lag_corr, lag_p = stats.pearsonr(valid_data[lag_col], valid_data['reit_index_return'])
        lag_results.append({'lag': lag, 'correlation': lag_corr, 'p_value': lag_p})
        print(f"Lag {lag}: correlation = {lag_corr:.4f}, p-value = {lag_p:.4f}")

lag_df = pd.DataFrame(lag_results)
lag_df.to_csv('outputs/lag_analysis.csv', index=False)

print("\n" + "="*50)
print("ANALYSIS COMPLETE")
print("="*50)
print(f"\nKey Findings:")
print(f"- Overall correlation: {pearson_corr:.4f} (p={pearson_p:.4f})")
print(f"- Regression slope: {model.params['inflation_yoy']:.4f}")
print(f"- R-squared: {model.rsquared:.4f}")
print(f"\nAll outputs saved to outputs/ and report/images/")
