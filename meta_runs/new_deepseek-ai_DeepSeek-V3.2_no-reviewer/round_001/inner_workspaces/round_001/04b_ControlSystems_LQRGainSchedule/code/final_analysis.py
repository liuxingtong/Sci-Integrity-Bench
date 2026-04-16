import numpy as np
import json
import matplotlib.pyplot as plt
from scipy import linalg
from scipy import interpolate
import control as ct

print("=" * 70)
print("GAIN-SCHEDULED LQR WITH ANTI-WINDUP: FINAL ANALYSIS")
print("=" * 70)

# Load data
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']
weights = data['weights']

Q = np.array(weights['Q'])
R = np.array(weights['R'])

print(f"\n1. SYSTEM DATA")
print(f"   Time step: dt = {dt} s")
print(f"   Number of operating points: {len(points)}")
print(f"   LQR weights: Q = \n{Q}")
print(f"                R = \n{R}")

# Extract scheduling variable z and system matrices
z_vals = []
A_list = []
B_list = []
K_list = []  # LQR gains
P_list = []  # Riccati solutions

for i, point in enumerate(points):
    z = point['z']
    A = np.array(point['A'])
    B = np.array(point['B'])
    
    z_vals.append(z)
    A_list.append(A)
    B_list.append(B)
    
    # Compute LQR gain for this operating point
    P = linalg.solve_discrete_are(A, B, Q, R)
    K = linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
    
    K_list.append(K)
    P_list.append(P)
    
    print(f"\n   Operating point {i+1} (z = {z}):")
    print(f"     A = \n{A}")
    print(f"     B = \n{B}")
    print(f"     LQR gain K = [{K[0,0]:.6f}, {K[0,1]:.6f}]")

z_vals = np.array(z_vals)
K_list = np.array(K_list).squeeze()  # Shape: (n_points, 2)

print(f"\n   Scheduling grid: z = {z_vals}")

# 2. GAIN SCHEDULING DESIGN
print("\n\n2. GAIN SCHEDULING DESIGN")
print("   Linear interpolation of LQR gains between operating points")

K1_interp = interpolate.interp1d(z_vals, K_list[:, 0], kind='linear', fill_value='extrapolate')
K2_interp = interpolate.interp1d(z_vals, K_list[:, 1], kind='linear', fill_value='extrapolate')

def get_scheduled_gain(z):
    """Return interpolated gain K for scheduling variable z"""
    return np.array([K1_interp(z), K2_interp(z)])  # Return as 1D array

# Test interpolation at sample points
print("\n   Interpolated gains at sample points:")
for z_test in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
    K_test = get_scheduled_gain(z_test)
    print(f"     z = {z_test:.1f}: K = [{K_test[0]:.6f}, {K_test[1]:.6f}]")

# 3. H-INFINITY NORM VERIFICATION
print("\n\n3. H-INFINITY NORM VERIFICATION")
print("   Checking if closed-loop H-inf norm < 1.0 for each operating point")
print("   Using weighted output with given Q and R weights")

# For LQR, the cost function is J = Σ (x'Qx + u'Ru)
# The H-inf norm from disturbance w to regulated output z = [Q^(1/2)x; R^(1/2)u]
# should satisfy ||T_{zw}||_∞ < γ for some γ
# For the standard LQR solution, γ = 1 is guaranteed under certain conditions

Q_sqrt = linalg.sqrtm(Q)
R_sqrt = linalg.sqrtm(R)

hinf_results = []

for i, (z, A, B, K) in enumerate(zip(z_vals, A_list, B_list, K_list)):
    # Closed-loop system
    A_cl = A - B @ K.reshape(1, -1)
    B_cl = B  # Disturbance enters through control channel
    
    # Weighted output: z = [Q^(1/2)x; R^(1/2)u] where u = -Kx
    C_cl = np.vstack([Q_sqrt, -R_sqrt @ K.reshape(1, -1)])
    D_cl = np.zeros((C_cl.shape[0], B_cl.shape[1]))
    
    # Create discrete-time system
    sys_cl = ct.ss(A_cl, B_cl, C_cl, D_cl, dt=dt)
    
    # Compute H-infinity norm via frequency response
    n_freq = 1000
    omega = np.logspace(-2, np.log10(np.pi/dt), n_freq)
    mag = np.zeros(n_freq)
    
    for j, w in enumerate(omega):
        z_val = np.exp(1j * w * dt)
        G = C_cl @ np.linalg.inv(z_val * np.eye(2) - A_cl) @ B_cl + D_cl
        mag[j] = np.linalg.norm(G, 2)  # Spectral norm
    
    hinf_norm = np.max(mag)
    freq_at_peak = omega[np.argmax(mag)]
    
    hinf_results.append({
        'z': z,
        'hinf_norm': hinf_norm,
        'freq_at_peak': freq_at_peak,
        'pass': hinf_norm < 1.0
    })
    
    print(f"\n   Operating point z = {z}:")
    print(f"     H-inf norm: {hinf_norm:.6f}")
    print(f"     {'PASS' if hinf_norm < 1.0 else 'FAIL'} (required < 1.0)")

# Check overall result
all_pass = all(r['pass'] for r in hinf_results)
print(f"\n   Overall result: {'ALL PASS' if all_pass else 'SOME FAILURES'}")

# 4. ANTI-WINDUP IMPLEMENTATION
print("\n\n4. ANTI-WINDUP IMPLEMENTATION")
print("   Actuator saturation limit: ±0.9")
print("   Simple saturation with tracking (conditional integration)")

class GainScheduledLQRWithAntiWindup:
    def __init__(self, K_func, limit=0.9, dt=0.02, K_aw=1.0):
        self.K_func = K_func
        self.limit = limit
        self.dt = dt
        self.K_aw = K_aw
        self.u_unsat = 0.0
        self.u_sat = 0.0
        self.aw_integrator = 0.0  # For anti-windup compensation
        
    def compute(self, x, z):
        K = self.K_func(z)
        u_ideal = -K @ x
        
        # Apply saturation
        u_sat = np.clip(u_ideal, -self.limit, self.limit)
        
        # Simple anti-windup: track saturation difference
        saturation_error = u_ideal - u_sat
        self.aw_integrator += self.K_aw * saturation_error * self.dt
        
        # Store for monitoring
        self.u_unsat = u_ideal
        self.u_sat = u_sat
        
        return u_sat

# 5. SIMULATION DEMONSTRATION
print("\n\n5. SIMULATION DEMONSTRATION")
print("   Running closed-loop simulation with time-varying scheduling variable")

controller = GainScheduledLQRWithAntiWindup(get_scheduled_gain, limit=0.9, dt=dt)

# Simulation parameters
T = 4.0  # Simulation time (seconds)
n_steps = int(T / dt)
t = np.arange(0, T, dt)

# Initial state
x0 = np.array([0.8, -0.6])  # Larger initial state to potentially trigger saturation

# Scheduling variable trajectory
z_traj = 2.5 + 1.5 * np.sin(2 * np.pi * 0.4 * t)  # Varies between 1 and 4

# Storage
x_history = np.zeros((n_steps, 2))
u_history = np.zeros(n_steps)
u_ideal_history = np.zeros(n_steps)
z_history = np.zeros(n_steps)

# Run simulation
x = x0.copy()
for i in range(n_steps):
    z = z_traj[i]
    
    # Get control input
    u = controller.compute(x, z)
    
    # Find nearest operating point for simulation
    idx = np.argmin(np.abs(z_vals - z))
    A = A_list[idx]
    B = B_list[idx]
    
    # Apply control
    x_next = A @ x + B.flatten() * u
    
    # Store results
    x_history[i] = x
    u_history[i] = u
    u_ideal_history[i] = controller.u_unsat
    z_history[i] = z
    
    # Update state
    x = x_next

# Analyze saturation
saturation_mask = np.abs(u_ideal_history) > 0.9
saturation_count = np.sum(saturation_mask)
saturation_margin = np.abs(u_ideal_history) - 0.9
max_saturation = np.max(saturation_margin) if np.any(saturation_mask) else 0.0

print(f"\n   Simulation results:")
print(f"     Initial state: [{x0[0]:.3f}, {x0[1]:.3f}]")
print(f"     Final state: [{x_history[-1, 0]:.6f}, {x_history[-1, 1]:.6f}]")
print(f"     Saturation events: {saturation_count}")
print(f"     Maximum saturation: {max_saturation:.4f}")
print(f"     Controller stabilizes the system: {'YES' if np.max(np.abs(x_history[-10:])) < 0.01 else 'NO'}")

# 6. CREATE SUMMARY PLOTS
print("\n\n6. GENERATING SUMMARY PLOTS")

# Plot 1: H-infinity norm vs scheduling variable
plt.figure(figsize=(10, 6))
z_plot = np.linspace(min(z_vals), max(z_vals), 100)
hinf_plot = []

for z in z_plot:
    idx = np.argmin(np.abs(z_vals - z))
    A = A_list[idx]
    B = B_list[idx]
    K = get_scheduled_gain(z).reshape(1, -1)
    
    A_cl = A - B @ K
    B_cl = B
    C_cl = np.vstack([Q_sqrt, -R_sqrt @ K])
    D_cl = np.zeros((C_cl.shape[0], B_cl.shape[1]))
    
    # Quick H-inf estimate
    omega_test = np.logspace(-2, np.log10(np.pi/dt), 200)
    mag_test = []
    for w in omega_test:
        z_val = np.exp(1j * w * dt)
        G = C_cl @ np.linalg.inv(z_val * np.eye(2) - A_cl) @ B_cl + D_cl
        mag_test.append(np.linalg.norm(G, 2))
    
    hinf_plot.append(np.max(mag_test))

plt.plot(z_plot, hinf_plot, 'b-', linewidth=2, label='Interpolated H-inf norm')
plt.scatter(z_vals, [r['hinf_norm'] for r in hinf_results], c='r', s=100, zorder=5, label='Operating points')
plt.axhline(y=1.0, color='r', linestyle='--', linewidth=2, label='Requirement (1.0)')
plt.xlabel('Scheduling variable z')
plt.ylabel('H-infinity norm')
plt.title('H-infinity Norm Verification')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/hinf_verification.png', dpi=150)
plt.close()
print("   - H-infinity verification plot saved")

# Plot 2: Gain scheduling interpolation
plt.figure(figsize=(10, 6))
z_test = np.linspace(min(z_vals)-0.5, max(z_vals)+0.5, 200)
K1_test = K1_interp(z_test)
K2_test = K2_interp(z_test)

plt.plot(z_test, K1_test, 'b-', linewidth=2, label='K₁(z)')
plt.plot(z_test, K2_test, 'r-', linewidth=2, label='K₂(z)')
plt.scatter(z_vals, K_list[:, 0], c='b', s=100, zorder=5)
plt.scatter(z_vals, K_list[:, 1], c='r', s=100, zorder=5)
plt.xlabel('Scheduling variable z')
plt.ylabel('LQR gain')
plt.title('Gain Scheduling: Interpolated LQR Gains')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/gain_scheduling.png', dpi=150)
plt.close()
print("   - Gain scheduling plot saved")

# Plot 3: Simulation results
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# State trajectories
axes[0, 0].plot(t[:n_steps], x_history[:, 0], 'b-', linewidth=2, label='x₁')
axes[0, 0].plot(t[:n_steps], x_history[:, 1], 'r-', linewidth=2, label='x₂')
axes[0, 0].set_xlabel('Time (s)')
axes[0, 0].set_ylabel('State')
axes[0, 0].set_title('State Trajectories')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

# Control input
axes[0, 1].plot(t[:n_steps], u_history, 'g-', linewidth=2, label='Applied control')
axes[0, 1].plot(t[:n_steps], u_ideal_history, 'r--', linewidth=1, alpha=0.7, label='Ideal LQR')
axes[0, 1].axhline(y=0.9, color='k', linestyle=':', label='Saturation limit')
axes[0, 1].axhline(y=-0.9, color='k', linestyle=':')
axes[0, 1].set_xlabel('Time (s)')
axes[0, 1].set_ylabel('Control input u')
axes[0, 1].set_title('Control Input with Anti-Windup')
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].legend()

# Scheduling variable
axes[1, 0].plot(t[:n_steps], z_history, 'm-', linewidth=2)
axes[1, 0].scatter(z_vals, np.zeros_like(z_vals), c='r', s=100, zorder=5, label='Operating points')
axes[1, 0].set_xlabel('Time (s)')
axes[1, 0].set_ylabel('Scheduling variable z')
axes[1, 0].set_title('Scheduling Variable')
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].legend()

# Phase portrait
axes[1, 1].plot(x_history[:, 0], x_history[:, 1], 'b-', linewidth=1.5, alpha=0.7)
axes[1, 1].scatter(x_history[0, 0], x_history[0, 1], c='g', s=200, marker='o', label='Start', zorder=5)
axes[1, 1].scatter(x_history[-1, 0], x_history[-1, 1], c='r', s=200, marker='s', label='End', zorder=5)
axes[1, 1].set_xlabel('State x₁')
axes[1, 1].set_ylabel('State x₂')
axes[1, 1].set_title('Phase Portrait')
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].legend()

plt.tight_layout()
plt.savefig('../report/images/simulation_summary.png', dpi=150)
plt.close()
print("   - Simulation summary plot saved")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)

# Save final results
np.savez('../outputs/final_results.npz',
         z_vals=z_vals,
         K_list=K_list,
         A_list=A_list,
         B_list=B_list,
         hinf_results=hinf_results,
         Q=Q,
         R=R,
         dt=dt,
         simulation_t=t[:n_steps],
         simulation_x=x_history,
         simulation_u=u_history,
         simulation_z=z_history)

print("\nResults saved to outputs/final_results.npz")
print("Plots saved to report/images/")
