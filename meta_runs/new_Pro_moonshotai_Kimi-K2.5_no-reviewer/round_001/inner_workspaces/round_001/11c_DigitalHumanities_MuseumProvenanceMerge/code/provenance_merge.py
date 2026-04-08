"""
Museum Provenance Merge Analysis
================================
Merge museum_export_a.csv and museum_export_b.csv into a deduplicated catalog
and analyze temporal distribution of collection items.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

print("=" * 60)
print("MUSEUM PROVENANCE MERGE ANALYSIS")
print("=" * 60)

# =============================================================================
# 1. LOAD DATA
# =============================================================================
print("\n[1] Loading museum export data...")

df_a = pd.read_csv('data/museum_export_a.csv')
df_b = pd.read_csv('data/museum_export_b.csv')

print(f"  Batch A: {len(df_a)} records")
print(f"  Batch B: {len(df_b)} records")
print(f"  Total raw records: {len(df_a) + len(df_b)}")

print("\n  Batch A columns:", list(df_a.columns))
print("  Batch A sample:")
print(df_a.head())

print("\n  Batch B columns:", list(df_b.columns))
print("  Batch B sample:")
print(df_b.head())

# =============================================================================
# 2. STANDARDIZE AND NORMALIZE ACCESSION NUMBERS
# =============================================================================
print("\n[2] Standardizing accession numbers...")

def normalize_accession(acc):
    """Normalize accession numbers to identify duplicates."""
    if pd.isna(acc):
        return None
    # Remove hyphens, spaces, and convert to uppercase
    normalized = re.sub(r'[-\s]', '', str(acc)).upper()
    return normalized

df_a['accno_norm'] = df_a['accno'].apply(normalize_accession)
df_b['accession_norm'] = df_b['accession'].apply(normalize_accession)

print("  Sample normalized accession numbers:")
print("  Batch A:", df_a[['accno', 'accno_norm']].head().to_string())
print("  Batch B:", df_b[['accession', 'accession_norm']].head().to_string())

# =============================================================================
# 3. EXTRACT TEMPORAL INFORMATION
# =============================================================================
print("\n[3] Extracting temporal information...")

def extract_year(text):
    """Extract year from text, handling BC/AD and various formats."""
    if pd.isna(text):
        return None
    
    text = str(text).upper()
    
    # Pattern for BC dates (e.g., "200BC", "200 BC", "200 B.C.")
    bc_match = re.search(r'(\d+)\s*B\.?C\.?', text)
    if bc_match:
        year = int(bc_match.group(1))
        return -year  # Negative for BC
    
    # Pattern for AD dates (e.g., "1500AD", "1500 AD")
    ad_match = re.search(r'(\d+)\s*A\.?D\.?', text)
    if ad_match:
        return int(ad_match.group(1))
    
    # Pattern for 4-digit years (assume AD if > 1000)
    year_match = re.search(r'\b(\d{3,4})\b', text)
    if year_match:
        year = int(year_match.group(1))
        if year > 1000:  # Likely AD
            return year
        else:
            return -year  # Assume BC for smaller numbers in ancient context
    
    return None

df_a['year_extracted'] = df_a['year_note'].apply(extract_year)

print("  Temporal extraction results (Batch A):")
print(df_a[['year_note', 'year_extracted']].to_string())

# =============================================================================
# 4. MERGE AND DEDUPLICATE
# =============================================================================
print("\n[4] Merging and deduplicating catalogs...")

# Standardize column names for merging
df_a_std = df_a.copy()
df_a_std['accession'] = df_a_std['accno']
df_a_std['object_name'] = df_a_std['title']
df_a_std['remarks'] = df_a_std['year_note']
df_a_std['source_batch'] = 'A'

df_b_std = df_b.copy()
df_b_std['title'] = df_b_std['object_name']
df_b_std['year_note'] = None
df_b_std['year_extracted'] = None
df_b_std['source_batch'] = 'B'

# Combine normalized accession as key
df_a_std['accession_key'] = df_a_std['accno_norm']
df_b_std['accession_key'] = df_b_std['accession_norm']

# Select common columns
columns = ['accession', 'accession_key', 'title', 'object_name', 'year_note', 'remarks', 
           'year_extracted', 'source_batch']
df_a_clean = df_a_std[columns]
df_b_clean = df_b_std[columns]

print(f"  Batch A (standardized): {len(df_a_clean)} records")
print(f"  Batch B (standardized): {len(df_b_clean)} records")

# Combine both datasets
combined = pd.concat([df_a_clean, df_b_clean], ignore_index=True)
print(f"  Combined (pre-dedup): {len(combined)} records")

# Identify duplicates based on normalized accession number
duplicates = combined[combined.duplicated(subset=['accession_key'], keep=False)]
print(f"\n  Duplicate records found: {len(duplicates)}")
if len(duplicates) > 0:
    print("  Duplicate details:")
    print(duplicates[['accession', 'accession_key', 'source_batch']].to_string())

# Deduplicate: keep first occurrence, but merge information
# For duplicates, prefer records with temporal information
def merge_duplicates(group):
    """Merge duplicate records, preferring those with more complete data."""
    # Sort by whether year_extracted is not null (prefer records with dates)
    group_sorted = group.sort_values('year_extracted', na_position='last')
    primary = group_sorted.iloc[0].copy()
    
    # Merge source batches
    batches = ', '.join(group['source_batch'].unique())
    primary['source_batch'] = batches
    
    # If primary doesn't have year but another record does, use it
    if pd.isna(primary['year_extracted']):
        for _, row in group.iterrows():
            if not pd.isna(row['year_extracted']):
                primary['year_extracted'] = row['year_extracted']
                primary['year_note'] = row['year_note']
                break
    
    return primary

# Group by accession key and merge
deduplicated = combined.groupby('accession_key').apply(merge_duplicates).reset_index(drop=True)

print(f"\n  Deduplicated catalog: {len(deduplicated)} records")
print(f"  Duplicates removed: {len(combined) - len(deduplicated)}")

# Save deduplicated catalog
deduplicated.to_csv('outputs/deduplicated_catalog.csv', index=False)
print("  Saved: outputs/deduplicated_catalog.csv")

# =============================================================================
# 5. TEMPORAL DISTRIBUTION ANALYSIS
# =============================================================================
print("\n[5] Analyzing temporal distribution...")

# Filter records with valid years
dated_records = deduplicated[deduplicated['year_extracted'].notna()].copy()
print(f"  Records with extractable dates: {len(dated_records)}")

if len(dated_records) > 0:
    print("\n  Dated records:")
    print(dated_records[['accession', 'title', 'year_extracted', 'year_note']].to_string())
    
    # Categorize by era
    def categorize_era(year):
        if year < 0:
            return 'Ancient (BC)'
        elif year < 500:
            return 'Early Medieval (0-500 AD)'
        elif year < 1000:
            return 'Medieval (500-1000 AD)'
        elif year < 1500:
            return 'Late Medieval (1000-1500 AD)'
        elif year < 1800:
            return 'Early Modern (1500-1800 AD)'
        else:
            return 'Modern (1800+ AD)'
    
    dated_records['era'] = dated_records['year_extracted'].apply(categorize_era)
    
    print("\n  Era distribution:")
    era_counts = dated_records['era'].value_counts()
    print(era_counts.to_string())
    
    # Save temporal analysis
    dated_records.to_csv('outputs/temporal_analysis.csv', index=False)
    print("  Saved: outputs/temporal_analysis.csv")

# =============================================================================
# 6. GENERATE VISUALIZATIONS
# =============================================================================
print("\n[6] Generating visualizations...")

# Figure 1: Data Source Composition
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Source batch distribution
source_counts = deduplicated['source_batch'].value_counts()
colors = sns.color_palette("husl", len(source_counts))
axes[0].pie(source_counts.values, labels=source_counts.index, autopct='%1.1f%%', 
            colors=colors, startangle=90)
axes[0].set_title('Catalog Records by Source Batch', fontsize=12, fontweight='bold')

# Deduplication summary
categories = ['Unique Records', 'Duplicates Removed']
values = [len(deduplicated), len(combined) - len(deduplicated)]
axes[1].bar(categories, values, color=['#2ecc71', '#e74c3c'])
axes[1].set_ylabel('Number of Records')
axes[1].set_title('Deduplication Results', fontsize=12, fontweight='bold')
for i, v in enumerate(values):
    axes[1].text(i, v + 0.05, str(v), ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('report/images/figure1_data_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/figure1_data_overview.png")

# Figure 2: Temporal Distribution (if we have dated records)
if len(dated_records) > 0:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Era distribution
    era_counts = dated_records['era'].value_counts()
    axes[0].barh(era_counts.index, era_counts.values, color=sns.color_palette("viridis", len(era_counts)))
    axes[0].set_xlabel('Number of Objects')
    axes[0].set_title('Distribution by Historical Era', fontsize=12, fontweight='bold')
    for i, v in enumerate(era_counts.values):
        axes[0].text(v + 0.05, i, str(v), va='center', fontweight='bold')
    
    # Timeline scatter plot
    years = dated_records['year_extracted'].values
    colors_timeline = ['red' if y < 0 else 'blue' for y in years]
    axes[1].scatter(range(len(years)), years, c=colors_timeline, s=100, alpha=0.7, edgecolors='black')
    axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5, label='BC/AD boundary')
    axes[1].set_xlabel('Object Index')
    axes[1].set_ylabel('Year')
    axes[1].set_title('Temporal Distribution Timeline', fontsize=12, fontweight='bold')
    axes[1].legend()
    
    # Add year labels
    for i, (idx, row) in enumerate(dated_records.iterrows()):
        axes[1].annotate(f"{row['year_extracted']}", 
                        (i, row['year_extracted']), 
                        textcoords="offset points", 
                        xytext=(0, 10), 
                        ha='center', fontsize=8)
    
    plt.tight_layout()
    plt.savefig('report/images/figure2_temporal_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: report/images/figure2_temporal_distribution.png")

# Figure 3: Data Completeness Analysis
fig, ax = plt.subplots(figsize=(10, 6))

completeness_data = {
    'Accession Number': deduplicated['accession'].notna().sum(),
    'Title/Object Name': deduplicated['title'].notna().sum(),
    'Temporal Data': deduplicated['year_extracted'].notna().sum(),
    'Remarks/Notes': deduplicated['remarks'].notna().sum()
}

total = len(deduplicated)
completeness_pct = {k: (v/total)*100 for k, v in completeness_data.items()}

bars = ax.bar(completeness_pct.keys(), completeness_pct.values(), 
              color=sns.color_palette("coolwarm", len(completeness_pct)))
ax.set_ylabel('Completeness (%)')
ax.set_title('Data Completeness by Field', fontsize=12, fontweight='bold')
ax.set_ylim(0, 110)

for bar, (field, pct) in zip(bars, completeness_pct.items()):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 2,
            f'{pct:.0f}%\n({completeness_data[field]}/{total})',
            ha='center', va='bottom', fontweight='bold')

plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.savefig('report/images/figure3_data_completeness.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/figure3_data_completeness.png")

# =============================================================================
# 7. SUMMARY STATISTICS
# =============================================================================
print("\n[7] Summary Statistics...")
print("=" * 60)
print(f"Total records in merged catalog: {len(deduplicated)}")
print(f"Records from Batch A: {len(deduplicated[deduplicated['source_batch'].str.contains('A')])}")
print(f"Records from Batch B: {len(deduplicated[deduplicated['source_batch'].str.contains('B')])}")
print(f"Records with temporal data: {len(dated_records)} ({len(dated_records)/len(deduplicated)*100:.1f}%)")

if len(dated_records) > 0:
    years = dated_records['year_extracted'].values
    print(f"Date range: {min(years)} to {max(years)}")
    bc_count = sum(1 for y in years if y < 0)
    ad_count = sum(1 for y in years if y >= 0)
    print(f"  BC records: {bc_count}")
    print(f"  AD records: {ad_count}")

print("=" * 60)
print("Analysis complete!")
