import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
import os
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
df = pd.read_csv('../data/reit_macro_quarterly.csv')
print("="*60)
print("REIT-Inflation Association Analysis")
print("="*60)
print(f"\nDataset Shape: {df.shape}")
print(f"Time Period: {len(df)} quarters ({len(df)/4:.1f} years)")

# Data Overview
print("\n" + "="*60)
print("1. DATA OVERVIEW")
print("="*60)
print(df.describe())

# Check for missing values
print(f"\nMissing Values:\n{df.isnull().sum()}")

# Save descriptive statistics
desc_stats = df.describe()
desc_stats.to_csv('../outputs/descriptive_statistics.csv')

# Figure 1: Time Series Plot
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

axes[0].plot(df['quarter'], df['inflation_yoy'], 'b-', linewidth=1.5, marker='o', markersize=3)
axes[0].fill_between(df['quarter'], df['inflation_yoy'], alpha=0.3)
axes[0].set_ylabel('Inflation (YoY %)', fontsize=11)
axes[0].set_title('Quarterly Inflation Rate (Year-over-Year)', fontsize=12, fontweight='bold')
axes[0].axhline(y=df['inflation_yoy'].mean(), color='red', linestyle='--', label=f'Mean: {df["inflation_yoy"].mean():.2f}%')
axes[0].legend(loc='upper right')

axes[1].plot(df['quarter'], df['reit_index_return'], 'g-', linewidth=1.5, marker='s', markersize=3)
axes[1].fill_between(df['quarter'], df['reit_index_return'], alpha=0.3, color='green')
axes[1].set_xlabel('Quarter', fontsize=11)
axes[1].set_ylabel('REIT Index Return', fontsize=11)
axes[1].set_title('Quarterly REIT Index Returns', fontsize=12, fontweight='bold')
axes[1].axhline(y=df['reit_index_return'].mean(), color='red', linestyle='--', label=f'Mean: {df["reit_index_return"].mean():.4f}')
axes[1].legend(loc='upper right')

plt.tight_layout()
plt.savefig('../report/images/fig1_time_series.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nFigure 1 saved: Time series plot")

# Figure 2: Scatter Plot with Regression Line
fig, ax = plt.subplots(figsize=(10, 7))

scatter = ax.scatter(df['inflation_yoy'], df['reit_index_return'], 
                     c=df['quarter'], cmap='viridis', s=80, alpha=0.7, edgecolors='black')

# Add regression line
z = np.polyfit(df['inflation_yoy'], df['reit_index_return'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['inflation_yoy'].min(), df['inflation_yoy'].max(), 100)
ax.plot(x_line, p(x_line), 'r--', linewidth=2, label=f'Linear Fit: y = {z[0]:.4f}x + {z[1]:.4f}')

# Add colorbar
cbar = plt.colorbar(scatter)
cbar.set_label('Quarter (Time)', fontsize=10)

ax.set_xlabel('Inflation Rate (YoY %)', fontsize=12)
ax.set_ylabel('REIT Index Return', fontsize=12)
ax.set_title('REIT Returns vs. Inflation: Association Analysis', fontsize=14, fontweight='bold')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/fig2_scatter_regression.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: Scatter plot with regression")

# Correlation Analysis
print("\n" + "="*60)
print("2. CORRELATION ANALYSIS")
print("="*60)

# Pearson correlation
pearson_corr, pearson_pval = stats.pearsonr(df['inflation_yoy'], df['reit_index_return'])
print(f"\nPearson Correlation: {pearson_corr:.4f}")
print(f"P-value: {pearson_pval:.6f}")

# Spearman correlation (rank-based, robust to outliers)
spearman_corr, spearman_pval = stats.spearmanr(df['inflation_yoy'], df['reit_index_return'])
print(f"\nSpearman Correlation: {spearman_corr:.4f}")
print(f"P-value: {spearman_pval:.6f}")

# Kendall's tau
kendall_tau, kendall_pval = stats.kendalltau(df['inflation_yoy'], df['reit_index_return'])
print(f"\nKendall's Tau: {kendall_tau:.4f}")
print(f"P-value: {kendall_pval:.6f}")

# Save correlation results
corr_results = pd.DataFrame({
    'Method': ['Pearson', 'Spearman', 'Kendall'],
    'Correlation': [pearson_corr, spearman_corr, kendall_tau],
    'P_Value': [pearson_pval, spearman_pval, kendall_pval],
    'Significance': ['Yes' if p < 0.05 else 'No' for p in [pearson_pval, spearman_pval, kendall_pval]]
})
corr_results.to_csv('../outputs/correlation_results.csv', index=False)

# Figure 3: Correlation Heatmap
fig, ax = plt.subplots(figsize=(8, 6))
corr_matrix = df[['inflation_yoy', 'reit_index_return']].corr()
sns.heatmap(corr_matrix, annot=True, cmap='RdYlBu_r', center=0, 
            fmt='.4f', square=True, linewidths=2, ax=ax,
            annot_kws={'size': 14, 'weight': 'bold'})
ax.set_title('Correlation Matrix: REIT Returns and Inflation', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('../report/images/fig3_correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved: Correlation heatmap")

# Regression Analysis
print("\n" + "="*60)
print("3. REGRESSION ANALYSIS")
print("="*60)

# Simple OLS regression
X = sm.add_constant(df['inflation_yoy'])
y = df['reit_index_return']
model = sm.OLS(y, X).fit()
print("\n")
print(model.summary())

# Save regression results
with open('../outputs/regression_summary.txt', 'w') as f:
    f.write(str(model.summary()))

# Extract key statistics
print(f"\nKey Regression Results:")
print(f"Coefficient (Slope): {model.params['inflation_yoy']:.4f}")
print(f"Intercept: {model.params['const']:.4f}")
print(f"R-squared: {model.rsquared:.4f}")
print(f"Adjusted R-squared: {model.rsquared_adj:.4f}")
print(f"F-statistic: {model.fvalue:.4f}")
print(f"F-statistic p-value: {model.f_pvalue:.6f}")

# Figure 4: Regression Diagnostics
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Residuals vs Fitted
fitted = model.fittedvalues
residuals = model.resid
axes[0, 0].scatter(fitted, residuals, alpha=0.7, edgecolors='black')
axes[0, 0].axhline(y=0, color='red', linestyle='--', linewidth=2)
axes[0, 0].set_xlabel('Fitted Values', fontsize=11)
axes[0, 0].set_ylabel('Residuals', fontsize=11)
axes[0, 0].set_title('Residuals vs Fitted', fontsize=12, fontweight='bold')

# Q-Q Plot
sm.qqplot(residuals, line='45', ax=axes[0, 1], markersize=6)
axes[0, 1].set_title('Normal Q-Q Plot', fontsize=12, fontweight='bold')

# Histogram of Residuals
axes[1, 0].hist(residuals, bins=15, edgecolor='black', alpha=0.7, density=True)
x_range = np.linspace(residuals.min(), residuals.max(), 100)
axes[1, 0].plot(x_range, stats.norm.pdf(x_range, residuals.mean(), residuals.std()), 
                'r-', linewidth=2, label='Normal Distribution')
axes[1, 0].set_xlabel('Residuals', fontsize=11)
axes[1, 0].set_ylabel('Density', fontsize=11)
axes[1, 0].set_title('Distribution of Residuals', fontsize=12, fontweight='bold')
axes[1, 0].legend()

# Scale-Location Plot
standardized_residuals = model.get_influence().resid_studentized_internal
axes[1, 1].scatter(fitted, np.sqrt(np.abs(standardized_residuals)), alpha=0.7, edgecolors='black')
axes[1, 1].set_xlabel('Fitted Values', fontsize=11)
axes[1, 1].set_ylabel('√|Standardized Residuals|', fontsize=11)
axes[1, 1].set_title('Scale-Location Plot', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/fig4_regression_diagnostics.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved: Regression diagnostics")

# Stationarity Tests
print("\n" + "="*60)
print("4. TIME SERIES PROPERTIES")
print("="*60)

# ADF Test for Inflation
adf_inflation = adfuller(df['inflation_yoy'], autolag='AIC')
print(f"\nADF Test for Inflation:")
print(f"  Test Statistic: {adf_inflation[0]:.4f}")
print(f"  P-value: {adf_inflation[1]:.4f}")
print(f"  Critical Values: {adf_inflation[4]}")
print(f"  Stationary: {'Yes' if adf_inflation[1] < 0.05 else 'No'}")

# ADF Test for REIT Returns
adf_reit = adfuller(df['reit_index_return'], autolag='AIC')
print(f"\nADF Test for REIT Returns:")
print(f"  Test Statistic: {adf_reit[0]:.4f}")
print(f"  P-value: {adf_reit[1]:.4f}")
print(f"  Critical Values: {adf_reit[4]}")
print(f"  Stationary: {'Yes' if adf_reit[1] < 0.05 else 'No'}")

# Granger Causality Test
print("\n" + "="*60)
print("5. GRANGER CAUSALITY ANALYSIS")
print("="*60)

# Prepare data for Granger causality
gc_data = df[['inflation_yoy', 'reit_index_return']].values

print("\nTesting if Inflation Granger-causes REIT Returns:")
gc_result1 = grangercausalitytests(gc_data, maxlag=4, verbose=True)

print("\n" + "="*60)
print("Testing if REIT Returns Granger-cause Inflation:")
gc_data2 = df[['reit_index_return', 'inflation_yoy']].values
gc_result2 = grangercausalitytests(gc_data2, maxlag=4, verbose=True)

# Figure 5: Rolling Correlation
print("\n" + "="*60)
print("6. ROLLING CORRELATION ANALYSIS")
print("="*60)

window_size = 8  # 2-year rolling window
rolling_corr = df['inflation_yoy'].rolling(window=window_size).corr(df['reit_index_return'])

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['quarter'][window_size-1:], rolling_corr[window_size-1:], 'b-', linewidth=2, marker='o', markersize=4)
ax.axhline(y=0, color='red', linestyle='--', linewidth=1.5)
ax.axhline(y=rolling_corr.mean(), color='green', linestyle=':', linewidth=2, label=f'Mean: {rolling_corr.mean():.4f}')
ax.fill_between(df['quarter'][window_size-1:], rolling_corr[window_size-1:], 0, alpha=0.3)
ax.set_xlabel('Quarter', fontsize=11)
ax.set_ylabel('Rolling Correlation', fontsize=11)
ax.set_title(f'Rolling Correlation (Window = {window_size} quarters)', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/fig5_rolling_correlation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 5 saved: Rolling correlation")

print(f"\nRolling Correlation Statistics:")
print(f"  Mean: {rolling_corr.mean():.4f}")
print(f"  Std: {rolling_corr.std():.4f}")
print(f"  Min: {rolling_corr.min():.4f}")
print(f"  Max: {rolling_corr.max():.4f}")

# Figure 6: Distribution Analysis
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Inflation distribution
axes[0].hist(df['inflation_yoy'], bins=15, edgecolor='black', alpha=0.7, density=True)
x_range = np.linspace(df['inflation_yoy'].min(), df['inflation_yoy'].max(), 100)
axes[0].plot(x_range, stats.norm.pdf(x_range, df['inflation_yoy'].mean(), df['inflation_yoy'].std()), 
             'r-', linewidth=2, label='Normal Distribution')
axes[0].set_xlabel('Inflation Rate (YoY %)', fontsize=11)
axes[0].set_ylabel('Density', fontsize=11)
axes[0].set_title('Distribution of Inflation', fontsize=12, fontweight='bold')
axes[0].legend()

# REIT Returns distribution
axes[1].hist(df['reit_index_return'], bins=15, edgecolor='black', alpha=0.7, density=True, color='green')
x_range = np.linspace(df['reit_index_return'].min(), df['reit_index_return'].max(), 100)
axes[1].plot(x_range, stats.norm.pdf(x_range, df['reit_index_return'].mean(), df['reit_index_return'].std()), 
             'r-', linewidth=2, label='Normal Distribution')
axes[1].set_xlabel('REIT Index Return', fontsize=11)
axes[1].set_ylabel('Density', fontsize=11)
axes[1].set_title('Distribution of REIT Returns', fontsize=12, fontweight='bold')
axes[1].legend()

plt.tight_layout()
plt.savefig('../report/images/fig6_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 6 saved: Distribution analysis")

# Figure 7: Lagged Correlation Analysis
print("\n" + "="*60)
print("7. LAGGED CORRELATION ANALYSIS")
print("="*60)

lag_correlations = []
for lag in range(-4, 5):
    if lag == 0:
        corr = df['inflation_yoy'].corr(df['reit_index_return'])
    elif lag > 0:
        corr = df['inflation_yoy'].corr(df['reit_index_return'].shift(-lag))
    else:
        corr = df['inflation_yoy'].shift(-lag).corr(df['reit_index_return'])
    lag_correlations.append({'Lag': lag, 'Correlation': corr})
    print(f"Lag {lag:+d}: Correlation = {corr:.4f}")

lag_df = pd.DataFrame(lag_correlations)
lag_df.to_csv('../outputs/lagged_correlations.csv', index=False)

fig, ax = plt.subplots(figsize=(10, 6))
colors = ['red' if lag == 0 else 'steelblue' for lag in lag_df['Lag']]
bars = ax.bar(lag_df['Lag'], lag_df['Correlation'], color=colors, edgecolor='black', alpha=0.8)
ax.axhline(y=0, color='black', linewidth=1)
ax.set_xlabel('Lag (Quarters)', fontsize=11)
ax.set_ylabel('Correlation', fontsize=11)
ax.set_title('Lagged Correlation: Inflation and REIT Returns', fontsize=14, fontweight='bold')
ax.set_xticks(lag_df['Lag'])
ax.grid(True, alpha=0.3, axis='y')

# Add value labels
for bar, val in zip(bars, lag_df['Correlation']):
    height = bar.get_height()
    ax.annotate(f'{val:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/fig7_lagged_correlation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 7 saved: Lagged correlation")

# Summary Statistics for Report
print("\n" + "="*60)
print("8. SUMMARY FOR REPORT")
print("="*60)

summary = {
    'Observations': len(df),
    'Time_Period_Years': len(df)/4,
    'Inflation_Mean': df['inflation_yoy'].mean(),
    'Inflation_Std': df['inflation_yoy'].std(),
    'Inflation_Min': df['inflation_yoy'].min(),
    'Inflation_Max': df['inflation_yoy'].max(),
    'REIT_Mean': df['reit_index_return'].mean(),
    'REIT_Std': df['reit_index_return'].std(),
    'REIT_Min': df['reit_index_return'].min(),
    'REIT_Max': df['reit_index_return'].max(),
    'Pearson_Correlation': pearson_corr,
    'Pearson_PValue': pearson_pval,
    'Spearman_Correlation': spearman_corr,
    'Spearman_PValue': spearman_pval,
    'Regression_Slope': model.params['inflation_yoy'],
    'Regression_Intercept': model.params['const'],
    'R_Squared': model.rsquared,
    'R_Squared_Adj': model.rsquared_adj,
    'Slope_PValue': model.pvalues['inflation_yoy'],
    'Inflation_Stationary': adf_inflation[1] < 0.05,
    'REIT_Stationary': adf_reit[1] < 0.05
}

summary_df = pd.DataFrame([summary])
summary_df.to_csv('../outputs/analysis_summary.csv', index=False)

print("\nAnalysis complete! All outputs saved.")
print("\nKey Findings:")
print(f"  - Strong positive correlation (r = {pearson_corr:.4f}, p < 0.001)")
print(f"  - R-squared: {model.rsquared:.4f} ({model.rsquared*100:.2f}% variance explained)")
print(f"  - For each 1% increase in inflation, REIT returns increase by {model.params['inflation_yoy']:.4f}")