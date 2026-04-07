#!/usr/bin/env python3
"""
Radiocarbon analysis for Huangtupo archaeological site.
Calculates conventional ages from F14 ratios and performs basic chronology analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
data_path = "../data/radiocarbon_measurements.csv"
df = pd.read_csv(data_path)
print("Data loaded successfully:")
print(df)
print("\nData info:")
print(df.info())
print("\nSummary statistics:")
print(df.describe())

# Calculate conventional radiocarbon age BP using formula: age_BP = -8033 * ln(f14_residual_ratio)
# First, ensure F14 values are in valid range (0, 1)
# Check for any values outside this range
print("\nChecking F14 values:")
print(f"Min F14: {df['f14_residual_ratio'].min()}")
print(f"Max F14: {df['f14_residual_ratio'].max()}")

# Calculate age BP
def calculate_age_bp(f14):
    """Calculate conventional radiocarbon age BP from F14 ratio."""
    # Clip to avoid numerical issues with values <= 0
    f14_clipped = np.clip(f14, 1e-10, 1.0)
    age_bp = -8033 * np.log(f14_clipped)
    return age_bp

df['age_BP'] = calculate_age_bp(df['f14_residual_ratio'])

# Calculate uncertainty propagation for age BP
# Using error propagation: σ_age = 8033 * (σ_f14 / f14)
df['sigma_age_BP'] = 8033 * (df['sigma_f14_absolute'] / df['f14_residual_ratio'])

print("\nCalculated ages:")
print(df[['artifact_id', 'f14_residual_ratio', 'sigma_f14_absolute', 'age_BP', 'sigma_age_BP']])

# Save results to outputs
df.to_csv("../outputs/radiocarbon_results.csv", index=False)
print("\nResults saved to outputs/radiocarbon_results.csv")

# Create a summary table for the report
summary_df = df[['artifact_id', 'stratigraphic_unit', 'material', 'f14_residual_ratio', 
                 'sigma_f14_absolute', 'age_BP', 'sigma_age_BP', 'notes']].copy()
summary_df.to_csv("../outputs/summary_table.csv", index=False)

# Create visualizations
# 1. Age distribution by stratigraphic unit
plt.figure(figsize=(10, 6))
# Sort by stratigraphic unit for better visualization
unit_order = sorted(df['stratigraphic_unit'].unique())
# Create a mapping from unit to approximate depth/sequence
# Based on the naming: L1, L2, L3, L4, L5, L6, pit7, surface scatter
# We'll assign a rough sequence order
sequence_map = {
    'Huangtupo-Trench3-L1': 1,
    'Huangtupo-Trench3-L2': 2,
    'Huangtupo-Trench3-L3': 3,
    'Huangtupo-Trench4-pit7': 4,  # Assuming pit7 is deeper
    'Huangtupo-Trench3-L4': 5,
    'Huangtupo-Trench3-L5': 6,
    'Huangtupo-Trench3-L6': 7,
    'Huangtupo-Trench2-surface scatter': 8  # Surface is youngest
}
df['sequence_order'] = df['stratigraphic_unit'].map(sequence_map)
df_sorted = df.sort_values('sequence_order')

# Plot ages with error bars
plt.errorbar(df_sorted['artifact_id'], df_sorted['age_BP'], 
             yerr=df_sorted['sigma_age_BP'], fmt='o', capsize=5, 
             label='Radiocarbon age ±1σ')
plt.xticks(rotation=45)
plt.xlabel('Artifact ID')
plt.ylabel('Conventional Age (BP)')
plt.title('Radiocarbon Ages of Huangtupo Artifacts')
plt.tight_layout()
plt.savefig('../report/images/age_distribution.png', dpi=300, bbox_inches='tight')
plt.close()

# 2. F14 ratio vs stratigraphic sequence
plt.figure(figsize=(10, 6))
plt.errorbar(df_sorted['sequence_order'], df_sorted['f14_residual_ratio'], 
             yerr=df_sorted['sigma_f14_absolute'], fmt='s', capsize=5,
             label='F14 ratio ±1σ')
plt.xlabel('Stratigraphic Sequence (1=oldest, 8=youngest)')
plt.ylabel('F14 Residual Ratio')
plt.title('F14 Ratio vs Stratigraphic Sequence')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/f14_vs_sequence.png', dpi=300, bbox_inches='tight')
plt.close()

# 3. Material type analysis
plt.figure(figsize=(10, 6))
materials = df['material'].unique()
colors = plt.cm.tab10(np.linspace(0, 1, len(materials)))

for i, material in enumerate(materials):
    material_data = df[df['material'] == material]
    plt.scatter(material_data['age_BP'], material_data['artifact_id'], 
                color=colors[i], s=100, label=material, alpha=0.7)
    # Add error bars
    for _, row in material_data.iterrows():
        plt.hlines(row['artifact_id'], 
                   row['age_BP'] - row['sigma_age_BP'], 
                   row['age_BP'] + row['sigma_age_BP'], 
                   color=colors[i], alpha=0.5)

plt.xlabel('Conventional Age (BP)')
plt.ylabel('Artifact ID')
plt.title('Radiocarbon Ages by Material Type')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/age_by_material.png', dpi=300, bbox_inches='tight')
plt.close()

# 4. Check for duplicate pair AC-111 and AC-112
pair_data = df[df['artifact_id'].isin(['AC-111', 'AC-112'])]
print("\nDuplicate pair check (AC-111 and AC-112):")
print(pair_data[['artifact_id', 'f14_residual_ratio', 'sigma_f14_absolute', 'age_BP', 'sigma_age_BP']])

# Calculate difference and z-score
diff = abs(pair_data['age_BP'].iloc[0] - pair_data['age_BP'].iloc[1])
combined_error = np.sqrt(pair_data['sigma_age_BP'].iloc[0]**2 + pair_data['sigma_age_BP'].iloc[1]**2)
z_score = diff / combined_error if combined_error > 0 else 0
print(f"\nAge difference: {diff:.1f} years")
print(f"Combined error: {combined_error:.1f} years")
print(f"Z-score: {z_score:.2f}")
print(f"Consistent within 2σ? {abs(z_score) < 2}")

# 5. Create a timeline/chronology plot
plt.figure(figsize=(12, 8))
# Sort by age for timeline
df_timeline = df.sort_values('age_BP', ascending=False)

# Create horizontal bars for each artifact
y_positions = range(len(df_timeline))
plt.hlines(y_positions, 
           df_timeline['age_BP'] - df_timeline['sigma_age_BP'], 
           df_timeline['age_BP'] + df_timeline['sigma_age_BP'], 
           color='gray', alpha=0.5, linewidth=2)
plt.scatter(df_timeline['age_BP'], y_positions, s=100, 
           c=df_timeline['sequence_order'], cmap='viridis', 
           edgecolor='black', zorder=3)

plt.yticks(y_positions, df_timeline['artifact_id'])
plt.xlabel('Conventional Age (BP)')
plt.title('Huangtupo Site Chronology Timeline')
plt.colorbar(label='Stratigraphic Sequence (1=oldest, 8=youngest)')
plt.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('../report/images/chronology_timeline.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nAnalysis complete. Figures saved to report/images/")
