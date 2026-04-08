import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

# Title
ax.text(7, 9.5, 'Cold-Chain Shipment Workflow', fontsize=16, fontweight='bold', 
        ha='center', va='center')

# Define workflow steps
steps = [
    {'name': 'Pre-Shipment\nPreparation', 'x': 2, 'y': 7, 'color': '#4CAF50'},
    {'name': 'Temperature Logger\nSetup', 'x': 5, 'y': 7, 'color': '#2196F3'},
    {'name': 'Packaging\nPreparation', 'x': 8, 'y': 7, 'color': '#2196F3'},
    {'name': 'Product\nPacking', 'x': 11, 'y': 7, 'color': '#FF9800'},
    {'name': 'Shipment\nDocumentation', 'x': 2, 'y': 4.5, 'color': '#FF9800'},
    {'name': 'Transportation\n& Monitoring', 'x': 5, 'y': 4.5, 'color': '#9C27B0'},
    {'name': 'Receipt &\nVerification', 'x': 8, 'y': 4.5, 'color': '#F44336'},
    {'name': 'Temperature\nData Review', 'x': 11, 'y': 4.5, 'color': '#F44336'},
]

# Draw boxes
for step in steps:
    box = FancyBboxPatch((step['x']-1, step['y']-0.6), 2, 1.2,
                         boxstyle="round,pad=0.05,rounding_size=0.2",
                         facecolor=step['color'], edgecolor='black', linewidth=2)
    ax.add_patch(box)
    ax.text(step['x'], step['y'], step['name'], fontsize=9, fontweight='bold',
            ha='center', va='center', color='white')

# Draw arrows
arrow_style = dict(arrowstyle='->', color='#333333', lw=2, 
                   connectionstyle='arc3,rad=0')

# Horizontal arrows top row
for i in range(3):
    ax.annotate('', xy=(steps[i+1]['x']-1, steps[i+1]['y']), 
                xytext=(steps[i]['x']+1, steps[i]['y']),
                arrowprops=arrow_style)

# Vertical arrow from step 4 to step 5
ax.annotate('', xy=(steps[4]['x'], steps[4]['y']+0.6), 
            xytext=(steps[3]['x'], steps[3]['y']-0.6),
            arrowprops=dict(arrowstyle='->', color='#333333', lw=2,
                          connectionstyle='arc3,rad=0.3'))

# Horizontal arrows bottom row
for i in range(4, 7):
    ax.annotate('', xy=(steps[i+1]['x']-1, steps[i+1]['y']), 
                xytext=(steps[i]['x']+1, steps[i]['y']),
                arrowprops=arrow_style)

# Add legend
legend_items = [
    ('Preparation Phase', '#4CAF50'),
    ('Setup Phase', '#2196F3'),
    ('Execution Phase', '#FF9800'),
    ('Transit Phase', '#9C27B0'),
    ('Verification Phase', '#F44336'),
]

for i, (label, color) in enumerate(legend_items):
    rect = mpatches.Rectangle((0.5, 2.5 - i*0.5), 0.3, 0.3, facecolor=color, edgecolor='black')
    ax.add_patch(rect)
    ax.text(1, 2.65 - i*0.5, label, fontsize=10, va='center')

# Add key notes
notes = [
    'Key Requirements from Email:',
    '• Temperature loggers in trucks',
    '• Calibration details with vendor',
    '• Secondary packaging coordination',
    '• Auditable cold-chain procedures'
]

for i, note in enumerate(notes):
    weight = 'bold' if i == 0 else 'normal'
    ax.text(7, 2.5 - i*0.4, note, fontsize=10, va='center', fontweight=weight)

# Add SOP sections reference
sop_text = 'SOP Sections: 5.1 Pre-Shipment → 5.2 Packing → 5.3 Documentation → 5.4 Transport → 5.5 Receipt'
ax.text(7, 0.5, sop_text, fontsize=9, ha='center', va='center', 
        style='italic', bbox=dict(boxstyle='round', facecolor='#E0E0E0', edgecolor='gray'))

plt.tight_layout()
plt.savefig('report/images/cold_chain_workflow.png', dpi=150, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
plt.close()

print('Workflow diagram saved successfully!')
