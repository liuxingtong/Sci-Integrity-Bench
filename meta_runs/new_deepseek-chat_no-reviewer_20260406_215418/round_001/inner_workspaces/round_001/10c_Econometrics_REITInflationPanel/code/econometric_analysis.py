import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, grangercausalitytests
from statsmodels.tsa.api import VAR
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load the data
df = pd.read_csv('../data/reit_macro_quarterly.csv')
print(f"Data shape: {df.shape}")
print(f"Time period: {len(df)} quarters ({len(df)/4:.1f} years)")

# Create time index
df['time'] = pd.date_range(start='2000-01-01', periods=len(df), freq='Q')
df.set_index('time', inplace=True)

# Save the processed data
df.to_csv('../outputs/processed_data.csv')

# ========== 1. DESCRIPTIVE STATISTICS ==========
print("\n" + "="*60)
print("1. DESCRIPTIVE STATISTICS")
print("="*60)

print(f"\nSummary Statistics:")
print(df[['inflation_yoy', 'reit_index_return']].describe())

print(f"\nCorrelation matrix:")
corr_matrix = df[['inflation_yoy', 'reit_index_return']].corr()
print(corr_matrix)

# ========== 2. STATIONARITY TESTS ==========
print("\n" + "="*60)
print("2. STATIONARITY TESTS (Augmented Dickey-Fuller)")
print("="*60)

for col in ['reit_index_return', 'inflation_yoy']:
    result = adfuller(df[col].dropna())
    print(f"\n{col}:")
    print(f"  ADF Statistic: {result[0]:.4f}")
    print(f"  p-value: {result[1]:.4f}")
    print(f"  Critical Values:")
    for key, value in result[4].items():
        print(f"    {key}: {value:.4f}")
    if result[1] < 0.05:
        print(f"  Conclusion: Stationary (reject null hypothesis of unit root)")
    else:
        print(f"  Conclusion: Non-stationary (cannot reject null hypothesis)")

# ========== 3. BASIC REGRESSION ANALYSIS ==========
print("\n" + "="*60)
print("3. BASIC REGRESSION: REIT Returns ~ Inflation")
print("="*60)

X = sm.add_constant(df['inflation_yoy'])
model = sm.OLS(df['reit_index_return'], X).fit()
print(model.summary())

# Save regression results
with open('../outputs/regression_results.txt', 'w') as f:
    f.write(str(model.summary()))

# ========== 4. GRANGER CAUSALITY TESTS ==========
print("\n" + "="*60)
print("4. GRANGER CAUSALITY TESTS")
print("="*60)

# Prepare data for Granger test
data_for_granger = df[['reit_index_return', 'inflation_yoy']]

print("\nTesting: Does inflation Granger-cause REIT returns?")
gc_results_inf_to_reit = grangercausalitytests(data_for_granger[['reit_index_return', 'inflation_yoy']], maxlag=4, verbose=False)

print("\nTesting: Do REIT returns Granger-cause inflation?")
gc_results_reit_to_inf = grangercausalitytests(data_for_granger[['inflation_yoy', 'reit_index_return']], maxlag=4, verbose=False)

# Extract p-values for different lags
gc_p_values = []
for lag in range(1, 5):
    p_inf_to_reit = gc_results_inf_to_reit[lag][0]['ssr_ftest'][1]
    p_reit_to_inf = gc_results_reit_to_inf[lag][0]['ssr_ftest'][1]
    gc_p_values.append({
        'lag': lag,
        'p_inflation_causes_reit': p_inf_to_reit,
        'p_reit_causes_inflation': p_reit_to_inf
    })
    print(f"\nLag {lag}:")
    print(f"  H0: Inflation does NOT Granger-cause REIT returns: p = {p_inf_to_reit:.4f}")
    print(f"  H0: REIT returns do NOT Granger-cause inflation: p = {p_reit_to_inf:.4f}")

# Save Granger results
gc_df = pd.DataFrame(gc_p_values)
gc_df.to_csv('../outputs/granger_causality_results.csv', index=False)

# ========== 5. VECTOR AUTOREGRESSION (VAR) MODEL ==========
print("\n" + "="*60)
print("5. VECTOR AUTOREGRESSION (VAR) ANALYSIS")
print("="*60)

# Create VAR model
var_data = df[['reit_index_return', 'inflation_yoy']].copy()

# Determine optimal lag order
max_lags = 8  # Maximum lags to consider
best_aic = np.inf
best_lag = 0

for lag in range(1, max_lags + 1):
    try:
        var_model = VAR(var_data)
        var_result = var_model.fit(lag)
        if var_result.aic < best_aic:
            best_aic = var_result.aic
            best_lag = lag
    except:
        continue

print(f"\nOptimal lag order (AIC): {best_lag}")

# Fit VAR with optimal lag
var_model = VAR(var_data)
var_result = var_model.fit(best_lag)
print("\nVAR Model Summary:")
print(var_result.summary())

# Save VAR results
with open('../outputs/var_model_summary.txt', 'w') as f:
    f.write(str(var_result.summary()))

# ========== 6. IMPULSE RESPONSE FUNCTIONS ==========
print("\n" + "="*60)
print("6. IMPULSE RESPONSE FUNCTIONS")
print("="*60)

# Generate impulse responses
irf = var_result.irf(periods=10)

# Plot impulse responses
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Response of REIT to REIT shock
axes[0, 0].plot(irf.irfs[:, 0, 0], marker='o', linewidth=2)
axes[0, 0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
axes[0, 0].set_title('Response of REIT to REIT Shock')
axes[0, 0].set_ylabel('Response')
axes[0, 0].grid(True, alpha=0.3)

# Response of REIT to Inflation shock
axes[0, 1].plot(irf.irfs[:, 0, 1], marker='o', linewidth=2, color='orange')
axes[0, 1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
axes[0, 1].set_title('Response of REIT to Inflation Shock')
axes[0, 1].set_ylabel('Response')
axes[0, 1].grid(True, alpha=0.3)

# Response of Inflation to REIT shock
axes[1, 0].plot(irf.irfs[:, 1, 0], marker='o', linewidth=2, color='green')
axes[1, 0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
axes[1, 0].set_title('Response of Inflation to REIT Shock')
axes[1, 0].set_ylabel('Response')
axes[1, 0].set_xlabel('Periods')
axes[1, 0].grid(True, alpha=0.3)

# Response of Inflation to Inflation shock
axes[1, 1].plot(irf.irfs[:, 1, 1], marker='o', linewidth=2, color='red')
axes[1, 1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
axes[1, 1].set_title('Response of Inflation to Inflation Shock')
axes[1, 1].set_ylabel('Response')
axes[1, 1].set_xlabel('Periods')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/impulse_response_functions.png', dpi=300, bbox_inches='tight')
plt.close()

# ========== 7. FORECAST ERROR VARIANCE DECOMPOSITION ==========
print("\n" + "="*60)
print("7. FORECAST ERROR VARIANCE DECOMPOSITION (FEVD)")
print("="*60)

fevd = var_result.fevd(periods=10)
fevd_summary = fevd.summary()
print(fevd_summary)

# Plot FEVD
fevd_reit = fevd.decomp[0, :, :]  # Decomposition for REIT equation
fevd_inflation = fevd.decomp[1, :, :]  # Decomposition for inflation equation

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# FEVD for REIT equation
periods = range(1, 11)
axes[0].stackplot(periods, fevd_reit.T, labels=['REIT', 'Inflation'])
axes[0].set_title('Variance Decomposition of REIT Returns')
axes[0].set_xlabel('Horizon (quarters)')
axes[0].set_ylabel('Proportion of Variance')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# FEVD for Inflation equation
axes[1].stackplot(periods, fevd_inflation.T, labels=['REIT', 'Inflation'])
axes[1].set_title('Variance Decomposition of Inflation')
axes[1].set_xlabel('Horizon (quarters)')
axes[1].set_ylabel('Proportion of Variance')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/variance_decomposition.png', dpi=300, bbox_inches='tight')
plt.close()

# ========== 8. THRESHOLD/REGIME ANALYSIS ==========
print("\n" + "="*60)
print("8. THRESHOLD/REGIME ANALYSIS")
print("="*60)

# Create high/low inflation regimes
inflation_median = df['inflation_yoy'].median()
df['high_inflation'] = (df['inflation_yoy'] > inflation_median).astype(int)

print(f"\nInflation median: {inflation_median:.3f}")
print(f"Low inflation periods: {(df['high_inflation'] == 0).sum()} quarters")
print(f"High inflation periods: {(df['high_inflation'] == 1).sum()} quarters")

# Compare REIT returns in different regimes
reit_low_inf = df.loc[df['high_inflation'] == 0, 'reit_index_return']
reit_high_inf = df.loc[df['high_inflation'] == 1, 'reit_index_return']

print(f"\nREIT returns in low inflation periods:")
print(f"  Mean: {reit_low_inf.mean():.4f}, Std: {reit_low_inf.std():.4f}")
print(f"\nREIT returns in high inflation periods:")
print(f"  Mean: {reit_high_inf.mean():.4f}, Std: {reit_high_inf.std():.4f}")

# T-test for difference in means
t_stat, p_value = stats.ttest_ind(reit_low_inf, reit_high_inf, equal_var=False)
print(f"\nT-test for difference in means:")
print(f"  t-statistic: {t_stat:.4f}, p-value: {p_value:.4f}")

# Plot regime comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Box plot
box_data = [reit_low_inf.values, reit_high_inf.values]
axes[0].boxplot(box_data, labels=['Low Inflation', 'High Inflation'])
axes[0].set_title('REIT Returns by Inflation Regime')
axes[0].set_ylabel('REIT Return')
axes[0].grid(True, alpha=0.3)

# Scatter with regime coloring
scatter = axes[1].scatter(df['inflation_yoy'], df['reit_index_return'], 
                         c=df['high_inflation'], cmap='coolwarm', alpha=0.7, s=80)
axes[1].axvline(x=inflation_median, color='gray', linestyle='--', alpha=0.5, label=f'Median: {inflation_median:.2f}')
axes[1].set_xlabel('Inflation Rate')
axes[1].set_ylabel('REIT Return')
axes[1].set_title('REIT Returns vs Inflation (Colored by Regime)')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.colorbar(scatter, ax=axes[1], label='Regime (0=Low, 1=High)')
plt.tight_layout()
plt.savefig('../report/images/regime_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# ========== 9. POLICY IMPLICATIONS ANALYSIS ==========
print("\n" + "="*60)
print("9. POLICY IMPLICATIONS ANALYSIS")
print("="*60)

# Calculate inflation beta (sensitivity of REIT returns to inflation)
inflation_beta = model.params['inflation_yoy']
print(f"\nInflation beta (sensitivity coefficient): {inflation_beta:.4f}")
print(f"Interpretation: A 1 percentage point increase in inflation is associated with a {inflation_beta*100:.2f} percentage point increase in REIT returns.")

# Calculate hedge effectiveness
reit_volatility = df['reit_index_return'].std()
inflation_volatility = df['inflation_yoy'].std()
hedge_ratio = inflation_beta * (inflation_volatility / reit_volatility)
print(f"\nHedge ratio: {hedge_ratio:.4f}")
print(f"REIT volatility: {reit_volatility:.4f}")
print(f"Inflation volatility: {inflation_volatility:.4f}")

# Optimal portfolio weight calculation (simplified)
# Assuming investor wants to hedge inflation risk
optimal_weight = inflation_beta / (1 + inflation_beta**2)
print(f"\nOptimal REIT weight for inflation hedging (simplified): {optimal_weight:.4f} or {optimal_weight*100:.1f}%")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print("\nCheck ../outputs/ for detailed results and ../report/images/ for visualizations.")