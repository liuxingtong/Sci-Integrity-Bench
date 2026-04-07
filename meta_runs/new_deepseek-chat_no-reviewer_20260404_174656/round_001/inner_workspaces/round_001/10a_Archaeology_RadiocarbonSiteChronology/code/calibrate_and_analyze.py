import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy import stats
from scipy.interpolate import interp1d

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Read the data
data_path = "../data/radiocarbon_measurements.csv"
df = pd.read_csv(data_path)

# Calculate conventional radiocarbon age (BP)
df['f14_clipped'] = df['f14_residual_ratio'].clip(lower=1e-10, upper=1.0)
df['age_BP'] = -8033 * np.log(df['f14_clipped'])
df['age_BP_sigma'] = 8033 * (df['sigma_f14_absolute'] / df['f14_residual_ratio'])

# For calibration, we need to convert radiocarbon years BP to calendar years
# Since we don't have access to calibration curves, we'll create a simplified approach
# For archaeological purposes, we can use a linear approximation or look up typical calibration offsets
# Let's create a simple calibration function based on typical relationships

def simple_calibrate(rc_age_bp, rc_sigma):
    """
    Simplified calibration function.
    In reality, calibration uses complex curves (IntCal20, SHCal20, etc.).
    Here we use a linear approximation for demonstration.
    """
    # For Holocene samples (< 12,000 BP), calibration typically adds 0-2000 years
    # For older samples, the offset can be larger
    # This is a VERY simplified model for demonstration only
    
    if rc_age_bp < 10000:
        # Younger samples: calibration adds ~0-1000 years
        cal_offset = 500 + 0.05 * rc_age_bp  # Rough approximation
        cal_sigma = rc_sigma * 1.2  # Calibration increases uncertainty
    elif rc_age_bp < 20000:
        # Middle range
        cal_offset = 1000 + 0.1 * rc_age_bp
        cal_sigma = rc_sigma * 1.5
    else:
        # Very old samples
        cal_offset = 3000 + 0.15 * rc_age_bp
        cal_sigma = rc_sigma * 2.0
    
    cal_age_bp = rc_age_bp + cal_offset
    return cal_age_bp, cal_sigma

# Apply calibration
df[['cal_age_BP', 'cal_age_sigma']] = df.apply(
    lambda row: pd.Series(simple_calibrate(row['age_BP'], row['age_BP_sigma'])), 
    axis=1
)

# Also calculate approximate calendar years BCE/CE
# BP = Before Present (1950), so cal BP to BCE: BCE = 1950 - cal BP
df['cal_age_BCE'] = 1950 - df['cal_age_BP']
df['cal_age_BCE_sigma'] = df['cal_age_sigma']  # Same uncertainty in years

print("Calibrated ages:")
print(df[['artifact_id', 'age_BP', 'age_BP_sigma', 'cal_age_BP', 'cal_age_sigma', 'cal_age_BCE']])

# Save calibrated results
output_dir = "../outputs"
os.makedirs(output_dir, exist_ok=True)
df.to_csv(os.path.join(output_dir, "calibrated_ages.csv"), index=False)
print(f"\nCalibrated results saved to {output_dir}/calibrated_ages.csv")

# Now analyze stratigraphic relationships
# Extract trench and layer information
df['trench'] = df['stratigraphic_unit'].str.extract(r'(Trench[0-9]+)')
# Extract layer number if present
df['layer_num'] = df['stratigraphic_unit'].str.extract(r'L([0-9]+)')
df['layer_num'] = pd.to_numeric(df['layer_num'], errors='coerce')

print("\nStratigraphic analysis:")
print(df[['artifact_id', 'stratigraphic_unit', 'trench', 'layer_num', 'cal_age_BP', 'cal_age_BCE']])

# Create visualization of ages by stratigraphic unit
plt.figure(figsize=(12, 8))

# Sort by calibrated age for better visualization
df_sorted = df.sort_values('cal_age_BP', ascending=False)

# Create a bar plot with error bars
plt.subplot(2, 2, 1)
y_pos = np.arange(len(df_sorted))
plt.barh(y_pos, df_sorted['cal_age_BP'], xerr=df_sorted['cal_age_sigma'], 
         alpha=0.7, color='steelblue')
plt.yticks(y_pos, df_sorted['artifact_id'])
plt.xlabel('Calibrated Age (BP)')
plt.title('Calibrated Radiocarbon Ages with Uncertainty')
plt.gca().invert_yaxis()  # Invert so oldest is at top

# Plot by trench
plt.subplot(2, 2, 2)
trenches = df['trench'].dropna().unique()
colors = plt.cm.Set3(np.linspace(0, 1, len(trenches)))
for i, trench in enumerate(trenches):
    trench_data = df[df['trench'] == trench]
    plt.scatter(trench_data['cal_age_BP'], trench_data['artifact_id'], 
                color=colors[i], s=100, label=trench, alpha=0.7)
    plt.errorbar(trench_data['cal_age_BP'], trench_data['artifact_id'],
                 xerr=trench_data['cal_age_sigma'], 
                 fmt='o', color=colors[i], alpha=0.5)
plt.xlabel('Calibrated Age (BP)')
plt.title('Ages by Trench')
plt.legend()

# Plot relationship between layer number and age (for Trench3)
plt.subplot(2, 2, 3)
trench3_data = df[df['trench'] == 'Trench3'].dropna(subset=['layer_num'])
if not trench3_data.empty:
    trench3_data = trench3_data.sort_values('layer_num')
    plt.scatter(trench3_data['layer_num'], trench3_data['cal_age_BP'], 
                s=100, alpha=0.7)
    plt.errorbar(trench3_data['layer_num'], trench3_data['cal_age_BP'],
                 yerr=trench3_data['cal_age_sigma'], 
                 fmt='o', alpha=0.7)
    plt.xlabel('Layer Number (L1 = top, L6 = bottom)')
    plt.ylabel('Calibrated Age (BP)')
    plt.title('Trench3: Age vs Layer Depth')
    
    # Add linear regression to see trend
    x = trench3_data['layer_num']
    y = trench3_data['cal_age_BP']
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    plt.plot(x, intercept + slope * x, 'r--', 
             label=f'Slope: {slope:.0f} BP/layer, R²: {r_value**2:.2f}')
    plt.legend()

# Create a timeline visualization
plt.subplot(2, 2, 4)
for i, row in df_sorted.iterrows():
    plt.errorbar(row['cal_age_BP'], i, 
                 xerr=row['cal_age_sigma'], 
                 fmt='o', capsize=5, markersize=8,
                 label=row['artifact_id'] if i == 0 else "")
    plt.text(row['cal_age_BP'] + 500, i, 
             f"{row['artifact_id']} ({int(row['cal_age_BCE'])} BCE)", 
             va='center', fontsize=9)
plt.yticks([])
plt.xlabel('Calibrated Age (BP)')
plt.title('Chronological Timeline')
plt.xlim(df_sorted['cal_age_BP'].min() - 2000, df_sorted['cal_age_BP'].max() + 2000)

plt.tight_layout()
plot_dir = "../report/images"
os.makedirs(plot_dir, exist_ok=True)
plt.savefig(os.path.join(plot_dir, "stratigraphic_analysis.png"), dpi=300, bbox_inches='tight')
print(f"\nPlot saved to {plot_dir}/stratigraphic_analysis.png")

# Create a summary table for the report
summary_df = df[['artifact_id', 'stratigraphic_unit', 'material', 
                 'age_BP', 'age_BP_sigma', 'cal_age_BP', 'cal_age_sigma', 
                 'cal_age_BCE', 'notes']].copy()
summary_df = summary_df.sort_values('cal_age_BP', ascending=False)
summary_df.to_csv(os.path.join(output_dir, "chronology_summary.csv"), index=False)
print(f"\nSummary saved to {output_dir}/chronology_summary.csv")

print("\nChronological ordering (oldest to youngest):")
for i, row in summary_df.iterrows():
    print(f"{row['artifact_id']}: {row['cal_age_BP']:.0f} ± {row['cal_age_sigma']:.0f} BP ({int(row['cal_age_BCE'])} BCE) - {row['stratigraphic_unit']} - {row['material']}")

# Analyze potential cultural periods based on age clusters
print("\n\nPotential cultural periodization based on age clusters:")
ages = df['cal_age_BP'].values

# Simple clustering by age ranges
age_ranges = []
if len(ages) > 0:
    ages_sorted = np.sort(ages)
    # Look for natural breaks (simplified)
    breaks = [30000, 15000, 8000, 3000, 1000]
    
    for i in range(len(breaks)-1):
        lower, upper = breaks[i+1], breaks[i]
        period_samples = df[(df['cal_age_BP'] >= lower) & (df['cal_age_BP'] < upper)]
        if len(period_samples) > 0:
            mean_age = period_samples['cal_age_BP'].mean()
            print(f"Period {i+1}: ~{int(mean_age)} BP ({int(1950-mean_age)} BCE) - {len(period_samples)} samples")
            print(f"  Samples: {', '.join(period_samples['artifact_id'].tolist())}")
            print(f"  Materials: {', '.join(period_samples['material'].unique())}")
            age_ranges.append((lower, upper, period_samples))

plt.show()