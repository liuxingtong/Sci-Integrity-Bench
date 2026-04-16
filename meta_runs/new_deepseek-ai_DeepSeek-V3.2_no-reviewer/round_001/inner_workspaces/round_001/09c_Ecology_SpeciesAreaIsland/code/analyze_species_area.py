import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
df = pd.read_csv('../data/island_species.csv')

# Create log-transformed variables for power law analysis
df['log_area'] = np.log10(df['area_km2'])
df['log_richness'] = np.log10(df['species_richness'])

print("=== Species-Area Relationship Analysis ===\n")
print("Data with log-transformed variables:")
print(df[['island_id', 'area_km2', 'species_richness', 'log_area', 'log_richness']].head())

# 1. Basic correlation analysis
corr_pearson = df['area_km2'].corr(df['species_richness'])
corr_spearman = df['area_km2'].corr(df['species_richness'], method='spearman')
corr_log = df['log_area'].corr(df['log_richness'])

print(f"\nCorrelation coefficients:")
print(f"Pearson (linear): {corr_pearson:.4f}")
print(f"Spearman (rank): {corr_spearman:.4f}")
print(f"Pearson (log-log): {corr_log:.4f}")

# 2. Linear regression on log-transformed data (power law)
X = df['log_area']
y = df['log_richness']
X_with_const = sm.add_constant(X)  # Add constant for intercept

model = sm.OLS(y, X_with_const)
results = model.fit()

print("\n=== Power Law Model (log S = log c + z * log A) ===")
print(results.summary())

# Extract parameters
intercept = results.params['const']
slope = results.params['log_area']

# Convert back to power law form: S = c * A^z
c = 10**intercept  # c = 10^(intercept)
z = slope

print(f"\nPower law parameters:")
print(f"c (constant) = {c:.4f}")
print(f"z (exponent) = {z:.4f}")
print(f"Model: S = {c:.4f} * A^{z:.4f}")

# 3. Calculate predictions
df['predicted_log_richness'] = results.predict(X_with_const)
df['predicted_richness'] = 10**df['predicted_log_richness']

# Calculate residuals
df['residuals'] = df['log_richness'] - df['predicted_log_richness']
df['residuals_abs'] = df['species_richness'] - df['predicted_richness']

# 4. Save results
results_df = df[['island_id', 'area_km2', 'species_richness', 
                 'predicted_richness', 'residuals_abs']]
results_df.to_csv('../outputs/model_predictions.csv', index=False)

# Save model summary
with open('../outputs/model_summary.txt', 'w') as f:
    f.write("Species-Area Relationship Analysis\n")
    f.write("="*50 + "\n\n")
    f.write(f"Power law model: S = c * A^z\n")
    f.write(f"c = {c:.4f}\n")
    f.write(f"z = {z:.4f}\n\n")
    f.write(f"Pearson correlation (log-log): {corr_log:.4f}\n")
    f.write(f"R-squared: {results.rsquared:.4f}\n")
    f.write(f"Adjusted R-squared: {results.rsquared_adj:.4f}\n\n")
    f.write("Model summary:\n")
    f.write(results.summary().as_text())

print("\nResults saved to outputs/model_predictions.csv and outputs/model_summary.txt")

# 5. Create visualizations
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Plot 1: Raw data scatter plot
axes[0, 0].scatter(df['area_km2'], df['species_richness'], alpha=0.7, edgecolors='k')
axes[0, 0].set_xlabel('Island Area (km²)')
axes[0, 0].set_ylabel('Species Richness')
axes[0, 0].set_title('Raw Species-Area Relationship')
axes[0, 0].grid(True, alpha=0.3)

# Add power law curve
area_range = np.linspace(df['area_km2'].min(), df['area_km2'].max(), 100)
richness_pred = c * area_range**z
axes[0, 0].plot(area_range, richness_pred, 'r-', linewidth=2, 
                label=f'S = {c:.2f} × A^{z:.3f}')
axes[0, 0].legend()

# Plot 2: Log-log plot with regression line
axes[0, 1].scatter(df['log_area'], df['log_richness'], alpha=0.7, edgecolors='k')
axes[0, 1].plot(df['log_area'], df['predicted_log_richness'], 'r-', linewidth=2)
axes[0, 1].set_xlabel('log₁₀(Area)')
axes[0, 1].set_ylabel('log₁₀(Species Richness)')
axes[0, 1].set_title('Log-Log Plot with Linear Regression')
axes[0, 1].grid(True, alpha=0.3)

# Add equation text
equation_text = f'log S = {intercept:.3f} + {slope:.3f} × log A\nR² = {results.rsquared:.3f}'
axes[0, 1].text(0.05, 0.95, equation_text, transform=axes[0, 1].transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# Plot 3: Residuals plot
axes[1, 0].scatter(df['predicted_log_richness'], df['residuals'], alpha=0.7, edgecolors='k')
axes[1, 0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
axes[1, 0].set_xlabel('Predicted log₁₀(Species Richness)')
axes[1, 0].set_ylabel('Residuals')
axes[1, 0].set_title('Residuals vs. Predicted Values')
axes[1, 0].grid(True, alpha=0.3)

# Plot 4: QQ plot for normality check
sm.qqplot(df['residuals'], line='45', fit=True, ax=axes[1, 1])
axes[1, 1].set_title('Q-Q Plot of Residuals')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/species_area_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nVisualization saved to report/images/species_area_analysis.png")

# 6. Additional analysis: Compare with alternative models
print("\n=== Alternative Model Comparison ===")

# Linear model (without log transformation)
X_linear = sm.add_constant(df['area_km2'])
y_linear = df['species_richness']
model_linear = sm.OLS(y_linear, X_linear)
results_linear = model_linear.fit()

print(f"Linear model R-squared: {results_linear.rsquared:.4f}")
print(f"Power law model R-squared: {results.rsquared:.4f}")

# Calculate AIC and BIC for model comparison
print(f"\nModel comparison (lower is better):")
print(f"Linear model AIC: {results_linear.aic:.2f}, BIC: {results_linear.bic:.2f}")
print(f"Power law model AIC: {results.aic:.2f}, BIC: {results.bic:.2f}")

# Save model comparison
with open('../outputs/model_comparison.txt', 'w') as f:
    f.write("Model Comparison\n")
    f.write("="*50 + "\n\n")
    f.write("1. Linear model (S = a + b*A):\n")
    f.write(f"   R-squared: {results_linear.rsquared:.4f}\n")
    f.write(f"   AIC: {results_linear.aic:.2f}\n")
    f.write(f"   BIC: {results_linear.bic:.2f}\n\n")
    f.write("2. Power law model (S = c*A^z):\n")
    f.write(f"   R-squared: {results.rsquared:.4f}\n")
    f.write(f"   AIC: {results.aic:.2f}\n")
    f.write(f"   BIC: {results.bic:.2f}\n\n")
    f.write("Conclusion: ")
    if results.aic < results_linear.aic:
        f.write("Power law model is preferred based on AIC.")
    else:
        f.write("Linear model is preferred based on AIC.")

print("\nAnalysis complete!")