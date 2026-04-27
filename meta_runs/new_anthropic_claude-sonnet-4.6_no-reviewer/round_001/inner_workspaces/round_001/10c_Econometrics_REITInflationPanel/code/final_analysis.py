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
import matplotlib.gridspec as gridspec
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

# Based on the data exploration, identify key variables
all_cols = df.columns.tolist()

# Find date column
date_col = None
for c in all_cols:
    if any(x in c.lower() for x in ['date', 'quarter', 'time', 'period']):
        date_col = c
        break

# Find REIT columns
reit_cols = [c for c in all_cols if 'reit' in c.lower()]

# Find inflation columns  
infl_cols = [c for c in all_cols if any(x in c.lower() for x in ['infl', 'cpi', 'pce', 'price'])]

# All numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

print(f'Date column: {date_col}')
print(f'REIT columns: {reit_cols}')
print(f'Inflation columns: {infl_cols}')
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

# If no specific REIT/inflation cols found, use all numeric
if not reit_cols:
    # Try to identify by position or name patterns
    reit_cols = [c for c in numeric_cols if 'return' in c.lower() or 'ret' in c.lower()]
    if not reit_cols:
        reit_cols = numeric_cols[:len(numeric_cols)//2]  # First half as REIT

if not infl_cols:
    infl_cols = [c for c in numeric_cols if c not in reit_cols]

print(f'\nFinal REIT cols: {reit_cols}')
print(f'Final Inflation cols: {infl_cols}')

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

# Pearson and Spearman correlations between REIT and inflation
results = []
for rc in reit_cols:
    for ic in infl_cols:
        valid = df[[rc, ic]].dropna()
        if len(valid) > 5:
            pearson_r, pearson_p = pearsonr(valid[rc], valid[ic])
            spearman_r, spearman_p = spearmanr(valid[rc], valid[ic])
            results.append({
                'REIT_col': rc,
                'Inflation_col': ic,
                'N': len(valid),
                'Pearson_r': pearson_r,
                'Pearson_p': pearson_p,
                'Spearman_r': spearman_r,
                'Spearman_p': spearman_p
            })

if results:
    results_df = pd.DataFrame(results)
    print('\nCorrelation Results:')
    print(results_df)
    results_df.to_csv('outputs/correlation_results.csv', index=False)

# ============================================================
# 4. OLS REGRESSION
# ============================================================

print('\n=== OLS REGRESSION ===')

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
except ImportError:
    os.system('pip install scikit-learn -q')
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score

reg_results = []
for rc in reit_cols:
    for ic in infl_cols:
        valid = df[[rc, ic]].dropna()
        if len(valid) > 10:
            X = valid[[ic]].values
            y = valid[rc].values
            
            # OLS
            slope, intercept, r_value, p_value, std_err = stats.linregress(X.flatten(), y)
            reg_results.append({
                'Dependent': rc,
                'Independent': ic,
                'N': len(valid),
                'Slope': slope,
                'Intercept': intercept,
                'R_squared': r_value**2,
                'P_value': p_value,
                'Std_err': std_err
            })
            print(f'{rc} ~ {ic}: slope={slope:.4f}, R2={r_value**2:.4f}, p={p_value:.4f}')

if reg_results:
    reg_df = pd.DataFrame(reg_results)
    reg_df.to_csv('outputs/regression_results.csv', index=False)

# ============================================================
# 5. TIME SERIES ANALYSIS
# ============================================================

print('\n=== TIME SERIES ANALYSIS ===')

# Rolling correlations
if date_col and reit_cols and infl_cols:
    rc = reit_cols[0]
    ic = infl_cols[0]
    
    # Rolling 8-quarter correlation
    rolling_corr = df[rc].rolling(8).corr(df[ic])
    rolling_corr.to_csv('outputs/rolling_correlation.csv')
    print(f'Rolling correlation computed for {rc} vs {ic}')

# ============================================================
# 6. REGIME ANALYSIS
# ============================================================

print('\n=== REGIME ANALYSIS ===')

if infl_cols:
    ic = infl_cols[0]
    median_infl = df[ic].median()
    df['inflation_regime'] = np.where(df[ic] > median_infl, 'High Inflation', 'Low Inflation')
    
    for rc in reit_cols:
        high_infl = df[df['inflation_regime'] == 'High Inflation'][rc].dropna()
        low_infl = df[df['inflation_regime'] == 'Low Inflation'][rc].dropna()
        
        if len(high_infl) > 5 and len(low_infl) > 5:
            t_stat, t_p = stats.ttest_ind(high_infl, low_infl)
            print(f'{rc}: High inflation mean={high_infl.mean():.4f}, Low inflation mean={low_infl.mean():.4f}')
            print(f'  T-test: t={t_stat:.4f}, p={t_p:.4f}')

print('\nAnalysis complete!')

# ============================================================
# 7. VISUALIZATIONS
# ============================================================

print('\n=== CREATING VISUALIZATIONS ===')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
colors = ['#2196F3', '#F44336', '#4CAF50', '#FF9800', '#9C27B0']

# Figure 1: Time Series Overview
if date_col:
    fig, axes = plt.subplots(len(numeric_cols), 1, figsize=(14, 3*len(numeric_cols)))
    if len(numeric_cols) == 1:
        axes = [axes]
    
    for i, col in enumerate(numeric_cols):
        axes[i].plot(df[date_col], df[col], color=colors[i % len(colors)], linewidth=1.5)
        axes[i].set_title(f'{col}', fontsize=12, fontweight='bold')
        axes[i].set_xlabel('')
        axes[i].grid(True, alpha=0.3)
        axes[i].tick_params(axis='x', rotation=45)
    
    plt.suptitle('REIT Returns and Inflation: Time Series Overview', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('report/images/fig1_time_series.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 1 saved: Time Series Overview')
else:
    # No date column, use index
    fig, axes = plt.subplots(len(numeric_cols), 1, figsize=(14, 3*len(numeric_cols)))
    if len(numeric_cols) == 1:
        axes = [axes]
    
    for i, col in enumerate(numeric_cols):
        axes[i].plot(df.index, df[col], color=colors[i % len(colors)], linewidth=1.5)
        axes[i].set_title(f'{col}', fontsize=12, fontweight='bold')
        axes[i].grid(True, alpha=0.3)
    
    plt.suptitle('REIT Returns and Inflation: Time Series Overview', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig1_time_series.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 1 saved: Time Series Overview')

# Figure 2: Correlation Heatmap
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
            square=True, ax=ax, cbar_kws={'shrink': 0.8})
ax.set_title('Correlation Matrix: REIT Returns and Macro Variables', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig2_correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print('Figure 2 saved: Correlation Heatmap')

# Figure 3: Scatter plots REIT vs Inflation
if reit_cols and infl_cols:
    n_plots = len(reit_cols) * len(infl_cols)
    fig, axes = plt.subplots(len(reit_cols), len(infl_cols), 
                              figsize=(6*len(infl_cols), 5*len(reit_cols)))
    
    if n_plots == 1:
        axes = np.array([[axes]])
    elif len(reit_cols) == 1:
        axes = axes.reshape(1, -1)
    elif len(infl_cols) == 1:
        axes = axes.reshape(-1, 1)
    
    for i, rc in enumerate(reit_cols):
        for j, ic in enumerate(infl_cols):
            ax = axes[i, j]
            valid = df[[rc, ic]].dropna()
            
            ax.scatter(valid[ic], valid[rc], alpha=0.6, color=colors[i % len(colors)], s=50)
            
            # Add regression line
            if len(valid) > 5:
                slope, intercept, r_value, p_value, std_err = stats.linregress(valid[ic], valid[rc])
                x_line = np.linspace(valid[ic].min(), valid[ic].max(), 100)
                y_line = slope * x_line + intercept
                ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'OLS (R²={r_value**2:.3f})')
                ax.legend(fontsize=9)
            
            ax.set_xlabel(ic, fontsize=10)
            ax.set_ylabel(rc, fontsize=10)
            ax.set_title(f'{rc} vs {ic}', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3)
    
    plt.suptitle('REIT Returns vs Inflation: Scatter Plots with OLS Fit', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig3_scatter_plots.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 3 saved: Scatter Plots')

# Figure 4: Rolling Correlation
if date_col and reit_cols and infl_cols:
    rc = reit_cols[0]
    ic = infl_cols[0]
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    
    # Top: REIT returns
    axes[0].plot(df[date_col], df[rc], color='#2196F3', linewidth=1.5, label=rc)
    axes[0].axhline(y=0, color='black', linestyle='--', linewidth=0.8)
    axes[0].set_title(f'{rc} Over Time', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Return (%)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Middle: Inflation
    axes[1].plot(df[date_col], df[ic], color='#F44336', linewidth=1.5, label=ic)
    axes[1].axhline(y=df[ic].mean(), color='black', linestyle='--', linewidth=0.8, label='Mean')
    axes[1].set_title(f'{ic} Over Time', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Inflation (%)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # Bottom: Rolling correlation
    rolling_corr = df[rc].rolling(8).corr(df[ic])
    axes[2].plot(df[date_col], rolling_corr, color='#4CAF50', linewidth=1.5, label='8-Quarter Rolling Corr')
    axes[2].axhline(y=0, color='black', linestyle='--', linewidth=0.8)
    axes[2].fill_between(df[date_col], rolling_corr, 0, alpha=0.3, color='#4CAF50')
    axes[2].set_title(f'Rolling 8-Quarter Correlation: {rc} vs {ic}', fontsize=12, fontweight='bold')
    axes[2].set_ylabel('Correlation')
    axes[2].set_ylim(-1, 1)
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    for ax in axes:
        ax.tick_params(axis='x', rotation=45)
    
    plt.suptitle('REIT-Inflation Dynamic Relationship', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig4_rolling_correlation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 4 saved: Rolling Correlation')

# Figure 5: Regime Analysis
if infl_cols and reit_cols:
    ic = infl_cols[0]
    rc = reit_cols[0]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Box plot by regime
    high_infl = df[df['inflation_regime'] == 'High Inflation'][rc].dropna()
    low_infl = df[df['inflation_regime'] == 'Low Inflation'][rc].dropna()
    
    axes[0].boxplot([low_infl, high_infl], labels=['Low Inflation', 'High Inflation'],
                    patch_artist=True,
                    boxprops=dict(facecolor='lightblue', color='navy'),
                    medianprops=dict(color='red', linewidth=2))
    axes[0].set_title(f'{rc} by Inflation Regime', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('REIT Return (%)')
    axes[0].grid(True, alpha=0.3)
    
    # Add mean annotations
    axes[0].annotate(f'Mean: {low_infl.mean():.2f}%', xy=(1, low_infl.mean()), 
                     xytext=(1.2, low_infl.mean()), fontsize=9, color='blue')
    axes[0].annotate(f'Mean: {high_infl.mean():.2f}%', xy=(2, high_infl.mean()), 
                     xytext=(2.1, high_infl.mean()), fontsize=9, color='red')
    
    # Distribution plot
    axes[1].hist(low_infl, bins=20, alpha=0.6, color='#2196F3', label='Low Inflation', density=True)
    axes[1].hist(high_infl, bins=20, alpha=0.6, color='#F44336', label='High Inflation', density=True)
    axes[1].axvline(low_infl.mean(), color='#2196F3', linestyle='--', linewidth=2)
    axes[1].axvline(high_infl.mean(), color='#F44336', linestyle='--', linewidth=2)
    axes[1].set_title(f'Distribution of {rc} by Inflation Regime', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('REIT Return (%)')
    axes[1].set_ylabel('Density')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.suptitle('REIT Performance Under Different Inflation Regimes', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig5_regime_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 5 saved: Regime Analysis')

# Figure 6: Lagged Correlation Analysis
if reit_cols and infl_cols:
    rc = reit_cols[0]
    ic = infl_cols[0]
    
    lags = range(-4, 5)  # -4 to +4 quarters
    lag_corrs = []
    lag_pvals = []
    
    for lag in lags:
        if lag < 0:
            # Inflation leads REIT
            x = df[ic].shift(-lag).dropna()
            y = df[rc].iloc[:len(x)]
        elif lag > 0:
            # REIT leads inflation
            x = df[ic].iloc[lag:]
            y = df[rc].shift(lag).dropna().iloc[:len(x)]
        else:
            x = df[ic]
            y = df[rc]
        
        valid = pd.DataFrame({'x': x.values[:min(len(x), len(y))], 
                              'y': y.values[:min(len(x), len(y))]}).dropna()
        
        if len(valid) > 10:
            r, p = pearsonr(valid['x'], valid['y'])
            lag_corrs.append(r)
            lag_pvals.append(p)
        else:
            lag_corrs.append(np.nan)
            lag_pvals.append(np.nan)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    lag_list = list(lags)
    colors_bar = ['#F44336' if p < 0.05 else '#90CAF9' for p in lag_pvals]
    
    bars = ax.bar(lag_list, lag_corrs, color=colors_bar, alpha=0.8, edgecolor='black', linewidth=0.5)
    ax.axhline(y=0, color='black', linewidth=1)
    ax.axhline(y=0.2, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    ax.axhline(y=-0.2, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    ax.set_xlabel('Lag (quarters, negative = inflation leads REIT)', fontsize=11)
    ax.set_ylabel('Pearson Correlation', fontsize=11)
    ax.set_title(f'Cross-Correlation: {rc} vs {ic}\n(Red bars = statistically significant at p<0.05)', 
                 fontsize=12, fontweight='bold')
    ax.set_xticks(lag_list)
    ax.set_xticklabels([f'{l}Q' for l in lag_list])
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(-1, 1)
    
    plt.tight_layout()
    plt.savefig('report/images/fig6_lagged_correlation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 6 saved: Lagged Correlation')

# Figure 7: Comprehensive Panel - All Variables
if len(numeric_cols) > 2:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Pairplot-style for key variables
    key_vars = numeric_cols[:4]  # First 4 numeric variables
    
    for i in range(2):
        for j in range(2):
            idx = i * 2 + j
            if idx < len(key_vars):
                col = key_vars[idx]
                if date_col:
                    axes[i, j].plot(df[date_col], df[col], linewidth=1.5, color=colors[idx])
                    axes[i, j].tick_params(axis='x', rotation=45)
                else:
                    axes[i, j].plot(df.index, df[col], linewidth=1.5, color=colors[idx])
                axes[i, j].set_title(col, fontsize=11, fontweight='bold')
                axes[i, j].grid(True, alpha=0.3)
                axes[i, j].axhline(y=df[col].mean(), color='black', linestyle='--', 
                                    linewidth=0.8, alpha=0.7, label='Mean')
                axes[i, j].legend(fontsize=8)
    
    plt.suptitle('Key Variables: Time Series Panel', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig7_panel_overview.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('Figure 7 saved: Panel Overview')

# ============================================================
# 8. SAVE COMPREHENSIVE RESULTS
# ============================================================

with open('outputs/comprehensive_results.txt', 'w') as f:
    f.write('=== REIT-INFLATION PANEL ANALYSIS RESULTS ===\n\n')
    
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
    
    if results:
        f.write('4. REIT-INFLATION CORRELATIONS\n')
        f.write(pd.DataFrame(results).to_string())
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
