import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.ticker import MaxNLocator

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load deduplicated data
df_dedup = pd.read_csv('../outputs/deduplicated_catalog.csv')

# Create figure directory
os.makedirs('../report/images', exist_ok=True)

print("Creating visualizations...")

# 1. Temporal distribution histogram
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Museum Collection Temporal Distribution Analysis', fontsize=16, fontweight='bold')

# Filter records with year values
year_df = df_dedup[df_dedup['year_value'].notna()].copy()

# Convert year_value to numeric (it might be read as string)
year_df['year_value'] = pd.to_numeric(year_df['year_value'], errors='coerce')
year_df = year_df[year_df['year_value'].notna()]

if len(year_df) > 0:
    # 1A. Histogram of all years
    ax = axes[0, 0]
    ax.hist(year_df['year_value'], bins=20, edgecolor='black', alpha=0.7)
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Objects')
    ax.set_title('Distribution of Objects by Year')
    ax.grid(True, alpha=0.3)
    
    # Add vertical line for mean
    mean_year = year_df['year_value'].mean()
    ax.axvline(mean_year, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_year:.0f}')
    ax.legend()
    
    # 1B. By century (grouped)
    ax = axes[0, 1]
    
    # Create century bins
    year_df['century'] = (year_df['year_value'] // 100) * 100
    
    # Separate BCE and CE for better visualization
    bce_df = year_df[year_df['century'] < 0].copy()
    ce_df = year_df[year_df['century'] >= 0].copy()
    
    if len(bce_df) > 0:
        bce_counts = bce_df['century'].value_counts().sort_index()
        bce_labels = [f'{abs(int(c))} BCE' for c in bce_counts.index]
        ax.bar(bce_labels, bce_counts.values, alpha=0.7, label='BCE', color='skyblue')
    
    if len(ce_df) > 0:
        ce_counts = ce_df['century'].value_counts().sort_index()
        ce_labels = [f'{int(c)}s' for c in ce_counts.index]
        x_pos = range(len(bce_labels) if len(bce_df) > 0 else 0, 
                     len(bce_labels) + len(ce_labels) if len(bce_df) > 0 else len(ce_labels))
        ax.bar(x_pos, ce_counts.values, alpha=0.7, label='CE', color='lightcoral')
    
    ax.set_xlabel('Century')
    ax.set_ylabel('Number of Objects')
    ax.set_title('Objects by Century')
    ax.legend()
    plt.sca(ax)
    plt.xticks(rotation=45, ha='right')
    
    # 1C. Timeline visualization
    ax = axes[1, 0]
    
    # Sort by year
    timeline_df = year_df.sort_values('year_value')
    
    # Create timeline
    y_pos = range(len(timeline_df))
    colors = ['green' if y >= 0 else 'blue' for y in timeline_df['year_value']]
    
    ax.scatter(timeline_df['year_value'], y_pos, c=colors, alpha=0.6, s=100)
    ax.set_xlabel('Year')
    ax.set_ylabel('Object Index (sorted)')
    ax.set_title('Timeline of Objects')
    ax.grid(True, alpha=0.3)
    
    # Add reference lines for common eras
    eras = [
        (-475, -221, 'Warring States', 'orange'),
        (-206, 220, 'Han Dynasty', 'red'),
        (618, 907, 'Tang Dynasty', 'purple'),
        (960, 1279, 'Song Dynasty', 'brown'),
        (1368, 1644, 'Ming Dynasty', 'green'),
        (1644, 1912, 'Qing Dynasty', 'blue'),
    ]
    
    for start, end, label, color in eras:
        ax.axvspan(start, end, alpha=0.1, color=color, label=label)
    
    # Add legend for eras (outside plot)
    ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1), borderaxespad=0.)
    
    # 1D. Year type breakdown
    ax = axes[1, 1]
    
    # Count year types
    if 'year_type' in year_df.columns:
        type_counts = year_df['year_type'].value_counts()
        
        # Group small categories
        threshold = 2
        main_types = type_counts[type_counts >= threshold]
        other_count = type_counts[type_counts < threshold].sum()
        
        if other_count > 0:
            main_types['Other'] = other_count
        
        if len(main_types) > 0:
            wedges, texts, autotexts = ax.pie(main_types.values, labels=main_types.index, 
                                             autopct='%1.1f%%', startangle=90)
            ax.set_title('Types of Year Information')
            
            # Improve readability
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
    else:
        ax.text(0.5, 0.5, 'Year type data not available', 
               ha='center', va='center', transform=ax.transAxes)
        ax.set_title('Types of Year Information')

plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust for suptitle
plt.savefig('../report/images/temporal_distribution.png', dpi=300, bbox_inches='tight')
print("Saved: ../report/images/temporal_distribution.png")

# 2. Deduplication summary
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 2A. Source comparison
ax = axes[0]
source_counts = df_dedup['source'].value_counts()
ax.bar(source_counts.index, source_counts.values, color=['skyblue', 'lightcoral'], alpha=0.7)
ax.set_xlabel('Data Source')
ax.set_ylabel('Number of Objects (Deduplicated)')
ax.set_title('Objects by Source After Deduplication')
ax.yaxis.set_major_locator(MaxNLocator(integer=True))

# Add value labels on bars
for i, v in enumerate(source_counts.values):
    ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')

# 2B. Year coverage
ax = axes[1]
has_year = df_dedup['year_value'].notna().sum()
no_year = len(df_dedup) - has_year

labels = ['With Year Info', 'Without Year Info']
values = [has_year, no_year]
colors = ['lightgreen', 'lightcoral']

wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
ax.set_title('Year Information Coverage')

# Improve readability
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')

plt.tight_layout()
plt.savefig('../report/images/deduplication_summary.png', dpi=300, bbox_inches='tight')
print("Saved: ../report/images/deduplication_summary.png")

# 3. Detailed century breakdown
fig, ax = plt.subplots(figsize=(10, 6))

if len(year_df) > 0:
    # Group by century with proper labels
    century_counts = year_df['century'].value_counts().sort_index()
    
    # Create labels
    labels = []
    for century in century_counts.index:
        if century < 0:
            labels.append(f'{abs(int(century))} BCE')
        else:
            labels.append(f'{int(century)}s CE')
    
    # Create bar chart
    bars = ax.bar(range(len(century_counts)), century_counts.values, 
                 color=plt.cm.viridis(np.linspace(0, 1, len(century_counts))))
    
    ax.set_xlabel('Century')
    ax.set_ylabel('Number of Objects')
    ax.set_title('Detailed Century Distribution')
    ax.set_xticks(range(len(century_counts)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
               f'{int(height)}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('../report/images/century_breakdown.png', dpi=300, bbox_inches='tight')
    print("Saved: ../report/images/century_breakdown.png")

print("\nVisualization complete!")