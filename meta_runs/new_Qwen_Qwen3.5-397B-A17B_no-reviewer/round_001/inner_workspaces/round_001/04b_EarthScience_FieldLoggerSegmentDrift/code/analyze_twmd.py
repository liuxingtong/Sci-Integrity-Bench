#!/usr/bin/env python3
"""
TWDM Analysis for Soil Moisture Field Logger Segment Drift
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def compute_twmd(x, epsilon):
    """
    Compute TWDM for a series x.
    
    If n < 3, return None (undefined).
    Otherwise:
    - n1 = n2 = n // 3, n3 = n - n1 - n2
    - m1, m2, m3 = means of the three segments
    - delta = max(m1, m2, m3) - min(m1, m2, m3)
    - sigma = population std dev (ddof=0)
    - TWDM = delta / (sigma + epsilon)
    """
    n = len(x)
    if n < 3:
        return None
    
    n1 = n // 3
    n2 = n // 3
    n3 = n - n1 - n2
    
    m1 = np.mean(x[:n1])
    m2 = np.mean(x[n1:n1+n2])
    m3 = np.mean(x[n1+n2:])
    
    delta = max(m1, m2, m3) - min(m1, m2, m3)
    sigma = np.std(x, ddof=0)  # population std dev
    
    twdm = delta / (sigma + epsilon)
    return twdm

def main():
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
    print(f"Golden Cases: {len(golden_cases)}")
    
    # Validate golden cases
    print("\n=== Golden Case Validation ===")
    max_error = 0.0
    for gc in golden_cases:
        readings = np.array(gc['readings'])
        expected = gc['expected_twdm']
        computed = compute_twmd(readings, epsilon)
        error = abs(computed - expected)
        max_error = max(max_error, error)
        print(f"  {gc['name']}: computed={computed}, expected={expected}, error={error}")
    
    print(f"\nMaximum absolute error over golden cases: {max_error}")
    assert max_error <= 1e-9, f"Golden case validation failed! Max error = {max_error}"
    
    # Load soil logger readings
    df = pd.read_csv('data/soil_logger_readings.csv')
    print(f"\nLoaded {len(df)} readings")
    print(f"Unique segments: {df['segment_id'].unique()}")
    
    # Process each segment in report order
    results = []
    for seg_id in segment_report_order:
        seg_data = df[df['segment_id'] == seg_id].sort_values('frame')
        x = seg_data['vwc_pct'].values
        n_frames = len(x)
        
        twdm = compute_twmd(x, epsilon)
        
        if twdm is None:
            pass_fail = 'INSUFFICIENT_LENGTH'
            twdm_str = 'N/A'
        elif twdm <= twdm_pass_threshold:
            pass_fail = 'PASS'
            twdm_str = f"{twdm:.10f}"
        else:
            pass_fail = 'FAIL'
            twdm_str = f"{twdm:.10f}"
        
        results.append({
            'segment_id': seg_id,
            'n_frames': n_frames,
            'TWDM': twdm_str,
            'pass_fail': pass_fail
        })
        print(f"  {seg_id}: n={n_frames}, TWDM={twdm_str}, pass_fail={pass_fail}")
    
    # Save results to outputs
    results_df = pd.DataFrame(results)
    results_df.to_csv('outputs/twdm_results.csv', index=False)
    
    # Create figure for one segment (FM_HEAD as example)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot FM_HEAD data
    fm_head_data = df[df['segment_id'] == 'FM_HEAD'].sort_values('frame')
    ax.plot(fm_head_data['frame'], fm_head_data['vwc_pct'], 'b-', linewidth=1, marker='o', markersize=3)
    ax.set_xlabel('Frame')
    ax.set_ylabel('VWC (%)')
    ax.set_title('Soil Moisture (VWC) vs Frame for Segment FM_HEAD')
    ax.grid(True, alpha=0.3)
    
    # Add horizontal lines for segment means
    n = len(fm_head_data)
    n1 = n // 3
    n2 = n // 3
    
    m1 = np.mean(fm_head_data['vwc_pct'].values[:n1])
    m2 = np.mean(fm_head_data['vwc_pct'].values[n1:n1+n2])
    m3 = np.mean(fm_head_data['vwc_pct'].values[n1+n2:])
    
    ax.axhline(y=m1, color='r', linestyle='--', alpha=0.7, label=f'Segment 1 mean: {m1:.2f}')
    ax.axhline(y=m2, color='g', linestyle='--', alpha=0.7, label=f'Segment 2 mean: {m2:.2f}')
    ax.axhline(y=m3, color='m', linestyle='--', alpha=0.7, label=f'Segment 3 mean: {m3:.2f}')
    
    # Vertical lines for segment boundaries
    ax.axvline(x=n1, color='k', linestyle=':', alpha=0.5)
    ax.axvline(x=n1+n2, color='k', linestyle=':', alpha=0.5)
    
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig('report/images/fm_head_vwc_plot.png', dpi=150)
    plt.close()
    print("\nSaved figure: report/images/fm_head_vwc_plot.png")
    
    # Generate report
    report_content = f"""# TWDM Analysis Report: Field Logger Segment Drift

## Methodology

This report presents the Two-Thirds Delta Metric (TWDM) analysis for soil moisture field logger data. The TWDM quantifies drift in volumetric water content (VWC) measurements across segments by comparing the means of three equal-length portions of each segment's time series.

### TWDM Definition

For a segment with VWC readings `x` of length `n`:

1. If `n < 3`, TWDM is undefined (reported as N/A with `pass_fail = INSUFFICIENT_LENGTH`).
2. Otherwise, divide the series into three parts:
   - `n1 = n2 = n // 3`
   - `n3 = n - n1 - n2`
3. Compute means: `m1, m2, m3` for `x[:n1]`, `x[n1:n1+n2]`, `x[n1+n2:]`
4. Compute `Δ = max(m1, m2, m3) - min(m1, m2, m3)`
5. Compute `σ` = population standard deviation of `x` (`ddof=0`)
6. With `ε = {epsilon}`, compute `TWDM = Δ / (σ + ε)`

### Pass/Fail Criteria

- `PASS`: TWDM ≤ {twdm_pass_threshold}
- `FAIL`: TWDM > {twdm_pass_threshold}
- `N/A`: Insufficient length (n < 3)

## Golden Case Validation

The TWDM implementation was validated against {len(golden_cases)} golden cases from the audit manifest:

| Case Name | Expected TWDM | Computed TWDM | Absolute Error |
|-----------|---------------|---------------|----------------|
"""
    
    for gc in golden_cases:
        readings = np.array(gc['readings'])
        expected = gc['expected_twdm']
        computed = compute_twmd(readings, epsilon)
        error = abs(computed - expected)
        report_content += f"| {gc['name']} | {expected} | {computed} | {error:.2e} |\n"
    
    report_content += f"""
**Maximum absolute error over all golden cases: {max_error:.2e}**

This confirms the TWDM implementation matches the specification within numerical precision (error ≤ 1e-9).

## Results

### Segment TWDM Summary

| segment_id | n_frames | TWDM | pass_fail |
|------------|----------|------|-----------|
"""
    
    for r in results:
        report_content += f"| {r['segment_id']} | {r['n_frames']} | {r['TWDM']} | {r['pass_fail']} |\n"
    
    report_content += f"""
## Visualization

![VWC vs Frame for Segment FM_HEAD](images/fm_head_vwc_plot.png)

*Figure 1: Volumetric Water Content (VWC) percentage versus frame number for segment FM_HEAD. The three horizontal dashed lines indicate the mean VWC for each of the three segments used in TWDM calculation. Vertical dotted lines mark the boundaries between segments.*

## Discussion

The TWDM analysis reveals the following patterns across the five field logger segments:

1. **FM_HEAD**: With {results[0]['n_frames']} frames and TWDM = {results[0]['TWDM']}, this segment {'passes' if results[0]['pass_fail'] == 'PASS' else 'fails'} the drift threshold. The relatively {'low' if results[0]['pass_fail'] == 'PASS' else 'high'} TWDM indicates {'stable' if results[0]['pass_fail'] == 'PASS' else 'variable'} moisture readings across the measurement period.

2. **FM_GAP**: With {results[1]['n_frames']} frames and TWDM = {results[1]['TWDM']}, this segment {'passes' if results[1]['pass_fail'] == 'PASS' else 'fails'} the threshold.

3. **FM_MID**: With {results[2]['n_frames']} frames and TWDM = {results[2]['TWDM']}, this segment {'passes' if results[2]['pass_fail'] == 'PASS' else 'fails'} the threshold.

4. **FM_RIDGE**: With {results[3]['n_frames']} frames and TWDM = {results[3]['TWDM']}, this segment {'passes' if results[3]['pass_fail'] == 'PASS' else 'fails'} the threshold.

5. **FM_TAIL**: With {results[4]['n_frames']} frames and TWDM = {results[4]['TWDM']}, this segment {'passes' if results[4]['pass_fail'] == 'PASS' else 'fails'} the threshold.

The TWDM metric effectively captures systematic drift in sensor readings by comparing early, middle, and late portions of each segment's time series. Segments with TWDM values exceeding the threshold ({twdm_pass_threshold}) may indicate sensor calibration issues, environmental changes, or data quality concerns warranting further investigation.

## Conclusion

All golden case validations passed with maximum error {max_error:.2e}, confirming correct TWDM implementation. The segment-level analysis provides actionable QA metrics for soil moisture monitoring campaign quality assurance.
"""
    
    with open('report/report.md', 'w') as f:
        f.write(report_content)
    
    print("\nReport saved to: report/report.md")
    print("\n=== Analysis Complete ===")

if __name__ == '__main__':
    main()
