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

print(f"Detected jumps at indices: {jumps}")

seg1 = df.iloc[:jumps[0]]
seg2 = df.iloc[jumps[0]:jumps[1]]
seg3 = df.iloc[jumps[1]:]

def newton_cooling(t, T_env, T0, k):
    return T_env + (T0 - T_env) * np.exp(-k * t)

# Model 1: Constant T_env, different k and T0 for each segment
def model_const_Tenv(t_all, T_env, k1, k2, k3, T0_1, T0_2, T0_3):
    t1 = seg1['time_min'].values - seg1['time_min'].iloc[0]
    t2 = seg2['time_min'].values - seg2['time_min'].iloc[0]
    t3 = seg3['time_min'].values - seg3['time_min'].iloc[0]
    
    y1 = T_env + (T0_1 - T_env) * np.exp(-k1 * t1)
    y2 = T_env + (T0_2 - T_env) * np.exp(-k2 * t2)
    y3 = T_env + (T0_3 - T_env) * np.exp(-k3 * t3)
    
    return np.concatenate([y1, y2, y3])

popt1, pcov1 = curve_fit(model_const_Tenv, df['time_min'], df['temperature_c'], 
                         p0=[25, 0.01, 0.01, 0.01, 85, 54, 40])

print("\nModel 1 (Constant T_env, Variable k):")
print(f"T_env = {popt1[0]:.2f} °C")
print(f"k1 = {popt1[1]:.5f}, k2 = {popt1[2]:.5f}, k3 = {popt1[3]:.5f}")
print(f"T0_1 = {popt1[4]:.2f}, T0_2 = {popt1[5]:.2f}, T0_3 = {popt1[6]:.2f}")

# Model 2: Constant T_env, Constant k, different T0
def model_const_Tenv_k(t_all, T_env, k, T0_1, T0_2, T0_3):
    t1 = seg1['time_min'].values - seg1['time_min'].iloc[0]
    t2 = seg2['time_min'].values - seg2['time_min'].iloc[0]
    t3 = seg3['time_min'].values - seg3['time_min'].iloc[0]
    
    y1 = T_env + (T0_1 - T_env) * np.exp(-k * t1)
    y2 = T_env + (T0_2 - T_env) * np.exp(-k * t2)
    y3 = T_env + (T0_3 - T_env) * np.exp(-k * t3)
    
    return np.concatenate([y1, y2, y3])

popt2, pcov2 = curve_fit(model_const_Tenv_k, df['time_min'], df['temperature_c'], 
                         p0=[25, 0.01, 85, 54, 40])

print("\nModel 2 (Constant T_env, Constant k):")
print(f"T_env = {popt2[0]:.2f} °C")
print(f"k = {popt2[1]:.5f}")
print(f"T0_1 = {popt2[2]:.2f}, T0_2 = {popt2[3]:.2f}, T0_3 = {popt2[4]:.2f}")

# Calculate R-squared for both models
y_true = df['temperature_c'].values
y_pred1 = model_const_Tenv(df['time_min'], *popt1)
y_pred2 = model_const_Tenv_k(df['time_min'], *popt2)

ss_res1 = np.sum((y_true - y_pred1)**2)
ss_res2 = np.sum((y_true - y_pred2)**2)
ss_tot = np.sum((y_true - np.mean(y_true))**2)

r2_1 = 1 - (ss_res1 / ss_tot)
r2_2 = 1 - (ss_res2 / ss_tot)

print(f"\nR^2 for Model 1: {r2_1:.6f}")
print(f"R^2 for Model 2: {r2_2:.6f}")

# Plotting
plt.figure(figsize=(12, 7))
plt.plot(df['time_min'], df['temperature_c'], 'k.', label='Observed Data', alpha=0.6)
plt.plot(df['time_min'], y_pred1, 'r-', label=f'Model 1 (Var k): R²={r2_1:.4f}', linewidth=2)
plt.plot(df['time_min'], y_pred2, 'b--', label=f'Model 2 (Const k): R²={r2_2:.4f}', linewidth=2)

plt.axvline(x=df['time_min'].iloc[jumps[0]], color='gray', linestyle=':', label='Intervention 1')
plt.axvline(x=df['time_min'].iloc[jumps[1]], color='gray', linestyle=':', label='Intervention 2')

plt.xlabel('Time (minutes)', fontsize=12)
plt.ylabel('Temperature (°C)', fontsize=12)
plt.title('Beverage Cooling: Newton\'s Law of Cooling Fits', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/model_comparison.png', dpi=300)
plt.close()

# Plot residuals for Model 1
plt.figure(figsize=(12, 5))
plt.plot(df['time_min'], y_true - y_pred1, 'r.', label='Residuals (Model 1)')
plt.axhline(y=0, color='k', linestyle='-')
plt.axvline(x=df['time_min'].iloc[jumps[0]], color='gray', linestyle=':')
plt.axvline(x=df['time_min'].iloc[jumps[1]], color='gray', linestyle=':')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature Residual (°C)')
plt.title('Residuals of Model 1 (Constant T_env, Variable k)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('report/images/residuals_model1.png', dpi=300)
plt.close()
