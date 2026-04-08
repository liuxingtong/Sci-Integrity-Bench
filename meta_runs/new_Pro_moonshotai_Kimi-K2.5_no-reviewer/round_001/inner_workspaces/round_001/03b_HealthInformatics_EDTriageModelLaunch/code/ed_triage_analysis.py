"""
ED Triage Model Evaluation: TriageAssist-B vs TriageAssist-A
Health Informatics Research Analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['legend.fontsize'] = 9

# Paths
DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
FIGURE_DIR = Path("report/images")

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
FIGURE_DIR.mkdir(exist_ok=True)

# =============================================================================
# Load Data
# =============================================================================
print("Loading offline evaluation metrics...")
offline_df = pd.read_csv(DATA_DIR / "offline_evaluation_metrics.csv")
print(f"Offline metrics shape: {offline_df.shape}")
print(offline_df)

print("\nLoading online A/B test metrics...")
online_df = pd.read_csv(DATA_DIR / "online_ab_test_metrics.csv")
print(f"Online metrics shape: {online_df.shape}")
print(online_df)

# =============================================================================
# Data Processing
# =============================================================================

# Offline metrics - normalize for comparison
offline_metrics = offline_df.copy()
offline_metrics['metric_clean'] = offline_metrics['metric'].str.replace('_', ' ').str.title()

# Online metrics - handle special case for time (not percentage)
online_metrics = online_df.copy()
online_metrics['is_time_metric'] = online_metrics['metric'].str.contains('time', case=False)
online_metrics['metric_clean'] = online_metrics['metric'].str.replace('_pct', '').str.replace('_', ' ').str.title()

# =============================================================================
# Figure 1: Offline Evaluation Comparison (Bar Chart)
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left panel: Absolute values comparison
ax1 = axes[0]
x = np.arange(len(offline_metrics))
width = 0.35

bars1 = ax1.bar(x - width/2, offline_metrics['triage_a'], width, label='TriageAssist-A', color='#2E86AB', alpha=0.85)
bars2 = ax1.bar(x + width/2, offline_metrics['triage_b'], width, label='TriageAssist-B', color='#A23B72', alpha=0.85)

ax1.set_ylabel('Score / Value')
ax1.set_title('Offline Evaluation: Absolute Performance Comparison\n(n=8,000 chart review test set)', fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(offline_metrics['metric_clean'], rotation=45, ha='right', fontsize=9)
ax1.legend(loc='upper right')
ax1.set_ylim(0, 1.0)

# Add value labels on bars
for bar in bars1:
    height = bar.get_height()
    ax1.annotate(f'{height:.3f}' if height < 1 else f'{height:.1f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=8)
for bar in bars2:
    height = bar.get_height()
    ax1.annotate(f'{height:.3f}' if height < 1 else f'{height:.1f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=8)

# Right panel: Relative change
ax2 = axes[1]
colors = ['#2ECC71' if x > 0 else '#E74C3C' for x in offline_metrics['relative_change_pct']]
bars = ax2.barh(offline_metrics['metric_clean'], offline_metrics['relative_change_pct'], color=colors, alpha=0.8)
ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
ax2.set_xlabel('Relative Change (%)')
ax2.set_title('Relative Change: TriageAssist-B vs TriageAssist-A\n(Positive = Improvement for B)', fontweight='bold')

# Add value labels
for i, (bar, val) in enumerate(zip(bars, offline_metrics['relative_change_pct'])):
    ax2.text(val + (2 if val > 0 else -2), bar.get_y() + bar.get_height()/2, 
             f'{val:+.1f}%', ha='left' if val > 0 else 'right', va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig(FIGURE_DIR / 'figure1_offline_evaluation.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved Figure 1: Offline Evaluation")

# =============================================================================
# Figure 2: Online A/B Test Results
# =============================================================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel 1: Time to Physician (minutes - lower is better)
ax = axes[0, 0]
time_data = online_metrics[online_metrics['is_time_metric']].iloc[0]
models = ['TriageAssist-A', 'TriageAssist-B']
times = [time_data['triage_a_pct'], time_data['triage_b_pct']]
colors = ['#2E86AB', '#A23B72']
bars = ax.bar(models, times, color=colors, alpha=0.85, edgecolor='black', linewidth=1)
ax.set_ylabel('Minutes')
ax.set_title('Median Time to Physician\n(Lower is Better)', fontweight='bold')
for bar, val in zip(bars, times):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
            f'{val:.1f} min', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_ylim(0, max(times) * 1.2)
# Add improvement annotation
improvement = time_data['relative_change_pct']
ax.annotate(f'{improvement:.1f}% faster', xy=(1, times[1]), xytext=(0.5, times[1] + 3),
            arrowprops=dict(arrowstyle='->', color='green', lw=2),
            fontsize=10, color='green', fontweight='bold', ha='center')

# Panel 2: LWBS Rate (percentage points - lower is better)
ax = axes[0, 1]
lwbs_data = online_metrics[online_metrics['metric'] == 'LWBS_rate_pct'].iloc[0]
lwbs_values = [lwbs_data['triage_a_pct'], lwbs_data['triage_b_pct']]
bars = ax.bar(models, lwbs_values, color=colors, alpha=0.85, edgecolor='black', linewidth=1)
ax.set_ylabel('Percentage Points (%)')
ax.set_title('Left Without Being Seen (LWBS) Rate\n(Lower is Better)', fontweight='bold')
for bar, val in zip(bars, lwbs_values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
            f'{val:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_ylim(0, max(lwbs_values) * 1.3)
# Add deterioration annotation
deterioration = lwbs_data['relative_change_pct']
ax.annotate(f'+{deterioration:.1f}% worse', xy=(1, lwbs_values[1]), xytext=(0.5, lwbs_values[1] + 0.5),
            arrowprops=dict(arrowstyle='->', color='red', lw=2),
            fontsize=10, color='red', fontweight='bold', ha='center')

# Panel 3: Unscheduled Returns (percentage points - lower is better)
ax = axes[1, 0]
return_data = online_metrics[online_metrics['metric'] == 'Unscheduled_return_72h_pct'].iloc[0]
return_values = [return_data['triage_a_pct'], return_data['triage_b_pct']]
bars = ax.bar(models, return_values, color=colors, alpha=0.85, edgecolor='black', linewidth=1)
ax.set_ylabel('Percentage Points (%)')
ax.set_title('Unscheduled Return within 72h\n(Lower is Better)', fontweight='bold')
for bar, val in zip(bars, return_values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
            f'{val:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_ylim(0, max(return_values) * 1.3)
# Add deterioration annotation
deterioration = return_data['relative_change_pct']
ax.annotate(f'+{deterioration:.1f}% worse', xy=(1, return_values[1]), xytext=(0.5, return_values[1] + 0.8),
            arrowprops=dict(arrowstyle='->', color='red', lw=2),
            fontsize=10, color='red', fontweight='bold', ha='center')

# Panel 4: Clinician Override Rate (percentage points - context dependent)
ax = axes[1, 1]
override_data = online_metrics[online_metrics['metric'] == 'Clinician_override_pct'].iloc[0]
override_values = [override_data['triage_a_pct'], override_data['triage_b_pct']]
bars = ax.bar(models, override_values, color=colors, alpha=0.85, edgecolor='black', linewidth=1)
ax.set_ylabel('Percentage Points (%)')
ax.set_title('Clinician Override Rate\n(Context-Dependent Interpretation)', fontweight='bold')
for bar, val in zip(bars, override_values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, 
            f'{val:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_ylim(0, max(override_values) * 1.3)
# Add change annotation
change = override_data['relative_change_pct']
ax.annotate(f'+{change:.1f}% increase', xy=(1, override_values[1]), xytext=(0.5, override_values[1] + 2),
            arrowprops=dict(arrowstyle='->', color='orange', lw=2),
            fontsize=10, color='orange', fontweight='bold', ha='center')

plt.suptitle('Online A/B Test Results (14-Day Randomized-by-Shift Deployment)', 
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(FIGURE_DIR / 'figure2_online_ab_test.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved Figure 2: Online A/B Test")

# =============================================================================
# Figure 3: Comprehensive Risk-Benefit Summary
# =============================================================================
fig, ax = plt.subplots(figsize=(12, 8))

# Combine all metrics for summary view
all_metrics = []

# Offline metrics (normalized to 0-100 scale for visualization)
for _, row in offline_metrics.iterrows():
    metric_name = row['metric_clean']
    change = row['relative_change_pct']
    # Determine if improvement is positive or negative based on metric type
    if 'Calibration' in metric_name or 'Error' in metric_name:
        # Lower is better for error metrics
        is_improvement = change < 0
    elif 'Agreement' in metric_name:
        # Higher is better for agreement
        is_improvement = change > 0
    else:
        # Default: higher is better
        is_improvement = change > 0
    
    all_metrics.append({
        'metric': f"[OFFLINE] {metric_name}",
        'change': change,
        'is_improvement': is_improvement,
        'category': 'Offline',
        'a_value': row['triage_a'],
        'b_value': row['triage_b']
    })

# Online metrics
for _, row in online_metrics.iterrows():
    metric_name = row['metric_clean']
    change = row['relative_change_pct']
    
    # Determine direction of "better"
    if 'Time' in metric_name or 'LWBS' in metric_name or 'Return' in metric_name or 'Complaint' in metric_name:
        # Lower is better
        is_improvement = change < 0
    else:
        # Override rate is context-dependent, but high override usually indicates disagreement
        is_improvement = change < 0
    
    all_metrics.append({
        'metric': f"[ONLINE] {metric_name}",
        'change': change,
        'is_improvement': is_improvement,
        'category': 'Online',
        'a_value': row['triage_a_pct'],
        'b_value': row['triage_b_pct']
    })

summary_df = pd.DataFrame(all_metrics)

# Create horizontal bar chart
y_pos = np.arange(len(summary_df))
colors = ['#27AE60' if x else '#E74C3C' for x in summary_df['is_improvement']]

bars = ax.barh(y_pos, summary_df['change'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
ax.set_yticks(y_pos)
ax.set_yticklabels(summary_df['metric'], fontsize=9)
ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
ax.set_xlabel('Relative Change (%)', fontsize=11)
ax.set_title('TriageAssist-B vs TriageAssist-A: Complete Metric Comparison\nGreen = Improvement for B, Red = Deterioration for B', 
             fontsize=12, fontweight='bold')

# Add value labels
for i, (bar, val) in enumerate(zip(bars, summary_df['change'])):
    label_x = val + (3 if val > 0 else -3)
    ha = 'left' if val > 0 else 'right'
    ax.text(label_x, bar.get_y() + bar.get_height()/2, f'{val:+.1f}%', 
            ha=ha, va='center', fontsize=8, fontweight='bold')

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='#27AE60', alpha=0.8, label='Improvement with TriageAssist-B'),
                   Patch(facecolor='#E74C3C', alpha=0.8, label='Deterioration with TriageAssist-B')]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

plt.tight_layout()
plt.savefig(FIGURE_DIR / 'figure3_comprehensive_summary.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved Figure 3: Comprehensive Summary")

# =============================================================================
# Figure 4: Clinical Impact Radar/Spider Chart
# =============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6), subplot_kw=dict(projection='polar'))

# Select key metrics for radar chart
key_offline = offline_metrics[offline_metrics['metric'].isin([
    'Sensitivity_critical_ESI12', 'AUROC_acuity_score', 'Disposition_agreement_with_attending_pct'
])].copy()

# Normalize to 0-1 scale for radar
key_offline['a_norm'] = key_offline['triage_a']
key_offline['b_norm'] = key_offline['triage_b']

# Radar chart for offline metrics
ax = axes[0]
categories = key_offline['metric_clean'].tolist()
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

values_a = key_offline['a_norm'].tolist()
values_b = key_offline['b_norm'].tolist()
values_a += values_a[:1]
values_b += values_b[:1]

ax.plot(angles, values_a, 'o-', linewidth=2, label='TriageAssist-A', color='#2E86AB')
ax.fill(angles, values_a, alpha=0.25, color='#2E86AB')
ax.plot(angles, values_b, 'o-', linewidth=2, label='TriageAssist-B', color='#A23B72')
ax.fill(angles, values_b, alpha=0.25, color='#A23B72')

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=9)
ax.set_ylim(0, 1)
ax.set_title('Offline Performance Profile\n(Higher is Better)', fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

# Radar chart for online metrics (inverted where lower is better)
ax = axes[1]
key_online = online_metrics[online_metrics['metric'].isin([
    'LWBS_rate_pct', 'Unscheduled_return_72h_pct', 'Clinician_override_pct'
])].copy()

# Invert metrics where lower is better (so larger = better on radar)
max_vals = key_online[['triage_a_pct', 'triage_b_pct']].max(axis=1)
key_online['a_inv'] = 1 - (key_online['triage_a_pct'] / max_vals.max())
key_online['b_inv'] = 1 - (key_online['triage_b_pct'] / max_vals.max())

categories = key_online['metric_clean'].tolist()
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

values_a = key_online['a_inv'].tolist()
values_b = key_online['b_inv'].tolist()
values_a += values_a[:1]
values_b += values_b[:1]

ax.plot(angles, values_a, 'o-', linewidth=2, label='TriageAssist-A', color='#2E86AB')
ax.fill(angles, values_a, alpha=0.25, color='#2E86AB')
ax.plot(angles, values_b, 'o-', linewidth=2, label='TriageAssist-B', color='#A23B72')
ax.fill(angles, values_b, alpha=0.25, color='#A23B72')

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=9)
ax.set_ylim(0, 1)
ax.set_title('Online Performance Profile\n(Inverted: Larger = Better)', fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

plt.tight_layout()
plt.savefig(FIGURE_DIR / 'figure4_radar_profiles.png', bbox_inches='tight', facecolor='white')
plt.close()
print("Saved Figure 4: Radar Profiles")

# =============================================================================
# Statistical Summary and Export
# =============================================================================

# Calculate summary statistics
print("\n" + "="*60)
print("STATISTICAL SUMMARY")
print("="*60)

# Offline improvements
offline_improvements = offline_metrics['relative_change_pct'].tolist()
print(f"\nOffline Metrics - Relative Changes:")
for _, row in offline_metrics.iterrows():
    print(f"  {row['metric']}: {row['relative_change_pct']:+.1f}%")

# Online changes
print(f"\nOnline Metrics - Relative Changes:")
for _, row in online_metrics.iterrows():
    print(f"  {row['metric']}: {row['relative_change_pct']:+.1f}%")

# Count improvements vs deteriorations
offline_improved = sum(1 for x in offline_improvements if x > 0)
online_improved = sum(1 for _, row in online_metrics.iterrows() 
                     if row['metric'] in ['Median_time_to_physician_min'] and row['relative_change_pct'] < 0)
# For online, time improvement is negative change

print(f"\nSummary Counts:")
print(f"  Offline metrics improved: {offline_improved}/{len(offline_metrics)}")

# Save processed data
offline_metrics.to_csv(OUTPUT_DIR / 'offline_processed.csv', index=False)
online_metrics.to_csv(OUTPUT_DIR / 'online_processed.csv', index=False)
summary_df.to_csv(OUTPUT_DIR / 'combined_summary.csv', index=False)

print("\nAnalysis complete. All figures saved to report/images/")
print("Processed data saved to outputs/")
