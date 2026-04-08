#!/usr/bin/env python3
"""
Preprocessing script for CyberSecurity Incident Narrative Triage
Generates summary statistics and prepares data for Gemini API analysis
"""

import pandas as pd
import json
import os

def main():
    # Load data
    df = pd.read_csv('data/incident_narratives.csv')
    
    # Basic statistics
    print("=== Data Overview ===")
    print(f"Total incidents: {len(df)}")
    print(f"\nSource system distribution:")
    print(df['source_system'].value_counts())
    
    # Text length analysis
    df['narrative_length'] = df['narrative_text'].apply(len)
    df['word_count'] = df['narrative_text'].apply(lambda x: len(x.split()))
    
    print(f"\n=== Narrative Length Statistics ===")
    print(f"Mean length (chars): {df['narrative_length'].mean():.2f}")
    print(f"Std length (chars): {df['narrative_length'].std():.2f}")
    print(f"Min length (chars): {df['narrative_length'].min()}")
    print(f"Max length (chars): {df['narrative_length'].max()}")
    
    print(f"\n=== Word Count Statistics ===")
    print(f"Mean word count: {df['word_count'].mean():.2f}")
    print(f"Std word count: {df['word_count'].std():.2f}")
    
    # Save summary statistics
    summary = {
        'total_incidents': len(df),
        'source_system_counts': df['source_system'].value_counts().to_dict(),
        'narrative_length_stats': {
            'mean': float(df['narrative_length'].mean()),
            'std': float(df['narrative_length'].std()),
            'min': int(df['narrative_length'].min()),
            'max': int(df['narrative_length'].max())
        },
        'word_count_stats': {
            'mean': float(df['word_count'].mean()),
            'std': float(df['word_count'].std()),
            'min': int(df['word_count'].min()),
            'max': int(df['word_count'].max())
        }
    }
    
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/summary_stats.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to outputs/summary_stats.json")
    
    # Save preprocessed data
    df.to_csv('outputs/preprocessed_data.csv', index=False)
    print(f"Preprocessed data saved to outputs/preprocessed_data.csv")
    
    return df

if __name__ == '__main__':
    main()
