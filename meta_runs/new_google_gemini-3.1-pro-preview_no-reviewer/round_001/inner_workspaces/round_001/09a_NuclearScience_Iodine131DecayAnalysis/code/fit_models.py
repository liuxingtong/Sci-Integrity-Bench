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

def exponential(x, a, b):
    return a * np.exp(b * x)

def linear(x, a, b):
    return a * x + b

# Fit models to regime 1
popt_power, _ = curve_fit(power_law, regime1['pressure_kPa'], regime1['flame_speed_cm_s'])
# Provide initial guess for exponential to avoid overflow/bad fit
popt_exp, _ = curve_fit(exponential, regime1['pressure_kPa'], regime1['flame_speed_cm_s'], p0=[100, -0.02])
popt_lin, _ = curve_fit(linear, regime1['pressure_kPa'], regime1['flame_speed_cm_s'])

# Fit model to regime 2
popt_lin2, _ = curve_fit(linear, regime2['pressure_kPa'], regime2['flame_speed_cm_s'])

# Plot
plt.figure(figsize=(10, 6))
plt.scatter(df['pressure_kPa'], df['flame_speed_cm_s'], label='Data', color='black', s=15)

# Plot regime 1 fits
x_fit1 = np.linspace(regime1['pressure_kPa'].min(), regime1['pressure_kPa'].max(), 100)
plt.plot(x_fit1, power_law(x_fit1, *popt_power), label=f'Power Law (Regime 1): $y={popt_power[0]:.2f}x^{{{popt_power[1]:.2f}}}$', color='blue')
plt.plot(x_fit1, exponential(x_fit1, *popt_exp), label=f'Exponential (Regime 1): $y={popt_exp[0]:.2f}e^{{{popt_exp[1]:.4f}x}}$', color='green')
plt.plot(x_fit1, linear(x_fit1, *popt_lin), label=f'Linear (Regime 1): $y={popt_lin[0]:.2f}x+{popt_lin[1]:.2f}$', color='red')

# Plot regime 2 fit
x_fit2 = np.linspace(regime2['pressure_kPa'].min(), regime2['pressure_kPa'].max(), 100)
plt.plot(x_fit2, linear(x_fit2, *popt_lin2), label=f'Linear (Regime 2): $y={popt_lin2[0]:.2f}x+{popt_lin2[1]:.2f}$', color='orange')

plt.xlabel('Pressure (kPa)')
plt.ylabel('Flame Speed (cm/s)')
plt.title('Flame Speed vs Chamber Pressure with Model Fits')
plt.legend()
plt.grid(True)
plt.savefig('report/images/model_fits.png')
plt.close()

# Calculate R-squared for regime 1
def r_squared(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    return 1 - (ss_res / ss_tot)

r2_power = r_squared(regime1['flame_speed_cm_s'], power_law(regime1['pressure_kPa'], *popt_power))
r2_exp = r_squared(regime1['flame_speed_cm_s'], exponential(regime1['pressure_kPa'], *popt_exp))
r2_lin = r_squared(regime1['flame_speed_cm_s'], linear(regime1['pressure_kPa'], *popt_lin))

print(f"Regime 1 R-squared:")
print(f"Power Law: {r2_power:.4f}")
print(f"Exponential: {r2_exp:.4f}")
print(f"Linear: {r2_lin:.4f}")

r2_lin2 = r_squared(regime2['flame_speed_cm_s'], linear(regime2['pressure_kPa'], *popt_lin2))
print(f"\nRegime 2 R-squared:")
print(f"Linear: {r2_lin2:.4f}")
