import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

# Define Fractional/Stretched Exponential Cooling model (Kohlrausch function)
def stretched_cooling_model(t, T_env, T_0, k, beta):
    return T_env + (T_0 - T_env) * np.exp(-(k * t)**beta)

# Initial guesses for parameters
p0 = [22.0, 85.0, 0.01, 1.0]

# Bounds
bounds = ([15.0, 60.0, 0.0, 0.1], [30.0, 100.0, 1.0, 2.0])

# Fit the model
popt, pcov = curve_fit(stretched_cooling_model, time, temp, p0=p0, bounds=bounds, maxfev=10000)

T_env_fit, T_0_fit, k_fit, beta_fit = popt

# Calculate R-squared
residuals = temp - stretched_cooling_model(time, *popt)
ss_res = np.sum(residuals**2)
ss_tot = np.sum((temp - np.mean(temp))**2)
r_squared = 1 - (ss_res / ss_tot)

# Save results
results = {
    'T_env': T_env_fit,
    'T_0': T_0_fit,
    'k': k_fit,
    'beta': beta_fit,
    'R_squared': r_squared,
    'RMSE': np.sqrt(ss_res/len(time))
}
with open('outputs/fit_results_stretched.json', 'w') as f:
    json.dump(results, f, indent=4)

# Plotting
plt.figure(figsize=(10, 6))
plt.scatter(time, temp, label='Data', s=10, color='blue', alpha=0.5)
plt.plot(time, stretched_cooling_model(time, *popt), label=f'Fit: beta={beta_fit:.3f}, T_env={T_env_fit:.2f}', color='red', linewidth=2)
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title("Stretched Exponential Cooling Fit")
plt.legend()
plt.grid(True)
plt.savefig('report/images/cooling_fit_stretched.png')
plt.close()

# Plot residuals
plt.figure(figsize=(10, 6))
plt.scatter(time, residuals, s=10, color='purple', alpha=0.5)
plt.axhline(0, color='black', linestyle='--')
plt.xlabel('Time (minutes)')
plt.ylabel('Residuals (°C)')
plt.title('Stretched Fit Residuals')
plt.grid(True)
plt.savefig('report/images/residuals_stretched.png')
plt.close()

print("Analysis complete. Results saved to outputs/fit_results_stretched.json")
print(f"R2: {r_squared:.6f}, RMSE: {np.sqrt(ss_res/len(time)):.6f}")
print(f"Fitted beta: {beta_fit:.4f}")
print(f"Fitted T_env: {T_env_fit:.4f}")
