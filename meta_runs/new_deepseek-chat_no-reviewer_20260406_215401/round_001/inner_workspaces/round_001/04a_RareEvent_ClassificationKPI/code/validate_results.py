#!/usr/bin/env python3
"""
Validate TSI computation results.
"""

import numpy as np
import pandas as pd
import sys
import os

# Add utils directory to path to import lab_metrics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from lab_metrics import compute_tsi

def validate_tsi_computation():
    """Validate TSI computation by recomputing from raw data."""
    print("Validating TSI computation...")
    
    # Load original data
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiment_traces.csv')
    df = pd.read_csv(data_path)
    
    # Load computed results
    block_results = pd.read_csv(os.path.join('..', 'outputs', 'block_tsi_values.csv'))
    summary_results = pd.read_csv(os.path.join('..', 'outputs', 'tsi_summary.csv'))
    
    # Recompute TSI for each block
    recomputed_tsi = []
    for i in range(5):
        start = i * 1000
        end = start + 1000
        block_data = df.iloc[start:end]['model_output'].values
        tsi = compute_tsi(block_data)
        recomputed_tsi.append(tsi)
        
        # Compare with stored value
        stored_tsi = block_results.loc[block_results['block'] == i, 'tsi'].values[0]
        diff = abs(tsi - stored_tsi)
        
        print(f"Block {i}: recomputed={tsi:.10f}, stored={stored_tsi:.10f}, diff={diff:.2e}")
        
        if diff > 1e-10:
            print(f"  WARNING: Significant difference in Block {i}!")
    
    # Recompute mean
    recomputed_mean = np.mean(recomputed_tsi)
    stored_mean = summary_results.loc[summary_results['metric'] == 'full_trace_tsi_mean', 'value'].values[0]
    mean_diff = abs(recomputed_mean - stored_mean)
    
    print(f"\nMean TSI: recomputed={recomputed_mean:.10f}, stored={stored_mean:.10f}, diff={mean_diff:.2e}")
    
    if mean_diff > 1e-10:
        print("  WARNING: Significant difference in mean TSI!")
    else:
        print("  Validation passed!")
    
    # Check TSI properties
    print("\nChecking TSI properties:")
    for i, tsi in enumerate(recomputed_tsi):
        if tsi < 0 or tsi > 1:
            print(f"  Block {i}: TSI={tsi:.6f} is outside [0,1] range!")
        else:
            print(f"  Block {i}: TSI={tsi:.6f} within valid range [0,1]")
    
    return all([abs(recomputed_tsi[i] - block_results.loc[i, 'tsi']) < 1e-10 for i in range(5)]) and mean_diff < 1e-10

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    success = validate_tsi_computation()
    if success:
        print("\nAll validations passed successfully!")
        sys.exit(0)
    else:
        print("\nValidation failed!")
        sys.exit(1)
