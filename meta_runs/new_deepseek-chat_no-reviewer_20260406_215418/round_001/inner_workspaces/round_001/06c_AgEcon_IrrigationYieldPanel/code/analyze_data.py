import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load the data
df = pd.read_csv('data/field_year_panel.csv')
print("Data loaded. Shape:", df.shape)

# 1. Correlation analysis
print("\n=== Correlation Analysis ===")
corr_matrix = df.corr()
print("Correlation matrix:")
print(corr_matrix)

# Save correlation matrix
corr_matrix.to_csv('outputs/correlation_matrix.csv')

# 2. Visualize distributions
print("\n=== Creating Distribution Plots ===")
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

variables = ['yield_t_ha', 'irrigation_m3', 'fertilizer_kg', 
             'groundwater_quota_enforcement', 'rainfall_mm']

for i, var in enumerate(variables):
    ax = axes[i]
    df[var].hist(ax=ax, bins=15, edgecolor='black')
    ax.set_title(f'Distribution of {var}')
    ax.set_xlabel(var)
    ax.set_ylabel('Frequency')

# Hide the last subplot (6th) since we only have 5 variables
axes[-1].set_visible(False)

plt.tight_layout()
plt.savefig('report/images/distributions.png', dpi=300, bbox_inches='tight')
print("Saved distributions.png")

# 3. Scatter plots of yield vs key variables
print("\n=== Creating Scatter Plots ===")
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

# Yield vs irrigation
axes[0].scatter(df['irrigation_m3'], df['yield_t_ha'], alpha=0.7)
axes[0].set_xlabel('Irrigation (m3)')
axes[0].set_ylabel('Yield (t/ha)')
axes[0].set_title('Yield vs Irrigation')

# Add trend line
z = np.polyfit(df['irrigation_m3'], df['yield_t_ha'], 1)
p = np.poly1d(z)
axes[0].plot(df['irrigation_m3'], p(df['irrigation_m3']), "r--", alpha=0.8)

# Yield vs fertilizer
axes[1].scatter(df['fertilizer_kg'], df['yield_t_ha'], alpha=0.7)
axes[1].set_xlabel('Fertilizer (kg)')
axes[1].set_ylabel('Yield (t/ha)')
axes[1].set_title('Yield vs Fertilizer')

# Add trend line
z = np.polyfit(df['fertilizer_kg'], df['yield_t_ha'], 1)
p = np.poly1d(z)
axes[1].plot(df['fertilizer_kg'], p(df['fertilizer_kg']), "r--", alpha=0.8)

# Yield vs rainfall
axes[2].scatter(df['rainfall_mm'], df['yield_t_ha'], alpha=0.7)
axes[2].set_xlabel('Rainfall (mm)')
axes[2].set_ylabel('Yield (t/ha)')
axes[2].set_title('Yield vs Rainfall')

# Add trend line
z = np.polyfit(df['rainfall_mm'], df['yield_t_ha'], 1)
p = np.poly1d(z)
axes[2].plot(df['rainfall_mm'], p(df['rainfall_mm']), "r--", alpha=0.8)

# Yield vs groundwater quota enforcement
axes[3].scatter(df['groundwater_quota_enforcement'], df['yield_t_ha'], alpha=0.7)
axes[3].set_xlabel('Groundwater Quota Enforcement')
axes[3].set_ylabel('Yield (t/ha)')
axes[3].set_title('Yield vs Groundwater Quota Enforcement')

# Add trend line
z = np.polyfit(df['groundwater_quota_enforcement'], df['yield_t_ha'], 1)
p = np.poly1d(z)
axes[3].plot(df['groundwater_quota_enforcement'], p(df['groundwater_quota_enforcement']), "r--", alpha=0.8)

plt.tight_layout()
plt.savefig('report/images/yield_scatter_plots.png', dpi=300, bbox_inches='tight')
print("Saved yield_scatter_plots.png")

# 4. Correlation heatmap
print("\n=== Creating Correlation Heatmap ===")
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8})
plt.title('Correlation Heatmap')
plt.tight_layout()
plt.savefig('report/images/correlation_heatmap.png', dpi=300, bbox_inches='tight')
print("Saved correlation_heatmap.png")

# 5. Pairplot for multivariate relationships
print("\n=== Creating Pairplot ===")
g = sns.pairplot(df[variables], diag_kind='kde', corner=False)
g.fig.suptitle('Pairplot of Key Variables', y=1.02)
plt.tight_layout()
g.savefig('report/images/pairplot.png', dpi=300, bbox_inches='tight')
print("Saved pairplot.png")

# 6. Regression analysis
print("\n=== Regression Analysis ===")
# Prepare data for regression
X = df[['irrigation_m3', 'fertilizer_kg', 'groundwater_quota_enforcement', 'rainfall_mm']]
X = sm.add_constant(X)  # Add constant term
Y = df['yield_t_ha']

# Fit OLS model
model = sm.OLS(Y, X).fit()
print(model.summary())

# Save regression results
with open('outputs/regression_results.txt', 'w') as f:
    f.write(str(model.summary()))

# 7. Check for interaction effects
print("\n=== Testing Interaction Effects ===")
# Test interaction between irrigation and groundwater quota enforcement
df['irrigation_x_enforcement'] = df['irrigation_m3'] * df['groundwater_quota_enforcement']

X_interaction = df[['irrigation_m3', 'fertilizer_kg', 'groundwater_quota_enforcement', 
                    'rainfall_mm', 'irrigation_x_enforcement']]
X_interaction = sm.add_constant(X_interaction)
model_interaction = sm.OLS(Y, X_interaction).fit()
print("\nModel with irrigation*enforcement interaction:")
print(model_interaction.summary())

# Save interaction model results
with open('outputs/interaction_model_results.txt', 'w') as f:
    f.write(str(model_interaction.summary()))

# 8. Analyze by groundwater quota enforcement levels
print("\n=== Analysis by Enforcement Levels ===")
# Create enforcement categories
bins = [0, 0.33, 0.66, 1.0]
labels = ['Low', 'Medium', 'High']
df['enforcement_level'] = pd.cut(df['groundwater_quota_enforcement'], bins=bins, labels=labels)

# Summary statistics by enforcement level
enforcement_stats = df.groupby('enforcement_level').agg({
    'yield_t_ha': ['mean', 'std', 'count'],
    'irrigation_m3': ['mean', 'std'],
    'rainfall_mm': ['mean', 'std']
}).round(3)

print("\nStatistics by groundwater quota enforcement level:")
print(enforcement_stats)

# Save enforcement level statistics
enforcement_stats.to_csv('outputs/enforcement_level_stats.csv')

# 9. Visualize yield by enforcement level
print("\n=== Creating Enforcement Level Visualization ===")
plt.figure(figsize=(10, 6))
sns.boxplot(x='enforcement_level', y='yield_t_ha', data=df)
plt.xlabel('Groundwater Quota Enforcement Level')
plt.ylabel('Yield (t/ha)')
plt.title('Yield Distribution by Groundwater Quota Enforcement Level')
plt.tight_layout()
plt.savefig('report/images/yield_by_enforcement.png', dpi=300, bbox_inches='tight')
print("Saved yield_by_enforcement.png")

# 10. Irrigation efficiency analysis
print("\n=== Irrigation Efficiency Analysis ===")
# Calculate yield per unit of irrigation
df['yield_per_irrigation'] = df['yield_t_ha'] / df['irrigation_m3']
# Handle infinite values (where irrigation is 0)
df['yield_per_irrigation'] = df['yield_per_irrigation'].replace([np.inf, -np.inf], np.nan)

# Scatter plot of irrigation efficiency vs enforcement
plt.figure(figsize=(10, 6))
plt.scatter(df['groundwater_quota_enforcement'], df['yield_per_irrigation'], alpha=0.7)
plt.xlabel('Groundwater Quota Enforcement')
plt.ylabel('Yield per Irrigation (t/ha per m3)')
plt.title('Irrigation Efficiency vs Groundwater Quota Enforcement')

# Add trend line
valid_data = df.dropna(subset=['yield_per_irrigation'])
if len(valid_data) > 1:
    z = np.polyfit(valid_data['groundwater_quota_enforcement'], 
                   valid_data['yield_per_irrigation'], 1)
    p = np.poly1d(z)
    plt.plot(valid_data['groundwater_quota_enforcement'], 
             p(valid_data['groundwater_quota_enforcement']), "r--", alpha=0.8)

plt.tight_layout()
plt.savefig('report/images/irrigation_efficiency.png', dpi=300, bbox_inches='tight')
print("Saved irrigation_efficiency.png")

print("\n=== Analysis Complete ===")
print("All outputs saved to outputs/ and report/images/")