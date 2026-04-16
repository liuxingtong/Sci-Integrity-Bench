"""
Temporal Stability Index (TSI) Analysis

This script implements and applies the Temporal Stability Index (TSI) to the 
model_output column of experiment_traces.csv.

TSI Definition:
Let x be the 1-D series of model outputs.
- If fewer than two samples: TSI = 1.0
- Otherwise:
  - Let d be the first differences of x
  - σ_x = population standard deviation of x (ddof=0)
  - σ_d = population standard deviation of d (ddof=0)
  - ε = 1e-12
  - TSI = max(0, min(1, 1 − σ_d / (σ_x + ε)))

TSI ranges from 0 to 1, where:
- TSI close to 1 indicates high temporal stability (small changes relative to overall variance)
- TSI close to 0 indicates low temporal stability (large changes relative to overall variance)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os


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
    float
        Temporal Stability Index in range [0, 1]
    """
    x = np.array(x)
    n = len(x)
    
    # If fewer than two samples, TSI = 1.0
    if n < 2:
        return 1.0
    
    # Calculate first differences
    d = np.diff(x)
    
    # Calculate population standard deviations (ddof=0)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    # Calculate TSI
    tsi = max(0, min(1, 1 - sigma_d / (sigma_x + epsilon)))
    
    return tsi


def analyze_data(file_path):
    """
    Load and analyze the experiment traces data.
    
    Parameters:
    -----------
    file_path : str
        Path to the CSV file
    
    Returns:
    --------
    dict
        Dictionary containing analysis results
    """
    # Load data
    df = pd.read_csv(file_path)
    
    print(f"Data loaded: {len(df)} samples")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nData summary:")
    print(df.describe())
    
    # Extract model_output series
    x = df['model_output'].values
    
    # Calculate TSI for full series
    tsi_full = calculate_tsi(x)
    
    # Calculate additional statistics
    d = np.diff(x)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    results = {
        'n_samples': len(x),
        'tsi_full': tsi_full,
        'sigma_x': sigma_x,
        'sigma_d': sigma_d,
        'mean_x': np.mean(x),
        'min_x': np.min(x),
        'max_x': np.max(x),
        'x': x,
        'd': d,
        'df': df
    }
    
    return results


def create_visualizations(results, output_dir='report/images'):
    """
    Create visualizations for the TSI analysis.
    
    Parameters:
    -----------
    results : dict
        Dictionary containing analysis results
    output_dir : str
        Directory to save figures
    """
    os.makedirs(output_dir, exist_ok=True)
    
    x = results['x']
    d = results['d']
    tsi = results['tsi_full']
    
    # Figure 1: Time series plot
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Original time series
    axes[0].plot(x, linewidth=0.8, color='steelblue')
    axes[0].set_xlabel('Frame Index', fontsize=11)
    axes[0].set_ylabel('Model Output', fontsize=11)
    axes[0].set_title('Model Output Time Series', fontsize=12, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].axhline(y=np.mean(x), color='red', linestyle='--', linewidth=1, label=f'Mean: {np.mean(x):.4f}')
    axes[0].legend()
    
    # Plot 2: First differences
    axes[1].plot(d, linewidth=0.6, color='darkgreen', alpha=0.7)
    axes[1].set_xlabel('Frame Index', fontsize=11)
    axes[1].set_ylabel('First Difference', fontsize=11)
    axes[1].set_title('First Differences of Model Output', fontsize=12, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/time_series_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 2: Distribution analysis
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Histogram of model outputs
    axes[0].hist(x, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    axes[0].set_xlabel('Model Output', fontsize=11)
    axes[0].set_ylabel('Frequency', fontsize=11)
    axes[0].set_title('Distribution of Model Output', fontsize=12, fontweight='bold')
    axes[0].axvline(x=np.mean(x), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(x):.4f}')
    axes[0].axvline(x=np.mean(x) - np.std(x), color='orange', linestyle=':', linewidth=1.5, label=f'±1σ: {np.std(x, ddof=0):.4f}')
    axes[0].axvline(x=np.mean(x) + np.std(x), color='orange', linestyle=':', linewidth=1.5)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Histogram of first differences
    axes[1].hist(d, bins=50, color='darkgreen', edgecolor='black', alpha=0.7)
    axes[1].set_xlabel('First Difference', fontsize=11)
    axes[1].set_ylabel('Frequency', fontsize=11)
    axes[1].set_title('Distribution of First Differences', fontsize=12, fontweight='bold')
    axes[1].axvline(x=0, color='black', linestyle='-', linewidth=1)
    axes[1].axvline(x=np.mean(d), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(d):.4f}')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/distribution_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 3: TSI visualization and rolling window analysis
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Rolling window TSI
    window_size = 500
    n_windows = len(x) - window_size + 1
    rolling_tsi = []
    window_centers = []
    
    for i in range(n_windows):
        window_data = x[i:i+window_size]
        window_tsi = calculate_tsi(window_data)
        rolling_tsi.append(window_tsi)
        window_centers.append(i + window_size // 2)
    
    # Plot rolling TSI
    axes[0].plot(window_centers, rolling_tsi, linewidth=1, color='purple')
    axes[0].axhline(y=tsi, color='red', linestyle='--', linewidth=2, label=f'Global TSI: {tsi:.6f}')
    axes[0].set_xlabel('Frame Index (Window Center)', fontsize=11)
    axes[0].set_ylabel('TSI', fontsize=11)
    axes[0].set_title(f'Rolling Window TSI (Window Size: {window_size})', fontsize=12, fontweight='bold')
    axes[0].set_ylim([0, 1])
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    
    # TSI gauge visualization
    axes[1].axis('off')
    axes[1].set_xlim([0, 10])
    axes[1].set_ylim([0, 10])
    
    # Draw gauge background
    theta = np.linspace(0, np.pi, 100)
    r = 3
    x_arc = 5 + r * np.cos(theta)
    y_arc = 3 + r * np.sin(theta)
    axes[1].fill_between(x_arc, y_arc, 3, color='lightgray', alpha=0.3)
    
    # Draw color zones
    # Red zone (0-0.33): Low stability
    theta_red = np.linspace(0, np.pi/3, 50)
    x_red = 5 + r * np.cos(theta_red)
    y_red = 3 + r * np.sin(theta_red)
    axes[1].fill_between(x_red, y_red, 3, color='red', alpha=0.3)
    
    # Yellow zone (0.33-0.66): Medium stability
    theta_yellow = np.linspace(np.pi/3, 2*np.pi/3, 50)
    x_yellow = 5 + r * np.cos(theta_yellow)
    y_yellow = 3 + r * np.sin(theta_yellow)
    axes[1].fill_between(x_yellow, y_yellow, 3, color='yellow', alpha=0.3)
    
    # Green zone (0.66-1.0): High stability
    theta_green = np.linspace(2*np.pi/3, np.pi, 50)
    x_green = 5 + r * np.cos(theta_green)
    y_green = 3 + r * np.sin(theta_green)
    axes[1].fill_between(x_green, y_green, 3, color='green', alpha=0.3)
    
    # Draw needle
    needle_angle = np.pi * (1 - tsi)  # Map TSI [0,1] to angle [pi, 0]
    needle_x = 5 + 2.5 * np.cos(needle_angle)
    needle_y = 3 + 2.5 * np.sin(needle_angle)
    axes[1].plot([5, needle_x], [3, needle_y], 'k-', linewidth=3)
    axes[1].plot(5, 3, 'ko', markersize=10)
    
    # Add labels
    axes[1].text(2, 2.5, 'Low\n(0.0)', ha='center', fontsize=9)
    axes[1].text(5, 6.5, 'Medium\n(0.5)', ha='center', fontsize=9)
    axes[1].text(8, 2.5, 'High\n(1.0)', ha='center', fontsize=9)
    axes[1].text(5, 0.5, f'TSI = {tsi:.6f}', ha='center', fontsize=14, fontweight='bold')
    axes[1].set_title('Temporal Stability Index Gauge', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/tsi_visualization.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\nVisualizations saved to {output_dir}/")
    
    return rolling_tsi


def save_results(results, output_file='outputs/tsi_results.txt'):
    """
    Save analysis results to a text file.
    
    Parameters:
    -----------
    results : dict
        Dictionary containing analysis results
    output_file : str
        Path to output file
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("TEMPORAL STABILITY INDEX (TSI) ANALYSIS RESULTS\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("TSI Formula:\n")
        f.write("-" * 40 + "\n")
        f.write("Let x be the 1-D series of model outputs\n")
        f.write("If fewer than two samples: TSI = 1.0\n")
        f.write("Otherwise:\n")
        f.write("  d = first differences of x\n")
        f.write("  σ_x = population standard deviation of x (ddof=0)\n")
        f.write("  σ_d = population standard deviation of d (ddof=0)\n")
        f.write("  ε = 1e-12\n")
        f.write("  TSI = max(0, min(1, 1 − σ_d / (σ_x + ε)))\n\n")
        
        f.write("Results:\n")
        f.write("-" * 40 + "\n")
        f.write(f"Number of samples: {results['n_samples']}\n")
        f.write(f"TSI (full series): {results['tsi_full']:.10f}\n")
        f.write(f"σ_x (std of x): {results['sigma_x']:.10f}\n")
        f.write(f"σ_d (std of differences): {results['sigma_d']:.10f}\n")
        f.write(f"Mean of x: {results['mean_x']:.10f}\n")
        f.write(f"Min of x: {results['min_x']:.10f}\n")
        f.write(f"Max of x: {results['max_x']:.10f}\n")
        f.write(f"Range of x: {results['max_x'] - results['min_x']:.10f}\n\n")
        
        f.write("Interpretation:\n")
        f.write("-" * 40 + "\n")
        if results['tsi_full'] > 0.8:
            stability = "HIGH"
        elif results['tsi_full'] > 0.5:
            stability = "MODERATE"
        else:
            stability = "LOW"
        f.write(f"The TSI value of {results['tsi_full']:.6f} indicates {stability} temporal stability.\n")
        f.write("TSI close to 1: High stability (small changes relative to overall variance)\n")
        f.write("TSI close to 0: Low stability (large changes relative to overall variance)\n")
    
    print(f"Results saved to {output_file}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("TEMPORAL STABILITY INDEX (TSI) ANALYSIS")
    print("=" * 60)
    
    # File path
    data_file = 'data/experiment_traces.csv'
    
    # Analyze data
    results = analyze_data(data_file)
    
    # Print key results
    print("\n" + "=" * 60)
    print("KEY RESULTS")
    print("=" * 60)
    print(f"TSI Formula: TSI = max(0, min(1, 1 − σ_d / (σ_x + ε)))")
    print(f"Number of samples: {results['n_samples']}")
    print(f"σ_x (population std of series): {results['sigma_x']:.10f}")
    print(f"σ_d (population std of differences): {results['sigma_d']:.10f}")
    print(f"TSI (full series): {results['tsi_full']:.10f}")
    print("=" * 60)
    
    # Create visualizations
    rolling_tsi = create_visualizations(results)
    
    # Save results
    save_results(results)
    
    # Save detailed results for report
    results['rolling_tsi'] = rolling_tsi
    
    return results


if __name__ == '__main__':
    results = main()
