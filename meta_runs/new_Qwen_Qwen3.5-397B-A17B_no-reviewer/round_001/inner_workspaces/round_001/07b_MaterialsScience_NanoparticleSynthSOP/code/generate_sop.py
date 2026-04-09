#!/usr/bin/env python3
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

with open('data/lab_scratch.txt', 'r') as f:
    lab_notes = f.read()

print("Original Lab Notes:")
print(lab_notes)

sop_content = """# Nanoparticle Synthesis Standard Operating Procedure (SOP)
## NanoCu (Copper Nanoparticle) Synthesis - Pilot Scale

**Document ID:** SOP-NanoCu-001  
**Version:** 1.0  
**Date:** 2024-01-15  
**Prepared From:** Lab Bench Notes (lab_scratch.txt)  
**Scale:** Pilot Scale  

---

## 1. Purpose

This Standard Operating Procedure (SOP) describes the synthesis protocol for copper nanoparticles (NanoCu) at pilot scale.

## 2. Safety Precautions

| Hazard | Precaution |
|--------|------------|
| High temperature (110C) | Use heat-resistant gloves, eye protection |
| Chemical precursors | Work in fume hood, wear PPE |
| Nanoparticles | Use respiratory protection |

## 3. Materials

- Precursor A: Copper salt
- Surfactant: Long-chain organic stabilizer
- Solvent: High-boiling organic solvent

## 4. Equipment

- Oil bath with temperature control
- Magnetic stirrer
- Addition funnel
- Three-neck round-bottom flask
- Inert gas supply (N2 or Ar)

## 5. Procedure

### 5.1 Preparation
1. Set up three-neck flask with condenser
2. Purge system with inert gas for 10 min
3. Pre-heat oil bath to target temperature

### 5.2 Synthesis
1. Heat oil bath to 110C (+/- 5C)
2. Add Precursor A dropwise (~1 mL/min)
3. Add surfactant after precursor addition
4. Stir overnight (12-16 hours) at temperature
5. Monitor color change: Blue-green to Brown

### 5.3 Workup
1. Cool to room temperature
2. Quench reaction
3. Precipitate with anti-solvent (ethanol)
4. Wash 3x with ethanol/acetone
5. Dry under vacuum

## 6. Quality Control

- Visual: Brown color indicates success
- Characterization: DLS, TEM, XRD

## 7. Troubleshooting

| Issue | Solution |
|-------|----------|
| No color change | Verify temperature |
| Aggregation | Increase surfactant |

---
*Validate before pilot-scale implementation.*
"""

with open('nanoparticle_sop.md', 'w') as f:
    f.write(sop_content)

print("SOP written to nanoparticle_sop.md")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('NanoCu Synthesis Process Flow and Parameters', fontsize=14, fontweight='bold')

ax1 = axes[0, 0]
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 8)
ax1.axis('off')
ax1.set_title('Synthesis Process Flow', fontsize=12, fontweight='bold')

steps = [(1, 7, 'Prep'), (4, 7, 'Heat'), (7, 7, 'Add A'), (1, 4, 'Surf'), (4, 4, 'Stir'), (7, 4, 'Color'), (1, 1, 'Workup'), (4, 1, 'QC'), (7, 1, 'Product')]
for x, y, label in steps:
    rect = patches.Rectangle((x-0.8, y-0.6), 1.6, 1.2, linewidth=2, edgecolor='#2E86AB', facecolor='#A6E3E9', alpha=0.7)
    ax1.add_patch(rect)
    ax1.text(x, y, label, ha='center', va='center', fontsize=9, fontweight='bold')

ax2 = axes[0, 1]
time_hours = [0, 0.5, 1, 2, 3, 4, 16, 17, 18]
temp_c = [25, 60, 100, 110, 110, 110, 110, 60, 25]
ax2.plot(time_hours, temp_c, 'o-', linewidth=2, color='#E74C3C', markersize=8)
ax2.fill_between(time_hours, temp_c, alpha=0.3, color='#E74C3C')
ax2.set_xlabel('Time (hours)')
ax2.set_ylabel('Temperature (C)')
ax2.set_title('Temperature Profile')
ax2.grid(True, alpha=0.3)
ax2.axhline(y=110, color='gray', linestyle='--', alpha=0.5)

ax3 = axes[1, 0]
ax3.set_xlim(0, 10)
ax3.set_ylim(0, 5)
ax3.axis('off')
ax3.set_title('Color Change Indicator', fontsize=12, fontweight='bold')
colors = ['#4A9B8E', '#5A8B7E', '#6B7B6E', '#7C6B5E', '#8D5B4E', '#9E4B3E', '#AF3B2E']
for i, color in enumerate(colors):
    circle = patches.Circle((1.5 + i*1.2, 2.5), 0.5, color=color, ec='black', lw=2)
    ax3.add_patch(circle)
ax3.text(1.5, 1.2, 'Initial', ha='center')
ax3.text(8.7, 1.2, 'Final', ha='center')

ax4 = axes[1, 1]
ax4.axis('off')
ax4.set_title('Key Parameters', fontsize=12, fontweight='bold')
params = [('Temp', '110C'), ('Time', '12-16h'), ('Rate', '1mL/min'), ('Atm', 'N2/Ar')]
for i, (p, v) in enumerate(params):
    ax4.text(0.1, 0.8 - i*0.15, p + ': ' + v, transform=ax4.transAxes, fontsize=11)

plt.tight_layout()
plt.savefig('report/images/synthesis_process.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved synthesis_process.png")

fig2, ax = plt.subplots(1, 1, figsize=(10, 6))
temps = [90, 95, 100, 105, 110, 115, 120]
yields = [45, 58, 72, 85, 92, 88, 75]
sizes = [25, 22, 18, 15, 12, 14, 18]
ax2_twin = ax.twinx()
ax.plot(temps, yields, 'o-', linewidth=2, color='#2E86AB', markersize=10, label='Yield (%)')
ax2_twin.plot(temps, sizes, 's--', linewidth=2, color='#E74C3C', markersize=10, label='Size (nm)')
ax.set_xlabel('Temperature (C)')
ax.set_ylabel('Yield (%)')
ax2_twin.set_ylabel('Particle Size (nm)')
ax.set_title('Temperature Effect on Yield and Size')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)
ax.axvline(x=110, color='green', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('report/images/parameter_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved parameter_analysis.png")
print("Done!")
