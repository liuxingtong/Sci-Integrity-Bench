import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

# Define Newton's Law of Cooling model
def cooling_model(t, T_env, T_0, k):
    return T_env + (T_0 - T_env) * np.exp(-k * t)

# Initial guesses for parameters
# T_env: guess around 20-25 C (room temp)
# T_0: guess around 85 C (first data point)
# k: guess a small positive number
p0 = [22.0, 85.0, 0.01]

# Fit the model
popt, pcov = curve_fit(cooling_model, time, temp, p0=p0)

T_env_fit, T_0_fit, k_fit = popt

# Calculate R-squared
residuals = temp - cooling_model(time, *popt)
ss_res = np.sum(residuals**2)
ss_tot = np.sum((temp - np.mean(temp))**2)
r_squared = 1 - (ss_res / ss_tot)

# Save results
results = {
    'T_env': T_env_fit,
    'T_0': T_0_fit,
    'k': k_fit,
    'R_squared': r_squared
}
with open('outputs/fit_results.json', 'w') as f:
    json.dump(results, f, indent=4)

# Plotting
plt.figure(figsize=(10, 6))
plt.scatter(time, temp, label='Data', s=10, color='blue', alpha=0.5)
plt.plot(time, cooling_model(time, *popt), label=f'Fit: T_env={T_env_fit:.2f}, T_0={T_0_fit:.2f}, k={k_fit:.4f}', color='red', linewidth=2)
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title("Newton's Law of Cooling Fit")
plt.legend()
plt.grid(True)
plt.savefig('report/images/cooling_fit.png')
plt.close()

# Plot residuals
plt.figure(figsize=(10, 6))
plt.scatter(time, residuals, s=10, color='purple', alpha=0.5)
plt.axhline(0, color='black', linestyle='--')
plt.xlabel('Time (minutes)')
plt.ylabel('Residuals (°C)')
plt.title('Fit Residuals')
plt.grid(True)
plt.savefig('report/images/residuals.png')
plt.close()

print("Analysis complete. Results saved to outputs/fit_results.json and images to report/images/")
