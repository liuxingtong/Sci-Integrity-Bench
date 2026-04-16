"""
Generate figures for the gain-scheduled LQR report.
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import os

def load_results():
    with open('../outputs/results.json', 'r') as f:
        results = json.load(f)
    return results

def plot_gain_interpolation(results, save_path='../report/images/gain_interpolation.png'):
    """Plot gain interpolation across scheduling variable."""
    z_grid = np.array(results['z_grid'])
    K_points = np.array(results['K_points'])
    
    # Fine grid for interpolation visualization
    z_fine = np.linspace(0.5, 4.5, 200)
    
    from scipy.interpolate import interp1d
    K0_interp = interp1d(z_grid, K_points[:, 0], kind='linear', fill_value='extrapolate')
    K1_interp = interp1d(z_grid, K_points[:, 1], kind='linear', fill_value='extrapolate')
    
    K0_fine = K0_interp(z_fine)
    K1_fine = K1_interp(z_fine)
    
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    
    # K[0] interpolation
    axes[0].plot(z_fine, K0_fine, 'b-', linewidth=2, label='Interpolated gain')
    axes[0].scatter(z_grid, K_points[:, 0], color='red', s=100, zorder=5, label='Design points')
    axes[0].set_xlabel('Scheduling variable z', fontsize=12)
    axes[0].set_ylabel('$K_1(z)$', fontsize=12)
    axes[0].set_title('Gain Interpolation: $K_1$ vs Scheduling Variable', fontsize=14)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=10)
    axes[0].set_xlim([0.5, 4.5])
    
    # K[1] interpolation
    axes[1].plot(z_fine, K1_fine, 'b-', linewidth=2, label='Interpolated gain')
    axes[1].scatter(z_grid, K_points[:, 1], color='red', s=100, zorder=5, label='Design points')
    axes[1].set_xlabel('Scheduling variable z', fontsize=12)
    axes[1].set_ylabel('$K_2(z)$', fontsize=12)
    axes[1].set_title('Gain Interpolation: $K_2$ vs Scheduling Variable', fontsize=14)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=10)
    axes[1].set_xlim([0.5, 4.5])
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def plot_hinf_verification(results, save_path='../report/images/hinf_verification.png'):
    """Plot H-infinity norm verification results."""
    hinf_data = results['hinf_verification']
    
    z_values = [r['z'] for r in hinf_data]
    hinf_norms = [r['hinf_norm'] for r in hinf_data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(z_values, hinf_norms, width=0.5, color='steelblue', edgecolor='navy', alpha=0.7)
    ax.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Requirement limit (1.0)')
    
    # Color bars based on pass/fail
    for i, (bar, hinf) in enumerate(zip(bars, hinf_norms)):
        if hinf < 1.0:
            bar.set_color('green')
            bar.set_alpha(0.6)
        else:
            bar.set_color('red')
            bar.set_alpha(0.6)
    
    ax.set_xlabel('Operating Point (z)', fontsize=12)
    ax.set_ylabel('H-infinity Norm', fontsize=12)
    ax.set_title('H-infinity Norm Verification for Each Operating Point', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(fontsize=10)
    
    # Add value labels on bars
    for z, hinf in zip(z_values, hinf_norms):
        ax.text(z, hinf + 0.02, f'{hinf:.4f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def plot_simulation1(results, save_path='../report/images/simulation1.png'):
    """Plot simulation 1: Regulation with constant scheduling."""
    sim = results['simulation1']
    t = np.array(sim['t'])
    x = np.array(sim['x'])
    u = np.array(sim['u'])
    u_unsat = np.array(sim['u_unsat'])
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # State trajectories
    axes[0].plot(t, x[:, 0], 'b-', linewidth=2, label='$x_1$')
    axes[0].plot(t, x[:, 1], 'r-', linewidth=2, label='$x_2$')
    axes[0].set_xlabel('Time (s)', fontsize=12)
    axes[0].set_ylabel('State', fontsize=12)
    axes[0].set_title('State Trajectories (Constant Scheduling, z=2.5)', fontsize=14)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=10)
    
    # Control input
    axes[1].plot(t, u, 'g-', linewidth=2, label='Saturated control $u$')
    axes[1].plot(t, u_unsat, 'm--', linewidth=1.5, alpha=0.7, label='Unsaturated control')
    axes[1].axhline(y=0.9, color='r', linestyle=':', alpha=0.5, label='Saturation limits')
    axes[1].axhline(y=-0.9, color='r', linestyle=':', alpha=0.5)
    axes[1].set_xlabel('Time (s)', fontsize=12)
    axes[1].set_ylabel('Control Input', fontsize=12)
    axes[1].set_title('Control Input with Anti-Windup Saturation (±0.9)', fontsize=14)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=10)
    
    # Phase portrait
    axes[2].plot(x[:, 0], x[:, 1], 'b-', linewidth=2)
    axes[2].scatter(x[0, 0], x[0, 1], color='green', s=100, marker='o', label='Initial', zorder=5)
    axes[2].scatter(x[-1, 0], x[-1, 1], color='red', s=100, marker='*', label='Final', zorder=5)
    axes[2].set_xlabel('$x_1$', fontsize=12)
    axes[2].set_ylabel('$x_2$', fontsize=12)
    axes[2].set_title('Phase Portrait', fontsize=14)
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(fontsize=10)
    axes[2].axis('equal')
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def plot_simulation2(results, save_path='report/images/simulation2.png'):
    """Plot simulation 2: Regulation with time-varying scheduling."""
    sim = results['simulation2']
    t = np.array(sim['t'])
    x = np.array(sim['x'])
    u = np.array(sim['u'])
    z = np.array(sim['z'])
    
    fig, axes = plt.subplots(4, 1, figsize=(12, 12))
    
    # Scheduling variable
    axes[0].plot(t, z, 'purple', linewidth=2)
    axes[0].set_xlabel('Time (s)', fontsize=12)
    axes[0].set_ylabel('z', fontsize=12)
    axes[0].set_title('Scheduling Variable Trajectory', fontsize=14)
    axes[0].grid(True, alpha=0.3)
    
    # State trajectories
    axes[1].plot(t, x[:, 0], 'b-', linewidth=2, label='$x_1$')
    axes[1].plot(t, x[:, 1], 'r-', linewidth=2, label='$x_2$')
    axes[1].set_xlabel('Time (s)', fontsize=12)
    axes[1].set_ylabel('State', fontsize=12)
    axes[1].set_title('State Trajectories (Time-Varying Scheduling)', fontsize=14)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=10)
    
    # Control input
    axes[2].plot(t, u, 'g-', linewidth=2)
    axes[2].axhline(y=0.9, color='r', linestyle=':', alpha=0.5)
    axes[2].axhline(y=-0.9, color='r', linestyle=':', alpha=0.5)
    axes[2].set_xlabel('Time (s)', fontsize=12)
    axes[2].set_ylabel('Control Input', fontsize=12)
    axes[2].set_title('Control Input', fontsize=14)
    axes[2].grid(True, alpha=0.3)
    
    # Gain variation
    K_points = np.array(results['K_points'])
    z_grid = np.array(results['z_grid'])
    from scipy.interpolate import interp1d
    K0_interp = interp1d(z_grid, K_points[:, 0], kind='linear', fill_value='extrapolate')
    K1_interp = interp1d(z_grid, K_points[:, 1], kind='linear', fill_value='extrapolate')
    K0_t = K0_interp(z)
    K1_t = K1_interp(z)
    
    axes[3].plot(t, K0_t, 'b-', linewidth=2, label='$K_1(z(t))$')
    axes[3].plot(t, K1_t, 'r-', linewidth=2, label='$K_2(z(t))$')
    axes[3].set_xlabel('Time (s)', fontsize=12)
    axes[3].set_ylabel('Gain', fontsize=12)
    axes[3].set_title('Interpolated Gains Over Time', fontsize=14)
    axes[3].grid(True, alpha=0.3)
    axes[3].legend(fontsize=10)
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def plot_simulation3(results, save_path='report/images/simulation3.png'):
    """Plot simulation 3: Large initial condition with saturation."""
    sim = results['simulation3']
    t = np.array(sim['t'])
    x = np.array(sim['x'])
    u = np.array(sim['u'])
    u_unsat = np.array(sim['u_unsat'])
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # State trajectories
    axes[0].plot(t, x[:, 0], 'b-', linewidth=2, label='$x_1$')
    axes[0].plot(t, x[:, 1], 'r-', linewidth=2, label='$x_2$')
    axes[0].set_xlabel('Time (s)', fontsize=12)
    axes[0].set_ylabel('State', fontsize=12)
    axes[0].set_title('State Trajectories (Large Initial Condition)', fontsize=14)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=10)
    
    # Control input with saturation visible
    axes[1].plot(t, u, 'g-', linewidth=2.5, label='Saturated control $u$')
    axes[1].plot(t, u_unsat, 'm--', linewidth=1.5, alpha=0.6, label='Unsaturated control')
    axes[1].axhline(y=0.9, color='r', linestyle=':', linewidth=2, alpha=0.7, label='Saturation limits')
    axes[1].axhline(y=-0.9, color='r', linestyle=':', linewidth=2, alpha=0.7)
    axes[1].fill_between(t, -0.9, 0.9, alpha=0.1, color='green', label='Linear region')
    axes[1].set_xlabel('Time (s)', fontsize=12)
    axes[1].set_ylabel('Control Input', fontsize=12)
    axes[1].set_title('Control Input Demonstrating Anti-Windup Behavior', fontsize=14)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=9, loc='upper right')
    
    # Saturation indicator
    saturation = np.abs(u_unsat) > 0.9
    axes[2].fill_between(t, 0, 1, where=saturation, alpha=0.3, color='red', label='Saturation active')
    axes[2].plot(t, np.abs(u_unsat) - 0.9, 'b-', linewidth=2)
    axes[2].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    axes[2].set_xlabel('Time (s)', fontsize=12)
    axes[2].set_ylabel('$|u_{unsat}| - 0.9$', fontsize=12)
    axes[2].set_title('Saturation Activity (Positive = Saturated)', fontsize=14)
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(fontsize=10)
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def plot_closed_loop_poles(results, save_path='../report/images/closed_loop_poles.png'):
    """Plot closed-loop pole locations for each operating point."""
    hinf_data = results['hinf_verification']
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Unit circle
    theta = np.linspace(0, 2*np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), 'k--', linewidth=1, label='Unit circle')
    ax.fill(np.cos(theta), np.sin(theta), alpha=0.05, color='gray')
    
    # Plot poles for each operating point
    colors = ['blue', 'green', 'orange', 'red']
    markers = ['o', 's', '^', 'd']
    
    for i, res in enumerate(hinf_data):
        eigs = res['eigenvalues']
        z = res['z']
        # Extract real and imaginary parts from dict format
        real_parts = [ev['real'] for ev in eigs]
        imag_parts = [ev['imag'] for ev in eigs]
        ax.scatter(real_parts, imag_parts, 
                  c=colors[i], marker=markers[i], s=150, 
                  label=f'z={z}', zorder=5, edgecolors='black', linewidths=1)
    
    ax.axhline(y=0, color='k', linewidth=0.5)
    ax.axvline(x=0, color='k', linewidth=0.5)
    ax.set_xlabel('Real', fontsize=12)
    ax.set_ylabel('Imaginary', fontsize=12)
    ax.set_title('Closed-Loop Pole Locations (Discrete-Time)', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    ax.axis('equal')
    ax.set_xlim([-1.2, 1.2])
    ax.set_ylim([-1.2, 1.2])
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

def main():
    print("Loading results...")
    results = load_results()
    
    print("\nGenerating figures...")
    plot_gain_interpolation(results)
    plot_hinf_verification(results)
    plot_simulation1(results)
    plot_simulation2(results)
    plot_simulation3(results)
    plot_closed_loop_poles(results)
    
    print("\nAll figures generated successfully!")

if __name__ == '__main__':
    main()
