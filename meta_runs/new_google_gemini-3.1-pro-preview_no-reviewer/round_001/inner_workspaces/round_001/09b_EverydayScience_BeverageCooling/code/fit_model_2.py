import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

df = pd.read_csv('data/beverage_temperature_series.csv')

seg1 = df.iloc[0:80]
seg2 = df.iloc[80:121]
seg3 = df.iloc[121:]

def combined_model_diff_k(t_all, T_env, k1, k2, k3, T0_1, T0_2, T0_3):
    t1 = seg1['time_min'].values - seg1['time_min'].iloc[0]
    t2 = seg2['time_min'].values - seg2['time_min'].iloc[0]
    t3 = seg3['time_min'].values - seg3['time_min'].iloc[0]
    
    y1 = T_env + (T0_1 - T_env) * np.exp(-k1 * t1)
    y2 = T_env + (T0_2 - T_env) * np.exp(-k2 * t2)
    y3 = T_env + (T0_3 - T_env) * np.exp(-k3 * t3)
    
    return np.concatenate([y1, y2, y3])

popt, pcov = curve_fit(combined_model_diff_k, df['time_min'], df['temperature_c'], p0=[20, 0.01, 0.01, 0.01, 85, 54, 40])
print(f"Combined Fit (diff k): T_env={popt[0]:.2f}")
print(f"k1={popt[1]:.4f}, k2={popt[2]:.4f}, k3={popt[3]:.4f}")
print(f"T0_1={popt[4]:.2f}, T0_2={popt[5]:.2f}, T0_3={popt[6]:.2f}")

plt.figure(figsize=(10, 6))
plt.plot(df['time_min'], df['temperature_c'], marker='.', linestyle='none', label='Data')
plt.plot(df['time_min'], combined_model_diff_k(df['time_min'], *popt), linestyle='-', label='Combined Fit (diff k)')
plt.xlabel('Time (min)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Temperature over Time with Newton\'s Law of Cooling Fit')
plt.legend()
plt.grid(True)
plt.savefig('report/images/combined_fit_diff_k.png')
plt.close()
