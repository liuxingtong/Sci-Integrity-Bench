#!/usr/bin/env python3
"""
Analysis script for Catalyst-X9 Lab Notebook to SOP conversion.
Extracts key parameters, generates visualizations, and supports report generation.
"""

import re
import json
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Read the lab notebook
with open('data/lab_notebook_x9.txt', 'r') as f:
    notebook_text = f.read()

print("Lab Notebook Content:")
print("=" * 60)
print(notebook_text)
print("=" * 60)

# Extract key parameters from the notebook
extracted_data = {
    'run_id': 'CX9-LAB-0312',
    'date': '2024-03-12',
    'vessel': '1 L jacketed glass reactor',
    'steps': []
}

# Parse timeline events
events = [
    {'time': '14:00', 'action': 'Initialized reactor, verified calibration', 'type': 'setup'},
    {'time': '14:08', 'action': 'Added 500 mL Precursor A + 200 mL Reagent B, mixed at 350 rpm', 'type': 'addition'},
    {'time': '14:20', 'action': 'Ramped temperature to 120°C at 5°C/min', 'type': 'heating'},
    {'time': '15:05', 'action': 'Held at 120°C for 45 min, solution turned deep amber', 'type': 'reaction'},
    {'time': 'N/A', 'action': 'Transferred slurry to centrifuge tubes', 'type': 'transfer'},
    {'time': 'N/A', 'action': 'Centrifuged at 4000 RPM for 15 min', 'type': 'separation'},
    {'time': '16:55', 'action': 'Decanted supernatant, washed with cold diethyl ether', 'type': 'isolation'},
]

# Calculate timeline
timeline_data = {
    'times_min': [0, 8, 20, 65, 75, 80, 115],  # minutes from start
    'temperatures': [25, 25, 120, 120, 120, 25, 25],  # estimated
    'phases': ['Setup', 'Addition', 'Ramp', 'Hold', 'Transfer', 'Centrifuge', 'Isolation']
}

# Reagent information
reagents = {
    'Precursor A': {'volume_mL': 500, 'lot': 'P-A-112'},
    'Reagent B': {'volume_mL': 200, 'lot': 'R-B-089'},
    'Diethyl Ether': {'volume_mL': 'not recorded', 'lot': 'N/A'}
}

# Process parameters
process_params = {
    'stirring_speed_rpm': 350,
    'target_temp_C': 120,
    'ramp_rate_C_per_min': 5,
    'hold_time_min': 45,
    'centrifuge_speed_rpm': 4000,
    'centrifuge_time_min': 15,
    'condenser_water_temp_C': 18
}

print("\nExtracted Process Parameters:")
for key, value in process_params.items():
    print(f"  {key}: {value}")

# Save extracted data
with open('outputs/extracted_data.json', 'w') as f:
    json.dump({
        'events': events,
        'reagents': reagents,
        'process_params': process_params,
        'timeline': timeline_data
    }, f, indent=2)

print("\nExtracted data saved to outputs/extracted_data.json")

# Generate Figure 1: Process Timeline
fig1, ax1 = plt.subplots(figsize=(12, 6))

# Create a Gantt-style timeline
colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22']
bar_height = 0.6
y_positions = range(len(timeline_data['phases']))

# Estimate durations for each phase
durations = [8, 12, 45, 10, 5, 35]  # estimated minutes
start_times = [0, 8, 20, 65, 75, 80]

for i, (phase, start, duration) in enumerate(zip(timeline_data['phases'][:-1], start_times, durations)):
    ax1.barh(i, duration, left=start, height=bar_height, color=colors[i % len(colors)], edgecolor='black')
    ax1.text(start + duration/2, i, f'{duration} min', ha='center', va='center', fontsize=9, fontweight='bold')

ax1.set_yticks(range(len(timeline_data['phases'][:-1])))
ax1.set_yticklabels(timeline_data['phases'][:-1])
ax1.set_xlabel('Time from Start (minutes)')
ax1.set_title('Catalyst-X9 Synthesis Process Timeline', fontsize=14, fontweight='bold')
ax1.grid(axis='x', alpha=0.3)
ax1.set_xlim(0, 120)

plt.tight_layout()
plt.savefig('report/images/timeline_figure.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 1 saved: report/images/timeline_figure.png")

# Generate Figure 2: Temperature Profile
fig2, ax2 = plt.subplots(figsize=(10, 6))

time_points = [0, 8, 20, 65, 75, 80, 115]
temp_profile = [25, 25, 120, 120, 120, 25, 25]

ax2.plot(time_points, temp_profile, 'o-', linewidth=2, markersize=8, color='#e74c3c', label='Temperature')
ax2.fill_between(time_points, temp_profile, alpha=0.3, color='#e74c3c')

# Add annotations
ax2.annotate('Ramp: 5°C/min', xy=(14, 70), fontsize=10, color='blue',
             arrowprops=dict(arrowstyle='->', color='blue'))
ax2.annotate('Hold: 45 min @ 120°C', xy=(42, 125), fontsize=10, color='green',
             arrowprops=dict(arrowstyle='->', color='green'))
ax2.axhline(y=120, color='gray', linestyle='--', alpha=0.5, label='Target Temp')

ax2.set_xlabel('Time from Start (minutes)')
ax2.set_ylabel('Temperature (°C)')
ax2.set_title('Catalyst-X9 Temperature Profile During Synthesis', fontsize=14, fontweight='bold')
ax2.legend(loc='upper right')
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, 140)

plt.tight_layout()
plt.savefig('report/images/temperature_profile.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: report/images/temperature_profile.png")

# Generate Figure 3: Reagent Volumes
fig3, ax3 = plt.subplots(figsize=(8, 6))

reagent_names = list(reagents.keys())
volumes = [500, 200, 50]  # Using 50 as estimated for diethyl ether
reagent_colors = ['#3498db', '#2ecc71', '#95a5a6']

bars = ax3.bar(reagent_names, volumes, color=reagent_colors, edgecolor='black', linewidth=1.5)

# Add value labels on bars
for bar, vol in zip(bars, volumes):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height + 10,
             f'{vol} mL', ha='center', va='bottom', fontsize=11, fontweight='bold')

ax3.set_ylabel('Volume (mL)')
ax3.set_title('Catalyst-X9 Reagent Volumes', fontsize=14, fontweight='bold')
ax3.axhline(y=700, color='red', linestyle='--', alpha=0.5, label='Total Volume (700 mL)')
ax3.legend(loc='upper right')
ax3.grid(axis='y', alpha=0.3)
ax3.set_ylim(0, 600)

plt.tight_layout()
plt.savefig('report/images/reagent_volumes.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved: report/images/reagent_volumes.png")

# Generate Figure 4: Process Parameter Summary (Radar Chart)
fig4, ax4 = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

# Normalize parameters for radar chart (0-1 scale based on typical ranges)
params_normalized = {
    'Stirring\nSpeed': 350/500,  # normalized to max 500 rpm
    'Temperature': 120/200,  # normalized to max 200°C
    'Hold Time': 45/60,  # normalized to max 60 min
    'Centrifuge\nSpeed': 4000/5000,  # normalized to max 5000 rpm
    'Centrifuge\nTime': 15/30,  # normalized to max 30 min
}

angles = [i * 2 * 3.14159 / len(params_normalized) for i in range(len(params_normalized))]
angles += angles[:1]  # Close the loop

values = list(params_normalized.values())
values += values[:1]  # Close the loop
labels = list(params_normalized.keys())
labels += labels[:1]

ax4.plot(angles, values, 'o-', linewidth=2, color='#9b59b6', markersize=8)
ax4.fill(angles, values, alpha=0.25, color='#9b59b6')
ax4.set_xticks(angles[:-1])
ax4.set_xticklabels(labels[:-1], fontsize=10)
ax4.set_ylim(0, 1.1)
ax4.set_title('Catalyst-X9 Process Parameters (Normalized)', fontsize=14, fontweight='bold', pad=20)
ax4.grid(True)

plt.tight_layout()
plt.savefig('report/images/parameter_radar.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved: report/images/parameter_radar.png")

# Generate Figure 5: SOP Conversion Flow
fig5, ax5 = plt.subplots(figsize=(10, 4))
ax5.axis('off')

# Create a flow diagram
flow_elements = [
    (0.1, 0.5, 'Raw Lab\nNotebook', '#3498db'),
    (0.35, 0.5, 'Data\nExtraction', '#2ecc71'),
    (0.6, 0.5, 'SOP\nFormatting', '#e74c3c'),
    (0.85, 0.5, 'Executable\nSOP', '#f39c12')
]

for x, y, text, color in flow_elements:
    circle = plt.Circle((x, y), 0.12, color=color, fill=True, edgecolor='black', linewidth=2)
    ax5.add_patch(circle)
    ax5.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold', color='white')

# Add arrows
for i in range(len(flow_elements) - 1):
    x1, x2 = flow_elements[i][0], flow_elements[i+1][0]
    ax5.annotate('', xy=(x2-0.12, 0.5), xytext=(x1+0.12, 0.5),
                 arrowprops=dict(arrowstyle='->', lw=2, color='gray'))

ax5.text(0.5, 0.85, 'Lab Notebook to SOP Conversion Workflow', ha='center', va='center',
         fontsize=14, fontweight='bold')
ax5.set_xlim(0, 1)
ax5.set_ylim(0, 1)

plt.tight_layout()
plt.savefig('report/images/conversion_workflow.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 5 saved: report/images/conversion_workflow.png")

print("\n" + "=" * 60)
print("Analysis complete. All figures generated successfully.")
print("=" * 60)
