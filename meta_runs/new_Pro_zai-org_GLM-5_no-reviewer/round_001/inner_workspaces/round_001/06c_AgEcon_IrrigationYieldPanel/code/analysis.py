import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
import os
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
df = pd.read_csv('../data/field_year_panel.csv')

print("="*60)
print("AGRICULTURAL IRRIGATION PROGRAM ANALYSIS")
print("="*60)

# =============================================================================
# 1. DATA OVERVIEW
# =============================================================================
print("\n1. DATA OVERVIEW")
print("-"*40)
print(f"Number of observations: {len(df)}")
print(f"Number of unique plots: {df['plot_id'].nunique()}")
print("\nVariable Summary:")
print(df.describe().round(3))

# Check for missing values
print(f"\nMissing values:\n{df.isnull().sum()}")

# =============================================================================
# 2. CORRELATION ANALYSIS
# =============================================================================
print("\n2. CORRELATION ANALYSIS")
print("-"*40)
corr_matrix = df[['yield_t_ha', 'irrigation_m3', 'fertilizer_kg', 
                   'groundwater_quota_enforcement', 'rainfall_mm']].corr()
print(corr_matrix.round(3))

# Save correlation matrix
corr_matrix.to_csv('../outputs/correlation_matrix.csv')

# =============================================================================
# 3. FIGURE 1: CORRELATION HEATMAP
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0, 
            fmt='.3f', square=True, linewidths=0.5,
            annot_kws={'size': 12})
plt.title('Correlation Matrix: Yield, Irrigation, and Policy Variables', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('../report/images/fig1_correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nFigure 1 saved: Correlation Heatmap")

# =============================================================================
# 4. FIGURE 2: DISTRIBUTION OF KEY VARIABLES
# =============================================================================
fig, axes = plt.subplots(2, 3, figsize=(14, 8))

variables = ['yield_t_ha', 'irrigation_m3', 'fertilizer_kg', 
             'groundwater_quota_enforcement', 'rainfall_mm']
titles = ['Yield (t/ha)', 'Irrigation (m³)', 'Fertilizer (kg)', 
          'Groundwater Quota Enforcement', 'Rainfall (mm)']
colors = ['#2ecc71', '#3498db', '#e74c3c', '#9b59b6', '#f39c12']

for idx, (var, title, color) in enumerate(zip(variables, titles, colors)):
    row = idx // 3
    col = idx % 3
    axes[row, col].hist(df[var], bins=20, color=color, edgecolor='white', alpha=0.7)
    axes[row, col].set_xlabel(title, fontsize=10)
    axes[row, col].set_ylabel('Frequency', fontsize=10)
    axes[row, col].set_title(f'Distribution of {title}', fontsize=11, fontweight='bold')

# Remove empty subplot
axes[1, 2].axis('off')
plt.suptitle('Distribution of Agricultural Variables', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('../report/images/fig2_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: Variable Distributions")

# =============================================================================
# 5. FIGURE 3: IRRIGATION VS YIELD SCATTER PLOT
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(df['irrigation_m3'], df['yield_t_ha'], 
                     c=df['groundwater_quota_enforcement'], cmap='viridis',
                     s=60, alpha=0.7, edgecolors='white', linewidth=0.5)
plt.colorbar(scatter, label='Groundwater Quota Enforcement')

# Add regression line
z = np.polyfit(df['irrigation_m3'], df['yield_t_ha'], 1)
p = np.poly1d(z)
x_line = np.linspace(df['irrigation_m3'].min(), df['irrigation_m3'].max(), 100)
ax.plot(x_line, p(x_line), 'r--', linewidth=2, label=f'Trend line (slope={z[0]:.4f})')

ax.set_xlabel('Irrigation (m³)', fontsize=12)
ax.set_ylabel('Yield (t/ha)', fontsize=12)
ax.set_title('Irrigation vs Yield: Impact of Groundwater Policy', fontsize=14, fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig('../report/images/fig3_irrigation_yield_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved: Irrigation vs Yield Scatter")

# =============================================================================
# 6. FIGURE 4: RAINFALL VS YIELD BY IRRIGATION LEVEL
# =============================================================================
# Create irrigation quartiles
df['irrigation_quartile'] = pd.qcut(df['irrigation_m3'], q=4, labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'])

fig, ax = plt.subplots(figsize=(10, 6))
colors = ['#e74c3c', '#f39c12', '#2ecc71', '#3498db']
for i, quartile in enumerate(['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)']):
    subset = df[df['irrigation_quartile'] == quartile]
    ax.scatter(subset['rainfall_mm'], subset['yield_t_ha'], 
               c=colors[i], label=quartile, alpha=0.6, s=50)

ax.set_xlabel('Rainfall (mm)', fontsize=12)
ax.set_ylabel('Yield (t/ha)', fontsize=12)
ax.set_title('Rainfall vs Yield by Irrigation Level', fontsize=14, fontweight='bold')
ax.legend(title='Irrigation Quartile')
plt.tight_layout()
plt.savefig('../report/images/fig4_rainfall_yield_by_irrigation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved: Rainfall vs Yield by Irrigation")

# =============================================================================
# 7. REGRESSION ANALYSIS
# =============================================================================
print("\n3. REGRESSION ANALYSIS")
print("-"*40)

# Model 1: Basic yield model
model1 = ols('yield_t_ha ~ irrigation_m3 + fertilizer_kg + rainfall_mm', data=df).fit()
print("\nModel 1: Basic Yield Model")
print(model1.summary().tables[1])

# Model 2: With policy variable
model2 = ols('yield_t_ha ~ irrigation_m3 + fertilizer_kg + rainfall_mm + groundwater_quota_enforcement', data=df).fit()
print("\nModel 2: With Groundwater Quota Enforcement")
print(model2.summary().tables[1])

# Model 3: With interaction term
model3 = ols('yield_t_ha ~ irrigation_m3 + fertilizer_kg + rainfall_mm + groundwater_quota_enforcement + irrigation_m3:groundwater_quota_enforcement', data=df).fit()
print("\nModel 3: With Irrigation × Policy Interaction")
print(model3.summary().tables[1])

# Save regression results
with open('../outputs/regression_results.txt', 'w') as f:
    f.write("REGRESSION ANALYSIS RESULTS\n")
    f.write("="*60 + "\n\n")
    f.write("Model 1: Basic Yield Model\n")
    f.write(str(model1.summary()))
    f.write("\n\n" + "="*60 + "\n")
    f.write("Model 2: With Groundwater Quota Enforcement\n")
    f.write(str(model2.summary()))
    f.write("\n\n" + "="*60 + "\n")
    f.write("Model 3: With Irrigation × Policy Interaction\n")
    f.write(str(model3.summary()))

print("\nRegression results saved to outputs/regression_results.txt")

# =============================================================================
# 8. FIGURE 5: REGRESSION COEFFICIENTS COMPARISON
# =============================================================================
fig, ax = plt.subplots(figsize=(12, 6))

# Extract coefficients from all models
models = [model1, model2, model3]
model_names = ['Model 1\n(Basic)', 'Model 2\n(+ Policy)', 'Model 3\n(+ Interaction)']

# Get common coefficients
coef_data = []
for i, model in enumerate(models):
    for var in model.params.index:
        if 'Intercept' not in var:
            coef_data.append({
                'Variable': var.replace('groundwater_quota_enforcement', 'Policy'),
                'Coefficient': model.params[var],
                'Std_Err': model.bse[var],
                'Model': model_names[i]
            })

coef_df = pd.DataFrame(coef_data)

# Plot
variables_to_plot = ['irrigation_m3', 'fertilizer_kg', 'rainfall_mm', 'Policy', 'irrigation_m3:Policy']
colors = {'Model 1\n(Basic)': '#3498db', 'Model 2\n(+ Policy)': '#2ecc71', 'Model 3\n(+ Interaction)': '#e74c3c'}

x_pos = 0
for var in variables_to_plot:
    subset = coef_df[coef_df['Variable'] == var]
    if len(subset) > 0:
        for idx, row in subset.iterrows():
            ax.bar(x_pos, row['Coefficient'], yerr=row['Std_Err']*1.96, 
                   color=colors[row['Model']], alpha=0.7, capsize=3)
            x_pos += 1
    else:
        x_pos += 3

ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.set_ylabel('Coefficient Value', fontsize=12)
ax.set_title('Regression Coefficients Across Models (with 95% CI)', fontsize=14, fontweight='bold')

# Create legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=colors[m], label=m) for m in model_names]
ax.legend(handles=legend_elements, loc='upper right')

plt.tight_layout()
plt.savefig('../report/images/fig5_regression_coefficients.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 5 saved: Regression Coefficients")

# =============================================================================
# 9. FIGURE 6: POLICY ENFORCEMENT IMPACT
# =============================================================================
# Create policy enforcement categories
df['policy_level'] = pd.cut(df['groundwater_quota_enforcement'], 
                            bins=[0, 0.33, 0.66, 1.0], 
                            labels=['Low (0-0.33)', 'Medium (0.33-0.66)', 'High (0.66-1.0)'])

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Panel A: Yield by Policy Level
policy_stats = df.groupby('policy_level').agg({
    'yield_t_ha': ['mean', 'std'],
    'irrigation_m3': ['mean', 'std']
}).reset_index()
policy_stats.columns = ['policy_level', 'yield_mean', 'yield_std', 'irrigation_mean', 'irrigation_std']

x = range(3)
axes[0].bar(x, policy_stats['yield_mean'], yerr=policy_stats['yield_std'], 
            color=['#e74c3c', '#f39c12', '#2ecc71'], capsize=5, alpha=0.7)
axes[0].set_xticks(x)
axes[0].set_xticklabels(['Low', 'Medium', 'High'])
axes[0].set_xlabel('Policy Enforcement Level', fontsize=12)
axes[0].set_ylabel('Mean Yield (t/ha)', fontsize=12)
axes[0].set_title('A: Yield by Policy Enforcement Level', fontsize=12, fontweight='bold')

# Panel B: Irrigation by Policy Level
axes[1].bar(x, policy_stats['irrigation_mean'], yerr=policy_stats['irrigation_std'],
            color=['#e74c3c', '#f39c12', '#2ecc71'], capsize=5, alpha=0.7)
axes[1].set_xticks(x)
axes[1].set_xticklabels(['Low', 'Medium', 'High'])
axes[1].set_xlabel('Policy Enforcement Level', fontsize=12)
axes[1].set_ylabel('Mean Irrigation (m³)', fontsize=12)
axes[1].set_title('B: Irrigation by Policy Enforcement Level', fontsize=12, fontweight='bold')

plt.suptitle('Impact of Groundwater Quota Enforcement', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('../report/images/fig6_policy_impact.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 6 saved: Policy Impact")

# =============================================================================
# 10. FIGURE 7: MARGINAL PRODUCTIVITY ANALYSIS
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Panel A: Irrigation efficiency by rainfall
df['rainfall_category'] = pd.cut(df['rainfall_mm'], bins=[0, 200, 400, 600, 800], 
                                  labels=['Low (<200)', 'Medium (200-400)', 
                                          'High (400-600)', 'Very High (>600)'])

rainfall_irrig = df.groupby('rainfall_category').agg({
    'irrigation_m3': 'mean',
    'yield_t_ha': 'mean'
}).reset_index()

axes[0].bar(range(len(rainfall_irrig)), rainfall_irrig['irrigation_m3'], 
            color=['#c0392b', '#e74c3c', '#52be80', '#27ae60'], alpha=0.7)
axes[0].set_xticks(range(len(rainfall_irrig)))
axes[0].set_xticklabels(['Low', 'Medium', 'High', 'Very High'], rotation=0)
axes[0].set_xlabel('Rainfall Category', fontsize=12)
axes[0].set_ylabel('Mean Irrigation (m³)', fontsize=12)
axes[0].set_title('A: Irrigation Use by Rainfall Level', fontsize=12, fontweight='bold')

# Panel B: Yield response to irrigation at different policy levels
for i, policy in enumerate(['Low (0-0.33)', 'Medium (0.33-0.66)', 'High (0.66-1.0)']):
    subset = df[df['policy_level'] == policy]
    axes[1].scatter(subset['irrigation_m3'], subset['yield_t_ha'], 
                    label=policy, alpha=0.5, s=40)

axes[1].set_xlabel('Irrigation (m³)', fontsize=12)
axes[1].set_ylabel('Yield (t/ha)', fontsize=12)
axes[1].set_title('B: Yield-Irrigation Relationship by Policy Level', fontsize=12, fontweight='bold')
axes[1].legend(title='Policy Level')

plt.suptitle('Irrigation Efficiency and Water Management', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('../report/images/fig7_irrigation_efficiency.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 7 saved: Irrigation Efficiency")

# =============================================================================
# 11. SUMMARY STATISTICS
# =============================================================================
print("\n4. SUMMARY STATISTICS BY GROUPS")
print("-"*40)

# By policy level
print("\nYield and Irrigation by Policy Enforcement Level:")
print(df.groupby('policy_level')[['yield_t_ha', 'irrigation_m3', 'fertilizer_kg']].mean().round(3))

# By rainfall category
print("\nYield and Irrigation by Rainfall Category:")
print(df.groupby('rainfall_category')[['yield_t_ha', 'irrigation_m3']].mean().round(3))

# Save summary statistics
summary_stats = df.groupby('policy_level')[['yield_t_ha', 'irrigation_m3', 'fertilizer_kg', 'rainfall_mm']].agg(['mean', 'std', 'count'])
summary_stats.to_csv('../outputs/summary_by_policy.csv')

# =============================================================================
# 12. KEY FINDINGS
# =============================================================================
print("\n" + "="*60)
print("KEY FINDINGS")
print("="*60)

# Calculate key metrics
irrigation_yield_corr = df['irrigation_m3'].corr(df['yield_t_ha'])
policy_irrigation_corr = df['groundwater_quota_enforcement'].corr(df['irrigation_m3'])
policy_yield_corr = df['groundwater_quota_enforcement'].corr(df['yield_t_ha'])

print(f"\n1. Irrigation-Yield Correlation: {irrigation_yield_corr:.3f}")
print(f"2. Policy-Irrigation Correlation: {policy_irrigation_corr:.3f}")
print(f"3. Policy-Yield Correlation: {policy_yield_corr:.3f}")

# Model comparison
print(f"\n4. Model R-squared Comparison:")
print(f"   - Model 1 (Basic): R² = {model1.rsquared:.3f}")
print(f"   - Model 2 (+ Policy): R² = {model2.rsquared:.3f}")
print(f"   - Model 3 (+ Interaction): R² = {model3.rsquared:.3f}")

# Policy effectiveness
low_policy_yield = df[df['policy_level'] == 'Low (0-0.33)']['yield_t_ha'].mean()
high_policy_yield = df[df['policy_level'] == 'High (0.66-1.0)']['yield_t_ha'].mean()
low_policy_irrig = df[df['policy_level'] == 'Low (0-0.33)']['irrigation_m3'].mean()
high_policy_irrig = df[df['policy_level'] == 'High (0.66-1.0)']['irrigation_m3'].mean()

print(f"\n5. Policy Impact Analysis:")
print(f"   - Low Policy Enforcement: Yield = {low_policy_yield:.2f} t/ha, Irrigation = {low_policy_irrig:.1f} m³")
print(f"   - High Policy Enforcement: Yield = {high_policy_yield:.2f} t/ha, Irrigation = {high_policy_irrig:.1f} m³")
print(f"   - Yield Difference: {high_policy_yield - low_policy_yield:.2f} t/ha ({((high_policy_yield - low_policy_yield)/low_policy_yield)*100:.1f}%)")
print(f"   - Irrigation Difference: {high_policy_irrig - low_policy_irrig:.1f} m³ ({((high_policy_irrig - low_policy_irrig)/low_policy_irrig)*100:.1f}%)")

print("\n" + "="*60)
print("Analysis complete. Results saved to outputs/ and report/images/")
print("="*60)
