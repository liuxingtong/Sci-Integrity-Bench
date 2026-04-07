import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats

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

# Calculate conventional radiocarbon age (BP)
# Using formula: age_BP = -8033 * ln(f14_residual_ratio)
# First, ensure f14_residual_ratio is in (0, 1) to avoid numerical issues
df['f14_clipped'] = df['f14_residual_ratio'].clip(lower=1e-10, upper=1.0)
df['age_BP'] = -8033 * np.log(df['f14_clipped'])

# Calculate uncertainty using error propagation
# For age_BP = -8033 * ln(f), uncertainty = 8033 * (sigma_f / f)
df['age_BP_sigma'] = 8033 * (df['sigma_f14_absolute'] / df['f14_residual_ratio'])

print("\nCalculated radiocarbon ages:")
print(df[['artifact_id', 'f14_residual_ratio', 'age_BP', 'age_BP_sigma']])

# Save results to outputs
output_dir = "../outputs"
os.makedirs(output_dir, exist_ok=True)
df.to_csv(os.path.join(output_dir, "radiocarbon_ages.csv"), index=False)
print(f"\nResults saved to {output_dir}/radiocarbon_ages.csv")

# Create a basic plot of ages
plt.figure(figsize=(10, 6))
plt.errorbar(df['age_BP'], range(len(df)), 
             xerr=df['age_BP_sigma'], 
             fmt='o', capsize=5, markersize=8)
plt.yticks(range(len(df)), df['artifact_id'])
plt.xlabel('Radiocarbon Age (BP)')
plt.ylabel('Artifact ID')
plt.title('Radiocarbon Ages with 1σ Uncertainty')
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Save plot
plot_dir = "../report/images"
os.makedirs(plot_dir, exist_ok=True)
plt.savefig(os.path.join(plot_dir, "radiocarbon_ages_basic.png"), dpi=300, bbox_inches='tight')
print(f"Plot saved to {plot_dir}/radiocarbon_ages_basic.png")

# Create another plot showing f14_residual_ratio vs age_BP
plt.figure(figsize=(10, 6))
plt.scatter(df['f14_residual_ratio'], df['age_BP'], s=100, alpha=0.7)
plt.errorbar(df['f14_residual_ratio'], df['age_BP'], 
             yerr=df['age_BP_sigma'], 
             fmt='o', capsize=5, alpha=0.7)
plt.xlabel('Fraction of Modern ¹⁴C (f14_residual_ratio)')
plt.ylabel('Radiocarbon Age (BP)')
plt.title('Relationship between f14 Residual Ratio and Radiocarbon Age')
plt.grid(True, alpha=0.3)

# Add artifact labels
for i, row in df.iterrows():
    plt.annotate(row['artifact_id'], 
                 (row['f14_residual_ratio'], row['age_BP']),
                 xytext=(5, 5), textcoords='offset points',
                 fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(plot_dir, "f14_vs_age.png"), dpi=300, bbox_inches='tight')
print(f"Plot saved to {plot_dir}/f14_vs_age.png")

# Group by stratigraphic unit for analysis
print("\nStratigraphic units:")
print(df['stratigraphic_unit'].unique())

# Extract trench and layer information
df['trench'] = df['stratigraphic_unit'].str.extract(r'(Trench[0-9]+)')
df['layer'] = df['stratigraphic_unit'].str.extract(r'(L[0-9]+)')

print("\nData with extracted trench and layer info:")
print(df[['artifact_id', 'stratigraphic_unit', 'trench', 'layer', 'age_BP', 'age_BP_sigma']])

plt.show()