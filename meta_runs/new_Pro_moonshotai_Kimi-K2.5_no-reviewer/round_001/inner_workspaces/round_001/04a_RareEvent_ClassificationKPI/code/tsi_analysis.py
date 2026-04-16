"""
Temporal Stability Index (TSI) Analysis

This script implements the TSI metric for industrial control telemetry data.
TSI measures the temporal stability of model outputs over time.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def compute_tsi(x, epsilon=1e-12):
    """
    Compute Temporal Stability Index (TSI) for a 1-D series.
    
    Parameters:
    -----------
    x : array-like
        1-D series of model outputs
    epsilon : float
        Small constant to avoid division by zero (default: 1e-12)
    
    Returns:
    --------
    float
        TSI value in range [0, 1]
    """
    x = np.array(x)
    n = len(x)
    
    # If fewer than two samples, set TSI = 1.0
    if n < 2:
        return 1.0
    
    # Compute population standard deviation of x (ddof=0)
    sigma_x = np.std(x, ddof=0)
    
    # Compute first differences
    d = np.diff(x)
    
    # Compute population standard deviation of differences (ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    # Compute TSI
    tsi = max(0, min(1, 1 - sigma_d / (sigma_x + epsilon)))
    
    return tsi

def compute_rolling_tsi(x, window_size=100, step=10):
    """
    Compute TSI over rolling windows to analyze temporal stability dynamics.
    
    Parameters:
    -----------
    x : array-like
        1-D series of model outputs
    window_size : int
        Size of rolling window
    step : int
        Step size for rolling window
    
    Returns:
    --------
    tuple
        (window_centers, tsi_values)
    """
    x = np.array(x)
    n = len(x)
    
    window_centers = []
    tsi_values = []
    
    for start in range(0, n - window_size + 1, step):
        end = start + window_size
        window_data = x[start:end]
        tsi = compute_tsi(window_data)
        
        window_centers.append((start + end) // 2)
        tsi_values.append(tsi)
    
    return np.array(window_centers), np.array(tsi_values)

def main():
    # Load data
    data_path = Path("data/experiment_traces.csv")
    df = pd.read_csv(data_path)
    
    print("=" * 60)
    print("TEMPORAL STABILITY INDEX (TSI) ANALYSIS")
    print("=" * 60)
    
    # Data overview
    print("\n1. DATA OVERVIEW")
    print("-" * 40)
    print(f"Total samples: {len(df)}")
    print(f"Frame range: {df['frame'].min()} to {df['frame'].max()}")
    print(f"Model output range: [{df['model_output'].min():.4f}, {df['model_output'].max():.4f}]")
    print(f"Model output mean: {df['model_output'].mean():.4f}")
    print(f"Model output std: {df['model_output'].std():.4f}")
    
    # Extract model output series
    x = df['model_output'].values
    
    # Compute global TSI
    print("\n2. GLOBAL TSI COMPUTATION")
    print("-" * 40)
    tsi_global = compute_tsi(x)
    print(f"Global TSI: {tsi_global:.6f}")
    
    # Compute intermediate statistics
    sigma_x = np.std(x, ddof=0)
    d = np.diff(x)
    sigma_d = np.std(d, ddof=0)
    
    print(f"\nIntermediate statistics:")
    print(f"  σ_x (population std of x): {sigma_x:.6f}")
    print(f"  σ_d (population std of differences): {sigma_d:.6f}")
    print(f"  Ratio σ_d / (σ_x + ε): {sigma_d / (sigma_x + 1e-12):.6f}")
    
    # Compute rolling TSI
    print("\n3. ROLLING TSI ANALYSIS")
    print("-" * 40)
    window_size = 500
    step = 50
    window_centers, tsi_values = compute_rolling_tsi(x, window_size=window_size, step=step)
    
    print(f"Window size: {window_size}")
    print(f"Step size: {step}")
    print(f"Number of windows: {len(tsi_values)}")
    print(f"Rolling TSI range: [{tsi_values.min():.4f}, {tsi_values.max():.4f}]")
    print(f"Rolling TSI mean: {tsi_values.mean():.4f}")
    print(f"Rolling TSI std: {tsi_values.std():.4f}")
    
    # Save results
    results = {
        'global_tsi': tsi_global,
        'sigma_x': sigma_x,
        'sigma_d': sigma_d,
        'n_samples': len(x),
        'rolling_tsi_mean': tsi_values.mean(),
        'rolling_tsi_std': tsi_values.std(),
        'rolling_tsi_min': tsi_values.min(),
        'rolling_tsi_max': tsi_values.max()
    }
    
    # Save to CSV
    results_df = pd.DataFrame([results])
    results_df.to_csv("outputs/tsi_results.csv", index=False)
    print("\nResults saved to outputs/tsi_results.csv")
    
    # Save rolling TSI
    rolling_df = pd.DataFrame({
        'window_center': window_centers,
        'tsi': tsi_values
    })
    rolling_df.to_csv("outputs/rolling_tsi.csv", index=False)
    print("Rolling TSI saved to outputs/rolling_tsi.csv")
    
    # Generate visualizations
    print("\n4. GENERATING VISUALIZATIONS")
    print("-" * 40)
    
    # Figure 1: Time series of model output
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    axes[0].plot(df['frame'], df['model_output'], linewidth=0.8, alpha=0.8, color='#2E86AB')
    axes[0].set_xlabel('Frame Index', fontsize=11)
    axes[0].set_ylabel('Model Output', fontsize=11)
    axes[0].set_title('Model Output Time Series', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # Figure 2: Rolling TSI
    axes[1].plot(window_centers, tsi_values, linewidth=1.5, color='#A23B72', marker='o', markersize=3)
    axes[1].axhline(y=tsi_global, color='#F18F01', linestyle='--', linewidth=2, label=f'Global TSI = {tsi_global:.4f}')
    axes[1].set_xlabel('Frame Index (Window Center)', fontsize=11)
    axes[1].set_ylabel('TSI', fontsize=11)
    axes[1].set_title(f'Rolling TSI (Window Size = {window_size}, Step = {step})', fontsize=12, fontweight='bold')
    axes[1].set_ylim([0, 1.05])
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc='best')
    
    plt.tight_layout()
    plt.savefig("report/images/figure1_time_series_and_tsi.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("  - Saved: report/images/figure1_time_series_and_tsi.png")
    
    # Figure 3: Distribution of model output
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    # Histogram
    axes[0].hist(df['model_output'], bins=50, color='#2E86AB', alpha=0.7, edgecolor='black')
    axes[0].axvline(x=df['model_output'].mean(), color='#F18F01', linestyle='--', linewidth=2, label=f'Mean = {df["model_output"].mean():.4f}')
    axes[0].set_xlabel('Model Output', fontsize=11)
    axes[0].set_ylabel('Frequency', fontsize=11)
    axes[0].set_title('Distribution of Model Output', fontsize=12, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Rolling TSI distribution
    axes[1].hist(tsi_values, bins=30, color='#A23B72', alpha=0.7, edgecolor='black')
    axes[1].axvline(x=tsi_global, color='#F18F01', linestyle='--', linewidth=2, label=f'Global TSI = {tsi_global:.4f}')
    axes[1].set_xlabel('TSI', fontsize=11)
    axes[1].set_ylabel('Frequency', fontsize=11)
    axes[1].set_title('Distribution of Rolling TSI', fontsize=12, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("report/images/figure2_distributions.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("  - Saved: report/images/figure2_distributions.png")
    
    # Figure 4: First differences analysis
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # First differences time series
    axes[0].plot(df['frame'][1:], d, linewidth=0.8, alpha=0.8, color='#06A77D')
    axes[0].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[0].set_xlabel('Frame Index', fontsize=11)
    axes[0].set_ylabel('First Difference', fontsize=11)
    axes[0].set_title('First Differences of Model Output', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # First differences histogram
    axes[1].hist(d, bins=50, color='#06A77D', alpha=0.7, edgecolor='black')
    axes[1].axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    axes[1].axvline(x=np.mean(d), color='#F18F01', linestyle='--', linewidth=2, label=f'Mean = {np.mean(d):.6f}')
    axes[1].set_xlabel('First Difference', fontsize=11)
    axes[1].set_ylabel('Frequency', fontsize=11)
    axes[1].set_title('Distribution of First Differences', fontsize=12, fontweight='bold')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("report/images/figure3_first_differences.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("  - Saved: report/images/figure3_first_differences.png")
    
    # Figure 5: TSI sensitivity analysis
    print("\n5. TSI SENSITIVITY ANALYSIS")
    print("-" * 40)
    
    window_sizes = [50, 100, 200, 500, 1000, 2000]
    tsi_by_window = []
    
    for ws in window_sizes:
        _, tsi_vals = compute_rolling_tsi(x, window_size=ws, step=ws//10)
        tsi_by_window.append({
            'window_size': ws,
            'mean_tsi': tsi_vals.mean(),
            'std_tsi': tsi_vals.std(),
            'min_tsi': tsi_vals.min(),
            'max_tsi': tsi_vals.max()
        })
    
    tsi_sens_df = pd.DataFrame(tsi_by_window)
    tsi_sens_df.to_csv("outputs/tsi_sensitivity.csv", index=False)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.errorbar(tsi_sens_df['window_size'], tsi_sens_df['mean_tsi'], 
                yerr=tsi_sens_df['std_tsi'], marker='o', markersize=8, 
                linewidth=2, capsize=5, color='#2E86AB')
    ax.axhline(y=tsi_global, color='#F18F01', linestyle='--', linewidth=2, label=f'Global TSI = {tsi_global:.4f}')
    ax.set_xlabel('Window Size', fontsize=11)
    ax.set_ylabel('Mean TSI', fontsize=11)
    ax.set_title('TSI Sensitivity to Window Size', fontsize=12, fontweight='bold')
    ax.set_xscale('log')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig("report/images/figure4_tsi_sensitivity.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("  - Saved: report/images/figure4_tsi_sensitivity.png")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nFinal Results:")
    print(f"  Global TSI: {tsi_global:.6f}")
    print(f"  Interpretation: {'High stability' if tsi_global > 0.8 else 'Moderate stability' if tsi_global > 0.5 else 'Low stability'}")
    
    return results

if __name__ == "__main__":
    results = main()
