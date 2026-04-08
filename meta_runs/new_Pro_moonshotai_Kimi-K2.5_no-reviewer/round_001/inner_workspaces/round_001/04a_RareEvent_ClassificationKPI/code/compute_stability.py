"""
Temporal Stability Index (TSI) Analysis for 5000-frame trace.

This script computes the lab's Temporal Stability Index on the full 5000-frame
trace by splitting into 5 contiguous blocks of 1000 frames each, as per protocol.
"""

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
from lab_metrics import compute_tsi

# Paths
DATA_PATH = Path(__file__).parent.parent / 'data' / 'experiment_traces.csv'
OUTPUTS_PATH = Path(__file__).parent.parent / 'outputs'
REPORT_IMAGES_PATH = Path(__file__).parent.parent / 'report' / 'images'

# Create output directories
OUTPUTS_PATH.mkdir(parents=True, exist_ok=True)
REPORT_IMAGES_PATH.mkdir(parents=True, exist_ok=True)


def load_trace(filepath):
    """Load the experiment trace from CSV."""
    df = pd.read_csv(filepath)
    return df['model_output'].values


def split_into_blocks(data, block_size=1000):
    """Split data into contiguous non-overlapping blocks."""
    n_blocks = len(data) // block_size
    blocks = []
    for i in range(n_blocks):
        start = i * block_size
        end = start + block_size
        blocks.append(data[start:end])
    return blocks


def compute_full_trace_tsi(data, block_size=1000):
    """
    Compute TSI for full trace by splitting into blocks and averaging.
    
    Returns:
        dict with block TSIs, mean TSI, and block indices
    """
    blocks = split_into_blocks(data, block_size)
    block_tsis = []
    
    for i, block in enumerate(blocks):
        tsi = compute_tsi(block)
        block_tsis.append({
            'block_index': i,
            'frame_start': i * block_size,
            'frame_end': (i + 1) * block_size - 1,
            'tsi': tsi,
            'mean': np.mean(block),
            'std': np.std(block)
        })
    
    # Compute arithmetic mean of block TSIs
    mean_tsi = np.mean([b['tsi'] for b in block_tsis])
    
    return {
        'block_tsis': block_tsis,
        'mean_tsi': mean_tsi,
        'n_blocks': len(blocks)
    }


def plot_trace_overview(data, results, save_path):
    """Create overview plot of the full trace with block boundaries."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    
    # Plot 1: Full trace with block boundaries
    ax1 = axes[0]
    frames = np.arange(len(data))
    ax1.plot(frames, data, linewidth=0.5, alpha=0.7, color='steelblue')
    
    # Add block boundaries
    block_size = 1000
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
    for i in range(5):
        start = i * block_size
        end = (i + 1) * block_size
        ax1.axvspan(start, end, alpha=0.1, color=colors[i])
        ax1.axvline(x=start, color=colors[i], linestyle='--', alpha=0.5, linewidth=1)
        # Add block label
        mid = (start + end) / 2
        ax1.text(mid, ax1.get_ylim()[1] * 0.9, f'Block {i+1}\nTSI={results["block_tsis"][i]["tsi"]:.4f}',
                ha='center', fontsize=9, color=colors[i], fontweight='bold')
    
    ax1.set_xlabel('Frame Index', fontsize=11)
    ax1.set_ylabel('Model Output', fontsize=11)
    ax1.set_title('Full 5000-Frame Trace with Block Boundaries and TSI Values', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 5000)
    
    # Plot 2: TSI values by block
    ax2 = axes[1]
    block_indices = [b['block_index'] + 1 for b in results['block_tsis']]
    tsi_values = [b['tsi'] for b in results['block_tsis']]
    
    bars = ax2.bar(block_indices, tsi_values, color=colors, edgecolor='black', linewidth=1.2)
    
    # Add mean line
    ax2.axhline(y=results['mean_tsi'], color='red', linestyle='-', linewidth=2, 
                label=f'Mean TSI = {results["mean_tsi"]:.4f}')
    
    # Add value labels on bars
    for bar, tsi in zip(bars, tsi_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{tsi:.4f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax2.set_xlabel('Block Number', fontsize=11)
    ax2.set_ylabel('Temporal Stability Index (TSI)', fontsize=11)
    ax2.set_title('TSI Values by Block (Mean TSI = {:.4f})'.format(results['mean_tsi']), 
                  fontsize=12, fontweight='bold')
    ax2.set_ylim(0, 1.1)
    ax2.set_xticks(block_indices)
    ax2.legend(loc='lower right', fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved trace overview plot to {save_path}")


def plot_block_details(data, results, save_path):
    """Create detailed view of each block."""
    fig, axes = plt.subplots(5, 1, figsize=(14, 12))
    
    block_size = 1000
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
    
    for i, (ax, block_info) in enumerate(zip(axes, results['block_tsis'])):
        start = block_info['frame_start']
        end = block_info['frame_end'] + 1
        block_data = data[start:end]
        frames = np.arange(start, end)
        
        ax.plot(frames, block_data, linewidth=0.8, color=colors[i], alpha=0.8)
        ax.fill_between(frames, block_data, alpha=0.2, color=colors[i])
        
        # Add statistics text
        stats_text = (f"TSI: {block_info['tsi']:.4f}\n"
                      f"Mean: {block_info['mean']:.4f}\n"
                      f"Std: {block_info['std']:.4f}")
        ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_ylabel('Model Output', fontsize=10)
        ax.set_title(f'Block {i+1}: Frames {start}-{end-1}', fontsize=11, fontweight='bold', color=colors[i])
        ax.grid(True, alpha=0.3)
        ax.set_xlim(start, end-1)
    
    axes[-1].set_xlabel('Frame Index', fontsize=11)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved block details plot to {save_path}")


def plot_tsi_summary(results, save_path):
    """Create summary visualization of TSI results."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
    block_indices = [b['block_index'] + 1 for b in results['block_tsis']]
    tsi_values = [b['tsi'] for b in results['block_tsis']]
    
    # Left plot: TSI values with mean
    ax1 = axes[0]
    bars = ax1.bar(block_indices, tsi_values, color=colors, edgecolor='black', linewidth=1.5)
    ax1.axhline(y=results['mean_tsi'], color='red', linestyle='--', linewidth=2.5,
                label=f'Overall Mean TSI = {results["mean_tsi"]:.4f}')
    
    for bar, tsi in zip(bars, tsi_values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.015,
                f'{tsi:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax1.set_xlabel('Block Number', fontsize=12)
    ax1.set_ylabel('Temporal Stability Index (TSI)', fontsize=12)
    ax1.set_title('TSI by Block', fontsize=13, fontweight='bold')
    ax1.set_ylim(0, 1.15)
    ax1.set_xticks(block_indices)
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Right plot: TSI stability (deviation from mean)
    ax2 = axes[1]
    deviations = [tsi - results['mean_tsi'] for tsi in tsi_values]
    bar_colors = ['green' if d >= 0 else 'orange' for d in deviations]
    bars2 = ax2.bar(block_indices, deviations, color=bar_colors, edgecolor='black', linewidth=1.5)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    
    for bar, dev in zip(bars2, deviations):
        height = bar.get_height()
        va = 'bottom' if height >= 0 else 'top'
        offset = 0.002 if height >= 0 else -0.002
        ax2.text(bar.get_x() + bar.get_width()/2., height + offset,
                f'{dev:+.4f}', ha='center', va=va, fontsize=10, fontweight='bold')
    
    ax2.set_xlabel('Block Number', fontsize=12)
    ax2.set_ylabel('Deviation from Mean TSI', fontsize=12)
    ax2.set_title(f'TSI Deviation from Mean ({results["mean_tsi"]:.4f})', fontsize=13, fontweight='bold')
    ax2.set_xticks(block_indices)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved TSI summary plot to {save_path}")


def save_results_to_markdown(results, data, output_path):
    """Save results to markdown file."""
    with open(output_path, 'w') as f:
        f.write("# Temporal Stability Index (TSI) Analysis Results\n\n")
        f.write("## Methodology\n\n")
        f.write("The Temporal Stability Index (TSI) was computed on the full 5000-frame trace ")
        f.write("following the protocol specified in `data/protocol_notes.md`.\n\n")
        f.write("### Procedure\n\n")
        f.write("1. Loaded the 5000-frame trace from `data/experiment_traces.csv`\n")
        f.write("2. Split the trajectory into **five contiguous, non-overlapping blocks** of 1000 frames each:\n")
        f.write("   - Block 1: Frames 0-999\n")
        f.write("   - Block 2: Frames 1000-1999\n")
        f.write("   - Block 3: Frames 2000-2999\n")
        f.write("   - Block 4: Frames 3000-3999\n")
        f.write("   - Block 5: Frames 4000-4999\n")
        f.write("3. Called `compute_tsi` from `utils/lab_metrics.py` on each block's model-output series\n")
        f.write("4. Computed the **definitive full-trace TSI** as the arithmetic mean of the five block-level TSI values\n\n")
        
        f.write("### TSI Definition\n\n")
        f.write("Per `lab_metrics.py`, TSI is computed as:\n\n")
        f.write("```\nTSI = clip(1 - std(d) / (std(x) + eps), 0, 1)\n```\n\n")
        f.write("where `x` is the sequence, `d` is the first differences of `x`, and `eps = 1e-12` for numerical stability.\n\n")
        
        f.write("## Results\n\n")
        f.write("### Block-Level TSI Values\n\n")
        f.write("| Block | Frame Range | TSI | Mean Output | Std Output |\n")
        f.write("|-------|-------------|-----|-------------|------------|\n")
        for b in results['block_tsis']:
            f.write(f"| {b['block_index']+1} | {b['frame_start']}-{b['frame_end']} | {b['tsi']:.6f} | {b['mean']:.6f} | {b['std']:.6f} |\n")
        
        f.write("\n### Aggregated Full-Trace TSI\n\n")
        f.write(f"**Mean TSI (Full 5000-frame trace): {results['mean_tsi']:.6f}**\n\n")
        
        # Compute additional statistics
        tsi_values = [b['tsi'] for b in results['block_tsis']]
        f.write(f"- TSI Standard Deviation across blocks: {np.std(tsi_values):.6f}\n")
        f.write(f"- TSI Range: {np.min(tsi_values):.6f} - {np.max(tsi_values):.6f}\n")
        f.write(f"- Coefficient of Variation: {np.std(tsi_values)/results['mean_tsi']*100:.2f}%\n\n")
        
        f.write("## Interpretation\n\n")
        f.write(f"The overall Temporal Stability Index of **{results['mean_tsi']:.4f}** indicates ")
        if results['mean_tsi'] > 0.9:
            f.write("**excellent temporal stability**. ")
        elif results['mean_tsi'] > 0.7:
            f.write("**good temporal stability**. ")
        elif results['mean_tsi'] > 0.5:
            f.write("**moderate temporal stability**. ")
        else:
            f.write("**poor temporal stability**. ")
        
        f.write("The TSI values across blocks show ")
        if np.std(tsi_values) < 0.05:
            f.write("**consistent stability** throughout the trace.\n")
        elif np.std(tsi_values) < 0.1:
            f.write("**some variation** in stability across the trace.\n")
        else:
            f.write("**significant variation** in stability across the trace.\n")
        
        # Overall data statistics
        f.write(f"\n### Full Trace Statistics\n\n")
        f.write(f"- Total frames: {len(data)}\n")
        f.write(f"- Overall mean: {np.mean(data):.6f}\n")
        f.write(f"- Overall std: {np.std(data):.6f}\n")
        f.write(f"- Min value: {np.min(data):.6f}\n")
        f.write(f"- Max value: {np.max(data):.6f}\n")
    
    print(f"Saved results to {output_path}")


def main():
    print("="*60)
    print("Temporal Stability Index (TSI) Analysis")
    print("="*60)
    
    # Load data
    print("\n[1/5] Loading trace data...")
    data = load_trace(DATA_PATH)
    print(f"      Loaded {len(data)} frames")
    
    # Compute TSI
    print("\n[2/5] Computing TSI for each block...")
    results = compute_full_trace_tsi(data)
    print(f"      Computed TSI for {results['n_blocks']} blocks")
    for b in results['block_tsis']:
        print(f"      Block {b['block_index']+1}: TSI = {b['tsi']:.6f}")
    print(f"\n      *** MEAN TSI (Full Trace): {results['mean_tsi']:.6f} ***")
    
    # Generate visualizations
    print("\n[3/5] Generating visualizations...")
    plot_trace_overview(data, results, REPORT_IMAGES_PATH / 'trace_overview.png')
    plot_block_details(data, results, REPORT_IMAGES_PATH / 'block_details.png')
    plot_tsi_summary(results, REPORT_IMAGES_PATH / 'tsi_summary.png')
    
    # Save results to markdown
    print("\n[4/5] Saving results to stability_results.md...")
    save_results_to_markdown(results, data, OUTPUTS_PATH / 'stability_results.md')
    
    # Also save to root for visibility
    save_results_to_markdown(results, data, Path(__file__).parent.parent / 'stability_results.md')
    
    # Save numerical results as JSON
    print("\n[5/5] Saving numerical results...")
    import json
    with open(OUTPUTS_PATH / 'tsi_results.json', 'w') as f:
        json.dump({
            'mean_tsi': float(results['mean_tsi']),
            'block_tsis': [
                {
                    'block': b['block_index'] + 1,
                    'frame_range': f"{b['frame_start']}-{b['frame_end']}",
                    'tsi': float(b['tsi']),
                    'mean': float(b['mean']),
                    'std': float(b['std'])
                }
                for b in results['block_tsis']
            ]
        }, f, indent=2)
    print(f"      Saved to {OUTPUTS_PATH / 'tsi_results.json'}")
    
    print("\n" + "="*60)
    print("Analysis Complete!")
    print(f"Mean TSI (Full 5000-frame trace): {results['mean_tsi']:.6f}")
    print("="*60)
    
    return results


if __name__ == '__main__':
    main()
