#!/usr/bin/env python3
"""
Museum Provenance Merge Analysis
Merges museum_export_a.csv and museum_export_b.csv into a deduplicated catalog
and analyzes the temporal distribution of the collection.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import re
import os
from collections import Counter

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOAD RAW DATA
# ─────────────────────────────────────────────────────────────────────────────

def load_raw(path, acc_col, name_col, note_col):
    """Load a CSV, skip blank rows and known non-object rows."""
    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={acc_col: 'raw_acc', name_col: 'title', note_col: 'notes'})
    # Drop rows where accession is blank or known system rows
    system_tokens = {'TOTAL_ROWS', 'EXPORT_NOTE', 'FOOTER', '---'}
    df['raw_acc'] = df['raw_acc'].fillna('').str.strip()
    df = df[df['raw_acc'] != '']
    df = df[~df['raw_acc'].isin(system_tokens)]
    # Drop the vendor header row that slipped in
    df = df[~df['raw_acc'].str.startswith('---')]
    df['title'] = df['title'].fillna('').str.strip()
    df['notes'] = df['notes'].fillna('').str.strip()
    return df.reset_index(drop=True)

df_a = load_raw('data/museum_export_a.csv', 'accno', 'title', 'year_note')
df_b = load_raw('data/museum_export_b.csv', 'accession', 'object_name', 'remarks')

print(f"Batch A raw rows: {len(df_a)}")
print(f"Batch B raw rows: {len(df_b)}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. NORMALISE ACCESSION NUMBERS
# ─────────────────────────────────────────────────────────────────────────────

def normalise_acc(acc):
    """
    Normalise accession numbers:
    - strip whitespace
    - uppercase
    - remove separators (-, _, space) between letter prefix and digits
    e.g. X-100, X 100, x_100 → X100
         T-088 → T88 (strip leading zeros after prefix)
    We only strip leading zeros when the numeric part has 3+ digits
    (to avoid collapsing meaningful short IDs like A001 → A1).
    """
    acc = str(acc).strip().upper()
    # Remove separators between letter prefix and numeric part
    acc = re.sub(r'([A-Z]+)[-_ ]+([0-9])', r'\1\2', acc)
    # Remove trailing spaces
    acc = acc.strip()
    # Strip leading zeros only when numeric suffix has 3+ digits
    # e.g. T088 → T88, K012 → K12, but A001 stays A001 (3 digits, leading zero)
    # Actually: strip leading zeros from numeric suffix uniformly for consistency
    # T-088 and T88 must match; K-012 and K12 must match
    # A-001 and A001 must match (both → A1 is fine as internal key)
    acc = re.sub(r'([A-Z]+)(0+)([1-9][0-9]*)', r'\1\3', acc)
    return acc

df_a['norm_acc'] = df_a['raw_acc'].apply(normalise_acc)
df_b['norm_acc'] = df_b['raw_acc'].apply(normalise_acc)

print("\nBatch A normalised accessions:")
print(df_a[['raw_acc','norm_acc']].to_string())
print("\nBatch B normalised accessions:")
print(df_b[['raw_acc','norm_acc']].to_string())

# ─────────────────────────────────────────────────────────────────────────────
# 3. FLAG KNOWN TYPO / MISMATCHED IDs
# ─────────────────────────────────────────────────────────────────────────────
# T88x in batch B is a known typo for T88
df_b.loc[df_b['norm_acc'] == 'T88X', 'norm_acc'] = 'T88'
df_b.loc[df_b['raw_acc'].str.strip().str.upper() == 'T88X', 'notes'] = \
    df_b.loc[df_b['raw_acc'].str.strip().str.upper() == 'T88X', 'notes'] + ' [typo corrected to T88]'

# ─────────────────────────────────────────────────────────────────────────────
# 4. COMBINE AND DEDUPLICATE
# ─────────────────────────────────────────────────────────────────────────────

df_a['source'] = 'A'
df_b['source'] = 'B'

combined = pd.concat([df_a, df_b], ignore_index=True)
print(f"\nCombined rows before dedup: {len(combined)}")

# For each normalised accession, keep the row with the most informative title
# (longest non-empty title) and merge notes from all duplicates.
def merge_group(grp):
    # Best title: longest
    best_title_idx = grp['title'].str.len().idxmax()
    best_title = grp.loc[best_title_idx, 'title']
    # Collect all raw accessions seen
    raw_accs = '; '.join(sorted(set(grp['raw_acc'].tolist())))
    # Collect all notes
    all_notes = '; '.join([n for n in grp['notes'].tolist() if n])
    # Sources
    sources = ','.join(sorted(set(grp['source'].tolist())))
    return pd.Series({
        'norm_acc': grp['norm_acc'].iloc[0],
        'title': best_title,
        'raw_acc_variants': raw_accs,
        'notes': all_notes,
        'sources': sources,
        'dup_count': len(grp)
    })

catalog = combined.groupby('norm_acc', sort=False).apply(merge_group).reset_index(drop=True)
print(f"Deduplicated catalog entries: {len(catalog)}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. DATE EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

# Map known accession prefixes / notes to approximate date ranges
# We'll extract a representative midpoint year for timeline analysis.

DATE_RULES = [
    # (pattern in notes/title, approx_start, approx_end, period_label)
    # More specific / later periods first to avoid false matches
    (r'republic|1920s|early 20th c', 1912, 1949, 'Republic Era (1912–1949)'),
    (r'1998|reproduction|replica|modern|20th c copy', 1900, 2000, 'Modern / Reproduction'),
    (r'19th c|1800s|1890|1880|late 19th', 1800, 1900, '19th Century'),
    (r'qing|kangxi|qianlong|1752|wanli|late qing', 1644, 1912, 'Qing (1644–1912)'),
    (r'edo|japan.*1600s|1600s.*japan|17th c', 1603, 1868, 'Edo (1603–1868)'),
    (r'ming|15th c|1400s', 1368, 1644, 'Ming (1368–1644)'),
    (r'islamic|12th c|medieval', 1100, 1200, 'Islamic / Medieval (12th c)'),
    (r'song|longquan|southern song', 960, 1279, 'Song (960–1279)'),
    (r'five dynasties|10th c', 907, 960, 'Five Dynasties (907–960)'),
    (r'tang|618.907', 618, 907, 'Tang (618–907)'),
    (r'northern qi|550\s*ce', 550, 577, 'Northern Qi (550–577)'),
    # Warring States BEFORE Han so it takes priority for iron sword etc.
    (r'warring states|400.200 bce|zhou', -475, -221, 'Warring States / Zhou'),
    (r'han|206\s*bce|206\s*bc|200\s*bc|206 bce.220 ce', -206, 220, 'Han (206 BCE–220 CE)'),

    (r'northern qi|550\s*ce', 550, 577, 'Northern Qi (550–577)'),
    (r'tang|618.907', 618, 907, 'Tang (618–907)'),
    (r'song|longquan|southern song', 960, 1279, 'Song (960–1279)'),
    (r'five dynasties|10th c', 907, 960, 'Five Dynasties (907–960)'),
    (r'ming|wanli|15th c|1400s', 1368, 1644, 'Ming (1368–1644)'),
    (r'qing|kangxi|qianlong|18th c|1752|1700s|mid.1700s|late qing|19th c.*qing', 1644, 1912, 'Qing (1644–1912)'),
    (r'edo|japan.*1600s|1600s.*japan|17th c', 1603, 1868, 'Edo (1603–1868)'),
    (r'islamic|12th c|medieval', 1100, 1200, 'Islamic / Medieval (12th c)'),
    (r'republic|1920s|early 20th c', 1912, 1949, 'Republic Era (1912–1949)'),
    (r'19th c|1800s|1890|1880|late 19th', 1800, 1900, '19th Century'),
    (r'1998|reproduction|replica|modern|20th c copy', 1900, 2000, 'Modern / Reproduction'),
]

def extract_date(row):
    combined_text = (row['title'] + ' ' + row['notes']).lower()
    for pattern, start, end, label in DATE_RULES:
        if re.search(pattern, combined_text):
            return pd.Series({'year_start': start, 'year_end': end,
                              'year_mid': (start + end) / 2, 'period_label': label})
    return pd.Series({'year_start': np.nan, 'year_end': np.nan,
                      'year_mid': np.nan, 'period_label': 'Unknown / Undated'})

date_info = catalog.apply(extract_date, axis=1)
catalog = pd.concat([catalog, date_info], axis=1)

print("\nCatalog with dates:")
print(catalog[['norm_acc','title','period_label','year_mid']].to_string())

# ─────────────────────────────────────────────────────────────────────────────
# 6. SAVE CATALOG
# ─────────────────────────────────────────────────────────────────────────────

os.makedirs('outputs', exist_ok=True)
catalog.to_csv('outputs/deduplicated_catalog.csv', index=False)
print("\nSaved outputs/deduplicated_catalog.csv")

# ─────────────────────────────────────────────────────────────────────────────
# 7. SUMMARY STATISTICS
# ─────────────────────────────────────────────────────────────────────────────

total_objects = len(catalog)
total_raw = len(combined)
duplicates_removed = total_raw - total_objects
only_in_a = len(catalog[catalog['sources'] == 'A'])
only_in_b = len(catalog[catalog['sources'] == 'B'])
in_both = len(catalog[catalog['sources'] == 'A,B'])

print(f"\n=== SUMMARY ===")
print(f"Total raw rows (both batches): {total_raw}")
print(f"Unique objects after dedup:    {total_objects}")
print(f"Duplicates removed:            {duplicates_removed}")
print(f"Objects only in Batch A:       {only_in_a}")
print(f"Objects only in Batch B:       {only_in_b}")
print(f"Objects in both batches:       {in_both}")

period_counts = catalog['period_label'].value_counts()
print("\nObjects by period:")
print(period_counts)

# ─────────────────────────────────────────────────────────────────────────────
# 8. VISUALISATIONS
# ─────────────────────────────────────────────────────────────────────────────

os.makedirs('report/images', exist_ok=True)

# ── Figure 1: Bar chart of objects by period ──────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
period_order = catalog.dropna(subset=['year_mid']).sort_values('year_mid')['period_label'].unique().tolist()
if 'Unknown / Undated' in period_counts.index:
    period_order.append('Unknown / Undated')

counts_ordered = [period_counts.get(p, 0) for p in period_order]
colors = plt.cm.tab20(np.linspace(0, 1, len(period_order)))
bars = ax.barh(period_order, counts_ordered, color=colors, edgecolor='white', linewidth=0.8)
ax.set_xlabel('Number of Objects', fontsize=12)
ax.set_title('Collection Distribution by Historical Period', fontsize=14, fontweight='bold')
for bar, count in zip(bars, counts_ordered):
    ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
            str(count), va='center', fontsize=10)
ax.set_xlim(0, max(counts_ordered) + 1.5)
plt.tight_layout()
plt.savefig('report/images/fig1_period_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_period_distribution.png")

# ── Figure 2: Timeline scatter of objects ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 5))
dated = catalog.dropna(subset=['year_mid']).copy()
undated = catalog[catalog['year_mid'].isna()].copy()

# Assign y-jitter for readability
np.random.seed(42)
dated['y_jitter'] = np.random.uniform(-0.3, 0.3, len(dated))

scatter = ax.scatter(dated['year_mid'], dated['y_jitter'],
                     c=dated['year_mid'], cmap='plasma',
                     s=80, alpha=0.85, edgecolors='grey', linewidths=0.5)

# Annotate each point with accession number
for _, row in dated.iterrows():
    ax.annotate(row['norm_acc'], (row['year_mid'], row['y_jitter']),
                fontsize=6.5, ha='center', va='bottom',
                xytext=(0, 5), textcoords='offset points')

cbar = plt.colorbar(scatter, ax=ax, orientation='horizontal', pad=0.15, fraction=0.04)
cbar.set_label('Approximate Year (CE; negative = BCE)', fontsize=9)
ax.axvline(0, color='black', linewidth=0.8, linestyle='--', alpha=0.5)
ax.text(0, 0.35, 'CE/BCE', fontsize=8, ha='center')
ax.set_yticks([])
ax.set_xlabel('Approximate Year', fontsize=12)
ax.set_title('Timeline of Collection Objects (Dated Items)', fontsize=14, fontweight='bold')
ax.set_xlim(dated['year_mid'].min() - 100, dated['year_mid'].max() + 100)
plt.tight_layout()
plt.savefig('report/images/fig2_timeline_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_timeline_scatter.png")

# ── Figure 3: Source overlap (Venn-style bar) ─────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
categories = ['Only in Batch A', 'In Both Batches', 'Only in Batch B']
values = [only_in_a, in_both, only_in_b]
bar_colors = ['#4C72B0', '#55A868', '#C44E52']
bars = ax.bar(categories, values, color=bar_colors, edgecolor='white', linewidth=1.2, width=0.5)
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            str(val), ha='center', va='bottom', fontsize=12, fontweight='bold')
ax.set_ylabel('Number of Objects', fontsize=12)
ax.set_title('Object Overlap Between Batch A and Batch B', fontsize=13, fontweight='bold')
ax.set_ylim(0, max(values) + 2)
plt.tight_layout()
plt.savefig('report/images/fig3_source_overlap.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_source_overlap.png")

# ── Figure 4: Century-level histogram ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
dated_ce = dated[dated['year_mid'] >= -500].copy()
bins = list(range(-500, 2100, 100))
ax.hist(dated_ce['year_mid'], bins=bins, color='steelblue', edgecolor='white', linewidth=0.7)
ax.set_xlabel('Approximate Year (CE; negative = BCE)', fontsize=12)
ax.set_ylabel('Number of Objects', fontsize=12)
ax.set_title('Collection Density by Century', fontsize=14, fontweight='bold')
ax.axvline(0, color='red', linewidth=1, linestyle='--', alpha=0.6, label='BCE/CE boundary')
ax.legend(fontsize=10)
plt.tight_layout()
plt.savefig('report/images/fig4_century_histogram.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig4_century_histogram.png")

# ── Figure 5: Duplicate count distribution ────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4))
dup_counts = catalog['dup_count'].value_counts().sort_index()
ax.bar(dup_counts.index.astype(str), dup_counts.values,
       color='coral', edgecolor='white', linewidth=1)
ax.set_xlabel('Number of Raw Rows per Object', fontsize=12)
ax.set_ylabel('Number of Objects', fontsize=12)
ax.set_title('Duplicate Row Frequency per Unique Object', fontsize=13, fontweight='bold')
for x, y in zip(dup_counts.index, dup_counts.values):
    ax.text(str(x), y + 0.1, str(y), ha='center', va='bottom', fontsize=11)
plt.tight_layout()
plt.savefig('report/images/fig5_dup_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig5_dup_distribution.png")

print("\nAll figures saved. Analysis complete.")

# ─────────────────────────────────────────────────────────────────────────────
# 9. SAVE SUMMARY STATS FOR REPORT
# ─────────────────────────────────────────────────────────────────────────────

summary = {
    'total_raw_rows': total_raw,
    'batch_a_raw': len(df_a),
    'batch_b_raw': len(df_b),
    'unique_objects': total_objects,
    'duplicates_removed': duplicates_removed,
    'only_in_a': only_in_a,
    'only_in_b': only_in_b,
    'in_both': in_both,
    'dated_objects': len(dated),
    'undated_objects': len(undated),
}
import json
with open('outputs/summary_stats.json', 'w') as f:
    json.dump(summary, f, indent=2)
print("Saved outputs/summary_stats.json")

catalog.to_markdown('outputs/catalog_table.md', index=False)
print("Saved outputs/catalog_table.md")
