import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr

df = pd.read_csv('data/reit_macro_quarterly.csv')

with open('outputs/actual_numbers.txt', 'w') as f:
    f.write('=== ACTUAL DATA NUMBERS ===\n\n')
    
    f.write('COLUMNS:\n')
    f.write(str(df.columns.tolist()) + '\n\n')
    
    f.write('SHAPE:\n')
    f.write(str(df.shape) + '\n\n')
    
    f.write('DESCRIPTIVE STATS:\n')
    f.write(df.describe().to_string() + '\n\n')
    
    # Identify columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    reit_cols = [c for c in df.columns if 'reit' in c.lower()]
    infl_cols = [c for c in df.columns if any(x in c.lower() for x in ['infl', 'cpi', 'pce'])]
    
    f.write(f'REIT cols: {reit_cols}\n')
    f.write(f'Inflation cols: {infl_cols}\n\n')
    
    # Correlations
    f.write('CORRELATIONS:\n')
    for rc in reit_cols:
        for ic in infl_cols:
            valid = df[[rc, ic]].dropna()
            r_p, p_p = pearsonr(valid[rc], valid[ic])
            r_s, p_s = spearmanr(valid[rc], valid[ic])
            f.write(f'{rc} vs {ic}: Pearson r={r_p:.4f} p={p_p:.4f}, Spearman r={r_s:.4f} p={p_s:.4f}\n')
    
    f.write('\nREGRESSIONS:\n')
    for rc in reit_cols:
        for ic in infl_cols:
            valid = df[[rc, ic]].dropna()
            slope, intercept, r_value, p_value, std_err = stats.linregress(valid[ic], valid[rc])
            f.write(f'{rc} ~ {ic}: slope={slope:.4f}, intercept={intercept:.4f}, R2={r_value**2:.4f}, p={p_value:.4f}\n')
    
    # Regime analysis
    if infl_cols:
        ic = infl_cols[0]
        median_infl = df[ic].median()
        df['regime'] = np.where(df[ic] > median_infl, 'High', 'Low')
        
        f.write(f'\nREGIME ANALYSIS (median inflation = {median_infl:.4f}):\n')
        for rc in reit_cols:
            high = df[df['regime'] == 'High'][rc].dropna()
            low = df[df['regime'] == 'Low'][rc].dropna()
            t, p = stats.ttest_ind(high, low)
            f.write(f'{rc}: High mean={high.mean():.4f}, Low mean={low.mean():.4f}, diff={high.mean()-low.mean():.4f}, t={t:.4f}, p={p:.4f}\n')
    
    # Correlation matrix
    f.write('\nCORRELATION MATRIX:\n')
    f.write(df[numeric_cols].corr().to_string() + '\n')

print('Done!')
