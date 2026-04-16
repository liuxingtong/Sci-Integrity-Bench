#!/usr/bin/env python3
"""
Temporal Stability Index (TSI) Analysis

Implementation of TSI for model_output series from experiment_traces.csv
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path


def calculate_tsi(x, epsilon=1e-12):
    """
    Calculate Temporal Stability Index (TSI) for a 1-D series x.
    
    Formula:
    - If fewer than two samples: TSI = 1.0
    - Otherwise:
        d = first differences of x
        σ_x = population std dev of x (ddof=0)
        σ_d = population std dev of d (ddof=0)
        TSI = max(0, min(1, 1 - σ_d / (σ_x + ε)))
    
    Parameters:
    -----------
    x : array-like
        1-D series of model outputs
    epsilon : float
        Small constant to avoid division by zero
        
    Returns:
    --------
    tsi : float
        Temporal Stability Index
    sigma_x : float
        Population standard deviation of x
    sigma_d : float
        Population standard deviation of first differences
    """
    x = np.asarray(x)
    
    # If fewer than two samples
    if len(x) < 2:
        return 1.0, 0.0, 0.0
    
    # Calculate first differences
    d = np.diff(x)
    
    # Calculate population standard deviations (ddof=0)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    # Calculate TSI
    ratio = sigma_d / (sigma_x + epsilon)
    tsi = max(0.0, min(1.0, 1.0 - ratio))
    
    return tsi, sigma_x, sigma_d


def load_data():
    """Load the experiment traces data."""
    # Use absolute path relative to script location
    script_dir = Path(__file__).parent.parent
    data_path = script_dir / "data" / "experiment_traces.csv"
    df = pd.read_csv(data_path)
    print(f"Data loaded: {len(df)} rows")
    print(f"Columns: {df.columns.tolist()}")
    print(f"First few values:\n{df.head()}")
    print(f"Summary statistics:\n{df['model_output'].describe()}")
    return df


def analyze_full_series(df):
    """Calculate TSI for the full series."""
    x = df['model_output'].values
    
    print("\n" + "="*60)
    print("TSI CALCULATION FOR FULL SERIES")
    print("="*60)
    
    tsi, sigma_x, sigma_d = calculate_tsi(x)
    
    print(f"Number of samples: {len(x)}")
    print(f"σ_x (population std dev of x): {sigma_x:.6f}")
    print(f"σ_d (population std dev of first differences): {sigma_d:.6f}")
    print(f"σ_d / σ_x ratio: {sigma_d/(sigma_x + 1e-12):.6f}")
    print(f"Temporal Stability Index (TSI): {tsi:.6f}")
    
    return tsi, sigma_x, sigma_d


def create_visualizations(df, tsi, sigma_x, sigma_d):
    """Create visualizations of the data and TSI calculation."""
    x = df['model_output'].values
    frame = df['frame'].values
    
    # Create output directory for images
    script_dir = Path(__file__).parent.parent
    output_dir = script_dir / "report" / "images"
    output_dir.mkdir(exist_ok=True)
    
    # 1. Time series plot
    plt.figure(figsize=(12, 6))
    plt.plot(frame, x, 'b-', linewidth=0.5, alpha=0.7)
    plt.xlabel('Frame')
    plt.ylabel('Model Output')
    plt.title(f'Model Output Time Series (TSI = {tsi:.4f})')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'time_series.png', dpi=150)
    plt.close()
    
    # 2. Histogram of model outputs
    plt.figure(figsize=(10, 6))
    plt.hist(x, bins=50, edgecolor='black', alpha=0.7)
    plt.xlabel('Model Output')
    plt.ylabel('Frequency')
    plt.title(f'Distribution of Model Outputs (σ_x = {sigma_x:.4f})')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'histogram.png', dpi=150)
    plt.close()
    
    # 3. First differences plot
    d = np.diff(x)
    plt.figure(figsize=(12, 6))
    plt.plot(frame[1:], d, 'r-', linewidth=0.5, alpha=0.7)
    plt.xlabel('Frame')
    plt.ylabel('First Difference')
    plt.title(f'First Differences of Model Output (σ_d = {sigma_d:.4f})')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'first_differences.png', dpi=150)
    plt.close()
    
    # 4. Histogram of first differences
    plt.figure(figsize=(10, 6))
    plt.hist(d, bins=50, edgecolor='black', alpha=0.7, color='red')
    plt.xlabel('First Difference')
    plt.ylabel('Frequency')
    plt.title(f'Distribution of First Differences (σ_d = {sigma_d:.4f})')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'diff_histogram.png', dpi=150)
    plt.close()
    
    # 5. Rolling window TSI analysis
    window_size = 100
    n_windows = len(x) - window_size + 1
    
    if n_windows > 0:
        tsi_values = []
        for i in range(n_windows):
            window_x = x[i:i+window_size]
            window_tsi, _, _ = calculate_tsi(window_x)
            tsi_values.append(window_tsi)
        
        plt.figure(figsize=(12, 6))
        plt.plot(frame[window_size-1:], tsi_values, 'g-', linewidth=1.5)
        plt.axhline(y=tsi, color='r', linestyle='--', label=f'Full series TSI = {tsi:.4f}')
        plt.xlabel('Frame (end of window)')
        plt.ylabel('TSI')
        plt.title(f'Rolling Window TSI (window size = {window_size})')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(output_dir / 'rolling_tsi.png', dpi=150)
        plt.close()
        
        print(f"\nRolling window analysis (window size = {window_size}):")
        print(f"  Mean TSI: {np.mean(tsi_values):.4f}")
        print(f"  Std TSI: {np.std(tsi_values):.4f}")
        print(f"  Min TSI: {np.min(tsi_values):.4f}")
        print(f"  Max TSI: {np.max(tsi_values):.4f}")
    
    print(f"\nVisualizations saved to {output_dir}/")