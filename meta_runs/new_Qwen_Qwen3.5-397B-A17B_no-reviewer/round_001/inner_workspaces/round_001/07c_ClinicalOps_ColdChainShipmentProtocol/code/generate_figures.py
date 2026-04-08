import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from datetime import datetime, timedelta

# Set style
plt.style.use('default')
plt.rcParams['font.size'] = 10
plt.rcParams['axes.linewidth'] = 1.2

# Figure 1: Cold Chain Process Flow Diagram
fig1, ax1 = plt.subplots(figsize=(12, 6))
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 6)
ax1.axis('off')
ax1.set_title('Figure 1: Cold-Chain Shipment Process Flow', fontsize=14, fontweight='bold', pad=20)

# Define process boxes
boxes = [
    (0.5, 4.5, 'Pre-Shipment\nPreparation', '#4A90D9'),
    (2.5, 4.5, 'Packaging\nProcess', '#4A90D9'),
    (4.5, 4.5, 'Documentation\n& Carrier Handoff', '#4A90D9'),
    (6.5, 4.5, 'In-Transit\nMonitoring', '#F5A623'),
    (8.5, 4.5, 'Receipt &\nVerification', '#7ED321'),
]

for i, (x, y, label, color) in enumerate(boxes):
    rect = patches.FancyBboxPatch((x, y), 1.5, 0.8, boxstyle="round,pad=0.1,rounding_size=0.1",
                                   linewidth=2, edgecolor='#333333', facecolor=color)
    ax1.add_patch(rect)
    ax1.text(x + 0.75, y + 0.4, label, ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    
    # Add arrows between boxes
    if i < len(boxes) - 1:
        ax1.annotate('', xy=(x + 1.6, y + 0.4), xytext=(x + 2.4, y + 0.4),
                    arrowprops=dict(arrowstyle='->', lw=2, color='#333333'))

# Add temperature monitoring indicator
ax1.text(5, 2.5, 'Temperature Monitoring:\n2°C to 8°C (Refrigerated)\n-20°C or below (Frozen)',
         ha='center', va='center', fontsize=10, style='italic',
         bbox=dict(boxstyle='round', facecolor='#f0f0f0', edgecolor='#666666', linewidth=1.5))

# Add key checkpoints
checkpoints = [
    (1.25, 3.5, '✓ Logger Setup\n✓ Calibration Check', '#E8F4FD'),
    (3.25, 3.5, '✓ Coolant Conditioning\n✓ Package Integrity', '#E8F4FD'),
    (5.25, 3.5, '✓ Documentation\n✓ Tracking Initiated', '#E8F4FD'),
    (7.25, 3.5, '✓ Status Monitoring\n✓ Delay Management', '#FEF5E7'),
    (9.25, 3.5, '✓ Temperature Review\n✓ Excursion Check', '#F0F9E8'),
]

for x, y, label, color in checkpoints:
    rect = patches.FancyBboxPatch((x - 0.6, y - 0.4), 1.2, 0.6, boxstyle="round,pad=0.1",
                                   linewidth=1, edgecolor='#666666', facecolor=color)
    ax1.add_patch(rect)
    ax1.text(x, y, label, ha='center', va='center', fontsize=8)

plt.tight_layout()
plt.savefig('report/images/figure1_process_flow.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 2: Temperature Profile Simulation
fig2, ax2 = plt.subplots(figsize=(10, 6))

# Simulate temperature data over 72 hours
np.random.seed(42)
hours = np.arange(0, 73)
base_temp = 5  # Target 5°C for refrigerated products

# Simulate realistic temperature fluctuations
temp_data = base_temp + np.sin(hours * 2 * np.pi / 24) * 0.5 + np.random.normal(0, 0.3, len(hours))

# Add a small excursion event (hours 45-50)
temp_data[45:50] += 4.5

# Plot temperature profile
ax2.plot(hours, temp_data, linewidth=2, color='#2E86AB', label='Recorded Temperature')
ax2.axhline(y=2, color='#D00000', linestyle='--', linewidth=2, label='Lower Limit (2°C)')
ax2.axhline(y=8, color='#D00000', linestyle='--', linewidth=2, label='Upper Limit (8°C)')
ax2.axhline(y=5, color='#06A77D', linestyle=':', linewidth=1.5, label='Target Temperature (5°C)')

# Highlight excursion area
ax2.axvspan(45, 50, alpha=0.3, color='#FF6B6B', label='Temperature Excursion')

ax2.set_xlabel('Time (hours)', fontsize=11)
ax2.set_ylabel('Temperature (°C)', fontsize=11)
ax2.set_title('Figure 2: Simulated Temperature Profile During Transit', fontsize=14, fontweight='bold')
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.set_xlim(0, 72)
ax2.set_ylim(-2, 12)

plt.tight_layout()
plt.savefig('report/images/figure2_temperature_profile.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 3: SOP Component Breakdown
fig3, ax3 = plt.subplots(figsize=(10, 8))

# SOP sections and their relative importance/coverage
sections = [
    ('Purpose & Scope', 8),
    ('Responsibilities', 12),
    ('Equipment & Materials', 15),
    ('Procedure', 35),
    ('Documentation', 10),
    ('Excursion Management', 12),
    ('Record Keeping', 5),
    ('Training & QA', 3),
]

labels = [s[0] for s in sections]
sizes = [s[1] for s in sections]
colors = ['#4A90D9', '#50A5E1', '#56BAE9', '#5CCFF1', '#F5A623', '#F08A5D', '#B83B5E', '#6A2C70']

# Create horizontal bar chart
y_pos = np.arange(len(labels))
bars = ax3.barh(y_pos, sizes, color=colors, edgecolor='#333333', linewidth=1.5)

ax3.set_yticks(y_pos)
ax3.set_yticklabels(labels, fontsize=10)
ax3.set_xlabel('Relative Content Coverage (%)', fontsize=11)
ax3.set_title('Figure 3: Cold-Chain SOP Section Distribution', fontsize=14, fontweight='bold')
ax3.invert_yaxis()

# Add value labels on bars
for i, (bar, size) in enumerate(zip(bars, sizes)):
    ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
             f'{size}%', va='center', fontsize=10, fontweight='bold')

ax3.set_xlim(0, 40)
ax3.grid(axis='x', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig('report/images/figure3_sop_distribution.png', dpi=150, bbox_inches='tight')
plt.close()

# Figure 4: Temperature Excursion Response Workflow
fig4, ax4 = plt.subplots(figsize=(10, 8))
ax4.set_xlim(0, 10)
ax4.set_ylim(0, 10)
ax4.axis('off')
ax4.set_title('Figure 4: Temperature Excursion Response Workflow', fontsize=14, fontweight='bold', pad=20)

# Workflow boxes
workflow = [
    (3.5, 8.5, 'Excursion Detected', '#FF6B6B', 'diamond'),
    (3.5, 7, 'Document Details:\n- Duration\n- Magnitude\n- Product Affected', '#FEF5E7', 'rect'),
    (3.5, 5.5, 'Notify QA & Clinical Ops\n(Within 24 hours)', '#F5A623', 'rect'),
    (3.5, 4, 'Complete Excursion\nReport Form', '#4A90D9', 'rect'),
    (3.5, 2.5, 'QA Review with\nStability Data', '#7ED321', 'rect'),
    (3.5, 1, 'Disposition Decision', '#6A2C70', 'diamond'),
]

for i, (x, y, label, color, shape) in enumerate(workflow):
    if shape == 'diamond':
        polygon = patches.Polygon([[x, y+0.4], [x+0.8, y], [x, y-0.4], [x-0.8, y]],
                                  linewidth=2, edgecolor='#333333', facecolor=color)
    else:
        polygon = patches.FancyBboxPatch((x-0.8, y-0.35), 1.6, 0.7,
                                         boxstyle="round,pad=0.1,rounding_size=0.1",
                                         linewidth=2, edgecolor='#333333', facecolor=color)
    ax4.add_patch(polygon)
    
    # Text wrapping for multi-line labels
    lines = label.split('\n')
    for j, line in enumerate(lines):
        ax4.text(x, y + 0.15 - j*0.25, line, ha='center', va='top', 
                 fontsize=8, fontweight='bold', color='white' if color != '#FEF5E7' else 'black')
    
    # Add arrows between boxes
    if i < len(workflow) - 1:
        next_y = workflow[i+1][1]
        ax4.annotate('', xy=(x, next_y + 0.35), xytext=(x, y - 0.35),
                    arrowprops=dict(arrowstyle='->', lw=2, color='#333333'))

# Add disposition outcomes
outcomes = [
    (1, 1, 'Use', '#7ED321'),
    (3.5, 1, 'Quarantine', '#F5A623'),
    (6, 1, 'Destroy', '#D00000'),
]

for x, y, label, color in outcomes:
    rect = patches.FancyBboxPatch((x-0.6, y-0.25), 1.2, 0.5,
                                  boxstyle="round,pad=0.1",
                                  linewidth=1.5, edgecolor='#333333', facecolor=color)
    ax4.add_patch(rect)
    ax4.text(x, y, label, ha='center', va='center', fontsize=9, fontweight='bold', color='white')
    
    # Arrow from decision to outcomes
    if x == 3.5:
        ax4.annotate('', xy=(x, y + 0.25), xytext=(x, y + 0.65),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='#333333'))
    else:
        ax4.annotate('', xy=(x, y + 0.25), xytext=(3.5, y + 0.65),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='#333333'))

plt.tight_layout()
plt.savefig('report/images/figure4_excursion_workflow.png', dpi=150, bbox_inches='tight')
plt.close()

print('All figures generated successfully!')
