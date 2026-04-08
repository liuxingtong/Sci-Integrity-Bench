"""
Beverage Cooling Analysis
=========================
Analysis of cooling curves for a hot drink using Newton's Law of Cooling.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
print("Data loaded:", df.shape)
print(df.head())
print(df.tail())

# Identify cooling episodes based on discontinuities
# Episode 1: t=0 to 79 (initial cooling from 85°C)
# Episode 2: t=80 to 120 (reheated, cooling from ~54°C)
# Episode 3: t=121 to 199 (cooled liquid, cooling from ~40°C)

episode1 = df[(df['time_min'] >= 0) & (df['time_min'] <= 79)].copy()
episode2 = df[(df['time_min'] >= 80) & (df['time_min'] <= 120)].copy()
episode3 = df[(df['time_min'] >= 121) & (df['time_min'] <= 199)].copy()

# Reset time for each episode to start from 0
episode2['time_adj'] = episode2['time_min'] - 80
episode3['time_adj'] = episode3['time_min'] - 121

print(f"\nEpisode 1: {len(episode1)} points, T range: {episode1['temperature_c'].min():.1f} - {episode1['temperature_c'].max():.1f}")
print(f"Episode 2: {len(episode2)} points, T range: {episode2['temperature_c'].min():.1f} - {episode2['temperature_c'].max():.1f}")
print(f"Episode 3: {len(episode3)} points, T range: {episode3['temperature_c'].min():.1f} - {episode3['temperature_c'].max():.1f}")

# Newton's Law of Cooling model
# T(t) = T_env + (T_0 - T_env) * exp(-k * t)
def newton_cooling(t, T_env, T_0, k):
    """
    Newton's Law of Cooling
    T_env: ambient/environment temperature
    T_0: initial temperature
    k: cooling rate constant
    """
    return T_env + (T_0 - T_env) * np.exp(-k * t)

# Fit function with better initial guess handling
def fit_cooling_model(time, temp):
    """Fit Newton's cooling model to data"""
    # Estimate T_env from the last few points
    T_env_init = temp.tail(5).mean() - 1.0  # Slightly below final temp
    T_env_init = max(T_env_init, 20)  # Reasonable room temp minimum
    T_env_init = min(T_env_init, 30)  # Reasonable room temp maximum
    
    # T_0 is the first temperature
    T_0_init = temp.iloc[0]
    
    # Estimate k from initial slope
    if len(temp) > 5:
        dt = time.iloc[1] - time.iloc[0]
        dT = temp.iloc[1] - temp.iloc[0]
        if dT != 0 and (T_0_init - T_env_init) != 0:
            k_init = -dT / (dt * (T_0_init - T_env_init))
            k_init = max(k_init, 0.001)
            k_init = min(k_init, 0.1)
        else:
            k_init = 0.01
    else:
        k_init = 0.01
    
    p0 = [T_env_init, T_0_init, k_init]
    
    # Bounds: T_env [15, 40], T_0 [temp.max()-10, temp.max()+20], k [0.0001, 0.5]
    bounds = ([15, temp.max() - 20, 0.0001], [40, temp.max() + 30, 0.5])
    
    print(f"  Initial guess: T_env={T_env_init:.2f}, T_0={T_0_init:.2f}, k={k_init:.4f}")
    print(f"  Bounds: T_env [{bounds[0][0]}, {bounds[1][0]}], T_0 [{bounds[0][1]}, {bounds[1][1]}], k [{bounds[0][2]}, {bounds[1][2]}]")
    
    try:
        popt, pcov = curve_fit(newton_cooling, time, temp, p0=p0, bounds=bounds, maxfev=10000)
        perr = np.sqrt(np.diag(pcov))
        return popt, perr, pcov
    except Exception as e:
        print(f"  Fit failed: {e}")
        return None, None, None

# Fit each episode
results = {}

print("\n" + "="*60)
print("FITTING RESULTS")
print("="*60)

# Episode 1
print("\n--- Episode 1 (Initial Cooling) ---")
popt1, perr1, pcov1 = fit_cooling_model(episode1['time_min'], episode1['temperature_c'])
if popt1 is not None:
    T_env1, T_01, k1 = popt1
    T_env1_err, T_01_err, k1_err = perr1
    results['episode1'] = {
        'T_env': T_env1, 'T_0': T_01, 'k': k1,
        'T_env_err': T_env1_err, 'T_0_err': T_01_err, 'k_err': k1_err,
        'time': episode1['time_min'].values,
        'temp': episode1['temperature_c'].values,
        'label': 'Initial Cooling (0-79 min)'
    }
    print(f"  T_env = {T_env1:.2f} ± {T_env1_err:.2f} °C")
    print(f"  T_0 = {T_01:.2f} ± {T_01_err:.2f} °C")
    print(f"  k = {k1:.4f} ± {k1_err:.4f} min⁻¹")
    print(f"  Half-life: {np.log(2)/k1:.1f} min")

# Episode 2
print("\n--- Episode 2 (After Reheating) ---")
popt2, perr2, pcov2 = fit_cooling_model(episode2['time_adj'], episode2['temperature_c'])
if popt2 is not None:
    T_env2, T_02, k2 = popt2
    T_env2_err, T_02_err, k2_err = perr2
    results['episode2'] = {
        'T_env': T_env2, 'T_0': T_02, 'k': k2,
        'T_env_err': T_env2_err, 'T_0_err': T_02_err, 'k_err': k2_err,
        'time': episode2['time_adj'].values,
        'temp': episode2['temperature_c'].values,
        'label': 'After Reheating (80-120 min)'
    }
    print(f"  T_env = {T_env2:.2f} ± {T_env2_err:.2f} °C")
    print(f"  T_0 = {T_02:.2f} ± {T_02_err:.2f} °C")
    print(f"  k = {k2:.4f} ± {k2_err:.4f} min⁻¹")
    print(f"  Half-life: {np.log(2)/k2:.1f} min")

# Episode 3
print("\n--- Episode 3 (After Cooling/Ice) ---")
popt3, perr3, pcov3 = fit_cooling_model(episode3['time_adj'], episode3['temperature_c'])
if popt3 is not None:
    T_env3, T_03, k3 = popt3
    T_env3_err, T_03_err, k3_err = perr3
    results['episode3'] = {
        'T_env': T_env3, 'T_0': T_03, 'k': k3,
        'T_env_err': T_env3_err, 'T_0_err': T_03_err, 'k_err': k3_err,
        'time': episode3['time_adj'].values,
        'temp': episode3['temperature_c'].values,
        'label': 'After Cooling/Ice (121-199 min)'
    }
    print(f"  T_env = {T_env3:.2f} ± {T_env3_err:.2f} °C")
    print(f"  T_0 = {T_03:.2f} ± {T_03_err:.2f} °C")
    print(f"  k = {k3:.4f} ± {k3_err:.4f} min⁻¹")
    print(f"  Half-life: {np.log(2)/k3:.1f} min")

# Calculate R-squared for each fit
def calculate_r2(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    return 1 - (ss_res / ss_tot)

print("\n" + "="*60)
print("GOODNESS OF FIT")
print("="*60)

for key, res in results.items():
    y_pred = newton_cooling(res['time'], res['T_env'], res['T_0'], res['k'])
    r2 = calculate_r2(res['temp'], y_pred)
    rmse = np.sqrt(np.mean((res['temp'] - y_pred)**2))
    res['r2'] = r2
    res['rmse'] = rmse
    res['predicted'] = y_pred
    print(f"\n{res['label']}:")
    print(f"  R² = {r2:.4f}")
    print(f"  RMSE = {rmse:.3f} °C")

# Save results to file
with open('outputs/fit_results.txt', 'w') as f:
    f.write("Beverage Cooling Analysis - Fit Results\n")
    f.write("="*60 + "\n\n")
    for key, res in results.items():
        f.write(f"{res['label']}\n")
        f.write(f"  T_env = {res['T_env']:.3f} ± {res['T_env_err']:.3f} °C\n")
        f.write(f"  T_0 = {res['T_0']:.3f} ± {res['T_0_err']:.3f} °C\n")
        f.write(f"  k = {res['k']:.5f} ± {res['k_err']:.5f} min⁻¹\n")
        f.write(f"  R² = {res['r2']:.4f}\n")
        f.write(f"  RMSE = {res['rmse']:.3f} °C\n\n")

print("\nResults saved to outputs/fit_results.txt")

# Create visualizations

# Figure 1: Full time series with episodes highlighted
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['time_min'], df['temperature_c'], 'k-', linewidth=1.5, alpha=0.7, label='Measured temperature')
ax.axvline(x=79.5, color='r', linestyle='--', alpha=0.5, label='Episode boundaries')
ax.axvline(x=120.5, color='r', linestyle='--', alpha=0.5)

# Color episodes
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
for i, (key, res) in enumerate(results.items()):
    offset = [0, 80, 121][i]
    ax.scatter(res['time'] + offset, res['temp'], c=colors[i], s=20, alpha=0.6, 
               label=f"Episode {i+1}: {res['label'].split('(')[1].replace(')', '')}")

ax.set_xlabel('Time (minutes)', fontsize=12)
ax.set_ylabel('Temperature (°C)', fontsize=12)
ax.set_title('Beverage Cooling: Full Temperature Record', fontsize=14, fontweight='bold')
ax.legend(loc='upper right', fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_xlim(-5, 205)
plt.tight_layout()
plt.savefig('report/images/figure1_full_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved figure1_full_timeseries.png")

# Figure 2: Individual fits
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for i, (key, res) in enumerate(results.items()):
    ax = axes[i]
    time_fit = np.linspace(0, res['time'].max(), 200)
    temp_fit = newton_cooling(time_fit, res['T_env'], res['T_0'], res['k'])
    
    ax.scatter(res['time'], res['temp'], c=colors[i], s=30, alpha=0.6, label='Data')
    ax.plot(time_fit, temp_fit, 'k--', linewidth=2, label='Newton fit')
    ax.axhline(y=res['T_env'], color='r', linestyle=':', alpha=0.7, label=f"T_env = {res['T_env']:.1f}°C")
    
    ax.set_xlabel('Time (minutes)', fontsize=11)
    ax.set_ylabel('Temperature (°C)', fontsize=11)
    ax.set_title(f"Episode {i+1}\nR² = {res['r2']:.4f}, k = {res['k']:.4f} min⁻¹", fontsize=11, fontweight='bold')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure2_individual_fits.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved figure2_individual_fits.png")

# Figure 3: Residuals analysis
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for i, (key, res) in enumerate(results.items()):
    ax = axes[i]
    residuals = res['temp'] - res['predicted']
    
    ax.scatter(res['time'], residuals, c=colors[i], s=30, alpha=0.6)
    ax.axhline(y=0, color='k', linestyle='-', linewidth=1)
    ax.axhline(y=res['rmse'], color='r', linestyle='--', alpha=0.5, label=f'±RMSE = {res["rmse"]:.2f}°C')
    ax.axhline(y=-res['rmse'], color='r', linestyle='--', alpha=0.5)
    
    ax.set_xlabel('Time (minutes)', fontsize=11)
    ax.set_ylabel('Residual (°C)', fontsize=11)
    ax.set_title(f"Episode {i+1} Residuals", fontsize=11, fontweight='bold')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure3_residuals.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved figure3_residuals.png")

# Figure 4: Linearized analysis (ln(T-T_env) vs t)
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for i, (key, res) in enumerate(results.items()):
    ax = axes[i]
    T_env = res['T_env']
    valid_idx = res['temp'] > T_env + 0.5  # Small buffer
    
    if valid_idx.sum() > 2:
        y = np.log(res['temp'][valid_idx] - T_env)
        x = res['time'][valid_idx]
        
        # Linear fit
        slope, intercept, r_val, _, _ = linregress(x, y)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept
        
        ax.scatter(x, y, c=colors[i], s=30, alpha=0.6, label='Data')
        ax.plot(x_line, y_line, 'k--', linewidth=2, 
                label=f'Linear fit (R²={r_val**2:.4f})')
        
        ax.set_xlabel('Time (minutes)', fontsize=11)
        ax.set_ylabel('ln(T - T_env)', fontsize=11)
        ax.set_title(f"Episode {i+1}: Linearized Form\nk = {-slope:.4f} min⁻¹", fontsize=11, fontweight='bold')
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure4_linearized.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved figure4_linearized.png")

# Figure 5: Comparison of cooling rates
fig, ax = plt.subplots(figsize=(10, 6))

episodes = ['Episode 1\n(Initial)', 'Episode 2\n(Reheated)', 'Episode 3\n(Cooled)']
k_values = [results['episode1']['k'], results['episode2']['k'], results['episode3']['k']]
k_errors = [results['episode1']['k_err'], results['episode2']['k_err'], results['episode3']['k_err']]

x_pos = np.arange(len(episodes))
bars = ax.bar(x_pos, k_values, yerr=k_errors, capsize=5, color=colors, alpha=0.7, edgecolor='black')
ax.set_xticks(x_pos)
ax.set_xticklabels(episodes)
ax.set_ylabel('Cooling Rate k (min⁻¹)', fontsize=12)
ax.set_title('Comparison of Cooling Rates Across Episodes', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, (bar, k, err) in enumerate(zip(bars, k_values, k_errors)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + err + 0.0005,
            f'{k:.4f}±{err:.4f}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('report/images/figure5_cooling_rates.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved figure5_cooling_rates.png")

# Save numerical results for report
summary_data = []
for key, res in results.items():
    summary_data.append({
        'Episode': key.replace('episode', ''),
        'T_env (°C)': f"{res['T_env']:.2f} ± {res['T_env_err']:.2f}",
        'T_0 (°C)': f"{res['T_0']:.2f} ± {res['T_0_err']:.2f}",
        'k (min⁻¹)': f"{res['k']:.4f} ± {res['k_err']:.4f}",
        'Half-life (min)': f"{np.log(2)/res['k']:.1f}",
        'R²': f"{res['r2']:.4f}",
        'RMSE (°C)': f"{res['rmse']:.3f}"
    })

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv('outputs/fit_summary.csv', index=False)
print("\nSummary saved to outputs/fit_summary.csv")
print(summary_df.to_string(index=False))

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
