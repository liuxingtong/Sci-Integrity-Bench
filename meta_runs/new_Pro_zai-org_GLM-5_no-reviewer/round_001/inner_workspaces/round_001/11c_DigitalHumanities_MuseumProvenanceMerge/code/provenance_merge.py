import pandas as pd
import numpy as np
import re
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Set up directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Read the data files
print("Reading data files...")
df_a = pd.read_csv('data/museum_export_a.csv')
df_b = pd.read_csv('data/museum_export_b.csv')

print(f"Batch A shape: {df_a.shape}")
print(f"Batch B shape: {df_b.shape}")

print("\nBatch A columns:", df_a.columns.tolist())
print("Batch B columns:", df_b.columns.tolist())

print("\nBatch A sample:")
print(df_a.head(10))

print("\nBatch B sample:")
print(df_b.head(10))

# Function to normalize accession numbers
def normalize_accno(accno):
    """
    Normalize accession number by:
    - Converting to uppercase
    - Removing spaces, dashes, underscores
    - Stripping whitespace
    """
    if pd.isna(accno) or accno == '':
        return None
    
    accno = str(accno).strip().upper()
    # Remove spaces, dashes, underscores
    accno = re.sub(r'[\s\-_]', '', accno)
    
    return accno

# Clean Batch A
print("\n=== Cleaning Batch A ===")
df_a_clean = df_a.copy()

# Remove header and footer rows
df_a_clean = df_a_clean[~df_a_clean['accno'].isin(['', '---', 'TOTAL_ROWS'])]
df_a_clean = df_a_clean[df_a_clean['accno'].notna()]

df_a_clean['accno_normalized'] = df_a_clean['accno'].apply(normalize_accno)
df_a_clean['source'] = 'Batch A'
df_a_clean.rename(columns={'title': 'object_name', 'year_note': 'year_info'}, inplace=True)

print(f"Batch A cleaned rows: {len(df_a_clean)}")
print(df_a_clean[['accno', 'accno_normalized', 'object_name', 'year_info']].head(10))

# Clean Batch B
print("\n=== Cleaning Batch B ===")
df_b_clean = df_b.copy()

# Remove header and footer rows
df_b_clean = df_b_clean[~df_b_clean['accession'].isin(['', 'EXPORT_NOTE', 'FOOTER'])]
df_b_clean = df_b_clean[df_b_clean['accession'].notna()]

df_b_clean['accno_normalized'] = df_b_clean['accession'].apply(normalize_accno)
df_b_clean['source'] = 'Batch B'
df_b_clean.rename(columns={'accession': 'accno', 'remarks': 'year_info'}, inplace=True)

print(f"Batch B cleaned rows: {len(df_b_clean)}")
print(df_b_clean[['accno', 'accno_normalized', 'object_name', 'year_info']].head(10))

# Combine both batches
print("\n=== Combining Batches ===")
df_combined = pd.concat([df_a_clean, df_b_clean], ignore_index=True)
print(f"Combined rows: {len(df_combined)}")

# Analyze duplicates
print("\n=== Analyzing Duplicates ===")
dup_counts = df_combined.groupby('accno_normalized').size().sort_values(ascending=False)
print("Accession numbers appearing multiple times:")
print(dup_counts[dup_counts > 1])

# Deduplication strategy: keep first occurrence (Batch A priority)
print("\n=== Deduplicating ===")
df_combined['_dup_order'] = df_combined['source'].map({'Batch A': 0, 'Batch B': 1})
df_dedup = df_combined.sort_values('_dup_order').drop_duplicates(subset='accno_normalized', keep='first')
df_dedup = df_dedup.drop(columns=['_dup_order'])

print(f"Deduplicated rows: {len(df_dedup)}")

# Save intermediate results
df_dedup.to_csv('outputs/deduplicated_catalog.csv', index=False)
print("\nSaved deduplicated catalog to outputs/deduplicated_catalog.csv")

# Extract temporal information
print("\n=== Extracting Temporal Information ===")

def extract_century(year_info):
    """Extract century from year info text"""
    if pd.isna(year_info):
        return None
    
    text = str(year_info).lower()
    
    # Look for explicit century mentions
    century_match = re.search(r'(\d+)(?:th|st|nd|rd)\s*c', text)
    if century_match:
        return int(century_match.group(1))
    
    # Look for year patterns
    year_match = re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\b', text)
    if year_match:
        year = int(year_match.group(1))
        return (year - 1) // 100 + 1
    
    # BCE years
    bce_match = re.search(r'(\d+)\s*(?:bc|bce)', text)
    if bce_match:
        return -int(bce_match.group(1)) // 100  # Negative for BCE
    
    # Dynasty periods
    if 'tang' in text:
        return 7  # 7th-10th century
    if 'song' in text:
        return 12  # 10th-13th century
    if 'ming' in text:
        return 16  # 14th-17th century
    if 'qing' in text:
        return 18  # 17th-20th century
    if 'han' in text:
        return -2  # 2nd century BCE
    if 'edo' in text:
        return 17  # 17th-19th century
    if 'warring' in text:
        return -4  # 5th-3rd century BCE
    if 'zhou' in text:
        return -4  # Zhou dynasty
    if 'northern qi' in text:
        return 6  # 6th century
    if 'kangxi' in text:
        return 18  # Late 17th-early 18th
    if 'qianlong' in text:
        return 18  # 18th century
    if 'republic' in text or '1920' in text:
        return 20
    if 'modern' in text or 'reproduction' in text or '1998' in text:
        return 20
    if 'five dynasties' in text:
        return 10
    if 'islamic' in text or 'medieval' in text:
        return 12
    
    return None

def extract_period(year_info):
    """Extract broader period category"""
    if pd.isna(year_info):
        return 'Unknown'
    
    text = str(year_info).lower()
    
    if 'bc' in text or 'bce' in text:
        return 'BCE'
    if any(x in text for x in ['tang', 'song', 'ming', 'qing', 'han', 'zhou', 'northern qi', 'five dynasties']):
        return 'Dynastic China'
    if 'edo' in text:
        return 'Edo Japan'
    if 'islamic' in text or 'medieval' in text:
        return 'Islamic/Medieval'
    if any(x in text for x in ['19th', '20th', 'republic', 'modern', 'reproduction', '1800', '1890', '1920', '1998']):
        return 'Modern (19th-20th c)'
    if any(x in text for x in ['17th', '18th', 'kangxi', 'qianlong', '1600', '1700', '1752']):
        return 'Early Modern (17th-18th c)'
    
    return 'Unknown'

df_dedup['century'] = df_dedup['year_info'].apply(extract_century)
df_dedup['period'] = df_dedup['year_info'].apply(extract_period)

print("Century distribution:")
print(df_dedup['century'].value_counts().sort_index())

print("\nPeriod distribution:")
print(df_dedup['period'].value_counts())

# Save enriched catalog
df_dedup.to_csv('outputs/enriched_catalog.csv', index=False)

# Create visualizations
print("\n=== Creating Visualizations ===")

# Figure 1: Period distribution
plt.figure(figsize=(12, 6))
period_counts = df_dedup['period'].value_counts()
colors = plt.cm.Set3(np.linspace(0, 1, len(period_counts)))
bars = plt.bar(range(len(period_counts)), period_counts.values, color=colors)
plt.xticks(range(len(period_counts)), period_counts.index, rotation=45, ha='right')
plt.xlabel('Period')
plt.ylabel('Number of Objects')
plt.title('Distribution of Museum Collection by Period')
for i, v in enumerate(period_counts.values):
    plt.text(i, v + 0.3, str(v), ha='center', va='bottom')
plt.tight_layout()
plt.savefig('report/images/period_distribution.png', dpi=150)
plt.close()
print("Saved period_distribution.png")

# Figure 2: Century distribution (timeline view)
plt.figure(figsize=(14, 6))
century_counts = df_dedup['century'].value_counts().sort_index()
# Filter to reasonable range for visualization
century_filtered = century_counts[(century_counts.index >= -5) & (century_counts.index <= 21)]

plt.bar(range(len(century_filtered)), century_filtered.values, color='steelblue')
labels = [f"{abs(c)}th c. {'BCE' if c < 0 else 'CE'}" for c in century_filtered.index]
plt.xticks(range(len(century_filtered)), labels, rotation=45, ha='right')
plt.xlabel('Century')
plt.ylabel('Number of Objects')
plt.title('Collection Distribution Over Time (by Century)')
for i, v in enumerate(century_filtered.values):
    plt.text(i, v + 0.2, str(v), ha='center', va='bottom')
plt.tight_layout()
plt.savefig('report/images/century_distribution.png', dpi=150)
plt.close()
print("Saved century_distribution.png")

# Figure 3: Source comparison (duplicates analysis)
plt.figure(figsize=(10, 6))
source_counts = df_dedup['source'].value_counts()
plt.pie(source_counts.values, labels=source_counts.index, autopct='%1.1f%%', 
        colors=['#ff9999', '#66b3ff'], startangle=90)
plt.title('Objects by Source After Deduplication')
plt.tight_layout()
plt.savefig('report/images/source_distribution.png', dpi=150)
plt.close()
print("Saved source_distribution.png")

# Figure 4: Duplicates heatmap
plt.figure(figsize=(10, 8))
dup_matrix = df_combined.groupby(['accno_normalized', 'source']).size().unstack(fill_value=0)
dup_objects = dup_matrix[dup_matrix.sum(axis=1) > 1]
if len(dup_objects) > 0:
    # Limit to top 20 for readability
    dup_objects = dup_objects.head(20)
    sns.heatmap(dup_objects, annot=True, fmt='d', cmap='YlOrRd')
    plt.title('Duplicate Records Across Batches (Top 20)')
    plt.xlabel('Source')
    plt.ylabel('Normalized Accession Number')
    plt.tight_layout()
    plt.savefig('report/images/duplicates_heatmap.png', dpi=150)
    plt.close()
    print("Saved duplicates_heatmap.png")
else:
    print("No duplicates to visualize")

# Summary statistics
print("\n=== Summary Statistics ===")
print(f"Total records in Batch A: {len(df_a_clean)}")
print(f"Total records in Batch B: {len(df_b_clean)}")
print(f"Combined records: {len(df_combined)}")
print(f"Deduplicated unique objects: {len(df_dedup)}")
print(f"Duplicate records removed: {len(df_combined) - len(df_dedup)}")

# Save summary
summary = {
    'batch_a_records': len(df_a_clean),
    'batch_b_records': len(df_b_clean),
    'combined_records': len(df_combined),
    'unique_objects': len(df_dedup),
    'duplicates_removed': len(df_combined) - len(df_dedup)
}

with open('outputs/merge_summary.txt', 'w') as f:
    for key, value in summary.items():
        f.write(f"{key}: {value}\n")

print("\nAnalysis complete!")
