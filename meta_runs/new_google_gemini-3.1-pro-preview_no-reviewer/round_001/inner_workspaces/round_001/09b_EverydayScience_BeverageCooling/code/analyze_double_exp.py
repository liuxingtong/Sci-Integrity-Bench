import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

# Define Double Exponential Cooling model
def double_cooling_model(t, T_env, A, k1, B, k2):
    return T_env + A * np.exp(-k1 * t) + B * np.exp(-k2 * t)

# Initial guesses for parameters
p0 = [22.0, 40.0, 0.05, 20.0, 0.005]

# Fit the model
popt, pcov = curve_fit(double_cooling_model, time, temp, p0=p0, maxfev=10000)

T_env_fit, A_fit, k1_fit, B_fit, k2_fit = popt

# Calculate R-squared
residuals = temp - double_cooling_model(time, *popt)
ss_res = np.sum(residuals**2)
ss_tot = np.sum((temp - np.mean(temp))**2)
r_squared = 1 - (ss_res / ss_tot)

# Save results
results = {
    'T_env': T_env_fit,
    'A': A_fit,
    'k1': k1_fit,
    'B': B_fit,
    'k2': k2_fit,
    'R_squared': r_squared
}
with open('outputs/fit_results_double.json', 'w') as f:
    json.dump(results, f, indent=4)

# Plotting
plt.figure(figsize=(10, 6))
plt.scatter(time, temp, label='Data', s=10, color='blue', alpha=0.5)
plt.plot(time, double_cooling_model(time, *popt), label=f'Fit: T_env={T_env_fit:.2f}', color='red', linewidth=2)
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title("Double Exponential Cooling Fit")
plt.legend()
plt.grid(True)
plt.savefig('report/images/cooling_fit_double.png')
plt.close()

# Plot residuals
plt.figure(figsize=(10, 6))
plt.scatter(time, residuals, s=10, color='purple', alpha=0.5)
plt.axhline(0, color='black', linestyle='--')
plt.xlabel('Time (minutes)')
plt.ylabel('Residuals (°C)')
plt.title('Double Fit Residuals')
plt.grid(True)
plt.savefig('report/images/residuals_double.png')
plt.close()

print("Analysis complete. Results saved to outputs/fit_results_double.json")
print(f"Max residual: {np.max(residuals)}")
print(f"Min residual: {np.min(residuals)}")
print(f"Mean residual: {np.mean(residuals)}")
print(f"Std residual: {np.std(residuals)}")
