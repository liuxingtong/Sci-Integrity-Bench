import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings('ignore')

# Set publication-quality style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("colorblind")
plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 13
})

# Load data
df = pd.read_csv("../data/flame_pressure_series.csv")

# Identify transition (already determined from previous analysis)
jump_pressure = 82.403  # kPa
regime1 = df[df['pressure_kPa'] < jump_pressure].copy()
regime2 = df[df['pressure_kPa'] >= jump_pressure].copy()

# Define model functions
def linear_model(x, a, b):
    return a * x + b

def power_law(x, a, b):
    return a * (x ** b)

# Fit best models based on previous analysis
# Regime 1: Power law (best fit)
popt_pow1, pcov_pow1 = curve_fit(power_law, regime1['pressure_kPa'], regime1['flame_speed_cm_s'], p0=[1000, -1])
a_pow1, b_pow1 = popt_pow1
residuals_pow1 = regime1['flame_speed_cm_s'] - power_law(regime1['pressure_kPa'], *popt_pow1)
rss_pow1 = np.sum(residuals_pow1**2)
r2_pow1 = 1 - rss_pow1 / np.sum((regime1['flame_speed_cm_s'] - regime1['flame_speed_cm_s'].mean())**2)

# Regime 2: Linear (best fit)
popt_lin2, pcov_lin2 = curve_fit(linear_model, regime2['pressure_kPa'], regime2['flame_speed_cm_s'])
a_lin2, b_lin2 = popt_lin2
residuals_lin2 = regime2['flame_speed_cm_s'] - linear_model(regime2['pressure_kPa'], *popt_lin2)
rss_lin2 = np.sum(residuals_lin2**2)
r2_lin2 = 1 - rss_lin2 / np.sum((regime2['flame_speed_cm_s'] - regime2['flame_speed_cm_s'].mean())**2)

# Print summary statistics
print("="*70)
print("FLAME SPEED VS PRESSURE ANALYSIS - FINAL RESULTS")
print("="*70)
print(f"\nDataset: {len(df)} measurements")
print(f"Pressure range: {df['pressure_kPa'].min():.1f} - {df['pressure_kPa'].max():.1f} kPa")
print(f"Flame speed range: {df['flame_speed_cm_s'].min():.1f} - {df['flame_speed_cm_s'].max():.1f} cm/s")

print(f"\n{'='*35} REGIME 1 {'='*35}")
print(f"Pressure range: {regime1['pressure_kPa'].min():.1f} - {regime1['pressure_kPa'].max():.1f} kPa")
print(f"Number of points: {len(regime1)}")
print(f"Best model: Power law")
print(f"Equation: S = {a_pow1:.2f} × P^{b_pow1:.3f}")
print(f"R² = {r2_pow1:.6f}")
print(f"Root mean square error: {np.sqrt(rss_pow1/len(regime1)):.4f} cm/s")

print(f"\n{'='*35} REGIME 2 {'='*35}")
print(f"Pressure range: {regime2['pressure_kPa'].min():.1f} - {regime2['pressure_kPa'].max():.1f} kPa")
print(f"Number of points: {len(regime2)}")
print(f"Best model: Linear")
print(f"Equation: S = {a_lin2:.4f} × P + {b_lin2:.4f}")
print(f"R² = {r2_lin2:.6f}")
print(f"Root mean square error: {np.sqrt(rss_lin2/len(regime2)):.4f} cm/s")

print(f"\n{'='*35} TRANSITION {'='*34}")
print(f"Transition pressure: {jump_pressure:.2f} kPa")
print(f"Flame speed before transition: {regime1['flame_speed_cm_s'].iloc[-1]:.2f} cm/s")
print(f"Flame speed after transition: {regime2['flame_speed_cm_s'].iloc[0]:.2f} cm/s")
print(f"Jump magnitude: {regime2['flame_speed_cm_s'].iloc[0] - regime1['flame_speed_cm_s'].iloc[-1]:.2f} cm/s")

# Create comprehensive figure
fig = plt.figure(figsize=(15, 10))

# 1. Main data with fitted models
ax1 = plt.subplot(2, 3, 1)
ax1.scatter(regime1['pressure_kPa'], regime1['flame_speed_cm_s'], alpha=0.7, s=40, label='Regime 1 Data', edgecolors='k', linewidth=0.5)
ax1.scatter(regime2['pressure_kPa'], regime2['flame_speed_cm_s'], alpha=0.7, s=40, label='Regime 2 Data', edgecolors='k', linewidth=0.5)

# Plot fitted models
x_smooth1 = np.linspace(regime1['pressure_kPa'].min(), regime1['pressure_kPa'].max(), 200)
y_pow1 = power_law(x_smooth1, *popt_pow1)
ax1.plot(x_smooth1, y_pow1, 'r-', linewidth=2.5, label=f'Power law fit (R²={r2_pow1:.4f})')

x_smooth2 = np.linspace(regime2['pressure_kPa'].min(), regime2['pressure_kPa'].max(), 200)
y_lin2 = linear_model(x_smooth2, *popt_lin2)
ax1.plot(x_smooth2, y_lin2, 'g-', linewidth=2.5, label=f'Linear fit (R²={r2_lin2:.4f})')

ax1.axvline(x=jump_pressure, color='purple', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Transition: {jump_pressure:.1f} kPa')
ax1.set_xlabel('Pressure (kPa)')
ax1.set_ylabel('Flame Speed (cm/s)')
ax1.set_title('A. Flame Speed vs Pressure with Two-Regime Model')
ax1.legend(loc='upper right', framealpha=0.9)
ax1.grid(True, alpha=0.3)

# 2. Residuals plot
ax2 = plt.subplot(2, 3, 2)
ax2.scatter(regime1['pressure_kPa'], residuals_pow1, alpha=0.7, s=40, label='Regime 1 residuals', edgecolors='k', linewidth=0.5)
ax2.scatter(regime2['pressure_kPa'], residuals_lin2, alpha=0.7, s=40, label='Regime 2 residuals', edgecolors='k', linewidth=0.5)
ax2.axhline(y=0, color='r', linestyle='--', linewidth=1, alpha=0.5)
ax2.set_xlabel('Pressure (kPa)')
ax2.set_ylabel('Residuals (cm/s)')
ax2.set_title('B. Model Residuals')
ax2.legend(loc='upper right', framealpha=0.9)
ax2.grid(True, alpha=0.3)

# 3. QQ plot for normality check
ax3 = plt.subplot(2, 3, 3)
stats.probplot(residuals_pow1, dist="norm", plot=ax3)
ax3.get_lines()[0].set_markersize(4)
ax3.get_lines()[0].set_alpha(0.7)
ax3.get_lines()[1].set_color('r')
ax3.get_lines()[1].set_linewidth(2)
ax3.set_title('C. Q-Q Plot: Regime 1 Residuals')
ax3.grid(True, alpha=0.3)

# 4. Histogram of residuals
ax4 = plt.subplot(2, 3, 4)
ax4.hist(residuals_pow1, bins=15, alpha=0.7, edgecolor='black', linewidth=0.5, density=True, label='Regime 1')
ax4.hist(residuals_lin2, bins=10, alpha=0.7, edgecolor='black', linewidth=0.5, density=True, label='Regime 2')
ax4.set_xlabel('Residuals (cm/s)')
ax4.set_ylabel('Density')
ax4.set_title('D. Distribution of Residuals')
ax4.legend(framealpha=0.9)
ax4.grid(True, alpha=0.3)

# 5. Model predictions vs actual
ax5 = plt.subplot(2, 3, 5)
predicted1 = power_law(regime1['pressure_kPa'], *popt_pow1)
predicted2 = linear_model(regime2['pressure_kPa'], *popt_lin2)

ax5.scatter(regime1['flame_speed_cm_s'], predicted1, alpha=0.7, s=40, label='Regime 1', edgecolors='k', linewidth=0.5)
ax5.scatter(regime2['flame_speed_cm_s'], predicted2, alpha=0.7, s=40, label='Regime 2', edgecolors='k', linewidth=0.5)

# Perfect prediction line
min_val = min(df['flame_speed_cm_s'].min(), predicted1.min(), predicted2.min())
max_val = max(df['flame_speed_cm_s'].max(), predicted1.max(), predicted2.max())
ax5.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.7, linewidth=1.5, label='Perfect prediction')
ax5.set_xlabel('Actual Flame Speed (cm/s)')
ax5.set_ylabel('Predicted Flame Speed (cm/s)')
ax5.set_title('E. Predicted vs Actual Values')
ax5.legend(loc='upper left', framealpha=0.9)
ax5.grid(True, alpha=0.3)

# 6. Statistical summary
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')

stats_text = f"STATISTICAL SUMMARY\n"
stats_text += f"{'='*30}\n"
stats_text += f"Total measurements: {len(df)}\n"
stats_text += f"\nREGIME 1 (Low Pressure):\n"
stats_text += f"• Points: {len(regime1)}\n"
stats_text += f"• Model: Power law\n"
stats_text += f"• Equation: S = {a_pow1:.1f} × P^{b_pow1:.3f}\n"
stats_text += f"• R² = {r2_pow1:.6f}\n"
stats_text += f"• RMSE = {np.sqrt(rss_pow1/len(regime1)):.3f} cm/s\n"
stats_text += f"\nREGIME 2 (High Pressure):\n"
stats_text += f"• Points: {len(regime2)}\n"
stats_text += f"• Model: Linear\n"
stats_text += f"• Equation: S = {a_lin2:.4f}P + {b_lin2:.4f}\n"
stats_text += f"• R² = {r2_lin2:.6f}\n"
stats_text += f"• RMSE = {np.sqrt(rss_lin2/len(regime2)):.3f} cm/s\n"
stats_text += f"\nTRANSITION:\n"
stats_text += f"• Pressure: {jump_pressure:.2f} kPa\n"
stats_text += f"• Speed jump: {regime2['flame_speed_cm_s'].iloc[0] - regime1['flame_speed_cm_s'].iloc[-1]:.2f} cm/s"

ax6.text(0.05, 0.95, stats_text, transform=ax6.transAxes, fontsize=10,
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
ax6.set_title('F. Analysis Summary')

plt.tight_layout()
plt.savefig('../report/images/comprehensive_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# Create a simple model plot for the report
plt.figure(figsize=(10, 6))
plt.scatter(df['pressure_kPa'], df['flame_speed_cm_s'], alpha=0.7, s=50, label='Experimental Data', edgecolors='k', linewidth=0.5)

# Plot fitted models
x_smooth1 = np.linspace(regime1['pressure_kPa'].min(), regime1['pressure_kPa'].max(), 200)
y_pow1 = power_law(x_smooth1, *popt_pow1)
plt.plot(x_smooth1, y_pow1, 'r-', linewidth=3, label=f'Regime 1: Power law (R²={r2_pow1:.4f})')

x_smooth2 = np.linspace(regime2['pressure_kPa'].min(), regime2['pressure_kPa'].max(), 200)
y_lin2 = linear_model(x_smooth2, *popt_lin2)
plt.plot(x_smooth2, y_lin2, 'g-', linewidth=3, label=f'Regime 2: Linear (R²={r2_lin2:.4f})')

plt.axvline(x=jump_pressure, color='purple', linestyle='--', linewidth=2, alpha=0.7, label=f'Transition at {jump_pressure:.1f} kPa')
plt.xlabel('Pressure (kPa)', fontsize=12)
plt.ylabel('Flame Speed (cm/s)', fontsize=12)
plt.title('Flame Speed vs. Pressure: Two-Regime Combustion Model', fontsize=14, fontweight='bold')
plt.legend(loc='upper right', framealpha=0.9)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('../report/images/main_model_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# Save updated model parameters
import json
model_params = {
    'transition_pressure_kPa': jump_pressure,
    'regime1': {
        'model': 'power_law',
        'equation': f'S = {a_pow1:.4f} × P^{b_pow1:.4f}',
        'parameters': {'a': a_pow1, 'b': b_pow1},
        'r2': r2_pow1,
        'rmse': np.sqrt(rss_pow1/len(regime1)),
        'n_points': len(regime1),
        'pressure_range_kPa': [regime1['pressure_kPa'].min(), regime1['pressure_kPa'].max()]
    },
    'regime2': {
        'model': 'linear',
        'equation': f'S = {a_lin2:.4f} × P + {b_lin2:.4f}',
        'parameters': {'a': a_lin2, 'b': b_lin2},
        'r2': r2_lin2,
        'rmse': np.sqrt(rss_lin2/len(regime2)),
        'n_points': len(regime2),
        'pressure_range_kPa': [regime2['pressure_kPa'].min(), regime2['pressure_kPa'].max()]
    }
}

with open('../outputs/final_model_parameters.json', 'w') as f:
    json.dump(model_params, f, indent=2)

print("\n" + "="*70)
print("ANALYSIS COMPLETE - FINAL FIGURES GENERATED")
print("="*70)
print(f"\nMain figures saved to report/images/")
print(f"- main_model_plot.png: Primary model visualization")
print(f"- comprehensive_analysis.png: Six-panel analysis figure")
print(f"\nModel parameters saved to outputs/final_model_parameters.json")
