import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit
import os
import warnings
warnings.filterwarnings('ignore')

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load data
print("Loading data...")
df = pd.read_csv('../data/flame_pressure_series.csv')
print(f"Data shape: {df.shape}")
print(f"\nData summary:\n{df.describe()}")

# Extract variables
pressure = df['pressure_kPa'].values
flame_speed = df['flame_speed_cm_s'].values

# Basic statistics
print(f"\nPressure range: {pressure.min():.2f} - {pressure.max():.2f} kPa")
print(f"Flame speed range: {flame_speed.min():.2f} - {flame_speed.max():.2f} cm/s")

# Correlation analysis
correlation = np.corrcoef(pressure, flame_speed)[0, 1]
print(f"\nPearson correlation coefficient: {correlation:.4f}")

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(pressure, flame_speed)
print(f"\nLinear Regression Results:")
print(f"  Slope: {slope:.4f} cm/s per kPa")
print(f"  Intercept: {intercept:.4f} cm/s")
print(f"  R-squared: {r_value**2:.4f}")
print(f"  P-value: {p_value:.4e}")
print(f"  Standard error: {std_err:.4f}")

# Polynomial fit (2nd degree)
coeffs_poly2 = np.polyfit(pressure, flame_speed, 2)
poly2 = np.poly1d(coeffs_poly2)
print(f"\nPolynomial (2nd degree) coefficients:")
print(f"  {coeffs_poly2}")

# Calculate R-squared for polynomial
y_pred_poly2 = poly2(pressure)
ss_res_poly2 = np.sum((flame_speed - y_pred_poly2)**2)
ss_tot = np.sum((flame_speed - np.mean(flame_speed))**2)
r2_poly2 = 1 - (ss_res_poly2 / ss_tot)
print(f"  R-squared: {r2_poly2:.4f}")

# Exponential decay model: y = a * exp(-b * x) + c
def exp_decay(x, a, b, c):
    return a * np.exp(-b * x) + c

# Initial parameter guess
p0 = [30, 0.01, 20]
try:
    popt, pcov = curve_fit(exp_decay, pressure, flame_speed, p0=p0, maxfev=5000)
    y_pred_exp = exp_decay(pressure, *popt)
    ss_res_exp = np.sum((flame_speed - y_pred_exp)**2)
    r2_exp = 1 - (ss_res_exp / ss_tot)
    print(f"\nExponential decay model: y = {popt[0]:.2f} * exp(-{popt[1]:.4f} * x) + {popt[2]:.2f}")
    print(f"  R-squared: {r2_exp:.4f}")
    exp_fit_success = True
except:
    print("\nExponential fit failed")
    exp_fit_success = False

# Power law model: y = a * x^b
def power_law(x, a, b):
    return a * np.power(x, b)

try:
    popt_power, pcov_power = curve_fit(power_law, pressure, flame_speed, p0=[100, -0.5], maxfev=5000)
    y_pred_power = power_law(pressure, *popt_power)
    ss_res_power = np.sum((flame_speed - y_pred_power)**2)
    r2_power = 1 - (ss_res_power / ss_tot)
    print(f"\nPower law model: y = {popt_power[0]:.2f} * x^{popt_power[1]:.4f}")
    print(f"  R-squared: {r2_power:.4f}")
    power_fit_success = True
except:
    print("\nPower law fit failed")
    power_fit_success = False

# Save model comparison results
model_comparison = {
    'Model': ['Linear', 'Polynomial (2nd)', 'Exponential Decay', 'Power Law'],
    'R-squared': [r_value**2, r2_poly2, r2_exp if exp_fit_success else np.nan, r2_power if power_fit_success else np.nan]
}
model_df = pd.DataFrame(model_comparison)
model_df.to_csv('../outputs/model_comparison.csv', index=False)
print(f"\nModel comparison saved to outputs/model_comparison.csv")

# Figure 1: Scatter plot with linear regression
fig1, ax1 = plt.subplots(figsize=(10, 6))
ax1.scatter(pressure, flame_speed, alpha=0.7, label='Data', color='blue', edgecolors='darkblue')
x_line = np.linspace(pressure.min(), pressure.max(), 100)
y_line = slope * x_line + intercept
ax1.plot(x_line, y_line, 'r-', linewidth=2, label=f'Linear fit (R-squared = {r_value**2:.4f})')
ax1.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax1.set_ylabel('Flame Speed (cm/s)', fontsize=12)
ax1.set_title('Flame Speed vs Chamber Pressure with Linear Regression', fontsize=14)
ax1.legend()
ax1.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/linear_regression.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 1 saved: linear_regression.png")

# Figure 2: Multiple model comparison
fig2, ax2 = plt.subplots(figsize=(12, 7))
ax2.scatter(pressure, flame_speed, alpha=0.7, label='Data', color='blue', edgecolors='darkblue', zorder=5)
x_fit = np.linspace(pressure.min(), pressure.max(), 200)

# Linear
ax2.plot(x_fit, slope * x_fit + intercept, 'r-', linewidth=2, label=f'Linear (R-squared = {r_value**2:.4f})')

# Polynomial
ax2.plot(x_fit, poly2(x_fit), 'g-', linewidth=2, label=f'Polynomial 2nd (R-squared = {r2_poly2:.4f})')

# Exponential
if exp_fit_success:
    ax2.plot(x_fit, exp_decay(x_fit, *popt), 'm-', linewidth=2, label=f'Exponential (R-squared = {r2_exp:.4f})')

# Power law
if power_fit_success:
    ax2.plot(x_fit, power_law(x_fit, *popt_power), 'c-', linewidth=2, label=f'Power Law (R-squared = {r2_power:.4f})')

ax2.set_xlabel('Chamber Pressure (kPa)', fontsize=12)
ax2.set_ylabel('Flame Speed (cm/s)', fontsize=12)
ax2.set_title('Flame Speed vs Chamber Pressure: Model Comparison', fontsize=14)
ax2.legend(loc='upper right')
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/model_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: model_comparison.png")

# Figure 3: Residuals analysis for linear model
y_pred_linear = slope * pressure + intercept
residuals = flame_speed - y_pred_linear

fig3, axes = plt.subplots(1, 2, figsize=(14, 5))

# Residuals vs fitted
axes[0].scatter(y_pred_linear, residuals, alpha=0.7, color='blue', edgecolors='darkblue')
axes[0].axhline(y=0, color='r', linestyle='--', linewidth=1.5)
axes[0].set_xlabel('Fitted Values (cm/s)', fontsize=12)
axes[0].set_ylabel('Residuals (cm/s)', fontsize=12)
axes[0].set_title('Residuals vs Fitted Values', fontsize=14)
axes[0].grid(True, alpha=0.3)

# Histogram of residuals
axes[1].hist(residuals, bins=15, edgecolor='black', alpha=0.7, color='steelblue')
axes[1].axvline(x=0, color='r', linestyle='--', linewidth=1.5)
axes[1].set_xlabel('Residuals (cm/s)', fontsize=12)
axes[1].set_ylabel('Frequency', fontsize=12)
axes[1].set_title('Distribution of Residuals', fontsize=14)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/residuals_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved: residuals_analysis.png")

# Figure 4: Data overview with statistics
fig4, axes = plt.subplots(1, 2, figsize=(14, 5))

# Pressure distribution
axes[0].hist(pressure, bins=15, edgecolor='black', alpha=0.7, color='coral')
axes[0].axvline(x=np.mean(pressure), color='r', linestyle='--', linewidth=2, label=f'Mean = {np.mean(pressure):.2f} kPa')
axes[0].set_xlabel('Chamber Pressure (kPa)', fontsize=12)
axes[0].set_ylabel('Frequency', fontsize=12)
axes[0].set_title('Distribution of Chamber Pressure', fontsize=14)
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Flame speed distribution
axes[1].hist(flame_speed, bins=15, edgecolor='black', alpha=0.7, color='lightgreen')
axes[1].axvline(x=np.mean(flame_speed), color='r', linestyle='--', linewidth=2, label=f'Mean = {np.mean(flame_speed):.2f} cm/s')
axes[1].set_xlabel('Flame Speed (cm/s)', fontsize=12)
axes[1].set_ylabel('Frequency', fontsize=12)
axes[1].set_title('Distribution of Flame Speed', fontsize=14)
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/data_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved: data_distribution.png")

# Save detailed statistics
stats_output = {
    'Metric': [
        'Number of observations',
        'Pressure mean (kPa)',
        'Pressure std (kPa)',
        'Pressure min (kPa)',
        'Pressure max (kPa)',
        'Flame speed mean (cm/s)',
        'Flame speed std (cm/s)',
        'Flame speed min (cm/s)',
        'Flame speed max (cm/s)',
        'Correlation coefficient',
        'Linear slope (cm/s per kPa)',
        'Linear intercept (cm/s)',
        'Linear R-squared',
        'Linear p-value',
        'Polynomial R-squared'
    ],
    'Value': [
        len(pressure),
        np.mean(pressure),
        np.std(pressure),
        np.min(pressure),
        np.max(pressure),
        np.mean(flame_speed),
        np.std(flame_speed),
        np.min(flame_speed),
        np.max(flame_speed),
        correlation,
        slope,
        intercept,
        r_value**2,
        p_value,
        r2_poly2
    ]
}
stats_df = pd.DataFrame(stats_output)
stats_df.to_csv('../outputs/statistics_summary.csv', index=False)
print("\nStatistics summary saved to outputs/statistics_summary.csv")

# Identify potential outliers (residuals > 2 std)
residual_std = np.std(residuals)
outlier_mask = np.abs(residuals) > 2 * residual_std
outliers_df = df[outlier_mask].copy()
outliers_df['residual'] = residuals[outlier_mask]
if len(outliers_df) > 0:
    outliers_df.to_csv('../outputs/outliers.csv', index=False)
    print(f"\nIdentified {len(outliers_df)} potential outliers saved to outputs/outliers.csv")

print("\nAnalysis complete!")
