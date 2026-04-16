#!/usr/bin/env python3
"""
Main script for TSI analysis
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tsi_analysis import load_data, analyze_full_series, create_visualizations


def main():
    """Main analysis function."""
    print("="*60)
    print("TEMPORAL STABILITY INDEX (TSI) ANALYSIS")
    print("="*60)
    
    # Load data
    df = load_data()
    
    # Analyze full series
    tsi, sigma_x, sigma_d = analyze_full_series(df)
    
    # Create visualizations
    create_visualizations(df, tsi, sigma_x, sigma_d)
    
    # Save results to file
    script_dir = Path(__file__).parent.parent
    results_dir = script_dir / "outputs"
    os.makedirs(results_dir, exist_ok=True)
    
    results_file = results_dir / "tsi_results.txt"
    with open(results_file, "w") as f:
        f.write("TEMPORAL STABILITY INDEX (TSI) RESULTS\n")
        f.write("="*50 + "\n\n")
        f.write(f"Data file: experiment_traces.csv\n")
        f.write(f"Number of samples: {len(df)}\n\n")
        f.write("TSI Formula:\n")
        f.write("  If n < 2: TSI = 1.0\n")
        f.write("  Otherwise:\n")
        f.write("    d = first differences of x\n")
        f.write("    σ_x = population std dev of x (ddof=0)\n")
        f.write("    σ_d = population std dev of d (ddof=0)\n")
        f.write("    ε = 1e-12\n")
        f.write("    TSI = max(0, min(1, 1 - σ_d / (σ_x + ε)))\n\n")
        f.write("Results:\n")
        f.write(f"  σ_x (population std dev of x): {sigma_x:.6f}\n")
        f.write(f"  σ_d (population std dev of first differences): {sigma_d:.6f}\n")
        f.write(f"  σ_d / σ_x ratio: {sigma_d/(sigma_x + 1e-12):.6f}\n")
        f.write(f"  Temporal Stability Index (TSI): {tsi:.6f}\n")
    
    print(f"\nResults saved to {results_dir}/tsi_results.txt")
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()