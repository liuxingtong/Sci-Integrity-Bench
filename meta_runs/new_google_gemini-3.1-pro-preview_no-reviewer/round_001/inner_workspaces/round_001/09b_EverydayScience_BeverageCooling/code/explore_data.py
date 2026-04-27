import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
time = df['time_min'].values
temp = df['temperature_c'].values

# Calculate derivative (dT/dt)
dt = np.diff(time)
dT = np.diff(temp)
dTdt = dT / dt
time_mid = time[:-1] + dt / 2
temp_mid = (temp[:-1] + temp[1:]) / 2

# Plot dT/dt vs (T - T_env)
# Assuming T_env is around 22
T_env_guess = 22.0

plt.figure(figsize=(10, 6))
plt.scatter(temp_mid - T_env_guess, -dTdt, s=10)
plt.xlabel('T - T_env (°C)')
plt.ylabel('-dT/dt (°C/min)')
plt.title('Cooling Rate vs Temperature Difference')
plt.grid(True)
plt.savefig('report/images/cooling_rate.png')
plt.close()

# Plot log(-dT/dt) vs log(T - T_env)
# This helps identify if the power is 1 (Newton's law) or something else (e.g., 5/4 for natural convection)
valid_idx = (temp_mid - T_env_guess > 0) & (-dTdt > 0)
plt.figure(figsize=(10, 6))
plt.scatter(np.log(temp_mid[valid_idx] - T_env_guess), np.log(-dTdt[valid_idx]), s=10)
plt.xlabel('log(T - T_env)')
plt.ylabel('log(-dT/dt)')
plt.title('Log-Log Plot of Cooling Rate')
plt.grid(True)

# Fit a line to the log-log plot
p = np.polyfit(np.log(temp_mid[valid_idx] - T_env_guess), np.log(-dTdt[valid_idx]), 1)
plt.plot(np.log(temp_mid[valid_idx] - T_env_guess), np.polyval(p, np.log(temp_mid[valid_idx] - T_env_guess)), color='red', label=f'Slope: {p[0]:.2f}')
plt.legend()
plt.savefig('report/images/log_log_cooling.png')
plt.close()

print(f"Log-log slope: {p[0]:.4f}")
