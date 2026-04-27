import pandas as pd
import re

df_a = pd.read_csv('data/museum_export_a.csv')
df_b = pd.read_csv('data/museum_export_b.csv')

# Rename columns to match
df_a = df_a.rename(columns={'accno': 'accession', 'title': 'title', 'year_note': 'note'})
df_b = df_b.rename(columns={'accession': 'accession', 'object_name': 'title', 'remarks': 'note'})

# Combine
df = pd.concat([df_a, df_b], ignore_index=True)

# Drop NaNs in accession
df = df.dropna(subset=['accession'])

# Filter out header/footer rows
ignore_accs = ['---', 'EXPORT_NOTE', 'FOOTER', 'TOTAL_ROWS']
df = df[~df['accession'].isin(ignore_accs)]

# Normalize accession
def normalize_acc(acc):
    acc = str(acc).upper()
    # Remove non-alphanumeric
    acc = re.sub(r'[^A-Z0-9]', '', acc)
    # Remove trailing 'X' if it's a typo like T88X
    if acc.endswith('X') and len(acc) > 1 and acc[-2].isdigit():
        acc = acc[:-1]
    # Remove leading zeros in the numeric part
    match = re.match(r'([A-Z]+)0*(\d+)', acc)
    if match:
        acc = match.group(1) + match.group(2)
    return acc

df['norm_acc'] = df['accession'].apply(normalize_acc)

print(f"Total rows: {len(df)}")
print(f"Unique accessions: {df['norm_acc'].nunique()}")

# Group by normalized accession and aggregate
def agg_strings(series):
    return ' | '.join(series.dropna().unique())

df_grouped = df.groupby('norm_acc').agg({
    'accession': agg_strings,
    'title': agg_strings,
    'note': agg_strings
}).reset_index()

print(df_grouped.head(10))
print(f"Total unique objects: {len(df_grouped)}")

df_grouped.to_csv('outputs/merged_catalog.csv', index=False)
