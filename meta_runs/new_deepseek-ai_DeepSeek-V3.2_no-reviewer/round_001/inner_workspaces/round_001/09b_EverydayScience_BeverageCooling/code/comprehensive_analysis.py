import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import stats
import os

# Load the data
df = pd.read_csv('data/beverage_temperature_series.csv')

# Define phases
phase1 = df[(df['time_min'] >= 0) & (df['time_min'] <= 79)].copy()
phase2 = df[(df['time_min'] >= 80) & (df['time_min'] <= 120)].copy()
phase3 = df[(df['time_min'] >= 121) & (df['time_min'] <= 199)].copy()

print("=== BEVERAGE COOLING ANALYSIS ===")
print(f"Total data points: {len(df)}")
print(f"Phase 1 (0-79 min): {len(phase1)} points")
print(f"Phase 2 (80-120 min): {len(phase2)} points")
print(f"Phase 3 (121-199 min): {len(phase3)} points")

# Define Newton's Law of Cooling function
def newton_cooling(t, T_env, T0, k):
    """Newton's Law of Cooling: T(t) = T_env + (T0 - T_env) * exp(-k*t)"""
    return T_env + (T0 - T_env) * np.exp(-k * t)

# Define alternative: Power-law cooling (sometimes used for beverages)
def power_law_cooling(t, T_env, T0, a, b):
    """Power-law cooling: T(t) = T_env + (T0 - T_env) * (1 + a*t)**(-b)"""
    return T_env + (T0 - T_env) * (1 + a * t) ** (-b)

# Define alternative: Bi-exponential (for more complex cooling)
def biexponential_cooling(t, T_env, T0, k1, k2, alpha):
    """Bi-exponential cooling for non-uniform temperature distribution"""
    return T_env + (T0 - T_env) * (alpha * np.exp(-k1 * t) + (1 - alpha) * np.exp(-k2 * t))

# Fit Newton's Law to each phase with relaxed bounds
print("\n=== NEWTON'S LAW FITS TO EACH PHASE ===")

phases = [('Phase 1', phase1, 0), ('Phase 2', phase2, 80), ('Phase 3', phase3, 121)]
newton_results = {}

for phase_name, phase_data, time_offset in phases:
    t = phase_data['time_min'].values - time_offset
    T = phase_data['temperature_c'].values
    
    # Initial guesses and bounds
    T_env_guess = T[-1] if len(T) > 10 else 30.0
    T0_guess = T[0]
    k_guess = 0.01
    
    # Relaxed bounds
    bounds = ([10, T0_guess*0.9, 0.0001], [40, T0_guess*1.1, 0.5])
    
    try:
        popt, pcov = curve_fit(newton_cooling, t, T, p0=[T_env_guess, T0_guess, k_guess], bounds=bounds, maxfev=5000)
        perr = np.sqrt(np.diag(pcov))
        
        # Calculate fit metrics
        T_pred = newton_cooling(t, *popt)
        residuals = T - T_pred
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((T - np.mean(T))**2)
        r_squared = 1 - (ss_res / ss_tot)
        rmse = np.sqrt(np.mean(residuals**2))
        
        # Calculate half-life
        half_life = np.log(2) / popt[2] if popt[2] > 0 else np.inf
        
        newton_results[phase_name] = {
            'params': popt,
            'errors': perr,
            'r_squared': r_squared,
            'rmse': rmse,
            'half_life': half_life
        }
        
        print(f"\n{phase_name}:")
        print(f"  T_env = {popt[0]:.3f} ± {perr[0]:.3f} °C")
        print(f"  T0 = {popt[1]:.3f} ± {perr[1]:.3f} °C")
        print(f"  k = {popt[2]:.4f} ± {perr[2]:.4f} min⁻¹")
        print(f"  R² = {r_squared:.6f}")
        print(f"  RMSE = {rmse:.4f} °C")
        print(f"  Half-life = {half_life:.1f} minutes")
        
    except Exception as e:
        print(f"\n{phase_name}: Fit failed - {e}")
        newton_results[phase_name] = None

# Compare cooling constants
print("\n=== COMPARISON OF COOLING CONSTANTS ===")
for phase_name in newton_results:
    if newton_results[phase_name] is not None:
        k = newton_results[phase_name]['params'][2]
        k_err = newton_results[phase_name]['errors'][2]
        print(f"{phase_name}: k = {k:.4f} ± {k_err:.4f} min⁻¹")

# Test if data follows Newton's Law exactly for Phase 1
# For Newton's Law, ln((T - T_env)/(T0 - T_env)) = -k*t should be linear
print("\n=== TESTING LINEARITY OF LOG-TRANSFORMED DATA (Phase 1) ===")
if 'Phase 1' in newton_results and newton_results['Phase 1'] is not None:
    phase1_data = phase1.copy()
    T_env = newton_results['Phase 1']['params'][0]
    T0 = newton_results['Phase 1']['params'][1]
    
    # Transform according to Newton's Law
    phase1_data['log_transform'] = np.log((phase1_data['temperature_c'] - T_env) / (T0 - T_env))
    phase1_data['time_shifted'] = phase1_data['time_min'] - phase1_data['time_min'].min()
    
    # Fit linear model to transformed data
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        phase1_data['time_shifted'], phase1_data['log_transform']
    )
    
    print(f"Linear fit to transformed data:")
    print(f"  Slope (should be -k) = {slope:.6f} (k = {-slope:.6f})")
    print(f"  Intercept (should be 0) = {intercept:.6f}")
    print(f"  R² = {r_value**2:.6f}")
    print(f"  p-value = {p_value:.6f}")
    
    # Plot transformed data
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(phase1_data['time_shifted'], phase1_data['log_transform'], 'bo-', linewidth=1.5, markersize=4)
    plt.xlabel('Time (minutes)')
    plt.ylabel('ln((T-T_env)/(T0-T_env))')
    plt.title('Log-Transformed Phase 1 Data')
    plt.grid(True, alpha=0.3)
    
    # Add linear fit
    x_fit = np.linspace(0, phase1_data['time_shifted'].max(), 100)
    y_fit = intercept + slope * x_fit
    plt.plot(x_fit, y_fit, 'r--', linewidth=2, label=f'Linear fit: slope={slope:.4f}')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    residuals = phase1_data['log_transform'] - (intercept + slope * phase1_data['time_shifted'])
    plt.plot(phase1_data['time_shifted'], residuals, 'ro-', linewidth=1.5, markersize=4)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    plt.xlabel('Time (minutes)')
    plt.ylabel('Residuals')
    plt.title('Residuals of Linear Fit')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('outputs/log_transform_phase1.png', dpi=150)
    plt.savefig('report/images/log_transform_phase1.png', dpi=150)
    plt.close()

# Try alternative model: Power-law cooling for Phase 1
print("\n=== ALTERNATIVE MODEL: POWER-LAW COOLING (Phase 1) ===")
if len(phase1) > 10:
    t = phase1['time_min'].values - phase1['time_min'].min()
    T = phase1['temperature_c'].values
    
    # Initial guesses
    T_env_guess = T[-1]
    T0_guess = T[0]
    a_guess = 0.01
    b_guess = 1.0
    
    try:
        popt_power, pcov_power = curve_fit(power_law_cooling, t, T, 
                                          p0=[T_env_guess, T0_guess, a_guess, b_guess],
                                          bounds=([10, 70, 0.0001, 0.1], [40, 90, 1.0, 5.0]),
                                          maxfev=5000)
        
        T_pred_power = power_law_cooling(t, *popt_power)
        residuals_power = T - T_pred_power
        ss_res_power = np.sum(residuals_power**2)
        ss_tot_power = np.sum((T - np.mean(T))**2)
        r_squared_power = 1 - (ss_res_power / ss_tot_power)
        rmse_power = np.sqrt(np.mean(residuals_power**2))
        
        print(f"Power-law fit parameters:")
        print(f"  T_env = {popt_power[0]:.3f} °C")
        print(f"  T0 = {popt_power[1]:.3f} °C")
        print(f"  a = {popt_power[2]:.6f}")
        print(f"  b = {popt_power[3]:.6f}")
        print(f"  R² = {r_squared_power:.6f}")
        print(f"  RMSE = {rmse_power:.4f} °C")
        
        # Compare with Newton model
        if 'Phase 1' in newton_results and newton_results['Phase 1'] is not None:
            newton_rmse = newton_results['Phase 1']['rmse']
            print(f"\nComparison with Newton model:")
            print(f"  Newton RMSE: {newton_rmse:.4f} °C")
            print(f"  Power-law RMSE: {rmse_power:.4f} °C")
            print(f"  Difference: {abs(newton_rmse - rmse_power):.6f} °C")
            
    except Exception as e:
        print(f"Power-law fit failed: {e}")

# Create comprehensive visualization
print("\n=== CREATING COMPREHENSIVE VISUALIZATION ===")
plt.figure(figsize=(16, 10))

# Plot 1: Raw data with phases
plt.subplot(2, 2, 1)
plt.plot(df['time_min'], df['temperature_c'], 'k-', alpha=0.7, linewidth=1.5, label='Data')
plt.axvline(x=80, color='r', linestyle='--', alpha=0.5, label='Intervention 1')
plt.axvline(x=121, color='r', linestyle=':', alpha=0.5, label='Intervention 2')
plt.fill_betweenx([20, 90], 0, 79, alpha=0.1, color='blue', label='Phase 1')
plt.fill_betweenx([20, 90], 80, 120, alpha=0.1, color='green', label='Phase 2')
plt.fill_betweenx([20, 90], 121, 199, alpha=0.1, color='orange', label='Phase 3')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Cooling Data with Interventions')
plt.grid(True, alpha=0.3)
plt.legend(loc='upper right')

# Plot 2: Newton fits for each phase
plt.subplot(2, 2, 2)
plt.plot(df['time_min'], df['temperature_c'], 'k-', alpha=0.5, linewidth=1, label='Data')

colors = ['blue', 'green', 'red']
for idx, (phase_name, phase_data, time_offset) in enumerate(phases):
    if phase_name in newton_results and newton_results[phase_name] is not None:
        t_fine = np.linspace(time_offset, time_offset + (phase_data['time_min'].max() - phase_data['time_min'].min()), 100)
        t_fine_shifted = t_fine - time_offset
        T_fit = newton_cooling(t_fine_shifted, *newton_results[phase_name]['params'])
        plt.plot(t_fine, T_fit, colors[idx] + '--', linewidth=2, 
                label=f'{phase_name}: k={newton_results[phase_name]["params"][2]:.4f}')

plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title("Newton's Law Fits to Each Phase")
plt.grid(True, alpha=0.3)
plt.legend()

# Plot 3: Cooling rate (dT/dt) vs temperature
plt.subplot(2, 2, 3)
# Calculate cooling rate using finite differences
df['cooling_rate'] = -df['temperature_c'].diff() / df['time_min'].diff()  # Negative for cooling
# Remove first point (NaN) and anomalies
cooling_df = df.iloc[1:].copy()
cooling_df = cooling_df[~cooling_df['time_min'].isin([80, 121])]  # Remove intervention points

plt.scatter(cooling_df['temperature_c'], cooling_df['cooling_rate'], alpha=0.6, s=20)
plt.xlabel('Temperature (°C)')
plt.ylabel('Cooling Rate (°C/min)')
plt.title('Cooling Rate vs Temperature')
plt.grid(True, alpha=0.3)

# For Newton's Law, cooling rate = -k*(T - T_env) should be linear
# Add linear fit if we have phase 1 Newton parameters
if 'Phase 1' in newton_results and newton_results['Phase 1'] is not None:
    k = newton_results['Phase 1']['params'][2]
    T_env = newton_results['Phase 1']['params'][0]
    T_range = np.linspace(25, 85, 100)
    cooling_rate_newton = k * (T_range - T_env)
    plt.plot(T_range, cooling_rate_newton, 'r-', linewidth=2, 
             label=f"Newton: dT/dt = -{k:.4f}(T-{T_env:.1f})")
    plt.legend()

# Plot 4: Residuals if we fit single Newton model to entire dataset
plt.subplot(2, 2, 4)
# Fit single Newton model to entire dataset (for comparison)
t_full = df['time_min'].values - df['time_min'].min()
T_full = df['temperature_c'].values

try:
    popt_full, _ = curve_fit(newton_cooling, t_full, T_full, 
                            p0=[30, T_full[0], 0.01],
                            bounds=([20, 70, 0.001], [40, 90, 0.1]))
    
    T_pred_full = newton_cooling(t_full, *popt_full)
    residuals_full = T_full - T_pred_full
    
    plt.plot(df['time_min'], residuals_full, 'ko-', alpha=0.7, linewidth=1, markersize=3)
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.axvline(x=80, color='b', linestyle='--', alpha=0.3)
    plt.axvline(x=121, color='b', linestyle='--', alpha=0.3)
    plt.xlabel('Time (minutes)')
    plt.ylabel('Residuals (°C)')
    plt.title('Residuals: Single Newton Model Fit to Entire Dataset')
    plt.grid(True, alpha=0.3)
    
    # Add annotation about interventions
    plt.text(80, max(residuals_full)*0.8, 'Intervention 1', rotation=90, alpha=0.7)
    plt.text(121, max(residuals_full)*0.8, 'Intervention 2', rotation=90, alpha=0.7)
    
except Exception as e:
    plt.text(0.5, 0.5, f'Fit failed: {str(e)[:50]}...', 
             horizontalalignment='center', verticalalignment='center',
             transform=plt.gca().transAxes)
    plt.title('Residuals Plot (Fit Failed)')

plt.tight_layout()
plt.savefig('outputs/comprehensive_analysis.png', dpi=150)
plt.savefig('report/images/comprehensive_analysis.png', dpi=150)
plt.close()

print("\nAnalysis complete. Figures saved to outputs/ and report/images/")
