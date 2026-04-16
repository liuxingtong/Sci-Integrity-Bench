import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 12

# Load data
df = pd.read_csv('../data/island_species.csv')
print("Data loaded:")
print(df.head())
print(f"\nShape: {df.shape}")
print(f"\nSummary statistics:")
print(df.describe())

# Species-Area Relationship: S = c * A^z
# Linearized: log(S) = log(c) + z * log(A)

# Log transform
log_area = np.log(df['area_km2'])
log_species = np.log(df['species_richness'])

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(log_area, log_species)

print(f"\n=== Species-Area Relationship Results ===")
print(f"Model: log(S) = {intercept:.4f} + {slope:.4f} * log(A)")
print(f"R-squared: {r_value**2:.4f}")
print(f"P-value: {p_value:.6f}")
print(f"Slope (z): {slope:.4f} +/- {std_err:.4f}")

# Back-transform to power law
c = np.exp(intercept)
z = slope
print(f"\nPower law: S = {c:.4f} * A^{z:.4f}")

# Create figure with multiple panels
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Panel 1: Raw data with fitted curve
ax1 = axes[0]
ax1.scatter(df['area_km2'], df['species_richness'], s=80, alpha=0.7, edgecolors='black', linewidth=0.5)

# Generate smooth curve for power law
area_range = np.linspace(df['area_km2'].min(), df['area_km2'].max(), 100)
species_pred = c * area_range ** z
ax1.plot(area_range, species_pred, 'r-', linewidth=2, label=f'S = {c:.2f} x A^{z:.3f}')
ax1.set_xlabel('Island Area (km2)')
ax1.set_ylabel('Species Richness')
ax1.set_title('Species-Area Relationship (Raw Scale)')
ax1.legend()

# Panel 2: Log-log plot with regression line
ax2 = axes[1]
ax2.scatter(log_area, log_species, s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
log_pred = intercept + slope * log_area
ax2.plot(log_area, log_pred, 'r-', linewidth=2, label=f'log(S) = {intercept:.2f} + {slope:.3f}xlog(A)')
ax2.set_xlabel('log(Island Area)')
ax2.set_ylabel('log(Species Richness)')
ax2.set_title('Species-Area Relationship (Log-Log Scale)')
ax2.legend()

# Add R-squared annotation
ax2.text(0.05, 0.95, f'R2 = {r_value**2:.4f}', transform=ax2.transAxes, 
         fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Panel 3: Residuals
ax3 = axes[2]
residuals = log_species - log_pred
ax3.scatter(log_pred, residuals, s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
ax3.axhline(y=0, color='r', linestyle='--', linewidth=2)
ax3.set_xlabel('Predicted log(Species Richness)')
ax3.set_ylabel('Residuals')
ax3.set_title('Residual Plot')

plt.tight_layout()
plt.savefig('../report/images/species_area_relationship.png', dpi=150, bbox_inches='tight')
plt.close()

# Create conservation implications figure
fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))

# Panel 1: Species accumulation with area
ax4 = axes2[0]
ax4.scatter(df['area_km2'], df['species_richness'], s=80, alpha=0.7, edgecolors='black', linewidth=0.5)
ax4.plot(area_range, species_pred, 'r-', linewidth=2)

# Highlight conservation scenarios
small_area = 1.0
large_area = 5.0
small_species = c * small_area ** z
large_species = c * large_area ** z

ax4.axvline(x=small_area, color='blue', linestyle='--', alpha=0.5, label=f'{small_area} km2 -> {small_species:.1f} spp')
ax4.axvline(x=large_area, color='green', linestyle='--', alpha=0.5, label=f'{large_area} km2 -> {large_species:.1f} spp')
ax4.axhline(y=small_species, color='blue', linestyle=':', alpha=0.5)
ax4.axhline(y=large_species, color='green', linestyle=':', alpha=0.5)

ax4.set_xlabel('Island Area (km2)')
ax4.set_ylabel('Species Richness')
ax4.set_title('Conservation Implications: Area vs Species')
ax4.legend(loc='lower right')

# Panel 2: Species loss from habitat reduction
ax5 = axes2[1]
area_reduction = np.linspace(0.1, 0.9, 100)  # 10% to 90% reduction
remaining_area = 1 - area_reduction
species_remaining = remaining_area ** z  # Relative species richness
species_loss = 1 - species_remaining

ax5.plot(area_reduction * 100, species_loss * 100, 'r-', linewidth=2)
ax5.fill_between(area_reduction * 100, species_loss * 100, alpha=0.3, color='red')
ax5.set_xlabel('Habitat Area Reduction (%)')
ax5.set_ylabel('Expected Species Loss (%)')
ax5.set_title(f'Predicted Species Loss from Habitat Reduction (z={z:.3f})')
ax5.grid(True, alpha=0.3)

# Add specific points
for reduction in [25, 50, 75]:
    loss = (1 - (1 - reduction/100) ** z) * 100
    ax5.plot(reduction, loss, 'ko')
    ax5.annotate(f'{reduction}% -> {loss:.1f}%', 
                 xy=(reduction, loss), xytext=(reduction+5, loss+5),
                 fontsize=9, arrowprops=dict(arrowstyle='->', alpha=0.5))

plt.tight_layout()
plt.savefig('../report/images/conservation_implications.png', dpi=150, bbox_inches='tight')
plt.close()

# Save results to file
results = {
    'model_intercept': intercept,
    'model_slope': slope,
    'r_squared': r_value**2,
    'p_value': p_value,
    'std_error': std_err,
    'c_parameter': c,
    'z_parameter': z
}

results_df = pd.DataFrame([results])
results_df.to_csv('../outputs/model_results.csv', index=False)

print("\n=== Analysis Complete ===")
print("Figures saved to report/images/")
print("Results saved to outputs/model_results.csv")
