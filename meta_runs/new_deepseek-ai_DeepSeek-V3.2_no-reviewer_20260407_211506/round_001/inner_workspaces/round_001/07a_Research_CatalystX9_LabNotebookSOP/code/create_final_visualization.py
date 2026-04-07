#!/usr/bin/env python3
"""
Create final visualization showing transformation from notebook to SOP.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np


def create_transformation_diagram():
    """Create diagram showing notebook to SOP transformation."""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(6, 9.5, 'Lab Notebook to SOP Transformation Process', 
            fontsize=18, fontweight='bold', ha='center', color='navy')
    
    # Process steps
    steps = [
        (2, 7, 'Raw Notebook\nUnstructured text', '#FF9999', 'data/lab_notebook_x9.txt'),
        (4, 7, 'Text Analysis\nParameter extraction', '#66B3FF', 'code/analyze_notebook.py'),
        (6, 7, 'Data Structuring\nCritical parameters', '#99FF99', 'outputs/'),
        (8, 7, 'SOP Generation\nChecklists, safety', '#FFD700', 'code/generate_final_sop.py'),
        (10, 7, 'Executable SOP\nVersion controlled', '#FF6B6B', 'report/synthesis_sop.md')
    ]
    
    # Draw steps
    for x, y, text, color, output in steps:
        # Box with rounded corners
        bbox = FancyBboxPatch((x-1.2, y-0.8), 2.4, 1.6, 
                             boxstyle="round,pad=0.1",
                             linewidth=2, edgecolor='black', facecolor=color, alpha=0.8)
        ax.add_patch(bbox)
        
        # Text
        lines = text.split('\\n')
        for i, line in enumerate(lines):
            offset = 0.3 - (i * 0.3)
            ax.text(x, y + offset, line, fontsize=10, ha='center', fontweight='bold')
        
        # Output label
        ax.text(x, y-1.1, output, fontsize=8, ha='center', style='italic', alpha=0.7)
    
    # Draw arrows
    for i in range(len(steps) - 1):
        x1 = steps[i][0] + 1.2
        x2 = steps[i+1][0] - 1.2
        y = steps[i][1]
        
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                   arrowprops=dict(arrowstyle='->', lw=2, color='black', shrinkA=5, shrinkB=5))
    
    # Add transformation labels
    transformations = [
        (3, 6.5, 'NLP Analysis\nRegex extraction'),
        (5, 6.5, 'Parameter\nIdentification'),
        (7, 6.5, 'Structure\nDesign'),
        (9, 6.5, 'Version Control\n& Safety')
    ]
    
    for x, y, text in transformations:
        ax.text(x, y, text, fontsize=9, ha='center', 
               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.7))
    
    # Add visualizations section
    ax.text(6, 3.5, 'Generated Visualizations', fontsize=14, fontweight='bold', ha='center')
    
    viz_items = [
        (2, 2.5, 'Timeline', 'images/synthesis_timeline.png'),
        (6, 2.5, 'Process Flow', 'images/process_flowchart.png'),
        (10, 2.5, 'Summary Stats', 'images/synthesis_summary.png')
    ]
    
    for x, y, title, filepath in viz_items:
        # Circle
        circle = plt.Circle((x, y), 0.8, color='lightblue', alpha=0.7, ec='black', lw=2)
        ax.add_patch(circle)
        ax.text(x, y+0.2, title, fontsize=10, ha='center', fontweight='bold')
        ax.text(x, y-0.2, filepath, fontsize=7, ha='center', style='italic')
        
        # Connector to process
        ax.plot([x, x], [y+0.8, 3.8], 'k--', alpha=0.3)
    
    # Quality metrics
    ax.text(6, 0.8, 'Quality Metrics:', fontsize=12, fontweight='bold', ha='center')
    
    metrics = [
        (3, 0.3, '5 Steps\nExtracted'),
        (6, 0.3, '11 Safety\nChecks'),
        (9, 0.3, '3 Troubleshooting\nScenarios')
    ]
    
    for x, y, text in metrics:
        ax.text(x, y, text, fontsize=9, ha='center', 
               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
    
    plt.tight_layout()
    
    # Save figure
    fig_path = '../report/images/transformation_process.png'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Transformation diagram saved to: {fig_path}")
    
    # Update report to include this visualization
    update_report_with_new_figure(fig_path)


def update_report_with_new_figure(fig_path):
    """Update report to include the new transformation diagram."""
    try:
        with open('../report/report.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the visualization section and add new figure
        if '### 3.3 Visualizations' in content:
            # Add after the existing figures
            new_figure = "\n#### Figure 4: Notebook to SOP Transformation Process\n"
            new_figure += "![Transformation Process](images/transformation_process.png)\n"
            new_figure += "*Figure 4: Diagram showing the transformation process from raw notebook text to executable SOP with intermediate analysis steps and generated visualizations.*\n\n"
            
            # Insert after the third figure
            insert_point = content.find("*Figure 3: Summary visualizations")
            if insert_point != -1:
                # Find the end of that line
                end_line = content.find("\n", insert_point)
                new_content = content[:end_line+1] + new_figure + content[end_line+1:]
                
                with open('../report/report.md', 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("Report updated with new figure")
            
    except Exception as e:
        print(f"Error updating report: {e}")


if __name__ == "__main__":
    create_transformation_diagram()