import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
from scipy import stats
import os

os.makedirs('outputs', exist_ok=True)

df = pd.read_csv('data/reit_macro_quarterly.csv')

# Get exact numbers
reit_cols = [c for c in df.columns if 'reit' in c.lower()]
infl_cols = [c for c in df.columns if 'infl' in c.lower()]
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

# Descriptive stats
desc = df[numeric_cols].describe()

# Correlations
corr_data = {}
for rc in reit_cols:
    for ic in infl_cols:
        valid = df[[rc, ic]].dropna()
        r_p, p_p = pearsonr(valid[rc], valid[ic])
        r_s, p_s = spearmanr(valid[rc], valid[ic])
        corr_data[f'{rc}_vs_{ic}'] = {'pearson_r': r_p, 'pearson_p': p_p, 'spearman_r': r_s, 'spearman_p': p_s}

# Regressions
reg_data = {}
for rc in reit_cols:
    for ic in infl_cols:
        valid = df[[rc, ic]].dropna()
        slope, intercept, r_value, p_value, std_err = stats.linregress(valid[ic], valid[rc])
        reg_data[f'{rc}_vs_{ic}'] = {'slope': slope, 'intercept': intercept, 'r2': r_value**2, 'p': p_value}

# Regime
if infl_cols:
    ic = infl_cols[0]
    median_infl = df[ic].median()
    df['regime'] = np.where(df[ic] > median_infl, 'High', 'Low')
    regime_data = {}
    for rc in reit_cols:
        high = df[df['regime'] == 'High'][rc].dropna()
        low = df[df['regime'] == 'Low'][rc].dropna()
        t, p = stats.ttest_ind(high, low)
        regime_data[rc] = {'high_mean': high.mean(), 'low_mean': low.mean(), 'diff': high.mean()-low.mean(), 't': t, 'p': p}

# Lagged correlations
rc = reit_cols[0]
ic = infl_cols[0]
lag_data = {}
for lag in range(-6, 7):
    if lag < 0:
        x = df[ic].values[:len(df)+lag]
        y = df[rc].values[-lag:]
    elif lag > 0:
        x = df[ic].values[lag:]
        y = df[rc].values[:len(df)-lag]
    else:
        x = df[ic].values
        y = df[rc].values
    
    valid_mask = ~(np.isnan(x) | np.isnan(y))
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    
    if len(x_valid) > 10:
        r, p = pearsonr(x_valid, y_valid)
        lag_data[lag] = {'r': r, 'p': p}

# Write all numbers to file
with open('outputs/exact_numbers.txt', 'w') as f:
    f.write('=== EXACT NUMBERS FROM DATA ===\n\n')
    
    f.write('DESCRIPTIVE STATS:\n')
    for col in numeric_cols:
        f.write(f'  {col}: mean={desc[col]["mean"]:.4f}, std={desc[col]["std"]:.4f}, min={desc[col]["min"]:.4f}, median={desc[col]["50%"]:.4f}, max={desc[col]["max"]:.4f}\n')
    
    f.write('\nCORRELATIONS:\n')
    for key, val in corr_data.items():
        f.write(f'  {key}: Pearson r={val["pearson_r"]:.4f} p={val["pearson_p"]:.4f}, Spearman r={val["spearman_r"]:.4f} p={val["spearman_p"]:.4f}\n')
    
    f.write('\nREGRESSIONS:\n')
    for key, val in reg_data.items():
        f.write(f'  {key}: slope={val["slope"]:.4f}, intercept={val["intercept"]:.4f}, R2={val["r2"]:.4f}, p={val["p"]:.4f}\n')
    
    f.write(f'\nREGIME (median inflation={median_infl:.4f}):\n')
    for rc, val in regime_data.items():
        f.write(f'  {rc}: High={val["high_mean"]:.4f}, Low={val["low_mean"]:.4f}, diff={val["diff"]:.4f}, t={val["t"]:.4f}, p={val["p"]:.4f}\n')
    
    f.write('\nLAGGED CORRELATIONS:\n')
    for lag, val in lag_data.items():
        f.write(f'  lag={lag}: r={val["r"]:.4f}, p={val["p"]:.4f}\n')
    
    f.write('\nCORRELATION MATRIX:\n')
    f.write(df[numeric_cols].corr().to_string())

print('Done!')
