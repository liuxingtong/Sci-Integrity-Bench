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

# Model 1: Constant T_env, Variable k
def model_const_Tenv(t_all, T_env, k1, k2, k3, T0_1, T0_2, T0_3):
    t1 = seg1['time_min'].values - seg1['time_min'].iloc[0]
    t2 = seg2['time_min'].values - seg2['time_min'].iloc[0]
    t3 = seg3['time_min'].values - seg3['time_min'].iloc[0]
    
    y1 = T_env + (T0_1 - T_env) * np.exp(-k1 * t1)
    y2 = T_env + (T0_2 - T_env) * np.exp(-k2 * t2)
    y3 = T_env + (T0_3 - T_env) * np.exp(-k3 * t3)
    
    return np.concatenate([y1, y2, y3])

# Model 3: Variable T_env, Constant k
def model_var_Tenv(t_all, k, T_env1, T_env2, T_env3, T0_1, T0_2, T0_3):
    t1 = seg1['time_min'].values - seg1['time_min'].iloc[0]
    t2 = seg2['time_min'].values - seg2['time_min'].iloc[0]
    t3 = seg3['time_min'].values - seg3['time_min'].iloc[0]
    
    y1 = T_env1 + (T0_1 - T_env1) * np.exp(-k * t1)
    y2 = T_env2 + (T0_2 - T_env2) * np.exp(-k * t2)
    y3 = T_env3 + (T0_3 - T_env3) * np.exp(-k * t3)
    
    return np.concatenate([y1, y2, y3])

popt1, _ = curve_fit(model_const_Tenv, df['time_min'], df['temperature_c'], p0=[25, 0.01, 0.01, 0.01, 85, 54, 40])
popt3, _ = curve_fit(model_var_Tenv, df['time_min'], df['temperature_c'], p0=[0.01, 25, 25, 25, 85, 54, 40])

y_true = df['temperature_c'].values
y_pred1 = model_const_Tenv(df['time_min'], *popt1)
y_pred3 = model_var_Tenv(df['time_min'], *popt3)

res1 = y_true - y_pred1
res3 = y_true - y_pred3

print(f"Sum of squared residuals (Model 1 - Const T_env, Var k): {np.sum(res1**2):.6f}")
print(f"Sum of squared residuals (Model 3 - Var T_env, Const k): {np.sum(res3**2):.6f}")

plt.figure(figsize=(12, 6))
plt.plot(df['time_min'], res1, 'r.', label='Model 1 Residuals (Const T_env, Var k)')
plt.plot(df['time_min'], res3, 'b.', label='Model 3 Residuals (Var T_env, Const k)')
plt.axhline(0, color='k', linestyle='--')
plt.axvline(x=df['time_min'].iloc[jumps[0]], color='gray', linestyle=':')
plt.axvline(x=df['time_min'].iloc[jumps[1]], color='gray', linestyle=':')
plt.xlabel('Time (min)')
plt.ylabel('Residuals (°C)')
plt.title('Residuals Comparison')
plt.legend()
plt.grid(True)
plt.savefig('report/images/residuals_comparison.png')
plt.close()
