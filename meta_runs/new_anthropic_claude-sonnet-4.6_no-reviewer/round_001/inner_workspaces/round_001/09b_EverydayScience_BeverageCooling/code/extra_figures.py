#!/usr/bin/env python3
"""
Extra figures for the beverage cooling report.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings('ignore')

# ─── Load Data ───────────────────────────────────────────────────────────────
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

# ─── Model ───────────────────────────────────────────────────────────────────
def newton_cooling(t, T_amb, T0, k, t0=0):
    return T_amb + (T0 - T_amb) * np.exp(-k * (t - t0))

# Fitted parameters (from analysis.py)
params = [
    {'T_amb': 25.002, 'T0': 85.000, 'k': 0.011553, 't0': 0,   'end': 79,  'color': '#2196F3', 'label': 'Segment 1 (t=0–79 min)\nT_amb=25°C'},
    {'T_amb': 34.000, 'T0': 54.239, 'k': 0.011553, 't0': 80,  'end': 120, 'color': '#FF5722', 'label': 'Segment 2 (t=80–120 min)\nT_amb=34°C'},
    {'T_amb': 25.000, 'T0': 39.828, 'k': 0.011553, 't0': 121, 'end': 199, 'color': '#4CAF50', 'label': 'Segment 3 (t=121–199 min)\nT_amb=25°C'},
]

# ─── Figure 1: Annotated overview ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))

# Background shading for segments
bg_colors = ['#E3F2FD', '#FBE9E7', '#E8F5E9']
seg_ranges = [(0, 79), (80, 120), (121, 199)]
for (t_s, t_e), bg in zip(seg_ranges, bg_colors):
    ax.axvspan(t_s, t_e, alpha=0.3, color=bg)

# Data points
ax.scatter(time, temp, s=6, color='#333333', alpha=0.5, zorder=3, label='Observed data')

# Fitted curves
for p in params:
    t_seg = np.linspace(p['t0'], p['end'], 500)
    T_seg = newton_cooling(t_seg, p['T_amb'], p['T0'], p['k'], p['t0'])
    ax.plot(t_seg, T_seg, color=p['color'], lw=2.5, zorder=4)
    # Ambient line
    ax.hlines(p['T_amb'], p['t0'], p['end'], colors=p['color'], lw=1.2,
              linestyles='--', alpha=0.7)

# Annotations for ambient temperatures
ax.annotate('$T_{amb}$ = 25°C', xy=(40, 25.5), fontsize=10, color='#1565C0',
            ha='center')
ax.annotate('$T_{amb}$ = 34°C', xy=(100, 34.5), fontsize=10, color='#BF360C',
            ha='center')
ax.annotate('$T_{amb}$ = 25°C', xy=(160, 25.5), fontsize=10, color='#1B5E20',
            ha='center')

# Discontinuity annotations
ax.annotate('', xy=(80, 54.24), xytext=(79, 49.09),
            arrowprops=dict(arrowstyle='->', color='#FF5722', lw=2))
ax.text(81, 51.5, 'Moved to\nwarmer env.\n(+5.2°C jump)', fontsize=8,
        color='#BF360C', va='center')

ax.annotate('', xy=(121, 39.83), xytext=(120, 46.75),
            arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=2))
ax.text(122, 43.0, 'Moved to\ncooler env.\n(−6.9°C jump)', fontsize=8,
        color='#1B5E20', va='center')

# Legend
patches = [
    mpatches.Patch(color='#2196F3', label='Seg 1: T₀=85°C, T_amb=25°C'),
    mpatches.Patch(color='#FF5722', label='Seg 2: T₀=54.2°C, T_amb=34°C'),
    mpatches.Patch(color='#4CAF50', label='Seg 3: T₀=39.8°C, T_amb=25°C'),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#333333',
               markersize=5, label='Observed data'),
]
ax.legend(handles=patches, fontsize=9, loc='upper right')

ax.set_xlabel('Time (min)', fontsize=12)
ax.set_ylabel('Temperature (°C)', fontsize=12)
ax.set_title("Beverage Cooling: Piecewise Newton's Law of Cooling\n"
             r"$T(t) = T_{amb} + (T_0 - T_{amb})\,e^{-k(t-t_0)}$, "
             r"$k = 0.01155\,\mathrm{min}^{-1}$ (all segments)",
             fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.set_xlim(-2, 202)
ax.set_ylim(20, 92)

plt.tight_layout()
plt.savefig('report/images/overview_annotated.png', dpi=150, bbox_inches='tight')
print("Saved: report/images/overview_annotated.png")
plt.close()

# ─── Figure 2: Exponential decay visualization ────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Newton's Law of Cooling: Exponential Decay Analysis", fontsize=12, fontweight='bold')

# Left: T(t) - T_amb vs time (should be exponential)
ax = axes[0]
for p in params:
    t_seg = np.array([t for t in time if p['t0'] <= t <= p['end']])
    T_seg = np.array([temp[i] for i, t in enumerate(time) if p['t0'] <= t <= p['end']])
    excess = T_seg - p['T_amb']
    ax.plot(t_seg - p['t0'], excess, 'o', markersize=4, color=p['color'],
            alpha=0.6, label=p['label'].split('\n')[0])
    # Theoretical
    t_fine = np.linspace(0, p['end'] - p['t0'], 300)
    ax.plot(t_fine, (p['T0'] - p['T_amb']) * np.exp(-p['k'] * t_fine),
            color=p['color'], lw=2, alpha=0.8)

ax.set_xlabel('Time since segment start (min)', fontsize=11)
ax.set_ylabel('T(t) − T_amb (°C)', fontsize=11)
ax.set_title('Temperature Excess vs Time\n(exponential decay)', fontsize=10)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Right: log(T - T_amb) vs time (should be linear)
ax = axes[1]
for p in params:
    t_seg = np.array([t for t in time if p['t0'] <= t <= p['end']])
    T_seg = np.array([temp[i] for i, t in enumerate(time) if p['t0'] <= t <= p['end']])
    excess = T_seg - p['T_amb']
    valid = excess > 0
    ax.plot(t_seg[valid] - p['t0'], np.log(excess[valid]), 'o', markersize=4,
            color=p['color'], alpha=0.6, label=p['label'].split('\n')[0])
    # Theoretical line
    t_fine = np.linspace(0, p['end'] - p['t0'], 300)
    ax.plot(t_fine, np.log(p['T0'] - p['T_amb']) - p['k'] * t_fine,
            color=p['color'], lw=2, alpha=0.8)

ax.set_xlabel('Time since segment start (min)', fontsize=11)
ax.set_ylabel('ln(T(t) − T_amb)', fontsize=11)
ax.set_title('Log Temperature Excess vs Time\n(linear = confirms exponential decay)', fontsize=10)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Add slope annotation
ax.text(0.05, 0.05, f'Slope = −k = −0.01155 min⁻¹\n(same for all segments)',
        transform=ax.transAxes, fontsize=9, color='black',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/exponential_decay.png', dpi=150, bbox_inches='tight')
print("Saved: report/images/exponential_decay.png")
plt.close()

# ─── Figure 3: Half-life visualization ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))

# Use segment 1 as canonical example
p = params[0]
t_fine = np.linspace(0, 200, 1000)
T_fine = newton_cooling(t_fine, p['T_amb'], p['T0'], p['k'], 0)
excess_fine = T_fine - p['T_amb']

ax.plot(t_fine, excess_fine, 'b-', lw=2.5, label='T(t) − T_amb')

# Mark half-lives
t_half = np.log(2) / p['k']  # ≈ 60 min
initial_excess = p['T0'] - p['T_amb']
for n in range(1, 4):
    t_n = n * t_half
    T_n = initial_excess * (0.5 ** n)
    ax.plot([t_n, t_n], [0, T_n], 'r--', lw=1, alpha=0.7)
    ax.plot([0, t_n], [T_n, T_n], 'r--', lw=1, alpha=0.7)
    ax.plot(t_n, T_n, 'ro', markersize=8)
    ax.annotate(f't½×{n}={t_n:.0f} min\n{T_n:.1f}°C excess',
                xy=(t_n, T_n), xytext=(t_n + 5, T_n + 2),
                fontsize=8, color='darkred')

ax.axhline(0, color='gray', lw=1, ls=':')
ax.set_xlabel('Time (min)', fontsize=11)
ax.set_ylabel('Temperature Excess T(t) − T_amb (°C)', fontsize=11)
ax.set_title(f"Half-Life Analysis: t½ = ln(2)/k = {t_half:.1f} min\n"
             f"(k = {p['k']:.5f} min⁻¹, τ = {1/p['k']:.1f} min)",
             fontsize=11, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 200)
ax.set_ylim(-2, 65)

plt.tight_layout()
plt.savefig('report/images/half_life.png', dpi=150, bbox_inches='tight')
print("Saved: report/images/half_life.png")
plt.close()

print("All extra figures saved.")
