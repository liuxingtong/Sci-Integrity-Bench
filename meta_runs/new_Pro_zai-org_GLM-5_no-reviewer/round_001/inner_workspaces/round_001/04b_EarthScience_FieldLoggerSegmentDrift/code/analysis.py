import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/soil_logger_readings.csv')
with open('data/twdm_audit_manifest.json', 'r') as f:
    manifest = json.load(f)

epsilon = manifest['epsilon']
twdm_pass_threshold = manifest['twdm_pass_threshold']
segment_report_order = manifest['segment_report_order']
golden_cases = manifest['golden_cases']

def compute_twdm(x):
    """
    Compute TWDM for a series x.
    Returns (twdm, status) where status is 'OK', 'INSUFFICIENT_LENGTH', or 'ZERO_STD'
    """
    n = len(x)
    if n < 3:
        return None, 'INSUFFICIENT_LENGTH'
    
    # Split into thirds
    n1 = n // 3
    n2 = n // 3
    n3 = n - n1 - n2
    
    m1 = np.mean(x[:n1])
    m2 = np.mean(x[n1:n1+n2])
    m3 = np.mean(x[n1+n2:])
    
    delta = max(m1, m2, m3) - min(m1, m2, m3)
    sigma = np.std(x, ddof=0)  # population standard deviation
    
    twdm = delta / (sigma + epsilon)
    return twdm, 'OK'

# Validate golden cases
print("="*60)
print("Golden Case Validation")
print("="*60)
max_error = 0.0
for case in golden_cases:
    name = case['name']
    readings = np.array(case['readings'])
    expected = case['expected_twdm']
    
    twdm, status = compute_twdm(readings)
    error = abs(twdm - expected) if twdm is not None else abs(expected)
    max_error = max(max_error, error)
    
    print(f"\nCase: {name}")
    print(f"  Readings: {readings}")
    print(f"  Computed TWDM: {twdm}")
    print(f"  Expected TWDM: {expected}")
    print(f"  Absolute Error: {error:.2e}")

print(f"\n{'='*60}")
print(f"Maximum Absolute Error: {max_error:.2e}")
print(f"Threshold: 1e-9")
print(f"Validation: {'PASS' if max_error <= 1e-9 else 'FAIL'}")
print(f"{'='*60}\n")

# Process all segments
print("\n" + "="*60)
print("Segment Analysis")
print("="*60)

results = []
for segment_id in segment_report_order:
    segment_data = df[df['segment_id'] == segment_id].sort_values('frame')
    x = segment_data['vwc_pct'].values
    n_frames = len(x)
    
    twdm, status = compute_twdm(x)
    
    if status == 'INSUFFICIENT_LENGTH':
        pass_fail = 'INSUFFICIENT_LENGTH'
        twdm_str = 'N/A'
    elif twdm <= twdm_pass_threshold:
        pass_fail = 'PASS'
        twdm_str = f'{twdm:.6f}'
    else:
        pass_fail = 'FAIL'
        twdm_str = f'{twdm:.6f}'
    
    results.append({
        'segment_id': segment_id,
        'n_frames': n_frames,
        'TWDM': twdm_str,
        'pass_fail': pass_fail,
        'twdm_numeric': twdm
    })
    
    print(f"\nSegment: {segment_id}")
    print(f"  n_frames: {n_frames}")
    print(f"  TWDM: {twdm_str}")
    print(f"  Status: {pass_fail}")

# Create results table
results_df = pd.DataFrame(results)
print("\n" + "="*60)
print("Results Table")
print("="*60)
print(results_df[['segment_id', 'n_frames', 'TWDM', 'pass_fail']].to_string(index=False))

# Save results to outputs
results_df.to_csv('outputs/segment_results.csv', index=False)

# Generate figure for one segment (FM_HEAD as it has most data)
segment_to_plot = 'FM_HEAD'
segment_data = df[df['segment_id'] == segment_to_plot].sort_values('frame')

plt.figure(figsize=(10, 6))
plt.plot(segment_data['frame'], segment_data['vwc_pct'], 'b-', linewidth=1.5, marker='o', markersize=3)
plt.xlabel('Frame', fontsize=12)
plt.ylabel('VWC (%)', fontsize=12)
plt.title(f'Soil Moisture Readings for Segment {segment_to_plot}', fontsize=14)
plt.grid(True, alpha=0.3)

# Add horizontal lines for segment means
n = len(segment_data)
n1 = n // 3
n2 = n // 3

m1 = np.mean(segment_data['vwc_pct'].values[:n1])
m2 = np.mean(segment_data['vwc_pct'].values[n1:n1+n2])
m3 = np.mean(segment_data['vwc_pct'].values[n1+n2:])

plt.axhline(y=m1, color='r', linestyle='--', alpha=0.7, label=f'Mean 1st third: {m1:.2f}%')
plt.axhline(y=m2, color='g', linestyle='--', alpha=0.7, label=f'Mean 2nd third: {m2:.2f}%')
plt.axhline(y=m3, color='purple', linestyle='--', alpha=0.7, label=f'Mean 3rd third: {m3:.2f}%')

plt.legend(loc='best')
plt.tight_layout()
plt.savefig('report/images/fm_head_vwc_plot.png', dpi=150)
plt.close()

print(f"\nFigure saved: report/images/fm_head_vwc_plot.png")

# Save max error for report
with open('outputs/max_error.txt', 'w') as f:
    f.write(f"{max_error}")

print("\nAnalysis complete!")
