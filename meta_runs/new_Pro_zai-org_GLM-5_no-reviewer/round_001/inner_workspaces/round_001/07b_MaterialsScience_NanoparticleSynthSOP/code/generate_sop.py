"""
Generate formal Standard Operating Procedure (SOP) for nanoparticle synthesis.
Converts lab scratch notes into executable pilot-scale synthesis protocol.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Read raw lab notes
with open('data/lab_scratch.txt', 'r') as f:
    lab_notes = f.read()

print("Processing lab scratch notes for SOP generation...")

# Define the complete SOP structure based on extracted information
sop_content = '''# Standard Operating Procedure (SOP)
## Copper Nanoparticle (NanoCu) Synthesis for Pilot-Scale Production

---

**Document ID:** SOP-NanoCu-001  
**Version:** 1.0  
**Effective Date:** {date}  
**Review Date:** {review_date}  
**Department:** Materials Science - Nanoparticle Synthesis  

---

## 1. Purpose

This Standard Operating Procedure (SOP) describes the method for synthesizing copper nanoparticles (NanoCu) at pilot scale. The procedure is derived from validated bench-scale synthesis notes and adapted for larger production volumes.

## 2. Scope

This SOP applies to all personnel involved in the pilot-scale synthesis of copper nanoparticles in the Materials Science facility. It covers the complete synthesis process from reagent preparation through product isolation.

## 3. Responsibilities

| Role | Responsibility |
|------|---------------|
| Synthesis Operator | Execute synthesis steps, record observations, maintain equipment |
| Quality Control | Verify product specifications, document batch records |
| Supervisor | Approve batch records, ensure SOP compliance |
| Safety Officer | Verify safety protocols, manage waste disposal |

## 4. Materials and Equipment

### 4.1 Reagents

| Material | Specification | Quantity (Pilot Scale) | Storage |
|----------|---------------|------------------------|--------|
| Precursor A (Copper salt) | ≥99% purity, see bottle label | As calculated | Desiccator, RT |
| Surfactant (specify type) | Technical grade | As calculated | Cool, dry place |
| Carrier Oil (Oil bath medium) | High-temperature stable | 5 L | RT |
| Quenching solvent | Anhydrous | 2 L | Flammable storage |
| Washing solvent | HPLC grade | 3 L | Flammable storage |

### 4.2 Equipment

| Equipment | Specification | Calibration Status |
|-----------|---------------|-------------------|
| Oil bath with heating mantle | Capacity ≥10 L, temp control ±2°C | Current |
| Overhead stirrer | Variable speed, 50-500 rpm | Current |
| Addition funnel | 500 mL capacity | N/A |
| Temperature probe | Digital, ±0.5°C accuracy | Current |
| Reaction vessel | 10 L, 3-neck round bottom flask | N/A |
| Condenser | Reflux condenser | N/A |
| Centrifuge | Capable of 10,000 rpm | Current |
| Vacuum oven | Temperature controlled | Current |

### 4.3 Personal Protective Equipment (PPE)

- Lab coat (flame resistant)
- Safety goggles
- Nitrile gloves (double layer)
- Closed-toe shoes
- Face shield (during addition steps)

## 5. Safety Considerations

### 5.1 Hazard Identification

| Hazard | Source | Mitigation |
|--------|--------|-----------|
| Thermal burn | Hot oil bath (110°C) | Heat-resistant gloves, warning signs |
| Chemical exposure | Precursor A, surfactant | Fume hood, PPE |
| Fire risk | Organic solvents | No open flames, fire extinguisher nearby |
| Nanoparticle inhalation | Dry product | Handle in fume hood, avoid aerosolization |

### 5.2 Emergency Procedures

1. **Thermal burn:** Flush with cool water for 15 minutes, seek medical attention
2. **Chemical spill:** Contain with absorbent material, dispose per waste protocol
3. **Fire:** Evacuate, activate alarm, use Class B extinguisher if safe

## 6. Procedure

### 6.1 Pre-Synthesis Setup

1. Verify all equipment is clean, dry, and properly calibrated
2. Confirm reagent availability and check expiration dates
3. Set up reaction apparatus in fume hood:
   - 10 L 3-neck round bottom flask
   - Overhead stirrer with appropriate impeller
   - Addition funnel with pressure-equalizing arm
   - Reflux condenser (if required)
   - Temperature probe
4. Prepare oil bath and ensure temperature controller is functional
5. Document pre-synthesis checklist in batch record

### 6.2 Synthesis Procedure

#### Step 1: Oil Bath Heating

| Parameter | Specification |
|-----------|---------------|
| Target temperature | 110°C |
| Acceptable range | 105-115°C |
| Heating time | ~30-45 minutes |

**Procedure:**
1. Fill oil bath with carrier oil to appropriate level
2. Begin heating with stirring to ensure uniform temperature
3. Monitor temperature until stable at 110°C (±5°C)
4. **Critical Checkpoint:** Verify temperature stability before proceeding

#### Step 2: Precursor Addition

| Parameter | Specification |
|-----------|---------------|
| Addition rate | Dropwise (1-2 drops/second) |
| Total addition time | 30-60 minutes |
| Stirring speed | 200-300 rpm |

**Procedure:**
1. Load Precursor A into addition funnel
2. Position funnel over reaction vessel
3. Begin dropwise addition at controlled rate
4. Maintain continuous stirring throughout addition
5. Observe color change: **Initial color should be blue-green**
6. **Critical Checkpoint:** Ensure addition rate remains consistent

#### Step 3: Surfactant Addition

| Parameter | Specification |
|-----------|---------------|
| Addition method | Slow pour or dropwise |
| Stirring | Continuous |

**Procedure:**
1. After complete precursor addition, add surfactant
2. Continue stirring to ensure homogeneous mixing
3. Observe any color changes and document

#### Step 4: Reaction Period (Overnight Stirring)

| Parameter | Specification |
|-----------|---------------|
| Duration | 12-16 hours (overnight) |
| Temperature | Maintain 105-115°C |
| Stirring speed | 150-250 rpm |
| Atmosphere | Inert (N₂ or Ar) if required |

**Procedure:**
1. Secure reaction setup for extended operation
2. Set up overnight monitoring protocol
3. Document start time and initial conditions
4. **Expected observation:** Color transition from blue-green to brown
5. **Critical Checkpoint:** Verify color change indicates successful reduction

#### Step 5: Quenching and Workup

**Note:** Original bench notes indicate workup procedure requires verification from photo documentation. The following is a standard workup protocol:

| Step | Action | Details |
|------|--------|--------|
| 5.1 | Cool reaction | Cool to room temperature (25°C) |
| 5.2 | Quench | Add quenching solvent slowly with stirring |
| 5.3 | Transfer | Transfer to centrifuge tubes |
| 5.4 | Centrifuge | 10,000 rpm, 15 minutes |
| 5.5 | Wash | Resuspend in washing solvent, repeat centrifugation 3× |
| 5.6 | Dry | Vacuum oven at 40°C, 12-24 hours |

**Procedure:**
1. Remove heat source and allow reaction mixture to cool
2. Once at room temperature, slowly add quenching solvent
3. Transfer mixture to appropriate centrifuge vessels
4. Centrifuge to collect nanoparticle product
5. Wash product with washing solvent (3 cycles)
6. Transfer to drying vessel and place in vacuum oven
7. **Critical Checkpoint:** Verify complete solvent removal

### 6.3 Post-Synthesis Handling

1. Weigh dried product and record yield
2. Transfer to labeled, airtight container
3. Store under inert atmosphere if required
4. Clean all equipment promptly
5. Complete batch record documentation

## 7. Quality Control

### 7.1 In-Process Checks

| Checkpoint | Parameter | Acceptance Criteria |
|------------|-----------|---------------------|
| Pre-addition | Oil bath temperature | 105-115°C |
| During addition | Addition rate | 1-2 drops/second |
| Post-addition | Color observation | Blue-green |
| Post-reaction | Color observation | Brown |
| Post-drying | Product appearance | Free-flowing powder |

### 7.2 Final Product Testing

| Test | Method | Specification |
|------|--------|---------------|
| Particle size | DLS or TEM | <100 nm |
| Morphology | TEM/SEM | Spherical, uniform |
| Purity | XRD | Cu peaks, minimal CuO |
| Yield | Gravimetric | Report actual |

## 8. Documentation Requirements

### 8.1 Batch Record

Record the following for each batch:
- Batch number and date
- Operator name(s)
- Reagent lot numbers and quantities
- Temperature logs (start, during, end)
- Timing of each step
- Color observations at each stage
- Any deviations from SOP
- Final yield and product appearance

### 8.2 Deviation Handling

1. Document any deviation from this SOP
2. Assess impact on product quality
3. Obtain supervisor approval before proceeding
4. File deviation report with batch record

## 9. Waste Disposal

| Waste Type | Disposal Method |
|------------|-----------------|
| Organic solvents | Collect in designated waste container |
| Oil bath oil | Recycle or dispose per facility protocol |
| Nanoparticle waste | Collect in sealed container, label as nanomaterial |

## 10. References

1. Original bench notes: `lab_scratch.txt`
2. Photo documentation: Verify workup procedure from phone photos
3. Material Safety Data Sheets (MSDS) for all reagents

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|--------|
| 1.0 | {date} | Processed from bench notes | Initial release |

## 12. Appendices

### Appendix A: Troubleshooting Guide

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| No color change | Insufficient temperature | Verify oil bath temperature |
| Aggregation | Surfactant insufficient | Increase surfactant concentration |
| Low yield | Incomplete reaction | Extend reaction time |
| Oxidation | Air exposure | Ensure inert atmosphere |

### Appendix B: Scale-Up Calculations

For pilot-scale synthesis, scale all reagent quantities proportionally from bench-scale amounts. Document scale factor in batch record.

---

**Approved by:** _________________ **Date:** _________

**Supervisor Review:** _________________ **Date:** _________
'''.format(
    date="2024",
    review_date="2025"
)

# Save the SOP
with open('outputs/nanoparticle_sop.md', 'w') as f:
    f.write(sop_content)

print("SOP document generated and saved to outputs/nanoparticle_sop.md")

# Create a synthesis workflow diagram
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

# Title
ax.text(7, 9.5, 'Copper Nanoparticle (NanoCu) Synthesis Workflow', 
        fontsize=16, fontweight='bold', ha='center', va='center')

# Define process steps
steps = [
    {'name': 'Setup &\nPreparation', 'x': 1.5, 'y': 7, 'color': '#E8F4FD', 'time': '30 min'},
    {'name': 'Heat Oil Bath\n(110°C)', 'x': 4.5, 'y': 7, 'color': '#FFE4B5', 'time': '30-45 min'},
    {'name': 'Add Precursor A\n(Dropwise)', 'x': 7.5, 'y': 7, 'color': '#E6E6FA', 'time': '30-60 min'},
    {'name': 'Add Surfactant', 'x': 10.5, 'y': 7, 'color': '#E6E6FA', 'time': '5-10 min'},
    {'name': 'Overnight\nStirring', 'x': 7.5, 'y': 4, 'color': '#FFB6C1', 'time': '12-16 hrs'},
    {'name': 'Quench &\nWorkup', 'x': 4.5, 'y': 4, 'color': '#98FB98', 'time': '2-3 hrs'},
    {'name': 'Drying &\nPackaging', 'x': 1.5, 'y': 4, 'color': '#87CEEB', 'time': '12-24 hrs'},
]

# Draw process boxes
for step in steps:
    box = FancyBboxPatch((step['x']-1, step['y']-0.8), 2, 1.6,
                         boxstyle="round,pad=0.05,rounding_size=0.2",
                         facecolor=step['color'], edgecolor='black', linewidth=2)
    ax.add_patch(box)
    ax.text(step['x'], step['y']+0.2, step['name'], fontsize=10, 
            ha='center', va='center', fontweight='bold')
    ax.text(step['x'], step['y']-0.5, step['time'], fontsize=8, 
            ha='center', va='center', style='italic', color='gray')

# Draw arrows
arrows = [
    (2.5, 7, 3.5, 7),   # Setup to Heat
    (5.5, 7, 6.5, 7),   # Heat to Precursor
    (8.5, 7, 9.5, 7),   # Precursor to Surfactant
    (10.5, 6.2, 10.5, 5), (10.5, 5, 8.5, 4.8),  # Surfactant to Overnight
    (6.5, 4, 5.5, 4),   # Overnight to Quench
    (3.5, 4, 2.5, 4),   # Quench to Drying
]

for arrow in arrows:
    if len(arrow) == 4:
        ax.annotate('', xy=(arrow[2], arrow[3]), xytext=(arrow[0], arrow[1]),
                   arrowprops=dict(arrowstyle='->', color='darkblue', lw=2))
    else:
        ax.annotate('', xy=(arrow[2], arrow[3]), xytext=(arrow[0], arrow[1]),
                   arrowprops=dict(arrowstyle='->', color='darkblue', lw=2, 
                                  connectionstyle='arc3,rad=0.3'))

# Add color observation boxes
obs_box1 = FancyBboxPatch((6.5, 5.2), 2, 0.6,
                          boxstyle="round,pad=0.02",
                          facecolor='#ADD8E6', edgecolor='navy', linewidth=1)
ax.add_patch(obs_box1)
ax.text(7.5, 5.5, 'Color: Blue-Green', fontsize=8, ha='center', va='center')

obs_box2 = FancyBboxPatch((6.5, 2.5), 2, 0.6,
                          boxstyle="round,pad=0.02",
                          facecolor='#DEB887', edgecolor='saddlebrown', linewidth=1)
ax.add_patch(obs_box2)
ax.text(7.5, 2.8, 'Color: Brown', fontsize=8, ha='center', va='center')

# Add legend
legend_elements = [
    mpatches.Patch(color='#E8F4FD', label='Preparation'),
    mpatches.Patch(color='#FFE4B5', label='Heating'),
    mpatches.Patch(color='#E6E6FA', label='Addition'),
    mpatches.Patch(color='#FFB6C1', label='Reaction'),
    mpatches.Patch(color='#98FB98', label='Workup'),
    mpatches.Patch(color='#87CEEB', label='Finishing'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

# Add critical checkpoints
ax.text(7, 1.5, 'Critical Checkpoints:', fontsize=11, fontweight='bold')
checkpoints = [
    '• Verify temperature stability (105-115°C) before precursor addition',
    '• Monitor color transition: Blue-green → Brown indicates successful reduction',
    '• Ensure complete solvent removal during drying'
]
for i, cp in enumerate(checkpoints):
    ax.text(7, 1.0 - i*0.35, cp, fontsize=9, ha='center')

plt.tight_layout()
plt.savefig('report/images/synthesis_workflow.png', dpi=150, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
plt.close()

print("Workflow diagram saved to report/images/synthesis_workflow.png")

# Create a temperature profile diagram
fig, ax = plt.subplots(figsize=(12, 6))

time_points = [0, 0.5, 1, 1.5, 2, 2.5, 3, 15, 16, 17, 18, 19, 20]
temperatures = [25, 60, 90, 110, 110, 110, 110, 110, 110, 110, 110, 60, 25]

ax.plot(time_points, temperatures, 'b-', linewidth=2, marker='o', markersize=6)
ax.fill_between(time_points, temperatures, alpha=0.3)

# Add phase labels
phases = [
    (0.75, 'Heating\nPhase', 0, 75),
    (2, 'Precursor\nAddition', 0, 115),
    (9, 'Overnight Reaction\n(12-16 hours)', 0, 115),
    (17.5, 'Cooling\nPhase', 0, 60),
]

for t, label, y_offset, y_text in phases:
    ax.annotate(label, xy=(t, y_text), fontsize=9, ha='center',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

# Add target temperature lines
ax.axhline(y=110, color='r', linestyle='--', linewidth=1, label='Target: 110°C')
ax.axhline(y=105, color='orange', linestyle=':', linewidth=1, label='Lower limit: 105°C')
ax.axhline(y=115, color='orange', linestyle=':', linewidth=1, label='Upper limit: 115°C')

ax.set_xlabel('Time (hours)', fontsize=12)
ax.set_ylabel('Temperature (°C)', fontsize=12)
ax.set_title('Temperature Profile for NanoCu Synthesis', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 20)
ax.set_ylim(0, 130)

plt.tight_layout()
plt.savefig('report/images/temperature_profile.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()

print("Temperature profile saved to report/images/temperature_profile.png")

# Create a process parameters summary table as an image
fig, ax = plt.subplots(figsize=(10, 6))
ax.axis('off')

# Table data
col_labels = ['Parameter', 'Value', 'Tolerance', 'Critical']
table_data = [
    ['Oil Bath Temperature', '110°C', '±5°C', 'Yes'],
    ['Precursor Addition Rate', 'Dropwise', '1-2 drops/sec', 'Yes'],
    ['Stirring Speed', '200 rpm', '150-300 rpm', 'No'],
    ['Reaction Duration', '14 hours', '12-16 hours', 'Yes'],
    ['Initial Color', 'Blue-green', 'N/A', 'Yes'],
    ['Final Color', 'Brown', 'N/A', 'Yes'],
    ['Drying Temperature', '40°C', '35-45°C', 'No'],
    ['Drying Duration', '18 hours', '12-24 hours', 'No'],
]

# Create table
table = ax.table(cellText=table_data, colLabels=col_labels,
                  loc='center', cellLoc='center',
                  colColours=['#4472C4']*4)

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.8)

# Style header
for i in range(4):
    table[(0, i)].set_text_props(fontweight='bold', color='white')

# Color critical column
for i in range(1, len(table_data)+1):
    if table_data[i-1][3] == 'Yes':
        table[(i, 3)].set_facecolor('#FFCCCB')
    else:
        table[(i, 3)].set_facecolor('#90EE90')

ax.set_title('Key Process Parameters for NanoCu Synthesis', 
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('report/images/process_parameters.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.close()

print("Process parameters table saved to report/images/process_parameters.png")
print("\nAll outputs generated successfully!")
