import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

# Define Cooling model with linear drift in ambient temperature
def drift_cooling_model(t, T_env_0, m, T_0, k):
    return T_env_0 + m * t - m/k + (T_0 - T_env_0 + m/k) * np.exp(-k * t)

# Initial guesses for parameters
p0 = [22.0, 0.0, 85.0, 0.01]

# Fit the model
popt, pcov = curve_fit(drift_cooling_model, time, temp, p0=p0, maxfev=10000)

T_env_0_fit, m_fit, T_0_fit, k_fit = popt

# Calculate R-squared
residuals = temp - drift_cooling_model(time, *popt)
ss_res = np.sum(residuals**2)
ss_tot = np.sum((temp - np.mean(temp))**2)
r_squared = 1 - (ss_res / ss_tot)

# Save results
results = {
    'T_env_0': T_env_0_fit,
    'm': m_fit,
    'T_0': T_0_fit,
    'k': k_fit,
    'R_squared': r_squared
}
with open('outputs/fit_results_drift.json', 'w') as f:
    json.dump(results, f, indent=4)

# Plotting
plt.figure(figsize=(10, 6))
plt.scatter(time, temp, label='Data', s=10, color='blue', alpha=0.5)
plt.plot(time, drift_cooling_model(time, *popt), label=f'Fit: T_env_0={T_env_0_fit:.2f}, m={m_fit:.4f}', color='red', linewidth=2)
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title("Cooling Fit with Ambient Drift")
plt.legend()
plt.grid(True)
plt.savefig('report/images/cooling_fit_drift.png')
plt.close()

# Plot residuals
plt.figure(figsize=(10, 6))
plt.scatter(time, residuals, s=10, color='purple', alpha=0.5)
plt.axhline(0, color='black', linestyle='--')
plt.xlabel('Time (minutes)')
plt.ylabel('Residuals (°C)')
plt.title('Drift Fit Residuals')
plt.grid(True)
plt.savefig('report/images/residuals_drift.png')
plt.close()

print("Analysis complete. Results saved to outputs/fit_results_drift.json")
print(f"Max residual: {np.max(residuals)}")
print(f"Min residual: {np.min(residuals)}")
print(f"Mean residual: {np.mean(residuals)}")
print(f"Std residual: {np.std(residuals)}")
