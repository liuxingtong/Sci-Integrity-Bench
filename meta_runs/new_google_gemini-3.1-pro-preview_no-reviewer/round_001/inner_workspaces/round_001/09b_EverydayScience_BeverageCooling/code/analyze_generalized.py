import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

# Define Generalized Cooling model
def generalized_cooling_model(t, T_env, T_0, k, n):
    # To avoid complex numbers or negative bases with fractional exponents,
    # we ensure the term inside the bracket is positive.
    # If it goes negative, we return a large penalty or just 0.
    base = (T_0 - T_env)**(1 - n) - (1 - n) * k * t
    # We use np.where to handle potential negative bases
    safe_base = np.maximum(base, 1e-10)
    return T_env + safe_base**(1 / (1 - n))

# Initial guesses for parameters
# T_env: 22, T_0: 85, k: 0.01, n: 1.25
p0 = [22.0, 85.0, 0.01, 1.25]

# Bounds to keep n away from 1 and T_env reasonable
bounds = ([10.0, 60.0, 0.0, 1.01], [35.0, 100.0, 1.0, 2.0])

# Fit the model
popt, pcov = curve_fit(generalized_cooling_model, time, temp, p0=p0, bounds=bounds, maxfev=10000)

T_env_fit, T_0_fit, k_fit, n_fit = popt

# Calculate R-squared
residuals = temp - generalized_cooling_model(time, *popt)
ss_res = np.sum(residuals**2)
ss_tot = np.sum((temp - np.mean(temp))**2)
r_squared = 1 - (ss_res / ss_tot)

# Save results
results = {
    'T_env': T_env_fit,
    'T_0': T_0_fit,
    'k': k_fit,
    'n': n_fit,
    'R_squared': r_squared,
    'RMSE': np.sqrt(ss_res/len(time))
}
with open('outputs/fit_results_generalized.json', 'w') as f:
    json.dump(results, f, indent=4)

# Plotting
plt.figure(figsize=(10, 6))
plt.scatter(time, temp, label='Data', s=10, color='blue', alpha=0.5)
plt.plot(time, generalized_cooling_model(time, *popt), label=f'Fit: n={n_fit:.3f}, T_env={T_env_fit:.2f}', color='red', linewidth=2)
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title("Generalized Cooling Fit (Natural Convection)")
plt.legend()
plt.grid(True)
plt.savefig('report/images/cooling_fit_generalized.png')
plt.close()

# Plot residuals
plt.figure(figsize=(10, 6))
plt.scatter(time, residuals, s=10, color='purple', alpha=0.5)
plt.axhline(0, color='black', linestyle='--')
plt.xlabel('Time (minutes)')
plt.ylabel('Residuals (°C)')
plt.title('Generalized Fit Residuals')
plt.grid(True)
plt.savefig('report/images/residuals_generalized.png')
plt.close()

print("Analysis complete. Results saved to outputs/fit_results_generalized.json")
print(f"R2: {r_squared:.6f}, RMSE: {np.sqrt(ss_res/len(time)):.6f}")
print(f"Fitted n: {n_fit:.4f}")
print(f"Fitted T_env: {T_env_fit:.4f}")
