import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import optimize
import os

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')

print("="*60)
print("ALTERNATIVE MODELING APPROACHES")
print("="*60)

# Approach 1: Single Newton cooling model for entire dataset (ignoring intervention)
print("\n1. SINGLE NEWTON COOLING MODEL (ignoring intervention)")

def newton_cooling(t, T_env, T0, k):
    return T_env + (T0 - T_env) * np.exp(-k * t)

t = df['time_min'].values
T = df['temperature_c'].values

# Initial guesses
T_env_guess = np.min(T)
T0_guess = T[0]
k_guess = 0.01

try:
    params, params_covariance = optimize.curve_fit(newton_cooling, t, T, 
                                                  p0=[T_env_guess, T0_guess, k_guess],
                                                  maxfev=5000)
    T_env_fit, T0_fit, k_fit = params
    
    # Calculate predictions and metrics
    T_pred = newton_cooling(t, *params)
    residuals = T - T_pred
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((T - np.mean(T))**2)
    r_squared = 1 - (ss_res / ss_tot)
    rmse = np.sqrt(np.mean(residuals**2))
    mae = np.mean(np.abs(residuals))
    
    print(f"Fitted parameters:")
    print(f"  Ambient temperature (T_env): {T_env_fit:.4f} °C")
    print(f"  Initial temperature (T0): {T0_fit:.4f} °C")
    print(f"  Cooling constant (k): {k_fit:.6f} min⁻¹")
    print(f"  Half-life: {np.log(2)/k_fit:.2f} min")
    print(f"\nModel performance:")
    print(f"  R-squared: {r_squared:.6f}")
    print(f"  RMSE: {rmse:.4f} °C")
    print(f"  MAE: {mae:.4f} °C")
    print(f"  Max residual: {np.max(np.abs(residuals)):.4f} °C")
    
    # Plot
    plt.figure(figsize=(14, 10))
    
    plt.subplot(2, 2, 1)
    plt.plot(t, T, 'b-', linewidth=2, label='Data', alpha=0.7)
    plt.plot(t, T_pred, 'r--', linewidth=2, label='Single Newton Model')
    plt.xlabel('Time (minutes)')
    plt.ylabel('Temperature (°C)')
    plt.title(f'Single Newton Model: T_env={T_env_fit:.1f}°C, k={k_fit:.4f}, R²={r_squared:.4f}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 2)
    plt.scatter(t, residuals, alpha=0.6)
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.xlabel('Time (minutes)')
    plt.ylabel('Residuals (°C)')
    plt.title('Residuals of Single Newton Model')
    plt.grid(True, alpha=0.3)
    
    # Highlight the intervention point
    plt.axvline(x=80, color='g', linestyle=':', alpha=0.7, label='Intervention')
    plt.legend()
    
except Exception as e:
    print(f"Fitting failed: {e}")

# Approach 2: Newton cooling with intervention as parameter
print("\n" + "-"*60)
print("2. NEWTON COOLING WITH INTERVENTION MODEL")
print("-"*60)

# Model: T(t) = T_env + (T0 - T_env) * exp(-k*t) for t < t_intervention
# Then at t_intervention, temperature jumps by delta_T
# Then continues cooling: T(t) = T_env + (T0_intervention - T_env) * exp(-k*(t-t_intervention))
# where T0_intervention = T(t_intervention) + delta_T

def newton_with_intervention(t, T_env, T0, k, t_intervention, delta_T):
    """Newton cooling with a temperature jump at intervention time"""
    result = np.zeros_like(t)
    
    # Before intervention
    mask_before = t < t_intervention
    result[mask_before] = T_env + (T0 - T_env) * np.exp(-k * t[mask_before])
    
    # At intervention (use the value just before intervention)
    T_at_intervention = T_env + (T0 - T_env) * np.exp(-k * t_intervention)
    T0_after = T_at_intervention + delta_T
    
    # After intervention
    mask_after = t >= t_intervention
    t_after = t[mask_after] - t_intervention
    result[mask_after] = T_env + (T0_after - T_env) * np.exp(-k * t_after)
    
    return result

# Initial guesses
T_env_guess = 25.0
T0_guess = 85.0
k_guess = 0.0115
t_intervention_guess = 80.0
delta_T_guess = 5.0  # Positive jump

# Set bounds
bounds = ([20, 80, 0.001, 70, 0], [30, 90, 0.05, 90, 10])

try:
    params, params_covariance = optimize.curve_fit(newton_with_intervention, t, T, 
                                                  p0=[T_env_guess, T0_guess, k_guess, t_intervention_guess, delta_T_guess],
                                                  bounds=bounds,
                                                  maxfev=10000)
    T_env_fit2, T0_fit2, k_fit2, t_intervention_fit2, delta_T_fit2 = params
    
    # Calculate predictions and metrics
    T_pred2 = newton_with_intervention(t, *params)
    residuals2 = T - T_pred2
    ss_res2 = np.sum(residuals2**2)
    ss_tot2 = np.sum((T - np.mean(T))**2)
    r_squared2 = 1 - (ss_res2 / ss_tot2)
    rmse2 = np.sqrt(np.mean(residuals2**2))
    mae2 = np.mean(np.abs(residuals2))
    
    print(f"Fitted parameters:")
    print(f"  Ambient temperature (T_env): {T_env_fit2:.4f} °C")
    print(f"  Initial temperature (T0): {T0_fit2:.4f} °C")
    print(f"  Cooling constant (k): {k_fit2:.6f} min⁻¹")
    print(f"  Intervention time: {t_intervention_fit2:.2f} min")
    print(f"  Temperature jump: {delta_T_fit2:.4f} °C")
    print(f"  Half-life: {np.log(2)/k_fit2:.2f} min")
    print(f"\nModel performance:")
    print(f"  R-squared: {r_squared2:.6f}")
    print(f"  RMSE: {rmse2:.4f} °C")
    print(f"  MAE: {mae2:.4f} °C")
    print(f"  Max residual: {np.max(np.abs(residuals2)):.4f} °C")
    
    # Plot
    plt.subplot(2, 2, 3)
    plt.plot(t, T, 'b-', linewidth=2, label='Data', alpha=0.7)
    plt.plot(t, T_pred2, 'g--', linewidth=2, label='Newton with Intervention')
    plt.axvline(x=t_intervention_fit2, color='orange', linestyle=':', alpha=0.7, label=f'Intervention at {t_intervention_fit2:.1f} min')
    plt.xlabel('Time (minutes)')
    plt.ylabel('Temperature (°C)')
    plt.title(f'Newton with Intervention: R²={r_squared2:.4f}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 4)
    plt.scatter(t, residuals2, alpha=0.6)
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.xlabel('Time (minutes)')
    plt.ylabel('Residuals (°C)')
    plt.title('Residuals of Newton with Intervention Model')
    plt.grid(True, alpha=0.3)
    
except Exception as e:
    print(f"Fitting failed: {e}")
    import traceback
    traceback.print_exc()

plt.tight_layout()
plt.savefig('report/images/alternative_models.png', dpi=300, bbox_inches='tight')
plt.savefig('outputs/alternative_models.png', dpi=300, bbox_inches='tight')

# Approach 3: Compare cooling constants
print("\n" + "-"*60)
print("3. COOLING CONSTANT ANALYSIS")
print("-"*60)

# Calculate instantaneous cooling rate
cooling_rate = -np.gradient(T, t)

# According to Newton's law: dT/dt = -k(T - T_env)
# So k = -dT/dt / (T - T_env)
# We need to estimate T_env

# Estimate T_env from later measurements (where cooling is slow)
T_env_est = np.mean(T[-20:])  # Average of last 20 measurements
print(f"Estimated ambient temperature from tail: {T_env_est:.2f} °C")

# Calculate instantaneous k values
k_instant = cooling_rate / (T - T_env_est)
k_instant = np.where(k_instant > 0, k_instant, np.nan)  # Remove negative values

# Plot k over time
plt.figure(figsize=(12, 8))
plt.subplot(2, 1, 1)
plt.plot(t, T, 'b-', linewidth=2)
plt.axhline(y=T_env_est, color='r', linestyle='--', alpha=0.7, label=f'Estimated T_env = {T_env_est:.1f}°C')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Temperature with Estimated Ambient Temperature')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(2, 1, 2)
plt.plot(t, k_instant, 'g-', linewidth=2, alpha=0.7, label='Instantaneous k')
plt.axhline(y=k_fit, color='r', linestyle='--', alpha=0.7, label=f'Single model k = {k_fit:.5f}')
if 'k_fit2' in locals():
    plt.axhline(y=k_fit2, color='orange', linestyle='--', alpha=0.7, label=f'Intervention model k = {k_fit2:.5f}')
plt.xlabel('Time (minutes)')
plt.ylabel('Cooling constant k (min⁻¹)')
plt.title('Instantaneous Cooling Constant k')
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(0, 0.03)

plt.tight_layout()
plt.savefig('report/images/cooling_constant_analysis.png', dpi=300, bbox_inches='tight')
plt.savefig('outputs/cooling_constant_analysis.png', dpi=300, bbox_inches='tight')

# Calculate average k before and after intervention
intervention_idx = np.argmax(t >= 80)  # Index near intervention
k_before = np.nanmean(k_instant[:intervention_idx])
k_after = np.nanmean(k_instant[intervention_idx:])
print(f"\nAverage cooling constant before intervention: {k_before:.6f} min⁻¹")
print(f"Average cooling constant after intervention: {k_after:.6f} min⁻¹")
print(f"Ratio (after/before): {k_after/k_before:.3f}")

print("\nAnalysis complete!")