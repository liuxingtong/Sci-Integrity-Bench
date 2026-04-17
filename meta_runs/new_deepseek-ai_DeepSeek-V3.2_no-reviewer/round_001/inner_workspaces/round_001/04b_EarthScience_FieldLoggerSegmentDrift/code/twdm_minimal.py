#!/usr/bin/env python3
"""
Minimal TWDM analysis for soil moisture campaign QA.
Computes TWDM for each segment and validates against golden cases.
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import os


def compute_twdm(x, epsilon):
    """Compute TWDM for series x with epsilon."""
    n = len(x)
    if n < 3:
        return np.nan
    
    n1 = n // 3
    n2 = n // 3
    n3 = n - n1 - n2
    
    m1 = np.mean(x[:n1])
    m2 = np.mean(x[n1:n1+n2])
    m3 = np.mean(x[n1+n2:])
    
    delta = max(m1, m2, m3) - min(m1, m2, m3)
    sigma = np.std(x, ddof=0)
    
    return delta / (sigma + epsilon)


# Load data
df = pd.read_csv('data/soil_logger_readings.csv')
with open('data/twdm_audit_manifest.json', 'r') as f:
    manifest = json.load(f)

epsilon = manifest['epsilon']
threshold = manifest['twdm_pass_threshold']
segment_order = manifest['segment_report_order']
golden_cases = manifest['golden_cases']

# Validate golden cases
max_error = 0.0
for case in golden_cases:
    computed = compute_twdm(case['readings'], epsilon)
    error = abs(computed - case['expected_twdm'])
    max_error = max(max_error, error)
    
print(f"Maximum absolute error from golden cases: {max_error}")
print(f"Required tolerance: ≤ 1e-9")
print(f"Validation passed: {max_error <= 1e-9}")

# Analyze segments
results = []
for segment_id in segment_order:
    seg_data = df[df['segment_id'] == segment_id].sort_values('frame')
    x = seg_data['vwc_pct'].values
    n = len(x)
    
    if n < 3:
        twdm = np.nan
        pass_fail = 'INSUFFICIENT_LENGTH'
    else:
        twdm = compute_twdm(x, epsilon)
        pass_fail = 'PASS' if twdm <= threshold else 'FAIL'
    
    results.append({
        'segment_id': segment_id,
        'n_frames': n,
        'TWDM': twdm,
        'pass_fail': pass_fail
    })

# Create results dataframe
results_df = pd.DataFrame(results)

# Save results
os.makedirs('outputs', exist_ok=True)
results_df.to_csv('outputs/twdm_results_minimal.csv', index=False)
print("\nTWDM Results:")
print(results_df.to_string(index=False))

# Create plot for one segment (FM_HEAD)
os.makedirs('report/images', exist_ok=True)
segment_id = 'FM_HEAD'
seg_data = df[df['segment_id'] == segment_id].sort_values('frame')

plt.figure(figsize=(10, 6))
plt.plot(seg_data['frame'], seg_data['vwc_pct'], 
         marker='o', markersize=3, linewidth=1, alpha=0.7)
plt.xlabel('Frame')
plt.ylabel('VWC (%)')
plt.title(f'Soil Moisture (VWC) vs Frame for Segment {segment_id}')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/segment_plot_minimal.png', dpi=150)
plt.close()

print(f"\nPlot saved to report/images/segment_plot_minimal.png")
print(f"Segment {segment_id} has TWDM = {results_df[results_df['segment_id']==segment_id]['TWDM'].values[0]:.4f}")