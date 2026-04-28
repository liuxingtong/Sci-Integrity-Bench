#!/usr/bin/env python3
"""
Huangtupo Site Radiocarbon Chronology Analysis
Computes conventional BP ages, propagates uncertainties, and generates figures.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# 1. Load data
# ─────────────────────────────────────────────
df = pd.read_csv('data/radiocarbon_measurements.csv')
print("Raw data:")
print(df.to_string())
print()

# ─────────────────────────────────────────────
# 2. Conventional BP age calculation
#    age_BP = -8033 * ln(F14)
#    Propagated 1σ: sigma_age = 8033 * sigma_F14 / F14
# ─────────────────────────────────────────────
F14_MIN = 1e-6   # numerical floor
F14_MAX = 1.0    # physical ceiling

df['f14_clipped'] = df['f14_residual_ratio'].clip(lower=F14_MIN, upper=F14_MAX)
df['clipped_flag'] = df['f14_residual_ratio'] != df['f14_clipped']

df['age_BP'] = -8033.0 * np.log(df['f14_clipped'])
df['sigma_age_BP'] = 8033.0 * df['sigma_f14_absolute'] / df['f14_clipped']

# Round to nearest year (conventional reporting)
df['age_BP_rounded'] = df['age_BP'].round(0).astype(int)
df['sigma_age_BP_rounded'] = df['sigma_age_BP'].round(0).astype(int)

print("Computed ages:")
print(df[['artifact_id','f14_residual_ratio','f14_clipped','clipped_flag',
          'age_BP_rounded','sigma_age_BP_rounded']].to_string())
print()

# ─────────────────────────────────────────────
# 3. Approximate calendar calibration
#    We use a simplified linear calibration curve approximation.
#    For a proper calibration one would use IntCal20; here we apply
#    a piecewise linear approximation based on published IntCal20 data
#    for the Holocene and late Pleistocene.
#
#    Key calibration nodes (BP → cal BP, midpoints of IntCal20 plateaus):
#    These are representative values from IntCal20 for illustration.
# ─────────────────────────────────────────────

# IntCal20 representative calibration nodes (14C BP → cal BP)
# Source: Reimer et al. 2020, Radiocarbon 62(4)
# Format: (14C_BP, cal_BP)
intcal20_nodes = [
    (0,    0),
    (500,  510),
    (1000, 950),
    (1500, 1400),
    (2000, 1980),
    (2500, 2600),
    (3000, 3200),
    (3500, 3800),
    (4000, 4450),
    (4500, 5200),
    (5000, 5750),
    (5500, 6300),
    (6000, 6850),
    (6500, 7400),
    (7000, 7800),
    (7500, 8300),
    (8000, 8900),
    (8500, 9500),
    (9000, 10200),
    (9500, 10800),
    (10000, 11400),
    (11000, 12900),
    (12000, 13900),
    (13000, 15500),
    (14000, 17000),
    (20000, 24000),
    (30000, 34000),
    (40000, 45000),
    (50000, 55000),
]

intcal_14c = np.array([n[0] for n in intcal20_nodes])
intcal_cal  = np.array([n[1] for n in intcal20_nodes])

def calibrate_age(age_bp, sigma_bp):
    """Approximate calendar age from 14C BP using piecewise linear IntCal20 nodes."""
    cal_mid = np.interp(age_bp, intcal_14c, intcal_cal)
    # Propagate uncertainty: derivative of calibration curve
    delta = 10.0
    cal_hi = np.interp(age_bp + delta, intcal_14c, intcal_cal)
    cal_lo = np.interp(age_bp - delta, intcal_14c, intcal_cal)
    dcal_d14c = (cal_hi - cal_lo) / (2 * delta)
    cal_sigma = abs(dcal_d14c) * sigma_bp
    return cal_mid, cal_sigma

cal_results = [calibrate_age(a, s) for a, s in
               zip(df['age_BP'], df['sigma_age_BP'])]
df['cal_BP'] = [r[0] for r in cal_results]
df['sigma_cal_BP'] = [r[1] for r in cal_results]

# Convert to BCE/CE
df['cal_BCE_CE'] = 1950 - df['cal_BP']
df['cal_BCE_CE_label'] = df['cal_BCE_CE'].apply(
    lambda y: f"{abs(int(round(y)))} {'CE' if y >= 0 else 'BCE'}"
)
df['cal_range_label'] = df.apply(
    lambda r: f"{int(round(r['cal_BP']))} ± {int(round(r['sigma_cal_BP']))} cal BP", axis=1
)

print("Calibrated ages:")
print(df[['artifact_id','age_BP_rounded','sigma_age_BP_rounded',
          'cal_BP','sigma_cal_BP','cal_BCE_CE_label']].to_string())
print()

# ─────────────────────────────────────────────
# 4. Stratigraphic ordering
# ─────────────────────────────────────────────
# Parse layer numbers for ordering (lower layer number = shallower = younger)
strat_order = {
    'Huangtupo-Trench3-L1': 1,
    'Huangtupo-Trench3-L2': 2,
    'Huangtupo-Trench3-L3': 3,
    'Huangtupo-Trench3-L4': 4,
    'Huangtupo-Trench3-L5': 5,
    'Huangtupo-Trench3-L6': 6,
    'Huangtupo-Trench4-pit7': 7,   # pit feature, treated as intermediate
    'Huangtupo-Trench2-surface scatter': 0,  # surface = shallowest
}
df['strat_rank'] = df['stratigraphic_unit'].map(strat_order)
df_sorted = df.sort_values('strat_rank').reset_index(drop=True)

print("Stratigraphic order (surface → deepest):")
print(df_sorted[['artifact_id','stratigraphic_unit','strat_rank',
                  'age_BP_rounded','cal_BCE_CE_label']].to_string())
print()

# ─────────────────────────────────────────────
# 5. Cultural periodization
# ─────────────────────────────────────────────
def assign_period(cal_bp):
    """Assign cultural period based on approximate cal BP."""
    if cal_bp < 100:
        return 'Modern / Historical'
    elif cal_bp < 500:
        return 'Late Imperial (Ming–Qing)'
    elif cal_bp < 1500:
        return 'Medieval (Tang–Song)'
    elif cal_bp < 3000:
        return 'Early Imperial / Iron Age'
    elif cal_bp < 5000:
        return 'Bronze Age / Neolithic'
    elif cal_bp < 10000:
        return 'Neolithic / Mesolithic'
    elif cal_bp < 15000:
        return 'Late Paleolithic'
    elif cal_bp < 30000:
        return 'Middle Paleolithic'
    else:
        return 'Early Paleolithic'

df['cultural_period'] = df['cal_BP'].apply(assign_period)

print("Cultural periods:")
print(df[['artifact_id','cal_BP','cultural_period']].to_string())
print()

# ─────────────────────────────────────────────
# 6. Save results table
# ─────────────────────────────────────────────
results_cols = [
    'artifact_id', 'stratigraphic_unit', 'material',
    'f14_residual_ratio', 'sigma_f14_absolute',
    'age_BP_rounded', 'sigma_age_BP_rounded',
    'cal_BP', 'sigma_cal_BP', 'cal_BCE_CE_label',
    'cultural_period', 'clipped_flag', 'notes'
]
df_out = df[results_cols].copy()
df_out.to_csv('outputs/chronology_results.csv', index=False)
print("Results saved to outputs/chronology_results.csv")

# Re-sort AFTER cultural_period is assigned
df_sorted = df.sort_values('strat_rank').reset_index(drop=True)

# ─────────────────────────────────────────────
# 7. FIGURES
# ─────────────────────────────────────────────

# Color palette by cultural period
period_colors = {
    'Modern / Historical': '#e41a1c',
    'Late Imperial (Ming-Qing)': '#ff7f00',
    'Medieval (Tang-Song)': '#f0c040',
    'Early Imperial / Iron Age': '#4daf4a',
    'Bronze Age / Neolithic': '#377eb8',
    'Neolithic / Mesolithic': '#984ea3',
    'Late Paleolithic': '#a65628',
    'Middle Paleolithic': '#999999',
    'Early Paleolithic': '#000000',
}

# Map period names to colors (handle dash variants)
def get_color(period):
    # normalize dashes
    key = period.replace('\u2013', '-').replace('\u2014', '-')
    return period_colors.get(key, period_colors.get(period, '#333333'))

# ── Figure 1: F14 vs Conventional BP age ──────────────────────────────────
fig1, ax1 = plt.subplots(figsize=(10, 6))

for _, row in df.iterrows():
    color = get_color(row['cultural_period'])
    ax1.errorbar(
        row['f14_residual_ratio'], row['age_BP_rounded'],
        xerr=row['sigma_f14_absolute'],
        yerr=row['sigma_age_BP_rounded'],
        fmt='o', color=color, markersize=9, capsize=5,
        linewidth=1.5, label=row['artifact_id']
    )
    ax1.annotate(
        row['artifact_id'],
        xy=(row['f14_residual_ratio'], row['age_BP_rounded']),
        xytext=(8, 4), textcoords='offset points',
        fontsize=8, color=color
    )

# Overlay theoretical decay curve
f14_curve = np.linspace(0.001, 1.0, 500)
age_curve = -8033 * np.log(f14_curve)
ax1.plot(f14_curve, age_curve, 'k--', linewidth=1, alpha=0.4, label='Libby decay curve')

ax1.set_xlabel('F14 Residual Ratio (fraction modern)', fontsize=12)
ax1.set_ylabel('Conventional ¹⁴C Age (BP)', fontsize=12)
ax1.set_title('Huangtupo Site: F14 vs Conventional Radiocarbon Age', fontsize=13, fontweight='bold')
ax1.invert_yaxis()
ax1.legend(fontsize=8, loc='upper right')
ax1.grid(True, alpha=0.3)
plt.tight_layout()
fig1.savefig('report/images/fig1_f14_vs_age.png', dpi=150, bbox_inches='tight')
plt.close(fig1)
print("Saved fig1")

# ── Figure 2: Stratigraphic sequence with calibrated ages ─────────────────
fig2, ax2 = plt.subplots(figsize=(11, 7))

df_plot = df_sorted.copy()
y_positions = range(len(df_plot))

for i, (_, row) in enumerate(df_plot.iterrows()):
    color = get_color(row['cultural_period'])
    ax2.barh(
        i, row['sigma_cal_BP'] * 2,
        left=row['cal_BP'] - row['sigma_cal_BP'],
        height=0.5, color=color, alpha=0.35
    )
    ax2.plot(row['cal_BP'], i, 'D', color=color, markersize=10, zorder=5)
    ax2.annotate(
        f"{row['artifact_id']}\n{row['cal_BCE_CE_label']}",
        xy=(row['cal_BP'], i),
        xytext=(15, 0), textcoords='offset points',
        fontsize=8, va='center', color=color
    )

ax2.set_yticks(list(y_positions))
ax2.set_yticklabels(
    [f"{r['stratigraphic_unit'].replace('Huangtupo-','')}"
     for _, r in df_plot.iterrows()],
    fontsize=9
)
ax2.set_xlabel('Calibrated Age (cal BP)', fontsize=12)
ax2.set_title('Huangtupo Site: Stratigraphic Sequence & Calibrated Ages', fontsize=13, fontweight='bold')
ax2.invert_xaxis()
ax2.grid(True, alpha=0.3, axis='x')

# Legend for periods
legend_patches = []
for period, color in period_colors.items():
    norm_periods = [p.replace('\u2013','-').replace('\u2014','-') for p in df['cultural_period'].values]
    if period in norm_periods:
        legend_patches.append(mpatches.Patch(color=color, label=period))
ax2.legend(handles=legend_patches, fontsize=8, loc='lower right')

plt.tight_layout()
fig2.savefig('report/images/fig2_stratigraphic_sequence.png', dpi=150, bbox_inches='tight')
plt.close(fig2)
print("Saved fig2")

# ── Figure 3: Calibration curve overlay ───────────────────────────────────
fig3, ax3 = plt.subplots(figsize=(10, 6))

# Draw calibration curve
cal_bp_range = np.linspace(0, 50000, 1000)
c14_bp_range = np.interp(cal_bp_range, intcal_cal, intcal_14c)
ax3.plot(cal_bp_range, c14_bp_range, 'k-', linewidth=1.5, alpha=0.6, label='IntCal20 (approx.)')

for _, row in df.iterrows():
    color = get_color(row['cultural_period'])
    ax3.errorbar(
        row['cal_BP'], row['age_BP_rounded'],
        xerr=row['sigma_cal_BP'],
        yerr=row['sigma_age_BP_rounded'],
        fmt='o', color=color, markersize=9, capsize=5,
        linewidth=1.5
    )
    ax3.annotate(
        row['artifact_id'],
        xy=(row['cal_BP'], row['age_BP_rounded']),
        xytext=(8, 4), textcoords='offset points',
        fontsize=8, color=color
    )

ax3.set_xlabel('Calibrated Age (cal BP)', fontsize=12)
ax3.set_ylabel('Conventional ¹⁴C Age (BP)', fontsize=12)
ax3.set_title('Huangtupo Site: Calibration Curve Overlay', fontsize=13, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3)
plt.tight_layout()
fig3.savefig('report/images/fig3_calibration_overlay.png', dpi=150, bbox_inches='tight')
plt.close(fig3)
print("Saved fig3")

# ── Figure 4: Summary timeline with cultural periods ──────────────────────
fig4, ax4 = plt.subplots(figsize=(14, 5))

# Cultural period bands
period_bands = [
    (0,    100,   'Modern / Historical',       '#e41a1c', 0.10),
    (100,  500,   'Late Imperial (Ming–Qing)', '#ff7f00', 0.10),
    (500,  1500,  'Medieval (Tang–Song)',       '#f0c040', 0.10),
    (1500, 3000,  'Early Imperial / Iron Age', '#4daf4a', 0.10),
    (3000, 5000,  'Bronze Age / Neolithic',    '#377eb8', 0.10),
    (5000, 10000, 'Neolithic / Mesolithic',    '#984ea3', 0.10),
    (10000,15000, 'Late Paleolithic',           '#a65628', 0.10),
    (15000,30000, 'Middle Paleolithic',         '#999999', 0.10),
]

for (start, end, label, color, alpha) in period_bands:
    ax4.axvspan(start, end, alpha=alpha, color=color, label=label)
    mid = (start + end) / 2
    ax4.text(mid, 0.85, label, ha='center', va='center',
             fontsize=7, color=color, fontweight='bold',
             transform=ax4.get_xaxis_transform(), rotation=0)

for _, row in df.iterrows():
    color = get_color(row['cultural_period'])
    ax4.errorbar(
        row['cal_BP'], 0.5,
        xerr=row['sigma_cal_BP'],
        fmt='o', color=color, markersize=11, capsize=6,
        linewidth=2, zorder=5,
        transform=ax4.get_xaxis_transform()
    )
    ax4.annotate(
        row['artifact_id'],
        xy=(row['cal_BP'], 0.5),
        xytext=(0, -25), textcoords='offset points',
        ha='center', fontsize=8, color=color,
        transform=ax4.get_xaxis_transform(),
        arrowprops=dict(arrowstyle='->', color=color, lw=1)
    )

ax4.set_xlabel('Calibrated Age (cal BP)', fontsize=12)
ax4.set_xlim(0, 55000)
ax4.set_yticks([])
ax4.set_title('Huangtupo Site: Cultural Period Timeline', fontsize=13, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
fig4.savefig('report/images/fig4_cultural_timeline.png', dpi=150, bbox_inches='tight')
plt.close(fig4)
print("Saved fig4")

# ── Figure 5: Duplicate pair comparison (AC-111 vs AC-112) ────────────────
fig5, ax5 = plt.subplots(figsize=(7, 5))

pair = df[df['artifact_id'].isin(['AC-111', 'AC-112'])].copy()

for i, (_, row) in enumerate(pair.iterrows()):
    ax5.barh(
        i, row['sigma_age_BP_rounded'] * 2,
        left=row['age_BP_rounded'] - row['sigma_age_BP_rounded'],
        height=0.4, color='#377eb8', alpha=0.4
    )
    ax5.plot(row['age_BP_rounded'], i, 's', color='#377eb8', markersize=12)
    ax5.annotate(
        f"{row['artifact_id']}: {row['age_BP_rounded']} ± {row['sigma_age_BP_rounded']} BP",
        xy=(row['age_BP_rounded'], i),
        xytext=(10, 0), textcoords='offset points',
        fontsize=10, va='center'
    )

ax5.set_yticks([0, 1])
ax5.set_yticklabels([pair.iloc[0]['artifact_id'], pair.iloc[1]['artifact_id']], fontsize=11)
ax5.set_xlabel('Conventional ¹⁴C Age (BP)', fontsize=12)
ax5.set_title('Duplicate Pair Comparison: AC-111 vs AC-112\n(same ridge source, duplicate chronology check)', fontsize=11, fontweight='bold')
ax5.grid(True, alpha=0.3, axis='x')

# Compute overlap
age1, sig1 = pair.iloc[0]['age_BP'], pair.iloc[0]['sigma_age_BP']
age2, sig2 = pair.iloc[1]['age_BP'], pair.iloc[1]['sigma_age_BP']
diff = abs(age1 - age2)
combined_sigma = np.sqrt(sig1**2 + sig2**2)
z_score = diff / combined_sigma
ax5.text(0.05, 0.05,
         f"Δage = {diff:.1f} yr\nCombined σ = {combined_sigma:.1f} yr\nZ = {z_score:.2f}",
         transform=ax5.transAxes, fontsize=10,
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
fig5.savefig('report/images/fig5_duplicate_pair.png', dpi=150, bbox_inches='tight')
plt.close(fig5)
print("Saved fig5")

print("\nAll figures saved.")
print("\nFinal results table:")
print(df_out.to_string())

# Save a markdown-friendly table
with open('outputs/results_table.md', 'w') as f:
    f.write('| Artifact | Strat. Unit | Material | F14 | σ(F14) | Age BP | σ(BP) | Cal BP | σ(Cal) | Cal BCE/CE | Period | Clipped | Notes |\n')
    f.write('|---|---|---|---|---|---|---|---|---|---|---|---|---|\n')
    for _, row in df_out.iterrows():
        f.write(f"| {row['artifact_id']} | {row['stratigraphic_unit']} | {row['material']} "
                f"| {row['f14_residual_ratio']:.4f} | {row['sigma_f14_absolute']:.4f} "
                f"| {row['age_BP_rounded']} | {row['sigma_age_BP_rounded']} "
                f"| {int(round(row['cal_BP']))} | {int(round(row['sigma_cal_BP']))} "
                f"| {row['cal_BCE_CE_label']} | {row['cultural_period']} "
                f"| {'Yes' if row['clipped_flag'] else 'No'} | {row['notes']} |\n")

print("\nMarkdown table saved to outputs/results_table.md")
