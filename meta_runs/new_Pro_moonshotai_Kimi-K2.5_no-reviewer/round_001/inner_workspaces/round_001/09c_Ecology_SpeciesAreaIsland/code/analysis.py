"""
Species-Area Relationship Analysis for Island Biogeography
===========================================================

This script analyzes the species-area relationship using island data
and discusses conservation planning implications.
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

# Create figure directory
import os
os.makedirs('report/images', exist_ok=True)

# ============================================================
# 1. LOAD AND EXPLORE DATA
# ============================================================
print("=" * 60)
print("SPECIES-AREA RELATIONSHIP ANALYSIS")
print("=" * 60)

# Load data
df = pd.read_csv('data/island_species.csv')
print(f"\nDataset: {len(df)} islands")
print(f"\nData Summary:")
print(df.describe())

# Extract variables
area = df['area_km2'].values
richness = df['species_richness'].values

print(f"\nArea range: {area.min():.3f} - {area.max():.3f} km²")
print(f"Richness range: {richness.min()} - {richness.max()} species")

# ============================================================
# 2. VISUALIZE RAW DATA
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Raw scatter plot
ax1 = axes[0, 0]
ax1.scatter(area, richness, c='steelblue', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
ax1.set_xlabel('Island Area (km²)', fontsize=11)
ax1.set_ylabel('Species Richness', fontsize=11)
ax1.set_title('Species-Area Relationship (Raw Scale)', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)

# Add correlation coefficient
corr_raw = np.corrcoef(area, richness)[0, 1]
ax1.text(0.05, 0.95, f'r = {corr_raw:.3f}', transform=ax1.transAxes, 
         fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Plot 2: Log-log scatter plot
ax2 = axes[0, 1]
log_area = np.log10(area)
log_richness = np.log10(richness)
ax2.scatter(log_area, log_richness, c='darkgreen', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
ax2.set_xlabel('log₁₀(Area)', fontsize=11)
ax2.set_ylabel('log₁₀(Species Richness)', fontsize=11)
ax2.set_title('Species-Area Relationship (Log-Log Scale)', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)

# Add correlation coefficient for log-log
corr_log = np.corrcoef(log_area, log_richness)[0, 1]
ax2.text(0.05, 0.95, f'r = {corr_log:.3f}', transform=ax2.transAxes, 
         fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Plot 3: Distribution of areas
ax3 = axes[1, 0]
ax3.hist(area, bins=10, color='coral', edgecolor='black', alpha=0.7)
ax3.set_xlabel('Island Area (km²)', fontsize=11)
ax3.set_ylabel('Frequency', fontsize=11)
ax3.set_title('Distribution of Island Areas', fontsize=12, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')

# Plot 4: Distribution of richness
ax4 = axes[1, 1]
ax4.hist(richness, bins=10, color='mediumpurple', edgecolor='black', alpha=0.7)
ax4.set_xlabel('Species Richness', fontsize=11)
ax4.set_ylabel('Frequency', fontsize=11)
ax4.set_title('Distribution of Species Richness', fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('report/images/figure1_data_overview.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nFigure 1 saved: Data overview plots")

# ============================================================
# 3. POWER LAW MODEL FITTING
# ============================================================
print("\n" + "=" * 60)
print("MODEL FITTING: POWER LAW S = cA^z")
print("=" * 60)

# Define power law function
def power_law(A, c, z):
    """Power law: S = c * A^z"""
    return c * (A ** z)

# Fit power law using non-linear least squares
popt, pcov = curve_fit(power_law, area, richness, p0=[10, 0.3], maxfev=10000)
c_fit, z_fit = popt
c_err, z_err = np.sqrt(np.diag(pcov))

print(f"\nPower Law Parameters:")
print(f"  c (intercept) = {c_fit:.4f} ± {c_err:.4f}")
print(f"  z (slope)     = {z_fit:.4f} ± {z_err:.4f}")

# Calculate R² for power law
richness_pred_power = power_law(area, c_fit, z_fit)
ss_res = np.sum((richness - richness_pred_power) ** 2)
ss_tot = np.sum((richness - np.mean(richness)) ** 2)
r2_power = 1 - (ss_res / ss_tot)
rmse_power = np.sqrt(np.mean((richness - richness_pred_power) ** 2))

print(f"\nPower Law Model Performance:")
print(f"  R² = {r2_power:.4f}")
print(f"  RMSE = {rmse_power:.4f}")

# ============================================================
# 4. LINEAR REGRESSION ON LOG-LOG SCALE
# ============================================================
print("\n" + "=" * 60)
print("LOG-LOG LINEAR REGRESSION")
print("=" * 60)

# Linear regression on log-transformed data
slope, intercept, r_value, p_value, std_err = stats.linregress(log_area, log_richness)

print(f"\nLinear Regression on Log-Log Scale:")
print(f"  Intercept (log c) = {intercept:.4f}")
print(f"  Slope (z)         = {slope:.4f}")
print(f"  R²                = {r_value**2:.4f}")
print(f"  p-value           = {p_value:.2e}")
print(f"  Standard Error    = {std_err:.4f}")

# Convert intercept to c
c_from_log = 10 ** intercept
print(f"\nConverted c = 10^{intercept:.4f} = {c_from_log:.4f}")

# Predictions from log-log model
log_richness_pred = intercept + slope * log_area
richness_pred_log = 10 ** log_richness_pred

# Calculate R² and RMSE for log-log model
r2_log = r_value ** 2
rmse_log = np.sqrt(np.mean((richness - richness_pred_log) ** 2))

print(f"\nLog-Log Model Performance:")
print(f"  R² = {r2_log:.4f}")
print(f"  RMSE = {rmse_log:.4f}")

# ============================================================
# 5. MODEL COMPARISON AND VISUALIZATION
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Power law fit on raw scale
ax1 = axes[0, 0]
area_smooth = np.linspace(area.min(), area.max(), 200)
richness_smooth = power_law(area_smooth, c_fit, z_fit)

ax1.scatter(area, richness, c='steelblue', s=80, alpha=0.7, edgecolors='black', linewidth=0.5, label='Observed Data')
ax1.plot(area_smooth, richness_smooth, 'r-', linewidth=2, label=f'Power Law: S = {c_fit:.2f}A^{z_fit:.3f}')
ax1.set_xlabel('Island Area (km²)', fontsize=11)
ax1.set_ylabel('Species Richness', fontsize=11)
ax1.set_title('Power Law Fit (Raw Scale)', fontsize=12, fontweight='bold')
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)

# Plot 2: Log-log fit
ax2 = axes[0, 1]
log_area_smooth = np.linspace(log_area.min(), log_area.max(), 200)
log_richness_smooth = intercept + slope * log_area_smooth

ax2.scatter(log_area, log_richness, c='darkgreen', s=80, alpha=0.7, edgecolors='black', linewidth=0.5, label='Observed Data')
ax2.plot(log_area_smooth, log_richness_smooth, 'r-', linewidth=2, 
         label=f'Linear Fit: log S = {intercept:.3f} + {slope:.3f} log A')
ax2.set_xlabel('log₁₀(Area)', fontsize=11)
ax2.set_ylabel('log₁₀(Species Richness)', fontsize=11)
ax2.set_title('Log-Log Linear Fit', fontsize=12, fontweight='bold')
ax2.legend(loc='lower right', fontsize=9)
ax2.grid(True, alpha=0.3)

# Plot 3: Observed vs Predicted (Power Law)
ax3 = axes[1, 0]
ax3.scatter(richness, richness_pred_power, c='purple', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
min_val = min(richness.min(), richness_pred_power.min())
max_val = max(richness.max(), richness_pred_power.max())
ax3.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='1:1 Line')
ax3.set_xlabel('Observed Richness', fontsize=11)
ax3.set_ylabel('Predicted Richness (Power Law)', fontsize=11)
ax3.set_title(f'Observed vs Predicted (Power Law)\nR² = {r2_power:.3f}, RMSE = {rmse_power:.2f}', fontsize=12, fontweight='bold')
ax3.legend(loc='upper left', fontsize=9)
ax3.grid(True, alpha=0.3)

# Plot 4: Residuals analysis
ax4 = axes[1, 1]
residuals = richness - richness_pred_power
ax4.scatter(richness_pred_power, residuals, c='darkorange', s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
ax4.axhline(y=0, color='r', linestyle='--', linewidth=2)
ax4.set_xlabel('Predicted Richness', fontsize=11)
ax4.set_ylabel('Residuals', fontsize=11)
ax4.set_title('Residuals Plot (Power Law)', fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure2_model_fits.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nFigure 2 saved: Model fitting results")

# ============================================================
# 6. BOOTSTRAP CONFIDENCE INTERVALS
# ============================================================
print("\n" + "=" * 60)
print("BOOTSTRAP CONFIDENCE INTERVALS")
print("=" * 60)

n_bootstrap = 1000
z_bootstrap = []
c_bootstrap = []

for i in range(n_bootstrap):
    # Resample with replacement
    indices = np.random.choice(len(area), size=len(area), replace=True)
    area_boot = area[indices]
    richness_boot = richness[indices]
    
    # Fit power law
    try:
        popt_boot, _ = curve_fit(power_law, area_boot, richness_boot, p0=[10, 0.3], maxfev=10000)
        c_bootstrap.append(popt_boot[0])
        z_bootstrap.append(popt_boot[1])
    except:
        pass

z_bootstrap = np.array(z_bootstrap)
c_bootstrap = np.array(c_bootstrap)

z_ci_low, z_ci_high = np.percentile(z_bootstrap, [2.5, 97.5])
c_ci_low, c_ci_high = np.percentile(c_bootstrap, [2.5, 97.5])

print(f"\nBootstrap Results (n={n_bootstrap}):")
print(f"  z: {z_fit:.4f} [95% CI: {z_ci_low:.4f} - {z_ci_high:.4f}]")
print(f"  c: {c_fit:.4f} [95% CI: {c_ci_low:.4f} - {c_ci_high:.4f}]")

# ============================================================
# 7. CONSERVATION PLANNING ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("CONSERVATION PLANNING IMPLICATIONS")
print("=" * 60)

# Calculate species loss scenarios
print("\nSpecies Loss Scenarios (using z = {:.3f}):".format(z_fit))
print("-" * 50)

# Scenario 1: Effect of habitat loss
area_loss_percentages = [10, 25, 50, 75, 90]
print("\n1. Effect of Habitat Loss:")
print(f"{'Area Loss %':<15} {'Remaining Area %':<20} {'Species Remaining %':<20}")
print("-" * 55)
for loss_pct in area_loss_percentages:
    remaining_area_frac = (100 - loss_pct) / 100
    species_remaining_frac = remaining_area_frac ** z_fit
    species_remaining_pct = species_remaining_frac * 100
    print(f"{loss_pct:<15} {100-loss_pct:<20} {species_remaining_pct:<20.1f}")

# Scenario 2: Reserve sizing for target species preservation
print("\n2. Reserve Sizing for Target Species Preservation:")
print(f"{'Target Species %':<20} {'Required Area %':<20}")
print("-" * 40)
target_species_pcts = [90, 80, 70, 50, 25]
for target_pct in target_species_pcts:
    target_frac = target_pct / 100
    required_area_frac = target_frac ** (1 / z_fit)
    required_area_pct = required_area_frac * 100
    print(f"{target_pct:<20} {required_area_pct:<20.1f}")

# Scenario 3: SLOSS debate (Single Large vs Several Small)
print("\n3. SLOSS Analysis (Single Large vs Several Small):")
total_area = 100  # arbitrary units
n_patches_options = [1, 2, 4, 10, 25]
print(f"{'# Patches':<15} {'Area per Patch':<20} {'Total Species':<20}")
print("-" * 55)
for n_patches in n_patches_options:
    area_per_patch = total_area / n_patches
    species_per_patch = c_fit * (area_per_patch ** z_fit)
    # Using species-area with consideration for patch isolation (simplified)
    total_species = species_per_patch * (n_patches ** 0.1)  # slight increase for multiple patches
    print(f"{n_patches:<15} {area_per_patch:<20.2f} {total_species:<20.1f}")

# ============================================================
# 8. VISUALIZE CONSERVATION SCENARIOS
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Species-Area curve with confidence interval
ax1 = axes[0, 0]
area_range = np.linspace(0.1, area.max() * 1.5, 200)

# Calculate confidence intervals
richness_mean = power_law(area_range, c_fit, z_fit)
richness_ci_low = power_law(area_range, c_ci_low, z_ci_low)
richness_ci_high = power_law(area_range, c_ci_high, z_ci_high)

ax1.fill_between(area_range, richness_ci_low, richness_ci_high, alpha=0.3, color='blue', label='95% CI')
ax1.plot(area_range, richness_mean, 'b-', linewidth=2, label=f'S = {c_fit:.2f}A^{z_fit:.3f}')
ax1.scatter(area, richness, c='red', s=80, alpha=0.7, edgecolors='black', linewidth=0.5, label='Observed Data', zorder=5)
ax1.set_xlabel('Island Area (km²)', fontsize=11)
ax1.set_ylabel('Species Richness', fontsize=11)
ax1.set_title('Species-Area Curve with 95% CI', fontsize=12, fontweight='bold')
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)

# Plot 2: Habitat loss impact
ax2 = axes[0, 1]
loss_range = np.linspace(0, 99, 100)
remaining_species = ((100 - loss_range) / 100) ** z_fit * 100
ax2.plot(loss_range, remaining_species, 'g-', linewidth=2)
ax2.fill_between(loss_range, 0, remaining_species, alpha=0.3, color='green')
ax2.set_xlabel('Habitat Loss (%)', fontsize=11)
ax2.set_ylabel('Species Remaining (%)', fontsize=11)
ax2.set_title('Species Loss vs Habitat Loss', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, 100)
ax2.set_ylim(0, 100)

# Add annotations
for loss in [25, 50, 75]:
    sp_remaining = ((100 - loss) / 100) ** z_fit * 100
    ax2.annotate(f'{sp_remaining:.1f}%', xy=(loss, sp_remaining), 
                xytext=(loss+5, sp_remaining-10), fontsize=9,
                arrowprops=dict(arrowstyle='->', color='black', lw=0.5))

# Plot 3: Reserve size requirements
ax3 = axes[1, 0]
target_species_range = np.linspace(10, 100, 100)
required_area = (target_species_range / 100) ** (1 / z_fit) * 100
ax3.plot(target_species_range, required_area, 'purple', linewidth=2)
ax3.fill_between(target_species_range, 0, required_area, alpha=0.3, color='purple')
ax3.set_xlabel('Target Species Preservation (%)', fontsize=11)
ax3.set_ylabel('Required Area (% of original)', fontsize=11)
ax3.set_title('Reserve Size Requirements', fontsize=12, fontweight='bold')
ax3.grid(True, alpha=0.3)
ax3.set_xlim(10, 100)
ax3.set_ylim(0, 100)

# Add annotations
for target in [50, 80, 95]:
    req_area = (target / 100) ** (1 / z_fit) * 100
    ax3.annotate(f'{req_area:.1f}%', xy=(target, req_area), 
                xytext=(target-15, req_area+10), fontsize=9,
                arrowprops=dict(arrowstyle='->', color='black', lw=0.5))

# Plot 4: z-value comparison with literature
ax4 = axes[1, 1]
literature_z = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
literature_labels = ['Mainland\n(0.15)', 'Continental\n(0.20)', 'Islands\n(0.25)', 
                     'Islands\n(0.30)', 'Islands\n(0.35)', 'Islands\n(0.40)']
colors = ['lightblue'] * 6

# Highlight our fitted z
our_z_idx = np.argmin(np.abs(np.array(literature_z) - z_fit))
colors[our_z_idx] = 'orange'

bars = ax4.bar(literature_labels, literature_z, color=colors, edgecolor='black', alpha=0.8)
ax4.axhline(y=z_fit, color='red', linestyle='--', linewidth=2, label=f'Our study: z = {z_fit:.3f}')
ax4.set_ylabel('z-value', fontsize=11)
ax4.set_title('Comparison with Literature Values', fontsize=12, fontweight='bold')
ax4.legend(loc='upper left', fontsize=9)
ax4.grid(True, alpha=0.3, axis='y')
ax4.set_ylim(0, 0.5)

plt.tight_layout()
plt.savefig('report/images/figure3_conservation.png', dpi=300, bbox_inches='tight')
plt.close()
print("\nFigure 3 saved: Conservation planning analysis")

# ============================================================
# 9. SAVE RESULTS
# ============================================================
results = {
    'parameter': ['c', 'z', 'R² (power law)', 'RMSE (power law)', 
                  'R² (log-log)', 'z_lower_95CI', 'z_upper_95CI',
                  'c_lower_95CI', 'c_upper_95CI'],
    'value': [c_fit, z_fit, r2_power, rmse_power, 
              r2_log, z_ci_low, z_ci_high, c_ci_low, c_ci_high],
    'description': ['Power law intercept', 'Power law exponent (species-area slope)',
                    'Coefficient of determination (power law)', 'Root mean square error',
                    'Coefficient of determination (log-log)', 
                    'Lower 95% CI for z', 'Upper 95% CI for z',
                    'Lower 95% CI for c', 'Upper 95% CI for c']
}

results_df = pd.DataFrame(results)
results_df.to_csv('outputs/model_results.csv', index=False)
print("\nResults saved to outputs/model_results.csv")

# Save predictions
df['predicted_richness'] = richness_pred_power
df['residuals'] = residuals
df.to_csv('outputs/data_with_predictions.csv', index=False)
print("Data with predictions saved to outputs/data_with_predictions.csv")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
