import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import ttest_ind
import os

os.makedirs('outputs', exist_ok=True)

df = pd.read_csv('data/field_year_panel.csv')

yield_col = 'yield_kg_ha'
irrig_col = 'irrigation_mm'
fert_col = 'fertilizer_kg_ha'
rain_col = 'rainfall_mm'
quota_col = 'quota_enforced'
year_col = 'year'
field_col = 'field_id'

results = {}

# Basic stats
results['n_obs'] = len(df)
results['n_fields'] = df[field_col].nunique()
results['year_min'] = df[year_col].min()
results['year_max'] = df[year_col].max()
results['yield_mean'] = df[yield_col].mean()
results['yield_std'] = df[yield_col].std()
results['yield_min'] = df[yield_col].min()
results['yield_max'] = df[yield_col].max()
results['irrig_mean'] = df[irrig_col].mean()
results['irrig_std'] = df[irrig_col].std()
results['fert_mean'] = df[fert_col].mean()
results['fert_std'] = df[fert_col].std()
results['rain_mean'] = df[rain_col].mean()
results['rain_std'] = df[rain_col].std()
results['quota_rate'] = df[quota_col].mean()

# Correlations
results['r_irrig_yield'] = df[[irrig_col, yield_col]].corr().iloc[0,1]
results['r_rain_yield'] = df[[rain_col, yield_col]].corr().iloc[0,1]
results['r_fert_yield'] = df[[fert_col, yield_col]].corr().iloc[0,1]
results['r_rain_irrig'] = df[[rain_col, irrig_col]].corr().iloc[0,1]

df['total_water'] = df[rain_col] + df[irrig_col]
results['r_total_water_yield'] = df[['total_water', yield_col]].corr().iloc[0,1]

# Bivariate regressions
for x_col, key in [(irrig_col, 'irrig'), (rain_col, 'rain'), (fert_col, 'fert')]:
    valid = df[[x_col, yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[x_col], valid[yield_col])
    results[f'{key}_slope'] = slope
    results[f'{key}_r'] = r_value
    results[f'{key}_p'] = p_value

# Quota effects
quota_vals = sorted(df[quota_col].unique())
g0 = df[df[quota_col] == quota_vals[0]][yield_col].dropna()
g1 = df[df[quota_col] == quota_vals[1]][yield_col].dropna()
t_stat, p_val = ttest_ind(g0, g1)
results['quota_yield_g0_mean'] = g0.mean()
results['quota_yield_g1_mean'] = g1.mean()
results['quota_yield_diff'] = g1.mean() - g0.mean()
results['quota_yield_t'] = t_stat
results['quota_yield_p'] = p_val
results['quota_yield_n0'] = len(g0)
results['quota_yield_n1'] = len(g1)

g0_i = df[df[quota_col] == quota_vals[0]][irrig_col].dropna()
g1_i = df[df[quota_col] == quota_vals[1]][irrig_col].dropna()
t_stat_i, p_val_i = ttest_ind(g0_i, g1_i)
results['quota_irrig_g0_mean'] = g0_i.mean()
results['quota_irrig_g1_mean'] = g1_i.mean()
results['quota_irrig_diff'] = g1_i.mean() - g0_i.mean()
results['quota_irrig_t'] = t_stat_i
results['quota_irrig_p'] = p_val_i

# Multiple regression
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    
    X_cols = [irrig_col, rain_col, fert_col, quota_col]
    valid = df[X_cols + [yield_col]].dropna()
    
    scaler = StandardScaler()
    X = scaler.fit_transform(valid[X_cols])
    y = valid[yield_col].values
    
    reg = LinearRegression()
    reg.fit(X, y)
    
    results['r2'] = reg.score(X, y)
    for col, coef in zip(X_cols, reg.coef_):
        results[f'beta_{col}'] = coef
except Exception as e:
    print(f'Regression error: {e}')

# Save results
with open('outputs/key_stats.txt', 'w') as f:
    f.write('=== KEY STATISTICAL RESULTS ===\n\n')
    for key, val in results.items():
        if isinstance(val, float):
            f.write(f'{key}: {val:.4f}\n')
        else:
            f.write(f'{key}: {val}\n')

print('Key stats saved.')
for key, val in results.items():
    if isinstance(val, float):
        print(f'{key}: {val:.4f}')
    else:
        print(f'{key}: {val}')
