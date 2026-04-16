"""
LQR Gain Scheduling Analysis for Hot-Water Header Tank

This script implements:
1. Parameter blending via linear interpolation
2. Stability verification at all scheduling abscissas
3. Simulation with actuator saturation
4. Visualization of results
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set up paths
workspace = Path(__file__).parent.parent
data_path = workspace / 'data' / 'plant_linearizations.json'
outputs_path = workspace / 'outputs'
images_path = workspace / 'report' / 'images'

# Create directories
outputs_path.mkdir(exist_ok=True)
images_path.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 1. Load Data
# =============================================================================
print("="*60)
print("LQR Gain Scheduling Analysis")
print("="*60)

with open(data_path, 'r') as f:
    data = json.load(f)

dt = data['dt']
u_sat = data['u_sat']
z_verify = data['z_verify']
points = data['points']

print(f"\nLoaded parameters:")
print(f"  dt = {dt}")
print(f"  u_sat = {u_sat}")
print(f"  z_verify = {z_verify}")

# Extract endpoint data
z0 = points[0]['z']
z1 = points[1]['z']
A0 = points[0]['A'][0][0]  # Extract scalar from 1x1 matrix
B0 = points[0]['B'][0][0]
K0 = points[0]['K'][0][0]
A1 = points[1]['A'][0][0]
B1 = points[1]['B'][0][0]
K1 = points[1]['K'][0][0]

print(f"\nEndpoint calibrations:")
print(f"  z=0: A={A0}, B={B0}, K={K0}")
print(f"  z=1: A={A1}, B={B1}, K={K1}")

# =============================================================================
# 2. Parameter Blending (Linear Interpolation)
# =============================================================================
def interpolate_params(z):
    """
    Linear interpolation of A, B, K between endpoints.
    
    Formula: param(z) = param(z0) + (param(z1) - param(z0)) * (z - z0) / (z1 - z0)
    
    Since z0=0 and z1=1, this simplifies to:
    param(z) = param(0) + (param(1) - param(0)) * z
    """
    # Linear interpolation
    A = A0 + (A1 - A0) * z
    B = B0 + (B1 - B0) * z
    K = K0 + (K1 - K0) * z
    return A, B, K

# =============================================================================
# 3. Stability Verification
# =============================================================================
print("\n" + "="*60)
print("Stability Verification")
print("="*60)

stability_results = []
print(f"\n{'z':<8} {'A(z)':<10} {'B(z)':<10} {'K(z)':<10} {'A_cl(z)':<12} {'|A_cl(z)|':<12} {'Stable?'}")
print("-"*70)

for z in z_verify:
    A, B, K = interpolate_params(z)
    A_cl = A - B * K  # Closed-loop dynamics: x[k+1] = (A - B*K) * x[k]
    magnitude = abs(A_cl)
    stable = magnitude < 1.0
    stability_results.append({
        'z': z,
        'A': A,
        'B': B,
        'K': K,
        'A_cl': A_cl,
        'magnitude': magnitude,
        'stable': stable
    })
    status = "YES" if stable else "NO"
    print(f"{z:<8.2f} {A:<10.4f} {B:<10.4f} {K:<10.4f} {A_cl:<12.6f} {magnitude:<12.6f} {status}")

# Save stability results
with open(outputs_path / 'stability_results.json', 'w') as f:
    json.dump(stability_results, f, indent=2)

# =============================================================================
# 4. Simulation with Saturation
# =============================================================================
print("\n" + "="*60)
print("Simulation with Actuator Saturation")
print("="*60)

def saturation(u, u_max):
    """Output clamping (anti-windup for systems without integrator)"""
    return np.clip(u, -u_max, u_max)

def simulate(x0, z_profile, N_steps, dt, u_sat):
    """
    Simulate the closed-loop system with gain scheduling and saturation.
    
    x[k+1] = A(z[k]) * x[k] + B(z[k]) * u[k]
    u[k] = sat(-K(z[k]) * x[k], ±u_sat)
    
    Note: Anti-windup here is only output clamping since there's no integrator.
    """
    x_history = np.zeros(N_steps + 1)
    u_history = np.zeros(N_steps)
    z_history = np.zeros(N_steps)
    
    x_history[0] = x0
    
    for k in range(N_steps):
        z = z_profile(k * dt)
        z_history[k] = z
        
        # Get interpolated parameters
        A, B, K = interpolate_params(z)
        
        # Compute control with saturation
        u_raw = -K * x_history[k]
        u = saturation(u_raw, u_sat)
        u_history[k] = u
        
        # State update
        x_history[k + 1] = A * x_history[k] + B * u
    
    return x_history, u_history, z_history

# Define time-varying z profile
def z_profile(t):
    """
    Piecewise time-varying scheduling parameter.
    - t < 5s: z = 0 (quiet day)
    - 5s <= t < 15s: z ramps from 0 to 1 (transition to busy day)
    - t >= 15s: z = 1 (busy day)
    """
    if t < 5.0:
        return 0.0
    elif t < 15.0:
        return (t - 5.0) / 10.0  # Linear ramp
    else:
        return 1.0

# Simulation parameters
x0 = 2.0  # Initial water level deviation (e.g., tank is overfull)
N_steps = 300  # 30 seconds at dt=0.1

# Run simulation
x_hist, u_hist, z_hist = simulate(x0, z_profile, N_steps, dt, u_sat)

# Create time array
time = np.arange(N_steps + 1) * dt
time_u = np.arange(N_steps) * dt

print(f"\nSimulation completed:")
print(f"  Initial state x0 = {x0}")
print(f"  Duration = {N_steps * dt} seconds")
print(f"  Final state x = {x_hist[-1]:.6f}")
print(f"  Max |u| = {np.max(np.abs(u_hist)):.4f} (saturation limit = {u_sat})")

# Check for saturation events
saturation_events = np.sum(np.abs(u_hist) >= u_sat - 1e-9)
print(f"  Saturation events = {saturation_events} out of {N_steps} steps")

# =============================================================================
# 5. Visualization
# =============================================================================
print("\n" + "="*60)
print("Generating Figures")
print("="*60)

# Figure 1: State and Control Trajectories
fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

# Plot x[k]
axes[0].plot(time, x_hist, 'b-', linewidth=2, label='x[k] (water level)')
axes[0].axhline(y=0, color='k', linestyle='--', alpha=0.3)
axes[0].set_ylabel('Water Level x[k]', fontsize=12)
axes[0].legend(loc='upper right')
axes[0].grid(True, alpha=0.3)
axes[0].set_title('Closed-Loop State Trajectory with Gain Scheduling', fontsize=14)

# Plot u[k] with saturation bounds
axes[1].plot(time_u, u_hist, 'r-', linewidth=2, label='u[k] (pump command)')
axes[1].axhline(y=u_sat, color='k', linestyle='--', alpha=0.5, label=f'±u_sat = ±{u_sat}')
axes[1].axhline(y=-u_sat, color='k', linestyle='--', alpha=0.5)
axes[1].fill_between(time_u, -u_sat, u_sat, alpha=0.1, color='gray')
axes[1].set_ylabel('Control u[k]', fontsize=12)
axes[1].legend(loc='upper right')
axes[1].grid(True, alpha=0.3)
axes[1].set_title('Saturated Control Input', fontsize=14)

# Plot z[k]
axes[2].plot(time_u, z_hist, 'g-', linewidth=2, label='z[k] (load parameter)')
axes[2].set_ylabel('Scheduling z[k]', fontsize=12)
axes[2].set_xlabel('Time [s]', fontsize=12)
axes[2].legend(loc='upper right')
axes[2].grid(True, alpha=0.3)
axes[2].set_title('Time-Varying Scheduling Parameter', fontsize=14)

plt.tight_layout()
plt.savefig(images_path / 'simulation_results.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {images_path / 'simulation_results.png'}")

# Figure 2: Stability Analysis
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Plot closed-loop eigenvalue magnitude vs z
z_range = np.linspace(0, 1, 100)
A_cl_range = []
for z in z_range:
    A, B, K = interpolate_params(z)
    A_cl_range.append(abs(A - B * K))

axes[0].plot(z_range, A_cl_range, 'b-', linewidth=2, label='|A_cl(z)|')
axes[0].axhline(y=1.0, color='r', linestyle='--', linewidth=2, label='Stability boundary')
axes[0].scatter(z_verify, [r['magnitude'] for r in stability_results], 
               c='red', s=100, zorder=5, label='Verification points')
axes[0].set_xlabel('Scheduling Parameter z', fontsize=12)
axes[0].set_ylabel('|A_cl(z)|', fontsize=12)
axes[0].set_title('Closed-Loop Stability Across Scheduling Range', fontsize=14)
axes[0].legend()
axes[0].grid(True, alpha=0.3)
axes[0].set_ylim([0, max(A_cl_range) * 1.2])

# Bar chart of verification points
z_labels = [f'z={z}' for z in z_verify]
magnitudes = [r['magnitude'] for r in stability_results]
colors = ['green' if m < 1.0 else 'red' for m in magnitudes]

bars = axes[1].bar(z_labels, magnitudes, color=colors, alpha=0.7, edgecolor='black')
axes[1].axhline(y=1.0, color='r', linestyle='--', linewidth=2, label='Stability boundary')
axes[1].set_xlabel('Scheduling Parameter', fontsize=12)
axes[1].set_ylabel('|A_cl(z)|', fontsize=12)
axes[1].set_title('Stability Verification at Check Abscissas', fontsize=14)
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, mag in zip(bars, magnitudes):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{mag:.4f}', ha='center', va='bottom', fontsize=11)

plt.tight_layout()
plt.savefig(images_path / 'stability_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {images_path / 'stability_analysis.png'}")

# Figure 3: Parameter Interpolation
fig, axes = plt.subplots(1, 3, figsize=(14, 4))

z_range = np.linspace(0, 1, 100)
A_range = [interpolate_params(z)[0] for z in z_range]
B_range = [interpolate_params(z)[1] for z in z_range]
K_range = [interpolate_params(z)[2] for z in z_range]

axes[0].plot(z_range, A_range, 'b-', linewidth=2)
axes[0].scatter([0, 1], [A0, A1], c='red', s=100, zorder=5, label='Calibration points')
axes[0].set_xlabel('z', fontsize=12)
axes[0].set_ylabel('A(z)', fontsize=12)
axes[0].set_title('Plant Parameter A(z)', fontsize=14)
axes[0].grid(True, alpha=0.3)
axes[0].legend()

axes[1].plot(z_range, B_range, 'g-', linewidth=2)
axes[1].scatter([0, 1], [B0, B1], c='red', s=100, zorder=5, label='Calibration points')
axes[1].set_xlabel('z', fontsize=12)
axes[1].set_ylabel('B(z)', fontsize=12)
axes[1].set_title('Plant Parameter B(z)', fontsize=14)
axes[1].grid(True, alpha=0.3)
axes[1].legend()

axes[2].plot(z_range, K_range, 'm-', linewidth=2)
axes[2].scatter([0, 1], [K0, K1], c='red', s=100, zorder=5, label='Calibration points')
axes[2].set_xlabel('z', fontsize=12)
axes[2].set_ylabel('K(z)', fontsize=12)
axes[2].set_title('Controller Gain K(z)', fontsize=14)
axes[2].grid(True, alpha=0.3)
axes[2].legend()

plt.tight_layout()
plt.savefig(images_path / 'parameter_interpolation.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {images_path / 'parameter_interpolation.png'}")

# =============================================================================
# 6. Save Simulation Data
# =============================================================================
simulation_data = {
    'dt': dt,
    'u_sat': u_sat,
    'x0': x0,
    'N_steps': N_steps,
    'time': time.tolist(),
    'x_history': x_hist.tolist(),
    'u_history': u_hist.tolist(),
    'z_history': z_hist.tolist()
}

with open(outputs_path / 'simulation_data.json', 'w') as f:
    json.dump(simulation_data, f, indent=2)

print(f"\nSaved simulation data to {outputs_path / 'simulation_data.json'}")

print("\n" + "="*60)
print("Analysis Complete!")
print("="*60)
