"""
Species-Area Relationship Analysis for Island Biogeography

This script analyzes the relationship between island area and species richness,
fitting power law models and discussing implications for conservation planning.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

# Load data
data = pd.read_csv('data/island_species.csv')
print("Data Overview:")
print(data.head(10))
print(f"\nDataset shape: {data.shape}")
print(f"\nDescriptive statistics:")
print(data.describe())

# Extract variables
area = data['area_km2'].values
richness = data['species_richness'].values

# ============================================================================
# 1. EXPLORATORY DATA ANALYSIS
# ============================================================================

# Create data overview figure
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Histogram of area
axes[0, 0].hist(area, bins=10, color='steelblue', edgecolor='black', alpha=0.7)
axes[0, 0].set_xlabel('Area (km²)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Distribution of Island Areas')

# Histogram of species richness
axes[0, 1].hist(richness, bins=10, color='forestgreen', edgecolor='black', alpha=0.7)
axes[0, 1].set_xlabel('Species Richness')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Distribution of Species Richness')

# Scatter plot: Area vs Richness (linear scale)
axes[1, 0].scatter(area, richness, c='darkblue', alpha=0.6, s=80, edgecolors='black')
axes[1, 0].set_xlabel('Area (km²)')
axes[1, 0].set_ylabel('Species Richness')
axes[1, 0].set_title('Species-Area Relationship (Linear Scale)')

# Scatter plot: log-log scale
log_area = np.log10(area)
log_richness = np.log10(richness)
axes[1, 1].scatter(log_area, log_richness, c='darkred', alpha=0.6, s=80, edgecolors='black')
axes[1, 1].set_xlabel('log₁₀(Area)')
axes[1, 1].set_ylabel('log₁₀(Species Richness)')
axes[1, 1].set_title('Species-Area Relationship (Log-Log Scale)')

plt.tight_layout()
plt.savefig('report/images/figure1_data_overview.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nFigure 1 saved: Data overview")

# ============================================================================
# 2. POWER LAW MODEL FITTING
# ============================================================================

# Power law model: S = c * A^z
def power_law(A, c, z):
    return c * (A ** z)

# Fit power law using non-linear least squares
popt, pcov = curve_fit(power_law, area, richness, p0=[10, 0.3], maxfev=10000)
c_fit, z_fit = popt
c_err, z_err = np.sqrt(np.diag(pcov))

print(f"\n=== Power Law Model: S = c × A^z ===")
print(f"Fitted parameters:")
print(f"  c (constant) = {c_fit:.4f} ± {c_err:.4f}")
print(f"  z (exponent) = {z_fit:.4f} ± {z_err:.4f}")

# Predictions
richness_pred_power = power_law(area, c_fit, z_fit)

# Model evaluation
ss_res = np.sum((richness - richness_pred_power) ** 2)
ss_tot = np.sum((richness - np.mean(richness)) ** 2)
r2_power = 1 - (ss_res / ss_tot)
rmse_power = np.sqrt(np.mean((richness - richness_pred_power) ** 2))

print(f"\nModel performance:")
print(f"  R² = {r2_power:.4f}")
print(f"  RMSE = {rmse_power:.4f}")

# ============================================================================
# 3. LINEAR MODEL ON LOG-LOG SCALE
# ============================================================================

# Linear regression on log-log data: log(S) = log(c) + z*log(A)
slope, intercept, r_value, p_value, std_err = stats.linregress(log_area, log_richness)

# Convert back to power law parameters
c_linear = 10 ** intercept
z_linear = slope

print(f"\n=== Linear Model on Log-Log Scale ===")
print(f"Fitted parameters:")
print(f"  c (constant) = {c_linear:.4f}")
print(f"  z (exponent) = {z_linear:.4f}")
print(f"  R² (log-log) = {r_value**2:.4f}")
print(f"  p-value = {p_value:.2e}")

# Predictions
richness_pred_linear = c_linear * (area ** z_linear)

# Model evaluation
r2_linear = r_value ** 2
rmse_linear = np.sqrt(np.mean((richness - richness_pred_linear) ** 2))

print(f"\nModel performance:")
print(f"  RMSE = {rmse_linear:.4f}")

# ============================================================================
# 4. MODEL COMPARISON AND VALIDATION
# ============================================================================

# Compare models
print(f"\n=== Model Comparison ===")
print(f"{'Metric':<20} {'Power Law (NLS)':<20} {'Linear (Log-Log)':<20}")
print(f"{'-'*60}")
print(f"{'c (constant)':<20} {c_fit:<20.4f} {c_linear:<20.4f}")
print(f"{'z (exponent)':<20} {z_fit:<20.4f} {z_linear:<20.4f}")
print(f"{'R²':<20} {r2_power:<20.4f} {r2_linear:<20.4f}")
print(f"{'RMSE':<20} {rmse_power:<20.4f} {rmse_linear:<20.4f}")

# ============================================================================
# 5. VISUALIZATION OF MODEL FITS
# ============================================================================

# Create model comparison figure
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Linear scale plot
axes[0].scatter(area, richness, c='darkblue', alpha=0.6, s=80, edgecolors='black', label='Observed data')
area_smooth = np.linspace(area.min(), area.max(), 200)
richness_smooth_power = power_law(area_smooth, c_fit, z_fit)
richness_smooth_linear = c_linear * (area_smooth ** z_linear)
axes[0].plot(area_smooth, richness_smooth_power, 'r-', linewidth=2, label=f'Power Law (z={z_fit:.3f})')
axes[0].plot(area_smooth, richness_smooth_linear, 'g--', linewidth=2, label=f'Log-Linear (z={z_linear:.3f})')
axes[0].set_xlabel('Area (km²)', fontsize=12)
axes[0].set_ylabel('Species Richness', fontsize=12)
axes[0].set_title('Species-Area Relationship (Linear Scale)', fontsize=13)
axes[0].legend(loc='upper left')
axes[0].grid(True, alpha=0.3)

# Log-log scale plot
axes[1].scatter(log_area, log_richness, c='darkred', alpha=0.6, s=80, edgecolors='black', label='Observed data')
log_area_smooth = np.log10(area_smooth)
log_richness_smooth_power = np.log10(richness_smooth_power)
log_richness_smooth_linear = np.log10(richness_smooth_linear)
axes[1].plot(log_area_smooth, log_richness_smooth_power, 'r-', linewidth=2, label=f'Power Law fit')
axes[1].plot(log_area_smooth, log_richness_smooth_linear, 'g--', linewidth=2, label=f'Linear fit')
# Add fitted line for linear model
axes[1].plot(log_area_smooth, intercept + slope * log_area_smooth, 'orange', linewidth=2, linestyle=':', label=f'Regression line (R²={r2_linear:.3f})')
axes[1].set_xlabel('log₁₀(Area)', fontsize=12)
axes[1].set_ylabel('log₁₀(Species Richness)', fontsize=12)
axes[1].set_title('Species-Area Relationship (Log-Log Scale)', fontsize=13)
axes[1].legend(loc='lower right')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure2_model_fits.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nFigure 2 saved: Model fits")

# ============================================================================
# 6. RESIDUAL ANALYSIS
# ============================================================================

residuals_power = richness - richness_pred_power
residuals_linear = richness - richness_pred_linear

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Residuals vs fitted (Power Law)
axes[0, 0].scatter(richness_pred_power, residuals_power, c='darkblue', alpha=0.6, s=60)
axes[0, 0].axhline(y=0, color='r', linestyle='--')
axes[0, 0].set_xlabel('Fitted Values (Power Law)')
axes[0, 0].set_ylabel('Residuals')
axes[0, 0].set_title('Residuals vs Fitted (Power Law)')
axes[0, 0].grid(True, alpha=0.3)

# Q-Q plot for Power Law
stats.probplot(residuals_power, dist="norm", plot=axes[0, 1])
axes[0, 1].set_title('Q-Q Plot (Power Law Residuals)')
axes[0, 1].grid(True, alpha=0.3)

# Residuals vs fitted (Linear)
axes[1, 0].scatter(richness_pred_linear, residuals_linear, c='darkgreen', alpha=0.6, s=60)
axes[1, 0].axhline(y=0, color='r', linestyle='--')
axes[1, 0].set_xlabel('Fitted Values (Linear)')
axes[1, 0].set_ylabel('Residuals')
axes[1, 0].set_title('Residuals vs Fitted (Log-Linear)')
axes[1, 0].grid(True, alpha=0.3)

# Q-Q plot for Linear
stats.probplot(residuals_linear, dist="norm", plot=axes[1, 1])
axes[1, 1].set_title('Q-Q Plot (Log-Linear Residuals)')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure3_residual_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("Figure 3 saved: Residual analysis")

# ============================================================================
# 7. CONSERVATION PLANNING IMPLICATIONS
# ============================================================================

# Calculate species loss predictions for different scenarios
print("\n=== Conservation Planning Implications ===")

# Scenario 1: Effect of habitat loss
print("\n1. Effect of Habitat Loss on Species Richness:")
print(f"   Using z = {z_fit:.4f} (Power Law model)")
print(f"   {'Original Area':<15} {'50% Loss':<15} {'75% Loss':<15} {'90% Loss':<15}")
print(f"   {'-'*60}")

for original_area in [5.0, 3.0, 1.0]:
    original_richness = power_law(original_area, c_fit, z_fit)
    richness_50_loss = power_law(original_area * 0.5, c_fit, z_fit)
    richness_75_loss = power_law(original_area * 0.25, c_fit, z_fit)
    richness_90_loss = power_law(original_area * 0.1, c_fit, z_fit)
    
    print(f"   {original_area:<15.2f} {richness_50_loss:<15.1f} {richness_75_loss:<15.1f} {richness_90_loss:<15.1f}")

# Scenario 2: Minimum area requirements
print("\n2. Minimum Area Requirements for Target Species Richness:")
target_richness_values = [10, 15, 20, 30, 40]
print(f"   {'Target Richness':<20} {'Required Area (km²)':<20}")
print(f"   {'-'*40}")
for target in target_richness_values:
    min_area = (target / c_fit) ** (1 / z_fit)
    print(f"   {target:<20} {min_area:<20.3f}")

# Scenario 3: SLOSS debate (Single Large vs Several Small)
print("\n3. SLOSS Analysis (Single Large vs Several Small):")
total_area = 10.0  # Total conservation area available
print(f"   Total conservation area available: {total_area} km²")
print(f"   {'Configuration':<30} {'Expected Species Richness':<30}")
print(f"   {'-'*60}")

# One large reserve
one_large = power_law(total_area, c_fit, z_fit)
print(f"   {'1 reserve of 10 km²':<30} {one_large:<30.1f}")

# Multiple small reserves
for n_patches in [2, 5, 10]:
    area_per_patch = total_area / n_patches
    richness_per_patch = power_law(area_per_patch, c_fit, z_fit)
    # Assuming no shared species (upper bound)
    total_richness_upper = n_patches * richness_per_patch
    print(f"   {f'{n_patches} reserves of {area_per_patch:.1f} km²':<30} {total_richness_upper:<30.1f}")

# ============================================================================
# 8. SAVE RESULTS
# ============================================================================

# Save model parameters and predictions
results = pd.DataFrame({
    'island_id': data['island_id'],
    'area_km2': area,
    'observed_richness': richness,
    'predicted_richness_power': richness_pred_power,
    'predicted_richness_linear': richness_pred_linear,
    'residuals_power': residuals_power,
    'residuals_linear': residuals_linear
})
results.to_csv('outputs/model_predictions.csv', index=False)

# Save model summary
with open('outputs/model_summary.txt', 'w') as f:
    f.write("="*60 + "\n")
    f.write("SPECIES-AREA RELATIONSHIP ANALYSIS RESULTS\n")
    f.write("="*60 + "\n\n")
    
    f.write("POWER LAW MODEL (Non-linear Least Squares)\n")
    f.write("-"*60 + "\n")
    f.write(f"Model: S = c × A^z\n")
    f.write(f"c (constant) = {c_fit:.4f} ± {c_err:.4f}\n")
    f.write(f"z (exponent) = {z_fit:.4f} ± {z_err:.4f}\n")
    f.write(f"R² = {r2_power:.4f}\n")
    f.write(f"RMSE = {rmse_power:.4f}\n\n")
    
    f.write("LINEAR MODEL (Log-Log Scale)\n")
    f.write("-"*60 + "\n")
    f.write(f"Model: log(S) = log(c) + z × log(A)\n")
    f.write(f"c (constant) = {c_linear:.4f}\n")
    f.write(f"z (exponent) = {z_linear:.4f}\n")
    f.write(f"R² = {r2_linear:.4f}\n")
    f.write(f"p-value = {p_value:.2e}\n")
    f.write(f"RMSE = {rmse_linear:.4f}\n\n")
    
    f.write("INTERPRETATION\n")
    f.write("-"*60 + "\n")
    f.write(f"The z-value of {z_fit:.4f} indicates {'strong' if z_fit > 0.3 else 'moderate' if z_fit > 0.2 else 'weak'} ")
    f.write("species-area relationship.\n")
    f.write("Typical z-values for islands range from 0.20 to 0.35.\n")

print("\nResults saved to outputs/")
print("\nAnalysis complete!")
