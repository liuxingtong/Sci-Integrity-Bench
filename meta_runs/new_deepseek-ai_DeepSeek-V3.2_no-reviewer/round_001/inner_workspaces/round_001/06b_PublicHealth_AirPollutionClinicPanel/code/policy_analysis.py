import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import statsmodels.api as sm
from scipy import stats

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
data_path = '../data/daily_panel.csv'
df = pd.read_csv(data_path)

print("=== Policy-Relevant Analysis ===")
print(f"Dataset: {len(df)} daily observations")

# Create output directory
os.makedirs('../outputs', exist_ok=True)

# 1. Threshold analysis: Is there a PM2.5 level above which effects are stronger?
print("\n1. Threshold Analysis for PM2.5 Effects")

# Define thresholds (WHO guideline: 15 μg/m³ annual mean, but we use daily)
thresholds = [10, 15, 20, 25]
threshold_results = []

for threshold in thresholds:
    df[f'above_{threshold}'] = (df['pm25'] > threshold).astype(int)
    
    # Model with threshold indicator
    X = sm.add_constant(df[['pm25', f'above_{threshold}', 'heating_degree_day', 'flu_index', 'school_holiday']])
    y = df['respiratory_visits']
    model = sm.OLS(y, X).fit()
    
    # Get coefficient for threshold indicator
    if f'above_{threshold}' in model.params:
        coef = model.params[f'above_{threshold}']
        pval = model.pvalues[f'above_{threshold}']
        threshold_results.append({
            'threshold': threshold,
            'coef': coef,
            'p_value': pval,
            'significant': pval < 0.05
        })

threshold_df = pd.DataFrame(threshold_results)
print("\nThreshold Analysis Results:")
print(threshold_df.to_string())

# 2. Lag analysis: Do effects of PM2.5 persist over days?
print("\n\n2. Lag Analysis for PM2.5 Effects")

# Create lagged variables (up to 3 days)
for lag in [1, 2, 3]:
    df[f'pm25_lag{lag}'] = df['pm25'].shift(lag)

# Drop rows with NaN from lagging
df_lag = df.dropna().copy()

lag_results = []
for lag in [0, 1, 2, 3]:
    if lag == 0:
        pm25_var = 'pm25'
    else:
        pm25_var = f'pm25_lag{lag}'
    
    X = sm.add_constant(df_lag[[pm25_var, 'heating_degree_day', 'flu_index', 'school_holiday']])
    y = df_lag['respiratory_visits']
    model = sm.OLS(y, X).fit()
    
    if pm25_var in model.params:
        coef = model.params[pm25_var]
        pval = model.pvalues[pm25_var]
        lag_results.append({
            'lag_days': lag,
            'coef': coef,
            'p_value': pval,
            'significant': pval < 0.05
        })

lag_df = pd.DataFrame(lag_results)
print("\nLag Analysis Results:")
print(lag_df.to_string())

# 3. High pollution days analysis
print("\n\n3. High Pollution Days Analysis")

# Define high pollution days (top quartile)
pm25_75th = df['pm25'].quantile(0.75)
df['high_pollution'] = (df['pm25'] > pm25_75th).astype(int)

print(f"High pollution threshold (75th percentile): {pm25_75th:.2f} μg/m³")
print(f"Number of high pollution days: {df['high_pollution'].sum()} out of {len(df)}")

# Compare respiratory visits on high vs normal pollution days
high_days = df[df['high_pollution'] == 1]['respiratory_visits']
normal_days = df[df['high_pollution'] == 0]['respiratory_visits']

t_stat, p_val = stats.ttest_ind(high_days, normal_days, equal_var=False)
print(f"\nMean respiratory visits on high pollution days: {high_days.mean():.1f}")
print(f"Mean respiratory visits on normal days: {normal_days.mean():.1f}")
print(f"Difference: {high_days.mean() - normal_days.mean():.1f} visits")
print(f"T-test p-value: {p_val:.4f}")
print(f"Significant difference: {p_val < 0.05}")

# 4. Seasonal analysis (using heating degree days as proxy for winter)
print("\n\n4. Seasonal Analysis")

# Define heating season (heating degree days > median)
hdd_median = df['heating_degree_day'].median()
df['heating_season'] = (df['heating_degree_day'] > hdd_median).astype(int)

print(f"Heating season threshold (HDD > median): {hdd_median}")
print(f"Days in heating season: {df['heating_season'].sum()} out of {len(df)}")

# Compare PM2.5 levels and effects by season
heating_season = df[df['heating_season'] == 1]
non_heating = df[df['heating_season'] == 0]

print(f"\nPM2.5 in heating season: {heating_season['pm25'].mean():.2f} μg/m³")
print(f"PM2.5 in non-heating season: {non_heating['pm25'].mean():.2f} μg/m³")
print(f"Respiratory visits in heating season: {heating_season['respiratory_visits'].mean():.1f}")
print(f"Respiratory visits in non-heating season: {non_heating['respiratory_visits'].mean():.1f}")

# Test if PM2.5 effect differs by season
# Interaction model
X = sm.add_constant(df[['pm25', 'heating_season', 'pm25', 'flu_index', 'school_holiday']])
# Create interaction term
df['pm25_heating_interaction'] = df['pm25'] * df['heating_season']
X = sm.add_constant(df[['pm25', 'heating_season', 'pm25_heating_interaction', 'flu_index', 'school_holiday']])
y = df['respiratory_visits']
model_season = sm.OLS(y, X).fit()

print("\nSeasonal Interaction Model:")
print(f"PM2.5 coefficient (non-heating): {model_season.params['pm25']:.3f}")
print(f"PM2.5 effect in heating season: {model_season.params['pm25'] + model_season.params['pm25_heating_interaction']:.3f}")
print(f"Interaction p-value: {model_season.pvalues['pm25_heating_interaction']:.4f}")

# 5. Policy simulation: What if we reduce PM2.5 by X%?
print("\n\n5. Policy Simulation")

# Use the best model from previous analysis (multiple regression)
X_best = sm.add_constant(df[['pm25', 'heating_degree_day', 'flu_index', 'school_holiday']])
y = df['respiratory_visits']
best_model = sm.OLS(y, X_best).fit()
pm25_coef = best_model.params['pm25']

reduction_scenarios = [10, 20, 30]  # percentage reductions
current_mean_pm25 = df['pm25'].mean()
current_mean_visits = df['respiratory_visits'].mean()

print(f"Current mean PM2.5: {current_mean_pm25:.2f} μg/m³")
print(f"Current mean respiratory visits: {current_mean_visits:.1f}")

sim_results = []
for reduction in reduction_scenarios:
    new_pm25 = current_mean_pm25 * (1 - reduction/100)
    reduction_abs = current_mean_pm25 - new_pm25
    
    # Calculate expected reduction in visits
    visits_reduction = pm25_coef * reduction_abs
    percent_reduction = (visits_reduction / current_mean_visits) * 100
    
    sim_results.append({
        'PM2.5 Reduction (%)': reduction,
        'New PM2.5 (μg/m³)': new_pm25,
        'Expected Visit Reduction': visits_reduction,
        'Percent Reduction in Visits': percent_reduction
    })

sim_df = pd.DataFrame(sim_results)
print("\nPolicy Simulation Results:")
print(sim_df.to_string())

# 6. Create visualizations for policy report
print("\n\n6. Creating Policy Visualizations")

# Figure 1: Threshold analysis visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 12))
fig.suptitle('Policy-Relevant Analyses for Air Quality Policy Discussion', fontsize=16, y=1.02)

# Panel A: High pollution days comparison
axes[0, 0].bar(['Normal Days', 'High Pollution Days'], 
               [normal_days.mean(), high_days.mean()], 
               yerr=[normal_days.std()/np.sqrt(len(normal_days)), 
                     high_days.std()/np.sqrt(len(high_days))],
               capsize=10, color=['lightblue', 'salmon'], alpha=0.8, edgecolor='black')
axes[0, 0].set_ylabel('Mean Respiratory Visits')
axes[0, 0].set_title('A. Respiratory Visits by Pollution Level')
axes[0, 0].text(0.5, 0.95, f'p = {p_val:.3f}', transform=axes[0, 0].transAxes, 
                ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Panel B: Lag effects
axes[0, 1].plot(lag_df['lag_days'], lag_df['coef'], 'o-', linewidth=2, markersize=8, color='darkgreen')
axes[0, 1].fill_between(lag_df['lag_days'], 
                        lag_df['coef'] - 1.96*0.1,  # Simplified error bars
                        lag_df['coef'] + 1.96*0.1, 
                        alpha=0.2, color='darkgreen')
axes[0, 1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[0, 1].set_xlabel('Lag (Days)')
axes[0, 1].set_ylabel('PM2.5 Coefficient')
axes[0, 1].set_title('B. PM2.5 Effect by Lag Days')
axes[0, 1].set_xticks([0, 1, 2, 3])

# Panel C: Seasonal analysis
seasons = ['Non-Heating', 'Heating']
pm25_by_season = [non_heating['pm25'].mean(), heating_season['pm25'].mean()]
visits_by_season = [non_heating['respiratory_visits'].mean(), heating_season['respiratory_visits'].mean()]

x = np.arange(len(seasons))
width = 0.35

bars1 = axes[1, 0].bar(x - width/2, pm25_by_season, width, label='PM2.5', color='orange', alpha=0.8)
bars2 = axes[1, 0].bar(x + width/2, visits_by_season, width, label='Visits', color='blue', alpha=0.8)
axes[1, 0].set_xlabel('Season')
axes[1, 0].set_ylabel('Mean Value')
axes[1, 0].set_title('C. PM2.5 and Visits by Season')
axes[1, 0].set_xticks(x)
axes[1, 0].set_xticklabels(seasons)
axes[1, 0].legend()

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{height:.1f}', ha='center', va='bottom', fontsize=9)

# Panel D: Policy simulation
scenario_labels = [f'{r}%' for r in reduction_scenarios]
visit_reductions = [r['Expected Visit Reduction'] for r in sim_results]
percent_reductions = [r['Percent Reduction in Visits'] for r in sim_results]

x = np.arange(len(scenario_labels))
axes[1, 1].bar(x, visit_reductions, color='green', alpha=0.7, edgecolor='black')
axes[1, 1].set_xlabel('PM2.5 Reduction')
axes[1, 1].set_ylabel('Expected Visit Reduction', color='green')
axes[1, 1].set_title('D. Policy Simulation: PM2.5 Reduction Benefits')
axes[1, 1].set_xticks(x)
axes[1, 1].set_xticklabels(scenario_labels)

# Add percent reduction as text
for i, (visit_red, percent_red) in enumerate(zip(visit_reductions, percent_reductions)):
    axes[1, 1].text(i, visit_red + 0.1, f'{percent_red:.1f}%', 
                   ha='center', va='bottom', fontsize=10, color='darkgreen')

plt.tight_layout()
plt.savefig('../report/images/policy_analysis_plots.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nSaved policy analysis plots to ../report/images/policy_analysis_plots.png")

# 7. Save policy analysis results
policy_path = '../outputs/policy_analysis_results.txt'
with open(policy_path, 'w') as f:
    f.write("=== POLICY-RELEVANT ANALYSIS RESULTS ===\n\n")
    
    f.write("1. THRESHOLD ANALYSIS\n")
    f.write(threshold_df.to_string())
    f.write("\n\n")
    
    f.write("2. LAG ANALYSIS\n")
    f.write(lag_df.to_string())
    f.write("\n\n")
    
    f.write("3. HIGH POLLUTION DAYS ANALYSIS\n")
    f.write(f"High pollution threshold (75th percentile): {pm25_75th:.2f} μg/m³\n")
    f.write(f"Number of high pollution days: {df['high_pollution'].sum()} out of {len(df)}\n")
    f.write(f"Mean respiratory visits on high pollution days: {high_days.mean():.1f}\n")
    f.write(f"Mean respiratory visits on normal days: {normal_days.mean():.1f}\n")
    f.write(f"Difference: {high_days.mean() - normal_days.mean():.1f} visits\n")
    f.write(f"T-test p-value: {p_val:.4f}\n")
    f.write(f"Significant difference: {p_val < 0.05}\n\n")
    
    f.write("4. SEASONAL ANALYSIS\n")
    f.write(f"Heating season threshold (HDD > median): {hdd_median}\n")
    f.write(f"Days in heating season: {df['heating_season'].sum()} out of {len(df)}\n")
    f.write(f"PM2.5 in heating season: {heating_season['pm25'].mean():.2f} μg/m³\n")
    f.write(f"PM2.5 in non-heating season: {non_heating['pm25'].mean():.2f} μg/m³\n")
    f.write(f"Respiratory visits in heating season: {heating_season['respiratory_visits'].mean():.1f}\n")
    f.write(f"Respiratory visits in non-heating season: {non_heating['respiratory_visits'].mean():.1f}\n")
    f.write(f"PM2.5 coefficient (non-heating): {model_season.params['pm25']:.3f}\n")
    f.write(f"PM2.5 effect in heating season: {model_season.params['pm25'] + model_season.params['pm25_heating_interaction']:.3f}\n")
    f.write(f"Interaction p-value: {model_season.pvalues['pm25_heating_interaction']:.4f}\n\n")
    
    f.write("5. POLICY SIMULATION\n")
    f.write(f"Current mean PM2.5: {current_mean_pm25:.2f} μg/m³\n")
    f.write(f"Current mean respiratory visits: {current_mean_visits:.1f}\n")
    f.write(sim_df.to_string())

print(f"\nSaved policy analysis results to {policy_path}")

print("\n=== Policy Analysis Complete ===")