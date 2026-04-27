import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Create directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# 1. Load manifest
with open('data/twdm_audit_manifest.json', 'r') as f:
    manifest = json.load(f)

epsilon = manifest['epsilon']
twdm_pass_threshold = manifest['twdm_pass_threshold']
segment_report_order = manifest['segment_report_order']
golden_cases = manifest['golden_cases']

# TWDM function
def compute_twdm(x, eps):
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
    sigma = np.std(x, ddof=0)
    return delta / (sigma + eps)

# 2. Golden cases
max_error = 0.0
for case in golden_cases:
    readings = case['readings']
    expected = case['expected_twdm']
    computed = compute_twdm(readings, epsilon)
    if computed is None and expected is None:
        error = 0.0
    elif computed is not None and expected is not None:
        error = abs(computed - expected)
    else:
        error = float('inf')
    max_error = max(max_error, error)

print(f'Max golden case error: {max_error}')

# 3. Process data
df = pd.read_csv('data/soil_logger_readings.csv')

results = []
for seg_id in segment_report_order:
    seg_df = df[df['segment_id'] == seg_id].sort_values('frame')
    x = seg_df['vwc_pct'].values
    n = len(x)
    
    if n < 3:
        twdm_val = 'N/A'
        pass_fail = 'INSUFFICIENT_LENGTH'
    else:
        twdm_num = compute_twdm(x, epsilon)
        twdm_val = f"{twdm_num:.6f}"
        if twdm_num <= twdm_pass_threshold:
            pass_fail = 'PASS'
        else:
            pass_fail = 'FAIL'
            
    results.append({
        'segment_id': seg_id,
        'n_frames': n,
        'TWDM': twdm_val,
        'pass_fail': pass_fail
    })

results_df = pd.DataFrame(results)
results_df.to_csv('outputs/results.csv', index=False)

# 4. Plot
plot_seg_id = segment_report_order[0]
plot_df = df[df['segment_id'] == plot_seg_id].sort_values('frame')
plt.figure(figsize=(10, 6))
plt.plot(plot_df['frame'], plot_df['vwc_pct'], marker='o', linestyle='-')
plt.title(f'VWC vs Frame for Segment {plot_seg_id}')
plt.xlabel('Frame')
plt.ylabel('VWC (%)')
plt.grid(True)
plt.savefig(f'report/images/segment_{plot_seg_id}.png')
plt.close()

# Generate report
report_content = f"""# Soil-Moisture Campaign QA Report

## Methodology
This report analyzes soil-moisture campaign data to evaluate segment drift using the Time-Windowed Drift Metric (TWDM). 
For each segment, the readings are sorted by frame. If the number of frames $n < 3$, TWDM is undefined. Otherwise, the series is split into three windows of sizes $n_1 = n // 3$, $n_2 = n // 3$, and $n_3 = n - n_1 - n_2$. The means $m_1, m_2, m_3$ of these windows are computed. The drift $\Delta$ is the difference between the maximum and minimum of these means. The TWDM is then calculated as $\Delta / (\sigma + \epsilon)$, where $\sigma$ is the population standard deviation of the series and $\epsilon$ is a small constant to prevent division by zero.

## Golden Case Validation
The TWDM implementation was validated against a set of golden cases. The maximum absolute error versus the expected TWDM over all golden cases is **{max_error:.2e}**.

## Results

The following table summarizes the TWDM and pass/fail status for each segment in the specified report order.

{results_df.to_markdown(index=False)}

## Discussion

The table above shows the drift analysis for each segment. Segments with a TWDM exceeding the threshold of {twdm_pass_threshold} are marked as FAIL, indicating significant drift over time. Segments with fewer than 3 frames are marked as INSUFFICIENT_LENGTH.

![VWC vs Frame for Segment {plot_seg_id}](images/segment_{plot_seg_id}.png)
*Figure 1: VWC vs Frame for Segment {plot_seg_id}.*
"""

with open('report/report.md', 'w') as f:
    f.write(report_content)
