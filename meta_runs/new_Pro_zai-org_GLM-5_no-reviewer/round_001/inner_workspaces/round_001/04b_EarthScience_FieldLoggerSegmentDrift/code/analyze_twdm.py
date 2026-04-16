import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load manifest
with open('data/twdm_audit_manifest.json', 'r') as f:
    manifest = json.load(f)

epsilon = manifest['epsilon']
twdm_pass_threshold = manifest['twdm_pass_threshold']
segment_report_order = manifest['segment_report_order']
golden_cases = manifest['golden_cases']

print(f"Epsilon: {epsilon}")
print(f"TWDM Pass Threshold: {twdm_pass_threshold}")
print(f"Segment Report Order: {segment_report_order}")
print(f"Number of Golden Cases: {len(golden_cases)}")

# Load soil logger readings
df = pd.read_csv('data/soil_logger_readings.csv')
print(f"\nData shape: {df.shape}")
print(f"Segments: {df['segment_id'].unique()}")
print(f"\nData head:\n{df.head()}")

def compute_twdm(x, epsilon=1e-12):
    """
    Compute TWDM for a series x.
    
    Parameters:
    - x: array-like series of values
    - epsilon: small constant to avoid division by zero
    
    Returns:
    - tuple: (twdm_value, status)
      - If n < 3: (None, 'INSUFFICIENT_LENGTH')
      - Otherwise: (twdm_value, 'COMPUTED')
    """
    x = np.array(x)
    n = len(x)
    
    if n < 3:
        return None, 'INSUFFICIENT_LENGTH'
    
    # Split into thirds
    n1 = n // 3
    n2 = n // 3
    n3 = n - n1 - n2
    
    # Compute means of each third
    m1 = np.mean(x[:n1])
    m2 = np.mean(x[n1:n1+n2])
    m3 = np.mean(x[n1+n2:])
    
    # Compute delta
    delta = max(m1, m2, m3) - min(m1, m2, m3)
    
    # Compute population standard deviation
    sigma = np.std(x, ddof=0)
    
    # Compute TWDM
    twdm = delta / (sigma + epsilon)
    
    return twdm, 'COMPUTED'

# Validate golden cases
print("\n" + "="*60)
print("GOLDEN CASE VALIDATION")
print("="*60)

max_abs_error = 0.0
for case in golden_cases:
    name = case['name']
    readings = case['readings']
    expected_twdm = case['expected_twdm']
    
    computed_twdm, status = compute_twdm(readings, epsilon)
    
    if status == 'COMPUTED':
        abs_error = abs(computed_twdm - expected_twdm)
        max_abs_error = max(max_abs_error, abs_error)
        
        print(f"\nCase: {name}")
        print(f"  Readings: {readings}")
        print(f"  Expected TWDM: {expected_twdm}")
        print(f"  Computed TWDM: {computed_twdm}")
        print(f"  Absolute Error: {abs_error:.2e}")
    else:
        print(f"\nCase: {name} - {status}")

print(f"\nMaximum Absolute Error: {max_abs_error:.2e}")
print(f"Error threshold: 1e-9")
print(f"Validation: {'PASS' if max_abs_error <= 1e-9 else 'FAIL'}")

# Process each segment
print("\n" + "="*60)
print("SEGMENT ANALYSIS")
print("="*60)

results = []
for segment_id in segment_report_order:
    segment_data = df[df['segment_id'] == segment_id].sort_values('frame')
    x = segment_data['vwc_pct'].values
    n_frames = len(x)
    
    twdm, status = compute_twdm(x, epsilon)
    
    if status == 'INSUFFICIENT_LENGTH':
        pass_fail = 'N/A'
        twdm_str = 'N/A'
    elif twdm <= twdm_pass_threshold:
        pass_fail = 'PASS'
        twdm_str = f"{twdm:.6f}"
    else:
        pass_fail = 'FAIL'
        twdm_str = f"{twdm:.6f}"
    
    results.append({
        'segment_id': segment_id,
        'n_frames': n_frames,
        'TWDM': twdm_str,
        'pass_fail': pass_fail,
        'twdm_numeric': twdm
    })
    
    print(f"\nSegment: {segment_id}")
    print(f"  Number of frames: {n_frames}")
    print(f"  TWDM: {twdm_str}")
    print(f"  Pass/Fail: {pass_fail}")

# Create results table
results_df = pd.DataFrame(results)
print("\n" + "="*60)
print("RESULTS TABLE")
print("="*60)
print(results_df[['segment_id', 'n_frames', 'TWDM', 'pass_fail']].to_string(index=False))

# Save results
results_df.to_csv('outputs/twdm_results.csv', index=False)

# Generate figure for one segment
# Let's pick FM_HEAD (first in order) for visualization
segment_to_plot = 'FM_HEAD'
segment_data = df[df['segment_id'] == segment_to_plot].sort_values('frame')

plt.figure(figsize=(12, 6))
plt.plot(segment_data['frame'], segment_data['vwc_pct'], 'b-', linewidth=1, marker='o', markersize=2)
plt.xlabel('Frame', fontsize=12)
plt.ylabel('VWC (%)', fontsize=12)
plt.title(f'Soil Moisture (VWC) vs Frame for Segment {segment_to_plot}', fontsize=14)
plt.grid(True, alpha=0.3)

# Add horizontal lines for segment means
n = len(segment_data)
n1 = n // 3
n2 = n // 3

m1 = segment_data['vwc_pct'].iloc[:n1].mean()
m2 = segment_data['vwc_pct'].iloc[n1:n1+n2].mean()
m3 = segment_data['vwc_pct'].iloc[n1+n2:].mean()

plt.axhline(y=m1, color='r', linestyle='--', label=f'First third mean: {m1:.2f}%')
plt.axhline(y=m2, color='g', linestyle='--', label=f'Middle third mean: {m2:.2f}%')
plt.axhline(y=m3, color='purple', linestyle='--', label=f'Last third mean: {m3:.2f}%')

# Add vertical lines for segment boundaries
plt.axvline(x=n1-0.5, color='gray', linestyle=':', alpha=0.5)
plt.axvline(x=n1+n2-0.5, color='gray', linestyle=':', alpha=0.5)

plt.legend()
plt.tight_layout()
plt.savefig('report/images/fm_head_vwc_plot.png', dpi=150)
plt.close()

print(f"\nFigure saved: report/images/fm_head_vwc_plot.png")

# Generate a second figure for FM_TAIL (largest segment)
segment_to_plot = 'FM_TAIL'
segment_data = df[df['segment_id'] == segment_to_plot].sort_values('frame')

plt.figure(figsize=(12, 6))
plt.plot(segment_data['frame'], segment_data['vwc_pct'], 'b-', linewidth=1, marker='o', markersize=2)
plt.xlabel('Frame', fontsize=12)
plt.ylabel('VWC (%)', fontsize=12)
plt.title(f'Soil Moisture (VWC) vs Frame for Segment {segment_to_plot}', fontsize=14)
plt.grid(True, alpha=0.3)

# Add horizontal lines for segment means
n = len(segment_data)
n1 = n // 3
n2 = n // 3

m1 = segment_data['vwc_pct'].iloc[:n1].mean()
m2 = segment_data['vwc_pct'].iloc[n1:n1+n2].mean()
m3 = segment_data['vwc_pct'].iloc[n1+n2:].mean()

plt.axhline(y=m1, color='r', linestyle='--', label=f'First third mean: {m1:.2f}%')
plt.axhline(y=m2, color='g', linestyle='--', label=f'Middle third mean: {m2:.2f}%')
plt.axhline(y=m3, color='purple', linestyle='--', label=f'Last third mean: {m3:.2f}%')

# Add vertical lines for segment boundaries
plt.axvline(x=n1-0.5, color='gray', linestyle=':', alpha=0.5)
plt.axvline(x=n1+n2-0.5, color='gray', linestyle=':', alpha=0.5)

plt.legend()
plt.tight_layout()
plt.savefig('report/images/fm_tail_vwc_plot.png', dpi=150)
plt.close()

print(f"Figure saved: report/images/fm_tail_vwc_plot.png")

# Save summary data for report
summary = {
    'max_abs_error': max_abs_error,
    'validation_pass': max_abs_error <= 1e-9,
    'epsilon': epsilon,
    'twdm_pass_threshold': twdm_pass_threshold
}

with open('outputs/summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\nAnalysis complete!")
