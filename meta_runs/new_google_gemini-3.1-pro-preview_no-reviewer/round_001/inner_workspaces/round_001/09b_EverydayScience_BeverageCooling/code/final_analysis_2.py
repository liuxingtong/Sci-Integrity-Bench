import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os

os.makedirs('report/images', exist_ok=True)

df = pd.read_csv('data/beverage_temperature_series.csv')

# Detect segments based on temperature jumps
diff = np.diff(df['temperature_c'])
jumps = np.where(np.abs(diff) > 2.0)[0] + 1

seg1 = df.iloc[:jumps[0]]
seg2 = df.iloc[jumps[0]:jumps[1]]
seg3 = df.iloc[jumps[1]:]

# Model 3: Variable T_env, Constant k
def model_var_Tenv_const_k(t_all, k, T_env1, T_env2, T_env3, T0_1, T0_2, T0_3):
    t1 = seg1['time_min'].values - seg1['time_min'].iloc[0]
    t2 = seg2['time_min'].values - seg2['time_min'].iloc[0]
    t3 = seg3['time_min'].values - seg3['time_min'].iloc[0]
    
    y1 = T_env1 + (T0_1 - T_env1) * np.exp(-k * t1)
    y2 = T_env2 + (T0_2 - T_env2) * np.exp(-k * t2)
    y3 = T_env3 + (T0_3 - T_env3) * np.exp(-k * t3)
    
    return np.concatenate([y1, y2, y3])

popt3, pcov3 = curve_fit(model_var_Tenv_const_k, df['time_min'], df['temperature_c'], 
                         p0=[0.01, 25, 25, 25, 85, 54, 40])

print("\nModel 3 (Variable T_env, Constant k):")
print(f"k = {popt3[0]:.5f}")
print(f"T_env1 = {popt3[1]:.2f} °C, T_env2 = {popt3[2]:.2f} °C, T_env3 = {popt3[3]:.2f} °C")
print(f"T0_1 = {popt3[4]:.2f}, T0_2 = {popt3[5]:.2f}, T0_3 = {popt3[6]:.2f}")

y_true = df['temperature_c'].values
y_pred3 = model_var_Tenv_const_k(df['time_min'], *popt3)
ss_res3 = np.sum((y_true - y_pred3)**2)
ss_tot = np.sum((y_true - np.mean(y_true))**2)
r2_3 = 1 - (ss_res3 / ss_tot)
print(f"R^2 for Model 3: {r2_3:.6f}")
