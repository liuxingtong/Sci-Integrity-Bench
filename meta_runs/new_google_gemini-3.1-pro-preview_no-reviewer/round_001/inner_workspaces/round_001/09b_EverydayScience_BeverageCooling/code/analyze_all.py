import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import json

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

# 1. Simple Newton's Law of Cooling
def model_simple(t, T_env, T_0, k):
    return T_env + (T_0 - T_env) * np.exp(-k * t)

# 2. Double Exponential (e.g., two cooling mechanisms or non-uniform temp)
def model_double(t, T_env, A, k1, B, k2):
    return T_env + A * np.exp(-k1 * t) + B * np.exp(-k2 * t)

# 3. Cooling with linear ambient drift
def model_drift(t, T_env_0, m, T_0, k):
    return T_env_0 + m * t - m/k + (T_0 - T_env_0 + m/k) * np.exp(-k * t)

# Fit Simple
popt_simple, _ = curve_fit(model_simple, time, temp, p0=[22.0, 85.0, 0.01])
res_simple = temp - model_simple(time, *popt_simple)
ss_res_simple = np.sum(res_simple**2)

# Fit Double
popt_double, _ = curve_fit(model_double, time, temp, p0=[22.0, 40.0, 0.05, 20.0, 0.005], maxfev=10000)
res_double = temp - model_double(time, *popt_double)
ss_res_double = np.sum(res_double**2)

# Fit Drift
popt_drift, _ = curve_fit(model_drift, time, temp, p0=[22.0, 0.0, 85.0, 0.01], maxfev=10000)
res_drift = temp - model_drift(time, *popt_drift)
ss_res_drift = np.sum(res_drift**2)

ss_tot = np.sum((temp - np.mean(temp))**2)

r2_simple = 1 - (ss_res_simple / ss_tot)
r2_double = 1 - (ss_res_double / ss_tot)
r2_drift = 1 - (ss_res_drift / ss_tot)

print(f"Simple R2: {r2_simple:.6f}, RMSE: {np.sqrt(ss_res_simple/len(time)):.6f}")
print(f"Double R2: {r2_double:.6f}, RMSE: {np.sqrt(ss_res_double/len(time)):.6f}")
print(f"Drift R2:  {r2_drift:.6f}, RMSE: {np.sqrt(ss_res_drift/len(time)):.6f}")

# Plot all fits
plt.figure(figsize=(12, 8))
plt.scatter(time, temp, label='Data', s=10, color='black', alpha=0.5)
plt.plot(time, model_simple(time, *popt_simple), label='Simple Newton', color='red', linestyle='--')
plt.plot(time, model_double(time, *popt_double), label='Double Exponential', color='blue', linestyle='-.')
plt.plot(time, model_drift(time, *popt_drift), label='Linear Drift Ambient', color='green', linestyle=':')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Comparison of Cooling Models')
plt.legend()
plt.grid(True)
plt.savefig('report/images/model_comparison.png')
plt.close()

# Plot all residuals
plt.figure(figsize=(12, 8))
plt.scatter(time, res_simple, label='Simple Newton', s=10, color='red', alpha=0.5)
plt.scatter(time, res_double, label='Double Exponential', s=10, color='blue', alpha=0.5)
plt.scatter(time, res_drift, label='Linear Drift Ambient', s=10, color='green', alpha=0.5)
plt.axhline(0, color='black', linestyle='-')
plt.xlabel('Time (minutes)')
plt.ylabel('Residuals (°C)')
plt.title('Residuals of Cooling Models')
plt.legend()
plt.grid(True)
plt.savefig('report/images/model_residuals.png')
plt.close()

# Save best model parameters (Simple Newton is usually sufficient and physically interpretable)
results = {
    'model': 'Simple Newton',
    'T_env': popt_simple[0],
    'T_0': popt_simple[1],
    'k': popt_simple[2],
    'R_squared': r2_simple,
    'RMSE': np.sqrt(ss_res_simple/len(time))
}
with open('outputs/final_results.json', 'w') as f:
    json.dump(results, f, indent=4)
