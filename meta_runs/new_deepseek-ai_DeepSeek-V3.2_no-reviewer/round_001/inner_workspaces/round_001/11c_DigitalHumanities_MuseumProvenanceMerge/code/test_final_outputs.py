import pandas as pd
import os

print("Testing final outputs...")
print("="*50)

# Check that all required files exist
required_files = [
    'outputs/deduplicated_catalog.csv',
    'outputs/catalog_with_years.csv', 
    'outputs/century_distribution.csv',
    'report/images/temporal_distribution.png',
    'report/images/timeline.png',
    'report/images/century_distribution.png',
    'report/report.md'
]

for file in required_files:
    if os.path.exists(file):
        print(f"✓ {file} exists")
    else:
        print(f"✗ {file} MISSING!")

print("\n" + "="*50)
print("Checking deduplicated catalog content...")
dedup = pd.read_csv('outputs/deduplicated_catalog.csv')
print(f"Shape: {dedup.shape}")
print(f"Columns: {dedup.columns.tolist()}")
print("\nContent:")
print(dedup)

print("\n" + "="*50)
print("Checking catalog with years...")
catalog_years = pd.read_csv('outputs/catalog_with_years.csv')
print(f"Shape: {catalog_years.shape}")
print(f"Columns: {catalog_years.columns.tolist()}")
print("\nContent:")
print(catalog_years)

print("\n" + "="*50)
print("Checking century distribution...")
century_dist = pd.read_csv('outputs/century_distribution.csv')
print(f"Shape: {century_dist.shape}")
print("\nContent:")
print(century_dist)

print("\n" + "="*50)
print("Checking report file size...")
report_size = os.path.getsize('report/report.md')
print(f"Report size: {report_size} bytes")
if report_size > 1000:
    print("✓ Report is sufficiently detailed")
else:
    print("✗ Report may be too brief")

print("\n" + "="*50)
print("All tests completed!")