import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.sandbox.regression.gmm import IV2SLS

# Load data
df = pd.read_csv('data/field_year_panel.csv')

# 1. Summary statistics
summary = df.describe()
summary.to_csv('outputs/summary_statistics.csv')

# 2. Correlation matrix
corr = df.corr()
corr.to_csv('outputs/correlation_matrix.csv')

plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f')
plt.title('Correlation Matrix')
plt.tight_layout()
plt.savefig('report/images/correlation_matrix.png')
plt.close()

# 3. Scatter plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

sns.scatterplot(data=df, x='groundwater_quota_enforcement', y='irrigation_m3', ax=axes[0, 0])
axes[0, 0].set_title('Irrigation vs. Quota Enforcement')

sns.scatterplot(data=df, x='irrigation_m3', y='yield_t_ha', ax=axes[0, 1])
axes[0, 1].set_title('Yield vs. Irrigation')

sns.scatterplot(data=df, x='rainfall_mm', y='irrigation_m3', ax=axes[1, 0])
axes[1, 0].set_title('Irrigation vs. Rainfall')

sns.scatterplot(data=df, x='fertilizer_kg', y='yield_t_ha', ax=axes[1, 1])
axes[1, 1].set_title('Yield vs. Fertilizer')

plt.tight_layout()
plt.savefig('report/images/scatter_plots.png')
plt.close()

# 4. OLS Regressions
# Model 1: Effect of enforcement on irrigation
X1 = df[['groundwater_quota_enforcement', 'rainfall_mm']]
X1 = sm.add_constant(X1)
y1 = df['irrigation_m3']
model1 = sm.OLS(y1, X1).fit()
with open('outputs/regression_irrigation.txt', 'w') as f:
    f.write(model1.summary().as_text())

# Model 2: Effect of irrigation on yield (OLS)
X2 = df[['irrigation_m3', 'fertilizer_kg', 'rainfall_mm']]
X2 = sm.add_constant(X2)
y2 = df['yield_t_ha']
model2 = sm.OLS(y2, X2).fit()
with open('outputs/regression_yield_ols.txt', 'w') as f:
    f.write(model2.summary().as_text())

# Model 3: Reduced form (Effect of enforcement on yield)
X3 = df[['groundwater_quota_enforcement', 'fertilizer_kg', 'rainfall_mm']]
X3 = sm.add_constant(X3)
y3 = df['yield_t_ha']
model3 = sm.OLS(y3, X3).fit()
with open('outputs/regression_yield_reduced.txt', 'w') as f:
    f.write(model3.summary().as_text())

# Model 4: IV Regression (Enforcement as IV for Irrigation)
# IV2SLS(endog, exog, instrument)
# endog: yield_t_ha
# exog: constant, fertilizer_kg, rainfall_mm, irrigation_m3
# instrument: constant, fertilizer_kg, rainfall_mm, groundwater_quota_enforcement

exog_iv = sm.add_constant(df[['fertilizer_kg', 'rainfall_mm', 'irrigation_m3']])
instruments = sm.add_constant(df[['fertilizer_kg', 'rainfall_mm', 'groundwater_quota_enforcement']])
model4 = IV2SLS(df['yield_t_ha'], exog_iv, instrument=instruments).fit()
with open('outputs/regression_yield_iv.txt', 'w') as f:
    f.write(model4.summary().as_text())

print("Analysis complete.")
