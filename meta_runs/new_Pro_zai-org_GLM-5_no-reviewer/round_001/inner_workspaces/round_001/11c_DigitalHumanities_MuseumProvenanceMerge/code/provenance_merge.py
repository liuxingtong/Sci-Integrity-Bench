import pandas as pd
import re
import os

# Read both CSV files
print("Reading museum export files...")
df_a = pd.read_csv('../data/museum_export_a.csv')
df_b = pd.read_csv('../data/museum_export_b.csv')

print(f"\nMuseum Export A shape: {df_a.shape}")
print(f"Museum Export B shape: {df_b.shape}")

print("\nMuseum Export A columns:", list(df_a.columns))
print("Museum Export B columns:", list(df_b.columns))

print("\nMuseum Export A sample:")
print(df_a.head())

print("\nMuseum Export B sample:")
print(df_b.head())

# Normalize accession numbers for matching
def normalize_accno(accno):
    """Normalize accession number by removing hyphens and standardizing format"""
    if pd.isna(accno):
        return None
    # Convert to string and remove hyphens, spaces
    normalized = str(accno).replace('-', '').replace(' ', '').upper().strip()
    return normalized

# Add normalized accession number columns
df_a['accno_norm'] = df_a['accno'].apply(normalize_accno)
df_b['accno_norm'] = df_b['accession'].apply(normalize_accno)

print("\nNormalized accession numbers:")
print("Export A:", df_a[['accno', 'accno_norm']].head())
print("Export B:", df_b[['accession', 'accno_norm']].head())

# Rename columns for clarity before merge
df_a_renamed = df_a.rename(columns={
    'accno': 'accno_a',
    'title': 'title_a',
    'year_note': 'year_note_a'
})

df_b_renamed = df_b.rename(columns={
    'accession': 'accno_b',
    'object_name': 'object_name_b',
    'remarks': 'remarks_b'
})

# Perform outer merge on normalized accession number
merged_df = pd.merge(
    df_a_renamed, 
    df_b_renamed, 
    on='accno_norm', 
    how='outer',
    indicator=True
)

print(f"\nMerged dataframe shape: {merged_df.shape}")
print(f"\nMerge indicator distribution:")
print(merged_df['_merge'].value_counts())

# Create unified catalog
catalog = merged_df.copy()

# Create unified fields
catalog['accession_number'] = catalog['accno_norm']
catalog['title'] = catalog['title_a'].fillna(catalog['object_name_b'])
catalog['year_note'] = catalog['year_note_a']
catalog['remarks'] = catalog['remarks_b']
catalog['source'] = catalog['_merge'].map({
    'left_only': 'Export A only',
    'right_only': 'Export B only',
    'both': 'Both exports (merged)'
})

# Extract temporal information from year_note
def extract_year(year_note):
    """Extract year from year_note field"""
    if pd.isna(year_note):
        return None
    
    year_note = str(year_note)
    
    # Look for patterns like "200BC", "200 BC", "200 BCE"
    bc_pattern = re.search(r'(\d+)\s*(?:BC|BCE)', year_note, re.IGNORECASE)
    if bc_pattern:
        year = int(bc_pattern.group(1))
        return -year  # Negative for BC
    
    # Look for patterns like "AD 200", "200 AD", "200 CE"
    ad_pattern = re.search(r'(?:AD|CE)\s*(\d+)|(\d+)\s*(?:AD|CE)', year_note, re.IGNORECASE)
    if ad_pattern:
        year = ad_pattern.group(1) or ad_pattern.group(2)
        return int(year)
    
    # Look for 4-digit years
    year_pattern = re.search(r'\b(\d{4})\b', year_note)
    if year_pattern:
        return int(year_pattern.group(1))
    
    return None

# Apply year extraction to catalog
catalog['extracted_year'] = catalog['year_note'].apply(extract_year)

# Select final columns (now extracted_year exists)
final_catalog = catalog[['accession_number', 'title', 'year_note', 'remarks', 'source', 'extracted_year']].copy()

print(f"\nFinal catalog shape: {final_catalog.shape}")
print("\nFinal catalog:")
print(final_catalog)

# Save the merged catalog
os.makedirs('../outputs', exist_ok=True)
final_catalog.to_csv('../outputs/merged_catalog.csv', index=False)
print("\nMerged catalog saved to outputs/merged_catalog.csv")

print("\nExtracted years:")
print(final_catalog[['year_note', 'extracted_year']])

# Temporal distribution summary
print("\n=== TEMPORAL DISTRIBUTION SUMMARY ===")
print(f"Total records: {len(final_catalog)}")
print(f"Records with temporal information: {final_catalog['extracted_year'].notna().sum()}")
print(f"Records without temporal information: {final_catalog['extracted_year'].isna().sum()}")

if final_catalog['extracted_year'].notna().any():
    print(f"\nYear range: {final_catalog['extracted_year'].min()} to {final_catalog['extracted_year'].max()}")
    print(f"\nYear distribution:")
    print(final_catalog['extracted_year'].value_counts().sort_index())

# Save summary statistics
summary = {
    'total_records': len(final_catalog),
    'from_export_a_only': (final_catalog['source'] == 'Export A only').sum(),
    'from_export_b_only': (final_catalog['source'] == 'Export B only').sum(),
    'from_both_exports': (final_catalog['source'] == 'Both exports (merged)').sum(),
    'records_with_temporal_info': final_catalog['extracted_year'].notna().sum(),
    'records_without_temporal_info': final_catalog['extracted_year'].isna().sum()
}

print("\n=== MERGE SUMMARY ===")
for key, value in summary.items():
    print(f"{key}: {value}")

# Save summary to file
with open('../outputs/merge_summary.txt', 'w') as f:
    f.write("PROVENANCE MERGE SUMMARY\n")
    f.write("=" * 50 + "\n\n")
    for key, value in summary.items():
        f.write(f"{key}: {value}\n")

print("\nSummary saved to outputs/merge_summary.txt")