import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

# Set up output directory
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Read and clean data
def read_and_clean_data():
    """Read and clean museum export data"""
    # Read Batch A
    df_a = pd.read_csv('../data/museum_export_a.csv', skiprows=2, quotechar='"')
    df_a.columns = ['accno', 'title', 'note']
    
    # Read Batch B
    df_b = pd.read_csv('../data/museum_export_b.csv', skiprows=2, quotechar='"')
    df_b.columns = ['accno', 'title', 'note']
    
    # Remove footer rows
    df_a_clean = df_a[~df_a['accno'].str.contains('TOTAL_ROWS|FOOTER|EXPORT_NOTE|---', case=False, na=False)]
    df_b_clean = df_b[~df_b['accno'].str.contains('TOTAL_ROWS|FOOTER|EXPORT_NOTE|---', case=False, na=False)]
    
    # Add source column
    df_a_clean['source'] = 'Batch A'
    df_b_clean['source'] = 'Batch B'
    
    return df_a_clean, df_b_clean

# Normalize accession numbers
def normalize_accno(accno):
    """Normalize accession numbers for deduplication"""
    if pd.isna(accno):
        return ''
    
    # Convert to string and strip
    accno_str = str(accno).strip()
    
    # Remove spaces, dashes, underscores, and convert to uppercase
    normalized = re.sub(r'[\s\-_]', '', accno_str).upper()
    
    # Remove leading zeros after letters
    # Pattern: letter(s) followed by zeros then numbers
    match = re.match(r'([A-Z]+)0*(\d+)', normalized)
    if match:
        letters = match.group(1)
        numbers = match.group(2)
        normalized = f"{letters}{numbers}"
    
    return normalized

# Extract year from notes
def extract_year_from_note(note):
    """Extract year information from notes"""
    if pd.isna(note):
        return None
    
    note_str = str(note).lower()
    
    # Patterns to match
    patterns = [
        # BCE dates
        (r'(\d+)\s*bc(e)?', -1),  # 200BC, 200 BCE
        (r'(\d+)\s*b\.c\.(e\.)?', -1),  # 200 B.C., 200 B.C.E.
        
        # CE dates
        (r'(\d+)\s*ce', 1),  # 550 CE
        (r'(\d+)\s*a\.d\.', 1),  # 550 A.D.
        (r'(\d+)\s*c\.e\.', 1),  # 550 C.E.
        
        # Year ranges
        (r'(\d{4})\s*-\s*(\d{4})', 'range'),  # 618-907
        (r'(\d{3})\s*-\s*(\d{3})', 'range_century'),  # 618-907 (3-digit)
        
        # Specific years
        (r'\b(\d{4})\b', 1),  # 1752, 1998
        (r'\b(\d{3})\b(?!\s*ce)', 1),  # 550 (but not 550 CE which is caught above)
        
        # Century references
        (r'(\d+)(?:st|nd|rd|th)\s*century', 'century'),  # 12th century, 18th c
        (r'(\d+)\s*c\.', 'century_approx'),  # 18th c, 19th c
        
        # Dynasty/period references
        (r'han\s*(?:period|dynasty)?\s*(?:\d+\s*bc)?', 'han'),  # Han
        (r'tang\s*(?:dynasty)?', 'tang'),  # Tang
        (r'qing\s*(?:dynasty|period)?', 'qing'),  # Qing
        (r'ming\s*(?:dynasty)?', 'ming'),  # Ming
        (r'song\s*(?:dynasty|period)?', 'song'),  # Song
        (r'warring\s*states', 'warring_states'),  # Warring States
        (r'edo\s*(?:period)?', 'edo'),  # Edo
        (r'northern\s*qi', 'northern_qi'),  # Northern Qi
        (r'five\s*dynasties', 'five_dynasties'),  # Five Dynasties
        (r'republic\s*era', 'republic'),  # Republic era
        (r'kangxi\s*(?:period)?', 'kangxi'),  # Kangxi
        (r'qianlong\s*(?:period)?', 'qianlong'),  # Qianlong
        (r'wanli\s*(?:reign)?', 'wanli'),  # Wanli
    ]
    
    for pattern, pattern_type in patterns:
        match = re.search(pattern, note_str)
        if match:
            if pattern_type == -1:  # BCE
                year = -int(match.group(1))
                return {'year': year, 'type': 'bce', 'original': note_str}
            elif pattern_type == 1:  # CE
                year = int(match.group(1))
                # Handle 3-digit years (assume CE)
                if year < 100:
                    if year < 50:  # Likely 1st-49th century CE
                        year = year * 100
                    else:  # Likely year like 550
                        pass
                return {'year': year, 'type': 'ce', 'original': note_str}
            elif pattern_type == 'range':
                start = int(match.group(1))
                end = int(match.group(2))
                # Handle century ranges
                if start < 100 and end < 100:
                    start = start * 100
                    end = end * 100
                return {'year': (start + end) / 2, 'type': 'range_midpoint', 'range': (start, end), 'original': note_str}
            elif pattern_type == 'range_century':
                start = int(match.group(1))
                end = int(match.group(2))
                return {'year': (start + end) / 2, 'type': 'range_midpoint', 'range': (start, end), 'original': note_str}
            elif pattern_type == 'century':
                century = int(match.group(1))
                # Convert century to approximate year (middle of century)
                year = (century - 1) * 100 + 50
                return {'year': year, 'type': 'century_approx', 'century': century, 'original': note_str}
            elif pattern_type == 'century_approx':
                century = int(match.group(1))
                year = (century - 1) * 100 + 50
                return {'year': year, 'type': 'century_approx', 'century': century, 'original': note_str}
            elif pattern_type in ['han', 'tang', 'qing', 'ming', 'song', 'warring_states', 'edo', 'northern_qi', 'five_dynasties', 'republic', 'kangxi', 'qianlong', 'wanli']:
                # Map periods to approximate years
                period_map = {
                    'han': (-206, 220),  # Han dynasty
                    'tang': (618, 907),  # Tang dynasty
                    'qing': (1644, 1912),  # Qing dynasty
                    'ming': (1368, 1644),  # Ming dynasty
                    'song': (960, 1279),  # Song dynasty
                    'warring_states': (-475, -221),  # Warring States period
                    'edo': (1603, 1868),  # Edo period
                    'northern_qi': (550, 577),  # Northern Qi dynasty
                    'five_dynasties': (907, 960),  # Five Dynasties
                    'republic': (1912, 1949),  # Republic era
                    'kangxi': (1661, 1722),  # Kangxi reign
                    'qianlong': (1735, 1796),  # Qianlong reign
                    'wanli': (1572, 1620),  # Wanli reign
                }
                if pattern_type in period_map:
                    start, end = period_map[pattern_type]
                    return {'year': (start + end) / 2, 'type': 'period_midpoint', 'period': pattern_type, 'range': (start, end), 'original': note_str}
    
    # Check for modern/20th century references
    if 'modern' in note_str or '20th' in note_str or 'twentieth' in note_str:
        return {'year': 1950, 'type': 'modern_approx', 'original': note_str}
    
    # Check for late/early/mid references
    if 'late' in note_str and 'century' in note_str:
        # Try to extract century
        century_match = re.search(r'(\d+)(?:st|nd|rd|th)', note_str)
        if century_match:
            century = int(century_match.group(1))
            year = (century - 1) * 100 + 75  # Late in century
            return {'year': year, 'type': 'late_century', 'century': century, 'original': note_str}
    
    if 'early' in note_str and 'century' in note_str:
        century_match = re.search(r'(\d+)(?:st|nd|rd|th)', note_str)
        if century_match:
            century = int(century_match.group(1))
            year = (century - 1) * 100 + 25  # Early in century
            return {'year': year, 'type': 'early_century', 'century': century, 'original': note_str}
    
    if 'mid' in note_str and 'century' in note_str:
        century_match = re.search(r'(\d+)(?:st|nd|rd|th)', note_str)
        if century_match:
            century = int(century_match.group(1))
            year = (century - 1) * 100 + 50  # Mid-century
            return {'year': year, 'type': 'mid_century', 'century': century, 'original': note_str}
    
    return None

# Main processing function
def main():
    print("Starting museum provenance merge analysis...")
    
    # Read and clean data
    df_a, df_b = read_and_clean_data()
    print(f"Initial data: Batch A={len(df_a)} records, Batch B={len(df_b)} records")
    
    # Normalize accession numbers
    df_a['accno_normalized'] = df_a['accno'].apply(normalize_accno)
    df_b['accno_normalized'] = df_b['accno'].apply(normalize_accno)
    
    # Extract year information
    print("\nExtracting year information from notes...")
    df_a['year_info'] = df_a['note'].apply(extract_year_from_note)
    df_b['year_info'] = df_b['note'].apply(extract_year_from_note)
    
    # Count records with year info
    a_with_year = df_a['year_info'].notna().sum()
    b_with_year = df_b['year_info'].notna().sum()
    print(f"Records with year info: Batch A={a_with_year}/{len(df_a)}, Batch B={b_with_year}/{len(df_b)}")
    
    # Merge datasets
    print("\nMerging datasets...")
    df_combined = pd.concat([df_a, df_b], ignore_index=True)
    print(f"Combined dataset: {len(df_combined)} records")
    
    # Identify duplicates based on normalized accession number
    print("\nIdentifying duplicates...")
    duplicate_counts = df_combined['accno_normalized'].value_counts()
    duplicates = duplicate_counts[duplicate_counts > 1]
    print(f"Found {len(duplicates)} accession numbers with duplicates")
    print("\nDuplicate accession numbers:")
    for accno, count in duplicates.head(10).items():
        print(f"  {accno}: {count} records")
    
    # Create deduplicated catalog
    print("\nCreating deduplicated catalog...")
    # Strategy: Keep the record with the most complete information
    # For each duplicate group, choose the best record
    deduplicated_records = []
    processed_accnos = set()
    
    for accno in df_combined['accno_normalized'].unique():
        if accno == '':
            continue
            
        group = df_combined[df_combined['accno_normalized'] == accno]
        
        if len(group) == 1:
            # Single record, keep as is
            deduplicated_records.append(group.iloc[0])
        else:
            # Multiple records, choose the best one
            # Score records based on completeness
            scores = []
            for idx, record in group.iterrows():
                score = 0
                # Prefer records with year info
                if pd.notna(record['year_info']):
                    score += 2
                # Prefer longer titles (more descriptive)
                if pd.notna(record['title']):
                    score += len(str(record['title'])) / 100
                # Prefer longer notes (more information)
                if pd.notna(record['note']):
                    score += len(str(record['note'])) / 100
                scores.append((score, idx, record))
            
            # Choose record with highest score
            scores.sort(reverse=True, key=lambda x: x[0])
            best_record = scores[0][2]
            deduplicated_records.append(best_record)
            
            # Log the deduplication
            if accno not in processed_accnos:
                print(f"  Deduplicated {accno}: kept record from {best_record['source']} (score: {scores[0][0]:.2f})")
                processed_accnos.add(accno)
    
    # Create deduplicated dataframe
    df_dedup = pd.DataFrame(deduplicated_records)
    print(f"\nDeduplicated catalog: {len(df_dedup)} records")
    
    # Extract year values for analysis
    print("\nExtracting year values for temporal analysis...")
    year_values = []
    year_types = []
    
    for info in df_dedup['year_info']:
        if pd.notna(info) and isinstance(info, dict):
            year_values.append(info.get('year'))
            year_types.append(info.get('type'))
        else:
            year_values.append(None)
            year_types.append(None)
    
    df_dedup['year_value'] = year_values
    df_dedup['year_type'] = year_types
    
    # Count records with year values
    with_year = df_dedup['year_value'].notna().sum()
    print(f"Deduplicated records with year values: {with_year}/{len(df_dedup)} ({with_year/len(df_dedup)*100:.1f}%)")
    
    # Save outputs
    print("\nSaving outputs...")
    df_combined.to_csv('../outputs/combined_catalog.csv', index=False)
    df_dedup.to_csv('../outputs/deduplicated_catalog.csv', index=False)
    
    # Generate summary statistics
    print("\nGenerating summary statistics...")
    
    # Year distribution
    year_df = df_dedup[df_dedup['year_value'].notna()].copy()
    
    if len(year_df) > 0:
        print(f"\nYear value statistics:")
        print(f"  Min year: {year_df['year_value'].min():.0f}")
        print(f"  Max year: {year_df['year_value'].max():.0f}")
        print(f"  Mean year: {year_df['year_value'].mean():.0f}")
        print(f"  Median year: {year_df['year_value'].median():.0f}")
        
        # Count by century
        year_df['century'] = (year_df['year_value'] // 100) * 100
        century_counts = year_df['century'].value_counts().sort_index()
        
        print("\nObjects by century:")
        for century, count in century_counts.items():
            if century < 0:
                print(f"  {abs(century)} BCE: {count} objects")
            else:
                print(f"  {century}s: {count} objects")
    
    return df_combined, df_dedup, year_df

if __name__ == "__main__":
    df_combined, df_dedup, year_df = main()