"""
Temporal Stability Index (TSI) Analysis for 5000-frame Industrial Control Telemetry

This script computes the lab-defined TSI metric on the full 5000-frame trace
by following the approved protocol of splitting into 5 contiguous blocks.
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from lab_metrics import compute_tsi

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_data():
    """Load the experiment traces data."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiment_traces.csv')
    df = pd.read_csv(data_path)
    return df

def compute_block_tsis(model_outputs):
    """
    Compute TSI for each of 5 contiguous blocks of 1000 frames.
    
    Parameters
    ----------
    model_outputs : np.ndarray
        Full 5000-frame model output sequence
    
    Returns
    -------
    list of float
        TSI values for each block
    list of tuple
        (start, end) indices for each block
    """
    n_frames = len(model_outputs)
    block_size = 1000
    n_blocks = n_frames // block_size
    
    tsis = []
    block_ranges = []
    
    for i in range(n_blocks):
        start = i * block_size
        end = (i + 1) * block_size
        block_data = model_outputs[start:end]
        tsi = compute_tsi(block_data)
        tsis.append(tsi)
        block_ranges.append((start, end))
        print(f"Block {i+1} (frames {start}-{end-1}): TSI = {tsi:.6f}")
    
    return tsis, block_ranges

def create_visualizations(df, tsis, block_ranges, output_dir):
    """Create publication-quality visualizations."""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    model_outputs = df['model_output'].values
    frames = df['frame'].values
    
    # Figure 1: Full trajectory with block boundaries
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(frames, model_outputs, linewidth=0.5, alpha=0.8, color='#2E86AB')
    
    # Add block boundaries
    for i, (start, end) in enumerate(block_ranges):
        ax.axvline(x=start, color='red', linestyle='--', alpha=0.5, linewidth=1)
        # Add block label
        mid = (start + end) // 2
        ax.text(mid, ax.get_ylim()[1] * 0.95, f'Block {i+1}\nTSI={tsis[i]:.4f}', 
                ha='center', va='top', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    ax.set_xlabel('Frame Index', fontsize=12)
    ax.set_ylabel('Model Output', fontsize=12)
    ax.set_title('Full 5000-Frame Trajectory with TSI Block Analysis', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 5000)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'full_trajectory.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    # Figure 2: TSI values by block (bar chart)
    fig, ax = plt.subplots(figsize=(10, 6))
    block_labels = [f'Block {i+1}\n({block_ranges[i][0]}-{block_ranges[i][1]-1})' for i in range(len(tsis))]
    colors = ['#E63946' if t < 0.5 else '#2A9D8F' for t in tsis]
    bars = ax.bar(block_labels, tsis, color=colors, edgecolor='black', linewidth=1.5)
    
    # Add mean line
    mean_tsi = np.mean(tsis)
    ax.axhline(y=mean_tsi, color='navy', linestyle='--', linewidth=2, label=f'Mean TSI = {mean_tsi:.4f}')
    
    # Add value labels on bars
    for bar, tsi in zip(bars, tsis):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                f'{tsi:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_xlabel('Block (Frame Range)', fontsize=12)
    ax.set_ylabel('Temporal Stability Index (TSI)', fontsize=12)
    ax.set_title('TSI Values by Block with Mean Aggregation', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.legend(loc='upper right', fontsize=11)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'tsi_by_block.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    # Figure 3: Block-level trajectory comparison
    fig, axes = plt.subplots(5, 1, figsize=(14, 12), sharey=True)
    for i, (start, end) in enumerate(block_ranges):
        block_data = model_outputs[start:end]
        block_frames = np.arange(start, end)
        axes[i].plot(block_frames, block_data, linewidth=0.5, alpha=0.8, color='#2E86AB')
        axes[i].set_ylabel(f'Block {i+1}\nTSI={tsis[i]:.4f}', fontsize=10)
        axes[i].set_xlim(start, end)
        axes[i].axhline(y=np.mean(block_data), color='red', linestyle=':', alpha=0.7, linewidth=1)
    
    axes[-1].set_xlabel('Frame Index', fontsize=12)
    fig.suptitle('Block-Level Trajectory Comparison', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'block_comparison.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    # Figure 4: Statistical summary of each block
    block_stats = []
    for i, (start, end) in enumerate(block_ranges):
        block_data = model_outputs[start:end]
        block_stats.append({
            'Block': i + 1,
            'Start': start,
            'End': end - 1,
            'Mean': np.mean(block_data),
            'Std': np.std(block_data),
            'Min': np.min(block_data),
            'Max': np.max(block_data),
            'Range': np.max(block_data) - np.min(block_data),
            'TSI': tsis[i]
        })
    
    stats_df = pd.DataFrame(block_stats)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Mean by block
    axes[0, 0].bar(stats_df['Block'], stats_df['Mean'], color='#264653', edgecolor='black')
    axes[0, 0].set_xlabel('Block')
    axes[0, 0].set_ylabel('Mean Output')
    axes[0, 0].set_title('Mean Output by Block', fontweight='bold')
    
    # Std by block
    axes[0, 1].bar(stats_df['Block'], stats_df['Std'], color='#2A9D8F', edgecolor='black')
    axes[0, 1].set_xlabel('Block')
    axes[0, 1].set_ylabel('Std Dev')
    axes[0, 1].set_title('Standard Deviation by Block', fontweight='bold')
    
    # Range by block
    axes[1, 0].bar(stats_df['Block'], stats_df['Range'], color='#E9C46A', edgecolor='black')
    axes[1, 0].set_xlabel('Block')
    axes[1, 0].set_ylabel('Range (Max - Min)')
    axes[1, 0].set_title('Output Range by Block', fontweight='bold')
    
    # TSI by block
    colors = ['#E63946' if t < 0.5 else '#2A9D8F' for t in stats_df['TSI']]
    axes[1, 1].bar(stats_df['Block'], stats_df['TSI'], color=colors, edgecolor='black')
    axes[1, 1].axhline(y=mean_tsi, color='navy', linestyle='--', linewidth=2)
    axes[1, 1].set_xlabel('Block')
    axes[1, 1].set_ylabel('TSI')
    axes[1, 1].set_title('TSI by Block', fontweight='bold')
    axes[1, 1].set_ylim(0, 1)
    
    fig.suptitle('Block-Level Statistical Summary', fontsize=14, fontweight='bold')
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'block_statistics.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return stats_df

def main():
    """Main analysis function."""
    print("="*60)
    print("Temporal Stability Index (TSI) Analysis")
    print("="*60)
    
    # Load data
    print("\n1. Loading data...")
    df = load_data()
    print(f"   Loaded {len(df)} frames")
    print(f"   Frame range: {df['frame'].min()} to {df['frame'].max()}")
    print(f"   Output range: {df['model_output'].min():.4f} to {df['model_output'].max():.4f}")
    
    # Compute block-level TSIs
    print("\n2. Computing TSI for each 1000-frame block...")
    model_outputs = df['model_output'].values
    tsis, block_ranges = compute_block_tsis(model_outputs)
    
    # Compute mean TSI
    mean_tsi = np.mean(tsis)
    print(f"\n3. Aggregated Results:")
    print(f"   Mean TSI (definitive full-trace TSI): {mean_tsi:.6f}")
    print(f"   Min block TSI: {min(tsis):.6f}")
    print(f"   Max block TSI: {max(tsis):.6f}")
    print(f"   Std of block TSIs: {np.std(tsis):.6f}")
    
    # Create visualizations
    print("\n4. Creating visualizations...")
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'report', 'images')
    stats_df = create_visualizations(df, tsis, block_ranges, output_dir)
    print(f"   Figures saved to {output_dir}")
    
    # Save results to outputs directory
    outputs_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    
    results = {
        'block_tsis': tsis,
        'block_ranges': block_ranges,
        'mean_tsi': mean_tsi,
        'stats_df': stats_df
    }
    
    # Save detailed results
    results_path = os.path.join(outputs_dir, 'tsi_results.txt')
    with open(results_path, 'w') as f:
        f.write("Temporal Stability Index (TSI) Results\n")
        f.write("="*50 + "\n\n")
        f.write("Block-Level TSI Values:\n")
        for i, (tsi, (start, end)) in enumerate(zip(tsis, block_ranges)):
            f.write(f"  Block {i+1} (frames {start}-{end-1}): {tsi:.6f}\n")
        f.write(f"\nDefinitive Full-Trace TSI (Mean): {mean_tsi:.6f}\n")
    print(f"   Results saved to {results_path}")
    
    # Save statistics
    stats_path = os.path.join(outputs_dir, 'block_statistics.csv')
    stats_df.to_csv(stats_path, index=False)
    print(f"   Statistics saved to {stats_path}")
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)
    
    return results

if __name__ == "__main__":
    results = main()