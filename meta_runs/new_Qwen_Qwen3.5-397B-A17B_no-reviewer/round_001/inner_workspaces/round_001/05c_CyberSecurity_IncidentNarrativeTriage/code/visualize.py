#!/usr/bin/env python3
"""
Visualization script for CyberSecurity Incident Narrative Triage
Generates figures for the research report
"""

import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os

def main():
    # Set style
    sns.set_style('whitegrid')
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['font.size'] = 12
    
    # Load data
    df = pd.read_csv('outputs/preprocessed_data.csv')
    
    with open('outputs/gemini_raw.json', 'r') as f:
        triage_results = json.load(f)
    
    # Create outputs directory for images
    os.makedirs('report/images', exist_ok=True)
    
    # Figure 1: Source System Distribution
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    source_counts = df['source_system'].value_counts()
    colors = ['#2ecc71', '#3498db']
    bars = ax1.bar(source_counts.index, source_counts.values, color=colors, edgecolor='black', linewidth=1.5)
    ax1.set_xlabel('Source System', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Incidents', fontsize=12, fontweight='bold')
    ax1.set_title('Distribution of Incidents by Source System', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, max(source_counts.values) + 1)
    
    # Add value labels on bars
    for bar, val in zip(bars, source_counts.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(val), ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('report/images/figure1_source_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/figure1_source_distribution.png")
    
    # Figure 2: Narrative Length by Source System
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    df['narrative_length'] = df['narrative_text'].apply(len)
    
    # Box plot of narrative length by source system
    edr_lengths = df[df['source_system'] == 'edr']['narrative_length']
    network_lengths = df[df['source_system'] == 'network_ids']['narrative_length']
    
    data_to_plot = [edr_lengths.values, network_lengths.values]
    labels = ['EDR', 'Network IDS']
    colors_box = ['#e74c3c', '#3498db']
    
    bp = ax2.boxplot(data_to_plot, labels=labels, patch_artist=True, 
                     medianprops=dict(color='black', linewidth=2),
                     boxprops=dict(linewidth=1.5),
                     whiskerprops=dict(linewidth=1.5),
                     capprops=dict(linewidth=1.5))
    
    for patch, color in zip(bp['boxes'], colors_box):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.set_ylabel('Narrative Length (characters)', fontsize=12, fontweight='bold')
    ax2.set_title('Narrative Length Distribution by Source System', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, 150)
    
    plt.tight_layout()
    plt.savefig('report/images/figure2_narrative_length.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/figure2_narrative_length.png")
    
    # Figure 3: Triage Severity Distribution
    fig3, ax3 = plt.subplots(figsize=(8, 5))
    
    # Extract severity from triage results
    severities = [r['triage_result'].get('severity', 'UNKNOWN') for r in triage_results]
    severity_counts = pd.Series(severities).value_counts()
    
    # Order by severity level
    severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    severity_counts = severity_counts.reindex([s for s in severity_order if s in severity_counts.index])
    
    colors_sev = ['#c0392b', '#e67e22', '#f39c12', '#27ae60']
    colors_sev = colors_sev[:len(severity_counts)]
    
    bars3 = ax3.bar(severity_counts.index, severity_counts.values, color=colors_sev, edgecolor='black', linewidth=1.5)
    ax3.set_xlabel('Severity Level', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Number of Incidents', fontsize=12, fontweight='bold')
    ax3.set_title('Automated Triage: Severity Distribution', fontsize=14, fontweight='bold')
    ax3.set_ylim(0, max(severity_counts.values) + 1)
    
    for bar, val in zip(bars3, severity_counts.values):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(val), ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('report/images/figure3_severity_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/figure3_severity_distribution.png")
    
    # Figure 4: Confidence Scores by Source System
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    
    # Extract confidence scores
    confidence_data = []
    source_data = []
    for r in triage_results:
        conf = r['triage_result'].get('confidence', 0)
        confidence_data.append(conf)
        source_data.append(r['source_system'])
    
    conf_df = pd.DataFrame({
        'confidence': confidence_data,
        'source_system': source_data
    })
    
    # Scatter plot with jitter
    edr_conf = conf_df[conf_df['source_system'] == 'edr']['confidence']
    network_conf = conf_df[conf_df['source_system'] == 'network_ids']['confidence']
    
    x_edr = [1] * len(edr_conf)
    x_network = [2] * len(network_conf)
    
    ax4.scatter(x_edr, edr_conf, c='#e74c3c', s=100, alpha=0.7, edgecolors='black', linewidth=1.5, label='EDR')
    ax4.scatter(x_network, network_conf, c='#3498db', s=100, alpha=0.7, edgecolors='black', linewidth=1.5, label='Network IDS')
    
    # Add mean lines
    ax4.axhline(y=edr_conf.mean(), color='#e74c3c', linestyle='--', linewidth=2, alpha=0.8, label=f'EDR Mean: {edr_conf.mean():.2f}')
    ax4.axhline(y=network_conf.mean(), color='#3498db', linestyle='--', linewidth=2, alpha=0.8, label=f'Network Mean: {network_conf.mean():.2f}')
    
    ax4.set_xticks([1, 2])
    ax4.set_xticklabels(['EDR', 'Network IDS'])
    ax4.set_ylabel('Confidence Score', fontsize=12, fontweight='bold')
    ax4.set_title('Triage Confidence Scores by Source System', fontsize=14, fontweight='bold')
    ax4.set_ylim(0.5, 1.0)
    ax4.legend(loc='lower right')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/figure4_confidence_scores.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/figure4_confidence_scores.png")
    
    print("\nAll figures generated successfully!")

if __name__ == '__main__':
    main()
