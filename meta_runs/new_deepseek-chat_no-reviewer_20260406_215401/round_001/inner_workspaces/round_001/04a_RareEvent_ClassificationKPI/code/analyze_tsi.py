#!/usr/bin/env python3
"""
Compute Temporal Stability Index (TSI) for 5000-frame trace.

This script follows the protocol in data/protocol_notes.md:
1. Load the 5000-frame trace from experiment_traces.csv
2. Split into 5 non-overlapping blocks of 1000 frames each
3. Compute TSI for each block using compute_tsi from lab_metrics.py
4. Calculate arithmetic mean of block TSIs as definitive full-trace TSI
5. Generate visualizations and save results
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

def load_trace_data():
    """Load the 5000-frame trace from CSV."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiment_traces.csv')
    df = pd.read_csv(data_path)
    print(f"Loaded trace data with {len(df)} frames")
    print(f"Frame range: {df['frame'].min()} to {df['frame'].max()}")
    print(f"Model output range: {df['model_output'].min():.4f} to {df['model_output'].max():.4f}")
    return df

def split_into_blocks(df, block_size=1000):
    """Split dataframe into non-overlapping blocks."""
    n_frames = len(df)
    n_blocks = n_frames // block_size
    blocks = []
    for i in range(n_blocks):
        start_idx = i * block_size
        end_idx = (i + 1) * block_size
        block = df.iloc[start_idx:end_idx]
        blocks.append(block)
        print(f"Block {i}: frames {start_idx} to {end_idx-1}, {len(block)} samples")
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

def plot_trace_overview(df, save_path):
    """Create overview plot of the full trace."""
    plt.figure(figsize=(12, 6))
    
    # Plot full trace
    plt.subplot(2, 1, 1)
    plt.plot(df['frame'], df['model_output'], 'b-', alpha=0.7, linewidth=0.5)
    plt.xlabel('Frame')
    plt.ylabel('Model Output')
    plt.title('Full 5000-Frame Trace')
    plt.grid(True, alpha=0.3)
    
    # Plot with block boundaries
    plt.subplot(2, 1, 2)
    plt.plot(df['frame'], df['model_output'], 'b-', alpha=0.7, linewidth=0.5)
    
    # Add vertical lines for block boundaries
    for i in range(1, 5):
        plt.axvline(x=i*1000 - 0.5, color='r', linestyle='--', alpha=0.7, linewidth=1)
    
    plt.xlabel('Frame')
    plt.ylabel('Model Output')
    plt.title('Trace with Block Boundaries (1000 frames each)')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved trace overview plot to {save_path}")

def plot_block_analysis(blocks, tsi_values, save_path):
    """Create detailed plot showing each block and its TSI."""
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    # Plot each block
    for i, (block, tsi) in enumerate(zip(blocks, tsi_values)):
        ax = axes[i]
        frame_offset = i * 1000
        frames = block['frame'].values
        outputs = block['model_output'].values
        
        ax.plot(frames, outputs, 'b-', alpha=0.8, linewidth=0.8)
        ax.set_xlabel('Frame')
        ax.set_ylabel('Model Output')
        ax.set_title(f'Block {i}: Frames {frame_offset}-{frame_offset+999}\nTSI = {tsi:.6f}')
        ax.grid(True, alpha=0.3)
    
    # Plot TSI summary in the last subplot
    ax = axes[5]
    x_pos = np.arange(len(tsi_values))
    bars = ax.bar(x_pos, tsi_values, color='skyblue', edgecolor='navy')
    
    # Add value labels on bars
    for bar, tsi in zip(bars, tsi_values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{tsi:.4f}', ha='center', va='bottom', fontsize=9)
    
    ax.set_xlabel('Block Index')
    ax.set_ylabel('TSI Value')
    ax.set_title('TSI Values by Block')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f'Block {i}' for i in range(len(tsi_values))])
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 1.1)
    
    # Add mean line
    mean_tsi = np.mean(tsi_values)
    ax.axhline(y=mean_tsi, color='r', linestyle='--', linewidth=2, alpha=0.7, 
               label=f'Mean TSI = {mean_tsi:.6f}')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved block analysis plot to {save_path}")

def save_results(tsi_values, mean_tsi, output_dir):
    """Save TSI results to CSV files."""
    # Save block TSI values
    block_df = pd.DataFrame({
        'block': range(len(tsi_values)),
        'start_frame': [i*1000 for i in range(len(tsi_values))],
        'end_frame': [i*1000 + 999 for i in range(len(tsi_values))],
        'tsi': tsi_values
    })
    block_csv_path = os.path.join(output_dir, 'block_tsi_values.csv')
    block_df.to_csv(block_csv_path, index=False)
    print(f"Saved block TSI values to {block_csv_path}")
    
    # Save summary
    summary_df = pd.DataFrame({
        'metric': ['full_trace_tsi_mean'],
        'value': [mean_tsi]
    })
    summary_csv_path = os.path.join(output_dir, 'tsi_summary.csv')
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"Saved TSI summary to {summary_csv_path}")
    
    return block_csv_path, summary_csv_path

def main():
    """Main analysis pipeline."""
    print("=" * 60)
    print("Temporal Stability Index (TSI) Analysis")
    print("=" * 60)
    
    # Create output directories
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    # Load data
    df = load_trace_data()
    
    # Split into blocks
    blocks = split_into_blocks(df, block_size=1000)
    
    # Compute TSI for each block
    print("\nComputing TSI for each block:")
    tsi_values = compute_block_tsi(blocks)
    
    # Calculate mean TSI
    mean_tsi = np.mean(tsi_values)
    print(f"\nMean TSI (full trace): {mean_tsi:.6f}")
    
    # Generate plots
    print("\nGenerating visualizations...")
    plot_trace_overview(df, 'report/images/full_trace_overview.png')
    plot_block_analysis(blocks, tsi_values, 'report/images/block_analysis.png')
    
    # Save results
    print("\nSaving results...")
    block_csv, summary_csv = save_results(tsi_values, mean_tsi, 'outputs')
    
    # Create stability_results.md
    create_stability_report(tsi_values, mean_tsi, block_csv, summary_csv)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)

def create_stability_report(tsi_values, mean_tsi, block_csv, summary_csv):
    """Create stability_results.md report."""
    report_content = f"""# Temporal Stability Index (TSI) Analysis Report

## Methodology

This analysis follows the protocol specified in `data/protocol_notes.md`:

1. **Data Loading**: The 5000-frame trace was loaded from `experiment_traces.csv`.
2. **Block Splitting**: The trace was split into five contiguous, non-overlapping blocks of 1000 frames each:
   - Block 0: Frames 0-999
   - Block 1: Frames 1000-1999
   - Block 2: Frames 2000-2999
   - Block 3: Frames 3000-3999
   - Block 4: Frames 4000-4999
3. **TSI Computation**: The Temporal Stability Index was computed for each block using the `compute_tsi` function from `utils/lab_metrics.py`.
4. **Aggregation**: The definitive full-trace TSI was calculated as the arithmetic mean of the five block-level TSI values.

## Results

### Block-Level TSI Values

| Block | Start Frame | End Frame | TSI Value |
|-------|-------------|-----------|-----------|
"""
    
    for i, tsi in enumerate(tsi_values):
        report_content += f"| {i} | {i*1000} | {i*1000 + 999} | {tsi:.6f} |\n"
    
    report_content += f"""
### Full-Trace TSI

The definitive Temporal Stability Index for the full 5000-frame trace is:

**TSI = {mean_tsi:.6f}**

This value represents the arithmetic mean of the five block-level TSI values.

## Visualizations

### Figure 1: Full Trace Overview
![Full Trace Overview](images/full_trace_overview.png)

This figure shows the complete 5000-frame trace of model outputs. The bottom panel includes vertical dashed lines indicating the boundaries between the five 1000-frame blocks.

### Figure 2: Block Analysis
![Block Analysis](images/block_analysis.png)

This figure displays each block separately with its computed TSI value. The bottom-right panel shows a bar chart of all block TSI values with the mean TSI indicated by a red dashed line.

## Data Files

- Block-level TSI values: `{block_csv}`
- TSI summary: `{summary_csv}`

## Interpretation

The Temporal Stability Index (TSI) measures the stability of a time series, with values ranging from 0 to 1:
- **TSI ≈ 1**: High temporal stability (low variation in first differences relative to overall variation)
- **TSI ≈ 0**: Low temporal stability (high variation in first differences relative to overall variation)

The computed TSI of {mean_tsi:.6f} indicates {'high' if mean_tsi > 0.7 else 'moderate' if mean_tsi > 0.3 else 'low'} temporal stability across the 5000-frame trace.

## Notes

- All computations were performed using the exact `compute_tsi` implementation from `utils/lab_metrics.py`.
- The analysis adheres to the protocol requirements, including the 1000-frame buffer limitation of the TSI computation function.
- Results are reproducible using the provided code and data.
"""
    
    report_path = 'stability_results.md'
    with open(report_path, 'w') as f:
        f.write(report_content)
    print(f"Saved stability report to {report_path}")

if __name__ == '__main__':
    main()
