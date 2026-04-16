"""
Beverage Cooling Analysis
Fits Newton's Law of Cooling to temperature data with interventions.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.integrate import odeint
import json

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

print("Data loaded:")
print(f"  Time range: {time.min()} to {time.max()} minutes")
print(f"  Temperature range: {temp.min():.2f} to {temp.max():.2f} °C")
print(f"  Number of observations: {len(time)}")

# Identify segments based on interventions
# Visual inspection shows jumps at ~80 min and ~121 min
segment1_mask = time < 80
segment2_mask = (time >= 80) & (time < 121)
segment3_mask = time >= 121

print("\nSegments identified:")
print(f"  Segment 1 (0-79 min): {segment1_mask.sum()} points")
print(f"  Segment 2 (80-120 min): {segment2_mask.sum()} points")
print(f"  Segment 3 (121-199 min): {segment3_mask.sum()} points")

# Newton's Law of Cooling: T(t) = T_env + (T_0 - T_env) * exp(-k*t)
# For each segment, we fit: T(t) = T_env + A * exp(-k*(t - t_start))

def cooling_model(t, T_env, A, k, t_start):
    """Newton's Law of Cooling model"""
    return T_env + A * np.exp(-k * (t - t_start))

# Fit segment 1 (initial cooling)
t1 = time[segment1_mask]
T1 = temp[segment1_mask]
p0_1 = [20, 65, 0.01]  # Initial guess: T_env=20, A=65, k=0.01
popt1, pcov1 = curve_fit(lambda t, T_env, A, k: cooling_model(t, T_env, A, k, 0), 
                          t1, T1, p0=p0_1, maxfev=10000)
T_env1, A1, k1 = popt1
print(f"\nSegment 1 fit:")
print(f"  T_env = {T_env1:.3f} °C")
print(f"  A = {A1:.3f} °C")
print(f"  k = {k1:.5f} min^-1")
print(f"  T_0 = {T_env1 + A1:.3f} °C")

# Fit segment 2 (after first intervention)
t2 = time[segment2_mask]
T2 = temp[segment2_mask]
p0_2 = [20, 35, 0.01]
popt2, pcov2 = curve_fit(lambda t, T_env, A, k: cooling_model(t, T_env, A, k, 80), 
                          t2, T2, p0=p0_2, maxfev=10000)
T_env2, A2, k2 = popt2
print(f"\nSegment 2 fit:")
print(f"  T_env = {T_env2:.3f} °C")
print(f"  A = {A2:.3f} °C")
print(f"  k = {k2:.5f} min^-1")
print(f"  T_0 (at t=80) = {T_env2 + A2:.3f} °C")

# Fit segment 3 (after second intervention)
t3 = time[segment3_mask]
T3 = temp[segment3_mask]
p0_3 = [20, 20, 0.01]
popt3, pcov3 = curve_fit(lambda t, T_env, A, k: cooling_model(t, T_env, A, k, 121), 
                          t3, T3, p0=p0_3, maxfev=10000)
T_env3, A3, k3 = popt3
print(f"\nSegment 3 fit:")
print(f"  T_env = {T_env3:.3f} °C")
print(f"  A = {A3:.3f} °C")
print(f"  k = {k3:.5f} min^-1")
print(f"  T_0 (at t=121) = {T_env3 + A3:.3f} °C")

# Calculate fitted values for all segments
T_fit1 = cooling_model(t1, T_env1, A1, k1, 0)
T_fit2 = cooling_model(t2, T_env2, A2, k2, 80)
T_fit3 = cooling_model(t3, T_env3, A3, k3, 121)

# Calculate residuals and R-squared
residuals1 = T1 - T_fit1
residuals2 = T2 - T_fit2
residuals3 = T3 - T_fit3

ss_res1 = np.sum(residuals1**2)
ss_res2 = np.sum(residuals2**2)
ss_res3 = np.sum(residuals3**2)

ss_tot1 = np.sum((T1 - np.mean(T1))**2)
ss_tot2 = np.sum((T2 - np.mean(T2))**2)
ss_tot3 = np.sum((T3 - np.mean(T3))**2)

r2_1 = 1 - ss_res1/ss_tot1
r2_2 = 1 - ss_res2/ss_tot2
r2_3 = 1 - ss_res3/ss_tot3

print(f"\nGoodness of fit:")
print(f"  Segment 1 R² = {r2_1:.5f}")
print(f"  Segment 2 R² = {r2_2:.5f}")
print(f"  Segment 3 R² = {r2_3:.5f}")

# Calculate overall fit statistics
T_fit_all = np.concatenate([T_fit1, T_fit2, T_fit3])
residuals_all = np.concatenate([residuals1, residuals2, residuals3])
rmse = np.sqrt(np.mean(residuals_all**2))
mae = np.mean(np.abs(residuals_all))

print(f"\nOverall fit statistics:")
print(f"  RMSE = {rmse:.4f} °C")
print(f"  MAE = {mae:.4f} °C")

# Save results
results = {
    'segment1': {
        'T_env': float(T_env1),
        'A': float(A1),
        'k': float(k1),
        'T_initial': float(T_env1 + A1),
        'R_squared': float(r2_1)
    },
    'segment2': {
        'T_env': float(T_env2),
        'A': float(A2),
        'k': float(k2),
        'T_initial': float(T_env2 + A2),
        'R_squared': float(r2_2)
    },
    'segment3': {
        'T_env': float(T_env3),
        'A': float(A3),
        'k': float(k3),
        'T_initial': float(T_env3 + A3),
        'R_squared': float(r2_3)
    },
    'overall': {
        'RMSE': float(rmse),
        'MAE': float(mae)
    }
}

with open('outputs/fit_results.json', 'w') as f:
    json.dump(results, f, indent=2)

# Save fitted data
df['fitted_temp'] = np.nan
df.loc[segment1_mask, 'fitted_temp'] = T_fit1
df.loc[segment2_mask, 'fitted_temp'] = T_fit2
df.loc[segment3_mask, 'fitted_temp'] = T_fit3
df['residual'] = df['temperature_c'] - df['fitted_temp']
df.to_csv('outputs/fitted_data.csv', index=False)

print("\nResults saved to outputs/")

# Create plots
plt.figure(figsize=(12, 8))

# Plot 1: Data and fitted curves
plt.subplot(2, 2, 1)
plt.scatter(time, temp, c='blue', alpha=0.5, s=20, label='Observed data')
plt.plot(t1, T_fit1, 'r-', linewidth=2, label='Segment 1 fit')
plt.plot(t2, T_fit2, 'g-', linewidth=2, label='Segment 2 fit')
plt.plot(t3, T_fit3, 'm-', linewidth=2, label='Segment 3 fit')
plt.axvline(x=80, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=121, color='gray', linestyle='--', alpha=0.5)
plt.xlabel('Time (min)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Cooling: Data and Model Fits')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 2: Residuals
plt.subplot(2, 2, 2)
plt.scatter(t1, residuals1, c='red', alpha=0.5, s=20)
plt.scatter(t2, residuals2, c='green', alpha=0.5, s=20)
plt.scatter(t3, residuals3, c='magenta', alpha=0.5, s=20)
plt.axhline(y=0, color='black', linestyle='-', linewidth=1)
plt.axvline(x=80, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=121, color='gray', linestyle='--', alpha=0.5)
plt.xlabel('Time (min)')
plt.ylabel('Residual (°C)')
plt.title('Residuals (Observed - Fitted)')
plt.grid(True, alpha=0.3)

# Plot 3: Semi-log plot to show exponential nature
plt.subplot(2, 2, 3)
# Calculate temperature excess above environment for each segment
excess1 = T1 - T_env1
excess2 = T2 - T_env2
excess3 = T3 - T_env3
plt.semilogy(t1, excess1, 'r.', alpha=0.5, label='Segment 1')
plt.semilogy(t2, excess2, 'g.', alpha=0.5, label='Segment 2')
plt.semilogy(t3, excess3, 'm.', alpha=0.5, label='Segment 3')
# Plot fitted lines
plt.semilogy(t1, A1 * np.exp(-k1 * t1), 'r--', linewidth=2)
plt.semilogy(t2, A2 * np.exp(-k2 * (t2 - 80)), 'g--', linewidth=2)
plt.semilogy(t3, A3 * np.exp(-k3 * (t3 - 121)), 'm--', linewidth=2)
plt.axvline(x=80, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=121, color='gray', linestyle='--', alpha=0.5)
plt.xlabel('Time (min)')
plt.ylabel('Temperature excess (°C)')
plt.title('Semi-log Plot: Exponential Decay')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 4: Cooling rate analysis
plt.subplot(2, 2, 4)
# Calculate numerical derivative (cooling rate)
dt = np.diff(time)
dT = np.diff(temp)
cooling_rate = -dT / dt  # Positive cooling rate
plt.plot(time[:-1], cooling_rate, 'b-', alpha=0.7, linewidth=1)
plt.axvline(x=80, color='gray', linestyle='--', alpha=0.5)
plt.axvline(x=121, color='gray', linestyle='--', alpha=0.5)
plt.xlabel('Time (min)')
plt.ylabel('Cooling rate (°C/min)')
plt.title('Instantaneous Cooling Rate')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/cooling_analysis.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure saved to report/images/cooling_analysis.png")

# Create detailed fit comparison plot
plt.figure(figsize=(14, 5))

plt.subplot(1, 2, 1)
plt.scatter(time, temp, c='blue', alpha=0.4, s=25, label='Observed data', zorder=5)
plt.plot(t1, T_fit1, 'r-', linewidth=2.5, label=f'Segment 1: k={k1:.4f} min⁻¹', zorder=4)
plt.plot(t2, T_fit2, 'g-', linewidth=2.5, label=f'Segment 2: k={k2:.4f} min⁻¹', zorder=4)
plt.plot(t3, T_fit3, 'm-', linewidth=2.5, label=f'Segment 3: k={k3:.4f} min⁻¹', zorder=4)
plt.axvline(x=80, color='orange', linestyle='--', alpha=0.7, label='Intervention 1')
plt.axvline(x=121, color='purple', linestyle='--', alpha=0.7, label='Intervention 2')
plt.xlabel('Time (min)', fontsize=12)
plt.ylabel('Temperature (°C)', fontsize=12)
plt.title('Newton\'s Law of Cooling: Piecewise Fit', fontsize=13)
plt.legend(loc='upper right', fontsize=9)
plt.grid(True, alpha=0.3)
plt.xlim(-5, 205)

plt.subplot(1, 2, 2)
plt.scatter(time, temp, c='blue', alpha=0.4, s=25, zorder=5)
plt.plot(t1, T_fit1, 'r-', linewidth=2.5, zorder=4)
plt.plot(t2, T_fit2, 'g-', linewidth=2.5, zorder=4)
plt.plot(t3, T_fit3, 'm-', linewidth=2.5, zorder=4)
plt.axvline(x=80, color='orange', linestyle='--', alpha=0.7)
plt.axvline(x=121, color='purple', linestyle='--', alpha=0.7)
plt.xlabel('Time (min)', fontsize=12)
plt.ylabel('Temperature (°C)', fontsize=12)
plt.title('Zoom: Early Cooling Phase', fontsize=13)
plt.grid(True, alpha=0.3)
plt.xlim(-2, 100)
plt.ylim(45, 90)

plt.tight_layout()
plt.savefig('report/images/fit_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure saved to report/images/fit_comparison.png")

# Create parameter summary plot
fig, axes = plt.subplots(1, 3, figsize=(14, 4))

segments = ['Segment 1\n(0-79 min)', 'Segment 2\n(80-120 min)', 'Segment 3\n(121-199 min)']
k_values = [k1, k2, k3]
T_env_values = [T_env1, T_env2, T_env3]
R2_values = [r2_1, r2_2, r2_3]

axes[0].bar(segments, k_values, color=['red', 'green', 'magenta'], alpha=0.7, edgecolor='black')
axes[0].set_ylabel('Cooling rate k (min⁻¹)', fontsize=11)
axes[0].set_title('Cooling Rate Constant', fontsize=12)
axes[0].grid(True, alpha=0.3, axis='y')
for i, v in enumerate(k_values):
    axes[0].text(i, v + 0.0001, f'{v:.4f}', ha='center', va='bottom', fontsize=10)

axes[1].bar(segments, T_env_values, color=['red', 'green', 'magenta'], alpha=0.7, edgecolor='black')
axes[1].set_ylabel('Ambient temperature (°C)', fontsize=11)
axes[1].set_title('Fitted Ambient Temperature', fontsize=12)
axes[1].grid(True, alpha=0.3, axis='y')
for i, v in enumerate(T_env_values):
    axes[1].text(i, v + 0.5, f'{v:.1f}', ha='center', va='bottom', fontsize=10)

axes[2].bar(segments, R2_values, color=['red', 'green', 'magenta'], alpha=0.7, edgecolor='black')
axes[2].set_ylabel('R²', fontsize=11)
axes[2].set_title('Goodness of Fit', fontsize=12)
axes[2].set_ylim(0.999, 1.0001)
axes[2].grid(True, alpha=0.3, axis='y')
for i, v in enumerate(R2_values):
    axes[2].text(i, v - 0.00005, f'{v:.5f}', ha='center', va='top', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/parameter_summary.png', dpi=150, bbox_inches='tight')
plt.close()

print("Figure saved to report/images/parameter_summary.png")

print("\n=== Analysis Complete ===")
