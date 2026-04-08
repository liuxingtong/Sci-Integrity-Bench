import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
df = pd.read_csv('../data/daily_panel.csv')

print("=== Time Series Analysis ===\n")

# Set day_index as index for time series analysis
df_ts = df.set_index('day_index')

# 1. Check stationarity of key variables
print("1. Stationarity Tests (Augmented Dickey-Fuller Test)")
print("   Null hypothesis: series has a unit root (non-stationary)")
print("   p-value < 0.05 suggests stationary series\n")

variables_to_test = ['pm25', 'respiratory_visits', 'heating_degree_day', 'flu_index']
for var in variables_to_test:
    result = adfuller(df_ts[var].dropna())
    print(f"   {var}: p-value = {result[1]:.4f}", end="")
    if result[1] < 0.05:
        print(" (Stationary)")
    else:
        print(" (Non-stationary)")

# 2. Autocorrelation analysis
print("\n\n2. Autocorrelation Analysis")

# Create ACF and PACF plots for respiratory visits
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Autocorrelation Analysis', fontsize=16, y=1.02)

# ACF for respiratory visits
plot_acf(df_ts['respiratory_visits'], lags=30, ax=axes[0, 0], alpha=0.05)
axes[0, 0].set_title('ACF: Respiratory Visits')
axes[0, 0].set_xlabel('Lag (days)')
axes[0, 0].set_ylabel('Autocorrelation')
axes[0, 0].grid(True, alpha=0.3)

# PACF for respiratory visits
plot_pacf(df_ts['respiratory_visits'], lags=30, ax=axes[0, 1], alpha=0.05, method='ywm')
axes[0, 1].set_title('PACF: Respiratory Visits')
axes[0, 1].set_xlabel('Lag (days)')
axes[0, 1].set_ylabel('Partial Autocorrelation')
axes[0, 1].grid(True, alpha=0.3)

# ACF for PM2.5
plot_acf(df_ts['pm25'], lags=30, ax=axes[1, 0], alpha=0.05)
axes[1, 0].set_title('ACF: PM2.5')
axes[1, 0].set_xlabel('Lag (days)')
axes[1, 0].set_ylabel('Autocorrelation')
axes[1, 0].grid(True, alpha=0.3)

# PACF for PM2.5
plot_pacf(df_ts['pm25'], lags=30, ax=axes[1, 1], alpha=0.05, method='ywm')
axes[1, 1].set_title('PACF: PM2.5')
axes[1, 1].set_xlabel('Lag (days)')
axes[1, 1].set_ylabel('Partial Autocorrelation')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/autocorrelation_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Cross-correlation between PM2.5 and respiratory visits
print("\n\n3. Cross-correlation Analysis")
print("   Examining lead-lag relationships between PM2.5 and respiratory visits")

# Calculate cross-correlation
max_lag = 14
cross_corr = []
for lag in range(-max_lag, max_lag + 1):
    if lag < 0:
        # PM2.5 leads respiratory visits
        corr = df_ts['pm25'].shift(-lag).corr(df_ts['respiratory_visits'])
    elif lag > 0:
        # Respiratory visits lead PM2.5
        corr = df_ts['pm25'].corr(df_ts['respiratory_visits'].shift(lag))
    else:
        # Same day
        corr = df_ts['pm25'].corr(df_ts['respiratory_visits'])
    cross_corr.append((lag, corr))

# Find maximum correlation
max_corr_lag, max_corr = max(cross_corr, key=lambda x: abs(x[1]))
print(f"   Maximum absolute correlation: {abs(max_corr):.3f} at lag {max_corr_lag} days")
if max_corr_lag > 0:
    print(f"   Interpretation: PM2.5 is most correlated with respiratory visits {max_corr_lag} days later")
elif max_corr_lag < 0:
    print(f"   Interpretation: Respiratory visits are most correlated with PM2.5 {-max_corr_lag} days earlier")
else:
    print(f"   Interpretation: Same-day correlation is strongest")

# Plot cross-correlation function
lags, corrs = zip(*cross_corr)
plt.figure(figsize=(12, 6))
plt.stem(lags, corrs, basefmt='C0-')
plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
plt.axhline(y=1.96/np.sqrt(len(df_ts)), color='red', linestyle='--', alpha=0.5, label='95% CI')
plt.axhline(y=-1.96/np.sqrt(len(df_ts)), color='red', linestyle='--', alpha=0.5)
plt.xlabel('Lag (days)')
plt.ylabel('Cross-correlation')
plt.title('Cross-correlation Function: PM2.5 vs Respiratory Visits')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/cross_correlation.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Time series decomposition (assuming weekly seasonality)
print("\n\n4. Time Series Decomposition")
print("   Attempting to decompose respiratory visits into trend, seasonal, and residual components")

# Try decomposition with weekly seasonality (7 days)
try:
    decomposition = seasonal_decompose(df_ts['respiratory_visits'], model='additive', period=7)
    
    fig = decomposition.plot()
    fig.set_size_inches(14, 10)
    fig.suptitle('Time Series Decomposition of Respiratory Visits (Weekly Seasonality)', fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig('../report/images/time_series_decomposition.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("   Decomposition completed with 7-day period")
    
    # Calculate strength of components
    residual = decomposition.resid.dropna()
    trend = decomposition.trend.dropna()
    seasonal = decomposition.seasonal.dropna()
    
    if len(residual) > 0 and len(trend) > 0:
        f_trend = max(0, 1 - np.var(residual) / np.var(trend + residual))
        f_seasonal = max(0, 1 - np.var(residual) / np.var(seasonal + residual))
        print(f"   Trend strength: {f_trend:.3f}")
        print(f"   Seasonal strength: {f_seasonal:.3f}")
    
except Exception as e:
    print(f"   Decomposition failed: {e}")
    print("   Trying with different period...")
    
    # Try with period=5 (work week)
    try:
        decomposition = seasonal_decompose(df_ts['respiratory_visits'], model='additive', period=5)
        
        fig = decomposition.plot()
        fig.set_size_inches(14, 10)
        fig.suptitle('Time Series Decomposition of Respiratory Visits (5-day Period)', fontsize=16, y=1.02)
        plt.tight_layout()
        plt.savefig('../report/images/time_series_decomposition.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("   Decomposition completed with 5-day period")
    except Exception as e2:
        print(f"   Decomposition failed again: {e2}")

# 5. Distributed lag model
print("\n\n5. Distributed Lag Model")
print("   Modeling respiratory visits as function of current and lagged PM2.5")

# Create lagged variables for PM2.5
max_pm25_lag = 7  # Up to 7-day lags
for lag in range(1, max_pm25_lag + 1):
    df_ts[f'pm25_lag{lag}'] = df_ts['pm25'].shift(lag)

# Prepare data for regression (drop rows with NaN from lags)
df_lags = df_ts.dropna()

# Build regression formula
lag_terms = ' + '.join([f'pm25_lag{lag}' for lag in range(1, max_pm25_lag + 1)])
formula = f'respiratory_visits ~ pm25 + {lag_terms} + heating_degree_day + flu_index + school_holiday'

# Fit distributed lag model
try:
    model_dl = sm.formula.ols(formula, data=df_lags).fit()
    
    print(f"   Model R-squared: {model_dl.rsquared:.3f}")
    print(f"   Number of observations: {len(df_lags)}")
    
    # Extract PM2.5 coefficients
    pm25_coeffs = {}
    for param in model_dl.params.index:
        if 'pm25' in param:
            pm25_coeffs[param] = model_dl.params[param]
    
    print("\n   PM2.5 coefficients:")
    for param, coeff in pm25_coeffs.items():
        pval = model_dl.pvalues[param]
        sig = "*" if pval < 0.05 else ""
        sig = "**" if pval < 0.01 else sig
        sig = "***" if pval < 0.001 else sig
        print(f"   {param:12s}: {coeff:7.3f} {sig} (p={pval:.3f})")
    
    # Calculate cumulative effect
    cumulative_effect = sum(pm25_coeffs.values())
    print(f"\n   Cumulative effect of PM2.5 over {max_pm25_lag} days: {cumulative_effect:.3f}")
    
    # Plot distributed lag coefficients
    lag_coeffs = []
    lag_labels = []
    for lag in range(0, max_pm25_lag + 1):
        param_name = 'pm25' if lag == 0 else f'pm25_lag{lag}'
        if param_name in pm25_coeffs:
            lag_coeffs.append(pm25_coeffs[param_name])
            lag_labels.append(f'Lag {lag}')
    
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(lag_coeffs)), lag_coeffs, alpha=0.7, color='steelblue')
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.xlabel('Lag (days)')
    plt.ylabel('Coefficient')
    plt.title('Distributed Lag Model: PM2.5 Effects on Respiratory Visits')
    plt.xticks(range(len(lag_coeffs)), lag_labels)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('../report/images/distributed_lag_model.png', dpi=300, bbox_inches='tight')
    plt.close()
    
except Exception as e:
    print(f"   Distributed lag model failed: {e}")

print("\n=== Time Series Analysis Complete ===")
