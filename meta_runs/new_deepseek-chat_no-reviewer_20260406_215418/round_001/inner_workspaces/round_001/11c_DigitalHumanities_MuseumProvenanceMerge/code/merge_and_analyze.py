import pandas as pd
import re
import matplotlib.pyplot as plt
import os

# Create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Read the data
df_a = pd.read_csv('data/museum_export_a.csv')
df_b = pd.read_csv('data/museum_export_b.csv')

print("Dataset A:")
print(df_a)
print("\nDataset B:")
print(df_b)

# Standardize column names for merging
df_a_standardized = df_a.copy()
df_a_standardized.columns = ['accession', 'title', 'year_note']

# For df_b, we need to map columns: accession, object_name -> title, remarks -> year_note?
# Actually, looking at the data:
# df_a: X-100, "Vase, Han style", "listed as 200BC in card"
# df_b: X100, "Vase Han", "see batch1 duplicate?"
# The remarks field in df_b doesn't contain year info, but mentions duplicate

# Let's create a unified dataframe with all information
df_combined = pd.DataFrame({
    'source': ['export_a', 'export_b'],
    'accession': [df_a['accno'].iloc[0], df_b['accession'].iloc[0]],
    'title': [df_a['title'].iloc[0], df_b['object_name'].iloc[0]],
    'year_note': [df_a['year_note'].iloc[0], df_b['remarks'].iloc[0]],
    'original_accno': [df_a['accno'].iloc[0], None],
    'original_object_name': [None, df_b['object_name'].iloc[0]],
    'original_remarks': [None, df_b['remarks'].iloc[0]]
})

print("\nCombined data:")
print(df_combined)

# Extract year from year_note using regex
def extract_year(text):
    if pd.isna(text):
        return None
    
    # Look for patterns like 200BC, 200 BC, 200 BCE, 200 B.C., etc.
    patterns = [
        r'(\d+)\s*BCE?',
        r'(\d+)\s*B\.?C\.?',
        r'(\d+)\s*AD',
        r'(\d+)\s*A\.?D\.?',
        r'(\d{4})'  # Four-digit year
    ]
    
    for pattern in patterns:
        match = re.search(pattern, str(text), re.IGNORECASE)
        if match:
            year_str = match.group(1)
            # Convert to integer
            try:
                year = int(year_str)
                # Handle BC/BCE years (negative)
                if 'BC' in text.upper() or 'BCE' in text.upper():
                    year = -year
                return year
            except ValueError:
                continue
    return None

# Apply extraction
df_combined['extracted_year'] = df_combined['year_note'].apply(extract_year)

print("\nData with extracted years:")
print(df_combined[['accession', 'title', 'year_note', 'extracted_year']])

# Create a deduplicated catalog
# Based on the data, these appear to be the same object
# Strategy: keep the record with the most complete information
# For deduplication, we need to identify duplicates
# In this minimal dataset, we'll assume objects with similar titles are duplicates

# Create a simple deduplication key (normalized title)
def normalize_title(title):
    if pd.isna(title):
        return ''
    return re.sub(r'[^a-zA-Z0-9]', '', title.lower())

df_combined['normalized_title'] = df_combined['title'].apply(normalize_title)

print("\nNormalized titles:")
print(df_combined[['title', 'normalized_title']])

# Group by normalized title to identify potential duplicates
grouped = df_combined.groupby('normalized_title')

# Create deduplicated catalog
deduplicated_records = []
for name, group in grouped:
    if len(group) > 1:
        print(f"\nPotential duplicates found for '{name}':")
        print(group[['accession', 'title', 'year_note', 'extracted_year']])
        
        # Choose the record with year information
        has_year = group[~group['extracted_year'].isna()]
        if not has_year.empty:
            chosen = has_year.iloc[0]
        else:
            chosen = group.iloc[0]
            
        # Combine information from all records
        combined_accession = '; '.join(group['accession'].dropna().astype(str).unique())
        combined_title = chosen['title']  # Use the chosen title
        combined_year_note = '; '.join(group['year_note'].dropna().unique())
        combined_year = chosen['extracted_year']
        
        deduplicated_records.append({
            'accession': combined_accession,
            'title': combined_title,
            'year_note': combined_year_note,
            'extracted_year': combined_year,
            'source': 'merged',
            'duplicate_count': len(group)
        })
    else:
        # Single record, keep as is
        record = group.iloc[0].to_dict()
        record['duplicate_count'] = 1
        deduplicated_records.append(record)

# Create deduplicated dataframe
df_dedup = pd.DataFrame(deduplicated_records)

print("\nDeduplicated catalog:")
print(df_dedup)

# Save to outputs
output_path = 'outputs/deduplicated_catalog.csv'
df_dedup.to_csv(output_path, index=False)
print(f"\nDeduplicated catalog saved to: {output_path}")

# Temporal distribution analysis
print("\n=== Temporal Distribution Analysis ===")

# Filter records with extracted years
df_with_years = df_dedup[~df_dedup['extracted_year'].isna()].copy()

if not df_with_years.empty:
    print(f"Records with extracted years: {len(df_with_years)}")
    print(df_with_years[['accession', 'title', 'extracted_year']])
    
    # Basic statistics
    print(f"\nYear statistics:")
    print(f"Earliest year: {df_with_years['extracted_year'].min()}")
    print(f"Latest year: {df_with_years['extracted_year'].max()}")
    print(f"Mean year: {df_with_years['extracted_year'].mean():.1f}")
    
    # Create temporal distribution visualization
    plt.figure(figsize=(10, 6))
    
    # Histogram of years
    plt.subplot(1, 2, 1)
    plt.hist(df_with_years['extracted_year'], bins=10, edgecolor='black', alpha=0.7)
    plt.xlabel('Year')
    plt.ylabel('Frequency')
    plt.title('Distribution of Object Years')
    plt.grid(True, alpha=0.3)
    
    # Timeline plot
    plt.subplot(1, 2, 2)
    years = df_with_years['extracted_year'].values
    plt.scatter(years, [1] * len(years), alpha=0.6, s=100)
    plt.xlabel('Year')
    plt.yticks([])
    plt.title('Timeline of Objects')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure
    fig_path = 'report/images/temporal_distribution.png'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"\nTemporal distribution plot saved to: {fig_path}")
    
    # Show the plot
    plt.show()
    
else:
    print("No records with extractable year information found.")
    
    # Create a simple visualization anyway for the report
    plt.figure(figsize=(8, 4))
    plt.text(0.5, 0.5, 'No temporal data available\nfor visualization', 
             ha='center', va='center', fontsize=14)
    plt.axis('off')
    
    fig_path = 'report/images/temporal_distribution.png'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    print(f"Placeholder visualization saved to: {fig_path}")

# Also create a summary statistics file
summary_stats = {
    'total_records_original': len(df_a) + len(df_b),
    'total_records_deduplicated': len(df_dedup),
    'records_with_extracted_years': len(df_with_years) if 'df_with_years' in locals() else 0,
    'duplicates_merged': len(df_a) + len(df_b) - len(df_dedup)
}

summary_df = pd.DataFrame([summary_stats])
summary_path = 'outputs/summary_statistics.csv'
summary_df.to_csv(summary_path, index=False)
print(f"\nSummary statistics saved to: {summary_path}")
print("\nSummary:")
for key, value in summary_stats.items():
    print(f"  {key}: {value}")