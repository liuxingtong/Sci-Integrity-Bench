"""
Detailed Beverage Cooling Analysis
==================================
Exploring Newton's Law of Cooling with model validation and physical interpretation.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress, probplot
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')

# Identify cooling episodes
episode1 = df[(df['time_min'] >= 0) & (df['time_min'] <= 79)].copy()
episode2 = df[(df['time_min'] >= 80) & (df['time_min'] <= 120)].copy()
episode3 = df[(df['time_min'] >= 121) & (df['time_min'] <= 199)].copy()

# Reset time for each episode
episode2['time_adj'] = episode2['time_min'] - 80
episode3['time_adj'] = episode3['time_min'] - 121

# Newton's Law of Cooling
def newton_cooling(t, T_env, T_0, k):
    return T_env + (T_0 - T_env) * np.exp(-k * t)

# Fit function
def fit_cooling_model(time, temp):
    T_env_init = max(min(temp.tail(5).mean() - 1.0, 30), 20)
    T_0_init = temp.iloc[0]
    k_init = 0.01
    
    p0 = [T_env_init, T_0_init, k_init]
    bounds = ([15, temp.max() - 20, 0.0001], [40, temp.max() + 30, 0.5])
    
    popt, pcov = curve_fit(newton_cooling, time, temp, p0=p0, bounds=bounds, maxfev=10000)
    perr = np.sqrt(np.diag(pcov))
    return popt, perr, pcov

# Fit all episodes
results = {}
episodes_data = [
    ('episode1', episode1['time_min'], episode1['temperature_c'], 'Initial Cooling'),
    ('episode2', episode2['time_adj'], episode2['temperature_c'], 'After Reheating'),
    ('episode3', episode3['time_adj'], episode3['temperature_c'], 'After Cooling/Ice')
]

for key, time, temp, label in episodes_data:
    popt, perr, pcov = fit_cooling_model(time, temp)
    T_env, T_0, k = popt
    T_env_err, T_0_err, k_err = perr
    
    y_pred = newton_cooling(time, T_env, T_0, k)
    residuals = temp.values - y_pred
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((temp.values - np.mean(temp.values))**2)
    r2 = 1 - (ss_res / ss_tot)
    rmse = np.sqrt(np.mean(residuals**2))
    
    results[key] = {
        'T_env': T_env, 'T_0': T_0, 'k': k,
        'T_env_err': T_env_err, 'T_0_err': T_0_err, 'k_err': k_err,
        'time': time.values, 'temp': temp.values,
        'predicted': y_pred, 'residuals': residuals,
        'r2': r2, 'rmse': rmse, 'label': label
    }

# Check for synthetic data characteristics
print("Checking data characteristics...")
for key, res in results.items():
    # Check if residuals are essentially zero
    max_residual = np.max(np.abs(res['residuals']))
    print(f"{key}: Max |residual| = {max_residual:.6f}°C")

# Figure 1: Full time series with annotations
fig, ax = plt.subplots(figsize=(14, 7))
ax.plot(df['time_min'], df['temperature_c'], 'k-', linewidth=1.5, alpha=0.8, label='Temperature')

# Add episode shading
ax.axvspan(0, 79, alpha=0.1, color='blue', label='Episode 1: Initial cooling')
ax.axvspan(80, 120, alpha=0.1, color='orange', label='Episode 2: After reheating')
ax.axvspan(121, 199, alpha=0.1, color='green', label='Episode 3: After cooling/ice')

# Mark transitions
ax.axvline(x=79.5, color='red', linestyle='--', alpha=0.7, linewidth=2)
ax.axvline(x=120.5, color='red', linestyle='--', alpha=0.7, linewidth=2)

# Annotate key events
ax.annotate('Reheating\n(+5°C jump)', xy=(80, 54.2), xytext=(90, 65),
            arrowprops=dict(arrowstyle='->', color='red'),
            fontsize=10, ha='center', color='red')
ax.annotate('Added cold liquid/ice\n(-14°C drop)', xy=(121, 39.8), xytext=(140, 50),
            arrowprops=dict(arrowstyle='->', color='blue'),
            fontsize=10, ha='center', color='blue')

ax.set_xlabel('Time (minutes)', fontsize=13)
ax.set_ylabel('Temperature (°C)', fontsize=13)
ax.set_title('Beverage Cooling Experiment: Full Temperature Record', fontsize=15, fontweight='bold')
ax.legend(loc='upper right', fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xlim(-5, 205)
ax.set_ylim(25, 90)

plt.tight_layout()
plt.savefig('report/images/figure1_full_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 2: Individual fits with confidence intervals
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

for i, (key, res) in enumerate(results.items()):
    ax = axes[i]
    
    # Generate smooth fit curve
    time_fit = np.linspace(0, res['time'].max(), 200)
    temp_fit = newton_cooling(time_fit, res['T_env'], res['T_0'], res['k'])
    
    # Plot data and fit
    ax.scatter(res['time'], res['temp'], c=colors[i], s=40, alpha=0.7, edgecolors='black', linewidth=0.5, label='Data')
    ax.plot(time_fit, temp_fit, 'k--', linewidth=2.5, label='Newton fit')
    
    # Add T_env line
    ax.axhline(y=res['T_env'], color='red', linestyle=':', alpha=0.8, linewidth=2, 
               label=f"T_env = {res['T_env']:.1f}°C")
    
    # Add equation text
    eq_text = f"T(t) = {res['T_env']:.1f} + {res['T_0']-res['T_env']:.1f}·exp(-{res['k']:.4f}t)"
    ax.text(0.05, 0.95, eq_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax.set_xlabel('Time (minutes)', fontsize=12)
    ax.set_ylabel('Temperature (°C)', fontsize=12)
    ax.set_title(f"Episode {i+1}: {res['label']}\nR² = {res['r2']:.6f}, RMSE = {res['rmse']:.4f}°C", 
                 fontsize=11, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure2_individual_fits.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 3: Residuals analysis
fig, axes = plt.subplots(2, 3, figsize=(15, 8))

for i, (key, res) in enumerate(results.items()):
    # Time series residuals
    ax1 = axes[0, i]
    ax1.scatter(res['time'], res['residuals'], c=colors[i], s=30, alpha=0.7, edgecolors='black', linewidth=0.5)
    ax1.axhline(y=0, color='k', linestyle='-', linewidth=1.5)
    ax1.axhline(y=res['rmse'], color='r', linestyle='--', alpha=0.6, label=f'RMSE = {res["rmse"]:.4f}°C')
    ax1.axhline(y=-res['rmse'], color='r', linestyle='--', alpha=0.6)
    ax1.set_xlabel('Time (minutes)', fontsize=11)
    ax1.set_ylabel('Residual (°C)', fontsize=11)
    ax1.set_title(f"Episode {i+1} Residuals vs Time", fontsize=11, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Q-Q plot for normality check
    ax2 = axes[1, i]
    probplot(res['residuals'], dist="norm", plot=ax2)
    ax2.set_title(f"Episode {i+1} Q-Q Plot", fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure3_residuals.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 4: Linearized analysis
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

for i, (key, res) in enumerate(results.items()):
    ax = axes[i]
    T_env = res['T_env']
    
    # Only use points well above T_env
    valid_idx = res['temp'] > T_env + 0.1
    
    if valid_idx.sum() > 2:
        y = np.log(res['temp'][valid_idx] - T_env)
        x = res['time'][valid_idx]
        
        # Linear fit
        slope, intercept, r_val, _, std_err = linregress(x, y)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept
        
        ax.scatter(x, y, c=colors[i], s=40, alpha=0.7, edgecolors='black', linewidth=0.5, label='Data')
        ax.plot(x_line, y_line, 'k--', linewidth=2.5, label=f'Linear fit')
        
        # Add fit info
        fit_text = f"Slope = {slope:.5f}\nR² = {r_val**2:.6f}"
        ax.text(0.05, 0.95, fit_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.set_xlabel('Time (minutes)', fontsize=12)
        ax.set_ylabel('ln(T - T_env)', fontsize=12)
        ax.set_title(f"Episode {i+1}: Linearized Form\nk = {-slope:.5f} min⁻¹", fontsize=11, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure4_linearized.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 5: Cooling rate comparison
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

episodes = ['Episode 1\n(Initial)', 'Episode 2\n(Reheated)', 'Episode 3\n(Cooled)']
k_values = [results['episode1']['k'], results['episode2']['k'], results['episode3']['k']]
k_errors = [results['episode1']['k_err'], results['episode2']['k_err'], results['episode3']['k_err']]
T_env_values = [results['episode1']['T_env'], results['episode2']['T_env'], results['episode3']['T_env']]
T_env_errors = [results['episode1']['T_env_err'], results['episode2']['T_env_err'], results['episode3']['T_env_err']]

x_pos = np.arange(len(episodes))

# Cooling rates
bars1 = ax1.bar(x_pos, k_values, yerr=k_errors, capsize=8, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(episodes, fontsize=11)
ax1.set_ylabel('Cooling Rate k (min⁻¹)', fontsize=12)
ax1.set_title('Cooling Rate Constants', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')

for i, (bar, k, err) in enumerate(zip(bars1, k_values, k_errors)):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + err + 0.0003,
            f'{k:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

# T_env values
bars2 = ax2.bar(x_pos, T_env_values, yerr=T_env_errors, capsize=8, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(episodes, fontsize=11)
ax2.set_ylabel('Ambient Temperature T_env (°C)', fontsize=12)
ax2.set_title('Estimated Ambient Temperatures', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')

for i, (bar, T, err) in enumerate(zip(bars2, T_env_values, T_env_errors)):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + err + 0.3,
            f'{T:.1f}°C', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/figure5_parameter_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 6: Half-life and time constant analysis
fig, ax = plt.subplots(figsize=(10, 6))

half_lives = [np.log(2)/k for k in k_values]
time_constants = [1/k for k in k_values]

x = np.arange(len(episodes))
width = 0.35

bars1 = ax.bar(x - width/2, half_lives, width, label='Half-life (ln(2)/k)', color='steelblue', alpha=0.8, edgecolor='black')
bars2 = ax.bar(x + width/2, time_constants, width, label='Time constant (1/k)', color='coral', alpha=0.8, edgecolor='black')

ax.set_ylabel('Time (minutes)', fontsize=12)
ax.set_title('Characteristic Cooling Times', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(episodes)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, axis='y')

# Add value labels
for bar in bars1:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{height:.1f}', ha='center', va='bottom', fontsize=10)
for bar in bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1,
            f'{height:.1f}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/figure6_time_constants.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 7: Model validation - comparing all episodes on normalized scale
fig, ax = plt.subplots(figsize=(10, 7))

for i, (key, res) in enumerate(results.items()):
    # Normalize: (T - T_env) / (T_0 - T_env)
    normalized_temp = (res['temp'] - res['T_env']) / (res['T_0'] - res['T_env'])
    
    # Theoretical exponential decay
    time_norm = np.linspace(0, res['time'].max(), 200)
    theoretical = np.exp(-res['k'] * time_norm)
    
    ax.scatter(res['time'], normalized_temp, c=colors[i], s=30, alpha=0.6, 
               label=f"Episode {i+1} (data)")
    ax.plot(time_norm, theoretical, '--', color=colors[i], linewidth=2, 
            label=f"Episode {i+1} (fit)")

ax.axhline(y=0.5, color='gray', linestyle=':', alpha=0.7, label='Halfway point')
ax.set_xlabel('Time (minutes)', fontsize=12)
ax.set_ylabel('Normalized Temperature (T-T_env)/(T₀-T_env)', fontsize=12)
ax.set_title('Normalized Cooling Curves: Universal Exponential Behavior', fontsize=14, fontweight='bold')
ax.legend(loc='upper right', fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_ylim(-0.05, 1.05)

plt.tight_layout()
plt.savefig('report/images/figure7_normalized_comparison.png', dpi=150, bbox_inches='tight')
plt.close()

# Save comprehensive results
with open('outputs/detailed_results.txt', 'w') as f:
    f.write("="*70 + "\n")
    f.write("BEVERAGE COOLING ANALYSIS - DETAILED RESULTS\n")
    f.write("="*70 + "\n\n")
    
    f.write("DATA CHARACTERISTICS:\n")
    f.write("-"*70 + "\n")
    f.write(f"Total measurements: {len(df)}\n")
    f.write(f"Time span: {df['time_min'].min()} to {df['time_min'].max()} minutes\n")
    f.write(f"Temperature range: {df['temperature_c'].min():.2f} to {df['temperature_c'].max():.2f} °C\n\n")
    
    f.write("EPISODE BREAKDOWN:\n")
    f.write("-"*70 + "\n")
    for i, (key, res) in enumerate(results.items(), 1):
        f.write(f"\nEpisode {i}: {res['label']}\n")
        f.write(f"  Data points: {len(res['time'])}\n")
        f.write(f"  Temperature range: {res['temp'].min():.2f} to {res['temp'].max():.2f} °C\n")
        f.write(f"  Duration: {res['time'].max():.0f} minutes\n")
    
    f.write("\n\nFITTING RESULTS (Newton's Law of Cooling):\n")
    f.write("-"*70 + "\n")
    f.write("Model: T(t) = T_env + (T_0 - T_env) * exp(-k*t)\n\n")
    
    for i, (key, res) in enumerate(results.items(), 1):
        f.write(f"\nEpisode {i}: {res['label']}\n")
        f.write(f"  T_env = {res['T_env']:.4f} ± {res['T_env_err']:.4f} °C\n")
        f.write(f"  T_0 = {res['T_0']:.4f} ± {res['T_0_err']:.4f} °C\n")
        f.write(f"  k = {res['k']:.6f} ± {res['k_err']:.6f} min⁻¹\n")
        f.write(f"  Time constant τ = 1/k = {1/res['k']:.2f} min\n")
        f.write(f"  Half-life t_1/2 = ln(2)/k = {np.log(2)/res['k']:.2f} min\n")
        f.write(f"  R² = {res['r2']:.6f}\n")
        f.write(f"  RMSE = {res['rmse']:.6f} °C\n")
        f.write(f"  Max |residual| = {np.max(np.abs(res['residuals'])):.6f} °C\n")
    
    f.write("\n\nKEY FINDINGS:\n")
    f.write("-"*70 + "\n")
    f.write("1. All three episodes follow Newton's Law of Cooling with exceptional precision.\n")
    f.write("2. The cooling rate constant k is consistent across episodes (~0.0116 min⁻¹).\n")
    f.write("3. Episode 2 shows elevated T_env (34°C), suggesting a warmer environment or\n")
    f.write("   measurement after reheating in a different location.\n")
    f.write("4. The near-perfect fits (R² ≈ 1.0000) indicate either:\n")
    f.write("   a) Highly controlled experimental conditions\n")
    f.write("   b) Data generated from the model itself (simulation)\n")
    f.write("5. Half-life of ~60 minutes indicates moderate cooling rate typical for\n")
    f.write("   a ceramic mug in still air.\n")

print("Detailed analysis complete. Results saved to outputs/detailed_results.txt")

# Save summary CSV
summary_data = []
for i, (key, res) in enumerate(results.items(), 1):
    summary_data.append({
        'Episode': i,
        'Description': res['label'],
        'T_env_C': res['T_env'],
        'T_env_err_C': res['T_env_err'],
        'T_0_C': res['T_0'],
        'T_0_err_C': res['T_0_err'],
        'k_per_min': res['k'],
        'k_err_per_min': res['k_err'],
        'time_constant_min': 1/res['k'],
        'half_life_min': np.log(2)/res['k'],
        'R_squared': res['r2'],
        'RMSE_C': res['rmse']
    })

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv('outputs/fit_summary.csv', index=False)
print("Summary saved to outputs/fit_summary.csv")
print(summary_df.to_string(index=False))
