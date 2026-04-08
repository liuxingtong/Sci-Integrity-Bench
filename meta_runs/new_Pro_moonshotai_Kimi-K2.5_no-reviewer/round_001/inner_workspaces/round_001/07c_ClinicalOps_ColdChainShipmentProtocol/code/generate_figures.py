"""
Generate figures for Cold-Chain Shipment SOP Research Report
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

# Create output directory for images
os.makedirs('report/images', exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10

def create_workflow_diagram():
    """Create cold-chain shipment workflow diagram"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define colors
    color_prep = '#3498db'
    color_pack = '#2ecc71'
    color_ship = '#e74c3c'
    color_receive = '#9b59b6'
    
    # Title
    ax.text(7, 9.5, 'Cold-Chain Shipment Workflow', fontsize=16, fontweight='bold', 
            ha='center', va='center')
    
    # Phase 1: Pre-Shipment Preparation
    y_pos = 7.5
    ax.add_patch(FancyBboxPatch((0.5, y_pos-0.4), 3, 0.8, boxstyle="round,pad=0.1", 
                                 facecolor=color_prep, edgecolor='black', linewidth=2, alpha=0.8))
    ax.text(2, y_pos, 'Pre-Shipment\nPreparation', ha='center', va='center', 
            fontsize=10, fontweight='bold', color='white')
    
    # Sub-steps
    steps_prep = ['Verify specimen\nintegrity', 'Check temperature\nrequirements', 
                  'Program\nlogger', 'Complete\ndocumentation']
    for i, step in enumerate(steps_prep):
        x = 1 + i * 0.7
        ax.add_patch(FancyBboxPatch((x-0.3, y_pos-1.5), 0.6, 0.6, boxstyle="round,pad=0.05", 
                                     facecolor='#aed6f1', edgecolor=color_prep, linewidth=1.5))
        ax.text(x, y_pos-1.2, step, ha='center', va='center', fontsize=7)
        ax.annotate('', xy=(x, y_pos-0.4), xytext=(x, y_pos-0.9),
                   arrowprops=dict(arrowstyle='->', color=color_prep, lw=1.5))
    
    # Arrow to next phase
    ax.annotate('', xy=(4.5, y_pos), xytext=(3.6, y_pos),
               arrowprops=dict(arrowstyle='->', color='black', lw=2))
    
    # Phase 2: Packaging
    ax.add_patch(FancyBboxPatch((4.5, y_pos-0.4), 3, 0.8, boxstyle="round,pad=0.1", 
                                 facecolor=color_pack, edgecolor='black', linewidth=2, alpha=0.8))
    ax.text(6, y_pos, 'Secondary\nPackaging', ha='center', va='center', 
            fontsize=10, fontweight='bold', color='white')
    
    # Sub-steps
    steps_pack = ['Condition\nPCM/gel packs', 'Assemble\ninsulated box', 
                  'Place specimen\n& logger', 'Seal &\nlabel']
    for i, step in enumerate(steps_pack):
        x = 5 + i * 0.7
        ax.add_patch(FancyBboxPatch((x-0.3, y_pos-1.5), 0.6, 0.6, boxstyle="round,pad=0.05", 
                                     facecolor='#abebc6', edgecolor=color_pack, linewidth=1.5))
        ax.text(x, y_pos-1.2, step, ha='center', va='center', fontsize=7)
        ax.annotate('', xy=(x, y_pos-0.4), xytext=(x, y_pos-0.9),
                   arrowprops=dict(arrowstyle='->', color=color_pack, lw=1.5))
    
    # Arrow to next phase
    ax.annotate('', xy=(8.5, y_pos), xytext=(7.6, y_pos),
               arrowprops=dict(arrowstyle='->', color='black', lw=2))
    
    # Phase 3: Shipment
    ax.add_patch(FancyBboxPatch((8.5, y_pos-0.4), 3, 0.8, boxstyle="round,pad=0.1", 
                                 facecolor=color_ship, edgecolor='black', linewidth=2, alpha=0.8))
    ax.text(10, y_pos, 'Cold-Chain\nTransport', ha='center', va='center', 
            fontsize=10, fontweight='bold', color='white')
    
    # Sub-steps
    steps_ship = ['Carrier\npickup', 'Continuous\nmonitoring', 
                  'In-transit\ntracking', 'Delivery\nconfirmation']
    for i, step in enumerate(steps_ship):
        x = 9 + i * 0.7
        ax.add_patch(FancyBboxPatch((x-0.3, y_pos-1.5), 0.6, 0.6, boxstyle="round,pad=0.05", 
                                     facecolor='#f5b7b1', edgecolor=color_ship, linewidth=1.5))
        ax.text(x, y_pos-1.2, step, ha='center', va='center', fontsize=7)
        ax.annotate('', xy=(x, y_pos-0.4), xytext=(x, y_pos-0.9),
                   arrowprops=dict(arrowstyle='->', color=color_ship, lw=1.5))
    
    # Arrow to next phase
    ax.annotate('', xy=(12.5, y_pos), xytext=(11.6, y_pos),
               arrowprops=dict(arrowstyle='->', color='black', lw=2))
    
    # Phase 4: Receipt
    ax.add_patch(FancyBboxPatch((12.5, y_pos-0.4), 1.2, 0.8, boxstyle="round,pad=0.1", 
                                 facecolor=color_receive, edgecolor='black', linewidth=2, alpha=0.8))
    ax.text(13.1, y_pos, 'Receipt &\nVerification', ha='center', va='center', 
            fontsize=9, fontweight='bold', color='white')
    
    # Temperature monitoring indicator
    ax.add_patch(FancyBboxPatch((0.5, 4.5), 13, 1.5, boxstyle="round,pad=0.1", 
                                 facecolor='#fef9e7', edgecolor='#f39c12', linewidth=2, linestyle='--'))
    ax.text(7, 5.8, 'CONTINUOUS TEMPERATURE MONITORING', ha='center', va='center', 
            fontsize=11, fontweight='bold', color='#d68910')
    ax.text(7, 5.2, 'Electronic data loggers record temperature at 15-minute intervals throughout the entire shipment process', 
            ha='center', va='center', fontsize=9, style='italic')
    ax.text(7, 4.7, 'Calibration: Maintained by vendor | Data Review: Required within 24h of receipt | Excursion: Report to QA immediately', 
            ha='center', va='center', fontsize=8, color='#7f8c8d')
    
    # Documentation flow
    ax.add_patch(FancyBboxPatch((0.5, 2.5), 13, 1.5, boxstyle="round,pad=0.1", 
                                 facecolor='#eaf2f8', edgecolor='#2980b9', linewidth=2, linestyle='--'))
    ax.text(7, 3.8, 'AUDIT TRAIL DOCUMENTATION', ha='center', va='center', 
            fontsize=11, fontweight='bold', color='#2471a3')
    
    docs = ['Shipment\nRequest', 'Chain of\nCustody', 'Packaging\nRecord', 'Temperature\nData', 'Receipt\nConfirmation']
    for i, doc in enumerate(docs):
        x = 1.5 + i * 2.5
        ax.add_patch(FancyBboxPatch((x-0.6, 2.7), 1.2, 0.6, boxstyle="round,pad=0.05", 
                                     facecolor='#d4e6f1', edgecolor='#2980b9', linewidth=1.5))
        ax.text(x, 3, doc, ha='center', va='center', fontsize=8)
        if i < len(docs) - 1:
            ax.annotate('', xy=(x+1.3, 3), xytext=(x+0.7, 3),
                       arrowprops=dict(arrowstyle='->', color='#2980b9', lw=1.5))
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=color_prep, edgecolor='black', label='Pre-Shipment'),
        mpatches.Patch(facecolor=color_pack, edgecolor='black', label='Packaging'),
        mpatches.Patch(facecolor=color_ship, edgecolor='black', label='Transport'),
        mpatches.Patch(facecolor=color_receive, edgecolor='black', label='Receipt')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9, framealpha=0.9)
    
    # Compliance note
    ax.text(7, 0.5, 'Compliant with: IATA DGR | WHO Guidelines | FDA GDP | Temperature-sensitive biologics protocol', 
            ha='center', va='center', fontsize=9, style='italic', color='#5d6d7e',
            bbox=dict(boxstyle='round', facecolor='#f8f9f9', edgecolor='#aeb6bf'))
    
    plt.tight_layout()
    plt.savefig('report/images/cold_chain_workflow.png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    print("Figure 1: Cold-chain workflow diagram saved.")


def create_temperature_profile():
    """Create simulated temperature profile for cold-chain shipment"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Time points (hours)
    np.random.seed(42)
    hours = np.linspace(0, 48, 193)  # 15-minute intervals over 48 hours
    
    # Scenario 1: Successful cold-chain (2-8°C)
    ax1 = axes[0]
    temp_ideal = 5 + 1.5 * np.sin(2 * np.pi * hours / 24) + np.random.normal(0, 0.3, len(hours))
    temp_ideal = np.clip(temp_ideal, 2, 8)
    
    ax1.fill_between(hours, 2, 8, alpha=0.2, color='green', label='Acceptable Range (2-8°C)')
    ax1.plot(hours, temp_ideal, 'b-', linewidth=1.5, label='Temperature Profile')
    ax1.axhline(y=2, color='green', linestyle='--', alpha=0.7)
    ax1.axhline(y=8, color='green', linestyle='--', alpha=0.7)
    ax1.axhline(y=5, color='gray', linestyle=':', alpha=0.5, label='Target (5°C)')
    
    # Mark key events
    events = [(0, 'Packaging'), (4, 'Pickup'), (24, 'In-Transit'), (44, 'Delivery'), (46, 'Receipt')]
    for t, label in events:
        ax1.axvline(x=t, color='red', linestyle='--', alpha=0.5)
        ax1.text(t, 8.5, label, rotation=90, fontsize=8, ha='center')
    
    ax1.set_xlabel('Time (hours)', fontsize=10)
    ax1.set_ylabel('Temperature (°C)', fontsize=10)
    ax1.set_title('Scenario A: Compliant Cold-Chain Shipment (Refrigerated Biologics)', fontsize=12, fontweight='bold')
    ax1.set_xlim(0, 48)
    ax1.set_ylim(0, 10)
    ax1.legend(loc='lower right', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # Add compliance indicator
    ax1.text(24, 1, '✓ COMPLIANT - All readings within 2-8°C range', 
             ha='center', fontsize=10, color='green', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='#d5f5e3', edgecolor='green'))
    
    # Scenario 2: Temperature excursion
    ax2 = axes[1]
    temp_excursion = 5 + 1.5 * np.sin(2 * np.pi * hours / 24) + np.random.normal(0, 0.3, len(hours))
    # Add excursion at hour 20-24
    excursion_idx = (hours >= 20) & (hours <= 24)
    temp_excursion[excursion_idx] += 5  # Temperature spike
    temp_excursion = np.clip(temp_excursion, 2, 15)
    
    ax2.fill_between(hours, 2, 8, alpha=0.2, color='green', label='Acceptable Range (2-8°C)')
    ax2.fill_between(hours, 8, 15, alpha=0.2, color='red', label='Excursion Zone')
    ax2.plot(hours, temp_excursion, 'b-', linewidth=1.5, label='Temperature Profile')
    ax2.axhline(y=2, color='green', linestyle='--', alpha=0.7)
    ax2.axhline(y=8, color='green', linestyle='--', alpha=0.7)
    
    # Highlight excursion
    ax2.fill_between(hours[excursion_idx], 8, temp_excursion[excursion_idx], 
                     alpha=0.5, color='red')
    
    for t, label in events:
        ax2.axvline(x=t, color='red', linestyle='--', alpha=0.5)
        ax2.text(t, 13, label, rotation=90, fontsize=8, ha='center')
    
    ax2.set_xlabel('Time (hours)', fontsize=10)
    ax2.set_ylabel('Temperature (°C)', fontsize=10)
    ax2.set_title('Scenario B: Temperature Excursion Event (Deviation Investigation Required)', fontsize=12, fontweight='bold')
    ax2.set_xlim(0, 48)
    ax2.set_ylim(0, 15)
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # Add excursion alert
    ax2.text(22, 12, '⚠ EXCURSION DETECTED\nHours 20-24: Temperature >8°C', 
             ha='center', fontsize=10, color='red', fontweight='bold',
             bbox=dict(boxstyle='round', facecolor='#fadbd8', edgecolor='red'))
    
    plt.tight_layout()
    plt.savefig('report/images/temperature_profile.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Figure 2: Temperature profile scenarios saved.")


def create_responsibility_matrix():
    """Create responsibility matrix visualization"""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(6, 9.5, 'Cold-Chain Shipment Responsibility Matrix', fontsize=14, fontweight='bold', ha='center')
    
    # Roles and activities
    roles = ['Clinical\nOperations', 'Packaging\nTeam', 'Logistics\nCoordinator', 'Quality\nAssurance', 'Vendor']
    activities = ['SOP Maintenance', 'Logger Calibration', 'Packaging Execution', 'Shipment Scheduling', 
                  'Temperature Monitoring', 'Documentation Review', 'Deviation Investigation', 'Audit Trail']
    
    # Responsibility codes
    # R = Responsible, A = Accountable, C = Consulted, I = Informed
    matrix = [
        ['A', 'C', 'R', 'C', 'I'],  # SOP Maintenance
        ['I', 'C', 'I', 'C', 'R'],  # Logger Calibration
        ['C', 'R', 'C', 'I', 'I'],  # Packaging Execution
        ['C', 'I', 'R', 'C', 'I'],  # Shipment Scheduling
        ['I', 'R', 'I', 'C', 'C'],  # Temperature Monitoring
        ['I', 'I', 'R', 'A', 'I'],  # Documentation Review
        ['C', 'I', 'I', 'R', 'C'],  # Deviation Investigation
        ['A', 'C', 'R', 'R', 'I'],  # Audit Trail
    ]
    
    # Draw header
    header_y = 8.5
    ax.add_patch(FancyBboxPatch((0.5, header_y-0.3), 3.5, 0.6, boxstyle="round,pad=0.05", 
                                 facecolor='#2c3e50', edgecolor='black', linewidth=1))
    ax.text(2.25, header_y, 'Activity / Role', ha='center', va='center', fontsize=10, 
            fontweight='bold', color='white')
    
    for i, role in enumerate(roles):
        x = 4.2 + i * 1.5
        ax.add_patch(FancyBboxPatch((x-0.6, header_y-0.3), 1.2, 0.6, boxstyle="round,pad=0.05", 
                                     facecolor='#34495e', edgecolor='black', linewidth=1))
        ax.text(x, header_y, role, ha='center', va='center', fontsize=8, 
                fontweight='bold', color='white')
    
    # Draw matrix
    colors = {'R': '#27ae60', 'A': '#2980b9', 'C': '#f39c12', 'I': '#95a5a6'}
    labels = {'R': 'Responsible', 'A': 'Accountable', 'C': 'Consulted', 'I': 'Informed'}
    
    for i, activity in enumerate(activities):
        y = 7.8 - i * 0.9
        
        # Activity name
        ax.add_patch(FancyBboxPatch((0.5, y-0.35), 3.5, 0.7, boxstyle="round,pad=0.05", 
                                     facecolor='#ecf0f1', edgecolor='black', linewidth=1))
        ax.text(2.25, y, activity, ha='center', va='center', fontsize=9)
        
        # Responsibility cells
        for j, resp in enumerate(matrix[i]):
            x = 4.2 + j * 1.5
            ax.add_patch(FancyBboxPatch((x-0.6, y-0.35), 1.2, 0.7, boxstyle="round,pad=0.05", 
                                         facecolor=colors[resp], edgecolor='black', linewidth=1, alpha=0.8))
            ax.text(x, y, resp, ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    
    # Legend
    legend_y = 0.8
    for i, (code, color) in enumerate(colors.items()):
        x = 2 + i * 2.5
        ax.add_patch(FancyBboxPatch((x-0.3, legend_y-0.2), 0.6, 0.4, boxstyle="round,pad=0.05", 
                                     facecolor=color, edgecolor='black', linewidth=1))
        ax.text(x, legend_y, code, ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        ax.text(x+0.5, legend_y, f'= {labels[code]}', ha='left', va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('report/images/responsibility_matrix.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Figure 3: Responsibility matrix saved.")


def create_packaging_specifications():
    """Create packaging specifications diagram"""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(6, 9.5, 'Qualified Packaging System Specifications', fontsize=14, fontweight='bold', ha='center')
    
    # Three layers of packaging
    layers = [
        {'name': 'Primary Packaging', 'y': 7, 'height': 1.2, 'color': '#3498db', 
         'items': ['Leak-proof container', 'Absorbent material', 'Specimen label']},
        {'name': 'Secondary Packaging', 'y': 5, 'height': 1.5, 'color': '#2ecc71',
         'items': ['Insulated container', 'Phase-change materials', 'Temperature logger', 'Cushioning']},
        {'name': 'Outer Packaging', 'y': 2.8, 'height': 1.2, 'color': '#e74c3c',
         'items': ['Corrugated fiberboard', 'UN 3373 labels', 'Orientation arrows', 'Emergency contact']}
    ]
    
    for layer in layers:
        y = layer['y']
        h = layer['height']
        
        # Main box
        ax.add_patch(FancyBboxPatch((2, y-h/2), 6, h, boxstyle="round,pad=0.1", 
                                     facecolor=layer['color'], edgecolor='black', linewidth=2, alpha=0.8))
        ax.text(5, y, layer['name'], ha='center', va='center', fontsize=11, 
                fontweight='bold', color='white')
        
        # Items
        for i, item in enumerate(layer['items']):
            item_x = 8.5 + (i % 2) * 2.5
            item_y = y + 0.3 - (i // 2) * 0.5
            ax.add_patch(FancyBboxPatch((item_x-1, item_y-0.2), 2, 0.4, boxstyle="round,pad=0.05", 
                                         facecolor='white', edgecolor=layer['color'], linewidth=1.5))
            ax.text(item_x, item_y, item, ha='center', va='center', fontsize=8)
            
            # Arrow from layer to item
            if i < 2:
                start_x = 8
            else:
                start_x = 8
            ax.annotate('', xy=(item_x-1.1, item_y), xytext=(start_x, y),
                       arrowprops=dict(arrowstyle='->', color=layer['color'], lw=1, alpha=0.5))
    
    # Temperature ranges
    ax.add_patch(FancyBboxPatch((0.5, 0.5), 11, 1.5, boxstyle="round,pad=0.1", 
                                 facecolor='#fef9e7', edgecolor='#f39c12', linewidth=2))
    ax.text(6, 1.7, 'Temperature Requirements by Specimen Type', ha='center', va='center', 
            fontsize=11, fontweight='bold', color='#d68910')
    
    ranges = [
        ('Frozen', '-20°C to -80°C', '#85c1e9'),
        ('Refrigerated', '2°C to 8°C', '#82e0aa'),
        ('Ambient', '15°C to 25°C', '#f8c471')
    ]
    
    for i, (type_name, range_str, color) in enumerate(ranges):
        x = 2 + i * 3.5
        ax.add_patch(FancyBboxPatch((x-1.3, 0.7), 2.6, 0.7, boxstyle="round,pad=0.05", 
                                     facecolor=color, edgecolor='black', linewidth=1, alpha=0.7))
        ax.text(x, 1.2, type_name, ha='center', va='center', fontsize=9, fontweight='bold')
        ax.text(x, 0.9, range_str, ha='center', va='center', fontsize=8)
    
    plt.tight_layout()
    plt.savefig('report/images/packaging_specifications.png', dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Figure 4: Packaging specifications saved.")


if __name__ == '__main__':
    create_workflow_diagram()
    create_temperature_profile()
    create_responsibility_matrix()
    create_packaging_specifications()
    print("\nAll figures generated successfully!")
