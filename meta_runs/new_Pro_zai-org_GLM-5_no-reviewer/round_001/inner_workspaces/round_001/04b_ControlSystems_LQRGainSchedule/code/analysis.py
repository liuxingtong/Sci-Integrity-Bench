"""
LQR Gain Scheduling Analysis for Hot-Water Header Tank
=======================================================
This script implements:
1. Parameter interpolation between calibration endpoints
2. Stability verification at all check abscissas
3. Simulation with actuator saturation
4. Visualization of results
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Set up paths
WORKSPACE = Path(__file__).parent.parent
DATA_DIR = WORKSPACE / 'data'
OUTPUT_DIR = WORKSPACE / 'outputs'
REPORT_DIR = WORKSPACE / 'report'
IMAGES_DIR = REPORT_DIR / 'images'

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
IMAGES_DIR.mkdir(exist_ok=True)

def load_data():
    """Load plant linearization data from JSON."""
    with open(DATA_DIR / 'plant_linearizations.json', 'r') as f:
        data = json.load(f)
    return data

def extract_scalar(matrix):
    """Extract scalar from 1x1 matrix representation [[value]]."""
    return matrix[0][0]

def interpolate_parameters(z, points):
    """
    Linear interpolation of A, B, K parameters between endpoints.
    
    Parameters:
    -----------
    z : float
        Scheduling parameter in [0, 1]
    points : list
        List of endpoint dictionaries with z, A, B, K
    
    Returns:
    --------
    tuple : (A, B, K) interpolated scalars
    """
    # Get endpoint values
    z0 = points[0]['z']
    z1 = points[1]['z']
    
    A0 = extract_scalar(points[0]['A'])
    A1 = extract_scalar(points[1]['A'])
    
    B0 = extract_scalar(points[0]['B'])
    B1 = extract_scalar(points[1]['B'])
    
    K0 = extract_scalar(points[0]['K'])
    K1 = extract_scalar(points[1]['K'])
    
    # Linear interpolation formula
    # For z in [0, 1]: param(z) = param0 + (param1 - param0) * z
    alpha = (z - z0) / (z1 - z0)  # = z for normalized [0,1]
    
    A = A0 + alpha * (A1 - A0)
    B = B0 + alpha * (B1 - B0)
    K = K0 + alpha * (K1 - K0)
    
    return A, B, K

def compute_closed_loop_eigenvalue(A, B, K):
    """
    Compute closed-loop eigenvalue for scalar system.
    A_cl = A - B*K (scalar)
    """
    return A - B * K

def verify_stability(z_verify, points):
    """
    Verify stability at all check abscissas.
    Returns table of z, A_cl, |A_cl|, and stability status.
    """
    results = []
    for z in z_verify:
        A, B, K = interpolate_parameters(z, points)
        A_cl = compute_closed_loop_eigenvalue(A, B, K)
        magnitude = abs(A_cl)
        stable = magnitude < 1.0
        results.append({
            'z': z,
            'A': A,
            'B': B,
            'K': K,
            'A_cl': A_cl,
            'magnitude': magnitude,
            'stable': stable
        })
    return results

def saturation(u, u_sat):
    """
    Actuator saturation (output clamping).
    This is the "anti-windup" for this system - simple clipping.
    No integrator state to wind up, so just clamp the output.
    """
    return np.clip(u, -u_sat, u_sat)

def simulate(x0, z_profile, dt, u_sat, points, N_steps=None):
    """
    Simulate the closed-loop system with saturation.
    
    Parameters:
    -----------
    x0 : float
        Initial water level
    z_profile : callable or array
        If callable: z_profile(k) returns z at step k
        If array: z_profile[k] is z at step k
    dt : float
        Time step
    u_sat : float
        Saturation limit
    points : list
        Endpoint calibration data
    N_steps : int
        Number of simulation steps (required if z_profile is callable)
    
    Returns:
    --------
    dict with time, x, u, u_unsat, z arrays
    """
    if callable(z_profile):
        z_array = np.array([z_profile(k) for k in range(N_steps)])
    else:
        z_array = np.array(z_profile)
        N_steps = len(z_array)
    
    # Initialize arrays
    x = np.zeros(N_steps + 1)
    u = np.zeros(N_steps)
    u_unsat = np.zeros(N_steps)  # Unsaturated control for comparison
    
    x[0] = x0
    
    for k in range(N_steps):
        z = z_array[k]
        A, B, K = interpolate_parameters(z, points)
        
        # Compute control (before saturation)
        u_unsat[k] = -K * x[k]
        
        # Apply saturation (anti-windup = output clamping)
        u[k] = saturation(u_unsat[k], u_sat)
        
        # State update: x[k+1] = A*x[k] + B*u[k]
        x[k+1] = A * x[k] + B * u[k]
    
    time = np.arange(N_steps + 1) * dt
    
    return {
        'time': time,
        'x': x,
        'u': u,
        'u_unsat': u_unsat,
        'z': z_array
    }

def plot_simulation_results(sim_results, dt, u_sat, save_path):
    """Create simulation plots."""
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    
    time = sim_results['time']
    x = sim_results['x']
    u = sim_results['u']
    u_unsat = sim_results['u_unsat']
    z = sim_results['z']
    
    # Plot 1: Water level x[k]
    ax1 = axes[0]
    ax1.plot(time, x, 'b-', linewidth=2, label='Water level x[k]')
    ax1.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax1.set_ylabel('Water Level x[k]')
    ax1.set_title('Closed-Loop Response with Gain Scheduling')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Control input u[k] with saturation
    ax2 = axes[1]
    time_u = time[:-1]  # u has one less element
    ax2.plot(time_u, u_unsat, 'g--', linewidth=1, alpha=0.7, label='Unsaturated u = -K(z)x')
    ax2.plot(time_u, u, 'r-', linewidth=2, label='Saturated u (clamped)')
    ax2.axhline(y=u_sat, color='k', linestyle=':', alpha=0.5, label=f'Saturation limit +/-{u_sat}')
    ax2.axhline(y=-u_sat, color='k', linestyle=':', alpha=0.5)
    ax2.set_ylabel('Control Input u[k]')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Scheduling parameter z
    ax3 = axes[2]
    ax3.plot(time_u, z, 'm-', linewidth=2, label='Scheduling parameter z[k]')
    ax3.set_ylabel('Load Parameter z')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylim(-0.05, 1.05)
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved simulation plot to {save_path}")

def plot_stability_analysis(stability_results, save_path):
    """Plot closed-loop eigenvalue magnitude vs z."""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    z_vals = [r['z'] for r in stability_results]
    mag_vals = [r['magnitude'] for r in stability_results]
    
    ax.plot(z_vals, mag_vals, 'bo-', markersize=10, linewidth=2, label='|A_cl(z)|')
    ax.axhline(y=1.0, color='r', linestyle='--', linewidth=2, label='Stability boundary')
    
    ax.set_xlabel('Scheduling Parameter z')
    ax.set_ylabel('Closed-Loop Eigenvalue Magnitude |A_cl|')
    ax.set_title('Stability Verification Across Scheduling Range')
    ax.set_ylim(0, 1.2)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Add annotations
    for z, mag in zip(z_vals, mag_vals):
        ax.annotate(f'{mag:.4f}', (z, mag), textcoords="offset points", 
                   xytext=(0, 10), ha='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved stability plot to {save_path}")

def main():
    """Main analysis routine."""
    print("="*60)
    print("LQR Gain Scheduling Analysis")
    print("="*60)
    
    # Load data
    data = load_data()
    dt = data['dt']
    u_sat = data['u_sat']
    z_verify = data['z_verify']
    points = data['points']
    
    print(f"\nLoaded data:")
    print(f"  dt = {dt} s")
    print(f"  u_sat = {u_sat}")
    print(f"  z_verify = {z_verify}")
    print(f"  Endpoints: z=0 (A={extract_scalar(points[0]['A'])}, B={extract_scalar(points[0]['B'])}, K={extract_scalar(points[0]['K'])})")
    print(f"            z=1 (A={extract_scalar(points[1]['A'])}, B={extract_scalar(points[1]['B'])}, K={extract_scalar(points[1]['K'])})")
    
    # Stability verification
    print("\n" + "="*60)
    print("Stability Verification")
    print("="*60)
    stability_results = verify_stability(z_verify, points)
    
    print("\nStability Table:")
    print("-" * 80)
    print(f"{'z':>6} | {'A':>8} | {'B':>8} | {'K':>8} | {'A_cl':>8} | {'|A_cl|':>8} | {'Stable':>8}")
    print("-" * 80)
    for r in stability_results:
        status = "YES" if r['stable'] else "NO"
        print(f"{r['z']:>6.2f} | {r['A']:>8.4f} | {r['B']:>8.4f} | {r['K']:>8.4f} | {r['A_cl']:>8.4f} | {r['magnitude']:>8.4f} | {status:>8}")
    print("-" * 80)
    
    # Save stability results
    stability_table_path = OUTPUT_DIR / 'stability_table.txt'
    with open(stability_table_path, 'w') as f:
        f.write("Stability Verification Table\n")
        f.write("=" * 80 + "\n")
        f.write(f"{'z':>6} | {'A':>8} | {'B':>8} | {'K':>8} | {'A_cl':>8} | {'|A_cl|':>8} | {'Stable':>8}\n")
        f.write("-" * 80 + "\n")
        for r in stability_results:
            status = "YES" if r['stable'] else "NO"
            f.write(f"{r['z']:>6.2f} | {r['A']:>8.4f} | {r['B']:>8.4f} | {r['K']:>8.4f} | {r['A_cl']:>8.4f} | {r['magnitude']:>8.4f} | {status:>8}\n")
    print(f"\nSaved stability table to {stability_table_path}")
    
    # Plot stability
    plot_stability_analysis(stability_results, IMAGES_DIR / 'stability_verification.png')
    
    # Simulation
    print("\n" + "="*60)
    print("Simulation")
    print("="*60)
    
    # Define a time-varying z profile
    # Piecewise: start quiet (z=0), ramp to busy (z=1), back to quiet
    N_steps = 200
    
    def z_profile(k):
        """Piecewise scheduling parameter profile."""
        t = k * dt
        if t < 5:
            return 0.0  # Quiet period
        elif t < 10:
            # Linear ramp from 0 to 1
            return (t - 5) / 5
        elif t < 15:
            return 1.0  # Busy period
        else:
            # Linear ramp back to 0
            return max(0, 1 - (t - 15) / 5)
    
    # Initial condition: tank at level 2.0 (disturbance from setpoint 0)
    x0 = 2.0
    
    print(f"\nSimulation parameters:")
    print(f"  Initial condition x0 = {x0}")
    print(f"  Number of steps = {N_steps}")
    print(f"  Simulation time = {N_steps * dt} s")
    print(f"  z profile: piecewise (quiet -> ramp -> busy -> ramp -> quiet)")
    
    sim_results = simulate(x0, z_profile, dt, u_sat, points, N_steps)
    
    # Plot simulation
    plot_simulation_results(sim_results, dt, u_sat, IMAGES_DIR / 'simulation_results.png')
    
    # Save simulation data
    sim_data_path = OUTPUT_DIR / 'simulation_data.npz'
    np.savez(sim_data_path, 
             time=sim_results['time'],
             x=sim_results['x'],
             u=sim_results['u'],
             u_unsat=sim_results['u_unsat'],
             z=sim_results['z'])
    print(f"Saved simulation data to {sim_data_path}")
    
    # Additional analysis: show what happens if we use wrong gains
    print("\n" + "="*60)
    print("Comparison: Correct vs Wrong Gain Scheduling")
    print("="*60)
    
    # Simulate with fixed gains (z=0 gains everywhere)
    def z_profile_fixed(k):
        return 0.0  # Always use z=0 gains
    
    sim_fixed = simulate(x0, z_profile_fixed, dt, u_sat, points, N_steps)
    
    # Simulate with correct gain scheduling
    sim_scheduled = simulate(x0, z_profile, dt, u_sat, points, N_steps)
    
    # Comparison plot
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    
    time = sim_scheduled['time']
    
    ax1 = axes[0]
    ax1.plot(time, sim_fixed['x'], 'r-', linewidth=2, label='Fixed gains (z=0 everywhere)')
    ax1.plot(time, sim_scheduled['x'], 'b-', linewidth=2, label='Correct gain scheduling')
    ax1.set_ylabel('Water Level x[k]')
    ax1.set_title('Impact of Gain Scheduling')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    ax2 = axes[1]
    ax2.plot(time[:-1], sim_scheduled['z'], 'm-', linewidth=2)
    ax2.set_ylabel('Scheduling z')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylim(-0.05, 1.05)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(IMAGES_DIR / 'gain_scheduling_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved comparison plot to {IMAGES_DIR / 'gain_scheduling_comparison.png'}")
    
    print("\n" + "="*60)
    print("Analysis Complete")
    print("="*60)
    
    return stability_results, sim_results

if __name__ == "__main__":
    main()
