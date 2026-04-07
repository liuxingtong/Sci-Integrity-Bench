#!/usr/bin/env python3
"""
Temporal Stability Index (TSI) analysis for 5000-frame trajectory.

This script implements the protocol from data/protocol_notes.md:
1. Load the 5000-frame trajectory from experiment_traces.csv
2. Split into 5 contiguous, non-overlapping blocks of 1000 frames each
3. Compute TSI for each block using utils.lab_metrics.compute_tsi
4. Calculate the arithmetic mean as the definitive full-trace TSI
5. Generate visualizations and save results
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# Add parent directory to path to import lab_metrics
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.lab_metrics import compute_tsi


def load_data():
    """Load the experiment traces from CSV."""
    data_path = os.path.join("..", "data", "experiment_traces.csv")
    df = pd.read_csv(data_path)
    print(f"Loaded data shape: {df.shape}")
    print(f"Frame range: {df['frame'].min()} to {df['frame'].max()}")
    print(f"Model output range: {df['model_output'].min():.4f} to {df['model_output'].max():.4f}")
    return df


def split_into_blocks(df, block_size=1000):
    """Split dataframe into contiguous blocks of specified size."""
    n_frames = len(df)
    n_blocks = n_frames // block_size
    
    if n_frames % block_size != 0:
        print(f"Warning: Data length {n_frames} not divisible by block size {block_size}")
    
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
    return tsi_values


def visualize_trajectory(df, blocks, tsi_values, output_dir="../report/images"):
    """Create visualizations of the trajectory and TSI results."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Create figure with subplots
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # 1. Full trajectory
    axes[0].plot(df['frame'], df['model_output'], linewidth=0.5, alpha=0.7)
    axes[0].set_xlabel('Frame')
    axes[0].set_ylabel('Model Output')
    axes[0].set_title('Full 5000-Frame Trajectory')
    axes[0].grid(True, alpha=0.3)
    
    # Add vertical lines to show block boundaries
    for i in range(1, 5):
        axes[0].axvline(x=i*1000 - 0.5, color='red', linestyle='--', alpha=0.5, linewidth=0.8)
    
    # 2. Block-wise visualization
    colors = plt.cm.Set3(np.linspace(0, 1, len(blocks)))
    for i, block in enumerate(blocks):
        axes[1].plot(block['frame'], block['model_output'], 
                    color=colors[i], linewidth=0.8, alpha=0.8,
                    label=f'Block {i} (TSI={tsi_values[i]:.4f})')
    axes[1].set_xlabel('Frame')
    axes[1].set_ylabel('Model Output')
    axes[1].set_title('Trajectory by 1000-Frame Blocks')
    axes[1].legend(loc='upper right', fontsize=8)
    axes[1].grid(True, alpha=0.3)
    
    # 3. TSI values bar chart
    x_pos = np.arange(len(tsi_values))
    bars = axes[2].bar(x_pos, tsi_values, color=colors, alpha=0.7)
    axes[2].set_xlabel('Block Index')
    axes[2].set_ylabel('TSI Value')
    axes[2].set_title('Temporal Stability Index by Block')
    axes[2].set_xticks(x_pos)
    axes[2].set_xticklabels([f'Block {i}\n(Frames {i*1000}-{(i+1)*1000-1})' for i in range(len(tsi_values))])
    axes[2].grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, tsi in zip(bars, tsi_values):
        height = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{tsi:.4f}', ha='center', va='bottom', fontsize=8)
    
    # Add horizontal line for mean TSI
    mean_tsi = np.mean(tsi_values)
    axes[2].axhline(y=mean_tsi, color='red', linestyle='--', alpha=0.7, linewidth=1.5,
                   label=f'Mean TSI = {mean_tsi:.4f}')
    axes[2].legend(loc='upper right')
    
    plt.tight_layout()
    fig_path = os.path.join(output_dir, 'tsi_analysis.png')
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"Saved figure to {fig_path}")
    plt.close()
    
    # Create additional figure: distribution of model outputs
    fig2, axes2 = plt.subplots(1, 2, figsize=(12, 5))
    
    # Histogram of all model outputs
    axes2[0].hist(df['model_output'], bins=50, alpha=0.7, edgecolor='black')
    axes2[0].set_xlabel('Model Output Value')
    axes2[0].set_ylabel('Frequency')
    axes2[0].set_title('Distribution of Model Outputs (Full Trajectory)')
    axes2[0].grid(True, alpha=0.3)
    
    # Box plot by block
    block_outputs = [block['model_output'].values for block in blocks]
    bp = axes2[1].boxplot(block_outputs, labels=[f'Block {i}' for i in range(len(blocks))])
    axes2[1].set_xlabel('Block')
    axes2[1].set_ylabel('Model Output Value')
    axes2[1].set_title('Model Output Distribution by Block')
    axes2[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    fig2_path = os.path.join(output_dir, 'distribution_analysis.png')
    plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
    print(f"Saved distribution figure to {fig2_path}")
    plt.close()


def save_results(tsi_values, output_dir="../outputs"):
    """Save TSI results to files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate mean TSI
    mean_tsi = np.mean(tsi_values)
    
    # Save as CSV
    results_df = pd.DataFrame({
        'block': list(range(len(tsi_values))),
        'start_frame': [i*1000 for i in range(len(tsi_values))],
        'end_frame': [(i+1)*1000-1 for i in range(len(tsi_values))],
        'tsi': tsi_values
    })
    
    csv_path = os.path.join(output_dir, 'tsi_results.csv')
    results_df.to_csv(csv_path, index=False)
    print(f"Saved TSI results to {csv_path}")
    
    # Save summary text file
    summary_path = os.path.join(output_dir, 'tsi_summary.txt')
    with open(summary_path, 'w') as f:
        f.write("Temporal Stability Index (TSI) Analysis\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total frames analyzed: 5000\n")
        f.write(f"Block size: 1000 frames\n")
        f.write(f"Number of blocks: {len(tsi_values)}\n\n")
        
        f.write("Block-wise TSI values:\n")
        for i, tsi in enumerate(tsi_values):
            f.write(f"  Block {i} (frames {i*1000}-{(i+1)*1000-1}): TSI = {tsi:.6f}\n")
        
        f.write(f"\nMean TSI (full-trace definitive value): {mean_tsi:.6f}\n")
        
        # Add interpretation
        f.write("\n" + "=" * 50 + "\n")
        f.write("Interpretation:\n")
        f.write("TSI ranges from 0 (completely unstable) to 1 (perfectly stable).\n")
        f.write(f"A mean TSI of {mean_tsi:.4f} indicates ")
        if mean_tsi > 0.8:
            f.write("high temporal stability.\n")
        elif mean_tsi > 0.6:
            f.write("moderate temporal stability.\n")
        elif mean_tsi > 0.4:
            f.write("moderate temporal instability.\n")
        else:
            f.write("significant temporal instability.\n")
    
    print(f"Saved summary to {summary_path}")
    
    return mean_tsi


def main():
    """Main analysis pipeline."""
    print("Starting TSI analysis for 5000-frame trajectory\n")
    
    # Step 1: Load data
    df = load_data()
    
    # Step 2: Split into blocks
    blocks = split_into_blocks(df, block_size=1000)
    
    # Step 3: Compute TSI for each block
    tsi_values = compute_block_tsi(blocks)
    
    # Step 4: Calculate mean TSI
    mean_tsi = np.mean(tsi_values)
    print(f"\nMean TSI (full-trace definitive value): {mean_tsi:.6f}")
    
    # Step 5: Save results
    mean_tsi = save_results(tsi_values)
    
    # Step 6: Generate visualizations
    visualize_trajectory(df, blocks, tsi_values)
    
    print("\nAnalysis complete!")
    return mean_tsi, tsi_values


if __name__ == "__main__":
    main()