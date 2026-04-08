import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
data_path = "../data/radiocarbon_measurements.csv"
df = pd.read_csv(data_path)
print("Data loaded:")
print(df)
print("\nData info:")
print(df.info())
print("\nData description:")
print(df.describe())

# Convert F14 to conventional radiocarbon years BP
# Formula: age_BP = -8033 * ln(f14_residual_ratio)
# First, ensure F14 values are in (0, 1) to avoid numerical issues
print("\nChecking F14 values:")
print(f"Min F14: {df['f14_residual_ratio'].min()}")
print(f"Max F14: {df['f14_residual_ratio'].max()}")

# Calculate conventional age
# Note: We need to handle very small F14 values carefully
df['conventional_age_BP'] = -8033 * np.log(df['f14_residual_ratio'])

# Calculate uncertainty propagation
# Using error propagation: sigma_age = 8033 * (sigma_f14 / f14)
df['sigma_age_BP'] = 8033 * (df['sigma_f14_absolute'] / df['f14_residual_ratio'])

print("\nCalculated ages:")
print(df[['artifact_id', 'f14_residual_ratio', 'conventional_age_BP', 'sigma_age_BP']])

# Save results to CSV
output_path = "../outputs/calculated_ages.csv"
df.to_csv(output_path, index=False)
print(f"\nResults saved to {output_path}")

# Create a basic plot of ages by stratigraphic unit
plt.figure(figsize=(10, 6))

# Sort by stratigraphic unit for better visualization
# Extract numeric layer from stratigraphic_unit for sorting
def extract_layer(unit):
    # Try to extract layer number from unit string
    import re
    match = re.search(r'L(\d+)', unit)
    if match:
        return int(match.group(1))
    # For other units, assign high number
    return 999

df['layer_num'] = df['stratigraphic_unit'].apply(extract_layer)
df_sorted = df.sort_values('layer_num')

# Plot with error bars
plt.errorbar(df_sorted['conventional_age_BP'], 
             range(len(df_sorted)),
             xerr=df_sorted['sigma_age_BP'],
             fmt='o', capsize=5, capthick=2)
plt.yticks(range(len(df_sorted)), df_sorted['artifact_id'])
plt.xlabel('Conventional Radiocarbon Age (BP)')
plt.title('Radiocarbon Ages with 1σ Uncertainty')
plt.grid(True, alpha=0.3)

# Add stratigraphic unit labels
for i, row in enumerate(df_sorted.itertuples()):
    plt.text(row.conventional_age_BP + row.sigma_age_BP + 200, 
             i, 
             f"{row.stratigraphic_unit}\n({row.material})", 
             fontsize=8, va='center')

plt.tight_layout()
plot_path = "../report/images/radiocarbon_ages.png"
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to {plot_path}")

# Create another plot showing F14 values vs age
plt.figure(figsize=(10, 6))
plt.scatter(df['f14_residual_ratio'], df['conventional_age_BP'], 
            s=100, alpha=0.7, edgecolors='k')

# Add error bars
plt.errorbar(df['f14_residual_ratio'], df['conventional_age_BP'],
             xerr=df['sigma_f14_absolute'],
             yerr=df['sigma_age_BP'],
             fmt='none', alpha=0.5, color='gray')

plt.xlabel('F14 Residual Ratio (fraction of modern $^{14}$C)')
plt.ylabel('Conventional Age (BP)')
plt.title('Relationship between F14 Ratio and Radiocarbon Age')
plt.grid(True, alpha=0.3)

# Add labels for each point
for i, row in enumerate(df.itertuples()):
    plt.annotate(row.artifact_id, 
                 (row.f14_residual_ratio, row.conventional_age_BP),
                 xytext=(5, 5), textcoords='offset points',
                 fontsize=8)

plt.tight_layout()
plot_path2 = "../report/images/f14_vs_age.png"
plt.savefig(plot_path2, dpi=300, bbox_inches='tight')
print(f"Plot saved to {plot_path2}")

# Analyze stratigraphic relationships
print("\n=== Stratigraphic Analysis ===")
print("Stratigraphic units:")
for unit in df['stratigraphic_unit'].unique():
    unit_samples = df[df['stratigraphic_unit'] == unit]
    print(f"  {unit}: {len(unit_samples)} samples")
    for _, sample in unit_samples.iterrows():
        print(f"    - {sample['artifact_id']}: {sample['conventional_age_BP']:.0f} ± {sample['sigma_age_BP']:.0f} BP")

# Check for consistency in duplicate samples (AC-111 and AC-112)
duplicates = df[df['artifact_id'].isin(['AC-111', 'AC-112'])]
print("\nDuplicate check (AC-111 and AC-112):")
print(duplicates[['artifact_id', 'f14_residual_ratio', 'conventional_age_BP', 'sigma_age_BP']])

# Calculate difference between duplicates
diff_age = abs(duplicates.iloc[0]['conventional_age_BP'] - duplicates.iloc[1]['conventional_age_BP'])
combined_error = np.sqrt(duplicates.iloc[0]['sigma_age_BP']**2 + duplicates.iloc[1]['sigma_age_BP']**2)
print(f"Age difference: {diff_age:.0f} BP")
print(f"Combined error: {combined_error:.0f} BP")
print(f"Difference/Error ratio: {diff_age/combined_error:.2f}")

print("\nAnalysis complete!")