#!/usr/bin/env python3
"""
Preprocessing and analysis script for cybersecurity incident narratives.
Performs reproducible preprocessing and generates scripted summaries.
"""

import pandas as pd
import numpy as np
import re
import json
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import os

# Set style for better visualizations
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


def load_data(filepath: str) -> pd.DataFrame:
    """Load incident narratives data."""
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df)} incidents from {filepath}")
    print(f"Columns: {df.columns.tolist()}")
    return df


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess the incident narratives data."""
    # Create a copy to avoid modifying original
    df_processed = df.copy()
    
    # Calculate narrative length
    df_processed['narrative_length'] = df_processed['narrative_text'].apply(len)
    
    # Calculate word count
    df_processed['word_count'] = df_processed['narrative_text'].apply(lambda x: len(str(x).split()))
    
    # Extract key terms (simplified approach)
    security_terms = [
        'blocked', 'reset', 'disabled', 'reimage', 'sinkhole', 
        'false positive', 'closed', 'WAF', 'SOC', 'firewall',
        'ransomware', 'tunneling', 'exfil', 'payload', 'encoded',
        'suspicious', 'unusual', 'failed', 'spike', 'newly registered'
    ]
    
    def extract_terms(text):
        text_lower = str(text).lower()
        found_terms = [term for term in security_terms if term in text_lower]
        return found_terms
    
    df_processed['extracted_terms'] = df_processed['narrative_text'].apply(extract_terms)
    df_processed['term_count'] = df_processed['extracted_terms'].apply(len)
    
    # Extract severity indicators
    severity_indicators = {
        'high': ['ransomware', 'encoded payload', 'tunneling', 'exfil'],
        'medium': ['suspicious', 'unusual', 'failed logins', 'newly registered'],
        'low': ['false positive', 'closed', 'review requested']
    }
    
    def estimate_severity(text):
        text_lower = str(text).lower()
        for severity, indicators in severity_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return severity
        return 'unknown'
    
    df_processed['estimated_severity'] = df_processed['narrative_text'].apply(estimate_severity)
    
    return df_processed


def generate_summaries(df: pd.DataFrame) -> Dict:
    """Generate comprehensive summaries of the data."""
    summaries = {}
    
    # Basic counts
    summaries['total_incidents'] = len(df)
    summaries['by_source'] = df['source_system'].value_counts().to_dict()
    summaries['by_severity'] = df['estimated_severity'].value_counts().to_dict()
    
    # Narrative statistics
    summaries['narrative_stats'] = {
        'mean_length': float(df['narrative_length'].mean()),
        'median_length': float(df['narrative_length'].median()),
        'min_length': int(df['narrative_length'].min()),
        'max_length': int(df['narrative_length'].max()),
        'std_length': float(df['narrative_length'].std()),
        'mean_word_count': float(df['word_count'].mean()),
        'median_word_count': float(df['word_count'].median()),
    }
    
    # Term frequency analysis
    all_terms = []
    for terms in df['extracted_terms']:
        all_terms.extend(terms)
    
    term_counts = Counter(all_terms)
    summaries['top_terms'] = dict(term_counts.most_common(10))
    
    # Cross-tabulation
    cross_tab = pd.crosstab(df['source_system'], df['estimated_severity'])
    summaries['source_severity_cross'] = cross_tab.to_dict()
    
    return summaries


def create_visualizations(df: pd.DataFrame, output_dir: str):
    """Create visualizations and save to output directory."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Figure 1: Distribution of incidents by source system
    plt.figure(figsize=(10, 6))
    source_counts = df['source_system'].value_counts()
    bars = plt.bar(source_counts.index, source_counts.values, color=['skyblue', 'lightcoral'])
    plt.title('Distribution of Incidents by Source System', fontsize=16, fontweight='bold')
    plt.xlabel('Source System', fontsize=12)
    plt.ylabel('Number of Incidents', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                 f'{int(height)}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure1_source_distribution.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 2: Narrative length distribution
    plt.figure(figsize=(10, 6))
    plt.hist(df['narrative_length'], bins=15, edgecolor='black', alpha=0.7, color='lightgreen')
    plt.title('Distribution of Narrative Length (Characters)', fontsize=16, fontweight='bold')
    plt.xlabel('Narrative Length (characters)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(alpha=0.3)
    plt.axvline(df['narrative_length'].mean(), color='red', linestyle='--', 
                label=f'Mean: {df["narrative_length"].mean():.1f}')
    plt.axvline(df['narrative_length'].median(), color='blue', linestyle=':', 
                label=f'Median: {df["narrative_length"].median():.1f}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure2_narrative_length.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 3: Severity distribution by source system
    plt.figure(figsize=(10, 6))
    severity_by_source = pd.crosstab(df['source_system'], df['estimated_severity'])
    severity_by_source.plot(kind='bar', stacked=True, ax=plt.gca())
    plt.title('Severity Distribution by Source System', fontsize=16, fontweight='bold')
    plt.xlabel('Source System', fontsize=12)
    plt.ylabel('Number of Incidents', fontsize=12)
    plt.legend(title='Estimated Severity')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure3_severity_by_source.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 4: Word count vs narrative length
    plt.figure(figsize=(10, 6))
    plt.scatter(df['word_count'], df['narrative_length'], alpha=0.7, color='purple', s=100)
    plt.title('Word Count vs Narrative Length', fontsize=16, fontweight='bold')
    plt.xlabel('Word Count', fontsize=12)
    plt.ylabel('Narrative Length (characters)', fontsize=12)
    
    # Add regression line
    z = np.polyfit(df['word_count'], df['narrative_length'], 1)
    p = np.poly1d(z)
    plt.plot(df['word_count'], p(df['word_count']), "r--", alpha=0.8, label='Trend line')
    
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'figure4_word_vs_length.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 5: Term frequency
    all_terms = []
    for terms in df['extracted_terms']:
        all_terms.extend(terms)
    
    term_counts = Counter(all_terms)
    top_terms = term_counts.most_common(8)
    
    if top_terms:
        plt.figure(figsize=(10, 6))
        terms, counts = zip(*top_terms)
        bars = plt.barh(terms, counts, color='orange')
        plt.title('Top Security Terms in Incident Narratives', fontsize=16, fontweight='bold')
        plt.xlabel('Frequency', fontsize=12)
        plt.ylabel('Security Term', fontsize=12)
        plt.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                     f'{int(width)}', ha='left', va='center')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'figure5_term_frequency.png'), dpi=300, bbox_inches='tight')
        plt.close()
    
    print(f"Visualizations saved to {output_dir}")


def save_summaries(summaries: Dict, output_path: str):
    """Save summaries to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(summaries, f, indent=2)
    print(f"Summaries saved to {output_path}")


def main():
    """Main execution function."""
    # Paths
    data_path = "../data/incident_narratives.csv"
    output_dir = "../outputs"
    figures_dir = "../report/images"
    
    # Load data
    print("Loading data...")
    df = load_data(data_path)
    
    # Display sample
    print("\nFirst few rows:")
    print(df.head())
    
    # Preprocess data
    print("\nPreprocessing data...")
    df_processed = preprocess_data(df)
    
    # Display processed data
    print("\nProcessed data (first few rows):")
    print(df_processed.head())
    
    # Generate summaries
    print("\nGenerating summaries...")
    summaries = generate_summaries(df_processed)
    
    # Print key summaries
    print("\n=== KEY SUMMARY STATISTICS ===")
    print(f"Total incidents: {summaries['total_incidents']}")
    print(f"By source system: {summaries['by_source']}")
    print(f"By estimated severity: {summaries['by_severity']}")
    print(f"\nNarrative statistics:")
    for key, value in summaries['narrative_stats'].items():
        print(f"  {key}: {value}")
    print(f"\nTop security terms: {summaries['top_terms']}")
    
    # Save summaries
    summaries_path = os.path.join(output_dir, "data_summaries.json")
    save_summaries(summaries, summaries_path)
    
    # Save processed data
    processed_path = os.path.join(output_dir, "processed_incidents.csv")
    df_processed.to_csv(processed_path, index=False)
    print(f"Processed data saved to {processed_path}")
    
    # Create visualizations
    print("\nCreating visualizations...")
    create_visualizations(df_processed, figures_dir)
    
    print("\nPreprocessing and analysis complete!")


if __name__ == "__main__":
    main()