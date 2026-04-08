"""
Huangtupo Radiocarbon Site Chronology Analysis
==============================================

This script performs:
1. Conversion of F14 residual ratios to conventional radiocarbon years BP
2. Stratigraphic analysis for relative chronology
3. Cultural periodization based on calibrated ages
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load data
df = pd.read_csv('data/radiocarbon_measurements.csv')
print("Loaded data:")
print(df)
print()

# Constants for F14 to BP conversion (Libby's mean life form)
LIBBY_MEAN_LIFE = 8033  # years

def f14_to_bp(f14, clip=True):
    """
    Convert F14 residual ratio to conventional radiocarbon years BP.
    Using Libby's mean life form: age_BP = -8033 * ln(f14_residual_ratio)
    """
    f14 = np.array(f14, dtype=float)
    if clip:
        f14_clipped = np.clip(f14, 0.001, 1.0)
        clipped_mask = (f14 != f14_clipped)
        if np.any(clipped_mask):
            print(f"  Warning: {np.sum(clipped_mask)} values were clipped for log calculation")
        f14 = f14_clipped
    
    age_bp = -LIBBY_MEAN_LIFE * np.log(f14)
    return age_bp

def f14_error_to_bp_error(f14, sigma_f14):
    """
    Propagate F14 uncertainty to BP uncertainty.
    """
    derivative = LIBBY_MEAN_LIFE / f14
    sigma_bp = derivative * sigma_f14
    return sigma_bp

# Calculate conventional ages
df['age_bp'] = f14_to_bp(df['f14_residual_ratio'])
df['sigma_bp'] = f14_error_to_bp_error(df['f14_residual_ratio'], df['sigma_f14_absolute'])

# Round for display
df['age_bp_rounded'] = df['age_bp'].round(0).astype(int)
df['sigma_bp_rounded'] = df['sigma_bp'].round(0).astype(int)

print("Calculated conventional radiocarbon ages:")
print(df[['artifact_id', 'stratigraphic_unit', 'f14_residual_ratio', 'age_bp_rounded', 'sigma_bp_rounded']])
print()

# Extract layer numbers for stratigraphic ordering
def extract_layer_info(unit):
    """Extract trench and layer information from stratigraphic unit."""
    if 'Trench3' in unit:
        if 'L' in unit:
            layer = int(unit.split('L')[1])
            return ('Trench3', layer)
        else:
            return ('Trench3', 0)
    elif 'Trench4' in unit:
        return ('Trench4', -1)
    elif 'Trench2' in unit:
        return ('Trench2', 99)
    else:
        return ('Other', 0)

df['trench'] = df['stratigraphic_unit'].apply(lambda x: extract_layer_info(x)[0])
df['layer_order'] = df['stratigraphic_unit'].apply(lambda x: extract_layer_info(x)[1])

# Sort by stratigraphic context
df_sorted = df.sort_values(['trench', 'layer_order'])

print("Stratigraphically sorted data:")
print(df_sorted[['artifact_id', 'stratigraphic_unit', 'trench', 'layer_order', 'age_bp_rounded']])
print()

# Define cultural periods
def assign_period(age_bp):
    """Assign cultural period based on conventional radiocarbon age."""
    if age_bp < 1000:
        return "Historical/Late Prehistoric"
    elif age_bp < 3000:
        return "Late Neolithic/Bronze Age"
    elif age_bp < 5000:
        return "Middle Neolithic"
    elif age_bp < 8000:
        return "Early Neolithic"
    elif age_bp < 12000:
        return "Paleolithic/Early Holocene"
    else:
        return "Upper Paleolithic"

df['period'] = df['age_bp'].apply(assign_period)

# Save processed data
df.to_csv('outputs/processed_radiocarbon_data.csv', index=False)
print("Saved processed data to outputs/processed_radiocarbon_data.csv")

# Create summary table
summary_table = df[['artifact_id', 'stratigraphic_unit', 'material', 
                     'f14_residual_ratio', 'sigma_f14_absolute',
                     'age_bp_rounded', 'sigma_bp_rounded', 'period', 'notes']].copy()
summary_table.columns = ['Artifact ID', 'Stratigraphic Unit', 'Material',
                          'F14 Ratio', 'F14 Sigma', 'Age BP', 'Sigma BP', 
                          'Period', 'Notes']
summary_table.to_csv('outputs/summary_table.csv', index=False)
print("Saved summary table to outputs/summary_table.csv")

# Create visualization 1: Age vs Stratigraphic Position
fig, ax = plt.subplots(figsize=(12, 8))

colors = {'Trench3': '#1f77b4', 'Trench4': '#ff7f0e', 'Trench2': '#2ca02c'}
markers = {'Trench3': 'o', 'Trench4': 's', 'Trench2': '^'}

for trench in df['trench'].unique():
    subset = df[df['trench'] == trench]
    ax.errorbar(subset['age_bp'], subset['layer_order'], 
                xerr=subset['sigma_bp'], fmt=markers.get(trench, 'o'),
                color=colors.get(trench, 'gray'), label=trench, 
                markersize=10, capsize=5, capthick=2, elinewidth=2)
    
    for _, row in subset.iterrows():
        ax.annotate(row['artifact_id'], 
                   (row['age_bp'], row['layer_order']),
                   textcoords="offset points", xytext=(10, 5), fontsize=9)

ax.set_xlabel('Conventional Radiocarbon Age (years BP)', fontsize=12)
ax.set_ylabel('Stratigraphic Layer (Trench 3: L1=top, L6=bottom)', fontsize=12)
ax.set_title('Huangtupo Site: Radiocarbon Ages vs Stratigraphic Position', fontsize=14, fontweight='bold')
ax.legend(title='Trench', loc='upper right')
ax.grid(True, alpha=0.3)
ax.invert_xaxis()
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('report/images/age_vs_stratigraphy.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved figure: report/images/age_vs_stratigraphy.png")

# Create visualization 2: Chronological sequence plot
fig, ax = plt.subplots(figsize=(14, 8))

df_chrono = df.sort_values('age_bp')
y_positions = np.arange(len(df_chrono))
colors_list = [colors.get(t, 'gray') for t in df_chrono['trench']]

ax.barh(y_positions, df_chrono['age_bp'], xerr=df_chrono['sigma_bp'],
        color=colors_list, alpha=0.7, capsize=5, height=0.6)

ax.set_yticks(y_positions)
ax.set_yticklabels([f"{row['artifact_id']}\n{row['stratigraphic_unit']}\n{row['material']}" 
                    for _, row in df_chrono.iterrows()], fontsize=9)
ax.set_xlabel('Conventional Radiocarbon Age (years BP)', fontsize=12)
ax.set_title('Huangtupo Site: Chronological Sequence of Radiocarbon Dates', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')
ax.invert_xaxis()

period_boundaries = [1000, 3000, 5000, 8000, 12000]
period_labels = ["Historical", "Late Neolithic/\nBronze Age", "Middle Neolithic", 
                 "Early Neolithic", "Paleolithic"]
for i, (boundary, label) in enumerate(zip(period_boundaries, period_labels)):
    ax.axvline(x=boundary, color='red', linestyle='--', alpha=0.5)
    ax.text(boundary, len(df_chrono) - 0.5, label, rotation=90, 
            verticalalignment='top', fontsize=8, color='red')

plt.tight_layout()
plt.savefig('report/images/chronological_sequence.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved figure: report/images/chronological_sequence.png")

# Create visualization 3: Stratigraphic correlation diagram
fig, ax = plt.subplots(figsize=(10, 10))

trench3_data = df[df['trench'] == 'Trench3'].sort_values('layer_order')

layer_width = 2
for _, row in trench3_data.iterrows():
    layer = row['layer_order']
    age = row['age_bp']
    sigma = row['sigma_bp']
    
    rect = plt.Rectangle((0, layer - 0.4), layer_width, 0.8, 
                         fill=True, facecolor='lightgray', edgecolor='black', linewidth=2)
    ax.add_patch(rect)
    
    ax.text(layer_width/2, layer, f"{row['artifact_id']}\n{int(age)}±{int(sigma)} BP", 
            ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax.text(layer_width + 0.2, layer, f"{row['material']}", 
            ha='left', va='center', fontsize=9, style='italic')

other_data = df[df['trench'] != 'Trench3'].sort_values('age_bp')
offset_x = 4
for i, (_, row) in enumerate(other_data.iterrows()):
    y_pos = 7 + i * 1.5
    rect = plt.Rectangle((offset_x, y_pos - 0.4), layer_width, 0.8, 
                         fill=True, facecolor='lightyellow', edgecolor='black', linewidth=2)
    ax.add_patch(rect)
    ax.text(offset_x + layer_width/2, y_pos, f"{row['artifact_id']}\n{int(row['age_bp'])}±{int(row['sigma_bp'])} BP", 
            ha='center', va='center', fontsize=9, fontweight='bold')
    ax.text(offset_x + layer_width + 0.2, y_pos, f"{row['stratigraphic_unit']}\n{row['material']}", 
            ha='left', va='center', fontsize=8, style='italic')

ax.set_xlim(-0.5, 8)
ax.set_ylim(0, 12)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('Huangtupo Site: Stratigraphic Column and Chronology', fontsize=14, fontweight='bold', pad=20)

ax.text(-0.3, 6.5, 'Trench 3\nStratigraphy', fontsize=11, fontweight='bold', ha='center')
ax.text(offset_x + layer_width/2, 11.5, 'Other Contexts', fontsize=11, fontweight='bold', ha='center')

plt.tight_layout()
plt.savefig('report/images/stratigraphic_column.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved figure: report/images/stratigraphic_column.png")

# Create visualization 4: Duplicate pair analysis
fig, ax = plt.subplots(figsize=(10, 6))

pair_data = df[df['artifact_id'].isin(['AC-111', 'AC-112'])]

x_pos = [1, 2]
ages = pair_data['age_bp'].values
sigmas = pair_data['sigma_bp'].values

ax.errorbar(x_pos, ages, yerr=sigmas, fmt='o', markersize=15, capsize=10, 
            capthick=3, elinewidth=3, color='darkblue')
ax.set_xticks(x_pos)
ax.set_xticklabels(pair_data['artifact_id'].values, fontsize=12)
ax.set_ylabel('Conventional Radiocarbon Age (years BP)', fontsize=12)
ax.set_title('Duplicate Chronology Check: AC-111 and AC-112\n(Same ridge source)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

age_diff = abs(ages[0] - ages[1])
combined_sigma = np.sqrt(sigmas[0]**2 + sigmas[1]**2)
ax.text(1.5, max(ages) + 200, f'Age difference: {age_diff:.0f} years\nCombined σ: {combined_sigma:.0f} years\nAgreement: {"Good" if age_diff < 2*combined_sigma else "Poor"}', 
        ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('report/images/duplicate_check.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved figure: report/images/duplicate_check.png")

# Statistical summary
print("\n" + "="*60)
print("STATISTICAL SUMMARY")
print("="*60)
print(f"\nTotal samples analyzed: {len(df)}")
print(f"Age range: {df['age_bp'].min():.0f} - {df['age_bp'].max():.0f} BP")
print(f"Mean age: {df['age_bp'].mean():.0f} ± {df['age_bp'].std():.0f} BP")
print(f"\nStratigraphic consistency check (Trench 3):")
trench3_ages = df[df['trench'] == 'Trench3'].sort_values('layer_order')['age_bp'].values
is_consistent = all(trench3_ages[i] <= trench3_ages[i+1] for i in range(len(trench3_ages)-1))
print(f"  Ages increase with depth: {is_consistent}")
print(f"  Layer sequence ages: {trench3_ages}")

print("\nDuplicate pair analysis (AC-111 vs AC-112):")
print(f"  AC-111: {ages[0]:.0f} ± {sigmas[0]:.0f} BP")
print(f"  AC-112: {ages[1]:.0f} ± {sigmas[1]:.0f} BP")
print(f"  Difference: {age_diff:.0f} years (within {age_diff/combined_sigma:.1f}σ)")

print("\n" + "="*60)
print("Analysis complete!")
print("="*60)
