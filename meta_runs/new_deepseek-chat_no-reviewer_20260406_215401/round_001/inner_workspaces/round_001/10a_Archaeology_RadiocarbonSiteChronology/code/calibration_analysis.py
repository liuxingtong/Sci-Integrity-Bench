#!/usr/bin/env python3
"""
Radiocarbon calibration for Huangtupo archaeological site.
Implements simplified calibration using IntCal20 approximation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the calculated ages
df = pd.read_csv("../outputs/radiocarbon_results.csv")
print("Loaded radiocarbon results:")
print(df[['artifact_id', 'age_BP', 'sigma_age_BP']])

# For calibration, we need a calibration curve
# Since we don't have the actual IntCal20 curve, we'll create a simplified calibration
# using a polynomial approximation based on typical calibration curve behavior
# This is for demonstration purposes - in real research, actual calibration curve data should be used

# Simplified calibration function (approximation for IntCal20 in the 0-50k BP range)
def simple_calibrate(age_bp, sigma_bp):
    """
    Simplified calibration approximation.
    For ages < 10000 BP: cal_age ≈ age_bp * 1.03 (rough approximation)
    For ages 10000-25000 BP: cal_age ≈ age_bp * 1.1
    For ages > 25000 BP: calibration becomes more complex
    
    Returns calibrated age range (2σ)
    """
    if age_bp < 10000:
        cal_factor = 1.03
        cal_uncertainty_factor = 1.1
    elif age_bp < 25000:
        cal_factor = 1.1
        cal_uncertainty_factor = 1.2
    else:
        cal_factor = 1.15
        cal_uncertainty_factor = 1.3
    
    # Simple calibration
    cal_age = age_bp * cal_factor
    
    # Increased uncertainty for calibration
    cal_sigma = sigma_bp * cal_uncertainty_factor
    
    # Calculate 2σ range
    cal_age_min = cal_age - 2 * cal_sigma
    cal_age_max = cal_age + 2 * cal_sigma
    
    return cal_age, cal_sigma, cal_age_min, cal_age_max

# Apply calibration
df['cal_age_BCE'] = np.nan
df['cal_sigma'] = np.nan
df['cal_age_min_BCE'] = np.nan
df['cal_age_max_BCE'] = np.nan

for idx, row in df.iterrows():
    cal_age, cal_sigma, cal_min, cal_max = simple_calibrate(row['age_BP'], row['sigma_age_BP'])
    # Convert BP to BCE (BP = 1950 CE, so BCE = BP - 1950)
    df.at[idx, 'cal_age_BCE'] = cal_age - 1950
    df.at[idx, 'cal_sigma'] = cal_sigma
    df.at[idx, 'cal_age_min_BCE'] = cal_min - 1950
    df.at[idx, 'cal_age_max_BCE'] = cal_max - 1950

print("\nCalibrated ages (BCE):")
print(df[['artifact_id', 'age_BP', 'sigma_age_BP', 'cal_age_BCE', 'cal_sigma', 
          'cal_age_min_BCE', 'cal_age_max_BCE']])

# Save calibrated results
df.to_csv("../outputs/calibrated_results.csv", index=False)
print("\nCalibrated results saved to outputs/calibrated_results.csv")

# Create calibration visualization
plt.figure(figsize=(12, 8))

# Sort by calibrated age
df_cal_sorted = df.sort_values('cal_age_BCE', ascending=False)
y_positions = range(len(df_cal_sorted))

# Plot calibrated age ranges
for i, (_, row) in enumerate(df_cal_sorted.iterrows()):
    plt.hlines(i, row['cal_age_min_BCE'], row['cal_age_max_BCE'], 
               color='blue', alpha=0.7, linewidth=3)
    plt.scatter(row['cal_age_BCE'], i, s=100, color='red', 
                edgecolor='black', zorder=3, label='Calibrated age' if i == 0 else "")

plt.yticks(y_positions, df_cal_sorted['artifact_id'])
plt.xlabel('Calibrated Calendar Age (BCE)')
plt.title('Calibrated Age Ranges (2σ) for Huangtupo Artifacts')
plt.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('../report/images/calibrated_ages.png', dpi=300, bbox_inches='tight')
plt.close()

# Create comparison plot: conventional vs calibrated ages
plt.figure(figsize=(10, 8))

# Convert BP to BCE for comparison
conventional_bce = df['age_BP'] - 1950
calibrated_bce = df['cal_age_BCE']

plt.errorbar(conventional_bce, df['artifact_id'], 
             xerr=df['sigma_age_BP'], fmt='o', capsize=5,
             label='Conventional age ±1σ', alpha=0.7)
plt.scatter(calibrated_bce, df['artifact_id'], 
            color='red', s=100, marker='s', 
            edgecolor='black', label='Calibrated age', zorder=3)

plt.xlabel('Calendar Age (BCE)')
plt.title('Comparison: Conventional vs Calibrated Ages')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/conventional_vs_calibrated.png', dpi=300, bbox_inches='tight')
plt.close()

# Analyze stratigraphic consistency
# Check if ages are consistent with stratigraphic sequence
print("\nStratigraphic consistency analysis:")

# Create sequence order mapping (from previous analysis)
sequence_map = {
    'Huangtupo-Trench3-L1': 1,
    'Huangtupo-Trench3-L2': 2,
    'Huangtupo-Trench3-L3': 3,
    'Huangtupo-Trench4-pit7': 4,
    'Huangtupo-Trench3-L4': 5,
    'Huangtupo-Trench3-L5': 6,
    'Huangtupo-Trench3-L6': 7,
    'Huangtupo-Trench2-surface scatter': 8
}
df['sequence_order'] = df['stratigraphic_unit'].map(sequence_map)

# Sort by sequence order
df_seq = df.sort_values('sequence_order')

# Check for reversals (younger ages in deeper layers)
reversals = []
for i in range(1, len(df_seq)):
    if df_seq['cal_age_BCE'].iloc[i] > df_seq['cal_age_BCE'].iloc[i-1]:
        # Younger age (more recent) in deeper layer
        reversals.append((df_seq['artifact_id'].iloc[i-1], df_seq['artifact_id'].iloc[i],
                         df_seq['cal_age_BCE'].iloc[i-1], df_seq['cal_age_BCE'].iloc[i]))

if reversals:
    print(f"Found {len(reversals)} potential stratigraphic reversals:")
    for rev in reversals:
        print(f"  {rev[0]} ({rev[2]:.0f} BCE) → {rev[1]} ({rev[3]:.0f} BCE)")
else:
    print("No clear stratigraphic reversals detected.")

# Calculate correlation between sequence order and age
corr, p_value = stats.pearsonr(df_seq['sequence_order'], df_seq['cal_age_BCE'])
print(f"\nCorrelation between stratigraphic sequence and calibrated age:")
print(f"  Pearson r = {corr:.3f}, p = {p_value:.3f}")
if p_value < 0.05:
    print("  Significant correlation (p < 0.05)")
else:
    print("  Not statistically significant")

# Create stratigraphic sequence plot
plt.figure(figsize=(10, 8))

plt.errorbar(df_seq['cal_age_BCE'], df_seq['sequence_order'],
             xerr=2*df_seq['cal_sigma'], fmt='o', capsize=5,
             label='Calibrated age ±2σ')
plt.gca().invert_yaxis()  # Invert so depth increases downward
plt.xlabel('Calibrated Calendar Age (BCE)')
plt.ylabel('Stratigraphic Sequence (1=shallow/young, 8=deep/old)')
plt.title('Stratigraphic Sequence vs Calibrated Age')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/stratigraphic_sequence.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nCalibration analysis complete. Figures saved to report/images/")
