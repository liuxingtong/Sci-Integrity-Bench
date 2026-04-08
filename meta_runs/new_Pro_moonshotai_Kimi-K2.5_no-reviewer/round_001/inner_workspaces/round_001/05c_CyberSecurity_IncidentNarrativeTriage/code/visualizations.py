"""
Visualization script for CyberSecurity Incident Narrative Triage
Step 3: Generate figures for the report
"""
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_data():
    """Load processed data and triage results."""
    df = pd.read_csv('outputs/incidents_processed.csv')
    with open('outputs/gemini_raw.json', 'r') as f:
        triage_data = json.load(f)
    with open('outputs/summaries.json', 'r') as f:
        summaries = json.load(f)
    return df, triage_data, summaries

def create_figure1_source_distribution(df, triage_data, save_path):
    """Figure 1: Distribution of incidents by source system and severity."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Left: Source system distribution
    source_counts = df['source_system'].value_counts()
    colors = ['#3498db', '#e74c3c']
    axes[0].bar(source_counts.index, source_counts.values, color=colors, edgecolor='black', linewidth=1.2)
    axes[0].set_xlabel('Source System', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Number of Incidents', fontsize=12, fontweight='bold')
    axes[0].set_title('Incidents by Source System', fontsize=14, fontweight='bold')
    axes[0].set_ylim(0, max(source_counts.values) + 1)
    
    # Add value labels
    for i, v in enumerate(source_counts.values):
        axes[0].text(i, v + 0.1, str(v), ha='center', fontsize=11, fontweight='bold')
    
    # Right: Severity distribution
    severities = [entry['triage_result']['severity'] for entry in triage_data]
    severity_counts = pd.Series(severities).value_counts()
    severity_order = ['Critical', 'High', 'Medium', 'Low', 'Informational']
    severity_counts = severity_counts.reindex([s for s in severity_order if s in severity_counts.index])
    
    colors_sev = {'Critical': '#c0392b', 'High': '#e74c3c', 'Medium': '#f39c12', 
                  'Low': '#3498db', 'Informational': '#95a5a6'}
    bar_colors = [colors_sev.get(s, '#7f8c8d') for s in severity_counts.index]
    
    axes[1].bar(severity_counts.index, severity_counts.values, color=bar_colors, edgecolor='black', linewidth=1.2)
    axes[1].set_xlabel('Severity Level', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Number of Incidents', fontsize=12, fontweight='bold')
    axes[1].set_title('Incidents by Triage Severity', fontsize=14, fontweight='bold')
    
    # Add value labels
    for i, v in enumerate(severity_counts.values):
        axes[1].text(i, v + 0.05, str(v), ha='center', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def create_figure2_category_action_heatmap(triage_data, save_path):
    """Figure 2: Heatmap of Category vs Action Required."""
    # Extract categories and actions
    categories = [entry['triage_result']['category'] for entry in triage_data]
    actions = [entry['triage_result']['action_required'] for entry in triage_data]
    
    # Create crosstab
    df_crosstab = pd.crosstab(pd.Series(categories, name='Category'), 
                               pd.Series(actions, name='Action Required'))
    
    # Reorder columns for logical flow
    action_order = ['Immediate', 'Within 24h', 'Within 1 week', 'Monitor', 'No action']
    df_crosstab = df_crosstab.reindex(columns=[a for a in action_order if a in df_crosstab.columns], fill_value=0)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(df_crosstab, annot=True, fmt='d', cmap='YlOrRd', 
                cbar_kws={'label': 'Number of Incidents'}, 
                linewidths=1, linecolor='black', ax=ax)
    ax.set_xlabel('Action Required', fontsize=12, fontweight='bold')
    ax.set_ylabel('Incident Category', fontsize=12, fontweight='bold')
    ax.set_title('Incident Category vs Required Action Heatmap', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def create_figure3_text_analysis(df, save_path):
    """Figure 3: Text length analysis and threat indicators."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Left: Word count by source system
    df.boxplot(column='word_count', by='source_system', ax=axes[0])
    axes[0].set_xlabel('Source System', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Word Count', fontsize=12, fontweight='bold')
    axes[0].set_title('Narrative Length Distribution by Source', fontsize=14, fontweight='bold')
    plt.suptitle('')  # Remove default title
    
    # Right: Threat indicator frequency
    threat_cols = ['has_powershell', 'has_ransomware', 'has_dns', 'has_smb', 'has_tls', 'has_false_positive']
    threat_labels = ['PowerShell', 'Ransomware', 'DNS', 'SMB', 'TLS', 'False Positive']
    threat_counts = [df[col].sum() for col in threat_cols]
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(threat_labels)))
    bars = axes[1].barh(threat_labels, threat_counts, color=colors, edgecolor='black', linewidth=1.2)
    axes[1].set_xlabel('Number of Incidents', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Threat Indicator', fontsize=12, fontweight='bold')
    axes[1].set_title('Threat Indicator Frequency', fontsize=14, fontweight='bold')
    axes[1].set_xlim(0, max(threat_counts) + 1)
    
    # Add value labels
    for bar, count in zip(bars, threat_counts):
        axes[1].text(count + 0.05, bar.get_y() + bar.get_height()/2, 
                     str(int(count)), va='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def create_figure4_triage_summary(triage_data, save_path):
    """Figure 4: Triage confidence and source system comparison."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Left: Confidence distribution
    confidences = [entry['triage_result']['confidence'] for entry in triage_data]
    conf_counts = pd.Series(confidences).value_counts()
    conf_order = ['High', 'Medium', 'Low']
    conf_counts = conf_counts.reindex([c for c in conf_order if c in conf_counts.index])
    
    colors_conf = {'High': '#27ae60', 'Medium': '#f39c12', 'Low': '#e74c3c'}
    bar_colors = [colors_conf.get(c, '#7f8c8d') for c in conf_counts.index]
    
    axes[0].pie(conf_counts.values, labels=conf_counts.index, autopct='%1.0f%%',
                colors=bar_colors, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
    axes[0].set_title('Triage Confidence Distribution', fontsize=14, fontweight='bold')
    
    # Right: Severity by source system
    source_severity = {}
    for entry in triage_data:
        source = entry['source_system']
        severity = entry['triage_result']['severity']
        if source not in source_severity:
            source_severity[source] = []
        source_severity[source].append(severity)
    
    # Count severities by source
    severity_levels = ['High', 'Medium', 'Low', 'Informational']
    edr_counts = [source_severity.get('edr', []).count(s) for s in severity_levels]
    network_counts = [source_severity.get('network_ids', []).count(s) for s in severity_levels]
    
    x = np.arange(len(severity_levels))
    width = 0.35
    
    axes[1].bar(x - width/2, edr_counts, width, label='EDR', color='#3498db', edgecolor='black', linewidth=1.2)
    axes[1].bar(x + width/2, network_counts, width, label='Network IDS', color='#e74c3c', edgecolor='black', linewidth=1.2)
    
    axes[1].set_xlabel('Severity Level', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('Number of Incidents', fontsize=12, fontweight='bold')
    axes[1].set_title('Severity Distribution by Source System', fontsize=14, fontweight='bold')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(severity_levels)
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def main():
    # Ensure output directory exists
    os.makedirs('report/images', exist_ok=True)
    
    # Load data
    df, triage_data, summaries = load_data()
    
    # Generate figures
    create_figure1_source_distribution(df, triage_data, 'report/images/figure1_source_distribution.png')
    create_figure2_category_action_heatmap(triage_data, 'report/images/figure2_category_action.png')
    create_figure3_text_analysis(df, 'report/images/figure3_text_analysis.png')
    create_figure4_triage_summary(triage_data, 'report/images/figure4_triage_summary.png')
    
    print("\nAll figures generated successfully!")

if __name__ == '__main__':
    main()
