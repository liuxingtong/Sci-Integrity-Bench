import numpy as np
import pandas as pd

# Test the TSI calculation with simple examples
def calculate_tsi(x, epsilon=1e-12):
    """Calculate Temporal Stability Index (TSI) for a 1-D series x."""
    x = np.asarray(x)
    
    if len(x) < 2:
        return 1.0
    
    d = np.diff(x)
    sigma_x = np.std(x, ddof=0)
    sigma_d = np.std(d, ddof=0)
    
    tsi = 1 - sigma_d / (sigma_x + epsilon)
    tsi = max(0, min(1, tsi))
    
    return tsi

# Test cases
print("TSI Calculation Validation Tests")
print("=" * 40)

# Test 1: Perfectly stable series (no change)
test1 = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
tsi1 = calculate_tsi(test1)
print(f"Test 1 - Constant series: {test1}")
print(f"  σ_x = {np.std(test1, ddof=0):.6f}, σ_d = {np.std(np.diff(test1), ddof=0):.6f}")
print(f"  TSI = {tsi1:.6f} (expected: 1.0)")
print()

# Test 2: Perfectly unstable (maximal change relative to variance)
# This is tricky to construct, but we can test edge cases
test2 = np.array([0, 1, 0, 1, 0, 1])
tsi2 = calculate_tsi(test2)
print(f"Test 2 - Alternating series: {test2}")
print(f"  σ_x = {np.std(test2, ddof=0):.6f}, σ_d = {np.std(np.diff(test2), ddof=0):.6f}")
print(f"  TSI = {tsi2:.6f}")
print()

# Test 3: Single sample
test3 = np.array([5.0])
tsi3 = calculate_tsi(test3)
print(f"Test 3 - Single sample: {test3}")
print(f"  TSI = {tsi3:.6f} (expected: 1.0)")
print()

# Test 4: Realistic example similar to our data
test4 = np.array([-0.1, -0.2, -0.15, -0.05, -0.21])
tsi4 = calculate_tsi(test4)
print(f"Test 4 - Realistic series: {test4}")
print(f"  σ_x = {np.std(test4, ddof=0):.6f}, σ_d = {np.std(np.diff(test4), ddof=0):.6f}")
print(f"  TSI = {tsi4:.6f}")
print()

# Test 5: Edge case where σ_x = 0 (avoid division by zero)
test5 = np.array([2.0, 2.0, 2.0, 2.0, 2.0, 2.0])
tsi5 = calculate_tsi(test5)
print(f"Test 5 - Constant series (σ_x = 0): {test5}")
print(f"  σ_x = {np.std(test5, ddof=0):.6f}, σ_d = {np.std(np.diff(test5), ddof=0):.6f}")
print(f"  TSI = {tsi5:.6f} (expected: 1.0)")
print()

# Verify our actual data calculation
print("Actual Data Verification")
print("=" * 40)
df = pd.read_csv('../data/experiment_traces.csv')
x = df['model_output'].values

# Manual calculation
sigma_x = np.std(x, ddof=0)
sigma_d = np.std(np.diff(x), ddof=0)
epsilon = 1e-12
tsi_manual = 1 - sigma_d / (sigma_x + epsilon)
tsi_manual = max(0, min(1, tsi_manual))

print(f"Dataset: {len(x)} samples")
print(f"σ_x (population std): {sigma_x:.6f}")
print(f"σ_d (population std of differences): {sigma_d:.6f}")
print(f"Ratio σ_d/σ_x: {sigma_d/(sigma_x + epsilon):.6f}")
print(f"TSI (manual): {tsi_manual:.6f}")
print(f"TSI (function): {calculate_tsi(x):.6f}")
print(f"Match: {np.isclose(tsi_manual, calculate_tsi(x))}")