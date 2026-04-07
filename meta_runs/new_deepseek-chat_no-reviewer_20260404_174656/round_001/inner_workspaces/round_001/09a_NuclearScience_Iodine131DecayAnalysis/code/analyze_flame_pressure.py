import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.optimize import curve_fit
import os

# Set style for better plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# Load the data
data_path = '../data/flame_pressure_series.csv'
df = pd.read_csv(data_path)
print(f"Data shape: {df.shape}")
print(df.head())
print(df.describe())

# Check for missing values
print(f"\nMissing values:\n{df.isnull().sum()}")

# Basic statistics
print(f"\nCorrelation coefficient: {df['pressure_kPa'].corr(df['flame_speed_cm_s'])}")

# Create a scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(df['pressure_kPa'], df['flame_speed_cm_s'], alpha=0.7, edgecolors='k', linewidth=0.5)
plt.xlabel('Pressure (kPa)', fontsize=12)
plt.ylabel('Flame Speed (cm/s)', fontsize=12)
plt.title('Flame Speed vs Chamber Pressure', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/scatter_plot.png', dpi=300, bbox_inches='tight')
plt.savefig('../outputs/scatter_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# Check for potential grouping in the data
# Looking at the data, there seems to be a jump around 82 kPa
# Let's identify potential clusters
from sklearn.cluster import KMeans

# Try K-means clustering
X = df.values
kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(X)

# Plot with clusters
plt.figure(figsize=(10, 6))
colors = ['red', 'blue']
for cluster in [0, 1]:
    cluster_data = df[df['cluster'] == cluster]
    plt.scatter(cluster_data['pressure_kPa'], cluster_data['flame_speed_cm_s'], 
                alpha=0.7, edgecolors='k', linewidth=0.5, 
                label=f'Cluster {cluster}', color=colors[cluster])
plt.xlabel('Pressure (kPa)', fontsize=12)
plt.ylabel('Flame Speed (cm/s)', fontsize=12)
plt.title('Flame Speed vs Pressure with K-means Clustering (k=2)', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/cluster_plot.png', dpi=300, bbox_inches='tight')
plt.savefig('../outputs/cluster_plot.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"\nCluster distribution:\n{df['cluster'].value_counts()}")
print(f"\nCluster centers:\n{kmeans.cluster_centers_}")

# Let's also try to fit different models to different regions
# Based on visual inspection, there's a clear break around 80-82 kPa
threshold = 81.0  # Approximate break point
low_pressure = df[df['pressure_kPa'] < threshold]
high_pressure = df[df['pressure_kPa'] >= threshold]

print(f"\nLow pressure region (< {threshold} kPa): {len(low_pressure)} points")
print(f"High pressure region (>= {threshold} kPa): {len(high_pressure)} points")

# Fit linear models to each region
low_slope, low_intercept, low_r_value, low_p_value, low_std_err = stats.linregress(
    low_pressure['pressure_kPa'], low_pressure['flame_speed_cm_s'])
high_slope, high_intercept, high_r_value, high_p_value, high_std_err = stats.linregress(
    high_pressure['pressure_kPa'], high_pressure['flame_speed_cm_s'])

print(f"\nLow pressure region linear fit:")
print(f"  Slope: {low_slope:.4f}, Intercept: {low_intercept:.4f}")
print(f"  R-squared: {low_r_value**2:.4f}, p-value: {low_p_value:.4e}")

print(f"\nHigh pressure region linear fit:")
print(f"  Slope: {high_slope:.4f}, Intercept: {high_intercept:.4f}")
print(f"  R-squared: {high_r_value**2:.4f}, p-value: {high_p_value:.4e}")

# Plot with separate fits
plt.figure(figsize=(10, 6))
plt.scatter(low_pressure['pressure_kPa'], low_pressure['flame_speed_cm_s'], 
            alpha=0.7, edgecolors='k', linewidth=0.5, label='Low pressure region', color='blue')
plt.scatter(high_pressure['pressure_kPa'], high_pressure['flame_speed_cm_s'], 
            alpha=0.7, edgecolors='k', linewidth=0.5, label='High pressure region', color='red')

# Plot regression lines
x_low = np.linspace(low_pressure['pressure_kPa'].min(), low_pressure['pressure_kPa'].max(), 100)
y_low = low_intercept + low_slope * x_low
plt.plot(x_low, y_low, 'b--', linewidth=2, label=f'Low region fit: y = {low_intercept:.2f} + {low_slope:.3f}x')

x_high = np.linspace(high_pressure['pressure_kPa'].min(), high_pressure['pressure_kPa'].max(), 100)
y_high = high_intercept + high_slope * x_high
plt.plot(x_high, y_high, 'r--', linewidth=2, label=f'High region fit: y = {high_intercept:.2f} + {high_slope:.3f}x')

plt.xlabel('Pressure (kPa)', fontsize=12)
plt.ylabel('Flame Speed (cm/s)', fontsize=12)
plt.title('Flame Speed vs Pressure with Separate Linear Fits', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/separate_fits.png', dpi=300, bbox_inches='tight')
plt.savefig('../outputs/separate_fits.png', dpi=300, bbox_inches='tight')
plt.close()

# Try a piecewise linear model (continuous at breakpoint)
def piecewise_linear(x, x0, a1, b1, a2, b2):
    """Piecewise linear function with break at x0"""
    return np.where(x < x0, a1 + b1*x, a2 + b2*x)

# Initial guess for parameters
# x0: break point, a1,b1: low region, a2,b2: high region
initial_guess = [81.0, 50.0, -0.3, 35.0, -0.05]

# Fit piecewise model
popt, pcov = curve_fit(piecewise_linear, df['pressure_kPa'], df['flame_speed_cm_s'], p0=initial_guess, maxfev=5000)
x0_fit, a1_fit, b1_fit, a2_fit, b2_fit = popt

print(f"\nPiecewise linear fit:")
print(f"  Break point (x0): {x0_fit:.2f} kPa")
print(f"  Low region: y = {a1_fit:.2f} + {b1_fit:.3f}x")
print(f"  High region: y = {a2_fit:.2f} + {b2_fit:.3f}x")

# Calculate R-squared for piecewise model
y_pred = piecewise_linear(df['pressure_kPa'], *popt)
residuals = df['flame_speed_cm_s'] - y_pred
ss_res = np.sum(residuals**2)
ss_tot = np.sum((df['flame_speed_cm_s'] - np.mean(df['flame_speed_cm_s']))**2)
r_squared = 1 - (ss_res / ss_tot)
print(f"  R-squared: {r_squared:.4f}")

# Plot piecewise fit
plt.figure(figsize=(10, 6))
plt.scatter(df['pressure_kPa'], df['flame_speed_cm_s'], alpha=0.7, edgecolors='k', linewidth=0.5, label='Data')

# Generate points for piecewise function
x_fine = np.linspace(df['pressure_kPa'].min(), df['pressure_kPa'].max(), 500)
y_fine = piecewise_linear(x_fine, *popt)
plt.plot(x_fine, y_fine, 'r-', linewidth=2, label='Piecewise linear fit')

# Mark the break point
plt.axvline(x=x0_fit, color='g', linestyle='--', alpha=0.7, label=f'Break point: {x0_fit:.1f} kPa')

plt.xlabel('Pressure (kPa)', fontsize=12)
plt.ylabel('Flame Speed (cm/s)', fontsize=12)
plt.title('Flame Speed vs Pressure with Piecewise Linear Fit', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/piecewise_fit.png', dpi=300, bbox_inches='tight')
plt.savefig('../outputs/piecewise_fit.png', dpi=300, bbox_inches='tight')
plt.close()

# Also try a simple polynomial fit for comparison
degree = 3
coeffs = np.polyfit(df['pressure_kPa'], df['flame_speed_cm_s'], degree)
poly = np.poly1d(coeffs)

print(f"\nPolynomial fit (degree {degree}):")
print(f"  Coefficients: {coeffs}")
print(f"  Equation: y = {coeffs[0]:.2e}x^3 + {coeffs[1]:.2e}x^2 + {coeffs[2]:.3f}x + {coeffs[3]:.2f}")

# Calculate R-squared for polynomial
poly_pred = poly(df['pressure_kPa'])
poly_residuals = df['flame_speed_cm_s'] - poly_pred
poly_ss_res = np.sum(poly_residuals**2)
poly_r_squared = 1 - (poly_ss_res / ss_tot)
print(f"  R-squared: {poly_r_squared:.4f}")

# Plot polynomial fit
plt.figure(figsize=(10, 6))
plt.scatter(df['pressure_kPa'], df['flame_speed_cm_s'], alpha=0.7, edgecolors='k', linewidth=0.5, label='Data')
plt.plot(x_fine, poly(x_fine), 'purple', linewidth=2, label=f'Polynomial fit (degree {degree})')
plt.xlabel('Pressure (kPa)', fontsize=12)
plt.ylabel('Flame Speed (cm/s)', fontsize=12)
plt.title('Flame Speed vs Pressure with Polynomial Fit', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/polynomial_fit.png', dpi=300, bbox_inches='tight')
plt.savefig('../outputs/polynomial_fit.png', dpi=300, bbox_inches='tight')
plt.close()

# Compare all models
print(f"\nModel comparison:")
print(f"  Piecewise linear R-squared: {r_squared:.4f}")
print(f"  Polynomial (degree {degree}) R-squared: {poly_r_squared:.4f}")
print(f"  Low region only R-squared: {low_r_value**2:.4f}")
print(f"  High region only R-squared: {high_r_value**2:.4f}")

# Save results to CSV
results_df = pd.DataFrame({
    'model': ['piecewise_linear', f'polynomial_degree_{degree}', 'low_region_only', 'high_region_only'],
    'r_squared': [r_squared, poly_r_squared, low_r_value**2, high_r_value**2],
    'parameters': [str(popt), str(coeffs), f'slope={low_slope:.4f}, intercept={low_intercept:.4f}', 
                   f'slope={high_slope:.4f}, intercept={high_intercept:.4f}']
})
results_df.to_csv('../outputs/model_comparison.csv', index=False)

print("\nAnalysis complete. Results saved to ../outputs/ and ../report/images/")
