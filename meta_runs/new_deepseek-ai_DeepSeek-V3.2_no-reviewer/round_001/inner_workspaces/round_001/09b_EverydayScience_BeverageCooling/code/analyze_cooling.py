import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

# Load data
df = pd.read_csv('../data/beverage_temperature_series.csv')

# Create output directory for images
os.makedirs('../report/images', exist_ok=True)

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

print("=== Segment 1 (0-79 min) ===")
print(f"Initial temp: {segment1['temperature_c'].iloc[0]:.2f}°C")
print(f"Final temp: {segment1['temperature_c'].iloc[-1]:.2f}°C")
print(f"Duration: {segment1['time_rel'].max()} min")

print("\n=== Segment 2 (80-120 min) ===")
print(f"Initial temp: {segment2['temperature_c'].iloc[0]:.2f}°C")
print(f"Final temp: {segment2['temperature_c'].iloc[-1]:.2f}°C")
print(f"Duration: {segment2['time_rel'].max()} min")

print("\n=== Segment 3 (121-199 min) ===")
print(f"Initial temp: {segment3['temperature_c'].iloc[0]:.2f}°C")
print(f"Final temp: {segment3['temperature_c'].iloc[-1]:.2f}°C")
print(f"Duration: {segment3['time_rel'].max()} min")

# Fit Newton's Law to each segment
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

segments = [segment1, segment2, segment3]
segment_names = ['Segment 1 (0-79 min)', 'Segment 2 (80-120 min)', 'Segment 3 (121-199 min)']
colors = ['blue', 'red', 'green']

results = []

for i, (seg, name, color) in enumerate(zip(segments, segment_names, colors)):
    if len(seg) < 3:
        continue
    
    # Initial guesses: T_env around final temperature, T0 = initial temp, k small positive
    T0_guess = seg['temperature_c'].iloc[0]
    T_env_guess = seg['temperature_c'].iloc[-1]  # Approximate ambient from final temp
    k_guess = 0.01  # Rough guess
    
    try:
        # Fit the model
        popt, pcov = curve_fit(newtons_cooling, 
                               seg['time_rel'], 
                               seg['temperature_c'],
                               p0=[T_env_guess, T0_guess, k_guess],
                               bounds=([0, 0, 0], [100, 100, 1]))  # Reasonable bounds
        
        T_env_fit, T0_fit, k_fit = popt
        perr = np.sqrt(np.diag(pcov))  # Parameter errors
        
        # Calculate fitted values
        t_fit = np.linspace(0, seg['time_rel'].max(), 100)
        T_fit = newtons_cooling(t_fit, *popt)
        
        # Calculate R-squared
        residuals = seg['temperature_c'] - newtons_cooling(seg['time_rel'], *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((seg['temperature_c'] - np.mean(seg['temperature_c']))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        results.append({
            'segment': name,
            'T_env': T_env_fit,
            'T_env_err': perr[0],
            'T0': T0_fit,
            'T0_err': perr[1],
            'k': k_fit,
            'k_err': perr[2],
            'r_squared': r_squared,
            'half_life': np.log(2) / k_fit if k_fit > 0 else np.inf
        })
        
        # Plot
        ax = axes[i]
        ax.scatter(seg['time_rel'], seg['temperature_c'], alpha=0.6, label='Data', color=color)
        ax.plot(t_fit, T_fit, 'k-', linewidth=2, label=f'Newton Fit: T_env={T_env_fit:.2f}°C, k={k_fit:.4f}/min')
        ax.set_xlabel('Time (minutes)')
        ax.set_ylabel('Temperature (°C)')
        ax.set_title(f'{name}\nR² = {r_squared:.4f}')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        print(f"\n{name} Fit Results:")
        print(f"  Ambient temperature (T_env): {T_env_fit:.2f} ± {perr[0]:.2f}°C")
        print(f"  Initial temperature (T0): {T0_fit:.2f} ± {perr[1]:.2f}°C")
        print(f"  Cooling constant (k): {k_fit:.4f} ± {perr[2]:.4f} /min")
        print(f"  Half-life (ln(2)/k): {np.log(2)/k_fit:.1f} min")
        print(f"  R-squared: {r_squared:.4f}")
        
    except Exception as e:
        print(f"Error fitting {name}: {e}")
        # Just plot data if fit fails
        ax = axes[i]
        ax.scatter(seg['time_rel'], seg['temperature_c'], alpha=0.6, label='Data', color=color)
        ax.set_xlabel('Time (minutes)')
        ax.set_ylabel('Temperature (°C)')
        ax.set_title(f'{name} (Fit failed)')
        ax.grid(True, alpha=0.3)
        ax.legend()

# Plot all segments together for comparison
ax = axes[3]
for i, (seg, name, color) in enumerate(zip(segments, segment_names, colors)):
    ax.plot(seg['time_min'], seg['temperature_c'], '-', linewidth=2, color=color, label=name)
ax.set_xlabel('Time (minutes)')
ax.set_ylabel('Temperature (°C)')
ax.set_title('All Segments (Original Time Scale)')
ax.grid(True, alpha=0.3)
ax.legend()

plt.tight_layout()
plt.savefig('../report/images/newton_fits_segments.png', dpi=150)
plt.close()

# Create a summary table
if results:
    print("\n=== Summary of Fitting Results ===")
    print("Segment | T_env (°C) | k (/min) | Half-life (min) | R²")
    print("-" * 60)
    for res in results:
        print(f"{res['segment']:20} | {res['T_env']:6.2f} ± {res['T_env_err']:.2f} | {res['k']:.4f} ± {res['k_err']:.4f} | {res['half_life']:6.1f} | {res['r_squared']:.4f}")

# Save results to file
if results:
    results_df = pd.DataFrame(results)
    results_df.to_csv('../outputs/fitting_results.csv', index=False)
    print("\nResults saved to outputs/fitting_results.csv")