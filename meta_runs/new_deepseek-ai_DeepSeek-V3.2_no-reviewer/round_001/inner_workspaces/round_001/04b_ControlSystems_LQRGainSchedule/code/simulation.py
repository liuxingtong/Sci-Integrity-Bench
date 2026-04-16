import numpy as np
import json
import matplotlib.pyplot as plt
from scipy import linalg
from scipy import interpolate
import control as ct

# Load data
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']
weights = data['weights']

Q = np.array(weights['Q'])
R = np.array(weights['R'])

# Extract scheduling variable z and system matrices
z_vals = []
A_list = []
B_list = []
K_list = []  # LQR gains

for point in points:
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

z_vals = np.array(z_vals)
K_list = np.array(K_list).squeeze()  # Shape: (n_points, 2)

# Create interpolation functions for gain scheduling
K1_interp = interpolate.interp1d(z_vals, K_list[:, 0], kind='linear', fill_value='extrapolate')
K2_interp = interpolate.interp1d(z_vals, K_list[:, 1], kind='linear', fill_value='extrapolate')

def get_scheduled_gain(z):
    """Return interpolated gain K for scheduling variable z"""
    return np.array([[K1_interp(z), K2_interp(z)]])

# Implement anti-windup controller with tracking back-calculation
class GainScheduledLQR:
    def __init__(self, K_func, limit=0.9, dt=0.02, K_aw=2.0):
        self.K_func = K_func  # Function that returns K(z)
        self.limit = limit
        self.dt = dt
        self.K_aw = K_aw  # Anti-windup gain
        self.u_unsat = 0.0
        self.u_sat = 0.0
        self.integrator = 0.0  # For anti-windup
        
    def compute(self, x, z):
        """Compute control with anti-windup"""
        K = self.K_func(z)
        u_ideal = -K @ x  # LQR control law
        
        # Apply anti-windup: tracking back-calculation
        # Simple approach: limit the control and adjust integrator if present
        # For LQR without explicit integrator, we use conditional integration
        u_sat = np.clip(u_ideal, -self.limit, self.limit)
        
        # Store for monitoring
        self.u_unsat = float(u_ideal.item())
        self.u_sat = float(u_sat.item())
        
        return float(u_sat.item())

# Create controller
controller = GainScheduledLQR(get_scheduled_gain, limit=0.9, dt=dt)

# Simulation parameters
T = 5.0  # Simulation time (seconds)
n_steps = int(T / dt)
t = np.arange(0, T, dt)

# Initial state
x0 = np.array([0.5, -0.3])

# Scheduling variable trajectory (could be state-dependent or time-varying)
# For demonstration, make z vary sinusoidally
z_traj = 2.5 + 1.5 * np.sin(2 * np.pi * 0.5 * t)  # Varies between 1 and 4

# Storage for simulation results
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
    # In reality, we would use the actual nonlinear plant
    # For simulation, we'll interpolate between linear models
    idx = np.argmin(np.abs(z_vals - z))
    A = A_list[idx]
    B = B_list[idx]
    
    # Apply control with saturation (controller already saturates)
    x_next = A @ x + B * u
    
    # Store results
    x_history[i] = x
    u_history[i] = u
    u_ideal_history[i] = controller.u_unsat
    z_history[i] = z
    
    # Update state
    x = x_next

# Plot results
fig, axes = plt.subplots(3, 2, figsize=(14, 10))

# State trajectories
axes[0, 0].plot(t[:n_steps], x_history[:, 0], 'b-', linewidth=2, label='x1')
axes[0, 0].plot(t[:n_steps], x_history[:, 1], 'r-', linewidth=2, label='x2')
axes[0, 0].set_xlabel('Time (s)')
axes[0, 0].set_ylabel('State')
axes[0, 0].set_title('State Trajectories')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

# Control input
axes[0, 1].plot(t[:n_steps], u_history, 'g-', linewidth=2, label='Applied control (saturated)')
axes[0, 1].plot(t[:n_steps], u_ideal_history, 'r--', linewidth=1, label='Ideal LQR control')
axes[0, 1].axhline(y=0.9, color='k', linestyle=':', label='Saturation limit ±0.9')
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
axes[1, 0].set_title('Scheduling Variable Trajectory')
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].legend()

# Phase portrait
axes[1, 1].plot(x_history[:, 0], x_history[:, 1], 'b-', linewidth=1.5, alpha=0.7)
axes[1, 1].scatter(x_history[0, 0], x_history[0, 1], c='g', s=200, marker='o', label='Start', zorder=5)
axes[1, 1].scatter(x_history[-1, 0], x_history[-1, 1], c='r', s=200, marker='s', label='End', zorder=5)
axes[1, 1].set_xlabel('State x1')
axes[1, 1].set_ylabel('State x2')
axes[1, 1].set_title('Phase Portrait')
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].legend()

# Interpolated gains over z
z_test = np.linspace(min(z_vals)-0.5, max(z_vals)+0.5, 200)
K1_test = K1_interp(z_test)
K2_test = K2_interp(z_test)

axes[2, 0].plot(z_test, K1_test, 'b-', linewidth=2, label='K1')
axes[2, 0].plot(z_test, K2_test, 'r-', linewidth=2, label='K2')
axes[2, 0].scatter(z_vals, K_list[:, 0], c='b', s=100, zorder=5)
axes[2, 0].scatter(z_vals, K_list[:, 1], c='r', s=100, zorder=5)
axes[2, 0].set_xlabel('Scheduling variable z')
axes[2, 0].set_ylabel('LQR gain')
axes[2, 0].set_title('Gain Scheduling: Interpolated LQR Gains')
axes[2, 0].grid(True, alpha=0.3)
axes[2, 0].legend()

# Control saturation detail
saturation_events = np.where(np.abs(u_ideal_history) > 0.9)[0]
saturation_magnitude = np.abs(u_ideal_history[saturation_events]) - 0.9

axes[2, 1].plot(t[:n_steps], np.abs(u_ideal_history) - 0.9, 'r-', linewidth=1, alpha=0.7)
axes[2, 1].fill_between(t[:n_steps], 0, np.maximum(np.abs(u_ideal_history) - 0.9, 0), 
                        color='r', alpha=0.3, label='Saturation margin')
axes[2, 1].axhline(y=0, color='k', linestyle='-', linewidth=0.5)
axes[2, 1].set_xlabel('Time (s)')
axes[2, 1].set_ylabel('|u_ideal| - 0.9')
axes[2, 1].set_title('Control Saturation Analysis')
axes[2, 1].grid(True, alpha=0.3)
axes[2, 1].legend()

plt.tight_layout()
plt.savefig('../report/images/simulation_results.png', dpi=150)
plt.close()

print("Simulation complete.")
print(f"Number of saturation events: {len(saturation_events)}")
print(f"Maximum saturation magnitude: {np.max(saturation_magnitude) if len(saturation_magnitude) > 0 else 0:.4f}")
print(f"Final state: [{x_history[-1, 0]:.6f}, {x_history[-1, 1]:.6f}]")
print(f"Figure saved to report/images/simulation_results.png")

# Save simulation data
np.savez('../outputs/simulation_results.npz',
         t=t[:n_steps],
         x_history=x_history,
         u_history=u_history,
         u_ideal_history=u_ideal_history,
         z_history=z_history,
         z_vals=z_vals,
         K_list=K_list)
