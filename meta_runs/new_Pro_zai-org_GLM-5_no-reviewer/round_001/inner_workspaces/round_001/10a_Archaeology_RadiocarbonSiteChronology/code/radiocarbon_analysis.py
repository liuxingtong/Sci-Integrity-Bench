"""
Radiocarbon Chronology Analysis for Huangtupo Site
====================================================
This script processes radiocarbon measurements, calculates conventional ages,
and generates calibrated age estimates with stratigraphic analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import stats

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Read the radiocarbon data
df = pd.read_csv('data/radiocarbon_measurements.csv')

print("="*60)
print("HUANGTUP SITE RADIOCARBON CHRONOLOGY ANALYSIS")
print("="*60)
print("\nRaw Data:")
print(df.to_string())

# =============================================================================
# STEP 1: Calculate Conventional Radiocarbon Age (BP)
# =============================================================================
# Formula: age_BP = -8033 * ln(F14)
# Using Libby's mean life (8033 years)

def calculate_age_bp(f14, sigma_f14):
    """
    Calculate conventional radiocarbon age BP from F14 ratio.
    
    Parameters:
    -----------
    f14 : float - Fraction of modern 14C
    sigma_f14 : float - 1σ uncertainty in F14
    
    Returns:
    --------
    age_bp : float - Conventional radiocarbon age in years BP
    sigma_age : float - 1σ uncertainty in years
    """
    # Clip F14 to valid range (0, 1]
    f14_clipped = np.clip(f14, 1e-10, 1.0)
    
    # Calculate age
    age_bp = -8033 * np.log(f14_clipped)
    
    # Propagate uncertainty using error propagation
    # d(age)/d(F14) = -8033/F14
    # sigma_age = |d(age)/d(F14)| * sigma_f14
    sigma_age = (8033 / f14_clipped) * sigma_f14
    
    return age_bp, sigma_age

# Calculate ages for all samples
ages_bp = []
sigmas_bp = []

for idx, row in df.iterrows():
    age, sigma = calculate_age_bp(row['f14_residual_ratio'], row['sigma_f14_absolute'])
    ages_bp.append(age)
    sigmas_bp.append(sigma)

df['age_BP'] = ages_bp
df['sigma_BP'] = sigmas_bp

print("\n" + "="*60)
print("CONVENTIONAL RADIOCARBON AGES (BP)")
print("="*60)
for idx, row in df.iterrows():
    print(f"{row['artifact_id']}: {row['age_BP']:.0f} ± {row['sigma_BP']:.0f} BP "
          f"(F14 = {row['f14_residual_ratio']:.4f} ± {row['sigma_f14_absolute']:.4f})")

# =============================================================================
# STEP 2: Calibrated Calendar Ages
# =============================================================================
# Simplified calibration using IntCal20 approximation
# For a proper calibration, we would use the IntCal20 curve
# Here we use a simplified approach based on known calibration relationships

def simple_calibrate(age_bp, sigma_bp):
    """
    Simplified calibration approximation.
    
    This provides approximate calibrated age ranges.
    For publication, proper calibration with OxCal or CALIB is recommended.
    
    The calibration curve has wiggles, but we can approximate:
    - For ages < 1000 BP: cal age ≈ BP age (minimal offset)
    - For ages 1000-3000 BP: cal age ≈ BP age + 0-200 years
    - For ages > 3000 BP: cal age ≈ BP age + 100-400 years
    
    We'll use a simplified polynomial approximation.
    """
    # Approximate calibration offset based on IntCal20
    # This is a rough approximation for demonstration
    if age_bp < 500:
        offset = 20
        offset_sigma = 30
    elif age_bp < 2000:
        offset = 50 + (age_bp - 500) * 0.05
        offset_sigma = 50
    elif age_bp < 5000:
        offset = 125 + (age_bp - 2000) * 0.08
        offset_sigma = 80
    elif age_bp < 10000:
        offset = 525 + (age_bp - 5000) * 0.15
        offset_sigma = 120
    else:
        offset = 1275 + (age_bp - 10000) * 0.20
        offset_sigma = 150
    
    cal_age = age_bp + offset
    cal_sigma = np.sqrt(sigma_bp**2 + offset_sigma**2)
    
    return cal_age, cal_sigma

# Calculate calibrated ages
cal_ages = []
cal_sigmas = []

for idx, row in df.iterrows():
    cal_age, cal_sigma = simple_calibrate(row['age_BP'], row['sigma_BP'])
    cal_ages.append(cal_age)
    cal_sigmas.append(cal_sigma)

df['cal_age_BP'] = cal_ages
df['cal_sigma_BP'] = cal_sigmas

# Calculate 2-sigma ranges (95.4% confidence)
df['cal_age_min'] = df['cal_age_BP'] - 2 * df['cal_sigma_BP']
df['cal_age_max'] = df['cal_age_BP'] + 2 * df['cal_sigma_BP']

print("\n" + "="*60)
print("CALIBRATED CALENDAR AGES (approximate, cal BP)")
print("="*60)
print("Note: For publication, use OxCal or CALIB with IntCal20")
print("-" * 60)
for idx, row in df.iterrows():
    print(f"{row['artifact_id']}: {row['cal_age_BP']:.0f} ± {row['cal_sigma_BP']:.0f} cal BP")
    print(f"         2σ range: {row['cal_age_min']:.0f} - {row['cal_age_max']:.0f} cal BP")

# =============================================================================
# STEP 3: Stratigraphic Analysis
# =============================================================================
print("\n" + "="*60)
print("STRATIGRAPHIC SEQUENCE ANALYSIS")
print("="*60)

# Extract layer numbers for Trench 3 samples
def extract_layer_number(unit):
    """Extract layer number from stratigraphic unit string."""
    if 'L' in unit:
        try:
            return int(unit.split('L')[1].split('-')[0].split('_')[0])
        except:
            return 99
    elif 'pit' in unit.lower():
        return 0  # Pit feature - intrusive?
    elif 'surface' in unit.lower():
        return -1  # Surface scatter - youngest
    return 99

df['layer_num'] = df['stratigraphic_unit'].apply(extract_layer_number)

# Sort by stratigraphic position (deepest = oldest)
df_sorted = df.sort_values('layer_num', ascending=False)

print("\nStratigraphic Order (deepest/oldest to shallowest/youngest):")
print("-" * 60)
for idx, row in df_sorted.iterrows():
    print(f"{row['stratigraphic_unit']:30s} | Layer {row['layer_num']:2d} | "
          f"{row['cal_age_BP']:.0f} ± {row['cal_sigma_BP']:.0f} cal BP | {row['material']}")

# Check stratigraphic consistency
print("\n" + "="*60)
print("STRATIGRAPHIC CONSISTENCY CHECK")
print("="*60)

# For Trench 3 layers, check if deeper layers are older
trench3 = df[df['stratigraphic_unit'].str.contains('Trench3')].copy()
trench3 = trench3.sort_values('layer_num')

print("\nTrench 3 Sequence (L1=shallowest, L6=deepest):")
print("-" * 60)
for idx, row in trench3.iterrows():
    print(f"{row['stratigraphic_unit']:25s} | {row['cal_age_BP']:.0f} cal BP")

# Check for reversals
reversals = []
for i in range(len(trench3)-1):
    upper = trench3.iloc[i]
    lower = trench3.iloc[i+1]
    # Upper layer should be younger (smaller age)
    if upper['cal_age_BP'] > lower['cal_age_BP'] + 2*(upper['cal_sigma_BP'] + lower['cal_sigma_BP']):
        reversals.append((upper['artifact_id'], lower['artifact_id']))

if reversals:
    print("\n⚠ STRATIGRAPHIC REVERSALS DETECTED:")
    for upper, lower in reversals:
        print(f"  {upper} appears older than {lower} (deeper layer)")
else:
    print("\n✓ No significant stratigraphic reversals detected")

# =============================================================================
# STEP 4: Cultural Periodization
# =============================================================================
print("\n" + "="*60)
print("CULTURAL PERIODIZATION")
print("="*60)

def assign_cultural_period(cal_age_bp):
    """
    Assign cultural period based on calibrated age.
    Using standard Chinese archaeological chronology.
    """
    # Convert cal BP to BCE (cal BP 2024 = 0 CE)
    # cal BP 2024 = 0 CE, cal BP 0 = 2024 CE
    # BCE = cal_BP - 2024
    bce = cal_age_bp - 2024
    
    if cal_age_bp < 200:  # < 200 cal BP
        return "Modern/Contemporary"
    elif cal_age_bp < 500:  # 200-500 cal BP (1524-1824 CE)
        return "Ming-Qing Dynasty"
    elif cal_age_bp < 1000:  # 500-1000 cal BP (1024-1524 CE)
        return "Song-Yuan Dynasty"
    elif cal_age_bp < 1500:  # 1000-1500 cal BP (524-1024 CE)
        return "Tang-Five Dynasties"
    elif cal_age_bp < 2200:  # 1500-2200 cal BP (176 BCE - 524 CE)
        return "Han Dynasty"
    elif cal_age_bp < 2800:  # 2200-2800 cal BP (776-176 BCE)
        return "Warring States/Qin"
    elif cal_age_bp < 3000:  # 2800-3000 cal BP (976-776 BCE)
        return "Spring and Autumn"
    elif cal_age_bp < 3600:  # 3000-3600 cal BP (1576-976 BCE)
        return "Western Zhou"
    elif cal_age_bp < 4000:  # 3600-4000 cal BP (1976-1576 BCE)
        return "Shang Dynasty"
    elif cal_age_bp < 5000:  # 4000-5000 cal BP (2976-1976 BCE)
        return "Xia/Early Bronze Age"
    elif cal_age_bp < 7000:  # 5000-7000 cal BP (4976-2976 BCE)
        return "Neolithic (Yangshao/Longshan)"
    elif cal_age_bp < 10000:  # 7000-10000 cal BP
        return "Early Neolithic"
    else:
        return "Paleolithic/Early Holocene"

df['cultural_period'] = df['cal_age_BP'].apply(assign_cultural_period)

# Calculate BCE years
df['cal_BCE'] = df['cal_age_BP'] - 2024

print("\nCultural Period Assignments:")
print("-" * 60)
for idx, row in df.iterrows():
    bce_str = f"{abs(row['cal_BCE']):.0f} {'BCE' if row['cal_BCE'] > 0 else 'CE'}"
    print(f"{row['artifact_id']:10s} | {row['cal_age_BP']:.0f} cal BP ({bce_str}) | {row['cultural_period']}")

# =============================================================================
# STEP 5: Generate Visualizations
# =============================================================================

# Figure 1: Radiocarbon Age Plot with Stratigraphy
fig, ax = plt.subplots(figsize=(12, 8))

# Sort by age for plotting
df_plot = df.sort_values('cal_age_BP', ascending=True)

# Create y-positions based on stratigraphic order
df_plot['y_pos'] = range(len(df_plot))

# Plot with error bars
for idx, row in df_plot.iterrows():
    color = plt.cm.viridis(row['cal_age_BP'] / df_plot['cal_age_BP'].max())
    ax.errorbar(row['cal_age_BP'], row['y_pos'], 
                xerr=2*row['cal_sigma_BP'],
                fmt='o', markersize=10, capsize=5, capthick=2,
                color=color, ecolor=color, alpha=0.8)
    
    # Add label
    label = f"{row['artifact_id']}\n{row['stratigraphic_unit']}"
    ax.annotate(label, (row['cal_age_BP'], row['y_pos']),
                xytext=(10, 0), textcoords='offset points',
                fontsize=8, va='center')

ax.set_yticks(df_plot['y_pos'])
ax.set_yticklabels([f"{row['stratigraphic_unit']}\n({row['material']})" 
                    for _, row in df_plot.iterrows()], fontsize=9)
ax.set_xlabel('Calibrated Age (cal BP)', fontsize=12)
ax.set_title('Huangtupo Site Radiocarbon Chronology', fontsize=14, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('report/images/chronology_plot.png', dpi=150, bbox_inches='tight')
plt.close()

print("\n✓ Saved: report/images/chronology_plot.png")

# Figure 2: Stratigraphic Column with Ages
fig, ax = plt.subplots(figsize=(10, 10))

# Focus on Trench 3 for stratigraphic column
trench3_sorted = df[df['stratigraphic_unit'].str.contains('Trench3')].sort_values('layer_num', ascending=False)

# Draw stratigraphic column
for i, (idx, row) in enumerate(trench3_sorted.iterrows()):
    y = i * 2
    
    # Draw layer box
    rect = plt.Rectangle((0, y), 4, 1.8, 
                          facecolor=plt.cm.YlOrBr(0.3 + 0.1*i),
                          edgecolor='black', linewidth=2)
    ax.add_patch(rect)
    
    # Add layer label
    ax.text(0.2, y + 0.9, f"Layer {row['layer_num']}", fontsize=11, fontweight='bold')
    ax.text(0.2, y + 0.5, f"{row['material']}", fontsize=9)
    
    # Add age on the right
    ax.text(4.5, y + 0.9, f"{row['cal_age_BP']:.0f} ± {row['cal_sigma_BP']:.0f} cal BP",
            fontsize=10, va='center')
    ax.text(4.5, y + 0.4, f"({row['cultural_period']})",
            fontsize=9, va='center', style='italic')
    
    # Draw connecting line to age
    ax.plot([4, 4.5], [y + 0.9, y + 0.9], 'k-', linewidth=1)

ax.set_xlim(-0.5, 10)
ax.set_ylim(-0.5, len(trench3_sorted) * 2 + 0.5)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('Huangtupo Trench 3: Stratigraphic Sequence with Radiocarbon Ages',
             fontsize=14, fontweight='bold', pad=20)

# Add depth indicator
ax.annotate('', xy=(0, 0), xytext=(0, len(trench3_sorted) * 2),
            arrowprops=dict(arrowstyle='->', lw=2))
ax.text(-0.3, len(trench3_sorted), 'Increasing\nDepth', fontsize=9, 
        ha='center', va='top', rotation=90)

plt.tight_layout()
plt.savefig('report/images/stratigraphic_column.png', dpi=150, bbox_inches='tight')
plt.close()

print("✓ Saved: report/images/stratigraphic_column.png")

# Figure 3: Age Distribution and Timeline
fig, ax = plt.subplots(figsize=(14, 6))

# Sort by calibrated age
df_timeline = df.sort_values('cal_age_BP')

# Plot timeline
for idx, row in df_timeline.iterrows():
    # Plot 2-sigma range as a bar
    ax.barh(0.5, row['cal_age_max'] - row['cal_age_min'], 
            left=row['cal_age_min'], height=0.3,
            color=plt.cm.tab10(list(df_timeline.index).index(idx) % 10),
            alpha=0.6, edgecolor='black')
    
    # Plot mean age as a point
    ax.plot(row['cal_age_BP'], 0.5, 'ko', markersize=8)
    
    # Add label above
    ax.text(row['cal_age_BP'], 0.7, row['artifact_id'], 
            rotation=45, ha='left', fontsize=9)

# Add cultural period bands
periods = [
    (0, 2000, 'Historical Period', 'lightgray'),
    (2000, 4000, 'Bronze Age', 'wheat'),
    (4000, 7000, 'Neolithic', 'lightgreen'),
    (7000, 12000, 'Early Holocene', 'lightblue')
]

for start, end, name, color in periods:
    ax.axvspan(start, end, alpha=0.2, color=color, ymin=0, ymax=0.3)
    ax.text((start + end)/2, 0.15, name, ha='center', fontsize=9)

ax.set_xlim(0, max(df['cal_age_max']) * 1.1)
ax.set_ylim(0, 1)
ax.set_xlabel('Calibrated Years BP', fontsize=12)
ax.set_yticks([])
ax.set_title('Huangtupo Site: Radiocarbon Age Ranges (2σ) on Cultural Timeline',
             fontsize=14, fontweight='bold')
ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/age_timeline.png', dpi=150, bbox_inches='tight')
plt.close()

print("✓ Saved: report/images/age_timeline.png")

# =============================================================================
# STEP 6: Save Results to CSV
# =============================================================================

# Create summary table
summary_df = df[['artifact_id', 'stratigraphic_unit', 'material', 
                 'f14_residual_ratio', 'sigma_f14_absolute',
                 'age_BP', 'sigma_BP', 'cal_age_BP', 'cal_sigma_BP',
                 'cal_age_min', 'cal_age_max', 'cal_BCE', 'cultural_period']].copy()

summary_df.to_csv('outputs/radiocarbon_results.csv', index=False)
print("\n✓ Saved: outputs/radiocarbon_results.csv")

# =============================================================================
# STEP 7: Generate Summary Statistics
# =============================================================================

print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

print(f"\nTotal samples: {len(df)}")
print(f"Age range: {df['cal_age_BP'].min():.0f} - {df['cal_age_BP'].max():.0f} cal BP")
print(f"Time span: {df['cal_age_BP'].max() - df['cal_age_BP'].min():.0f} years")

print("\nMaterials analyzed:")
print(df['material'].value_counts().to_string())

print("\nCultural periods represented:")
print(df['cultural_period'].value_counts().to_string())

# Site occupation summary
print("\n" + "="*60)
print("SITE OCCUPATION SUMMARY")
print("="*60)

# Group by period
period_groups = df.groupby('cultural_period')['cal_age_BP'].agg(['mean', 'min', 'max', 'count'])
print(period_groups.to_string())

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)
