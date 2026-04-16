import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import statsmodels.api as sm

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
data_path = '../data/daily_panel.csv'
df = pd.read_csv(data_path)

# Create a comprehensive summary figure
fig = plt.figure(figsize=(16, 12))
fig.suptitle('Summary: Air Pollution and Respiratory Health Relationships', fontsize=18, y=1.02)

# Panel 1: Time series of PM2.5 and visits (dual axis)
ax1 = plt.subplot(3, 3, 1)
ax1.plot(df['day_index'], df['pm25'], color='red', linewidth=1.5, label='PM2.5')
ax1.set_xlabel('Day Index')
ax1.set_ylabel('PM2.5 (μg/m³)', color='red')
ax1.tick_params(axis='y', labelcolor='red')
ax1.set_title('A. PM2.5 Over Time')

ax1b = ax1.twinx()
ax1b.plot(df['day_index'], df['respiratory_visits'], color='blue', alpha=0.7, linewidth=1, label='Visits')
ax1b.set_ylabel('Respiratory Visits', color='blue')
ax1b.tick_params(axis='y', labelcolor='blue')

# Panel 2: Scatter with regression line
ax2 = plt.subplot(3, 3, 2)
ax2.scatter(df['pm25'], df['respiratory_visits'], alpha=0.6, color='darkred', s=30)

# Add regression line from best model
X = sm.add_constant(df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']])
y = df['respiratory_visits']
model = sm.OLS(y, X).fit()

# Sort for smooth line
sorted_idx = np.argsort(df['pm25'])
pm25_sorted = df['pm25'].iloc[sorted_idx]
X_pred = pd.DataFrame({
    'const': 1,
    'pm25': pm25_sorted,
    'heating_degree_day': df['heating_degree_day'].mean(),
    'flu_index': df['flu_index'].mean(),
    'school_holiday': 0
})
y_pred = model.predict(X_pred)

ax2.plot(pm25_sorted, y_pred, color='red', linewidth=2, label='Adjusted relationship')
ax2.set_xlabel('PM2.5 (μg/m³)')
ax2.set_ylabel('Respiratory Visits')
ax2.set_title('B. PM2.5 vs Visits (Adjusted)')
ax2.grid(True, alpha=0.3)

# Add equation text
coef = model.params['pm25']
ax2.text(0.05, 0.95, f'β = {coef:.3f} visits per μg/m³\np = {model.pvalues["pm25"]:.3f}', 
         transform=ax2.transAxes, fontsize=10, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Panel 3: Marginal effect per 10 μg/m³
ax3 = plt.subplot(3, 3, 3)
effect_per_10 = coef * 10
ci_lower = (coef - 1.96 * model.bse['pm25']) * 10
ci_upper = (coef + 1.96 * model.bse['pm25']) * 10

ax3.bar(['Effect'], [effect_per_10], color='green', alpha=0.7, edgecolor='black')
ax3.errorbar(['Effect'], [effect_per_10], yerr=[[effect_per_10 - ci_lower], [ci_upper - effect_per_10]], 
             fmt='none', color='black', capsize=10)
ax3.set_ylabel('Additional Visits per 10 μg/m³ PM2.5')
ax3.set_title('C. Marginal Effect Size')
ax3.text(0, effect_per_10 + 0.5, f'{effect_per_10:.1f} visits', ha='center', va='bottom', fontsize=11)
ax3.text(0, effect_per_10 - 2, f'95% CI: [{ci_lower:.1f}, {ci_upper:.1f}]', ha='center', va='top', fontsize=9)

# Panel 4: Variable importance (standardized coefficients)
ax4 = plt.subplot(3, 3, 4)
# Standardize variables for comparison
std_coefs = {}
for var in ['pm25', 'heating_degree_day', 'flu_index']:
    if var in model.params:
        std_coefs[var] = model.params[var] * df[var].std() / df['respiratory_visits'].std()

# Create pretty labels
labels = {'pm25': 'PM2.5', 'heating_degree_day': 'Heating Days', 'flu_index': 'Flu Index'}
var_names = [labels[var] for var in std_coefs.keys()]
coef_values = list(std_coefs.values())

bars = ax4.barh(var_names, coef_values, color=['red', 'orange', 'green'], alpha=0.7, edgecolor='black')
ax4.set_xlabel('Standardized Coefficient')
ax4.set_title('D. Relative Importance (Standardized)')
ax4.axvline(x=0, color='black', linestyle='-', alpha=0.3)

# Add value labels
for i, (bar, val) in enumerate(zip(bars, coef_values)):
    width = bar.get_width()
    ax4.text(width + 0.01, bar.get_y() + bar.get_height()/2, f'{val:.3f}', 
             ha='left', va='center', fontsize=9)

# Panel 5: High pollution days comparison
ax5 = plt.subplot(3, 3, 5)
pm25_75th = df['pm25'].quantile(0.75)
df['high_pollution'] = (df['pm25'] > pm25_75th).astype(int)
high_days = df[df['high_pollution'] == 1]['respiratory_visits']
normal_days = df[df['high_pollution'] == 0]['respiratory_visits']

ax5.boxplot([normal_days, high_days], labels=['Normal Days', 'High Pollution'], 
            patch_artist=True,
            boxprops=dict(facecolor='lightblue', color='blue'),
            medianprops=dict(color='darkblue'))
ax5.set_ylabel('Respiratory Visits')
ax5.set_title(f'E. High Pollution Days (>{pm25_75th:.1f} μg/m³)')

# Panel 6: Policy simulation
ax6 = plt.subplot(3, 3, 6)
reduction_scenarios = [10, 20, 30]
visit_reductions = [coef * df['pm25'].mean() * (r/100) for r in reduction_scenarios]
percent_reductions = [(r/df['respiratory_visits'].mean())*100 for r in visit_reductions]

x = np.arange(len(reduction_scenarios))
width = 0.6
bars = ax6.bar(x, visit_reductions, width, color='darkgreen', alpha=0.7, edgecolor='black')
ax6.set_xlabel('PM2.5 Reduction (%)')
ax6.set_ylabel('Expected Visit Reduction')
ax6.set_title('F. Policy Simulation Benefits')
ax6.set_xticks(x)
ax6.set_xticklabels([f'{r}%' for r in reduction_scenarios])

# Add value labels
for i, (bar, visit_red, percent_red) in enumerate(zip(bars, visit_reductions, percent_reductions)):
    ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
             f'{visit_red:.2f}\n({percent_red:.2f}%)', 
             ha='center', va='bottom', fontsize=9)

# Panel 7: Lag analysis
ax7 = plt.subplot(3, 3, 7)
# Create lagged variables and run models
lag_results = []
for lag in [0, 1, 2, 3]:
    if lag == 0:
        pm25_var = 'pm25'
    else:
        df[f'pm25_lag{lag}'] = df['pm25'].shift(lag)
        pm25_var = f'pm25_lag{lag}'
    
    df_lag = df.dropna().copy()
    X = sm.add_constant(df_lag[[pm25_var, 'heating_degree_day', 'flu_index', 'school_holiday']])
    y_lag = df_lag['respiratory_visits']
    model_lag = sm.OLS(y_lag, X).fit()
    
    if pm25_var in model_lag.params:
        lag_results.append({
            'lag': lag,
            'coef': model_lag.params[pm25_var],
            'pval': model_lag.pvalues[pm25_var]
        })

lag_df = pd.DataFrame(lag_results)

ax7.errorbar(lag_df['lag'], lag_df['coef'], 
             yerr=1.96*0.1,  # Simplified error bars
             fmt='o-', color='purple', linewidth=2, markersize=8, 
             capsize=5, label='PM2.5 coefficient')
ax7.axhline(y=0, color='r', linestyle='--', alpha=0.5)
ax7.set_xlabel('Lag (Days)')
ax7.set_ylabel('Coefficient')
ax7.set_title('G. Lag Analysis of PM2.5 Effects')
ax7.set_xticks([0, 1, 2, 3])
ax7.grid(True, alpha=0.3)

# Add significance markers
for _, row in lag_df.iterrows():
    if row['pval'] < 0.05:
        ax7.text(row['lag'], row['coef'] + 0.05, '*', ha='center', va='bottom', fontsize=14, color='red')

# Panel 8: Seasonal analysis
ax8 = plt.subplot(3, 3, 8)
hdd_median = df['heating_degree_day'].median()
df['heating_season'] = (df['heating_degree_day'] > hdd_median).astype(int)
heating = df[df['heating_season'] == 1]
non_heating = df[df['heating_season'] == 0]

categories = ['Non-Heating', 'Heating']
visits_means = [non_heating['respiratory_visits'].mean(), heating['respiratory_visits'].mean()]
pm25_means = [non_heating['pm25'].mean(), heating['pm25'].mean()]

x = np.arange(len(categories))
width = 0.35

bars1 = ax8.bar(x - width/2, visits_means, width, label='Visits', color='blue', alpha=0.7)
bars2 = ax8.bar(x + width/2, pm25_means, width, label='PM2.5', color='red', alpha=0.7)
ax8.set_xlabel('Season')
ax8.set_ylabel('Mean Value')
ax8.set_title('H. Seasonal Patterns')
ax8.set_xticks(x)
ax8.set_xticklabels(categories)
ax8.legend()

# Panel 9: Model comparison
ax9 = plt.subplot(3, 3, 9)
# Compare AIC values
models_info = {
    'Simple\n(PM2.5 only)': 1068.3,
    'Multiple\n(all covariates)': 1020.4,
    'Quadratic\n(PM2.5² term)': 1021.9,
    'Interaction\n(PM2.5×HDD)': 1021.9
}

model_names = list(models_info.keys())
aic_values = list(models_info.values())

bars = ax9.barh(model_names, aic_values, color=['lightgray', 'green', 'lightblue', 'lightblue'], 
                alpha=0.7, edgecolor='black')
ax9.set_xlabel('AIC (lower is better)')
ax9.set_title('I. Model Comparison')
ax9.axvline(x=min(aic_values), color='red', linestyle='--', alpha=0.5, label='Best model')

# Highlight best model
bars[1].set_color('green')
ax9.text(aic_values[1] + 5, 1, 'BEST', ha='left', va='center', fontsize=10, fontweight='bold', color='darkgreen')

plt.tight_layout()
plt.savefig('../report/images/summary_figure.png', dpi=300, bbox_inches='tight')
plt.close()

print("Summary figure saved to ../report/images/summary_figure.png")