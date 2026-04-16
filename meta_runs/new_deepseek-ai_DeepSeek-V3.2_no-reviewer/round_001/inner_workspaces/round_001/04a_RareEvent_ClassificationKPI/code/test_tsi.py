#!/usr/bin/env python3
"""
Test script to verify TSI calculation correctness
"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tsi_analysis import calculate_tsi


def test_tsi_calculation():
    """Test TSI calculation with known values."""
    print("Testing TSI calculation...")
    
    # Test 1: Single value (should return 1.0)
    x1 = [5.0]
    tsi1, sigma_x1, sigma_d1 = calculate_tsi(x1)
    print(f"Test 1 - Single value: TSI={tsi1:.6f} (expected: 1.000000)")
    assert abs(tsi1 - 1.0) < 1e-10, f"Single value test failed: {tsi1}"
    
    # Test 2: Constant series (should return 1.0)
    x2 = [3.0, 3.0, 3.0, 3.0]
    tsi2, sigma_x2, sigma_d2 = calculate_tsi(x2)
    print(f"Test 2 - Constant series: TSI={tsi2:.6f} (expected: 1.000000)")
    assert abs(tsi2 - 1.0) < 1e-10, f"Constant series test failed: {tsi2}"
    
    # Test 3: Perfectly alternating series (maximal change)
    # If x = [0, 1, 0, 1], then σ_x ≈ 0.5, σ_d = 1, ratio = 2, TSI = 0
    x3 = [0.0, 1.0, 0.0, 1.0]
    tsi3, sigma_x3, sigma_d3 = calculate_tsi(x3)
    expected_ratio = sigma_d3 / (sigma_x3 + 1e-12)
    print(f"Test 3 - Alternating series: TSI={tsi3:.6f}, ratio={expected_ratio:.6f} (expected: TSI≈0.0)")
    assert tsi3 < 0.1, f"Alternating series test failed: {tsi3}"
    
    # Test 4: Linear trend (moderate stability)
    x4 = [0.0, 0.1, 0.2, 0.3, 0.4]
    tsi4, sigma_x4, sigma_d4 = calculate_tsi(x4)
    # For linear series, σ_d is constant, σ_x increases with length
    print(f"Test 4 - Linear series: TSI={tsi4:.6f}")
    
    # Test 5: Compare with manual calculation for simple case
    x5 = [1.0, 2.0, 3.0, 4.0]
    tsi5, sigma_x5, sigma_d5 = calculate_tsi(x5)
    # Manual calculation:
    # x = [1,2,3,4], mean=2.5, σ_x = sqrt((1.5^2+0.5^2+0.5^2+1.5^2)/4) = sqrt(5/4)=1.118034
    # d = [1,1,1], σ_d = 0
    # TSI = 1 - 0/(1.118034+ε) = 1
    expected_sigma_x5 = np.sqrt(5/4)  # Population std dev
    expected_tsi5 = 1.0
    print(f"Test 5 - Arithmetic series: TSI={tsi5:.6f}, σ_x={sigma_x5:.6f} (expected: TSI=1.000000, σ_x={expected_sigma_x5:.6f})")
    assert abs(tsi5 - expected_tsi5) < 1e-6, f"Arithmetic series test failed: {tsi5}"
    assert abs(sigma_x5 - expected_sigma_x5) < 1e-6, f"Sigma_x calculation failed: {sigma_x5} vs {expected_sigma_x5}"
    
    print("\nAll tests passed!")
    
    # Test with actual data
    print("\nVerifying full dataset calculation...")
    import pandas as pd
    from pathlib import Path
    
    script_dir = Path(__file__).parent.parent
    data_path = script_dir / "data" / "experiment_traces.csv"
    df = pd.read_csv(data_path)
    x = df['model_output'].values
    
    tsi, sigma_x, sigma_d = calculate_tsi(x)
    
    print(f"Full dataset (n={len(x)}):")
    print(f"  σ_x = {sigma_x:.6f}")
    print(f"  σ_d = {sigma_d:.6f}")
    print(f"  σ_d/σ_x = {sigma_d/(sigma_x + 1e-12):.6f}")
    print(f"  TSI = {tsi:.6f}")
    
    # Verify against previously computed value
    expected_tsi = 0.968440
    assert abs(tsi - expected_tsi) < 1e-6, f"Full dataset TSI mismatch: {tsi} vs {expected_tsi}"
    
    print(f"\nTSI matches expected value: {tsi:.6f} ≈ {expected_tsi:.6f}")


if __name__ == "__main__":
    test_tsi_calculation()