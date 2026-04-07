import pandas as pd
import re
import matplotlib.pyplot as plt
import os
from datetime import datetime

# Create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Read the data
df_a = pd.read_csv('data/museum_export_a.csv')
df_b = pd.read_csv('data/museum_export_b.csv')

print("=== Museum Provenance Merge Analysis ===")
print(f"Dataset A records: {len(df_a)}")
print(f"Dataset B records: {len(df_b)}")
print(f"Total records: {len(df_a) + len(df_b)}")

# Standardize the data
# Create a unified structure
df_a_clean = pd.DataFrame({
    'original_source': 'export_a',
    'accession': df_a['accno'],
    'title': df_a['title'],
    'year_info': df_a['year_note'],
    'notes': ''
})

df_b_clean = pd.DataFrame({
    'original_source': 'export_b',
    'accession': df_b['accession'],
    'title': df_b['object_name'],
    'year_info': '',
    'notes': df_b['remarks']
})

# Combine all records
df_all = pd.concat([df_a_clean, df_b_clean], ignore_index=True)

print("\n=== Combined Data ===")
print(df_all)

# Function to extract year from text
def extract_year_from_text(text):
    """Extract year from text, handling BC/AD notation"""
    if pd.isna(text) or text == '':
        return None
    
    text = str(text).upper()
    
    # Patterns to match
    patterns = [
        (r'(\d+)\s*BCE?', -1),  # BC or BCE
        (r'(\d+)\s*B\.?C\.?', -1),  # B.C. or BC
        (r'(\d+)\s*AD', 1),  # AD
        (r'(\d+)\s*A\.?D\.?', 1),  # A.D.
        (r'(\d{4})', 1),  # Four-digit year (assumed AD)
        (r'(\d{1,3})\s*CENTURY', None),  # Century notation
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                year_val = int(match.group(1))
                if multiplier == -1:
                    return -year_val
                elif multiplier == 1:
                    return year_val
                elif multiplier is None and 'CENTURY' in text:
                    # Convert century to approximate year (middle of century)
                    return (year_val - 1) * 100 + 50
            except ValueError:
                continue
    
    return None

# Apply year extraction
df_all['extracted_year'] = df_all['year_info'].apply(extract_year_from_text)

print("\n=== Data with Extracted Years ===")
print(df_all[['accession', 'title', 'year_info', 'extracted_year']])

# Improved deduplication logic
# Create a matching key based on normalized accession and title
def create_match_key(accession, title):
    """Create a key for matching potential duplicates"""
    # Normalize accession: remove hyphens, spaces, convert to lowercase
    norm_acc = re.sub(r'[^a-zA-Z0-9]', '', str(accession)).lower()
    
    # Normalize title: remove punctuation, spaces, convert to lowercase
    norm_title = re.sub(r'[^a-zA-Z0-9]', '', str(title)).lower()
    
    # Use the shorter of the two as base for matching
    # This helps match "Vase Han" with "Vase, Han style"
    return norm_acc if len(norm_acc) < len(norm_title) else norm_title

# Apply matching key
df_all['match_key'] = df_all.apply(lambda row: create_match_key(row['accession'], row['title']), axis=1)

print("\n=== Matching Keys ===")
print(df_all[['accession', 'title', 'match_key']])

# Group by match_key to identify duplicates
duplicate_groups = df_all.groupby('match_key').filter(lambda x: len(x) > 1)
unique_groups = df_all.groupby('match_key').filter(lambda x: len(x) == 1)

print(f"\nPotential duplicate groups found: {duplicate_groups['match_key'].nunique() if not duplicate_groups.empty else 0}")

# Create deduplicated catalog
deduplicated_records = []

# Process duplicate groups
for key, group in df_all.groupby('match_key'):
    if len(group) > 1:
        print(f"\nMerging duplicate group for key '{key}':")
        print(group[['accession', 'title', 'extracted_year']].to_string(index=False))
        
        # Merge strategy: combine information from all records
        merged_accession = ' | '.join(sorted(group['accession'].astype(str).unique()))
        
        # Choose the most descriptive title
        titles = group['title'].tolist()
        # Prefer longer titles (more descriptive)
        merged_title = max(titles, key=len)
        
        # Combine year information
        year_records = group[~group['extracted_year'].isna()]
        if not year_records.empty:
            merged_year = year_records['extracted_year'].iloc[0]
            year_source = year_records['year_info'].iloc[0]
        else:
            merged_year = None
            year_source = ''
        
        # Combine notes
        all_notes = ' | '.join(filter(None, group['notes'].fillna('').tolist()))
        
        deduplicated_records.append({
            'accession': merged_accession,
            'title': merged_title,
            'year_info': year_source,
            'extracted_year': merged_year,
            'notes': all_notes,
            'original_sources': ' | '.join(sorted(group['original_source'].unique())),
            'record_count': len(group),
            'status': 'merged'
        })
    else:
        # Single record
        record = group.iloc[0]
        deduplicated_records.append({
            'accession': record['accession'],
            'title': record['title'],
            'year_info': record['year_info'],
            'extracted_year': record['extracted_year'],
            'notes': record['notes'],
            'original_sources': record['original_source'],
            'record_count': 1,
            'status': 'unique'
        })

# Create deduplicated dataframe
df_dedup = pd.DataFrame(deduplicated_records)

print("\n=== Deduplicated Catalog ===")
print(df_dedup[['accession', 'title', 'extracted_year', 'record_count', 'status']])

# Save deduplicated catalog
output_path = 'outputs/deduplicated_catalog_final.csv'
df_dedup.to_csv(output_path, index=False)
print(f"\nDeduplicated catalog saved to: {output_path}")

# Temporal analysis
print("\n=== Temporal Distribution Analysis ===")

# Filter records with extracted years
df_with_years = df_dedup[~df_dedup['extracted_year'].isna()].copy()

if not df_with_years.empty:
    print(f"Objects with date information: {len(df_with_years)}")
    
    # Basic statistics
    print(f"\nTemporal Statistics:")
    print(f"Earliest year: {df_with_years['extracted_year'].min():.0f}")
    print(f"Latest year: {df_with_years['extracted_year'].max():.0f}")
    print(f"Mean year: {df_with_years['extracted_year'].mean():.1f}")
    print(f"Median year: {df_with_years['extracted_year'].median():.1f}")
    
    # Create enhanced visualization
    plt.figure(figsize=(12, 8))
    
    # Plot 1: Timeline with points sized by record count
    plt.subplot(2, 2, 1)
    years = df_with_years['extracted_year'].values
    counts = df_with_years['record_count'].values
    titles = df_with_years['title'].values
    
    # Create a timeline
    plt.scatter(years, [0] * len(years), s=counts*100, alpha=0.7, edgecolors='black')
    
    # Add labels for points
    for i, (year, title) in enumerate(zip(years, titles)):
        plt.text(year, 0.1, title[:15] + '...' if len(title) > 15 else title, 
                ha='center', va='bottom', fontsize=8, rotation=45)
    
    plt.xlabel('Year (negative = BC)')
    plt.yticks([])
    plt.title('Timeline of Museum Objects')
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Histogram
    plt.subplot(2, 2, 2)
    if len(years) > 1:
        bins = min(10, len(years))
        plt.hist(years, bins=bins, edgecolor='black', alpha=0.7, color='skyblue')
    else:
        # Single year - show as bar
        plt.bar(years, [1], width=10, edgecolor='black', alpha=0.7)
        plt.xlim(years[0] - 50, years[0] + 50)
    
    plt.xlabel('Year')
    plt.ylabel('Frequency')
    plt.title('Distribution of Object Dates')
    plt.grid(True, alpha=0.3)
    
    # Plot 3: Summary statistics
    plt.subplot(2, 2, 3)
    stats_labels = ['Total Objects', 'With Dates', 'Merged Records']
    stats_values = [len(df_dedup), len(df_with_years), len(df_dedup[df_dedup['status'] == 'merged'])]
    
    bars = plt.bar(stats_labels, stats_values, color=['lightgray', 'lightblue', 'lightcoral'])
    plt.ylabel('Count')
    plt.title('Collection Statistics')
    
    # Add value labels on bars
    for bar, value in zip(bars, stats_values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(value), ha='center', va='bottom')
    
    # Plot 4: Year distribution by century
    plt.subplot(2, 2, 4)
    if len(years) > 0:
        # Convert to centuries
        centuries = []
        for year in years:
            if year < 0:
                century = -((-year - 1) // 100 + 1)  # Negative centuries for BC
            else:
                century = (year - 1) // 100 + 1
            centuries.append(century)
        
        century_counts = pd.Series(centuries).value_counts().sort_index()
        
        # Create bar chart
        century_labels = [f'{abs(c)}th century ' + ('BC' if c < 0 else 'AD') for c in century_counts.index]
        plt.bar(range(len(century_counts)), century_counts.values, color='lightgreen')
        plt.xticks(range(len(century_counts)), century_labels, rotation=45, ha='right')
        plt.ylabel('Number of Objects')
        plt.title('Objects by Century')
    else:
        plt.text(0.5, 0.5, 'Insufficient data\nfor century analysis', 
                ha='center', va='center', fontsize=12)
        plt.axis('off')
    
    plt.tight_layout()
    
    # Save figure
    fig_path = 'report/images/temporal_analysis_comprehensive.png'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"\nComprehensive temporal analysis plot saved to: {fig_path}")
    
else:
    print("No objects with extractable date information.")
    
    # Create a simple visualization for the report
    plt.figure(figsize=(10, 6))
    
    plt.subplot(1, 2, 1)
    stats_labels = ['Total Objects', 'With Dates', 'Merged Records']
    stats_values = [len(df_dedup), 0, len(df_dedup[df_dedup['status'] == 'merged'])]
    
    bars = plt.bar(stats_labels, stats_values, color=['lightgray', 'lightblue', 'lightcoral'])
    plt.ylabel('Count')
    plt.title('Collection Statistics')
    
    # Add value labels on bars
    for bar, value in zip(bars, stats_values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(value), ha='center', va='bottom')
    
    plt.subplot(1, 2, 2)
    plt.text(0.5, 0.5, 'No temporal data available\nfor distribution analysis', 
             ha='center', va='center', fontsize=14)
    plt.axis('off')
    
    plt.tight_layout()
    
    fig_path = 'report/images/temporal_analysis_comprehensive.png'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"\nBasic collection statistics plot saved to: {fig_path}")

# Create summary report
summary = {
    'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'total_original_records': len(df_a) + len(df_b),
    'total_deduplicated_records': len(df_dedup),
    'records_with_extracted_years': len(df_with_years),
    'duplicates_merged': len(df_dedup[df_dedup['status'] == 'merged']),
    'earliest_year': df_with_years['extracted_year'].min() if not df_with_years.empty else 'N/A',
    'latest_year': df_with_years['extracted_year'].max() if not df_with_years.empty else 'N/A',
    'mean_year': df_with_years['extracted_year'].mean() if not df_with_years.empty else 'N/A'
}

summary_df = pd.DataFrame([summary])
summary_path = 'outputs/analysis_summary.csv'
summary_df.to_csv(summary_path, index=False)

print("\n=== Analysis Summary ===")
for key, value in summary.items():
    print(f"{key.replace('_', ' ').title()}: {value}")

print("\n=== Analysis Complete ===")