import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats, optimize
import statsmodels.api as sm
from sklearn.metrics import r2_score, mean_squared_error
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the processed data
df = pd.read_csv('../outputs/processed_data.csv')
print("Loaded processed data with shape:", df.shape)

# Create output directory for figures
os.makedirs('../report/images', exist_ok=True)

# Define the classic species-area model: S = c * A^z
# In log form: log(S) = log(c) + z * log(A)

# 1. Fit linear model on log-transformed data (standard approach)
X_log = sm.add_constant(df['log_area'])  # Add constant for intercept
y_log = df['log_richness']

model_log = sm.OLS(y_log, X_log).fit()
print("\n=== Log-Log Linear Model (S = cA^z) ===")
print(model_log.summary())

# Extract parameters
log_c = model_log.params['const']  # log10(c)
z = model_log.params['log_area']  # z-value
c = 10**log_c  # c-value

print(f"\nModel parameters:")
print(f"c = {c:.4f}")
print(f"z = {z:.4f}")
print(f"R² = {model_log.rsquared:.4f}")
print(f"Adjusted R² = {model_log.rsquared_adj:.4f}")

# 2. Fit power law directly using nonlinear least squares
def power_law(A, c, z):
    return c * (A**z)

# Initial guesses: c ~ 10, z ~ 0.25 (typical values from literature)
initial_guess = [10, 0.25]
params, params_covariance = optimize.curve_fit(power_law, 
                                               df['area_km2'], 
                                               df['species_richness'],
                                               p0=initial_guess,
                                               maxfev=5000)

c_nls, z_nls = params
print(f"\n=== Nonlinear Least Squares Fit ===")
print(f"c = {c_nls:.4f}")
print(f"z = {z_nls:.4f}")

# Calculate predictions for both models
area_range = np.linspace(df['area_km2'].min(), df['area_km2'].max(), 100)
log_area_range = np.log10(area_range)

# Predictions from log-linear model
log_richness_pred = log_c + z * log_area_range
richness_pred_loglinear = 10**log_richness_pred

# Predictions from nonlinear fit
richness_pred_nls = power_law(area_range, c_nls, z_nls)

# 3. Calculate model performance metrics
# For log-linear model
log_pred = log_c + z * df['log_area']
richness_pred_log = 10**log_pred
r2_log = r2_score(df['species_richness'], richness_pred_log)
rmse_log = np.sqrt(mean_squared_error(df['species_richness'], richness_pred_log))

# For nonlinear model
richness_pred_nls_data = power_law(df['area_km2'], c_nls, z_nls)
r2_nls = r2_score(df['species_richness'], richness_pred_nls_data)
rmse_nls = np.sqrt(mean_squared_error(df['species_richness'], richness_pred_nls_data))

print(f"\n=== Model Performance ===")
print(f"Log-linear model: R² = {r2_log:.4f}, RMSE = {rmse_log:.4f}")
print(f"Nonlinear model: R² = {r2_nls:.4f}, RMSE = {rmse_nls:.4f}")

# 4. Create comprehensive visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Panel A: Raw data with both fitted curves
ax = axes[0, 0]
ax.scatter(df['area_km2'], df['species_richness'], alpha=0.7, s=80, label='Observations')
ax.plot(area_range, richness_pred_loglinear, 'r-', linewidth=2, 
        label=f'Log-linear: S = {c:.2f}A$^{{{z:.3f}}}$ (R²={r2_log:.3f})')
ax.plot(area_range, richness_pred_nls, 'g--', linewidth=2, 
        label=f'Nonlinear: S = {c_nls:.2f}A$^{{{z_nls:.3f}}}$ (R²={r2_nls:.3f})')
ax.set_xlabel('Island Area (km²)', fontsize=12)
ax.set_ylabel('Species Richness', fontsize=12)
ax.set_title('A. Species-Area Relationship with Fitted Models', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

# Panel B: Log-log plot with linear fit
ax = axes[0, 1]
ax.scatter(df['log_area'], df['log_richness'], alpha=0.7, s=80, label='Observations')
ax.plot(log_area_range, log_richness_pred, 'r-', linewidth=2, 
        label=f'Fit: log(S) = {log_c:.3f} + {z:.3f}·log(A)')
ax.set_xlabel('log10(Area) (log10 km²)', fontsize=12)
ax.set_ylabel('log10(Species Richness)', fontsize=12)
ax.set_title('B. Log-Log Transformation with Linear Fit', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

# Panel C: Residuals from log-linear model
ax = axes[1, 0]
residuals_log = df['species_richness'] - richness_pred_log
ax.scatter(df['area_km2'], residuals_log, alpha=0.7, s=80)
ax.axhline(y=0, color='r', linestyle='-', alpha=0.5)
ax.set_xlabel('Island Area (km²)', fontsize=12)
ax.set_ylabel('Residuals (Observed - Predicted)', fontsize=12)
ax.set_title('C. Residuals from Log-Linear Model', fontsize=14)
ax.grid(True, alpha=0.3)

# Panel D: QQ plot of residuals
ax = axes[1, 1]
stats.probplot(residuals_log, dist="norm", plot=ax)
ax.set_title('D. Q-Q Plot of Residuals (Normality Check)', fontsize=14)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/model_fits.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nFigures saved to report/images/model_fits.png")

# 5. Conservation implications: Extinction debt and reserve sizing
print("\n=== Conservation Implications ===")

# Calculate expected species loss for area reduction
current_area = df['area_km2'].mean()
print(f"Average island area: {current_area:.2f} km²")
print(f"Average species richness: {df['species_richness'].mean():.1f} species")

# For different area reductions
area_reductions = [0.1, 0.25, 0.5, 0.75, 0.9]  # 10%, 25%, 50%, 75%, 90% loss
print("\nPredicted species loss for area reduction (using z = {:.3f}):".format(z))
print("Area Reduction | Remaining Area | Species Remaining | Species Lost")
print("-" * 70)

for reduction in area_reductions:
    remaining_area = 1 - reduction
    # Using species-area relationship: S2/S1 = (A2/A1)^z
    species_remaining = remaining_area**z
    species_lost = 1 - species_remaining
    print(f"{reduction*100:3.0f}%          | {remaining_area:6.2f}        | {species_remaining*100:6.1f}%          | {species_lost*100:6.1f}%")

# Calculate minimum area to preserve X% of species
target_preservation = [0.5, 0.75, 0.9, 0.95]  # 50%, 75%, 90%, 95% of species
print("\nMinimum area needed to preserve target percentage of species:")
print("Target Preservation | Minimum Area Required")
print("-" * 50)

for target in target_preservation:
    # From S2/S1 = (A2/A1)^z, solve for A2/A1
    min_area_ratio = target**(1/z)
    print(f"{target*100:6.0f}%              | {min_area_ratio*100:6.1f}% of original area")

# Save model results
results_df = pd.DataFrame({
    'model': ['log_linear', 'nonlinear'],
    'c': [c, c_nls],
    'z': [z, z_nls],
    'r2': [r2_log, r2_nls],
    'rmse': [rmse_log, rmse_nls],
    'log_c': [log_c, np.log10(c_nls)]
})

results_df.to_csv('../outputs/model_results.csv', index=False)
print("\nModel results saved to outputs/model_results.csv")

# 6. Create a figure for conservation implications
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel A: Species loss vs area loss
ax = axes[0]
area_loss_percent = np.linspace(0, 0.95, 100)  # 0% to 95% area loss
species_loss_percent = 1 - (1 - area_loss_percent)**z

ax.plot(area_loss_percent*100, species_loss_percent*100, 'b-', linewidth=2)
ax.fill_between(area_loss_percent*100, 0, species_loss_percent*100, alpha=0.3)
ax.set_xlabel('Habitat Area Loss (%)', fontsize=12)
ax.set_ylabel('Predicted Species Loss (%)', fontsize=12)
ax.set_title('A. Extinction Debt: Species Loss vs Area Loss', fontsize=14)
ax.grid(True, alpha=0.3)
ax.set_xlim([0, 100])
ax.set_ylim([0, 100])

# Add reference lines
for loss in [10, 25, 50, 75, 90]:
    area_ratio = 1 - loss/100
    species_ratio = area_ratio**z
    species_loss = (1 - species_ratio) * 100
    ax.plot([loss, loss], [0, species_loss], 'r--', alpha=0.5, linewidth=0.5)
    ax.plot([0, loss], [species_loss, species_loss], 'r--', alpha=0.5, linewidth=0.5)
    ax.text(loss+1, species_loss+1, f'{species_loss:.0f}%', fontsize=9)

# Panel B: Area needed for species preservation
ax = axes[1]
species_preserve = np.linspace(0.1, 0.99, 100)  # 10% to 99% species preservation
area_needed = species_preserve**(1/z) * 100  # as percentage of original area

ax.plot(species_preserve*100, area_needed, 'g-', linewidth=2)
ax.fill_between(species_preserve*100, area_needed, 100, alpha=0.3)
ax.set_xlabel('Target Species Preservation (%)', fontsize=12)
ax.set_ylabel('Minimum Area Required (% of original)', fontsize=12)
ax.set_title('B. Reserve Sizing: Area Needed for Species Preservation', fontsize=14)
ax.grid(True, alpha=0.3)
ax.set_xlim([0, 100])
ax.set_ylim([0, 100])

# Add reference lines
for preserve in [50, 75, 90, 95]:
    area_required = (preserve/100)**(1/z) * 100
    ax.plot([preserve, preserve], [0, area_required], 'r--', alpha=0.5, linewidth=0.5)
    ax.plot([0, preserve], [area_required, area_required], 'r--', alpha=0.5, linewidth=0.5)
    ax.text(preserve+1, area_required+1, f'{area_required:.0f}%', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/conservation_implications.png', dpi=300, bbox_inches='tight')
plt.close()

print("Conservation implications figure saved to report/images/conservation_implications.png")