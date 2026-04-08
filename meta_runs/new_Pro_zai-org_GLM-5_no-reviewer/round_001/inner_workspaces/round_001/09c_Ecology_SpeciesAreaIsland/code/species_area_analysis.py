"""
Species-Area Relationship Analysis for Island Biogeography

This script analyzes the species-area relationship using island data,
fits the power law model (S = c * A^z), and discusses conservation implications.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
print("Loading island species data...")
df = pd.read_csv('data/island_species.csv')
print(f"Dataset contains {len(df)} islands")
print(df.describe())

# Basic statistics
print("\n=== Data Summary ===")
print(f"Area range: {df['area_km2'].min():.3f} - {df['area_km2'].max():.3f} km²")
print(f"Species richness range: {df['species_richness'].min()} - {df['species_richness'].max()}")
print(f"Mean area: {df['area_km2'].mean():.3f} km²")
print(f"Mean species richness: {df['species_richness'].mean():.1f}")

# Define the power law model: S = c * A^z
def species_area_power(area, c, z):
    """Power law species-area relationship: S = c * A^z"""
    return c * (area ** z)

# Log-transform for linear regression: log(S) = log(c) + z * log(A)
df['log_area'] = np.log(df['area_km2'])
df['log_richness'] = np.log(df['species_richness'])

# Linear regression on log-transformed data
slope, intercept, r_value, p_value, std_err = stats.linregress(df['log_area'], df['log_richness'])

# Extract parameters
c_linear = np.exp(intercept)
z_linear = slope
r_squared = r_value ** 2

print("\n=== Species-Area Relationship (Log-Log Linear Regression) ===")
print(f"Model: S = c * A^z")
print(f"c (intercept coefficient) = {c_linear:.3f}")
print(f"z (slope) = {z_linear:.3f}")
print(f"R² = {r_squared:.4f}")
print(f"p-value = {p_value:.2e}")
print(f"Standard error of z = {std_err:.4f}")

# Non-linear least squares fit for comparison
try:
    popt, pcov = curve_fit(species_area_power, df['area_km2'], df['species_richness'], 
                           p0=[c_linear, z_linear], maxfev=10000)
    c_nls, z_nls = popt
    perr = np.sqrt(np.diag(pcov))
    
    print("\n=== Non-linear Least Squares Fit ===")
    print(f"c = {c_nls:.3f} ± {perr[0]:.3f}")
    print(f"z = {z_nls:.3f} ± {perr[1]:.3f}")
except Exception as e:
    print(f"Non-linear fit failed: {e}")
    c_nls, z_nls = c_linear, z_linear

# Calculate predicted values
df['predicted_linear'] = c_linear * (df['area_km2'] ** z_linear)
df['residuals'] = df['species_richness'] - df['predicted_linear']

# Calculate confidence intervals for the regression
n = len(df)
t_value = stats.t.ppf(0.975, n - 2)
se_pred = np.sqrt(np.sum(df['residuals']**2) / (n - 2)) * np.sqrt(1/n + (df['log_area'] - df['log_area'].mean())**2 / np.sum((df['log_area'] - df['log_area'].mean())**2))

# Sort for plotting
area_range = np.linspace(df['area_km2'].min(), df['area_km2'].max(), 100)
predicted_range = c_linear * (area_range ** z_linear)

# Figure 1: Species-Area Relationship with Power Law Fit
fig, ax = plt.subplots(figsize=(10, 7))
ax.scatter(df['area_km2'], df['species_richness'], s=80, alpha=0.7, edgecolor='black', linewidth=1, label='Observed data')
ax.plot(area_range, predicted_range, 'r-', linewidth=2, label=f'Power law fit: S = {c_linear:.2f} × A$^{{{z_linear:.3f}}}$')
ax.set_xlabel('Island Area (km²)', fontsize=12)
ax.set_ylabel('Species Richness', fontsize=12)
ax.set_title('Species-Area Relationship for Islands', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

# Add R² annotation
ax.text(0.05, 0.95, f'R² = {r_squared:.4f}\np < 0.001', transform=ax.transAxes, fontsize=11,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/figure1_species_area_curve.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nFigure 1 saved: report/images/figure1_species_area_curve.png")

# Figure 2: Log-Log Plot with Linear Regression
fig, ax = plt.subplots(figsize=(10, 7))
ax.scatter(df['log_area'], df['log_richness'], s=80, alpha=0.7, edgecolor='black', linewidth=1, label='Log-transformed data')

# Regression line
log_area_range = np.linspace(df['log_area'].min(), df['log_area'].max(), 100)
log_pred = intercept + slope * log_area_range
ax.plot(log_area_range, log_pred, 'r-', linewidth=2, label=f'Linear fit: log(S) = {intercept:.3f} + {slope:.3f} × log(A)')

ax.set_xlabel('log(Area) [log km²]', fontsize=12)
ax.set_ylabel('log(Species Richness)', fontsize=12)
ax.set_title('Log-Log Species-Area Relationship', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

# Add statistics annotation
ax.text(0.05, 0.95, f'Slope (z) = {z_linear:.3f} ± {std_err:.3f}\nR² = {r_squared:.4f}', 
        transform=ax.transAxes, fontsize=11,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/figure2_log_log_regression.png', dpi=300, bbox_inches='tight')
plt.close()
print("Figure 2 saved: report/images/figure2_log_log_regression.png")

# Figure 3: Residual Analysis
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Residuals vs Fitted
axes[0].scatter(df['predicted_linear'], df['residuals'], s=60, alpha=0.7, edgecolor='black', linewidth=1)
axes[0].axhline(y=0, color='r', linestyle='--', linewidth=1.5)
axes[0].set_xlabel('Fitted Values', fontsize=12)
axes[0].set_ylabel('Residuals', fontsize=12)
axes[0].set_title('Residuals vs Fitted Values', fontsize=13, fontweight='bold')
axes[0].grid(True, alpha=0.3)

# Q-Q Plot
stats.probplot(df['residuals'], dist="norm", plot=axes[1])
axes[1].set_title('Normal Q-Q Plot of Residuals', fontsize=13, fontweight='bold')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure3_residual_analysis.png', dpi=300, bbox_inches='tight')
plt.close()
print("Figure 3 saved: report/images/figure3_residual_analysis.png")

# Figure 4: Conservation Planning Implications
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel A: Species accumulation with area
area_conservation = np.linspace(0.1, 100, 500)
species_predicted = c_linear * (area_conservation ** z_linear)

axes[0].plot(area_conservation, species_predicted, 'b-', linewidth=2.5)
axes[0].axvline(x=df['area_km2'].mean(), color='green', linestyle='--', linewidth=1.5, label=f'Mean island area ({df["area_km2"].mean():.2f} km²)')
axes[0].axvline(x=df['area_km2'].max(), color='orange', linestyle='--', linewidth=1.5, label=f'Largest island ({df["area_km2"].max():.2f} km²)')
axes[0].set_xlabel('Reserve Area (km²)', fontsize=12)
axes[0].set_ylabel('Predicted Species Richness', fontsize=12)
axes[0].set_title('Species Accumulation Curve for Reserve Planning', fontsize=13, fontweight='bold')
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)
axes[0].set_xlim(0, 20)

# Panel B: Area required for target species richness
target_species = np.arange(10, 60, 5)
area_required = (target_species / c_linear) ** (1 / z_linear)

axes[1].bar(range(len(target_species)), area_required, color='steelblue', edgecolor='black', alpha=0.8)
axes[1].set_xticks(range(len(target_species)))
axes[1].set_xticklabels(target_species, fontsize=10)
axes[1].set_xlabel('Target Species Richness', fontsize=12)
axes[1].set_ylabel('Required Area (km²)', fontsize=12)
axes[1].set_title('Minimum Area Required for Conservation Targets', fontsize=13, fontweight='bold')
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/figure4_conservation_implications.png', dpi=300, bbox_inches='tight')
plt.close()
print("Figure 4 saved: report/images/figure4_conservation_implications.png")

# Figure 5: Comparison with theoretical z-values
fig, ax = plt.subplots(figsize=(10, 6))

# Theoretical z-values
z_theoretical = {
    'This study': z_linear,
    'Typical islands (0.25-0.35)': 0.30,
    'Mainland reserves (0.12-0.18)': 0.15,
    'Isolated islands (>0.35)': 0.40
}

colors = ['red', 'blue', 'green', 'orange']
bars = ax.bar(range(len(z_theoretical)), list(z_theoretical.values()), color=colors, edgecolor='black', alpha=0.7)
ax.set_xticks(range(len(z_theoretical)))
ax.set_xticklabels(list(z_theoretical.keys()), fontsize=10, rotation=15, ha='right')
ax.set_ylabel('z-value (slope)', fontsize=12)
ax.set_title('Comparison of Species-Area Slope (z) with Literature Values', fontsize=13, fontweight='bold')
ax.axhline(y=0.25, color='gray', linestyle=':', linewidth=1, label='Lower bound for islands')
ax.axhline(y=0.35, color='gray', linestyle=':', linewidth=1, label='Upper bound for islands')
ax.grid(True, alpha=0.3, axis='y')

# Add value labels
for bar, val in zip(bars, z_theoretical.values()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, f'{val:.3f}', 
            ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/figure5_z_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("Figure 5 saved: report/images/figure5_z_comparison.png")

# Save results to outputs
results = {
    'Parameter': ['c (coefficient)', 'z (slope)', 'R-squared', 'p-value', 'Standard Error (z)', 'n (sample size)'],
    'Value': [c_linear, z_linear, r_squared, p_value, std_err, n]
}
results_df = pd.DataFrame(results)
results_df.to_csv('outputs/model_parameters.csv', index=False)
print("\nModel parameters saved to outputs/model_parameters.csv")

# Save detailed data with predictions
df.to_csv('outputs/analysis_data.csv', index=False)
print("Analysis data saved to outputs/analysis_data.csv")

# Conservation planning calculations
print("\n=== Conservation Planning Implications ===")
print(f"\n1. Species-Area Relationship: S = {c_linear:.3f} × A^{z_linear:.3f}")
print(f"\n2. Area needed to support target species richness:")
for target in [15, 20, 25, 30, 40]:
    area_needed = (target / c_linear) ** (1 / z_linear)
    print(f"   - {target} species: {area_needed:.2f} km²")

print(f"\n3. Extinction risk heuristic:")
print(f"   - A 90% habitat loss (A → 0.1A) would reduce species by approximately:")
reduction = 1 - (0.1 ** z_linear)
print(f"     {reduction*100:.1f}% of species")

print(f"\n4. Reserve sizing recommendation:")
print(f"   - To maintain current average richness ({df['species_richness'].mean():.1f} species):")
area_for_mean = (df['species_richness'].mean() / c_linear) ** (1 / z_linear)
print(f"     Minimum reserve area: {area_for_mean:.2f} km²")

print("\n=== Analysis Complete ===")
