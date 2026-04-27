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
    base = (T_0 - T_env)**(1 - n) - (1 - n) * k * t
    safe_base = np.maximum(base, 1e-10)
    return T_env + safe_base**(1 / (1 - n))

# Initial guesses for parameters
p0 = [22.0, 85.0, 0.01, 1.25]

# Bounds to keep n away from 1 and T_env reasonable (e.g., room temp 18-26)
bounds = ([18.0, 60.0, 0.0, 1.01], [26.0, 100.0, 1.0, 2.0])

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
with open('outputs/fit_results_generalized_fixed.json', 'w') as f:
    json.dump(results, f, indent=4)

print("Analysis complete. Results saved to outputs/fit_results_generalized_fixed.json")
print(f"R2: {r_squared:.6f}, RMSE: {np.sqrt(ss_res/len(time)):.6f}")
print(f"Fitted n: {n_fit:.4f}")
print(f"Fitted T_env: {T_env_fit:.4f}")
