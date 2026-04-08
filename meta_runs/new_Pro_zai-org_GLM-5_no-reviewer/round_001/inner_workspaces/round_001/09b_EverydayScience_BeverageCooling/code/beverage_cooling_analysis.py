"""
Beverage Cooling Analysis
=========================
Analysis of temperature cooling data using Newton's Law of Cooling
and related thermodynamic models.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress
import os
import warnings
warnings.filterwarnings('ignore')

# Set up paths
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(workspace_dir, 'data', 'beverage_temperature_series.csv')
outputs_dir = os.path.join(workspace_dir, 'outputs')
images_dir = os.path.join(workspace_dir, 'report', 'images')

# Create directories if they don't exist
os.makedirs(outputs_dir, exist_ok=True)
os.makedirs(images_dir, exist_ok=True)

# Load data
print("Loading data...")
df = pd.read_csv(data_path)
print(f"Data shape: {df.shape}")
print(f"Time range: {df['time_min'].min()} to {df['time_min'].max()} minutes")
print(f"Temperature range: {df['temperature_c'].min():.2f} to {df['temperature_c'].max():.2f} °C")

# Save data summary
with open(os.path.join(outputs_dir, 'data_summary.txt'), 'w') as f:
    f.write("Beverage Cooling Data Summary\n")
    f.write("="*50 + "\n\n")
    f.write(f"Number of observations: {len(df)}\n")
    f.write(f"Time range: {df['time_min'].min()} to {df['time_min'].max()} minutes\n")
    f.write(f"Temperature range: {df['temperature_c'].min():.2f} to {df['temperature_c'].max():.2f} °C\n")
    f.write(f"\nFirst 10 rows:\n{df.head(10).to_string()}\n")
    f.write(f"\nLast 10 rows:\n{df.tail(10).to_string()}\n")

# Detect discontinuities (sudden jumps in temperature)
print("\nDetecting discontinuities...")
df['temp_diff'] = df['temperature_c'].diff()
discontinuities = df[abs(df['temp_diff']) > 2]
print(f"Discontinuities detected at: {discontinuities['time_min'].tolist()}")

# Newton's Law of Cooling model: T(t) = T_env + (T0 - T_env) * exp(-k * t)
def newton_cooling(t, T_env, T0, k):
    """
    Newton's Law of Cooling
    T(t) = T_env + (T0 - T_env) * exp(-k * t)
    
    Parameters:
    - T_env: ambient/environment temperature (°C)
    - T0: initial temperature (°C)
    - k: cooling constant (1/min)
    """
    return T_env + (T0 - T_env) * np.exp(-k * t)

# Alternative model: Power law cooling
def power_law_cooling(t, T_env, T0, a, n):
    """
    Power law cooling model
    T(t) = T_env + (T0 - T_env) / (1 + a * t)^n
    """
    return T_env + (T0 - T_env) / np.power(1 + a * t, n)

# Linear model (for comparison)
def linear_approx(t, T0, slope):
    """Linear approximation for short time scales"""
    return T0 + slope * t

# Analyze the first segment (before first discontinuity)
print("\n" + "="*60)
print("SEGMENT 1: Minutes 0-79")
print("="*60)

segment1 = df[(df['time_min'] >= 0) & (df['time_min'] <= 79)].copy()
t1 = segment1['time_min'].values
T1 = segment1['temperature_c'].values

# Fit Newton's Law of Cooling to segment 1
try:
    # Initial guesses
    T0_guess = T1[0]
    T_env_guess = 20.0  # Room temperature guess
    k_guess = 0.02
    
    popt1, pcov1 = curve_fit(newton_cooling, t1, T1, 
                              p0=[T_env_guess, T0_guess, k_guess],
                              bounds=([0, 50, 0.001], [40, 100, 0.5]),
                              maxfev=10000)
    
    T_env1, T0_fit1, k1 = popt1
    perr1 = np.sqrt(np.diag(pcov1))
    
    print(f"Newton's Law of Cooling Fit:")
    print(f"  T_env (ambient): {T_env1:.2f} ± {perr1[0]:.2f} °C")
    print(f"  T0 (initial): {T0_fit1:.2f} ± {perr1[1]:.2f} °C")
    print(f"  k (cooling constant): {k1:.4f} ± {perr1[2]:.4f} min^-1")
    print(f"  Half-life: {np.log(2)/k1:.1f} minutes")
    
    # Calculate R-squared
    T1_pred = newton_cooling(t1, *popt1)
    ss_res1 = np.sum((T1 - T1_pred)**2)
    ss_tot1 = np.sum((T1 - np.mean(T1))**2)
    r2_1 = 1 - (ss_res1 / ss_tot1)
    print(f"  R-squared: {r2_1:.6f}")
    
    # RMSE
    rmse1 = np.sqrt(np.mean((T1 - T1_pred)**2))
    print(f"  RMSE: {rmse1:.4f} °C")
    
    fit1_success = True
except Exception as e:
    print(f"Fit failed: {e}")
    fit1_success = False

# Analyze segment 2 (minutes 80-120)
print("\n" + "="*60)
print("SEGMENT 2: Minutes 80-120")
print("="*60)

segment2 = df[(df['time_min'] >= 80) & (df['time_min'] <= 120)].copy()
t2 = segment2['time_min'].values
T2 = segment2['temperature_c'].values

# Fit Newton's Law of Cooling to segment 2
try:
    T0_guess2 = T2[0]
    T_env_guess2 = 20.0
    k_guess2 = 0.02
    
    popt2, pcov2 = curve_fit(newton_cooling, t2, T2, 
                              p0=[T_env_guess2, T0_guess2, k_guess2],
                              bounds=([0, 40, 0.001], [40, 60, 0.5]),
                              maxfev=10000)
    
    T_env2, T0_fit2, k2 = popt2
    perr2 = np.sqrt(np.diag(pcov2))
    
    print(f"Newton's Law of Cooling Fit:")
    print(f"  T_env (ambient): {T_env2:.2f} ± {perr2[0]:.2f} °C")
    print(f"  T0 (initial): {T0_fit2:.2f} ± {perr2[1]:.2f} °C")
    print(f"  k (cooling constant): {k2:.4f} ± {perr2[2]:.4f} min^-1")
    print(f"  Half-life: {np.log(2)/k2:.1f} minutes")
    
    T2_pred = newton_cooling(t2, *popt2)
    ss_res2 = np.sum((T2 - T2_pred)**2)
    ss_tot2 = np.sum((T2 - np.mean(T2))**2)
    r2_2 = 1 - (ss_res2 / ss_tot2)
    print(f"  R-squared: {r2_2:.6f}")
    
    rmse2 = np.sqrt(np.mean((T2 - T2_pred)**2))
    print(f"  RMSE: {rmse2:.4f} °C")
    
    fit2_success = True
except Exception as e:
    print(f"Fit failed: {e}")
    fit2_success = False

# Analyze segment 3 (minutes 121-199)
print("\n" + "="*60)
print("SEGMENT 3: Minutes 121-199")
print("="*60)

segment3 = df[(df['time_min'] >= 121) & (df['time_min'] <= 199)].copy()
t3 = segment3['time_min'].values
T3 = segment3['temperature_c'].values

# Fit Newton's Law of Cooling to segment 3
try:
    T0_guess3 = T3[0]
    T_env_guess3 = 25.0
    k_guess3 = 0.02
    
    popt3, pcov3 = curve_fit(newton_cooling, t3, T3, 
                              p0=[T_env_guess3, T0_guess3, k_guess3],
                              bounds=([0, 30, 0.001], [35, 45, 0.5]),
                              maxfev=10000)
    
    T_env3, T0_fit3, k3 = popt3
    perr3 = np.sqrt(np.diag(pcov3))
    
    print(f"Newton's Law of Cooling Fit:")
    print(f"  T_env (ambient): {T_env3:.2f} ± {perr3[0]:.2f} °C")
    print(f"  T0 (initial): {T0_fit3:.2f} ± {perr3[1]:.2f} °C")
    print(f"  k (cooling constant): {k3:.4f} ± {perr3[2]:.4f} min^-1")
    print(f"  Half-life: {np.log(2)/k3:.1f} minutes")
    
    T3_pred = newton_cooling(t3, *popt3)
    ss_res3 = np.sum((T3 - T3_pred)**2)
    ss_tot3 = np.sum((T3 - np.mean(T3))**2)
    r2_3 = 1 - (ss_res3 / ss_tot3)
    print(f"  R-squared: {r2_3:.6f}")
    
    rmse3 = np.sqrt(np.mean((T3 - T3_pred)**2))
    print(f"  RMSE: {rmse3:.4f} °C")
    
    fit3_success = True
except Exception as e:
    print(f"Fit failed: {e}")
    fit3_success = False

# Try fitting the entire dataset with a single model (for comparison)
print("\n" + "="*60)
print("FULL DATASET FIT (for comparison)")
print("="*60)

t_full = df['time_min'].values
T_full = df['temperature_c'].values

try:
    T0_guess_full = T_full[0]
    T_env_guess_full = 25.0
    k_guess_full = 0.01
    
    popt_full, pcov_full = curve_fit(newton_cooling, t_full, T_full, 
                                     p0=[T_env_guess_full, T0_guess_full, k_guess_full],
                                     bounds=([0, 50, 0.001], [40, 100, 0.5]),
                                     maxfev=10000)
    
    T_env_full, T0_fit_full, k_full = popt_full
    perr_full = np.sqrt(np.diag(pcov_full))
    
    print(f"Newton's Law of Cooling Fit:")
    print(f"  T_env (ambient): {T_env_full:.2f} ± {perr_full[0]:.2f} °C")
    print(f"  T0 (initial): {T0_fit_full:.2f} ± {perr_full[1]:.2f} °C")
    print(f"  k (cooling constant): {k_full:.4f} ± {perr_full[2]:.4f} min^-1")
    
    T_full_pred = newton_cooling(t_full, *popt_full)
    ss_res_full = np.sum((T_full - T_full_pred)**2)
    ss_tot_full = np.sum((T_full - np.mean(T_full))**2)
    r2_full = 1 - (ss_res_full / ss_tot_full)
    print(f"  R-squared: {r2_full:.6f}")
    
    rmse_full = np.sqrt(np.mean((T_full - T_full_pred)**2))
    print(f"  RMSE: {rmse_full:.4f} °C")
    
    fit_full_success = True
except Exception as e:
    print(f"Fit failed: {e}")
    fit_full_success = False

# Save fit results
results = {
    'segment1': {'T_env': T_env1, 'T0': T0_fit1, 'k': k1, 'r2': r2_1, 'rmse': rmse1} if fit1_success else None,
    'segment2': {'T_env': T_env2, 'T0': T0_fit2, 'k': k2, 'r2': r2_2, 'rmse': rmse2} if fit2_success else None,
    'segment3': {'T_env': T_env3, 'T0': T0_fit3, 'k': k3, 'r2': r2_3, 'rmse': rmse3} if fit3_success else None,
    'full': {'T_env': T_env_full, 'T0': T0_fit_full, 'k': k_full, 'r2': r2_full, 'rmse': rmse_full} if fit_full_success else None
}

# Create visualizations
print("\n" + "="*60)
print("CREATING VISUALIZATIONS")
print("="*60)

# Figure 1: Full temperature profile
fig1, ax1 = plt.subplots(figsize=(12, 6))
ax1.plot(df['time_min'], df['temperature_c'], 'b-', linewidth=1.5, label='Observed Temperature')
ax1.set_xlabel('Time (minutes)', fontsize=12)
ax1.set_ylabel('Temperature (°C)', fontsize=12)
ax1.set_title('Beverage Cooling Curve: Temperature vs Time', fontsize=14)
ax1.grid(True, alpha=0.3)
ax1.legend()

# Mark discontinuities
if len(discontinuities) > 0:
    for t_disc in discontinuities['time_min']:
        ax1.axvline(x=t_disc, color='r', linestyle='--', alpha=0.5, label='Discontinuity' if t_disc == discontinuities['time_min'].iloc[0] else '')

plt.tight_layout()
plt.savefig(os.path.join(images_dir, 'figure1_temperature_profile.png'), dpi=150)
plt.close()
print("Saved: figure1_temperature_profile.png")

# Figure 2: Newton's Law fits for each segment
fig2, axes = plt.subplots(1, 3, figsize=(15, 5))

# Segment 1
if fit1_success:
    t1_fine = np.linspace(0, 79, 200)
    T1_fine = newton_cooling(t1_fine, *popt1)
    axes[0].plot(t1, T1, 'bo', markersize=4, label='Observed', alpha=0.7)
    axes[0].plot(t1_fine, T1_fine, 'r-', linewidth=2, label='Newton Fit')
    axes[0].set_xlabel('Time (min)')
    axes[0].set_ylabel('Temperature (°C)')
    axes[0].set_title(f'Segment 1 (0-79 min)\nR² = {r2_1:.4f}')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

# Segment 2
if fit2_success:
    t2_fine = np.linspace(80, 120, 200)
    T2_fine = newton_cooling(t2_fine, *popt2)
    axes[1].plot(t2, T2, 'bo', markersize=4, label='Observed', alpha=0.7)
    axes[1].plot(t2_fine, T2_fine, 'r-', linewidth=2, label='Newton Fit')
    axes[1].set_xlabel('Time (min)')
    axes[1].set_ylabel('Temperature (°C)')
    axes[1].set_title(f'Segment 2 (80-120 min)\nR² = {r2_2:.4f}')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

# Segment 3
if fit3_success:
    t3_fine = np.linspace(121, 199, 200)
    T3_fine = newton_cooling(t3_fine, *popt3)
    axes[2].plot(t3, T3, 'bo', markersize=4, label='Observed', alpha=0.7)
    axes[2].plot(t3_fine, T3_fine, 'r-', linewidth=2, label='Newton Fit')
    axes[2].set_xlabel('Time (min)')
    axes[2].set_ylabel('Temperature (°C)')
    axes[2].set_title(f'Segment 3 (121-199 min)\nR² = {r2_3:.4f}')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(images_dir, 'figure2_segment_fits.png'), dpi=150)
plt.close()
print("Saved: figure2_segment_fits.png")

# Figure 3: Residuals analysis
fig3, axes = plt.subplots(1, 3, figsize=(15, 5))

if fit1_success:
    residuals1 = T1 - newton_cooling(t1, *popt1)
    axes[0].plot(t1, residuals1, 'go-', markersize=3, linewidth=1)
    axes[0].axhline(y=0, color='k', linestyle='--', alpha=0.5)
    axes[0].set_xlabel('Time (min)')
    axes[0].set_ylabel('Residual (°C)')
    axes[0].set_title(f'Segment 1 Residuals\nRMSE = {rmse1:.3f} °C')
    axes[0].grid(True, alpha=0.3)

if fit2_success:
    residuals2 = T2 - newton_cooling(t2, *popt2)
    axes[1].plot(t2, residuals2, 'go-', markersize=3, linewidth=1)
    axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.5)
    axes[1].set_xlabel('Time (min)')
    axes[1].set_ylabel('Residual (°C)')
    axes[1].set_title(f'Segment 2 Residuals\nRMSE = {rmse2:.3f} °C')
    axes[1].grid(True, alpha=0.3)

if fit3_success:
    residuals3 = T3 - newton_cooling(t3, *popt3)
    axes[2].plot(t3, residuals3, 'go-', markersize=3, linewidth=1)
    axes[2].axhline(y=0, color='k', linestyle='--', alpha=0.5)
    axes[2].set_xlabel('Time (min)')
    axes[2].set_ylabel('Residual (°C)')
    axes[2].set_title(f'Segment 3 Residuals\nRMSE = {rmse3:.3f} °C')
    axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(images_dir, 'figure3_residuals.png'), dpi=150)
plt.close()
print("Saved: figure3_residuals.png")

# Figure 4: Comparison of full fit vs segmented fits
fig4, ax4 = plt.subplots(figsize=(12, 6))

# Plot observed data
ax4.plot(df['time_min'], df['temperature_c'], 'b-', linewidth=1.5, label='Observed', alpha=0.7)

# Plot full fit
if fit_full_success:
    t_fine = np.linspace(0, 199, 400)
    T_full_fine = newton_cooling(t_fine, *popt_full)
    ax4.plot(t_fine, T_full_fine, 'g--', linewidth=2, label=f'Full Fit (R²={r2_full:.3f})', alpha=0.7)

# Plot segmented fits
if fit1_success:
    t1_fine = np.linspace(0, 79, 100)
    T1_fine = newton_cooling(t1_fine, *popt1)
    ax4.plot(t1_fine, T1_fine, 'r-', linewidth=2, label='Segment 1 Fit')

if fit2_success:
    t2_fine = np.linspace(80, 120, 100)
    T2_fine = newton_cooling(t2_fine, *popt2)
    ax4.plot(t2_fine, T2_fine, 'r-', linewidth=2)

if fit3_success:
    t3_fine = np.linspace(121, 199, 100)
    T3_fine = newton_cooling(t3_fine, *popt3)
    ax4.plot(t3_fine, T3_fine, 'r-', linewidth=2, label='Segment Fits')

ax4.set_xlabel('Time (minutes)', fontsize=12)
ax4.set_ylabel('Temperature (°C)', fontsize=12)
ax4.set_title('Comparison: Full Dataset Fit vs Segmented Fits', fontsize=14)
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(images_dir, 'figure4_fit_comparison.png'), dpi=150)
plt.close()
print("Saved: figure4_fit_comparison.png")

# Figure 5: Cooling rate analysis
fig5, axes = plt.subplots(1, 2, figsize=(14, 5))

# Temperature difference (cooling rate proxy)
df['cooling_rate'] = -df['temp_diff']  # Positive = cooling
axes[0].plot(df['time_min'], df['cooling_rate'], 'purple', linewidth=1)
axes[0].set_xlabel('Time (minutes)')
axes[0].set_ylabel('Cooling Rate (°C/min)')
axes[0].set_title('Instantaneous Cooling Rate vs Time')
axes[0].grid(True, alpha=0.3)

# Temperature vs cooling rate (should be linear for Newton's Law)
axes[1].scatter(df['temperature_c'], df['cooling_rate'], c=df['time_min'], cmap='viridis', alpha=0.6, s=20)
axes[1].set_xlabel('Temperature (°C)')
axes[1].set_ylabel('Cooling Rate (°C/min)')
axes[1].set_title('Cooling Rate vs Temperature\n(Linear relationship expected for Newton\'s Law)')
axes[1].grid(True, alpha=0.3)
cbar = plt.colorbar(axes[1].collections[0], ax=axes[1])
cbar.set_label('Time (min)')

plt.tight_layout()
plt.savefig(os.path.join(images_dir, 'figure5_cooling_rate.png'), dpi=150)
plt.close()
print("Saved: figure5_cooling_rate.png")

# Figure 6: Model parameters comparison
fig6, ax6 = plt.subplots(figsize=(10, 6))

segments = ['Segment 1\n(0-79 min)', 'Segment 2\n(80-120 min)', 'Segment 3\n(121-199 min)']
k_values = [k1, k2, k3]
k_errors = [perr1[2], perr2[2], perr3[2]]

bars = ax6.bar(segments, k_values, yerr=k_errors, capsize=5, color=['#3498db', '#e74c3c', '#2ecc71'], alpha=0.7)
ax6.set_ylabel('Cooling Constant k (min⁻¹)', fontsize=12)
ax6.set_title('Comparison of Cooling Constants Across Segments', fontsize=14)
ax6.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, val, err in zip(bars, k_values, k_errors):
    ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + err + 0.001, 
             f'{val:.4f}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(images_dir, 'figure6_cooling_constants.png'), dpi=150)
plt.close()
print("Saved: figure6_cooling_constants.png")

# Save detailed results to file
with open(os.path.join(outputs_dir, 'fit_results.txt'), 'w') as f:
    f.write("Beverage Cooling Analysis Results\n")
    f.write("="*60 + "\n\n")
    
    f.write("SEGMENT 1 (Minutes 0-79)\n")
    f.write("-"*40 + "\n")
    if fit1_success:
        f.write(f"Newton's Law of Cooling: T(t) = T_env + (T0 - T_env) * exp(-k*t)\n")
        f.write(f"  T_env = {T_env1:.3f} ± {perr1[0]:.3f} °C\n")
        f.write(f"  T0 = {T0_fit1:.3f} ± {perr1[1]:.3f} °C\n")
        f.write(f"  k = {k1:.5f} ± {perr1[2]:.5f} min^-1\n")
        f.write(f"  Half-life = {np.log(2)/k1:.2f} minutes\n")
        f.write(f"  R-squared = {r2_1:.6f}\n")
        f.write(f"  RMSE = {rmse1:.4f} °C\n")
    f.write("\n")
    
    f.write("SEGMENT 2 (Minutes 80-120)\n")
    f.write("-"*40 + "\n")
    if fit2_success:
        f.write(f"Newton's Law of Cooling: T(t) = T_env + (T0 - T_env) * exp(-k*t)\n")
        f.write(f"  T_env = {T_env2:.3f} ± {perr2[0]:.3f} °C\n")
        f.write(f"  T0 = {T0_fit2:.3f} ± {perr2[1]:.3f} °C\n")
        f.write(f"  k = {k2:.5f} ± {perr2[2]:.5f} min^-1\n")
        f.write(f"  Half-life = {np.log(2)/k2:.2f} minutes\n")
        f.write(f"  R-squared = {r2_2:.6f}\n")
        f.write(f"  RMSE = {rmse2:.4f} °C\n")
    f.write("\n")
    
    f.write("SEGMENT 3 (Minutes 121-199)\n")
    f.write("-"*40 + "\n")
    if fit3_success:
        f.write(f"Newton's Law of Cooling: T(t) = T_env + (T0 - T_env) * exp(-k*t)\n")
        f.write(f"  T_env = {T_env3:.3f} ± {perr3[0]:.3f} °C\n")
        f.write(f"  T0 = {T0_fit3:.3f} ± {perr3[1]:.3f} °C\n")
        f.write(f"  k = {k3:.5f} ± {perr3[2]:.5f} min^-1\n")
        f.write(f"  Half-life = {np.log(2)/k3:.2f} minutes\n")
        f.write(f"  R-squared = {r2_3:.6f}\n")
        f.write(f"  RMSE = {rmse3:.4f} °C\n")
    f.write("\n")
    
    f.write("FULL DATASET FIT\n")
    f.write("-"*40 + "\n")
    if fit_full_success:
        f.write(f"Newton's Law of Cooling: T(t) = T_env + (T0 - T_env) * exp(-k*t)\n")
        f.write(f"  T_env = {T_env_full:.3f} ± {perr_full[0]:.3f} °C\n")
        f.write(f"  T0 = {T0_fit_full:.3f} ± {perr_full[1]:.3f} °C\n")
        f.write(f"  k = {k_full:.5f} ± {perr_full[2]:.5f} min^-1\n")
        f.write(f"  R-squared = {r2_full:.6f}\n")
        f.write(f"  RMSE = {rmse_full:.4f} °C\n")
    f.write("\n")
    
    f.write("DISCONTINUITIES DETECTED\n")
    f.write("-"*40 + "\n")
    f.write(f"Discontinuities at minutes: {discontinuities['time_min'].tolist()}\n")
    f.write(f"Temperature jumps: {discontinuities['temp_diff'].tolist()}\n")

print("\nAnalysis complete!")
print(f"Results saved to: {outputs_dir}")
print(f"Figures saved to: {images_dir}")
