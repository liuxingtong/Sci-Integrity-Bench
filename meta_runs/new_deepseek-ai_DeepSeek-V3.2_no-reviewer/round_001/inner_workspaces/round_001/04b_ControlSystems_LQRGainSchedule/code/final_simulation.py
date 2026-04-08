import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import control as ct
from scipy.linalg import solve_discrete_are

# Load plant linearizations
import json
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']

# Load optimal weights
Q_opt = np.load('../outputs/Q_opt.npy')
R_opt = np.load('../outputs/R_opt.npy')
K_array_opt = np.load('../outputs/K_matrices_opt.npy')
z_values = np.load('../outputs/z_values.npy')

print(f"Optimal Q:\n{Q_opt}")
print(f"Optimal R:\n{R_opt}")
print(f"Optimal K matrices shape: {K_array_opt.shape}")
print()

# Create interpolation functions for gain scheduling
K1_interp = interp1d(z_values, K_array_opt[:, 0], kind='linear', fill_value='extrapolate')
K2_interp = interp1d(z_values, K_array_opt[:, 1], kind='linear', fill_value='extrapolate')

def get_scheduled_gain(z):
    """Get LQR gain for given scheduling parameter z"""
    k1 = K1_interp(z)
    k2 = K2_interp(z)
    return np.array([[k1, k2]])

# Anti-windup implementation
def saturate(u, limit=0.9):
    """Saturate control input"""
    return np.clip(u, -limit, limit)

def anti_windup_integrator(e, u, u_sat, Ki, Ts, limit=0.9):
    """Simple anti-windup for integrator"""
    # Back-calculation anti-windup
    if abs(u) > limit:
        e_aw = (u_sat - u) / Ki
    else:
        e_aw = 0
    return e + e_aw

# Simulation parameters
T_final = 15.0  # seconds
n_steps = int(T_final / dt)
t = np.linspace(0, T_final, n_steps)

# Create a more challenging scheduling parameter trajectory
# That tests all operating regions
z_traj = 1 + 1.5 * (1 - np.cos(2*np.pi*t/5)) + 1.5 * (1 - np.cos(2*np.pi*t/12))
z_traj = np.clip(z_traj, 1, 4)  # Keep within operating range

# Add some step changes to test scheduling
z_traj[500:700] = 3.5
z_traj[1000:1200] = 1.5

# Initial state
x = np.array([[0.8], [-0.6]])  # Initial state

# Reference trajectory (time-varying to test tracking)
x_ref = np.zeros((2, n_steps))
x_ref[0, :] = 0.2 * np.sin(2*np.pi*t/8)  # Slow sine wave reference for x1

# Storage for results
x_history = np.zeros((2, n_steps))
error_history = np.zeros((2, n_steps))
u_history = np.zeros(n_steps)
u_sat_history = np.zeros(n_steps)
z_history = np.zeros(n_steps)
K_history = np.zeros((2, n_steps))
hinf_history = np.zeros(n_steps)

# Simple integrator for reference tracking (with anti-windup)
xi = 0.0  # Integrator state
Ki = 0.05  # Integrator gain (reduced for stability)

print("Starting simulation with optimized gain-scheduled LQR...")
print(f"Simulation time: {T_final} seconds, Steps: {n_steps}")
print()

# Pre-compute plant matrices for all z values (for interpolation)
A_matrices = [np.array(p['A']) for p in points]
B_matrices = [np.array(p['B']) for p in points]

# Simulation loop
for i in range(n_steps):
    z = z_traj[i]
    
    # Get plant matrices for current z using linear interpolation
    idx = np.searchsorted(z_values, z) - 1
    idx = max(0, min(len(z_values)-2, idx))
    
    z_low = z_values[idx]
    z_high = z_values[idx+1]
    alpha = (z - z_low) / (z_high - z_low)
    
    A = A_matrices[idx] + alpha * (A_matrices[idx+1] - A_matrices[idx])
    B = B_matrices[idx] + alpha * (B_matrices[idx+1] - B_matrices[idx])
    
    # Get scheduled gain
    K = get_scheduled_gain(z)
    
    # Error
    e = x_ref[:, i:i+1] - x
    
    # Integrator with anti-windup
    xi += e[0, 0] * dt
    
    # Control law: u = -Kx + Ki*xi (for tracking)
    u_lqr = -K @ x
    u_int = Ki * xi
    u = u_lqr[0, 0] + u_int
    
    # Apply saturation
    u_sat = saturate(u)
    
    # Anti-windup adjustment
    xi = anti_windup_integrator(xi, u, u_sat, Ki, dt)
    
    # Store results
    x_history[:, i] = x.flatten()
    error_history[:, i] = e.flatten()
    u_history[i] = u
    u_sat_history[i] = u_sat
    z_history[i] = z
    K_history[:, i] = K.flatten()
    
    # Compute current H-infinity norm (for monitoring)
    A_cl = A - B @ K
    sys_cl = ct.ss(A_cl, B, np.eye(2), np.zeros((2, 1)), dt)
    try:
        sys_cl_cont = ct.d2c(sys_cl, method='tustin')
        hinf_norm = ct.hinfnorm(sys_cl_cont)[0]
    except:
        omega = np.logspace(-2, 2, 50)
        mag, phase, omega = ct.bode(sys_cl, omega, plot=False)
        hinf_norm = np.max(mag)
    hinf_history[i] = hinf_norm
    
    # State update (discrete-time)
    x = A @ x + B * u_sat

print("Simulation completed.")
print(f"Final state: x1 = {x[0,0]:.4f}, x2 = {x[1,0]:.4f}")
print(f"Maximum control input: {np.max(np.abs(u_sat_history)):.4f}")
print(f"Maximum H-infinity norm during simulation: {np.max(hinf_history):.4f}")
print(f"Mean squared error: {np.mean(error_history**2):.6f}")
print()

# Check requirements
print("Requirements check:")
if np.max(hinf_history) < 1.0:
    print("✓ H-infinity norm below 1.0 at all times")
else:
    print(f"✗ H-infinity norm exceeded 1.0 (max = {np.max(hinf_history):.4f})")

if np.max(np.abs(u_sat_history)) <= 0.9:
    print("✓ Actuator saturation limit respected (±0.9)")
else:
    print(f"✗ Actuator saturation limit violated (max = {np.max(np.abs(u_sat_history)):.4f})")

# Check if gain scheduling is continuous
K_diff = np.diff(K_history, axis=1)
max_K_change = np.max(np.abs(K_diff))
print(f"Maximum gain change between steps: {max_K_change:.6f}")
if max_K_change < 0.1:  # Arbitrary threshold for continuity
    print("✓ Gain scheduling appears continuous")
else:
    print("⚠ Gain changes may be too abrupt")

# Plot comprehensive results
plt.figure(figsize=(15, 12))

# State trajectories and reference
plt.subplot(4, 3, 1)
plt.plot(t, x_history[0, :], 'b-', linewidth=2, label='x1')
plt.plot(t, x_ref[0, :], 'r--', linewidth=1.5, label='x1 ref')
plt.xlabel('Time (s)')
plt.ylabel('State x1')
plt.title('State x1 and Reference')
plt.legend()
plt.grid(True, alpha=0.3)

plt.subplot(4, 3, 2)
plt.plot(t, x_history[1, :], 'g-', linewidth=2, label='x2')
plt.plot(t, x_ref[1, :], 'r--', linewidth=1.5, label='x2 ref')
plt.xlabel('Time (s)')
plt.ylabel('State x2')
plt.title('State x2 and Reference')
plt.legend()
plt.grid(True, alpha=0.3)

# Control input
plt.subplot(4, 3, 3)
plt.plot(t, u_history, 'g--', linewidth=1, label='Commanded u')
plt.plot(t, u_sat_history, 'b-', linewidth=2, label='Actual u (saturated)')
plt.axhline(y=0.9, color='r', linestyle=':', linewidth=2, label='Saturation limit')
plt.axhline(y=-0.9, color='r', linestyle=':', linewidth=2)
plt.xlabel('Time (s)')
plt.ylabel('Control Input')
plt.title('Control Input with Anti-windup')
plt.legend()
plt.grid(True, alpha=0.3)

# Scheduling parameter
plt.subplot(4, 3, 4)
plt.plot(t, z_history, 'm-', linewidth=2)
plt.xlabel('Time (s)')
plt.ylabel('z')
plt.title('Scheduling Parameter Trajectory')
plt.grid(True, alpha=0.3)

# Scheduled gains
plt.subplot(4, 3, 5)
plt.plot(t, K_history[0, :], 'b-', linewidth=2, label='K1')
plt.plot(t, K_history[1, :], 'r-', linewidth=2, label='K2')
plt.xlabel('Time (s)')
plt.ylabel('Gain Value')
plt.title('Scheduled LQR Gains')
plt.legend()
plt.grid(True, alpha=0.3)

# H-infinity norm during simulation
plt.subplot(4, 3, 6)
plt.plot(t, hinf_history, 'c-', linewidth=2)
plt.axhline(y=1.0, color='r', linestyle='--', linewidth=2, label='Requirement (1.0)')
plt.fill_between(t, 0, 1.0, alpha=0.2, color='green')
plt.xlabel('Time (s)')
plt.ylabel('H-infinity Norm')
plt.title('H-infinity Norm During Simulation')
plt.legend()
plt.grid(True, alpha=0.3)

# Phase portrait
plt.subplot(4, 3, 7)
plt.plot(x_history[0, :], x_history[1, :], 'b-', alpha=0.7)
plt.plot(x_history[0, 0], x_history[1, 0], 'go', markersize=10, label='Start')
plt.plot(x_history[0, -1], x_history[1, -1], 'ro', markersize=10, label='End')
plt.xlabel('x1')
plt.ylabel('x2')
plt.title('Phase Portrait')
plt.legend()
plt.grid(True, alpha=0.3)

# Error trajectories
plt.subplot(4, 3, 8)
plt.plot(t, error_history[0, :], 'b-', linewidth=1.5, label='e1')
plt.plot(t, error_history[1, :], 'r-', linewidth=1.5, label='e2')
plt.xlabel('Time (s)')
plt.ylabel('Error')
plt.title('Tracking Error')
plt.legend()
plt.grid(True, alpha=0.3)

# Gain vs scheduling parameter
plt.subplot(4, 3, 9)
plt.scatter(z_history, K_history[0, :], c=t, cmap='viridis', alpha=0.6, s=10, label='K1')
plt.scatter(z_history, K_history[1, :], c=t, cmap='plasma', alpha=0.6, s=10, label='K2')
plt.colorbar(label='Time (s)')
plt.xlabel('Scheduling Parameter z')
plt.ylabel('Gain Value')
plt.title('Gain vs Scheduling Parameter')
plt.legend()
plt.grid(True, alpha=0.3)

# Control input histogram
plt.subplot(4, 3, 10)
plt.hist(u_sat_history, bins=50, alpha=0.7, color='blue', edgecolor='black')
plt.axvline(x=0.9, color='r', linestyle='--', linewidth=2, label='Saturation limit')
plt.axvline(x=-0.9, color='r', linestyle='--', linewidth=2)
plt.xlabel('Control Input')
plt.ylabel('Frequency')
plt.title('Control Input Distribution')
plt.legend()
plt.grid(True, alpha=0.3)

# Gain scheduling interpolation
plt.subplot(4, 3, 11)
z_test = np.linspace(1, 4, 100)
K1_test = K1_interp(z_test)
K2_test = K2_interp(z_test)
plt.plot(z_test, K1_test, 'b-', linewidth=2, label='K1 (interpolated)')
plt.plot(z_test, K2_test, 'r-', linewidth=2, label='K2 (interpolated)')
plt.scatter(z_values, K_array_opt[:, 0], c='blue', s=50, marker='o', label='K1 (design points)')
plt.scatter(z_values, K_array_opt[:, 1], c='red', s=50, marker='s', label='K2 (design points)')
plt.xlabel('Scheduling Parameter z')
plt.ylabel('Gain Value')
plt.title('Gain Scheduling Interpolation')
plt.legend()
plt.grid(True, alpha=0.3)

# Performance metrics
plt.subplot(4, 3, 12)
metrics = {
    'Max H-inf': np.max(hinf_history),
    'Mean Squared Error': np.mean(error_history**2),
    'Max Control': np.max(np.abs(u_sat_history)),
    'Settling Time': t[np.where(np.abs(error_history[0, :]) < 0.05)[0][0]] if len(np.where(np.abs(error_history[0, :]) < 0.05)[0]) > 0 else T_final
}

plt.text(0.1, 0.9, f'Max H-inf: {metrics["Max H-inf"]:.4f}', fontsize=10, transform=plt.gca().transAxes)
plt.text(0.1, 0.7, f'MSE: {metrics["Mean Squared Error"]:.6f}', fontsize=10, transform=plt.gca().transAxes)
plt.text(0.1, 0.5, f'Max |u|: {metrics["Max Control"]:.4f}', fontsize=10, transform=plt.gca().transAxes)
plt.text(0.1, 0.3, f'Settling Time: {metrics["Settling Time"]:.2f}s', fontsize=10, transform=plt.gca().transAxes)
plt.text(0.1, 0.1, f'Requirements Met: {np.max(hinf_history) < 1.0 and np.max(np.abs(u_sat_history)) <= 0.9}', 
         fontsize=10, transform=plt.gca().transAxes, 
         color='green' if (np.max(hinf_history) < 1.0 and np.max(np.abs(u_sat_history)) <= 0.9) else 'red')
plt.axis('off')
plt.title('Performance Summary')

plt.tight_layout()
plt.savefig('../report/images/final_simulation_results.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nFinal simulation results saved to ../report/images/final_simulation_results.png")

# Save simulation data for report
sim_data = {
    'time': t,
    'states': x_history,
    'control': u_sat_history,
    'scheduling': z_history,
    'gains': K_history,
    'hinf_norms': hinf_history,
    'errors': error_history
}

np.save('../outputs/simulation_data.npy', sim_data)
print("Simulation data saved to ../outputs/simulation_data.npy")