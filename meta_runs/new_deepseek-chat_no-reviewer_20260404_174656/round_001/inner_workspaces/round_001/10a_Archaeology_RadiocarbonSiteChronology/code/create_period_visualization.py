import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the detailed chronology
df = pd.read_csv("../outputs/detailed_chronology.csv")

# Define cultural periods based on analysis
periods = [
    {
        'name': 'Upper Paleolithic',
        'age_range': (50000, 60000),
        'color': 'lightcoral',
        'samples': ['AC-109', 'AC-110']
    },
    {
        'name': 'Epipaleolithic / Early Neolithic',
        'age_range': (15000, 16000),
        'color': 'lightgreen',
        'samples': ['AC-111', 'AC-112']
    },
    {
        'name': 'Late Neolithic / Bronze Age',
        'age_range': (1000, 8000),
        'color': 'lightblue',
        'samples': ['AC-107', 'AC-108', 'AC-113', 'AC-114']
    }
]

# Create visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Plot 1: Timeline with cultural periods
for i, period in enumerate(periods):
    # Shade the period range
    ax1.axvspan(period['age_range'][0], period['age_range'][1], 
                alpha=0.3, color=period['color'], 
                label=period['name'])
    
    # Plot samples in this period
    period_samples = df[df['artifact_id'].isin(period['samples'])]
    for _, row in period_samples.iterrows():
        ax1.errorbar(row['cal_age_BP'], i, 
                     xerr=2*row['cal_sigma'],
                     fmt='o', capsize=5, markersize=8,
                     color='black', alpha=0.7)
        ax1.text(row['cal_age_BP'], i + 0.2, row['artifact_id'], 
                 ha='center', fontsize=9, fontweight='bold')

ax1.set_yticks(range(len(periods)))
ax1.set_yticklabels([p['name'] for p in periods])
ax1.set_xlabel('Calibrated Age (BP)')
ax1.set_title('Cultural Periods and Sample Distribution')
ax1.grid(True, alpha=0.3)
ax1.legend(loc='upper right')
ax1.invert_yaxis()

# Plot 2: Stratigraphic column for Trench3
trench3 = df[df['trench'] == 'Trench3'].dropna(subset=['layer_num'])
trench3 = trench3.sort_values('layer_num', ascending=False)  # L1 at top

if not trench3.empty:
    # Create stratigraphic column
    layer_height = 1.0
    for _, row in trench3.iterrows():
        y_bottom = row['layer_num'] - 0.4
        y_top = row['layer_num'] + 0.4
        
        # Determine period color
        period_color = 'gray'
        for period in periods:
            if row['artifact_id'] in period['samples']:
                period_color = period['color']
                break
        
        # Draw layer rectangle
        ax2.add_patch(plt.Rectangle((0, y_bottom), 1, 0.8, 
                                   facecolor=period_color, alpha=0.5,
                                   edgecolor='black'))
        
        # Add layer label
        ax2.text(0.5, row['layer_num'], f"L{int(row['layer_num'])}", 
                ha='center', va='center', fontweight='bold')
        
        # Add sample info
        ax2.text(1.1, row['layer_num'], 
                f"{row['artifact_id']}: {row['cal_age_BP']:.0f} BP",
                va='center', fontsize=9)
        
        # Add material info
        ax2.text(2.0, row['layer_num'], row['material'],
                va='center', fontsize=8, style='italic')
    
    ax2.set_xlim(-0.5, 3.0)
    ax2.set_ylim(trench3['layer_num'].min() - 1, trench3['layer_num'].max() + 1)
    ax2.set_xlabel('Stratigraphic Information')
    ax2.set_ylabel('Layer (L1 = top)')
    ax2.set_title('Trench3 Stratigraphic Column with Ages')
    ax2.set_aspect('auto')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Remove x-axis ticks
    ax2.set_xticks([])

plt.tight_layout()

# Save plot
plot_dir = "../report/images"
os.makedirs(plot_dir, exist_ok=True)
plt.savefig(os.path.join(plot_dir, "cultural_periods.png"), dpi=300, bbox_inches='tight')
print(f"Plot saved to {plot_dir}/cultural_periods.png")

# Create a summary table for the report
summary_table = "## Summary Table: Cultural Periods at Huangtupo\n\n"
summary_table += "| Period | Approximate Age (BP) | Calendar BCE | Samples | Key Characteristics |\n"
summary_table += "|--------|---------------------|--------------|---------|---------------------|\n"

for period in periods:
    period_samples = df[df['artifact_id'].isin(period['samples'])]
    mean_age = period_samples['cal_age_BP'].mean()
    bce_age = int(1950 - mean_age)
    samples_str = ", ".join(period['samples'])
    
    # Determine key characteristics
    materials = period_samples['material'].unique()
    contexts = period_samples['stratigraphic_unit'].unique()
    
    characteristics = []
    if 'shell organics' in materials:
        characteristics.append("shell artifacts (reservoir effect)")
    if len(period_samples) >= 2 and all('charcoal' in m for m in materials):
        characteristics.append("multiple charcoal samples")
    if 'charred bone' in materials:
        characteristics.append("bone processing evidence")
    
    if period['name'] == 'Epipaleolithic / Early Neolithic':
        characteristics.append("duplicate-validated")
    if period['name'] == 'Upper Paleolithic':
        characteristics.append("provisional dating")
    
    characteristics_str = "; ".join(characteristics)
    
    summary_table += f"| {period['name']} | {mean_age:.0f} BP | {bce_age} BCE | {samples_str} | {characteristics_str} |\n"

# Save summary table
with open(os.path.join("../outputs", "period_summary.md"), "w") as f:
    f.write(summary_table)

print("\nSummary table created in outputs/period_summary.md")
print("\n" + summary_table)

plt.show()