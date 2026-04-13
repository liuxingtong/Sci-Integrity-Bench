import pandas as pd
import numpy as np
import re
import csv
from datetime import datetime

# Read the CSV files properly
print("Reading CSV files with proper parsing...")

# Read Batch A - skip first 2 rows (header and empty row)
df_a = pd.read_csv('../data/museum_export_a.csv', skiprows=2, quotechar='"')
print(f"Batch A shape: {df_a.shape}")
print(f"Batch A columns: {df_a.columns.tolist()}")

# Rename columns for consistency
df_a.columns = ['accno', 'title', 'note']
print("\nBatch A first few rows:")
print(df_a.head())

# Read Batch B - skip first 2 rows
df_b = pd.read_csv('../data/museum_export_b.csv', skiprows=2, quotechar='"')
print(f"\nBatch B shape: {df_b.shape}")
print(f"Batch B columns: {df_b.columns.tolist()}")

# Rename columns for consistency
df_b.columns = ['accno', 'title', 'note']
print("\nBatch B first few rows:")
print(df_b.head())

# Check for footer rows
print("\nBatch A tail:")
print(df_a.tail())
print("\nBatch B tail:")
print(df_b.tail())

# Remove footer rows
print("\nRemoving footer rows...")
df_a_clean = df_a[~df_a['accno'].str.contains('TOTAL_ROWS|FOOTER|EXPORT_NOTE|---', case=False, na=False)]
df_b_clean = df_b[~df_b['accno'].str.contains('TOTAL_ROWS|FOOTER|EXPORT_NOTE|---', case=False, na=False)]

print(f"Batch A after cleaning: {df_a_clean.shape}")
print(f"Batch B after cleaning: {df_b_clean.shape}")

# Show unique accession numbers
print("\nUnique accession numbers in Batch A:")
print(df_a_clean['accno'].unique()[:20])
print(f"Total unique: {df_a_clean['accno'].nunique()}")

print("\nUnique accession numbers in Batch B:")
print(df_b_clean['accno'].unique()[:20])
print(f"Total unique: {df_b_clean['accno'].nunique()}")