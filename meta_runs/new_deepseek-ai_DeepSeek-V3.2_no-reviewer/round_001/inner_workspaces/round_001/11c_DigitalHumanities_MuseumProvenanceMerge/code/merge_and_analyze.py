import pandas as pd
import numpy as np
import re
from datetime import datetime
import matplotlib.pyplot as plt
import os

# Create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load the datasets
print("Loading datasets...")
df_a = pd.read_csv('data/museum_export_a.csv')
df_b = pd.read_csv('data/museum_export_b.csv')

print(f"Dataset A shape: {df_a.shape}")
print(f"Dataset B shape: {df_b.shape}")
print("\nDataset A columns:", df_a.columns.tolist())
print("Dataset B columns:", df_b.columns.tolist())

# Standardize column names for merging
# Based on inspection, we need to map:
# accno <-> accession
# title <-> object_name  
# year_note <-> remarks

# Rename columns in df_b to match df_a
df_b_renamed = df_b.rename(columns={
    'accession': 'accno',
    'object_name': 'title',
    'remarks': 'year_note'
})

print("\nAfter renaming df_b columns:")
print(df_b_renamed.columns.tolist())

# Check for duplicates based on accession number
# Note: df_a has 'X-100' and df_b has 'X100' - these might be the same
print("\nUnique accession numbers in df_a:", df_a['accno'].unique())
print("Unique accession numbers in df_b_renamed:", df_b_renamed['accno'].unique())

# Let's create a function to normalize accession numbers
def normalize_accno(accno):
    if pd.isna(accno):
        return ''
    # Remove hyphens and spaces, convert to uppercase
    return str(accno).replace('-', '').replace(' ', '').upper()

# Apply normalization
df_a['accno_normalized'] = df_a['accno'].apply(normalize_accno)
df_b_renamed['accno_normalized'] = df_b_renamed['accno'].apply(normalize_accno)

print("\nNormalized accession numbers:")
print("df_a:", df_a['accno_normalized'].unique())
print("df_b_renamed:", df_b_renamed['accno_normalized'].unique())

# Now merge/concatenate the datasets
combined = pd.concat([df_a, df_b_renamed], ignore_index=True)
print(f"\nCombined dataset shape: {combined.shape}")
print("\nCombined dataset:")
print(combined)

# Identify duplicates based on normalized accession number
duplicate_mask = combined.duplicated(subset=['accno_normalized'], keep='first')
duplicates = combined[duplicate_mask]
unique_combined = combined[~duplicate_mask].copy()

print(f"\nNumber of duplicates found: {len(duplicates)}")
print(f"Number of unique records: {len(unique_combined)}")

if len(duplicates) > 0:
    print("\nDuplicate records:")
    print(duplicates)

print("\nUnique records (deduplicated catalog):")
print(unique_combined)

# Save the deduplicated catalog
unique_combined.to_csv('outputs/deduplicated_catalog.csv', index=False)
print("\nDeduplicated catalog saved to outputs/deduplicated_catalog.csv")

# Now extract temporal information from year_note
# This is a text field that might contain year information
def extract_year_from_note(text):
    if pd.isna(text):
        return None
    
    # Look for patterns like 200BC, 200 BC, 200 BCE, 200AD, 200 AD, 200 CE
    # Also look for 4-digit years like 1200, 1500, 1800, 1900, 2000
    
    text = str(text).upper()
    
    # Pattern for BC/BCE years
    bc_pattern = r'(\d+)\s*(BC|BCE|B\.C\.|B\.C\.E\.)'
    bc_match = re.search(bc_pattern, text)
    if bc_match:
        year = int(bc_match.group(1))
        return -year  # Negative for BC years
    
    # Pattern for AD/CE years
    ad_pattern = r'(\d+)\s*(AD|CE|A\.D\.|C\.E\.)'
    ad_match = re.search(ad_pattern, text)
    if ad_match:
        year = int(ad_match.group(1))
        return year
    
    # Pattern for standalone 1-4 digit numbers (assume AD if not specified)
    year_pattern = r'\b(\d{1,4})\b'
    year_match = re.search(year_pattern, text)
    if year_match:
        year = int(year_match.group(1))
        # If year is 1-99, assume it's AD year like 50 AD
        if year < 100:
            return year
        # If year is 1000-2999, assume it's a full year
        elif 1000 <= year <= 2999:
            return year
    
    return None

# Apply year extraction
unique_combined['extracted_year'] = unique_combined['year_note'].apply(extract_year_from_note)

print("\nYear extraction results:")
for idx, row in unique_combined.iterrows():
    print(f"{row['accno']}: '{row['year_note']}' -> {row['extracted_year']}")

# Save the catalog with extracted years
unique_combined.to_csv('outputs/catalog_with_years.csv', index=False)
print("\nCatalog with extracted years saved to outputs/catalog_with_years.csv")

# Create temporal distribution summary
print("\n" + "="*50)
print("TEMPORAL DISTRIBUTION SUMMARY")
print("="*50)

# Count records with extracted years
years_extracted = unique_combined['extracted_year'].dropna()
print(f"\nRecords with extractable year information: {len(years_extracted)} out of {len(unique_combined)}")

if len(years_extracted) > 0:
    # Convert to numeric for calculations
    years_numeric = pd.to_numeric(years_extracted, errors='coerce')
    years_numeric = years_numeric.dropna()
    
    if len(years_numeric) > 0:
        print(f"\nYear statistics:")
        print(f"  Earliest year: {years_numeric.min()}")
        print(f"  Latest year: {years_numeric.max()}")
        print(f"  Mean year: {years_numeric.mean():.1f}")
        print(f"  Median year: {years_numeric.median():.1f}")
        
        # Create histogram of years
        plt.figure(figsize=(10, 6))
        
        # For BC/AD timeline, we need special handling
        # Separate BC and AD years for better visualization
        bc_years = years_numeric[years_numeric < 0]
        ad_years = years_numeric[years_numeric >= 0]
        
        if len(bc_years) > 0 or len(ad_years) > 0:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            if len(bc_years) > 0:
                # Convert BC years to positive for histogram
                bc_years_pos = abs(bc_years)
                ax1.hist(bc_years_pos, bins=min(10, len(bc_years)), edgecolor='black', alpha=0.7)
                ax1.set_title('BC/BCE Years Distribution')
                ax1.set_xlabel('Year (BC/BCE)')
                ax1.set_ylabel('Count')
                ax1.invert_xaxis()  # So earlier years are on the right
                
            if len(ad_years) > 0:
                ax2.hist(ad_years, bins=min(10, len(ad_years)), edgecolor='black', alpha=0.7, color='green')
                ax2.set_title('AD/CE Years Distribution')
                ax2.set_xlabel('Year (AD/CE)')
                ax2.set_ylabel('Count')
                
            plt.tight_layout()
            plt.savefig('report/images/temporal_distribution.png', dpi=300, bbox_inches='tight')
            print("\nTemporal distribution plot saved to report/images/temporal_distribution.png")
        else:
            # If all years are one type, use a single plot
            plt.hist(years_numeric, bins=min(10, len(years_numeric)), edgecolor='black', alpha=0.7)
            plt.title('Temporal Distribution of Museum Objects')
            plt.xlabel('Year (negative = BC/BCE, positive = AD/CE)')
            plt.ylabel('Count')
            plt.grid(True, alpha=0.3)
            plt.savefig('report/images/temporal_distribution.png', dpi=300, bbox_inches='tight')
            print("\nTemporal distribution plot saved to report/images/temporal_distribution.png")
        
        # Create a timeline visualization
        plt.figure(figsize=(12, 4))
        
        # Create a simple timeline with points for each object
        y_positions = np.zeros(len(years_numeric))
        colors = ['red' if year < 0 else 'blue' for year in years_numeric]
        
        plt.scatter(years_numeric, y_positions, c=colors, alpha=0.6, s=100)
        plt.axvline(x=0, color='black', linestyle='--', alpha=0.5, label='BC/AD Divide')
        plt.xlabel('Year (negative = BC/BCE, positive = AD/CE)')
        plt.title('Timeline of Museum Objects')
        plt.yticks([])
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('report/images/timeline.png', dpi=300, bbox_inches='tight')
        print("Timeline plot saved to report/images/timeline.png")
        
        # Create a summary table by century
        print("\nDistribution by century:")
        
        def century_from_year(year):
            if pd.isna(year):
                return 'Unknown'
            year_int = int(year)
            if year_int < 0:
                # For BC years: 200 BC is 3rd century BC
                century = abs(year_int) // 100 + 1
                return f"{century}th century BC"
            else:
                # For AD years: 200 AD is 3rd century AD
                century = year_int // 100 + 1
                return f"{century}th century AD"
        
        unique_combined['century'] = unique_combined['extracted_year'].apply(century_from_year)
        century_counts = unique_combined['century'].value_counts()
        
        for century, count in century_counts.items():
            print(f"  {century}: {count} objects")
        
        # Save century distribution
        century_counts.to_csv('outputs/century_distribution.csv')
        print("\nCentury distribution saved to outputs/century_distribution.csv")
        
        # Create century distribution bar chart
        plt.figure(figsize=(10, 6))
        century_counts.plot(kind='bar', color='skyblue', edgecolor='black')
        plt.title('Distribution of Objects by Century')
        plt.xlabel('Century')
        plt.ylabel('Number of Objects')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('report/images/century_distribution.png', dpi=300, bbox_inches='tight')
        print("Century distribution plot saved to report/images/century_distribution.png")
    else:
        print("\nNo valid numeric years could be extracted.")
else:
    print("\nNo year information could be extracted from the records.")

print("\nAnalysis complete!")