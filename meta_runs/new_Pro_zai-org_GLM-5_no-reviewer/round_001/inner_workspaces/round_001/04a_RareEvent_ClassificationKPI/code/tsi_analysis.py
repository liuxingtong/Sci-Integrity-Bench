"""
Temporal Stability Index (TSI) Analysis

This script implements and applies the TSI metric to the model_output column
of the experiment_traces.csv data.

TSI Definition:
- Let x be the 1-D series of model outputs
- If fewer than two samples, set TSI = 1.0
- Otherwise:
  - Let d be the first differences of x
  - σ_x = population standard deviation of x (ddof=0)
  - σ_d = population standard deviation of d (ddof=0)
  - ε = 1e-12
  - TSI = max(0, min(1, 1 − σ_d / (σ_x + ε)))
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# Create output directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

def compute_tsi(x):
    """
    Compute the Temporal Stability Index (TSI) for a 1-D series.
    
    Parameters:
    -----------
    x : array-like
        1-D series of model outputs
    
    Returns:
    --------
    float : TSI value in range [0, 1]
    
    Formula:
    --------
    - If fewer than 2 samples, TSI = 1.0
    - Otherwise:
      - d = first differences of x
      - σ_x = population std of x (ddof=0)
      - σ_d = population std of d (ddof=0)
      - ε = 1e-12
      - TSI = max(0, min(1, 1 − σ_d / (σ_x + ε)))
    """
    x = np.asarray(x, dtype=np.float64)
    
    # Handle edge case: fewer than 2 samples
    if len(x) < 2:
        return 1.0
    
    # Compute first differences
    d = np.diff(x)
    
    # Population standard deviations (ddof=0)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    # Small constant to avoid division by zero
    epsilon = 1e-12
    
    # Compute TSI
    tsi = 1 - sigma_d / (sigma_x + epsilon)
    
    # Clamp to [0, 1]
    tsi = max(0.0, min(1.0, tsi))
    
    return tsi


def main():
    # Load data
    print("Loading data...")
    df = pd.read_csv('data/experiment_traces.csv')
    
    print(f"Data shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst few rows:")
    print(df.head())
    print(f"\nLast few rows:")
    print(df.tail())
    print(f"\nBasic statistics:")
    print(df['model_output'].describe())
    
    # Extract model_output series
    x = df['model_output'].values
    
    # Compute TSI for the full series
    tsi_full = compute_tsi(x)
    print(f"\n{'='*60}")
    print(f"TEMPORAL STABILITY INDEX (TSI) RESULTS")
    print(f"{'='*60}")
    print(f"TSI for full series: {tsi_full:.6f}")
    
    # Compute intermediate values for reporting
    d = np.diff(x)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    epsilon = 1e-12
    
    print(f"\nIntermediate calculations:")
    print(f"  Number of samples (n): {len(x)}")
    print(f"  σ_x (population std of x): {sigma_x:.6f}")
    print(f"  σ_d (population std of first differences): {sigma_d:.6f}")
    print(f"  σ_d / (σ_x + ε): {sigma_d / (sigma_x + epsilon):.6f}")
    print(f"  1 - σ_d / (σ_x + ε): {1 - sigma_d / (sigma_x + epsilon):.6f}")
    
    # Save results to file
    results = {
        'tsi': tsi_full,
        'n_samples': len(x),
        'sigma_x': sigma_x,
        'sigma_d': sigma_d,
        'ratio': sigma_d / (sigma_x + epsilon)
    }
    
    # Save as text file
    with open('outputs/tsi_results.txt', 'w') as f:
        f.write("Temporal Stability Index (TSI) Results\n")
        f.write("="*50 + "\n\n")
        f.write(f"TSI Formula:\n")
        f.write(f"  TSI = max(0, min(1, 1 - σ_d / (σ_x + ε)))\n\n")
        f.write(f"Where:\n")
        f.write(f"  x = 1-D series of model outputs\n")
        f.write(f"  d = first differences of x\n")
        f.write(f"  σ_x = population std of x (ddof=0)\n")
        f.write(f"  σ_d = population std of d (ddof=0)\n")
        f.write(f"  ε = 1e-12\n\n")
        f.write(f"Results:\n")
        f.write(f"  Number of samples: {len(x)}\n")
        f.write(f"  σ_x: {sigma_x:.6f}\n")
        f.write(f"  σ_d: {sigma_d:.6f}\n")
        f.write(f"  σ_d / (σ_x + ε): {sigma_d / (sigma_x + epsilon):.6f}\n")
        f.write(f"  TSI: {tsi_full:.6f}\n")
    
    print(f"\nResults saved to outputs/tsi_results.txt")
    
    # Create visualizations
    print("\nCreating visualizations...")
    
    # Figure 1: Full time series
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(df['frame'], df['model_output'], linewidth=0.5, alpha=0.8)
    ax.set_xlabel('Frame Index', fontsize=12)
    ax.set_ylabel('Model Output', fontsize=12)
    ax.set_title(f'Model Output Time Series (n={len(x)}, TSI={tsi_full:.4f})', fontsize=14)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/time_series_full.png', dpi=150)
    plt.close()
    print("  Saved: report/images/time_series_full.png")
    
    # Figure 2: Distribution of model outputs
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    axes[0].hist(df['model_output'], bins=50, edgecolor='black', alpha=0.7)
    axes[0].set_xlabel('Model Output', fontsize=12)
    axes[0].set_ylabel('Frequency', fontsize=12)
    axes[0].set_title('Distribution of Model Outputs', fontsize=14)
    axes[0].axvline(np.mean(x), color='red', linestyle='--', label=f'Mean: {np.mean(x):.3f}')
    axes[0].legend()
    
    axes[1].hist(d, bins=50, edgecolor='black', alpha=0.7, color='orange')
    axes[1].set_xlabel('First Difference', fontsize=12)
    axes[1].set_ylabel('Frequency', fontsize=12)
    axes[1].set_title('Distribution of First Differences', fontsize=14)
    axes[1].axvline(np.mean(d), color='red', linestyle='--', label=f'Mean: {np.mean(d):.3f}')
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig('report/images/distributions.png', dpi=150)
    plt.close()
    print("  Saved: report/images/distributions.png")
    
    # Figure 3: Rolling TSI analysis
    window_sizes = [100, 500, 1000]
    fig, axes = plt.subplots(len(window_sizes) + 1, 1, figsize=(14, 10))
    
    # Original series
    axes[0].plot(df['frame'], df['model_output'], linewidth=0.5, alpha=0.8)
    axes[0].set_ylabel('Model Output', fontsize=12)
    axes[0].set_title('Model Output Time Series', fontsize=14)
    axes[0].grid(True, alpha=0.3)
    
    # Rolling TSI for different window sizes
    for i, window in enumerate(window_sizes):
        rolling_tsi = []
        for j in range(len(x) - window + 1):
            window_data = x[j:j+window]
            rolling_tsi.append(compute_tsi(window_data))
        
        axes[i+1].plot(df['frame'][window-1:], rolling_tsi, linewidth=1)
        axes[i+1].set_ylabel(f'TSI (w={window})', fontsize=12)
        axes[i+1].set_title(f'Rolling TSI (Window Size = {window})', fontsize=12)
        axes[i+1].set_ylim([0, 1.05])
        axes[i+1].grid(True, alpha=0.3)
        axes[i+1].axhline(tsi_full, color='red', linestyle='--', alpha=0.7, 
                         label=f'Full TSI: {tsi_full:.4f}')
        axes[i+1].legend(loc='lower right')
    
    axes[-1].set_xlabel('Frame Index', fontsize=12)
    plt.tight_layout()
    plt.savefig('report/images/rolling_tsi.png', dpi=150)
    plt.close()
    print("  Saved: report/images/rolling_tsi.png")
    
    # Figure 4: TSI interpretation visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create a bar chart showing the components
    categories = ['σ_x', 'σ_d', 'σ_d/σ_x', 'TSI']
    values = [sigma_x, sigma_d, sigma_d/sigma_x, tsi_full]
    colors = ['steelblue', 'coral', 'green', 'purple']
    
    bars = ax.bar(categories, values, color=colors, edgecolor='black', alpha=0.8)
    ax.set_ylabel('Value', fontsize=12)
    ax.set_title('TSI Components Analysis', fontsize=14)
    
    # Add value labels on bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{val:.4f}', ha='center', va='bottom', fontsize=11)
    
    ax.set_ylim(0, max(values) * 1.2)
    plt.tight_layout()
    plt.savefig('report/images/tsi_components.png', dpi=150)
    plt.close()
    print("  Saved: report/images/tsi_components.png")
    
    # Figure 5: Segment analysis - TSI for different segments of the data
    segment_size = 500
    n_segments = len(x) // segment_size
    segment_tsis = []
    segment_starts = []
    
    for i in range(n_segments):
        segment_data = x[i*segment_size:(i+1)*segment_size]
        segment_tsis.append(compute_tsi(segment_data))
        segment_starts.append(i*segment_size)
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    
    # Top: Time series with segment boundaries
    axes[0].plot(df['frame'], df['model_output'], linewidth=0.5, alpha=0.8)
    for i in range(n_segments):
        axes[0].axvline(i*segment_size, color='red', linestyle='--', alpha=0.3)
    axes[0].set_ylabel('Model Output', fontsize=12)
    axes[0].set_title(f'Model Output with Segment Boundaries (Segment Size = {segment_size})', fontsize=14)
    axes[0].grid(True, alpha=0.3)
    
    # Bottom: TSI per segment
    segment_centers = [s + segment_size//2 for s in segment_starts]
    axes[1].bar(segment_centers, segment_tsis, width=segment_size*0.8, 
                edgecolor='black', alpha=0.7)
    axes[1].axhline(tsi_full, color='red', linestyle='--', linewidth=2,
                   label=f'Full Series TSI: {tsi_full:.4f}')
    axes[1].set_xlabel('Frame Index', fontsize=12)
    axes[1].set_ylabel('TSI', fontsize=12)
    axes[1].set_title('TSI by Segment', fontsize=14)
    axes[1].set_ylim([0, 1.05])
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/segment_analysis.png', dpi=150)
    plt.close()
    print("  Saved: report/images/segment_analysis.png")
    
    print("\nAnalysis complete!")
    return tsi_full


if __name__ == '__main__':
    main()
