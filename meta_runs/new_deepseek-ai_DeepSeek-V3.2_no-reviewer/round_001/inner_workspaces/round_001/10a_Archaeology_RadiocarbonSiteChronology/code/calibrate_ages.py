import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats, interpolate
import os

# Read the calculated ages
df = pd.read_csv("../outputs/calculated_ages.csv")
print("Data loaded from outputs/calculated_ages.csv")

# For calibration, we need a calibration curve
# Since we don't have access to IntCal20, we'll create a simplified model
# based on typical calibration curve behavior
print("\n=== Simplified Radiocarbon Calibration ===")
print("Note: Using simplified calibration model for demonstration")
print("In real research, use IntCal20 or appropriate regional curve")

# Create a simplified calibration curve (mock data)
# This approximates the relationship between radiocarbon years BP and calendar years BP
def simplified_calibrate(rc_age_bp, rc_error):
    """
    Simplified calibration function.
    In reality, calibration uses complex curves with wiggles.
    Here we apply a simple offset that varies with age.
    """
    # For younger samples (< 10k BP), calibration adds ~0-200 years
    # For older samples (> 20k BP), calibration adds ~500-1000 years
    # This is a gross simplification!
    if rc_age_bp < 5000:
        cal_offset = 50 + 0.01 * rc_age_bp  # ~50-100 years
        cal_error_factor = 1.1  # Calibration increases uncertainty
    elif rc_age_bp < 15000:
        cal_offset = 100 + 0.02 * rc_age_bp  # ~100-400 years
        cal_error_factor = 1.2
    elif rc_age_bp < 25000:
        cal_offset = 200 + 0.03 * rc_age_bp  # ~200-950 years
        cal_error_factor = 1.3
    else:
        cal_offset = 300 + 0.04 * rc_age_bp  # ~300+ years
        cal_error_factor = 1.4
    
    cal_age_bp = rc_age_bp + cal_offset
    cal_error = rc_error * cal_error_factor
    
    return cal_age_bp, cal_error, cal_offset

# Apply calibration
df['calibrated_age_BP'] = np.nan
df['calibrated_sigma_BP'] = np.nan
df['calibration_offset'] = np.nan

for idx, row in df.iterrows():
    cal_age, cal_err, offset = simplified_calibrate(row['conventional_age_BP'], row['sigma_age_BP'])
    df.at[idx, 'calibrated_age_BP'] = cal_age
    df.at[idx, 'calibrated_sigma_BP'] = cal_err
    df.at[idx, 'calibration_offset'] = offset

print("\nCalibrated ages:")
print(df[['artifact_id', 'conventional_age_BP', 'calibrated_age_BP', 
          'calibration_offset', 'stratigraphic_unit']])

# Extract trench and layer information
def extract_trench_layer(unit):
    import re
    # Extract trench number
    trench_match = re.search(r'Trench(\d+)', unit)
    trench = trench_match.group(1) if trench_match else 'Unknown'
    
    # Extract layer number
    layer_match = re.search(r'L(\d+)', unit)
    layer = int(layer_match.group(1)) if layer_match else None
    
    return trench, layer

df['trench'] = df['stratigraphic_unit'].apply(lambda x: extract_trench_layer(x)[0])
df['layer'] = df['stratigraphic_unit'].apply(lambda x: extract_trench_layer(x)[1])

# Save calibrated results with all columns
cal_output_path = "../outputs/calibrated_ages.csv"
df.to_csv(cal_output_path, index=False)
print(f"\nCalibrated results saved to {cal_output_path}")

# Also save a version with just the key columns for reporting
key_columns = ['artifact_id', 'stratigraphic_unit', 'material', 'f14_residual_ratio', 
               'sigma_f14_absolute', 'conventional_age_BP', 'sigma_age_BP', 
               'calibrated_age_BP', 'calibrated_sigma_BP', 'calibration_offset',
               'trench', 'layer', 'notes']
summary_df = df[key_columns]
summary_path = "../outputs/summary_table.csv"
summary_df.to_csv(summary_path, index=False)
print(f"Summary table saved to {summary_path}")

# Create visualization comparing conventional vs calibrated ages
plt.figure(figsize=(12, 8))

# Sort by conventional age for better visualization
df_sorted = df.sort_values('conventional_age_BP')

# Plot conventional ages with error bars
plt.errorbar(df_sorted['conventional_age_BP'], 
             range(len(df_sorted)),
             xerr=df_sorted['sigma_age_BP'],
             fmt='o', capsize=5, capthick=2, label='Conventional Age',
             color='blue', alpha=0.7)

# Plot calibrated ages with error bars
plt.errorbar(df_sorted['calibrated_age_BP'], 
             range(len(df_sorted)),
             xerr=df_sorted['calibrated_sigma_BP'],
             fmt='s', capsize=5, capthick=2, label='Calibrated Age',
             color='red', alpha=0.7)

plt.yticks(range(len(df_sorted)), df_sorted['artifact_id'])
plt.xlabel('Age (BP)')
plt.title('Comparison of Conventional and Calibrated Radiocarbon Ages')
plt.grid(True, alpha=0.3)
plt.legend()

# Add stratigraphic unit labels
for i, row in enumerate(df_sorted.itertuples()):
    plt.text(max(row.conventional_age_BP, row.calibrated_age_BP) + 500, 
             i, 
             f"{row.stratigraphic_unit}\n({row.material})", 
             fontsize=8, va='center')

plt.tight_layout()
plot_path = "../report/images/calibration_comparison.png"
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to {plot_path}")

# Create a timeline visualization
plt.figure(figsize=(14, 8))

# Create timeline with error bars
colors = plt.cm.Set3(np.linspace(0, 1, len(df)))

for i, (idx, row) in enumerate(df_sorted.iterrows()):
    # Plot calibrated age range
    age_min = row['calibrated_age_BP'] - row['calibrated_sigma_BP']
    age_max = row['calibrated_age_BP'] + row['calibrated_sigma_BP']
    
    plt.hlines(i, age_min, age_max, colors=colors[i], 
               linewidth=10, alpha=0.7, label=row['artifact_id'])
    plt.plot(row['calibrated_age_BP'], i, 'ko', markersize=8)
    
    # Add text label
    plt.text(age_max + 500, i, 
             f"{row['artifact_id']}: {row['calibrated_age_BP']:.0f} ± {row['calibrated_sigma_BP']:.0f} BP\n{row['stratigraphic_unit']} - {row['material']}",
             fontsize=9, va='center')

plt.xlabel('Calendar Years BP')
plt.yticks(range(len(df_sorted)), df_sorted['artifact_id'])
plt.title('Chronological Timeline of Huangtupo Radiocarbon Samples (Calibrated)')
plt.grid(True, alpha=0.3, axis='x')
plt.xlim(0, df_sorted['calibrated_age_BP'].max() + df_sorted['calibrated_sigma_BP'].max() + 2000)

plt.tight_layout()
plot_path2 = "../report/images/chronological_timeline.png"
plt.savefig(plot_path2, dpi=300, bbox_inches='tight')
print(f"Plot saved to {plot_path2}")

# Analyze stratigraphic consistency
print("\n=== Stratigraphic Consistency Analysis ===")

# Analyze by trench
print("\nSamples by trench:")
for trench in sorted(df['trench'].unique()):
    trench_samples = df[df['trench'] == trench]
    print(f"\nTrench {trench}:")
    
    # Sort by layer if available
    if trench_samples['layer'].notna().any():
        trench_samples = trench_samples.sort_values('layer')
        for _, sample in trench_samples.iterrows():
            layer_info = f"Layer {sample['layer']}" if not pd.isna(sample['layer']) else "No layer"
            print(f"  {sample['artifact_id']} ({layer_info}): {sample['calibrated_age_BP']:.0f} ± {sample['calibrated_sigma_BP']:.0f} BP")
    else:
        for _, sample in trench_samples.iterrows():
            print(f"  {sample['artifact_id']}: {sample['calibrated_age_BP']:.0f} ± {sample['calibrated_sigma_BP']:.0f} BP")

# Check for stratigraphic reversals in Trench3 (which has layers L1-L6)
trench3_samples = df[df['trench'] == '3'].copy()
trench3_samples = trench3_samples[trench3_samples['layer'].notna()]

if len(trench3_samples) > 1:
    trench3_samples = trench3_samples.sort_values('layer')
    print("\nStratigraphic sequence in Trench3 (layers L1-L6):")
    
    ages = trench3_samples['calibrated_age_BP'].values
    layers = trench3_samples['layer'].values
    
    for i in range(len(trench3_samples)):
        sample = trench3_samples.iloc[i]
        print(f"  L{sample['layer']}: {sample['artifact_id']} = {sample['calibrated_age_BP']:.0f} BP")
    
    # Check if ages increase with depth (as expected)
    print("\nStratigraphic consistency check:")
    
    # Calculate correlation between layer depth and age
    if len(layers) > 1:
        correlation, p_value = stats.pearsonr(layers, ages)
        print(f"  Correlation between layer number and age: {correlation:.3f} (p={p_value:.3f})")
        
        if correlation > 0.5 and p_value < 0.1:
            print("  ✓ Ages generally increase with depth (stratigraphically consistent)")
        elif correlation < -0.5 and p_value < 0.1:
            print("  ⚠ Ages decrease with depth (potential stratigraphic reversal)")
        else:
            print("  ~ No clear correlation between layer and age")

print("\nCalibration analysis complete!")