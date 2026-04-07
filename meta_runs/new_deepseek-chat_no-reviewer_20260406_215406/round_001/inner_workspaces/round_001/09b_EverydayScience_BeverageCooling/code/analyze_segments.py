import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

# Load the data
data_path = '../data/beverage_temperature_series.csv'
df = pd.read_csv(data_path)

# Identify segments based on anomalies
# Looking at the data, there are jumps at t=80 and t=121
segments = [
    {'start': 0, 'end': 79, 'name': 'Segment 1 (0-79 min)'},
    {'start': 80, 'end': 120, 'name': 'Segment 2 (80-120 min)'},
    {'start': 121, 'end': 199, 'name': 'Segment 3 (121-199 min)'}
]

# Newton's Law of Cooling model
def newton_cooling(t, T_env, T0, k):
    """Newton's Law of Cooling: T(t) = T_env + (T0 - T_env) * exp(-k*t)"""
    return T_env + (T0 - T_env) * np.exp(-k * t)

# Create a figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
ax = axes.flatten()

# Plot 1: Raw data with segments highlighted
ax[0].plot(df['time_min'], df['temperature_c'], 'b-', linewidth=1.5, label='Raw data')
colors = ['red', 'green', 'purple']
for i, seg in enumerate(segments):
    seg_data = df[(df['time_min'] >= seg['start']) & (df['time_min'] <= seg['end'])]
    ax[0].plot(seg_data['time_min'], seg_data['temperature_c'], 
               color=colors[i], linewidth=2.5, label=seg['name'])

ax[0].set_xlabel('Time (minutes)')
ax[0].set_ylabel('Temperature (°C)')
ax[0].set_title('Beverage Cooling with Segments Highlighted')
ax[0].grid(True, alpha=0.3)
ax[0].legend()

# Analyze each segment
results = []

for i, seg in enumerate(segments):
    seg_data = df[(df['time_min'] >= seg['start']) & (df['time_min'] <= seg['end'])].copy()
    
    # Reset time to 0 for each segment for fitting
    seg_data['time_rel'] = seg_data['time_min'] - seg['start']
    
    # Initial guesses
    T_env_guess = seg_data['temperature_c'].iloc[-1]  # Last temperature as ambient guess
    T0_guess = seg_data['temperature_c'].iloc[0]  # First temperature
    k_guess = 0.01  # Rough guess
    
    try:
        # Fit Newton's Law of Cooling
        popt, pcov = curve_fit(newton_cooling, 
                               seg_data['time_rel'], 
                               seg_data['temperature_c'],
                               p0=[T_env_guess, T0_guess, k_guess],
                               bounds=([20, T0_guess*0.9, 0], 
                                       [40, T0_guess*1.1, 1]))
        
        T_env_fit, T0_fit, k_fit = popt
        perr = np.sqrt(np.diag(pcov))
        
        # Calculate predictions
        t_fit = np.linspace(0, seg['end'] - seg['start'], 100)
        T_fit = newton_cooling(t_fit, T_env_fit, T0_fit, k_fit)
        
        # Calculate R-squared
        residuals = seg_data['temperature_c'] - newton_cooling(seg_data['time_rel'], T_env_fit, T0_fit, k_fit)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((seg_data['temperature_c'] - np.mean(seg_data['temperature_c']))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        # Store results
        results.append({
            'segment': seg['name'],
            'T_env': T_env_fit,
            'T_env_err': perr[0],
            'T0': T0_fit,
            'T0_err': perr[1],
            'k': k_fit,
            'k_err': perr[2],
            'r_squared': r_squared,
            'half_life': np.log(2) / k_fit if k_fit > 0 else np.nan
        })
        
        # Plot the fit
        ax[i+1].plot(seg_data['time_rel'], seg_data['temperature_c'], 'bo', 
                    markersize=4, label='Data')
        ax[i+1].plot(t_fit, T_fit, 'r-', linewidth=2, 
                    label=f'Fit: T_env={T_env_fit:.2f}°C, k={k_fit:.4f}/min')
        ax[i+1].set_xlabel('Time relative to segment start (minutes)')
        ax[i+1].set_ylabel('Temperature (°C)')
        ax[i+1].set_title(f'{seg["name"]} - Newton Cooling Fit')
        ax[i+1].grid(True, alpha=0.3)
        ax[i+1].legend()
        
        # Add residual plot inset
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        inset_ax = inset_axes(ax[i+1], width="40%", height="30%", loc='upper right')
        inset_ax.plot(seg_data['time_rel'], residuals, 'g.', markersize=3)
        inset_ax.axhline(y=0, color='r', linestyle='--', linewidth=1)
        inset_ax.set_xlabel('Time')
        inset_ax.set_ylabel('Residuals')
        inset_ax.set_title('Residuals')
        inset_ax.grid(True, alpha=0.3)
        
    except Exception as e:
        print(f"Error fitting segment {seg['name']}: {e}")
        results.append({
            'segment': seg['name'],
            'error': str(e)
        })

plt.tight_layout()
plt.savefig('../report/images/segment_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

# Print results
df_results = pd.DataFrame(results)
print("\nFitting Results:")
print(df_results.to_string())

# Save results to CSV
df_results.to_csv('../outputs/fitting_results.csv', index=False)
print("\nResults saved to outputs/fitting_results.csv")

# Also try a single exponential fit to the entire dataset (ignoring anomalies)
# Let's use only segment 3 which seems most consistent
seg3 = df[(df['time_min'] >= 121) & (df['time_min'] <= 199)].copy()
seg3['time_rel'] = seg3['time_min'] - 121

# Fit Newton's law
popt3, pcov3 = curve_fit(newton_cooling, 
                         seg3['time_rel'], 
                         seg3['temperature_c'],
                         p0=[30, 40, 0.01],
                         bounds=([25, 35, 0], [35, 45, 0.1]))

T_env3, T03, k3 = popt3
perr3 = np.sqrt(np.diag(pcov3))

print(f"\nSegment 3 detailed fit:")
print(f"Ambient temperature: {T_env3:.2f} ± {perr3[0]:.2f} °C")
print(f"Initial temperature: {T03:.2f} ± {perr3[1]:.2f} °C")
print(f"Cooling constant k: {k3:.4f} ± {perr3[2]:.4f} /min")
print(f"Half-life (time to reduce temp diff by half): {np.log(2)/k3:.1f} minutes")

# Calculate cooling time to reach certain temperatures
for target_temp in [40, 35, 32]:
    if target_temp > T_env3:
        time_to_target = -np.log((target_temp - T_env3) / (T03 - T_env3)) / k3
        print(f"Time to reach {target_temp}°C: {time_to_target:.1f} minutes from segment start")

# Plot comparison of all segments
plt.figure(figsize=(12, 6))
for i, seg in enumerate(segments):
    seg_data = df[(df['time_min'] >= seg['start']) & (df['time_min'] <= seg['end'])].copy()
    seg_data['time_rel'] = seg_data['time_min'] - seg['start']
    plt.plot(seg_data['time_rel'], seg_data['temperature_c'], 
             color=colors[i], linewidth=2, marker='o', markersize=3, 
             label=seg['name'])

plt.xlabel('Time relative to segment start (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Comparison of All Segments (Aligned at Start)')
plt.grid(True, alpha=0.3)
plt.legend()
plt.savefig('../report/images/segments_comparison.png', dpi=300, bbox_inches='tight')
plt.show()