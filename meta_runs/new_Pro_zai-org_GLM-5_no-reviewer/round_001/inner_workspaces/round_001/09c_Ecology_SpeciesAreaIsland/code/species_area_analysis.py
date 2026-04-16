import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit
import seaborn as sns
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
data = pd.read_csv('data/island_species.csv')
print("Data Overview:")
print(data.describe())
print("\nFirst few rows:")
print(data.head())

# Basic statistics
area = data['area_km2'].values
richness = data['species_richness'].values

# Log-transform for power law model
log_area = np.log(area)
log_richness = np.log(richness)

# Linear regression on log-transformed data (power law: S = c * A^z)
slope, intercept, r_value, p_value, std_err = stats.linregress(log_area, log_richness)

# Power law parameters
z = slope  # exponent
c = np.exp(intercept)  # coefficient
r_squared = r_value ** 2

print(f"\n=== Species-Area Relationship (Power Law Model) ===")
print(f"Model: S = c * A^z")
print(f"Parameters:")
print(f"  c (coefficient) = {c:.3f}")
print(f"  z (exponent) = {z:.3f}")
print(f"  R² = {r_squared:.4f}")
print(f"  p-value = {p_value:.2e}")
print(f"  Standard error of z = {std_err:.4f}")

# Calculate predicted values
area_pred = np.linspace(area.min(), area.max(), 100)
richness_pred_power = c * (area_pred ** z)

# Also fit alternative models for comparison
# 1. Linear model: S = a + b*A
slope_linear, intercept_linear, r_value_linear, p_value_linear, std_err_linear = stats.linregress(area, richness)
r_squared_linear = r_value_linear ** 2
richness_pred_linear = intercept_linear + slope_linear * area_pred

print(f"\n=== Linear Model (for comparison) ===")
print(f"Model: S = a + b*A")
print(f"  a = {intercept_linear:.3f}")
print(f"  b = {slope_linear:.3f}")
print(f"  R² = {r_squared_linear:.4f}")

# 2. Logarithmic model: S = a + b*log(A)
slope_log, intercept_log, r_value_log, p_value_log, std_err_log = stats.linregress(log_area, richness)
r_squared_log = r_value_log ** 2
richness_pred_log = intercept_log + slope_log * np.log(area_pred)

print(f"\n=== Logarithmic Model (for comparison) ===")
print(f"Model: S = a + b*log(A)")
print(f"  a = {intercept_log:.3f}")
print(f"  b = {slope_log:.3f}")
print(f"  R² = {r_squared_log:.4f}")

# Model comparison
print(f"\n=== Model Comparison ===")
print(f"Power Law R²: {r_squared:.4f}")
print(f"Linear R²: {r_squared_linear:.4f}")
print(f"Logarithmic R²: {r_squared_log:.4f}")

# Calculate AIC for model comparison
n = len(area)

# Power law residuals
residuals_power = richness - (c * (area ** z))
SSE_power = np.sum(residuals_power ** 2)
AIC_power = n * np.log(SSE_power / n) + 2 * 2  # 2 parameters

# Linear residuals
residuals_linear = richness - (intercept_linear + slope_linear * area)
SSE_linear = np.sum(residuals_linear ** 2)
AIC_linear = n * np.log(SSE_linear / n) + 2 * 2

# Logarithmic residuals
residuals_log = richness - (intercept_log + slope_log * log_area)
SSE_log = np.sum(residuals_log ** 2)
AIC_log = n * np.log(SSE_log / n) + 2 * 2

print(f"\nAIC (lower is better):")
print(f"Power Law AIC: {AIC_power:.2f}")
print(f"Linear AIC: {AIC_linear:.2f}")
print(f"Logarithmic AIC: {AIC_log:.2f}")

# Save results to file
results = {
    'Model': ['Power Law', 'Linear', 'Logarithmic'],
    'R_squared': [r_squared, r_squared_linear, r_squared_log],
    'AIC': [AIC_power, AIC_linear, AIC_log]
}
results_df = pd.DataFrame(results)
results_df.to_csv('outputs/model_comparison.csv', index=False)

# Save power law parameters
params = {
    'Parameter': ['c (coefficient)', 'z (exponent)', 'R_squared', 'p_value', 'std_err_z'],
    'Value': [c, z, r_squared, p_value, std_err]
}
params_df = pd.DataFrame(params)
params_df.to_csv('outputs/power_law_parameters.csv', index=False)

# Figure 1: Species-Area Relationship with Power Law Fit
fig, ax = plt.subplots(figsize=(10, 7))
ax.scatter(area, richness, s=80, alpha=0.7, edgecolor='black', linewidth=1, label='Observed data')
ax.plot(area_pred, richness_pred_power, 'r-', linewidth=2, label=f'Power law: S = {c:.2f} × A^{z:.3f}')
ax.set_xlabel('Island Area (km²)', fontsize=12)
ax.set_ylabel('Species Richness', fontsize=12)
ax.set_title('Species-Area Relationship for Islands', fontsize=14)
ax.legend(fontsize=10)
ax.text(0.05, 0.95, f'R² = {r_squared:.4f}\np < 0.001', transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
plt.tight_layout()
plt.savefig('report/images/species_area_power_law.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nFigure 1 saved: species_area_power_law.png")

# Figure 2: Log-Log Plot
fig, ax = plt.subplots(figsize=(10, 7))
ax.scatter(log_area, log_richness, s=80, alpha=0.7, edgecolor='black', linewidth=1, label='Observed data')
ax.plot(np.log(area_pred), np.log(richness_pred_power), 'r-', linewidth=2, 
        label=f'Linear fit: log(S) = {intercept:.3f} + {z:.3f} × log(A)')
ax.set_xlabel('log(Island Area) [log km²]', fontsize=12)
ax.set_ylabel('log(Species Richness)', fontsize=12)
ax.set_title('Species-Area Relationship (Log-Log Scale)', fontsize=14)
ax.legend(fontsize=10)
ax.text(0.05, 0.95, f'Slope (z) = {z:.3f} ± {std_err:.3f}\nR² = {r_squared:.4f}', 
        transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
plt.tight_layout()
plt.savefig('report/images/log_log_plot.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: log_log_plot.png")

# Figure 3: Model Comparison
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Power Law
axes[0].scatter(area, richness, s=60, alpha=0.7, edgecolor='black', linewidth=1)
axes[0].plot(area_pred, richness_pred_power, 'r-', linewidth=2)
axes[0].set_xlabel('Island Area (km²)', fontsize=11)
axes[0].set_ylabel('Species Richness', fontsize=11)
axes[0].set_title(f'Power Law Model\nR² = {r_squared:.4f}', fontsize=12)

# Linear
axes[1].scatter(area, richness, s=60, alpha=0.7, edgecolor='black', linewidth=1)
axes[1].plot(area_pred, richness_pred_linear, 'g-', linewidth=2)
axes[1].set_xlabel('Island Area (km²)', fontsize=11)
axes[1].set_ylabel('Species Richness', fontsize=11)
axes[1].set_title(f'Linear Model\nR² = {r_squared_linear:.4f}', fontsize=12)

# Logarithmic
axes[2].scatter(area, richness, s=60, alpha=0.7, edgecolor='black', linewidth=1)
axes[2].plot(area_pred, richness_pred_log, 'b-', linewidth=2)
axes[2].set_xlabel('Island Area (km²)', fontsize=11)
axes[2].set_ylabel('Species Richness', fontsize=11)
axes[2].set_title(f'Logarithmic Model\nR² = {r_squared_log:.4f}', fontsize=12)

plt.tight_layout()
plt.savefig('report/images/model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved: model_comparison.png")

# Figure 4: Residuals Analysis
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Residuals vs Fitted
fitted_values = c * (area ** z)
residuals = richness - fitted_values
axes[0].scatter(fitted_values, residuals, s=60, alpha=0.7, edgecolor='black', linewidth=1)
axes[0].axhline(y=0, color='r', linestyle='--', linewidth=1.5)
axes[0].set_xlabel('Fitted Values', fontsize=11)
axes[0].set_ylabel('Residuals', fontsize=11)
axes[0].set_title('Residuals vs Fitted Values', fontsize=12)

# Q-Q Plot
stats.probplot(residuals, dist="norm", plot=axes[1])
axes[1].set_title('Normal Q-Q Plot of Residuals', fontsize=12)

plt.tight_layout()
plt.savefig('report/images/residuals_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved: residuals_analysis.png")

# Figure 5: Conservation Implications
fig, ax = plt.subplots(figsize=(10, 7))

# Calculate species for different area scenarios
area_scenarios = np.array([0.5, 1, 2, 5, 10, 20, 50, 100])
species_predicted = c * (area_scenarios ** z)

ax.bar(range(len(area_scenarios)), species_predicted, color='steelblue', edgecolor='black', linewidth=1)
ax.set_xticks(range(len(area_scenarios)))
ax.set_xticklabels([f'{a:.1f}' for a in area_scenarios])
ax.set_xlabel('Island Area (km²)', fontsize=12)
ax.set_ylabel('Predicted Species Richness', fontsize=12)
ax.set_title('Predicted Species Richness for Different Island Areas', fontsize=14)

# Add value labels on bars
for i, v in enumerate(species_predicted):
    ax.text(i, v + 0.5, f'{v:.1f}', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig('report/images/conservation_predictions.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 5 saved: conservation_predictions.png")

# Calculate some conservation-relevant metrics
print("\n=== Conservation Implications ===")
print(f"Doubling area increases species by factor: {2**z:.3f}")
print(f"10-fold area increase multiplies species by: {10**z:.3f}")
print(f"\nPredicted species for different areas:")
for a, s in zip(area_scenarios, species_predicted):
    print(f"  Area = {a:6.1f} km² → Species = {s:.1f}")

# Identify potential outliers (islands with unusual species richness)
standardized_residuals = residuals / np.std(residuals)
outlier_threshold = 2
outliers = data[np.abs(standardized_residuals) > outlier_threshold]
print(f"\nPotential outliers (|standardized residual| > 2):")
if len(outliers) > 0:
    print(outliers)
else:
    print("No significant outliers detected.")

print("\nAnalysis complete!")