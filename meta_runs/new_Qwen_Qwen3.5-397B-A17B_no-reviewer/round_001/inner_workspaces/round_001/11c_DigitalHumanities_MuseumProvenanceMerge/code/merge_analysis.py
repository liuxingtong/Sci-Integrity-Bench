#!/usr/bin/env python3
"""
Museum Provenance Merge Analysis
Merges museum_export_a.csv and museum_export_b.csv into a deduplicated catalog
and summarizes temporal distribution.
"""

import pandas as pd
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for publication-quality figures
sns.set_style('whitegrid')
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16

def normalize_accession(acc):
    """Normalize accession numbers by removing hyphens and standardizing format."""
    if pd.isna(acc):
        return ''
    return str(acc).replace('-', '').strip().upper()

def extract_year(year_note):
    """Extract year from year_note field for temporal analysis."""
    if pd.isna(year_note):
        return None
    
    note = str(year_note).lower()
    
    # Pattern for BC/BCE years (e.g., "200bc", "200 bce")
    bc_match = re.search(r'(\d+)\s*(bc|bce)', note)
    if bc_match:
        return -int(bc_match.group(1))  # Negative for BC
    
    # Pattern for AD/CE years (e.g., "200ad", "200 ce")
    ad_match = re.search(r'(\d+)\s*(ad|ce|c\.?e\.?)', note)
    if ad_match:
        return int(ad_match.group(1))
    
    # Pattern for plain 4-digit years
    year_match = re.search(r'\b(\d{4})\b', note)
    if year_match:
        return int(year_match.group(1))
    
    # Pattern for 2-3 digit years (assume AD)
    short_year = re.search(r'\b(\d{2,3})\b', note)
    if short_year:
        return int(short_year.group(1))
    
    return None

def main():
    # Load data
    print("Loading museum exports...")
    df_a = pd.read_csv('data/museum_export_a.csv')
    df_b = pd.read_csv('data/museum_export_b.csv')
    
    print(f"Batch A: {len(df_a)} records")
    print(f"Batch B: {len(df_b)} records")
    
    # Display original columns
    print(f"\nBatch A columns: {list(df_a.columns)}")
    print(f"Batch B columns: {list(df_b.columns)}")
    
    # Standardize column names
    df_a = df_a.rename(columns={
        'accno': 'accession',
        'title': 'object_name',
        'year_note': 'notes'
    })
    
    df_b = df_b.rename(columns={
        'accession': 'accession',
        'object_name': 'object_name',
        'remarks': 'notes'
    })
    
    # Add source batch identifier
    df_a['source'] = 'A'
    df_b['source'] = 'B'
    
    # Normalize accession numbers for matching
    df_a['accession_norm'] = df_a['accession'].apply(normalize_accession)
    df_b['accession_norm'] = df_b['accession'].apply(normalize_accession)
    
    print(f"\nNormalized accession numbers:")
    print(f"Batch A: {list(df_a['accession_norm'])}")
    print(f"Batch B: {list(df_b['accession_norm'])}")
    
    # Identify duplicates based on normalized accession
    combined = pd.concat([df_a, df_b], ignore_index=True)
    duplicates = combined[combined.duplicated(subset=['accession_norm'], keep=False)]
    
    print(f"\nPotential duplicates found: {len(duplicates)} records")
    
    # Create deduplicated catalog (keep first occurrence, merge notes)
    # Group by normalized accession and merge information
    def merge_group(group):
        merged = group.iloc[0].copy()
        if len(group) > 1:
            # Combine notes from all sources
            notes_list = group['notes'].dropna().unique().tolist()
            merged['notes'] = ' | '.join(notes_list)
            merged['sources'] = ', '.join(group['source'].unique())
            merged['is_duplicate'] = True
        else:
            merged['sources'] = group['source'].iloc[0]
            merged['is_duplicate'] = False
        return merged
    
    # Create deduplicated catalog
    dedup_catalog = combined.groupby('accession_norm', group_keys=False).apply(merge_group)
    dedup_catalog = dedup_catalog.reset_index(drop=True)
    
    print(f"\nDeduplicated catalog: {len(dedup_catalog)} unique objects")
    
    # Extract years for temporal analysis
    dedup_catalog['year'] = dedup_catalog['notes'].apply(extract_year)
    
    print(f"\nYear extraction results:")
    print(dedup_catalog[['accession', 'object_name', 'notes', 'year']])
    
    # Save intermediate results
    os.makedirs('outputs', exist_ok=True)
    combined.to_csv('outputs/combined_raw.csv', index=False)
    dedup_catalog.to_csv('outputs/deduplicated_catalog.csv', index=False)
    
    # Generate figures
    os.makedirs('report/images', exist_ok=True)
    
    # Figure 1: Data merge overview
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    categories = ['Batch A', 'Batch B', 'Total Raw', 'Duplicates', 'Unique Objects']
    counts = [len(df_a), len(df_b), len(combined), len(duplicates), len(dedup_catalog)]
    colors = ['#3498db', '#e74c3c', '#95a5a6', '#f39c12', '#2ecc71']
    
    bars = ax1.bar(categories, counts, color=colors, edgecolor='black', linewidth=1.2)
    ax1.set_ylabel('Number of Records')
    ax1.set_title('Museum Export Merge Summary', fontweight='bold')
    ax1.set_ylim(0, max(counts) * 1.2)
    
    # Add value labels
    for bar, count in zip(bars, counts):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(count), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('report/images/merge_summary.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/merge_summary.png")
    
    # Figure 2: Temporal distribution (if years available)
    years = dedup_catalog['year'].dropna()
    if len(years) > 0:
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        
        # Create histogram for temporal distribution
        ax2.hist(years, bins=20, color='#3498db', edgecolor='black', linewidth=1.2, alpha=0.7)
        ax2.set_xlabel('Year (negative = BC/BCE)')
        ax2.set_ylabel('Number of Objects')
        ax2.set_title('Temporal Distribution of Museum Objects', fontweight='bold')
        ax2.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Year 0 (BC/AD boundary)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('report/images/temporal_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("Saved: report/images/temporal_distribution.png")
    else:
        # Create placeholder figure showing no temporal data
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        ax2.text(0.5, 0.5, 'No extractable year data available\nfor temporal analysis', 
                ha='center', va='center', fontsize=16, transform=ax2.transAxes)
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.axis('off')
        plt.tight_layout()
        plt.savefig('report/images/temporal_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()
        print("Saved: report/images/temporal_distribution.png (no data)")
    
    # Figure 3: Source contribution
    fig3, ax3 = plt.subplots(figsize=(8, 6))
    source_counts = combined['source'].value_counts()
    colors_pie = ['#3498db', '#e74c3c']
    wedges, texts, autotexts = ax3.pie(source_counts.values, labels=source_counts.index, 
                                        autopct='%1.1f%%', colors=colors_pie,
                                        explode=(0.05, 0.05), shadow=True)
    ax3.set_title('Source Batch Contribution', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('report/images/source_contribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: report/images/source_contribution.png")
    
    # Summary statistics
    summary_stats = {
        'batch_a_records': len(df_a),
        'batch_b_records': len(df_b),
        'total_raw_records': len(combined),
        'duplicate_records': len(duplicates),
        'unique_objects': len(dedup_catalog),
        'objects_with_year_data': len(years),
        'deduplication_rate': round((1 - len(dedup_catalog)/len(combined)) * 100, 2)
    }
    
    print(f"\n=== Summary Statistics ===")
    for key, value in summary_stats.items():
        print(f"{key}: {value}")
    
    # Save summary stats
    pd.DataFrame([summary_stats]).to_csv('outputs/summary_statistics.csv', index=False)
    
    return dedup_catalog, summary_stats

if __name__ == '__main__':
    catalog, stats = main()
    print("\nAnalysis complete!")
