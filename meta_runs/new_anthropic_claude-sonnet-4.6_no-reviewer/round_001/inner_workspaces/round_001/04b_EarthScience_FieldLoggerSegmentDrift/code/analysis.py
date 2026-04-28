import json
import math
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Paths
DATA_CSV = 'data/soil_logger_readings.csv'
MANIFEST = 'data/twdm_audit_manifest.json'
OUT_DIR  = 'outputs'
IMG_DIR  = 'report/images'
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# Load manifest
with open(MANIFEST) as f:
    manifest = json.load(f)

epsilon             = manifest['epsilon']
twdm_pass_threshold = manifest['twdm_pass_threshold']
segment_report_order = manifest['segment_report_order']
golden_cases        = manifest['golden_cases']

print(f'epsilon={epsilon}, threshold={twdm_pass_threshold}')
print(f'segment_report_order={segment_report_order}')

# TWDM function
def compute_twdm(x, eps):
    x = list(x)
    n = len(x)
    if n < 3:
        return None, 'INSUFFICIENT_LENGTH'
    n1 = n // 3
    n2 = n // 3
    # n3 = n - n1 - n2  (not needed explicitly)
    seg1 = x[:n1]
    seg2 = x[n1:n1+n2]
    seg3 = x[n1+n2:]
    m1 = sum(seg1) / len(seg1)
    m2 = sum(seg2) / len(seg2)
    m3 = sum(seg3) / len(seg3)
    delta = max(m1, m2, m3) - min(m1, m2, m3)
    mean_all = sum(x) / n
    variance = sum((v - mean_all)**2 for v in x) / n
    sigma = math.sqrt(variance)
    twdm = delta / (sigma + eps)
    return twdm, None

# Golden-case validation
max_abs_error = 0.0
print('\n=== Golden Case Validation ===')
for gc in golden_cases:
    twdm_val, _ = compute_twdm(gc['readings'], epsilon)
    err = abs(twdm_val - gc['expected_twdm'])
    max_abs_error = max(max_abs_error, err)
    print(f"  {gc['name']}: computed={twdm_val:.15f}, expected={gc['expected_twdm']:.15f}, err={err:.2e}")

print(f'\nMax absolute error over golden cases: {max_abs_error:.2e}')
assert max_abs_error <= 1e-9, f'Golden case error too large: {max_abs_error}'

# Load readings
df = pd.read_csv(DATA_CSV)
print(f'\nLoaded {len(df)} rows, segments: {df["segment_id"].unique().tolist()}')

# Per-segment TWDM
results = []
for seg_id in segment_report_order:
    seg_df = df[df['segment_id'] == seg_id].sort_values('frame')
    x = seg_df['vwc_pct'].tolist()
    n = len(x)
    twdm_val, special = compute_twdm(x, epsilon)
    if special == 'INSUFFICIENT_LENGTH':
        twdm_str  = 'N/A'
        pass_fail = 'INSUFFICIENT_LENGTH'
        twdm_num  = None
    else:
        twdm_str  = f'{twdm_val:.8f}'
        pass_fail = 'PASS' if twdm_val <= twdm_pass_threshold else 'FAIL'
        twdm_num  = twdm_val
    results.append({
        'segment_id':   seg_id,
        'n_frames':     n,
        'TWDM':         twdm_str,
        'pass_fail':    pass_fail,
        'twdm_numeric': twdm_num
    })
    print(f'  {seg_id}: n={n}, TWDM={twdm_str}, {pass_fail}')

# Save results table
results_df = pd.DataFrame(results)[['segment_id','n_frames','TWDM','pass_fail']]
results_df.to_csv(f'{OUT_DIR}/segment_twdm_results.csv', index=False)
print(f'\nResults saved to {OUT_DIR}/segment_twdm_results.csv')

# Figure 1: VWC vs frame for FM_HEAD
seg_plot = 'FM_HEAD'
seg_df_plot = df[df['segment_id'] == seg_plot].sort_values('frame')

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(seg_df_plot['frame'], seg_df_plot['vwc_pct'],
        color='steelblue', linewidth=0.8, alpha=0.85)
ax.set_xlabel('Frame', fontsize=12)
ax.set_ylabel('VWC (%)', fontsize=12)
ax.set_title(f'Volumetric Water Content vs Frame  |  Segment: {seg_plot}', fontsize=13)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
fig.savefig(f'{IMG_DIR}/vwc_fm_head.png', dpi=150)
plt.close(fig)
print(f'Figure saved: {IMG_DIR}/vwc_fm_head.png')

# Figure 2: All segments multi-panel
fig2, axes = plt.subplots(len(segment_report_order), 1,
                          figsize=(12, 3*len(segment_report_order)), sharex=False)
for i, seg_id in enumerate(segment_report_order):
    seg_df2 = df[df['segment_id'] == seg_id].sort_values('frame')
    ax2 = axes[i]
    ax2.plot(seg_df2['frame'], seg_df2['vwc_pct'],
             linewidth=0.7, color='darkorange', alpha=0.85)
    row = results[i]
    ax2.set_title(
        f"{seg_id}  |  n={row['n_frames']}  |  TWDM={row['TWDM']}  |  {row['pass_fail']}",
        fontsize=10)
    ax2.set_ylabel('VWC (%)', fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.4)
axes[-1].set_xlabel('Frame', fontsize=11)
fig2.suptitle('VWC vs Frame  —  All Segments', fontsize=14, y=1.01)
plt.tight_layout()
fig2.savefig(f'{IMG_DIR}/vwc_all_segments.png', dpi=150, bbox_inches='tight')
plt.close(fig2)
print(f'Figure saved: {IMG_DIR}/vwc_all_segments.png')

# Save summary
summary = {
    'max_golden_error': max_abs_error,
    'epsilon': epsilon,
    'twdm_pass_threshold': twdm_pass_threshold,
    'results': results
}
with open(f'{OUT_DIR}/summary.json', 'w') as f:
    json.dump(summary, f, indent=2)
print('\nDone.')
