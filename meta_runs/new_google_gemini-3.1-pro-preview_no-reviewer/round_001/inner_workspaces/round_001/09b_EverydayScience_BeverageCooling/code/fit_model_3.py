import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

df = pd.read_csv('data/beverage_temperature_series.csv')

seg1 = df.iloc[0:80]
seg2 = df.iloc[80:121]
seg3 = df.iloc[121:]

def newton_cooling(t, T_env, T0, k):
    return T_env + (T0 - T_env) * np.exp(-k * t)

# Fit each segment with a fixed T_env to see the k values
T_envs = np.linspace(20, 30, 101)
k1s, k2s, k3s = [], [], []
errors = []

for T_env in T_envs:
    try:
        popt1, _ = curve_fit(lambda t, T0, k: newton_cooling(t, T_env, T0, k), seg1['time_min'] - seg1['time_min'].iloc[0], seg1['temperature_c'], p0=[85, 0.01])
        popt2, _ = curve_fit(lambda t, T0, k: newton_cooling(t, T_env, T0, k), seg2['time_min'] - seg2['time_min'].iloc[0], seg2['temperature_c'], p0=[54, 0.01])
        popt3, _ = curve_fit(lambda t, T0, k: newton_cooling(t, T_env, T0, k), seg3['time_min'] - seg3['time_min'].iloc[0], seg3['temperature_c'], p0=[40, 0.01])
        
        k1s.append(popt1[1])
        k2s.append(popt2[1])
        k3s.append(popt3[1])
        
        err1 = np.sum((seg1['temperature_c'] - newton_cooling(seg1['time_min'] - seg1['time_min'].iloc[0], T_env, *popt1))**2)
        err2 = np.sum((seg2['temperature_c'] - newton_cooling(seg2['time_min'] - seg2['time_min'].iloc[0], T_env, *popt2))**2)
        err3 = np.sum((seg3['temperature_c'] - newton_cooling(seg3['time_min'] - seg3['time_min'].iloc[0], T_env, *popt3))**2)
        errors.append(err1 + err2 + err3)
    except:
        k1s.append(np.nan)
        k2s.append(np.nan)
        k3s.append(np.nan)
        errors.append(np.inf)

best_idx = np.argmin(errors)
best_T_env = T_envs[best_idx]
print(f"Best T_env: {best_T_env:.2f}")
print(f"k1: {k1s[best_idx]:.6f}")
print(f"k2: {k2s[best_idx]:.6f}")
print(f"k3: {k3s[best_idx]:.6f}")

plt.figure()
plt.plot(T_envs, k1s, label='k1')
plt.plot(T_envs, k2s, label='k2')
plt.plot(T_envs, k3s, label='k3')
plt.xlabel('T_env')
plt.ylabel('k')
plt.legend()
plt.savefig('outputs/k_vs_T_env.png')
plt.close()
