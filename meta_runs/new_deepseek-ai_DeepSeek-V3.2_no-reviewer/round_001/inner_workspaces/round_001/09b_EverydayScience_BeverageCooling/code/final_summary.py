import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

# Load data
df = pd.read_csv('data/beverage_temperature_series.csv')
t = df['time_min'].values
T = df['temperature_c'].values

# Load results
with open('outputs/log_linear_results.json', 'r') as f:
    results = json.load(f)

print("="*60)
print("FINAL SUMMARY OF BEVERAGE COOLING ANALYSIS")
print("="*60)

# Create comprehensive summary figure
plt.figure(figsize=(16, 12))

# 1. Raw data with interventions marked
plt.subplot(3, 2, 1)
plt.plot(t, T, 'b-', linewidth=2, alpha=0.8, label='Temperature data')
plt.axvline(x=80, color='r', linestyle='--', alpha=0.7, linewidth=1.5, label='Intervention at 80 min')
# Mark the temperature jump
plt.annotate('Temperature jump
+5.15°C', xy=(80, 54.24), xytext=(60, 70),
             arrowprops=dict(arrowstyle='->', color='red', alpha=0.7),
             fontsize=10, color='red')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title('Beverage Cooling Data with Intervention')
plt.legend(loc='upper right')
plt.grid(True, alpha=0.3)

# 2. Newton cooling fit for Segment 1
plt.subplot(3, 2, 2)
mask_before = t < 80
t_before = t[mask_before]
T_before = T[mask_before]

# Newton model for Segment 1
T_env1 = results['before_intervention']['T_env']
k1 = results['before_intervention']['k']
T01 = results['before_intervention']['T0']

def newton_cooling(t, T_env, T0, k):
    return T_env + (T0 - T_env) * np.exp(-k * t)

T_pred_before = newton_cooling(t_before, T_env1, T01, k1)

plt.plot(t_before, T_before, 'b-', linewidth=2, alpha=0.7, label='Data')
plt.plot(t_before, T_pred_before, 'r--', linewidth=2.5, label=f'Newton fit: T_env={T_env1:.1f}°C, k={k1:.5f}')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title(f'Segment 1 (0-79 min): Perfect Newton Cooling (R²=1.000)')
plt.legend()
plt.grid(True, alpha=0.3)

# 3. Newton cooling fit for Segment 2
plt.subplot(3, 2, 3)
mask_after = t >= 80
t_after = t[mask_after]
T_after = T[mask_after]

# Newton model for Segment 2
T_env2 = results['after_intervention']['T_env']
k2 = results['after_intervention']['k']
# Use actual initial temperature at t=80, not the unrealistic fitted T0
T02_actual = T_after[0]  # 54.24°C

# Time relative to intervention
t_after_rel = t_after - 80
T_pred_after = newton_cooling(t_after_rel, T_env2, T02_actual, k2)

plt.plot(t_after, T_after, 'b-', linewidth=2, alpha=0.7, label='Data')
plt.plot(t_after, T_pred_after, 'g--', linewidth=2.5, label=f'Newton fit: T_env={T_env2:.1f}°C, k={k2:.5f}')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.title(f'Segment 2 (80-199 min): Newton Cooling (R²={results["after_intervention"]["r2"]:.3f})')
plt.legend()
plt.grid(True, alpha=0.3)

# 4. Log-linear plot for Segment 1
plt.subplot(3, 2, 4)
y_before = np.log(T_before - T_env1)
plt.scatter(t_before, y_before, alpha=0.6, label='Data')

# Linear fit
slope1 = -k1
intercept1 = np.log(T01 - T_env1)
x_line1 = np.array([t_before.min(), t_before.max()])
y_line1 = intercept1 + slope1 * x_line1
plt.plot(x_line1, y_line1, 'r-', linewidth=2, label=f'Linear fit: slope={slope1:.5f}')

plt.xlabel('Time (minutes)')
plt.ylabel('ln(T - T_env)')
plt.title('Log-Linear Plot: Segment 1 (Perfect Linear Fit)')
plt.legend()
plt.grid(True, alpha=0.3)

# 5. Log-linear plot for Segment 2
plt.subplot(3, 2, 5)
y_after = np.log(T_after - T_env2)
plt.scatter(t_after, y_after, alpha=0.6, label='Data')

# Linear fit
slope2 = -k2
intercept2 = np.log(T02_actual - T_env2)
x_line2 = np.array([t_after.min(), t_after.max()])
y_line2 = intercept2 + slope2 * (x_line2 - 80)  # Adjust for time shift
plt.plot(x_line2, y_line2, 'g-', linewidth=2, label=f'Linear fit: slope={slope2:.5f}')

plt.xlabel('Time (minutes)')
plt.ylabel('ln(T - T_env)')
plt.title('Log-Linear Plot: Segment 2 (Good but Not Perfect Linear Fit)')
plt.legend()
plt.grid(True, alpha=0.3)

# 6. Cooling constants comparison
plt.subplot(3, 2, 6)
# Calculate instantaneous cooling rate
cooling_rate = -np.gradient(T, t)
# Estimate T_env from tail for k calculation
T_env_est = np.mean(T[-20:])
k_instant = cooling_rate / (T - T_env_est)
k_instant = np.where(k_instant > 0, k_instant, np.nan)

plt.plot(t, k_instant, 'b-', alpha=0.5, linewidth=1, label='Instantaneous k')
plt.axhline(y=k1, color='r', linestyle='--', linewidth=2, label=f'Segment 1: k={k1:.5f}')
plt.axhline(y=k2, color='g', linestyle='--', linewidth=2, label=f'Segment 2: k={k2:.5f}')
plt.axvline(x=80, color='k', linestyle=':', alpha=0.5, label='Intervention')
plt.xlabel('Time (minutes)')
plt.ylabel('Cooling constant k (min⁻¹)')
plt.title(f'Cooling Constant: Increased by factor {k2/k1:.2f} after intervention')
plt.legend(loc='upper right')
plt.grid(True, alpha=0.3)
plt.ylim(0, 0.03)

plt.tight_layout()
plt.savefig('report/images/final_summary.png', dpi=300, bbox_inches='tight')
plt.savefig('outputs/final_summary.png', dpi=300, bbox_inches='tight')

# Print key findings
print("\nKEY FINDINGS:")
print("="*60)
print("1. DATA OVERVIEW:")
print(f"   - {len(df)} measurements over {t.max()} minutes")
print(f"   - Temperature range: {T.min():.1f}°C to {T.max():.1f}°C")
print(f"   - Clear intervention at t=80 min: temperature jumps from {T[79]:.2f}°C to {T[80]:.2f}°C (+{T[80]-T[79]:.2f}°C)")

print("\n2. SEGMENT 1 (0-79 min):")
print(f"   - Perfect fit to Newton's Law of Cooling (R² = {results['before_intervention']['r2']:.6f})")
print(f"   - Ambient temperature T_env = {T_env1:.2f}°C (reasonable room temperature)")
print(f"   - Cooling constant k = {k1:.6f} min⁻¹")
print(f"   - Half-life (time for ΔT to halve) = {np.log(2)/k1:.1f} minutes")
print(f"   - Initial temperature T0 = {T01:.2f}°C")

print("\n3. SEGMENT 2 (80-199 min):")
print(f"   - Good but not perfect fit (R² = {results['after_intervention']['r2']:.6f})")
print(f"   - Apparent ambient temperature T_env = {T_env2:.2f}°C (higher than Segment 1)")
print(f"   - Cooling constant k = {k2:.6f} min⁻¹ ({k2/k1:.2f}x faster than Segment 1)")
print(f"   - Half-life = {np.log(2)/k2:.1f} minutes")
print(f"   - The unrealistic T0 estimate ({results['after_intervention']['T0_at_intervention']:.1f}°C) suggests")
print("     the simple Newton model doesn't fully capture post-intervention dynamics")

print("\n4. PHYSICAL INTERPRETATION:")
print("   - The temperature jump at t=80 min suggests external intervention")
print("   - Possible scenarios:")
print("     a) Addition of hot liquid to the beverage")
print("     b) Beverage was stirred or moved to a different location")
print("     c) Measurement error or sensor recalibration")
print("   - The increased cooling constant (k) after intervention suggests:")
print("     - Changed heat transfer properties (different container?)")
print("     - Changed ambient conditions (moved to cooler location?)")
print("     - Beverage properties changed (different liquid added?)")

print("\n5. MODEL RECOMMENDATIONS:")
print("   - For Segment 1: Simple Newton cooling model is excellent")
print("   - For Segment 2: Newton model works but with different parameters")
print("   - For full dataset: Piecewise Newton model with intervention at t=80 min")
print("   - The intervention should be modeled as a temperature jump of +5.15°C")

print("\n" + "="*60)
print("Analysis complete. Summary figure saved to report/images/final_summary.png")