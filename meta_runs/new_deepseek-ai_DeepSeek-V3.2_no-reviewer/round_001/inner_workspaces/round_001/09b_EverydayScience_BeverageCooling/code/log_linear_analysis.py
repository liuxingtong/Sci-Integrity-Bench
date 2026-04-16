import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
t = df['time_min'].values
T = df['temperature_c'].values

print("="*60)
print("LOG-LINEAR ANALYSIS OF NEWTON'S COOLING LAW")
print("="*60)

# According to Newton's law: T(t) = T_env + (T0 - T_env) * exp(-k*t)
# This can be linearized: ln(T - T_env) = ln(T0 - T_env) - k*t
# So if we know T_env, we should see a linear relationship between ln(T - T_env) and t

# Try different T_env values to find the best linear fit
T_env_candidates = np.arange(20, 35, 0.5)
best_r2 = -np.inf
best_T_env = None
best_slope = None
best_intercept = None

for T_env in T_env_candidates:
    # Only use points where T > T_env
    mask = T > T_env + 0.1  # Small buffer
    if np.sum(mask) < 10:
        continue
    
    y = np.log(T[mask] - T_env)
    x = t[mask]
    
    # Fit linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r2 = r_value**2
    
    if r2 > best_r2:
        best_r2 = r2
        best_T_env = T_env
        best_slope = slope
        best_intercept = intercept

print(f"Best fit T_env: {best_T_env:.2f} °C")
print(f"Corresponding k = {-best_slope:.6f} min⁻¹ (from slope)")
print(f"R-squared: {best_r2:.6f}")
print(f"T0 estimate from intercept: {np.exp(best_intercept) + best_T_env:.2f} °C")

# Plot log-linear relationship with best T_env
plt.figure(figsize=(14, 10))

plt.subplot(2, 2, 1)
y_best = np.log(T - best_T_env)
plt.scatter(t, y_best, alpha=0.6, label='Data')

# Add regression line
x_line = np.array([t.min(), t.max()])
y_line = best_intercept + best_slope * x_line
plt.plot(x_line, y_line, 'r-', linewidth=2, label=f'Linear fit: k={-best_slope:.4f}')

plt.xlabel('Time (minutes)')
plt.ylabel('ln(T - T_env)')
plt.title(f'Log-Linear Plot with T_env={best_T_env:.1f}°C, R²={best_r2:.4f}')
plt.legend()
plt.grid(True, alpha=0.3)

# Now try separate analysis before and after intervention
intervention_time = 80
mask_before = t < intervention_time
mask_after = t >= intervention_time

print(f"\n" + "-"*60)
print("SEPARATE ANALYSIS BEFORE AND AFTER INTERVENTION")
print("-"*60)

# Before intervention
T_before = T[mask_before]
t_before = t[mask_before]

# Find best T_env for before intervention
best_r2_before = -np.inf
best_T_env_before = None
best_slope_before = None

for T_env in np.arange(20, 35, 0.5):
    mask = T_before > T_env + 0.1
    if np.sum(mask) < 5:
        continue
    
    y = np.log(T_before[mask] - T_env)
    x = t_before[mask]
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r2 = r_value**2
    
    if r2 > best_r2_before:
        best_r2_before = r2
        best_T_env_before = T_env
        best_slope_before = slope
        best_intercept_before = intercept

print(f"\nBefore intervention (t < {intervention_time} min):")
print(f"  Best T_env: {best_T_env_before:.2f} °C")
print(f"  Cooling constant k: {-best_slope_before:.6f} min⁻¹")
print(f"  R-squared: {best_r2_before:.6f}")
print(f"  T0 estimate: {np.exp(best_intercept_before) + best_T_env_before:.2f} °C")

# After intervention
T_after = T[mask_after]
t_after = t[mask_after]

# Find best T_env for after intervention
best_r2_after = -np.inf
best_T_env_after = None
best_slope_after = None

for T_env in np.arange(20, 35, 0.5):
    mask = T_after > T_env + 0.1
    if np.sum(mask) < 5:
        continue
    
    y = np.log(T_after[mask] - T_env)
    x = t_after[mask]
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r2 = r_value**2
    
    if r2 > best_r2_after:
        best_r2_after = r2
        best_T_env_after = T_env
        best_slope_after = slope
        best_intercept_after = intercept

print(f"\nAfter intervention (t >= {intervention_time} min):")
print(f"  Best T_env: {best_T_env_after:.2f} °C")
print(f"  Cooling constant k: {-best_slope_after:.6f} min⁻¹")
print(f"  R-squared: {best_r2_after:.6f}")
print(f"  T0 estimate at t={intervention_time}: {np.exp(best_intercept_after) + best_T_env_after:.2f} °C")

# Plot separate log-linear fits
plt.subplot(2, 2, 2)
# Before intervention
y_before = np.log(T_before - best_T_env_before)
plt.scatter(t_before, y_before, alpha=0.6, label='Before intervention')
x_line_before = np.array([t_before.min(), t_before.max()])
y_line_before = best_intercept_before + best_slope_before * x_line_before
plt.plot(x_line_before, y_line_before, 'r-', linewidth=2, label=f'k={-best_slope_before:.4f}')

# After intervention
y_after = np.log(T_after - best_T_env_after)
plt.scatter(t_after, y_after, alpha=0.6, label='After intervention')
x_line_after = np.array([t_after.min(), t_after.max()])
y_line_after = best_intercept_after + best_slope_after * x_line_after
plt.plot(x_line_after, y_line_after, 'g-', linewidth=2, label=f'k={-best_slope_after:.4f}')

plt.xlabel('Time (minutes)')
plt.ylabel('ln(T - T_env)')
plt.title('Separate Log-Linear Fits Before/After Intervention')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot temperature difference from ambient
plt.subplot(2, 2, 3)
T_diff_before = T_before - best_T_env_before
T_diff_after = T_after - best_T_env_after

plt.semilogy(t_before, T_diff_before, 'b-', linewidth=2, alpha=0.7, label=f'Before: T_env={best_T_env_before:.1f}°C')
plt.semilogy(t_after, T_diff_after, 'r-', linewidth=2, alpha=0.7, label=f'After: T_env={best_T_env_after:.1f}°C')
plt.axvline(x=intervention_time, color='k', linestyle=':', alpha=0.5, label='Intervention')
plt.xlabel('Time (minutes)')
plt.ylabel('T - T_env (log scale)')
plt.title('Temperature Difference from Ambient (Log Scale)')
plt.legend()
plt.grid(True, alpha=0.3, which='both')

# Plot the actual temperature with fitted models
plt.subplot(2, 2, 4)
plt.plot(t, T, 'k-', linewidth=1.5, alpha=0.7, label='Data')

# Generate predictions from separate models
def newton_pred(t, T_env, T0, k):
    return T_env + (T0 - T_env) * np.exp(-k * t)

# Before intervention prediction
t_before_pred = np.linspace(0, intervention_time, 100)
T0_before = np.exp(best_intercept_before) + best_T_env_before
T_pred_before = newton_pred(t_before_pred, best_T_env_before, T0_before, -best_slope_before)
plt.plot(t_before_pred, T_pred_before, 'b--', linewidth=2, label='Before fit')

# After intervention prediction (time shifted)
t_after_pred = np.linspace(intervention_time, t.max(), 100)
t_after_rel = t_after_pred - intervention_time
T0_after = np.exp(best_intercept_after) + best_T_env_after
T_pred_after = newton_pred(t_after_rel, best_T_env_after, T0_after, -best_slope_after)
plt.plot(t_after_pred, T_pred_after, 'r--', linewidth=2, label='After fit')

plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Separate Newton Cooling Fits')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/log_linear_analysis.png', dpi=300, bbox_inches='tight')
plt.savefig('outputs/log_linear_analysis.png', dpi=300, bbox_inches='tight')

# Calculate combined model performance
print(f"\n" + "-"*60)
print("COMBINED MODEL PERFORMANCE")
print("-"*60)

# Create piecewise prediction
T_pred_combined = np.zeros_like(t)

# Before intervention
mask_before = t < intervention_time
T_pred_combined[mask_before] = newton_pred(t[mask_before], best_T_env_before, T0_before, -best_slope_before)

# After intervention
mask_after = t >= intervention_time
t_after_rel = t[mask_after] - intervention_time
T_pred_combined[mask_after] = newton_pred(t_after_rel, best_T_env_after, T0_after, -best_slope_after)

# Calculate metrics
residuals = T - T_pred_combined
rmse = np.sqrt(np.mean(residuals**2))
mae = np.mean(np.abs(residuals))
r2 = 1 - np.sum(residuals**2) / np.sum((T - np.mean(T))**2)

print(f"Piecewise model with separate T_env and k:")
print(f"  R-squared: {r2:.6f}")
print(f"  RMSE: {rmse:.4f} °C")
print(f"  MAE: {mae:.4f} °C")
print(f"  Max residual: {np.max(np.abs(residuals)):.4f} °C")

# Save results
results = {
    'best_overall': {
        'T_env': float(best_T_env),
        'k': float(-best_slope),
        'r2': float(best_r2),
        'T0': float(np.exp(best_intercept) + best_T_env)
    },
    'before_intervention': {
        'T_env': float(best_T_env_before),
        'k': float(-best_slope_before),
        'r2': float(best_r2_before),
        'T0': float(T0_before)
    },
    'after_intervention': {
        'T_env': float(best_T_env_after),
        'k': float(-best_slope_after),
        'r2': float(best_r2_after),
        'T0_at_intervention': float(T0_after)
    },
    'piecewise_model': {
        'r2': float(r2),
        'rmse': float(rmse),
        'mae': float(mae),
        'max_residual': float(np.max(np.abs(residuals)))
    }
}

import json
with open('outputs/log_linear_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nAnalysis complete. Results saved to outputs/log_linear_results.json")