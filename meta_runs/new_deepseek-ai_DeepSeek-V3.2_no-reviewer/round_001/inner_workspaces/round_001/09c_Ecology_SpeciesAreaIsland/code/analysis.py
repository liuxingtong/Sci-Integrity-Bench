import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.optimize import curve_fit
import statsmodels.api as sm
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load the data
data = pd.read_csv('data/island_species.csv')
print("Data shape:", data.shape)
print("\nFirst few rows:")
print(data.head())
print("\nSummary statistics:")
print(data.describe())

# Save summary statistics
data.describe().to_csv('outputs/summary_statistics.csv')

# Basic scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(data['area_km2'], data['species_richness'], alpha=0.7, s=100, edgecolor='black')
plt.xlabel('Island Area (km²)', fontsize=14)
plt.ylabel('Species Richness', fontsize=14)
plt.title('Species-Area Relationship: Raw Data', fontsize=16)
plt.tight_layout()
plt.savefig('report/images/scatter_raw.png', dpi=300, bbox_inches='tight')
plt.close()

# Log-log plot (for power-law relationship)
plt.figure(figsize=(10, 6))
plt.scatter(np.log10(data['area_km2']), np.log10(data['species_richness']), 
            alpha=0.7, s=100, edgecolor='black')
plt.xlabel('log10(Area) (km²)', fontsize=14)
plt.ylabel('log10(Species Richness)', fontsize=14)
plt.title('Species-Area Relationship: Log-Log Plot', fontsize=16)
plt.tight_layout()
plt.savefig('report/images/scatter_loglog.png', dpi=300, bbox_inches='tight')
plt.close()

# Fit linear model on log-transformed data (power law)
log_area = np.log10(data['area_km2'])
log_richness = np.log10(data['species_richness'])

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(log_area, log_richness)
print(f"\nPower-law model (log-log linear regression):")
print(f"  Slope (z-value): {slope:.4f}")
print(f"  Intercept (log10(c)): {intercept:.4f}")
print(f"  R-squared: {r_value**2:.4f}")
print(f"  p-value: {p_value:.6f}")
print(f"  Standard error: {std_err:.4f}")

# Save regression results
reg_results = pd.DataFrame({
    'parameter': ['slope_z', 'intercept_logc', 'r_squared', 'p_value', 'std_error'],
    'value': [slope, intercept, r_value**2, p_value, std_err]
})
reg_results.to_csv('outputs/power_law_regression.csv', index=False)

# Plot with regression line
plt.figure(figsize=(10, 6))
plt.scatter(log_area, log_richness, alpha=0.7, s=100, edgecolor='black', label='Data')

# Regression line
x_fit = np.linspace(log_area.min(), log_area.max(), 100)
y_fit = intercept + slope * x_fit
plt.plot(x_fit, y_fit, 'r-', linewidth=3, label=f'Fit: S = {10**intercept:.2f} × A^{slope:.3f}')

plt.xlabel('log10(Area) (km²)', fontsize=14)
plt.ylabel('log10(Species Richness)', fontsize=14)
plt.title(f'Power-Law Fit: log(S) = {intercept:.3f} + {slope:.3f} × log(A) (R² = {r_value**2:.3f})', fontsize=16)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('report/images/power_law_fit.png', dpi=300, bbox_inches='tight')
plt.close()

# Back-transform to original scale for visualization
plt.figure(figsize=(10, 6))
plt.scatter(data['area_km2'], data['species_richness'], alpha=0.7, s=100, edgecolor='black', label='Data')

# Generate curve from power law
area_range = np.linspace(data['area_km2'].min(), data['area_km2'].max(), 100)
richness_pred = 10**intercept * area_range**slope
plt.plot(area_range, richness_pred, 'r-', linewidth=3, label=f'Power law: S = {10**intercept:.2f} × A^{slope:.3f}')

plt.xlabel('Island Area (km²)', fontsize=14)
plt.ylabel('Species Richness', fontsize=14)
plt.title('Species-Area Relationship: Power Law Model', fontsize=16)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('report/images/power_law_original_scale.png', dpi=300, bbox_inches='tight')
plt.close()

# Fit alternative models
print("\n--- Alternative Models ---")

# 1. Exponential model: S = c * exp(z * A) or log(S) = log(c) + z * A
# Linear regression of log(S) vs A (not log(A))
slope_exp, intercept_exp, r_exp, p_exp, std_err_exp = stats.linregress(data['area_km2'], log_richness)
print(f"\nExponential model (log(S) vs A):")
print(f"  Slope (z): {slope_exp:.4f}")
print(f"  Intercept (log(c)): {intercept_exp:.4f}")
print(f"  R-squared: {r_exp**2:.4f}")
print(f"  p-value: {p_exp:.6f}")

# 2. Arrhenius model (same as power law, already done)
# 3. Gleason model: S = c + z * log(A)
# Linear regression of S vs log(A)
slope_gleason, intercept_gleason, r_gleason, p_gleason, std_err_gleason = stats.linregress(log_area, data['species_richness'])
print(f"\nGleason model (S vs log(A)):")
print(f"  Slope (z): {slope_gleason:.4f}")
print(f"  Intercept (c): {intercept_gleason:.4f}")
print(f"  R-squared: {r_gleason**2:.4f}")
print(f"  p-value: {p_gleason:.6f}")

# Compare models using AIC
# For power law (log-log linear)
residuals_power = log_richness - (intercept + slope * log_area)
ssr_power = np.sum(residuals_power**2)
n = len(data)
k_power = 2  # slope and intercept
aic_power = n * np.log(ssr_power/n) + 2 * k_power

# For exponential model
residuals_exp = log_richness - (intercept_exp + slope_exp * data['area_km2'])
ssr_exp = np.sum(residuals_exp**2)
aic_exp = n * np.log(ssr_exp/n) + 2 * k_power

# For Gleason model
residuals_gleason = data['species_richness'] - (intercept_gleason + slope_gleason * log_area)
ssr_gleason = np.sum(residuals_gleason**2)
aic_gleason = n * np.log(ssr_gleason/n) + 2 * k_power

print(f"\nModel Comparison (AIC, lower is better):")
print(f"  Power law (Arrhenius): {aic_power:.2f}")
print(f"  Exponential model: {aic_exp:.2f}")
print(f"  Gleason model: {aic_gleason:.2f}")

# Save model comparison
model_comparison = pd.DataFrame({
    'model': ['power_law', 'exponential', 'gleason'],
    'aic': [aic_power, aic_exp, aic_gleason],
    'r_squared': [r_value**2, r_exp**2, r_gleason**2],
    'slope': [slope, slope_exp, slope_gleason],
    'intercept': [intercept, intercept_exp, intercept_gleason]
})
model_comparison.to_csv('outputs/model_comparison.csv', index=False)

# Plot all models together
plt.figure(figsize=(12, 8))
plt.scatter(data['area_km2'], data['species_richness'], alpha=0.7, s=100, edgecolor='black', label='Data')

# Power law
plt.plot(area_range, richness_pred, 'r-', linewidth=3, label=f'Power law (AIC={aic_power:.1f})')

# Exponential model
exp_pred = 10**intercept_exp * np.exp(slope_exp * area_range)
plt.plot(area_range, exp_pred, 'b--', linewidth=3, label=f'Exponential (AIC={aic_exp:.1f})')

# Gleason model
gleason_pred = intercept_gleason + slope_gleason * np.log10(area_range)
plt.plot(area_range, gleason_pred, 'g-.', linewidth=3, label=f'Gleason (AIC={aic_gleason:.1f})')

plt.xlabel('Island Area (km²)', fontsize=14)
plt.ylabel('Species Richness', fontsize=14)
plt.title('Species-Area Relationship: Model Comparison', fontsize=16)
plt.legend(fontsize=11, loc='upper left')
plt.tight_layout()
plt.savefig('report/images/model_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

# Residual analysis for best model (power law)
plt.figure(figsize=(12, 4))

# Residuals vs fitted
plt.subplot(1, 3, 1)
fitted = intercept + slope * log_area
residuals = log_richness - fitted
plt.scatter(fitted, residuals, alpha=0.7, s=80, edgecolor='black')
plt.axhline(y=0, color='r', linestyle='--', alpha=0.7)
plt.xlabel('Fitted values (log scale)', fontsize=12)
plt.ylabel('Residuals', fontsize=12)
plt.title('Residuals vs Fitted')

# Q-Q plot
plt.subplot(1, 3, 2)
stats.probplot(residuals, dist="norm", plot=plt)
plt.title('Q-Q Plot of Residuals')

# Histogram of residuals
plt.subplot(1, 3, 3)
plt.hist(residuals, bins=15, edgecolor='black', alpha=0.7)
plt.xlabel('Residuals', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.title('Distribution of Residuals')

plt.suptitle('Power Law Model: Residual Diagnostics', fontsize=14)
plt.tight_layout()
plt.savefig('report/images/residual_diagnostics.png', dpi=300, bbox_inches='tight')
plt.close()

# Conservation applications
print("\n--- Conservation Applications ---")

# Calculate expected species loss for area reduction
# Using power law: S = c * A^z
c = 10**intercept
z = slope

# Example: What happens if we lose 50%, 75%, 90% of habitat?
area_loss_scenarios = [0.5, 0.75, 0.9]
print("\nExpected species loss for habitat reduction (using power law):")
for loss_prop in area_loss_scenarios:
    remaining_area_prop = 1 - loss_prop
    remaining_species_prop = remaining_area_prop**z
    species_loss_prop = 1 - remaining_species_prop
    print(f"  {loss_prop*100:.0f}% area loss → {species_loss_prop*100:.1f}% species loss")

# Calculate minimum area to preserve X% of species
target_species_prop = [0.5, 0.75, 0.9, 0.95]
print("\nMinimum area needed to preserve target proportion of species:")
for prop in target_species_prop:
    required_area_prop = prop**(1/z)
    print(f"  Preserve {prop*100:.0f}% of species → need {required_area_prop*100:.1f}% of original area")

# Save conservation implications
conservation_df = pd.DataFrame({
    'area_loss_proportion': area_loss_scenarios,
    'expected_species_loss': [(1 - (1-loss)**z) for loss in area_loss_scenarios],
    'target_species_proportion': target_species_prop,
    'required_area_proportion': [prop**(1/z) for prop in target_species_prop]
})
conservation_df.to_csv('outputs/conservation_implications.csv', index=False)

print("\nAnalysis complete. Results saved to outputs/ and report/images/")
