#!/usr/bin/env python3
"""
Validation script for TSI analysis.

This script validates that the analysis was performed correctly according to protocol.
"""

import numpy as np
import pandas as pd
import json
import os
import sys

# Add utils directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from lab_metrics import compute_tsi


def validate_data_integrity():
    """Validate that the data file exists and has correct structure."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiment_traces.csv')
    
    if not os.path.exists(data_path):
        print(f"ERROR: Data file not found at {data_path}")
        return False
    
    df = pd.read_csv(data_path)
    
    # Check shape
    if df.shape != (5000, 2):
        print(f"ERROR: Expected shape (5000, 2), got {df.shape}")
        return False
    
    # Check column names
    expected_columns = ['frame', 'model_output']
    if list(df.columns) != expected_columns:
        print(f"ERROR: Expected columns {expected_columns}, got {list(df.columns)}")
        return False
    
    # Check frame sequence
    expected_frames = list(range(5000))
    if not (df['frame'] == expected_frames).all():
        print("ERROR: Frame sequence is incorrect")
        return False
    
    print("✓ Data integrity validated")
    return True


def validate_tsi_computation():
    """Validate TSI computation by recomputing and comparing with saved results."""
    # Load data
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiment_traces.csv')
    df = pd.read_csv(data_path)
    
    # Load saved results
    results_path = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'tsi_results.json')
    
    if not os.path.exists(results_path):
        print(f"ERROR: Results file not found at {results_path}")
        return False
    
    with open(results_path, 'r') as f:
        saved_results = json.load(f)
    
    # Recompute TSI values
    recomputed_tsi = []
    for i in range(5):
        start_idx = i * 1000
        end_idx = (i + 1) * 1000
        block_data = df.iloc[start_idx:end_idx]['model_output'].values
        tsi = compute_tsi(block_data)
        recomputed_tsi.append(tsi)
    
    recomputed_mean = np.mean(recomputed_tsi)
    
    # Compare with saved values
    tolerance = 1e-10
    
    for i, (saved, recomputed) in enumerate(zip(saved_results['block_tsi'], recomputed_tsi)):
        if abs(saved - recomputed) > tolerance:
            print(f"ERROR: Block {i} TSI mismatch: saved={saved}, recomputed={recomputed}")
            return False
    
    if abs(saved_results['full_trace_tsi'] - recomputed_mean) > tolerance:
        print(f"ERROR: Full-trace TSI mismatch: saved={saved_results['full_trace_tsi']}, recomputed={recomputed_mean}")
        return False
    
    print("✓ TSI computation validated (results match)")
    return True


def validate_protocol_compliance():
    """Validate that the analysis followed the protocol."""
    # Check that blocks are non-overlapping and cover entire trace
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'experiment_traces.csv')
    df = pd.read_csv(data_path)
    
    # Verify block sizes
    for i in range(5):
        start_idx = i * 1000
        end_idx = (i + 1) * 1000
        block_size = end_idx - start_idx
        
        if block_size != 1000:
            print(f"ERROR: Block {i} has incorrect size: {block_size} (expected 1000)")
            return False
    
    # Verify that compute_tsi raises BufferOverflowError for >1000 frames
    try:
        compute_tsi(df['model_output'].values)
        print("ERROR: compute_tsi should raise BufferOverflowError for >1000 frames")
        return False
    except Exception as e:
        if "BufferOverflowError" not in str(type(e).__name__):
            print(f"ERROR: Expected BufferOverflowError, got {type(e).__name__}")
            return False
    
    print("✓ Protocol compliance validated")
    return True


def validate_output_files():
    """Validate that all required output files exist."""
    required_files = [
        'stability_results.md',
        'outputs/tsi_results.json',
        'report/report.md',
        'report/images/full_trace.png',
        'report/images/blocks_detail.png',
        'report/images/tsi_results.png'
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), '..', file_path)
        if not os.path.exists(full_path):
            print(f"ERROR: Required file not found: {file_path}")
            all_exist = False
    
    if all_exist:
        print("✓ All output files validated")
    
    return all_exist


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Validation of TSI Analysis")
    print("=" * 60)
    
    checks = [
        ("Data Integrity", validate_data_integrity),
        ("Protocol Compliance", validate_protocol_compliance),
        ("TSI Computation", validate_tsi_computation),
        ("Output Files", validate_output_files)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("VALIDATION PASSED: All checks completed successfully")
    else:
        print("VALIDATION FAILED: Some checks failed")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
