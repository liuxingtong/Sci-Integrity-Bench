import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Read calibrated data
df = pd.read_csv("../outputs/calibrated_ages.csv")
print("Calibrated data loaded")

# Define cultural periods for the region (approximate, based on Chinese archaeology)
# These are generalized periods for demonstration
cultural_periods = [
    {"name": "Paleolithic", "start_BP": 50000, "end_BP": 10000, "color": "#8c510a"},
    {"name": "Early Neolithic", "start_BP": 10000, "end_BP": 7000, "color": "#d8b365"},
    {"name": "Middle Neolithic", "start_BP": 7000, "end_BP": 5000, "color": "#f6e8c3"},
    {"name": "Late Neolithic", "start_BP": 5000, "end_BP": 4000, "color": "#c7eae5"},
    {"name": "Bronze Age", "start_BP": 4000, "end_BP": 2500, "color": "#5ab4ac"},
    {"name": "Iron Age", "start_BP": 2500, "end_BP": 2000, "color": "#01665e"},
    {"name": "Historical Period", "start_BP": 2000, "end_BP": 0, "color": "#003c30"},
]

# Assign samples to cultural periods
def assign_period(age_bp):
    for period in cultural_periods:
        if period["end_BP"] <= age_bp < period["start_BP"]:
            return period["name"]
    return "Unknown"

df['cultural_period'] = df['calibrated_age_BP'].apply(assign_period)

print("\n=== Cultural Period Assignment ===")
print("Cultural periods defined:")
for period in cultural_periods:
    print(f"  {period['name']}: {period['start_BP']:,} - {period['end_BP']:,} BP")

print("\nSample period assignments:")
for _, row in df.iterrows():
    print(f"  {row['artifact_id']}: {row['calibrated_age_BP']:.0f} BP → {row['cultural_period']}")

# Create visualization of cultural periods with samples
plt.figure(figsize=(14, 10))

# Plot cultural periods as horizontal bars
for i, period in enumerate(cultural_periods):
    plt.barh(i, period["start_BP"] - period["end_BP"], 
             left=period["end_BP"], 
             color=period["color"], 
             alpha=0.7, 
             edgecolor='black')
    plt.text(period["end_BP"] + (period["start_BP"] - period["end_BP"])/2, 
             i, 
             period["name"], 
             ha='center', va='center', 
             fontweight='bold', fontsize=10)

# Plot samples with error bars
# Map periods to y-positions
period_to_y = {period["name"]: i for i, period in enumerate(cultural_periods)}

for _, row in df.iterrows():
    y_pos = period_to_y.get(row['cultural_period'], len(cultural_periods))
    
    # Plot point
    plt.plot(row['calibrated_age_BP'], y_pos + 0.3, 
             'o', markersize=10, 
             color='red', markeredgecolor='black', 
             label=row['artifact_id'] if _ == 0 else "")
    
    # Plot error bar
    plt.errorbar(row['calibrated_age_BP'], y_pos + 0.3,
                 xerr=row['calibrated_sigma_BP'],
                 fmt='none', color='black', alpha=0.7, capsize=5)
    
    # Add label
    plt.text(row['calibrated_age_BP'] + row['calibrated_sigma_BP'] + 200, 
             y_pos + 0.3, 
             f"{row['artifact_id']}\n{row['stratigraphic_unit']}\n{row['material']}",
             fontsize=8, va='center')

plt.xlabel('Calendar Years BP')
plt.ylabel('Cultural Period')
plt.title('Huangtupo Site: Cultural Periodization Based on Radiocarbon Dates')
plt.yticks(range(len(cultural_periods)), [p["name"] for p in cultural_periods])
plt.gca().invert_xaxis()  # Older to the right
plt.grid(True, alpha=0.3, axis='x')
plt.legend(['Radiocarbon Samples'], loc='upper right')

plt.tight_layout()
plot_path = "../report/images/cultural_periodization.png"
plt.savefig(plot_path, dpi=300, bbox_inches='tight')
print(f"\nPlot saved to {plot_path}")

# Analyze sample distribution across periods
print("\n=== Distribution Analysis ===")
period_counts = df['cultural_period'].value_counts()
print("Samples per cultural period:")
for period, count in period_counts.items():
    samples = df[df['cultural_period'] == period]['artifact_id'].tolist()
    print(f"  {period}: {count} samples ({', '.join(samples)})")

# Calculate statistics by period
print("\nStatistics by cultural period:")
for period in cultural_periods:
    period_samples = df[df['cultural_period'] == period["name"]]
    if len(period_samples) > 0:
        ages = period_samples['calibrated_age_BP']
        print(f"\n{period['name']}:")
        print(f"  Number of samples: {len(period_samples)}")
        print(f"  Mean age: {ages.mean():.0f} BP")
        print(f"  Age range: {ages.min():.0f} - {ages.max():.0f} BP")
        print(f"  Samples: {', '.join(period_samples['artifact_id'].tolist())}")

# Check for anomalies
print("\n=== Anomaly Detection ===")
# Samples that don't fit expected stratigraphic order
print("Potential anomalies:")

# AC-109 and AC-110 are extremely old compared to other Trench3 samples
old_samples = df[df['calibrated_age_BP'] > 20000]
if len(old_samples) > 0:
    print("\nVery old samples (>20k BP):")
    for _, sample in old_samples.iterrows():
        print(f"  {sample['artifact_id']}: {sample['calibrated_age_BP']:.0f} BP from {sample['stratigraphic_unit']}")
        print(f"    Material: {sample['material']}, Notes: {sample['notes']}")
        print(f"    This may indicate: contamination, old carbon reservoir, or re-deposited material")

# Check for consistency within trenches
trench_groups = df.groupby('trench')
print("\nTrench-level consistency:")
for trench, group in trench_groups:
    if len(group) > 1:
        age_range = group['calibrated_age_BP'].max() - group['calibrated_age_BP'].min()
        print(f"\nTrench {trench}:")
        print(f"  Age range: {age_range:.0f} years")
        print(f"  Samples span: {group['calibrated_age_BP'].min():.0f} - {group['calibrated_age_BP'].max():.0f} BP")
        
        if age_range > 10000:
            print(f"  ⚠ Large age range suggests mixed deposits or sampling issues")
        elif age_range > 5000:
            print(f"  ~ Moderate age range, possible multi-period occupation")
        else:
            print(f"  ✓ Relatively consistent ages")

print("\nCultural periodization analysis complete!")