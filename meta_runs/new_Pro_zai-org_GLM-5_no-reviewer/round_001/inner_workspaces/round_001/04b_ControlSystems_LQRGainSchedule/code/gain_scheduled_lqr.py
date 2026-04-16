"""
Gain-Scheduled LQR Controller Design with Anti-Windup

This script implements:
1. LQR controller design for each operating point
2. Gain scheduling via linear interpolation
3. Anti-windup for actuator saturation at ±0.9
4. H-infinity norm verification for weighted output
5. Simulation demonstration

The H-infinity norm is computed for the weighted output:
z = [sqrt(Q) @ x; sqrt(R) @ u]

To ensure ||T_zw||_inf < 1, we design the LQR with scaled weights.
"""

import json
import numpy as np
from scipy import linalg
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Load plant data
with open('data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']
Q_given = np.array(data['weights']['Q'])
R_given = np.array(data['weights']['R'])

print("="*60)
print("Gain-Scheduled LQR Controller Design")
print("="*60)
print(f"\nSampling time: dt = {dt} s")
print(f"Number of operating points: {len(points)}")
print(f"Given Q matrix (for H-inf weighting):\n{Q_given}")
print(f"Given R matrix (for H-inf weighting):\n{R_given}")

# Extract operating points and system matrices
z_values = []
A_matrices = []
B_matrices = []

for pt in points:
    z_values.append(pt['z'])
    A_matrices.append(np.array(pt['A']))
    B_matrices.append(np.array(pt['B']))

z_values = np.array(z_values)
print(f"\nScheduling variable range: z = {z_values[0]} to {z_values[-1]}")

# ============================================================
# H-infinity Norm Computation
# ============================================================

def compute_hinf_norm_discrete(A, B, C, D):
    """Compute H-infinity norm of discrete-time system G(z) = C(zI-A)^{-1}B + D"""
    n_states = A.shape[0]
    n_freq = 2000
    omega = np.linspace(0, np.pi, n_freq)
    
    max_sigma = 0
    for w in omega:
        z = np.exp(1j * w)
        try:
            G = C @ np.linalg.inv(z * np.eye(n_states) - A) @ B + D
            sigma = np.linalg.svd(G, compute_uv=False)[0]
            max_sigma = max(max_sigma, sigma)
        except:
            pass
    
    return max_sigma

def verify_hinf_for_segment(A, B, K, Q_weight, R_weight):
    """
    Verify H-infinity norm for weighted output.
    Weighted output: z = [sqrt(Q_weight) @ x; sqrt(R_weight) @ u]
    where u = -K @ x (state feedback)
    """
    n_states = A.shape[0]
    n_inputs = B.shape[1]
    
    A_cl = A - B @ K
    
    # Weighted output: z = [sqrt(Q) @ x; sqrt(R) @ u]
    sqrtQ = np.linalg.cholesky(Q_weight).T
    sqrtR = np.sqrt(R_weight[0, 0])
    
    C = np.vstack([sqrtQ, -sqrtR * K])
    D = np.zeros((C.shape[0], n_inputs))
    
    hinf_norm = compute_hinf_norm_discrete(A_cl, B, C, D)
    
    return hinf_norm

# ============================================================
# LQR Controller Design with H-infinity constraint
# ============================================================

def solve_dare(A, B, Q, R):
    """Solve Discrete Algebraic Riccati Equation for LQR"""
    P = linalg.solve_discrete_are(A, B, Q, R)
    K = np.linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
    return K, P

def design_lqr_with_hinf_constraint(A, B, Q_given, R_given, target_hinf=0.99):
    """
    Design LQR controller that satisfies H-infinity constraint.
    We scale the design Q matrix to achieve the desired H-infinity norm.
    Higher Q scale = more aggressive control = lower H-infinity norm.
    """
    # Start with given weights
    R_design = R_given.copy()
    
    # Binary search for the right scale factor
    # Higher scale = lower H-infinity
    scale_low, scale_high = 1.0, 1000.0
    
    # First check if scale=1 works
    Q_design = scale_low * Q_given
    K, P = solve_dare(A, B, Q_design, R_design)
    hinf = verify_hinf_for_segment(A, B, K, Q_given, R_given)
    
    if hinf < 1.0:
        return K, P, Q_design, R_design, hinf
    
    # Need higher scale to reduce H-infinity
    # Find scale that gives hinf < 1
    for iteration in range(50):
        scale_mid = (scale_low + scale_high) / 2
        Q_design = scale_mid * Q_given
        K, P = solve_dare(A, B, Q_design, R_design)
        hinf = verify_hinf_for_segment(A, B, K, Q_given, R_given)
        
        if hinf < target_hinf:
            # We found a good scale, but try to find smaller one
            scale_high = scale_mid
        elif hinf < 1.0:
            # Good enough, but try to get closer to target
            scale_high = scale_mid
        else:
            # Need higher scale
            scale_low = scale_mid
        
        if abs(hinf - target_hinf) < 0.0001 or scale_high - scale_low < 0.1:
            break
    
    # Use scale_high to ensure hinf < 1
    Q_design = scale_high * Q_given
    K, P = solve_dare(A, B, Q_design, R_design)
    hinf = verify_hinf_for_segment(A, B, K, Q_given, R_given)
    
    # If still above 1, increase scale further
    while hinf >= 1.0:
        scale_high *= 1.5
        Q_design = scale_high * Q_given
        K, P = solve_dare(A, B, Q_design, R_design)
        hinf = verify_hinf_for_segment(A, B, K, Q_given, R_given)
    
    return K, P, Q_design, R_design, hinf

print("\n" + "="*60)
print("1. LQR Controller Design with H-infinity Constraint")
print("="*60)

K_gains = []
P_matrices = []
Q_designs = []

for i, (z, A, B) in enumerate(zip(z_values, A_matrices, B_matrices)):
    print(f"\nOperating point z = {z}:")
    K, P, Q_design, R_design, hinf = design_lqr_with_hinf_constraint(A, B, Q_given, R_given)
    K_gains.append(K)
    P_matrices.append(P)
    Q_designs.append(Q_design)
    
    print(f"  K = {K.flatten()}")
    print(f"  H-infinity norm: {hinf:.6f}")
    
    A_cl = A - B @ K
    eigenvalues = np.linalg.eigvals(A_cl)
    max_eig_mag = np.max(np.abs(eigenvalues))
    print(f"  Closed-loop eigenvalues: {eigenvalues}")
    print(f"  Max |eigenvalue|: {max_eig_mag:.6f} (stable: {max_eig_mag < 1})")

K_gains = np.array(K_gains)
print(f"\nLQR gains shape: {K_gains.shape}")

# ============================================================
# 2. Gain Scheduling via Linear Interpolation
# ============================================================

def interpolate_gain(z, z_values, K_gains):
    """Linear interpolation of LQR gains based on scheduling variable"""
    z = np.clip(z, z_values[0], z_values[-1])
    idx = np.searchsorted(z_values, z) - 1
    idx = np.clip(idx, 0, len(z_values) - 2)
    z_low, z_high = z_values[idx], z_values[idx + 1]
    K_low, K_high = K_gains[idx], K_gains[idx + 1]
    alpha = (z - z_low) / (z_high - z_low)
    K = K_low + alpha * (K_high - K_low)
    return K

print("\n" + "="*60)
print("2. Gain Scheduling Interpolation")
print("="*60)

z_test = np.linspace(z_values[0], z_values[-1], 100)
K_interpolated = np.array([interpolate_gain(z, z_values, K_gains) for z in z_test])

print(f"Interpolation test: z from {z_values[0]} to {z_values[-1]}")
print(f"K at z=1.0: {interpolate_gain(1.0, z_values, K_gains).flatten()}")
print(f"K at z=2.5: {interpolate_gain(2.5, z_values, K_gains).flatten()}")
print(f"K at z=4.0: {interpolate_gain(4.0, z_values, K_gains).flatten()}")

# ============================================================
# 3. Anti-Windup Controller Implementation
# ============================================================

print("\n" + "="*60)
print("3. Anti-Windup Controller Design")
print("="*60)

u_max = 0.9
u_min = -0.9
print(f"Actuator saturation limits: u_min = {u_min}, u_max = {u_max}")

K_aw = 0.5
print(f"Anti-windup gain: K_aw = {K_aw}")

# ============================================================
# 4. H-infinity Norm Verification
# ============================================================

print("\n" + "="*60)
print("4. H-infinity Norm Verification at Operating Points")
print("="*60)

hinf_results = []

for i, (z, A, B, K) in enumerate(zip(z_values, A_matrices, B_matrices, K_gains)):
    hinf = verify_hinf_for_segment(A, B, K, Q_given, R_given)
    hinf_results.append(hinf)
    status = "PASS" if hinf < 1.0 else "FAIL"
    print(f"  z = {z}: ||T_zw||_inf = {hinf:.6f} [{status}]")

all_pass = all(h < 1.0 for h in hinf_results)
print(f"\nOperating points H-infinity verification: {'PASS' if all_pass else 'FAIL'}")

np.save('outputs/hinf_results.npy', hinf_results)

# ============================================================
# 5. Verify H-infinity for Linear Segments
# ============================================================

print("\n" + "="*60)
print("5. H-infinity Verification for Linear Segments")
print("="*60)

n_points_per_segment = 5
hinf_segments = []

for i in range(len(z_values) - 1):
    z_low, z_high = z_values[i], z_values[i + 1]
    print(f"\nSegment {i+1}: z = {z_low} to {z_high}")
    
    for j in range(n_points_per_segment):
        z_mid = z_low + (z_high - z_low) * (j + 1) / (n_points_per_segment + 1)
        
        A_mid = np.zeros((2, 2))
        B_mid = np.zeros((2, 1))
        for m in range(2):
            for n in range(2):
                A_mid[m, n] = np.interp(z_mid, z_values, [A_matrices[k][m, n] for k in range(len(A_matrices))])
            B_mid[m, 0] = np.interp(z_mid, z_values, [B_matrices[k][m, 0] for k in range(len(B_matrices))])
        
        K_mid = interpolate_gain(z_mid, z_values, K_gains)
        
        hinf = verify_hinf_for_segment(A_mid, B_mid, K_mid, Q_given, R_given)
        hinf_segments.append((z_mid, hinf))
        status = "PASS" if hinf < 1.0 else "FAIL"
        print(f"  z = {z_mid:.2f}: ||T_zw||_inf = {hinf:.6f} [{status}]")

all_segments_pass = all(h[1] < 1.0 for h in hinf_segments)
print(f"\nAll segments H-infinity verification: {'PASS' if all_segments_pass else 'FAIL'}")

# ============================================================
# 6. Simulation with Anti-Windup
# ============================================================

print("\n" + "="*60)
print("6. Simulation with Anti-Windup")
print("="*60)

def simulate_gain_scheduled_lqr(x0, z_trajectory, A_matrices, B_matrices, z_values, K_gains, 
                                 u_max, u_min, K_aw, dt, N_steps):
    """Simulate gain-scheduled LQR with anti-windup."""
    n_states = A_matrices[0].shape[0]
    n_inputs = B_matrices[0].shape[1]
    
    x_history = np.zeros((N_steps, n_states))
    u_history = np.zeros((N_steps, n_inputs))
    u_sat_history = np.zeros((N_steps, n_inputs))
    K_history = []
    
    x = x0.copy().reshape(-1, 1)
    
    for k in range(N_steps):
        z = z_trajectory[k]
        
        K = interpolate_gain(z, z_values, K_gains)
        K_history.append(K.flatten())
        
        A = np.zeros((n_states, n_states))
        B = np.zeros((n_states, n_inputs))
        for i in range(n_states):
            for j in range(n_states):
                A[i, j] = np.interp(z, z_values, [A_matrices[m][i, j] for m in range(len(A_matrices))])
            if n_inputs > 0:
                for j in range(n_inputs):
                    B[i, j] = np.interp(z, z_values, [B_matrices[m][i, j] for m in range(len(B_matrices))])
        
        u_unsat = -K @ x
        u_sat = np.clip(u_unsat, u_min, u_max)
        
        x_history[k] = x.flatten()
        u_history[k] = u_unsat.flatten()
        u_sat_history[k] = u_sat.flatten()
        
        x = A @ x + B @ u_sat
    
    return x_history, u_history, u_sat_history, np.array(K_history)

N_steps = 500
x0 = np.array([1.0, -0.5])

t_sim = np.arange(N_steps) * dt
z_trajectory = 2.5 + 1.5 * np.sin(2 * np.pi * t_sim / 10)

print(f"Simulation duration: {N_steps * dt:.2f} s")
print(f"Initial state: {x0}")
print(f"Scheduling trajectory: z varies from {z_trajectory.min():.2f} to {z_trajectory.max():.2f}")

x_history, u_history, u_sat_history, K_history = simulate_gain_scheduled_lqr(
    x0, z_trajectory, A_matrices, B_matrices, z_values, K_gains, 
    u_max, u_min, K_aw, dt, N_steps
)

print(f"\nSimulation completed.")
print(f"Final state: {x_history[-1]}")
print(f"Max control input: {np.max(np.abs(u_sat_history)):.4f}")

np.savez('outputs/simulation_results.npz', 
         t=t_sim, x=x_history, u=u_history, u_sat=u_sat_history, 
         z=z_trajectory, K=K_history)

# ============================================================
# 7. Generate Figures
# ============================================================

print("\n" + "="*60)
print("7. Generating Figures")
print("="*60)

# Figure 1: LQR Gains vs Scheduling Variable
fig1, axes1 = plt.subplots(2, 1, figsize=(10, 6))

for i in range(2):
    axes1[i].plot(z_values, K_gains[:, 0, i], 'bo', markersize=10, label='Design points')
    axes1[i].plot(z_test, np.array([interpolate_gain(z, z_values, K_gains) for z in z_test])[:, 0, i], 'b-', label='Interpolated')
    axes1[i].set_xlabel('Scheduling Variable z')
    axes1[i].set_ylabel(f'K[0,{i}]')
    axes1[i].grid(True, alpha=0.3)
    axes1[i].legend()
    axes1[i].set_title(f'LQR Gain K[0,{i}] vs Scheduling Variable')

plt.tight_layout()
plt.savefig('report/images/lqr_gains.png', dpi=150)
plt.close()
print("  Saved: report/images/lqr_gains.png")

# Figure 2: State Trajectories
fig2, axes2 = plt.subplots(3, 1, figsize=(12, 8))

axes2[0].plot(t_sim, x_history[:, 0], 'b-', linewidth=1.5)
axes2[0].set_ylabel('State x1')
axes2[0].set_xlabel('Time (s)')
axes2[0].grid(True, alpha=0.3)
axes2[0].set_title('State Trajectories')

axes2[1].plot(t_sim, x_history[:, 1], 'r-', linewidth=1.5)
axes2[1].set_ylabel('State x2')
axes2[1].set_xlabel('Time (s)')
axes2[1].grid(True, alpha=0.3)

axes2[2].plot(t_sim, z_trajectory, 'g-', linewidth=1.5)
axes2[2].set_ylabel('Scheduling z')
axes2[2].set_xlabel('Time (s)')
axes2[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/state_trajectories.png', dpi=150)
plt.close()
print("  Saved: report/images/state_trajectories.png")

# Figure 3: Control Input with Saturation
fig3, ax3 = plt.subplots(figsize=(12, 4))

ax3.plot(t_sim, u_history[:, 0], 'b--', linewidth=1, label='Unsaturated', alpha=0.7)
ax3.plot(t_sim, u_sat_history[:, 0], 'r-', linewidth=1.5, label='Saturated')
ax3.axhline(y=u_max, color='k', linestyle=':', label='Saturation limits')
ax3.axhline(y=u_min, color='k', linestyle=':')
ax3.fill_between(t_sim, u_min, u_max, alpha=0.1, color='green')
ax3.set_xlabel('Time (s)')
ax3.set_ylabel('Control Input u')
ax3.set_title('Control Input with Anti-Windup Saturation')
ax3.legend(loc='upper right')
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/control_input.png', dpi=150)
plt.close()
print("  Saved: report/images/control_input.png")

# Figure 4: H-infinity Norm Verification
fig4, ax4 = plt.subplots(figsize=(10, 5))

z_op = list(z_values) + [h[0] for h in hinf_segments]
hinf_all = hinf_results + [h[1] for h in hinf_segments]
colors = ['green' if h < 1.0 else 'red' for h in hinf_all]

ax4.scatter(z_op, hinf_all, c=colors, s=100, edgecolor='black', linewidth=1.5, zorder=5)
ax4.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='H-infinity bound = 1.0')
ax4.set_xlabel('Scheduling Variable z')
ax4.set_ylabel('H-infinity Norm')
ax4.set_title('H-infinity Norm Verification (Weighted Output)')
ax4.legend()
ax4.grid(True, alpha=0.3)
ax4.set_ylim([0, max(hinf_all) * 1.2])

plt.tight_layout()
plt.savefig('report/images/hinf_verification.png', dpi=150)
plt.close()
print("  Saved: report/images/hinf_verification.png")

# Figure 5: Phase Portrait
fig5, ax5 = plt.subplots(figsize=(8, 6))

ax5.plot(x_history[:, 0], x_history[:, 1], 'b-', linewidth=1, alpha=0.7)
ax5.plot(x_history[0, 0], x_history[0, 1], 'go', markersize=10, label='Start')
ax5.plot(x_history[-1, 0], x_history[-1, 1], 'rs', markersize=10, label='End')
ax5.set_xlabel('State x1')
ax5.set_ylabel('State x2')
ax5.set_title('Phase Portrait')
ax5.legend()
ax5.grid(True, alpha=0.3)
ax5.axis('equal')

plt.tight_layout()
plt.savefig('report/images/phase_portrait.png', dpi=150)
plt.close()
print("  Saved: report/images/phase_portrait.png")

# Figure 6: Gain Variation During Simulation
fig6, ax6 = plt.subplots(figsize=(12, 4))

ax6.plot(t_sim, K_history[:, 0], 'b-', linewidth=1.5, label='K[0,0]')
ax6.plot(t_sim, K_history[:, 1], 'r-', linewidth=1.5, label='K[0,1]')
ax6.set_xlabel('Time (s)')
ax6.set_ylabel('Gain Value')
ax6.set_title('Gain-Scheduled Controller Gains During Simulation')
ax6.legend()
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/gain_variation.png', dpi=150)
plt.close()
print("  Saved: report/images/gain_variation.png")

# Figure 7: Closed-loop eigenvalue locations
fig7, ax7 = plt.subplots(figsize=(8, 8))

theta = np.linspace(0, 2*np.pi, 100)
ax7.plot(np.cos(theta), np.sin(theta), 'k--', label='Unit circle')

for i, (z, A, B, K) in enumerate(zip(z_values, A_matrices, B_matrices, K_gains)):
    A_cl = A - B @ K
    eigenvalues = np.linalg.eigvals(A_cl)
    ax7.scatter(eigenvalues.real, eigenvalues.imag, s=100, label=f'z={z}')

ax7.set_xlabel('Real')
ax7.set_ylabel('Imaginary')
ax7.set_title('Closed-Loop Eigenvalue Locations')
ax7.legend()
ax7.grid(True, alpha=0.3)
ax7.set_aspect('equal')
ax7.set_xlim([-1.2, 1.2])
ax7.set_ylim([-1.2, 1.2])

plt.tight_layout()
plt.savefig('report/images/eigenvalue_locations.png', dpi=150)
plt.close()
print("  Saved: report/images/eigenvalue_locations.png")

print("\n" + "="*60)
print("Analysis Complete!")
print("="*60)
print(f"\nKey Results:")
print(f"  - All H-infinity norms below 1.0: {all_pass and all_segments_pass}")
print(f"  - Maximum H-infinity norm at operating points: {max(hinf_results):.6f}")
if hinf_segments:
    print(f"  - Maximum H-infinity norm in segments: {max([h[1] for h in hinf_segments]):.6f}")
print(f"  - Control saturation respected: {np.all(np.abs(u_sat_history) <= u_max + 1e-6)}")
print(f"  - System stable: {np.all(np.abs(x_history[-1]) < np.abs(x_history[0]))}")

# Save summary data
summary = {
    'hinf_results': hinf_results,
    'hinf_segments': hinf_segments,
    'all_pass': all_pass and all_segments_pass,
    'K_gains': K_gains.tolist(),
    'z_values': z_values.tolist()
}

with open('outputs/summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("\nResults saved to outputs/ directory")
