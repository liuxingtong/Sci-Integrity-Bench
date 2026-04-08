import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

df = pd.read_csv('data/reit_macro_quarterly.csv')
print("Data shape:", df.shape)
print(df.head())
print(df.describe())

df['quarter'] = range(len(df))

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0, 0].plot(df['quarter'], df['inflation_yoy'], 'b-o', linewidth=2, markersize=4)
axes[0, 0].set_xlabel('Quarter')
axes[0, 0].set_ylabel('Inflation YoY (%)')
axes[0, 0].set_title('Inflation Rate Over Time')
axes[0, 0].axhline(y=df['inflation_yoy'].mean(), color='r', linestyle='--', label=f'Mean: {df["inflation_yoy"].mean():.2f}%')
axes[0, 0].legend()

axes[0, 1].plot(df['quarter'], df['reit_index_return'], 'g-o', linewidth=2, markersize=4)
axes[0, 1].set_xlabel('Quarter')
axes[0, 1].set_ylabel('REIT Index Return')
axes[0, 1].set_title('REIT Index Returns Over Time')
axes[0, 1].axhline(y=df['reit_index_return'].mean(), color='r', linestyle='--', label=f'Mean: {df["reit_index_return"].mean():.4f}')
axes[0, 1].legend()

axes[1, 0].scatter(df['inflation_yoy'], df['reit_index_return'], s=80, alpha=0.7, edgecolors='black')
z = np.polyfit(df['inflation_yoy'], df['reit_index_return'], 1)
p = np.poly1d(z)
axes[1, 0].plot(df['inflation_yoy'], p(df['inflation_yoy']), "r--", linewidth=2)
axes[1, 0].set_xlabel('Inflation YoY (%)')
axes[1, 0].set_ylabel('REIT Index Return')
axes[1, 0].set_title('REIT Returns vs Inflation')

corr_matrix = df[['inflation_yoy', 'reit_index_return']].corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=axes[1, 1], fmt='.3f', square=True, annot_kws={'size': 14})
axes[1, 1].set_title('Correlation Matrix')

plt.tight_layout()
plt.savefig('report/images/data_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure saved: report/images/data_overview.png")

corr, p_value = stats.pearsonr(df['inflation_yoy'], df['reit_index_return'])
spearman_corr, spearman_p = stats.spearmanr(df['inflation_yoy'], df['reit_index_return'])
print(f"Pearson correlation: {corr:.4f} (p-value: {p_value:.4f})")
print(f"Spearman correlation: {spearman_corr:.4f} (p-value: {spearman_p:.4f})")

from scipy import stats as scipy_stats
X = df['inflation_yoy'].values
y = df['reit_index_return'].values
X_with_const = np.column_stack([np.ones(len(X)), X])
beta_hat = np.linalg.inv(X_with_const.T @ X_with_const) @ X_with_const.T @ y
alpha_hat, beta_hat_infl = beta_hat[0], beta_hat[1]
y_pred = alpha_hat + beta_hat_infl * X
residuals = y - y_pred
n = len(y)
RSS = np.sum(residuals**2)
sigma2_hat = RSS / (n - 2)
var_beta = sigma2_hat * np.linalg.inv(X_with_const.T @ X_with_const)
se_alpha = np.sqrt(var_beta[0, 0])
se_beta = np.sqrt(var_beta[1, 1])
t_alpha = alpha_hat / se_alpha
t_beta = beta_hat_infl / se_beta
p_alpha = 2 * (1 - scipy_stats.t.cdf(np.abs(t_alpha), n - 2))
p_beta = 2 * (1 - scipy_stats.t.cdf(np.abs(t_beta), n - 2))
TSS = np.sum((y - y.mean())**2)
R2 = 1 - RSS / TSS
print(f"REIT_return = {alpha_hat:.6f} + {beta_hat_infl:.6f} * inflation")
print(f"R-squared: {R2:.4f}")

regression_results = {'intercept': alpha_hat, 'intercept_se': se_alpha, 'inflation_coef': beta_hat_infl, 'inflation_se': se_beta, 'r_squared': R2, 'n_obs': n}
reg_df = pd.DataFrame(regression_results, index=['value'])
reg_df.to_csv('outputs/regression_results.csv')

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes[0, 0].scatter(y_pred, y, s=60, alpha=0.7, edgecolors='black')
axes[0, 0].plot([y.min(), y.max()], [y.min(), y.max()], 'r--', linewidth=2)
axes[0, 0].set_xlabel('Fitted Values')
axes[0, 0].set_ylabel('Actual Values')
axes[0, 0].set_title('Actual vs Fitted REIT Returns')
axes[0, 1].scatter(y_pred, residuals, s=60, alpha=0.7, edgecolors='black')
axes[0, 1].axhline(y=0, color='r', linestyle='--')
axes[0, 1].set_xlabel('Fitted Values')
axes[0, 1].set_ylabel('Residuals')
axes[0, 1].set_title('Residuals vs Fitted')
scipy_stats.probplot(residuals, dist="norm", plot=axes[1, 0])
axes[1, 0].set_title('Q-Q Plot of Residuals')
axes[1, 1].plot(df['quarter'], residuals, 'o-', linewidth=1.5, markersize=5)
axes[1, 1].axhline(y=0, color='r', linestyle='--')
axes[1, 1].set_xlabel('Quarter')
axes[1, 1].set_ylabel('Residuals')
axes[1, 1].set_title('Residuals Over Time')
plt.tight_layout()
plt.savefig('report/images/regression_diagnostics.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure saved: report/images/regression_diagnostics.png")

window = 8
rolling_corr = df['reit_index_return'].rolling(window=window).corr(df['inflation_yoy'])
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['quarter'], rolling_corr, 'b-o', linewidth=2, markersize=5)
ax.axhline(y=rolling_corr.mean(), color='r', linestyle='--', label=f'Mean: {rolling_corr.mean():.3f}')
ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
ax.set_xlabel('Quarter')
ax.set_ylabel('Rolling Correlation (8-quarter window)')
ax.set_title('Rolling Correlation: REIT Returns vs Inflation')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/rolling_correlation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure saved: report/images/rolling_correlation.png")

inflation_median = df['inflation_yoy'].median()
df['high_inflation'] = (df['inflation_yoy'] > inflation_median).astype(int)
print(f"Median inflation: {inflation_median:.3f}%")
low_inf_reit = df[df['high_inflation'] == 0]['reit_index_return']
high_inf_reit = df[df['high_inflation'] == 1]['reit_index_return']
print(f"Low Inflation Mean REIT: {low_inf_reit.mean():.4f}")
print(f"High Inflation Mean REIT: {high_inf_reit.mean():.4f}")
t_stat, t_pval = stats.ttest_ind(high_inf_reit, low_inf_reit)
print(f"T-test: t={t_stat:.4f}, p={t_pval:.4f}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].boxplot([low_inf_reit, high_inf_reit], labels=['Low Inflation', 'High Inflation'])
axes[0].set_ylabel('REIT Index Return')
axes[0].set_title('REIT Returns by Inflation Regime')
axes[0].grid(True, alpha=0.3)
axes[1].hist(low_inf_reit, alpha=0.6, bins=8, label=f'Low Inf (mean={low_inf_reit.mean():.3f})', color='blue')
axes[1].hist(high_inf_reit, alpha=0.6, bins=8, label=f'High Inf (mean={high_inf_reit.mean():.3f})', color='red')
axes[1].set_xlabel('REIT Index Return')
axes[1].set_ylabel('Frequency')
axes[1].set_title('Distribution of REIT Returns by Inflation Regime')
axes[1].legend()
axes[1].grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/inflation_regime_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure saved: report/images/inflation_regime_analysis.png")

summary_stats = pd.DataFrame({'Variable': ['Inflation YoY (%)', 'REIT Index Return'], 'Mean': [df['inflation_yoy'].mean(), df['reit_index_return'].mean()], 'Std': [df['inflation_yoy'].std(), df['reit_index_return'].std()], 'Min': [df['inflation_yoy'].min(), df['reit_index_return'].min()], 'Max': [df['inflation_yoy'].max(), df['reit_index_return'].max()], 'N': [len(df), len(df)]})
summary_stats.to_csv('outputs/summary_statistics.csv', index=False)
print("Analysis complete!")
