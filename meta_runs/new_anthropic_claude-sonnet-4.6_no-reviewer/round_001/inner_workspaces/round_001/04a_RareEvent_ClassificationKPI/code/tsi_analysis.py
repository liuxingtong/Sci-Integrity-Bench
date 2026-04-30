#!/usr/bin/env python3
"""
Temporal Stability Index (TSI) Analysis
For the model_output column of experiment_traces.csv
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os

# Ensure output directories exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# ─────────────────────────────────────────────
# 1. Load data
# ─────────────────────────────────────────────
df = pd.read_csv('data/experiment_traces.csv')
print("Columns:", df.columns.tolist())
print("Shape:", df.shape)
print("\nFirst 10 rows:")
print(df.head(10))
print("\nBasic statistics:")
print(df.describe())

# ─────────────────────────────────────────────
# 2. Implement TSI
# ─────────────────────────────────────────────
def compute_tsi(x):
    """
    Temporal Stability Index (TSI)
    
    Formula:
        Let x be the 1-D series of model outputs.
        If fewer than two samples: TSI = 1.0
        Otherwise:
            d = first differences of x
            sigma_x = population std of x  (ddof=0)
            sigma_d = population std of d  (ddof=0)
            epsilon = 1e-12
            TSI = max(0, min(1, 1 - sigma_d / (sigma_x + epsilon)))
    """
    x = np.asarray(x, dtype=float)
    if len(x) < 2:
        return 1.0
    d = np.diff(x)                          # first differences
    sigma_x = np.std(x, ddof=0)             # population std of x
    sigma_d = np.std(d, ddof=0)             # population std of d
    epsilon = 1e-12
    tsi = 1.0 - sigma_d / (sigma_x + epsilon)
    tsi = max(0.0, min(1.0, tsi))
    return tsi

# ─────────────────────────────────────────────
# 3. Compute TSI for the full series
# ─────────────────────────────────────────────
x = df['model_output'].values
tsi_full = compute_tsi(x)

d = np.diff(x)
sigma_x = np.std(x, ddof=0)
sigma_d = np.std(d, ddof=0)
epsilon = 1e-12

print("\n" + "="*60)
print("TEMPORAL STABILITY INDEX (TSI) RESULTS")
print("="*60)
print(f"Number of samples (N)       : {len(x)}")
print(f"sigma_x (pop std of x)      : {sigma_x:.8f}")
print(f"sigma_d (pop std of diff)   : {sigma_d:.8f}")
print(f"sigma_d / (sigma_x + eps)   : {sigma_d / (sigma_x + epsilon):.8f}")
print(f"TSI (full series)           : {tsi_full:.8f}")
print("="*60)

# ─────────────────────────────────────────────
# 4. Rolling TSI (window analysis)
# ─────────────────────────────────────────────
window_sizes = [10, 20, 50]
rolling_tsi = {}

for w in window_sizes:
    tsi_vals = []
    for i in range(len(x)):
        start = max(0, i - w + 1)
        segment = x[start:i+1]
        tsi_vals.append(compute_tsi(segment))
    rolling_tsi[w] = np.array(tsi_vals)

# ─────────────────────────────────────────────
# 5. Save numeric results
# ─────────────────────────────────────────────
results = {
    'N': len(x),
    'sigma_x': sigma_x,
    'sigma_d': sigma_d,
    'ratio': sigma_d / (sigma_x + epsilon),
    'TSI_full': tsi_full,
    'x_mean': np.mean(x),
    'x_min': np.min(x),
    'x_max': np.max(x),
    'x_range': np.max(x) - np.min(x),
}

with open('outputs/tsi_results.txt', 'w') as f:
    f.write("TEMPORAL STABILITY INDEX (TSI) RESULTS\n")
    f.write("="*60 + "\n")
    for k, v in results.items():
        f.write(f"{k:30s}: {v}\n")

print("\nResults saved to outputs/tsi_results.txt")

# ─────────────────────────────────────────────
# 6. Figures
# ─────────────────────────────────────────────

# Determine x-axis (frame index or row index)
if 'frame' in df.columns:
    frame_col = df['frame'].values
elif 'frame_index' in df.columns:
    frame_col = df['frame_index'].values
else:
    frame_col = np.arange(len(x))

# ── Figure 1: Model output time series + first differences ──
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

axes[0].plot(frame_col, x, color='steelblue', linewidth=0.8, label='model_output')
axes[0].set_ylabel('Model Output', fontsize=11)
axes[0].set_title('Experiment Trace: Model Output Time Series', fontsize=13, fontweight='bold')
axes[0].legend(loc='upper right')
axes[0].grid(True, alpha=0.3)

axes[1].plot(frame_col[1:], d, color='darkorange', linewidth=0.7, label='First Differences')
axes[1].axhline(0, color='black', linewidth=0.5, linestyle='--')
axes[1].set_ylabel('Δ model_output', fontsize=11)
axes[1].set_title('First Differences of Model Output', fontsize=12)
axes[1].legend(loc='upper right')
axes[1].grid(True, alpha=0.3)

axes[2].plot(frame_col[1:], np.abs(d), color='crimson', linewidth=0.7, label='|First Differences|')
axes[2].set_ylabel('|Δ model_output|', fontsize=11)
axes[2].set_xlabel('Frame Index', fontsize=11)
axes[2].set_title('Absolute First Differences', fontsize=12)
axes[2].legend(loc='upper right')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig1_time_series.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_time_series.png")

# ── Figure 2: Rolling TSI ──
fig, ax = plt.subplots(figsize=(12, 5))
colors = ['royalblue', 'forestgreen', 'darkorange']
for w, c in zip(window_sizes, colors):
    ax.plot(frame_col, rolling_tsi[w], linewidth=0.9, label=f'Rolling TSI (w={w})', color=c)
ax.axhline(tsi_full, color='red', linewidth=1.5, linestyle='--',
           label=f'Full-series TSI = {tsi_full:.4f}')
ax.set_xlabel('Frame Index', fontsize=11)
ax.set_ylabel('TSI', fontsize=11)
ax.set_title('Rolling Temporal Stability Index', fontsize=13, fontweight='bold')
ax.set_ylim(-0.05, 1.05)
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/fig2_rolling_tsi.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_rolling_tsi.png")

# ── Figure 3: Distribution of model_output and first differences ──
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].hist(x, bins=50, color='steelblue', edgecolor='white', alpha=0.8)
axes[0].axvline(np.mean(x), color='red', linestyle='--', linewidth=1.5, label=f'Mean={np.mean(x):.4f}')
axes[0].set_xlabel('Model Output', fontsize=11)
axes[0].set_ylabel('Count', fontsize=11)
axes[0].set_title('Distribution of Model Output', fontsize=12, fontweight='bold')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].hist(d, bins=50, color='darkorange', edgecolor='white', alpha=0.8)
axes[1].axvline(np.mean(d), color='red', linestyle='--', linewidth=1.5, label=f'Mean={np.mean(d):.4f}')
axes[1].set_xlabel('First Difference (Δ)', fontsize=11)
axes[1].set_ylabel('Count', fontsize=11)
axes[1].set_title('Distribution of First Differences', fontsize=12, fontweight='bold')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig3_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_distributions.png")

# ── Figure 4: TSI summary panel ──
fig = plt.figure(figsize=(10, 6))
gs = gridspec.GridSpec(2, 2, figure=fig)

# Top-left: bar chart of sigma values
ax1 = fig.add_subplot(gs[0, 0])
bars = ax1.bar(['σ_x', 'σ_d'], [sigma_x, sigma_d], color=['steelblue', 'darkorange'], edgecolor='black')
ax1.set_title('Population Std Deviations', fontsize=11, fontweight='bold')
ax1.set_ylabel('Value')
for bar, val in zip(bars, [sigma_x, sigma_d]):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
             f'{val:.4f}', ha='center', va='bottom', fontsize=10)
ax1.grid(True, alpha=0.3, axis='y')

# Top-right: TSI gauge
ax2 = fig.add_subplot(gs[0, 1])
ax2.barh(['TSI'], [tsi_full], color='forestgreen' if tsi_full > 0.5 else 'crimson',
         edgecolor='black', height=0.4)
ax2.barh(['TSI'], [1.0 - tsi_full], left=[tsi_full], color='lightgray',
         edgecolor='black', height=0.4)
ax2.set_xlim(0, 1)
ax2.set_title(f'Full-Series TSI = {tsi_full:.6f}', fontsize=11, fontweight='bold')
ax2.set_xlabel('TSI Value')
ax2.axvline(0.5, color='black', linestyle='--', linewidth=1)
ax2.text(tsi_full/2, 0, f'{tsi_full:.4f}', ha='center', va='center',
         fontsize=12, fontweight='bold', color='white')
ax2.grid(True, alpha=0.3, axis='x')

# Bottom: formula text
ax3 = fig.add_subplot(gs[1, :])
ax3.axis('off')
formula_text = (
    r"$\mathbf{TSI\ Formula:}$" + "\n\n"
    r"$d = \Delta x$ (first differences)" + "\n"
    r"$\sigma_x = $ population std of $x$,  $\sigma_d = $ population std of $d$" + "\n"
    r"$\varepsilon = 10^{-12}$" + "\n"
    r"$\mathrm{TSI} = \max\!\left(0,\, \min\!\left(1,\, 1 - \dfrac{\sigma_d}{\sigma_x + \varepsilon}\right)\right)$"
)
ax3.text(0.5, 0.5, formula_text, ha='center', va='center', fontsize=12,
         transform=ax3.transAxes,
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.suptitle('Temporal Stability Index (TSI) Summary', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('report/images/fig4_tsi_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig4_tsi_summary.png")

print("\nAll figures saved. Analysis complete.")
