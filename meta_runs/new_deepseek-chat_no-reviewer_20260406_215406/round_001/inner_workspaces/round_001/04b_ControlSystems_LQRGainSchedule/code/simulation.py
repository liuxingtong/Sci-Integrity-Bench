import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import solve_discrete_are
import control as ct
from scipy import interpolate
import pickle

# Load plant linearizations
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']

# Extract operating points
z_values = np.array([p['z'] for p in points])
A_matrices = [np.array(p['A']) for p in points]
B_matrices = [np.array(p['B']) for p in points]

# Load tuned weights
Q_tuned = np.load('../outputs/Q_tuned.npy')
R_tuned = np.load('../outputs/R_tuned.npy')

print(f"Using tuned weights:")
print(f"Q = \n{Q_tuned}")
print(f"R = \n{R_tuned}")

# Function to compute discrete-time LQR gain
def dlqr(A, B, Q, R):
    """Solve the discrete-time LQR controller."""
    P = solve_discrete_are(A, B, Q, R)
    K = np.linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
    return K

# Compute LQR gains with tuned weights
K_gains_tuned = []
for i, (A, B) in enumerate(zip(A_matrices, B_matrices)):
    K = dlqr(A, B, Q_tuned, R_tuned)
    K_gains_tuned.append(K.flatten())

K_gains_tuned = np.array(K_gains_tuned)

# Create interpolation functions for gain scheduling
K1_interp = interpolate.interp1d(z_values, K_gains_tuned[:, 0], kind='linear', fill_value='extrapolate')
K2_interp = interpolate.interp1d(z_values, K_gains_tuned[:, 1], kind='linear', fill_value='extrapolate')

def get_interpolated_gain(z):
    """Return interpolated LQR gain for given z."""
    k1 = K1_interp(z)
    k2 = K2_interp(z)
    return np.array([[k1, k2]])

# Anti-windup saturation limits
U_MIN = -0.9
U_MAX = 0.9

def saturate(u):
    """Apply actuator saturation."""
    return np.clip(u, U_MIN, U_MAX)

# Anti-windup: conditional integration or back-calculation
# We'll use a simple back-calculation method
def anti_windup(u_unsaturated, u_saturated, K, dt, windup_gain=1.0):
    """
    Simple anti-windup compensation.
    Returns adjustment to add to controller state.
    """
    # Difference between commanded and actual control
    error = u_saturated - u_unsaturated
    
    # Back-calculation: adjust integral-like terms
    # For LQR (state feedback), we can adjust a virtual integrator
    # or use a simple correction factor
    correction = windup_gain * error * dt
    return correction

# Simulation of gain-scheduled LQR with anti-windup
def simulate_gain_scheduled_lqr(z_trajectory, x0, reference, T_sim, windup_enabled=True):
    """
    Simulate gain-scheduled LQR controller.
    
    Parameters:
    - z_trajectory: function z(t) returning operating point
    - x0: initial state [2x1]
    - reference: reference state to track [2x1]
    - T_sim: simulation time (seconds)
    - windup_enabled: whether to use anti-windup
    
    Returns:
    - t: time vector
    - x: state history
    - u: control history
    - u_sat: saturated control history
    - z_vals: operating point history
    """
    n_steps = int(T_sim / dt)
    t = np.arange(0, T_sim, dt)
    
    # Initialize arrays
    x = np.zeros((n_steps, 2))
    u = np.zeros(n_steps)
    u_sat = np.zeros(n_steps)
    z_vals = np.zeros(n_steps)
    K_history = np.zeros((n_steps, 2))
    
    # Initial state
    x[0] = x0.flatten()
    
    # Anti-windup state (integral of saturation error)
    aw_state = 0.0
    
    for k in range(n_steps - 1):
        # Current operating point
        z = z_trajectory(t[k])
        z_vals[k] = z
        
        # Get interpolated gain
        K = get_interpolated_gain(z)
        K_history[k] = K.flatten()
        
        # State error
        x_err = x[k] - reference.flatten()
        
        # Compute control signal
        u_unsat = -K @ x_err  # Negative feedback
        
        # Apply anti-windup correction if enabled
        if windup_enabled and k > 0:
            # Simple back-calculation
            sat_error = u_sat[k-1] - u[k-1]
            aw_state += 0.1 * sat_error * dt  # Integrate saturation error
            u_unsat += aw_state  # Add correction
        
        u[k] = u_unsat[0]
        
        # Apply saturation
        u_sat[k] = saturate(u[k])
        
        # Determine which plant model to use based on z
        # Find nearest operating point for simulation
        idx = np.argmin(np.abs(z_values - z))
        A = A_matrices[idx]
        B = B_matrices[idx]
        
        # State update (discrete-time)
        # Convert x[k] to column vector for matrix multiplication
        x_k_col = x[k].reshape(-1, 1)
        x_next = A @ x_k_col + B * u_sat[k]
        # Ensure we have a 1D array of length 2
        x_next_flat = np.squeeze(x_next)
        x[k+1] = x_next_flat
    
    # Last time step
    z_vals[-1] = z_trajectory(t[-1])
    K = get_interpolated_gain(z_vals[-1])
    K_history[-1] = K.flatten()
    x_err = x[-1] - reference.flatten()
    u[-1] = (-K @ x_err)[0]
    u_sat[-1] = saturate(u[-1])
    
    return t, x, u, u_sat, z_vals, K_history

# Test scenarios
print("\n" + "=" * 60)
print("SIMULATION SCENARIOS")
print("=" * 60)

# Scenario 1: Constant operating point z=2.5
print("\nScenario 1: Constant operating point z=2.5")
z_traj1 = lambda t: 2.5
x0_1 = np.array([[0.5], [-0.3]])  # Initial state
ref_1 = np.array([[0], [0]])  # Regulate to origin

# Scenario 2: Ramping operating point z from 1 to 4
print("Scenario 2: Ramping operating point z from 1 to 4")
z_traj2 = lambda t: 1.0 + 3.0 * min(t/10.0, 1.0)  # Ramp over 10 seconds
x0_2 = np.array([[0.2], [0.1]])
ref_2 = np.array([[0], [0]])

# Scenario 3: Sinusoidal operating point variation
print("Scenario 3: Sinusoidal operating point variation")
z_traj3 = lambda t: 2.5 + 1.5 * np.sin(0.5 * t)
x0_3 = np.array([[-0.4], [0.3]])
ref_3 = np.array([[0], [0]])

# Run simulations
T_sim = 15.0  # seconds

print(f"\nRunning simulations for {T_sim} seconds...")

# Run all scenarios
scenarios = [
    ("Constant z=2.5", z_traj1, x0_1, ref_1),
    ("Ramping z 1→4", z_traj2, x0_2, ref_2),
    ("Sinusoidal z", z_traj3, x0_3, ref_3)
]

results = {}
for name, z_traj, x0, ref in scenarios:
    print(f"  Running {name}...")
    t, x, u, u_sat, z_vals, K_hist = simulate_gain_scheduled_lqr(
        z_traj, x0, ref, T_sim, windup_enabled=True
    )
    results[name] = (t, x, u, u_sat, z_vals, K_hist)

print("\nSimulations complete.")

# Plot results
print("\nGenerating plots...")

fig, axes = plt.subplots(4, 3, figsize=(15, 12))
fig.suptitle('Gain-Scheduled LQR with Anti-Windup: Simulation Results', fontsize=16)

for col, (name, (t, x, u, u_sat, z_vals, K_hist)) in enumerate(results.items()):
    # Column 0: States
    axes[0, col].plot(t, x[:, 0], 'b-', label='x1')
    axes[0, col].plot(t, x[:, 1], 'r-', label='x2')
    axes[0, col].set_ylabel('State')
    axes[0, col].set_title(f'{name}')
    axes[0, col].grid(True)
    axes[0, col].legend()
    
    # Column 1: Control signals
    axes[1, col].plot(t, u, 'g--', label='Commanded', alpha=0.7)
    axes[1, col].plot(t, u_sat, 'b-', label='Actual (saturated)', linewidth=2)
    axes[1, col].axhline(y=U_MAX, color='r', linestyle='--', alpha=0.5, label='Saturation limits')
    axes[1, col].axhline(y=U_MIN, color='r', linestyle='--', alpha=0.5)
    axes[1, col].set_ylabel('Control input')
    axes[1, col].grid(True)
    axes[1, col].legend()
    
    # Column 2: Operating point and gains
    ax2 = axes[2, col]
    ax2.plot(t, z_vals, 'b-', label='Operating point z')
    ax2.set_ylabel('z')
    ax2.grid(True)
    ax2.legend(loc='upper left')
    
    ax3 = ax2.twinx()
    ax3.plot(t, K_hist[:, 0], 'g--', label='K1', alpha=0.7)
    ax3.plot(t, K_hist[:, 1], 'r--', label='K2', alpha=0.7)
    ax3.set_ylabel('Gain values')
    ax3.legend(loc='upper right')
    
    # Column 3: Saturation effect
    saturation_ratio = np.sum(np.abs(u_sat) >= 0.89) / len(u_sat) * 100
    axes[3, col].plot(t, u - u_sat, 'r-', label='Saturation error')
    axes[3, col].set_xlabel('Time (s)')
    axes[3, col].set_ylabel('Saturation error')
    axes[3, col].grid(True)
    axes[3, col].legend()
    axes[3, col].set_title(f'Saturation: {saturation_ratio:.1f}% near limits')

plt.tight_layout()
plt.savefig('../report/images/simulation_results.png', dpi=300)
plt.close()

print("Simulation results plot saved to report/images/simulation_results.png")

# Verify H-infinity constraint with tuned weights
print("\n" + "=" * 60)
print("VERIFICATION: H-infinity constraint check with tuned weights")
print("=" * 60)

def compute_hinf_norm(A, B, K, dt):
    """Compute approximate H-infinity norm of closed-loop system."""
    A_cl = A - B @ K
    C = np.eye(2)
    D = np.zeros((2, 1))
    sys_cl = ct.ss(A_cl, B, C, D, dt)
    
    omega = np.logspace(-2, 2, 200)
    mag, phase, omega = ct.freqresp(sys_cl, omega)
    return np.max(np.abs(mag))

# Check all operating points
all_pass = True
for i, (z, A, B) in enumerate(zip(z_values, A_matrices, B_matrices)):
    K = get_interpolated_gain(z)
    hinf_norm = compute_hinf_norm(A, B, K, dt)
    
    print(f"z = {z}: H-infinity norm = {hinf_norm:.6f}", end=" ")
    if hinf_norm < 1.0:
        print("✓ PASS")
    else:
        print("✗ FAIL")
        all_pass = False

# Check segment midpoints
print("\nSegment midpoints:")
for i in range(len(z_values) - 1):
    z_mid = (z_values[i] + z_values[i + 1]) / 2
    alpha = 0.5
    A_mid = A_matrices[i] * (1 - alpha) + A_matrices[i + 1] * alpha
    B_mid = B_matrices[i] * (1 - alpha) + B_matrices[i + 1] * alpha
    
    K_mid = get_interpolated_gain(z_mid)
    hinf_norm_mid = compute_hinf_norm(A_mid, B_mid, K_mid, dt)
    
    print(f"z = {z_mid:.1f}: H-infinity norm = {hinf_norm_mid:.6f}", end=" ")
    if hinf_norm_mid < 1.0:
        print("✓ PASS")
    else:
        print("✗ FAIL")
        all_pass = False

if all_pass:
    print("\n✓ All H-infinity norms satisfy constraint (< 1.0)")
else:
    print("\n✗ Some H-infinity norms violate constraint")

# Save simulation data for report
sim_data = {
    'scenarios': list(results.keys()),
    'dt': dt,
    'U_MIN': U_MIN,
    'U_MAX': U_MAX,
    'Q_tuned': Q_tuned.tolist(),
    'R_tuned': R_tuned.tolist(),
    'hinf_all_pass': all_pass
}

with open('../outputs/simulation_summary.json', 'w') as f:
    json.dump(sim_data, f, indent=2)

print("\nSimulation summary saved to outputs/simulation_summary.json")
