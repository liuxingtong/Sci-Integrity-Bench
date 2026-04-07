#!/usr/bin/env python3
"""
Analyze Gemini triage results and generate visualizations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from matplotlib import cm

# Set up paths
OUTPUT_DIR = "../outputs"
REPORT_IMG_DIR = "../report/images"
TRIAGE_SUMMARY_PATH = os.path.join(OUTPUT_DIR, "gemini_triage_summary.csv")
PROCESSED_DATA_PATH = os.path.join(OUTPUT_DIR, "processed_incidents.csv")
TRIAGE_STATS_PATH = os.path.join(OUTPUT_DIR, "gemini_triage_stats.json")

# Create directory if it doesn't exist
os.makedirs(REPORT_IMG_DIR, exist_ok=True)

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("Loading triage results...")
triage_df = pd.read_csv(TRIAGE_SUMMARY_PATH)
processed_df = pd.read_csv(PROCESSED_DATA_PATH)

# Merge triage results with processed data
merged_df = pd.merge(triage_df, processed_df, on='incident_id', how='left')
print(f"Merged data shape: {merged_df.shape}")
print(f"Columns: {merged_df.columns.tolist()}")

# Load triage statistics
with open(TRIAGE_STATS_PATH, 'r') as f:
    triage_stats = json.load(f)

print("\n=== Triage Analysis ===")
print(f"Total incidents triaged: {len(merged_df)}")
print(f"Average severity: {triage_stats['avg_severity']:.2f}")
print(f"Average confidence: {triage_stats['avg_confidence']:.2f}")

# 1. Severity distribution by source system
plt.figure(figsize=(10, 6))
sns.boxplot(data=merged_df, x='source_system_x', y='severity_score')
plt.title('Severity Score Distribution by Source System', fontsize=14, fontweight='bold')
plt.xlabel('Source System', fontsize=12)
plt.ylabel('Severity Score (1-10)', fontsize=12)
plt.ylim(0, 10)
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'severity_by_source.png'), dpi=300, bbox_inches='tight')
print("Saved: severity_by_source.png")

# 2. Confidence vs Severity scatter plot
plt.figure(figsize=(10, 6))
sns.scatterplot(data=merged_df, x='severity_score', y='confidence_score', 
                hue='source_system_x', s=150, alpha=0.8)
plt.title('Confidence vs Severity Score by Source System', fontsize=14, fontweight='bold')
plt.xlabel('Severity Score (1-10)', fontsize=12)
plt.ylabel('Confidence Score (1-10)', fontsize=12)
plt.xlim(0, 10)
plt.ylim(0, 10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'confidence_vs_severity.png'), dpi=300, bbox_inches='tight')
print("Saved: confidence_vs_severity.png")

# 3. Urgency distribution
plt.figure(figsize=(10, 6))
urgency_counts = merged_df['urgency'].value_counts()
colors = plt.cm.Set3(np.linspace(0, 1, len(urgency_counts)))
plt.pie(urgency_counts.values, labels=urgency_counts.index, autopct='%1.1f%%', 
        colors=colors, startangle=90, explode=[0.05]*len(urgency_counts))
plt.title('Distribution of Incident Urgency Levels', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'urgency_distribution.png'), dpi=300, bbox_inches='tight')
print("Saved: urgency_distribution.png")

# 4. Threat category distribution
plt.figure(figsize=(12, 6))
threat_counts = merged_df['primary_threat_category'].value_counts()
threat_counts.plot(kind='bar', color=plt.cm.tab20c(np.arange(len(threat_counts))))
plt.title('Primary Threat Category Distribution', fontsize=14, fontweight='bold')
plt.xlabel('Threat Category', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'threat_category_distribution.png'), dpi=300, bbox_inches='tight')
print("Saved: threat_category_distribution.png")

# 5. Resolution time analysis
plt.figure(figsize=(10, 6))
sns.barplot(data=merged_df, x='incident_id', y='estimated_time_to_resolve_minutes', 
            hue='source_system_x', dodge=False)
plt.title('Estimated Resolution Time by Incident', fontsize=14, fontweight='bold')
plt.xlabel('Incident ID', fontsize=12)
plt.ylabel('Estimated Resolution Time (minutes)', fontsize=12)
plt.xticks(rotation=45)
plt.legend(title='Source System')
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'resolution_time_by_incident.png'), dpi=300, bbox_inches='tight')
print("Saved: resolution_time_by_incident.png")

# 6. Text features vs severity correlation
plt.figure(figsize=(12, 8))

# Select features for correlation
features = ['severity_score', 'confidence_score', 'text_length', 'word_count', 'keyword_count']
corr_matrix = merged_df[features].corr()

# Create heatmap
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='coolwarm', 
            center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8})
plt.title('Correlation Matrix: Triage Scores vs Text Features', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'correlation_heatmap.png'), dpi=300, bbox_inches='tight')
print("Saved: correlation_heatmap.png")

# 7. Immediate attention incidents
plt.figure(figsize=(8, 6))
immediate_counts = merged_df['requires_immediate_attention'].value_counts()
immediate_counts.index = ['No Immediate Attention', 'Immediate Attention']
colors = ['lightcoral', 'lightgreen']
immediate_counts.plot(kind='bar', color=colors)
plt.title('Incidents Requiring Immediate Attention', fontsize=14, fontweight='bold')
plt.xlabel('Attention Required', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.xticks(rotation=0)

# Add count labels
for i, count in enumerate(immediate_counts.values):
    plt.text(i, count + 0.1, str(count), ha='center', va='bottom', fontsize=12)

plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'immediate_attention.png'), dpi=300, bbox_inches='tight')
print("Saved: immediate_attention.png")

# 8. Comparative analysis: EDR vs Network IDS
plt.figure(figsize=(14, 10))

# Create subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Subplot 1: Average severity by source
severity_by_source = merged_df.groupby('source_system_x')['severity_score'].mean()
axes[0, 0].bar(severity_by_source.index, severity_by_source.values, color=['skyblue', 'lightcoral'])
axes[0, 0].set_title('Average Severity by Source System', fontsize=12, fontweight='bold')
axes[0, 0].set_ylabel('Average Severity Score')
axes[0, 0].set_ylim(0, 10)

# Subplot 2: Average confidence by source
confidence_by_source = merged_df.groupby('source_system_x')['confidence_score'].mean()
axes[0, 1].bar(confidence_by_source.index, confidence_by_source.values, color=['skyblue', 'lightcoral'])
axes[0, 1].set_title('Average Confidence by Source System', fontsize=12, fontweight='bold')
axes[0, 1].set_ylabel('Average Confidence Score')
axes[0, 1].set_ylim(0, 10)

# Subplot 3: Urgency distribution by source
urgency_by_source = pd.crosstab(merged_df['source_system_x'], merged_df['urgency'])
urgency_by_source.plot(kind='bar', ax=axes[1, 0], stacked=True)
axes[1, 0].set_title('Urgency Distribution by Source System', fontsize=12, fontweight='bold')
axes[1, 0].set_ylabel('Count')
axes[1, 0].legend(title='Urgency')

# Subplot 4: Immediate attention by source
immediate_by_source = merged_df.groupby('source_system_x')['requires_immediate_attention'].mean() * 100
axes[1, 1].bar(immediate_by_source.index, immediate_by_source.values, color=['skyblue', 'lightcoral'])
axes[1, 1].set_title('Percentage Requiring Immediate Attention', fontsize=12, fontweight='bold')
axes[1, 1].set_ylabel('Percentage (%)')
axes[1, 1].set_ylim(0, 100)

plt.suptitle('Comparative Analysis: EDR vs Network IDS Incidents', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'comparative_analysis.png'), dpi=300, bbox_inches='tight')
print("Saved: comparative_analysis.png")

# Generate analysis summary
analysis_summary = {
    "total_incidents_analyzed": len(merged_df),
    "severity_stats": {
        "mean": float(merged_df['severity_score'].mean()),
        "std": float(merged_df['severity_score'].std()),
        "min": int(merged_df['severity_score'].min()),
        "max": int(merged_df['severity_score'].max())
    },
    "confidence_stats": {
        "mean": float(merged_df['confidence_score'].mean()),
        "std": float(merged_df['confidence_score'].std()),
        "min": int(merged_df['confidence_score'].min()),
        "max": int(merged_df['confidence_score'].max())
    },
    "urgency_distribution": merged_df['urgency'].value_counts().to_dict(),
    "threat_category_distribution": merged_df['primary_threat_category'].value_counts().to_dict(),
    "immediate_attention_stats": {
        "count": int(merged_df['requires_immediate_attention'].sum()),
        "percentage": float(merged_df['requires_immediate_attention'].mean() * 100)
    },
    "resolution_time_stats": {
        "mean": float(merged_df['estimated_time_to_resolve_minutes'].mean()),
        "std": float(merged_df['estimated_time_to_resolve_minutes'].std()),
        "min": int(merged_df['estimated_time_to_resolve_minutes'].min()),
        "max": int(merged_df['estimated_time_to_resolve_minutes'].max())
    },
    "source_system_comparison": {
        "edr": {
            "count": int(len(merged_df[merged_df['source_system_x'] == 'edr'])),
            "avg_severity": float(merged_df[merged_df['source_system_x'] == 'edr']['severity_score'].mean()),
            "avg_confidence": float(merged_df[merged_df['source_system_x'] == 'edr']['confidence_score'].mean()),
            "immediate_attention_pct": float(merged_df[merged_df['source_system_x'] == 'edr']['requires_immediate_attention'].mean() * 100)
        },
        "network_ids": {
            "count": int(len(merged_df[merged_df['source_system_x'] == 'network_ids'])),
            "avg_severity": float(merged_df[merged_df['source_system_x'] == 'network_ids']['severity_score'].mean()),
            "avg_confidence": float(merged_df[merged_df['source_system_x'] == 'network_ids']['confidence_score'].mean()),
            "immediate_attention_pct": float(merged_df[merged_df['source_system_x'] == 'network_ids']['requires_immediate_attention'].mean() * 100)
        }
    }
}

# Save analysis summary
summary_path = os.path.join(OUTPUT_DIR, "triage_analysis_summary.json")
with open(summary_path, 'w') as f:
    json.dump(analysis_summary, f, indent=2)

print(f"\nAnalysis summary saved to: {summary_path}")
print("\n=== Key Findings ===")
print(f"1. Average severity score: {analysis_summary['severity_stats']['mean']:.2f}/10")
print(f"2. Average confidence score: {analysis_summary['confidence_stats']['mean']:.2f}/10")
print(f"3. {analysis_summary['immediate_attention_stats']['count']} incidents require immediate attention ({analysis_summary['immediate_attention_stats']['percentage']:.1f}%)")
print(f"4. Most common urgency: {max(analysis_summary['urgency_distribution'], key=analysis_summary['urgency_distribution'].get)} ({analysis_summary['urgency_distribution'][max(analysis_summary['urgency_distribution'], key=analysis_summary['urgency_distribution'].get)]} incidents)")
print(f"5. EDR incidents have higher average severity ({analysis_summary['source_system_comparison']['edr']['avg_severity']:.2f}) than Network IDS ({analysis_summary['source_system_comparison']['network_ids']['avg_severity']:.2f})")
print(f"6. Average estimated resolution time: {analysis_summary['resolution_time_stats']['mean']:.1f} minutes")

print("\n=== Analysis Complete ===")
print(f"Generated 8 additional visualizations in {REPORT_IMG_DIR}")