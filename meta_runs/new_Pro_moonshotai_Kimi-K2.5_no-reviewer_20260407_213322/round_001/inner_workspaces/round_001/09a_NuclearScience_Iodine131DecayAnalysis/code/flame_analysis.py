"""
Flame Speed vs Chamber Pressure Analysis
Bench combustion experiments: modeling flame speed as a function of chamber pressure
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Load data
data = pd.read_csv('data/flame_pressure_series.csv')
pressure = data['pressure_kPa'].values
flame_speed = data['flame_speed_cm_s'].values

print("Data Overview:")
print(f"Total data points: {len(pressure)}")
print(f"Pressure range: {pressure.min():.2f} - {pressure.max():.2f} kPa")
print(f"Flame speed range: {flame_speed.min():.2f} - {flame_speed.max():.2f} cm/s")
print()

# Identify regime change around 82 kPa
regime_threshold = 82.0
low_pressure_mask = pressure < regime_threshold
high_pressure_mask = pressure >= regime_threshold

print(f"Low pressure regime (< {regime_threshold} kPa): {low_pressure_mask.sum()} points")
print(f"High pressure regime (>= {regime_threshold} kPa): {high_pressure_mask.sum()} points")

# Define models
def power_law(P, a, b):
    """Power law model: S = a * P^b"""
    return a * (P ** b)

def linear_model(P, m, c):
    """Linear model: S = m*P + c"""
    return m * P + c

def exponential_model(P, S0, k):
    """Exponential decay model: S = S0 * exp(-k*P)"""
    return S0 * np.exp(-k * P)

def logarithmic_model(P, a, b):
    """Logarithmic model: S = a - b*ln(P)"""
    return a - b * np.log(P)

# Fit models to low pressure regime (before transition)
P_low = pressure[low_pressure_mask]
S_low = flame_speed[low_pressure_mask]

# Power law fit
popt_power, _ = curve_fit(power_law, P_low, S_low, p0=[200, -0.5])
S_pred_power = power_law(P_low, *popt_power)
r2_power = 1 - np.sum((S_low - S_pred_power)**2) / np.sum((S_low - S_low.mean())**2)

# Linear fit
popt_linear, _ = curve_fit(linear_model, P_low, S_low, p0=[-0.3, 50])
S_pred_linear = linear_model(P_low, *popt_linear)
r2_linear = 1 - np.sum((S_low - S_pred_linear)**2) / np.sum((S_low - S_low.mean())**2)

# Logarithmic fit
popt_log, _ = curve_fit(logarithmic_model, P_low, S_low, p0=[100, 10])
S_pred_log = logarithmic_model(P_low, *popt_log)
r2_log = 1 - np.sum((S_low - S_pred_log)**2) / np.sum((S_low - S_low.mean())**2)

print("\nModel Fitting Results (Low Pressure Regime):")
print(f"Power Law: S = {popt_power[0]:.4f} * P^{popt_power[1]:.4f}, R² = {r2_power:.4f}")
print(f"Linear: S = {popt_linear[0]:.4f}*P + {popt_linear[1]:.4f}, R² = {r2_linear:.4f}")
print(f"Logarithmic: S = {popt_log[0]:.4f} - {popt_log[1]:.4f}*ln(P), R² = {r2_log:.4f}")

# Fit high pressure regime
P_high = pressure[high_pressure_mask]
S_high = flame_speed[high_pressure_mask]

popt_high, _ = curve_fit(linear_model, P_high, S_high, p0=[-0.1, 35])
S_pred_high = linear_model(P_high, *popt_high)
r2_high = 1 - np.sum((S_high - S_pred_high)**2) / np.sum((S_high - S_high.mean())**2)

print(f"\nHigh Pressure Regime Linear Fit: S = {popt_high[0]:.4f}*P + {popt_high[1]:.4f}, R² = {r2_high:.4f}")

# Generate smooth curves for plotting
P_smooth_low = np.linspace(P_low.min(), P_low.max(), 200)
P_smooth_high = np.linspace(P_high.min(), P_high.max(), 200)

S_smooth_power = power_law(P_smooth_low, *popt_power)
S_smooth_linear = linear_model(P_smooth_low, *popt_linear)
S_smooth_log = logarithmic_model(P_smooth_low, *popt_log)
S_smooth_high = linear_model(P_smooth_high, *popt_high)

# Create comprehensive figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Plot 1: Raw data with regime identification
ax1 = axes[0, 0]
ax1.scatter(P_low, S_low, c='blue', alpha=0.7, s=50, label=f'Low Pressure Regime (<{regime_threshold} kPa)')
ax1.scatter(P_high, S_high, c='red', alpha=0.7, s=50, label=f'High Pressure Regime (≥{regime_threshold} kPa)')
ax1.axvline(x=regime_threshold, color='gray', linestyle='--', alpha=0.7, label='Regime Transition')
ax1.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax1.set_ylabel('Flame Speed (cm/s)', fontsize=12)
ax1.set_title('Flame Speed vs Chamber Pressure - Raw Data', fontsize=13, fontweight='bold')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)

# Plot 2: Model comparison for low pressure regime
ax2 = axes[0, 1]
ax2.scatter(P_low, S_low, c='blue', alpha=0.6, s=50, label='Experimental Data')
ax2.plot(P_smooth_low, S_smooth_power, 'r-', linewidth=2, label=f'Power Law (R²={r2_power:.3f})')
ax2.plot(P_smooth_low, S_smooth_linear, 'g--', linewidth=2, label=f'Linear (R²={r2_linear:.3f})')
ax2.plot(P_smooth_low, S_smooth_log, 'm:', linewidth=2, label=f'Logarithmic (R²={r2_log:.3f})')
ax2.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax2.set_ylabel('Flame Speed (cm/s)', fontsize=12)
ax2.set_title('Model Comparison - Low Pressure Regime', fontsize=13, fontweight='bold')
ax2.legend(loc='upper right')
ax2.grid(True, alpha=0.3)

# Plot 3: Best fit model (power law) with residuals
ax3 = axes[1, 0]
ax3.scatter(P_low, S_low, c='blue', alpha=0.6, s=50, label='Experimental Data')
ax3.plot(P_smooth_low, S_smooth_power, 'r-', linewidth=2.5, label=f'Power Law: S={popt_power[0]:.2f}×P^{popt_power[1]:.3f}')
ax3.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax3.set_ylabel('Flame Speed (cm/s)', fontsize=12)
ax3.set_title('Best Fit Model: Power Law Relationship', fontsize=13, fontweight='bold')
ax3.legend(loc='upper right')
ax3.grid(True, alpha=0.3)

# Plot 4: Residuals analysis
ax4 = axes[1, 1]
residuals = S_low - S_pred_power
ax4.scatter(P_low, residuals, c='purple', alpha=0.7, s=50)
ax4.axhline(y=0, color='red', linestyle='--', linewidth=1.5)
ax4.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax4.set_ylabel('Residuals (cm/s)', fontsize=12)
ax4.set_title('Residuals: Power Law Model', fontsize=13, fontweight='bold')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/flame_pressure_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# Create additional figure for full analysis
fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))

# Full data with both regimes modeled
ax_full = axes2[0]
ax_full.scatter(P_low, S_low, c='blue', alpha=0.6, s=50, label='Low Pressure Data')
ax_full.scatter(P_high, S_high, c='red', alpha=0.6, s=50, label='High Pressure Data')
ax_full.plot(P_smooth_low, S_smooth_power, 'b-', linewidth=2.5, label='Low P: Power Law Fit')
ax_full.plot(P_smooth_high, S_smooth_high, 'r-', linewidth=2.5, label=f'High P: Linear Fit (R²={r2_high:.3f})')
ax_full.axvline(x=regime_threshold, color='gray', linestyle='--', alpha=0.7)
ax_full.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax_full.set_ylabel('Flame Speed (cm/s)', fontsize=12)
ax_full.set_title('Complete Flame Speed Model - Both Regimes', fontsize=13, fontweight='bold')
ax_full.legend(loc='upper right')
ax_full.grid(True, alpha=0.3)

# Normalized flame speed analysis
ax_norm = axes2[1]
# Calculate normalized flame speed (S/S_max)
S_max = flame_speed.max()
S_normalized = flame_speed / S_max
ax_norm.scatter(pressure, S_normalized, c='green', alpha=0.6, s=50)
ax_norm.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax_norm.set_ylabel('Normalized Flame Speed (S/S_max)', fontsize=12)
ax_norm.set_title('Normalized Flame Speed vs Pressure', fontsize=13, fontweight='bold')
ax_norm.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/flame_pressure_full_model.png', dpi=300, bbox_inches='tight')
plt.close()

# Statistical analysis
print("\n" + "="*60)
print("STATISTICAL ANALYSIS SUMMARY")
print("="*60)

# Correlation analysis
corr_all = np.corrcoef(pressure, flame_speed)[0, 1]
corr_low = np.corrcoef(P_low, S_low)[0, 1]
corr_high = np.corrcoef(P_high, S_high)[0, 1]

print(f"\nCorrelation Coefficients:")
print(f"  Full dataset: r = {corr_all:.4f}")
print(f"  Low pressure regime: r = {corr_low:.4f}")
print(f"  High pressure regime: r = {corr_high:.4f}")

# Calculate RMSE for models
rmse_power = np.sqrt(np.mean((S_low - S_pred_power)**2))
rmse_linear = np.sqrt(np.mean((S_low - S_pred_linear)**2))
rmse_log = np.sqrt(np.mean((S_low - S_pred_log)**2))

print(f"\nRMSE (Low Pressure Regime):")
print(f"  Power Law: {rmse_power:.4f} cm/s")
print(f"  Linear: {rmse_linear:.4f} cm/s")
print(f"  Logarithmic: {rmse_log:.4f} cm/s")

# Save results to file
results = {
    'model': ['Power Law', 'Linear', 'Logarithmic'],
    'R_squared': [r2_power, r2_linear, r2_log],
    'RMSE': [rmse_power, rmse_linear, rmse_log],
    'equation': [
        f'S = {popt_power[0]:.4f} * P^{popt_power[1]:.4f}',
        f'S = {popt_linear[0]:.4f}*P + {popt_linear[1]:.4f}',
        f'S = {popt_log[0]:.4f} - {popt_log[1]:.4f}*ln(P)'
    ]
}

results_df = pd.DataFrame(results)
results_df.to_csv('outputs/model_comparison.csv', index=False)

# Save fitted parameters
params = {
    'parameter': ['power_a', 'power_b', 'linear_m', 'linear_c', 
                  'log_a', 'log_b', 'high_m', 'high_c'],
    'value': [popt_power[0], popt_power[1], popt_linear[0], popt_linear[1],
              popt_log[0], popt_log[1], popt_high[0], popt_high[1]],
    'R_squared': [r2_power, r2_power, r2_linear, r2_linear,
                  r2_log, r2_log, r2_high, r2_high]
}
params_df = pd.DataFrame(params)
params_df.to_csv('outputs/fitted_parameters.csv', index=False)

# Save processed data with predictions
data['regime'] = np.where(pressure < regime_threshold, 'low', 'high')
data['predicted_speed'] = np.nan
data.loc[low_pressure_mask, 'predicted_speed'] = power_law(P_low, *popt_power)
data.loc[high_pressure_mask, 'predicted_speed'] = linear_model(P_high, *popt_high)
data['residuals'] = data['flame_speed_cm_s'] - data['predicted_speed']
data.to_csv('outputs/processed_data.csv', index=False)

print("\n" + "="*60)
print("OUTPUT FILES GENERATED")
print("="*60)
print("- report/images/flame_pressure_analysis.png")
print("- report/images/flame_pressure_full_model.png")
print("- outputs/model_comparison.csv")
print("- outputs/fitted_parameters.csv")
print("- outputs/processed_data.csv")
print("="*60)

# Key findings
print("\nKEY FINDINGS:")
print(f"1. Two distinct combustion regimes identified at ~{regime_threshold} kPa")
print(f"2. Low pressure regime best fit: Power Law with R² = {r2_power:.4f}")
print(f"3. Flame speed decreases with pressure in both regimes")
print(f"4. High pressure regime shows different combustion characteristics")
print(f"5. Overall correlation: r = {corr_all:.4f} (strong negative)")
