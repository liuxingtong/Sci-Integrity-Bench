import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load data
df = pd.read_csv("../data/flame_pressure_series.csv")

# Identify the discontinuity point
df['flame_speed_diff'] = df['flame_speed_cm_s'].diff()
max_jump_idx = df['flame_speed_diff'].idxmax()
max_jump_pressure = df.loc[max_jump_idx, 'pressure_kPa']
max_jump_speed = df.loc[max_jump_idx, 'flame_speed_cm_s']

print(f"Maximum jump occurs at pressure: {max_jump_pressure:.3f} kPa")
print(f"Flame speed jumps from {df.loc[max_jump_idx-1, 'flame_speed_cm_s']:.3f} to {max_jump_speed:.3f} cm/s")
print(f"Jump magnitude: {df.loc[max_jump_idx, 'flame_speed_diff']:.3f} cm/s")

# Split data into two regimes based on the jump
regime1 = df[df['pressure_kPa'] < max_jump_pressure].copy()
regime2 = df[df['pressure_kPa'] >= max_jump_pressure].copy()

print(f"\nRegime 1 (low pressure): {len(regime1)} data points")
print(f"Pressure range: {regime1['pressure_kPa'].min():.1f} to {regime1['pressure_kPa'].max():.1f} kPa")
print(f"Flame speed range: {regime1['flame_speed_cm_s'].min():.2f} to {regime1['flame_speed_cm_s'].max():.2f} cm/s")

print(f"\nRegime 2 (high pressure): {len(regime2)} data points")
print(f"Pressure range: {regime2['pressure_kPa'].min():.1f} to {regime2['pressure_kPa'].max():.1f} kPa")
print(f"Flame speed range: {regime2['flame_speed_cm_s'].min():.2f} to {regime2['flame_speed_cm_s'].max():.2f} cm/s")

# Create visualization with two regimes
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Scatter plot with color-coded regimes
ax = axes[0, 0]
ax.scatter(regime1['pressure_kPa'], regime1['flame_speed_cm_s'], 
           alpha=0.7, s=60, label='Regime 1 (Low Pressure)', color='blue')
ax.scatter(regime2['pressure_kPa'], regime2['flame_speed_cm_s'], 
           alpha=0.7, s=60, label='Regime 2 (High Pressure)', color='red')
ax.axvline(x=max_jump_pressure, color='gray', linestyle='--', alpha=0.7, 
           label=f'Discontinuity at {max_jump_pressure:.1f} kPa')
ax.set_xlabel('Pressure (kPa)')
ax.set_ylabel('Flame Speed (cm/s)')
ax.set_title('Flame Speed vs Chamber Pressure (Two Regimes)')
ax.legend()
ax.grid(True, alpha=0.3)

# Time series view (assuming data is in chronological order)
ax = axes[0, 1]
ax.plot(df.index, df['flame_speed_cm_s'], 'o-', alpha=0.7, markersize=4)
ax.axvline(x=max_jump_idx, color='gray', linestyle='--', alpha=0.7)
ax.set_xlabel('Measurement Index')
ax.set_ylabel('Flame Speed (cm/s)')
ax.set_title('Flame Speed Time Series')
ax.grid(True, alpha=0.3)

# Histograms of flame speeds for each regime
ax = axes[1, 0]
ax.hist(regime1['flame_speed_cm_s'], bins=15, alpha=0.7, label='Regime 1', color='blue', density=True)
ax.hist(regime2['flame_speed_cm_s'], bins=15, alpha=0.7, label='Regime 2', color='red', density=True)
ax.set_xlabel('Flame Speed (cm/s)')
ax.set_ylabel('Density')
ax.set_title('Distribution of Flame Speeds in Two Regimes')
ax.legend()
ax.grid(True, alpha=0.3)

# Box plot comparison
ax = axes[1, 1]
box_data = [regime1['flame_speed_cm_s'], regime2['flame_speed_cm_s']]
box_labels = ['Regime 1', 'Regime 2']
bp = ax.boxplot(box_data, labels=box_labels, patch_artist=True)
bp['boxes'][0].set_facecolor('blue')
bp['boxes'][1].set_facecolor('red')
ax.set_ylabel('Flame Speed (cm/s)')
ax.set_title('Box Plot Comparison of Two Regimes')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/data_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# Statistical comparison
print("\n--- Statistical Comparison ---")
print(f"Regime 1 mean flame speed: {regime1['flame_speed_cm_s'].mean():.3f} ± {regime1['flame_speed_cm_s'].std():.3f} cm/s")
print(f"Regime 2 mean flame speed: {regime2['flame_speed_cm_s'].mean():.3f} ± {regime2['flame_speed_cm_s'].std():.3f} cm/s")

# T-test for difference in means
t_stat, p_value = stats.ttest_ind(regime1['flame_speed_cm_s'], regime2['flame_speed_cm_s'])
print(f"\nT-test for difference in means:")
print(f"  t-statistic: {t_stat:.4f}")
print(f"  p-value: {p_value:.6f}")
if p_value < 0.05:
    print("  Significant difference at p < 0.05")
else:
    print("  No significant difference at p < 0.05")

# Save regime data for modeling
regime1.to_csv('../outputs/regime1_data.csv', index=False)
regime2.to_csv('../outputs/regime2_data.csv', index=False)
df.to_csv('../outputs/full_data_with_diff.csv', index=False)

print("\nAnalysis complete. Figures saved to report/images/")
print("Data saved to outputs/")
