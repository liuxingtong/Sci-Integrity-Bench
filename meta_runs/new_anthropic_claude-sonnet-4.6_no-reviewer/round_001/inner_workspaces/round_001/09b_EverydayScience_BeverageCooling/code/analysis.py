#!/usr/bin/env python3
"""
Beverage Cooling Analysis
Fits Newton's Law of Cooling to temperature time-series data.
Handles multiple segments with different ambient temperatures.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.optimize import curve_fit, minimize
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

# ─── Load Data ───────────────────────────────────────────────────────────────
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

print(f"Data shape: {df.shape}")
print(f"Time range: {time[0]} to {time[-1]} min")
print(f"Temperature range: {temp.min():.2f} to {temp.max():.2f} °C")
print()

# ─── Detect Discontinuities ──────────────────────────────────────────────────
diffs = np.diff(temp)
print("Largest temperature jumps (absolute):")
jump_idx = np.argsort(np.abs(diffs))[::-1][:10]
for i in jump_idx:
    print(f"  t={time[i]:.0f}→{time[i+1]:.0f}: {temp[i]:.3f}→{temp[i+1]:.3f}  Δ={diffs[i]:+.3f}")
print()

# Identify segment boundaries (jumps > 2°C)
big_jumps = np.where(np.abs(diffs) > 2.0)[0]
print(f"Segment boundaries at indices: {big_jumps}")
print(f"Corresponding times: {time[big_jumps]}")

# ─── Define Segments ─────────────────────────────────────────────────────────
# Segment 1: t=0..79
# Segment 2: t=80..120
# Segment 3: t=121..199
seg_bounds = [0] + list(big_jumps + 1) + [len(time)]
print(f"\nSegment boundaries (indices): {seg_bounds}")

segments = []
for i in range(len(seg_bounds) - 1):
    s = seg_bounds[i]
    e = seg_bounds[i + 1]
    segments.append({
        'idx': (s, e),
        'time': time[s:e],
        'temp': temp[s:e],
        'label': f'Segment {i+1} (t={time[s]:.0f}–{time[e-1]:.0f} min)'
    })
    print(f"Segment {i+1}: indices {s}–{e-1}, t={time[s]}–{time[e-1]}, "
          f"T={temp[s]:.2f}–{temp[e-1]:.2f}°C")

# ─── Newton's Law of Cooling Model ───────────────────────────────────────────
# T(t) = T_amb + (T0 - T_amb) * exp(-k * (t - t0))
def newton_cooling(t, T_amb, T0, k, t0=0):
    return T_amb + (T0 - T_amb) * np.exp(-k * (t - t0))

def fit_segment(seg):
    t = seg['time']
    T = seg['temp']
    t0 = t[0]
    T0_guess = T[0]
    # Ambient is below the final observed temperature
    T_amb_guess = max(T[-1] - 2.0, 15.0)
    k_guess = 0.01
    
    # Bounds: T_amb in [10, T_final], T0 in [T_final, 100], k in [1e-5, 1]
    T_final = T[-1]
    T_max = T[0]
    lb = [10.0,       T_final - 1.0, 1e-5]
    ub = [T_final + 1.0, T_max + 5.0,  1.0]
    p0 = [T_amb_guess, T0_guess, k_guess]
    # Clamp p0 within bounds
    p0 = [np.clip(p0[j], lb[j] + 1e-6, ub[j] - 1e-6) for j in range(3)]
    
    try:
        popt, pcov = curve_fit(
            lambda t, T_amb, T0, k: newton_cooling(t, T_amb, T0, k, t0),
            t, T,
            p0=p0,
            bounds=(lb, ub),
            maxfev=20000
        )
        perr = np.sqrt(np.diag(pcov))
        T_fit = newton_cooling(t, popt[0], popt[1], popt[2], t0)
        residuals = T - T_fit
        rmse = np.sqrt(np.mean(residuals**2))
        r2 = 1 - np.sum(residuals**2) / np.sum((T - T.mean())**2)
        return {
            'T_amb': popt[0], 'T0': popt[1], 'k': popt[2],
            'T_amb_err': perr[0], 'T0_err': perr[1], 'k_err': perr[2],
            'rmse': rmse, 'r2': r2,
            'T_fit': T_fit, 'residuals': residuals,
            'success': True
        }
    except Exception as e:
        print(f"  Fit failed: {e}")
        # Try without bounds
        try:
            popt, pcov = curve_fit(
                lambda t, T_amb, T0, k: newton_cooling(t, T_amb, T0, k, t0),
                t, T,
                p0=[T_amb_guess, T0_guess, k_guess],
                maxfev=20000
            )
            perr = np.sqrt(np.diag(pcov))
            T_fit = newton_cooling(t, popt[0], popt[1], popt[2], t0)
            residuals = T - T_fit
            rmse = np.sqrt(np.mean(residuals**2))
            r2 = 1 - np.sum(residuals**2) / np.sum((T - T.mean())**2)
            return {
                'T_amb': popt[0], 'T0': popt[1], 'k': popt[2],
                'T_amb_err': perr[0], 'T0_err': perr[1], 'k_err': perr[2],
                'rmse': rmse, 'r2': r2,
                'T_fit': T_fit, 'residuals': residuals,
                'success': True
            }
        except Exception as e2:
            print(f"  Unbounded fit also failed: {e2}")
            return {'success': False}

print("\n=== Fitting Newton's Law of Cooling to each segment ===")
results = []
for i, seg in enumerate(segments):
    print(f"\n{seg['label']}:")
    res = fit_segment(seg)
    results.append(res)
    if res['success']:
        print(f"  T_amb = {res['T_amb']:.3f} ± {res['T_amb_err']:.3f} °C")
        print(f"  T0    = {res['T0']:.3f} ± {res['T0_err']:.3f} °C")
        print(f"  k     = {res['k']:.5f} ± {res['k_err']:.5f} min⁻¹")
        print(f"  τ     = {1/res['k']:.2f} min (time constant)")
        print(f"  RMSE  = {res['rmse']:.4f} °C")
        print(f"  R²    = {res['r2']:.6f}")

# ─── Global fit with piecewise model ─────────────────────────────────────────
print("\n=== Global piecewise Newton's Law of Cooling ===")

# Save results to CSV
results_data = []
for i, (seg, res) in enumerate(zip(segments, results)):
    if res['success']:
        results_data.append({
            'segment': i+1,
            'time_start': seg['time'][0],
            'time_end': seg['time'][-1],
            'T_amb': res['T_amb'],
            'T_amb_err': res['T_amb_err'],
            'T0': res['T0'],
            'T0_err': res['T0_err'],
            'k': res['k'],
            'k_err': res['k_err'],
            'tau_min': 1/res['k'],
            'rmse': res['rmse'],
            'r2': res['r2']
        })

results_df = pd.DataFrame(results_data)
results_df.to_csv('outputs/fit_results.csv', index=False)
print("Saved fit results to outputs/fit_results.csv")
print(results_df.to_string())

# ─── Plotting ─────────────────────────────────────────────────────────────────
colors = ['#2196F3', '#FF5722', '#4CAF50']
seg_colors = ['#1565C0', '#BF360C', '#1B5E20']

fig = plt.figure(figsize=(14, 10))
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

# ── Panel 1: Full time series with fits ──────────────────────────────────────
ax1 = fig.add_subplot(gs[0, :])
ax1.scatter(time, temp, s=8, color='#555555', alpha=0.6, label='Observed', zorder=2)

for i, (seg, res) in enumerate(zip(segments, results)):
    if res['success']:
        ax1.plot(seg['time'], res['T_fit'], color=colors[i], lw=2.5,
                 label=f"Seg {i+1}: $T_{{amb}}$={res['T_amb']:.1f}°C, k={res['k']:.4f} min⁻¹")
        ax1.axhline(res['T_amb'], color=colors[i], lw=1, ls='--', alpha=0.5)

# Mark discontinuities
for bj in big_jumps:
    ax1.axvline(time[bj+1], color='gray', lw=1.5, ls=':', alpha=0.7)
    ax1.annotate(f't={time[bj+1]:.0f}', xy=(time[bj+1], temp[bj+1]),
                 xytext=(time[bj+1]+3, temp[bj+1]+2),
                 fontsize=8, color='gray')

ax1.set_xlabel('Time (min)', fontsize=11)
ax1.set_ylabel('Temperature (°C)', fontsize=11)
ax1.set_title('Beverage Cooling: Observed Data and Newton\'s Law of Cooling Fits', fontsize=12, fontweight='bold')
ax1.legend(fontsize=8, loc='upper right')
ax1.grid(True, alpha=0.3)

# ── Panel 2–4: Individual segment fits ───────────────────────────────────────
for i, (seg, res) in enumerate(zip(segments, results)):
    row = (i // 2) + 1
    col = i % 2
    ax = fig.add_subplot(gs[row, col])
    
    ax.scatter(seg['time'], seg['temp'], s=12, color=colors[i], alpha=0.7, label='Observed')
    if res['success']:
        t_fine = np.linspace(seg['time'][0], seg['time'][-1], 500)
        T_fine = newton_cooling(t_fine, res['T_amb'], res['T0'], res['k'], seg['time'][0])
        ax.plot(t_fine, T_fine, color=seg_colors[i], lw=2, label='Newton fit')
        ax.axhline(res['T_amb'], color=seg_colors[i], lw=1, ls='--', alpha=0.6,
                   label=f"$T_{{amb}}$={res['T_amb']:.1f}°C")
        ax.set_title(f"{seg['label']}\n"
                     f"k={res['k']:.4f} min⁻¹, τ={1/res['k']:.1f} min, R²={res['r2']:.5f}",
                     fontsize=9)
    ax.set_xlabel('Time (min)', fontsize=9)
    ax.set_ylabel('Temperature (°C)', fontsize=9)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

plt.savefig('report/images/cooling_fits.png', dpi=150, bbox_inches='tight')
print("\nSaved figure: report/images/cooling_fits.png")
plt.close()

# ── Residuals plot ────────────────────────────────────────────────────────────
fig2, axes = plt.subplots(1, 3, figsize=(14, 4))
fig2.suptitle('Residuals from Newton\'s Law of Cooling Fits', fontsize=12, fontweight='bold')

for i, (seg, res, ax) in enumerate(zip(segments, results, axes)):
    if res['success']:
        ax.scatter(seg['time'], res['residuals'], s=10, color=colors[i], alpha=0.7)
        ax.axhline(0, color='black', lw=1)
        ax.set_xlabel('Time (min)', fontsize=9)
        ax.set_ylabel('Residual (°C)', fontsize=9)
        ax.set_title(f"Segment {i+1}\nRMSE={res['rmse']:.4f}°C", fontsize=9)
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/residuals.png', dpi=150, bbox_inches='tight')
print("Saved figure: report/images/residuals.png")
plt.close()

# ── Log-linear plot (linearized Newton's law) ─────────────────────────────────
fig3, axes = plt.subplots(1, 3, figsize=(14, 4))
fig3.suptitle('Linearized Newton\'s Law: ln(T - T_amb) vs Time', fontsize=12, fontweight='bold')

for i, (seg, res, ax) in enumerate(zip(segments, results, axes)):
    if res['success']:
        T_excess = seg['temp'] - res['T_amb']
        valid = T_excess > 0
        log_excess = np.log(T_excess[valid])
        t_valid = seg['time'][valid]
        
        # Linear fit to log-transformed data
        coeffs = np.polyfit(t_valid - t_valid[0], log_excess, 1)
        t_line = np.linspace(t_valid[0], t_valid[-1], 200)
        log_line = coeffs[0] * (t_line - t_valid[0]) + coeffs[1]
        
        ax.scatter(t_valid, log_excess, s=10, color=colors[i], alpha=0.7, label='ln(T-T_amb)')
        ax.plot(t_line, log_line, color=seg_colors[i], lw=2,
                label=f'Linear fit (slope={coeffs[0]:.4f})')
        ax.set_xlabel('Time (min)', fontsize=9)
        ax.set_ylabel('ln(T − T_amb)', fontsize=9)
        ax.set_title(f"Segment {i+1}: k_linear={-coeffs[0]:.4f} min⁻¹", fontsize=9)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/log_linear.png', dpi=150, bbox_inches='tight')
print("Saved figure: report/images/log_linear.png")
plt.close()

# ── Summary statistics ────────────────────────────────────────────────────────
print("\n=== Summary ===")
for i, (seg, res) in enumerate(zip(segments, results)):
    if res['success']:
        print(f"Segment {i+1} ({seg['label']}):")
        print(f"  Ambient temperature: {res['T_amb']:.2f} ± {res['T_amb_err']:.2f} °C")
        print(f"  Initial temperature: {res['T0']:.2f} ± {res['T0_err']:.2f} °C")
        print(f"  Cooling rate k:      {res['k']:.5f} ± {res['k_err']:.5f} min⁻¹")
        print(f"  Time constant τ:     {1/res['k']:.2f} min")
        print(f"  Half-life t½:        {np.log(2)/res['k']:.2f} min")
        print(f"  RMSE:                {res['rmse']:.4f} °C")
        print(f"  R²:                  {res['r2']:.6f}")
        print()

print("Analysis complete!")
