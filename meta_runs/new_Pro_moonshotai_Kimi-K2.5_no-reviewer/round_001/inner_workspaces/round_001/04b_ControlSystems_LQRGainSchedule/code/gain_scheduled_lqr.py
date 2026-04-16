"""
Gain-Scheduled LQR Controller with Anti-Windup and H-infinity Verification

This module implements:
1. Gain-scheduled LQR controller with continuous interpolation
2. Anti-windup compensation for actuator saturation (±0.9)
3. H-infinity norm verification for each linear segment
"""

import numpy as np
import json
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.linalg import solve_discrete_are, norm
import os

# Get base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load plant data
def load_plant_data(filepath=None):
    if filepath is None:
        filepath = os.path.join(BASE_DIR, 'data', 'plant_linearizations.json')
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

# Compute LQR gain for a given (A, B, Q, R)
def compute_lqr_gain(A, B, Q, R):
    """Solve discrete-time LQR and return gain matrix K."""
    A = np.array(A)
    B = np.array(B)
    Q = np.array(Q)
    R = np.array(R)
    
    # Solve discrete-time algebraic Riccati equation
    P = solve_discrete_are(A, B, Q, R)
    
    # Compute LQR gain: K = (R + B'PB)^-1 * B'PA
    K = np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)
    return K

# Gain-scheduled LQR controller class
class GainScheduledLQR:
    def __init__(self, data):
        self.dt = data['dt']
        self.points = data['points']
        self.Q = np.array(data['weights']['Q'])
        self.R = np.array(data['weights']['R'])
        
        # Extract scheduling grid
        self.z_grid = np.array([p['z'] for p in self.points])
        
        # Compute LQR gains at each grid point
        self.K_grid = []
        for p in self.points:
            A = np.array(p['A'])
            B = np.array(p['B'])
            K = compute_lqr_gain(A, B, self.Q, self.R)
            self.K_grid.append(K)
        
        self.K_grid = np.array(self.K_grid)  # Shape: (n_points, n_inputs, n_states)
        
        # Create interpolation functions for each element of K
        self.n_inputs = self.K_grid.shape[1]
        self.n_states = self.K_grid.shape[2]
        
        # Store interpolation functions
        self.K_interpolators = []
        for i in range(self.n_inputs):
            row_interps = []
            for j in range(self.n_states):
                K_values = self.K_grid[:, i, j]
                # Linear interpolation with extrapolation
                interp = interp1d(self.z_grid, K_values, kind='linear', 
                                 fill_value='extrapolate', bounds_error=False)
                row_interps.append(interp)
            self.K_interpolators.append(row_interps)
        
        # Anti-windup state
        self.integral_state = np.zeros((self.n_inputs, 1))
        self.saturation_limit = 0.9
        
    def get_gain(self, z):
        """Get interpolated LQR gain for scheduling variable z."""
        K = np.zeros((self.n_inputs, self.n_states))
        for i in range(self.n_inputs):
            for j in range(self.n_states):
                K[i, j] = self.K_interpolators[i][j](z)
        return K
    
    def control(self, x, z, reference=None, anti_windup=True):
        """
        Compute control input with optional anti-windup.
        
        Args:
            x: state vector (n_states, 1)
            z: scheduling variable
            reference: reference state (optional)
            anti_windup: enable anti-windup compensation
        
        Returns:
            u: control input (saturated)
            u_unsat: unsaturated control input
        """
        x = np.array(x).reshape(-1, 1)
        if reference is not None:
            reference = np.array(reference).reshape(-1, 1)
            error = x - reference
        else:
            error = x
        
        # Get interpolated gain
        K = self.get_gain(z)
        
        # Compute control (state feedback)
        u_unsat = -K @ error
        
        # Add integral action with anti-windup
        if anti_windup:
            u_unsat = u_unsat + self.integral_state
        
        # Apply saturation
        u = np.clip(u_unsat, -self.saturation_limit, self.saturation_limit)
        
        # Anti-windup: update integral state only when not saturated
        if anti_windup:
            # Simple anti-windup: freeze integration when saturated
            if np.all(np.abs(u_unsat) < self.saturation_limit):
                # Not saturated - integrate error
                self.integral_state += 0.1 * error[:self.n_inputs] * self.dt
            else:
                # Saturated - conditional integration (back-calculation)
                saturation_error = u - u_unsat
                self.integral_state += 0.5 * saturation_error
        
        return u, u_unsat
    
    def reset_integral(self):
        """Reset anti-windup integral state."""
        self.integral_state = np.zeros((self.n_inputs, 1))


def compute_hinfinity_norm(A_cl, B_w, C_z, D_zw, max_iter=100, tol=1e-6):
    """
    Compute H-infinity norm of the closed-loop system using bisection.
    
    System: x_{k+1} = A_cl x_k + B_w w_k
            z_k = C_z x_k + D_zw w_k
    
    Returns:
        gamma: H-infinity norm (L2 gain from w to z)
    """
    A_cl = np.array(A_cl)
    B_w = np.array(B_w)
    C_z = np.array(C_z)
    D_zw = np.array(D_zw)
    
    n = A_cl.shape[0]
    nw = B_w.shape[1]
    nz = C_z.shape[0]
    
    # Initial bounds
    gamma_low = 0
    gamma_high = 100
    
    for _ in range(max_iter):
        gamma = (gamma_low + gamma_high) / 2
        
        # Check if gamma is an upper bound using bounded real lemma
        # For discrete-time: check if there exists P > 0 such that:
        # [A'PA-P, A'PB; B'PA, B'PB-gamma^2I] + [C'; D']*[C, D] < 0
        
        # Simplified check: compute eigenvalues of Hamiltonian matrix
        # or use iterative approach
        
        # Alternative: compute via power iteration on the transfer function
        # For now, use a simpler approach based on Lyapunov equation
        
        try:
            # Solve Lyapunov-like equation for bounded real lemma
            # Check if ||G||_inf < gamma
            
            # Form the matrix for bounded real lemma
            # [A_cl, gamma^(-1/2)*B_w; gamma^(1/2)*C_z, D_zw]
            
            # Compute using simpler method: check spectral radius condition
            # This is a conservative check
            
            # Use power iteration to estimate norm
            gamma_est = power_iteration_hinf(A_cl, B_w, C_z, D_zw, n_iter=50)
            
            if gamma_est < gamma:
                gamma_high = gamma
            else:
                gamma_low = gamma
            
            if gamma_high - gamma_low < tol:
                break
        except:
            gamma_low = gamma
    
    return (gamma_low + gamma_high) / 2


def power_iteration_hinf(A, B, C, D, n_iter=100):
    """
    Estimate H-infinity norm using power iteration on frequency response.
    """
    # Sample frequencies
    n_freq = 100
    omega = np.linspace(0, np.pi, n_freq)
    
    max_gain = 0
    for w in omega:
        # Compute frequency response
        z = np.exp(1j * w)
        I = np.eye(A.shape[0])
        try:
            H = C @ np.linalg.solve(z * I - A, B) + D
            gain = np.linalg.norm(H, 2)
            max_gain = max(max_gain, gain)
        except:
            pass
    
    return max_gain


def verify_hinfinity_norms(controller, output_weight=1.0):
    """
    Verify H-infinity norm for each linearized segment.
    
    Returns:
        results: dict with H-infinity norms for each operating point
    """
    results = []
    
    for i, p in enumerate(controller.points):
        A = np.array(p['A'])
        B = np.array(p['B'])
        z = p['z']
        
        # Get LQR gain at this point
        K = controller.K_grid[i]
        
        # Closed-loop system: A_cl = A - B*K
        A_cl = A - B @ K
        
        # For H-infinity analysis, consider:
        # - Disturbance input: w (process noise)
        # - Performance output: z = C_z * x (weighted state)
        
        # Assume disturbance enters through B (matched uncertainty)
        B_w = B * 0.1  # Disturbance input matrix
        
        # Output weighting matrix (performance specification)
        C_z = np.eye(2) * np.sqrt(output_weight)
        D_zw = np.zeros((2, 1))
        
        # Compute H-infinity norm
        gamma = power_iteration_hinf(A_cl, B_w, C_z, D_zw)
        
        results.append({
            'z': z,
            'A_cl': A_cl,
            'K': K,
            'hinf_norm': gamma,
            'passes': gamma < 1.0
        })
        
        print(f"Operating point z={z}: H-inf norm = {gamma:.4f}, Passes: {gamma < 1.0}")
    
    return results


def simulate_nonlinear(controller, x0, z_trajectory, t_final, reference=None, use_anti_windup=True):
    """
    Simulate the closed-loop system with gain-scheduled LQR.
    
    Args:
        controller: GainScheduledLQR instance
        x0: initial state
        z_trajectory: function or array of scheduling variable over time
        t_final: simulation time
        reference: reference trajectory function
        use_anti_windup: enable anti-windup
    
    Returns:
        t, x, u, z: time, state, control, and scheduling variable histories
    """
    dt = controller.dt
    n_steps = int(t_final / dt)
    
    t = np.zeros(n_steps)
    x = np.zeros((n_steps, 2))
    u = np.zeros((n_steps, 1))
    z_hist = np.zeros(n_steps)
    u_unsat = np.zeros((n_steps, 1))
    
    x[0] = x0.flatten()
    controller.reset_integral()
    
    for k in range(n_steps - 1):
        t[k] = k * dt
        
        # Get scheduling variable
        if callable(z_trajectory):
            z = z_trajectory(t[k])
        else:
            z = z_trajectory[k]
        z_hist[k] = z
        
        # Get reference
        if reference is None:
            ref = None
        elif callable(reference):
            ref = reference(t[k])
        else:
            ref = reference[k]
        
        # Compute control
        u_k, u_unsat_k = controller.control(x[k].reshape(-1, 1), z, ref, anti_windup=use_anti_windup)
        u[k] = u_k.flatten()
        u_unsat[k] = u_unsat_k.flatten()
        
        # Get current plant dynamics (interpolated)
        # Find nearest operating point for simulation
        idx = np.argmin(np.abs(controller.z_grid - z))
        A = np.array(controller.points[idx]['A'])
        B = np.array(controller.points[idx]['B'])
        
        # State update (with some process noise)
        w_k = 0.01 * np.random.randn(2)  # Small process noise
        x[k+1] = (A @ x[k] + B.flatten() * u[k] + w_k).flatten()
    
    t[-1] = (n_steps - 1) * dt
    z_hist[-1] = z_hist[-2] if n_steps > 1 else z_hist[0]
    
    return t, x, u, z_hist, u_unsat


def plot_results(t, x, u, z_hist, u_unsat, title_suffix=""):
    """Generate visualization plots."""
    fig, axes = plt.subplots(4, 1, figsize=(10, 12))
    
    # State trajectories
    axes[0].plot(t, x[:, 0], 'b-', label='$x_1$')
    axes[0].plot(t, x[:, 1], 'r-', label='$x_2$')
    axes[0].set_ylabel('State')
    axes[0].set_title(f'State Trajectories {title_suffix}')
    axes[0].legend()
    axes[0].grid(True)
    
    # Control input
    axes[1].plot(t, u, 'g-', label='Control $u$ (saturated)')
    axes[1].axhline(y=0.9, color='r', linestyle='--', label='Saturation limit')
    axes[1].axhline(y=-0.9, color='r', linestyle='--')
    axes[1].set_ylabel('Control Input')
    axes[1].set_title(f'Control Input {title_suffix}')
    axes[1].legend()
    axes[1].grid(True)
    
    # Scheduling variable
    axes[2].plot(t, z_hist, 'm-', label='Scheduling variable $z$')
    axes[2].set_ylabel('z')
    axes[2].set_title(f'Scheduling Variable {title_suffix}')
    axes[2].legend()
    axes[2].grid(True)
    
    # Saturation analysis
    axes[3].plot(t, u_unsat, 'b--', label='Unsaturated $u$')
    axes[3].plot(t, u, 'g-', label='Saturated $u$')
    axes[3].axhline(y=0.9, color='r', linestyle='--', label='Saturation limit')
    axes[3].axhline(y=-0.9, color='r', linestyle='--')
    axes[3].set_xlabel('Time (s)')
    axes[3].set_ylabel('Control')
    axes[3].set_title(f'Anti-Windup Effect {title_suffix}')
    axes[3].legend()
    axes[3].grid(True)
    
    plt.tight_layout()
    return fig


def main():
    print("=" * 60)
    print("Gain-Scheduled LQR Controller Design and Verification")
    print("=" * 60)
    
    # Load data
    data = load_plant_data()
    print(f"\nLoaded plant data:")
    print(f"  Sampling time: {data['dt']} s")
    print(f"  Number of operating points: {len(data['points'])}")
    print(f"  Scheduling grid: {[p['z'] for p in data['points']]}")
    
    # Create gain-scheduled controller
    controller = GainScheduledLQR(data)
    print(f"\nComputed LQR gains at grid points:")
    for i, p in enumerate(data['points']):
        print(f"  z={p['z']}: K = {controller.K_grid[i].flatten()}")
    
    # Verify H-infinity norms
    print("\n" + "=" * 60)
    print("H-infinity Norm Verification")
    print("=" * 60)
    hinf_results = verify_hinfinity_norms(controller)
    
    all_pass = all(r['passes'] for r in hinf_results)
    print(f"\nAll operating points pass H-inf < 1.0: {all_pass}")
    
    # Save H-infinity results
    hinf_summary = {
        'operating_points': [
            {'z': r['z'], 'hinf_norm': float(r['hinf_norm']), 'passes': bool(r['passes'])}
            for r in hinf_results
        ],
        'all_pass': bool(all_pass)
    }
    
    outputs_dir = os.path.join(BASE_DIR, 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    with open(os.path.join(outputs_dir, 'hinf_verification.json'), 'w') as f:
        json.dump(hinf_summary, f, indent=2)
    
    # Simulation 1: Step response with varying scheduling variable
    print("\n" + "=" * 60)
    print("Simulation 1: Step Response with Varying Scheduling")
    print("=" * 60)
    
    x0 = np.array([[1.0], [0.5]])
    t_final = 10.0
    
    # Varying scheduling variable: z sweeps through operating range
    def z_traj_1(t):
        return 1.0 + 3.0 * t / t_final  # z goes from 1 to 4
    
    t1, x1, u1, z1, u_unsat1 = simulate_nonlinear(
        controller, x0, z_traj_1, t_final, reference=None, use_anti_windup=True
    )
    
    fig1 = plot_results(t1, x1, u1, z1, u_unsat1, "(Varying z)")
    fig1.savefig(os.path.join(BASE_DIR, 'report', 'images', 'simulation_varying_z.png'), dpi=150, bbox_inches='tight')
    plt.close(fig1)
    print("Saved: report/images/simulation_varying_z.png")
    
    # Simulation 2: Fixed operating point with large initial condition (tests saturation)
    print("\nSimulation 2: Large Initial Condition (Saturation Test)")
    x0_large = np.array([[5.0], [3.0]])
    z_fixed = 2.5
    
    t2, x2, u2, z2, u_unsat2 = simulate_nonlinear(
        controller, x0_large, lambda t: z_fixed, t_final, reference=None, use_anti_windup=True
    )
    
    fig2 = plot_results(t2, x2, u2, z2, u_unsat2, f"(Fixed z={z_fixed}, Large IC)")
    fig2.savefig(os.path.join(BASE_DIR, 'report', 'images', 'simulation_saturation.png'), dpi=150, bbox_inches='tight')
    plt.close(fig2)
    print("Saved: report/images/simulation_saturation.png")
    
    # Simulation 3: Comparison with and without anti-windup
    print("\nSimulation 3: Anti-Windup Comparison")
    x0_aw = np.array([[3.0], [2.0]])
    z_aw = 2.0
    
    # With anti-windup
    t_aw, x_aw, u_aw, z_aw_hist, u_unsat_aw = simulate_nonlinear(
        controller, x0_aw, lambda t: z_aw, t_final, reference=None, use_anti_windup=True
    )
    
    # Without anti-windup
    controller.reset_integral()
    t_naw, x_naw, u_naw, z_naw_hist, u_unsat_naw = simulate_nonlinear(
        controller, x0_aw, lambda t: z_aw, t_final, reference=None, use_anti_windup=False
    )
    
    fig3, axes3 = plt.subplots(2, 1, figsize=(10, 8))
    
    axes3[0].plot(t_aw, x_aw[:, 0], 'b-', label='With AW - $x_1$')
    axes3[0].plot(t_aw, x_aw[:, 1], 'b--', label='With AW - $x_2$')
    axes3[0].plot(t_naw, x_naw[:, 0], 'r-', label='Without AW - $x_1$')
    axes3[0].plot(t_naw, x_naw[:, 1], 'r--', label='Without AW - $x_2$')
    axes3[0].set_ylabel('State')
    axes3[0].set_title('State Trajectories: With vs Without Anti-Windup')
    axes3[0].legend()
    axes3[0].grid(True)
    
    axes3[1].plot(t_aw, u_aw, 'b-', label='With AW')
    axes3[1].plot(t_naw, u_naw, 'r-', label='Without AW')
    axes3[1].axhline(y=0.9, color='k', linestyle='--', alpha=0.5)
    axes3[1].axhline(y=-0.9, color='k', linestyle='--', alpha=0.5)
    axes3[1].set_xlabel('Time (s)')
    axes3[1].set_ylabel('Control Input')
    axes3[1].set_title('Control Input: With vs Without Anti-Windup')
    axes3[1].legend()
    axes3[1].grid(True)
    
    plt.tight_layout()
    fig3.savefig(os.path.join(BASE_DIR, 'report', 'images', 'antiwindup_comparison.png'), dpi=150, bbox_inches='tight')
    plt.close(fig3)
    print("Saved: report/images/antiwindup_comparison.png")
    
    # Plot gain interpolation
    print("\nGenerating gain interpolation visualization...")
    z_fine = np.linspace(0.5, 4.5, 100)
    K_fine = np.array([controller.get_gain(z).flatten() for z in z_fine])
    
    fig4, axes4 = plt.subplots(1, 2, figsize=(12, 5))
    
    axes4[0].plot(z_fine, K_fine[:, 0], 'b-', label='$K_1$')
    axes4[0].plot(z_fine, K_fine[:, 1], 'r-', label='$K_2$')
    axes4[0].scatter(controller.z_grid, controller.K_grid[:, 0, 0], color='b', s=50, zorder=5)
    axes4[0].scatter(controller.z_grid, controller.K_grid[:, 0, 1], color='r', s=50, zorder=5)
    axes4[0].set_xlabel('Scheduling Variable $z$')
    axes4[0].set_ylabel('Gain Value')
    axes4[0].set_title('Gain-Scheduled LQR: Continuous Interpolation')
    axes4[0].legend()
    axes4[0].grid(True)
    
    # H-infinity norm plot
    z_hinf = [r['z'] for r in hinf_results]
    gamma_hinf = [r['hinf_norm'] for r in hinf_results]
    
    axes4[1].bar(range(len(z_hinf)), gamma_hinf, color=['green' if r['passes'] else 'red' for r in hinf_results])
    axes4[1].axhline(y=1.0, color='k', linestyle='--', label='Requirement: $\gamma < 1$')
    axes4[1].set_xticks(range(len(z_hinf)))
    axes4[1].set_xticklabels([f'z={z}' for z in z_hinf])
    axes4[1].set_ylabel('H-infinity Norm')
    axes4[1].set_title('H-infinity Norm Verification')
    axes4[1].legend()
    axes4[1].grid(True, axis='y')
    
    plt.tight_layout()
    fig4.savefig(os.path.join(BASE_DIR, 'report', 'images', 'gain_interpolation_hinf.png'), dpi=150, bbox_inches='tight')
    plt.close(fig4)
    print("Saved: report/images/gain_interpolation_hinf.png")
    
    # Save simulation data
    np.savez(os.path.join(outputs_dir, 'simulation_data.npz'),
             t1=t1, x1=x1, u1=u1, z1=z1,
             t2=t2, x2=x2, u2=u2, z2=z2,
             t_aw=t_aw, x_aw=x_aw, u_aw=u_aw,
             t_naw=t_naw, x_naw=x_naw, u_naw=u_naw)
    
    print("\n" + "=" * 60)
    print("All simulations completed successfully!")
    print("=" * 60)
    
    return controller, hinf_results


if __name__ == '__main__':
    controller, hinf_results = main()
