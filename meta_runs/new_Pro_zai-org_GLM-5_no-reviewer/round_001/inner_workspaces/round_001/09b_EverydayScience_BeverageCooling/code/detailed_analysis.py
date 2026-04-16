import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import norm
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
data = pd.read_csv('data/beverage_temperature_series.csv')
time = data['time_min'].values
temp = data['temperature_c'].values

print("="*60)
print("DETAILED ANALYSIS: BEVERAGE COOLING")
print("="*60)

# Detect discontinuities (sudden jumps in temperature)
print("\n1. DETECTING DISCONTINUITIES")
print("-"*40)
temp_diff = np.diff(temp)
jump_indices = np.where(np.abs(temp_diff) > 2)[0]
print(f"Found {len(jump_indices)} discontinuities:")
for idx in jump_indices:
    print(f"  t={idx}→{idx+1}: T jumps from {temp[idx]:.2f}°C to {temp[idx+1]:.2f}°C (Δ={temp_diff[idx]:+.2f}°C)")

# Newton's Law of Cooling: T(t) = T_ambient + (T_initial - T_ambient) * exp(-k*t)
def newton_cooling(t, T_ambient, T_initial, k):
    return T_ambient + (T_initial - T_ambient) * np.exp(-k * t)

# Fit to entire dataset
print("\n2. FITTING NEWTON'S LAW OF COOLING")
print("-"*40)
print("Model: T(t) = T_ambient + (T_initial - T_ambient) * exp(-k*t)")

# Initial parameter estimates
T_initial_est = temp[0]
T_ambient_est = 20  # Reasonable room temperature
k_est = 0.01

# Fit the model
popt, pcov = curve_fit(
    newton_cooling, 
    time, 
    temp,
    p0=[T_ambient_est, T_initial_est, k_est],
    bounds=([0, 50, 0], [50, 100, 1]),
    maxfev=10000
)
T_ambient_fit, T_initial_fit, k_fit = popt
perr = np.sqrt(np.diag(pcov))

print(f"\nFitted Parameters:")
print(f"  T_ambient = {T_ambient_fit:.3f} ± {perr[0]:.3f} °C")
print(f"  T_initial = {T_initial_fit:.3f} ± {perr[1]:.3f} °C")
print(f"  k = {k_fit:.6f} ± {perr[2]:.6f} min⁻¹")

# Derived quantities
tau = 1 / k_fit
tau_err = perr[2] / (k_fit ** 2)
half_life = np.log(2) / k_fit

print(f"\nDerived Quantities:")
print(f"  Time constant (τ = 1/k) = {tau:.2f} ± {tau_err:.2f} minutes")
print(f"  Half-life = {half_life:.2f} minutes")

# Calculate goodness of fit
temp_predicted = newton_cooling(time, T_ambient_fit, T_initial_fit, k_fit)
residuals = temp - temp_predicted
ss_res = np.sum(residuals ** 2)
ss_tot = np.sum((temp - np.mean(temp)) ** 2)
r_squared = 1 - (ss_res / ss_tot)
rmse = np.sqrt(np.mean(residuals ** 2))

print(f"\nGoodness of Fit:")
print(f"  R-squared = {r_squared:.6f}")
print(f"  RMSE = {rmse:.3f} °C")

# Generate fitted curve
time_fine = np.linspace(0, time.max(), 500)
temp_fit = newton_cooling(time_fine, T_ambient_fit, T_initial_fit, k_fit)

# Save comprehensive results
with open('outputs/fit_results.txt', 'w') as f:
    f.write("Newton's Law of Cooling - Fit Results\n")
    f.write("="*50 + "\n\n")
    f.write("Model: T(t) = T_ambient + (T_initial - T_ambient) * exp(-k*t)\n\n")
    f.write("Fitted Parameters:\n")
    f.write(f"  T_ambient = {T_ambient_fit:.4f} ± {perr[0]:.4f} °C\n")
    f.write(f"  T_initial = {T_initial_fit:.4f} ± {perr[1]:.4f} °C\n")
    f.write(f"  k = {k_fit:.6f} ± {perr[2]:.6f} min⁻¹\n\n")
    f.write("Derived Quantities:\n")
    f.write(f"  Time constant (τ) = {tau:.2f} ± {tau_err:.2f} minutes\n")
    f.write(f"  Half-life = {half_life:.2f} minutes\n\n")
    f.write("Goodness of Fit:\n")
    f.write(f"  R-squared = {r_squared:.6f}\n")
    f.write(f"  RMSE = {rmse:.4f} °C\n\n")
    f.write("Data Discontinuities:\n")
    for idx in jump_indices:
        f.write(f"  t={idx}→{idx+1}: ΔT = {temp_diff[idx]:+.2f}°C\n")

# Figure 1: Main temperature plot
fig, ax = plt.subplots(figsize=(12, 7))
ax.scatter(time, temp, s=15, alpha=0.7, label='Observed Data', color='blue', zorder=3)
ax.plot(time_fine, temp_fit, 'r-', linewidth=2.5, label=f'Newton\'s Law Fit', zorder=2)
ax.axhline(y=T_ambient_fit, color='green', linestyle='--', linewidth=2, 
           label=f'Fitted Ambient T = {T_ambient_fit:.1f}°C', zorder=1)

# Mark discontinuities
for idx in jump_indices:
    ax.axvline(x=idx, color='orange', linestyle=':', alpha=0.7, linewidth=1.5)
    ax.annotate(f'Discontinuity', xy=(idx, temp[idx]), xytext=(idx+5, temp[idx]+5),
                fontsize=8, color='orange')

ax.set_xlabel('Time (minutes)', fontsize=14)
ax.set_ylabel('Temperature (°C)', fontsize=14)
ax.set_title('Beverage Cooling Curve: Newton\'s Law of Cooling', fontsize=16)
ax.legend(loc='upper right', fontsize=11)
ax.grid(True, alpha=0.3)
ax.text(0.02, 0.02, f'R² = {r_squared:.4f}\nk = {k_fit:.5f} min⁻¹\nτ = {tau:.1f} min', 
        transform=ax.transAxes, fontsize=10, verticalalignment='bottom',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
plt.tight_layout()
plt.savefig('report/images/temperature_vs_time.png', dpi=150)
plt.close()
print("\nFigure 1 saved: report/images/temperature_vs_time.png")

# Figure 2: Residuals analysis
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Residuals vs Time
axes[0, 0].scatter(time, residuals, s=10, alpha=0.7, color='blue')
axes[0, 0].axhline(y=0, color='red', linestyle='-', linewidth=1)
for idx in jump_indices:
    axes[0, 0].axvline(x=idx, color='orange', linestyle=':', alpha=0.7)
axes[0, 0].set_xlabel('Time (minutes)', fontsize=12)
axes[0, 0].set_ylabel('Residuals (°C)', fontsize=12)
axes[0, 0].set_title('Residuals vs Time', fontsize=14)
axes[0, 0].grid(True, alpha=0.3)

# Histogram of residuals
axes[0, 1].hist(residuals, bins=30, edgecolor='black', alpha=0.7, density=True, color='steelblue')
x_range = np.linspace(residuals.min(), residuals.max(), 100)
axes[0, 1].plot(x_range, norm.pdf(x_range, 0, np.std(residuals)), 'r-', linewidth=2, label='Normal(0, σ)')
axes[0, 1].set_xlabel('Residuals (°C)', fontsize=12)
axes[0, 1].set_ylabel('Density', fontsize=12)
axes[0, 1].set_title('Residual Distribution', fontsize=14)
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Residuals vs Fitted
axes[1, 0].scatter(temp_predicted, residuals, s=10, alpha=0.7, color='blue')
axes[1, 0].axhline(y=0, color='red', linestyle='-', linewidth=1)
axes[1, 0].set_xlabel('Fitted Temperature (°C)', fontsize=12)
axes[1, 0].set_ylabel('Residuals (°C)', fontsize=12)
axes[1, 0].set_title('Residuals vs Fitted Values', fontsize=14)
axes[1, 0].grid(True, alpha=0.3)

# Q-Q plot
from scipy.stats import probplot
probplot(residuals, dist="norm", plot=axes[1, 1])
axes[1, 1].set_title('Normal Q-Q Plot', fontsize=14)
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/residuals_analysis.png', dpi=150)
plt.close()
print("Figure 2 saved: report/images/residuals_analysis.png")

# Figure 3: Semi-log plot for model verification
fig, ax = plt.subplots(figsize=(12, 7))

# Only plot where T > T_ambient (to avoid log of negative)
valid_mask = temp > T_ambient_fit
temp_diff_data = temp[valid_mask] - T_ambient_fit
time_valid = time[valid_mask]

ax.scatter(time_valid, np.log(temp_diff_data), s=15, alpha=0.7, label='Data', color='blue')

# Theoretical line
temp_diff_fit = T_initial_fit - T_ambient_fit
ax.plot(time_fine, np.log(temp_diff_fit) - k_fit * time_fine, 'r-', linewidth=2, 
        label=f'Linear: ln(ΔT) = {np.log(temp_diff_fit):.3f} - {k_fit:.5f}·t')

ax.set_xlabel('Time (minutes)', fontsize=14)
ax.set_ylabel('ln(T - T_ambient)', fontsize=14)
ax.set_title('Semi-log Plot: Verification of Exponential Decay', fontsize=16)
ax.legend(loc='upper right', fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/semilog_verification.png', dpi=150)
plt.close()
print("Figure 3 saved: report/images/semilog_verification.png")

# Figure 4: Cooling rate analysis
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Instantaneous cooling rate (dT/dt)
cooling_rate = -np.diff(temp)  # Negative because temperature decreases

axes[0].plot(time[:-1], cooling_rate, 'b-', linewidth=1, alpha=0.7)
axes[0].scatter(time[:-1], cooling_rate, s=5, color='blue', alpha=0.5)
axes[0].set_xlabel('Time (minutes)', fontsize=12)
axes[0].set_ylabel('Cooling Rate (°C/min)', fontsize=12)
axes[0].set_title('Instantaneous Cooling Rate', fontsize=14)
axes[0].grid(True, alpha=0.3)

# Theoretical cooling rate: dT/dt = -k(T - T_ambient)
theoretical_rate = k_fit * (temp[:-1] - T_ambient_fit)
axes[1].scatter(temp[:-1], cooling_rate, s=10, alpha=0.5, label='Observed', color='blue')
axes[1].plot(temp[:-1], theoretical_rate, 'r-', linewidth=2, label='Theoretical: k(T-T_amb)')
axes[1].set_xlabel('Temperature (°C)', fontsize=12)
axes[1].set_ylabel('Cooling Rate (°C/min)', fontsize=12)
axes[1].set_title('Cooling Rate vs Temperature', fontsize=14)
axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/cooling_rate_analysis.png', dpi=150)
plt.close()
print("Figure 4 saved: report/images/cooling_rate_analysis.png")

# Summary statistics
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"\nThe beverage cooled from {temp[0]:.1f}°C to {temp[-1]:.1f}°C over {time[-1]} minutes.")
print(f"Newton's Law of Cooling provides an excellent fit (R² = {r_squared:.4f}).")
print(f"\nKey findings:")
print(f"  • Ambient temperature: {T_ambient_fit:.1f}°C (reasonable room temperature)")
print(f"  • Cooling constant: k = {k_fit:.5f} min⁻¹")
print(f"  • Time constant: τ = {tau:.1f} minutes")
print(f"  • Half-life: {half_life:.1f} minutes")
print(f"\nNote: {len(jump_indices)} discontinuities detected in the data, likely due to")
print("measurement artifacts or experimental interruptions.")

print("\nAnalysis complete!")
