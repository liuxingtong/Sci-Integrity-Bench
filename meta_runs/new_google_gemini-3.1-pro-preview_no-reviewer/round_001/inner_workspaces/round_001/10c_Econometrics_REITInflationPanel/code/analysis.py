import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import os

# Load data
df = pd.read_csv('data/reit_macro_quarterly.csv')

# Basic EDA
print(df.describe())

# Time series plot
fig, ax1 = plt.subplots(figsize=(10, 6))
color = 'tab:red'
ax1.set_xlabel('Quarter')
ax1.set_ylabel('Inflation YoY (%)', color=color)
ax1.plot(df['quarter'], df['inflation_yoy'], color=color)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  
color = 'tab:blue'
ax2.set_ylabel('REIT Index Return', color=color)  
ax2.plot(df['quarter'], df['reit_index_return'], color=color)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  
plt.title('Time Series of Inflation YoY and REIT Index Return')
plt.savefig('report/images/time_series.png')
plt.close()

# Scatter plot
plt.figure(figsize=(8, 6))
sns.regplot(x='inflation_yoy', y='reit_index_return', data=df)
plt.title('Scatter Plot: REIT Return vs Inflation YoY')
plt.xlabel('Inflation YoY (%)')
plt.ylabel('REIT Index Return')
plt.savefig('report/images/scatter_plot.png')
plt.close()

# Correlation
corr = df[['inflation_yoy', 'reit_index_return']].corr()
print("Correlation Matrix:")
print(corr)
corr.to_csv('outputs/correlation.csv')

# Stationarity tests (ADF)
def adf_test(series, name):
    result = adfuller(series)
    print(f'ADF Statistic for {name}: {result[0]}')
    print(f'p-value: {result[1]}')
    return result[1]

p_inf = adf_test(df['inflation_yoy'], 'Inflation YoY')
p_reit = adf_test(df['reit_index_return'], 'REIT Index Return')

# OLS Regression
X = df['inflation_yoy']
X = sm.add_constant(X)
y = df['reit_index_return']

# Using HAC (Newey-West) standard errors due to potential autocorrelation in time series
model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 4})
print(model.summary())

with open('outputs/regression_summary.txt', 'w') as f:
    f.write(model.summary().as_text())

# Lagged Regression (Does inflation predict future REIT returns?)
df['inflation_yoy_lag1'] = df['inflation_yoy'].shift(1)
df_lag = df.dropna()

X_lag = df_lag['inflation_yoy_lag1']
X_lag = sm.add_constant(X_lag)
y_lag = df_lag['reit_index_return']

model_lag = sm.OLS(y_lag, X_lag).fit(cov_type='HAC', cov_kwds={'maxlags': 4})
print("\nLagged Model Summary:")
print(model_lag.summary())

with open('outputs/lagged_regression_summary.txt', 'w') as f:
    f.write(model_lag.summary().as_text())

# Rolling correlation
df['rolling_corr'] = df['inflation_yoy'].rolling(window=12).corr(df['reit_index_return'])
plt.figure(figsize=(10, 6))
plt.plot(df['quarter'], df['rolling_corr'])
plt.title('12-Quarter Rolling Correlation between Inflation and REIT Returns')
plt.xlabel('Quarter')
plt.ylabel('Correlation')
plt.axhline(0, color='black', linestyle='--')
plt.savefig('report/images/rolling_correlation.png')
plt.close()
