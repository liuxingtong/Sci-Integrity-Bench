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
df = pd.read_csv('data/island_species.csv')
print(f"Data shape: {df.shape}")
print(df.head())
print(df.describe())

# Create outputs directory if not exists
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Species-Area Relationship: S = c * A^z
# Linearized: log(S) = log(c) + z * log(A)

# Prepare log-transformed data
df['log_area'] = np.log10(df['area_km2'])
df['log_species'] = np.log10(df['species_richness'])

# Fit linear regression on log-transformed data
slope, intercept, r_value, p_value, std_err = stats.linregress(df['log_area'], df['log_species'])

print(f"\nSpecies-Area Relationship (Power Law Model):")
print(f"log10(S) = {intercept:.4f} + {slope:.4f} * log10(A)")
print(f"R-squared: {r_value**2:.4f}")
print(f"P-value: {p_value:.6f}")
print(f"z (slope): {slope:.4f} ± {std_err:.4f}")
print(f"c (10^intercept): {10**intercept:.4f}")

# Calculate predicted values
df['log_species_pred'] = intercept + slope * df['log_area']
df['species_pred'] = 10 ** df['log_species_pred']

# Figure 1: Species-Area Relationship (log-log plot)
fig1, ax1 = plt.subplots(figsize=(10, 8))
ax1.scatter(df['log_area'], df['log_species'], s=100, alpha=0.7, 
            edgecolors='black', linewidth=1, label='Observed data', zorder=5)

# Plot regression line
x_range = np.linspace(df['log_area'].min(), df['log_area'].max(), 100)
y_range = intercept + slope * x_range
ax1.plot(x_range, y_range, 'r-', linewidth=2, 
         label=f'Fitted: log(S) = {intercept:.3f} + {slope:.3f}·log(A)\nR² = {r_value**2:.3f}')

ax1.set_xlabel('log10(Area) [km²]', fontsize=14)
ax1.set_ylabel('log10(Species Richness)', fontsize=14)
ax1.set_title('Species-Area Relationship (Log-Log Scale)', fontsize=16)
ax1.legend(loc='upper left', fontsize=12)
ax1.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/species_area_loglog.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/species_area_loglog.png")

# Figure 2: Species-Area Relationship (original scale)
fig2, ax2 = plt.subplots(figsize=(10, 8))
ax2.scatter(df['area_km2'], df['species_richness'], s=100, alpha=0.7,
            edgecolors='black', linewidth=1, label='Observed data', zorder=5)

# Plot power law curve
x_curve = np.linspace(df['area_km2'].min(), df['area_km2'].max(), 100)
y_curve = (10**intercept) * (x_curve ** slope)
ax2.plot(x_curve, y_curve, 'r-', linewidth=2,
         label=f'Fitted: S = {10**intercept:.3f} · A^{slope:.3f}\nR² = {r_value**2:.3f}')

ax2.set_xlabel('Island Area (km²)', fontsize=14)
ax2.set_ylabel('Species Richness', fontsize=14)
ax2.set_title('Species-Area Relationship (Original Scale)', fontsize=16)
ax2.legend(loc='upper left', fontsize=12)
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/species_area_original.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/species_area_original.png")

# Figure 3: Residuals analysis
fig3, axes = plt.subplots(1, 2, figsize=(14, 6))

# Residuals vs Fitted
residuals = df['log_species'] - df['log_species_pred']
axes[0].scatter(df['log_species_pred'], residuals, s=100, alpha=0.7,
                edgecolors='black', linewidth=1)
axes[0].axhline(y=0, color='r', linestyle='--', linewidth=2)
axes[0].set_xlabel('Fitted log10(Species Richness)', fontsize=12)
axes[0].set_ylabel('Residuals', fontsize=12)
axes[0].set_title('Residuals vs Fitted Values', fontsize=14)
axes[0].grid(True, alpha=0.3)

# Q-Q plot for normality of residuals
stats.probplot(residuals, dist="norm", plot=axes[1])
axes[1].set_title('Q-Q Plot of Residuals', fontsize=14)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/residuals_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/residuals_analysis.png")

# Figure 4: Conservation implications - extinction risk
fig4, ax4 = plt.subplots(figsize=(10, 8))

# Calculate species loss for different area reductions
area_ratios = np.linspace(0.1, 1.0, 100)
species_ratios = area_ratios ** slope

ax4.plot(area_ratios * 100, species_ratios * 100, 'b-', linewidth=3)
ax4.axhline(y=50, color='r', linestyle='--', linewidth=2, label='50% species loss')
ax4.axvline(x=50, color='g', linestyle='--', linewidth=2, label='50% habitat loss')

# Mark key points
key_area_loss = [10, 25, 50, 75, 90]
for area_loss in key_area_loss:
    remaining_area = (100 - area_loss) / 100
    remaining_species = remaining_area ** slope
    species_loss = (1 - remaining_species) * 100
    ax4.scatter([100 - area_loss], [remaining_species * 100], s=150, 
                color='darkred', zorder=5)
    ax4.annotate(f'{area_loss}% area loss\n→ {species_loss:.1f}% species loss',
                 xy=(100 - area_loss, remaining_species * 100),
                 xytext=(100 - area_loss - 15, remaining_species * 100 + 10),
                 fontsize=10, ha='right',
                 arrowprops=dict(arrowstyle='->', color='darkred'))

ax4.set_xlabel('Remaining Habitat Area (%)', fontsize=14)
ax4.set_ylabel('Remaining Species Richness (%)', fontsize=14)
ax4.set_title(f'Extinction Risk from Habitat Loss (z = {slope:.3f})', fontsize=16)
ax4.legend(loc='upper left', fontsize=12)
ax4.set_xlim(0, 105)
ax4.set_ylim(0, 105)
ax4.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/extinction_risk.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/extinction_risk.png")

# Save summary statistics
summary = {
    'model': 'Power Law (S = c * A^z)',
    'intercept_log': intercept,
    'slope_z': slope,
    'c_value': 10**intercept,
    'r_squared': r_value**2,
    'p_value': p_value,
    'std_error': std_err,
    'n_observations': len(df)
}

# Save results to CSV
df.to_csv('outputs/fitted_data.csv', index=False)
print("Saved: outputs/fitted_data.csv")

# Print summary
print("\n" + "="*60)
print("SUMMARY FOR CONSERVATION PLANNING")
print("="*60)
print(f"Fitted z-value: {slope:.4f} (typical range: 0.15-0.35)")
print(f"This means: 10% habitat loss → approximately {(1 - 0.9**slope)*100:.1f}% species loss")
print(f"50% habitat loss → approximately {(1 - 0.5**slope)*100:.1f}% species loss")
print(f"90% habitat loss → approximately {(1 - 0.1**slope)*100:.1f}% species loss")
print("="*60)
