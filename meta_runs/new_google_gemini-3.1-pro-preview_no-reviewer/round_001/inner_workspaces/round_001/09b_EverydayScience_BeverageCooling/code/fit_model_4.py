import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

df = pd.read_csv('data/beverage_temperature_series.csv')

seg1 = df.iloc[0:80]
seg2 = df.iloc[80:121]
seg3 = df.iloc[121:]

def combined_model_diff_Tenv(t_all, k, T_env1, T_env2, T_env3, T0_1, T0_2, T0_3):
    t1 = seg1['time_min'].values - seg1['time_min'].iloc[0]
    t2 = seg2['time_min'].values - seg2['time_min'].iloc[0]
    t3 = seg3['time_min'].values - seg3['time_min'].iloc[0]
    
    y1 = T_env1 + (T0_1 - T_env1) * np.exp(-k * t1)
    y2 = T_env2 + (T0_2 - T_env2) * np.exp(-k * t2)
    y3 = T_env3 + (T0_3 - T_env3) * np.exp(-k * t3)
    
    return np.concatenate([y1, y2, y3])

popt, pcov = curve_fit(combined_model_diff_Tenv, df['time_min'], df['temperature_c'], p0=[0.01, 25, 25, 25, 85, 54, 40])
print(f"Combined Fit (diff T_env): k={popt[0]:.4f}")
print(f"T_env1={popt[1]:.2f}, T_env2={popt[2]:.2f}, T_env3={popt[3]:.2f}")
print(f"T0_1={popt[4]:.2f}, T0_2={popt[5]:.2f}, T0_3={popt[6]:.2f}")
