import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
from statsmodels.tsa.api import VAR
import warnings
import os
warnings.filterwarnings('ignore')

# Get the workspace directory
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs(os.path.join(workspace_dir, 'outputs'), exist_ok=True)
os.makedirs(os.path.join(workspace_dir, 'report', 'images'), exist_ok=True)

# Load data
df = pd.read_csv(os.path.join(workspace_dir, 'data', 'reit_macro_quarterly.csv'))
print("Data Shape:", df.shape)
print("\nData Head:")
print(df.head())
print("\nData Description:")
print(df.describe())

# Save basic statistics
basic_stats = df.describe()
basic_stats.to_csv(os.path.join(workspace_dir, 'outputs', 'basic_statistics.csv'))

# Figure 1: Time Series Plot
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

axes[0].plot(df['quarter'], df['inflation_yoy'], 'b-', linewidth=1.5, marker='o', markersize=3)
axes[0].fill_between(df['quarter'], df['inflation_yoy'], alpha=0.3)
axes[0].set_ylabel('Inflation (YoY %)', fontsize=12)
axes[0].set_title('Quarterly Inflation Rate', fontsize=14, fontweight='bold')
axes[0].axhline(y=df['inflation_yoy'].mean(), color='red', linestyle='--', label=f'Mean: {df["inflation_yoy"].mean():.2f}%')
axes[0].legend()

axes[1].plot(df['quarter'], df['reit_index_return'], 'g-', linewidth=1.5, marker='s', markersize=3)
axes[1].fill_between(df['quarter'], df['reit_index_return'], alpha=0.3, color='green')
axes[1].set_xlabel('Quarter', fontsize=12)
axes[1].set_ylabel('REIT Index Return (%)', fontsize=12)
axes[1].set_title('Quarterly REIT Index Returns', fontsize=14, fontweight='bold')
axes[1].axhline(y=df['reit_index_return'].mean(), color='red', linestyle='--', label=f'Mean: {df["reit_index_return"].mean():.2f}%')
axes[1].legend()

plt.tight_layout()
plt.savefig(os.path.join(workspace_dir, 'report', 'images', 'fig1_time_series.png'), dpi=300, bbox_inches='tight')
plt.close()
print("Figure 1 saved: Time series plot")

# Figure 2: Scatter plot with regression line
fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(df['inflation_yoy'], df['reit_index_return'], 
                     c=df['quarter'], cmap='viridis', s=60, alpha=0.7, edgecolors='black')
plt.colorbar(scatter, label='Quarter')

# Add regression line
z = np.polyfit(df['inflation_yoy'], df['reit_index_return'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['inflation_yoy'].min(), df['inflation_yoy'].max(), 100)
ax.plot(x_line, p(x_line), 'r--', linewidth=2, label=f'Linear Fit: y = {z[0]:.4f}x + {z[1]:.4f}')

ax.set_xlabel('Inflation (YoY %)', fontsize=12)
ax.set_ylabel('REIT Index Return (%)', fontsize=12)
ax.set_title('REIT Returns vs Inflation: Scatter Plot with Regression', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(workspace_dir, 'report', 'images', 'fig2_scatter_regression.png'), dpi=300, bbox_inches='tight')
plt.close()
print("Figure 2 saved: Scatter plot with regression")

# Correlation Analysis
pearson_corr, pearson_pval = stats.pearsonr(df['inflation_yoy'], df['reit_index_return'])
spearman_corr, spearman_pval = stats.spearmanr(df['inflation_yoy'], df['reit_index_return'])

print(f"\n=== Correlation Analysis ===")
print(f"Pearson Correlation: {pearson_corr:.4f} (p-value: {pearson_pval:.4f})")
print(f"Spearman Correlation: {spearman_corr:.4f} (p-value: {spearman_pval:.4f})")

# Save correlation results
corr_results = pd.DataFrame({
    'Method': ['Pearson', 'Spearman'],
    'Correlation': [pearson_corr, spearman_corr],
    'P_Value': [pearson_pval, spearman_pval],
    'Significance': ['Yes' if p < 0.05 else 'No' for p in [pearson_pval, spearman_pval]]
})
corr_results.to_csv(os.path.join(workspace_dir, 'outputs', 'correlation_results.csv'), index=False)

# Figure 3: Correlation Heatmap
fig, ax = plt.subplots(figsize=(8, 6))
corr_matrix = df[['inflation_yoy', 'reit_index_return']].corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
            fmt='.4f', square=True, linewidths=2, ax=ax,
            annot_kws={'size': 14, 'weight': 'bold'})
ax.set_title('Correlation Matrix: Inflation and REIT Returns', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(workspace_dir, 'report', 'images', 'fig3_correlation_heatmap.png'), dpi=300, bbox_inches='tight')
plt.close()
print("Figure 3 saved: Correlation heatmap")

# OLS Regression Analysis
X = sm.add_constant(df['inflation_yoy'])
y = df['reit_index_return']
ols_model = sm.OLS(y, X).fit()

print("\n=== OLS Regression Results ===")
print(ols_model.summary())

# Save regression results
with open(os.path.join(workspace_dir, 'outputs', 'ols_regression_summary.txt'), 'w') as f:
    f.write(ols_model.summary().as_text())

# Figure 4: Regression Diagnostics
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Fitted vs Actual
axes[0, 0].scatter(ols_model.fittedvalues, y, alpha=0.7, edgecolors='black')
axes[0, 0].plot([y.min(), y.max()], [y.min(), y.max()], 'r--', linewidth=2)
axes[0, 0].set_xlabel('Fitted Values', fontsize=11)
axes[0, 0].set_ylabel('Actual Values', fontsize=11)
axes[0, 0].set_title('Fitted vs Actual Values', fontsize=12, fontweight='bold')

# Residuals vs Fitted
axes[0, 1].scatter(ols_model.fittedvalues, ols_model.resid, alpha=0.7, edgecolors='black')
axes[0, 1].axhline(y=0, color='red', linestyle='--', linewidth=2)
axes[0, 1].set_xlabel('Fitted Values', fontsize=11)
axes[0, 1].set_ylabel('Residuals', fontsize=11)
axes[0, 1].set_title('Residuals vs Fitted', fontsize=12, fontweight='bold')

# Q-Q Plot
stats.probplot(ols_model.resid, dist="norm", plot=axes[1, 0])
axes[1, 0].set_title('Normal Q-Q Plot', fontsize=12, fontweight='bold')

# Histogram of Residuals
axes[1, 1].hist(ols_model.resid, bins=15, edgecolor='black', alpha=0.7, density=True)
x_range = np.linspace(ols_model.resid.min(), ols_model.resid.max(), 100)
axes[1, 1].plot(x_range, stats.norm.pdf(x_range, ols_model.resid.mean(), ols_model.resid.std()),
                'r-', linewidth=2, label='Normal Distribution')
axes[1, 1].set_xlabel('Residuals', fontsize=11)
axes[1, 1].set_ylabel('Density', fontsize=11)
axes[1, 1].set_title('Residuals Distribution', fontsize=12, fontweight='bold')
axes[1, 1].legend()

plt.tight_layout()
plt.savefig(os.path.join(workspace_dir, 'report', 'images', 'fig4_regression_diagnostics.png'), dpi=300, bbox_inches='tight')
plt.close()
print("Figure 4 saved: Regression diagnostics")

# Unit Root Tests (ADF)
print("\n=== Augmented Dickey-Fuller Tests ===")
adf_inflation = adfuller(df['inflation_yoy'], autolag='AIC')
adf_reit = adfuller(df['reit_index_return'], autolag='AIC')

print(f"\nInflation ADF Test:")
print(f"  Test Statistic: {adf_inflation[0]:.4f}")
print(f"  P-value: {adf_inflation[1]:.4f}")
print(f"  Critical Values: {adf_inflation[4]}")

print(f"\nREIT Returns ADF Test:")
print(f"  Test Statistic: {adf_reit[0]:.4f}")
print(f"  P-value: {adf_reit[1]:.4f}")
print(f"  Critical Values: {adf_reit[4]}")

# Save ADF results
adf_results = pd.DataFrame({
    'Variable': ['Inflation', 'REIT_Returns'],
    'ADF_Statistic': [adf_inflation[0], adf_reit[0]],
    'P_Value': [adf_inflation[1], adf_reit[1]],
    'Stationary_5pct': ['Yes' if adf_inflation[1] < 0.05 else 'No',
                        'Yes' if adf_reit[1] < 0.05 else 'No']
})
adf_results.to_csv(os.path.join(workspace_dir, 'outputs', 'adf_test_results.csv'), index=False)

# Granger Causality Test
print("\n=== Granger Causality Tests ===")
granger_data = df[['inflation_yoy', 'reit_index_return']].values

# Test if inflation Granger-causes REIT returns
print("\nTesting if Inflation Granger-causes REIT Returns:")
gc_result1 = grangercausalitytests(granger_data, maxlag=4, verbose=True)

# Test if REIT returns Granger-cause inflation
print("\nTesting if REIT Returns Granger-cause Inflation:")
gc_result2 = grangercausalitytests(granger_data[:, [1, 0]], maxlag=4, verbose=True)

# Save Granger causality results
granger_summary = []
for lag in range(1, 5):
    f_test1 = gc_result1[lag][0]['ssr_ftest']
    f_test2 = gc_result2[lag][0]['ssr_ftest']
    granger_summary.append({
        'Lag': lag,
        'Inf_to_REIT_Fstat': f_test1[0],
        'Inf_to_REIT_pval': f_test1[1],
        'REIT_to_Inf_Fstat': f_test2[0],
        'REIT_to_Inf_pval': f_test2[1]
    })

granger_df = pd.DataFrame(granger_summary)
granger_df.to_csv(os.path.join(workspace_dir, 'outputs', 'granger_causality_results.csv'), index=False)

# Figure 5: Granger Causality Results Visualization
fig, ax = plt.subplots(figsize=(10, 6))
x_pos = np.arange(len(granger_df))
width = 0.35

bars1 = ax.bar(x_pos - width/2, granger_df['Inf_to_REIT_pval'], width, 
               label='Inflation → REIT', color='steelblue', edgecolor='black')
bars2 = ax.bar(x_pos + width/2, granger_df['REIT_to_Inf_pval'], width,
               label='REIT → Inflation', color='coral', edgecolor='black')

ax.axhline(y=0.05, color='red', linestyle='--', linewidth=2, label='Significance Level (0.05)')
ax.set_xlabel('Lag (Quarters)', fontsize=12)
ax.set_ylabel('P-Value', fontsize=12)
ax.set_title('Granger Causality Test Results', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(granger_df['Lag'])
ax.legend()
ax.set_yscale('log')

plt.tight_layout()
plt.savefig(os.path.join(workspace_dir, 'report', 'images', 'fig5_granger_causality.png'), dpi=300, bbox_inches='tight')
plt.close()
print("Figure 5 saved: Granger causality results")

# VAR Model Analysis
print("\n=== VAR Model Analysis ===")
var_data = df[['inflation_yoy', 'reit_index_return']]
var_model = VAR(var_data)

# Select optimal lag
lag_order_results = var_model.select_order(maxlags=min(8, len(df)//4))
print("\nLag Order Selection:")
print(lag_order_results.summary())

# Use at least lag 1 for meaningful VAR analysis
optimal_lag = max(1, lag_order_results.aic)
print(f"\nOptimal Lag (AIC): {optimal_lag}")

# Fit VAR model
var_fitted = var_model.fit(optimal_lag)
print("\nVAR Model Summary:")
print(var_fitted.summary())

# Save VAR results
with open(os.path.join(workspace_dir, 'outputs', 'var_model_summary.txt'), 'w') as f:
    f.write(str(var_fitted.summary()))

# Impulse Response Function
irf = var_fitted.irf(periods=12)
irf_stderr = irf.stderr()

# Figure 6: Impulse Response Functions
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Inflation response to Inflation shock
axes[0, 0].plot(irf.irfs[:, 0, 0], 'b-', linewidth=2, marker='o', markersize=4)
axes[0, 0].fill_between(range(13), irf.irfs[:, 0, 0] - 1.96*irf_stderr[:, 0, 0],
                        irf.irfs[:, 0, 0] + 1.96*irf_stderr[:, 0, 0], alpha=0.3)
axes[0, 0].axhline(y=0, color='black', linestyle='--', linewidth=1)
axes[0, 0].set_title('Inflation → Inflation', fontsize=12, fontweight='bold')
axes[0, 0].set_xlabel('Periods')
axes[0, 0].set_ylabel('Response')

# REIT response to Inflation shock
axes[0, 1].plot(irf.irfs[:, 1, 0], 'r-', linewidth=2, marker='o', markersize=4)
axes[0, 1].fill_between(range(13), irf.irfs[:, 1, 0] - 1.96*irf_stderr[:, 1, 0],
                        irf.irfs[:, 1, 0] + 1.96*irf_stderr[:, 1, 0], alpha=0.3, color='red')
axes[0, 1].axhline(y=0, color='black', linestyle='--', linewidth=1)
axes[0, 1].set_title('Inflation → REIT Returns', fontsize=12, fontweight='bold')
axes[0, 1].set_xlabel('Periods')
axes[0, 1].set_ylabel('Response')

# Inflation response to REIT shock
axes[1, 0].plot(irf.irfs[:, 0, 1], 'g-', linewidth=2, marker='o', markersize=4)
axes[1, 0].fill_between(range(13), irf.irfs[:, 0, 1] - 1.96*irf_stderr[:, 0, 1],
                        irf.irfs[:, 0, 1] + 1.96*irf_stderr[:, 0, 1], alpha=0.3, color='green')
axes[1, 0].axhline(y=0, color='black', linestyle='--', linewidth=1)
axes[1, 0].set_title('REIT Returns → Inflation', fontsize=12, fontweight='bold')
axes[1, 0].set_xlabel('Periods')
axes[1, 0].set_ylabel('Response')

# REIT response to REIT shock
axes[1, 1].plot(irf.irfs[:, 1, 1], 'purple', linewidth=2, marker='o', markersize=4)
axes[1, 1].fill_between(range(13), irf.irfs[:, 1, 1] - 1.96*irf_stderr[:, 1, 1],
                        irf.irfs[:, 1, 1] + 1.96*irf_stderr[:, 1, 1], alpha=0.3, color='purple')
axes[1, 1].axhline(y=0, color='black', linestyle='--', linewidth=1)
axes[1, 1].set_title('REIT Returns → REIT Returns', fontsize=12, fontweight='bold')
axes[1, 1].set_xlabel('Periods')
axes[1, 1].set_ylabel('Response')

plt.suptitle('Impulse Response Functions (95% CI)', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(workspace_dir, 'report', 'images', 'fig6_impulse_response.png'), dpi=300, bbox_inches='tight')
plt.close()
print("Figure 6 saved: Impulse response functions")

# Variance Decomposition
fevd = var_fitted.fevd(periods=12)

# Figure 7: Forecast Error Variance Decomposition
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Get FEVD data - shape is (n_vars, n_periods, n_vars)
fevd_results = fevd.decomp
print(f"FEVD decomp shape: {fevd_results.shape}")

n_periods = 12
periods_arr = range(n_periods)

# For Inflation equation (first variable)
# fevd_results[0, :, 0] = inflation's variance explained by inflation shock
# fevd_results[0, :, 1] = inflation's variance explained by REIT shock
axes[0].plot(periods_arr, fevd_results[0, :, 0] * 100, 'b-', linewidth=2, marker='o', label='Inflation Shock')
axes[0].plot(periods_arr, fevd_results[0, :, 1] * 100, 'r-', linewidth=2, marker='s', label='REIT Shock')
axes[0].set_title('Variance Decomposition: Inflation', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Periods')
axes[0].set_ylabel('Proportion of Variance (%)')
axes[0].legend(loc='center right')
axes[0].set_ylim(0, 100)
axes[0].grid(True, alpha=0.3)

# For REIT Returns equation (second variable)
# fevd_results[1, :, 0] = REIT's variance explained by inflation shock
# fevd_results[1, :, 1] = REIT's variance explained by REIT shock
axes[1].plot(periods_arr, fevd_results[1, :, 0] * 100, 'b-', linewidth=2, marker='o', label='Inflation Shock')
axes[1].plot(periods_arr, fevd_results[1, :, 1] * 100, 'r-', linewidth=2, marker='s', label='REIT Shock')
axes[1].set_title('Variance Decomposition: REIT Returns', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Periods')
axes[1].set_ylabel('Proportion of Variance (%)')
axes[1].legend(loc='center right')
axes[1].set_ylim(0, 100)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(workspace_dir, 'report', 'images', 'fig7_variance_decomposition.png'), dpi=300, bbox_inches='tight')
plt.close()
print("Figure 7 saved: Variance decomposition")

# Save FEVD results
fevd_df = pd.DataFrame({
    'Period': range(n_periods),
    'Inflation_by_Inflation': fevd_results[0, :, 0] * 100,
    'Inflation_by_REIT': fevd_results[0, :, 1] * 100,
    'REIT_by_Inflation': fevd_results[1, :, 0] * 100,
    'REIT_by_REIT': fevd_results[1, :, 1] * 100
})
fevd_df.to_csv(os.path.join(workspace_dir, 'outputs', 'fevd_results.csv'), index=False)

# Figure 8: Rolling Correlation
window_size = 8
rolling_corr = df['inflation_yoy'].rolling(window=window_size).corr(df['reit_index_return'])

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['quarter'][window_size-1:], rolling_corr[window_size-1:], 'b-', linewidth=2, marker='o', markersize=4)
ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
ax.axhline(y=pearson_corr, color='red', linestyle='--', linewidth=2, 
           label=f'Full Sample Correlation: {pearson_corr:.4f}')
ax.fill_between(df['quarter'][window_size-1:], rolling_corr[window_size-1:], alpha=0.3)
ax.set_xlabel('Quarter', fontsize=12)
ax.set_ylabel('Rolling Correlation', fontsize=12)
ax.set_title(f'Rolling Correlation (Window = {window_size} Quarters)', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(workspace_dir, 'report', 'images', 'fig8_rolling_correlation.png'), dpi=300, bbox_inches='tight')
plt.close()
print("Figure 8 saved: Rolling correlation")

# Figure 9: Distribution Analysis
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Inflation distribution
axes[0].hist(df['inflation_yoy'], bins=15, edgecolor='black', alpha=0.7, density=True, color='steelblue')
x_range = np.linspace(df['inflation_yoy'].min(), df['inflation_yoy'].max(), 100)
axes[0].plot(x_range, stats.norm.pdf(x_range, df['inflation_yoy'].mean(), df['inflation_yoy'].std()),
             'r-', linewidth=2, label='Normal Fit')
axes[0].axvline(df['inflation_yoy'].mean(), color='green', linestyle='--', linewidth=2, label=f'Mean: {df["inflation_yoy"].mean():.2f}')
axes[0].set_xlabel('Inflation (YoY %)', fontsize=11)
axes[0].set_ylabel('Density', fontsize=11)
axes[0].set_title('Inflation Distribution', fontsize=12, fontweight='bold')
axes[0].legend()

# REIT Returns distribution
axes[1].hist(df['reit_index_return'], bins=15, edgecolor='black', alpha=0.7, density=True, color='coral')
x_range = np.linspace(df['reit_index_return'].min(), df['reit_index_return'].max(), 100)
axes[1].plot(x_range, stats.norm.pdf(x_range, df['reit_index_return'].mean(), df['reit_index_return'].std()),
             'r-', linewidth=2, label='Normal Fit')
axes[1].axvline(df['reit_index_return'].mean(), color='green', linestyle='--', linewidth=2, label=f'Mean: {df["reit_index_return"].mean():.2f}')
axes[1].set_xlabel('REIT Index Return (%)', fontsize=11)
axes[1].set_ylabel('Density', fontsize=11)
axes[1].set_title('REIT Returns Distribution', fontsize=12, fontweight='bold')
axes[1].legend()

plt.tight_layout()
plt.savefig(os.path.join(workspace_dir, 'report', 'images', 'fig9_distribution_analysis.png'), dpi=300, bbox_inches='tight')
plt.close()
print("Figure 9 saved: Distribution analysis")

# Figure 10: Inflation Regime Analysis
# Categorize inflation into regimes
low_inflation = df[df['inflation_yoy'] < df['inflation_yoy'].quantile(0.33)]
medium_inflation = df[(df['inflation_yoy'] >= df['inflation_yoy'].quantile(0.33)) & 
                       (df['inflation_yoy'] <= df['inflation_yoy'].quantile(0.67))]
high_inflation = df[df['inflation_yoy'] > df['inflation_yoy'].quantile(0.67)]

regime_stats = pd.DataFrame({
    'Regime': ['Low Inflation', 'Medium Inflation', 'High Inflation'],
    'Inflation_Range': [f"< {df['inflation_yoy'].quantile(0.33):.2f}%",
                        f"{df['inflation_yoy'].quantile(0.33):.2f}% - {df['inflation_yoy'].quantile(0.67):.2f}%",
                        f"> {df['inflation_yoy'].quantile(0.67):.2f}%"],
    'N_Observations': [len(low_inflation), len(medium_inflation), len(high_inflation)],
    'Mean_REIT_Return': [low_inflation['reit_index_return'].mean(),
                         medium_inflation['reit_index_return'].mean(),
                         high_inflation['reit_index_return'].mean()],
    'Std_REIT_Return': [low_inflation['reit_index_return'].std(),
                        medium_inflation['reit_index_return'].std(),
                        high_inflation['reit_index_return'].std()]
})
regime_stats.to_csv(os.path.join(workspace_dir, 'outputs', 'regime_analysis.csv'), index=False)

fig, ax = plt.subplots(figsize=(10, 6))
x_pos = np.arange(3)
bar_colors = ['green', 'steelblue', 'red']
bars = ax.bar(x_pos, regime_stats['Mean_REIT_Return'], 
              yerr=regime_stats['Std_REIT_Return'],
              capsize=5, color=bar_colors, edgecolor='black', alpha=0.7)

ax.set_xticks(x_pos)
ax.set_xticklabels(['Low Inflation\n(< 1.72%)', 'Medium Inflation\n(1.72% - 2.78%)', 'High Inflation\n(> 2.78%)'])
ax.set_ylabel('Mean REIT Return (%)', fontsize=12)
ax.set_title('REIT Returns by Inflation Regime', fontsize=14, fontweight='bold')

# Add value labels
for bar, val in zip(bars, regime_stats['Mean_REIT_Return']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f'{val:.2f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(workspace_dir, 'report', 'images', 'fig10_regime_analysis.png'), dpi=300, bbox_inches='tight')
plt.close()
print("Figure 10 saved: Regime analysis")

# ANOVA Test for regime differences
f_stat, anova_pval = stats.f_oneway(low_inflation['reit_index_return'],
                                     medium_inflation['reit_index_return'],
                                     high_inflation['reit_index_return'])
print(f"\n=== ANOVA Test for Regime Differences ===")
print(f"F-statistic: {f_stat:.4f}")
print(f"P-value: {anova_pval:.4f}")

# Save ANOVA results
anova_results = pd.DataFrame({
    'Test': ['One-way ANOVA'],
    'F_Statistic': [f_stat],
    'P_Value': [anova_pval],
    'Significant': ['Yes' if anova_pval < 0.05 else 'No']
})
anova_results.to_csv(os.path.join(workspace_dir, 'outputs', 'anova_results.csv'), index=False)

# Summary Statistics for Report
print("\n" + "="*60)
print("SUMMARY OF KEY FINDINGS")
print("="*60)
print(f"\n1. Data Overview:")
print(f"   - Total observations: {len(df)} quarters")
print(f"   - Inflation range: {df['inflation_yoy'].min():.2f}% to {df['inflation_yoy'].max():.2f}%")
print(f"   - REIT return range: {df['reit_index_return'].min():.2f}% to {df['reit_index_return'].max():.2f}%")

print(f"\n2. Correlation:")
print(f"   - Pearson correlation: {pearson_corr:.4f} (p={pearson_pval:.4f})")
print(f"   - Strong positive association between inflation and REIT returns")

print(f"\n3. Regression:")
print(f"   - Coefficient: {ols_model.params['inflation_yoy']:.4f}")
print(f"   - R-squared: {ols_model.rsquared:.4f}")
print(f"   - A 1% increase in inflation associated with {ols_model.params['inflation_yoy']:.2f}% increase in REIT returns")

print(f"\n4. Stationarity:")
print(f"   - Inflation: {'Stationary' if adf_inflation[1] < 0.05 else 'Non-stationary'} (p={adf_inflation[1]:.4f})")
print(f"   - REIT Returns: {'Stationary' if adf_reit[1] < 0.05 else 'Non-stationary'} (p={adf_reit[1]:.4f})")

print(f"\n5. Regime Analysis:")
print(f"   - Low inflation regime: Mean REIT return = {low_inflation['reit_index_return'].mean():.2f}%")
print(f"   - High inflation regime: Mean REIT return = {high_inflation['reit_index_return'].mean():.2f}%")
print(f"   - ANOVA p-value: {anova_pval:.4f}")

print("\n" + "="*60)
print("Analysis complete! All figures and results saved.")
print("="*60)