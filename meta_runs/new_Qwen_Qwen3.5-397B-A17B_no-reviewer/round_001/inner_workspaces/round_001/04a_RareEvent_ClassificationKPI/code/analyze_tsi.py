"""
Temporal Stability Index (TSI) Analysis for 5000-frame trace.

Following protocol_notes.md:
- Split trajectory into 5 contiguous, non-overlapping blocks of 1000 frames each
- Compute TSI on each block using lab_metrics.compute_tsi
- Report arithmetic mean of block-level TSIs as the definitive full-trace TSI
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add utils to path for lab_metrics import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.lab_metrics import compute_tsi

# Paths
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiment_traces.csv')
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'outputs')
REPORT_IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'report', 'images')

# Ensure output directories exist
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(REPORT_IMAGES_DIR, exist_ok=True)

def load_data():
    """Load the experiment traces CSV."""
    df = pd.read_csv(DATA_PATH)
    return df['model_output'].values

def compute_block_tsis(data, block_size=1000):
    """
    Split data into blocks and compute TSI for each.
    
    Returns:
        block_tsIs: list of TSI values for each block
        block_data: list of data arrays for each block
    """
    n_frames = len(data)
    n_blocks = n_frames // block_size
    
    block_tsIs = []
    block_data = []
    
    for i in range(n_blocks):
        start_idx = i * block_size
        end_idx = start_idx + block_size
        block = data[start_idx:end_idx]
        tsi = compute_tsi(block)
        block_tsIs.append(tsi)
        block_data.append(block)
        print(f"Block {i+1} (frames {start_idx}-{end_idx-1}): TSI = {tsi:.6f}")
    
    return block_tsIs, block_data

def create_visualizations(data, block_tsIs, block_data):
    """Generate all required figures."""
    
    # Figure 1: Full trace overview
    plt.figure(figsize=(12, 6))
    plt.plot(range(len(data)), data, linewidth=0.5, color='steelblue')
    plt.xlabel('Frame')
    plt.ylabel('Model Output')
    plt.title('Full 5000-Frame Temporal Trace')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_IMAGES_DIR, 'full_trace.png'), dpi=150)
    plt.close()
    
    # Figure 2: Block-level TSI values
    plt.figure(figsize=(10, 6))
    block_indices = range(1, len(block_tsIs) + 1)
    bars = plt.bar(block_indices, block_tsIs, color='coral', edgecolor='black', alpha=0.7)
    plt.xlabel('Block Number')
    plt.ylabel('Temporal Stability Index (TSI)')
    plt.title('Block-Level TSI Values (1000 frames each)')
    plt.xticks(block_indices)
    plt.ylim(0, 1.05)
    
    # Add value labels on bars
    for i, v in enumerate(block_tsIs):
        plt.text(i + 1, v + 0.02, f'{v:.4f}', ha='center', fontsize=10)
    
    # Add mean line
    mean_tsi = np.mean(block_tsIs)
    plt.axhline(y=mean_tsi, color='red', linestyle='--', linewidth=2, label=f'Mean TSI = {mean_tsi:.4f}')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_IMAGES_DIR, 'block_tsi.png'), dpi=150)
    plt.close()
    
    # Figure 3: Individual block traces with TSI annotations
    fig, axes = plt.subplots(5, 1, figsize=(12, 10), sharex=True)
    for i, ax in enumerate(axes):
        start_frame = i * 1000
        end_frame = start_frame + 1000
        frames = range(start_frame, end_frame)
        ax.plot(frames, block_data[i], linewidth=0.5, color='navy')
        ax.set_ylabel('Output')
        ax.set_title(f'Block {i+1} (Frames {start_frame}-{end_frame-1}): TSI = {block_tsIs[i]:.4f}')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    axes[-1].set_xlabel('Frame')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_IMAGES_DIR, 'block_traces.png'), dpi=150)
    plt.close()
    
    # Figure 4: Statistical summary - distribution of model outputs
    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=50, color='teal', edgecolor='black', alpha=0.7)
    plt.xlabel('Model Output Value')
    plt.ylabel('Frequency')
    plt.title('Distribution of Model Outputs Across 5000 Frames')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_IMAGES_DIR, 'output_distribution.png'), dpi=150)
    plt.close()
    
    # Figure 5: Rolling statistics to show stability patterns
    window_size = 100
    rolling_mean = pd.Series(data).rolling(window=window_size).mean()
    rolling_std = pd.Series(data).rolling(window=window_size).std()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    ax1.plot(range(len(data)), data, linewidth=0.3, alpha=0.5, label='Raw Data')
    ax1.plot(range(len(data)), rolling_mean, color='red', linewidth=2, label=f'Rolling Mean (w={window_size})')
    ax1.set_ylabel('Model Output')
    ax1.set_title('Rolling Statistics Analysis')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(range(len(data)), rolling_std, color='green', linewidth=2)
    ax2.set_ylabel('Rolling Std Dev')
    ax2.set_xlabel('Frame')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_IMAGES_DIR, 'rolling_stats.png'), dpi=150)
    plt.close()

def save_results(block_tsIs, mean_tsi, data):
    """Save intermediate results to outputs directory."""
    results = {
        'block_tsIs': block_tsIs,
        'mean_tsi': mean_tsi,
        'n_frames': len(data),
        'n_blocks': len(block_tsIs),
        'data_stats': {
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data))
        }
    }
    
    # Save as text file for reference
    with open(os.path.join(OUTPUTS_DIR, 'tsi_results.txt'), 'w') as f:
        f.write("Temporal Stability Index (TSI) Analysis Results\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total frames analyzed: {results['n_frames']}\n")
        f.write(f"Number of blocks: {results['n_blocks']}\n")
        f.write(f"Block size: 1000 frames\n\n")
        f.write("Block-level TSI values:\n")
        for i, tsi in enumerate(block_tsIs):
            f.write(f"  Block {i+1}: {tsi:.6f}\n")
        f.write(f"\nMean TSI (Full-trace metric): {mean_tsi:.6f}\n\n")
        f.write("Data Statistics:\n")
        for key, val in results['data_stats'].items():
            f.write(f"  {key}: {val:.6f}\n")
    
    return results

def main():
    print("Loading data...")
    data = load_data()
    print(f"Loaded {len(data)} frames")
    
    print("\nComputing block-level TSIs...")
    block_tsIs, block_data = compute_block_tsis(data)
    
    mean_tsi = np.mean(block_tsIs)
    print(f"\nMean TSI (Full-trace metric): {mean_tsi:.6f}")
    
    print("\nGenerating visualizations...")
    create_visualizations(data, block_tsIs, block_data)
    
    print("\nSaving results...")
    results = save_results(block_tsIs, mean_tsi, data)
    
    print("\nAnalysis complete!")
    print(f"Figures saved to: {REPORT_IMAGES_DIR}")
    print(f"Results saved to: {OUTPUTS_DIR}")
    
    return results

if __name__ == '__main__':
    main()
