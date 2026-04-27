#!/usr/bin/env python3
"""
REIT-Inflation Panel Analysis
Comprehensive association analysis between REIT index returns and inflation
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)
os.makedirs('report', exist_ok=True)

print('Loading data...')
df = pd.read_csv('data/reit_macro_quarterly.csv')

print(f'Shape: {df.shape}')
print(f'Columns: {df.columns.tolist()}')

# ============================================================
# 1. DATA PREPARATION
# ============================================================

# Identify columns based on actual data
all_cols = df.columns.tolist()

# Find date column
date_col = None
for c in all_cols:
    if any(x in c.lower() for x in ['date', 'quarter', 'time', 'period', 'year']):
        date_col = c
        break

# Find REIT columns
reit_cols = [c for c in all_cols if 'reit' in c.lower() or 'return' in c.lower()]

# Find inflation columns  
infl_cols = [c for c in all_cols if any(x in c.lower() for x in ['infl', 'cpi', 'pce', 'price'])]

# Find other macro columns
other_macro = [c for c in all_cols if c not in [date_col] + reit_cols + infl_cols and c is not None]

# All numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

print(f'Date column: {date_col}')
print(f'REIT columns: {reit_cols}')
print(f'Inflation columns: {infl_cols}')
print(f'Other macro: {other_macro}')
print(f'Numeric columns: {numeric_cols}')

# Parse date
if date_col:
    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).reset_index(drop=True)
        print(f'Date range: {df[date_col].min()} to {df[date_col].max()}')
    except Exception as e:
        print(f'Date parse error: {e}')
        date_col = None

# ============================================================
# 2. DESCRIPTIVE STATISTICS
# ============================================================

print('\n=== DESCRIPTIVE STATISTICS ===')
desc_stats = df[numeric_cols].describe()
print(desc_stats)
desc_stats.to_csv('outputs/descriptive_stats.csv')

# ============================================================
# 3. CORRELATION ANALYSIS
# ============================================================

print('\n=== CORRELATION ANALYSIS ===')
corr_matrix = df[numeric_cols].corr()
print(corr_matrix)
corr_matrix.to_csv('outputs/correlation_matrix.csv')

# Detailed REIT-Inflation correlations
corr_results = []
for rc in reit_cols:
    for ic in infl_cols:
        valid = df[[rc, ic]].dropna()
        if len(valid) > 5:
            pearson_r, pearson_p = pearsonr(valid[rc], valid[ic])
            spearman_r, spearman_p = spearmanr(valid[rc], valid[ic])
            corr_results.append({
                'REIT_col': rc,
                'Inflation_col': ic,
                'N': len(valid),
                'Pearson_r': round(pearson_r, 4),
                'Pearson_p': round(pearson_p, 4),
                'Spearman_r': round(spearman_r, 4),
                'Spearman_p': round(spearman_p, 4),
                'Significant_5pct': pearson_p < 0.05
            })

if corr_results:
    corr_df = pd.DataFrame(corr_results)
    print('\nCorrelation Results:')
    print(corr_df)
    corr_df.to_csv('outputs/reit_inflation_correlations.csv', index=False)

# ============================================================
# 4. OLS REGRESSION
# ============================================================

print('\n=== OLS REGRESSION ===')

reg_results = []
for rc in reit_cols:
    for ic in infl_cols:
        valid = df[[rc, ic]].dropna()
        if len(valid) > 10:
            slope, intercept, r_value, p_value, std_err = stats.linregress(valid[ic], valid[rc])
            reg_results.append({
                'Dependent': rc,
                'Independent': ic,
                'N': len(valid),
                'Slope': round(slope, 4),
                'Intercept': round(intercept, 4),
                'R_squared': round(r_value**2, 4),
                'P_value': round(p_value, 4),
                'Std_err': round(std_err, 4),
                'Significant': p_value < 0.05
            })
            print(f'{rc} ~ {ic}: slope={slope:.4f}, R2={r_value**2:.4f}, p={p_value:.4f}')

if reg_results:
    reg_df = pd.DataFrame(reg_results)
    reg_df.to_csv('outputs/regression_results.csv', index=False)

# ============================================================
# 5. MULTIPLE REGRESSION (REIT ~ inflation + controls)
# ============================================================

print('\n=== MULTIPLE REGRESSION ===')

try:
    import statsmodels.api as sm
    
    multi_reg_results = []
    for rc in reit_cols:
        # Use inflation + other macro as predictors
        predictors = infl_cols + [c for c in other_macro if c in numeric_cols]
        valid_cols = [rc] + predictors
        valid = df[valid_cols].dropna()
        
        if len(valid) > len(predictors) + 5:
            X = sm.add_constant(valid[predictors])
            y = valid[rc]
            model = sm.OLS(y, X).fit()
            
            result_str = f'\n--- {rc} ~ {" + ".join(predictors)} ---\n'
            result_str += model.summary().as_text()
            print(result_str)
            
            multi_reg_results.append({
                'Dependent': rc,
                'Predictors': predictors,
                'N': len(valid),
                'R_squared': round(model.rsquared, 4),
                'Adj_R_squared': round(model.rsquared_adj, 4),
                'F_stat': round(model.fvalue, 4),
                'F_pvalue': round(model.f_pvalue, 4),
                'AIC': round(model.aic, 4),
                'BIC': round(model.bic, 4)
            })
            
            # Save full summary
            with open(f'outputs/regression_{rc}.txt', 'w') as f:
                f.write(model.summary().as_text())
    
    if multi_reg_results:
        pd.DataFrame(multi_reg_results).to_csv('outputs/multiple_regression_summary.csv', index=False)
        
except ImportError:
    print('statsmodels not available, using scipy only')

# ============================================================
# 6. REGIME ANALYSIS
# ============================================================

print('\n=== REGIME ANALYSIS ===')

if infl_cols:
    ic = infl_cols[0]
    median_infl = df[ic].median()
    df['inflation_regime'] = np.where(df[ic] > median_infl, 'High Inflation', 'Low Inflation')
    
    regime_results = []
    for rc in reit_cols:
        high_infl = df[df['inflation_regime'] == 'High Inflation'][rc].dropna()
        low_infl = df[df['inflation_regime'] == 'Low Inflation'][rc].dropna()
        
        if len(high_infl) > 5 and len(low_infl) > 5:
            t_stat, t_p = stats.ttest_ind(high_infl, low_infl)
            mw_stat, mw_p = stats.mannwhitneyu(high_infl, low_infl, alternative='two-sided')
            
            regime_results.append({
                'REIT_col': rc,
                'High_infl_mean': round(high_infl.mean(), 4),
                'High_infl_std': round(high_infl.std(), 4),
                'Low_infl_mean': round(low_infl.mean(), 4),
                'Low_infl_std': round(low_infl.std(), 4),
                'Diff_means': round(high_infl.mean() - low_infl.mean(), 4),
                'T_stat': round(t_stat, 4),
                'T_pvalue': round(t_p, 4),
                'MW_stat': round(mw_stat, 4),
                'MW_pvalue': round(mw_p, 4),
                'Significant': t_p < 0.05
            })
            print(f'{rc}: High={high_infl.mean():.4f}, Low={low_infl.mean():.4f}, t={t_stat:.4f}, p={t_p:.4f}')
    
    if regime_results:
        pd.DataFrame(regime_results).to_csv('outputs/regime_analysis.csv', index=False)

# ============================================================
# 7. LAGGED CORRELATION ANALYSIS
# ============================================================

print('\n=== LAGGED CORRELATION ANALYSIS ===')

if reit_cols and infl_cols:
    rc = reit_cols[0]
    ic = infl_cols[0]
    
    lags = range(-6, 7)  # -6 to +6 quarters
    lag_results = []
    
    for lag in lags:
        if lag < 0:
            # Inflation leads REIT (negative lag)
            x = df[ic].values[:len(df)+lag]
            y = df[rc].values[-lag:]
        elif lag > 0:
            # REIT leads inflation (positive lag)
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
            lag_results.append({'lag': lag, 'correlation': r, 'p_value': p, 'n': len(x_valid)})
    
    lag_df = pd.DataFrame(lag_results)
    lag_df.to_csv('outputs/lagged_correlations.csv', index=False)
    print(lag_df)

# ============================================================
# 8. VISUALIZATIONS
# ============================================================

print('\n=== CREATING VISUALIZATIONS ===')

plt.style.use('seaborn-v0_8-whitegrid')
colors = ['#1565C0', '#C62828', '#2E7D32', '#E65100', '#6A1B9A', '#00838F']

# ---- Figure 1: Time Series Overview ----
fig, axes = plt.subplots(len(numeric_cols), 1, figsize=(14, 3*len(numeric_cols)))
if len(numeric_cols) == 1:
    axes = [axes]

for i, col in enumerate(numeric_cols):
    color = colors[i % len(colors)]
    if date_col:
        axes[i].plot(df[date_col], df[col], color=color, linewidth=1.5, alpha=0.9)
        axes[i].tick_params(axis='x', rotation=45)
    else:
        axes[i].plot(df.index, df[col], color=color, linewidth=1.5, alpha=0.9)
    
    axes[i].axhline(y=df[col].mean(), color='black', linestyle='--', linewidth=0.8, alpha=0.6, label=f'Mean: {df[col].mean():.2f}')
    axes[i].set_title(col.replace('_', ' ').title(), fontsize=11, fontweight='bold')
    axes[i].legend(fontsize=8, loc='upper right')
    axes[i].grid(True, alpha=0.3)
    axes[i].set_ylabel(col)

plt.suptitle('REIT Returns and Macroeconomic Variables: Quarterly Time Series', 
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('report/images/fig1_time_series.png', dpi=150, bbox_inches='tight')
plt.close()
print('Figure 1 saved: Time Series Overview')

# ---- Figure 2: Correlation Heatmap ----
fig, ax = plt.subplots(figsize=(10, 8))
mask = np.zeros_like(corr_matrix, dtype=bool)
mask[np.triu_indices_from(mask, k=1)] = False  # Show full matrix

sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
            square=True, ax=ax, cbar_kws={'shrink': 0.8},
            linewidths=0.5, linecolor='white',
            annot_kws={'size': 9})
ax.set_title('Correlation Matrix: REIT Returns and Macroeconomic Variables', 
             fontsize=12, fontweight='bold', pad=15)
plt.tight_layout()
plt.savefig('report/images/fig2_correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print('Figure 2 saved: Correlation Heatmap')

# ---- Figure 3: Scatter Plots REIT vs Inflation ----
if reit_cols and infl_cols:
    n_reit = len(reit_cols)
    n_infl = len(infl_cols)
    
    fig, axes = plt.subplots(n_reit, n_infl, figsize=(6*n_infl, 5*n_reit))
    
    if n_reit == 1 and n_infl == 1:
        axes = np.array([[axes]])
    elif n_reit == 1:
        axes = axes.reshape(1, -1)
    elif n_infl == 1:
        axes = axes.reshape(-1, 1)
    
    for i, rc in enumerate(reit_cols):
        for j, ic in enumerate(infl_cols):
            ax = axes[i, j]
            valid = df[[rc, ic]].dropna()
            
            # Color by time period if date available
            if date_col and len(valid) > 0:
                time_idx = np.arange(len(valid))
                scatter = ax.scatter(valid[ic], valid[rc], c=time_idx, 
                                    cmap='viridis', alpha=0.7, s=60, edgecolors='white', linewidth=0.5)
                plt.colorbar(scatter, ax=ax, label='Time (quarters)')
            else:
                ax.scatter(valid[ic], valid[rc], alpha=0.6, color=colors[i % len(colors)], s=60)
            
            # Add regression line
            if len(valid) > 5:
                slope, intercept, r_value, p_value, std_err = stats.linregress(valid[ic], valid[rc])
                x_line = np.linspace(valid[ic].min(), valid[ic].max(), 100)
                y_line = slope * x_line + intercept
                ax.plot(x_line, y_line, 'r-', linewidth=2.5, 
                       label=f'OLS: β={slope:.3f}\nR²={r_value**2:.3f}, p={p_value:.3f}')
                ax.legend(fontsize=8, loc='best')
            
            ax.set_xlabel(ic.replace('_', ' ').title(), fontsize=10)
            ax.set_ylabel(rc.replace('_', ' ').title(), fontsize=10)
            ax.set_title(f'{rc.replace("_", " ").title()} vs {ic.replace("_", " ").title()}', 
                        fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3)
    
    plt.suptitle('REIT Returns vs Inflation: Scatter Plots with OLS Regression', 
                fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig3_scatter_plots.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 3 saved: Scatter Plots')

# ---- Figure 4: Rolling Correlation ----
if date_col and reit_cols and infl_cols:
    rc = reit_cols[0]
    ic = infl_cols[0]
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    
    # Top: REIT returns
    axes[0].fill_between(df[date_col], df[rc], 0, 
                         where=df[rc] >= 0, alpha=0.4, color='#2E7D32', label='Positive')
    axes[0].fill_between(df[date_col], df[rc], 0, 
                         where=df[rc] < 0, alpha=0.4, color='#C62828', label='Negative')
    axes[0].plot(df[date_col], df[rc], color='#1565C0', linewidth=1.2)
    axes[0].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    axes[0].axhline(y=df[rc].mean(), color='navy', linestyle='--', linewidth=1, 
                   label=f'Mean: {df[rc].mean():.2f}%')
    axes[0].set_title(f'{rc.replace("_", " ").title()}', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Return (%)')
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3)
    
    # Middle: Inflation
    axes[1].plot(df[date_col], df[ic], color='#C62828', linewidth=1.5)
    axes[1].fill_between(df[date_col], df[ic], df[ic].mean(), alpha=0.3, color='#C62828')
    axes[1].axhline(y=df[ic].mean(), color='black', linestyle='--', linewidth=1, 
                   label=f'Mean: {df[ic].mean():.2f}%')
    axes[1].set_title(f'{ic.replace("_", " ").title()}', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Inflation (%)')
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3)
    
    # Bottom: Rolling correlation
    rolling_corr_8 = df[rc].rolling(8).corr(df[ic])
    rolling_corr_4 = df[rc].rolling(4).corr(df[ic])
    
    axes[2].plot(df[date_col], rolling_corr_8, color='#2E7D32', linewidth=2, 
                label='8-Quarter Rolling Corr')
    axes[2].plot(df[date_col], rolling_corr_4, color='#E65100', linewidth=1.5, 
                alpha=0.7, linestyle='--', label='4-Quarter Rolling Corr')
    axes[2].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    axes[2].fill_between(df[date_col], rolling_corr_8, 0, alpha=0.2, color='#2E7D32')
    axes[2].set_title(f'Rolling Correlation: {rc.replace("_", " ").title()} vs {ic.replace("_", " ").title()}', 
                     fontsize=12, fontweight='bold')
    axes[2].set_ylabel('Correlation Coefficient')
    axes[2].set_ylim(-1.1, 1.1)
    axes[2].legend(fontsize=9)
    axes[2].grid(True, alpha=0.3)
    
    for ax in axes:
        ax.tick_params(axis='x', rotation=45)
    
    plt.suptitle('REIT-Inflation Dynamic Relationship Over Time', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig4_rolling_correlation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 4 saved: Rolling Correlation')

# ---- Figure 5: Regime Analysis ----
if infl_cols and reit_cols:
    ic = infl_cols[0]
    
    fig, axes = plt.subplots(1, len(reit_cols), figsize=(7*len(reit_cols), 6))
    if len(reit_cols) == 1:
        axes = [axes]
    
    for i, rc in enumerate(reit_cols):
        high_infl = df[df['inflation_regime'] == 'High Inflation'][rc].dropna()
        low_infl = df[df['inflation_regime'] == 'Low Inflation'][rc].dropna()
        
        bp = axes[i].boxplot([low_infl, high_infl], 
                             labels=['Low\nInflation', 'High\nInflation'],
                             patch_artist=True,
                             notch=True,
                             boxprops=dict(facecolor='lightblue', color='navy', alpha=0.7),
                             medianprops=dict(color='red', linewidth=2.5),
                             whiskerprops=dict(color='navy', linewidth=1.5),
                             capprops=dict(color='navy', linewidth=1.5),
                             flierprops=dict(marker='o', markerfacecolor='gray', markersize=4))
        
        # Color boxes differently
        bp['boxes'][0].set_facecolor('#90CAF9')
        bp['boxes'][1].set_facecolor('#EF9A9A')
        
        # Add mean markers
        axes[i].scatter([1, 2], [low_infl.mean(), high_infl.mean()], 
                       color='darkblue', s=100, zorder=5, marker='D', label='Mean')
        
        # Add t-test result
        t_stat, t_p = stats.ttest_ind(high_infl, low_infl)
        sig_text = f'p={t_p:.3f}' + (' *' if t_p < 0.05 else ' (ns)')
        axes[i].set_title(f'{rc.replace("_", " ").title()}\nby Inflation Regime\n({sig_text})', 
                         fontsize=11, fontweight='bold')
        axes[i].set_ylabel('REIT Return (%)')
        axes[i].legend(fontsize=9)
        axes[i].grid(True, alpha=0.3, axis='y')
        
        # Add text annotations
        axes[i].text(1, axes[i].get_ylim()[0] + 0.1*(axes[i].get_ylim()[1]-axes[i].get_ylim()[0]),
                    f'n={len(low_infl)}\nμ={low_infl.mean():.2f}', 
                    ha='center', fontsize=9, color='navy')
        axes[i].text(2, axes[i].get_ylim()[0] + 0.1*(axes[i].get_ylim()[1]-axes[i].get_ylim()[0]),
                    f'n={len(high_infl)}\nμ={high_infl.mean():.2f}', 
                    ha='center', fontsize=9, color='darkred')
    
    plt.suptitle('REIT Performance Under Different Inflation Regimes', 
                fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig5_regime_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 5 saved: Regime Analysis')

# ---- Figure 6: Lagged Correlation ----
if reit_cols and infl_cols:
    rc = reit_cols[0]
    ic = infl_cols[0]
    
    lag_df = pd.read_csv('outputs/lagged_correlations.csv')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bar_colors = ['#C62828' if p < 0.05 else '#90CAF9' for p in lag_df['p_value']]
    
    bars = ax.bar(lag_df['lag'], lag_df['correlation'], color=bar_colors, 
                 alpha=0.85, edgecolor='black', linewidth=0.5, width=0.7)
    
    ax.axhline(y=0, color='black', linewidth=1.2)
    
    # Add significance threshold lines
    n = lag_df['n'].mean()
    sig_threshold = 1.96 / np.sqrt(n)
    ax.axhline(y=sig_threshold, color='gray', linestyle='--', linewidth=1, 
              alpha=0.7, label=f'95% CI (±{sig_threshold:.3f})')
    ax.axhline(y=-sig_threshold, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    
    # Add value labels on bars
    for bar, val in zip(bars, lag_df['correlation']):
        if not np.isnan(val):
            ax.text(bar.get_x() + bar.get_width()/2, 
                   val + 0.02 * np.sign(val),
                   f'{val:.3f}', ha='center', va='bottom' if val >= 0 else 'top',
                   fontsize=8)
    
    ax.set_xlabel('Lag (quarters)\nNegative = Inflation leads REIT | Positive = REIT leads Inflation', 
                 fontsize=10)
    ax.set_ylabel('Pearson Correlation', fontsize=10)
    ax.set_title(f'Cross-Correlation Analysis: {rc.replace("_", " ").title()} vs {ic.replace("_", " ").title()}\n'
                f'(Red bars = statistically significant at p<0.05)', 
                fontsize=12, fontweight='bold')
    ax.set_xticks(lag_df['lag'])
    ax.set_xticklabels([f'{l}Q' for l in lag_df['lag']])
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(-1, 1)
    
    plt.tight_layout()
    plt.savefig('report/images/fig6_lagged_correlation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 6 saved: Lagged Correlation')

# ---- Figure 7: Multi-variable Scatter Matrix ----
if len(numeric_cols) >= 3:
    key_vars = numeric_cols[:min(5, len(numeric_cols))]
    
    fig, axes = plt.subplots(len(key_vars), len(key_vars), figsize=(14, 12))
    
    for i, var1 in enumerate(key_vars):
        for j, var2 in enumerate(key_vars):
            ax = axes[i, j]
            
            if i == j:
                # Diagonal: histogram
                ax.hist(df[var1].dropna(), bins=20, color=colors[i % len(colors)], 
                       alpha=0.7, edgecolor='white')
                ax.set_title(var1.replace('_', '\n'), fontsize=8, fontweight='bold')
            else:
                # Off-diagonal: scatter
                valid = df[[var1, var2]].dropna()
                ax.scatter(valid[var2], valid[var1], alpha=0.4, s=20, 
                          color=colors[i % len(colors)])
                
                if len(valid) > 5:
                    r, p = pearsonr(valid[var2], valid[var1])
                    ax.set_title(f'r={r:.2f}', fontsize=8, 
                               color='red' if p < 0.05 else 'black')
            
            if i == len(key_vars) - 1:
                ax.set_xlabel(var2.replace('_', ' '), fontsize=7)
            if j == 0:
                ax.set_ylabel(var1.replace('_', ' '), fontsize=7)
            
            ax.tick_params(labelsize=6)
    
    plt.suptitle('Pairwise Scatter Matrix: REIT Returns and Macroeconomic Variables', 
                fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig7_scatter_matrix.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 7 saved: Scatter Matrix')

# ---- Figure 8: Inflation Quartile Analysis ----
if infl_cols and reit_cols:
    ic = infl_cols[0]
    
    df['infl_quartile'] = pd.qcut(df[ic], q=4, labels=['Q1\n(Lowest)', 'Q2', 'Q3', 'Q4\n(Highest)'])
    
    fig, axes = plt.subplots(1, len(reit_cols), figsize=(7*len(reit_cols), 6))
    if len(reit_cols) == 1:
        axes = [axes]
    
    for i, rc in enumerate(reit_cols):
        quartile_means = df.groupby('infl_quartile')[rc].agg(['mean', 'std', 'count'])
        
        bars = axes[i].bar(range(4), quartile_means['mean'], 
                          color=['#1565C0', '#2E7D32', '#E65100', '#C62828'],
                          alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Error bars
        axes[i].errorbar(range(4), quartile_means['mean'], 
                        yerr=quartile_means['std']/np.sqrt(quartile_means['count']),
                        fmt='none', color='black', capsize=5, linewidth=2)
        
        axes[i].axhline(y=0, color='black', linewidth=1)
        axes[i].set_xticks(range(4))
        axes[i].set_xticklabels(quartile_means.index, fontsize=9)
        axes[i].set_xlabel(f'{ic.replace("_", " ").title()} Quartile', fontsize=10)
        axes[i].set_ylabel('Mean REIT Return (%)', fontsize=10)
        axes[i].set_title(f'Mean {rc.replace("_", " ").title()}\nby Inflation Quartile', 
                         fontsize=11, fontweight='bold')
        axes[i].grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, val in zip(bars, quartile_means['mean']):
            axes[i].text(bar.get_x() + bar.get_width()/2, 
                        val + 0.1 * np.sign(val),
                        f'{val:.2f}%', ha='center', va='bottom' if val >= 0 else 'top',
                        fontsize=9, fontweight='bold')
    
    plt.suptitle('REIT Returns by Inflation Quartile', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig8_quartile_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 8 saved: Quartile Analysis')

# ============================================================
# 9. SAVE COMPREHENSIVE RESULTS
# ============================================================

with open('outputs/comprehensive_results.txt', 'w') as f:
    f.write('=== REIT-INFLATION PANEL ANALYSIS: COMPREHENSIVE RESULTS ===\n\n')
    
    f.write('1. DATA OVERVIEW\n')
    f.write(f'   Observations: {len(df)}\n')
    f.write(f'   Variables: {numeric_cols}\n')
    if date_col:
        f.write(f'   Date range: {df[date_col].min()} to {df[date_col].max()}\n')
    f.write('\n')
    
    f.write('2. DESCRIPTIVE STATISTICS\n')
    f.write(df[numeric_cols].describe().to_string())
    f.write('\n\n')
    
    f.write('3. CORRELATION MATRIX\n')
    f.write(corr_matrix.to_string())
    f.write('\n\n')
    
    if corr_results:
        f.write('4. REIT-INFLATION CORRELATIONS\n')
        f.write(pd.DataFrame(corr_results).to_string())
        f.write('\n\n')
    
    if reg_results:
        f.write('5. OLS REGRESSION RESULTS\n')
        f.write(pd.DataFrame(reg_results).to_string())
        f.write('\n\n')
    
    if infl_cols and reit_cols:
        ic = infl_cols[0]
        rc = reit_cols[0]
        high_infl = df[df['inflation_regime'] == 'High Inflation'][rc].dropna()
        low_infl = df[df['inflation_regime'] == 'Low Inflation'][rc].dropna()
        t_stat, t_p = stats.ttest_ind(high_infl, low_infl)
        
        f.write('6. REGIME ANALYSIS\n')
        f.write(f'   Inflation median: {df[ic].median():.4f}\n')
        f.write(f'   High inflation REIT mean: {high_infl.mean():.4f}\n')
        f.write(f'   Low inflation REIT mean: {low_infl.mean():.4f}\n')
        f.write(f'   T-test: t={t_stat:.4f}, p={t_p:.4f}\n')
        f.write(f'   Significant difference: {"Yes" if t_p < 0.05 else "No"}\n')

print('\nAll results saved!')
print('\n=== ANALYSIS COMPLETE ===')
