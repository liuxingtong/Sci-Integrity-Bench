#!/usr/bin/env python3
"""
Create visualizations for the research report.
"""

import matplotlib.pyplot as plt
import numpy as np
import os

# Ensure report/images directory exists
os.makedirs('../report/images', exist_ok=True)

def create_requirements_chart():
    """Create chart showing extracted requirements from email."""
    categories = ['Purpose', 'Equipment', 'Procedures', 'Responsibilities', 'Documentation']
    counts = [1, 1, 1, 2, 0]  # From analysis
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(categories, counts, color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6B8F71'])
    
    ax.set_title('Requirements Extracted from Email Thread', fontsize=16, fontweight='bold')
    ax.set_ylabel('Number of Requirements', fontsize=12)
    ax.set_xlabel('Requirement Categories', fontsize=12)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{int(height)}', ha='center', va='bottom', fontsize=11)
    
    plt.tight_layout()
    plt.savefig('../report/images/requirements_extraction.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created requirements_extraction.png")

def create_sop_structure_chart():
    """Create chart showing SOP structure."""
    sections = ['1.0 Purpose & Scope', '2.0 Responsibilities', '3.0 Definitions', 
                '4.0 Equipment', '5.0 Procedures', '6.0 Documentation', 
                '7.0 Training', '8.0 References', '9.0 Revision History']
    
    # Estimated word count per section (based on generated SOP)
    word_counts = [120, 180, 100, 200, 300, 120, 80, 60, 40]
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Create horizontal bar chart
    y_pos = np.arange(len(sections))
    bars = ax.barh(y_pos, word_counts, color='#2E86AB', alpha=0.7)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(sections)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel('Estimated Word Count', fontsize=12)
    ax.set_title('SOP Structure and Content Distribution', fontsize=16, fontweight='bold')
    
    # Add value labels
    for i, (bar, count) in enumerate(zip(bars, word_counts)):
        width = bar.get_width()
        ax.text(width + 5, bar.get_y() + bar.get_height()/2.,
                f'{count}', ha='left', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('../report/images/sop_structure.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created sop_structure.png")

def create_process_flowchart():
    """Create a simple flowchart of the SOP generation process."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis('off')
    
    # Process steps
    steps = [
        '1. Email Analysis',
        '2. Requirements Extraction',
        '3. SOP Outline Generation',
        '4. Content Expansion',
        '5. Review & Validation',
        '6. Final SOP Document'
    ]
    
    # Draw flowchart
    box_height = 0.12
    box_width = 0.6
    y_positions = [0.85, 0.70, 0.55, 0.40, 0.25, 0.10]
    
    for i, (step, y) in enumerate(zip(steps, y_positions)):
        # Draw box
        box = plt.Rectangle((0.2, y), box_width, box_height, 
                           fill=True, facecolor='#2E86AB', alpha=0.7, 
                           edgecolor='black', linewidth=1.5)
        ax.add_patch(box)
        
        # Add text
        ax.text(0.5, y + box_height/2, step, 
               ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        
        # Draw arrow (except for last step)
        if i < len(steps) - 1:
            arrow_start = (0.5, y)
            arrow_end = (0.5, y_positions[i+1] + box_height)
            ax.annotate('', xy=arrow_end, xytext=arrow_start,
                       arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title('SOP Generation Process Flowchart', fontsize=16, fontweight='bold', y=0.95)
    
    plt.tight_layout()
    plt.savefig('../report/images/process_flowchart.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created process_flowchart.png")

def create_email_content_analysis():
    """Create visualization of email content analysis."""
    email_content = "From: ops@clinic.org\nWe need a cold-chain SOP for the new biologics route.\nTrucks have loggers but calibration details are with vendor.\nPackaging team will follow up on secondary packaging."
    
    # Count characters, words, sentences
    char_count = len(email_content)
    word_count = len(email_content.split())
    sentence_count = len([s for s in email_content.split('\n') if s.strip()])
    
    metrics = ['Characters', 'Words', 'Sentences']
    values = [char_count, word_count, sentence_count]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Bar chart
    bars = ax1.bar(metrics, values, color=['#2E86AB', '#A23B72', '#F18F01'])
    ax1.set_title('Email Content Metrics', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Count', fontsize=12)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom', fontsize=11)
    
    # Pie chart for requirement types
    req_types = ['Operational', 'Equipment', 'Procedural', 'Responsibility']
    req_counts = [1, 1, 1, 2]  # Based on analysis
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    
    ax2.pie(req_counts, labels=req_types, colors=colors, autopct='%1.0f%%', 
           startangle=90, textprops={'fontsize': 11})
    ax2.set_title('Requirement Types Distribution', fontsize=14, fontweight='bold')
    
    plt.suptitle('Email Thread Analysis', fontsize=16, fontweight='bold', y=1.05)
    plt.tight_layout()
    plt.savefig('../report/images/email_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Created email_analysis.png")

def main():
    """Create all visualizations."""
    print("Creating visualizations for research report...")
    
    create_requirements_chart()
    create_sop_structure_chart()
    create_process_flowchart()
    create_email_content_analysis()
    
    print("\nAll visualizations saved to report/images/")

if __name__ == "__main__":
    main()