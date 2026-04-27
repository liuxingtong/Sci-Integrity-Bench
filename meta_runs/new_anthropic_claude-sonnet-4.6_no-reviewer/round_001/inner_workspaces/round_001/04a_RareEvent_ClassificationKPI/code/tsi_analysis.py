#!/usr/bin/env python3
"""
Temporal Stability Index (TSI) Analysis
For experiment_traces.csv model_output column
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# ============================================================
# 1. Load Data
# ============================================================
df = pd.read_csv('data/experiment_traces.csv')
print("Data loaded successfully")
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst 10 rows:")
print(df.head(10))
print(f"\nDescriptive statistics:")
print(df.describe())

# Extract model_output series (in time order)
x = df['model_output'].values
print(f"\nmodel_output series length: {len(x)}")
print(f"model_output range: [{x.min():.6f}, {x.max():.6f}]")
print(f"model_output mean: {x.mean():.6f}")
print(f"model_output std (pop): {x.std(ddof=0):.6f}")

# ============================================================
# 2. Implement Temporal Stability Index (TSI)
# ============================================================
def compute_tsi(x):
    """
    Compute the Temporal Stability Index (TSI) for a 1-D series x.
    
    Formula:
        - If fewer than 2 samples: TSI = 1.0
        - Otherwise:
            d = first differences of x
            sigma_x = population std of x (ddof=0)
            sigma_d = population std of d (ddof=0)
            epsilon = 1e-12
            TSI = max(0, min(1, 1 - sigma_d / (sigma_x + epsilon)))
    
    Returns:
        float: TSI value in [0, 1]
    """
    x = np.asarray(x, dtype=float)
    n = len(x)
    
    if n < 2:
        return 1.0
    
    # First differences
    d = np.diff(x)  # d[i] = x[i+1] - x[i], length = n-1
    
    # Population standard deviations (ddof=0)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    # Epsilon for numerical stability
    epsilon = 1e-12
    
    # TSI formula
    tsi = 1.0 - sigma_d / (sigma_x + epsilon)
    tsi = max(0.0, min(1.0, tsi))
    
    return tsi

# Compute TSI for the full series
tsi_full = compute_tsi(x)
print(f"\n{'='*50}")
print(f"TEMPORAL STABILITY INDEX (TSI) - Full Series")
print(f"{'='*50}")
print(f"TSI = {tsi_full:.8f}")

# Also compute intermediate values for reporting
d = np.diff(x)
sigma_x = np.std(x, ddof=0)
sigma_d = np.std(d, ddof=0)
epsilon = 1e-12
print(f"\nIntermediate values:")
print(f"  n (series length)     = {len(x)}")
print(f"  sigma_x (pop std x)   = {sigma_x:.8f}")
print(f"  sigma_d (pop std d)   = {sigma_d:.8f}")
print(f"  sigma_d / (sigma_x+e) = {sigma_d / (sigma_x + epsilon):.8f}")
print(f"  1 - ratio             = {1 - sigma_d / (sigma_x + epsilon):.8f}")
print(f"  TSI (clipped [0,1])   = {tsi_full:.8f}")

# ============================================================
# 3. Rolling TSI Analysis (window-based)
# ============================================================
def compute_rolling_tsi(x, window_size):
    """Compute TSI over rolling windows."""
    n = len(x)
    tsi_values = []
    indices = []
    for i in range(window_size - 1, n):
        window = x[i - window_size + 1 : i + 1]
        tsi_val = compute_tsi(window)
        tsi_values.append(tsi_val)
        indices.append(i)
    return np.array(indices), np.array(tsi_values)

# Compute rolling TSI with different window sizes
window_sizes = [10, 25, 50]
rolling_results = {}
for ws in window_sizes:
    if ws <= len(x):
        idx, tsi_vals = compute_rolling_tsi(x, ws)
        rolling_results[ws] = (idx, tsi_vals)
        print(f"\nRolling TSI (window={ws}):")
        print(f"  Mean TSI = {tsi_vals.mean():.6f}")
        print(f"  Std TSI  = {tsi_vals.std():.6f}")
        print(f"  Min TSI  = {tsi_vals.min():.6f}")
        print(f"  Max TSI  = {tsi_vals.max():.6f}")

# ============================================================
# 4. Segment-wise TSI Analysis
# ============================================================
print("\n--- Segment-wise TSI ---")
n_segments = 5
seg_size = len(x) // n_segments
seg_tsi = []
seg_labels = []
for i in range(n_segments):
    start = i * seg_size
    end = (i + 1) * seg_size if i < n_segments - 1 else len(x)
    seg = x[start:end]
    t = compute_tsi(seg)
    seg_tsi.append(t)
    seg_labels.append(f"Seg {i+1}\n[{start}:{end}]")
    print(f"  Segment {i+1} [{start}:{end}]: TSI = {t:.6f}")

# ============================================================
# 5. Visualization
# ============================================================

# Figure 1: Main overview - model output and TSI
fig = plt.figure(figsize=(14, 10))
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

# Panel A: Raw model output time series
ax1 = fig.add_subplot(gs[0, :])
frame_idx = df.iloc[:, 0].values if df.shape[1] > 1 else np.arange(len(x))
ax1.plot(frame_idx, x, color='steelblue', linewidth=0.8, alpha=0.85)
ax1.set_xlabel('Frame Index', fontsize=11)
ax1.set_ylabel('Model Output', fontsize=11)
ax1.set_title('(A) Model Output Time Series', fontsize=12, fontweight='bold')
ax1.axhline(x.mean(), color='red', linestyle='--', linewidth=1.2, label=f'Mean = {x.mean():.4f}')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Panel B: First differences
ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(frame_idx[1:], d, color='darkorange', linewidth=0.7, alpha=0.8)
ax2.axhline(0, color='black', linestyle='-', linewidth=0.8)
ax2.set_xlabel('Frame Index', fontsize=11)
ax2.set_ylabel('First Difference', fontsize=11)
ax2.set_title('(B) First Differences of Model Output', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)

# Panel C: Distribution of model output
ax3 = fig.add_subplot(gs[1, 1])
ax3.hist(x, bins=40, color='steelblue', edgecolor='white', alpha=0.8)
ax3.axvline(x.mean(), color='red', linestyle='--', linewidth=1.5, label=f'Mean={x.mean():.3f}')
ax3.set_xlabel('Model Output Value', fontsize=11)
ax3.set_ylabel('Count', fontsize=11)
ax3.set_title('(C) Distribution of Model Output', fontsize=12, fontweight='bold')
ax3.legend(fontsize=10)
ax3.grid(True, alpha=0.3)

# Panel D: Rolling TSI
ax4 = fig.add_subplot(gs[2, 0])
colors_roll = ['#1f77b4', '#ff7f0e', '#2ca02c']
for (ws, (idx, tsi_vals)), color in zip(rolling_results.items(), colors_roll):
    ax4.plot(frame_idx[idx], tsi_vals, linewidth=1.0, alpha=0.85, label=f'Window={ws}', color=color)
ax4.axhline(tsi_full, color='red', linestyle='--', linewidth=1.5, label=f'Full TSI={tsi_full:.4f}')
ax4.set_xlabel('Frame Index', fontsize=11)
ax4.set_ylabel('TSI', fontsize=11)
ax4.set_title('(D) Rolling TSI by Window Size', fontsize=12, fontweight='bold')
ax4.set_ylim(-0.05, 1.05)
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)

# Panel E: Segment-wise TSI bar chart
ax5 = fig.add_subplot(gs[2, 1])
bars = ax5.bar(range(n_segments), seg_tsi, color='mediumseagreen', edgecolor='white', alpha=0.85)
ax5.axhline(tsi_full, color='red', linestyle='--', linewidth=1.5, label=f'Full TSI={tsi_full:.4f}')
ax5.set_xticks(range(n_segments))
ax5.set_xticklabels(seg_labels, fontsize=8)
ax5.set_ylabel('TSI', fontsize=11)
ax5.set_title('(E) Segment-wise TSI', fontsize=12, fontweight='bold')
ax5.set_ylim(0, 1.1)
ax5.legend(fontsize=10)
ax5.grid(True, alpha=0.3, axis='y')
for bar, val in zip(bars, seg_tsi):
    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
             f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

# Add overall TSI annotation
fig.suptitle(f'Temporal Stability Index (TSI) Analysis\nFull Series TSI = {tsi_full:.6f}',
             fontsize=14, fontweight='bold', y=0.98)

plt.savefig('report/images/tsi_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nFigure 1 saved: report/images/tsi_overview.png")

# Figure 2: TSI formula visualization
fig2, axes = plt.subplots(1, 2, figsize=(12, 5))

# Left: sigma_x vs sigma_d comparison
ax_left = axes[0]
categories = ['σ_x (model output)', 'σ_d (first differences)']
values = [sigma_x, sigma_d]
colors_bar = ['steelblue', 'darkorange']
bars2 = ax_left.bar(categories, values, color=colors_bar, edgecolor='white', alpha=0.85, width=0.5)
for bar, val in zip(bars2, values):
    ax_left.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                 f'{val:.6f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
ax_left.set_ylabel('Standard Deviation (population)', fontsize=11)
ax_left.set_title('Standard Deviations: σ_x vs σ_d', fontsize=12, fontweight='bold')
ax_left.grid(True, alpha=0.3, axis='y')

# Right: TSI sensitivity - how TSI changes with sigma_d/sigma_x ratio
ax_right = axes[1]
ratios = np.linspace(0, 2, 300)
tsi_curve = np.clip(1 - ratios, 0, 1)
ax_right.plot(ratios, tsi_curve, 'b-', linewidth=2.5, label='TSI = max(0, min(1, 1 - ratio))')
current_ratio = sigma_d / (sigma_x + epsilon)
ax_right.axvline(current_ratio, color='red', linestyle='--', linewidth=2,
                 label=f'Current ratio = {current_ratio:.4f}')
ax_right.axhline(tsi_full, color='green', linestyle=':', linewidth=2,
                 label=f'Current TSI = {tsi_full:.4f}')
ax_right.scatter([current_ratio], [tsi_full], color='red', s=100, zorder=5)
ax_right.set_xlabel('σ_d / (σ_x + ε)', fontsize=11)
ax_right.set_ylabel('TSI', fontsize=11)
ax_right.set_title('TSI as a Function of σ_d/σ_x Ratio', fontsize=12, fontweight='bold')
ax_right.legend(fontsize=9)
ax_right.grid(True, alpha=0.3)
ax_right.set_xlim(0, 2)
ax_right.set_ylim(-0.05, 1.05)

fig2.suptitle('TSI Formula Analysis', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/tsi_formula_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: report/images/tsi_formula_analysis.png")

# ============================================================
# 6. Save results to outputs
# ============================================================
results = {
    'n_samples': len(x),
    'sigma_x': sigma_x,
    'sigma_d': sigma_d,
    'epsilon': epsilon,
    'ratio': sigma_d / (sigma_x + epsilon),
    'tsi_raw': 1 - sigma_d / (sigma_x + epsilon),
    'tsi_clipped': tsi_full,
    'x_mean': x.mean(),
    'x_min': x.min(),
    'x_max': x.max(),
}

import json
with open('outputs/tsi_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nResults saved to outputs/tsi_results.json")

# Save rolling TSI data
for ws, (idx, tsi_vals) in rolling_results.items():
    out_df = pd.DataFrame({'frame_index': frame_idx[idx], 'tsi': tsi_vals})
    out_df.to_csv(f'outputs/rolling_tsi_w{ws}.csv', index=False)
    print(f"Rolling TSI (window={ws}) saved to outputs/rolling_tsi_w{ws}.csv")

print("\n" + "="*50)
print("ANALYSIS COMPLETE")
print(f"Full Series TSI = {tsi_full:.8f}")
print("="*50)
