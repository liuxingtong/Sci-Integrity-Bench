import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import control as ct

# Load saved data
K_array = np.load('../outputs/K_matrices.npy')
z_values = np.load('../outputs/z_values.npy')

# Load plant linearizations for simulation
import json
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']
weights = data['weights']

Q = np.array(weights['Q'])
R = np.array(weights['R'])

# Create interpolation functions for gain scheduling
# K has shape (4, 2) - 4 operating points, 2 gain values
K1_interp = interp1d(z_values, K_array[:, 0], kind='linear', fill_value='extrapolate')
K2_interp = interp1d(z_values, K_array[:, 1], kind='linear', fill_value='extrapolate')

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
T_final = 10.0  # seconds
n_steps = int(T_final / dt)
t = np.linspace(0, T_final, n_steps)

# Scheduling parameter trajectory (simulate moving through operating points)
# Create a smooth trajectory that goes through all operating points
z_traj = 1 + 3 * (1 - np.cos(2*np.pi*t/T_final)) / 2  # Oscillates between 1 and 4

# Initial state
x = np.array([[0.5], [-0.3]])  # Initial state

# Reference (setpoint)
x_ref = np.array([[0], [0]])  # Regulate to origin

# Storage for results
x_history = np.zeros((2, n_steps))
u_history = np.zeros(n_steps)
u_sat_history = np.zeros(n_steps)
z_history = np.zeros(n_steps)
K_history = np.zeros((2, n_steps))

# Simple integrator for reference tracking (with anti-windup)
xi = 0.0  # Integrator state
Ki = 0.1  # Integrator gain

# Simulation loop
for i in range(n_steps):
    z = z_traj[i]
    
    # Get plant matrices for current z (simplified - using nearest for simulation)
    # In reality, we would need a nonlinear plant model
    # For simulation, we'll use linear interpolation between A, B matrices
    idx = np.searchsorted(z_values, z) - 1
    idx = max(0, min(len(z_values)-2, idx))
    
    # Linear interpolation of A, B matrices
    z_low = z_values[idx]
    z_high = z_values[idx+1]
    alpha = (z - z_low) / (z_high - z_low)
    
    A_low = np.array(points[idx]['A'])
    B_low = np.array(points[idx]['B'])
    A_high = np.array(points[idx+1]['A'])
    B_high = np.array(points[idx+1]['B'])
    
    A = A_low + alpha * (A_high - A_low)
    B = B_low + alpha * (B_high - B_low)
    
    # Get scheduled gain
    K = get_scheduled_gain(z)
    
    # Error
    e = x_ref - x
    
    # Integrator with anti-windup
    xi += e[0, 0] * dt  # Simple integration
    
    # Control law: u = -Kx + Ki*xi
    u_lqr = -K @ x
    u_int = Ki * xi
    u = u_lqr[0, 0] + u_int
    
    # Apply saturation
    u_sat = saturate(u)
    
    # Anti-windup adjustment
    xi = anti_windup_integrator(xi, u, u_sat, Ki, dt)
    
    # Store results
    x_history[:, i] = x.flatten()
    u_history[i] = u
    u_sat_history[i] = u_sat
    z_history[i] = z
    K_history[:, i] = K.flatten()
    
    # State update (discrete-time)
    x = A @ x + B * u_sat

# Plot results
plt.figure(figsize=(12, 10))

# State trajectories
plt.subplot(3, 2, 1)
plt.plot(t, x_history[0, :], 'b-', label='x1')
plt.plot(t, x_history[1, :], 'r-', label='x2')
plt.xlabel('Time (s)')
plt.ylabel('State')
plt.title('State Trajectories')
plt.legend()
plt.grid(True)

# Control input
plt.subplot(3, 2, 2)
plt.plot(t, u_history, 'g--', label='Commanded u')
plt.plot(t, u_sat_history, 'b-', label='Actual u (saturated)')
plt.axhline(y=0.9, color='r', linestyle=':', label='Saturation limit')
plt.axhline(y=-0.9, color='r', linestyle=':')
plt.xlabel('Time (s)')
plt.ylabel('Control Input')
plt.title('Control Input with Anti-windup')
plt.legend()
plt.grid(True)

# Scheduling parameter
plt.subplot(3, 2, 3)
plt.plot(t, z_history, 'm-')
plt.xlabel('Time (s)')
plt.ylabel('z')
plt.title('Scheduling Parameter Trajectory')
plt.grid(True)

# Scheduled gains
plt.subplot(3, 2, 4)
plt.plot(t, K_history[0, :], 'b-', label='K1')
plt.plot(t, K_history[1, :], 'r-', label='K2')
plt.xlabel('Time (s)')
plt.ylabel('Gain Value')
plt.title('Scheduled LQR Gains')
plt.legend()
plt.grid(True)

# Phase portrait
plt.subplot(3, 2, 5)
plt.plot(x_history[0, :], x_history[1, :], 'b-')
plt.plot(x_history[0, 0], x_history[1, 0], 'go', label='Start')
plt.plot(x_history[0, -1], x_history[1, -1], 'ro', label='End')
plt.xlabel('x1')
plt.ylabel('x2')
plt.title('Phase Portrait')
plt.legend()
plt.grid(True)

# Control effort vs state
plt.subplot(3, 2, 6)
plt.scatter(x_history[0, :], u_sat_history, c=t, cmap='viridis', alpha=0.6)
plt.colorbar(label='Time (s)')
plt.xlabel('x1')
plt.ylabel('Control Input')
plt.title('Control Input vs State x1')
plt.grid(True)

plt.tight_layout()
plt.savefig('../report/images/simulation_results.png', dpi=300, bbox_inches='tight')
plt.show()

print("Simulation completed. Results saved to ../report/images/simulation_results.png")