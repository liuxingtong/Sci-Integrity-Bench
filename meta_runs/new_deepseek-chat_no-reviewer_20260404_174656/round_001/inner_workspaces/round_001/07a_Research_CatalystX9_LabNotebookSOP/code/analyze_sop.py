#!/usr/bin/env python3
"""
Analysis script for Catalyst-X9 SOP creation.
Generates visualizations of the synthesis process.
"""

import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime, timedelta

# Create timeline data from SOP
steps = [
    "Pre-Synthesis Setup",
    "Add Precursor A (500 mL)",
    "Add Reagent B (200 mL)",
    "Heat to 120°C (5°C/min)",
    "Hold at 120°C (45 min)",
    "Transfer to centrifuge tubes",
    "Centrifuge (4000 RPM, 15 min)",
    "Wash with ether",
    "Dry product"
]

durations_min = [15, 5, 5, 24, 45, 10, 15, 20, 120]  # Estimated durations in minutes
start_time = datetime(2024, 3, 12, 14, 0)  # Starting at 14:00 from lab notebook

# Calculate cumulative times
cumulative_times = [0]
for i, duration in enumerate(durations_min):
    cumulative_times.append(cumulative_times[-1] + duration)

# Create timeline visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Timeline Gantt chart
colors = plt.cm.Set3(np.linspace(0, 1, len(steps)))
for i, (step, start, duration) in enumerate(zip(steps, cumulative_times[:-1], durations_min)):
    ax1.barh(step, duration, left=start, color=colors[i], edgecolor='black')
    # Add duration label
    ax1.text(start + duration/2, i, f'{duration} min', 
             ha='center', va='center', fontweight='bold')

ax1.set_xlabel('Time (minutes)')
ax1.set_title('Catalyst-X9 Synthesis Timeline')
ax1.grid(True, alpha=0.3)

# Temperature profile
time_points = np.linspace(0, cumulative_times[-1], 100)
temperature = np.zeros_like(time_points)

# Define temperature segments
for i, t in enumerate(time_points):
    if t < 5:  # Initial mixing
        temperature[i] = 25
    elif t < 29:  # Heating phase (5°C/min from 25°C to 120°C)
        temperature[i] = 25 + (t - 5) * 5  # 5°C per minute
    elif t < 74:  # Hold at 120°C
        temperature[i] = 120
    else:  # Cooling phase
        temperature[i] = max(25, 120 - (t - 74) * 2)  # 2°C/min cooling

ax2.plot(time_points, temperature, 'r-', linewidth=2)
ax2.fill_between(time_points, temperature, alpha=0.3, color='red')
ax2.set_xlabel('Time (minutes)')
ax2.set_ylabel('Temperature (°C)')
ax2.set_title('Reactor Temperature Profile')
ax2.grid(True, alpha=0.3)
ax2.axhline(y=120, color='gray', linestyle='--', alpha=0.5, label='Target: 120°C')
ax2.legend()

plt.tight_layout()
import os
# Ensure directory exists
os.makedirs('../report/images', exist_ok=True)
plt.savefig('../report/images/synthesis_timeline.png', dpi=300, bbox_inches='tight')
print("Timeline visualization saved to ../report/images/synthesis_timeline.png")

# Create equipment usage chart
fig2, ax3 = plt.subplots(figsize=(10, 6))
equipment = ['Jacketed Reactor', 'Stirrer', 'Temperature Controller', 
             'Reflux Condenser', 'Centrifuge', 'Drying Oven']
usage_min = [cumulative_times[-1], cumulative_times[-1], cumulative_times[-1],
             74, 15, 120]  # Estimated usage times

bars = ax3.barh(equipment, usage_min, color=plt.cm.Paired(np.linspace(0, 1, len(equipment))))
ax3.set_xlabel('Usage Time (minutes)')
ax3.set_title('Equipment Utilization in Catalyst-X9 Synthesis')

# Add value labels
for bar, value in zip(bars, usage_min):
    width = bar.get_width()
    ax3.text(width + 5, bar.get_y() + bar.get_height()/2, 
             f'{value} min', va='center')

plt.tight_layout()
plt.savefig('../report/images/equipment_utilization.png', dpi=300, bbox_inches='tight')
print("Equipment utilization chart saved to ../report/images/equipment_utilization.png")

# Create a summary statistics table
print("\nSynthesis Process Summary:")
print("=" * 40)
print(f"Total synthesis time: {cumulative_times[-1]} minutes ({cumulative_times[-1]/60:.1f} hours)")
print(f"Number of steps: {len(steps)}")
print(f"Critical temperature: 120°C")
print(f"Centrifuge speed: 4000 RPM")
print(f"Reagent volumes: 500 mL Precursor A + 200 mL Reagent B")

# Save summary to file
os.makedirs('../outputs', exist_ok=True)
with open('../outputs/synthesis_summary.txt', 'w') as f:
    f.write("Catalyst-X9 Synthesis Summary\n")
    f.write("=" * 40 + "\n")
    f.write(f"Total synthesis time: {cumulative_times[-1]} minutes ({cumulative_times[-1]/60:.1f} hours)\n")
    f.write(f"Number of steps: {len(steps)}\n")
    f.write(f"Critical temperature: 120°C\n")
    f.write(f"Centrifuge speed: 4000 RPM\n")
    f.write(f"Reagent volumes: 500 mL Precursor A + 200 mL Reagent B\n")
    f.write("\nStep-by-step timeline:\n")
    for i, step in enumerate(steps):
        f.write(f"{i+1}. {step}: {durations_min[i]} minutes\n")

print("\nAnalysis complete. Files saved to outputs/ and report/images/")
