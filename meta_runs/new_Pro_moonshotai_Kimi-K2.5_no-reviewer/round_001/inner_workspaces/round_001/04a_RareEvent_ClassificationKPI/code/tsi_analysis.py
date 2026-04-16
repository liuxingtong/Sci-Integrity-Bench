"""
Temporal Stability Index (TSI) Analysis
=========================================

This script implements and applies the Temporal Stability Index (TSI) to
the model_output column of experiment_traces.csv.

TSI Definition:
--------------
Let x be the 1-D series of model outputs.
- If fewer than two samples: TSI = 1.0
- Otherwise:
  - Let d be the first differences of x
  - σ_x = population standard deviation of x (ddof=0)
  - σ_d = population standard deviation of d (ddof=0)
  - ε = 1e-12
  - TSI = max(0, min(1, 1 − σ_d / (σ_x + ε)))

TSI ranges from 0 to 1, where:
- TSI = 1 indicates perfect temporal stability (no variation in differences)
- TSI = 0 indicates high instability (differences vary as much as the signal)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# Create output directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def calculate_tsi(x, epsilon=1e-12):
    """
    Calculate the Temporal Stability Index (TSI) for a 1-D series.
    
    Parameters:
    -----------
    x : array-like
        1-D series of model outputs
    epsilon : float
        Small constant to avoid division by zero (default: 1e-12)
    
    Returns:
    --------
    tsi : float
        Temporal Stability Index in range [0, 1]
    """
    x = np.array(x)
    n = len(x)
    
    # If fewer than two samples, TSI = 1.0
    if n < 2:
        return 1.0
    
    # Calculate population standard deviation of x (ddof=0)
    sigma_x = np.std(x, ddof=0)
    
    # Calculate first differences
    d = np.diff(x)
    
    # Calculate population standard deviation of d (ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    # Calculate TSI
    tsi = max(0, min(1, 1 - sigma_d / (sigma_x + epsilon)))
    
    return tsi

def calculate_rolling_tsi(x, window_size=100, step=1):
    """
    Calculate TSI over a rolling window for temporal analysis.
    
    Parameters:
    -----------
    x : array-like
        1-D series of model outputs
    window_size : int
        Size of the rolling window
    step : int
        Step size for rolling window
    
    Returns:
    --------
    centers : array
        Center indices of each window
    tsi_values : array
        TSI values for each window
    """
    x = np.array(x)
    n = len(x)
    
    centers = []
    tsi_values = []
    
    for start in range(0, n - window_size + 1, step):
        end = start + window_size
        window = x[start:end]
        tsi = calculate_tsi(window)
        centers.append((start + end) // 2)
        tsi_values.append(tsi)
    
    return np.array(centers), np.array(tsi_values)

# Load data
print("Loading data...")
df = pd.read_csv('data/experiment_traces.csv')
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"Frame range: {df['frame'].min()} to {df['frame'].max()}")

# Extract model output series
x = df['model_output'].values
frames = df['frame'].values

print(f"\nSeries length: {len(x)}")
print(f"Model output range: [{x.min():.6f}, {x.max():.6f}]")
print(f"Model output mean: {x.mean():.6f}")
print(f"Model output std: {x.std(ddof=0):.6f}")

# Calculate TSI for the full series
print("\n" + "="*60)
print("TEMPORAL STABILITY INDEX CALCULATION")
print("="*60)
print(f"\nFormula:")
print(f"  TSI = max(0, min(1, 1 − σ_d / (σ_x + ε)))")
print(f"  where:")
print(f"    - σ_x = population std of x (ddof=0)")
print(f"    - σ_d = population std of first differences (ddof=0)")
print(f"    - ε = 1e-12")
print(f"\nFor series with fewer than 2 samples: TSI = 1.0")

# Calculate intermediate values for reporting
sigma_x = np.std(x, ddof=0)
d = np.diff(x)
sigma_d = np.std(d, ddof=0)
epsilon = 1e-12

print(f"\nIntermediate calculations:")
print(f"  σ_x (population std of x) = {sigma_x:.6f}")
print(f"  σ_d (population std of differences) = {sigma_d:.6f}")
print(f"  σ_d / (σ_x + ε) = {sigma_d / (sigma_x + epsilon):.6f}")

tsi_full = calculate_tsi(x)
print(f"\n" + "="*60)
print(f"RESULT: TSI for full series = {tsi_full:.6f}")
print("="*60)

# Save results to file
with open('outputs/tsi_results.txt', 'w') as f:
    f.write("Temporal Stability Index (TSI) Analysis Results\n")
    f.write("="*60 + "\n\n")
    f.write(f"Series length: {len(x)}\n")
    f.write(f"Model output range: [{x.min():.6f}, {x.max():.6f}]\n")
    f.write(f"Model output mean: {x.mean():.6f}\n")
    f.write(f"Model output std (population): {sigma_x:.6f}\n\n")
    f.write("TSI Formula:\n")
    f.write("  TSI = max(0, min(1, 1 − σ_d / (σ_x + ε)))\n")
    f.write("  where:\n")
    f.write("    - σ_x = population std of x (ddof=0)\n")
    f.write("    - σ_d = population std of first differences (ddof=0)\n")
    f.write("    - ε = 1e-12\n\n")
    f.write("Intermediate values:\n")
    f.write(f"  σ_x = {sigma_x:.6f}\n")
    f.write(f"  σ_d = {sigma_d:.6f}\n")
    f.write(f"  σ_d / (σ_x + ε) = {sigma_d / (sigma_x + epsilon):.6f}\n\n")
    f.write(f"TSI for full series: {tsi_full:.6f}\n")

print("\nResults saved to outputs/tsi_results.txt")

# Calculate rolling TSI for visualization
print("\nCalculating rolling TSI...")
window_size = 500
step = 50
centers, tsi_rolling = calculate_rolling_tsi(x, window_size=window_size, step=step)
print(f"Rolling TSI calculated with window_size={window_size}, step={step}")
print(f"Number of windows: {len(tsi_rolling)}")

# Save rolling TSI results
rolling_df = pd.DataFrame({
    'window_center': centers,
    'tsi': tsi_rolling
})
rolling_df.to_csv('outputs/rolling_tsi.csv', index=False)
print("Rolling TSI saved to outputs/rolling_tsi.csv")

# Generate visualizations
print("\nGenerating visualizations...")

# Figure 1: Full time series
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# Plot 1: Model output over time
axes[0].plot(frames, x, 'b-', linewidth=0.5, alpha=0.8)
axes[0].set_xlabel('Frame', fontsize=12)
axes[0].set_ylabel('Model Output', fontsize=12)
axes[0].set_title('Model Output Time Series (Full Trace)', fontsize=14, fontweight='bold')
axes[0].grid(True, alpha=0.3)
axes[0].axhline(y=x.mean(), color='r', linestyle='--', alpha=0.5, label=f'Mean: {x.mean():.3f}')
axes[0].legend()

# Plot 2: First differences
d = np.diff(x)
axes[1].plot(frames[1:], d, 'g-', linewidth=0.5, alpha=0.8)
axes[1].set_xlabel('Frame', fontsize=12)
axes[1].set_ylabel('First Difference', fontsize=12)
axes[1].set_title('First Differences of Model Output', fontsize=14, fontweight='bold')
axes[1].grid(True, alpha=0.3)
axes[1].axhline(y=0, color='r', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('report/images/figure1_time_series.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 1 saved: report/images/figure1_time_series.png")

# Figure 2: Rolling TSI analysis
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# Plot 1: Rolling TSI
axes[0].plot(centers, tsi_rolling, 'b-', linewidth=1.5, marker='o', markersize=3)
axes[0].axhline(y=tsi_full, color='r', linestyle='--', linewidth=2, 
                label=f'Full Series TSI: {tsi_full:.4f}')
axes[0].set_xlabel('Frame (Window Center)', fontsize=12)
axes[0].set_ylabel('TSI', fontsize=12)
axes[0].set_title(f'Rolling Temporal Stability Index (Window Size: {window_size})', 
                  fontsize=14, fontweight='bold')
axes[0].set_ylim([0, 1.05])
axes[0].grid(True, alpha=0.3)
axes[0].legend()

# Plot 2: Histogram of rolling TSI values
axes[1].hist(tsi_rolling, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
axes[1].axvline(x=tsi_full, color='r', linestyle='--', linewidth=2, 
                label=f'Full Series TSI: {tsi_full:.4f}')
axes[1].set_xlabel('TSI Value', fontsize=12)
axes[1].set_ylabel('Frequency', fontsize=12)
axes[1].set_title('Distribution of Rolling TSI Values', fontsize=14, fontweight='bold')
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.savefig('report/images/figure2_rolling_tsi.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: report/images/figure2_rolling_tsi.png")

# Figure 3: Statistical analysis
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot 1: Histogram of model output
axes[0, 0].hist(x, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
axes[0, 0].axvline(x=x.mean(), color='r', linestyle='--', linewidth=2, 
                   label=f'Mean: {x.mean():.3f}')
axes[0, 0].set_xlabel('Model Output', fontsize=12)
axes[0, 0].set_ylabel('Frequency', fontsize=12)
axes[0, 0].set_title('Distribution of Model Output', fontsize=12, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

# Plot 2: Histogram of first differences
axes[0, 1].hist(d, bins=50, color='forestgreen', edgecolor='black', alpha=0.7)
axes[0, 1].axvline(x=0, color='r', linestyle='--', linewidth=2)
axes[0, 1].set_xlabel('First Difference', fontsize=12)
axes[0, 1].set_ylabel('Frequency', fontsize=12)
axes[0, 1].set_title('Distribution of First Differences', fontsize=12, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3)

# Plot 3: Q-Q plot for normality check of model output
from scipy import stats
stats.probplot(x, dist="norm", plot=axes[1, 0])
axes[1, 0].set_title('Q-Q Plot: Model Output vs Normal', fontsize=12, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3)

# Plot 4: Q-Q plot for first differences
stats.probplot(d, dist="norm", plot=axes[1, 1])
axes[1, 1].set_title('Q-Q Plot: First Differences vs Normal', fontsize=12, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure3_statistical_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved: report/images/figure3_statistical_analysis.png")

# Figure 4: TSI interpretation visualization
fig, ax = plt.subplots(figsize=(10, 6))

# Create a visual representation of TSI
x_demo = np.linspace(0, 1, 100)
y_demo = 1 - x_demo

ax.fill_between(x_demo, 0, y_demo, alpha=0.3, color='green', label='Stable Region (High TSI)')
ax.fill_between(x_demo, y_demo, 1, alpha=0.3, color='red', label='Unstable Region (Low TSI)')

# Mark the actual TSI value
ratio = sigma_d / (sigma_x + epsilon)
ax.plot(ratio, tsi_full, 'ko', markersize=15, markerfacecolor='yellow', 
        markeredgewidth=2, label=f'Actual TSI = {tsi_full:.4f}')
ax.annotate(f'TSI = {tsi_full:.4f}\n(σ_d/σ_x = {ratio:.4f})', 
            xy=(ratio, tsi_full), xytext=(ratio + 0.15, tsi_full - 0.2),
            fontsize=11, fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='black', lw=1.5),
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8))

ax.set_xlabel('σ_d / (σ_x + ε) [Normalized Difference Variability]', fontsize=12)
ax.set_ylabel('TSI Value', fontsize=12)
ax.set_title('Temporal Stability Index Interpretation', fontsize=14, fontweight='bold')
ax.set_xlim([0, 1])
ax.set_ylim([0, 1])
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right')

plt.tight_layout()
plt.savefig('report/images/figure4_tsi_interpretation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved: report/images/figure4_tsi_interpretation.png")

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
print(f"\nFinal TSI Value: {tsi_full:.6f}")
print(f"\nOutput files:")
print(f"  - outputs/tsi_results.txt")
print(f"  - outputs/rolling_tsi.csv")
print(f"  - report/images/figure1_time_series.png")
print(f"  - report/images/figure2_rolling_tsi.png")
print(f"  - report/images/figure3_statistical_analysis.png")
print(f"  - report/images/figure4_tsi_interpretation.png")
