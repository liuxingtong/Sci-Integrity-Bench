import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

print("Generating data quality visualization...")

# Load original field data to show issues
field_df = pd.read_csv('../data/field_ops_export.csv', encoding='utf-8-sig')

# Create visualization of data quality issues
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: Valid vs Invalid Records
valid_count = 30  # From our analysis
invalid_count = 2  # From our analysis

categories = ['Valid Records', 'Invalid Records']
counts = [valid_count, invalid_count]
colors = ['#2ecc71', '#e74c3c']

axes[0].bar(categories, counts, color=colors, edgecolor='black')
axes[0].set_title('Field Data Quality Assessment', fontsize=14, fontweight='bold')
axes[0].set_ylabel('Number of Records', fontsize=12)
axes[0].grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, v in enumerate(counts):
    axes[0].text(i, v + 0.5, str(v), ha='center', va='bottom', fontweight='bold')

# Plot 2: kWh values highlighting outliers
# Identify the outlier values
outlier_data = field_df[field_df['Delivered_kWh'] > 100]  # The 9999 value
normal_data = field_df[field_df['Delivered_kWh'] <= 100]

axes[1].scatter(range(len(normal_data)), normal_data['Delivered_kWh'], 
               alpha=0.7, s=60, label='Normal Values (≤100 kWh)', color='#3498db')

# Plot outliers in red
if len(outlier_data) > 0:
    outlier_indices = outlier_data.index
    axes[1].scatter(outlier_indices, outlier_data['Delivered_kWh'], 
                   alpha=0.9, s=100, label='Outliers', color='#e74c3c', marker='X')
    
    # Annotate the outlier
    for idx, row in outlier_data.iterrows():
        axes[1].annotate(f'{row["Delivered_kWh"]} kWh', 
                        xy=(idx, row['Delivered_kWh']),
                        xytext=(idx, row['Delivered_kWh'] + 2000),
                        arrowprops=dict(arrowstyle='->', color='red', alpha=0.7),
                        ha='center', fontweight='bold', color='red')

axes[1].set_title('kWh Values with Outlier Detection', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Record Index', fontsize=12)
axes[1].set_ylabel('Delivered kWh', fontsize=12)
axes[1].legend(loc='upper left')
axes[1].grid(True, alpha=0.3)

# Add a horizontal line at 100 kWh for reference
axes[1].axhline(y=100, color='green', linestyle='--', alpha=0.5, label='Normal Range Threshold')

plt.tight_layout()
plt.savefig('../report/images/data_quality_issues.png', dpi=300, bbox_inches='tight')
print("Saved: data_quality_issues.png")
plt.close()

# Create a summary table of data quality issues
data_quality_summary = pd.DataFrame({
    'Issue Type': ['Missing Date', 'Invalid Date Format', 'Outlier Value'],
    'Count': [1, 1, 1],
    'Example': ['Date: NaN, Unit: T-01, Value: 9999 kWh', 
                "Date: '13/37/2024', Unit: T-02, Value: 1 kWh",
                'Value: 9999 kWh (obvious outlier)'],
    'Impact': ['Record excluded from analysis', 
               'Record excluded from analysis',
               'Record excluded from analysis']
})

data_quality_summary.to_csv('../outputs/data_quality_summary.csv', index=False)
print("\nData Quality Summary:")
print(data_quality_summary.to_string(index=False))
print("\nData quality visualization complete!")
