#!/usr/bin/env python3
"""
Irrigation Impact Analysis - Final Analysis
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
import os
import traceback

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

# Column names
field_col = 'field_id'
year_col = 'year'
yield_col = 'yield_kg_ha'
irrig_col = 'irrigation_mm'
fert_col = 'fertilizer_kg_ha'
rain_col = 'rainfall_mm'
quota_col = 'quota_enforced'

print('Data loaded:', df.shape)
print('Columns:', list(df.columns))
print(df.describe())

# Save descriptive stats
with open('outputs/descriptive_stats.txt', 'w') as f:
    f.write('=== DESCRIPTIVE STATISTICS ===\n\n')
    f.write(f'Total observations: {len(df)}\n')
    f.write(f'Fields: {df[field_col].nunique()}\n')
    f.write(f'Years: {df[year_col].min()} - {df[year_col].max()}\n')
    f.write(f'\nOverall stats:\n{df.describe()}\n')
    f.write(f'\nBy quota status:\n')
    for qval in sorted(df[quota_col].unique()):
        subset = df[df[quota_col] == qval]
        f.write(f'\nQuota={qval} (n={len(subset)}):\n')
        f.write(str(subset[[yield_col, irrig_col, fert_col, rain_col]].describe()) + '\n')

print('Descriptive stats saved.')

# ============================================================
# FIGURE 1: Data Overview - Distribution of Key Variables
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle('Field-Year Panel: Distribution of Key Variables', fontsize=15, fontweight='bold')

# Yield distribution
ax = axes[0][0]
data = df[yield_col].dropna()
ax.hist(data, bins=30, color='#2196F3', alpha=0.7, edgecolor='white')
ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {data.mean():.0f}')
ax.axvline(data.median(), color='orange', linestyle=':', linewidth=2, label=f'Median: {data.median():.0f}')
ax.set_title('Crop Yield (kg/ha)')
ax.set_xlabel('Yield (kg/ha)')
ax.set_ylabel('Frequency')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Irrigation distribution
ax = axes[0][1]
data = df[irrig_col].dropna()
ax.hist(data, bins=30, color='#4CAF50', alpha=0.7, edgecolor='white')
ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {data.mean():.0f}')
ax.axvline(data.median(), color='orange', linestyle=':', linewidth=2, label=f'Median: {data.median():.0f}')
ax.set_title('Irrigation Applied (mm)')
ax.set_xlabel('Irrigation (mm)')
ax.set_ylabel('Frequency')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Fertilizer distribution
ax = axes[0][2]
data = df[fert_col].dropna()
ax.hist(data, bins=30, color='#FF9800', alpha=0.7, edgecolor='white')
ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {data.mean():.0f}')
ax.axvline(data.median(), color='orange', linestyle=':', linewidth=2, label=f'Median: {data.median():.0f}')
ax.set_title('Fertilizer Applied (kg/ha)')
ax.set_xlabel('Fertilizer (kg/ha)')
ax.set_ylabel('Frequency')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Rainfall distribution
ax = axes[1][0]
data = df[rain_col].dropna()
ax.hist(data, bins=30, color='#9C27B0', alpha=0.7, edgecolor='white')
ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {data.mean():.0f}')
ax.axvline(data.median(), color='orange', linestyle=':', linewidth=2, label=f'Median: {data.median():.0f}')
ax.set_title('Rainfall (mm)')
ax.set_xlabel('Rainfall (mm)')
ax.set_ylabel('Frequency')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Quota enforcement distribution
ax = axes[1][1]
quota_counts = df[quota_col].value_counts().sort_index()
colors_bar = ['#F44336', '#4CAF50']
bars = ax.bar(['Not Enforced (0)', 'Enforced (1)'], quota_counts.values,
              color=colors_bar, alpha=0.8, edgecolor='white')
ax.set_title('Groundwater Quota Enforcement')
ax.set_xlabel('Quota Status')
ax.set_ylabel('Count')
for j, val in enumerate(quota_counts.values):
    ax.text(j, val + max(quota_counts.values)*0.01, str(val), ha='center', fontsize=11, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# Year distribution
ax = axes[1][2]
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
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Crop Yield Trends Over Time', fontsize=14, fontweight='bold')

# Overall yield trend
ax = axes[0]
yearly_yield = df.groupby(year_col)[yield_col].agg(['mean', 'std', 'count']).reset_index()
yearly_yield['se'] = yearly_yield['std'] / np.sqrt(yearly_yield['count'])
ax.plot(yearly_yield[year_col], yearly_yield['mean'], 'b-o', linewidth=2, markersize=7)
ax.fill_between(yearly_yield[year_col],
                yearly_yield['mean'] - yearly_yield['se'],
                yearly_yield['mean'] + yearly_yield['se'],
                alpha=0.3, color='blue')
ax.set_title('Mean Yield by Year (±SE)')
ax.set_xlabel('Year')
ax.set_ylabel('Yield (kg/ha)')
ax.grid(True, alpha=0.3)

# Yield by quota status over time
ax = axes[1]
quota_vals = sorted(df[quota_col].unique())
colors = ['#F44336', '#4CAF50']
for i, qval in enumerate(quota_vals):
    subset = df[df[quota_col] == qval]
    yearly = subset.groupby(year_col)[yield_col].agg(['mean', 'std', 'count']).reset_index()
    yearly['se'] = yearly['std'] / np.sqrt(yearly['count'])
    label = f'Quota Enforced={qval}'
    ax.plot(yearly[year_col], yearly['mean'], marker='o', linewidth=2,
            markersize=7, color=colors[i], label=label)
    ax.fill_between(yearly[year_col],
                    yearly['mean'] - yearly['se'],
                    yearly['mean'] + yearly['se'],
                    alpha=0.2, color=colors[i])
ax.set_title('Mean Yield by Year and Quota Status')
ax.set_xlabel('Year')
ax.set_ylabel('Yield (kg/ha)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig2_yield_trends.png', bbox_inches='tight')
plt.close()
print('Figure 2 saved.')

# ============================================================
# FIGURE 3: Irrigation Impact on Yield
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Irrigation Impact on Crop Yield', fontsize=14, fontweight='bold')

# Scatter: irrigation vs yield by quota status
ax = axes[0]
quota_vals = sorted(df[quota_col].unique())
colors = ['#F44336', '#4CAF50']
for i, qval in enumerate(quota_vals):
    subset = df[df[quota_col] == qval]
    label = f'Quota={qval}'
    ax.scatter(subset[irrig_col], subset[yield_col],
              alpha=0.4, s=20, color=colors[i], label=label)
ax.legend(fontsize=10)

valid = df[[irrig_col, yield_col]].dropna()
slope, intercept, r_value, p_value, std_err = stats.linregress(valid[irrig_col], valid[yield_col])
x_line = np.linspace(valid[irrig_col].min(), valid[irrig_col].max(), 100)
ax.plot(x_line, slope * x_line + intercept, 'k--', linewidth=2,
        label=f'OLS: r={r_value:.3f}')
ax.set_title('Irrigation vs. Yield')
ax.set_xlabel('Irrigation (mm)')
ax.set_ylabel('Yield (kg/ha)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Binned irrigation vs yield
ax = axes[1]
try:
    df['irrig_bin'] = pd.qcut(df[irrig_col], q=5, 
                               labels=['Q1\n(Low)', 'Q2', 'Q3', 'Q4', 'Q5\n(High)'],
                               duplicates='drop')
    bin_yield = df.groupby('irrig_bin', observed=True)[yield_col].agg(['mean', 'std', 'count']).reset_index()
    bin_yield['se'] = bin_yield['std'] / np.sqrt(bin_yield['count'])
    
    bar_colors = ['#1565C0', '#1976D2', '#1E88E5', '#42A5F5', '#90CAF9']
    bars = ax.bar(range(len(bin_yield)), bin_yield['mean'],
                  yerr=bin_yield['se'], capsize=5,
                  color=bar_colors[:len(bin_yield)],
                  alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(bin_yield)))
    ax.set_xticklabels(bin_yield['irrig_bin'])
    ax.set_title('Mean Yield by Irrigation Quintile')
    ax.set_xlabel('Irrigation Quintile')
    ax.set_ylabel('Mean Yield (kg/ha)')
    ax.grid(True, alpha=0.3, axis='y')
except Exception as e:
    print(f'Binning error: {e}')

plt.tight_layout()
plt.savefig('report/images/fig3_irrigation_yield.png', bbox_inches='tight')
plt.close()
print('Figure 3 saved.')

# ============================================================
# FIGURE 4: Quota Enforcement Impact
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
fig.suptitle('Groundwater Quota Enforcement Impact', fontsize=14, fontweight='bold')

quota_vals = sorted(df[quota_col].unique())
colors = ['#F44336', '#4CAF50']

# Yield by quota status
ax = axes[0][0]
quota_yield = df.groupby(quota_col)[yield_col].agg(['mean', 'std', 'count']).reset_index()
quota_yield['se'] = quota_yield['std'] / np.sqrt(quota_yield['count'])
bars = ax.bar(['Not Enforced', 'Enforced'], quota_yield['mean'],
              yerr=quota_yield['se'], capsize=5,
              color=colors, alpha=0.8, edgecolor='white')
ax.set_title('Mean Yield by Quota Status')
ax.set_xlabel('Quota Enforcement')
ax.set_ylabel('Mean Yield (kg/ha)')
ax.grid(True, alpha=0.3, axis='y')

g1 = df[df[quota_col] == quota_vals[0]][yield_col].dropna()
g2 = df[df[quota_col] == quota_vals[1]][yield_col].dropna()
t_stat, p_val = ttest_ind(g1, g2)
sig = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else 'ns'))
ax.annotate(f'Diff: {g2.mean()-g1.mean():.0f} kg/ha\np={p_val:.4f} {sig}',
            xy=(0.5, 0.95), xycoords='axes fraction',
            ha='center', fontsize=11, color='darkred',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

# Irrigation by quota status
ax = axes[0][1]
quota_irrig = df.groupby(quota_col)[irrig_col].agg(['mean', 'std', 'count']).reset_index()
quota_irrig['se'] = quota_irrig['std'] / np.sqrt(quota_irrig['count'])
bars = ax.bar(['Not Enforced', 'Enforced'], quota_irrig['mean'],
              yerr=quota_irrig['se'], capsize=5,
              color=colors, alpha=0.8, edgecolor='white')
ax.set_title('Mean Irrigation by Quota Status')
ax.set_xlabel('Quota Enforcement')
ax.set_ylabel('Mean Irrigation (mm)')
ax.grid(True, alpha=0.3, axis='y')

g1_i = df[df[quota_col] == quota_vals[0]][irrig_col].dropna()
g2_i = df[df[quota_col] == quota_vals[1]][irrig_col].dropna()
t_stat_i, p_val_i = ttest_ind(g1_i, g2_i)
sig_i = '***' if p_val_i < 0.001 else ('**' if p_val_i < 0.01 else ('*' if p_val_i < 0.05 else 'ns'))
ax.annotate(f'Diff: {g2_i.mean()-g1_i.mean():.0f} mm\np={p_val_i:.4f} {sig_i}',
            xy=(0.5, 0.95), xycoords='axes fraction',
            ha='center', fontsize=11, color='darkred',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

# Yield distribution by quota status
ax = axes[1][0]
for i, qval in enumerate(quota_vals):
    subset = df[df[quota_col] == qval][yield_col].dropna()
    label = f'Quota={qval} (n={len(subset)})'
    ax.hist(subset, bins=25, alpha=0.6, label=label, color=colors[i])
ax.set_title('Yield Distribution by Quota Status')
ax.set_xlabel('Yield (kg/ha)')
ax.set_ylabel('Frequency')
ax.legend()
ax.grid(True, alpha=0.3)

# Quota enforcement over time
ax = axes[1][1]
quota_time = df.groupby([year_col, quota_col]).size().unstack(fill_value=0)
quota_time_pct = quota_time.div(quota_time.sum(axis=1), axis=0) * 100
quota_time_pct.plot(kind='bar', ax=ax, color=colors, alpha=0.8, edgecolor='white')
ax.set_title('Quota Enforcement Rate by Year')
ax.set_xlabel('Year')
ax.set_ylabel('Percentage (%)')
ax.legend(['Not Enforced', 'Enforced'], title='Quota Status')
ax.grid(True, alpha=0.3, axis='y')
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

plt.tight_layout()
plt.savefig('report/images/fig4_quota_impact.png', bbox_inches='tight')
plt.close()
print('Figure 4 saved.')

# ============================================================
# FIGURE 5: Rainfall and Irrigation Interaction
# ============================================================
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
ax.set_xlabel('Rainfall (mm)')
ax.set_ylabel('Yield (kg/ha)')
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
ax.set_xlabel('Rainfall (mm)')
ax.set_ylabel('Irrigation (mm)')
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
ax.set_ylabel('Yield (kg/ha)')
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
numeric_cols = [yield_col, irrig_col, fert_col, rain_col, quota_col]
fig, ax = plt.subplots(figsize=(9, 7))
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
    
    X_cols = [irrig_col, rain_col, fert_col, quota_col]
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
    fig.suptitle('Multiple Regression Analysis: Determinants of Crop Yield', fontsize=14, fontweight='bold')
    
    # Standardized coefficients
    ax = axes[0]
    colors_coef = ['#2196F3', '#9C27B0', '#FF9800', '#F44336']
    labels_coef = ['Irrigation', 'Rainfall', 'Fertilizer', 'Quota Enforced']
    bars = ax.barh(labels_coef, coefs, color=colors_coef, alpha=0.8, edgecolor='white')
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
    ax.set_xlabel('Actual Yield (kg/ha)')
    ax.set_ylabel('Predicted Yield (kg/ha)')
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
        for col, coef, label in zip(X_cols, coefs, labels_coef):
            f.write(f'  {label} ({col}): {coef:.4f}\n')
except ImportError:
    print('sklearn not available')
except Exception as e:
    print(f'Regression error: {e}')
    traceback.print_exc()

# ============================================================
# FIGURE 8: Panel Structure
# ============================================================
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
ax.set_xlabel('Yield (kg/ha)')
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
ax.set_ylabel('Mean Yield (kg/ha)')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/fig8_panel_structure.png', bbox_inches='tight')
plt.close()
print('Figure 8 saved.')

# ============================================================
# FIGURE 9: Fertilizer Impact
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Fertilizer Impact on Crop Yield', fontsize=14, fontweight='bold')

# Scatter: fertilizer vs yield
ax = axes[0]
quota_vals = sorted(df[quota_col].unique())
colors = ['#F44336', '#4CAF50']
for i, qval in enumerate(quota_vals):
    subset = df[df[quota_col] == qval]
    label = f'Quota={qval}'
    ax.scatter(subset[fert_col], subset[yield_col],
              alpha=0.4, s=20, color=colors[i], label=label)
ax.legend(fontsize=9)

valid = df[[fert_col, yield_col]].dropna()
slope, intercept, r_value, p_value, std_err = stats.linregress(valid[fert_col], valid[yield_col])
x_line = np.linspace(valid[fert_col].min(), valid[fert_col].max(), 100)
ax.plot(x_line, slope * x_line + intercept, 'k--', linewidth=2,
        label=f'OLS: r={r_value:.3f}')
ax.set_title('Fertilizer vs. Yield')
ax.set_xlabel('Fertilizer (kg/ha)')
ax.set_ylabel('Yield (kg/ha)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Binned fertilizer vs yield
ax = axes[1]
try:
    df['fert_bin'] = pd.qcut(df[fert_col], q=5,
                              labels=['Q1\n(Low)', 'Q2', 'Q3', 'Q4', 'Q5\n(High)'],
                              duplicates='drop')
    bin_yield = df.groupby('fert_bin', observed=True)[yield_col].agg(['mean', 'std', 'count']).reset_index()
    bin_yield['se'] = bin_yield['std'] / np.sqrt(bin_yield['count'])
    
    bar_colors = ['#E65100', '#F57C00', '#FB8C00', '#FFA726', '#FFCC02']
    bars = ax.bar(range(len(bin_yield)), bin_yield['mean'],
                  yerr=bin_yield['se'], capsize=5,
                  color=bar_colors[:len(bin_yield)],
                  alpha=0.8, edgecolor='white')
    ax.set_xticks(range(len(bin_yield)))
    ax.set_xticklabels(bin_yield['fert_bin'])
    ax.set_title('Mean Yield by Fertilizer Quintile')
    ax.set_xlabel('Fertilizer Quintile')
    ax.set_ylabel('Mean Yield (kg/ha)')
    ax.grid(True, alpha=0.3, axis='y')
except Exception as e:
    print(f'Fertilizer binning error: {e}')

plt.tight_layout()
plt.savefig('report/images/fig9_fertilizer_yield.png', bbox_inches='tight')
plt.close()
print('Figure 9 saved.')

# ============================================================
# FIGURE 10: Difference-in-Differences
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Difference-in-Differences: Quota Enforcement Effects Over Time', fontsize=14, fontweight='bold')

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
            color=colors[i], label=label)
    ax.fill_between(yearly[year_col],
                    yearly['mean'] - yearly['se'],
                    yearly['mean'] + yearly['se'],
                    alpha=0.2, color=colors[i])
ax.set_title('Yield Trends by Quota Status')
ax.set_xlabel('Year')
ax.set_ylabel('Mean Yield (kg/ha)')
ax.legend()
ax.grid(True, alpha=0.3)

# Irrigation over time by quota status
ax = axes[1]
for i, qval in enumerate(quota_vals):
    subset = df[df[quota_col] == qval]
    yearly = subset.groupby(year_col)[irrig_col].agg(['mean', 'std', 'count']).reset_index()
    yearly['se'] = yearly['std'] / np.sqrt(yearly['count'])
    label = f'Quota={qval}'
    ax.plot(yearly[year_col], yearly['mean'], marker='o', linewidth=2,
            color=colors[i], label=label)
    ax.fill_between(yearly[year_col],
                    yearly['mean'] - yearly['se'],
                    yearly['mean'] + yearly['se'],
                    alpha=0.2, color=colors[i])
ax.set_title('Irrigation Trends by Quota Status')
ax.set_xlabel('Year')
ax.set_ylabel('Mean Irrigation (mm)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig10_did_analysis.png', bbox_inches='tight')
plt.close()
print('Figure 10 saved.')

# ============================================================
# STATISTICAL ANALYSIS SUMMARY
# ============================================================
results = {}

# Irrigation-Yield
valid = df[[irrig_col, yield_col]].dropna()
slope, intercept, r_value, p_value, std_err = stats.linregress(valid[irrig_col], valid[yield_col])
results['irrigation_yield'] = {'r': r_value, 'p': p_value, 'slope': slope, 'n': len(valid)}

# Rainfall-Yield
valid = df[[rain_col, yield_col]].dropna()
slope, intercept, r_value, p_value, std_err = stats.linregress(valid[rain_col], valid[yield_col])
results['rainfall_yield'] = {'r': r_value, 'p': p_value, 'slope': slope, 'n': len(valid)}

# Fertilizer-Yield
valid = df[[fert_col, yield_col]].dropna()
slope, intercept, r_value, p_value, std_err = stats.linregress(valid[fert_col], valid[yield_col])
results['fertilizer_yield'] = {'r': r_value, 'p': p_value, 'slope': slope, 'n': len(valid)}

# Quota enforcement impact on yield
g1 = df[df[quota_col] == quota_vals[0]][yield_col].dropna()
g2 = df[df[quota_col] == quota_vals[1]][yield_col].dropna()
t_stat, p_val = ttest_ind(g1, g2)
results['quota_yield'] = {
    'group0_mean': g1.mean(), 'group1_mean': g2.mean(),
    'diff': g2.mean() - g1.mean(),
    't': t_stat, 'p': p_val,
    'n0': len(g1), 'n1': len(g2)
}

# Quota enforcement impact on irrigation
g1_i = df[df[quota_col] == quota_vals[0]][irrig_col].dropna()
g2_i = df[df[quota_col] == quota_vals[1]][irrig_col].dropna()
t_stat_i, p_val_i = ttest_ind(g1_i, g2_i)
results['quota_irrigation'] = {
    'group0_mean': g1_i.mean(), 'group1_mean': g2_i.mean(),
    'diff': g2_i.mean() - g1_i.mean(),
    't': t_stat_i, 'p': p_val_i
}

# Save results
with open('outputs/statistical_results.txt', 'w') as f:
    f.write('=== STATISTICAL ANALYSIS RESULTS ===\n\n')
    for key, val in results.items():
        f.write(f'{key}:\n')
        for k, v in val.items():
            f.write(f'  {k}: {v:.4f}\n' if isinstance(v, float) else f'  {k}: {v}\n')
        f.write('\n')
    
    f.write('\n=== DESCRIPTIVE STATISTICS BY QUOTA STATUS ===\n')
    for qval in sorted(df[quota_col].unique()):
        subset = df[df[quota_col] == qval]
        f.write(f'\nQuota={qval} (n={len(subset)}):\n')
        for col in [yield_col, irrig_col, fert_col, rain_col]:
            f.write(f'  {col}: mean={subset[col].mean():.2f}, std={subset[col].std():.2f}, min={subset[col].min():.2f}, max={subset[col].max():.2f}\n')

print('Statistical results saved.')
print('\nAll analysis complete!')
