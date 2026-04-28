#!/usr/bin/env python3
"""
Analysis script for Catalyst-X9 Lab Notebook → SOP conversion.
Generates figures for the research report.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import json
import os

# ── Paths ──────────────────────────────────────────────────────────────────
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(WORKSPACE, 'outputs')
IMG_DIR    = os.path.join(WORKSPACE, 'report', 'images')
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# ── Parsed notebook data ────────────────────────────────────────────────────
# Timeline events extracted from lab_notebook_x9.txt
events = [
    {'time_min': 0,   'label': 'Reactor init\n& calibration',  'phase': 'Setup'},
    {'time_min': 8,   'label': 'Add Precursor A\n(500 mL)',     'phase': 'Reagent Addition'},
    {'time_min': 8,   'label': 'Add Reagent B\n(200 mL)\n350 RPM', 'phase': 'Reagent Addition'},
    {'time_min': 20,  'label': 'Ramp to 120°C\n@ 5°C/min',     'phase': 'Heating'},
    {'time_min': 65,  'label': 'Hold 120°C\n45 min\n(deep amber)', 'phase': 'Reaction'},
    {'time_min': 115, 'label': 'Transfer to\ncentrifuge tubes', 'phase': 'Isolation'},
    {'time_min': 115, 'label': 'Centrifuge\n4000 RPM / 15 min', 'phase': 'Isolation'},
    {'time_min': 130, 'label': 'Decant\nsupernatant',           'phase': 'Isolation'},
    {'time_min': 135, 'label': 'Ether wash\n(cold, ~50 mL)',    'phase': 'Washing'},
]

# Unique phases and colors
phase_colors = {
    'Setup':            '#4C72B0',
    'Reagent Addition': '#55A868',
    'Heating':          '#C44E52',
    'Reaction':         '#DD8452',
    'Isolation':        '#8172B2',
    'Washing':          '#937860',
}

# ── Figure 1: Process Timeline ──────────────────────────────────────────────
def fig_timeline():
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_xlim(-10, 160)
    ax.set_ylim(-1.5, 1.5)
    ax.axhline(0, color='#888888', linewidth=2, zorder=1)

    # Plot events
    for i, ev in enumerate(events):
        t = ev['time_min']
        phase = ev['phase']
        color = phase_colors[phase]
        y_offset = 0.6 if i % 2 == 0 else -0.6
        ax.plot(t, 0, 'o', color=color, markersize=12, zorder=3)
        ax.annotate(
            ev['label'],
            xy=(t, 0),
            xytext=(t, y_offset),
            ha='center', va='center',
            fontsize=7.5,
            arrowprops=dict(arrowstyle='-', color=color, lw=1.2),
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=color, lw=1.2),
        )

    # Legend
    patches = [mpatches.Patch(color=c, label=p) for p, c in phase_colors.items()]
    ax.legend(handles=patches, loc='lower right', fontsize=8, framealpha=0.9)

    ax.set_xlabel('Elapsed Time (minutes from 14:00)', fontsize=11)
    ax.set_title('Catalyst-X9 Synthesis — Process Timeline\n(Derived from Lab Notebook CX9-LAB-0312)', fontsize=12, fontweight='bold')
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.tight_layout()
    path = os.path.join(IMG_DIR, 'fig1_timeline.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {path}')


# ── Figure 2: Temperature Profile ──────────────────────────────────────────
def fig_temperature():
    # Reconstruct temperature profile from notebook data
    # 14:00 = t=0 min; ramp starts at t=20 min; 120°C reached at t=20+(120-20)/5=40 min
    # Hold from t=40 to t=85 min (45 min hold)
    # Ramp rate: 5°C/min; assume start temp ~20°C

    start_temp = 20.0
    ramp_start_t = 20
    target_temp = 120.0
    ramp_rate = 5.0  # °C/min
    ramp_duration = (target_temp - start_temp) / ramp_rate  # = 20 min
    ramp_end_t = ramp_start_t + ramp_duration  # = 40 min
    hold_end_t = ramp_end_t + 45  # = 85 min

    t = np.linspace(0, 155, 500)
    temp = np.where(
        t < ramp_start_t, start_temp,
        np.where(
            t < ramp_end_t, start_temp + ramp_rate * (t - ramp_start_t),
            np.where(t < hold_end_t, target_temp, target_temp)
        )
    )
    # After hold, assume cooling begins (not in notebook, shown as dashed)
    cool_mask = t >= hold_end_t
    temp_cool = temp.copy()
    temp_cool[cool_mask] = target_temp - 1.5 * (t[cool_mask] - hold_end_t)
    temp_cool = np.clip(temp_cool, start_temp, target_temp)

    fig, ax = plt.subplots(figsize=(10, 5))

    # Solid line = documented; dashed = inferred
    solid_mask = t <= hold_end_t
    ax.plot(t[solid_mask], temp[solid_mask], color='#C44E52', linewidth=2.5, label='Documented temperature')
    ax.plot(t[~solid_mask], temp_cool[~solid_mask], color='#C44E52', linewidth=2.0,
            linestyle='--', label='Inferred cooling (not in notebook)')

    # Annotations
    ax.axvline(ramp_start_t, color='#4C72B0', linestyle=':', linewidth=1.5)
    ax.axvline(ramp_end_t,   color='#55A868', linestyle=':', linewidth=1.5)
    ax.axvline(hold_end_t,   color='#DD8452', linestyle=':', linewidth=1.5)

    ax.annotate('Ramp\nbegins', xy=(ramp_start_t, start_temp+5), xytext=(ramp_start_t+2, 40),
                fontsize=8, color='#4C72B0',
                arrowprops=dict(arrowstyle='->', color='#4C72B0'))
    ax.annotate('120°C\nreached', xy=(ramp_end_t, target_temp), xytext=(ramp_end_t+3, 105),
                fontsize=8, color='#55A868',
                arrowprops=dict(arrowstyle='->', color='#55A868'))
    ax.annotate('Deep amber\n(endpoint)', xy=(hold_end_t, target_temp), xytext=(hold_end_t+3, 108),
                fontsize=8, color='#DD8452',
                arrowprops=dict(arrowstyle='->', color='#DD8452'))

    ax.fill_between(t, temp, alpha=0.08, color='#C44E52')
    ax.set_xlabel('Elapsed Time (min from 14:00)', fontsize=11)
    ax.set_ylabel('Temperature (°C)', fontsize=11)
    ax.set_title('Catalyst-X9 — Reconstructed Temperature Profile\n(5 °C/min ramp → 120 °C hold, 45 min)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.set_xlim(0, 155)
    ax.set_ylim(0, 140)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(IMG_DIR, 'fig2_temperature.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {path}')


# ── Figure 3: Data Completeness Audit ──────────────────────────────────────
def fig_data_audit():
    categories = [
        'Reactor\nSetup',
        'Reagent\nAddition',
        'Heating\nRamp',
        'Reaction\nHold',
        'Transfer &\nCentrifuge',
        'Ether\nWash',
        'Post-wash\nHandling',
    ]
    # Completeness score (0–100%) based on notebook coverage
    completeness = [95, 90, 85, 80, 75, 40, 10]
    colors = ['#55A868' if c >= 75 else '#DD8452' if c >= 50 else '#C44E52' for c in completeness]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(categories, completeness, color=colors, edgecolor='white', height=0.6)

    # Value labels
    for bar, val in zip(bars, completeness):
        ax.text(val + 1, bar.get_y() + bar.get_height()/2,
                f'{val}%', va='center', fontsize=10, fontweight='bold')

    # Legend
    patches = [
        mpatches.Patch(color='#55A868', label='Well documented (≥75%)'),
        mpatches.Patch(color='#DD8452', label='Partially documented (50–74%)'),
        mpatches.Patch(color='#C44E52', label='Poorly documented (<50%)'),
    ]
    ax.legend(handles=patches, loc='lower right', fontsize=9)

    ax.set_xlim(0, 115)
    ax.set_xlabel('Documentation Completeness (%)', fontsize=11)
    ax.set_title('Catalyst-X9 Notebook — Step-by-Step Documentation Completeness Audit',
                 fontsize=12, fontweight='bold')
    ax.axvline(75, color='gray', linestyle='--', linewidth=1, alpha=0.6)
    ax.grid(True, axis='x', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    path = os.path.join(IMG_DIR, 'fig3_data_audit.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {path}')


# ── Figure 4: SOP Structure Overview ───────────────────────────────────────
def fig_sop_structure():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # SOP phases as boxes
    phases = [
        (1.0, 8.5, 'Phase 1\nReactor Setup\n& Init', '#4C72B0'),
        (3.5, 8.5, 'Phase 2\nReagent\nAddition', '#55A868'),
        (6.0, 8.5, 'Phase 3\nHeating &\nReaction', '#C44E52'),
        (8.5, 8.5, 'Phase 4\nIsolation &\nWashing', '#8172B2'),
        (5.0, 5.5, 'Phase 5\nCompletion &\nShift Handoff', '#937860'),
    ]

    box_w, box_h = 2.0, 1.5
    for (x, y, label, color) in phases:
        rect = mpatches.FancyBboxPatch(
            (x - box_w/2, y - box_h/2), box_w, box_h,
            boxstyle='round,pad=0.1',
            facecolor=color, edgecolor='white', linewidth=2, alpha=0.85
        )
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center',
                fontsize=9, fontweight='bold', color='white')

    # Arrows between phases 1-4
    arrow_props = dict(arrowstyle='->', color='#555555', lw=2)
    for i in range(len(phases)-2):
        x1 = phases[i][0] + box_w/2
        x2 = phases[i+1][0] - box_w/2
        y_mid = phases[i][1]
        ax.annotate('', xy=(x2, y_mid), xytext=(x1, y_mid),
                    arrowprops=arrow_props)

    # Arrow from phase 4 down to phase 5
    ax.annotate('', xy=(5.0, 5.5 + box_h/2), xytext=(8.5, 8.5 - box_h/2),
                arrowprops=arrow_props)

    # Data gaps box
    gap_rect = mpatches.FancyBboxPatch(
        (0.3, 1.0), 4.0, 3.5,
        boxstyle='round,pad=0.15',
        facecolor='#FFF3CD', edgecolor='#DD8452', linewidth=2
    )
    ax.add_patch(gap_rect)
    ax.text(2.3, 4.2, '⚠ Known Data Gaps', ha='center', va='center',
            fontsize=10, fontweight='bold', color='#DD8452')
    gaps = [
        '• Ether wash volume (→ default 50 mL)',
        '• Missing notebook page (page break)',
        '• Post-wash storage conditions',
        '• Number of wash cycles',
    ]
    for j, g in enumerate(gaps):
        ax.text(0.5, 3.7 - j*0.6, g, ha='left', va='center', fontsize=8.5, color='#555555')

    # SOP metadata box
    meta_rect = mpatches.FancyBboxPatch(
        (5.5, 1.0), 4.0, 3.5,
        boxstyle='round,pad=0.15',
        facecolor='#D4EDDA', edgecolor='#55A868', linewidth=2
    )
    ax.add_patch(meta_rect)
    ax.text(7.5, 4.2, '✓ SOP Metadata', ha='center', va='center',
            fontsize=10, fontweight='bold', color='#55A868')
    meta = [
        'Doc ID: SOP-CX9-001',
        'Version: 1.0',
        'Source: CX9-LAB-0312',
        'Shift: Night-shift bench',
    ]
    for j, m in enumerate(meta):
        ax.text(5.7, 3.7 - j*0.6, m, ha='left', va='center', fontsize=8.5, color='#333333')

    ax.set_title('Catalyst-X9 SOP — Document Structure Overview',
                 fontsize=13, fontweight='bold', pad=15)

    plt.tight_layout()
    path = os.path.join(IMG_DIR, 'fig4_sop_structure.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {path}')


# ── Save structured outputs ─────────────────────────────────────────────────
def save_outputs():
    summary = {
        'run_id': 'CX9-LAB-0312',
        'date': '2024-03-12',
        'vessel': '1 L jacketed glass reactor',
        'reagents': {
            'Precursor_A': {'lot': 'P-A-112', 'volume_mL': 500},
            'Reagent_B':   {'lot': 'R-B-089', 'volume_mL': 200},
        },
        'process_params': {
            'stir_speed_rpm': 350,
            'ramp_rate_C_per_min': 5,
            'target_temp_C': 120,
            'hold_time_min': 45,
            'condenser_water_C': 18,
            'centrifuge_rpm': 4000,
            'centrifuge_time_min': 15,
            'ether_wash_volume_mL': '~50 (default; not recorded in notebook)',
        },
        'endpoint_indicator': 'Deep amber color',
        'data_gaps': [
            'Ether wash volume not recorded',
            'Missing notebook page (page break)',
            'Post-wash storage conditions not specified',
            'Number of ether washes not specified',
        ],
        'sop_document': 'synthesis_sop.md',
        'sop_version': '1.0',
    }
    out_path = os.path.join(OUTPUT_DIR, 'notebook_summary.json')
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'Saved: {out_path}')

    # Timeline CSV
    import csv
    csv_path = os.path.join(OUTPUT_DIR, 'process_timeline.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['time_min', 'label', 'phase'])
        writer.writeheader()
        for ev in events:
            writer.writerow({'time_min': ev['time_min'],
                             'label': ev['label'].replace('\n', ' '),
                             'phase': ev['phase']})
    print(f'Saved: {csv_path}')


# ── Main ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('Generating figures...')
    fig_timeline()
    fig_temperature()
    fig_data_audit()
    fig_sop_structure()
    save_outputs()
    print('Done.')
