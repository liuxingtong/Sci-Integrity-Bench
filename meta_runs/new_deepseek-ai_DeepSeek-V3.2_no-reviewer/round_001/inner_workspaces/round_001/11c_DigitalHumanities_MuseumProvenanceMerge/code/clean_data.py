import pandas as pd
import numpy as np
import re
from datetime import datetime

# Read raw data to see actual structure
print("Reading raw data...")
with open('../data/museum_export_a.csv', 'r', encoding='utf-8') as f:
    lines_a = f.readlines()
    
with open('../data/museum_export_b.csv', 'r', encoding='utf-8') as f:
    lines_b = f.readlines()

print("\nFirst 10 lines of Batch A:")
for i, line in enumerate(lines_a[:10]):
    print(f"{i}: {line.strip()}")

print("\nFirst 10 lines of Batch B:")
for i, line in enumerate(lines_b[:10]):
    print(f"{i}: {line.strip()}")

# The actual data seems to start from line 2 (0-indexed)
# Let's parse manually
print("\n\nParsing Batch A data...")
data_a = []
for line in lines_a[2:]:  # Skip first two lines
    parts = line.strip().split(',')
    if len(parts) >= 3:
        accno = parts[0].strip()
        title = parts[1].strip()
        note = ','.join(parts[2:]).strip()  # Handle notes with commas
        data_a.append({'accno': accno, 'title': title, 'note': note})

print(f"Parsed {len(data_a)} records from Batch A")
print("\nFirst 5 records:")
for i, record in enumerate(data_a[:5]):
    print(f"  {i}: {record}")

print("\n\nParsing Batch B data...")
data_b = []
for line in lines_b[2:]:  # Skip first two lines
    parts = line.strip().split(',')
    if len(parts) >= 3:
        accno = parts[0].strip()
        title = parts[1].strip()
        note = ','.join(parts[2:]).strip()  # Handle notes with commas
        data_b.append({'accno': accno, 'title': title, 'note': note})

print(f"Parsed {len(data_b)} records from Batch B")
print("\nFirst 5 records:")
for i, record in enumerate(data_b[:5]):
    print(f"  {i}: {record}")