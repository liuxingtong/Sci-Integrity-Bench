#!/usr/bin/env python3
"""
Preprocessing and scripted summaries for incident narratives.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from collections import Counter
import re

# Set up paths
DATA_PATH = "../data/incident_narratives.csv"
OUTPUT_DIR = "../outputs"
REPORT_IMG_DIR = "../report/images"

# Create directories if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_IMG_DIR, exist_ok=True)

# Set plotting style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("Loading data...")
df = pd.read_csv(DATA_PATH)
print(f"Data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print("\nFirst few rows:")
print(df.head())

# Basic data quality checks
print("\n=== Data Quality Checks ===")
print(f"Missing values:\n{df.isnull().sum()}")
print(f"\nSource system distribution:\n{df['source_system'].value_counts()}")
print(f"\nUnique incident IDs: {df['incident_id'].nunique()}")

# Text preprocessing and feature extraction
print("\n=== Text Analysis ===")

# Calculate text length features
df['text_length'] = df['narrative_text'].str.len()
df['word_count'] = df['narrative_text'].str.split().str.len()
df['sentence_count'] = df['narrative_text'].str.count(r'[.!?]+')

# Extract common security-related keywords
security_keywords = [
    'blocked', 'reset', 'disabled', 'reimage', 'sinkhole',
    'false positive', 'closed', 'WAF', 'SOC', 'firewall',
    'ransomware', 'tunneling', 'exfil', 'payload', 'encoded',
    'suspicious', 'unusual', 'failed', 'admin', 'logins'
]

for keyword in security_keywords:
    df[f'contains_{keyword.replace(" ", "_")}'] = df['narrative_text'].str.lower().str.contains(keyword.lower()).astype(int)

# Calculate keyword frequency
df['keyword_count'] = 0
for keyword in security_keywords:
    df['keyword_count'] += df['narrative_text'].str.lower().str.count(keyword.lower())

print("\nText statistics:")
print(df[['text_length', 'word_count', 'sentence_count', 'keyword_count']].describe())

print("\nText statistics by source system:")
print(df.groupby('source_system')[['text_length', 'word_count', 'sentence_count', 'keyword_count']].agg(['mean', 'std', 'min', 'max']))

# Save processed data
processed_path = os.path.join(OUTPUT_DIR, "processed_incidents.csv")
df.to_csv(processed_path, index=False)
print(f"\nProcessed data saved to: {processed_path}")

# Generate summary statistics
summary_stats = {
    "total_incidents": len(df),
    "edr_count": len(df[df['source_system'] == 'edr']),
    "network_ids_count": len(df[df['source_system'] == 'network_ids']),
    "avg_text_length": df['text_length'].mean(),
    "avg_word_count": df['word_count'].mean(),
    "avg_sentence_count": df['sentence_count'].mean(),
    "avg_keyword_count": df['keyword_count'].mean(),
    "most_common_keywords": {},
    "source_system_stats": {}
}

# Calculate most common keywords across all narratives
all_text = ' '.join(df['narrative_text'].str.lower())
keyword_freq = {}
for keyword in security_keywords:
    count = all_text.count(keyword.lower())
    if count > 0:
        keyword_freq[keyword] = count

summary_stats['most_common_keywords'] = dict(sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10])

# Calculate statistics by source system
for source in df['source_system'].unique():
    source_df = df[df['source_system'] == source]
    summary_stats['source_system_stats'][source] = {
        "count": len(source_df),
        "avg_text_length": source_df['text_length'].mean(),
        "avg_word_count": source_df['word_count'].mean(),
        "avg_keyword_count": source_df['keyword_count'].mean()
    }

# Save summary statistics
summary_path = os.path.join(OUTPUT_DIR, "summary_statistics.json")
with open(summary_path, 'w') as f:
    json.dump(summary_stats, f, indent=2)
print(f"Summary statistics saved to: {summary_path}")

print("\n=== Summary Statistics ===")
print(f"Total incidents: {summary_stats['total_incidents']}")
print(f"EDR incidents: {summary_stats['edr_count']}")
print(f"Network IDS incidents: {summary_stats['network_ids_count']}")
print(f"Average text length: {summary_stats['avg_text_length']:.1f} characters")
print(f"Average word count: {summary_stats['avg_word_count']:.1f} words")
print(f"Average sentence count: {summary_stats['avg_sentence_count']:.1f} sentences")
print(f"Average keyword count: {summary_stats['avg_keyword_count']:.1f} keywords")
print(f"\nTop 5 most common keywords: {list(summary_stats['most_common_keywords'].keys())[:5]}")

# Generate visualizations
print("\n=== Generating Visualizations ===")

# 1. Distribution of incidents by source system
plt.figure(figsize=(10, 6))
ax = sns.countplot(data=df, x='source_system', order=df['source_system'].value_counts().index)
plt.title('Distribution of Incidents by Source System', fontsize=14, fontweight='bold')
plt.xlabel('Source System', fontsize=12)
plt.ylabel('Count', fontsize=12)

# Add count labels on bars
for p in ax.patches:
    ax.annotate(f'{p.get_height()}', 
                (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha='center', va='bottom', fontsize=11)

plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'incident_distribution_by_source.png'), dpi=300, bbox_inches='tight')
print("Saved: incident_distribution_by_source.png")

# 2. Text length distribution by source system
plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x='source_system', y='text_length')
plt.title('Text Length Distribution by Source System', fontsize=14, fontweight='bold')
plt.xlabel('Source System', fontsize=12)
plt.ylabel('Text Length (characters)', fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'text_length_by_source.png'), dpi=300, bbox_inches='tight')
print("Saved: text_length_by_source.png")

# 3. Word count distribution
plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='word_count', hue='source_system', kde=True, bins=10)
plt.title('Word Count Distribution by Source System', fontsize=14, fontweight='bold')
plt.xlabel('Word Count', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'word_count_distribution.png'), dpi=300, bbox_inches='tight')
print("Saved: word_count_distribution.png")

# 4. Keyword frequency heatmap
plt.figure(figsize=(12, 8))
keyword_cols = [col for col in df.columns if col.startswith('contains_')]
keyword_matrix = df[keyword_cols].sum().sort_values(ascending=False).head(15)

# Extract keyword names from column names
keyword_names = [col.replace('contains_', '').replace('_', ' ') for col in keyword_matrix.index]

plt.barh(keyword_names, keyword_matrix.values)
plt.title('Top 15 Security Keywords in Incident Narratives', fontsize=14, fontweight='bold')
plt.xlabel('Frequency', fontsize=12)
plt.ylabel('Keyword', fontsize=12)
plt.gca().invert_yaxis()  # Highest frequency at top
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'keyword_frequency.png'), dpi=300, bbox_inches='tight')
print("Saved: keyword_frequency.png")

# 5. Scatter plot: text length vs keyword count
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='text_length', y='keyword_count', hue='source_system', s=100)
plt.title('Text Length vs Keyword Count by Source System', fontsize=14, fontweight='bold')
plt.xlabel('Text Length (characters)', fontsize=12)
plt.ylabel('Keyword Count', fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(REPORT_IMG_DIR, 'text_vs_keywords.png'), dpi=300, bbox_inches='tight')
print("Saved: text_vs_keywords.png")

print("\n=== Preprocessing Complete ===")
print(f"Generated {len(keyword_cols)} keyword features")
print(f"Created 5 visualizations in {REPORT_IMG_DIR}")
print(f"Saved processed data to {processed_path}")
print(f"Saved summary statistics to {summary_path}")