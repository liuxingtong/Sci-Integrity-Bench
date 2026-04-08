"""
AgEcon Irrigation Yield Panel Analysis
======================================

This script analyzes the relationship between irrigation programs and crop yields
using a field-year panel dataset. Key variables include:
- yield_t_ha: Crop yield (tons per hectare)
- irrigation_m3: Irrigation water applied (cubic meters)
- fertilizer_kg: Fertilizer applied (kg)
- groundwater_quota_enforcement: Policy enforcement level (0-1)
- rainfall_mm: Annual rainfall (mm)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
print("Loading data...")
df = pd.read_csv('data/field_year_panel.csv')
print(f"Dataset shape: {df.shape}")
print(f"\nColumn names: {df.columns.tolist()}")
print(f"\nFirst few rows:")
print(df.head())

# Data overview
print("\n" + "="*60)
print("DATA OVERVIEW")
print("="*60)
print(f"\nDescriptive Statistics:")
print(df.describe())

# Check for missing values
print(f"\nMissing values:\n{df.isnull().sum()}")

# Correlation analysis
print("\n" + "="*60)
print("CORRELATION ANALYSIS")
print("="*60)
corr_matrix = df.corr()
print("\nCorrelation Matrix:")
print(corr_matrix.round(3))

# Create correlation heatmap
fig, ax = plt.subplots(figsize=(10, 8))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.3f', cmap='RdBu_r', 
            center=0, square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)
ax.set_title('Correlation Matrix of Irrigation Program Variables', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/correlation_heatmap.png")

# Distribution analysis
print("\n" + "="*60)
print("DISTRIBUTION ANALYSIS")
print("="*60)

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

variables = ['yield_t_ha', 'irrigation_m3', 'fertilizer_kg', 
             'groundwater_quota_enforcement', 'rainfall_mm']
titles = ['Crop Yield (t/ha)', 'Irrigation (m³)', 'Fertilizer (kg)',
          'Groundwater Quota Enforcement', 'Rainfall (mm)']

for i, (var, title) in enumerate(zip(variables, titles)):
    ax = axes[i]
    ax.hist(df[var], bins=20, edgecolor='black', alpha=0.7, color='steelblue')
    ax.set_xlabel(title, fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title(f'Distribution of {title}', fontsize=12, fontweight='bold')
    ax.axvline(df[var].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df[var].mean():.2f}')
    ax.legend()

axes[5].axis('off')
plt.tight_layout()
plt.savefig('report/images/distributions.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/distributions.png")

# Key relationship: Irrigation vs Yield
print("\n" + "="*60)
print("IRRIGATION PROGRAM OUTCOMES")
print("="*60)

# Scatter plot: Irrigation vs Yield
fig, ax = plt.subplots(figsize=(10, 7))
scatter = ax.scatter(df['irrigation_m3'], df['yield_t_ha'], 
                     c=df['groundwater_quota_enforcement'], cmap='viridis', 
                     s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
ax.set_xlabel('Irrigation Water Applied (m³)', fontsize=12)
ax.set_ylabel('Crop Yield (t/ha)', fontsize=12)
ax.set_title('Irrigation vs Crop Yield\n(Color indicates Groundwater Quota Enforcement Level)', 
             fontsize=14, fontweight='bold')
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Groundwater Quota Enforcement', fontsize=11)

# Add trend line
z = np.polyfit(df['irrigation_m3'], df['yield_t_ha'], 1)
p = np.poly1d(z)
ax.plot(df['irrigation_m3'], p(df['irrigation_m3']), "r--", linewidth=2, label='Trend Line')
ax.legend()
plt.tight_layout()
plt.savefig('report/images/irrigation_vs_yield.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/irrigation_vs_yield.png")

# Calculate correlation between irrigation and yield
irrigation_yield_corr = df['irrigation_m3'].corr(df['yield_t_ha'])
print(f"\nCorrelation between Irrigation and Yield: {irrigation_yield_corr:.4f}")

# Statistical significance test
stat, p_value = stats.pearsonr(df['irrigation_m3'], df['yield_t_ha'])
print(f"Pearson correlation: r={stat:.4f}, p-value={p_value:.4f}")

# Policy enforcement analysis
print("\n" + "="*60)
print("POLICY ENFORCEMENT ANALYSIS")
print("="*60)

# Create policy enforcement categories
df['policy_category'] = pd.cut(df['groundwater_quota_enforcement'], 
                                bins=[0, 0.33, 0.66, 1.0], 
                                labels=['Low (0-0.33)', 'Medium (0.33-0.66)', 'High (0.66-1.0)'])

print("\nYield by Policy Enforcement Level:")
policy_stats = df.groupby('policy_category')['yield_t_ha'].agg(['mean', 'std', 'count'])
print(policy_stats)

# Box plot: Yield by Policy Category
fig, ax = plt.subplots(figsize=(10, 7))
df.boxplot(column='yield_t_ha', by='policy_category', ax=ax)
ax.set_xlabel('Groundwater Quota Enforcement Level', fontsize=12)
ax.set_ylabel('Crop Yield (t/ha)', fontsize=12)
ax.set_title('Crop Yield Distribution by Policy Enforcement Level', fontsize=14, fontweight='bold')
plt.suptitle('')  # Remove default title
plt.tight_layout()
plt.savefig('report/images/yield_by_policy.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/yield_by_policy.png")

# ANOVA test for policy categories
low_yield = df[df['policy_category'] == 'Low (0-0.33)']['yield_t_ha']
med_yield = df[df['policy_category'] == 'Medium (0.33-0.66)']['yield_t_ha']
high_yield = df[df['policy_category'] == 'High (0.66-1.0)']['yield_t_ha']

f_stat, p_val_anova = stats.f_oneway(low_yield, med_yield, high_yield)
print(f"\nANOVA Test Results:")
print(f"F-statistic: {f_stat:.4f}")
print(f"p-value: {p_val_anova:.4f}")

# Rainfall interaction analysis
print("\n" + "="*60)
print("RAINFALL AND IRRIGATION INTERACTION")
print("="*60)

# Create rainfall categories
df['rainfall_category'] = pd.cut(df['rainfall_mm'], 
                                  bins=[0, 300, 600, 900], 
                                  labels=['Low (<300mm)', 'Medium (300-600mm)', 'High (>600mm)'])

print("\nIrrigation and Yield by Rainfall Category:")
rainfall_stats = df.groupby('rainfall_category')[['irrigation_m3', 'yield_t_ha']].mean()
print(rainfall_stats)

# Scatter plot: Rainfall vs Yield, colored by irrigation
fig, ax = plt.subplots(figsize=(10, 7))
scatter = ax.scatter(df['rainfall_mm'], df['yield_t_ha'], 
                     c=df['irrigation_m3'], cmap='plasma', 
                     s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
ax.set_xlabel('Rainfall (mm)', fontsize=12)
ax.set_ylabel('Crop Yield (t/ha)', fontsize=12)
ax.set_title('Rainfall vs Crop Yield\n(Color indicates Irrigation Level)', 
             fontsize=14, fontweight='bold')
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Irrigation (m³)', fontsize=11)

# Add trend line
z = np.polyfit(df['rainfall_mm'], df['yield_t_ha'], 1)
p = np.poly1d(z)
ax.plot(df['rainfall_mm'], p(df['rainfall_mm']), "r--", linewidth=2, label='Trend Line')
ax.legend()
plt.tight_layout()
plt.savefig('report/images/rainfall_vs_yield.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/rainfall_vs_yield.png")

# Multiple regression analysis
print("\n" + "="*60)
print("MULTIPLE REGRESSION ANALYSIS")
print("="*60)

# Prepare features
X = df[['irrigation_m3', 'fertilizer_kg', 'groundwater_quota_enforcement', 'rainfall_mm']]
y = df['yield_t_ha']

# Fit regression model
model = LinearRegression()
model.fit(X, y)

# Get coefficients
coefficients = pd.DataFrame({
    'Variable': X.columns,
    'Coefficient': model.coef_,
    'Abs_Coefficient': np.abs(model.coef_)
}).sort_values('Abs_Coefficient', ascending=False)

print("\nRegression Coefficients (sorted by absolute value):")
print(coefficients)
print(f"\nIntercept: {model.intercept_:.4f}")
print(f"R-squared: {model.score(X, y):.4f}")

# Cross-validation
scores = cross_val_score(model, X, y, cv=5, scoring='r2')
print(f"Cross-validated R-squared: {scores.mean():.4f} (+/- {scores.std()*2:.4f})")

# Feature importance plot
fig, ax = plt.subplots(figsize=(10, 6))
colors = ['green' if c > 0 else 'red' for c in coefficients['Coefficient']]
bars = ax.barh(coefficients['Variable'], coefficients['Coefficient'], color=colors, alpha=0.7, edgecolor='black')
ax.set_xlabel('Regression Coefficient', fontsize=12)
ax.set_ylabel('Variable', fontsize=12)
ax.set_title('Feature Importance in Predicting Crop Yield\n(Green=Positive, Red=Negative Effect)', 
             fontsize=14, fontweight='bold')
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)

# Add value labels
for bar, coef in zip(bars, coefficients['Coefficient']):
    width = bar.get_width()
    ax.text(width, bar.get_y() + bar.get_height()/2, f'{coef:.4f}', 
            ha='left' if width > 0 else 'right', va='center', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/feature_importance.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/feature_importance.png")

# Irrigation efficiency analysis
print("\n" + "="*60)
print("IRRIGATION EFFICIENCY ANALYSIS")
print("="*60)

# Calculate irrigation efficiency (yield per unit of irrigation)
df['irrigation_efficiency'] = df['yield_t_ha'] / (df['irrigation_m3'] / 100)  # yield per 100 m³

print("\nIrrigation Efficiency Statistics:")
print(df['irrigation_efficiency'].describe())

# Efficiency by policy enforcement
print("\nIrrigation Efficiency by Policy Enforcement:")
efficiency_by_policy = df.groupby('policy_category')['irrigation_efficiency'].agg(['mean', 'std'])
print(efficiency_by_policy)

# Plot efficiency
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Efficiency vs Policy
ax1 = axes[0]
df.boxplot(column='irrigation_efficiency', by='policy_category', ax=ax1)
ax1.set_xlabel('Groundwater Quota Enforcement Level', fontsize=11)
ax1.set_ylabel('Irrigation Efficiency (t/ha per 100 m³)', fontsize=11)
ax1.set_title('Irrigation Efficiency by Policy Level', fontsize=12, fontweight='bold')

# Efficiency scatter
ax2 = axes[1]
scatter = ax2.scatter(df['irrigation_m3'], df['irrigation_efficiency'], 
                      c=df['groundwater_quota_enforcement'], cmap='coolwarm', 
                      s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
ax2.set_xlabel('Irrigation Water Applied (m³)', fontsize=11)
ax2.set_ylabel('Irrigation Efficiency (t/ha per 100 m³)', fontsize=11)
ax2.set_title('Irrigation Efficiency vs Water Applied', fontsize=12, fontweight='bold')
plt.colorbar(scatter, ax=ax2, label='Policy Enforcement')

plt.suptitle('')
plt.tight_layout()
plt.savefig('report/images/irrigation_efficiency.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: report/images/irrigation_efficiency.png")

# Summary statistics for report
print("\n" + "="*60)
print("SUMMARY STATISTICS FOR REPORT")
print("="*60)

summary_stats = {
    'Total Observations': len(df),
    'Mean Yield (t/ha)': df['yield_t_ha'].mean(),
    'Yield Std (t/ha)': df['yield_t_ha'].std(),
    'Mean Irrigation (m³)': df['irrigation_m3'].mean(),
    'Mean Fertilizer (kg)': df['fertilizer_kg'].mean(),
    'Mean Policy Enforcement': df['groundwater_quota_enforcement'].mean(),
    'Mean Rainfall (mm)': df['rainfall_mm'].mean(),
    'Irrigation-Yield Correlation': irrigation_yield_corr,
    'Model R-squared': model.score(X, y),
    'Cross-val R-squared': scores.mean()
}

for key, value in summary_stats.items():
    print(f"{key}: {value:.4f}" if isinstance(value, float) else f"{key}: {value}")

# Save summary to file
with open('outputs/summary_stats.txt', 'w') as f:
    f.write("IRRIGATION YIELD PANEL ANALYSIS - SUMMARY STATISTICS\n")
    f.write("="*60 + "\n\n")
    for key, value in summary_stats.items():
        f.write(f"{key}: {value:.4f}\n" if isinstance(value, float) else f"{key}: {value}\n")
    
    f.write("\n\nREGRESSION COEFFICIENTS\n")
    f.write("="*60 + "\n")
    f.write(coefficients.to_string())
    
    f.write("\n\nPOLICY ENFORCEMENT ANALYSIS\n")
    f.write("="*60 + "\n")
    f.write(policy_stats.to_string())
    
    f.write("\n\nRAINFALL CATEGORY ANALYSIS\n")
    f.write("="*60 + "\n")
    f.write(rainfall_stats.to_string())

print("\nSaved: outputs/summary_stats.txt")
print("\nAnalysis complete!")
