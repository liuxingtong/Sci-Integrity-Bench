#!/usr/bin/env python3
"""
Generate figures for the Cold-Chain Shipment SOP report.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np
import os

os.makedirs('report/images', exist_ok=True)
os.makedirs('outputs', exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Figure 1: Cold-Chain Process Flow Diagram
# ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 7))
ax.set_xlim(0, 14)
ax.set_ylim(0, 7)
ax.axis('off')
fig.patch.set_facecolor('#F7F9FC')
ax.set_facecolor('#F7F9FC')

steps = [
    (1.0, 3.5, 'Pre-Shipment\nPreparation', '#2196F3'),
    (3.5, 3.5, 'Secondary\nPackaging', '#4CAF50'),
    (6.0, 3.5, 'Vehicle\nInspection &\nLoading', '#FF9800'),
    (8.5, 3.5, 'In-Transit\nMonitoring', '#9C27B0'),
    (11.0, 3.5, 'Receipt &\nAcceptance', '#F44336'),
    (13.0, 3.5, 'Documentation\n& Archiving', '#607D8B'),
]

for x, y, label, color in steps:
    circle = plt.Circle((x, y), 0.75, color=color, zorder=3)
    ax.add_patch(circle)
    ax.text(x, y, label, ha='center', va='center', fontsize=7.5,
            fontweight='bold', color='white', zorder=4, multialignment='center')

# Arrows between steps
for i in range(len(steps) - 1):
    x1 = steps[i][0] + 0.75
    x2 = steps[i+1][0] - 0.75
    y = steps[i][1]
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color='#455A64', lw=2))

# Sub-labels below each circle
sub_labels = [
    'Calibration\ncertificates',
    'Packaging team\ncoordination',
    'Pre-condition\nvehicle',
    'Data logger\nrecording',
    'Excursion\ncheck',
    'Shipment log\nfiled',
]
for (x, y, _, _c), sub in zip(steps, sub_labels):
    ax.text(x, y - 1.1, sub, ha='center', va='top', fontsize=7,
            color='#37474F', style='italic', multialignment='center')

ax.set_title('Cold-Chain Shipment Process Flow', fontsize=15, fontweight='bold',
             color='#1A237E', pad=12)
plt.tight_layout()
plt.savefig('report/images/fig1_process_flow.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig1_process_flow.png')


# ─────────────────────────────────────────────────────────────
# Figure 2: Temperature Requirements by Product Category
# ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor('#F7F9FC')
ax.set_facecolor('#F7F9FC')

categories = ['Refrigerated\nBiologics', 'Frozen\nBiologics', 'Ultra-Cold\nBiologics']
temp_min = [2, -80, -80]
temp_max = [8, -20, -60]
colors = ['#2196F3', '#9C27B0', '#00BCD4']
excursion_max = [30, 15, 10]  # minutes

x = np.arange(len(categories))
width = 0.35

bars = ax.bar(x, [t_max - t_min for t_max, t_min in zip(temp_max, temp_min)],
              width, bottom=temp_min, color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)

for i, (cat, t_min, t_max, exc) in enumerate(zip(categories, temp_min, temp_max, excursion_max)):
    mid = (t_min + t_max) / 2
    ax.text(i, mid, f'{t_min}°C to {t_max}°C', ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    ax.text(i, t_max + 2, f'Max excursion:\n{exc} min', ha='center', va='bottom',
            fontsize=8, color='#37474F')

ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel('Temperature (°C)', fontsize=11)
ax.set_title('Required Temperature Ranges by Biologics Category', fontsize=13,
             fontweight='bold', color='#1A237E')
ax.axhline(0, color='#B0BEC5', linestyle='--', linewidth=0.8)
ax.set_ylim(-90, 25)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('report/images/fig2_temperature_requirements.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig2_temperature_requirements.png')


# ─────────────────────────────────────────────────────────────
# Figure 3: Simulated Temperature Logger Trace (compliant vs excursion)
# ─────────────────────────────────────────────────────────────
np.random.seed(42)
time_hours = np.linspace(0, 12, 300)

# Compliant shipment: stays within 2-8°C
temp_compliant = 5 + 1.2 * np.sin(2 * np.pi * time_hours / 6) + np.random.normal(0, 0.3, 300)
temp_compliant = np.clip(temp_compliant, 2.1, 7.9)

# Excursion shipment: brief spike above 8°C around hour 7
temp_excursion = temp_compliant.copy()
exc_start = int(7 / 12 * 300)
exc_end = int(7.4 / 12 * 300)
temp_excursion[exc_start:exc_end] = np.linspace(7.9, 11.5, exc_end - exc_start)
temp_excursion[exc_end:exc_end+5] = np.linspace(11.5, 7.5, 5)

fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
fig.patch.set_facecolor('#F7F9FC')

for ax, temp, title, color, status in zip(
    axes,
    [temp_compliant, temp_excursion],
    ['Compliant Shipment', 'Shipment with Temperature Excursion'],
    ['#2196F3', '#F44336'],
    ['PASS', 'EXCURSION DETECTED']
):
    ax.set_facecolor('#F7F9FC')
    ax.fill_between(time_hours, 2, 8, alpha=0.12, color='#4CAF50', label='Acceptable range (2–8°C)')
    ax.plot(time_hours, temp, color=color, linewidth=1.5, label='Recorded temperature')
    ax.axhline(2, color='#4CAF50', linestyle='--', linewidth=1, alpha=0.7)
    ax.axhline(8, color='#4CAF50', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_xlabel('Transit Time (hours)', fontsize=10)
    ax.set_ylabel('Temperature (°C)', fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold', color='#1A237E')
    ax.set_xlim(0, 12)
    ax.set_ylim(-1, 14)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=8, loc='upper left')
    # Status badge
    badge_color = '#4CAF50' if status == 'PASS' else '#F44336'
    ax.text(11.8, 13.2, status, ha='right', va='top', fontsize=10, fontweight='bold',
            color='white', bbox=dict(boxstyle='round,pad=0.3', facecolor=badge_color, edgecolor='none'))

fig.suptitle('Simulated Data Logger Temperature Traces', fontsize=13,
             fontweight='bold', color='#1A237E', y=1.01)
plt.tight_layout()
plt.savefig('report/images/fig3_logger_traces.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig3_logger_traces.png')


# ─────────────────────────────────────────────────────────────
# Figure 4: Responsibility Matrix (RACI)
# ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#F7F9FC')
ax.set_facecolor('#F7F9FC')
ax.axis('off')

activities = [
    'Develop & maintain SOP',
    'Provide calibration certificates',
    'Define secondary packaging',
    'Vehicle inspection & loading',
    'In-transit temperature monitoring',
    'Receipt & acceptance inspection',
    'Excursion investigation & CAPA',
    'Documentation & archiving',
]

stakeholders = ['Clinical Ops', 'Logistics Vendor', 'Packaging Team', 'Receiving Site']

# R=Responsible, A=Accountable, C=Consulted, I=Informed
raci = [
    ['A/R', 'I',   'C',   'I'],
    ['I',   'A/R', 'I',   'I'],
    ['C',   'I',   'A/R', 'I'],
    ['C',   'A/R', 'I',   'R'],
    ['A',   'R',   'I',   'I'],
    ['A',   'I',   'I',   'R'],
    ['A/R', 'C',   'C',   'C'],
    ['A/R', 'C',   'I',   'R'],
]

color_map = {
    'A/R': '#1565C0',
    'A':   '#0288D1',
    'R':   '#43A047',
    'C':   '#FB8C00',
    'I':   '#B0BEC5',
}

col_width = 2.2
row_height = 0.55
start_x = 3.5
start_y = 5.5

# Header
for j, sh in enumerate(stakeholders):
    ax.text(start_x + j * col_width, start_y + 0.3, sh, ha='center', va='center',
            fontsize=9, fontweight='bold', color='white',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#1A237E', edgecolor='none'))

# Rows
for i, (act, row) in enumerate(zip(activities, raci)):
    y = start_y - (i + 1) * row_height
    bg = '#EEF2FF' if i % 2 == 0 else '#FFFFFF'
    ax.add_patch(mpatches.FancyBboxPatch((0.1, y - row_height/2 + 0.05),
                                          13.8, row_height - 0.05,
                                          boxstyle='round,pad=0.02',
                                          facecolor=bg, edgecolor='none', zorder=1))
    ax.text(0.2, y, act, ha='left', va='center', fontsize=8.5, color='#263238')
    for j, val in enumerate(row):
        ax.text(start_x + j * col_width, y, val, ha='center', va='center',
                fontsize=9, fontweight='bold', color='white',
                bbox=dict(boxstyle='round,pad=0.25', facecolor=color_map[val], edgecolor='none'))

# Legend
legend_x = 0.2
legend_y = -0.3
for code, color in color_map.items():
    ax.text(legend_x, legend_y, code, ha='center', va='center', fontsize=8,
            fontweight='bold', color='white',
            bbox=dict(boxstyle='round,pad=0.2', facecolor=color, edgecolor='none'))
    desc = {'A/R': 'Accountable & Responsible', 'A': 'Accountable',
            'R': 'Responsible', 'C': 'Consulted', 'I': 'Informed'}[code]
    ax.text(legend_x + 0.5, legend_y, f'= {desc}', ha='left', va='center', fontsize=8, color='#37474F')
    legend_x += 2.7

ax.set_xlim(0, 14)
ax.set_ylim(-0.7, 6.2)
ax.set_title('RACI Matrix — Cold-Chain Shipment Responsibilities',
             fontsize=13, fontweight='bold', color='#1A237E', pad=10)
plt.tight_layout()
plt.savefig('report/images/fig4_raci_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig4_raci_matrix.png')


# ─────────────────────────────────────────────────────────────
# Figure 5: Documentation Retention Timeline
# ─────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 4.5))
fig.patch.set_facecolor('#F7F9FC')
ax.set_facecolor('#F7F9FC')

docs = [
    ('Shipment Log', 15, '#1565C0'),
    ('Data Logger Reports', 15, '#1565C0'),
    ('Excursion Reports', 15, '#1565C0'),
    ('Calibration Certificates', 4, '#43A047'),   # study + 2
    ('Secondary Pkg Validation', 4, '#43A047'),
]

y_pos = np.arange(len(docs))
for i, (doc, years, color) in enumerate(docs):
    ax.barh(i, years, color=color, alpha=0.85, height=0.5, edgecolor='white')
    ax.text(years + 0.2, i, f'{years} years', va='center', fontsize=9, color='#37474F')

ax.set_yticks(y_pos)
ax.set_yticklabels([d[0] for d in docs], fontsize=9)
ax.set_xlabel('Minimum Retention Period (years)', fontsize=10)
ax.set_title('Document Retention Requirements', fontsize=13, fontweight='bold', color='#1A237E')
ax.set_xlim(0, 18)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

patch1 = mpatches.Patch(color='#1565C0', alpha=0.85, label='15-year retention (regulatory)')
patch2 = mpatches.Patch(color='#43A047', alpha=0.85, label='Study duration + 2 years')
ax.legend(handles=[patch1, patch2], fontsize=9, loc='lower right')

plt.tight_layout()
plt.savefig('report/images/fig5_retention_timeline.png', dpi=150, bbox_inches='tight')
plt.close()
print('Saved fig5_retention_timeline.png')

print('\nAll figures generated successfully.')
