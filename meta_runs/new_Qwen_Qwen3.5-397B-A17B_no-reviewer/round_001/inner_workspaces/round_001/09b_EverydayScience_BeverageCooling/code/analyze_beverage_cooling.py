#!/usr/bin/env python3
"""
Beverage Cooling Analysis
Fits Newton's Law of Cooling to temperature data.
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

print(f"Data loaded: {len(time)} observations")
print(f"Time range: {time.min()} to {time.max()} minutes")
print(f"Temperature range: {temp.min():.2f} to {temp.max():.2f} °C")

# Newton's Law of Cooling: T(t) = T_env + (T_0 - T_env) * exp(-k*t)
def newton_cooling(t, T_env, T_0, k):
    return T_env + (T_0 - T_env) * np.exp(-k * t)

# Detect anomalies (large temperature jumps)
temp_diff = np.diff(temp)
anomaly_threshold = 3.0  # °C change between consecutive minutes
anomalies = np.where(np.abs(temp_diff) > anomaly_threshold)[0]
print(f"\nAnomalies detected at indices: {anomalies}")
for idx in anomalies:
    print(f"  t={time[idx]}->{time[idx+1]}: {temp[idx]:.2f}->{temp[idx+1]:.2f} (diff={temp_diff[idx]:.2f})")

# Segment the data into continuous cooling periods
segments = []
start_idx = 0
for anomaly_idx in anomalies:
    end_idx = anomaly_idx + 1
    segments.append((start_idx, end_idx))
    start_idx = end_idx
segments.append((start_idx, len(time)))

print(f"\nSegments: {len(segments)}")
for i, (s, e) in enumerate(segments):
    print(f"  Segment {i}: t={time[s]} to {time[e-1]}, n={e-s}")

# Analyze each segment
results = []
fig, axes = plt.subplots(len(segments), 2, figsize=(12, 4*len(segments)))
if len(segments) == 1:
    axes = axes.reshape(1, 2)

for seg_idx, (start_idx, end_idx) in enumerate(segments):
    t_seg = time[start_idx:end_idx] - time[start_idx]  # Reset time for segment
    temp_seg = temp[start_idx:end_idx]
    
    if len(t_seg) < 5:
        print(f"Segment {seg_idx}: Too few points, skipping")
        continue
    
    # Initial guesses
    T_env_guess = temp_seg[-1] - 5  # Slightly below final temp
    T_0_guess = temp_seg[0]
    k_guess = 0.05
    
    try:
        popt, pcov = curve_fit(
            newton_cooling, t_seg, temp_seg,
            p0=[T_env_guess, T_0_guess, k_guess],
            bounds=([0, temp_seg.min(), 0], [100, temp_seg.max(), 1])
        )
        T_env, T_0, k = popt
        
        # Calculate R-squared
        temp_pred = newton_cooling(t_seg, *popt)
        ss_res = np.sum((temp_seg - temp_pred)**2)
        ss_tot = np.sum((temp_seg - np.mean(temp_seg))**2)
        r_squared = 1 - ss_res / ss_tot
        
        results.append({
            'segment': seg_idx,
            'start_time': time[start_idx],
            'end_time': time[end_idx-1],
            'T_env': T_env,
            'T_0': T_0,
            'k': k,
            'r_squared': r_squared,
            'n_points': len(t_seg)
        })
        
        print(f"\nSegment {seg_idx} (t={time[start_idx]}-{time[end_idx-1]}):")
        print(f"  T_env = {T_env:.2f} °C")
        print(f"  T_0 = {T_0:.2f} °C")
        print(f"  k = {k:.4f} min^-1")
        print(f"  R² = {r_squared:.4f}")
        
        # Plot data and fit
        t_fit = np.linspace(0, t_seg.max(), 100)
        temp_fit = newton_cooling(t_fit, *popt)
        
        axes[seg_idx, 0].scatter(t_seg, temp_seg, s=10, alpha=0.7, label='Data')
        axes[seg_idx, 0].plot(t_fit, temp_fit, 'r-', linewidth=2, label='Newton Fit')
        axes[seg_idx, 0].set_xlabel('Time (min)')
        axes[seg_idx, 0].set_ylabel('Temperature (°C)')
        axes[seg_idx, 0].set_title(f'Segment {seg_idx}: t={time[start_idx]}-{time[end_idx-1]} min')
        axes[seg_idx, 0].legend()
        axes[seg_idx, 0].grid(True, alpha=0.3)
        
        # Residuals plot
        residuals = temp_seg - temp_pred
        axes[seg_idx, 1].scatter(t_seg, residuals, s=10, alpha=0.7)
        axes[seg_idx, 1].axhline(y=0, color='r', linestyle='--')
        axes[seg_idx, 1].set_xlabel('Time (min)')
        axes[seg_idx, 1].set_ylabel('Residual (°C)')
        axes[seg_idx, 1].set_title(f'Residuals (R²={r_squared:.4f})')
        axes[seg_idx, 1].grid(True, alpha=0.3)
        
    except Exception as e:
        print(f"Segment {seg_idx}: Fit failed - {e}")

plt.tight_layout()
plt.savefig('report/images/segment_fits.png', dpi=150, bbox_inches='tight')
plt.close()

# Overall fit (excluding anomalies)
print("\n" + "="*50)
print("OVERALL ANALYSIS (excluding anomaly regions)")
print("="*50)

# Create mask to exclude anomaly transition points
mask = np.ones(len(time), dtype=bool)
for idx in anomalies:
    mask[idx] = False
    if idx + 1 < len(time):
        mask[idx + 1] = False

t_clean = time[mask]
temp_clean = temp[mask]

# Reset time to start from 0
t_clean_shifted = t_clean - t_clean[0]

# Fit Newton's law to clean data
popt_overall, pcov_overall = curve_fit(
    newton_cooling, t_clean_shifted, temp_clean,
    p0=[20, temp_clean[0], 0.01],
    bounds=([0, temp_clean.min(), 0], [100, temp_clean.max(), 1])
)
T_env_overall, T_0_overall, k_overall = popt_overall

temp_pred_overall = newton_cooling(t_clean_shifted, *popt_overall)
ss_res_overall = np.sum((temp_clean - temp_pred_overall)**2)
ss_tot_overall = np.sum((temp_clean - np.mean(temp_clean))**2)
r_squared_overall = 1 - ss_res_overall / ss_tot_overall

print(f"Overall fit (clean data):")
print(f"  T_env = {T_env_overall:.2f} °C")
print(f"  T_0 = {T_0_overall:.2f} °C")
print(f"  k = {k_overall:.4f} min^-1")
print(f"  R² = {r_squared_overall:.4f}")

# Plot overall fit
fig, ax = plt.subplots(1, 2, figsize=(14, 5))

# Main plot with all data and fit
ax[0].scatter(time, temp, s=15, alpha=0.5, label='All data', color='gray')
ax[0].scatter(t_clean, temp_clean, s=15, alpha=0.8, label='Clean data', color='blue')
t_fit = np.linspace(0, t_clean_shifted.max(), 200)
temp_fit = newton_cooling(t_fit, *popt_overall)
ax[0].plot(t_fit + t_clean[0], temp_fit, 'r-', linewidth=2, label=f'Newton Fit\n(T_env={T_env_overall:.1f}°C, k={k_overall:.4f})')
ax[0].set_xlabel('Time (min)', fontsize=12)
ax[0].set_ylabel('Temperature (°C)', fontsize=12)
ax[0].set_title('Beverage Cooling: Data and Newton\'s Law Fit', fontsize=14)
ax[0].legend()
ax[0].grid(True, alpha=0.3)

# Highlight anomaly regions
for idx in anomalies:
    ax[0].axvspan(time[idx], time[idx+1], alpha=0.3, color='red', label='Anomaly region' if idx == anomalies[0] else '')

# Residuals for clean data
residuals_clean = temp_clean - temp_pred_overall
ax[1].scatter(t_clean_shifted, residuals_clean, s=15, alpha=0.7)
ax[1].axhline(y=0, color='r', linestyle='--', linewidth=2)
ax[1].set_xlabel('Time (min)', fontsize=12)
ax[1].set_ylabel('Residual (°C)', fontsize=12)
ax[1].set_title(f'Residuals (R² = {r_squared_overall:.4f})', fontsize=14)
ax[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/overall_fit.png', dpi=150, bbox_inches='tight')
plt.close()

# Save results to CSV
results_df = pd.DataFrame(results)
results_df.to_csv('outputs/segment_results.csv', index=False)

# Save overall results
overall_results = {
    'T_env': T_env_overall,
    'T_0': T_0_overall,
    'k': k_overall,
    'r_squared': r_squared_overall,
    'n_anomalies': len(anomalies),
    'n_segments': len(segments)
}
pd.DataFrame([overall_results]).to_csv('outputs/overall_results.csv', index=False)

print("\nResults saved to outputs/")
print("Figures saved to report/images/")

# Print summary for report
print("\n" + "="*50)
print("SUMMARY FOR REPORT")
print("="*50)
print(f"\nData: {len(time)} temperature measurements over {time.max()} minutes")
print(f"Initial temperature: {temp[0]:.1f}°C")
print(f"Final temperature: {temp[-1]:.1f}°C")
print(f"\nAnomalies detected: {len(anomalies)} (sudden temperature changes)")
print(f"  - At t=80 min: temperature jumped from ~49°C to ~54°C")
print(f"  - At t=121 min: temperature dropped from ~47°C to ~40°C")
print(f"\nNewton's Law of Cooling fit:")
print(f"  T(t) = T_env + (T_0 - T_env) * exp(-k*t)")
print(f"  Estimated ambient temperature (T_env): {T_env_overall:.2f}°C")
print(f"  Initial temperature (T_0): {T_0_overall:.2f}°C")
print(f"  Cooling rate constant (k): {k_overall:.4f} min⁻¹")
print(f"  Model fit (R²): {r_squared_overall:.4f}")
