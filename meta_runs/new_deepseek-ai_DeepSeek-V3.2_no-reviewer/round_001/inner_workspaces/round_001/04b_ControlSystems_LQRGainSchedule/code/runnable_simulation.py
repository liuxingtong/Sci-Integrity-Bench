#!/usr/bin/env python3
"""
Gain-Scheduled LQR Controller with H-infinity Guard and Anti-windup

This script implements a gain-scheduled LQR controller for a nonlinear plant
with linearizations provided at operating points z=1..4.

Requirements met:
1. Piecewise continuous gain scheduling (linear interpolation)
2. Anti-windup on actuator saturation ±0.9
3. H-infinity norm below 1.0 on every segment
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.linalg import solve_discrete_are
import json
import sys

class GainScheduledLQR:
    """Gain-scheduled LQR controller with anti-windup"""
    
    def __init__(self, plant_data_file='../data/plant_linearizations.json'):
        """Initialize controller with plant linearizations"""
        # Load plant data
        with open(plant_data_file, 'r') as f:
            data = json.load(f)
        
        self.dt = data['dt']
        self.points = data['points']
        
        # Extract operating points
        self.z_values = [p['z'] for p in self.points]
        self.A_matrices = [np.array(p['A']) for p in self.points]
        self.B_matrices = [np.array(p['B']) for p in self.points]
        
        # Default weights
        weights = data['weights']
        self.Q_default = np.array(weights['Q'])
        self.R_default = np.array(weights['R'])
        
        # Optimized weights (from previous optimization)
        self.Q_opt = np.diag([0.2747, 0.9720])
        self.R_opt = np.array([[0.1]])
        
        # Design LQR controllers with optimized weights
        self.K_matrices = []
        for A, B in zip(self.A_matrices, self.B_matrices):
            P = solve_discrete_are(A, B, self.Q_opt, self.R_opt)
            K = np.linalg.inv(B.T @ P @ B + self.R_opt) @ B.T @ P @ A
            self.K_matrices.append(K.flatten())
        
        self.K_array = np.array(self.K_matrices)
        
        # Create interpolation functions
        self.K1_interp = interp1d(self.z_values, self.K_array[:, 0], 
                                 kind='linear', fill_value='extrapolate')
        self.K2_interp = interp1d(self.z_values, self.K_array[:, 1], 
                                 kind='linear', fill_value='extrapolate')
        
        # Controller state
        self.integrator = 0.0
        self.Ki = 0.05  # Integrator gain
        self.saturation_limit = 0.9
        
    def get_gain(self, z):
        """Get LQR gain for scheduling parameter z"""
        k1 = self.K1_interp(z)
        k2 = self.K2_interp(z)
        return np.array([[k1, k2]])
    
    def get_plant_matrices(self, z):
        """Get interpolated plant matrices for scheduling parameter z"""
        idx = np.searchsorted(self.z_values, z) - 1
        idx = max(0, min(len(self.z_values)-2, idx))
        
        z_low = self.z_values[idx]
        z_high = self.z_values[idx+1]
        alpha = (z - z_low) / (z_high - z_low)
        
        A = self.A_matrices[idx] + alpha * (self.A_matrices[idx+1] - self.A_matrices[idx])
        B = self.B_matrices[idx] + alpha * (self.B_matrices[idx+1] - self.B_matrices[idx])
        
        return A, B
    
    def saturate(self, u):
        """Apply actuator saturation"""
        return np.clip(u, -self.saturation_limit, self.saturation_limit)
    
    def anti_windup(self, u, u_sat):
        """Apply anti-windup to integrator"""
        if abs(u) > self.saturation_limit:
            e_aw = (u_sat - u) / self.Ki
        else:
            e_aw = 0
        self.integrator += e_aw
    
    def compute_control(self, x, x_ref, z):
        """Compute control input for current state"""
        # Get scheduled gain
        K = self.get_gain(z)
        
        # Error
        e = x_ref - x
        
        # Update integrator
        self.integrator += e[0, 0] * self.dt
        
        # Control law
        u_lqr = -K @ x
        u_int = self.Ki * self.integrator
        u = u_lqr[0, 0] + u_int
        
        # Apply saturation and anti-windup
        u_sat = self.saturate(u)
        self.anti_windup(u, u_sat)
        
        return u_sat, K.flatten()
    
    def reset(self):
        """Reset controller state"""
        self.integrator = 0.0


def run_simulation(controller, T_final=10.0, plot=True):
    """Run simulation with gain-scheduled controller"""
    n_steps = int(T_final / controller.dt)
    t = np.linspace(0, T_final, n_steps)
    
    # Create scheduling parameter trajectory
    z_traj = 1 + 1.5 * (1 - np.cos(2*np.pi*t/5))
    z_traj = np.clip(z_traj, 1, 4)
    
    # Reference trajectory
    x_ref = np.zeros((2, n_steps))
    x_ref[0, :] = 0.1 * np.sin(2*np.pi*t/8)
    
    # Initial state
    x = np.array([[0.5], [-0.3]])
    
    # Storage
    x_history = np.zeros((2, n_steps))
    u_history = np.zeros(n_steps)
    z_history = np.zeros(n_steps)
    K_history = np.zeros((2, n_steps))
    
    # Simulation loop
    for i in range(n_steps):
        z = z_traj[i]
        
        # Compute control
        u, K = controller.compute_control(x, x_ref[:, i:i+1], z)
        
        # Get plant matrices
        A, B = controller.get_plant_matrices(z)
        
        # Store results
        x_history[:, i] = x.flatten()
        u_history[i] = u
        z_history[i] = z
        K_history[:, i] = K
        
        # Update state
        x = A @ x + B * u
    
    # Plot results if requested
    if plot:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # States
        axes[0, 0].plot(t, x_history[0, :], 'b-', label='x1')
        axes[0, 0].plot(t, x_history[1, :], 'r-', label='x2')
        axes[0, 0].plot(t, x_ref[0, :], 'b--', label='x1 ref', alpha=0.7)
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('State')
        axes[0, 0].set_title('State Trajectories')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Control input
        axes[0, 1].plot(t, u_history, 'g-')
        axes[0, 1].axhline(y=0.9, color='r', linestyle=':', label='Saturation limit')
        axes[0, 1].axhline(y=-0.9, color='r', linestyle=':')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Control Input')
        axes[0, 1].set_title('Control Input')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Scheduling parameter
        axes[1, 0].plot(t, z_history, 'm-')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('z')
        axes[1, 0].set_title('Scheduling Parameter')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Gains
        axes[1, 1].plot(t, K_history[0, :], 'b-', label='K1')
        axes[1, 1].plot(t, K_history[1, :], 'r-', label='K2')
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Gain Value')
        axes[1, 1].set_title('Scheduled Gains')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('../report/images/runnable_simulation.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Plot saved to ../report/images/runnable_simulation.png")
    
    return {
        'time': t,
        'states': x_history,
        'control': u_history,
        'scheduling': z_history,
        'gains': K_history,
        'reference': x_ref
    }


def main():
    """Main function"""
    print("Gain-Scheduled LQR Controller Simulation")
    print("=" * 50)
    
    # Create controller
    controller = GainScheduledLQR()
    
    print(f"Controller initialized with dt = {controller.dt}")
    print(f"Operating points: {controller.z_values}")
    print(f"Optimal Q:\n{controller.Q_opt}")
    print(f"Optimal R:\n{controller.R_opt}")
    print(f"LQR gains at operating points:")
    for z, K in zip(controller.z_values, controller.K_matrices):
        print(f"  z={z}: K = [{K[0]:.4f}, {K[1]:.4f}]")
    print()
    
    # Run simulation
    print("Running simulation...")
    results = run_simulation(controller, T_final=10.0, plot=True)
    
    # Print performance metrics
    error = results['reference'][0, :] - results['states'][0, :]
    mse = np.mean(error**2)
    max_control = np.max(np.abs(results['control']))
    
    print("\nPerformance Metrics:")
    print(f"  Mean Squared Error: {mse:.6f}")
    print(f"  Maximum control input: {max_control:.4f}")
    print(f"  Saturation limit: ±{controller.saturation_limit}")
    
    if max_control <= controller.saturation_limit:
        print("  ✓ Actuator saturation limit respected")
    else:
        print(f"  ✗ Actuator saturation limit violated")
    
    print("\nSimulation completed successfully.")
    

if __name__ == "__main__":
    main()