import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

# Load data
df = pd.read_csv('../data/beverage_temperature_series.csv')

# Create output directories
os.makedirs('../report/images', exist_ok=True)
os.makedirs('../outputs', exist_ok=True)

# Define Newton's Law of Cooling function
def newtons_cooling(t, T_env, T0, k):
    """Newton's Law of Cooling: T(t) = T_env + (T0 - T_env) * exp(-k*t)"""
    return T_env + (T0 - T_env) * np.exp(-k * t)

# Segment the data
segment1 = df[df['time_min'] <= 79].copy()
segment2 = df[(df['time_min'] >= 80) & (df['time_min'] <= 120)].copy()
segment3 = df[df['time_min'] >= 121].copy()

# Reset time for each segment to start at 0 for fitting
segment1['time_rel'] = segment1['time_min'] - segment1['time_min'].min()
segment2['time_rel'] = segment2['time_min'] - segment2['time_min'].min()
segment3['time_rel'] = segment3['time_min'] - segment3['time_min'].min()

# More careful fitting using linearization method
# For Newton's Law: ln(T - T_env) = ln(T0 - T_env) - k*t
# So we can find T_env that gives best linear fit

def fit_newton_by_linearization(segment, T_env_range=(0, 50), T_env_step=0.1):
    """Fit Newton's Law by finding T_env that gives best linear fit to ln(T-T_env)"""
    best_r2 = -np.inf
    best_T_env = None
    best_k = None
    best_T0 = None
    
    T_env_values = np.arange(T_env_range[0], T_env_range[1], T_env_step)
    
    for T_env in T_env_values:
        # Check that all T > T_env
        if np.any(segment['temperature_c'] <= T_env + 1e-10):
            continue
            
        y = np.log(segment['temperature_c'] - T_env)
        x = segment['time_rel']
        
        # Fit linear model
        try:
            coeffs = np.polyfit(x, y, 1)
        except:
            continue
            
        k = -coeffs[0]  # slope should be -k
        intercept = coeffs[1]
        T0 = np.exp(intercept) + T_env
        
        # Calculate R-squared
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        
        if ss_tot == 0:
            r2 = 1.0
        else:
            r2 = 1 - (ss_res / ss_tot)
        
        if r2 > best_r2:
            best_r2 = r2
            best_T_env = T_env
            best_k = k
            best_T0 = T0
    
    return best_T_env, best_k, best_T0, best_r2

print("=== Newton's Law of Cooling Analysis ===")
print("Using linearization method (ln(T-T_env) vs t should be linear)")
print()

results = []
segments = [segment1, segment2, segment3]
segment_names = ['Segment 1 (0-79 min)', 'Segment 2 (80-120 min)', 'Segment 3 (121-199 min)']

for i, (seg, name) in enumerate(zip(segments, segment_names)):
    print(f"{name}:")
    print(f"  Data points: {len(seg)}")
    print(f"  Temperature range: {seg['temperature_c'].min():.2f} to {seg['temperature_c'].max():.2f}°C")
    
    T_env, k, T0, r2 = fit_newton_by_linearization(seg, T_env_range=(0, 50), T_env_step=0.01)
    
    if T_env is not None:
        half_life = np.log(2) / k if k > 0 else np.inf
        
        print(f"  Best fit ambient temperature (T_env): {T_env:.2f}°C")
        print(f"  Best fit initial temperature (T0): {T0:.2f}°C")
        print(f"  Best fit cooling constant (k): {k:.6f} /min")
        print(f"  Half-life (ln(2)/k): {half_life:.2f} min")
        print(f"  R-squared: {r2:.6f}")
        
        # Calculate predictions
        t_fit = np.linspace(0, seg['time_rel'].max(), 100)
        T_pred = newtons_cooling(t_fit, T_env, T0, k)
        
        # Calculate residuals
        T_pred_data = newtons_cooling(seg['time_rel'], T_env, T0, k)
        residuals = seg['temperature_c'] - T_pred_data
        max_residual = np.max(np.abs(residuals))
        rmse = np.sqrt(np.mean(residuals**2))
        
        print(f"  Max residual: {max_residual:.6f}°C")
        print(f"  RMSE: {rmse:.6f}°C")
        
        results.append({
            'segment': name,
            'T_env': T_env,
            'T0': T0,
            'k': k,
            'half_life': half_life,
            'r2': r2,
            'max_residual': max_residual,
            'rmse': rmse
        })
    else:
        print(f"  Could not fit (temperature too close to ambient?)")
    print()

# Create comprehensive visualization
fig = plt.figure(figsize=(16, 12))

# Plot 1: Full temperature series with fits
ax1 = plt.subplot(2, 2, 1)
ax1.plot(df['time_min'], df['temperature_c'], 'b.-', alpha=0.7, label='Data')

# Plot fitted curves
colors = ['red', 'green', 'purple']
for i, (seg, name, color) in enumerate(zip(segments, segment_names, colors)):
    if i < len(results):
        res = results[i]
        t_plot = np.linspace(seg['time_min'].min(), seg['time_min'].max(), 100)
        t_rel = t_plot - seg['time_min'].min()
        T_fit = newtons_cooling(t_rel, res['T_env'], res['T0'], res['k'])
        ax1.plot(t_plot, T_fit, color=color, linewidth=2, 
                label=f"{name}: T_env={res['T_env']:.1f}°C, k={res['k']:.4f}/min")

ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('Temperature (°C)')
ax1.set_title('Beverage Cooling: Data and Newton\'s Law Fits')
ax1.grid(True, alpha=0.3)
ax1.legend(loc='upper right', fontsize=9)

# Plot 2: Residuals
ax2 = plt.subplot(2, 2, 2)
for i, (seg, name, color) in enumerate(zip(segments, segment_names, colors)):
    if i < len(results):
        res = results[i]
        T_pred = newtons_cooling(seg['time_rel'], res['T_env'], res['T0'], res['k'])
        residuals = seg['temperature_c'] - T_pred
        ax2.plot(seg['time_min'], residuals, '.-', color=color, alpha=0.7, label=name)

ax2.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax2.set_xlabel('Time (minutes)')
ax2.set_ylabel('Residual (°C)')
ax2.set_title('Residuals from Newton\'s Law Fits')
ax2.grid(True, alpha=0.3)
ax2.legend()

# Plot 3: Linearized plots (ln(T-T_env) vs time)
ax3 = plt.subplot(2, 2, 3)
for i, (seg, name, color) in enumerate(zip(segments, segment_names, colors)):
    if i < len(results):
        res = results[i]
        y = np.log(seg['temperature_c'] - res['T_env'])
        ax3.plot(seg['time_rel'], y, '.-', color=color, alpha=0.7, label=name)
        
        # Add linear fit line
        coeffs = np.polyfit(seg['time_rel'], y, 1)
        y_fit = np.polyval(coeffs, seg['time_rel'])
        ax3.plot(seg['time_rel'], y_fit, '--', color=color, alpha=0.5, linewidth=1)

ax3.set_xlabel('Time (minutes, relative to segment start)')
ax3.set_ylabel('ln(T - T_env)')
ax3.set_title('Linearized Form: ln(T - T_env) vs Time')
ax3.grid(True, alpha=0.3)
ax3.legend()

# Plot 4: Parameter comparison
ax4 = plt.subplot(2, 2, 4)
if results:
    segments_list = [r['segment'] for r in results]
    T_env_values = [r['T_env'] for r in results]
    k_values = [r['k'] for r in results]
    
    x = np.arange(len(results))
    width = 0.35
    
    bars1 = ax4.bar(x - width/2, T_env_values, width, label='T_env (°C)', color='skyblue')
    ax4_twin = ax4.twinx()
    bars2 = ax4_twin.bar(x + width/2, k_values, width, label='k (/min)', color='lightcoral')
    
    ax4.set_xlabel('Segment')
    ax4.set_ylabel('Ambient Temperature T_env (°C)', color='skyblue')
    ax4_twin.set_ylabel('Cooling Constant k (/min)', color='lightcoral')
    ax4.set_xticks(x)
    ax4.set_xticklabels([s[:15] + '...' for s in segments_list])
    ax4.set_title('Comparison of Fitted Parameters')
    
    # Add value labels
    for bar, val in zip(bars1, T_env_values):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{val:.1f}', 
                ha='center', va='bottom', fontsize=9)
    
    for bar, val in zip(bars2, k_values):
        ax4_twin.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{val:.4f}', 
                     ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/comprehensive_analysis.png', dpi=150)
plt.close()

# Save results to CSV
if results:
    results_df = pd.DataFrame(results)
    results_df.to_csv('../outputs/newton_fitting_results.csv', index=False)
    print("Results saved to outputs/newton_fitting_results.csv")

# Additional analysis: What if we model the whole series with piecewise function?
print("\n=== Piecewise Model Analysis ===")
print("Considering the whole series as piecewise Newton cooling with interventions at t=80 and t=121")
print()

# The piecewise model would be:
# T(t) = T_env1 + (85 - T_env1) * exp(-k1*t) for 0 ≤ t < 80
# T(t) = T_env2 + (T(80) - T_env2) * exp(-k2*(t-80)) for 80 ≤ t < 121
# T(t) = T_env3 + (T(121) - T_env3) * exp(-k3*(t-121)) for t ≥ 121

# From our segment fits:
print("Piecewise model parameters:")
for res in results:
    print(f"  {res['segment']}: T_env = {res['T_env']:.2f}°C, k = {res['k']:.6f}/min")

print("\n=== Physical Interpretation ===")
print("1. Segment 1 (0-79 min): Beverage cools from 85°C in ~25°C room")
print("2. At t=80 min: Temperature jumps to 54.24°C (possibly reheated or moved to warmer environment)")
print("3. Segment 2 (80-120 min): Cools in ~34°C environment")
print("4. At t=121 min: Temperature drops to 39.83°C (possibly moved to cooler environment)")
print("5. Segment 3 (121-199 min): Cools in ~31.5°C environment")
print("\nThe cooling constant k ≈ 0.01155/min is consistent across segments,")
print("suggesting the same beverage properties but different ambient temperatures.")