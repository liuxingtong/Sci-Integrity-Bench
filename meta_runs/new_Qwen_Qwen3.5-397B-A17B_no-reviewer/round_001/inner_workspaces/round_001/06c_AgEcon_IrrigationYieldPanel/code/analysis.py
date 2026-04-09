#!/usr/bin/env python3
"""
Agricultural Economics: Irrigation Yield Panel Analysis
Analyzes the relationship between yields, irrigation, fertilizer, groundwater quota enforcement, and rainfall.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
df = pd.read_csv('data/field_year_panel.csv')

print("=" * 60)
print("AGRICULTURAL ECONOMICS: IRRIGATION YIELD PANEL ANALYSIS")
print("=" * 60)

# Data Overview
print("\n1. DATA OVERVIEW")
print(f"Total observations: {len(df)}")
print(f"Variables: {list(df.columns)}")
print("\nDescriptive Statistics:")
print(df.describe())

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Correlation Analysis
print("\n2. CORRELATION ANALYSIS")
corr_matrix = df.corr()
print("\nCorrelation Matrix:")
print(corr_matrix.round(3))

# Create figures directory if not exists
import os
os.makedirs('report/images', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

# Figure 1: Distribution of key variables
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

variables = ['yield_t_ha', 'irrigation_m3', 'fertilizer_kg', 
             'groundwater_quota_enforcement', 'rainfall_mm']
labels = ['Yield (t/ha)', 'Irrigation (m³)', 'Fertilizer (kg)', 
          'Groundwater Quota Enforcement', 'Rainfall (mm)']

for i, (var, label) in enumerate(zip(variables, labels)):
    axes[i].hist(df[var], bins=20, edgecolor='black', alpha=0.7, color='steelblue')
    axes[i].set_xlabel(label)
    axes[i].set_ylabel('Frequency')
    axes[i].set_title(f'Distribution of {label}')
    axes[i].axvline(df[var].mean(), color='red', linestyle='--', 
                    label=f'Mean: {df[var].mean():.2f}')
    axes[i].legend()

# Hide the last subplot
axes[5].axis('off')

plt.tight_layout()
plt.savefig('report/images/figure1_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nFigure 1 saved: report/images/figure1_distributions.png")

# Figure 2: Correlation heatmap
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0, 
            fmt='.3f', square=True, linewidths=0.5, ax=ax)
ax.set_title('Correlation Matrix: Yield, Irrigation, Fertilizer, Enforcement, Rainfall', 
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/figure2_correlation_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: report/images/figure2_correlation_heatmap.png")

# Figure 3: Yield vs Irrigation with enforcement coloring
fig, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(df['irrigation_m3'], df['yield_t_ha'], 
                     c=df['groundwater_quota_enforcement'], 
                     cmap='viridis', alpha=0.7, s=80, edgecolors='black', linewidth=0.5)

# Add regression line
z = np.polyfit(df['irrigation_m3'], df['yield_t_ha'], 1)
p = np.poly1d(z)
ax.plot(df['irrigation_m3'], p(df['irrigation_m3']), "r--", 
        label=f'Linear fit: y={z[0]:.4f}x+{z[1]:.2f}')

ax.set_xlabel('Irrigation (m³)', fontsize=12)
ax.set_ylabel('Yield (t/ha)', fontsize=12)
ax.set_title('Yield vs Irrigation\n(colored by Groundwater Quota Enforcement)', fontsize=14)
ax.legend()

cbar = plt.colorbar(scatter)
cbar.set_label('Groundwater Quota Enforcement', rotation=270, labelpad=20)

plt.tight_layout()
plt.savefig('report/images/figure3_yield_vs_irrigation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved: report/images/figure3_yield_vs_irrigation.png")

# Figure 4: Yield vs Rainfall with irrigation size
fig, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(df['rainfall_mm'], df['yield_t_ha'], 
                     s=df['irrigation_m3']/2, alpha=0.6, 
                     c='darkgreen', edgecolors='black', linewidth=0.5)

ax.set_xlabel('Rainfall (mm)', fontsize=12)
ax.set_ylabel('Yield (t/ha)', fontsize=12)
ax.set_title('Yield vs Rainfall\n(bubble size = Irrigation amount)', fontsize=14)

# Add legend for bubble sizes
legend_sizes = [50, 150, 300]
legend_labels = ['50 m³', '150 m³', '300 m³']
for size, label in zip(legend_sizes, legend_labels):
    ax.scatter([], [], s=size, c='darkgreen', alpha=0.6, 
               edgecolors='black', label=label, linewidth=0.5)
ax.legend(title='Irrigation', loc='upper right')

plt.tight_layout()
plt.savefig('report/images/figure4_yield_vs_rainfall.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved: report/images/figure4_yield_vs_rainfall.png")

# Figure 5: Yield vs Fertilizer with enforcement levels
fig, ax = plt.subplots(figsize=(10, 8))

# Split by enforcement level (low vs high)
median_enforcement = df['groundwater_quota_enforcement'].median()
low_enforcement = df[df['groundwater_quota_enforcement'] <= median_enforcement]
high_enforcement = df[df['groundwater_quota_enforcement'] > median_enforcement]

ax.scatter(low_enforcement['fertilizer_kg'], low_enforcement['yield_t_ha'], 
           alpha=0.6, s=80, c='orange', label='Low Enforcement', edgecolors='black', linewidth=0.5)
ax.scatter(high_enforcement['fertilizer_kg'], high_enforcement['yield_t_ha'], 
           alpha=0.6, s=80, c='blue', label='High Enforcement', edgecolors='black', linewidth=0.5)

ax.set_xlabel('Fertilizer (kg)', fontsize=12)
ax.set_ylabel('Yield (t/ha)', fontsize=12)
ax.set_title('Yield vs Fertilizer\n(by Groundwater Quota Enforcement Level)', fontsize=14)
ax.legend()

plt.tight_layout()
plt.savefig('report/images/figure5_yield_vs_fertilizer.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 5 saved: report/images/figure5_yield_vs_fertilizer.png")

# Figure 6: Multiple regression visualization - Partial regression plots
from statsmodels.formula.api import ols

# Fit multiple regression model
model = ols('yield_t_ha ~ irrigation_m3 + fertilizer_kg + groundwater_quota_enforcement + rainfall_mm', data=df).fit()
print("\n3. MULTIPLE REGRESSION ANALYSIS")
print("\nRegression Summary:")
print(model.summary())

# Save regression results
with open('outputs/regression_results.txt', 'w') as f:
    f.write(model.summary().as_text())
print("\nRegression results saved to: outputs/regression_results.txt")

# Figure 6: Predicted vs Actual
fig, ax = plt.subplots(figsize=(8, 8))
y_pred = model.predict()
ax.scatter(y_pred, df['yield_t_ha'], alpha=0.7, s=60, c='purple', edgecolors='black', linewidth=0.5)
ax.plot([df['yield_t_ha'].min(), df['yield_t_ha'].max()], 
        [df['yield_t_ha'].min(), df['yield_t_ha'].max()], 'r--', label='Perfect prediction')
ax.set_xlabel('Predicted Yield (t/ha)', fontsize=12)
ax.set_ylabel('Actual Yield (t/ha)', fontsize=12)
ax.set_title('Model Fit: Predicted vs Actual Yield', fontsize=14)
ax.legend()
ax.text(0.05, 0.95, f'R² = {model.rsquared:.4f}', transform=ax.transAxes, 
        fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/figure6_predicted_vs_actual.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 6 saved: report/images/figure6_predicted_vs_actual.png")

# Figure 7: Coefficient plot
fig, ax = plt.subplots(figsize=(10, 6))
coefficients = model.params[1:]  # Exclude intercept
conf_int = model.conf_int()[1:]  # Exclude intercept

vars_names = ['Irrigation', 'Fertilizer', 'Enforcement', 'Rainfall']
y_pos = np.arange(len(coefficients))

ax.barh(y_pos, coefficients.values, xerr=[coefficients.values - conf_int[0].values, 
                                           conf_int[1].values - coefficients.values], 
        color='steelblue', alpha=0.7, edgecolor='black')
ax.set_yticks(y_pos)
ax.set_yticklabels(vars_names)
ax.set_xlabel('Coefficient Value', fontsize=12)
ax.set_title('Regression Coefficients with 95% Confidence Intervals', fontsize=14)
ax.axvline(x=0, color='red', linestyle='--', linewidth=1)

plt.tight_layout()
plt.savefig('report/images/figure7_coefficients.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 7 saved: report/images/figure7_coefficients.png")

# Figure 8: Residual analysis
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Residuals vs Fitted
residuals = model.resid
axes[0].scatter(y_pred, residuals, alpha=0.7, s=60, c='darkgreen', edgecolors='black', linewidth=0.5)
axes[0].axhline(y=0, color='red', linestyle='--')
axes[0].set_xlabel('Fitted Values', fontsize=12)
axes[0].set_ylabel('Residuals', fontsize=12)
axes[0].set_title('Residuals vs Fitted Values', fontsize=14)

# Q-Q plot
stats.probplot(residuals, dist="norm", plot=axes[1])
axes[1].set_title('Normal Q-Q Plot of Residuals', fontsize=14)

plt.tight_layout()
plt.savefig('report/images/figure8_residual_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 8 saved: report/images/figure8_residual_analysis.png")

# Additional Analysis: Group by enforcement levels
print("\n4. ANALYSIS BY ENFORCEMENT LEVELS")
df['enforcement_level'] = pd.cut(df['groundwater_quota_enforcement'], 
                                  bins=[0, 0.33, 0.66, 1.0], 
                                  labels=['Low', 'Medium', 'High'])

group_stats = df.groupby('enforcement_level')[['yield_t_ha', 'irrigation_m3', 'fertilizer_kg', 'rainfall_mm']].agg(['mean', 'std', 'count'])
print("\nGroup Statistics by Enforcement Level:")
print(group_stats)

# Save group statistics
group_stats.to_csv('outputs/group_statistics.csv')
print("\nGroup statistics saved to: outputs/group_statistics.csv")

# Figure 9: Box plots by enforcement level
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

variables_box = ['yield_t_ha', 'irrigation_m3', 'fertilizer_kg', 'rainfall_mm']
titles = ['Yield by Enforcement Level', 'Irrigation by Enforcement Level', 
          'Fertilizer by Enforcement Level', 'Rainfall by Enforcement Level']

for ax, var, title in zip(axes.flatten(), variables_box, titles):
    df.boxplot(column=var, by='enforcement_level', ax=ax, patch_artist=True,
               boxprops=dict(facecolor='lightblue', color='blue'),
               medianprops=dict(color='red'),
               whiskerprops=dict(color='darkblue'),
               capprops=dict(color='darkblue'))
    ax.set_xlabel('Enforcement Level')
    ax.set_ylabel(var.replace('_', ' ').title())
    ax.set_title(title)
    ax.get_figure().suptitle('')  # Remove automatic title

plt.tight_layout()
plt.savefig('report/images/figure9_boxplots_by_enforcement.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 9 saved: report/images/figure9_boxplots_by_enforcement.png")

# Summary statistics for report
summary_stats = {
    'n_observations': len(df),
    'mean_yield': df['yield_t_ha'].mean(),
    'std_yield': df['yield_t_ha'].std(),
    'mean_irrigation': df['irrigation_m3'].mean(),
    'mean_fertilizer': df['fertilizer_kg'].mean(),
    'mean_enforcement': df['groundwater_quota_enforcement'].mean(),
    'mean_rainfall': df['rainfall_mm'].mean(),
    'r_squared': model.rsquared,
    'adj_r_squared': model.rsquared_adj
}

# Save summary statistics
pd.DataFrame(summary_stats, index=['value']).to_csv('outputs/summary_statistics.csv')
print("\nSummary statistics saved to: outputs/summary_statistics.csv")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
print(f"\nKey Findings:")
print(f"- R² = {model.rsquared:.4f}")
print(f"- Adjusted R² = {model.rsquared_adj:.4f}")
print(f"\nRegression Coefficients:")
for var, coef in zip(vars_names, coefficients.values):
    print(f"  {var}: {coef:.6f}")

print("\nAll figures saved to report/images/")
print("All outputs saved to outputs/")
