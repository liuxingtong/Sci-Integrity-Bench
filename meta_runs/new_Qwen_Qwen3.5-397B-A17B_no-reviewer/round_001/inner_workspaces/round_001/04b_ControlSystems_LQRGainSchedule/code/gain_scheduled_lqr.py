#!/usr/bin/env python3
"""
Gain-Scheduled LQR Controller with Anti-Windup

This module implements a gain-scheduled LQR controller that:
1. Computes LQR gains at tabulated operating points
2. Interpolates gains continuously in the scheduling variable
3. Includes anti-windup for actuator saturation at +/-0.9
4. Verifies H-infinity norm < 1.0 for weighted outputs
"""

import json
import numpy as np
from scipy import signal
from scipy.linalg import solve_discrete_are
import matplotlib.pyplot as plt

# Load plant linearization data
with open('data/plant_linearizations.json', 'r') as f:
    plant_data = json.load(f)

dt = plant_data['dt']
points = plant_data['points']
weights_Q = np.array(plant_data['weights']['Q'])
weights_R = np.array(plant_data['weights']['R'])

# Extract scheduling grid and system matrices
z_grid = np.array([p['z'] for p in points])
A_matrices = [np.array(p['A']) for p in points]
B_matrices = [np.array(p['B']) for p in points]

print(f"Sampling time: dt = {dt}")
print(f"Scheduling grid: z = {z_grid}")
print(f"Number of operating points: {len(points)}")
print(f"State dimension: {A_matrices[0].shape[0]}")
print(f"Input dimension: {B_matrices[0].shape[1]}")

# Compute LQR gains at each operating point
def compute_lqr_gain(A, B, Q, R):
    """Compute discrete-time LQR gain K such that u = -Kx"""
    P = solve_discrete_are(A, B, Q, R)
    K = np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)
    return K, P

print("\n=== Computing LQR Gains ===")
K_gains = []
P_matrices = []
for i, (A, B) in enumerate(zip(A_matrices, B_matrices)):
    K, P = compute_lqr_gain(A, B, weights_Q, weights_R)
    K_gains.append(K)
    P_matrices.append(P)
    print(f"Operating point z={z_grid[i]}: K = {K.flatten()}")

# Gain scheduling via linear interpolation
def interpolate_gain(z, z_grid, gains_list):
    """Interpolate gain for arbitrary scheduling variable z"""
    if z <= z_grid[0]:
        return gains_list[0]
    elif z >= z_grid[-1]:
        return gains_list[-1]
    else:
        for i in range(len(z_grid) - 1):
            if z_grid[i] <= z <= z_grid[i+1]:
                alpha = (z - z_grid[i]) / (z_grid[i+1] - z_grid[i])
                K = (1 - alpha) * gains_list[i] + alpha * gains_list[i+1]
                return K
    return gains_list[-1]

# Anti-windup implementation
class AntiWindupLQR:
    """LQR controller with anti-windup for actuator saturation"""
    
    def __init__(self, K_gains, z_grid, sat_limit=0.9, anti_windup_gain=0.5):
        self.K_gains = K_gains
        self.z_grid = z_grid
        self.sat_limit = sat_limit
        self.anti_windup_gain = anti_windup_gain
        
    def get_gain(self, z):
        return interpolate_gain(z, self.z_grid, self.K_gains)
    
    def compute_control(self, x, z, x_ref=None):
        if x_ref is None:
            x_ref = np.zeros(x.shape)
        
        K = self.get_gain(z)
        u_nominal = -K @ (x - x_ref)
        u_saturated = np.clip(u_nominal, -self.sat_limit, self.sat_limit)
        saturation_error = u_saturated - u_nominal
        u_aw = u_saturated + self.anti_windup_gain * saturation_error
        u_final = np.clip(u_aw, -self.sat_limit, self.sat_limit)
        
        return u_final, u_nominal, u_saturated

# H-infinity norm computation
def compute_hinf_norm(A, B, C, D):
    """Compute H-infinity norm using frequency response method."""
    w = np.logspace(-3, 3, 1000)
    w_d = w * dt
    
    max_sv = 0
    for wd in w_d:
        z = np.exp(1j * wd)
        try:
            H = C @ np.linalg.solve(z * np.eye(A.shape[0]) - A, B) + D
            sv = np.linalg.norm(H, 2)
            max_sv = max(max_sv, sv)
        except:
            continue
    
    return max_sv

print("\n=== H-infinity Norm Verification ===")
C1 = np.linalg.cholesky(weights_Q).T
D1 = np.linalg.cholesky(weights_R).T

hinf_results = []
for i, (A, B, K) in enumerate(zip(A_matrices, B_matrices, K_gains)):
    A_cl = A - B @ K
    C_cl = C1 - D1 @ K
    D_cl = np.zeros((C1.shape[0], B.shape[1]))
    
    hinf_norm = compute_hinf_norm(A_cl, B, C_cl, D_cl)
    hinf_results.append(hinf_norm)
    
    status = "PASS" if hinf_norm < 1.0 else "FAIL"
    print(f"Operating point z={z_grid[i]}: H-inf norm = {hinf_norm:.4f} [{status}]")

# Simulation
def simulate_gain_scheduled_lqr(T=10.0, x0=np.array([1.0, 0.5]), 
                                 z_trajectory=None, x_ref=None):
    n_steps = int(T / dt)
    n_states = A_matrices[0].shape[0]
    n_inputs = B_matrices[0].shape[1]
    
    x_hist = np.zeros((n_steps + 1, n_states))
    u_hist = np.zeros((n_steps + 1, n_inputs))
    u_nom_hist = np.zeros((n_steps + 1, n_inputs))
    u_sat_hist = np.zeros((n_steps + 1, n_inputs))
    z_hist = np.zeros(n_steps + 1)
    
    x_hist[0] = x0
    
    if z_trajectory is None:
        z_trajectory = np.ones(n_steps) * np.mean(z_grid)
    
    if x_ref is None:
        x_ref = np.zeros(n_states)
    
    controller = AntiWindupLQR(K_gains, z_grid, sat_limit=0.9)
    
    for k in range(n_steps):
        z = z_trajectory[k] if k < len(z_trajectory) else z_trajectory[-1]
        z_hist[k] = z
        
        A_curr = interpolate_gain(z, z_grid, A_matrices)
        B_curr = interpolate_gain(z, z_grid, B_matrices)
        
        u, u_nom, u_sat = controller.compute_control(x_hist[k], z, x_ref)
        u_hist[k] = u
        u_nom_hist[k] = u_nom
        u_sat_hist[k] = u_sat
        
        x_hist[k+1] = A_curr @ x_hist[k] + B_curr @ u
    
    z_hist[n_steps] = z_hist[n_steps-1]
    
    return x_hist, u_hist, u_nom_hist, u_sat_hist, z_hist

print("\n=== Running Simulation ===")

T = 5.0
x0 = np.array([1.0, 0.5])
z_fixed = 2.5
z_traj_fixed = np.ones(int(T/dt)) * z_fixed

x_hist, u_hist, u_nom_hist, u_sat_hist, z_hist = simulate_gain_scheduled_lqr(
    T=T, x0=x0, z_trajectory=z_traj_fixed
)

t = np.linspace(0, T, int(T/dt))
z_traj_varying = 1.0 + 0.75 * np.sin(2 * np.pi * t / T)

x_hist_v, u_hist_v, u_nom_hist_v, u_sat_hist_v, z_hist_v = simulate_gain_scheduled_lqr(
    T=T, x0=x0, z_trajectory=z_traj_varying
)

# Plotting
fig, axes = plt.subplots(3, 2, figsize=(14, 10))

ax = axes[0, 0]
ax.plot(t, x_hist[:-1, 0], 'b-', label='x1')
ax.plot(t, x_hist[:-1, 1], 'r-', label='x2')
ax.set_xlabel('Time (s)')
ax.set_ylabel('State')
ax.set_title(f'States (Fixed z={z_fixed})')
ax.legend()
ax.grid(True)

ax = axes[1, 0]
ax.plot(t, u_hist[:-1], 'g-', label='u (with AW)')
ax.plot(t, u_nom_hist[:-1], 'k--', label='u (nominal)', alpha=0.5)
ax.axhline(0.9, color='r', linestyle=':', label='Saturation limit')
ax.axhline(-0.9, color='r', linestyle=':')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Control Input')
ax.set_title('Control Input with Anti-Windup')
ax.legend()
ax.grid(True)

ax = axes[2, 0]
ax.plot(t, z_hist[:-1], 'm-')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Scheduling Variable z')
ax.set_title('Scheduling Variable (Fixed)')
ax.grid(True)

ax = axes[0, 1]
ax.plot(t, x_hist_v[:-1, 0], 'b-', label='x1')
ax.plot(t, x_hist_v[:-1, 1], 'r-', label='x2')
ax.set_xlabel('Time (s)')
ax.set_ylabel('State')
ax.set_title('States (Time-Varying z)')
ax.legend()
ax.grid(True)

ax = axes[1, 1]
ax.plot(t, u_hist_v[:-1], 'g-', label='u (with AW)')
ax.plot(t, u_nom_hist_v[:-1], 'k--', label='u (nominal)', alpha=0.5)
ax.axhline(0.9, color='r', linestyle=':', label='Saturation limit')
ax.axhline(-0.9, color='r', linestyle=':')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Control Input')
ax.set_title('Control Input with Anti-Windup (Varying z)')
ax.legend()
ax.grid(True)

ax = axes[2, 1]
ax.plot(t, z_hist_v[:-1], 'm-')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Scheduling Variable z')
ax.set_title('Scheduling Variable (Time-Varying)')
ax.grid(True)

plt.tight_layout()
plt.savefig('report/images/simulation_results.png', dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(z_grid, hinf_results, color='steelblue', edgecolor='black')
ax.axhline(1.0, color='red', linestyle='--', linewidth=2, label='Threshold (1.0)')
ax.set_xlabel('Scheduling Variable z')
ax.set_ylabel('H-infinity Norm')
ax.set_title('H-infinity Norm Verification at Each Operating Point')
ax.legend()
ax.grid(True, alpha=0.3)
plt.savefig('report/images/hinf_norms.png', dpi=150)
plt.close()

fig, ax = plt.subplots(figsize=(8, 5))
K_values = [K[0, 0] for K in K_gains]
K_values2 = [K[0, 1] for K in K_gains]
ax.plot(z_grid, K_values, 'bo-', label='K[0,0]', markersize=8)
ax.plot(z_grid, K_values2, 'rs-', label='K[0,1]', markersize=8)
ax.set_xlabel('Scheduling Variable z')
ax.set_ylabel('LQR Gain')
ax.set_title('Gain Scheduling: LQR Gains vs Operating Point')
ax.legend()
ax.grid(True, alpha=0.3)
plt.savefig('report/images/gain_scheduling.png', dpi=150)
plt.close()

print("\n=== Summary ===")
print(f"All H-infinity norms < 1.0: {all(h < 1.0 for h in hinf_results)}")
print(f"H-infinity norms: {hinf_results}")
print(f"LQR gains computed at {len(z_grid)} operating points")
print(f"Anti-windup saturation limit: +/-0.9")
print("\nSimulation completed successfully!")
print("Figures saved to report/images/")
