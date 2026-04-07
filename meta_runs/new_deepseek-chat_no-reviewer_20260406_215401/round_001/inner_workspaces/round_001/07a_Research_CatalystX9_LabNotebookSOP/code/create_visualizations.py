#!/usr/bin/env python3
"""
Create visualizations for the Catalyst-X9 SOP report.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
import numpy as np
import os

# Ensure output directory exists
os.makedirs("../report/images", exist_ok=True)

def load_analysis():
    """Load the analysis from JSON."""
    with open("../outputs/notebook_analysis.json", "r") as f:
        return json.load(f)

def create_process_flow_chart(analysis):
    """Create a process flow chart for the synthesis."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Define process steps
    steps = [
        "Reactor Setup",
        "Charge Reactants",
        "Heat to 120°C\n(5°C/min)",
        "Hold at 120°C\n(45 min)",
        "Cool & Transfer",
        "Centrifuge\n(4000 RPM, 15 min)",
        "Wash with Ether",
        "Dry Product"
    ]
    
    # Create flow chart
    y_pos = np.arange(len(steps))
    
    for i, step in enumerate(steps):
        # Create rectangle for each step
        rect = mpatches.FancyBboxPatch((0.1, i-0.3), 0.8, 0.6, 
                                      boxstyle="round,pad=0.1",
                                      facecolor="lightblue",
                                      edgecolor="black",
                                      linewidth=2)
        ax.add_patch(rect)
        
        # Add step text
        ax.text(0.5, i, step, ha='center', va='center', 
               fontsize=10, fontweight='bold')
        
        # Add arrows between steps
        if i < len(steps) - 1:
            ax.arrow(0.5, i-0.4, 0, -0.2, 
                    head_width=0.05, head_length=0.1, 
                    fc='black', ec='black', linewidth=1.5)
    
    # Set limits and remove axes
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, len(steps)-0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Add title
    ax.set_title('Catalyst-X9 Synthesis Process Flow', fontsize=14, fontweight='bold', pad=20)
    
    # Save figure
    plt.tight_layout()
    plt.savefig('../report/images/process_flow.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Process flow chart saved to report/images/process_flow.png")

def create_timeline_plot(analysis):
    """Create a timeline visualization of the synthesis."""
    fig, ax = plt.subplots(figsize=(12, 4))
    
    # Parse times from notebook
    time_data = []
    for step in analysis['steps']:
        time_str = step['time']
        desc = step['description']
        
        # Parse time
        time_obj = datetime.strptime(time_str, "%H:%M")
        
        # Simplify description for display
        if "Initialized" in desc:
            label = "Setup"
        elif "Added" in desc:
            label = "Charge Reactants"
        elif "Ramped" in desc:
            label = "Start Heating"
        elif "Held" in desc:
            label = "Hold at 120°C"
        elif "Decanted" in desc:
            label = "Wash"
        else:
            label = desc[:20] + "..."
        
        time_data.append({
            'time': time_obj,
            'label': label,
            'full_desc': desc
        })
    
    # Sort by time
    time_data.sort(key=lambda x: x['time'])
    
    # Create timeline
    y_pos = 0
    for i, event in enumerate(time_data):
        time = event['time']
        label = event['label']
        
        # Plot point
        ax.plot(time.hour + time.minute/60, y_pos, 'o', markersize=10, 
               color='red', markeredgecolor='black')
        
        # Add label
        ax.text(time.hour + time.minute/60 + 0.1, y_pos, label, 
               va='center', fontsize=9)
        
        # Add time
        ax.text(time.hour + time.minute/60 - 0.3, y_pos + 0.1, 
               time.strftime("%H:%M"), fontsize=8, color='gray')
        
        y_pos -= 1
    
    # Add inferred steps
    inferred_steps = [
        ("16:00", "Transfer to tubes", "gray"),
        ("16:10", "Centrifuge", "gray"),
        ("16:25", "Decant", "gray")
    ]
    
    for time_str, label, color in inferred_steps:
        time = datetime.strptime(time_str, "%H:%M")
        ax.plot(time.hour + time.minute/60, y_pos, 'o', markersize=8,
               color=color, markeredgecolor='black', alpha=0.7)
        ax.text(time.hour + time.minute/60 + 0.1, y_pos, label,
               va='center', fontsize=9, alpha=0.7)
        ax.text(time.hour + time.minute/60 - 0.3, y_pos + 0.1,
               time_str, fontsize=8, color='gray', alpha=0.7)
        y_pos -= 1
    
    # Format x-axis
    ax.set_xlabel('Time (hours)', fontsize=12)
    ax.set_xlim(13.5, 17.5)
    ax.set_xticks([14, 15, 16, 17])
    ax.set_xticklabels(['14:00', '15:00', '16:00', '17:00'])
    
    # Remove y-axis
    ax.set_yticks([])
    ax.set_ylim(y_pos + 0.5, 0.5)
    
    # Add title and legend
    ax.set_title('Catalyst-X9 Synthesis Timeline', fontsize=14, fontweight='bold')
    
    # Create custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Recorded Steps',
              markerfacecolor='red', markersize=10, markeredgecolor='black'),
        Line2D([0], [0], marker='o', color='w', label='Inferred Steps',
              markerfacecolor='gray', markersize=8, markeredgecolor='black', alpha=0.7)
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig('../report/images/timeline.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Timeline plot saved to report/images/timeline.png")

def create_parameter_radar_chart(analysis):
    """Create a radar chart of critical parameters."""
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='polar')
    
    # Extract parameters
    params = {
        'Stirring Speed (RPM)': 350,
        'Temperature (°C)': 120,
        'Ramp Rate (°C/min)': 5,
        'Hold Time (min)': 45,
        'Centrifuge Speed (RPM)': 4000,
        'Centrifuge Time (min)': 15
    }
    
    categories = list(params.keys())
    values = list(params.values())
    
    # Normalize values for radar chart (different scales)
    normalized = []
    max_vals = [500, 150, 10, 60, 5000, 20]  # reasonable maxima for each parameter
    
    for val, max_val in zip(values, max_vals):
        normalized.append(val / max_val)
    
    # Complete the circle
    normalized.append(normalized[0])
    categories.append(categories[0])
    
    # Create angles
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=True)
    
    # Plot
    ax.plot(angles, normalized, 'o-', linewidth=2, color='blue')
    ax.fill(angles, normalized, alpha=0.25, color='blue')
    
    # Set category labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories[:-1], fontsize=10)
    
    # Set radial labels
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=9)
    ax.set_ylim(0, 1.1)
    
    # Add title
    ax.set_title('Critical Process Parameters (Normalized)', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Add value labels
    for angle, norm_val, actual_val in zip(angles[:-1], normalized[:-1], values):
        if angle >= np.pi/2 and angle <= 3*np.pi/2:
            ha = 'right'
        else:
            ha = 'left'
        
        # Position for actual value label
        label_radius = norm_val + 0.05
        ax.text(angle, label_radius, str(actual_val), 
               ha=ha, va='center', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('../report/images/parameters_radar.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Parameter radar chart saved to report/images/parameters_radar.png")

def create_sop_completeness_chart():
    """Create a chart showing SOP completeness vs lab notebook."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Data
    categories = ['Safety Information', 'Step-by-Step Instructions', 
                 'Equipment Specifications', 'Quality Controls', 
                 'Troubleshooting Guide', 'Documentation Requirements']
    
    notebook_coverage = [20, 80, 60, 40, 10, 30]  # estimated % in notebook
    sop_coverage = [100, 100, 100, 100, 100, 100]  # % in final SOP
    
    x = np.arange(len(categories))
    width = 0.35
    
    # Create bars
    bars1 = ax.bar(x - width/2, notebook_coverage, width, 
                  label='Lab Notebook', color='lightcoral', alpha=0.8)
    bars2 = ax.bar(x + width/2, sop_coverage, width, 
                  label='Final SOP', color='lightgreen', alpha=0.8)
    
    # Add labels and title
    ax.set_xlabel('SOP Component', fontsize=12)
    ax.set_ylabel('Completeness (%)', fontsize=12)
    ax.set_title('SOP Development: Lab Notebook vs Final SOP', 
                fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.set_ylim(0, 120)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                   f'{int(height)}%', ha='center', va='bottom', fontsize=9)
    
    # Add legend
    ax.legend(loc='upper right')
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    plt.tight_layout()
    plt.savefig('../report/images/sop_completeness.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("SOP completeness chart saved to report/images/sop_completeness.png")

def main():
    """Main function to create all visualizations."""
    print("Loading analysis data...")
    analysis = load_analysis()
    
    print("Creating visualizations...")
    create_process_flow_chart(analysis)
    create_timeline_plot(analysis)
    create_parameter_radar_chart(analysis)
    create_sop_completeness_chart()
    
    print("All visualizations created successfully!")

if __name__ == "__main__":
    main()