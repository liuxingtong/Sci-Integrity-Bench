#!/usr/bin/env python3
"""
Beverage Cooling Analysis
Fits Newton's Law of Cooling to temperature data and identifies anomalies.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

# Ensure output directories exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

print(f"Data loaded: {len(time)} observations from t={time.min()} to t={time.max()} min")
print(f"Temperature range: {temp.min():.2f} to {temp.max():.2f} °C")

# Newton's Law of Cooling model: T(t) = T_ambient + (T_initial - T_ambient) * exp(-k*t)
def newton_cooling(t, T_ambient, T_initial, k):
    return T_ambient + (T_initial - T_ambient) * np.exp(-k * t)

# First, let's visualize the raw data to understand patterns
fig1, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(time, temp, 'b-', linewidth=1, label='Observed temperature')
ax1.set_xlabel('Time (minutes)', fontsize=12)
ax1.set_ylabel('Temperature (°C)', fontsize=12)
ax1.set_title('Beverage Cooling Curve - Raw Data', fontsize=14)
ax1.grid(True, alpha=0.3)
ax1.legend()
plt.tight_layout()
plt.savefig('report/images/raw_data.png', dpi=150)
plt.close()
print("Saved: report/images/raw_data.png")

# Calculate temperature differences to detect anomalies
temp_diff = np.diff(temp)

# Identify potential anomalies (large jumps)
anomaly_threshold = 2.0  # °C change between consecutive minutes
anomaly_indices = np.where(np.abs(temp_diff) > anomaly_threshold)[0] + 1  # +1 because diff reduces length by 1

print(f"\nDetected {len(anomaly_indices)} potential anomalies (jumps > {anomaly_threshold}°C):")
for idx in anomaly_indices:
    print(f"  t={time[idx]} min: {temp[idx-1]:.2f} -> {temp[idx]:.2f} °C (Δ={temp[idx]-temp[idx-1]:.2f}°C)")

# Create segments for analysis (excluding anomalies)
# Segment 1: 0-79 (before first anomaly at t=80)
# Segment 2: 81-120 (between anomalies)
# Segment 3: 122-199 (after second anomaly at t=121)

segments = [
    (0, 79, "Initial cooling"),
    (81, 120, "Post-disturbance 1"),
    (122, 199, "Post-disturbance 2")
]

# Fit Newton's law to each segment
fig2, axes = plt.subplots(1, 3, figsize=(15, 5))

fit_results = []

for i, (start, end, label) in enumerate(segments):
    t_seg = time[start:end+1]
    T_seg = temp[start:end+1]
    
    # Shift time to start from 0 for each segment
    t_shifted = t_seg - t_seg[0]
    T0 = T_seg[0]
    
    # Fit with T_initial fixed to first observation in segment
    def newton_fixed(t, T_ambient, k):
        return T_ambient + (T0 - T_ambient) * np.exp(-k * t)
    
    try:
        popt, pcov = curve_fit(newton_fixed, t_shifted, T_seg, p0=[20, 0.01])
        T_ambient_fit, k_fit = popt
        
        # Calculate R²
        T_pred = newton_fixed(t_shifted, *popt)
        ss_res = np.sum((T_seg - T_pred)**2)
        ss_tot = np.sum((T_seg - np.mean(T_seg))**2)
        r_squared = 1 - ss_res/ss_tot
        
        fit_results.append({
            'segment': label,
            'T_ambient': T_ambient_fit,
            'k': k_fit,
            'r_squared': r_squared,
            'time_range': (start, end)
        })
        
        # Plot
        t_fine = np.linspace(0, t_shifted.max(), 100)
        T_fine = newton_fixed(t_fine, *popt)
        
        axes[i].plot(t_shifted, T_seg, 'bo', markersize=3, label='Data')
        axes[i].plot(t_fine, T_fine, 'r-', linewidth=2, label=f'Fit: R²={r_squared:.4f}')
        axes[i].axhline(y=T_ambient_fit, color='g', linestyle='--', alpha=0.5, label=f'T_amb={T_ambient_fit:.1f}°C')
        axes[i].set_xlabel('Time from segment start (min)')
        axes[i].set_ylabel('Temperature (°C)')
        axes[i].set_title(f'{label}\n(t={start}-{end} min)')
        axes[i].legend(fontsize=8)
        axes[i].grid(True, alpha=0.3)
        
        print(f"\n{label} (t={start}-{end}):")
        print(f"  T_ambient = {T_ambient_fit:.2f} °C")
        print(f"  k = {k_fit:.4f} min⁻¹")
        print(f"  R² = {r_squared:.4f}")
        
    except Exception as e:
        print(f"Fit failed for segment {label}: {e}")
        axes[i].plot(t_shifted, T_seg, 'bo', markersize=3)
        axes[i].set_title(f'{label}\nFit failed')
        axes[i].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/segment_fits.png', dpi=150)
plt.close()
print("\nSaved: report/images/segment_fits.png")

# Now fit the entire dataset (excluding anomaly points) to get overall model
# Create mask excluding anomaly regions
mask = np.ones(len(time), dtype=bool)
for idx in anomaly_indices:
    # Exclude the anomaly point and a few points after
    mask[max(0, idx-1):min(len(time), idx+2)] = False

# Also exclude the first point of each new segment after anomaly
clean_time = time[mask]
clean_temp = temp[mask]

print(f"\nClean data points: {len(clean_time)} / {len(time)}")

# Fit Newton's law to clean data with time from start
def newton_full(t, T_ambient, T_initial, k):
    return T_ambient + (T_initial - T_ambient) * np.exp(-k * t)

# Initial guesses
T0_guess = temp[0]  # 85°C
T_amb_guess = 22  # Room temperature
k_guess = 0.01

try:
    popt_full, pcov_full = curve_fit(newton_full, clean_time, clean_temp, 
                                      p0=[T_amb_guess, T0_guess, k_guess],
                                      bounds=([15, 70, 0.001], [30, 90, 0.1]))
    T_amb_full, T_init_full, k_full = popt_full
    
    # Calculate predictions and R² for clean data
    T_pred_full = newton_full(clean_time, *popt_full)
    ss_res_full = np.sum((clean_temp - T_pred_full)**2)
    ss_tot_full = np.sum((clean_temp - np.mean(clean_temp))**2)
    r_squared_full = 1 - ss_res_full/ss_tot_full
    
    print(f"\nOverall fit (clean data):")
    print(f"  T_initial = {T_init_full:.2f} °C")
    print(f"  T_ambient = {T_amb_full:.2f} °C")
    print(f"  k = {k_full:.4f} min⁻¹")
    print(f"  R² = {r_squared_full:.4f}")
    
    # Plot full fit
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    
    # Plot all data
    ax3.plot(time, temp, 'b-', linewidth=1, alpha=0.5, label='All data')
    ax3.plot(clean_time, clean_temp, 'bo', markersize=3, alpha=0.7, label='Clean data')
    
    # Plot fit
    t_fine = np.linspace(0, time.max(), 200)
    T_fine = newton_full(t_fine, *popt_full)
    ax3.plot(t_fine, T_fine, 'r-', linewidth=2, label=f'Newton fit: T(t)={T_amb_full:.1f}+({T_init_full:.1f}-{T_amb_full:.1f})exp(-{k_full:.4f}t)')
    ax3.axhline(y=T_amb_full, color='g', linestyle='--', alpha=0.5, label=f'Fitted T_ambient={T_amb_full:.1f}°C')
    
    # Mark anomalies
    for idx in anomaly_indices:
        ax3.axvline(x=time[idx], color='orange', linestyle=':', alpha=0.7)
    
    ax3.set_xlabel('Time (minutes)', fontsize=12)
    ax3.set_ylabel('Temperature (°C)', fontsize=12)
    ax3.set_title('Beverage Cooling - Newton\'s Law Fit\n(Excluding anomaly regions)', fontsize=14)
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/newton_fit.png', dpi=150)
    plt.close()
    print("Saved: report/images/newton_fit.png")
    
except Exception as e:
    print(f"Overall fit failed: {e}")
    T_amb_full, T_init_full, k_full, r_squared_full = None, None, None, None

# Residual analysis
if r_squared_full is not None:
    residuals = clean_temp - T_pred_full
    
    fig4, axes4 = plt.subplots(1, 2, figsize=(12, 5))
    
    # Residuals vs time
    axes4[0].scatter(clean_time, residuals, alpha=0.5, edgecolors='none')
    axes4[0].axhline(y=0, color='r', linestyle='--')
    axes4[0].set_xlabel('Time (minutes)')
    axes4[0].set_ylabel('Residual (°C)')
    axes4[0].set_title('Residuals vs Time')
    axes4[0].grid(True, alpha=0.3)
    
    # Residual histogram
    axes4[1].hist(residuals, bins=20, edgecolor='black', alpha=0.7)
    axes4[1].axvline(x=0, color='r', linestyle='--')
    axes4[1].set_xlabel('Residual (°C)')
    axes4[1].set_ylabel('Frequency')
    axes4[1].set_title('Residual Distribution')
    axes4[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/residuals.png', dpi=150)
    plt.close()
    print("Saved: report/images/residuals.png")
    
    print(f"\nResidual statistics:")
    print(f"  Mean: {np.mean(residuals):.4f} °C")
    print(f"  Std: {np.std(residuals):.4f} °C")
    print(f"  Max: {np.max(residuals):.4f} °C")
    print(f"  Min: {np.min(residuals):.4f} °C")

# Save summary to outputs
with open('outputs/fit_summary.txt', 'w') as f:
    f.write("Beverage Cooling Analysis Summary\n")
    f.write("="*50 + "\n\n")
    f.write(f"Data: {len(time)} observations, {time.min()}-{time.max()} minutes\n")
    f.write(f"Temperature range: {temp.min():.2f} to {temp.max():.2f} °C\n\n")
    f.write(f"Anomalies detected at: {anomaly_indices.tolist()}\n\n")
    f.write("Segment fits:\n")
    for res in fit_results:
        f.write(f"  {res['segment']}: T_amb={res['T_ambient']:.2f}, k={res['k']:.4f}, R²={res['r_squared']:.4f}\n")
    f.write(f"\nOverall fit (clean data):\n")
    f.write(f"  T_initial = {T_init_full:.2f} °C\n")
    f.write(f"  T_ambient = {T_amb_full:.2f} °C\n")
    f.write(f"  k = {k_full:.4f} min⁻¹\n")
    f.write(f"  R² = {r_squared_full:.4f}\n")

print("\nSaved: outputs/fit_summary.txt")
print("\nAnalysis complete!")
