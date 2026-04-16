"""
Temporal Stability Index (TSI) Analysis
for Industrial Control Telemetry Model Output
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Create output directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def calculate_tsi(x):
    """
    Calculate the Temporal Stability Index (TSI) for a 1-D series.
    
    Parameters:
    -----------
    x : array-like
        1-D series of model outputs
    
    Returns:
    --------
    float : TSI value in range [0, 1]
    
    Definition:
    -----------
    - If fewer than two samples, TSI = 1.0
    - Otherwise:
        - d = first differences of x
        - σ_x = population std of x (ddof=0)
        - σ_d = population std of d (ddof=0)
        - ε = 1e-12
        - TSI = max(0, min(1, 1 − σ_d / (σ_x + ε)))
    """
    x = np.array(x).flatten()
    
    # If fewer than two samples, return 1.0
    if len(x) < 2:
        return 1.0
    
    # Calculate first differences
    d = np.diff(x)
    
    # Population standard deviations (ddof=0)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    # Small epsilon to avoid division by zero
    epsilon = 1e-12
    
    # Calculate TSI
    tsi = 1 - sigma_d / (sigma_x + epsilon)
    
    # Clamp to [0, 1]
    tsi = max(0.0, min(1.0, tsi))
    
    return tsi

# Load data
print("Loading data...")
df = pd.read_csv('data/experiment_traces.csv')
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst few rows:")
print(df.head())
print(f"\nLast few rows:")
print(df.tail())

# Extract model_output series
model_output = df['model_output'].values
frame = df['frame'].values

print(f"\nModel output statistics:")
print(f"  Min: {model_output.min():.4f}")
print(f"  Max: {model_output.max():.4f}")
print(f"  Mean: {model_output.mean():.4f}")
print(f"  Std (population): {np.std(model_output, ddof=0):.4f}")

# Calculate TSI for the entire series
tsi_value = calculate_tsi(model_output)
print(f"\n=== TSI Calculation ===")
print(f"Temporal Stability Index (TSI): {tsi_value:.6f}")

# Calculate intermediate values for reporting
x = model_output
d = np.diff(x)
sigma_x = np.std(x, ddof=0)
sigma_d = np.std(d, ddof=0)
epsilon = 1e-12

print(f"\nIntermediate values:")
print(f"  Number of samples (n): {len(x)}")
print(f"  Number of differences (n-1): {len(d)}")
print(f"  σ_x (population std of x): {sigma_x:.6f}")
print(f"  σ_d (population std of differences): {sigma_d:.6f}")
print(f"  σ_d / (σ_x + ε): {sigma_d / (sigma_x + epsilon):.6f}")
print(f"  1 - σ_d/(σ_x+ε): {1 - sigma_d / (sigma_x + epsilon):.6f}")

# Save results to file
results = {
    'TSI': tsi_value,
    'n_samples': len(x),
    'sigma_x': sigma_x,
    'sigma_d': sigma_d,
    'ratio': sigma_d / (sigma_x + epsilon)
}

with open('outputs/tsi_results.txt', 'w') as f:
    f.write("Temporal Stability Index (TSI) Results\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"TSI Value: {tsi_value:.6f}\n")
    f.write(f"Number of samples: {len(x)}\n")
    f.write(f"σ_x (population std of x): {sigma_x:.6f}\n")
    f.write(f"σ_d (population std of differences): {sigma_d:.6f}\n")
    f.write(f"σ_d / (σ_x + ε): {sigma_d / (sigma_x + epsilon):.6f}\n")

print("\nResults saved to outputs/tsi_results.txt")

# ============ Visualization ============

# Figure 1: Full time series plot
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(frame, model_output, 'b-', linewidth=0.5, alpha=0.8)
ax.set_xlabel('Frame Index', fontsize=12)
ax.set_ylabel('Model Output', fontsize=12)
ax.set_title(f'Model Output Time Series (TSI = {tsi_value:.4f})', fontsize=14)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/time_series_full.png', dpi=150)
plt.close()
print("Saved: report/images/time_series_full.png")

# Figure 2: First differences
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(frame[1:], d, 'r-', linewidth=0.5, alpha=0.8)
ax.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
ax.set_xlabel('Frame Index', fontsize=12)
ax.set_ylabel('First Difference (Δ)', fontsize=12)
ax.set_title(f'First Differences of Model Output (σ_d = {sigma_d:.4f})', fontsize=14)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/first_differences.png', dpi=150)
plt.close()
print("Saved: report/images/first_differences.png")

# Figure 3: Distribution comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Histogram of model output
axes[0].hist(model_output, bins=50, color='blue', alpha=0.7, edgecolor='black')
axes[0].axvline(x=np.mean(model_output), color='red', linestyle='--', label=f'Mean: {np.mean(model_output):.2f}')
axes[0].set_xlabel('Model Output', fontsize=12)
axes[0].set_ylabel('Frequency', fontsize=12)
axes[0].set_title(f'Distribution of Model Output\nσ_x = {sigma_x:.4f}', fontsize=12)
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Histogram of first differences
axes[1].hist(d, bins=50, color='red', alpha=0.7, edgecolor='black')
axes[1].axvline(x=np.mean(d), color='blue', linestyle='--', label=f'Mean: {np.mean(d):.4f}')
axes[1].set_xlabel('First Difference (Δ)', fontsize=12)
axes[1].set_ylabel('Frequency', fontsize=12)
axes[1].set_title(f'Distribution of First Differences\nσ_d = {sigma_d:.4f}', fontsize=12)
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/distributions.png', dpi=150)
plt.close()
print("Saved: report/images/distributions.png")

# Figure 4: Rolling TSI analysis (window-based)
window_sizes = [100, 500, 1000]
fig, axes = plt.subplots(len(window_sizes) + 1, 1, figsize=(14, 10))

# Original series
axes[0].plot(frame, model_output, 'b-', linewidth=0.5)
axes[0].set_ylabel('Model Output', fontsize=11)
axes[0].set_title('Original Model Output Time Series', fontsize=12)
axes[0].grid(True, alpha=0.3)

# Rolling TSI for different window sizes
for idx, window in enumerate(window_sizes):
    rolling_tsi = []
    rolling_frames = []
    for i in range(window, len(model_output) + 1):
        window_data = model_output[i-window:i]
        tsi = calculate_tsi(window_data)
        rolling_tsi.append(tsi)
        rolling_frames.append(frame[i-1])
    
    axes[idx + 1].plot(rolling_frames, rolling_tsi, 'g-', linewidth=0.8)
    axes[idx + 1].axhline(y=tsi_value, color='red', linestyle='--', linewidth=1, 
                          label=f'Global TSI: {tsi_value:.4f}')
    axes[idx + 1].set_ylabel('TSI', fontsize=11)
    axes[idx + 1].set_title(f'Rolling TSI (Window = {window})', fontsize=12)
    axes[idx + 1].set_ylim([0, 1.05])
    axes[idx + 1].legend(loc='lower right')
    axes[idx + 1].grid(True, alpha=0.3)

axes[-1].set_xlabel('Frame Index', fontsize=12)
plt.tight_layout()
plt.savefig('report/images/rolling_tsi.png', dpi=150)
plt.close()
print("Saved: report/images/rolling_tsi.png")

# Figure 5: TSI interpretation visualization
fig, ax = plt.subplots(figsize=(10, 6))

# Create a bar showing TSI position
ax.barh(['TSI'], [tsi_value], color='green', height=0.3, alpha=0.8)
ax.barh(['TSI'], [1-tsi_value], left=[tsi_value], color='lightgray', height=0.3, alpha=0.5)

# Add reference lines
ax.axvline(x=0, color='black', linewidth=1)
ax.axvline(x=1, color='black', linewidth=1)
ax.axvline(x=0.5, color='gray', linestyle='--', linewidth=1, alpha=0.5)

# Add text annotations
ax.text(tsi_value/2, 0, f'{tsi_value:.4f}', ha='center', va='center', fontsize=14, fontweight='bold')
ax.text(tsi_value + (1-tsi_value)/2, 0, f'{1-tsi_value:.4f}', ha='center', va='center', fontsize=12, color='gray')

ax.set_xlim([-0.05, 1.05])
ax.set_xlabel('TSI Value', fontsize=12)
ax.set_title('Temporal Stability Index (TSI) Interpretation\n(Higher = More Stable)', fontsize=14)

# Add interpretation zones
ax.axvspan(0, 0.3, alpha=0.1, color='red', label='Low stability')
ax.axvspan(0.3, 0.7, alpha=0.1, color='yellow', label='Moderate stability')
ax.axvspan(0.7, 1.0, alpha=0.1, color='green', label='High stability')
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)

plt.tight_layout()
plt.savefig('report/images/tsi_interpretation.png', dpi=150)
plt.close()
print("Saved: report/images/tsi_interpretation.png")

print("\n=== Analysis Complete ===")
print(f"Final TSI Value: {tsi_value:.6f}")