import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
from scipy import stats
import os

os.makedirs('outputs', exist_ok=True)

df = pd.read_csv('data/reit_macro_quarterly.csv')

result = []
result.append(f'Shape: {df.shape}')
result.append(f'Columns: {list(df.columns)}')
result.append('')
result.append('Describe:')
result.append(df.describe().to_string())
result.append('')

# Identify columns
reit_cols = [c for c in df.columns if 'reit' in c.lower()]
infl_cols = [c for c in df.columns if 'infl' in c.lower()]

result.append(f'REIT cols: {reit_cols}')
result.append(f'Inflation cols: {infl_cols}')
result.append('')

# Correlations
result.append('Correlations:')
for rc in reit_cols:
    for ic in infl_cols:
        valid = df[[rc, ic]].dropna()
        r_p, p_p = pearsonr(valid[rc], valid[ic])
        r_s, p_s = spearmanr(valid[rc], valid[ic])
        result.append(f'  {rc} vs {ic}: Pearson r={r_p:.4f} p={p_p:.4f}, Spearman r={r_s:.4f} p={p_s:.4f}')

result.append('')
result.append('Regressions:')
for rc in reit_cols:
    for ic in infl_cols:
        valid = df[[rc, ic]].dropna()
        slope, intercept, r_value, p_value, std_err = stats.linregress(valid[ic], valid[rc])
        result.append(f'  {rc} ~ {ic}: slope={slope:.4f}, intercept={intercept:.4f}, R2={r_value**2:.4f}, p={p_value:.4f}')

result.append('')
result.append('Regime analysis:')
if infl_cols:
    ic = infl_cols[0]
    median_infl = df[ic].median()
    result.append(f'  Median inflation: {median_infl:.4f}')
    df['regime'] = np.where(df[ic] > median_infl, 'High', 'Low')
    for rc in reit_cols:
        high = df[df['regime'] == 'High'][rc].dropna()
        low = df[df['regime'] == 'Low'][rc].dropna()
        t, p = stats.ttest_ind(high, low)
        result.append(f'  {rc}: High={high.mean():.4f}, Low={low.mean():.4f}, diff={high.mean()-low.mean():.4f}, t={t:.4f}, p={p:.4f}')

output = '\n'.join(result)
with open('outputs/actual_numbers.txt', 'w') as f:
    f.write(output)

print('Done!')
print(output)
