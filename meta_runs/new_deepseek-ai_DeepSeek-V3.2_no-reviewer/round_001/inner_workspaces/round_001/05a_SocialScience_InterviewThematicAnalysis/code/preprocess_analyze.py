#!/usr/bin/env python3
"""
Preprocessing and analysis of interview excerpts.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from collections import Counter
import re

# Set style for plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

# Create output directories
os.makedirs("outputs", exist_ok=True)
os.makedirs("report/images", exist_ok=True)

def load_data():
    """Load and preprocess the interview excerpts."""
    df = pd.read_csv("../data/interview_excerpts.csv")
    
    # Basic preprocessing
    df['response_length'] = df['response_text'].apply(len)
    df['word_count'] = df['response_text'].apply(lambda x: len(str(x).split()))
    
    # Extract potential themes/keywords (simple approach for quantitative analysis)
    keywords = [
        'app', 'time', 'delay', 'trust', 'safety', 'cost', 'price', 'parking',
        'map', 'route', 'transit', 'drive', 'train', 'bus', 'walk', 'bike',
        'interface', 'crowd', 'night', 'accessibility', 'offline', 'transfer'
    ]
    
    for keyword in keywords:
        df[f'contains_{keyword}'] = df['response_text'].str.lower().str.contains(keyword).astype(int)
    
    return df, keywords

def generate_summary_statistics(df, keywords):
    """Generate summary statistics and save to file."""
    summary = {}
    
    # Cohort counts
    summary['cohort_counts'] = df['cohort'].value_counts().to_dict()
    summary['total_respondents'] = len(df)
    
    # Response length statistics
    summary['response_length_stats'] = {
        'mean': df['response_length'].mean(),
        'median': df['response_length'].median(),
        'std': df['response_length'].std(),
        'min': df['response_length'].min(),
        'max': df['response_length'].max()
    }
    
    summary['word_count_stats'] = {
        'mean': df['word_count'].mean(),
        'median': df['word_count'].median(),
        'std': df['word_count'].std(),
        'min': df['word_count'].min(),
        'max': df['word_count'].max()
    }
    
    # Keyword frequencies
    keyword_freq = {}
    for keyword in keywords:
        keyword_freq[keyword] = df[f'contains_{keyword}'].sum()
    
    summary['keyword_frequencies'] = keyword_freq
    
    # Keyword frequencies by cohort
    keyword_by_cohort = {}
    for cohort in df['cohort'].unique():
        cohort_df = df[df['cohort'] == cohort]
        cohort_freq = {}
        for keyword in keywords:
            cohort_freq[keyword] = cohort_df[f'contains_{keyword}'].sum()
        keyword_by_cohort[cohort] = cohort_freq
    
    summary['keyword_frequencies_by_cohort'] = keyword_by_cohort
    
    # Save summary to JSON
    with open("../outputs/summary_statistics.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    # Also save as text for readability
    with open("../outputs/summary_statistics.txt", "w") as f:
        f.write("=== INTERVIEW EXCERPTS SUMMARY STATISTICS ===\n\n")
        f.write(f"Total respondents: {summary['total_respondents']}\n")
        f.write(f"Cohort distribution:\n")
        for cohort, count in summary['cohort_counts'].items():
            f.write(f"  {cohort}: {count} respondents\n")
        
        f.write("\nResponse length (characters):\n")
        for stat, value in summary['response_length_stats'].items():
            f.write(f"  {stat}: {value:.1f}\n")
        
        f.write("\nWord count:\n")
        for stat, value in summary['word_count_stats'].items():
            f.write(f"  {stat}: {value:.1f}\n")
        
        f.write("\nTop keywords across all respondents:\n")
        sorted_keywords = sorted(summary['keyword_frequencies'].items(), key=lambda x: x[1], reverse=True)
        for keyword, freq in sorted_keywords:
            f.write(f"  {keyword}: {freq} mentions\n")
        
        f.write("\nKeyword frequencies by cohort:\n")
        for cohort, freqs in summary['keyword_frequencies_by_cohort'].items():
            f.write(f"\n  {cohort}:\n")
            sorted_freqs = sorted(freqs.items(), key=lambda x: x[1], reverse=True)
            for keyword, freq in sorted_freqs:
                if freq > 0:
                    f.write(f"    {keyword}: {freq} mentions\n")
    
    return summary

def create_visualizations(df, summary):
    """Create visualizations for the report."""
    
    # 1. Cohort distribution
    plt.figure()
    cohort_counts = df['cohort'].value_counts()
    colors = ['#1f77b4', '#ff7f0e']
    plt.bar(cohort_counts.index, cohort_counts.values, color=colors)
    plt.title('Distribution of Respondents by Cohort', fontsize=14, fontweight='bold')
    plt.xlabel('Cohort', fontsize=12)
    plt.ylabel('Number of Respondents', fontsize=12)
    plt.tight_layout()
    plt.savefig('../report/images/cohort_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Response length by cohort
    plt.figure()
    sns.boxplot(data=df, x='cohort', y='word_count', palette=colors)
    plt.title('Word Count Distribution by Cohort', fontsize=14, fontweight='bold')
    plt.xlabel('Cohort', fontsize=12)
    plt.ylabel('Word Count', fontsize=12)
    plt.tight_layout()
    plt.savefig('../report/images/word_count_by_cohort.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Top keywords heatmap
    plt.figure(figsize=(12, 8))
    
    # Prepare data for heatmap
    keywords = list(summary['keyword_frequencies'].keys())
    cohorts = list(df['cohort'].unique())
    
    heatmap_data = []
    for keyword in keywords:
        row = []
        for cohort in cohorts:
            row.append(summary['keyword_frequencies_by_cohort'][cohort][keyword])
        heatmap_data.append(row)
    
    heatmap_data = np.array(heatmap_data)
    
    # Only show keywords mentioned at least once
    mentioned_keywords = [keywords[i] for i in range(len(keywords)) if heatmap_data[i].sum() > 0]
    mentioned_data = heatmap_data[[i for i in range(len(keywords)) if heatmap_data[i].sum() > 0]]
    
    if len(mentioned_keywords) > 0:
        plt.figure(figsize=(10, max(6, len(mentioned_keywords) * 0.5)))
        sns.heatmap(mentioned_data, annot=True, fmt='d', cmap='YlOrRd', 
                    xticklabels=cohorts, yticklabels=mentioned_keywords,
                    cbar_kws={'label': 'Number of Mentions'})
        plt.title('Keyword Mentions by Cohort', fontsize=14, fontweight='bold')
        plt.xlabel('Cohort', fontsize=12)
        plt.ylabel('Keyword', fontsize=12)
        plt.tight_layout()
        plt.savefig('../report/images/keyword_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    # 4. Top keywords overall
    plt.figure(figsize=(10, 6))
    top_keywords = sorted(summary['keyword_frequencies'].items(), key=lambda x: x[1], reverse=True)[:10]
    keywords_list = [k[0] for k in top_keywords]
    counts_list = [k[1] for k in top_keywords]
    
    bars = plt.barh(keywords_list, counts_list, color='steelblue')
    plt.gca().invert_yaxis()  # Highest count at top
    plt.title('Top 10 Keywords Across All Respondents', fontsize=14, fontweight='bold')
    plt.xlabel('Number of Mentions', fontsize=12)
    plt.ylabel('Keyword', fontsize=12)
    
    # Add count labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                str(int(width)), ha='left', va='center')
    
    plt.tight_layout()
    plt.savefig('../report/images/top_keywords.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Created 4 visualizations in ../report/images/")

def prepare_data_for_llm(df):
    """Prepare data for LLM thematic analysis."""
    # Group responses by cohort
    transit_responses = df[df['cohort'] == 'transit_primary']['response_text'].tolist()
    car_responses = df[df['cohort'] == 'car_primary']['response_text'].tolist()
    
    # Create a structured prompt
    prompt = {
        "transit_primary_responses": transit_responses,
        "car_primary_responses": car_responses,
        "total_transit": len(transit_responses),
        "total_car": len(car_responses)
    }
    
    # Save to JSON for LLM
    with open("../outputs/llm_input_data.json", "w") as f:
        json.dump(prompt, f, indent=2)
    
    return prompt

def main():
    """Main execution function."""
    print("Loading and preprocessing data...")
    df, keywords = load_data()
    
    print("Generating summary statistics...")
    summary = generate_summary_statistics(df, keywords)
    
    print("Creating visualizations...")
    create_visualizations(df, summary)
    
    print("Preparing data for LLM thematic analysis...")
    llm_data = prepare_data_for_llm(df)
    
    print("\n=== SUMMARY ===")
    print(f"Total respondents: {summary['total_respondents']}")
    print(f"Cohort distribution: {summary['cohort_counts']}")
    print(f"Average word count: {summary['word_count_stats']['mean']:.1f}")
    
    # Print top keywords
    print("\nTop 5 keywords:")
    sorted_keywords = sorted(summary['keyword_frequencies'].items(), key=lambda x: x[1], reverse=True)[:5]
    for keyword, freq in sorted_keywords:
        print(f"  {keyword}: {freq} mentions")
    
    print("\nAnalysis complete. Files saved to outputs/ and report/images/")

if __name__ == "__main__":
    main()