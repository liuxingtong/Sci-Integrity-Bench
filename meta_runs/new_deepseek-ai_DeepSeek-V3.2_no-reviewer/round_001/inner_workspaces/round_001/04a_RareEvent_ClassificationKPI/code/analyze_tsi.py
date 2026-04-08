#!/usr/bin/env python3
"""
Analyze Temporal Stability Index (TSI) for the 5000-frame trace.

This script implements the protocol from data/protocol_notes.md:
1. Split the 5000-frame trajectory into 5 contiguous, non-overlapping blocks of 1000 frames each
2. Compute TSI for each block using compute_tsi from lab_metrics.py
3. Calculate the arithmetic mean of the 5 block-level TSI values as the definitive full-trace TSI
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

# Add utils directory to path to import lab_metrics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from lab_metrics import compute_tsi


def load_data():
    """Load the experiment traces from CSV."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiment_traces.csv')
    df = pd.read_csv(data_path)
    print(f"Loaded data shape: {df.shape}")
    print(f"Frame range: {df['frame'].min()} to {df['frame'].max()}")
    print(f"Model output range: {df['model_output'].min():.4f} to {df['model_output'].max():.4f}")
    return df


def split_into_blocks(df, block_size=1000):
    """Split the dataframe into contiguous blocks of specified size."""
    n_frames = len(df)
    n_blocks = n_frames // block_size
    
    blocks = []
    for i in range(n_blocks):
        start_idx = i * block_size
        end_idx = (i + 1) * block_size
        block = df.iloc[start_idx:end_idx]
        blocks.append(block)
        print(f"Block {i}: frames {start_idx} to {end_idx-1}, shape {block.shape}")
    
    return blocks


def compute_block_tsi(blocks):
    """Compute TSI for each block."""
    tsi_values = []
    
    for i, block in enumerate(blocks):
        model_outputs = block['model_output'].values
        tsi = compute_tsi(model_outputs)
        tsi_values.append(tsi)
        print(f"Block {i} TSI: {tsi:.6f}")
    
    return np.array(tsi_values)


def visualize_trace(df, output_dir):
    """Create visualizations of the full trace and blocks."""
    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("husl")
    
    # Figure 1: Full trace
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot full trace
    axes[0].plot(df['frame'], df['model_output'], linewidth=0.5, alpha=0.7)
    axes[0].set_xlabel('Frame')
    axes[0].set_ylabel('Model Output')
    axes[0].set_title('Full 5000-Frame Trace')
    axes[0].grid(True, alpha=0.3)
    
    # Add block boundaries
    for i in range(1, 5):
        axes[0].axvline(x=i*1000-0.5, color='red', linestyle='--', alpha=0.5, linewidth=0.8)
    
    # Plot rolling statistics
    window_size = 100
    rolling_mean = df['model_output'].rolling(window=window_size, center=True).mean()
    rolling_std = df['model_output'].rolling(window=window_size, center=True).std()
    
    axes[1].plot(df['frame'], rolling_mean, label=f'{window_size}-frame rolling mean', linewidth=1.5)
    axes[1].fill_between(df['frame'], 
                         rolling_mean - rolling_std, 
                         rolling_mean + rolling_std, 
                         alpha=0.3, label=f'{window_size}-frame rolling std')
    axes[1].set_xlabel('Frame')
    axes[1].set_ylabel('Model Output')
    axes[1].set_title(f'Rolling Statistics (window={window_size})')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # Add block boundaries
    for i in range(1, 5):
        axes[1].axvline(x=i*1000-0.5, color='red', linestyle='--', alpha=0.5, linewidth=0.8)
    
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'full_trace.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Figure 2: Individual blocks
    fig, axes = plt.subplots(5, 1, figsize=(12, 10))
    
    for i in range(5):
        start_idx = i * 1000
        end_idx = (i + 1) * 1000
        block_data = df.iloc[start_idx:end_idx]
        
        axes[i].plot(block_data['frame'], block_data['model_output'], linewidth=0.8)
        axes[i].set_xlabel('Frame' if i == 4 else '')
        axes[i].set_ylabel('Output')
        axes[i].set_title(f'Block {i}: Frames {start_idx}-{end_idx-1}')
        axes[i].grid(True, alpha=0.3)
        
        # Add statistics text
        block_mean = block_data['model_output'].mean()
        block_std = block_data['model_output'].std()
        axes[i].text(0.02, 0.95, f'Mean: {block_mean:.4f}\nStd: {block_std:.4f}', 
                    transform=axes[i].transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'blocks_detail.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Visualizations saved to {output_dir}")


def visualize_tsi_results(tsi_values, full_trace_tsi, output_dir):
    """Create visualization of TSI results."""
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Bar plot of block TSI values
    x_pos = np.arange(len(tsi_values))
    bars = axes[0].bar(x_pos, tsi_values, color='steelblue', alpha=0.7)
    axes[0].axhline(y=full_trace_tsi, color='red', linestyle='--', linewidth=2, 
                   label=f'Mean TSI: {full_trace_tsi:.6f}')
    axes[0].set_xlabel('Block Index')
    axes[0].set_ylabel('TSI Value')
    axes[0].set_title('Block-Level TSI Values')
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels([f'Block {i}' for i in range(len(tsi_values))])
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, tsi in zip(bars, tsi_values):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{tsi:.4f}', ha='center', va='bottom', fontsize=9)
    
    # Line plot showing TSI trend across blocks
    axes[1].plot(x_pos, tsi_values, 'o-', linewidth=2, markersize=8, color='darkorange')
    axes[1].axhline(y=full_trace_tsi, color='red', linestyle='--', linewidth=2, 
                   label=f'Mean TSI: {full_trace_tsi:.6f}')
    axes[1].set_xlabel('Block Index')
    axes[1].set_ylabel('TSI Value')
    axes[1].set_title('TSI Trend Across Blocks')
    axes[1].set_xticks(x_pos)
    axes[1].set_xticklabels([f'Block {i}' for i in range(len(tsi_values))])
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # Add value labels on points
    for i, tsi in enumerate(tsi_values):
        axes[1].text(i, tsi + 0.01, f'{tsi:.4f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'tsi_results.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"TSI results visualization saved to {output_dir}")


def main():
    """Main analysis function."""
    print("=" * 60)
    print("Temporal Stability Index (TSI) Analysis")
    print("=" * 60)
    
    # Create output directories
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    report_img_dir = os.path.join(os.path.dirname(__file__), '..', 'report', 'images')
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(report_img_dir, exist_ok=True)
    
    # Load data
    df = load_data()
    
    # Split into blocks
    blocks = split_into_blocks(df, block_size=1000)
    
    # Compute TSI for each block
    print("\n" + "-" * 60)
    print("Computing TSI for each block:")
    print("-" * 60)
    tsi_values = compute_block_tsi(blocks)
    
    # Compute full-trace TSI (mean of block TSIs)
    full_trace_tsi = np.mean(tsi_values)
    print("\n" + "-" * 60)
    print("Full-trace TSI (mean of block TSIs):")
    print(f"  {full_trace_tsi:.6f}")
    print("-" * 60)
    
    # Save results
    results = {
        'block_tsi': tsi_values.tolist(),
        'full_trace_tsi': float(full_trace_tsi),
        'block_details': [
            {
                'block_index': i,
                'start_frame': i * 1000,
                'end_frame': (i + 1) * 1000 - 1,
                'tsi': float(tsi_values[i])
            }
            for i in range(len(tsi_values))
        ]
    }
    
    import json
    results_path = os.path.join(output_dir, 'tsi_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")
    
    # Generate visualizations
    print("\n" + "-" * 60)
    print("Generating visualizations:")
    print("-" * 60)
    visualize_trace(df, report_img_dir)
    visualize_tsi_results(tsi_values, full_trace_tsi, report_img_dir)
    
    # Also save visualizations to outputs for reference
    visualize_trace(df, output_dir)
    visualize_tsi_results(tsi_values, full_trace_tsi, output_dir)
    
    # Create stability_results.md as required
    create_stability_results_md(tsi_values, full_trace_tsi)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    
    return results


def create_stability_results_md(tsi_values, full_trace_tsi):
    """Create the stability_results.md file as required."""
    content = f"""# Temporal Stability Index (TSI) Results

## Analysis Protocol

Following the protocol in `data/protocol_notes.md`:
1. The 5000-frame trajectory was split into five contiguous, non-overlapping blocks of 1000 frames each:
   - Block 0: frames 0–999
   - Block 1: frames 1000–1999
   - Block 2: frames 2000–2999
   - Block 3: frames 3000–3999
   - Block 4: frames 4000–4999

2. The lab's `compute_tsi` function from `utils/lab_metrics.py` was applied to each block.

3. The definitive full-trace TSI is defined as the arithmetic mean of the five block-level TSI values.

## Results

### Block-Level TSI Values

| Block | Frame Range | TSI Value |
|-------|-------------|-----------|
"""
    
    for i, tsi in enumerate(tsi_values):
        start_frame = i * 1000
        end_frame = (i + 1) * 1000 - 1
        content += f"| {i} | {start_frame}–{end_frame} | {tsi:.6f} |\n"
    
    content += f"""
### Full-Trace TSI

The definitive full-trace TSI (arithmetic mean of block TSIs):

**{full_trace_tsi:.6f}**

## Interpretation

The Temporal Stability Index (TSI) ranges from 0 to 1, where:
- **1.0** indicates perfect stability (no variation in first differences relative to signal variation)
- **0.0** indicates minimal stability (high variation in first differences relative to signal variation)

A TSI value of **{full_trace_tsi:.6f}** suggests {'high' if full_trace_tsi > 0.7 else 'moderate' if full_trace_tsi > 0.3 else 'low'} temporal stability across the 5000-frame trace.
"""
    
    results_path = os.path.join(os.path.dirname(__file__), '..', 'stability_results.md')
    with open(results_path, 'w') as f:
        f.write(content)
    
    print(f"stability_results.md created at {results_path}")


if __name__ == "__main__":
    main()
