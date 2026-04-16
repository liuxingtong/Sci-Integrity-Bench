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

# Improved function to normalize accession numbers
def normalize_accno(accno):
    """
    Normalize accession number by:
    - Converting to uppercase
    - Removing spaces, dashes, underscores
    - Removing leading zeros in numeric portion
    - Stripping whitespace
    """
    if pd.isna(accno) or accno == '':
        return None
    
    accno = str(accno).strip().upper()
    # Remove spaces, dashes, underscores
    accno = re.sub(r'[\s\-_]', '', accno)
    
    # Extract letter prefix and number
    match = re.match(r'^([A-Z]+)0*(\d+)([A-Z]*)$', accno)
    if match:
        prefix = match.group(1)
        number = match.group(2).lstrip('0') or '0'  # Remove leading zeros
        suffix = match.group(3)
        return f"{prefix}{number}{suffix}"
    
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

# Show normalized accession numbers
print("\nNormalized accession numbers in deduplicated catalog:")
print(df_dedup['accno_normalized'].sort_values().tolist())

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

def extract_year_range(year_info):
    """Extract approximate year range for timeline visualization"""
    if pd.isna(year_info):
        return None, None
    
    text = str(year_info).lower()
    
    # BCE years
    bce_match = re.search(r'(\d+)\s*(?:bc|bce)', text)
    if bce_match:
        year = -int(bce_match.group(1))
        return year, year
    
    # Look for explicit year
    year_match = re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\b', text)
    if year_match:
        year = int(year_match.group(1))
        return year, year
    
    # Dynasty periods - approximate midpoints
    period_ranges = {
        'tang': (618, 907),
        'song': (960, 1279),
        'ming': (1368, 1644),
        'qing': (1644, 1912),
        'han': (-206, 220),
        'edo': (1603, 1868),
        'warring': (-475, -221),
        'zhou': (-1046, -256),
        'northern qi': (550, 577),
        'five dynasties': (907, 960),
    }
    
    for period, (start, end) in period_ranges.items():
        if period in text:
            return start, end
    
    # Century-based ranges
    century_match = re.search(r'(\d+)(?:th|st|nd|rd)\s*c', text)
    if century_match:
        c = int(century_match.group(1))
        start = (c - 1) * 100 + 1
        end = c * 100
        return start, end
    
    return None, None

df_dedup['century'] = df_dedup['year_info'].apply(extract_century)
df_dedup['period'] = df_dedup['year_info'].apply(extract_period)
df_dedup[['year_start', 'year_end']] = df_dedup['year_info'].apply(lambda x: pd.Series(extract_year_range(x)))

print("Century distribution:")
print(df_dedup['century'].value_counts().sort_index())

print("\nPeriod distribution:")
print(df_dedup['period'].value_counts())

# Save enriched catalog
df_dedup.to_csv('outputs/enriched_catalog.csv', index=False)

# Create visualizations
print("\n=== Creating Visualizations ===")

# Set style
plt.style.use('seaborn-v0_8-whitegrid')

# Figure 1: Period distribution
fig, ax = plt.subplots(figsize=(12, 6))
period_counts = df_dedup['period'].value_counts()
colors = plt.cm.Set3(np.linspace(0, 1, len(period_counts)))
bars = ax.bar(range(len(period_counts)), period_counts.values, color=colors, edgecolor='black', linewidth=0.5)
ax.set_xticks(range(len(period_counts)))
ax.set_xticklabels(period_counts.index, rotation=45, ha='right', fontsize=10)
ax.set_xlabel('Period', fontsize=12)
ax.set_ylabel('Number of Objects', fontsize=12)
ax.set_title('Distribution of Museum Collection by Historical Period', fontsize=14, fontweight='bold')
for i, v in enumerate(period_counts.values):
    ax.text(i, v + 0.2, str(v), ha='center', va='bottom', fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/period_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved period_distribution.png")

# Figure 2: Timeline visualization
fig, ax = plt.subplots(figsize=(14, 8))

# Filter objects with year data
df_timeline = df_dedup[df_dedup['year_start'].notna()].copy()
df_timeline = df_timeline.sort_values('year_start')

# Create timeline
y_positions = range(len(df_timeline))
for i, (idx, row) in enumerate(df_timeline.iterrows()):
    start = row['year_start']
    end = row['year_end'] if pd.notna(row['year_end']) else start
    
    # Color by period
    period_colors = {
        'BCE': '#8B4513',
        'Dynastic China': '#DAA520',
        'Edo Japan': '#CD853F',
        'Islamic/Medieval': '#9370DB',
        'Early Modern (17th-18th c)': '#4682B4',
        'Modern (19th-20th c)': '#2E8B57',
        'Unknown': '#808080'
    }
    color = period_colors.get(row['period'], '#808080')
    
    ax.barh(i, end - start, left=start, height=0.6, color=color, alpha=0.8, edgecolor='black', linewidth=0.5)

ax.set_yticks(y_positions)
ax.set_yticklabels([f"{row['accno_normalized']} - {row['object_name'][:20]}..." for idx, row in df_timeline.iterrows()], fontsize=8)
ax.set_xlabel('Year (CE, negative = BCE)', fontsize=12)
ax.set_title('Collection Timeline: Object Date Ranges', fontsize=14, fontweight='bold')

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=color, label=period, alpha=0.8) for period, color in period_colors.items() if period in df_timeline['period'].values]
ax.legend(handles=legend_elements, loc='upper left', fontsize=9)

# Add vertical line at year 0
ax.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='Year 0')

plt.tight_layout()
plt.savefig('report/images/collection_timeline.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved collection_timeline.png")

# Figure 3: Century distribution (bar chart)
fig, ax = plt.subplots(figsize=(12, 6))
century_counts = df_dedup['century'].value_counts().sort_index()

# Create labels for centuries
century_labels = []
for c in century_counts.index:
    if c < 0:
        century_labels.append(f"{abs(int(c))}th c. BCE")
    else:
        century_labels.append(f"{int(c)}th c. CE")

colors = ['#8B4513' if c < 0 else '#4682B4' for c in century_counts.index]
bars = ax.bar(range(len(century_counts)), century_counts.values, color=colors, edgecolor='black', linewidth=0.5)
ax.set_xticks(range(len(century_counts)))
ax.set_xticklabels(century_labels, rotation=45, ha='right', fontsize=10)
ax.set_xlabel('Century', fontsize=12)
ax.set_ylabel('Number of Objects', fontsize=12)
ax.set_title('Collection Distribution by Century', fontsize=14, fontweight='bold')
for i, v in enumerate(century_counts.values):
    ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig('report/images/century_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved century_distribution.png")

# Figure 4: Source distribution after deduplication
fig, ax = plt.subplots(figsize=(8, 6))
source_counts = df_dedup['source'].value_counts()
colors = ['#ff9999', '#66b3ff']
wedges, texts, autotexts = ax.pie(source_counts.values, labels=source_counts.index, autopct='%1.1f%%', 
        colors=colors, startangle=90, explode=[0.02, 0.02], shadow=True)
ax.set_title('Objects by Source After Deduplication', fontsize=14, fontweight='bold')
for autotext in autotexts:
    autotext.set_fontsize(12)
    autotext.set_fontweight('bold')
plt.tight_layout()
plt.savefig('report/images/source_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved source_distribution.png")

# Figure 5: Duplicates analysis heatmap
fig, ax = plt.subplots(figsize=(10, 8))
dup_matrix = df_combined.groupby(['accno_normalized', 'source']).size().unstack(fill_value=0)
dup_objects = dup_matrix[dup_matrix.sum(axis=1) > 1]
if len(dup_objects) > 0:
    # Limit to top 20 for readability
    dup_objects = dup_objects.head(20)
    sns.heatmap(dup_objects, annot=True, fmt='d', cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Record Count'})
    ax.set_title('Duplicate Records Across Batches (Top 20)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Source', fontsize=12)
    ax.set_ylabel('Normalized Accession Number', fontsize=12)
    plt.tight_layout()
    plt.savefig('report/images/duplicates_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved duplicates_heatmap.png")
else:
    print("No duplicates to visualize")

# Figure 6: Objects per period with breakdown
fig, ax = plt.subplots(figsize=(14, 6))
period_source = df_dedup.groupby(['period', 'source']).size().unstack(fill_value=0)
period_source.plot(kind='bar', ax=ax, color=['#ff9999', '#66b3ff'], edgecolor='black', linewidth=0.5)
ax.set_xlabel('Period', fontsize=12)
ax.set_ylabel('Number of Objects', fontsize=12)
ax.set_title('Collection Distribution by Period and Source', fontsize=14, fontweight='bold')
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.legend(title='Source', fontsize=10)
plt.tight_layout()
plt.savefig('report/images/period_by_source.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved period_by_source.png")

# Summary statistics
print("\n=== Summary Statistics ===")
print(f"Total records in Batch A: {len(df_a_clean)}")
print(f"Total records in Batch B: {len(df_b_clean)}")
print(f"Combined records: {len(df_combined)}")
print(f"Deduplicated unique objects: {len(df_dedup)}")
print(f"Duplicate records removed: {len(df_combined) - len(df_dedup)}")

# Count unique accession numbers
unique_accnos = df_combined['accno_normalized'].nunique()
print(f"Unique accession numbers: {unique_accnos}")

# Save summary statistics
summary_stats = {
    'batch_a_records': len(df_a_clean),
    'batch_b_records': len(df_b_clean),
    'combined_records': len(df_combined),
    'unique_objects': len(df_dedup),
    'duplicates_removed': len(df_combined) - len(df_dedup),
    'unique_accession_numbers': unique_accnos
}

# Save detailed duplicate analysis
dup_analysis = df_combined.groupby('accno_normalized').agg({
    'accno': lambda x: list(x),
    'source': lambda x: list(x),
    'object_name': lambda x: list(x)
}).reset_index()
dup_analysis['record_count'] = dup_analysis['accno'].apply(len)
dup_analysis = dup_analysis.sort_values('record_count', ascending=False)
dup_analysis.to_csv('outputs/duplicate_analysis.csv', index=False)

# Save final catalog
df_dedup.to_csv('outputs/final_catalog.csv', index=False)

print("\nAnalysis complete!")
print(f"Final catalog saved to outputs/final_catalog.csv")
