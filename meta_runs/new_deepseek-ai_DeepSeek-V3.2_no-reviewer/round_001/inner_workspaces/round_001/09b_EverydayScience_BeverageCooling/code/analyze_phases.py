import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

# Load the data
df = pd.read_csv('data/beverage_temperature_series.csv')

# Identify phase boundaries based on anomalies
# Phase 1: 0-79 minutes (before first intervention)
# Phase 2: 80-120 minutes (between interventions)
# Phase 3: 121-199 minutes (after second intervention)
phase1 = df[(df['time_min'] >= 0) & (df['time_min'] <= 79)].copy()
phase2 = df[(df['time_min'] >= 80) & (df['time_min'] <= 120)].copy()
phase3 = df[(df['time_min'] >= 121) & (df['time_min'] <= 199)].copy()

print(f"Phase 1: {len(phase1)} points, time range: {phase1['time_min'].min()}-{phase1['time_min'].max()} min")
print(f"Phase 2: {len(phase2)} points, time range: {phase2['time_min'].min()}-{phase2['time_min'].max()} min")
print(f"Phase 3: {len(phase3)} points, time range: {phase3['time_min'].min()}-{phase3['time_min'].max()} min")

# Plot with phases colored differently
plt.figure(figsize=(14, 7))
plt.plot(phase1['time_min'], phase1['temperature_c'], 'b-', linewidth=2, label='Phase 1 (0-79 min)')
plt.plot(phase2['time_min'], phase2['temperature_c'], 'g-', linewidth=2, label='Phase 2 (80-120 min)')
plt.plot(phase3['time_min'], phase3['temperature_c'], 'r-', linewidth=2, label='Phase 3 (121-199 min)')

# Mark intervention points
plt.axvline(x=80, color='k', linestyle='--', alpha=0.5, label='Intervention 1')
plt.axvline(x=121, color='k', linestyle=':', alpha=0.5, label='Intervention 2')

plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Cooling with Interventions (Three Phases)')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('outputs/phases_plot.png', dpi=150)
plt.savefig('report/images/phases_plot.png', dpi=150)
plt.close()

# Define Newton's Law of Cooling function
def newton_cooling(t, T_env, T0, k):
    """Newton's Law of Cooling: T(t) = T_env + (T0 - T_env) * exp(-k*t)"""
    return T_env + (T0 - T_env) * np.exp(-k * t)

# Fit Newton's Law to each phase separately
print("\n--- Fitting Newton's Law to Each Phase ---")

# For phase 1: shift time to start at 0 for fitting
phase1_time = phase1['time_min'].values - phase1['time_min'].min()
phase1_temp = phase1['temperature_c'].values

# Initial guesses: T_env ~ 31°C (from end of data), T0 ~ first temp, k ~ 0.01
p0_phase1 = [31.0, phase1_temp[0], 0.01]

# Set bounds: T_env between 20-40, T0 between 80-90, k between 0.001-0.1
bounds = ([20, 70, 0.001], [40, 90, 0.1])

try:
    popt1, pcov1 = curve_fit(newton_cooling, phase1_time, phase1_temp, p0=p0_phase1, bounds=bounds)
    perr1 = np.sqrt(np.diag(pcov1))
    print(f"\nPhase 1 Fit Parameters:")
    print(f"  T_env = {popt1[0]:.3f} ± {perr1[0]:.3f} °C")
    print(f"  T0 = {popt1[1]:.3f} ± {perr1[1]:.3f} °C")
    print(f"  k = {popt1[2]:.4f} ± {perr1[2]:.4f} min⁻¹")
    
    # Calculate R-squared
    residuals1 = phase1_temp - newton_cooling(phase1_time, *popt1)
    ss_res1 = np.sum(residuals1**2)
    ss_tot1 = np.sum((phase1_temp - np.mean(phase1_temp))**2)
    r_squared1 = 1 - (ss_res1 / ss_tot1)
    print(f"  R² = {r_squared1:.6f}")
    
    # Calculate cooling half-life
    half_life1 = np.log(2) / popt1[2]
    print(f"  Half-life (time to cool halfway to T_env) = {half_life1:.1f} minutes")
    
except Exception as e:
    print(f"Error fitting phase 1: {e}")
    popt1 = None

# For phase 2
phase2_time = phase2['time_min'].values - phase2['time_min'].min()
phase2_temp = phase2['temperature_c'].values
p0_phase2 = [31.0, phase2_temp[0], 0.01]

try:
    popt2, pcov2 = curve_fit(newton_cooling, phase2_time, phase2_temp, p0=p0_phase2, bounds=bounds)
    perr2 = np.sqrt(np.diag(pcov2))
    print(f"\nPhase 2 Fit Parameters:")
    print(f"  T_env = {popt2[0]:.3f} ± {perr2[0]:.3f} °C")
    print(f"  T0 = {popt2[1]:.3f} ± {perr2[1]:.3f} °C")
    print(f"  k = {popt2[2]:.4f} ± {perr2[2]:.4f} min⁻¹")
    
    residuals2 = phase2_temp - newton_cooling(phase2_time, *popt2)
    ss_res2 = np.sum(residuals2**2)
    ss_tot2 = np.sum((phase2_temp - np.mean(phase2_temp))**2)
    r_squared2 = 1 - (ss_res2 / ss_tot2)
    print(f"  R² = {r_squared2:.6f}")
    
    half_life2 = np.log(2) / popt2[2]
    print(f"  Half-life = {half_life2:.1f} minutes")
    
except Exception as e:
    print(f"Error fitting phase 2: {e}")
    popt2 = None

# For phase 3
phase3_time = phase3['time_min'].values - phase3['time_min'].min()
phase3_temp = phase3['temperature_c'].values
p0_phase3 = [31.0, phase3_temp[0], 0.01]

try:
    popt3, pcov3 = curve_fit(newton_cooling, phase3_time, phase3_temp, p0=p0_phase3, bounds=bounds)
    perr3 = np.sqrt(np.diag(pcov3))
    print(f"\nPhase 3 Fit Parameters:")
    print(f"  T_env = {popt3[0]:.3f} ± {perr3[0]:.3f} °C")
    print(f"  T0 = {popt3[1]:.3f} ± {perr3[1]:.3f} °C")
    print(f"  k = {popt3[2]:.4f} ± {perr3[2]:.4f} min⁻¹")
    
    residuals3 = phase3_temp - newton_cooling(phase3_time, *popt3)
    ss_res3 = np.sum(residuals3**2)
    ss_tot3 = np.sum((phase3_temp - np.mean(phase3_temp))**2)
    r_squared3 = 1 - (ss_res3 / ss_tot3)
    print(f"  R² = {r_squared3:.6f}")
    
    half_life3 = np.log(2) / popt3[2]
    print(f"  Half-life = {half_life3:.1f} minutes")
    
except Exception as e:
    print(f"Error fitting phase 3: {e}")
    popt3 = None

# Plot fits for each phase
plt.figure(figsize=(14, 8))

# Plot data
plt.plot(df['time_min'], df['temperature_c'], 'k-', alpha=0.5, linewidth=1, label='Data')

# Plot phase fits if available
time_fine = np.linspace(0, 79, 100)
if popt1 is not None:
    fit1 = newton_cooling(time_fine, *popt1)
    plt.plot(time_fine, fit1, 'b--', linewidth=2, label=f'Phase 1 Fit: k={popt1[2]:.4f} min⁻¹')
    
time_fine2 = np.linspace(80, 120, 100)
if popt2 is not None:
    fit2 = newton_cooling(time_fine2 - 80, *popt2)
    plt.plot(time_fine2, fit2, 'g--', linewidth=2, label=f'Phase 2 Fit: k={popt2[2]:.4f} min⁻¹')
    
time_fine3 = np.linspace(121, 199, 100)
if popt3 is not None:
    fit3 = newton_cooling(time_fine3 - 121, *popt3)
    plt.plot(time_fine3, fit3, 'r--', linewidth=2, label=f'Phase 3 Fit: k={popt3[2]:.4f} min⁻¹')

plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title("Newton's Law of Cooling Fits to Each Phase")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('outputs/newton_fits_phases.png', dpi=150)
plt.savefig('report/images/newton_fits_phases.png', dpi=150)
plt.close()

# Also try fitting a single Newton model to the entire dataset (ignoring interventions)
print("\n--- Attempting Single Newton Model Fit to Entire Dataset ---")
full_time = df['time_min'].values - df['time_min'].min()
full_temp = df['temperature_c'].values
p0_full = [31.0, full_temp[0], 0.01]

try:
    popt_full, pcov_full = curve_fit(newton_cooling, full_time, full_temp, p0=p0_full, bounds=bounds)
    perr_full = np.sqrt(np.diag(pcov_full))
    print(f"\nFull Dataset Fit Parameters:")
    print(f"  T_env = {popt_full[0]:.3f} ± {perr_full[0]:.3f} °C")
    print(f"  T0 = {popt_full[1]:.3f} ± {perr_full[1]:.3f} °C")
    print(f"  k = {popt_full[2]:.4f} ± {perr_full[2]:.4f} min⁻¹")
    
    residuals_full = full_temp - newton_cooling(full_time, *popt_full)
    ss_res_full = np.sum(residuals_full**2)
    ss_tot_full = np.sum((full_temp - np.mean(full_temp))**2)
    r_squared_full = 1 - (ss_res_full / ss_tot_full)
    print(f"  R² = {r_squared_full:.6f}")
    
    half_life_full = np.log(2) / popt_full[2]
    print(f"  Half-life = {half_life_full:.1f} minutes")
    
    # Plot single fit
    plt.figure(figsize=(14, 7))
    plt.plot(df['time_min'], df['temperature_c'], 'k-', alpha=0.7, linewidth=1.5, label='Data')
    
    time_fine_full = np.linspace(0, 199, 200)
    fit_full = newton_cooling(time_fine_full, *popt_full)
    plt.plot(time_fine_full, fit_full, 'r--', linewidth=2, label=f'Single Newton Fit: k={popt_full[2]:.4f} min⁻¹')
    
    plt.xlabel('Time (minutes)')
    plt.ylabel('Temperature (°C)')
    plt.title("Single Newton's Law Fit to Entire Dataset (With Interventions)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('outputs/single_newton_fit.png', dpi=150)
    plt.savefig('report/images/single_newton_fit.png', dpi=150)
    plt.close()
    
except Exception as e:
    print(f"Error fitting full dataset: {e}")

print("\nAnalysis complete.")
