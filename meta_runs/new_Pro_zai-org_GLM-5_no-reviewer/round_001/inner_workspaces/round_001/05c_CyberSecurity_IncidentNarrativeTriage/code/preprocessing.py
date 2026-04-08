"""
Preprocessing and Summary Statistics for Incident Narratives
CyberSecurity Incident Narrative Triage
"""

import pandas as pd
import json
import os

# Read the incident narratives data
data_path = '../data/incident_narratives.csv'
df = pd.read_csv(data_path)

print("="*60)
print("INCIDENT NARRATIVES - PREPROCESSING AND SUMMARY")
print("="*60)

# Basic counts
print("\n--- Basic Counts ---")
print(f"Total incidents: {len(df)}")
print(f"\nIncidents by source system:")
source_counts = df['source_system'].value_counts()
print(source_counts.to_string())

# Narrative text analysis
print("\n--- Narrative Text Analysis ---")
df['narrative_length'] = df['narrative_text'].str.len()
df['word_count'] = df['narrative_text'].str.split().str.len()

print(f"\nNarrative length (characters):")
print(f"  Min: {df['narrative_length'].min()}")
print(f"  Max: {df['narrative_length'].max()}")
print(f"  Mean: {df['narrative_length'].mean():.1f}")
print(f"  Median: {df['narrative_length'].median():.1f}")

print(f"\nWord count:")
print(f"  Min: {df['word_count'].min()}")
print(f"  Max: {df['word_count'].max()}")
print(f"  Mean: {df['word_count'].mean():.1f}")
print(f"  Median: {df['word_count'].median():.1f}")

# Statistics by source system
print("\n--- Statistics by Source System ---")
for source in df['source_system'].unique():
    subset = df[df['source_system'] == source]
    print(f"\n{source.upper()}:")
    print(f"  Count: {len(subset)}")
    print(f"  Avg narrative length: {subset['narrative_length'].mean():.1f} chars")
    print(f"  Avg word count: {subset['word_count'].mean():.1f} words")

# Word frequency analysis
print("\n--- Word Frequency Analysis ---")
all_words = ' '.join(df['narrative_text'].str.lower()).split()
# Remove common punctuation
import string
all_words = [word.strip(string.punctuation) for word in all_words]
all_words = [word for word in all_words if word and len(word) > 2]

from collections import Counter
word_freq = Counter(all_words)
print("\nTop 15 most common words:")
for word, count in word_freq.most_common(15):
    print(f"  {word}: {count}")

# Save summary statistics to JSON
summary = {
    'total_incidents': len(df),
    'source_system_counts': source_counts.to_dict(),
    'narrative_length_stats': {
        'min': int(df['narrative_length'].min()),
        'max': int(df['narrative_length'].max()),
        'mean': float(df['narrative_length'].mean()),
        'median': float(df['narrative_length'].median())
    },
    'word_count_stats': {
        'min': int(df['word_count'].min()),
        'max': int(df['word_count'].max()),
        'mean': float(df['word_count'].mean()),
        'median': float(df['word_count'].median())
    },
    'incidents': df.to_dict('records')
}

os.makedirs('../outputs', exist_ok=True)
with open('../outputs/summary_stats.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\n" + "="*60)
print("Summary saved to outputs/summary_stats.json")
print("="*60)
