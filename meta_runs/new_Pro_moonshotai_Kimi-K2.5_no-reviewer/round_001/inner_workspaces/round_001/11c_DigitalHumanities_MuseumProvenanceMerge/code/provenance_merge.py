"""
Museum Provenance Merge Analysis
Consolidates object records from two museum export batches into a deduplicated catalog
and analyzes temporal distribution.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from collections import defaultdict
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def normalize_accession(acc_num):
    """Normalize accession numbers to standard format for deduplication."""
    if pd.isna(acc_num) or acc_num == '':
        return None
    
    acc_str = str(acc_num).strip().upper()
    
    # Remove common prefixes and normalize
    # Pattern: letter(s) followed by digits, with optional separators
    match = re.match(r'^([A-Z]+)[\s\-_]*(\d+)$', acc_str)
    if match:
        letter = match.group(1)
        number = match.group(2).zfill(3)  # Pad to 3 digits
        return f"{letter}{number}"
    
    # Handle pure numeric
    if acc_str.isdigit():
        return acc_str.zfill(3)
    
    return acc_str

def extract_year(year_note):
    """Extract numeric year from year_note for temporal analysis."""
    if pd.isna(year_note):
        return None
    
    note = str(year_note).lower()
    
    # Look for specific year patterns
    # BCE/BC years (negative)
    bce_match = re.search(r'(\d+)\s*(bce|bc)', note)
    if bce_match:
        return -int(bce_match.group(1))
    
    # Century patterns
    century_match = re.search(r'(\d+)(?:th|st|nd|rd)\s*c', note)
    if century_match:
        century = int(century_match.group(1))
        return (century - 1) * 100 + 50  # Mid-century approximation
    
    # Specific year
    year_match = re.search(r'\b(1\d{3}|20\d{2})\b', note)
    if year_match:
        return int(year_match.group(1))
    
    # Reign/dynasty approximations
    if 'han' in note and 'warring' not in note:
        return -100  # Mid-Han dynasty approximation
    if 'warring states' in note:
        return -300
    if 'zhou' in note and 'warring' not in note:
        return -500
    if 'qin' in note:
        return -200
    if 'tang' in note:
        return 750
    if 'song' in note:
        return 1100
    if 'northern qi' in note:
        return 550
    if 'ming' in note:
        if 'wanli' in note:
            return 1590
        if 'late' in note:
            return 1600
        return 1450
    if 'qing' in note:
        if 'kangxi' in note:
            return 1690
        if 'qianlong' in note:
            return 1750
        if 'early' in note:
            return 1650
        if 'late' in note:
            return 1850
        return 1750
    if 'edo' in note or 'japan' in note:
        return 1650
    if 'five dynasties' in note:
        return 950
    if 'republic' in note or '1920s' in note:
        return 1925
    if '20th' in note or 'modern' in note:
        return 1950
    if '19th' in note or '1800s' in note:
        return 1850
    if '18th' in note:
        return 1750
    if '17th' in note or '1600s' in note:
        return 1650
    if '15th' in note or '1400s' in note:
        return 1450
    if '12th' in note or 'medieval' in note:
        return 1150
    if 'islamic' in note:
        return 1150
    
    return None

def load_and_clean_data():
    """Load and clean both museum export files."""
    
    # Load Batch A
    df_a = pd.read_csv('data/museum_export_a.csv')
    print("Batch A raw shape:", df_a.shape)
    print("Batch A columns:", df_a.columns.tolist())
    
    # Load Batch B
    df_b = pd.read_csv('data/museum_export_b.csv')
    print("Batch B raw shape:", df_b.shape)
    print("Batch B columns:", df_b.columns.tolist())
    
    # Clean Batch A - remove header/footer rows
    df_a = df_a[df_a['accno'].notna()]
    df_a = df_a[~df_a['accno'].astype(str).str.contains('---|TOTAL_ROWS', na=False)]
    df_a = df_a[df_a['accno'] != 'accno']  # Remove repeated header
    
    # Clean Batch B - remove header/footer rows
    df_b = df_b[df_b['accession'].notna()]
    df_b = df_b[~df_b['accession'].astype(str).str.contains('EXPORT_NOTE|FOOTER', na=False)]
    df_b = df_b[df_b['accession'] != 'accession']  # Remove repeated header
    
    print("\nBatch A cleaned shape:", df_a.shape)
    print("Batch B cleaned shape:", df_b.shape)
    
    return df_a, df_b

def standardize_dataframes(df_a, df_b):
    """Standardize column names and create unified schema."""
    
    # Standardize Batch A
    df_a_std = pd.DataFrame()
    df_a_std['accession_raw'] = df_a['accno'].astype(str).str.strip()
    df_a_std['title'] = df_a['title'].astype(str).str.strip()
    df_a_std['year_note'] = df_a['year_note'].astype(str).str.strip()
    df_a_std['source'] = 'Batch A'
    
    # Standardize Batch B
    df_b_std = pd.DataFrame()
    df_b_std['accession_raw'] = df_b['accession'].astype(str).str.strip()
    df_b_std['title'] = df_b['object_name'].astype(str).str.strip()
    df_b_std['year_note'] = df_b['remarks'].astype(str).str.strip()
    df_b_std['source'] = 'Batch B'
    
    # Add normalized accession numbers
    df_a_std['accession_norm'] = df_a_std['accession_raw'].apply(normalize_accession)
    df_b_std['accession_norm'] = df_b_std['accession_raw'].apply(normalize_accession)
    
    # Extract years
    df_a_std['year_extracted'] = df_a_std['year_note'].apply(extract_year)
    df_b_std['year_extracted'] = df_b_std['year_note'].apply(extract_year)
    
    return df_a_std, df_b_std

def merge_and_deduplicate(df_a_std, df_b_std):
    """Merge datasets and deduplicate based on normalized accession numbers."""
    
    # Combine both datasets
    combined = pd.concat([df_a_std, df_b_std], ignore_index=True)
    print(f"\nCombined records before deduplication: {len(combined)}")
    
    # Remove records without valid accession numbers
    combined = combined[combined['accession_norm'].notna()]
    print(f"Records with valid accession numbers: {len(combined)}")
    
    # Group by normalized accession and merge duplicates
    grouped = combined.groupby('accession_norm', sort=False)
    
    merged_records = []
    for acc_norm, group in grouped:
        # Use the first non-empty title
        titles = group['title'].dropna()
        title = titles.iloc[0] if len(titles) > 0 else ''
        
        # Use the first non-empty year_note
        year_notes = group['year_note'].dropna()
        year_note = year_notes.iloc[0] if len(year_notes) > 0 else ''
        
        # Get the best year (prefer specific years)
        years = group['year_extracted'].dropna()
        year = years.iloc[0] if len(years) > 0 else None
        
        # Track sources
        sources = group['source'].unique()
        source_str = ', '.join(sources)
        
        # Keep original accession variants
        raw_accessions = group['accession_raw'].unique()
        accession_variants = '; '.join(raw_accessions)
        
        merged_records.append({
            'accession_norm': acc_norm,
            'accession_variants': accession_variants,
            'title': title,
            'year_note': year_note,
            'year': year,
            'sources': source_str,
            'duplicate_count': len(group)
        })
    
    merged_df = pd.DataFrame(merged_records)
    print(f"Records after deduplication: {len(merged_df)}")
    
    return merged_df, combined

def analyze_temporal_distribution(merged_df):
    """Analyze and visualize temporal distribution of the collection."""
    
    # Filter records with valid years
    df_with_years = merged_df[merged_df['year'].notna()].copy()
    print(f"\nRecords with extractable years: {len(df_with_years)}")
    
    # Create period categories
    def categorize_period(year):
        if year < 0:
            return 'Ancient (Pre-500 CE)'
        elif year < 1000:
            return 'Early Medieval (500-1000)'
        elif year < 1500:
            return 'Medieval (1000-1500)'
        elif year < 1800:
            return 'Early Modern (1500-1800)'
        elif year < 1900:
            return 'Modern (1800-1900)'
        else:
            return 'Contemporary (1900+)'
    
    df_with_years['period'] = df_with_years['year'].apply(categorize_period)
    
    # Period distribution
    period_counts = df_with_years['period'].value_counts()
    print("\nPeriod distribution:")
    print(period_counts)
    
    # Dynasty/era distribution (from year_notes)
    def extract_era(year_note):
        note = str(year_note).lower()
        eras = []
        if 'han' in note:
            eras.append('Han Dynasty')
        if 'tang' in note:
            eras.append('Tang Dynasty')
        if 'song' in note:
            eras.append('Song Dynasty')
        if 'ming' in note:
            eras.append('Ming Dynasty')
        if 'qing' in note:
            eras.append('Qing Dynasty')
        if 'warring states' in note:
            eras.append('Warring States')
        if 'zhou' in note and 'warring' not in note:
            eras.append('Zhou Dynasty')
        if 'northern qi' in note:
            eras.append('Northern Qi')
        if 'edo' in note or 'japan' in note:
            eras.append('Edo Period')
        if 'five dynasties' in note:
            eras.append('Five Dynasties')
        if 'republic' in note:
            eras.append('Republic Era')
        if 'islamic' in note:
            eras.append('Islamic')
        if not eras:
            return 'Other/Unknown'
        return ', '.join(eras)
    
    merged_df['era'] = merged_df['year_note'].apply(extract_era)
    era_counts = merged_df['era'].value_counts()
    print("\nEra distribution:")
    print(era_counts)
    
    return df_with_years, period_counts, era_counts

def create_visualizations(df_with_years, period_counts, era_counts, merged_df, combined_df):
    """Create publication-quality visualizations."""
    
    # Figure 1: Timeline distribution
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    
    # Plot 1: Chronological timeline
    ax1 = axes[0, 0]
    years = df_with_years['year'].values
    colors = ['#d62728' if y < 0 else '#1f77b4' for y in years]
    ax1.scatter(range(len(years)), sorted(years), c=colors, alpha=0.7, s=60)
    ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5, label='CE/BCE boundary')
    ax1.set_xlabel('Object Index (sorted by date)', fontsize=11)
    ax1.set_ylabel('Year', fontsize=11)
    ax1.set_title('Chronological Distribution of Collection', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Period distribution bar chart
    ax2 = axes[0, 1]
    period_order = ['Ancient (Pre-500 CE)', 'Early Medieval (500-1000)', 
                    'Medieval (1000-1500)', 'Early Modern (1500-1800)',
                    'Modern (1800-1900)', 'Contemporary (1900+)']
    period_data = [period_counts.get(p, 0) for p in period_order]
    bars = ax2.barh(period_order, period_data, color=sns.color_palette("viridis", len(period_order)))
    ax2.set_xlabel('Number of Objects', fontsize=11)
    ax2.set_title('Distribution by Historical Period', fontsize=12, fontweight='bold')
    for i, v in enumerate(period_data):
        ax2.text(v + 0.1, i, str(v), va='center', fontsize=10)
    
    # Plot 3: Era distribution pie chart
    ax3 = axes[1, 0]
    top_eras = era_counts.head(8)
    colors_pie = sns.color_palette("Set2", len(top_eras))
    wedges, texts, autotexts = ax3.pie(top_eras.values, labels=top_eras.index, autopct='%1.1f%%',
                                        colors=colors_pie, startangle=90)
    ax3.set_title('Distribution by Cultural Era', fontsize=12, fontweight='bold')
    plt.setp(autotexts, size=9)
    plt.setp(texts, size=9)
    
    # Plot 4: Source overlap analysis
    ax4 = axes[1, 1]
    source_counts = merged_df['sources'].value_counts()
    bars = ax4.bar(source_counts.index, source_counts.values, 
                   color=['#2ca02c', '#ff7f0e', '#d62728'])
    ax4.set_ylabel('Number of Objects', fontsize=11)
    ax4.set_title('Data Source Distribution', fontsize=12, fontweight='bold')
    ax4.set_xticklabels(['Batch A Only', 'Batch B Only', 'Both Batches'], rotation=0)
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('report/images/figure1_temporal_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Figure 2: Data quality and deduplication analysis
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Plot 1: Deduplication effectiveness
    ax1 = axes[0]
    original_count = len(combined_df)
    final_count = len(merged_df)
    duplicate_reduction = original_count - final_count
    
    categories = ['Original\nRecords', 'Duplicates\nRemoved', 'Final\nCatalog']
    values = [original_count, duplicate_reduction, final_count]
    colors = ['#1f77b4', '#d62728', '#2ca02c']
    bars = ax1.bar(categories, values, color=colors, alpha=0.8)
    ax1.set_ylabel('Record Count', fontsize=11)
    ax1.set_title('Deduplication Summary', fontsize=12, fontweight='bold')
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    # Plot 2: Year extraction coverage
    ax2 = axes[1]
    with_year = len(df_with_years)
    without_year = len(merged_df) - with_year
    labels = ['With Date\nInformation', 'Date\nUnclear']
    sizes = [with_year, without_year]
    colors = ['#2ca02c', '#ff7f0e']
    explode = (0.05, 0)
    wedges, texts, autotexts = ax2.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                                        colors=colors, startangle=90)
    ax2.set_title('Date Information Coverage', fontsize=12, fontweight='bold')
    
    # Plot 3: Accession number format variations
    ax3 = axes[2]
    variation_counts = merged_df['duplicate_count'].value_counts().sort_index()
    ax3.bar(variation_counts.index, variation_counts.values, color='#9467bd', alpha=0.8)
    ax3.set_xlabel('Number of Raw Variants per Object', fontsize=11)
    ax3.set_ylabel('Count of Objects', fontsize=11)
    ax3.set_title('Accession Number Variations', fontsize=12, fontweight='bold')
    ax3.set_xticks(range(1, variation_counts.index.max() + 1))
    
    plt.tight_layout()
    plt.savefig('report/images/figure2_data_quality.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\nVisualizations saved to report/images/")

def generate_summary_stats(merged_df, combined_df, df_with_years):
    """Generate summary statistics for the report."""
    
    stats = {
        'batch_a_raw': 32,  # From initial inspection
        'batch_b_raw': 26,
        'combined_raw': len(combined_df),
        'final_catalog': len(merged_df),
        'duplicates_removed': len(combined_df) - len(merged_df),
        'with_dates': len(df_with_years),
        'without_dates': len(merged_df) - len(df_with_years),
        'date_coverage_pct': round(len(df_with_years) / len(merged_df) * 100, 1),
        'batch_a_only': len(merged_df[merged_df['sources'] == 'Batch A']),
        'batch_b_only': len(merged_df[merged_df['sources'] == 'Batch B']),
        'both_batches': len(merged_df[merged_df['sources'] == 'Batch A, Batch B']),
        'year_range': f"{int(df_with_years['year'].min())} to {int(df_with_years['year'].max())}" if len(df_with_years) > 0 else 'N/A'
    }
    
    return stats

def save_outputs(merged_df, stats):
    """Save processed data and statistics."""
    
    # Save merged catalog
    merged_df.to_csv('outputs/merged_catalog.csv', index=False)
    
    # Save summary statistics
    with open('outputs/summary_stats.txt', 'w') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    
    # Save sample of merged records
    sample_df = merged_df[['accession_norm', 'title', 'year', 'sources']].head(10)
    sample_df.to_csv('outputs/sample_records.csv', index=False)
    
    print("\nOutputs saved to outputs/ directory")

def main():
    print("="*60)
    print("MUSEUM PROVENANCE MERGE ANALYSIS")
    print("="*60)
    
    # Step 1: Load and clean data
    print("\n[1] Loading and cleaning data...")
    df_a, df_b = load_and_clean_data()
    
    # Step 2: Standardize dataframes
    print("\n[2] Standardizing data formats...")
    df_a_std, df_b_std = standardize_dataframes(df_a, df_b)
    
    # Step 3: Merge and deduplicate
    print("\n[3] Merging and deduplicating records...")
    merged_df, combined_df = merge_and_deduplicate(df_a_std, df_b_std)
    
    # Step 4: Analyze temporal distribution
    print("\n[4] Analyzing temporal distribution...")
    df_with_years, period_counts, era_counts = analyze_temporal_distribution(merged_df)
    
    # Step 5: Generate statistics
    print("\n[5] Generating summary statistics...")
    stats = generate_summary_stats(merged_df, combined_df, df_with_years)
    
    # Step 6: Create visualizations
    print("\n[6] Creating visualizations...")
    create_visualizations(df_with_years, period_counts, era_counts, merged_df, combined_df)
    
    # Step 7: Save outputs
    print("\n[7] Saving outputs...")
    save_outputs(merged_df, stats)
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    
    return merged_df, stats, df_with_years

if __name__ == "__main__":
    merged_df, stats, df_with_years = main()
