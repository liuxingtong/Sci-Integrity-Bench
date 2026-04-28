import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

# Load data
df = pd.read_csv('data/flame_pressure_series.csv')

# Split data into two regimes
regime1 = df[df['pressure_kPa'] < 82]
regime2 = df[df['pressure_kPa'] >= 82]

# Define models
def power_law(x, a, b):
    return a * np.power(x, b)

def linear(x, a, b):
    return a * x + b

# Fit models
popt_power, _ = curve_fit(power_law, regime1['pressure_kPa'], regime1['flame_speed_cm_s'])
popt_lin2, _ = curve_fit(linear, regime2['pressure_kPa'], regime2['flame_speed_cm_s'])

# Plot
plt.figure(figsize=(10, 6))
plt.scatter(regime1['pressure_kPa'], regime1['flame_speed_cm_s'], label='Regime 1 Data', color='blue', s=20, alpha=0.7)
plt.scatter(regime2['pressure_kPa'], regime2['flame_speed_cm_s'], label='Regime 2 Data', color='red', s=20, alpha=0.7)

# Plot regime 1 fit
x_fit1 = np.linspace(regime1['pressure_kPa'].min(), regime1['pressure_kPa'].max(), 100)
plt.plot(x_fit1, power_law(x_fit1, *popt_power), label=f'Power Law Fit (Regime 1): $y={popt_power[0]:.2f}x^{{{popt_power[1]:.2f}}}$', color='darkblue', linewidth=2)

# Plot regime 2 fit
x_fit2 = np.linspace(regime2['pressure_kPa'].min(), regime2['pressure_kPa'].max(), 100)
plt.plot(x_fit2, linear(x_fit2, *popt_lin2), label=f'Linear Fit (Regime 2): $y={popt_lin2[0]:.2f}x+{popt_lin2[1]:.2f}$', color='darkred', linewidth=2)

plt.xlabel('Chamber Pressure (kPa)', fontsize=12)
plt.ylabel('Flame Speed (cm/s)', fontsize=12)
plt.title('Flame Speed vs Chamber Pressure', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('report/images/final_model_plot.png', dpi=300)
plt.close()
