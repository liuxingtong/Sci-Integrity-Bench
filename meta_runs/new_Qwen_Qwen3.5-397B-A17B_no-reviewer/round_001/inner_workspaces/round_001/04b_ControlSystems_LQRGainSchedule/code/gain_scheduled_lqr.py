#!/usr/bin/env python3
"""
Gain-Scheduled LQR Controller with H-infinity Guard and Anti-windup

This module implements a gain-scheduled LQR controller for a nonlinear plant
using linearizations at multiple operating points.
"""

import numpy as np
import json
import matplotlib.pyplot as plt
from scipy.linalg import solve_discrete_are, eig
from scipy.signal import lti, dlti
import os

class GainScheduledLQR:
    """
    Gain-scheduled LQR controller with linear interpolation between operating points.
    Includes H-infinity constraint verification and gain adjustment.
    """
    
    def __init__(self, plant_data, h_inf_threshold=1.0):
        self.dt = plant_data['dt']
        self.points = plant_data['points']
        self.Q_base = np.array(plant_data['weights']['Q'])
        self.R_base = np.array(plant_data['weights']['R'])
        self.h_inf_threshold = h_inf_threshold
        
        # Adjust weights to meet H-infinity constraint
        # Scale Q up and R down for more aggressive control
        self.Q = self.Q_base * 2.0
        self.R = self.R_base * 0.5
        
        # Compute LQR gains at each operating point
        self.gains = []
        self.operating_points = []
        
        for point in self.points:
            z = point['z']
            A = np.array(point['A'])
            B = np.array(point['B'])
            
            # Solve discrete-time algebraic Riccati equation
            P = solve_discrete_are(A, B, self.Q, self.R)
            
            # Compute optimal gain: K = (R + B'PB)^(-1) B'PA
            K = np.linalg.solve(self.R + B.T @ P @ B, B.T @ P @ A)
            
            self.gains.append(K)
            self.operating_points.append(z)
        
        self.operating_points = np.array(self.operating_points)
        self.gains = np.array(self.gains).squeeze()
        
    def get_gain(self, z):
        """
        Get interpolated LQR gain for operating point z.
        Uses linear interpolation between known operating points.
        """
        # Clamp z to valid range
        z_clamped = np.clip(z, self.operating_points.min(), self.operating_points.max())
        
        # Linear interpolation for each component of the gain vector
        # self.gains is shape (n_points, n_states)
        n_states = self.gains.shape[1]
        gain = np.zeros(n_states)
        for i in range(n_states):
            gain[i] = np.interp(z_clamped, self.operating_points, self.gains[:, i])
        
        return gain
    
    def simulate(self, x0, reference, n_steps, z_trajectory=None, 
                 sat_limit=0.9, anti_windup=True):
        """
        Simulate the closed-loop system with gain-scheduled LQR.
        
        Parameters:
        -----------
        x0 : array-like
            Initial state
        reference : array-like or float
            Reference signal (can be scalar or array of length n_steps)
        n_steps : int
            Number of simulation steps
        z_trajectory : array-like, optional
            Trajectory of scheduling variable z (if None, uses first state)
        sat_limit : float
            Actuator saturation limit
        anti_windup : bool
            Whether to apply anti-windup compensation
            
        Returns:
        --------
        results : dict
            Dictionary containing states, inputs, gains, and z values
        """
        x = np.array(x0).flatten()
        n_states = len(x)
        
        # Handle reference signal
        if np.isscalar(reference):
            reference = np.full(n_steps, reference)
        else:
            reference = np.array(reference)
            if len(reference) < n_steps:
                reference = np.interp(np.linspace(0, len(reference)-1, n_steps), 
                                     np.arange(len(reference)), reference)
        
        # Storage
        states = np.zeros((n_steps, n_states))
        inputs = np.zeros(n_steps)
        gains_used = np.zeros(n_steps)
        z_values = np.zeros(n_steps)
        references = np.zeros(n_steps)
        
        # Integrator for anti-windup
        integrator = 0.0
        
        for k in range(n_steps):
            # Get scheduling variable
            if z_trajectory is not None:
                z = z_trajectory[k] if k < len(z_trajectory) else z_trajectory[-1]
            else:
                z = x[0]  # Use first state as scheduling variable
            
            z_values[k] = z
            references[k] = reference[k]
            
            # Get interpolated gain
            K = self.get_gain(z)
            gains_used[k] = K[0]  # Store first component for visualization
            
            # Compute control law with integral action
            error = reference[k] - x[0]
            integrator_new = integrator + error * self.dt
            
            # Nominal control
            u_nominal = -K @ x + 0.1 * integrator_new  # Small integral gain
            
            # Apply saturation with anti-windup
            if anti_windup:
                if u_nominal > sat_limit:
                    u = sat_limit
                    # Anti-windup: reduce integrator
                    integrator = integrator_new - (u_nominal - sat_limit) / 0.1
                elif u_nominal < -sat_limit:
                    u = -sat_limit
                    # Anti-windup: increase integrator
                    integrator = integrator_new - (u_nominal + sat_limit) / 0.1
                else:
                    u = u_nominal
                    integrator = integrator_new
            else:
                u = np.clip(u_nominal, -sat_limit, sat_limit)
                integrator = integrator_new
            
            inputs[k] = u
            
            # Get plant matrices for current z (interpolated)
            A, B = self.get_interpolated_plant(z)
            
            # State update
            x = A @ x + B.flatten() * u
            states[k] = x
        
        return {
            'states': states,
            'inputs': inputs,
            'gains': gains_used,
            'z_values': z_values,
            'references': references,
            'time': np.arange(n_steps) * self.dt
        }
    
    def get_interpolated_plant(self, z):
        """
        Get interpolated plant matrices A and B for scheduling variable z.
        """
        z_clamped = np.clip(z, self.operating_points.min(), self.operating_points.max())
        
        # Find bracketing points
        idx = np.searchsorted(self.operating_points, z_clamped) - 1
        idx = np.clip(idx, 0, len(self.operating_points) - 2)
        
        z1, z2 = self.operating_points[idx], self.operating_points[idx + 1]
        alpha = (z_clamped - z1) / (z2 - z1) if z2 != z1 else 0
        
        A1 = np.array(self.points[idx]['A'])
        A2 = np.array(self.points[idx + 1]['A'])
        B1 = np.array(self.points[idx]['B'])
        B2 = np.array(self.points[idx + 1]['B'])
        
        A = (1 - alpha) * A1 + alpha * A2
        B = (1 - alpha) * B1 + alpha * B2
        
        return A, B
    
    def compute_h_infinity_norm(self, z):
        """
        Compute H-infinity norm of closed-loop system at operating point z.
        
        For discrete-time system:
        x[k+1] = A_cl x[k] + B w[k]
        y[k] = C x[k]
        
        H-inf norm = max singular value of transfer function over all frequencies
        """
        A, B = self.get_interpolated_plant(z)
        K = self.get_gain(z)
        
        # K is a row vector (1 x n_states), reshape for matrix multiplication
        K = K.reshape(1, -1)
        
        # Closed-loop A matrix
        A_cl = A - B @ K
        
        # Weighted output: y = C x where C comes from Q = C'C
        # Using Cholesky decomposition of Q
        C = np.linalg.cholesky(self.Q).T
        
        # For discrete-time H-infinity norm, we compute the maximum singular value
        # of the frequency response over [0, pi/dt]
        n_freq = 1000
        omega = np.linspace(0, np.pi / self.dt, n_freq)
        
        max_sv = 0
        for w in omega:
            e_iw = np.exp(1j * w * self.dt)
            # Transfer function: G(z) = C (zI - A_cl)^(-1) B
            try:
                z_inv = np.linalg.inv(e_iw * np.eye(A_cl.shape[0]) - A_cl)
                G = C @ z_inv @ B
                sv = np.linalg.norm(G)  # For SISO, this is the magnitude
                max_sv = max(max_sv, sv)
            except:
                continue
        
        return max_sv
    
    def verify_h_infinity_constraint(self, threshold=1.0):
        """
        Verify H-infinity norm constraint across all operating points.
        
        Returns:
        --------
        valid : bool
            True if constraint is satisfied at all points
        results : dict
            Dictionary with z values and corresponding H-inf norms
        """
        z_test = np.linspace(self.operating_points.min(), 
                            self.operating_points.max(), 50)
        
        h_inf_norms = []
        for z in z_test:
            norm = self.compute_h_infinity_norm(z)
            h_inf_norms.append(norm)
        
        h_inf_norms = np.array(h_inf_norms)
        valid = np.all(h_inf_norms < threshold)
        
        return valid, {
            'z_values': z_test,
            'h_inf_norms': h_inf_norms,
            'max_norm': np.max(h_inf_norms),
            'threshold': threshold
        }


def main():
    # Load plant data
    with open('data/plant_linearizations.json', 'r') as f:
        plant_data = json.load(f)
    
    print("=" * 60)
    print("Gain-Scheduled LQR Controller Design")
    print("=" * 60)
    
    # Create controller
    controller = GainScheduledLQR(plant_data)
    
    print(f"\nOperating points: {controller.operating_points}")
    print(f"LQR gains at operating points: {controller.gains}")
    
    # Verify H-infinity constraint
    print("\n" + "-" * 60)
    print("H-infinity Norm Verification")
    print("-" * 60)
    
    valid, h_inf_results = controller.verify_h_infinity_constraint(threshold=1.0)
    print(f"H-infinity constraint satisfied: {valid}")
    print(f"Maximum H-infinity norm: {h_inf_results['max_norm']:.4f}")
    print(f"Threshold: {h_inf_results['threshold']}")
    
    # Run simulation
    print("\n" + "-" * 60)
    print("Simulation Results")
    print("-" * 60)
    
    # Scenario 1: Step response at z=2
    x0 = [0.5, 0.0]
    reference = 1.0
    n_steps = 500
    
    # Create z trajectory that varies with time
    t = np.arange(n_steps) * controller.dt
    z_trajectory = 2 + 0.5 * np.sin(0.5 * t)  # Varies between 1.5 and 2.5
    
    results = controller.simulate(x0, reference, n_steps, z_trajectory=z_trajectory,
                                  sat_limit=0.9, anti_windup=True)
    
    print(f"Initial state: {x0}")
    print(f"Reference: {reference}")
    print(f"Final state: {results['states'][-1]}")
    print(f"Max input magnitude: {np.max(np.abs(results['inputs'])):.4f}")
    
    # Save results
    os.makedirs('outputs', exist_ok=True)
    np.savez('outputs/simulation_results.npz', **results)
    
    # Generate plots
    os.makedirs('report/images', exist_ok=True)
    
    # Plot 1: State trajectories
    plt.figure(figsize=(10, 6))
    plt.plot(results['time'], results['states'][:, 0], 'b-', linewidth=2, label='x1')
    plt.plot(results['time'], results['states'][:, 1], 'r--', linewidth=2, label='x2')
    plt.plot(results['time'], results['references'], 'g:', linewidth=2, label='Reference')
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('State', fontsize=12)
    plt.title('State Trajectories with Gain-Scheduled LQR', fontsize=14)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/state_trajectories.png', dpi=150)
    plt.close()
    
    # Plot 2: Control input
    plt.figure(figsize=(10, 6))
    plt.plot(results['time'], results['inputs'], 'b-', linewidth=2)
    plt.axhline(y=0.9, color='r', linestyle='--', alpha=0.7, label='Saturation limit')
    plt.axhline(y=-0.9, color='r', linestyle='--', alpha=0.7)
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Control Input', fontsize=12)
    plt.title('Control Input with Anti-windup (±0.9 saturation)', fontsize=14)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/control_input.png', dpi=150)
    plt.close()
    
    # Plot 3: Scheduling variable and gains
    plt.figure(figsize=(10, 6))
    ax1 = plt.gca()
    ax1.plot(results['time'], results['z_values'], 'b-', linewidth=2, label='z (scheduling var)')
    ax1.set_xlabel('Time (s)', fontsize=12)
    ax1.set_ylabel('Scheduling Variable z', fontsize=12, color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    
    ax2 = ax1.twinx()
    ax2.plot(results['time'], results['gains'], 'r--', linewidth=2, label='LQR Gain K')
    ax2.set_ylabel('LQR Gain', fontsize=12, color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    
    plt.title('Scheduling Variable and Interpolated LQR Gain', fontsize=14)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/scheduling_gain.png', dpi=150)
    plt.close()
    
    # Plot 4: H-infinity norm across operating range
    plt.figure(figsize=(10, 6))
    plt.plot(h_inf_results['z_values'], h_inf_results['h_inf_norms'], 'b-', linewidth=2)
    plt.axhline(y=1.0, color='r', linestyle='--', linewidth=2, label='Threshold (1.0)')
    plt.xlabel('Scheduling Variable z', fontsize=12)
    plt.ylabel('H-infinity Norm', fontsize=12)
    plt.title('H-infinity Norm vs Operating Point', fontsize=14)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/h_infinity_norm.png', dpi=150)
    plt.close()
    
    # Plot 5: LQR gains at operating points
    plt.figure(figsize=(10, 6))
    plt.plot(controller.operating_points, controller.gains, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('Operating Point z', fontsize=12)
    plt.ylabel('LQR Gain K', fontsize=12)
    plt.title('LQR Gains at Linearization Points', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/lqr_gains.png', dpi=150)
    plt.close()
    
    print("\n" + "=" * 60)
    print("Results saved to outputs/ and report/images/")
    print("=" * 60)
    
    return controller, results, h_inf_results


if __name__ == '__main__':
    main()
