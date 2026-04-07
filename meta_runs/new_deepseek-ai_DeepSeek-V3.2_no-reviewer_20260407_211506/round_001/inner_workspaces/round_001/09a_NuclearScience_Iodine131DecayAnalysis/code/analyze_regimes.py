import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
df = pd.read_csv("../data/flame_pressure_series.csv")

# Identify the transition point based on the jump
# Find where flame speed jumps significantly
speed_diff = df['flame_speed_cm_s'].diff().abs()
jump_idx = speed_diff.idxmax()  # Index of maximum change
jump_pressure = df.loc[jump_idx, 'pressure_kPa']
print(f"Transition detected at pressure: {jump_pressure:.2f} kPa")
print(f"Transition index: {jump_idx}")

# Split data into two regimes
regime1 = df[df['pressure_kPa'] < jump_pressure].copy()
regime2 = df[df['pressure_kPa'] >= jump_pressure].copy()

print(f"\nRegime 1 (low pressure): {len(regime1)} points")
print(f"Pressure range: {regime1['pressure_kPa'].min():.2f} - {regime1['pressure_kPa'].max():.2f} kPa")
print(f"Flame speed range: {regime1['flame_speed_cm_s'].min():.2f} - {regime1['flame_speed_cm_s'].max():.2f} cm/s")

print(f"\nRegime 2 (high pressure): {len(regime2)} points")
print(f"Pressure range: {regime2['pressure_kPa'].min():.2f} - {regime2['pressure_kPa'].max():.2f} kPa")
print(f"Flame speed range: {regime2['flame_speed_cm_s'].min():.2f} - {regime2['flame_speed_cm_s'].max():.2f} cm/s")

# Define model functions
def linear_model(x, a, b):
    return a * x + b

def power_law(x, a, b):
    return a * (x ** b)

def exponential_decay(x, a, b, c):
    return a * np.exp(-b * x) + c

# Fit models to each regime
print("\n" + "="*60)
print("MODEL FITTING FOR REGIME 1 (Low Pressure)")
print("="*60)

# Try linear fit for regime 1
popt_lin1, pcov_lin1 = curve_fit(linear_model, regime1['pressure_kPa'], regime1['flame_speed_cm_s'])
a_lin1, b_lin1 = popt_lin1
residuals_lin1 = regime1['flame_speed_cm_s'] - linear_model(regime1['pressure_kPa'], *popt_lin1)
rss_lin1 = np.sum(residuals_lin1**2)
r2_lin1 = 1 - rss_lin1 / np.sum((regime1['flame_speed_cm_s'] - regime1['flame_speed_cm_s'].mean())**2)
print(f"Linear model: speed = {a_lin1:.4f} * pressure + {b_lin1:.4f}")
print(f"R² = {r2_lin1:.4f}, RSS = {rss_lin1:.4f}")

# Try power law fit for regime 1
try:
    popt_pow1, pcov_pow1 = curve_fit(power_law, regime1['pressure_kPa'], regime1['flame_speed_cm_s'], p0=[100, -0.5])
    a_pow1, b_pow1 = popt_pow1
    residuals_pow1 = regime1['flame_speed_cm_s'] - power_law(regime1['pressure_kPa'], *popt_pow1)
    rss_pow1 = np.sum(residuals_pow1**2)
    r2_pow1 = 1 - rss_pow1 / np.sum((regime1['flame_speed_cm_s'] - regime1['flame_speed_cm_s'].mean())**2)
    print(f"Power law: speed = {a_pow1:.4f} * pressure^{b_pow1:.4f}")
    print(f"R² = {r2_pow1:.4f}, RSS = {rss_pow1:.4f}")
except:
    print("Power law fit failed for regime 1")

# Try exponential decay for regime 1
try:
    popt_exp1, pcov_exp1 = curve_fit(exponential_decay, regime1['pressure_kPa'], regime1['flame_speed_cm_s'], p0=[20, 0.05, 20])
    a_exp1, b_exp1, c_exp1 = popt_exp1
    residuals_exp1 = regime1['flame_speed_cm_s'] - exponential_decay(regime1['pressure_kPa'], *popt_exp1)
    rss_exp1 = np.sum(residuals_exp1**2)
    r2_exp1 = 1 - rss_exp1 / np.sum((regime1['flame_speed_cm_s'] - regime1['flame_speed_cm_s'].mean())**2)
    print(f"Exponential decay: speed = {a_exp1:.4f} * exp(-{b_exp1:.4f} * pressure) + {c_exp1:.4f}")
    print(f"R² = {r2_exp1:.4f}, RSS = {rss_exp1:.4f}")
except:
    print("Exponential decay fit failed for regime 1")

print("\n" + "="*60)
print("MODEL FITTING FOR REGIME 2 (High Pressure)")
print("="*60)

# Try linear fit for regime 2
popt_lin2, pcov_lin2 = curve_fit(linear_model, regime2['pressure_kPa'], regime2['flame_speed_cm_s'])
a_lin2, b_lin2 = popt_lin2
residuals_lin2 = regime2['flame_speed_cm_s'] - linear_model(regime2['pressure_kPa'], *popt_lin2)
rss_lin2 = np.sum(residuals_lin2**2)
r2_lin2 = 1 - rss_lin2 / np.sum((regime2['flame_speed_cm_s'] - regime2['flame_speed_cm_s'].mean())**2)
print(f"Linear model: speed = {a_lin2:.4f} * pressure + {b_lin2:.4f}")
print(f"R² = {r2_lin2:.4f}, RSS = {rss_lin2:.4f}")

# Try power law fit for regime 2
try:
    popt_pow2, pcov_pow2 = curve_fit(power_law, regime2['pressure_kPa'], regime2['flame_speed_cm_s'], p0=[30, -0.1])
    a_pow2, b_pow2 = popt_pow2
    residuals_pow2 = regime2['flame_speed_cm_s'] - power_law(regime2['pressure_kPa'], *popt_pow2)
    rss_pow2 = np.sum(residuals_pow2**2)
    r2_pow2 = 1 - rss_pow2 / np.sum((regime2['flame_speed_cm_s'] - regime2['flame_speed_cm_s'].mean())**2)
    print(f"Power law: speed = {a_pow2:.4f} * pressure^{b_pow2:.4f}")
    print(f"R² = {r2_pow2:.4f}, RSS = {rss_pow2:.4f}")
except:
    print("Power law fit failed for regime 2")

# Create visualization
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Raw data with regime separation
ax = axes[0, 0]
ax.scatter(regime1['pressure_kPa'], regime1['flame_speed_cm_s'], alpha=0.7, label='Regime 1 (Low Pressure)', edgecolors='k', linewidth=0.5)
ax.scatter(regime2['pressure_kPa'], regime2['flame_speed_cm_s'], alpha=0.7, label='Regime 2 (High Pressure)', edgecolors='k', linewidth=0.5)
ax.axvline(x=jump_pressure, color='r', linestyle='--', alpha=0.7, label=f'Transition at {jump_pressure:.1f} kPa')
ax.set_xlabel('Pressure (kPa)')
ax.set_ylabel('Flame Speed (cm/s)')
ax.set_title('Flame Speed vs. Pressure with Regime Separation')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 2: Best fit for regime 1
ax = axes[0, 1]
ax.scatter(regime1['pressure_kPa'], regime1['flame_speed_cm_s'], alpha=0.7, label='Data', edgecolors='k', linewidth=0.5)

# Generate smooth curve for best model (exponential decay for regime 1 based on visual)
x_smooth1 = np.linspace(regime1['pressure_kPa'].min(), regime1['pressure_kPa'].max(), 100)
y_exp1 = exponential_decay(x_smooth1, *popt_exp1)
ax.plot(x_smooth1, y_exp1, 'r-', linewidth=2, label=f'Exponential decay fit (R²={r2_exp1:.3f})')

ax.set_xlabel('Pressure (kPa)')
ax.set_ylabel('Flame Speed (cm/s)')
ax.set_title('Regime 1: Low Pressure Region with Exponential Decay Fit')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 3: Best fit for regime 2
ax = axes[1, 0]
ax.scatter(regime2['pressure_kPa'], regime2['flame_speed_cm_s'], alpha=0.7, label='Data', edgecolors='k', linewidth=0.5)

# Generate smooth curve for best model (linear for regime 2)
x_smooth2 = np.linspace(regime2['pressure_kPa'].min(), regime2['pressure_kPa'].max(), 100)
y_lin2 = linear_model(x_smooth2, *popt_lin2)
ax.plot(x_smooth2, y_lin2, 'g-', linewidth=2, label=f'Linear fit (R²={r2_lin2:.3f})')

ax.set_xlabel('Pressure (kPa)')
ax.set_ylabel('Flame Speed (cm/s)')
ax.set_title('Regime 2: High Pressure Region with Linear Fit')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 4: Residuals for both regimes
ax = axes[1, 1]
residuals_exp1 = regime1['flame_speed_cm_s'] - exponential_decay(regime1['pressure_kPa'], *popt_exp1)
residuals_lin2 = regime2['flame_speed_cm_s'] - linear_model(regime2['pressure_kPa'], *popt_lin2)

ax.scatter(regime1['pressure_kPa'], residuals_exp1, alpha=0.7, label='Regime 1 residuals', edgecolors='k', linewidth=0.5)
ax.scatter(regime2['pressure_kPa'], residuals_lin2, alpha=0.7, label='Regime 2 residuals', edgecolors='k', linewidth=0.5)
ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
ax.set_xlabel('Pressure (kPa)')
ax.set_ylabel('Residuals (cm/s)')
ax.set_title('Residuals of Fitted Models')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/regime_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a combined model plot
plt.figure(figsize=(10, 6))
plt.scatter(df['pressure_kPa'], df['flame_speed_cm_s'], alpha=0.7, label='Experimental Data', edgecolors='k', linewidth=0.5)

# Plot regime 1 fit
x_smooth1_full = np.linspace(regime1['pressure_kPa'].min(), regime1['pressure_kPa'].max(), 100)
y_exp1_full = exponential_decay(x_smooth1_full, *popt_exp1)
plt.plot(x_smooth1_full, y_exp1_full, 'r-', linewidth=2, label='Regime 1: Exponential Decay')

# Plot regime 2 fit
x_smooth2_full = np.linspace(regime2['pressure_kPa'].min(), regime2['pressure_kPa'].max(), 100)
y_lin2_full = linear_model(x_smooth2_full, *popt_lin2)
plt.plot(x_smooth2_full, y_lin2_full, 'g-', linewidth=2, label='Regime 2: Linear')

plt.axvline(x=jump_pressure, color='purple', linestyle='--', alpha=0.7, label=f'Transition at {jump_pressure:.1f} kPa')
plt.xlabel('Pressure (kPa)')
plt.ylabel('Flame Speed (cm/s)')
plt.title('Flame Speed vs. Pressure: Two-Regime Model')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/combined_model.png', dpi=300, bbox_inches='tight')
plt.close()

# Save model parameters
model_params = {
    'transition_pressure_kPa': jump_pressure,
    'regime1': {
        'model': 'exponential_decay',
        'params': {'a': a_exp1, 'b': b_exp1, 'c': c_exp1},
        'r2': r2_exp1,
        'rss': rss_exp1,
        'n_points': len(regime1)
    },
    'regime2': {
        'model': 'linear',
        'params': {'a': a_lin2, 'b': b_lin2},
        'r2': r2_lin2,
        'rss': rss_lin2,
        'n_points': len(regime2)
    }
}

import json
with open('../outputs/model_parameters.json', 'w') as f:
    json.dump(model_params, f, indent=2)

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print(f"Figures saved to report/images/")
print(f"Model parameters saved to outputs/model_parameters.json")
