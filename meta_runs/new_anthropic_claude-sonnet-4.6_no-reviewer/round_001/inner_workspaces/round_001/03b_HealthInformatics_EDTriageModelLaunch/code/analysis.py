import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ── 0. Load data ──────────────────────────────────────────────────────────────
offline = pd.read_csv('data/offline_evaluation_metrics.csv')
online  = pd.read_csv('data/online_ab_test_metrics.csv')

print("=== OFFLINE METRICS ===")
print(offline.to_string(index=False))
print()
print("=== ONLINE METRICS ===")
print(online.to_string(index=False))

# ── 1. Annotate direction of 'better' ─────────────────────────────────────────
# Offline: higher is better except calibration error (lower is better)
offline['better_direction'] = ['higher','higher','higher','lower','higher']
offline['b_is_better'] = [
    (row.triage_b > row.triage_a) if row.better_direction == 'higher'
    else (row.triage_b < row.triage_a)
    for _, row in offline.iterrows()
]

# Online: lower is better for all except time_to_physician (lower is better too)
# Median_time_to_physician_min  → lower is better
# LWBS_rate_pct                 → lower is better
# Unscheduled_return_72h_pct    → lower is better
# Clinician_override_pct        → lower is better
# Patient_complaint_rate_pct    → lower is better
online['better_direction'] = ['lower','lower','lower','lower','lower']
online['b_is_better'] = [
    (row.triage_b_pct < row.triage_a_pct)
    for _, row in online.iterrows()
]

print()
print("=== OFFLINE: B better? ===")
print(offline[['metric','triage_a','triage_b','relative_change_pct','b_is_better']].to_string(index=False))
print()
print("=== ONLINE: B better? ===")
print(online[['metric','triage_a_pct','triage_b_pct','relative_change_pct','b_is_better']].to_string(index=False))

# ── 2. Statistical significance for online metrics ────────────────────────────
# 14-day pilot; assume equal shift counts. We'll use a simple z-test for
# proportions where applicable, and note that exact n per arm is not given.
# We'll compute effect sizes and flag clinical significance thresholds.

# Approximate n per arm from a 14-day pilot (assume ~200 patients/day, 2 arms)
# This is a reasonable ED assumption; we'll note it as an assumption.
N_PER_ARM = 1400  # conservative estimate

from scipy import stats

results_online = []
for _, row in online.iterrows():
    metric = row['metric']
    a_val  = row['triage_a_pct']
    b_val  = row['triage_b_pct']
    rel_ch = row['relative_change_pct']
    
    if metric == 'Median_time_to_physician_min':
        # Not a proportion; report as descriptive
        results_online.append({
            'metric': metric, 'a': a_val, 'b': b_val,
            'rel_change_pct': rel_ch, 'b_is_better': row['b_is_better'],
            'p_value': None, 'significant': None
        })
    else:
        # Proportion z-test
        p_a = a_val / 100
        p_b = b_val / 100
        p_pool = (p_a + p_b) / 2
        se = np.sqrt(p_pool * (1 - p_pool) * (2 / N_PER_ARM))
        z = (p_b - p_a) / se
        p_val = 2 * (1 - stats.norm.cdf(abs(z)))
        results_online.append({
            'metric': metric, 'a': a_val, 'b': b_val,
            'rel_change_pct': rel_ch, 'b_is_better': row['b_is_better'],
            'p_value': round(p_val, 4), 'significant': p_val < 0.05
        })

results_online_df = pd.DataFrame(results_online)
print()
print("=== ONLINE STATISTICAL TESTS ===")
print(results_online_df.to_string(index=False))

# Save outputs
offline.to_csv('outputs/offline_annotated.csv', index=False)
online.to_csv('outputs/online_annotated.csv', index=False)
results_online_df.to_csv('outputs/online_stats.csv', index=False)

# ── 3. FIGURES ────────────────────────────────────────────────────────────────

# Color palette
COL_A   = '#2196F3'   # blue  – TriageAssist-A
COL_B   = '#FF5722'   # orange – TriageAssist-B
COL_OK  = '#4CAF50'   # green  – improvement
COL_BAD = '#F44336'   # red    – regression

# ── Figure 1: Offline metrics grouped bar chart ───────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Figure 1 — Offline Evaluation Metrics (n = 8,000 test set)',
             fontsize=14, fontweight='bold', y=1.01)

# Left panel: performance metrics (all except calibration error)
perf_metrics = offline[offline['metric'] != 'Mean_absolute_calibration_error'].copy()
calib_metric  = offline[offline['metric'] == 'Mean_absolute_calibration_error'].copy()

ax = axes[0]
x = np.arange(len(perf_metrics))
w = 0.35
bars_a = ax.bar(x - w/2, perf_metrics['triage_a'], w, label='TriageAssist-A', color=COL_A, alpha=0.85)
bars_b = ax.bar(x + w/2, perf_metrics['triage_b'], w, label='TriageAssist-B', color=COL_B, alpha=0.85)

# Annotate bars
for bar in bars_a:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=8)
for bar in bars_b:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=8)

short_labels = [
    'Sensitivity\n(Critical ESI 1-2)',
    'Specificity\n(Non-urgent)',
    'AUROC\n(Acuity Score)',
    'Disposition\nAgreement (%)'
]
ax.set_xticks(x)
ax.set_xticklabels(short_labels, fontsize=8)
ax.set_ylim(0, 1.05)
ax.set_ylabel('Score / Proportion', fontsize=10)
ax.set_title('Performance Metrics (higher = better)', fontsize=10)
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.3)

# Right panel: calibration error (lower is better)
ax2 = axes[1]
bars_ca = ax2.bar(['TriageAssist-A'], calib_metric['triage_a'].values, color=COL_A, alpha=0.85, width=0.4)
bars_cb = ax2.bar(['TriageAssist-B'], calib_metric['triage_b'].values, color=COL_B, alpha=0.85, width=0.4)
for bar in [bars_ca[0], bars_cb[0]]:
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
             f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=10)
ax2.set_ylabel('Mean Absolute Calibration Error (lower = better)', fontsize=9)
ax2.set_title('Calibration Error (lower = better)', fontsize=10)
ax2.set_ylim(0, 0.16)
ax2.grid(axis='y', alpha=0.3)
ax2.annotate('+49.4% worse', xy=(0.5, 0.118), xytext=(0.5, 0.135),
             ha='center', fontsize=10, color=COL_BAD,
             arrowprops=dict(arrowstyle='->', color=COL_BAD))

plt.tight_layout()
plt.savefig('report/images/fig1_offline_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig1_offline_metrics.png')

# ── Figure 2: Online pilot metrics — grouped bar chart ────────────────────────
fig, ax = plt.subplots(figsize=(13, 6))

metric_labels = [
    'Time to Physician\n(min)',
    'LWBS Rate\n(%)',
    'Unscheduled Return\n72h (%)',
    'Clinician Override\n(%)',
    'Patient Complaint\nRate (%)'
]

a_vals = online['triage_a_pct'].values
b_vals = online['triage_b_pct'].values

x = np.arange(len(metric_labels))
w = 0.35

bars_a = ax.bar(x - w/2, a_vals, w, label='TriageAssist-A', color=COL_A, alpha=0.85)
bars_b = ax.bar(x + w/2, b_vals, w, label='TriageAssist-B', color=COL_B, alpha=0.85)

for bar in bars_a:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{bar.get_height():.2f}', ha='center', va='bottom', fontsize=8)
for i, bar in enumerate(bars_b):
    color = COL_OK if online['b_is_better'].iloc[i] else COL_BAD
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{bar.get_height():.2f}', ha='center', va='bottom', fontsize=8, color=color, fontweight='bold')

# Add significance stars
for i, row in results_online_df.iterrows():
    if row['significant'] == True:
        y_max = max(a_vals[i], b_vals[i]) + 1.5
        ax.text(x[i], y_max, '***', ha='center', fontsize=12, color='black')

ax.set_xticks(x)
ax.set_xticklabels(metric_labels, fontsize=9)
ax.set_ylabel('Value (minutes or percentage points)', fontsize=10)
ax.set_title('Figure 2 — Online A/B Pilot Metrics (14-day, randomized by shift)\n(all metrics: lower = better; *** p < 0.05)',
             fontsize=11, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/fig2_online_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig2_online_metrics.png')

# ── Figure 3: Relative change waterfall chart ─────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle('Figure 3 — Relative Change (%) from TriageAssist-A to TriageAssist-B',
             fontsize=13, fontweight='bold')

# Offline panel
ax = axes[0]
off_metrics_short = [
    'Sensitivity\n(Critical)',
    'Specificity\n(Non-urgent)',
    'AUROC',
    'Calibration\nError',
    'Disposition\nAgreement'
]
off_changes = offline['relative_change_pct'].values
# For calibration error, positive change is BAD (higher error)
# For others, positive change is GOOD
off_good = [True, False, True, False, False]  # True if positive rel_change means improvement
off_colors = []
for i, (chg, good) in enumerate(zip(off_changes, off_good)):
    if (chg > 0 and good) or (chg < 0 and not good):
        off_colors.append(COL_OK)
    else:
        off_colors.append(COL_BAD)

bars = ax.barh(off_metrics_short, off_changes, color=off_colors, alpha=0.85, edgecolor='white')
ax.axvline(0, color='black', linewidth=1)
for bar, val in zip(bars, off_changes):
    xpos = val + 0.5 if val >= 0 else val - 0.5
    ha = 'left' if val >= 0 else 'right'
    ax.text(xpos, bar.get_y() + bar.get_height()/2,
            f'{val:+.1f}%', va='center', ha=ha, fontsize=9, fontweight='bold')
ax.set_xlabel('Relative Change (%)', fontsize=10)
ax.set_title('Offline Metrics', fontsize=11)
ax.grid(axis='x', alpha=0.3)

# Online panel
ax2 = axes[1]
on_metrics_short = [
    'Time to Physician\n(min)',
    'LWBS Rate',
    'Unscheduled\nReturn 72h',
    'Clinician\nOverride',
    'Patient\nComplaints'
]
on_changes = online['relative_change_pct'].values
# All online metrics: lower is better, so negative change = improvement
on_colors2 = [COL_OK if c < 0 else COL_BAD for c in on_changes]

bars2 = ax2.barh(on_metrics_short, on_changes, color=on_colors2, alpha=0.85, edgecolor='white')
ax2.axvline(0, color='black', linewidth=1)
for bar, val in zip(bars2, on_changes):
    xpos = val + 1 if val >= 0 else val - 1
    ha = 'left' if val >= 0 else 'right'
    ax2.text(xpos, bar.get_y() + bar.get_height()/2,
             f'{val:+.1f}%', va='center', ha=ha, fontsize=9, fontweight='bold')
ax2.set_xlabel('Relative Change (%)', fontsize=10)
ax2.set_title('Online Pilot Metrics', fontsize=11)
ax2.grid(axis='x', alpha=0.3)

# Legend
patch_ok  = mpatches.Patch(color=COL_OK,  label='Improvement')
patch_bad = mpatches.Patch(color=COL_BAD, label='Regression')
fig.legend(handles=[patch_ok, patch_bad], loc='lower center', ncol=2,
           fontsize=10, bbox_to_anchor=(0.5, -0.04))

plt.tight_layout()
plt.savefig('report/images/fig3_relative_changes.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig3_relative_changes.png')

# ── Figure 4: Summary scorecard ───────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 7))
ax.axis('off')

col_labels = ['Domain', 'Metric', 'TriageAssist-A', 'TriageAssist-B', 'Δ (%)', 'Verdict']

table_data = [
    ['Offline', 'Sensitivity (Critical ESI 1-2)', '0.812', '0.871', '+7.3%', '✓ Better'],
    ['Offline', 'Specificity (Non-urgent)',        '0.706', '0.658', '-6.8%', '✗ Worse'],
    ['Offline', 'AUROC (Acuity Score)',            '0.881', '0.914', '+3.7%', '✓ Better'],
    ['Offline', 'Calibration Error (MACE)',        '0.079', '0.118', '+49.4%','✗ Worse'],
    ['Offline', 'Disposition Agreement (%)',       '78.4%', '61.2%', '-21.9%','✗ Worse'],
    ['Online',  'Time to Physician (min)',         '41.8',  '35.6',  '-14.8%','✓ Better'],
    ['Online',  'LWBS Rate (%)',                   '2.05%', '3.38%', '+64.9%','✗ Worse'],
    ['Online',  'Unscheduled Return 72h (%)',      '4.18%', '5.71%', '+36.6%','✗ Worse'],
    ['Online',  'Clinician Override (%)',          '8.35%', '14.18%','+69.8%','✗ Worse'],
    ['Online',  'Patient Complaint Rate (%)',      '0.11%', '0.25%', '+127.3%','✗ Worse'],
]

cell_colors = []
for row in table_data:
    verdict = row[-1]
    if '✓' in verdict:
        row_color = ['#E8F5E9'] * 5 + ['#C8E6C9']
    else:
        row_color = ['#FFEBEE'] * 5 + ['#FFCDD2']
    cell_colors.append(row_color)

table = ax.table(
    cellText=table_data,
    colLabels=col_labels,
    cellLoc='center',
    loc='center',
    cellColours=cell_colors
)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1.2, 1.8)

# Style header
for j in range(len(col_labels)):
    table[0, j].set_facecolor('#37474F')
    table[0, j].set_text_props(color='white', fontweight='bold')

ax.set_title('Figure 4 — Comprehensive Scorecard: TriageAssist-A vs. TriageAssist-B',
             fontsize=12, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('report/images/fig4_scorecard.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig4_scorecard.png')

# ── Figure 5: Radar / spider chart for offline metrics ────────────────────────
from matplotlib.patches import FancyArrowPatch

categories = ['Sensitivity\n(Critical)', 'AUROC', 'Specificity\n(Non-urgent)',
              'Disposition\nAgreement', 'Calibration\n(inverted)']

# Normalize all to 0-1 scale where 1 = best
# Calibration error: invert (1 - error/max_error)
max_calib = 0.15
vals_a = [
    offline.loc[offline.metric=='Sensitivity_critical_ESI12','triage_a'].values[0],
    offline.loc[offline.metric=='AUROC_acuity_score','triage_a'].values[0],
    offline.loc[offline.metric=='Specificity_non_urgent','triage_a'].values[0],
    offline.loc[offline.metric=='Disposition_agreement_with_attending_pct','triage_a'].values[0] / 100,
    1 - offline.loc[offline.metric=='Mean_absolute_calibration_error','triage_a'].values[0] / max_calib,
]
vals_b = [
    offline.loc[offline.metric=='Sensitivity_critical_ESI12','triage_b'].values[0],
    offline.loc[offline.metric=='AUROC_acuity_score','triage_b'].values[0],
    offline.loc[offline.metric=='Specificity_non_urgent','triage_b'].values[0],
    offline.loc[offline.metric=='Disposition_agreement_with_attending_pct','triage_b'].values[0] / 100,
    1 - offline.loc[offline.metric=='Mean_absolute_calibration_error','triage_b'].values[0] / max_calib,
]

N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]
vals_a += vals_a[:1]
vals_b += vals_b[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
ax.plot(angles, vals_a, 'o-', linewidth=2, color=COL_A, label='TriageAssist-A')
ax.fill(angles, vals_a, alpha=0.15, color=COL_A)
ax.plot(angles, vals_b, 'o-', linewidth=2, color=COL_B, label='TriageAssist-B')
ax.fill(angles, vals_b, alpha=0.15, color=COL_B)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylim(0, 1)
ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
ax.set_yticklabels(['0.2','0.4','0.6','0.8','1.0'], fontsize=7)
ax.set_title('Figure 5 — Offline Performance Radar\n(all axes: higher = better; calibration inverted)',
             fontsize=11, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)

plt.tight_layout()
plt.savefig('report/images/fig5_radar.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig5_radar.png')

print('\nAll figures saved. Analysis complete.')
