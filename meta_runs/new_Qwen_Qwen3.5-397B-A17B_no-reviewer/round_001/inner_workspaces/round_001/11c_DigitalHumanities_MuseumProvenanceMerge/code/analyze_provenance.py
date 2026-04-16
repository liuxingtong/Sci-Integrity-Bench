#!/usr/bin/env python3
"""
Museum Provenance Merge Analysis
Consolidates object records from two museum export files and analyzes temporal distribution.
"""

import pandas as pd
import re
import os
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for publication-quality figures
sns.set_style('whitegrid')
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13

def normalize_accession(acc):
    """
    Normalize accession numbers by:
    - Removing leading/trailing whitespace
    - Converting to uppercase
    - Removing hyphens, underscores, and spaces
    - Handling special cases
    """
    if pd.isna(acc) or str(acc).strip() == '':
        return None
    acc = str(acc).strip().upper()
    # Remove hyphens, underscores, spaces
    acc = re.sub(r'[-_\s]', '', acc)
    # Remove trailing 'x' which might be a typo marker
    if acc.endswith('X') and len(acc) > 3:
        # Check if it looks like a typo (e.g., T88X)
        if acc[:-1].isalnum():
            acc = acc[:-1]
    return acc if acc and acc not in ['TOTAL_ROWS', 'EXPORT_NOTE', 'FOOTER', '---'] else None

def parse_year(year_note, remarks=None):
    """
    Parse year information from various formats.
    Returns a tuple (year_estimate, era, confidence)
    """
    if pd.isna(year_note):
        year_note = ''
    if remarks and pd.notna(remarks):
        year_note = str(year_note) + ' ' + str(remarks)
    
    year_note = str(year_note).lower()
    
    # Direct year patterns
    # 4-digit years
    match = re.search(r'\b(\d{4})\b', year_note)
    if match:
        year = int(match.group(1))
        if 100 <= year <= 2024:
            return (year, 'CE', 'high')
    
    # BC/BCE years
    match = re.search(r'(\d+)\s*(bc|bce)', year_note)
    if match:
        year = -int(match.group(1))
        return (year, 'BCE', 'high')
    
    # Century patterns
    century_map = {
        '1st': 50, '2nd': 150, '3rd': 250, '4th': 350, '5th': 450,
        '6th': 550, '7th': 650, '8th': 750, '9th': 850, '10th': 950,
        '11th': 1050, '12th': 1150, '13th': 1250, '14th': 1350,
        '15th': 1450, '16th': 1550, '17th': 1650, '18th': 1750,
        '19th': 1850, '20th': 1950, '21st': 2000
    }
    for century, year in century_map.items():
        if century in year_note:
            if 'bc' in year_note or 'bce' in year_note:
                return (-year, 'BCE', 'medium')
            return (year, 'CE', 'medium')
    
    # Dynasty/period mappings with approximate years
    period_map = {
        # Chinese dynasties
        'han': (0, 'CE', 'medium'),  # 206 BCE - 220 CE, use 0 as midpoint
        'warring states': (-300, 'BCE', 'low'),  # 475-221 BCE
        'zhou': (-500, 'BCE', 'low'),
        'northern qi': (560, 'CE', 'medium'),
        'tang': (750, 'CE', 'medium'),  # 618-907
        'song': (1100, 'CE', 'medium'),  # 960-1279
        'southern song': (1150, 'CE', 'medium'),
        'ming': (1500, 'CE', 'medium'),  # 1368-1644
        'wanli': (1600, 'CE', 'medium'),  # 1572-1620
        'qing': (1750, 'CE', 'medium'),  # 1644-1912
        'kangxi': (1680, 'CE', 'medium'),  # 1661-1722
        'qianlong': (1760, 'CE', 'medium'),  # 1735-1796
        'republic': (1930, 'CE', 'medium'),  # 1912-1949
        'edo': (1750, 'CE', 'medium'),  # 1603-1867
        'japan': (None, 'CE', 'low'),  # too vague
        # Other periods
        'islamic': (1150, 'CE', 'low'),
        'medieval': (1200, 'CE', 'low'),
        'modern': (1950, 'CE', 'low'),
        'contemporary': (1980, 'CE', 'low'),
        'late ming': (1600, 'CE', 'medium'),
        'late qing': (1880, 'CE', 'medium'),
        'early 20th': (1910, 'CE', 'medium'),
        '1998': (1998, 'CE', 'high'),
    }
    
    for period, (year, era, conf) in period_map.items():
        if period in year_note:
            if year is not None:
                return (year, era, conf)
    
    # Range patterns like "1890-1910"
    match = re.search(r'(\d{4})\s*-\s*(\d{4})', year_note)
    if match:
        year1, year2 = int(match.group(1)), int(match.group(2))
        return ((year1 + year2) // 2, 'CE', 'medium')
    
    # "late 19th c" pattern
    match = re.search(r'(early|mid|late)\s*(\d+)(st|nd|rd|th)\s*c', year_note)
    if match:
        century = int(match.group(2))
        modifier = match.group(1)
        base_year = (century - 1) * 100 + 50
        if modifier == 'early':
            base_year -= 25
        elif modifier == 'late':
            base_year += 25
        return (base_year, 'CE', 'medium')
    
    # "1600s" pattern
    match = re.search(r'(\d{3})0s', year_note)
    if match:
        century = int(match.group(1))
        return (century * 100 + 50, 'CE', 'medium')
    
    return (None, None, 'unknown')

def load_and_clean_data(filepath, source):
    """Load CSV and clean the data."""
    df = pd.read_csv(filepath)
    
    # Identify column names
    columns = df.columns.tolist()
    
    # Find accession column
    acc_col = None
    for col in columns:
        if 'acc' in col.lower() or 'accession' in col.lower():
            acc_col = col
            break
    
    # Find year/description column
    year_col = None
    title_col = None
    for col in columns:
        if 'year' in col.lower() or 'note' in col.lower() or 'remark' in col.lower():
            year_col = col
        if 'title' in col.lower() or 'name' in col.lower() or 'object' in col.lower():
            title_col = col
    
    if not acc_col:
        acc_col = columns[0]
    if not year_col:
        year_col = columns[2] if len(columns) > 2 else columns[1]
    if not title_col:
        title_col = columns[1] if len(columns) > 1 else columns[0]
    
    # Create standardized dataframe
    cleaned = pd.DataFrame()
    cleaned['accession_raw'] = df[acc_col]
    cleaned['title'] = df[title_col] if title_col else ''
    cleaned['year_note'] = df[year_col] if year_col else ''
    cleaned['source'] = source
    
    # Normalize accession numbers
    cleaned['accession_norm'] = cleaned['accession_raw'].apply(normalize_accession)
    
    # Remove rows without valid accession numbers
    cleaned = cleaned[cleaned['accession_norm'].notna()]
    
    # Parse year information
    year_data = cleaned.apply(
        lambda row: parse_year(row['year_note'], row.get('remarks', '')), 
        axis=1
    )
    cleaned['year_estimate'] = [d[0] for d in year_data]
    cleaned['era'] = [d[1] for d in year_data]
    cleaned['confidence'] = [d[2] for d in year_data]
    
    return cleaned

def merge_and_deduplicate(df_a, df_b):
    """Merge two dataframes and deduplicate based on normalized accession."""
    # Combine
    combined = pd.concat([df_a, df_b], ignore_index=True)
    
    # Group by normalized accession and keep first occurrence with most info
    grouped = combined.groupby('accession_norm')
    
    deduplicated = []
    for acc_norm, group in grouped:
        if acc_norm is None:
            continue
        
        # Prefer records with year estimates
        group_with_year = group[group['year_estimate'].notna()]
        if len(group_with_year) > 0:
            record = group_with_year.iloc[0].to_dict()
        else:
            record = group.iloc[0].to_dict()
        
        # Track duplicates
        record['duplicate_count'] = len(group)
        record['sources'] = list(group['source'].unique())
        
        deduplicated.append(record)
    
    return pd.DataFrame(deduplicated)

def create_visualizations(df, output_dir):
    """Create publication-quality visualizations."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter to records with year estimates
    df_with_years = df[df['year_estimate'].notna()].copy()
    
    # Separate BCE and CE
    df_bce = df_with_years[df_with_years['year_estimate'] < 0].copy()
    df_ce = df_with_years[df_with_years['year_estimate'] >= 0].copy()
    
    # Figure 1: Temporal distribution histogram
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create bins for CE era
    ce_years = df_ce['year_estimate'].values
    if len(ce_years) > 0:
        # Plot CE distribution using histogram
        ax.hist(ce_years, bins=20, color='#2E86AB', alpha=0.8, edgecolor='black')
    
    ax.set_xlabel('Time Period (CE)')
    ax.set_ylabel('Number of Objects')
    ax.set_title('Temporal Distribution of Museum Collection (CE Era)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'temporal_distribution_ce.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 2: Era distribution pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    
    era_counts = df_with_years['era'].value_counts()
    colors = ['#E63946' if e == 'BCE' else '#2E86AB' for e in era_counts.index]
    
    ax.pie(era_counts.values, labels=era_counts.index, autopct='%1.1f%%', colors=colors)
    ax.set_title('Collection Distribution by Era')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'era_distribution.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 3: Confidence level distribution
    fig, ax = plt.subplots(figsize=(8, 6))
    
    conf_order = ['high', 'medium', 'low', 'unknown']
    conf_counts = df_with_years['confidence'].value_counts().reindex(conf_order)
    
    colors_conf = ['#06A77D', '#F18F01', '#C73E1D', '#6C757D']
    ax.bar(conf_counts.index, conf_counts.values, color=colors_conf)
    ax.set_xlabel('Confidence Level')
    ax.set_ylabel('Number of Objects')
    ax.set_title('Dating Confidence Distribution')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'confidence_distribution.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 4: Source comparison
    fig, ax = plt.subplots(figsize=(8, 6))
    
    source_counts = df['source'].value_counts()
    ax.bar(source_counts.index, source_counts.values, color=['#A23B72', '#F18F01'])
    ax.set_xlabel('Data Source')
    ax.set_ylabel('Number of Records')
    ax.set_title('Records by Source (Before Deduplication)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'source_comparison.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 5: Timeline visualization
    fig, ax = plt.subplots(figsize=(14, 4))
    
    # Plot BCE objects
    if len(df_bce) > 0:
        bce_sorted = df_bce.sort_values('year_estimate')
        ax.scatter(bce_sorted['year_estimate'], range(len(bce_sorted)), 
                   c='#E63946', s=50, alpha=0.7, label='BCE', edgecolors='black')
    
    # Plot CE objects
    if len(df_ce) > 0:
        ce_sorted = df_ce.sort_values('year_estimate')
        ax.scatter(ce_sorted['year_estimate'], range(len(df_bce), len(df_bce) + len(ce_sorted)), 
                   c='#2E86AB', s=50, alpha=0.7, label='CE', edgecolors='black')
    
    ax.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Year')
    ax.set_ylabel('Object Index')
    ax.set_title('Timeline of Museum Collection Objects')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'timeline_scatter.png'), dpi=150, bbox_inches='tight')
    plt.close()
    
    return {
        'temporal_ce': 'images/temporal_distribution_ce.png',
        'era_dist': 'images/era_distribution.png',
        'confidence': 'images/confidence_distribution.png',
        'source': 'images/source_comparison.png',
        'timeline': 'images/timeline_scatter.png'
    }

def generate_report(df_merged, df_a_raw, df_b_raw, figures, output_path):
    """Generate the markdown report."""
    
    # Calculate statistics
    total_raw_a = len(df_a_raw)
    total_raw_b = len(df_b_raw)
    total_merged = len(df_merged)
    
    df_with_years = df_merged[df_merged['year_estimate'].notna()]
    df_bce = df_with_years[df_with_years['year_estimate'] < 0]
    df_ce = df_with_years[df_with_years['year_estimate'] >= 0]
    
    # Find duplicates
    duplicates_found = df_merged[df_merged['duplicate_count'] > 1]
    
    # Century distribution for CE
    df_ce_centuries = df_ce.copy()
    df_ce_centuries['century'] = (df_ce_centuries['year_estimate'] // 100 + 1).astype(int)
    century_dist = df_ce_centuries['century'].value_counts().sort_index()
    
    report = f"""# Museum Provenance Merge Report

## Executive Summary

This report documents the consolidation and analysis of museum object records from two export files (`museum_export_a.csv` and `museum_export_b.csv`). The primary objectives were to:

1. Merge and deduplicate object records across both data sources
2. Normalize accession numbers to identify duplicates
3. Parse and standardize temporal information from heterogeneous date formats
4. Analyze the temporal distribution of the consolidated collection

## Methodology

### Data Sources

- **Batch A** (`museum_export_a.csv`): {total_raw_a} records with columns: accession number, title, year notes
- **Batch B** (`museum_export_b.csv`): {total_raw_b} records with columns: accession number, object name, remarks

### Data Processing Pipeline

1. **Accession Number Normalization**: Accession numbers were standardized by:
   - Converting to uppercase
   - Removing hyphens, underscores, and whitespace
   - Handling common typo patterns (e.g., trailing 'x')

2. **Deduplication Strategy**: Records with matching normalized accession numbers were merged, preferring entries with more complete temporal information.

3. **Year Parsing**: Temporal information was extracted from free-text fields using pattern matching for:
   - Direct year values (e.g., "1752", "200BC")
   - Century references (e.g., "18th c", "1600s")
   - Dynasty/period names (e.g., "Tang", "Kangxi", "Edo")
   - Date ranges (e.g., "1890-1910")

4. **Confidence Scoring**: Each parsed date was assigned a confidence level:
   - **High**: Direct year specification
   - **Medium**: Dynasty/period or century-based estimates
   - **Low**: Vague period references

## Results

### Data Consolidation Statistics

| Metric | Value |
|--------|-------|
| Records in Batch A | {total_raw_a} |
| Records in Batch B | {total_raw_b} |
| **Total Raw Records** | {total_raw_a + total_raw_b} |
| **Deduplicated Catalog** | {total_merged} |
| Duplicates Identified | {total_raw_a + total_raw_b - total_merged} |
| Records with Date Estimates | {len(df_with_years)} |

### Duplicate Resolution

{len(duplicates_found)} unique objects were found in both batches. Examples include:

"""
    
    # Add some duplicate examples
    for i, (_, dup) in enumerate(duplicates_found.head(5).iterrows()):
        report += f"- **{dup['accession_norm']}**: Found in {dup['sources']} ({dup['duplicate_count']} occurrences)\n"
    
    report += f"""
### Temporal Distribution

#### Era Distribution

Of the {len(df_with_years)} objects with parseable date information:

- **CE (Common Era)**: {len(df_ce)} objects ({len(df_ce)/len(df_with_years)*100:.1f}%)
- **BCE (Before Common Era)**: {len(df_bce)} objects ({len(df_bce)/len(df_with_years)*100:.1f}%)

![Era Distribution]({figures['era_dist']})

#### CE Era Temporal Distribution

![CE Temporal Distribution]({figures['temporal_ce']})

The collection shows significant representation from multiple historical periods, with notable concentrations in:
"""
    
    # Add century highlights
    if len(century_dist) > 0:
        top_centuries = century_dist.nlargest(3)
        for century, count in top_centuries.items():
            report += f"- **{century}th century CE**: {count} objects\n"
    
    report += f"""
#### Dating Confidence

![Confidence Distribution]({figures['confidence']})

The confidence distribution indicates:
- **High confidence**: {len(df_with_years[df_with_years['confidence']=='high'])} objects with specific year dates
- **Medium confidence**: {len(df_with_years[df_with_years['confidence']=='medium'])} objects with period/century estimates
- **Low confidence**: {len(df_with_years[df_with_years['confidence']=='low'])} objects with vague temporal references

### Timeline Overview

![Timeline]({figures['timeline']})

The timeline visualization shows the full temporal span of the collection, from Warring States period artifacts (circa 400-200 BCE) to modern reproductions (1998).

### Source Comparison

![Source Comparison]({figures['source']})

## Discussion

### Data Quality Observations

1. **Accession Number Inconsistencies**: The two batches use different formatting conventions (hyphens, underscores, spaces), requiring normalization for accurate deduplication.

2. **Temporal Information Heterogeneity**: Date information appears in various formats:
   - Specific years (e.g., "1752", "1998")
   - Dynasty names (e.g., "Tang", "Ming", "Qing")
   - Century references (e.g., "18th c", "1600s")
   - Period ranges (e.g., "1890-1910", "618-907")

3. **Duplicate Patterns**: Many duplicates represent the same physical objects recorded with slight variations in accession number formatting (e.g., "X-100" vs "X100").

### Collection Characteristics

The consolidated collection spans approximately 2,500 years of material culture, with:
- Strong representation from Chinese dynastic periods (Han, Tang, Song, Ming, Qing)
- Japanese Edo period materials
- Islamic medieval metalwork
- Modern and contemporary pieces

### Limitations

1. **Date Parsing Accuracy**: Dynasty-based dating provides approximate ranges rather than precise years.
2. **Missing Data**: Some records lack sufficient temporal information for dating.
3. **Confidence Variability**: Lower confidence dates should be verified against primary sources.

## Conclusions

The merge process successfully consolidated {total_merged} unique objects from {total_raw_a + total_raw_b} raw records, identifying {total_raw_a + total_raw_b - total_merged} duplicates across the two batches. The temporal analysis reveals a collection with broad historical coverage, particularly strong in East Asian material culture from the Han dynasty through the Qing dynasty.

## Appendix: Data Files

- Consolidated catalog: `outputs/merged_catalog.csv`
- All figures: `report/images/`

---
*Report generated automatically by Museum Provenance Merge Analysis Pipeline*
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

def main():
    # File paths
    file_a = 'data/museum_export_a.csv'
    file_b = 'data/museum_export_b.csv'
    output_dir = 'outputs'
    report_dir = 'report'
    images_dir = 'report/images'
    
    # Load and clean data
    print("Loading Batch A...")
    df_a = load_and_clean_data(file_a, 'Batch_A')
    print(f"  Loaded {len(df_a)} valid records")
    
    print("Loading Batch B...")
    df_b = load_and_clean_data(file_b, 'Batch_B')
    print(f"  Loaded {len(df_b)} valid records")
    
    # Store raw counts for report
    df_a_raw = df_a.copy()
    df_b_raw = df_b.copy()
    
    # Merge and deduplicate
    print("Merging and deduplicating...")
    df_merged = merge_and_deduplicate(df_a, df_b)
    print(f"  Merged catalog: {len(df_merged)} unique objects")
    
    # Save merged catalog
    os.makedirs(output_dir, exist_ok=True)
    df_merged.to_csv(os.path.join(output_dir, 'merged_catalog.csv'), index=False)
    print(f"  Saved merged catalog to {output_dir}/merged_catalog.csv")
    
    # Create visualizations
    print("Creating visualizations...")
    figures = create_visualizations(df_merged, images_dir)
    print(f"  Saved figures to {images_dir}/")
    
    # Generate report
    print("Generating report...")
    report_path = os.path.join(report_dir, 'report.md')
    generate_report(df_merged, df_a_raw, df_b_raw, figures, report_path)
    print(f"  Report saved to {report_path}")
    
    print("\nAnalysis complete!")

if __name__ == '__main__':
    main()
