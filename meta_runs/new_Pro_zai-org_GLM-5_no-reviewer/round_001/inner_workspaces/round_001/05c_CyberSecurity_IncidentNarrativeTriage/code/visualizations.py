"""
Visualization Script for Incident Narrative Triage
Generates figures for the report
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import numpy as np

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read data
df = pd.read_csv('../data/incident_narratives.csv')
with open('../outputs/gemini_raw.json', 'r') as f:
    triage_data = json.load(f)

# Convert to DataFrame
triage_df = pd.DataFrame([{
    'incident_id': t['incident_id'],
    'source_system': t['source_system'],
    'severity': t['triage_response']['severity'],
    'priority': t['triage_response']['priority'],
    'category': t['triage_response']['category'],
    'confidence': t['triage_response']['confidence']
} for t in triage_data])

# Add narrative length
df['narrative_length'] = df['narrative_text'].str.len()
df['word_count'] = df['narrative_text'].str.split().str.len()

# Create output directory
os.makedirs('../report/images', exist_ok=True)

# Figure 1: Severity and Priority Distribution
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Severity distribution
severity_order = ['Critical', 'High', 'Medium', 'Low']
severity_counts = triage_df['severity'].value_counts()
# Reorder to include all levels
severity_counts = severity_counts.reindex(severity_order, fill_value=0)

colors_severity = ['#d62728', '#ff7f0e', '#ffbb78', '#2ca02c']
bars1 = axes[0].bar(severity_counts.index, severity_counts.values, color=colors_severity, edgecolor='black', linewidth=1.2)
axes[0].set_title('Incident Severity Distribution', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Severity Level', fontsize=12)
axes[0].set_ylabel('Number of Incidents', fontsize=12)
axes[0].set_ylim(0, max(severity_counts.values) + 1)

# Add value labels on bars
for bar, val in zip(bars1, severity_counts.values):
    if val > 0:
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(int(val)), ha='center', va='bottom', fontsize=11, fontweight='bold')

# Priority distribution
priority_order = ['P1', 'P2', 'P3', 'P4']
priority_counts = triage_df['priority'].value_counts()
priority_counts = priority_counts.reindex(priority_order, fill_value=0)

colors_priority = ['#d62728', '#ff7f0e', '#8c564b', '#2ca02c']
bars2 = axes[1].bar(priority_counts.index, priority_counts.values, color=colors_priority, edgecolor='black', linewidth=1.2)
axes[1].set_title('Incident Priority Distribution', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Priority Level', fontsize=12)
axes[1].set_ylabel('Number of Incidents', fontsize=12)
axes[1].set_ylim(0, max(priority_counts.values) + 1)

# Add value labels on bars
for bar, val in zip(bars2, priority_counts.values):
    if val > 0:
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(int(val)), ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/fig1_severity_priority_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 1 saved: fig1_severity_priority_distribution.png")

# Figure 2: Source System Comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Incidents by source system
source_counts = df['source_system'].value_counts()
colors_source = ['#1f77b4', '#ff7f0e']
bars3 = axes[0].bar(source_counts.index, source_counts.values, color=colors_source, edgecolor='black', linewidth=1.2)
axes[0].set_title('Incidents by Source System', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Source System', fontsize=12)
axes[0].set_ylabel('Number of Incidents', fontsize=12)

for bar, val in zip(bars3, source_counts.values):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                str(int(val)), ha='center', va='bottom', fontsize=11, fontweight='bold')

# Severity by source system (stacked)
severity_by_source = triage_df.groupby(['source_system', 'severity']).size().unstack(fill_value=0)
severity_by_source = severity_by_source.reindex(columns=severity_order, fill_value=0)

x = np.arange(len(severity_by_source.index))
width = 0.6
bottom = np.zeros(len(severity_by_source.index))

for i, severity in enumerate(severity_order):
    if severity in severity_by_source.columns:
        vals = severity_by_source[severity].values
        axes[1].bar(x, vals, width, label=severity, bottom=bottom, color=colors_severity[i], edgecolor='black', linewidth=1)
        bottom += vals

axes[1].set_title('Severity Distribution by Source System', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Source System', fontsize=12)
axes[1].set_ylabel('Number of Incidents', fontsize=12)
axes[1].set_xticks(x)
axes[1].set_xticklabels(severity_by_source.index)
axes[1].legend(title='Severity', loc='upper right')

plt.tight_layout()
plt.savefig('../report/images/fig2_source_system_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: fig2_source_system_analysis.png")

# Figure 3: Incident Category Distribution
fig, ax = plt.subplots(figsize=(10, 6))

category_counts = triage_df['category'].value_counts()
colors_cat = plt.cm.Set3(np.linspace(0, 1, len(category_counts)))

bars = ax.barh(category_counts.index, category_counts.values, color=colors_cat, edgecolor='black', linewidth=1.2)
ax.set_title('Incident Categories from Triage Analysis', fontsize=14, fontweight='bold')
ax.set_xlabel('Number of Incidents', fontsize=12)
ax.set_ylabel('Category', fontsize=12)

# Add value labels
for bar, val in zip(bars, category_counts.values):
    ax.text(val + 0.05, bar.get_y() + bar.get_height()/2, 
            str(int(val)), ha='left', va='center', fontsize=11, fontweight='bold')

ax.set_xlim(0, max(category_counts.values) + 0.5)
plt.tight_layout()
plt.savefig('../report/images/fig3_category_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved: fig3_category_distribution.png")

# Figure 4: Narrative Length Analysis
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Narrative length by source system
for i, source in enumerate(df['source_system'].unique()):
    subset = df[df['source_system'] == source]
    axes[0].scatter([source] * len(subset), subset['narrative_length'], 
                   s=100, alpha=0.7, label=source, color=colors_source[i])

# Add mean line
means = df.groupby('source_system')['narrative_length'].mean()
for source, mean_val in means.items():
    axes[0].hlines(mean_val, -0.5 + list(df['source_system'].unique()).index(source), 
                   0.5 + list(df['source_system'].unique()).index(source), 
                   colors='red', linestyles='dashed', linewidth=2, label='Mean' if source == df['source_system'].unique()[0] else '')

axes[0].set_title('Narrative Length by Source System', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Source System', fontsize=12)
axes[0].set_ylabel('Narrative Length (characters)', fontsize=12)
axes[0].legend()

# Word count distribution
word_counts = df['word_count']
axes[1].hist(word_counts, bins=5, color='steelblue', edgecolor='black', linewidth=1.2, alpha=0.7)
axes[1].axvline(word_counts.mean(), color='red', linestyle='dashed', linewidth=2, label=f'Mean: {word_counts.mean():.1f}')
axes[1].set_title('Word Count Distribution', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Word Count', fontsize=12)
axes[1].set_ylabel('Frequency', fontsize=12)
axes[1].legend()

plt.tight_layout()
plt.savefig('../report/images/fig4_narrative_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved: fig4_narrative_analysis.png")

# Figure 5: Triage Priority Matrix
fig, ax = plt.subplots(figsize=(10, 6))

# Create a matrix of severity vs priority
severity_priority = triage_df.groupby(['severity', 'priority']).size().unstack(fill_value=0)
severity_priority = severity_priority.reindex(index=severity_order, columns=priority_order, fill_value=0)

# Create heatmap
sns.heatmap(severity_priority, annot=True, fmt='d', cmap='YlOrRd', 
            ax=ax, cbar_kws={'label': 'Number of Incidents'},
            linewidths=0.5, linecolor='black')
ax.set_title('Triage Matrix: Severity vs Priority', fontsize=14, fontweight='bold')
ax.set_xlabel('Priority', fontsize=12)
ax.set_ylabel('Severity', fontsize=12)

plt.tight_layout()
plt.savefig('../report/images/fig5_triage_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 5 saved: fig5_triage_matrix.png")

print("\n" + "="*60)
print("All figures generated successfully!")
print("="*60)
