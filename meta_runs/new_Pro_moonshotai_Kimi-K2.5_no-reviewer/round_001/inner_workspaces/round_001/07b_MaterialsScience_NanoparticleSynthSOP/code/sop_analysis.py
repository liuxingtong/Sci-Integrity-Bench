"""
Nanoparticle Synthesis SOP Analysis and Validation
Materials Science - Copper Nanoparticle Synthesis
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import seaborn as sns
import json
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# ============================================================================
# Section 1: Critical Process Parameters Analysis
# ============================================================================

def plot_critical_parameters():
    """Visualize critical process parameters and their acceptable ranges"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Critical Process Parameters for NanoCu Synthesis', fontsize=14, fontweight='bold')
    
    # Parameter 1: Temperature
    ax1 = axes[0, 0]
    temp_range = np.linspace(100, 120, 100)
    temp_acceptance = np.where((temp_range >= 108) & (temp_range <= 112), 1, 0)
    ax1.fill_between(temp_range, 0, temp_acceptance, alpha=0.3, color='green', label='Acceptable Range')
    ax1.axvline(x=110, color='red', linestyle='--', linewidth=2, label='Target: 110°C')
    ax1.axvspan(108, 112, alpha=0.2, color='green')
    ax1.set_xlabel('Temperature (°C)', fontsize=11)
    ax1.set_ylabel('Acceptance', fontsize=11)
    ax1.set_title('Reaction Temperature (Critical)', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.set_ylim(0, 1.2)
    ax1.text(110, 0.6, 'Target: 110°C\nRange: 108-112°C', ha='center', fontsize=9, 
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    # Parameter 2: Addition Time
    ax2 = axes[0, 1]
    time_range = np.linspace(5, 25, 100)
    time_acceptance = np.where((time_range >= 10) & (time_range <= 15), 1, 0.3)
    ax2.fill_between(time_range, 0, time_acceptance, alpha=0.3, color='blue')
    ax2.axvline(x=12.5, color='red', linestyle='--', linewidth=2, label='Target: 12.5 min')
    ax2.axvspan(10, 15, alpha=0.2, color='blue')
    ax2.set_xlabel('Addition Time (minutes)', fontsize=11)
    ax2.set_ylabel('Acceptance', fontsize=11)
    ax2.set_title('Precursor Addition Rate (Critical)', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.set_ylim(0, 1.2)
    ax2.text(12.5, 0.6, 'Target: 10-15 min\nDropwise addition', ha='center', fontsize=9,
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # Parameter 3: Reaction Time
    ax3 = axes[1, 0]
    rxn_time = np.linspace(8, 20, 100)
    rxn_acceptance = np.where((rxn_time >= 10) & (rxn_time <= 18), 1, 0.3)
    ax3.fill_between(rxn_time, 0, rxn_acceptance, alpha=0.3, color='orange')
    ax3.axvline(x=14, color='red', linestyle='--', linewidth=2, label='Target: 14 h')
    ax3.axvspan(12, 16, alpha=0.2, color='orange')
    ax3.set_xlabel('Reaction Time (hours)', fontsize=11)
    ax3.set_ylabel('Acceptance', fontsize=11)
    ax3.set_title('Reaction Duration (High Criticality)', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper right')
    ax3.set_ylim(0, 1.2)
    ax3.text(14, 0.6, 'Target: 12-16 h\n(Overnight)', ha='center', fontsize=9,
             bbox=dict(boxstyle='round', facecolor='moccasin', alpha=0.8))
    
    # Parameter 4: Surfactant Ratio
    ax4 = axes[1, 1]
    ratios = np.linspace(2, 6, 100)
    ratio_acceptance = np.where((ratios >= 3.5) & (ratios <= 4.5), 1, 0.3)
    ax4.fill_between(ratios, 0, ratio_acceptance, alpha=0.3, color='purple')
    ax4.axvline(x=4, color='red', linestyle='--', linewidth=2, label='Target: 4:1')
    ax4.axvspan(3.5, 4.5, alpha=0.2, color='purple')
    ax4.set_xlabel('Surfactant:Precursor Ratio (v/w)', fontsize=11)
    ax4.set_ylabel('Acceptance', fontsize=11)
    ax4.set_title('Surfactant Ratio (High Criticality)', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper right')
    ax4.set_ylim(0, 1.2)
    ax4.text(4, 0.6, 'Target: 4:1\nRange: 3.5-4.5:1', ha='center', fontsize=9,
             bbox=dict(boxstyle='round', facecolor='plum', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('report/images/fig1_critical_parameters.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/fig1_critical_parameters.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Figure 1 saved: Critical Process Parameters")

# ============================================================================
# Section 2: Process Flow Diagram
# ============================================================================

def plot_process_flow():
    """Create a visual process flow diagram for the synthesis"""
    
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(5, 9.5, 'NanoCu Synthesis Process Flow', fontsize=16, fontweight='bold', 
            ha='center', va='center')
    
    # Define box positions and colors
    boxes = [
        # (x, y, width, height, text, color)
        (1, 8, 1.5, 0.6, 'Precursor A\n(Cu acetate)', '#FFE4B5'),
        (3, 8, 1.5, 0.6, 'Solvent\n(Diphenyl ether)', '#E0FFFF'),
        (5, 8, 1.5, 0.6, 'Surfactant\n(Oleylamine)', '#DDA0DD'),
        (7, 8, 1.5, 0.6, 'N₂ Atmosphere', '#F0F0F0'),
        
        (4, 6.5, 2, 0.8, 'STEP 1\nHeat to 110°C', '#FFB6C1'),
        (4, 5, 2, 0.8, 'STEP 2\nAdd Precursor\n(Dropwise)', '#87CEEB'),
        (4, 3.5, 2, 0.8, 'STEP 3\nAdd Surfactant\n(Rapid)', '#98FB98'),
        (4, 2, 2, 0.8, 'STEP 4\nStir 12-16 h\n(Overnight)', '#F0E68C'),
        
        (1.5, 2, 1.5, 0.8, 'Color Change\nMonitor', '#FFFACD'),
        (7.5, 2, 1.5, 0.8, 'QC Sample', '#E6E6FA'),
        
        (4, 0.5, 2, 0.8, 'WORKUP\nQuench & Isolate', '#D3D3D3'),
    ]
    
    # Draw boxes
    for x, y, w, h, text, color in boxes:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", 
                             facecolor=color, edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Draw arrows
    arrows = [
        # From inputs to step 1
        ((1.75, 8), (4, 7.1)),
        ((3.75, 8), (4.5, 7.1)),
        ((5.75, 8), (5, 7.1)),
        ((7.75, 8), (5.5, 7.1)),
        # Between steps
        ((5, 6.5), (5, 5.8)),
        ((5, 5), (5, 4.3)),
        ((5, 3.5), (5, 2.8)),
        # Side connections
        ((4, 2.4), (3, 2.4)),
        ((6, 2.4), (7.5, 2.4)),
        # To workup
        ((5, 2), (5, 1.3)),
    ]
    
    for start, end in arrows:
        arrow = FancyArrowPatch(start, end, arrowstyle='->', mutation_scale=20, 
                               linewidth=2, color='darkblue')
        ax.add_patch(arrow)
    
    # Add annotations
    ax.text(0.5, 6.5, 'INPUTS', fontsize=11, fontweight='bold', rotation=90, va='center')
    ax.text(9.5, 4, 'SYNTHESIS', fontsize=11, fontweight='bold', rotation=90, va='center')
    ax.text(5, -0.3, 'OUTPUT: Cu Nanoparticles', fontsize=11, fontweight='bold', ha='center')
    
    # Color change indicator
    ax.annotate('', xy=(2.5, 1.5), xytext=(2.5, 2.5),
                arrowprops=dict(arrowstyle='->', color='green', lw=2))
    ax.text(2.5, 1.2, 'Blue-green\n→ Brown', ha='center', fontsize=8, color='green', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('report/images/fig2_process_flow.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/fig2_process_flow.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Figure 2 saved: Process Flow Diagram")

# ============================================================================
# Section 3: Scale-Up Analysis
# ============================================================================

def plot_scale_up_analysis():
    """Analyze scale-up parameters from lab to manufacturing"""
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Scale comparison
    ax1 = axes[0]
    scales = ['Lab Scale', 'Pilot Scale', 'Manufacturing']
    batch_sizes = [2.5, 55, 5000]  # grams
    colors = ['#87CEEB', '#98FB98', '#F0E68C']
    
    bars = ax1.bar(scales, batch_sizes, color=colors, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Batch Size (g)', fontsize=12)
    ax1.set_title('Scale-Up: Batch Size Progression', fontsize=13, fontweight='bold')
    ax1.set_yscale('log')
    
    # Add value labels
    for bar, size in zip(bars, batch_sizes):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{size:,} g', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Scale-up factors
    ax2 = axes[1]
    parameters = ['Heat Transfer\nArea', 'Mixing Power', 'Residence\nTime', 'Cooling\nRate']
    lab_vals = [1, 1, 1, 1]
    pilot_vals = [10, 15, 1.2, 0.8]
    manuf_vals = [500, 800, 1.5, 0.3]
    
    x = np.arange(len(parameters))
    width = 0.25
    
    bars1 = ax2.bar(x - width, lab_vals, width, label='Lab Scale', color='#87CEEB', edgecolor='black')
    bars2 = ax2.bar(x, pilot_vals, width, label='Pilot Scale', color='#98FB98', edgecolor='black')
    bars3 = ax2.bar(x + width, manuf_vals, width, label='Manufacturing', color='#F0E68C', edgecolor='black')
    
    ax2.set_ylabel('Relative Value (normalized)', fontsize=12)
    ax2.set_title('Scale-Up: Engineering Parameters', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(parameters, fontsize=10)
    ax2.legend(loc='upper left')
    ax2.set_yscale('log')
    
    plt.tight_layout()
    plt.savefig('report/images/fig3_scale_up.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/fig3_scale_up.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Figure 3 saved: Scale-Up Analysis")

# ============================================================================
# Section 4: Quality Control Metrics
# ============================================================================

def plot_quality_control():
    """Visualize quality control specifications and expected results"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Quality Control Specifications for NanoCu', fontsize=14, fontweight='bold')
    
    # Particle size distribution (simulated)
    ax1 = axes[0, 0]
    np.random.seed(42)
    sizes = np.random.normal(12, 3, 1000)  # nm
    sizes = sizes[(sizes > 0) & (sizes < 30)]
    
    ax1.hist(sizes, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
    ax1.axvline(x=5, color='red', linestyle='--', label='Lower spec: 5 nm')
    ax1.axvline(x=20, color='red', linestyle='--', label='Upper spec: 20 nm')
    ax1.axvspan(5, 20, alpha=0.2, color='green', label='Acceptable range')
    ax1.set_xlabel('Particle Size (nm)', fontsize=11)
    ax1.set_ylabel('Frequency', fontsize=11)
    ax1.set_title('Expected Particle Size Distribution', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.text(12, ax1.get_ylim()[1]*0.7, f'Mean: {np.mean(sizes):.1f} nm\nStd: {np.std(sizes):.1f} nm',
             ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # PDI (Polydispersity Index)
    ax2 = axes[0, 1]
    pdi_values = np.random.beta(7, 3, 500) * 0.3  # Target < 0.2
    ax2.hist(pdi_values, bins=25, color='coral', edgecolor='black', alpha=0.7)
    ax2.axvline(x=0.2, color='red', linestyle='--', linewidth=2, label='Spec limit: 0.2')
    ax2.axvspan(0, 0.2, alpha=0.2, color='green')
    ax2.set_xlabel('Polydispersity Index (PDI)', fontsize=11)
    ax2.set_ylabel('Frequency', fontsize=11)
    ax2.set_title('Size Distribution Quality (PDI)', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right')
    acceptance_rate = np.sum(pdi_values < 0.2) / len(pdi_values) * 100
    ax2.text(0.15, ax2.get_ylim()[1]*0.6, f'Expected Pass Rate:\n{acceptance_rate:.1f}%',
             ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    # Yield expectation
    ax3 = axes[1, 0]
    yields = np.random.beta(5, 2, 500) * 40 + 40  # 60-80% range
    ax3.hist(yields, bins=25, color='mediumseagreen', edgecolor='black', alpha=0.7)
    ax3.axvline(x=60, color='orange', linestyle='--', label='Min: 60%')
    ax3.axvline(x=80, color='green', linestyle='--', label='Target: 80%')
    ax3.axvspan(60, 80, alpha=0.2, color='green')
    ax3.set_xlabel('Yield (%)', fontsize=11)
    ax3.set_ylabel('Frequency', fontsize=11)
    ax3.set_title('Expected Product Yield', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper left')
    ax3.text(70, ax3.get_ylim()[1]*0.7, f'Typical: 60-80%\nMean: {np.mean(yields):.1f}%',
             ha='center', fontsize=9, bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # QC test summary
    ax4 = axes[1, 1]
    tests = ['Particle\nSize', 'PDI', 'Crystal\nPhase', 'Purity', 'Surface\nChemistry']
    specs = [95, 90, 98, 95, 92]  # Expected pass rates
    colors_qc = ['#2ecc71' if s >= 95 else '#f39c12' if s >= 90 else '#e74c3c' for s in specs]
    
    bars = ax4.barh(tests, specs, color=colors_qc, edgecolor='black', linewidth=1.5)
    ax4.axvline(x=95, color='red', linestyle='--', linewidth=2, label='Target: 95%')
    ax4.set_xlabel('Expected Pass Rate (%)', fontsize=11)
    ax4.set_title('QC Test Success Rates', fontsize=12, fontweight='bold')
    ax4.set_xlim(0, 100)
    ax4.legend(loc='lower right')
    
    for bar, spec in zip(bars, specs):
        width = bar.get_width()
        ax4.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{spec}%', ha='left', va='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('report/images/fig4_quality_control.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/fig4_quality_control.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Figure 4 saved: Quality Control Metrics")

# ============================================================================
# Section 5: Risk Assessment Matrix
# ============================================================================

def plot_risk_assessment():
    """Create a risk assessment heatmap for the synthesis process"""
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Risk matrix data
    process_steps = [
        'Heating (110°C)',
        'Precursor Addition',
        'Surfactant Addition', 
        'Overnight Reaction',
        'Cooling/Quenching',
        'Centrifugation',
        'Drying/Storage'
    ]
    
    risk_categories = ['Safety', 'Quality', 'Yield', 'Reproducibility']
    
    # Risk scores (1-5 scale, 5 = highest risk)
    risk_matrix = np.array([
        [4, 3, 2, 2],  # Heating
        [2, 4, 3, 3],  # Precursor addition
        [2, 3, 2, 2],  # Surfactant addition
        [3, 3, 4, 3],  # Overnight reaction
        [2, 4, 3, 3],  # Cooling/quenching
        [2, 2, 2, 2],  # Centrifugation
        [3, 3, 3, 3],  # Drying/storage
    ])
    
    # Create heatmap
    im = ax.imshow(risk_matrix, cmap='YlOrRd', aspect='auto', vmin=1, vmax=5)
    
    # Set ticks
    ax.set_xticks(np.arange(len(risk_categories)))
    ax.set_yticks(np.arange(len(process_steps)))
    ax.set_xticklabels(risk_categories, fontsize=11)
    ax.set_yticklabels(process_steps, fontsize=10)
    
    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Risk Level (1=Low, 5=High)', fontsize=11)
    
    # Add text annotations
    for i in range(len(process_steps)):
        for j in range(len(risk_categories)):
            text = ax.text(j, i, risk_matrix[i, j], ha='center', va='center',
                          color='white' if risk_matrix[i, j] > 3 else 'black',
                          fontsize=12, fontweight='bold')
    
    ax.set_title('Process Risk Assessment Matrix', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('report/images/fig5_risk_assessment.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/fig5_risk_assessment.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Figure 5 saved: Risk Assessment Matrix")

# ============================================================================
# Section 6: Time-Temperature Profile
# ============================================================================

def plot_time_temperature_profile():
    """Simulate and visualize the time-temperature profile for the synthesis"""
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Generate time points (in hours)
    time_points = np.linspace(0, 18, 500)
    
    # Simulate temperature profile
    temp_profile = np.piecewise(time_points, 
        [time_points < 0.5, 
         (time_points >= 0.5) & (time_points < 1.0),
         (time_points >= 1.0) & (time_points < 15.0),
         time_points >= 15.0],
        [lambda t: 25 + (110-25) * (t/0.5),  # Heating
         lambda t: 110,  # Hold at 110°C
         lambda t: 110,  # Reaction hold
         lambda t: 110 - (110-25) * ((t-15)/3)]  # Cooling
    )
    
    # Add some realistic noise
    np.random.seed(42)
    noise = np.random.normal(0, 1, len(temp_profile))
    temp_profile_noisy = temp_profile + noise
    
    # Plot
    ax.plot(time_points, temp_profile_noisy, 'b-', linewidth=1.5, alpha=0.7, label='Actual')
    ax.plot(time_points, temp_profile, 'r--', linewidth=2, label='Target')
    
    # Fill acceptable range
    ax.fill_between(time_points, 108, 112, alpha=0.2, color='green', label='Acceptable range')
    
    # Annotate phases
    phases = [
        (0.25, 70, 'Heating\n(0-0.5h)'),
        (0.75, 115, 'Stabilization\n(0.5-1h)'),
        (8, 115, 'Reaction\n(1-15h)'),
        (16.5, 70, 'Cooling\n(15-18h)')
    ]
    
    for x, y, text in phases:
        ax.annotate(text, xy=(x, y), ha='center', fontsize=9,
                   bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    ax.axhline(y=110, color='red', linestyle=':', alpha=0.5)
    ax.axvline(x=1, color='gray', linestyle=':', alpha=0.5)
    ax.axvline(x=15, color='gray', linestyle=':', alpha=0.5)
    
    ax.set_xlabel('Time (hours)', fontsize=12)
    ax.set_ylabel('Temperature (°C)', fontsize=12)
    ax.set_title('Synthesis Time-Temperature Profile', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.set_xlim(0, 18)
    ax.set_ylim(20, 125)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/fig6_time_temp_profile.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/fig6_time_temp_profile.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Figure 6 saved: Time-Temperature Profile")

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == '__main__':
    print("="*60)
    print("NanoCu Synthesis SOP Analysis")
    print("="*60)
    
    plot_critical_parameters()
    plot_process_flow()
    plot_scale_up_analysis()
    plot_quality_control()
    plot_risk_assessment()
    plot_time_temperature_profile()
    
    print("\n" + "="*60)
    print("All figures generated successfully!")
    print("="*60)
    
    # Save analysis summary
    summary = {
        "sop_version": "1.0",
        "analysis_date": "2024",
        "figures_generated": [
            "fig1_critical_parameters.png",
            "fig2_process_flow.png", 
            "fig3_scale_up.png",
            "fig4_quality_control.png",
            "fig5_risk_assessment.png",
            "fig6_time_temp_profile.png"
        ],
        "key_findings": {
            "critical_parameters": 4,
            "process_steps": 7,
            "qc_tests": 5,
            "scale_up_stages": 3
        }
    }
    
    with open('outputs/analysis_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("Analysis summary saved to outputs/analysis_summary.json")
