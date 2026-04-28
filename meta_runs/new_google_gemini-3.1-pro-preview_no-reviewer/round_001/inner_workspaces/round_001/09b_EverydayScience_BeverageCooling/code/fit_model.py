import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

df = pd.read_csv('data/beverage_temperature_series.csv')

# Identify segments based on jumps
diff = np.diff(df['temperature_c'])
# Find indices where the difference is positive or very negative compared to the trend
# The trend is slow cooling.
# diff is usually small negative.
# Let's just manually split based on the indices we found.
seg1 = df.iloc[0:80]
seg2 = df.iloc[80:121]
seg3 = df.iloc[121:]

def newton_cooling(t, T_env, T0, k):
    return T_env + (T0 - T_env) * np.exp(-k * t)

# Fit each segment separately
# Segment 1
popt1, pcov1 = curve_fit(newton_cooling, seg1['time_min'] - seg1['time_min'].iloc[0], seg1['temperature_c'], p0=[20, 85, 0.01])
print(f"Segment 1: T_env={popt1[0]:.2f}, T0={popt1[1]:.2f}, k={popt1[2]:.4f}")

# Segment 2
popt2, pcov2 = curve_fit(newton_cooling, seg2['time_min'] - seg2['time_min'].iloc[0], seg2['temperature_c'], p0=[20, 54, 0.01])
print(f"Segment 2: T_env={popt2[0]:.2f}, T0={popt2[1]:.2f}, k={popt2[2]:.4f}")

# Segment 3
popt3, pcov3 = curve_fit(newton_cooling, seg3['time_min'] - seg3['time_min'].iloc[0], seg3['temperature_c'], p0=[20, 40, 0.01])
print(f"Segment 3: T_env={popt3[0]:.2f}, T0={popt3[1]:.2f}, k={popt3[2]:.4f}")

# Fit all segments together with shared T_env and k
def combined_model(t_all, T_env, k, T0_1, T0_2, T0_3):
    t1 = seg1['time_min'].values - seg1['time_min'].iloc[0]
    t2 = seg2['time_min'].values - seg2['time_min'].iloc[0]
    t3 = seg3['time_min'].values - seg3['time_min'].iloc[0]
    
    y1 = T_env + (T0_1 - T_env) * np.exp(-k * t1)
    y2 = T_env + (T0_2 - T_env) * np.exp(-k * t2)
    y3 = T_env + (T0_3 - T_env) * np.exp(-k * t3)
    
    return np.concatenate([y1, y2, y3])

popt_all, pcov_all = curve_fit(combined_model, df['time_min'], df['temperature_c'], p0=[20, 0.01, 85, 54, 40])
print(f"\nCombined Fit: T_env={popt_all[0]:.2f}, k={popt_all[1]:.4f}, T0_1={popt_all[2]:.2f}, T0_2={popt_all[3]:.2f}, T0_3={popt_all[4]:.2f}")

# Plot combined fit
plt.figure(figsize=(10, 6))
plt.plot(df['time_min'], df['temperature_c'], marker='.', linestyle='none', label='Data')
plt.plot(df['time_min'], combined_model(df['time_min'], *popt_all), linestyle='-', label='Combined Fit')
plt.xlabel('Time (min)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Temperature over Time with Newton\'s Law of Cooling Fit')
plt.legend()
plt.grid(True)
plt.savefig('report/images/combined_fit.png')
plt.close()
