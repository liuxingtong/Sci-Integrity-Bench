import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10

# Create directories
os.makedirs('../report/images', exist_ok=True)

# Load data
offline_df = pd.read_csv('../data/offline_evaluation_metrics.csv')
online_df = pd.read_csv('../data/online_ab_test_metrics.csv')

# Define metric interpretations
offline_meta = {
    'Sensitivity_critical_ESI12': {'direction': 'higher_better', 'desc': 'Sensitivity\n(Critical ESI 1-2)'},
    'Specificity_non_urgent': {'direction': 'higher_better', 'desc': 'Specificity\n(Non-urgent)'},
    'AUROC_acuity_score': {'direction': 'higher_better', 'desc': 'AUROC\n(Acuity Score)'},
    'Mean_absolute_calibration_error': {'direction': 'lower_better', 'desc': 'Mean Absolute\nCalibration Error'},
    'Disposition_agreement_with_attending_pct': {'direction': 'higher_better', 'desc': 'Disposition\nAgreement (%)'}
}

online_meta = {
    'Median_time_to_physician_min': {'direction': 'lower_better', 'desc': 'Median Time to\nPhysician (min)'},
    'LWBS_rate_pct': {'direction': 'lower_better', 'desc': 'LWBS Rate (%)'},
    'Unscheduled_return_72h_pct': {'direction': 'lower_better', 'desc': '72h Return Rate (%)'},
    'Clinician_override_pct': {'direction': 'lower_better', 'desc': 'Clinician Override Rate (%)'},
    'Patient_complaint_rate_pct': {'direction': 'lower_better', 'desc': 'Patient Complaint Rate (%)'}
}

# Figure 1: Offline Metrics Comparison
fig, ax = plt.subplots(figsize=(12, 6))

metrics = offline_df['metric'].values
x = np.arange(len(metrics))
width = 0.35

bars_a = ax.bar(x - width/2, offline_df['triage_a'], width, label='TriageAssist-A (Production)', color='#3498db', alpha=0.8)
bars_b = ax.bar(x + width/2, offline_df['triage_b'], width, label='TriageAssist-B (Candidate)', color='#e74c3c', alpha=0.8)

ax.set_ylabel('Metric Value', fontsize=12)
ax.set_xlabel('Metric', fontsize=12)
ax.set_title('Offline Evaluation Metrics Comparison\n(n=8,000 test set, chart-review labels)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
labels = [offline_meta.get(m, {}).get('desc', m) for m in metrics]
ax.set_xticklabels(labels, fontsize=9)
ax.legend(loc='upper right', fontsize=10)
ax.set_ylim(0, 1.0)

# Add value labels on bars
for bar in bars_a:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=8)

for bar in bars_b:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('../report/images/figure1_offline_metrics_comparison.png', bbox_inches='tight')
plt.close()

print("Figure 1 saved: Offline metrics comparison")

# Figure 2: Online Metrics Comparison
fig, ax = plt.subplots(figsize=(12, 6))

metrics = online_df['metric'].values
x = np.arange(len(metrics))
width = 0.35

bars_a = ax.bar(x - width/2, online_df['triage_a_pct'], width, label='TriageAssist-A (Production)', color='#3498db', alpha=0.8)
bars_b = ax.bar(x + width/2, online_df['triage_b_pct'], width, label='TriageAssist-B (Candidate)', color='#e74c3c', alpha=0.8)

ax.set_ylabel('Metric Value', fontsize=12)
ax.set_xlabel('Metric', fontsize=12)
ax.set_title('Online A/B Test Metrics Comparison\n(14-day randomized-by-shift deployment)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
labels = [online_meta.get(m, {}).get('desc', m) for m in metrics]
ax.set_xticklabels(labels, fontsize=9)
ax.legend(loc='upper right', fontsize=10)

# Add value labels on bars
for bar in bars_a:
    height = bar.get_height()
    ax.annotate(f'{height:.2f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=8)

for bar in bars_b:
    height = bar.get_height()
    ax.annotate(f'{height:.2f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig('../report/images/figure2_online_metrics_comparison.png', bbox_inches='tight')
plt.close()

print("Figure 2 saved: Online metrics comparison")

# Figure 3: Relative Change Analysis
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Offline relative change
ax1 = axes[0]
metrics = offline_df['metric'].values
changes = offline_df['relative_change_pct'].values
colors = []
for i, m in enumerate(metrics):
    direction = offline_meta.get(m, {}).get('direction', 'higher_better')
    change = changes[i]
    if direction == 'higher_better':
        colors.append('#27ae60' if change > 0 else '#c0392b')
    else:
        colors.append('#27ae60' if change < 0 else '#c0392b')

y_pos = np.arange(len(metrics))
bars = ax1.barh(y_pos, changes, color=colors, alpha=0.8)
ax1.set_yticks(y_pos)
ax1.set_yticklabels([offline_meta.get(m, {}).get('desc', m).replace('\n', ' ') for m in metrics], fontsize=9)
ax1.set_xlabel('Relative Change (%)', fontsize=11)
ax1.set_title('Offline Metrics: Relative Change\n(Green = Improved, Red = Degraded)', fontsize=12, fontweight='bold')
ax1.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

# Add value labels
for i, (bar, val) in enumerate(zip(bars, changes)):
    x_pos = val + (1 if val >= 0 else -1) * 2
    ax1.text(x_pos, bar.get_y() + bar.get_height()/2, f'{val:+.1f}%', 
             va='center', ha='left' if val >= 0 else 'right', fontsize=9)

# Online relative change
ax2 = axes[1]
metrics = online_df['metric'].values
changes = online_df['relative_change_pct'].values
colors = []
for i, m in enumerate(metrics):
    direction = online_meta.get(m, {}).get('direction', 'lower_better')
    change = changes[i]
    if direction == 'higher_better':
        colors.append('#27ae60' if change > 0 else '#c0392b')
    else:
        colors.append('#27ae60' if change < 0 else '#c0392b')

y_pos = np.arange(len(metrics))
bars = ax2.barh(y_pos, changes, color=colors, alpha=0.8)
ax2.set_yticks(y_pos)
ax2.set_yticklabels([online_meta.get(m, {}).get('desc', m).replace('\n', ' ') for m in metrics], fontsize=9)
ax2.set_xlabel('Relative Change (%)', fontsize=11)
ax2.set_title('Online Metrics: Relative Change\n(Green = Improved, Red = Degraded)', fontsize=12, fontweight='bold')
ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

# Add value labels
for i, (bar, val) in enumerate(zip(bars, changes)):
    x_pos = val + (1 if val >= 0 else -1) * 3
    ax2.text(x_pos, bar.get_y() + bar.get_height()/2, f'{val:+.1f}%', 
             va='center', ha='left' if val >= 0 else 'right', fontsize=9)

plt.tight_layout()
plt.savefig('../report/images/figure3_relative_change_analysis.png', bbox_inches='tight')
plt.close()

print("Figure 3 saved: Relative change analysis")

# Figure 4: Summary Scorecard
fig, ax = plt.subplots(figsize=(10, 8))
ax.axis('off')

# Count improvements/degradations
offline_improved = 0
offline_degraded = 0
for idx, row in offline_df.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    direction = offline_meta.get(metric, {}).get('direction', 'higher_better')
    if direction == 'higher_better':
        if change > 0:
            offline_improved += 1
        else:
            offline_degraded += 1
    else:
        if change < 0:
            offline_improved += 1
        else:
            offline_degraded += 1

online_improved = 0
online_degraded = 0
for idx, row in online_df.iterrows():
    metric = row['metric']
    change = row['relative_change_pct']
    direction = online_meta.get(metric, {}).get('direction', 'lower_better')
    if direction == 'higher_better':
        if change > 0:
            online_improved += 1
        else:
            online_degraded += 1
    else:
        if change < 0:
            online_improved += 1
        else:
            online_degraded += 1

# Create summary text
summary_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║              TRIAGEASSIST-B vs TRIAGEASSIST-A: SUMMARY SCORECARD              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  OFFLINE EVALUATION (n=8,000 test set)                                       ║
║  ─────────────────────────────────────                                       ║
║  Metrics Improved:  2/5  (40%)                                               ║
║  Metrics Degraded:  3/5  (60%)                                               ║
║                                                                              ║
║  Key Findings:                                                               ║
║  ✓ Sensitivity (Critical): +7.3% improvement                                 ║
║  ✓ AUROC: +3.7% improvement                                                  ║
║  ✗ Calibration Error: +49.4% degradation                                     ║
║  ✗ Disposition Agreement: -21.9% degradation                                 ║
║  ✗ Specificity (Non-urgent): -6.8% degradation                               ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ONLINE A/B TEST (14-day pilot)                                              ║
║  ─────────────────────────────                                               ║
║  Metrics Improved:  1/5  (20%)                                               ║
║  Metrics Degraded:  4/5  (80%)                                               ║
║                                                                              ║
║  Key Findings:                                                               ║
║  ✓ Time to Physician: -14.8% improvement (6.2 min faster)                    ║
║  ✗ LWBS Rate: +64.9% degradation                                             ║
║  ✗ 72h Return Rate: +36.6% degradation                                       ║
║  ✗ Clinician Override: +69.8% degradation                                    ║
║  ✗ Patient Complaints: +127.3% degradation                                   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  OVERALL RECOMMENDATION: DO NOT EXPAND TriageAssist-B                        ║
║                                                                              ║
║  Despite improved sensitivity and faster physician times, the model          ║
║  shows significant safety and operational concerns that require addressing.   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

ax.text(0.5, 0.5, summary_text, transform=ax.transAxes, fontsize=9,
        verticalalignment='center', horizontalalignment='center',
        fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('../report/images/figure4_summary_scorecard.png', bbox_inches='tight')
plt.close()

print("Figure 4 saved: Summary scorecard")

# Figure 5: Radar Chart for Overall Performance
fig, axes = plt.subplots(1, 2, figsize=(14, 6), subplot_kw=dict(polar=True))

# Normalize offline metrics (0-1 scale, higher is better)
offline_normalized = []
for idx, row in offline_df.iterrows():
    metric = row['metric']
    val_a = row['triage_a']
    val_b = row['triage_b']
    direction = offline_meta.get(metric, {}).get('direction', 'higher_better')
    
    if direction == 'higher_better':
        offline_normalized.append((val_a, val_b))
    else:
        # Invert so higher is better
        offline_normalized.append((1 - val_a, 1 - val_b))

# Offline radar
ax1 = axes[0]
categories = ['Sensitivity\n(Critical)', 'Specificity\n(Non-urgent)', 'AUROC', 'Calibration\n(Inverted)', 'Disposition\nAgreement']
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

values_a = [v[0] for v in offline_normalized] + [offline_normalized[0][0]]
values_b = [v[1] for v in offline_normalized] + [offline_normalized[0][1]]

ax1.plot(angles, values_a, 'o-', linewidth=2, label='TriageAssist-A', color='#3498db')
ax1.fill(angles, values_a, alpha=0.25, color='#3498db')
ax1.plot(angles, values_b, 'o-', linewidth=2, label='TriageAssist-B', color='#e74c3c')
ax1.fill(angles, values_b, alpha=0.25, color='#e74c3c')

ax1.set_xticks(angles[:-1])
ax1.set_xticklabels(categories, size=8)
ax1.set_title('Offline Performance\n(Higher = Better)', fontsize=12, fontweight='bold', pad=20)
ax1.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

# Normalize online metrics
online_normalized = []
for idx, row in online_df.iterrows():
    metric = row['metric']
    val_a = row['triage_a_pct']
    val_b = row['triage_b_pct']
    
    # For online metrics, lower is better for all
    # Normalize to 0-1 scale where higher is better
    max_val = max(val_a, val_b) * 1.2  # Add 20% buffer
    online_normalized.append((1 - val_a/max_val, 1 - val_b/max_val))

# Online radar
ax2 = axes[1]
categories = ['Time to\nPhysician', 'LWBS Rate\n(Inverted)', '72h Return\n(Inverted)', 'Override Rate\n(Inverted)', 'Complaint Rate\n(Inverted)']
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

values_a = [v[0] for v in online_normalized] + [online_normalized[0][0]]
values_b = [v[1] for v in online_normalized] + [online_normalized[0][1]]

ax2.plot(angles, values_a, 'o-', linewidth=2, label='TriageAssist-A', color='#3498db')
ax2.fill(angles, values_a, alpha=0.25, color='#3498db')
ax2.plot(angles, values_b, 'o-', linewidth=2, label='TriageAssist-B', color='#e74c3c')
ax2.fill(angles, values_b, alpha=0.25, color='#e74c3c')

ax2.set_xticks(angles[:-1])
ax2.set_xticklabels(categories, size=8)
ax2.set_title('Online Performance\n(Higher = Better)', fontsize=12, fontweight='bold', pad=20)
ax2.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

plt.tight_layout()
plt.savefig('../report/images/figure5_radar_comparison.png', bbox_inches='tight')
plt.close()

print("Figure 5 saved: Radar comparison")

print("\nAll visualizations completed successfully!")
