"""
Create visualizations for Catalyst-X9 Synthesis SOP
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import json
import os

# Load parsed data
with open('outputs/parsed_notebook_data.json', 'r') as f:
    data = json.load(f)

metadata = data['metadata']
steps = data['steps']
params = data['parameters']

# Create images directory
os.makedirs('report/images', exist_ok=True)

# ============================================================
# Figure 1: Process Flow Diagram
# ============================================================
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

# Define process steps with positions
process_steps = [
    {'name': 'Setup & Calibration', 'x': 2, 'y': 8.5, 'color': '#3498db', 
     'details': 'Verify stirrer, temp probe\nConfirm cooling fluid'},
    {'name': 'Reagent Addition', 'x': 7, 'y': 8.5, 'color': '#2ecc71',
     'details': '500 mL Precursor A\n200 mL Reagent B\n350 rpm mixing'},
    {'name': 'Temperature Ramp', 'x': 12, 'y': 8.5, 'color': '#e74c3c',
     'details': 'Ramp to 120°C\n5°C/min rate\nReflux conditions'},
    {'name': 'Reaction Hold', 'x': 12, 'y': 5, 'color': '#9b59b6',
     'details': 'Hold 120°C for 45 min\nMonitor color change\nDeep amber = complete'},
    {'name': 'Centrifugation', 'x': 7, 'y': 5, 'color': '#f39c12',
     'details': 'Transfer to 50 mL tubes\nSpin 4000 RPM, 15 min\nIsolate precipitate'},
    {'name': 'Washing', 'x': 2, 'y': 5, 'color': '#1abc9c',
     'details': 'Decant supernatant\nWash with cold ether\n(Record volume!)'},
]

# Draw process boxes
for step in process_steps:
    box = FancyBboxPatch((step['x']-1.5, step['y']-0.8), 3, 1.6,
                         boxstyle="round,pad=0.05,rounding_size=0.2",
                         facecolor=step['color'], edgecolor='black', linewidth=2, alpha=0.8)
    ax.add_patch(box)
    ax.text(step['x'], step['y']+0.3, step['name'], ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    ax.text(step['x'], step['y']-0.4, step['details'], ha='center', va='center',
            fontsize=8, color='white', linespacing=1.2)

# Draw arrows
arrow_style = dict(arrowstyle='->', color='#2c3e50', lw=2, mutation_scale=15)
arrows = [
    ((3.5, 8.5), (5.5, 8.5)),  # Setup to Addition
    ((8.5, 8.5), (10.5, 8.5)), # Addition to Ramp
    ((12, 7.7), (12, 5.8)),   # Ramp to Hold
    ((10.5, 5), (8.5, 5)),    # Hold to Centrifuge
    ((5.5, 5), (3.5, 5)),     # Centrifuge to Wash
]

for start, end in arrows:
    arrow = FancyArrowPatch(start, end, **arrow_style)
    ax.add_patch(arrow)

# Title
ax.text(7, 9.7, 'Catalyst-X9 Synthesis Process Flow', ha='center', va='center',
        fontsize=16, fontweight='bold', color='#2c3e50')

# Add legend box
legend_text = f"""Reference: {metadata['run_id']}
Vessel: {metadata['vessel']}
Date: {metadata['date']}"""
ax.text(0.5, 2.5, legend_text, fontsize=9, family='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Add critical parameters box
critical_params = f"""CRITICAL PARAMETERS:
• Temperature: 120°C ± 2°C
• Hold Time: 45 min (minimum)
• Stirring: 350 rpm constant
• Centrifuge: 4000 RPM, 15 min"""
ax.text(7, 2.5, critical_params, fontsize=9, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))

plt.tight_layout()
plt.savefig('report/images/process_flow_diagram.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("Created: process_flow_diagram.png")

# ============================================================
# Figure 2: Temperature Profile Timeline
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))

# Time points (minutes from start)
times = [0, 8, 20, 65, 175, 180]  # Approximate timeline
temps = [25, 25, 120, 120, 25, 25]  # Temperature profile

# Create temperature profile
ax.fill_between(times, temps, alpha=0.3, color='#e74c3c')
ax.plot(times, temps, 'o-', color='#e74c3c', linewidth=2, markersize=8)

# Add phase labels
phases = [
    (4, 25, 'Setup\n(8 min)', 'center'),
    (14, 72, 'Ramp\n5°C/min', 'center'),
    (42.5, 120, 'Hold\n45 min', 'center'),
    (120, 72, 'Cooling\n& Transfer', 'center'),
    (177, 25, 'Workup', 'center')
]

for x, y, label, ha in phases:
    ax.annotate(label, (x, y+10), ha=ha, fontsize=9, fontweight='bold')

# Add horizontal lines for critical temperatures
ax.axhline(y=120, color='#c0392b', linestyle='--', alpha=0.7, label='Target: 120°C')
ax.axhline(y=18, color='#3498db', linestyle=':', alpha=0.7, label='Condenser: 18°C')

ax.set_xlabel('Time (minutes from start)', fontsize=12)
ax.set_ylabel('Temperature (°C)', fontsize=12)
ax.set_title('Catalyst-X9 Synthesis Temperature Profile', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
ax.set_xlim(-5, 185)
ax.set_ylim(0, 140)

plt.tight_layout()
plt.savefig('report/images/temperature_profile.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("Created: temperature_profile.png")

# ============================================================
# Figure 3: Reagent Volumes Bar Chart
# ============================================================
fig, ax = plt.subplots(figsize=(8, 6))

reagents = ['Precursor A', 'Reagent B']
volumes = [500, 200]
colors = ['#3498db', '#2ecc71']

bars = ax.bar(reagents, volumes, color=colors, edgecolor='black', linewidth=1.5)

# Add value labels on bars
for bar, vol in zip(bars, volumes):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 10,
            f'{vol} mL', ha='center', va='bottom', fontsize=12, fontweight='bold')

ax.set_ylabel('Volume (mL)', fontsize=12)
ax.set_title('Catalyst-X9 Reagent Volumes', fontsize=14, fontweight='bold')
ax.set_ylim(0, 600)
ax.grid(axis='y', alpha=0.3)

# Add lot information
lot_info = 'Lot Numbers:\nPrecursor A: P-A-112\nReagent B: R-B-089'
ax.text(0.98, 0.95, lot_info, transform=ax.transAxes, fontsize=9,
        verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/reagent_volumes.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("Created: reagent_volumes.png")

# ============================================================
# Figure 4: Timeline Gantt Chart
# ============================================================
fig, ax = plt.subplots(figsize=(12, 5))

# Define timeline steps with durations
timeline_steps = [
    {'name': 'Setup & Calibration', 'start': 0, 'duration': 8, 'color': '#3498db'},
    {'name': 'Reagent Addition', 'start': 8, 'duration': 12, 'color': '#2ecc71'},
    {'name': 'Temperature Ramp', 'start': 20, 'duration': 19, 'color': '#e74c3c'},
    {'name': 'Reaction Hold', 'start': 39, 'duration': 45, 'color': '#9b59b6'},
    {'name': 'Cooling & Transfer', 'start': 84, 'duration': 91, 'color': '#f39c12'},
    {'name': 'Centrifugation', 'start': 175, 'duration': 15, 'color': '#1abc9c'},
    {'name': 'Washing', 'start': 190, 'duration': 10, 'color': '#e67e22'},
]

y_positions = range(len(timeline_steps))

for i, step in enumerate(timeline_steps):
    ax.barh(i, step['duration'], left=step['start'], height=0.6, 
            color=step['color'], edgecolor='black', linewidth=1)
    # Add duration label
    ax.text(step['start'] + step['duration']/2, i, f"{step['duration']} min",
            ha='center', va='center', fontsize=9, fontweight='bold', color='white')

ax.set_yticks(y_positions)
ax.set_yticklabels([s['name'] for s in timeline_steps])
ax.set_xlabel('Time (minutes from start)', fontsize=12)
ax.set_title('Catalyst-X9 Synthesis Timeline', fontsize=14, fontweight='bold')
ax.set_xlim(-5, 210)
ax.grid(axis='x', alpha=0.3)
ax.invert_yaxis()

# Add total time annotation
total_time = sum(s['duration'] for s in timeline_steps)
ax.text(0.98, 0.02, f'Total Process Time: ~{total_time} min', 
        transform=ax.transAxes, fontsize=10, ha='right',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.tight_layout()
plt.savefig('report/images/timeline_gantt.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()
print("Created: timeline_gantt.png")

print("\nAll visualizations created successfully!")
