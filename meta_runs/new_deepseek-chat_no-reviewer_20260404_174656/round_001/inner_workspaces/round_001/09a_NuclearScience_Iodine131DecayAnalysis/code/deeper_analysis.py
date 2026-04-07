import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Load the data
data_path = '../data/flame_pressure_series.csv'
df = pd.read_csv(data_path)

# Create a histogram of flame speeds
plt.figure(figsize=(10, 6))
plt.hist(df['flame_speed_cm_s'], bins=15, edgecolor='black', alpha=0.7)
plt.xlabel('Flame Speed (cm/s)', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.title('Distribution of Flame Speeds', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/flame_speed_histogram.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a histogram of pressures
plt.figure(figsize=(10, 6))
plt.hist(df['pressure_kPa'], bins=15, edgecolor='black', alpha=0.7)
plt.xlabel('Pressure (kPa)', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.title('Distribution of Chamber Pressures', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/pressure_histogram.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a box plot of flame speeds by pressure region
threshold = 81.0
df['pressure_region'] = np.where(df['pressure_kPa'] < threshold, 'Low (<81 kPa)', 'High (≥81 kPa)')

plt.figure(figsize=(10, 6))
boxprops = dict(linestyle='-', linewidth=1.5, color='black')
medianprops = dict(linestyle='-', linewidth=2, color='red')
bp = plt.boxplot([df[df['pressure_region'] == 'Low (<81 kPa)']['flame_speed_cm_s'],
                  df[df['pressure_region'] == 'High (≥81 kPa)']['flame_speed_cm_s']],
                 labels=['Low Pressure (<81 kPa)', 'High Pressure (≥81 kPa)'],
                 patch_artist=True,
                 boxprops=boxprops,
                 medianprops=medianprops)

# Color the boxes
colors = ['lightblue', 'lightcoral']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)

plt.ylabel('Flame Speed (cm/s)', fontsize=12)
plt.title('Flame Speed Distribution by Pressure Region', fontsize=14)
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('../report/images/boxplot_by_region.png', dpi=300, bbox_inches='tight')
plt.close()

# Statistical test for difference between regions
low_speeds = df[df['pressure_region'] == 'Low (<81 kPa)']['flame_speed_cm_s']
high_speeds = df[df['pressure_region'] == 'High (≥81 kPa)']['flame_speed_cm_s']

# T-test for difference in means
t_stat, p_value = stats.ttest_ind(low_speeds, high_speeds, equal_var=False)
print(f"T-test between pressure regions:")
print(f"  t-statistic: {t_stat:.4f}")
print(f"  p-value: {p_value:.4e}")
print(f"  Mean low pressure: {low_speeds.mean():.4f} cm/s")
print(f"  Mean high pressure: {high_speeds.mean():.4f} cm/s")
print(f"  Difference: {low_speeds.mean() - high_speeds.mean():.4f} cm/s")

# Create a residual plot for the piecewise model
# First, let's reload the piecewise model parameters from the previous analysis
x0_fit = 81.00
a1_fit = 54.25
b1_fit = -0.449
a2_fit = 24.39
b2_fit = 0.071

def piecewise_linear(x, x0, a1, b1, a2, b2):
    return np.where(x < x0, a1 + b1*x, a2 + b2*x)

y_pred = piecewise_linear(df['pressure_kPa'], x0_fit, a1_fit, b1_fit, a2_fit, b2_fit)
residuals = df['flame_speed_cm_s'] - y_pred

plt.figure(figsize=(10, 6))
plt.scatter(y_pred, residuals, alpha=0.7, edgecolors='k', linewidth=0.5)
plt.axhline(y=0, color='r', linestyle='--', alpha=0.7)
plt.xlabel('Predicted Flame Speed (cm/s)', fontsize=12)
plt.ylabel('Residuals (cm/s)', fontsize=12)
plt.title('Residual Plot for Piecewise Linear Model', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/residual_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a Q-Q plot of residuals
plt.figure(figsize=(10, 6))
stats.probplot(residuals, dist="norm", plot=plt)
plt.title('Q-Q Plot of Residuals (Piecewise Linear Model)', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/qq_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# Calculate and print residual statistics
print(f"\nResidual statistics for piecewise model:")
print(f"  Mean residual: {residuals.mean():.4f} cm/s")
print(f"  Std of residuals: {residuals.std():.4f} cm/s")
print(f"  Max residual: {residuals.max():.4f} cm/s")
print(f"  Min residual: {residuals.min():.4f} cm/s")

# Shapiro-Wilk test for normality of residuals
shapiro_stat, shapiro_p = stats.shapiro(residuals)
print(f"  Shapiro-Wilk test for normality: statistic={shapiro_stat:.4f}, p-value={shapiro_p:.4e}")

# Create a combined plot showing all models
plt.figure(figsize=(12, 8))

# Scatter plot
plt.scatter(df['pressure_kPa'], df['flame_speed_cm_s'], alpha=0.7, edgecolors='k', linewidth=0.5, label='Data')

# Piecewise linear fit
x_fine = np.linspace(df['pressure_kPa'].min(), df['pressure_kPa'].max(), 500)
y_piecewise = piecewise_linear(x_fine, x0_fit, a1_fit, b1_fit, a2_fit, b2_fit)
plt.plot(x_fine, y_piecewise, 'r-', linewidth=2, label='Piecewise linear fit')

# Polynomial fit (degree 3)
coeffs = np.array([-3.61253358e-05, 2.29807977e-02, -2.70050987e+00, 1.12463017e+02])
poly = np.poly1d(coeffs)
y_poly = poly(x_fine)
plt.plot(x_fine, y_poly, 'g--', linewidth=2, label='Polynomial fit (degree 3)')

# Separate linear fits
x_low = np.linspace(df[df['pressure_kPa'] < threshold]['pressure_kPa'].min(), 
                    df[df['pressure_kPa'] < threshold]['pressure_kPa'].max(), 100)
y_low = 54.2530 + (-0.4488) * x_low
plt.plot(x_low, y_low, 'b:', linewidth=2, label='Low pressure linear fit')

x_high = np.linspace(df[df['pressure_kPa'] >= threshold]['pressure_kPa'].min(), 
                     df[df['pressure_kPa'] >= threshold]['pressure_kPa'].max(), 100)
y_high = 24.3863 + 0.0712 * x_high
plt.plot(x_high, y_high, 'm:', linewidth=2, label='High pressure linear fit')

plt.xlabel('Pressure (kPa)', fontsize=12)
plt.ylabel('Flame Speed (cm/s)', fontsize=12)
plt.title('Comparison of Different Models for Flame Speed vs Pressure', fontsize=14)
plt.legend(loc='best')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/model_comparison_plot.png', dpi=300, bbox_inches='tight')
plt.close()

print("\nDeeper analysis complete. Additional plots saved to ../report/images/")
