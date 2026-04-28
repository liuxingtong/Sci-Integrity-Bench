#!/usr/bin/env python3
"""
Full Analysis: Air Pollution and Respiratory Health Panel Study
PM2.5 effects on respiratory clinic visits with heating, flu, and school holiday covariates
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import os
import warnings
warnings.filterwarnings('ignore')

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
fig_dpi = 150
COLORS = {'pm25': '#E74C3C', 'visits': '#3498DB', 'heating': '#E67E22', 
          'flu': '#9B59B6', 'holiday': '#2ECC71', 'neutral': '#95A5A6'}

# ============================================================
# 1. LOAD AND PREPARE DATA
# ============================================================
df = pd.read_csv('data/daily_panel.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print("Dataset shape:", df.shape)
print("Columns:", df.columns.tolist())
print("Date range:", df['date'].min(), "to", df['date'].max())
print("\nDescriptive stats:")
print(df.describe())

# Column mapping based on actual data
pm25 = 'pm25'
visits = 'resp_visits'
heating = 'heating_degree_days'
flu = 'flu_index'
holiday = 'school_holiday'

print(f"\nUsing columns: pm25={pm25}, visits={visits}, heating={heating}, flu={flu}, holiday={holiday}")

# Add time features
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['dayofweek'] = df['date'].dt.dayofweek
df['season'] = df['month'].map({
    12: 'Winter', 1: 'Winter', 2: 'Winter',
    3: 'Spring', 4: 'Spring', 5: 'Spring',
    6: 'Summer', 7: 'Summer', 8: 'Summer',
    9: 'Autumn', 10: 'Autumn', 11: 'Autumn'
})

# ============================================================
# 2. FIGURE 1: TIME SERIES OVERVIEW
# ============================================================
fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
fig.suptitle('Daily Panel: Air Pollution and Respiratory Health Indicators', 
             fontsize=14, fontweight='bold', y=0.98)

# PM2.5
ax1 = axes[0]
ax1.fill_between(df['date'], df[pm25], alpha=0.4, color=COLORS['pm25'])
ax1.plot(df['date'], df[pm25], color=COLORS['pm25'], linewidth=0.8, alpha=0.8)
ax1.axhline(y=35, color='darkred', linestyle='--', linewidth=1.5, label='WHO 24h guideline (35 μg/m³)')
ax1.set_ylabel('PM2.5 (μg/m³)', fontsize=10)
ax1.legend(loc='upper right', fontsize=8)
ax1.set_title('PM2.5 Concentration', fontsize=10)

# Respiratory visits
ax2 = axes[1]
ax2.fill_between(df['date'], df[visits], alpha=0.4, color=COLORS['visits'])
ax2.plot(df['date'], df[visits], color=COLORS['visits'], linewidth=0.8, alpha=0.8)
ax2.set_ylabel('Visits (count)', fontsize=10)
ax2.set_title('Respiratory Clinic Visits', fontsize=10)

# Heating degree days
ax3 = axes[2]
ax3.fill_between(df['date'], df[heating], alpha=0.4, color=COLORS['heating'])
ax3.plot(df['date'], df[heating], color=COLORS['heating'], linewidth=0.8, alpha=0.8)
ax3.set_ylabel('HDD', fontsize=10)
ax3.set_title('Heating Degree Days', fontsize=10)

# Flu index
ax4 = axes[3]
ax4.fill_between(df['date'], df[flu], alpha=0.4, color=COLORS['flu'])
ax4.plot(df['date'], df[flu], color=COLORS['flu'], linewidth=0.8, alpha=0.8)
ax4.set_ylabel('Flu Index', fontsize=10)
ax4.set_title('Influenza Activity Index', fontsize=10)

# Format x-axis
for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('report/images/fig1_time_series_overview.png', dpi=fig_dpi, bbox_inches='tight')
plt.close()
print("Figure 1 saved.")

# ============================================================
# 3. FIGURE 2: CORRELATION MATRIX
# ============================================================
numeric_cols = [pm25, visits, heating, flu]
corr_df = df[numeric_cols].corr()

fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(corr_df, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
            vmin=-1, vmax=1, ax=ax, square=True,
            linewidths=0.5, cbar_kws={'shrink': 0.8})
ax.set_title('Correlation Matrix: Key Health and Environmental Variables', 
             fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig2_correlation_matrix.png', dpi=fig_dpi, bbox_inches='tight')
plt.close()
print("Figure 2 saved.")

# ============================================================
# 4. FIGURE 3: PM2.5 vs RESPIRATORY VISITS SCATTER
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Scatter with regression
ax = axes[0]
scatter = ax.scatter(df[pm25], df[visits], 
                     c=df['month'], cmap='RdYlBu_r', 
                     alpha=0.5, s=20, edgecolors='none')
plt.colorbar(scatter, ax=ax, label='Month')

# Add regression line
valid_mask = ~(df[pm25].isna() | df[visits].isna())
slope, intercept, r_value, p_value, std_err = stats.linregress(
    df[pm25][valid_mask], df[visits][valid_mask])
x_line = np.linspace(df[pm25].min(), df[pm25].max(), 100)
y_line = slope * x_line + intercept
ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'OLS: R²={r_value**2:.3f}, p={p_value:.4f}')
ax.set_xlabel('PM2.5 (μg/m³)', fontsize=11)
ax.set_ylabel('Respiratory Clinic Visits', fontsize=11)
ax.set_title('PM2.5 vs Respiratory Visits\n(colored by month)', fontsize=11)
ax.legend(fontsize=9)

# Box plot by PM2.5 quartile
ax = axes[1]
df['pm25_quartile'] = pd.qcut(df[pm25], q=4, labels=['Q1\n(Low)', 'Q2', 'Q3', 'Q4\n(High)'])
quartile_data = [df[df['pm25_quartile'] == q][visits].dropna().values 
                 for q in ['Q1\n(Low)', 'Q2', 'Q3', 'Q4\n(High)']]
bp = ax.boxplot(quartile_data, patch_artist=True, notch=False)
colors_box = ['#2ECC71', '#F1C40F', '#E67E22', '#E74C3C']
for patch, color in zip(bp['boxes'], colors_box):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax.set_xticklabels(['Q1\n(Low)', 'Q2', 'Q3', 'Q4\n(High)'])
ax.set_xlabel('PM2.5 Quartile', fontsize=11)
ax.set_ylabel('Respiratory Clinic Visits', fontsize=11)
ax.set_title('Respiratory Visits by PM2.5 Quartile', fontsize=11)

# Add mean markers
for i, data in enumerate(quartile_data):
    ax.scatter(i+1, np.mean(data), marker='D', color='black', s=50, zorder=5)

plt.tight_layout()
plt.savefig('report/images/fig3_pm25_visits_scatter.png', dpi=fig_dpi, bbox_inches='tight')
plt.close()
print("Figure 3 saved.")

# ============================================================
# 5. FIGURE 4: SEASONAL PATTERNS
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Seasonal Patterns in Air Pollution and Health Outcomes', 
             fontsize=13, fontweight='bold')

# Monthly PM2.5
ax = axes[0, 0]
monthly_pm25 = df.groupby('month')[pm25].agg(['mean', 'std'])
months = range(1, 13)
month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
ax.bar(months, monthly_pm25['mean'], color=COLORS['pm25'], alpha=0.7, 
       yerr=monthly_pm25['std'], capsize=3)
ax.axhline(y=35, color='darkred', linestyle='--', linewidth=1.5, label='WHO guideline')
ax.set_xticks(months)
ax.set_xticklabels(month_labels, rotation=45)
ax.set_ylabel('PM2.5 (μg/m³)')
ax.set_title('Monthly Average PM2.5')
ax.legend(fontsize=8)

# Monthly visits
ax = axes[0, 1]
monthly_visits = df.groupby('month')[visits].agg(['mean', 'std'])
ax.bar(months, monthly_visits['mean'], color=COLORS['visits'], alpha=0.7,
       yerr=monthly_visits['std'], capsize=3)
ax.set_xticks(months)
ax.set_xticklabels(month_labels, rotation=45)
ax.set_ylabel('Respiratory Visits')
ax.set_title('Monthly Average Respiratory Visits')

# Seasonal box plots - PM2.5
ax = axes[1, 0]
season_order = ['Winter', 'Spring', 'Summer', 'Autumn']
season_colors = ['#3498DB', '#2ECC71', '#F39C12', '#E74C3C']
season_data_pm25 = [df[df['season'] == s][pm25].dropna().values for s in season_order]
bp = ax.boxplot(season_data_pm25, patch_artist=True)
for patch, color in zip(bp['boxes'], season_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax.set_xticklabels(season_order)
ax.set_ylabel('PM2.5 (μg/m³)')
ax.set_title('PM2.5 by Season')
ax.axhline(y=35, color='darkred', linestyle='--', linewidth=1.5)

# Seasonal box plots - Visits
ax = axes[1, 1]
season_data_visits = [df[df['season'] == s][visits].dropna().values for s in season_order]
bp = ax.boxplot(season_data_visits, patch_artist=True)
for patch, color in zip(bp['boxes'], season_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
ax.set_xticklabels(season_order)
ax.set_ylabel('Respiratory Visits')
ax.set_title('Respiratory Visits by Season')

plt.tight_layout()
plt.savefig('report/images/fig4_seasonal_patterns.png', dpi=fig_dpi, bbox_inches='tight')
plt.close()
print("Figure 4 saved.")

# ============================================================
# 6. FIGURE 5: COVARIATE EFFECTS
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('Effect of Covariates on Respiratory Clinic Visits', 
             fontsize=13, fontweight='bold')

# School holiday effect
ax = axes[0]
holiday_groups = df.groupby(holiday)[visits].agg(['mean', 'std', 'count'])
labels = ['School Day', 'School Holiday']
means = holiday_groups['mean'].values
stds = holiday_groups['std'].values
bars = ax.bar(labels, means, color=[COLORS['visits'], COLORS['holiday']], 
              alpha=0.7, yerr=stds, capsize=5)
ax.set_ylabel('Mean Respiratory Visits')
ax.set_title('School Holiday Effect')
# Add significance test
groups = [df[df[holiday] == v][visits].dropna().values 
          for v in sorted(df[holiday].unique())]
t_stat, p_val = stats.ttest_ind(groups[0], groups[1])
ax.text(0.5, 0.95, f't-test p={p_val:.4f}', transform=ax.transAxes,
        ha='center', va='top', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Flu index effect (binned)
ax = axes[1]
df['flu_quartile'] = pd.qcut(df[flu], q=4, labels=['Low', 'Med-Low', 'Med-High', 'High'])
flu_means = df.groupby('flu_quartile')[visits].mean()
flu_stds = df.groupby('flu_quartile')[visits].std()
ax.bar(flu_means.index, flu_means.values, color=COLORS['flu'], alpha=0.7,
       yerr=flu_stds.values, capsize=5)
ax.set_xlabel('Flu Activity Level')
ax.set_ylabel('Mean Respiratory Visits')
ax.set_title('Flu Index Effect on Visits')
r, p = pearsonr(df[flu].dropna(), df[visits][df[flu].notna()])
ax.text(0.05, 0.95, f'r={r:.3f}, p={p:.4f}', transform=ax.transAxes,
        ha='left', va='top', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Heating degree days effect
ax = axes[2]
df['heating_quartile'] = pd.qcut(df[heating].clip(lower=0) + 0.001, q=4, 
                                  labels=['Low', 'Med-Low', 'Med-High', 'High'],
                                  duplicates='drop')
heating_means = df.groupby('heating_quartile')[visits].mean()
heating_stds = df.groupby('heating_quartile')[visits].std()
ax.bar(heating_means.index, heating_means.values, color=COLORS['heating'], alpha=0.7,
       yerr=heating_stds.values, capsize=5)
ax.set_xlabel('Heating Degree Days Level')
ax.set_ylabel('Mean Respiratory Visits')
ax.set_title('Heating Degree Days Effect')
r, p = pearsonr(df[heating].dropna(), df[visits][df[heating].notna()])
ax.text(0.05, 0.95, f'r={r:.3f}, p={p:.4f}', transform=ax.transAxes,
        ha='left', va='top', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/fig5_covariate_effects.png', dpi=fig_dpi, bbox_inches='tight')
plt.close()
print("Figure 5 saved.")

# ============================================================
# 7. REGRESSION ANALYSIS
# ============================================================
print("\n=== REGRESSION ANALYSIS ===")

from numpy.linalg import lstsq

# Prepare regression data
reg_cols = [pm25, heating, flu, holiday]
reg_df = df[reg_cols + [visits]].dropna()
X = reg_df[reg_cols].values
y = reg_df[visits].values

# Add intercept
X_with_intercept = np.column_stack([np.ones(len(X)), X])

# OLS
beta, residuals, rank, sv = lstsq(X_with_intercept, y, rcond=None)

# Calculate statistics
y_pred = X_with_intercept @ beta
ss_res = np.sum((y - y_pred)**2)
ss_tot = np.sum((y - np.mean(y))**2)
r_squared = 1 - ss_res / ss_tot

n = len(y)
k = len(beta) - 1  # number of predictors
adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)

print(f"\nMultiple Regression Results:")
print(f"R² = {r_squared:.4f}")
print(f"Adjusted R² = {adj_r_squared:.4f}")
print(f"N = {n}")

# Standard errors
MSE = ss_res / (n - k - 1)
var_beta = MSE * np.linalg.inv(X_with_intercept.T @ X_with_intercept)
se_beta = np.sqrt(np.diag(var_beta))
t_stats_reg = beta / se_beta
p_values_reg = 2 * (1 - stats.t.cdf(np.abs(t_stats_reg), df=n-k-1))

print("\nDetailed Regression Table:")
coef_names = ['Intercept'] + reg_cols
print(f"{'Variable':<25} {'Coef':>10} {'SE':>10} {'t-stat':>10} {'p-value':>10}")
print("-" * 65)
for name, coef, se, t, p in zip(coef_names, beta, se_beta, t_stats_reg, p_values_reg):
    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
    print(f"{name:<25} {coef:>10.4f} {se:>10.4f} {t:>10.4f} {p:>10.4f} {sig}")

# Save regression results
with open('outputs/regression_results.txt', 'w') as f:
    f.write("=== Multiple Regression Results ===\n\n")
    f.write(f"Dependent variable: {visits}\n")
    f.write(f"Independent variables: {reg_cols}\n\n")
    f.write(f"R² = {r_squared:.4f}\n")
    f.write(f"Adjusted R² = {adj_r_squared:.4f}\n")
    f.write(f"N = {n}\n\n")
    f.write(f"{'Variable':<25} {'Coef':>10} {'SE':>10} {'t-stat':>10} {'p-value':>10}\n")
    f.write("-" * 65 + "\n")
    for name, coef, se, t, p in zip(coef_names, beta, se_beta, t_stats_reg, p_values_reg):
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
        f.write(f"{name:<25} {coef:>10.4f} {se:>10.4f} {t:>10.4f} {p:>10.4f} {sig}\n")

print("\nRegression results saved.")

# ============================================================
# 8. FIGURE 6: REGRESSION DIAGNOSTICS
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Regression Diagnostics: PM2.5 and Respiratory Visits Model', 
             fontsize=13, fontweight='bold')

residuals_vals = y - y_pred

# Residuals vs Fitted
ax = axes[0, 0]
ax.scatter(y_pred, residuals_vals, alpha=0.4, s=15, color='steelblue')
ax.axhline(y=0, color='red', linestyle='--', linewidth=1.5)
ax.set_xlabel('Fitted Values')
ax.set_ylabel('Residuals')
ax.set_title('Residuals vs Fitted')

# Q-Q plot
ax = axes[0, 1]
stats.probplot(residuals_vals, dist='norm', plot=ax)
ax.set_title('Normal Q-Q Plot of Residuals')

# Scale-Location
ax = axes[1, 0]
ax.scatter(y_pred, np.sqrt(np.abs(residuals_vals)), alpha=0.4, s=15, color='steelblue')
ax.set_xlabel('Fitted Values')
ax.set_ylabel('√|Residuals|')
ax.set_title('Scale-Location Plot')

# Actual vs Predicted
ax = axes[1, 1]
ax.scatter(y, y_pred, alpha=0.4, s=15, color='steelblue')
min_val = min(y.min(), y_pred.min())
max_val = max(y.max(), y_pred.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=1.5, label='Perfect fit')
ax.set_xlabel('Actual Visits')
ax.set_ylabel('Predicted Visits')
ax.set_title(f'Actual vs Predicted (R²={r_squared:.3f})')
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig('report/images/fig6_regression_diagnostics.png', dpi=fig_dpi, bbox_inches='tight')
plt.close()
print("Figure 6 saved.")

# ============================================================
# 9. FIGURE 7: LAGGED EFFECTS ANALYSIS
# ============================================================
print("\n=== LAGGED EFFECTS ANALYSIS ===")

max_lag = 7
lag_correlations = []
lag_pvalues = []

for lag in range(0, max_lag + 1):
    if lag == 0:
        x_lag = df[pm25]
        y_lag = df[visits]
    else:
        x_lag = df[pm25].shift(lag)
        y_lag = df[visits]
    
    valid = ~(x_lag.isna() | y_lag.isna())
    r, p = pearsonr(x_lag[valid], y_lag[valid])
    lag_correlations.append(r)
    lag_pvalues.append(p)
    print(f"Lag {lag}: r={r:.4f}, p={p:.4f}")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Lagged Effects of PM2.5 on Respiratory Visits', 
             fontsize=13, fontweight='bold')

# Correlation by lag
ax = axes[0]
lags = range(0, max_lag + 1)
colors_lag = ['red' if p < 0.05 else 'gray' for p in lag_pvalues]
bars = ax.bar(lags, lag_correlations, color=colors_lag, alpha=0.7)
ax.axhline(y=0, color='black', linewidth=0.8)
ax.set_xlabel('Lag (days)')
ax.set_ylabel('Pearson Correlation')
ax.set_title('PM2.5 → Respiratory Visits\nCorrelation by Lag Day')
ax.set_xticks(list(lags))
ax.legend(handles=[
    plt.Rectangle((0,0),1,1, color='red', alpha=0.7, label='p < 0.05'),
    plt.Rectangle((0,0),1,1, color='gray', alpha=0.7, label='p ≥ 0.05')
], fontsize=9)

# Cumulative effect (distributed lag)
ax = axes[1]
cumulative_r = np.cumsum(lag_correlations)
ax.plot(lags, cumulative_r, 'o-', color='steelblue', linewidth=2, markersize=8)
ax.fill_between(lags, 0, cumulative_r, alpha=0.3, color='steelblue')
ax.axhline(y=0, color='black', linewidth=0.8)
ax.set_xlabel('Lag (days)')
ax.set_ylabel('Cumulative Correlation')
ax.set_title('Cumulative PM2.5 Effect\nover Lag Days')
ax.set_xticks(list(lags))

plt.tight_layout()
plt.savefig('report/images/fig7_lagged_effects.png', dpi=fig_dpi, bbox_inches='tight')
plt.close()
print("Figure 7 saved.")

# ============================================================
# 10. FIGURE 8: POLICY THRESHOLD ANALYSIS
# ============================================================
who_threshold = 35  # μg/m³ (24-hour guideline)
df['exceeds_who'] = df[pm25] > who_threshold

exceedance_rate = df['exceeds_who'].mean() * 100
print(f"\nWHO threshold exceedance rate: {exceedance_rate:.1f}%")

exceed_visits = df[df['exceeds_who']][visits].dropna()
non_exceed_visits = df[~df['exceeds_who']][visits].dropna()

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Policy Threshold Analysis: PM2.5 and Health Burden', 
             fontsize=13, fontweight='bold')

# Visits on exceedance vs non-exceedance days
ax = axes[0]
bp = ax.boxplot([non_exceed_visits, exceed_visits], patch_artist=True,
                labels=[f'PM2.5 ≤ 35\n(n={len(non_exceed_visits)})', 
                        f'PM2.5 > 35\n(n={len(exceed_visits)})'])
bp['boxes'][0].set_facecolor('#2ECC71')
bp['boxes'][0].set_alpha(0.7)
bp['boxes'][1].set_facecolor('#E74C3C')
bp['boxes'][1].set_alpha(0.7)

t_stat, p_val = stats.ttest_ind(non_exceed_visits, exceed_visits)
ax.set_ylabel('Respiratory Clinic Visits')
ax.set_title(f'Visits: WHO Threshold Exceedance\n(t-test p={p_val:.4f})')
ax.scatter([1, 2], [non_exceed_visits.mean(), exceed_visits.mean()], 
           marker='D', color='black', s=60, zorder=5, label='Mean')
ax.legend(fontsize=9)

# Mean visits by threshold status
ax = axes[1]
mean_diff = exceed_visits.mean() - non_exceed_visits.mean()
excess_days = df['exceeds_who'].sum()

categories = ['Non-exceedance\ndays', 'Exceedance\ndays']
means = [non_exceed_visits.mean(), exceed_visits.mean()]
colors_bar = ['#2ECC71', '#E74C3C']
bars = ax.bar(categories, means, color=colors_bar, alpha=0.7, width=0.5)
ax.set_ylabel('Mean Daily Respiratory Visits')
ax.set_title('Mean Visits by WHO Threshold Status')

for bar, mean in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{mean:.1f}', ha='center', va='bottom', fontweight='bold')

ax.annotate(f'Excess: +{mean_diff:.1f} visits/day\n({excess_days} exceedance days)',
            xy=(1, exceed_visits.mean()), xytext=(0.5, exceed_visits.mean() * 0.7),
            fontsize=9, ha='center',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
            arrowprops=dict(arrowstyle='->', color='black'))

plt.tight_layout()
plt.savefig('report/images/fig8_policy_threshold.png', dpi=fig_dpi, bbox_inches='tight')
plt.close()
print("Figure 8 saved.")

# ============================================================
# 11. FIGURE 9: INTERACTION EFFECTS
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Interaction Effects: PM2.5 with Flu Season and School Holidays', 
             fontsize=13, fontweight='bold')

# PM2.5 effect during flu season vs non-flu season
ax = axes[0]
flu_median = df[flu].median()
df['high_flu'] = df[flu] > flu_median

high_flu_df = df[df['high_flu']]
low_flu_df = df[~df['high_flu']]

ax.scatter(low_flu_df[pm25], low_flu_df[visits], alpha=0.3, s=15, 
           color='#3498DB', label='Low flu activity')
ax.scatter(high_flu_df[pm25], high_flu_df[visits], alpha=0.3, s=15, 
           color='#E74C3C', label='High flu activity')

for subset, color, label in [(low_flu_df, '#3498DB', 'Low flu'), 
                               (high_flu_df, '#E74C3C', 'High flu')]:
    valid = subset[[pm25, visits]].dropna()
    if len(valid) > 10:
        slope, intercept, r, p, se = stats.linregress(valid[pm25], valid[visits])
        x_line = np.linspace(valid[pm25].min(), valid[pm25].max(), 100)
        ax.plot(x_line, slope * x_line + intercept, color=color, linewidth=2)

ax.set_xlabel('PM2.5 (μg/m³)')
ax.set_ylabel('Respiratory Visits')
ax.set_title('PM2.5 Effect by Flu Activity Level')
ax.legend(fontsize=9)

# PM2.5 effect during school holidays vs school days
ax = axes[1]
holiday_vals = sorted(df[holiday].unique())

for val, color, label in zip(holiday_vals, 
                               ['#3498DB', '#E74C3C'],
                               ['School Day', 'School Holiday']):
    subset = df[df[holiday] == val]
    ax.scatter(subset[pm25], subset[visits], alpha=0.3, s=15, 
               color=color, label=label)
    valid = subset[[pm25, visits]].dropna()
    if len(valid) > 10:
        slope, intercept, r, p, se = stats.linregress(valid[pm25], valid[visits])
        x_line = np.linspace(valid[pm25].min(), valid[pm25].max(), 100)
        ax.plot(x_line, slope * x_line + intercept, color=color, linewidth=2)

ax.set_xlabel('PM2.5 (μg/m³)')
ax.set_ylabel('Respiratory Visits')
ax.set_title('PM2.5 Effect by School Holiday Status')
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig('report/images/fig9_interaction_effects.png', dpi=fig_dpi, bbox_inches='tight')
plt.close()
print("Figure 9 saved.")

# ============================================================
# 12. SUMMARY STATISTICS FOR REPORT
# ============================================================
print("\n=== SUMMARY STATISTICS ===")
print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
print(f"Total days: {len(df)}")
print(f"\nPM2.5 statistics:")
print(f"  Mean: {df[pm25].mean():.2f} μg/m³")
print(f"  Median: {df[pm25].median():.2f} μg/m³")
print(f"  Std: {df[pm25].std():.2f} μg/m³")
print(f"  Min: {df[pm25].min():.2f} μg/m³")
print(f"  Max: {df[pm25].max():.2f} μg/m³")
print(f"  Days exceeding WHO 35 μg/m³: {df['exceeds_who'].sum()} ({exceedance_rate:.1f}%)")

print(f"\nRespiratory visits statistics:")
print(f"  Mean: {df[visits].mean():.2f}")
print(f"  Median: {df[visits].median():.2f}")
print(f"  Std: {df[visits].std():.2f}")
print(f"  Min: {df[visits].min():.2f}")
print(f"  Max: {df[visits].max():.2f}")

r_pm25_visits, p_pm25_visits = pearsonr(df[pm25].dropna(), df[visits][df[pm25].notna()])
print(f"\nPM2.5 - Visits correlation: r={r_pm25_visits:.4f}, p={p_pm25_visits:.6f}")

# Save all summary stats
with open('outputs/summary_statistics.txt', 'w') as f:
    f.write("=== Air Pollution & Health Panel: Summary Statistics ===\n\n")
    f.write(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}\n")
    f.write(f"Total days: {len(df)}\n\n")
    f.write(f"PM2.5 statistics:\n")
    f.write(f"  Mean: {df[pm25].mean():.2f} μg/m³\n")
    f.write(f"  Median: {df[pm25].median():.2f} μg/m³\n")
    f.write(f"  Std: {df[pm25].std():.2f} μg/m³\n")
    f.write(f"  Min: {df[pm25].min():.2f} μg/m³\n")
    f.write(f"  Max: {df[pm25].max():.2f} μg/m³\n")
    f.write(f"  Days exceeding WHO 35 μg/m³: {df['exceeds_who'].sum()} ({exceedance_rate:.1f}%)\n\n")
    f.write(f"Respiratory visits statistics:\n")
    f.write(f"  Mean: {df[visits].mean():.2f}\n")
    f.write(f"  Median: {df[visits].median():.2f}\n")
    f.write(f"  Std: {df[visits].std():.2f}\n")
    f.write(f"  Min: {df[visits].min():.2f}\n")
    f.write(f"  Max: {df[visits].max():.2f}\n\n")
    f.write(f"PM2.5 - Visits correlation: r={r_pm25_visits:.4f}, p={p_pm25_visits:.6f}\n\n")
    f.write("Regression Results:\n")
    f.write(f"  R² = {r_squared:.4f}\n")
    f.write(f"  Adjusted R² = {adj_r_squared:.4f}\n")
    f.write(f"  N = {n}\n")
    f.write("\nCoefficients:\n")
    for name, coef, se, t, p in zip(coef_names, beta, se_beta, t_stats_reg, p_values_reg):
        sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
        f.write(f"  {name}: {coef:.4f} (SE={se:.4f}, t={t:.4f}, p={p:.4f}) {sig}\n")

print("\nAll analyses complete!")
print("Figures saved to report/images/")
print("Results saved to outputs/")
