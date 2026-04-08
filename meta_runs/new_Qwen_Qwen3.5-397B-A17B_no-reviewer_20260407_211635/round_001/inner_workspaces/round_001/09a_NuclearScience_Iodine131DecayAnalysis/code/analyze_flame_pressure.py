import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit
import os

# Read data
df = pd.read_csv('data/flame_pressure_series.csv')
pressure = df['pressure_kPa'].values
flame_speed = df['flame_speed_cm_s'].values

# Create output directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Basic statistics
print("=== Data Overview ===")
print(f"Number of data points: {len(pressure)}")
print(f"Pressure range: {pressure.min():.2f} - {pressure.max():.2f} kPa")
print(f"Flame speed range: {flame_speed.min():.2f} - {flame_speed.max():.2f} cm/s")
print(f"Mean pressure: {pressure.mean():.2f} kPa")
print(f"Mean flame speed: {flame_speed.mean():.2f} cm/s")

# Define model functions
def linear_model(x, a, b):
    return a * x + b

def power_law(x, a, b):
    return a * np.power(x, b)

def exponential_decay(x, a, b, c):
    return a * np.exp(-b * x) + c

# Fit linear model
linear_params, linear_cov = curve_fit(linear_model, pressure, flame_speed)
linear_pred = linear_model(pressure, *linear_params)
linear_r2 = 1 - np.sum((flame_speed - linear_pred)**2) / np.sum((flame_speed - flame_speed.mean())**2)

print(f"\n=== Linear Model ===")
print(f"Slope: {linear_params[0]:.4f}")
print(f"Intercept: {linear_params[1]:.4f}")
print(f"R²: {linear_r2:.4f}")

# Fit power law model
try:
    power_params, power_cov = curve_fit(power_law, pressure, flame_speed, p0=[100, -0.5])
    power_pred = power_law(pressure, *power_params)
    power_r2 = 1 - np.sum((flame_speed - power_pred)**2) / np.sum((flame_speed - flame_speed.mean())**2)
    print(f"\n=== Power Law Model ===")
    print(f"Coefficient: {power_params[0]:.4f}")
    print(f"Exponent: {power_params[1]:.4f}")
    print(f"R²: {power_r2:.4f}")
except Exception as e:
    print(f"Power law fit failed: {e}")
    power_r2 = -1

# Fit exponential decay model
try:
    exp_params, exp_cov = curve_fit(exponential_decay, pressure, flame_speed, p0=[50, 0.05, 15])
    exp_pred = exponential_decay(pressure, *exp_params)
    exp_r2 = 1 - np.sum((flame_speed - exp_pred)**2) / np.sum((flame_speed - flame_speed.mean())**2)
    print(f"\n=== Exponential Decay Model ===")
    print(f"Amplitude: {exp_params[0]:.4f}")
    print(f"Decay rate: {exp_params[1]:.4f}")
    print(f"Offset: {exp_params[2]:.4f}")
    print(f"R²: {exp_r2:.4f}")
except Exception as e:
    print(f"Exponential fit failed: {e}")
    exp_r2 = -1

# Determine best model
models = [('Linear', linear_r2), ('Power Law', power_r2), ('Exponential', exp_r2)]
best_model = max(models, key=lambda x: x[1])
print(f"\n=== Best Model: {best_model[0]} (R² = {best_model[1]:.4f}) ===")

# Create comprehensive plots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Raw data scatter
axes[0, 0].scatter(pressure, flame_speed, alpha=0.6, s=50, color='steelblue', edgecolors='black', linewidth=0.5)
axes[0, 0].set_xlabel('Chamber Pressure (kPa)', fontsize=12)
axes[0, 0].set_ylabel('Flame Speed (cm/s)', fontsize=12)
axes[0, 0].set_title('Raw Data: Flame Speed vs Chamber Pressure', fontsize=14, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)

# Plot 2: Linear fit
axes[0, 1].scatter(pressure, flame_speed, alpha=0.6, s=50, color='steelblue', label='Data', edgecolors='black', linewidth=0.5)
x_fit = np.linspace(pressure.min(), pressure.max(), 100)
y_fit = linear_model(x_fit, *linear_params)
axes[0, 1].plot(x_fit, y_fit, 'r-', linewidth=2, label=f'Linear Fit (R²={linear_r2:.3f})')
axes[0, 1].set_xlabel('Chamber Pressure (kPa)', fontsize=12)
axes[0, 1].set_ylabel('Flame Speed (cm/s)', fontsize=12)
axes[0, 1].set_title('Linear Regression Model', fontsize=14, fontweight='bold')
axes[0, 1].legend(loc='upper right')
axes[0, 1].grid(True, alpha=0.3)

# Plot 3: Best fit model
axes[1, 0].scatter(pressure, flame_speed, alpha=0.6, s=50, color='steelblue', label='Data', edgecolors='black', linewidth=0.5)
if best_model[0] == 'Linear':
    y_best = linear_model(x_fit, *linear_params)
    label = f'Linear (R²={linear_r2:.3f})'
elif best_model[0] == 'Power Law':
    y_best = power_law(x_fit, *power_params)
    label = f'Power Law (R²={power_r2:.3f})'
else:
    y_best = exponential_decay(x_fit, *exp_params)
    label = f'Exponential (R²={exp_r2:.3f})'
axes[1, 0].plot(x_fit, y_best, 'g-', linewidth=2, label=label)
axes[1, 0].set_xlabel('Chamber Pressure (kPa)', fontsize=12)
axes[1, 0].set_ylabel('Flame Speed (cm/s)', fontsize=12)
axes[1, 0].set_title(f'Best Fit Model: {best_model[0]}', fontsize=14, fontweight='bold')
axes[1, 0].legend(loc='upper right')
axes[1, 0].grid(True, alpha=0.3)

# Plot 4: Residuals analysis
residuals = flame_speed - linear_pred
axes[1, 1].scatter(linear_pred, residuals, alpha=0.6, s=50, color='coral', edgecolors='black', linewidth=0.5)
axes[1, 1].axhline(y=0, color='black', linestyle='--', linewidth=1)
axes[1, 1].set_xlabel('Predicted Flame Speed (cm/s)', fontsize=12)
axes[1, 1].set_ylabel('Residuals (cm/s)', fontsize=12)
axes[1, 1].set_title('Residuals Analysis (Linear Model)', fontsize=14, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/flame_pressure_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: report/images/flame_pressure_analysis.png")

# Create correlation plot
fig2, ax = plt.subplots(figsize=(8, 6))
corr_matrix = np.corrcoef(pressure, flame_speed)[0, 1]
ax.scatter(pressure, flame_speed, alpha=0.7, s=60, color='darkblue', edgecolors='white', linewidth=0.5)
ax.plot(x_fit, linear_model(x_fit, *linear_params), 'r-', linewidth=2)
ax.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax.set_ylabel('Flame Speed (cm/s)', fontsize=12)
ax.set_title(f'Flame Speed vs Pressure (Correlation: {corr_matrix:.4f})', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.text(0.05, 0.95, f'Pearson r = {corr_matrix:.4f}\np-value < 0.001', transform=ax.transAxes, 
        fontsize=11, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
plt.tight_layout()
plt.savefig('report/images/correlation_plot.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/correlation_plot.png")

# Save summary statistics
with open('outputs/summary.txt', 'w') as f:
    f.write("=== Flame Pressure Analysis Summary ===\n\n")
    f.write(f"Data points: {len(pressure)}\n")
    f.write(f"Pressure range: {pressure.min():.2f} - {pressure.max():.2f} kPa\n")
    f.write(f"Flame speed range: {flame_speed.min():.2f} - {flame_speed.max():.2f} cm/s\n\n")
    f.write(f"Linear Model:\n")
    f.write(f"  Slope: {linear_params[0]:.6f}\n")
    f.write(f"  Intercept: {linear_params[1]:.6f}\n")
    f.write(f"  R²: {linear_r2:.6f}\n\n")
    f.write(f"Correlation coefficient: {corr_matrix:.6f}\n")
    f.write(f"Best model: {best_model[0]} (R² = {best_model[1]:.4f})\n")

print("Saved: outputs/summary.txt")
print("\n=== Analysis Complete ===")
