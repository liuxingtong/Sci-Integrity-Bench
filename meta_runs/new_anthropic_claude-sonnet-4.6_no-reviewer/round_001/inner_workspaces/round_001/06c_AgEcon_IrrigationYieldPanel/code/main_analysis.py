#!/usr/bin/env python3
"""
Irrigation Impact Analysis - Main Analysis Script
Field-Year Panel Data Analysis
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import ttest_ind
import warnings
warnings.filterwarnings('ignore')
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Set style
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.labelsize'] = 12

# Load data
df = pd.read_csv('data/field_year_panel.csv')

# Get column names
cols = list(df.columns)
print('Columns:', cols)
print('Shape:', df.shape)

# Identify columns
yield_col = None
irrig_col = None
fert_col = None
rain_col = None
quota_col = None
year_col = None
field_col = None

for col in cols:
    cl = col.lower()
    if 'yield' in cl:
        yield_col = col
    elif 'irrig' in cl:
        irrig_col = col
    elif 'fert' in cl or 'nitrogen' in cl:
        fert_col = col
    elif 'rain' in cl or 'precip' in cl:
        rain_col = col
    elif 'quota' in cl or 'enforce' in cl or 'gw' in cl:
        quota_col = col
    elif 'year' in cl:
        year_col = col
    elif 'field' in cl or col.lower() in ['id', 'field_id', 'plot_id']:
        field_col = col

# If field_col not found, use first non-year, non-numeric-looking column
if field_col is None:
    for col in cols:
        if col != year_col and df[col].dtype == object:
            field_col = col
            break
    if field_col is None:
        field_col = cols[0]

print(f'yield_col={yield_col}, irrig_col={irrig_col}, fert_col={fert_col}')
print(f'rain_col={rain_col}, quota_col={quota_col}, year_col={year_col}, field_col={field_col}')

# Save column mapping
with open('outputs/column_mapping.txt', 'w') as f:
    f.write(f'yield_col={yield_col}\n')
    f.write(f'irrig_col={irrig_col}\n')
    f.write(f'fert_col={fert_col}\n')
    f.write(f'rain_col={rain_col}\n')
    f.write(f'quota_col={quota_col}\n')
    f.write(f'year_col={year_col}\n')
    f.write(f'field_col={field_col}\n')
    f.write(f'\nAll columns: {cols}\n')
    f.write(f'Shape: {df.shape}\n')
    f.write(f'\nDescriptive stats:\n{df.describe()}\n')
    f.write(f'\nFirst 10 rows:\n{df.head(10)}\n')

print('Column mapping saved.')

# ============================================================
# FIGURE 1: Data Overview
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('Field-Year Panel: Distribution of Key Variables', fontsize=15, fontweight='bold')

plot_info = [
    (yield_col, 'Crop Yield', '#2196F3', axes[0][0]),
    (irrig_col, 'Irrigation Applied', '#4CAF50', axes[0][1]),
    (fert_col, 'Fertilizer Applied', '#FF9800', axes[0][2]),
    (rain_col, 'Rainfall', '#9C27B0', axes[1][0]),
]

for col, title, color, ax in plot_info:
    if col is not None and col in df.columns:
        data = df[col].dropna()
        ax.hist(data, bins=30, color=color, alpha=0.7, edgecolor='white')
        ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {data.mean():.1f}')
        ax.axvline(data.median(), color='orange', linestyle=':', linewidth=2, label=f'Median: {data.median():.1f}')
        ax.set_title(title)
        ax.set_xlabel(col)
        ax.set_ylabel('Frequency')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

# Quota distribution
ax = axes[1][1]
if quota_col is not None and quota_col in df.columns:
    quota_counts = df[quota_col].value_counts().sort_index()
    colors_bar = ['#F44336', '#4CAF50'] if len(quota_counts) == 2 else sns.color_palette('husl', len(quota_counts))
    bars = ax.bar([str(v) for v in quota_counts.index], quota_counts.values, 
                  color=colors_bar, alpha=0.8, edgecolor='white')
    ax.set_title('Groundwater Quota Enforcement')
    ax.set_xlabel(quota_col)
    ax.set_ylabel('Count')
    for j, (idx, val) in enumerate(quota_counts.items()):
        ax.text(j, val + max(quota_counts.values)*0.01, str(val), ha='center', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

# Year distribution
ax = axes[1][2]
if year_col is not None and year_col in df.columns:
    year_counts = df[year_col].value_counts().sort_index()
    ax.bar(year_counts.index, year_counts.values, color='#607D8B', alpha=0.8, edgecolor='white')
    ax.set_title('Observations by Year')
    ax.set_xlabel('Year')
    ax.set_ylabel('Count')
    ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/fig1_data_overview.png', bbox_inches='tight')
plt.close()
print('Figure 1 saved.')

# ============================================================
# FIGURE 2: Yield Trends Over Time
# ============================================================
if year_col is not None and yield_col is not None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Crop Yield Trends Over Time', fontsize=14, fontweight='bold')
    
    yearly_yield = df.groupby(year_col)[yield_col].agg(['mean', 'std', 'count']).reset_index()
    yearly_yield['se'] = yearly_yield['std'] / np.sqrt(yearly_yield['count'])
    
    ax = axes[0]
    ax.plot(yearly_yield[year_col], yearly_yield['mean'], 'b-o', linewidth=2, markersize=7)
    ax.fill_between(yearly_yield[year_col],
                    yearly_yield['mean'] - yearly_yield['se'],
                    yearly_yield['mean'] + yearly_yield['se'],
                    alpha=0.3, color='blue')
    ax.set_title('Mean Yield by Year (±SE)')
    ax.set_xlabel('Year')
    ax.set_ylabel(f'{yield_col}')
    ax.grid(True, alpha=0.3)
    
    # Yield by quota enforcement status
    ax = axes[1]
    if quota_col is not None and quota_col in df.columns:
        quota_vals = sorted(df[quota_col].unique())
        colors = ['#F44336', '#4CAF50', '#2196F3', '#FF9800']
        for i, qval in enumerate(quota_vals):
            subset = df[df[quota_col] == qval]
            yearly = subset.groupby(year_col)[yield_col].agg(['mean', 'std', 'count']).reset_index()
            yearly['se'] = yearly['std'] / np.sqrt(yearly['count'])
            label = f'Quota Enforced={qval}'
            ax.plot(yearly[year_col], yearly['mean'], marker='o', linewidth=2,
                    markersize=7, color=colors[i % len(colors)], label=label)
            ax.fill_between(yearly[year_col],
                            yearly['mean'] - yearly['se'],
                            yearly['mean'] + yearly['se'],
                            alpha=0.2, color=colors[i % len(colors)])
        ax.legend()
    ax.set_title('Mean Yield by Year and Quota Status')
    ax.set_xlabel('Year')
    ax.set_ylabel(f'{yield_col}')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig2_yield_trends.png', bbox_inches='tight')
    plt.close()
    print('Figure 2 saved.')

# ============================================================
# FIGURE 3: Irrigation Impact on Yield
# ============================================================
if irrig_col is not None and yield_col is not None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Irrigation Impact on Crop Yield', fontsize=14, fontweight='bold')
    
    ax = axes[0]
    if quota_col is not None and quota_col in df.columns:
        quota_vals = sorted(df[quota_col].unique())
        colors = ['#F44336', '#4CAF50', '#2196F3', '#FF9800']
        for i, qval in enumerate(quota_vals):
            subset = df[df[quota_col] == qval]
            label = f'Quota={qval}'
            ax.scatter(subset[irrig_col], subset[yield_col],
                      alpha=0.4, s=20, color=colors[i % len(colors)], label=label)
        ax.legend(fontsize=9)
    else:
        ax.scatter(df[irrig_col], df[yield_col], alpha=0.4, s=20, color='blue')
    
    valid = df[[irrig_col, yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[irrig_col], valid[yield_col])
    x_line = np.linspace(valid[irrig_col].min(), valid[irrig_col].max(), 100)
    ax.plot(x_line, slope * x_line + intercept, 'k--', linewidth=2,
            label=f'OLS: r={r_value:.3f}, p={p_value:.3f}')
    ax.set_title('Irrigation vs. Yield')
    ax.set_xlabel(irrig_col)
    ax.set_ylabel(yield_col)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # Binned irrigation vs yield
    ax = axes[1]
    try:
        df['irrig_bin'] = pd.qcut(df[irrig_col], q=5, labels=['Q1\n(Low)', 'Q2', 'Q3', 'Q4', 'Q5\n(High)'], duplicates='drop')
        bin_yield = df.groupby('irrig_bin', observed=True)[yield_col].agg(['mean', 'std', 'count']).reset_index()
        bin_yield['se'] = bin_yield['std'] / np.sqrt(bin_yield['count'])
        
        bars = ax.bar(range(len(bin_yield)), bin_yield['mean'],
                      yerr=bin_yield['se'], capsize=5,
                      color=['#1565C0', '#1976D2', '#1E88E5', '#42A5F5', '#90CAF9'][:len(bin_yield)],
                      alpha=0.8, edgecolor='white')
        ax.set_xticks(range(len(bin_yield)))
        ax.set_xticklabels(bin_yield['irrig_bin'])
        ax.set_title('Mean Yield by Irrigation Quintile')
        ax.set_xlabel('Irrigation Quintile')
        ax.set_ylabel(f'Mean {yield_col}')
        ax.grid(True, alpha=0.3, axis='y')
    except Exception as e:
        print(f'Binning error: {e}')
        ax.text(0.5, 0.5, 'Binning not available', ha='center', va='center', transform=ax.transAxes)
    
    plt.tight_layout()
    plt.savefig('report/images/fig3_irrigation_yield.png', bbox_inches='tight')
    plt.close()
    print('Figure 3 saved.')

# ============================================================
# FIGURE 4: Quota Enforcement Impact
# ============================================================
if quota_col is not None and quota_col in df.columns:
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle('Groundwater Quota Enforcement Impact', fontsize=14, fontweight='bold')
    
    quota_vals = sorted(df[quota_col].unique())
    colors = ['#F44336', '#4CAF50'] if len(quota_vals) == 2 else sns.color_palette('husl', len(quota_vals))
    
    # Yield by quota status
    ax = axes[0][0]
    quota_yield = df.groupby(quota_col)[yield_col].agg(['mean', 'std', 'count']).reset_index()
    quota_yield['se'] = quota_yield['std'] / np.sqrt(quota_yield['count'])
    bars = ax.bar(range(len(quota_yield)), quota_yield['mean'],
                  yerr=quota_yield['se'], capsize=5,
                  color=colors, alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(quota_yield)))
    ax.set_xticklabels([str(v) for v in quota_yield[quota_col]])
    ax.set_title('Mean Yield by Quota Status')
    ax.set_xlabel('Quota Enforced')
    ax.set_ylabel(f'Mean {yield_col}')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add significance annotation
    if len(quota_vals) == 2:
        g1 = df[df[quota_col] == quota_vals[0]][yield_col].dropna()
        g2 = df[df[quota_col] == quota_vals[1]][yield_col].dropna()
        t_stat, p_val = ttest_ind(g1, g2)
        sig = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else 'ns'))
        y_max = max(quota_yield['mean'] + quota_yield['se'])
        ax.annotate(f'p={p_val:.4f} {sig}', xy=(0.5, 0.95), xycoords='axes fraction',
                    ha='center', fontsize=11, color='darkred')
    
    # Irrigation by quota status
    if irrig_col is not None:
        ax = axes[0][1]
        quota_irrig = df.groupby(quota_col)[irrig_col].agg(['mean', 'std', 'count']).reset_index()
        quota_irrig['se'] = quota_irrig['std'] / np.sqrt(quota_irrig['count'])
        bars = ax.bar(range(len(quota_irrig)), quota_irrig['mean'],
                      yerr=quota_irrig['se'], capsize=5,
                      color=colors, alpha=0.8, edgecolor='white')
        ax.set_xticks(range(len(quota_irrig)))
        ax.set_xticklabels([str(v) for v in quota_irrig[quota_col]])
        ax.set_title('Mean Irrigation by Quota Status')
        ax.set_xlabel('Quota Enforced')
        ax.set_ylabel(f'Mean {irrig_col}')
        ax.grid(True, alpha=0.3, axis='y')
        
        if len(quota_vals) == 2:
            g1_i = df[df[quota_col] == quota_vals[0]][irrig_col].dropna()
            g2_i = df[df[quota_col] == quota_vals[1]][irrig_col].dropna()
            t_stat_i, p_val_i = ttest_ind(g1_i, g2_i)
            sig_i = '***' if p_val_i < 0.001 else ('**' if p_val_i < 0.01 else ('*' if p_val_i < 0.05 else 'ns'))
            ax.annotate(f'p={p_val_i:.4f} {sig_i}', xy=(0.5, 0.95), xycoords='axes fraction',
                        ha='center', fontsize=11, color='darkred')
    
    # Yield distribution by quota status
    ax = axes[1][0]
    for i, qval in enumerate(quota_vals):
        subset = df[df[quota_col] == qval][yield_col].dropna()
        label = f'Quota={qval}'
        ax.hist(subset, bins=25, alpha=0.6, label=label,
                color=colors[i] if isinstance(colors, list) else colors[i])
    ax.set_title('Yield Distribution by Quota Status')
    ax.set_xlabel(yield_col)
    ax.set_ylabel('Frequency')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Quota enforcement over time
    if year_col is not None:
        ax = axes[1][1]
        quota_time = df.groupby([year_col, quota_col]).size().unstack(fill_value=0)
        quota_time_pct = quota_time.div(quota_time.sum(axis=1), axis=0) * 100
        quota_time_pct.plot(kind='bar', ax=ax, color=colors, alpha=0.8, edgecolor='white')
        ax.set_title('Quota Enforcement Rate by Year')
        ax.set_xlabel('Year')
        ax.set_ylabel('Percentage (%)')
        ax.legend(title='Quota Status')
        ax.grid(True, alpha=0.3, axis='y')
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig('report/images/fig4_quota_impact.png', bbox_inches='tight')
    plt.close()
    print('Figure 4 saved.')

# ============================================================
# FIGURE 5: Rainfall and Irrigation Interaction
# ============================================================
if rain_col is not None and irrig_col is not None and yield_col is not None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Rainfall, Irrigation, and Yield Interactions', fontsize=14, fontweight='bold')
    
    # Rainfall vs yield
    ax = axes[0]
    ax.scatter(df[rain_col], df[yield_col], alpha=0.3, s=15, color='#2196F3')
    valid = df[[rain_col, yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[rain_col], valid[yield_col])
    x_line = np.linspace(valid[rain_col].min(), valid[rain_col].max(), 100)
    ax.plot(x_line, slope * x_line + intercept, 'r-', linewidth=2)
    ax.set_title('Rainfall vs. Yield')
    ax.set_xlabel(rain_col)
    ax.set_ylabel(yield_col)
    ax.text(0.05, 0.95, f'r = {r_value:.3f}\np = {p_value:.4f}',
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax.grid(True, alpha=0.3)
    
    # Rainfall vs irrigation
    ax = axes[1]
    ax.scatter(df[rain_col], df[irrig_col], alpha=0.3, s=15, color='#4CAF50')
    valid = df[[rain_col, irrig_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[rain_col], valid[irrig_col])
    x_line = np.linspace(valid[rain_col].min(), valid[rain_col].max(), 100)
    ax.plot(x_line, slope * x_line + intercept, 'r-', linewidth=2)
    ax.set_title('Rainfall vs. Irrigation')
    ax.set_xlabel(rain_col)
    ax.set_ylabel(irrig_col)
    ax.text(0.05, 0.95, f'r = {r_value:.3f}\np = {p_value:.4f}',
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax.grid(True, alpha=0.3)
    
    # Total water vs yield
    df['total_water'] = df[rain_col] + df[irrig_col]
    ax = axes[2]
    ax.scatter(df['total_water'], df[yield_col], alpha=0.3, s=15, color='#9C27B0')
    valid = df[['total_water', yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid['total_water'], valid[yield_col])
    x_line = np.linspace(valid['total_water'].min(), valid['total_water'].max(), 100)
    ax.plot(x_line, slope * x_line + intercept, 'r-', linewidth=2)
    ax.set_title('Total Water (Rain + Irrigation) vs. Yield')
    ax.set_xlabel('Total Water (mm)')
    ax.set_ylabel(yield_col)
    ax.text(0.05, 0.95, f'r = {r_value:.3f}\np = {p_value:.4f}',
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig5_water_yield.png', bbox_inches='tight')
    plt.close()
    print('Figure 5 saved.')

# ============================================================
# FIGURE 6: Correlation Matrix
# ============================================================
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols = [c for c in numeric_cols if 'bin' not in c.lower() and c != 'total_water']

if len(numeric_cols) >= 3:
    fig, ax = plt.subplots(figsize=(10, 8))
    corr_matrix = df[numeric_cols].corr()
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.3f',
                cmap='RdYlGn', center=0, ax=ax,
                square=True, linewidths=0.5,
                cbar_kws={'shrink': 0.8})
    ax.set_title('Correlation Matrix of Key Variables', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('report/images/fig6_correlation_matrix.png', bbox_inches='tight')
    plt.close()
    print('Figure 6 saved.')

# ============================================================
# FIGURE 7: Multiple Regression Analysis
# ============================================================
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import r2_score
    
    X_cols = [c for c in [irrig_col, rain_col, fert_col] if c is not None and c in df.columns]
    if len(X_cols) >= 2 and yield_col is not None:
        valid = df[X_cols + [yield_col]].dropna()
        
        scaler = StandardScaler()
        X = scaler.fit_transform(valid[X_cols])
        y = valid[yield_col].values
        
        reg = LinearRegression()
        reg.fit(X, y)
        
        coefs = reg.coef_
        r2 = reg.score(X, y)
        y_pred = reg.predict(X)
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('Multiple Regression Analysis', fontsize=14, fontweight='bold')
        
        # Standardized coefficients
        ax = axes[0]
        colors_coef = ['#2196F3', '#4CAF50', '#FF9800'][:len(X_cols)]
        bars = ax.barh(X_cols, coefs, color=colors_coef, alpha=0.8, edgecolor='white')
        ax.axvline(0, color='black', linewidth=1)
        ax.set_title(f'Standardized Regression Coefficients\n(R² = {r2:.3f})')
        ax.set_xlabel('Standardized Coefficient')
        ax.set_ylabel('Variable')
        ax.grid(True, alpha=0.3, axis='x')
        for bar, coef in zip(bars, coefs):
            ax.text(coef + (0.005 if coef >= 0 else -0.005), bar.get_y() + bar.get_height()/2,
                    f'{coef:.3f}', ha='left' if coef >= 0 else 'right', va='center', fontsize=10)
        
        # Predicted vs actual
        ax = axes[1]
        ax.scatter(y, y_pred, alpha=0.4, s=20, color='#1976D2')
        min_val = min(y.min(), y_pred.min())
        max_val = max(y.max(), y_pred.max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect fit')
        ax.set_title(f'Predicted vs. Actual Yield\n(R² = {r2:.3f})')
        ax.set_xlabel('Actual Yield')
        ax.set_ylabel('Predicted Yield')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('report/images/fig7_regression.png', bbox_inches='tight')
        plt.close()
        print('Figure 7 saved.')
        
        # Save regression results
        with open('outputs/regression_results.txt', 'w') as f:
            f.write('=== MULTIPLE REGRESSION RESULTS ===\n\n')
            f.write(f'Dependent variable: {yield_col}\n')
            f.write(f'Independent variables: {X_cols}\n')
            f.write(f'N = {len(valid)}\n')
            f.write(f'R² = {r2:.4f}\n\n')
            f.write('Standardized Coefficients:\n')
            for col, coef in zip(X_cols, coefs):
                f.write(f'  {col}: {coef:.4f}\n')
except ImportError:
    print('sklearn not available, skipping regression figure')

# ============================================================
# FIGURE 8: Panel Fixed Effects Visualization
# ============================================================
if field_col is not None and year_col is not None and yield_col is not None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Panel Structure: Field and Year Effects', fontsize=14, fontweight='bold')
    
    # Field-level yield variation
    ax = axes[0]
    field_yield = df.groupby(field_col)[yield_col].agg(['mean', 'std']).reset_index()
    field_yield = field_yield.sort_values('mean')
    
    if len(field_yield) > 30:
        field_yield_plot = pd.concat([field_yield.head(15), field_yield.tail(15)])
    else:
        field_yield_plot = field_yield
    
    ax.barh(range(len(field_yield_plot)), field_yield_plot['mean'],
            xerr=field_yield_plot['std'], capsize=3,
            color='#1976D2', alpha=0.7, edgecolor='white')
    ax.set_yticks(range(len(field_yield_plot)))
    ax.set_yticklabels([str(f) for f in field_yield_plot[field_col]], fontsize=8)
    ax.set_title('Mean Yield by Field (±SD)')
    ax.set_xlabel(yield_col)
    ax.set_ylabel('Field ID')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Year fixed effects
    ax = axes[1]
    year_yield = df.groupby(year_col)[yield_col].agg(['mean', 'std', 'count']).reset_index()
    year_yield['se'] = year_yield['std'] / np.sqrt(year_yield['count'])
    
    ax.bar(year_yield[year_col], year_yield['mean'],
           yerr=year_yield['se'], capsize=5,
           color='#388E3C', alpha=0.8, edgecolor='white')
    ax.set_title('Mean Yield by Year (±SE)')
    ax.set_xlabel('Year')
    ax.set_ylabel(f'Mean {yield_col}')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('report/images/fig8_panel_structure.png', bbox_inches='tight')
    plt.close()
    print('Figure 8 saved.')

# ============================================================
# STATISTICAL ANALYSIS SUMMARY
# ============================================================
results = {}

# Irrigation-Yield
if irrig_col is not None and yield_col is not None:
    valid = df[[irrig_col, yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[irrig_col], valid[yield_col])
    results['irrigation_yield'] = {'r': r_value, 'p': p_value, 'slope': slope, 'n': len(valid)}

# Rainfall-Yield
if rain_col is not None and yield_col is not None:
    valid = df[[rain_col, yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[rain_col], valid[yield_col])
    results['rainfall_yield'] = {'r': r_value, 'p': p_value, 'slope': slope, 'n': len(valid)}

# Fertilizer-Yield
if fert_col is not None and yield_col is not None:
    valid = df[[fert_col, yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[fert_col], valid[yield_col])
    results['fertilizer_yield'] = {'r': r_value, 'p': p_value, 'slope': slope, 'n': len(valid)}

# Quota enforcement impact
if quota_col is not None and quota_col in df.columns and yield_col is not None:
    quota_vals = sorted(df[quota_col].unique())
    if len(quota_vals) == 2:
        g1 = df[df[quota_col] == quota_vals[0]][yield_col].dropna()
        g2 = df[df[quota_col] == quota_vals[1]][yield_col].dropna()
        t_stat, p_val = ttest_ind(g1, g2)
        results['quota_yield'] = {
            'group1_mean': g1.mean(), 'group2_mean': g2.mean(),
            'diff': g2.mean() - g1.mean(),
            't': t_stat, 'p': p_val,
            'n1': len(g1), 'n2': len(g2)
        }
        
        if irrig_col is not None:
            g1_i = df[df[quota_col] == quota_vals[0]][irrig_col].dropna()
            g2_i = df[df[quota_col] == quota_vals[1]][irrig_col].dropna()
            t_stat_i, p_val_i = ttest_ind(g1_i, g2_i)
            results['quota_irrigation'] = {
                'group1_mean': g1_i.mean(), 'group2_mean': g2_i.mean(),
                'diff': g2_i.mean() - g1_i.mean(),
                't': t_stat_i, 'p': p_val_i
            }

# Save results
with open('outputs/statistical_results.txt', 'w') as f:
    f.write('=== STATISTICAL ANALYSIS RESULTS ===\n\n')
    for key, val in results.items():
        f.write(f'{key}:\n')
        for k, v in val.items():
            f.write(f'  {k}: {v}\n')
        f.write('\n')
    
    f.write('\n=== DESCRIPTIVE STATISTICS BY QUOTA STATUS ===\n')
    if quota_col is not None and quota_col in df.columns:
        for qval in sorted(df[quota_col].unique()):
            subset = df[df[quota_col] == qval]
            f.write(f'\nQuota={qval} (n={len(subset)}):\n')
            for col in [yield_col, irrig_col, fert_col, rain_col]:
                if col is not None and col in df.columns:
                    f.write(f'  {col}: mean={subset[col].mean():.2f}, std={subset[col].std():.2f}, min={subset[col].min():.2f}, max={subset[col].max():.2f}\n')

print('Statistical results saved.')
print('\nAll analysis complete!')
