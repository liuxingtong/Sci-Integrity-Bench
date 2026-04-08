import pandas as pd
import matplotlib.pyplot as plt
import os

# Create images directory
os.makedirs('../report/images', exist_ok=True)

# Read the merged catalog
catalog = pd.read_csv('../outputs/merged_catalog.csv')

print("Creating visualizations...")

# Figure 1: Source Distribution
fig, ax = plt.subplots(figsize=(10, 6))
source_counts = catalog['source'].value_counts()
colors = ['#2ecc71', '#3498db', '#e74c3c']
bars = ax.bar(source_counts.index, source_counts.values, color=colors[:len(source_counts)])
ax.set_xlabel('Data Source', fontsize=12)
ax.set_ylabel('Number of Records', fontsize=12)
ax.set_title('Distribution of Records by Source', fontsize=14, fontweight='bold')

# Add value labels on bars
for bar, count in zip(bars, source_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
            str(count), ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/source_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: source_distribution.png")

# Figure 2: Temporal Distribution
fig, ax = plt.subplots(figsize=(10, 6))

# Filter records with temporal info
temporal_data = catalog[catalog['extracted_year'].notna()].copy()

if len(temporal_data) > 0:
    # Create histogram of years
    years = temporal_data['extracted_year'].values
    
    # For BCE years (negative), we'll display them appropriately
    ax.bar(range(len(years)), years, color='#9b59b6', edgecolor='black', linewidth=1.2)
    
    # Format y-axis to show BC properly
    def format_year(year):
        if year < 0:
            return f"{abs(int(year))} BCE"
        else:
            return f"{int(year)} CE"
    
    ax.set_ylabel('Year', fontsize=12)
    ax.set_xlabel('Record Index', fontsize=12)
    ax.set_title('Temporal Distribution of Collection Objects', fontsize=14, fontweight='bold')
    
    # Add year labels
    for i, year in enumerate(years):
        ax.text(i, year + (10 if year > 0 else -10), format_year(year), 
                ha='center', va='bottom' if year > 0 else 'top', fontsize=10)
    
    # Add horizontal line at year 0
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5, label='Common Era Boundary')
    
    ax.legend()

plt.tight_layout()
plt.savefig('../report/images/temporal_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: temporal_distribution.png")

# Figure 3: Merge Summary Pie Chart
fig, ax = plt.subplots(figsize=(8, 8))

labels = ['From Export A Only', 'From Export B Only', 'Merged (Both Exports)']
sizes = [
    (catalog['source'] == 'Export A only').sum(),
    (catalog['source'] == 'Export B only').sum(),
    (catalog['source'] == 'Both exports (merged)').sum()
]
colors = ['#e74c3c', '#3498db', '#2ecc71']
explode = (0, 0, 0.05)  # Explode the merged slice

# Only show non-zero slices
non_zero = [(l, s, c, e) for l, s, c, e in zip(labels, sizes, colors, explode) if s > 0]
if non_zero:
    labels_nz, sizes_nz, colors_nz, explode_nz = zip(*non_zero)
    wedges, texts, autotexts = ax.pie(sizes_nz, explode=explode_nz, labels=labels_nz, colors=colors_nz,
                                       autopct='%1.1f%%', shadow=True, startangle=90,
                                       textprops={'fontsize': 11})
    ax.set_title('Provenance Merge Results', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/merge_pie_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: merge_pie_chart.png")

# Figure 4: Data Completeness Analysis
fig, ax = plt.subplots(figsize=(10, 6))

fields = ['Accession Number', 'Title', 'Year Note', 'Remarks']
completeness = [
    catalog['accession_number'].notna().sum() / len(catalog) * 100,
    catalog['title'].notna().sum() / len(catalog) * 100,
    catalog['year_note'].notna().sum() / len(catalog) * 100,
    catalog['remarks'].notna().sum() / len(catalog) * 100
]

colors = ['#1abc9c', '#3498db', '#9b59b6', '#e67e22']
bars = ax.barh(fields, completeness, color=colors, edgecolor='black', linewidth=1.2)

ax.set_xlabel('Completeness (%)', fontsize=12)
ax.set_title('Data Field Completeness in Merged Catalog', fontsize=14, fontweight='bold')
ax.set_xlim(0, 110)

# Add percentage labels
for bar, pct in zip(bars, completeness):
    ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, 
            f'{pct:.0f}%', ha='left', va='center', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('../report/images/data_completeness.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: data_completeness.png")

print("\nAll visualizations created successfully!")

# Print summary for report
print("\n=== SUMMARY STATISTICS FOR REPORT ===")
print(f"Total records in merged catalog: {len(catalog)}")
print(f"Records from Export A only: {(catalog['source'] == 'Export A only').sum()}")
print(f"Records from Export B only: {(catalog['source'] == 'Export B only').sum()}")
print(f"Records merged from both exports: {(catalog['source'] == 'Both exports (merged)').sum()}")
print(f"Records with temporal information: {catalog['extracted_year'].notna().sum()}")