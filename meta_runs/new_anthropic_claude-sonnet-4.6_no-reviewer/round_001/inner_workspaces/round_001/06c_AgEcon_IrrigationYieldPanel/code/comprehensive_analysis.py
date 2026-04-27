#!/usr/bin/env python3
"""
Irrigation Impact Analysis - Comprehensive Analysis
Field-Year Panel Data Analysis
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, spearmanr, ttest_ind
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
print('Loading data...')
df = pd.read_csv('data/field_year_panel.csv')

print('Shape:', df.shape)
print('Columns:', df.columns.tolist())

# Based on the data overview, identify key columns
# The data has: field_id, year, yield_kg_ha, irrigation_mm, fertilizer_kg_ha, 
# rainfall_mm, quota_enforced (or similar)

# Let's check what we have
cols = df.columns.tolist()
print('All columns:', cols)

# Identify columns by type
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
    if 'irrig' in cl:
        irrig_col = col
    if 'fert' in cl or 'nitrogen' in cl:
        fert_col = col
    if 'rain' in cl or 'precip' in cl:
        rain_col = col
    if 'quota' in cl or 'enforce' in cl or 'gw_quota' in cl:
        quota_col = col
    if 'year' in cl:
        year_col = col
    if 'field' in cl or ('id' in cl and 'field' in cl):
        field_col = col

# If field_col not found, look for id-like columns
if field_col is None:
    for col in cols:
        if col.lower() in ['id', 'field_id', 'plot_id', 'farm_id']:
            field_col = col
            break
    if field_col is None and len(cols) > 0:
        # Use first column as field identifier
        field_col = cols[0]

print(f'\nIdentified columns:')
print(f'  Yield: {yield_col}')
print(f'  Irrigation: {irrig_col}')
print(f'  Fertilizer: {fert_col}')
print(f'  Rainfall: {rain_col}')
print(f'  Quota: {quota_col}')
print(f'  Year: {year_col}')
print(f'  Field: {field_col}')

# Save column mapping
with open('outputs/column_mapping.txt', 'w') as f:
    f.write('Column Mapping:\n')
    f.write(f'  Yield: {yield_col}\n')
    f.write(f'  Irrigation: {irrig_col}\n')
    f.write(f'  Fertilizer: {fert_col}\n')
    f.write(f'  Rainfall: {rain_col}\n')
    f.write(f'  Quota: {quota_col}\n')
    f.write(f'  Year: {year_col}\n')
    f.write(f'  Field: {field_col}\n')

# ============================================================
# FIGURE 1: Data Overview - Distribution of Key Variables
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Distribution of Key Variables in Field-Year Panel', fontsize=15, fontweight='bold')

plot_vars = [yield_col, irrig_col, fert_col, rain_col]
plot_titles = ['Crop Yield', 'Irrigation Applied', 'Fertilizer Applied', 'Rainfall']
plot_colors = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0']

for i, (var, title, color) in enumerate(zip(plot_vars, plot_titles, plot_colors)):
    if var is not None and var in df.columns:
        ax = axes[i // 3][i % 3]
        data = df[var].dropna()
        ax.hist(data, bins=30, color=color, alpha=0.7, edgecolor='white')
        ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {data.mean():.1f}')
        ax.axvline(data.median(), color='orange', linestyle='--', linewidth=2, label=f'Median: {data.median():.1f}')
        ax.set_title(title)
        ax.set_xlabel(var)
        ax.set_ylabel('Frequency')
        ax.legend(fontsize=9)

# Quota distribution
if quota_col is not None and quota_col in df.columns:
    ax = axes[1][1]
    quota_counts = df[quota_col].value_counts()
    ax.bar(quota_counts.index.astype(str), quota_counts.values, color=['#F44336', '#4CAF50'], alpha=0.8)
    ax.set_title('Groundwater Quota Enforcement')
    ax.set_xlabel(quota_col)
    ax.set_ylabel('Count')
    for j, (idx, val) in enumerate(quota_counts.items()):
        ax.text(j, val + 5, str(val), ha='center', fontsize=10)

# Year distribution
if year_col is not None and year_col in df.columns:
    ax = axes[1][2]
    year_counts = df[year_col].value_counts().sort_index()
    ax.bar(year_counts.index, year_counts.values, color='#607D8B', alpha=0.8)
    ax.set_title('Observations by Year')
    ax.set_xlabel('Year')
    ax.set_ylabel('Count')

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
    
    # Mean yield by year
    yearly_yield = df.groupby(year_col)[yield_col].agg(['mean', 'std', 'count']).reset_index()
    yearly_yield['se'] = yearly_yield['std'] / np.sqrt(yearly_yield['count'])
    
    ax = axes[0]
    ax.plot(yearly_yield[year_col], yearly_yield['mean'], 'b-o', linewidth=2, markersize=6)
    ax.fill_between(yearly_yield[year_col], 
                    yearly_yield['mean'] - yearly_yield['se'],
                    yearly_yield['mean'] + yearly_yield['se'],
                    alpha=0.3, color='blue')
    ax.set_title('Mean Yield by Year (±SE)')
    ax.set_xlabel('Year')
    ax.set_ylabel(f'{yield_col}')
    ax.grid(True, alpha=0.3)
    
    # Yield by quota enforcement status
    if quota_col is not None and quota_col in df.columns:
        ax = axes[1]
        quota_vals = df[quota_col].unique()
        colors = ['#F44336', '#4CAF50', '#2196F3', '#FF9800']
        
        for i, qval in enumerate(sorted(quota_vals)):
            subset = df[df[quota_col] == qval]
            yearly = subset.groupby(year_col)[yield_col].mean().reset_index()
            label = f'Quota={qval}' if not isinstance(qval, bool) else ('Enforced' if qval else 'Not Enforced')
            ax.plot(yearly[year_col], yearly[yield_col], 
                   marker='o', linewidth=2, markersize=6,
                   color=colors[i % len(colors)], label=label)
        
        ax.set_title('Mean Yield by Year and Quota Status')
        ax.set_xlabel('Year')
        ax.set_ylabel(f'{yield_col}')
        ax.legend()
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
    
    # Scatter plot: irrigation vs yield
    ax = axes[0]
    if quota_col is not None and quota_col in df.columns:
        quota_vals = sorted(df[quota_col].unique())
        colors = ['#F44336', '#4CAF50', '#2196F3', '#FF9800']
        for i, qval in enumerate(quota_vals):
            subset = df[df[quota_col] == qval]
            label = f'Quota={qval}' if not isinstance(qval, bool) else ('Enforced' if qval else 'Not Enforced')
            ax.scatter(subset[irrig_col], subset[yield_col], 
                      alpha=0.4, s=20, color=colors[i % len(colors)], label=label)
        ax.legend()
    else:
        ax.scatter(df[irrig_col], df[yield_col], alpha=0.4, s=20, color='blue')
    
    # Add regression line
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
    df['irrig_bin'] = pd.qcut(df[irrig_col], q=5, labels=['Q1\n(Low)', 'Q2', 'Q3', 'Q4', 'Q5\n(High)'])
    bin_yield = df.groupby('irrig_bin')[yield_col].agg(['mean', 'std', 'count']).reset_index()
    bin_yield['se'] = bin_yield['std'] / np.sqrt(bin_yield['count'])
    
    bars = ax.bar(range(len(bin_yield)), bin_yield['mean'], 
                  yerr=bin_yield['se'], capsize=5,
                  color=['#1565C0', '#1976D2', '#1E88E5', '#42A5F5', '#90CAF9'],
                  alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(bin_yield)))
    ax.set_xticklabels(bin_yield['irrig_bin'])
    ax.set_title('Mean Yield by Irrigation Quintile')
    ax.set_xlabel('Irrigation Quintile')
    ax.set_ylabel(f'Mean {yield_col}')
    ax.grid(True, alpha=0.3, axis='y')
    
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
    
    # Yield by quota status
    ax = axes[0][0]
    quota_yield = df.groupby(quota_col)[yield_col].agg(['mean', 'std', 'count']).reset_index()
    quota_yield['se'] = quota_yield['std'] / np.sqrt(quota_yield['count'])
    colors = ['#F44336', '#4CAF50'] if len(quota_vals) == 2 else sns.color_palette('husl', len(quota_vals))
    bars = ax.bar(range(len(quota_yield)), quota_yield['mean'],
                  yerr=quota_yield['se'], capsize=5,
                  color=colors, alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(quota_yield)))
    ax.set_xticklabels([str(v) for v in quota_yield[quota_col]])
    ax.set_title('Mean Yield by Quota Status')
    ax.set_xlabel('Quota Enforced')
    ax.set_ylabel(f'Mean {yield_col}')
    ax.grid(True, alpha=0.3, axis='y')
    
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
    ax.plot(x_line, slope * x_line + intercept, 'r--', linewidth=2,
            label=f'r={r_value:.3f}, p={p_value:.3f}')
    ax.set_title('Rainfall vs. Yield')
    ax.set_xlabel(rain_col)
    ax.set_ylabel(yield_col)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Rainfall vs irrigation
    ax = axes[1]
    ax.scatter(df[rain_col], df[irrig_col], alpha=0.3, s=15, color='#4CAF50')
    valid = df[[rain_col, irrig_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[rain_col], valid[irrig_col])
    x_line = np.linspace(valid[rain_col].min(), valid[rain_col].max(), 100)
    ax.plot(x_line, slope * x_line + intercept, 'r--', linewidth=2,
            label=f'r={r_value:.3f}, p={p_value:.3f}')
    ax.set_title('Rainfall vs. Irrigation')
    ax.set_xlabel(rain_col)
    ax.set_ylabel(irrig_col)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Total water (rain + irrigation) vs yield
    df['total_water'] = df[rain_col] + df[irrig_col]
    ax = axes[2]
    ax.scatter(df['total_water'], df[yield_col], alpha=0.3, s=15, color='#9C27B0')
    valid = df[['total_water', yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid['total_water'], valid[yield_col])
    x_line = np.linspace(valid['total_water'].min(), valid['total_water'].max(), 100)
    ax.plot(x_line, slope * x_line + intercept, 'r--', linewidth=2,
            label=f'r={r_value:.3f}, p={p_value:.3f}')
    ax.set_title('Total Water (Rain + Irrigation) vs. Yield')
    ax.set_xlabel('Total Water (mm)')
    ax.set_ylabel(yield_col)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig5_water_yield.png', bbox_inches='tight')
    plt.close()
    print('Figure 5 saved.')

# ============================================================
# FIGURE 6: Fertilizer Impact
# ============================================================
if fert_col is not None and yield_col is not None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Fertilizer Impact on Crop Yield', fontsize=14, fontweight='bold')
    
    # Scatter: fertilizer vs yield
    ax = axes[0]
    if quota_col is not None and quota_col in df.columns:
        quota_vals = sorted(df[quota_col].unique())
        colors = ['#F44336', '#4CAF50', '#2196F3', '#FF9800']
        for i, qval in enumerate(quota_vals):
            subset = df[df[quota_col] == qval]
            label = f'Quota={qval}'
            ax.scatter(subset[fert_col], subset[yield_col], 
                      alpha=0.4, s=20, color=colors[i % len(colors)], label=label)
        ax.legend(fontsize=9)
    else:
        ax.scatter(df[fert_col], df[yield_col], alpha=0.4, s=20, color='#FF9800')
    
    valid = df[[fert_col, yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[fert_col], valid[yield_col])
    x_line = np.linspace(valid[fert_col].min(), valid[fert_col].max(), 100)
    ax.plot(x_line, slope * x_line + intercept, 'k--', linewidth=2,
            label=f'OLS: r={r_value:.3f}, p={p_value:.3f}')
    ax.set_title('Fertilizer vs. Yield')
    ax.set_xlabel(fert_col)
    ax.set_ylabel(yield_col)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    
    # Binned fertilizer vs yield
    ax = axes[1]
    df['fert_bin'] = pd.qcut(df[fert_col], q=5, labels=['Q1\n(Low)', 'Q2', 'Q3', 'Q4', 'Q5\n(High)'])
    bin_yield = df.groupby('fert_bin')[yield_col].agg(['mean', 'std', 'count']).reset_index()
    bin_yield['se'] = bin_yield['std'] / np.sqrt(bin_yield['count'])
    
    bars = ax.bar(range(len(bin_yield)), bin_yield['mean'],
                  yerr=bin_yield['se'], capsize=5,
                  color=['#E65100', '#F57C00', '#FB8C00', '#FFA726', '#FFCC02'],
                  alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(bin_yield)))
    ax.set_xticklabels(bin_yield['fert_bin'])
    ax.set_title('Mean Yield by Fertilizer Quintile')
    ax.set_xlabel('Fertilizer Quintile')
    ax.set_ylabel(f'Mean {yield_col}')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('report/images/fig6_fertilizer_yield.png', bbox_inches='tight')
    plt.close()
    print('Figure 6 saved.')

# ============================================================
# FIGURE 7: Correlation Matrix
# ============================================================
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
# Remove bin columns
numeric_cols = [c for c in numeric_cols if 'bin' not in c.lower()]

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
    plt.savefig('report/images/fig7_correlation_matrix.png', bbox_inches='tight')
    plt.close()
    print('Figure 7 saved.')

# ============================================================
# FIGURE 8: Panel Fixed Effects Analysis
# ============================================================
if field_col is not None and year_col is not None and yield_col is not None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Panel Structure and Fixed Effects', fontsize=14, fontweight='bold')
    
    # Field-level yield variation
    ax = axes[0]
    field_yield = df.groupby(field_col)[yield_col].agg(['mean', 'std']).reset_index()
    field_yield = field_yield.sort_values('mean')
    
    # Show top/bottom fields if too many
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
# STATISTICAL ANALYSIS
# ============================================================
results = {}

# 1. Irrigation-Yield correlation
if irrig_col is not None and yield_col is not None:
    valid = df[[irrig_col, yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[irrig_col], valid[yield_col])
    results['irrigation_yield_r'] = r_value
    results['irrigation_yield_p'] = p_value
    results['irrigation_yield_slope'] = slope
    print(f'\nIrrigation-Yield: r={r_value:.4f}, p={p_value:.4f}, slope={slope:.4f}')

# 2. Rainfall-Yield correlation
if rain_col is not None and yield_col is not None:
    valid = df[[rain_col, yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[rain_col], valid[yield_col])
    results['rainfall_yield_r'] = r_value
    results['rainfall_yield_p'] = p_value
    results['rainfall_yield_slope'] = slope
    print(f'Rainfall-Yield: r={r_value:.4f}, p={p_value:.4f}, slope={slope:.4f}')

# 3. Fertilizer-Yield correlation
if fert_col is not None and yield_col is not None:
    valid = df[[fert_col, yield_col]].dropna()
    slope, intercept, r_value, p_value, std_err = stats.linregress(valid[fert_col], valid[yield_col])
    results['fertilizer_yield_r'] = r_value
    results['fertilizer_yield_p'] = p_value
    results['fertilizer_yield_slope'] = slope
    print(f'Fertilizer-Yield: r={r_value:.4f}, p={p_value:.4f}, slope={slope:.4f}')

# 4. Quota enforcement impact
if quota_col is not None and quota_col in df.columns and yield_col is not None:
    quota_vals = sorted(df[quota_col].unique())
    if len(quota_vals) == 2:
        group1 = df[df[quota_col] == quota_vals[0]][yield_col].dropna()
        group2 = df[df[quota_col] == quota_vals[1]][yield_col].dropna()
        t_stat, p_val = ttest_ind(group1, group2)
        results['quota_yield_tstat'] = t_stat
        results['quota_yield_p'] = p_val
        results['quota_yield_diff'] = group2.mean() - group1.mean()
        print(f'Quota enforcement yield difference: {results["quota_yield_diff"]:.2f}')
        print(f'T-test: t={t_stat:.4f}, p={p_val:.4f}')
        
        # Also check irrigation difference
        if irrig_col is not None:
            group1_irrig = df[df[quota_col] == quota_vals[0]][irrig_col].dropna()
            group2_irrig = df[df[quota_col] == quota_vals[1]][irrig_col].dropna()
            t_stat_i, p_val_i = ttest_ind(group1_irrig, group2_irrig)
            results['quota_irrig_tstat'] = t_stat_i
            results['quota_irrig_p'] = p_val_i
            results['quota_irrig_diff'] = group2_irrig.mean() - group1_irrig.mean()
            print(f'Quota enforcement irrigation difference: {results["quota_irrig_diff"]:.2f}')
            print(f'T-test: t={t_stat_i:.4f}, p={p_val_i:.4f}')

# Save statistical results
with open('outputs/statistical_results.txt', 'w') as f:
    f.write('=== STATISTICAL ANALYSIS RESULTS ===\n\n')
    for key, val in results.items():
        f.write(f'{key}: {val}\n')
    
    f.write('\n=== DESCRIPTIVE STATISTICS BY QUOTA STATUS ===\n')
    if quota_col is not None and quota_col in df.columns:
        for qval in sorted(df[quota_col].unique()):
            subset = df[df[quota_col] == qval]
            f.write(f'\nQuota={qval} (n={len(subset)}):\n')
            for col in [yield_col, irrig_col, fert_col, rain_col]:
                if col is not None and col in df.columns:
                    f.write(f'  {col}: mean={subset[col].mean():.2f}, std={subset[col].std():.2f}\n')

print('\nStatistical results saved.')

# ============================================================
# FIGURE 9: Regression Analysis Summary
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
fig.suptitle('Regression Analysis: Determinants of Crop Yield', fontsize=14, fontweight='bold')

plot_pairs = [
    (irrig_col, yield_col, 'Irrigation vs. Yield', '#2196F3'),
    (rain_col, yield_col, 'Rainfall vs. Yield', '#4CAF50'),
    (fert_col, yield_col, 'Fertilizer vs. Yield', '#FF9800'),
]

for i, (x_col, y_col, title, color) in enumerate(plot_pairs):
    if x_col is not None and y_col is not None and x_col in df.columns and y_col in df.columns:
        ax = axes[i // 2][i % 2]
        valid = df[[x_col, y_col]].dropna()
        
        ax.scatter(valid[x_col], valid[y_col], alpha=0.3, s=15, color=color)
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(valid[x_col], valid[y_col])
        x_line = np.linspace(valid[x_col].min(), valid[x_col].max(), 100)
        ax.plot(x_line, slope * x_line + intercept, 'k-', linewidth=2)
        
        ax.set_title(title)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.text(0.05, 0.95, f'r = {r_value:.3f}\np = {p_value:.4f}\nslope = {slope:.3f}',
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax.grid(True, alpha=0.3)

# Multiple regression summary
ax = axes[1][1]
if all(c is not None and c in df.columns for c in [irrig_col, rain_col, fert_col, yield_col]):
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    
    X_cols = [c for c in [irrig_col, rain_col, fert_col] if c is not None and c in df.columns]
    valid = df[X_cols + [yield_col]].dropna()
    
    scaler = StandardScaler()
    X = scaler.fit_transform(valid[X_cols])
    y = valid[yield_col].values
    
    reg = LinearRegression()
    reg.fit(X, y)
    
    coefs = reg.coef_
    r2 = reg.score(X, y)
    
    bars = ax.barh(X_cols, coefs, color=['#2196F3', '#4CAF50', '#FF9800'][:len(X_cols)], alpha=0.8)
    ax.axvline(0, color='black', linewidth=1)
    ax.set_title(f'Standardized Regression Coefficients\n(R² = {r2:.3f})')
    ax.set_xlabel('Standardized Coefficient')
    ax.set_ylabel('Variable')
    ax.grid(True, alpha=0.3, axis='x')
    
    for bar, coef in zip(bars, coefs):
        ax.text(coef + (0.01 if coef >= 0 else -0.01), bar.get_y() + bar.get_height()/2,
                f'{coef:.3f}', ha='left' if coef >= 0 else 'right', va='center')

plt.tight_layout()
plt.savefig('report/images/fig9_regression_analysis.png', bbox_inches='tight')
plt.close()
print('Figure 9 saved.')

# ============================================================
# FIGURE 10: Difference-in-Differences Analysis
# ============================================================
if quota_col is not None and quota_col in df.columns and year_col is not None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Difference-in-Differences: Quota Enforcement Effects', fontsize=14, fontweight='bold')
    
    quota_vals = sorted(df[quota_col].unique())
    colors = ['#F44336', '#4CAF50']
    
    # Yield over time by quota status
    ax = axes[0]
    for i, qval in enumerate(quota_vals):
        subset = df[df[quota_col] == qval]
        yearly = subset.groupby(year_col)[yield_col].agg(['mean', 'std', 'count']).reset_index()
        yearly['se'] = yearly['std'] / np.sqrt(yearly['count'])
        label = f'Quota={qval}'
        ax.plot(yearly[year_col], yearly['mean'], marker='o', linewidth=2, 
                color=colors[i % len(colors)], label=label)
        ax.fill_between(yearly[year_col],
                        yearly['mean'] - yearly['se'],
                        yearly['mean'] + yearly['se'],
                        alpha=0.2, color=colors[i % len(colors)])
    ax.set_title('Yield Trends by Quota Status')
    ax.set_xlabel('Year')
    ax.set_ylabel(f'Mean {yield_col}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Irrigation over time by quota status
    if irrig_col is not None:
        ax = axes[1]
        for i, qval in enumerate(quota_vals):
            subset = df[df[quota_col] == qval]
            yearly = subset.groupby(year_col)[irrig_col].agg(['mean', 'std', 'count']).reset_index()
            yearly['se'] = yearly['std'] / np.sqrt(yearly['count'])
            label = f'Quota={qval}'
            ax.plot(yearly[year_col], yearly['mean'], marker='o', linewidth=2,
                    color=colors[i % len(colors)], label=label)
            ax.fill_between(yearly[year_col],
                            yearly['mean'] - yearly['se'],
                            yearly['mean'] + yearly['se'],
                            alpha=0.2, color=colors[i % len(colors)])
        ax.set_title('Irrigation Trends by Quota Status')
        ax.set_xlabel('Year')
        ax.set_ylabel(f'Mean {irrig_col}')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig10_did_analysis.png', bbox_inches='tight')
    plt.close()
    print('Figure 10 saved.')

print('\nAll figures saved!')
print('Analysis complete!')
