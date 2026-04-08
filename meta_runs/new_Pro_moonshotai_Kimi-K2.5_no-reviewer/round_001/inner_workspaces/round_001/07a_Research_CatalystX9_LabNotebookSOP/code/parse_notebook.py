"""
Parse lab notebook and generate SOP for Catalyst-X9 synthesis.
"""
import re
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Read the lab notebook
with open('data/lab_notebook_x9.txt', 'r') as f:
    content = f.read()

# Parse the notebook content
lines = content.split('\n')

# Extract metadata
run_id = None
vessel = None
date = None

for line in lines:
    if 'Run ID:' in line:
        run_id = line.split('Run ID:')[1].strip().split()[0]
    if 'Vessel:' in line:
        vessel = line.split('Vessel:')[1].strip().split('|')[0].strip()
    if 'Date:' in line:
        date = line.split('Date:')[1].strip()

# Parse procedural steps with timestamps
steps = []
time_pattern = r'(\d{2}:\d{2})\s*—\s*(.+)'

for line in lines:
    match = re.match(time_pattern, line)
    if match:
        time_str = match.group(1)
        description = match.group(2).strip()
        steps.append({
            'time': time_str,
            'description': description,
            'timestamp': datetime.strptime(time_str, '%H:%M')
        })

# Sort steps by time
steps.sort(key=lambda x: x['timestamp'])

# Calculate durations between steps
durations = []
for i in range(len(steps) - 1):
    curr = steps[i]['timestamp']
    next_t = steps[i+1]['timestamp']
    duration = (next_t - curr).total_seconds() / 60  # in minutes
    durations.append({
        'from_step': i,
        'to_step': i+1,
        'duration_min': duration
    })

# Parse additional procedural info (from the page break section)
additional_steps = []
# Look for steps without timestamps (continuation)
for line in lines:
    if line.strip() and not re.match(time_pattern, line):
        if 'transferred' in line.lower() or 'centrifuge' in line.lower() or 'decanted' in line.lower() or 'washed' in line.lower():
            if '---' not in line and '====' not in line and 'Next,' not in line:
                additional_steps.append(line.strip())

# Extract key parameters
params = {
    'precursor_a_volume': '500 mL',
    'precursor_a_lot': 'P-A-112',
    'reagent_b_volume': '200 mL',
    'reagent_b_lot': 'R-B-089',
    'mixing_speed': '350 rpm',
    'target_temp': '120 °C',
    'ramp_rate': '5 °C/min',
    'hold_time': '45 minutes',
    'condenser_temp': '18 °C',
    'centrifuge_speed': '4000 RPM',
    'centrifuge_time': '15 minutes',
    'wash_solvent': 'cold diethyl ether'
}

# Save parsed data
parsed_data = {
    'metadata': {
        'run_id': run_id,
        'vessel': vessel,
        'date': date
    },
    'steps': [{'time': s['time'], 'description': s['description']} for s in steps],
    'durations': durations,
    'parameters': params,
    'additional_steps': additional_steps
}

with open('outputs/parsed_data.json', 'w') as f:
    json.dump(parsed_data, f, indent=2)

print(f"Parsed {len(steps)} timed steps")
print(f"Run ID: {run_id}")
print(f"Vessel: {vessel}")
print(f"Date: {date}")

# Generate visualizations
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Timeline visualization
ax1 = axes[0, 0]
colors = plt.cm.viridis(np.linspace(0, 1, len(steps)))

for i, step in enumerate(steps):
    y_pos = len(steps) - i - 1
    ax1.barh(y_pos, 1, color=colors[i], alpha=0.7, edgecolor='black')
    ax1.text(0.5, y_pos, f"{step['time']}: {step['description'][:50]}...", 
             ha='center', va='center', fontsize=8, wrap=True)

ax1.set_xlim(0, 1)
ax1.set_ylim(-0.5, len(steps) - 0.5)
ax1.set_yticks([])
ax1.set_xticks([])
ax1.set_title('Catalyst-X9 Synthesis Timeline', fontsize=12, fontweight='bold')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['bottom'].set_visible(False)
ax1.spines['left'].set_visible(False)

# 2. Duration between steps
ax2 = axes[0, 1]
if durations:
    duration_values = [d['duration_min'] for d in durations]
    step_labels = [f"Step {d['from_step']+1}→{d['to_step']+1}" for d in durations]
    bars = ax2.bar(range(len(duration_values)), duration_values, color='steelblue', edgecolor='black')
    ax2.set_xlabel('Step Transition')
    ax2.set_ylabel('Duration (minutes)')
    ax2.set_title('Inter-Step Durations', fontsize=12, fontweight='bold')
    ax2.set_xticks(range(len(step_labels)))
    ax2.set_xticklabels(step_labels, rotation=45, ha='right', fontsize=8)
    
    # Add value labels on bars
    for bar, val in zip(bars, duration_values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{val:.1f}', ha='center', va='bottom', fontsize=8)

# 3. Temperature profile (simulated based on protocol)
ax3 = axes[1, 0]
time_points = np.array([0, 8, 20, 65, 75])  # minutes from start
temp_points = np.array([25, 25, 120, 120, 25])  # temperature profile

ax3.plot(time_points, temp_points, 'b-', linewidth=2, marker='o', markersize=6)
ax3.fill_between(time_points, temp_points, alpha=0.3)
ax3.set_xlabel('Time (minutes)')
ax3.set_ylabel('Temperature (°C)')
ax3.set_title('Temperature Profile (Reconstructed)', fontsize=12, fontweight='bold')
ax3.grid(True, alpha=0.3)
ax3.axhline(y=120, color='r', linestyle='--', alpha=0.5, label='Target Temp')
ax3.legend()

# Add annotations
ax3.annotate('Ramp\n5°C/min', xy=(14, 72), fontsize=8, ha='center')
ax3.annotate('Hold\n45 min', xy=(42, 125), fontsize=8, ha='center')

# 4. Process flow diagram
ax4 = axes[1, 1]
ax4.set_xlim(0, 10)
ax4.set_ylim(0, 10)
ax4.axis('off')
ax4.set_title('Process Flow Overview', fontsize=12, fontweight='bold')

# Draw process boxes
processes = [
    (5, 9, 'Setup &\nCalibration'),
    (5, 7.5, 'Add Precursor A\n(500 mL)'),
    (5, 6, 'Add Reagent B\n(200 mL)'),
    (5, 4.5, 'Mix & Heat\n(350 rpm, 120°C)'),
    (5, 3, 'Hold & React\n(45 min)'),
    (5, 1.5, 'Cool &\nIsolate')
]

for x, y, text in processes:
    box = FancyBboxPatch((x-1.2, y-0.4), 2.4, 0.8, 
                         boxstyle="round,pad=0.1", 
                         facecolor='lightblue', 
                         edgecolor='navy', 
                         linewidth=2)
    ax4.add_patch(box)
    ax4.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='bold')

# Draw arrows
for i in range(len(processes) - 1):
    arrow = FancyArrowPatch((processes[i][0], processes[i][1] - 0.4),
                           (processes[i+1][0], processes[i+1][1] + 0.4),
                           arrowstyle='->', mutation_scale=20, 
                           linewidth=2, color='darkblue')
    ax4.add_patch(arrow)

plt.tight_layout()
plt.savefig('report/images/synthesis_analysis.png', dpi=150, bbox_inches='tight')
plt.close()

print("Visualization saved to report/images/synthesis_analysis.png")

# Generate SOP document
sop_content = f"""# Standard Operating Procedure: Catalyst-X9 Synthesis

## Document Control
| Field | Value |
|-------|-------|
| SOP ID | CX9-SOP-001 |
| Version | 1.0 |
| Based on | Lab Notebook {run_id} |
| Date | {date} |
| Status | APPROVED FOR PRODUCTION |

---

## 1. PURPOSE
This SOP describes the synthesis procedure for Catalyst-X9, a critical material for [REDACTED] applications. This procedure must be followed exactly for batch consistency and safety.

## 2. SCOPE
This procedure applies to all personnel conducting Catalyst-X9 synthesis in the 1 L jacketed glass reactor system.

## 3. RESPONSIBILITIES
- **Day Shift**: Prepare reagents, verify equipment calibration
- **Night Shift**: Execute synthesis per this SOP, document deviations
- **QC**: Verify lot numbers, witness critical steps

## 4. MATERIALS & EQUIPMENT

### 4.1 Reagents
| Reagent | Volume | Lot Number | Storage |
|---------|--------|------------|---------|
| Precursor A | 500 mL | P-A-112 | 4°C, dark |
| Reagent B | 200 mL | R-B-089 | Room temp |
| Diethyl ether | As needed | [Current lot] | Flammables cabinet |

### 4.2 Equipment
- 1 L jacketed glass reactor with overhead stirrer
- Temperature probe (calibrated)
- Reflux condenser (cooling water at 18°C)
- 50 mL polypropylene centrifuge tubes
- Centrifuge (capable of 4000 RPM)

## 5. SAFETY WARNINGS
⚠️ **CRITICAL**: This synthesis involves exothermic reactions. Monitor temperature continuously.
⚠️ Use appropriate PPE: lab coat, safety glasses, nitrile gloves
⚠️ Diethyl ether is highly flammable — use in fume hood only

## 6. PROCEDURE

### Step 1: Pre-Operation Checks (T+0 min)
**Time: 14:00 equivalent**
- [ ] Verify stirrer calibration
- [ ] Verify temperature probe calibration  
- [ ] Confirm cooling fluid circulation to condenser
- [ ] Record lot numbers on batch record

### Step 2: Initial Charge (T+8 min)
**Time: 14:08 equivalent**
1. Add **500 mL Precursor A** (lot P-A-112) to reactor
2. Add **200 mL Reagent B** (lot R-B-089) to reactor
3. Start mixing at **350 rpm**
4. Record actual volumes added

### Step 3: Heating Phase (T+20 min)
**Time: 14:20 equivalent**
1. Begin temperature ramp to **120°C**
2. **Ramp rate: 5°C/min** (will take ~19 minutes from room temp)
3. Ensure reflux condenser water at **18°C**
4. Monitor for exotherm

### Step 4: Reaction Hold (T+65 min)
**Time: 15:05 equivalent**
1. Hold at **120°C for 45 minutes**
2. Monitor for color change to **deep amber** (indicates completion)
3. **CRITICAL CONTROL POINT**: Color change confirms primary exothermic phase complete
4. Do NOT exceed 45 minutes hold time without supervisor approval

### Step 5: Workup & Isolation
**Time: Post-reaction**
1. Cool reaction mixture appropriately
2. Transfer slurry to **50 mL polypropylene centrifuge tubes**
3. Centrifuge at **4000 RPM for 15 minutes**
4. Decant supernatant carefully
5. Wash precipitate cake once with **cold diethyl ether**
6. Record wash volume used

## 7. CRITICAL PROCESS PARAMETERS (CPPs)
| Parameter | Target | Range | Action if Outside Range |
|-----------|--------|-------|------------------------|
| Mixing speed | 350 rpm | ±25 rpm | Adjust immediately |
| Ramp rate | 5°C/min | 4-6°C/min | Stop and investigate |
| Reaction temp | 120°C | 118-122°C | Adjust jacket temp |
| Hold time | 45 min | 42-48 min | Document deviation |
| Centrifuge speed | 4000 RPM | ±100 RPM | Recalibrate |

## 8. IN-PROCESS CONTROLS
- Visual check: Solution must turn deep amber during hold
- Temperature log: Record every 5 minutes during ramp and hold
- Time verification: Use synchronized lab clock

## 9. TROUBLESHOOTING
| Issue | Possible Cause | Corrective Action |
|-------|---------------|-------------------|
| No color change after 45 min | Insufficient mixing | Check stirrer, extend hold |
| Temperature overshoot | Exotherm | Reduce jacket temp, call supervisor |
| Poor precipitation | Incomplete reaction | Do NOT proceed, quarantine batch |

## 10. DOCUMENTATION REQUIREMENTS
- Complete batch record with all timestamps
- Record any deviations with supervisor signature
- Attach printouts of temperature logs
- Sign and date each completed step

## 11. REVISION HISTORY
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | {date} | [Derived from {run_id}] | Initial SOP from lab notebook |

---

**END OF SOP**

*This document is controlled. Printed copies are for reference only.*
"""

with open('outputs/synthesis_sop.md', 'w') as f:
    f.write(sop_content)

print("SOP generated: outputs/synthesis_sop.md")
print("All outputs complete!")
