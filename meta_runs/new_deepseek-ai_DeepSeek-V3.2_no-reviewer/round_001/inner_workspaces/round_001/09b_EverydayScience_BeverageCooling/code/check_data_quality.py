import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('../data/beverage_temperature_series.csv')

print("=== Data Quality Check ===")
print(f"Total data points: {len(df)}")
print(f"Time range: {df['time_min'].min()} to {df['time_min'].max()} minutes")
print(f"Temperature range: {df['temperature_c'].min():.2f} to {df['temperature_c'].max():.2f}°C")

# Check if data follows Newton's Law exactly
# For Newton's Law: ln(T - T_env) = ln(T0 - T_env) - k*t
# So ln(T - T_env) vs t should be linear

# Try to estimate T_env from the data
# For segment 1 (0-79 min)
seg1 = df[df['time_min'] <= 79]

# Try different T_env values and check linearity
best_r2 = -np.inf
best_T_env = None
best_k = None

for T_env_guess in np.arange(20, 30, 0.5):
    # Calculate ln(T - T_env)
    y = np.log(seg1['temperature_c'] - T_env_guess)
    x = seg1['time_min']
    
    # Fit linear model
    coeffs = np.polyfit(x, y, 1)
    k = -coeffs[0]  # slope should be -k
    intercept = coeffs[1]
    
    # Calculate R-squared
    y_pred = np.polyval(coeffs, x)
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else -np.inf
    
    if r2 > best_r2:
        best_r2 = r2
        best_T_env = T_env_guess
        best_k = k

print(f"\n=== Segment 1 Analysis ===")
print(f"Best fit T_env: {best_T_env:.2f}°C")
print(f"Best fit k: {best_k:.6f} /min")
print(f"R-squared for linear fit of ln(T-T_env): {best_r2:.6f}")

# Check if data is exactly exponential
# Calculate what the temperature should be if perfectly exponential
T0 = seg1['temperature_c'].iloc[0]
T_env = best_T_env
k = best_k

expected = T_env + (T0 - T_env) * np.exp(-k * seg1['time_min'])
residuals = seg1['temperature_c'] - expected
max_residual = np.max(np.abs(residuals))

print(f"\nMaximum residual between data and perfect exponential: {max_residual:.6f}°C")
print(f"Mean absolute residual: {np.mean(np.abs(residuals)):.6f}°C")

# Check if residuals are essentially zero (within machine precision)
if max_residual < 1e-10:
    print("Data appears to be PERFECTLY exponential (within machine precision)")
else:
    print("Data has small but non-zero residuals from exponential model")

# Do the same for segment 3
seg3 = df[df['time_min'] >= 121]

best_r2_seg3 = -np.inf
best_T_env_seg3 = None
best_k_seg3 = None

for T_env_guess in np.arange(20, 35, 0.5):
    y = np.log(seg3['temperature_c'] - T_env_guess)
    x = seg3['time_min'] - seg3['time_min'].min()  # Reset time to 0
    
    coeffs = np.polyfit(x, y, 1)
    k = -coeffs[0]
    
    y_pred = np.polyval(coeffs, x)
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else -np.inf
    
    if r2 > best_r2_seg3:
        best_r2_seg3 = r2
        best_T_env_seg3 = T_env_guess
        best_k_seg3 = k

print(f"\n=== Segment 3 Analysis ===")
print(f"Best fit T_env: {best_T_env_seg3:.2f}°C")
print(f"Best fit k: {best_k_seg3:.6f} /min")
print(f"R-squared for linear fit of ln(T-T_env): {best_r2_seg3:.6f}")

# Check segment 2
seg2 = df[(df['time_min'] >= 80) & (df['time_min'] <= 120)]

best_r2_seg2 = -np.inf
best_T_env_seg2 = None
best_k_seg2 = None

for T_env_guess in np.arange(30, 45, 0.5):
    y = np.log(seg2['temperature_c'] - T_env_guess)
    x = seg2['time_min'] - seg2['time_min'].min()  # Reset time to 0
    
    coeffs = np.polyfit(x, y, 1)
    k = -coeffs[0]
    
    y_pred = np.polyval(coeffs, x)
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else -np.inf
    
    if r2 > best_r2_seg2:
        best_r2_seg2 = r2
        best_T_env_seg2 = T_env_guess
        best_k_seg2 = k

print(f"\n=== Segment 2 Analysis ===")
print(f"Best fit T_env: {best_T_env_seg2:.2f}°C")
print(f"Best fit k: {best_k_seg2:.6f} /min")
print(f"R-squared for linear fit of ln(T-T_env): {best_r2_seg2:.6f}")

# Create visualization of linearity check
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# Plot 1: Segment 1 temperature
ax = axes[0, 0]
ax.plot(seg1['time_min'], seg1['temperature_c'], 'b.-')
ax.set_xlabel('Time (min)')
ax.set_ylabel('Temperature (°C)')
ax.set_title('Segment 1: Temperature vs Time')
ax.grid(True, alpha=0.3)

# Plot 2: Segment 1 ln(T - T_env) vs time
ax = axes[0, 1]
y = np.log(seg1['temperature_c'] - best_T_env)
ax.plot(seg1['time_min'], y, 'r.-')
# Add linear fit
coeffs = np.polyfit(seg1['time_min'], y, 1)
y_fit = np.polyval(coeffs, seg1['time_min'])
ax.plot(seg1['time_min'], y_fit, 'k--', alpha=0.7, label=f'Linear fit: slope={-coeffs[0]:.4f}')
ax.set_xlabel('Time (min)')
ax.set_ylabel('ln(T - T_env)')
ax.set_title(f'Segment 1: ln(T - {best_T_env:.1f}°C) vs Time')
ax.grid(True, alpha=0.3)
ax.legend()

# Plot 3: Segment 1 residuals
ax = axes[0, 2]
residuals = y - y_fit
ax.plot(seg1['time_min'], residuals, 'g.-')
ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax.set_xlabel('Time (min)')
ax.set_ylabel('Residual')
ax.set_title('Segment 1: Residuals from linear fit')
ax.grid(True, alpha=0.3)

# Repeat for segment 3
ax = axes[1, 0]
ax.plot(seg3['time_min'], seg3['temperature_c'], 'b.-')
ax.set_xlabel('Time (min)')
ax.set_ylabel('Temperature (°C)')
ax.set_title('Segment 3: Temperature vs Time')
ax.grid(True, alpha=0.3)

ax = axes[1, 1]
y3 = np.log(seg3['temperature_c'] - best_T_env_seg3)
time_rel = seg3['time_min'] - seg3['time_min'].min()
ax.plot(time_rel, y3, 'r.-')
coeffs3 = np.polyfit(time_rel, y3, 1)
y_fit3 = np.polyval(coeffs3, time_rel)
ax.plot(time_rel, y_fit3, 'k--', alpha=0.7, label=f'Linear fit: slope={-coeffs3[0]:.4f}')
ax.set_xlabel('Time (min, relative)')
ax.set_ylabel('ln(T - T_env)')
ax.set_title(f'Segment 3: ln(T - {best_T_env_seg3:.1f}°C) vs Time')
ax.grid(True, alpha=0.3)
ax.legend()

ax = axes[1, 2]
residuals3 = y3 - y_fit3
ax.plot(time_rel, residuals3, 'g.-')
ax.axhline(y=0, color='k', linestyle='--', alpha=0.5)
ax.set_xlabel('Time (min, relative)')
ax.set_ylabel('Residual')
ax.set_title('Segment 3: Residuals from linear fit')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/linearity_check.png', dpi=150)
plt.close()

print("\n=== Conclusion ===")
print("The data appears to be synthetic and follows Newton's Law of Cooling exactly")
print("for each segment, with different ambient temperatures for each segment.")
print("This suggests experimental interventions at times 80 and 121 minutes.")