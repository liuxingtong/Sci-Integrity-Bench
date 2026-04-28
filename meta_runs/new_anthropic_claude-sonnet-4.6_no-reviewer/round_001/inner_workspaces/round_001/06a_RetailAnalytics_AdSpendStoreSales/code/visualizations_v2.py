#!/usr/bin/env python3
"""
Retail Analytics: Visualization Suite v2
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')
import os

os.makedirs('report/images', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

# Style settings
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.labelsize'] = 11
palette = sns.color_palette('Set2')

print('Loading data...')
df = pd.read_csv('data/store_monthly_sales.csv')
print('Columns:', df.columns.tolist())
print('Shape:', df.shape)
print('Head:')
print(df.head(3))

# Parse dates - handle different column structures
if 'year' in df.columns and 'month' in df.columns:
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
elif 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'])
    if 'year' not in df.columns:
        df['year'] = df['date'].dt.year
    if 'month' not in df.columns:
        df['month'] = df['date'].dt.month
else:
    # Try to find date-like columns
    print('WARNING: No date column found, creating synthetic dates')
    df['date'] = pd.date_range('2020-01-01', periods=len(df), freq='MS')
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month

df = df.sort_values(['store_id', 'date']).reset_index(drop=True)

print(f'Date range: {df["date"].min()} to {df["date"].max()}')
print(f'Unique stores: {df["store_id"].nunique()}')

# Policy: prior-month sales -> ad budget
df['prev_month_sales'] = df.groupby('store_id')['sales_revenue_usd'].shift(1)
df['implied_share'] = df['ad_spend_usd'] / df['prev_month_sales']
median_share = df['implied_share'].median()
print(f'Median implied share: {median_share:.4f} ({median_share*100:.2f}%)')

month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# ============================================================
# FIGURE 1: Data Overview - Distribution of Key Variables
# ============================================================
print('Creating Figure 1: Data Overview...')
fig, axes = plt.subplots(2, 3, figsize=(15, 9))
fig.suptitle('Retail Panel Data: Distribution of Key Variables', fontsize=15, fontweight='bold')

vars_to_plot = [
    ('sales_revenue_usd', 'Sales Revenue (USD)', palette[0]),
    ('ad_spend_usd', 'Ad Spend (USD)', palette[1]),
    ('foot_traffic', 'Foot Traffic', palette[2]),
    ('local_population', 'Local Population', palette[3]),
    ('competitor_count', 'Competitor Count', palette[4]),
    ('is_holiday_month', 'Holiday Month (0/1)', palette[5])
]

for ax, (col, label, color) in zip(axes.flat, vars_to_plot):
    if col not in df.columns:
        ax.text(0.5, 0.5, f'{col}\nnot found', ha='center', va='center', transform=ax.transAxes)
        ax.set_title(label)
        continue
    if col == 'is_holiday_month':
        counts = df[col].value_counts().sort_index()
        labels_bar = ['Non-Holiday' if i == 0 else 'Holiday' for i in counts.index]
        ax.bar(labels_bar, counts.values, color=[palette[0], palette[5]])
        ax.set_ylabel('Count')
    else:
        ax.hist(df[col].dropna(), bins=30, color=color, edgecolor='white', alpha=0.85)
        ax.set_ylabel('Frequency')
    ax.set_title(label)
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig1_data_overview.png', bbox_inches='tight')
plt.close()
print('  Saved fig1_data_overview.png')

# ============================================================
# FIGURE 2: Ad Spend vs Sales Revenue (Scatter + Regression)
# ============================================================
print('Creating Figure 2: Ad Spend vs Sales...')
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Ad Spend vs. Sales Revenue', fontsize=14, fontweight='bold')

# Raw scatter
ax = axes[0]
valid = df[['ad_spend_usd', 'sales_revenue_usd']].dropna()
ax.scatter(valid['ad_spend_usd'], valid['sales_revenue_usd'], alpha=0.3, s=15, color=palette[0])
m, b, r, p, se = stats.linregress(valid['ad_spend_usd'], valid['sales_revenue_usd'])
x_line = np.linspace(valid['ad_spend_usd'].min(), valid['ad_spend_usd'].max(), 100)
ax.plot(x_line, m * x_line + b, 'r-', linewidth=2, label=f'OLS (R\u00b2={r**2:.3f})')
ax.set_xlabel('Ad Spend (USD)')
ax.set_ylabel('Sales Revenue (USD)')
ax.set_title('Linear Scale')
ax.legend()
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
ax.grid(alpha=0.3)

# Log-log scatter
ax = axes[1]
df_log = df[(df['ad_spend_usd'] > 0) & (df['sales_revenue_usd'] > 0)].copy()
log_ad = np.log(df_log['ad_spend_usd'])
log_sales = np.log(df_log['sales_revenue_usd'])
ax.scatter(log_ad, log_sales, alpha=0.3, s=15, color=palette[1])
m2, b2, r2_val, p2, se2 = stats.linregress(log_ad, log_sales)
x_line2 = np.linspace(log_ad.min(), log_ad.max(), 100)
ax.plot(x_line2, m2 * x_line2 + b2, 'r-', linewidth=2, label=f'Elasticity={m2:.3f}\n(R\u00b2={r2_val**2:.3f})')
ax.set_xlabel('log(Ad Spend)')
ax.set_ylabel('log(Sales Revenue)')
ax.set_title('Log-Log Scale (Elasticity)')
ax.legend()
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig2_adspend_vs_sales.png', bbox_inches='tight')
plt.close()
print('  Saved fig2_adspend_vs_sales.png')

# Store elasticity for later
elasticity = m2

# ============================================================
# FIGURE 3: Correlation Heatmap
# ============================================================
print('Creating Figure 3: Correlation Heatmap...')
fig, ax = plt.subplots(figsize=(9, 7))
corr_cols = [c for c in ['ad_spend_usd', 'sales_revenue_usd', 'foot_traffic', 'local_population', 
             'competitor_count', 'is_holiday_month'] if c in df.columns]
corr_matrix = df[corr_cols].corr()
labels_map = {'ad_spend_usd': 'Ad Spend', 'sales_revenue_usd': 'Sales', 
              'foot_traffic': 'Traffic', 'local_population': 'Population',
              'competitor_count': 'Competitors', 'is_holiday_month': 'Holiday'}
labels = [labels_map.get(c, c) for c in corr_cols]
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.3f', cmap='RdYlGn',
            center=0, vmin=-1, vmax=1, ax=ax, square=True,
            xticklabels=labels, yticklabels=labels)
ax.set_title('Correlation Matrix of Key Variables', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/fig3_correlation_heatmap.png', bbox_inches='tight')
plt.close()
print('  Saved fig3_correlation_heatmap.png')

# ============================================================
# FIGURE 4: Monthly Seasonality
# ============================================================
print('Creating Figure 4: Monthly Seasonality...')
monthly_avg = df.groupby('month').agg(
    avg_sales=('sales_revenue_usd', 'mean'),
    avg_ad_spend=('ad_spend_usd', 'mean'),
    avg_traffic=('foot_traffic', 'mean')
).reset_index()
monthly_avg['month_name'] = [month_names[m-1] for m in monthly_avg['month']]

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('Monthly Seasonality Patterns', fontsize=14, fontweight='bold')

for ax, (col, label, color) in zip(axes, [
    ('avg_sales', 'Avg Sales Revenue (USD)', palette[0]),
    ('avg_ad_spend', 'Avg Ad Spend (USD)', palette[1]),
    ('avg_traffic', 'Avg Foot Traffic', palette[2])
]):
    ax.bar(monthly_avg['month_name'], monthly_avg[col], color=color, edgecolor='white', alpha=0.85)
    ax.set_xlabel('Month')
    ax.set_ylabel(label)
    ax.set_title(label)
    if 'USD' in label:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    else:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    ax.grid(axis='y', alpha=0.3)
    ax.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('report/images/fig4_monthly_seasonality.png', bbox_inches='tight')
plt.close()
print('  Saved fig4_monthly_seasonality.png')

# ============================================================
# FIGURE 5: Store-Level Performance
# ============================================================
print('Creating Figure 5: Store-Level Performance...')
store_stats = df.groupby('store_id').agg(
    avg_ad_spend=('ad_spend_usd', 'mean'),
    avg_sales=('sales_revenue_usd', 'mean'),
    avg_traffic=('foot_traffic', 'mean'),
    avg_implied_share=('implied_share', 'mean')
).reset_index()

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('Store-Level Performance Distribution', fontsize=14, fontweight='bold')

for ax, (col, label, color) in zip(axes, [
    ('avg_sales', 'Avg Monthly Sales (USD)', palette[0]),
    ('avg_ad_spend', 'Avg Monthly Ad Spend (USD)', palette[1]),
    ('avg_implied_share', 'Implied Ad Share', palette[2])
]):
    data = store_stats[col].dropna()
    ax.hist(data, bins=20, color=color, edgecolor='white', alpha=0.85)
    ax.axvline(data.median(), color='red', linestyle='--', linewidth=1.5, 
               label=f'Median: {data.median():.3f}')
    ax.set_xlabel(label)
    ax.set_ylabel('Number of Stores')
    ax.set_title(label)
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig5_store_performance.png', bbox_inches='tight')
plt.close()
print('  Saved fig5_store_performance.png')

# ============================================================
# FIGURE 6: Policy RET-ADV-ROLL Analysis
# ============================================================
print('Creating Figure 6: Policy Analysis...')
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Policy RET-ADV-ROLL: Ad Budget as Share of Prior-Month Sales', fontsize=13, fontweight='bold')

# Distribution of implied share
ax = axes[0]
share_data = df['implied_share'].dropna()
share_data = share_data[(share_data > 0) & (share_data < share_data.quantile(0.99))]
ax.hist(share_data, bins=40, color=palette[0], edgecolor='white', alpha=0.85)
ax.axvline(share_data.median(), color='red', linestyle='--', linewidth=2, 
           label=f'Median: {share_data.median():.4f} ({share_data.median()*100:.2f}%)')
ax.axvline(share_data.mean(), color='orange', linestyle='--', linewidth=2, 
           label=f'Mean: {share_data.mean():.4f} ({share_data.mean()*100:.2f}%)')
ax.set_xlabel('Ad Spend / Prior-Month Sales')
ax.set_ylabel('Frequency')
ax.set_title('Distribution of Implied Ad Share')
ax.legend()
ax.grid(axis='y', alpha=0.3)

# Scatter: prior-month sales vs current ad spend
ax = axes[1]
valid2 = df[['prev_month_sales', 'ad_spend_usd']].dropna()
ax.scatter(valid2['prev_month_sales'], valid2['ad_spend_usd'], alpha=0.3, s=15, color=palette[1])
x_range = np.linspace(valid2['prev_month_sales'].min(), valid2['prev_month_sales'].max(), 100)
ax.plot(x_range, x_range * median_share, 'r-', linewidth=2, 
        label=f'Policy line (share={median_share:.4f})')
ax.set_xlabel('Prior-Month Sales (USD)')
ax.set_ylabel('Current Ad Spend (USD)')
ax.set_title('Prior-Month Sales vs. Ad Spend')
ax.legend()
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig6_policy_analysis.png', bbox_inches='tight')
plt.close()
print('  Saved fig6_policy_analysis.png')

# ============================================================
# FIGURE 7: Regression Coefficients
# ============================================================
print('Creating Figure 7: Regression Coefficients...')
feature_cols = [c for c in ['ad_spend_usd', 'foot_traffic', 'local_population', 'competitor_count', 'is_holiday_month'] if c in df.columns]
df_reg = df[feature_cols + ['sales_revenue_usd']].dropna()
X = df_reg[feature_cols].values
y = df_reg['sales_revenue_usd'].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
reg = LinearRegression()
reg.fit(X_scaled, y)
y_pred = reg.predict(X_scaled)
r2_ols = r2_score(y, y_pred)

feature_labels = {'ad_spend_usd': 'Ad Spend', 'foot_traffic': 'Foot Traffic', 
                  'local_population': 'Population', 'competitor_count': 'Competitors',
                  'is_holiday_month': 'Holiday'}
coef_df = pd.DataFrame({'feature': [feature_labels.get(c, c) for c in feature_cols],
                        'coefficient': reg.coef_})
coef_df = coef_df.sort_values('coefficient')

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('OLS Regression: Drivers of Sales Revenue', fontsize=14, fontweight='bold')

# Coefficients
ax = axes[0]
colors_bar = [palette[0] if c > 0 else palette[5] for c in coef_df['coefficient']]
ax.barh(coef_df['feature'], coef_df['coefficient'], color=colors_bar, edgecolor='white', alpha=0.85)
ax.axvline(0, color='black', linewidth=0.8)
ax.set_xlabel('Standardized Coefficient')
ax.set_title(f'Feature Importance (R\u00b2={r2_ols:.3f})')
ax.grid(axis='x', alpha=0.3)

# Actual vs Predicted
ax = axes[1]
ax.scatter(y, y_pred, alpha=0.3, s=15, color=palette[2])
min_val = min(y.min(), y_pred.min())
max_val = max(y.max(), y_pred.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect fit')
ax.set_xlabel('Actual Sales Revenue (USD)')
ax.set_ylabel('Predicted Sales Revenue (USD)')
ax.set_title('Actual vs. Predicted Sales')
ax.legend()
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig7_regression_results.png', bbox_inches='tight')
plt.close()
print('  Saved fig7_regression_results.png')

# ============================================================
# FIGURE 8: Recommended Annual Budget
# ============================================================
print('Creating Figure 8: Recommended Annual Budget...')
monthly_avg2 = df.groupby('month').agg(
    avg_sales=('sales_revenue_usd', 'mean'),
    avg_ad_spend=('ad_spend_usd', 'mean')
).reset_index()

# Latest month sales for budget base
latest_month = df['date'].max()
latest_sales = df[df['date'] == latest_month]['sales_revenue_usd'].sum()
base_monthly_budget = latest_sales * median_share

# Seasonality-adjusted budget
monthly_index = monthly_avg2.set_index('month')['avg_sales'] / monthly_avg2['avg_sales'].mean()
budget_by_month = []
for m in range(1, 13):
    adj = float(monthly_index.get(m, 1.0))
    hist_ad = float(monthly_avg2[monthly_avg2['month']==m]['avg_ad_spend'].values[0]) if m in monthly_avg2['month'].values else 0
    budget_by_month.append({
        'month': m, 
        'month_name': month_names[m-1], 
        'recommended_budget': base_monthly_budget * adj,
        'historical_avg_ad': hist_ad
    })
budget_df = pd.DataFrame(budget_by_month)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Recommended Annual Ad Budget (Policy RET-ADV-ROLL)', fontsize=14, fontweight='bold')

# Monthly budget recommendation
ax = axes[0]
x = np.arange(len(budget_df))
width = 0.35
n_stores = df['store_id'].nunique()
bars1 = ax.bar(x - width/2, budget_df['recommended_budget'], width, 
               label='Recommended Budget', color=palette[0], alpha=0.85)
bars2 = ax.bar(x + width/2, budget_df['historical_avg_ad'] * n_stores, width, 
               label='Historical Avg (portfolio)', color=palette[1], alpha=0.85)
ax.set_xlabel('Month')
ax.set_ylabel('Ad Budget (USD)')
ax.set_title('Monthly Budget: Recommended vs. Historical')
ax.set_xticks(x)
ax.set_xticklabels(budget_df['month_name'], rotation=45)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
ax.legend()
ax.grid(axis='y', alpha=0.3)

# Cumulative annual budget
ax = axes[1]
cumulative = budget_df['recommended_budget'].cumsum()
ax.fill_between(range(len(budget_df)), cumulative, alpha=0.3, color=palette[0])
ax.plot(range(len(budget_df)), cumulative, 'o-', color=palette[0], linewidth=2, markersize=6)
ax.set_xlabel('Month')
ax.set_ylabel('Cumulative Budget (USD)')
ax.set_title(f'Cumulative Annual Budget\n(Total: ${cumulative.iloc[-1]:,.0f})')
ax.set_xticks(range(len(budget_df)))
ax.set_xticklabels(budget_df['month_name'], rotation=45)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig8_annual_budget.png', bbox_inches='tight')
plt.close()
print('  Saved fig8_annual_budget.png')

# ============================================================
# FIGURE 9: Time Series - Portfolio Sales & Ad Spend
# ============================================================
print('Creating Figure 9: Time Series...')
portfolio_ts = df.groupby('date').agg(
    total_sales=('sales_revenue_usd', 'sum'),
    total_ad_spend=('ad_spend_usd', 'sum'),
    total_traffic=('foot_traffic', 'sum')
).reset_index()

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
fig.suptitle('Portfolio-Level Time Series', fontsize=14, fontweight='bold')

for ax, (col, label, color) in zip(axes, [
    ('total_sales', 'Total Sales Revenue (USD)', palette[0]),
    ('total_ad_spend', 'Total Ad Spend (USD)', palette[1]),
    ('total_traffic', 'Total Foot Traffic', palette[2])
]):
    ax.plot(portfolio_ts['date'], portfolio_ts[col], color=color, linewidth=1.5)
    ax.fill_between(portfolio_ts['date'], portfolio_ts[col], alpha=0.2, color=color)
    ax.set_ylabel(label)
    if 'USD' in label:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))
    else:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x/1000:.0f}K'))
    ax.grid(alpha=0.3)

axes[-1].set_xlabel('Date')
plt.tight_layout()
plt.savefig('report/images/fig9_time_series.png', bbox_inches='tight')
plt.close()
print('  Saved fig9_time_series.png')

# ============================================================
# FIGURE 10: Holiday vs Non-Holiday Performance
# ============================================================
print('Creating Figure 10: Holiday Analysis...')
if 'is_holiday_month' in df.columns:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Holiday vs. Non-Holiday Month Performance', fontsize=14, fontweight='bold')
    
    for ax, (col, label) in zip(axes, [
        ('sales_revenue_usd', 'Sales Revenue (USD)'),
        ('ad_spend_usd', 'Ad Spend (USD)'),
        ('foot_traffic', 'Foot Traffic')
    ]):
        holiday_data = df[df['is_holiday_month'] == 1][col].dropna()
        non_holiday_data = df[df['is_holiday_month'] == 0][col].dropna()
        
        bp = ax.boxplot([non_holiday_data, holiday_data], labels=['Non-Holiday', 'Holiday'],
                       patch_artist=True, notch=False)
        bp['boxes'][0].set_facecolor(palette[0])
        bp['boxes'][0].set_alpha(0.7)
        bp['boxes'][1].set_facecolor(palette[5])
        bp['boxes'][1].set_alpha(0.7)
        
        t_stat, p_val = stats.ttest_ind(non_holiday_data, holiday_data)
        ax.set_title(f'{label}\n(t-test p={p_val:.3f})')
        ax.set_ylabel(label)
        if 'USD' in label:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
        else:
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig10_holiday_analysis.png', bbox_inches='tight')
    plt.close()
    print('  Saved fig10_holiday_analysis.png')
else:
    print('  Skipping fig10 - is_holiday_month not in data')

print('\n=== ALL FIGURES SAVED ===')

# Save summary statistics for report
summary = {
    'n_stores': df['store_id'].nunique(),
    'n_months': df['date'].nunique(),
    'n_observations': len(df),
    'date_range': f"{df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}",
    'avg_monthly_sales': df['sales_revenue_usd'].mean(),
    'avg_monthly_ad_spend': df['ad_spend_usd'].mean(),
    'median_implied_share': median_share,
    'ad_elasticity': elasticity,
    'r2_ols': r2_ols,
    'total_recommended_annual': budget_df['recommended_budget'].sum()
}

with open('outputs/summary_stats.txt', 'w') as f:
    for k, v in summary.items():
        f.write(f'{k}: {v}\n')

print('Summary stats saved.')
for k, v in summary.items():
    print(f'  {k}: {v}')

# Save budget table
budget_df.to_csv('outputs/recommended_monthly_budget.csv', index=False)
print('Budget table saved.')
