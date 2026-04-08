"""
Preprocessing script for CyberSecurity Incident Narrative Triage
Step 1: Reproducible preprocessing + scripted summaries
"""
import pandas as pd
import json
import re
from collections import Counter
import os

# Set random seed for reproducibility
RANDOM_SEED = 42

def load_data(filepath):
    """Load incident narratives data."""
    df = pd.read_csv(filepath)
    return df

def preprocess_narratives(df):
    """Preprocess narrative text: clean, tokenize, extract features."""
    df = df.copy()
    
    # Basic text cleaning
    df['narrative_clean'] = df['narrative_text'].str.lower()
    df['narrative_clean'] = df['narrative_clean'].str.replace(r'[^\w\s]', ' ', regex=True)
    
    # Text length features
    df['char_count'] = df['narrative_text'].str.len()
    df['word_count'] = df['narrative_text'].str.split().str.len()
    
    # Extract key entities using regex patterns
    df['has_powershell'] = df['narrative_text'].str.contains('PowerShell|powershell', case=False, na=False)
    df['has_ransomware'] = df['narrative_text'].str.contains('ransomware|ransom', case=False, na=False)
    df['has_dns'] = df['narrative_text'].str.contains('DNS|dns', case=False, na=False)
    df['has_smb'] = df['narrative_text'].str.contains('SMB|smb', case=False, na=False)
    df['has_tls'] = df['narrative_text'].str.contains('TLS|tls|SSL|ssl', case=False, na=False)
    df['has_false_positive'] = df['narrative_text'].str.contains('false positive|closed', case=False, na=False)
    
    # Extract hostnames (patterns like XXX-NNN)
    df['hostnames'] = df['narrative_text'].apply(lambda x: re.findall(r'\b[A-Z]{2,6}-\d{2,4}\b', x))
    df['hostname_count'] = df['hostnames'].str.len()
    
    # Extract IP-like patterns
    df['ip_mentions'] = df['narrative_text'].str.contains(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', case=False, na=False)
    
    return df

def generate_summaries(df):
    """Generate scripted summaries: counts, lengths, frequencies."""
    summaries = {}
    
    # Basic counts
    summaries['total_incidents'] = len(df)
    summaries['source_system_counts'] = df['source_system'].value_counts().to_dict()
    
    # Length statistics
    summaries['char_count_stats'] = df['char_count'].describe().to_dict()
    summaries['word_count_stats'] = df['word_count'].describe().to_dict()
    
    # Threat indicator frequencies
    threat_indicators = ['has_powershell', 'has_ransomware', 'has_dns', 'has_smb', 'has_tls', 'has_false_positive']
    summaries['threat_indicator_counts'] = {col: int(df[col].sum()) for col in threat_indicators}
    
    # Source system breakdown
    summaries['by_source'] = {}
    for source in df['source_system'].unique():
        source_df = df[df['source_system'] == source]
        summaries['by_source'][source] = {
            'count': len(source_df),
            'avg_word_count': float(source_df['word_count'].mean()),
            'avg_char_count': float(source_df['char_count'].mean()),
            'threat_indicators': {col: int(source_df[col].sum()) for col in threat_indicators}
        }
    
    # Word frequency analysis
    all_words = ' '.join(df['narrative_clean']).split()
    word_freq = Counter(all_words)
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'per', 'no', 'not'}
    filtered_freq = {word: count for word, count in word_freq.items() if word not in stop_words and len(word) > 2}
    summaries['top_words'] = dict(Counter(filtered_freq).most_common(20))
    
    return summaries

def main():
    # Load data
    data_path = 'data/incident_narratives.csv'
    df = load_data(data_path)
    print(f"Loaded {len(df)} incidents")
    
    # Preprocess
    df_processed = preprocess_narratives(df)
    
    # Generate summaries
    summaries = generate_summaries(df_processed)
    
    # Save processed data
    os.makedirs('outputs', exist_ok=True)
    df_processed.to_csv('outputs/incidents_processed.csv', index=False)
    
    # Save summaries
    with open('outputs/summaries.json', 'w') as f:
        json.dump(summaries, f, indent=2)
    
    print("Preprocessing complete. Saved to outputs/")
    print(f"\nSummary Statistics:")
    print(f"Total incidents: {summaries['total_incidents']}")
    print(f"Source systems: {summaries['source_system_counts']}")
    print(f"Average word count: {summaries['word_count_stats']['mean']:.1f}")
    
    return df_processed, summaries

if __name__ == '__main__':
    main()
