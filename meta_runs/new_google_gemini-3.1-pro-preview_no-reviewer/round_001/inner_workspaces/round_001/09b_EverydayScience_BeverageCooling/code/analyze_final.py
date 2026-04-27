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

# 3. Stretched Exponential (Kohlrausch)
def model_stretched(t, T_env, T_0, k, beta):
    return T_env + (T_0 - T_env) * np.exp(-(k * t)**beta)

# Fit Simple
popt_simple, _ = curve_fit(model_simple, time, temp, p0=[22.0, 85.0, 0.01])
res_simple = temp - model_simple(time, *popt_simple)
ss_res_simple = np.sum(res_simple**2)

# Fit Double
popt_double, _ = curve_fit(model_double, time, temp, p0=[22.0, 40.0, 0.05, 20.0, 0.005], maxfev=10000)
res_double = temp - model_double(time, *popt_double)
ss_res_double = np.sum(res_double**2)

# Fit Stretched
popt_stretched, _ = curve_fit(model_stretched, time, temp, p0=[22.0, 85.0, 0.01, 1.0], bounds=([15.0, 60.0, 0.0, 0.1], [30.0, 100.0, 1.0, 2.0]), maxfev=10000)
res_stretched = temp - model_stretched(time, *popt_stretched)
ss_res_stretched = np.sum(res_stretched**2)

ss_tot = np.sum((temp - np.mean(temp))**2)

r2_simple = 1 - (ss_res_simple / ss_tot)
r2_double = 1 - (ss_res_double / ss_tot)
r2_stretched = 1 - (ss_res_stretched / ss_tot)

rmse_simple = np.sqrt(ss_res_simple/len(time))
rmse_double = np.sqrt(ss_res_double/len(time))
rmse_stretched = np.sqrt(ss_res_stretched/len(time))

# Plot all fits
plt.figure(figsize=(10, 6))
plt.scatter(time, temp, label='Observed Data', s=15, color='black', alpha=0.6)
plt.plot(time, model_simple(time, *popt_simple), label=f'Newton\'s Law (R²={r2_simple:.3f})', color='red', linestyle='--')
plt.plot(time, model_double(time, *popt_double), label=f'Double Exponential (R²={r2_double:.3f})', color='blue', linestyle='-.')
plt.plot(time, model_stretched(time, *popt_stretched), label=f'Stretched Exponential (R²={r2_stretched:.3f})', color='green', linestyle=':')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Comparison of Beverage Cooling Models')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/model_comparison.png', dpi=300)
plt.close()

# Plot all residuals
plt.figure(figsize=(10, 6))
plt.scatter(time, res_simple, label='Newton\'s Law', s=15, color='red', alpha=0.6)
plt.scatter(time, res_double, label='Double Exponential', s=15, color='blue', alpha=0.6)
plt.scatter(time, res_stretched, label='Stretched Exponential', s=15, color='green', alpha=0.6)
plt.axhline(0, color='black', linestyle='-', linewidth=1)
plt.xlabel('Time (minutes)')
plt.ylabel('Residuals (°C)')
plt.title('Residuals of Cooling Models')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/model_residuals.png', dpi=300)
plt.close()

# Save final results
results = {
    'Newton': {
        'T_env': popt_simple[0],
        'T_0': popt_simple[1],
        'k': popt_simple[2],
        'R2': r2_simple,
        'RMSE': rmse_simple
    },
    'Double_Exponential': {
        'T_env': popt_double[0],
        'A': popt_double[1],
        'k1': popt_double[2],
        'B': popt_double[3],
        'k2': popt_double[4],
        'R2': r2_double,
        'RMSE': rmse_double
    },
    'Stretched_Exponential': {
        'T_env': popt_stretched[0],
        'T_0': popt_stretched[1],
        'k': popt_stretched[2],
        'beta': popt_stretched[3],
        'R2': r2_stretched,
        'RMSE': rmse_stretched
    }
}
with open('outputs/final_model_metrics.json', 'w') as f:
    json.dump(results, f, indent=4)
