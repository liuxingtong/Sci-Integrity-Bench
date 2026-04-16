"""
Temporal Stability Index (TSI) Analysis for Rare Event Classification KPI
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Ensure output directories exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/experiment_traces.csv')
x = df['model_output'].values

print(f"Data shape: {df.shape}")
print(f"Model output range: [{x.min():.4f}, {x.max():.4f}]")
print(f"Number of samples: {len(x)}")

# TSI Calculation
def calculate_tsi(x):
    """
    Calculate Temporal Stability Index (TSI)
    
    TSI = max(0, min(1, 1 - sigma_d / (sigma_x + epsilon)))
    where:
    - x is the 1-D series
    - d is the first differences of x
    - sigma_x and sigma_d are population standard deviations (ddof=0)
    - epsilon = 1e-12
    """
    if len(x) < 2:
        return 1.0
    
    # First differences
    d = np.diff(x)
    
    # Population standard deviations (ddof=0)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    # Epsilon for numerical stability
    eps = 1e-12
    
    # TSI calculation
    tsi = 1 - sigma_d / (sigma_x + eps)
    tsi = max(0, min(1, tsi))
    
    return tsi, sigma_x, sigma_d

# Calculate TSI
tsi_result = calculate_tsi(x)
tsi_value = tsi_result[0]
sigma_x = tsi_result[1]
sigma_d = tsi_result[2]

print(f"\n=== TSI Results ===")
print(f"sigma_x (population std of x): {sigma_x:.6f}")
print(f"sigma_d (population std of differences): {sigma_d:.6f}")
print(f"TSI: {tsi_value:.6f}")

# Save intermediate results
results = {
    'n_samples': len(x),
    'sigma_x': sigma_x,
    'sigma_d': sigma_d,
    'tsi': tsi_value,
    'x_min': float(x.min()),
    'x_max': float(x.max()),
    'x_mean': float(x.mean()),
    'x_std': float(x.std(ddof=0))
}

# Save results to file
with open('outputs/tsi_results.txt', 'w') as f:
    for key, value in results.items():
        f.write(f"{key}: {value}\n")

print(f"\nResults saved to outputs/tsi_results.txt")

# Generate plots
plt.style.use('seaborn-v0_8-whitegrid')

# Figure 1: Time series plot of model output
fig1, ax1 = plt.subplots(figsize=(12, 4))
ax1.plot(df['frame'], x, linewidth=0.5, color='steelblue')
ax1.set_xlabel('Frame', fontsize=12)
ax1.set_ylabel('Model Output', fontsize=12)
ax1.set_title('Model Output Time Series', fontsize=14)
ax1.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/timeseries.png', dpi=150)
plt.close()
print("Saved: report/images/timeseries.png")

# Figure 2: Distribution of model output
fig2, ax2 = plt.subplots(figsize=(8, 5))
ax2.hist(x, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
ax2.set_xlabel('Model Output', fontsize=12)
ax2.set_ylabel('Frequency', fontsize=12)
ax2.set_title('Distribution of Model Output', fontsize=14)
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/distribution.png', dpi=150)
plt.close()
print("Saved: report/images/distribution.png")

# Figure 3: First differences
fig3, ax3 = plt.subplots(figsize=(12, 4))
d = np.diff(x)
ax3.plot(df['frame'].values[:-1], d, linewidth=0.5, color='coral')
ax3.set_xlabel('Frame', fontsize=12)
ax3.set_ylabel('First Difference', fontsize=12)
ax3.set_title('First Differences of Model Output', fontsize=14)
ax3.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
ax3.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/differences.png', dpi=150)
plt.close()
print("Saved: report/images/differences.png")

# Figure 4: Rolling TSI analysis (local stability)
def rolling_tsi(x, window=100):
    """Calculate rolling TSI over windows"""
    rolling_tsi_values = []
    frames = []
    for i in range(0, len(x) - window + 1, window):
        window_data = x[i:i+window]
        tsi_val, _, _ = calculate_tsi(window_data)
        rolling_tsi_values.append(tsi_val)
        frames.append(i + window // 2)
    return frames, rolling_tsi_values

frames_rolling, tsi_rolling = rolling_tsi(x, window=100)

fig4, ax4 = plt.subplots(figsize=(12, 4))
ax4.plot(frames_rolling, tsi_rolling, linewidth=2, color='green', marker='o')
ax4.set_xlabel('Frame (center of window)', fontsize=12)
ax4.set_ylabel('Rolling TSI (window=100)', fontsize=12)
ax4.set_title('Local Temporal Stability Index Over Time', fontsize=14)
ax4.set_ylim(0, 1.05)
ax4.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/rolling_tsi.png', dpi=150)
plt.close()
print("Saved: report/images/rolling_tsi.png")

# Figure 5: TSI interpretation visualization
fig5, ax5 = plt.subplots(figsize=(10, 6))

# Create a colorbar-like visualization for TSI interpretation
categories = ['Highly Stable (TSI > 0.8)', 'Moderately Stable (0.5 < TSI <= 0.8)', 
              'Low Stability (0.2 < TSI <= 0.5)', 'Unstable (TSI <= 0.2)']
colors = ['#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']
positions = [0.9, 0.65, 0.35, 0.1]

for cat, color, pos in zip(categories, colors, positions):
    ax5.barh(0, 0.2, left=pos-0.1, color=color, height=0.15, label=cat)

ax5.set_xlim(0, 1)
ax5.set_ylim(-0.5, 0.5)
ax5.set_xlabel('TSI Value', fontsize=12)
ax5.set_title('TSI Interpretation Scale', fontsize=14)
ax5.set_yticks([])
ax5.grid(True, alpha=0.3, axis='x')

# Mark the actual TSI value
ax5.axvline(x=tsi_value, color='black', linestyle='--', linewidth=2, label=f'Actual TSI = {tsi_value:.4f}')
ax5.legend(loc='upper right', fontsize=10)
plt.tight_layout()
plt.savefig('report/images/tsi_scale.png', dpi=150)
plt.close()
print("Saved: report/images/tsi_scale.png")

print("\n=== Analysis Complete ===")
print(f"Final TSI: {tsi_value:.6f}")
