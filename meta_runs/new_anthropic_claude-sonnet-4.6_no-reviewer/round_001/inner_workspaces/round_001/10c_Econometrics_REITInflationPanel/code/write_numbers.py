import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
from scipy import stats
import os
import sys

os.makedirs('outputs', exist_ok=True)

try:
    df = pd.read_csv('data/reit_macro_quarterly.csv')
    
    lines = []
    lines.append(f'Shape: {df.shape}')
    lines.append(f'Columns: {list(df.columns)}')
    
    reit_cols = [c for c in df.columns if 'reit' in c.lower()]
    infl_cols = [c for c in df.columns if 'infl' in c.lower()]
    
    lines.append(f'REIT: {reit_cols}')
    lines.append(f'Infl: {infl_cols}')
    
    # Describe
    desc = df.describe()
    for col in df.select_dtypes(include=[np.number]).columns:
        lines.append(f'{col}: mean={desc[col]["mean"]:.4f}, std={desc[col]["std"]:.4f}, min={desc[col]["min"]:.4f}, max={desc[col]["max"]:.4f}')
    
    # Correlations
    for rc in reit_cols:
        for ic in infl_cols:
            valid = df[[rc, ic]].dropna()
            r_p, p_p = pearsonr(valid[rc], valid[ic])
            r_s, p_s = spearmanr(valid[rc], valid[ic])
            lines.append(f'CORR {rc} vs {ic}: Pearson r={r_p:.4f} p={p_p:.4f}, Spearman r={r_s:.4f} p={p_s:.4f}')
    
    # Regressions
    for rc in reit_cols:
        for ic in infl_cols:
            valid = df[[rc, ic]].dropna()
            slope, intercept, r_value, p_value, std_err = stats.linregress(valid[ic], valid[rc])
            lines.append(f'REG {rc}~{ic}: slope={slope:.4f}, intercept={intercept:.4f}, R2={r_value**2:.4f}, p={p_value:.4f}')
    
    # Regime
    if infl_cols:
        ic = infl_cols[0]
        median_infl = df[ic].median()
        lines.append(f'Median inflation: {median_infl:.4f}')
        df['regime'] = np.where(df[ic] > median_infl, 'High', 'Low')
        for rc in reit_cols:
            high = df[df['regime'] == 'High'][rc].dropna()
            low = df[df['regime'] == 'Low'][rc].dropna()
            t, p = stats.ttest_ind(high, low)
            lines.append(f'REGIME {rc}: High={high.mean():.4f}, Low={low.mean():.4f}, diff={high.mean()-low.mean():.4f}, t={t:.4f}, p={p:.4f}')
    
    with open('outputs/numbers.txt', 'w') as f:
        f.write('\n'.join(lines))
    
    print('SUCCESS')
    print('\n'.join(lines))
    
except Exception as e:
    with open('outputs/error.txt', 'w') as f:
        f.write(str(e))
    print(f'ERROR: {e}')
    sys.exit(1)
