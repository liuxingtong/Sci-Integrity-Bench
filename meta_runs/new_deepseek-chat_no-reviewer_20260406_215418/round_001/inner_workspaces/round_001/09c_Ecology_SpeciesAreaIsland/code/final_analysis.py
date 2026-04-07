import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats, optimize
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.metrics import r2_score, mean_squared_error
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data with diagnostics
df = pd.read_csv('../outputs/data_with_diagnostics.csv')
print("Loaded data with diagnostics, shape:", df.shape)

# Create output directory for figures
os.makedirs('../report/images', exist_ok=True)

print("\n=== Model Comparison with/without Outliers ===")

# 1. Original model with all data
X_all = sm.add_constant(df['log_area'])
y_all = df['log_richness']
model_all = sm.OLS(y_all, X_all).fit()

# 2. Model without outliers
df_no_outliers = df[~df['is_outlier']].copy()
X_no_out = sm.add_constant(df_no_outliers['log_area'])
y_no_out = df_no_outliers['log_richness']
model_no_out = sm.OLS(y_no_out, X_no_out).fit()

# 3. Robust regression using Huber's T (less sensitive to outliers)
model_robust = sm.RLM(y_all, X_all, M=sm.robust.norms.HuberT()).fit()

print("\nModel parameters (log(S) = log(c) + z*log(A)):")
print("Model                    | log(c)     | z         | R²       | n")
print("-" * 70)
print(f"All data                | {model_all.params['const']:.4f}    | {model_all.params['log_area']:.4f}    | {model_all.rsquared:.4f}  | {len(df)}")
print(f"Without outliers        | {model_no_out.params['const']:.4f}    | {model_no_out.params['log_area']:.4f}    | {model_no_out.rsquared:.4f}  | {len(df_no_outliers)}")
print(f"Robust regression       | {model_robust.params[0]:.4f}    | {model_robust.params[1]:.4f}    | -        | {len(df)}")

# Convert to power law form
print("\nPower law parameters (S = cA^z):")
print("Model                    | c          | z")
print("-" * 50)
print(f"All data                | {10**model_all.params['const']:.3f}     | {model_all.params['log_area']:.4f}")
print(f"Without outliers        | {10**model_no_out.params['const']:.3f}     | {model_no_out.params['log_area']:.4f}")
print(f"Robust regression       | {10**model_robust.params[0]:.3f}     | {model_robust.params[1]:.4f}")

# Calculate predictions for visualization
area_range = np.linspace(df['area_km2'].min(), df['area_km2'].max(), 100)
log_area_range = np.log10(area_range)

# Predictions from each model
pred_all = 10**(model_all.params['const'] + model_all.params['log_area'] * log_area_range)
pred_no_out = 10**(model_no_out.params['const'] + model_no_out.params['log_area'] * log_area_range)
pred_robust = 10**(model_robust.params[0] + model_robust.params[1] * log_area_range)

# Create comparison visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel A: Model comparison
ax = axes[0]
# Plot data points
ax.scatter(df['area_km2'][~df['is_outlier']], df['species_richness'][~df['is_outlier']], 
           alpha=0.6, s=60, label='Normal points', color='blue')
ax.scatter(df['area_km2'][df['is_outlier']], df['species_richness'][df['is_outlier']], 
           alpha=0.9, s=100, color='red', marker='o', edgecolors='k', linewidth=1.5,
           label=f'Outliers (n={df["is_outlier"].sum()})')

# Plot model fits
ax.plot(area_range, pred_all, 'k-', linewidth=2, label=f'All data: z={model_all.params["log_area"]:.3f}')
ax.plot(area_range, pred_no_out, 'g--', linewidth=2, label=f'No outliers: z={model_no_out.params["log_area"]:.3f}')
ax.plot(area_range, pred_robust, 'b:', linewidth=2, label=f'Robust: z={model_robust.params[1]:.3f}')

ax.set_xlabel('Island Area (km²)', fontsize=12)
ax.set_ylabel('Species Richness', fontsize=12)
ax.set_title('A. Model Comparison: Impact of Outliers', fontsize=14)
ax.legend(loc='best')
ax.grid(True, alpha=0.3)

# Panel B: z-value comparison across models
ax = axes[1]
models = ['All data', 'No outliers', 'Robust']
z_values = [model_all.params['log_area'], model_no_out.params['log_area'], model_robust.params[1]]
z_errors = [model_all.bse['log_area'], model_no_out.bse['log_area'], model_robust.bse[1]]

x_pos = np.arange(len(models))
ax.bar(x_pos, z_values, yerr=z_errors, capsize=10, alpha=0.7, color=['black', 'green', 'blue'])
ax.set_xticks(x_pos)
ax.set_xticklabels(models)
ax.set_ylabel('z-value (slope)', fontsize=12)
ax.set_title('B. Comparison of z-values Across Models', fontsize=14)
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, (z, err) in enumerate(zip(z_values, z_errors)):
    ax.text(i, z + 0.005, f'{z:.3f} ± {err:.3f}', 
            ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('../report/images/model_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nModel comparison figure saved to report/images/model_comparison.png")

# 4. Calculate confidence intervals for predictions
print("\n=== Confidence Intervals for Predictions ===")

# Get predictions and confidence intervals for log-linear model
predictions = model_all.get_prediction(X_all)
pred_summary = predictions.summary_frame(alpha=0.05)

# Convert back to linear scale
pred_linear = 10**pred_summary['mean']
ci_lower_linear = 10**pred_summary['mean_ci_lower']
ci_upper_linear = 10**pred_summary['mean_ci_upper']
pi_lower_linear = 10**pred_summary['obs_ci_lower']
pi_upper_linear = 10**pred_summary['obs_ci_upper']

# Create prediction interval visualization
plt.figure(figsize=(10, 6))

# Sort by area for clean plotting
sort_idx = np.argsort(df['area_km2'])
area_sorted = df['area_km2'].iloc[sort_idx].values
richness_sorted = df['species_richness'].iloc[sort_idx].values
pred_sorted = pred_linear.iloc[sort_idx].values
ci_lower_sorted = ci_lower_linear.iloc[sort_idx].values
ci_upper_sorted = ci_upper_linear.iloc[sort_idx].values
pi_lower_sorted = pi_lower_linear.iloc[sort_idx].values
pi_upper_sorted = pi_upper_linear.iloc[sort_idx].values

# Plot prediction intervals
plt.fill_between(area_sorted, pi_lower_sorted, pi_upper_sorted, 
                 alpha=0.2, color='gray', label='95% Prediction Interval')
plt.fill_between(area_sorted, ci_lower_sorted, ci_upper_sorted, 
                 alpha=0.3, color='blue', label='95% Confidence Interval')

# Plot data and fitted line
plt.scatter(df['area_km2'], df['species_richness'], alpha=0.7, s=60, label='Observations')
plt.plot(area_sorted, pred_sorted, 'r-', linewidth=2, label='Fitted model')

# Highlight outliers
outlier_mask = df['is_outlier'].iloc[sort_idx].values
if outlier_mask.any():
    plt.scatter(area_sorted[outlier_mask], richness_sorted[outlier_mask], 
                color='red', s=100, marker='o', edgecolors='k', linewidth=1.5,
                label=f'Outliers (n={outlier_mask.sum()})', zorder=5)

plt.xlabel('Island Area (km²)', fontsize=12)
plt.ylabel('Species Richness', fontsize=12)
plt.title('Species-Area Relationship with Confidence and Prediction Intervals', fontsize=14)
plt.legend(loc='best')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/prediction_intervals.png', dpi=300, bbox_inches='tight')
plt.close()

print("Prediction intervals figure saved to report/images/prediction_intervals.png")

# 5. Final conservation recommendations based on robust model
print("\n=== Final Conservation Recommendations ===")
print("Based on robust regression (less sensitive to outliers):")
print(f"z = {model_robust.params[1]:.4f}")
print(f"c = {10**model_robust.params[0]:.3f}")

z_final = model_robust.params[1]

print("\nSpecies loss predictions for habitat reduction:")
print("Habitat Loss | Expected Species Loss")
print("-" * 45)
for loss in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
    remaining = 1 - loss/100
    species_remaining = remaining**z_final
    species_loss = (1 - species_remaining) * 100
    print(f"{loss:3.0f}%        | {species_loss:5.1f}%")

print("\nMinimum protected area for species preservation:")
print("Target Preservation | Minimum Area Required")
print("-" * 45)
for preserve in [50, 75, 90, 95, 99]:
    area_needed = (preserve/100)**(1/z_final) * 100
    print(f"{preserve:6.0f}%        | {area_needed:6.1f}% of original habitat")

# Save final model results
final_results = pd.DataFrame({
    'model': ['all_data', 'no_outliers', 'robust'],
    'log_c': [model_all.params['const'], model_no_out.params['const'], model_robust.params[0]],
    'z': [model_all.params['log_area'], model_no_out.params['log_area'], model_robust.params[1]],
    'c': [10**model_all.params['const'], 10**model_no_out.params['const'], 10**model_robust.params[0]],
    'r2': [model_all.rsquared, model_no_out.rsquared, np.nan],
    'n': [len(df), len(df_no_outliers), len(df)]
})

final_results.to_csv('../outputs/final_model_results.csv', index=False)
print("\nFinal model results saved to outputs/final_model_results.csv")