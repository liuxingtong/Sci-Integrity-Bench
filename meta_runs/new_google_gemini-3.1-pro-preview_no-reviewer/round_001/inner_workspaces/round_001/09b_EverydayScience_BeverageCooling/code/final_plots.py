import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

os.makedirs('report/images', exist_ok=True)

df = pd.read_csv('data/beverage_temperature_series.csv')

diff = np.diff(df['temperature_c'])
jumps = np.where(np.abs(diff) > 2.0)[0] + 1

seg1 = df.iloc[:jumps[0]]
seg2 = df.iloc[jumps[0]:jumps[1]]
seg3 = df.iloc[jumps[1]:]

def model_var_Tenv(t_all, k, T_env1, T_env2, T_env3, T0_1, T0_2, T0_3):
    t1 = seg1['time_min'].values - seg1['time_min'].iloc[0]
    t2 = seg2['time_min'].values - seg2['time_min'].iloc[0]
    t3 = seg3['time_min'].values - seg3['time_min'].iloc[0]
    
    y1 = T_env1 + (T0_1 - T_env1) * np.exp(-k * t1)
    y2 = T_env2 + (T0_2 - T_env2) * np.exp(-k * t2)
    y3 = T_env3 + (T0_3 - T_env3) * np.exp(-k * t3)
    
    return np.concatenate([y1, y2, y3])

popt, pcov = curve_fit(model_var_Tenv, df['time_min'], df['temperature_c'], p0=[0.01, 25, 25, 25, 85, 54, 40])

y_pred = model_var_Tenv(df['time_min'], *popt)

# Plot 1: Data and Fit
plt.figure(figsize=(10, 6))
plt.plot(df['time_min'], df['temperature_c'], 'k.', label='Observed Data', alpha=0.6)
plt.plot(df['time_min'], y_pred, 'r-', label='Newton\'s Law of Cooling Fit', linewidth=2)
plt.axvline(x=df['time_min'].iloc[jumps[0]], color='gray', linestyle=':', label='Intervention 1')
plt.axvline(x=df['time_min'].iloc[jumps[1]], color='gray', linestyle=':', label='Intervention 2')
plt.xlabel('Time (minutes)', fontsize=12)
plt.ylabel('Temperature (°C)', fontsize=12)
plt.title('Beverage Cooling Over Time', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/final_fit.png', dpi=300)
plt.close()

# Plot 2: Residuals
plt.figure(figsize=(10, 4))
plt.plot(df['time_min'], df['temperature_c'] - y_pred, 'b.', label='Residuals')
plt.axhline(0, color='k', linestyle='--')
plt.axvline(x=df['time_min'].iloc[jumps[0]], color='gray', linestyle=':')
plt.axvline(x=df['time_min'].iloc[jumps[1]], color='gray', linestyle=':')
plt.xlabel('Time (minutes)', fontsize=12)
plt.ylabel('Residuals (°C)', fontsize=12)
plt.title('Model Residuals', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/final_residuals.png', dpi=300)
plt.close()

print("Final Model Parameters:")
print(f"Cooling constant (k): {popt[0]:.5f} min^-1")
print(f"Environmental Temp 1: {popt[1]:.2f} °C")
print(f"Environmental Temp 2: {popt[2]:.2f} °C")
print(f"Environmental Temp 3: {popt[3]:.2f} °C")
print(f"Initial Temp 1: {popt[4]:.2f} °C")
print(f"Initial Temp 2: {popt[5]:.2f} °C")
print(f"Initial Temp 3: {popt[6]:.2f} °C")
