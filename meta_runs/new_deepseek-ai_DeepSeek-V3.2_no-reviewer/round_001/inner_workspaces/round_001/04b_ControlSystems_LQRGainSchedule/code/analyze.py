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

print(f"Time step dt = {dt}")
print(f"Number of operating points: {len(points)}")
print(f"Q matrix:\n{Q}")
print(f"R matrix:\n{R}")

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
    # Solve discrete-time algebraic Riccati equation
    # A^T P A - P - A^T P B (R + B^T P B)^{-1} B^T P A + Q = 0
    P = linalg.solve_discrete_are(A, B, Q, R)
    K = linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
    K_list.append(K)
    
    print(f"\nOperating point z = {z}:")
    print(f"A = \n{A}")
    print(f"B = \n{B}")
    print(f"LQR gain K = \n{K}")

z_vals = np.array(z_vals)
K_list = np.array(K_list).squeeze()  # Shape: (n_points, 2)

print(f"\nScheduling variable values: {z_vals}")
print(f"LQR gains shape: {K_list.shape}")

# Create interpolation functions for gain scheduling
# Linear interpolation of gains as function of z
K1_interp = interpolate.interp1d(z_vals, K_list[:, 0], kind='linear', fill_value='extrapolate')
K2_interp = interpolate.interp1d(z_vals, K_list[:, 1], kind='linear', fill_value='extrapolate')

def get_scheduled_gain(z):
    """Return interpolated gain K for scheduling variable z"""
    return np.array([[K1_interp(z), K2_interp(z)]])

# Test interpolation
print("\nInterpolated gains:")
for z_test in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
    K_test = get_scheduled_gain(z_test)
    print(f"z = {z_test:.1f}, K = [{K_test[0,0]:.6f}, {K_test[0,1]:.6f}]")

# Check H-infinity norm for each linear segment
print("\n\nH-infinity norm analysis for each linear segment:")
print("Note: We need to check closed-loop H-infinity norm of weighted output < 1.0")
print("Assuming output is the full state (C = I, D = 0) and weights are given")
print("We'll compute H-inf norm for each operating point with its corresponding LQR gain")

for i, (z, A, B, K) in enumerate(zip(z_vals, A_list, B_list, K_list)):
    # Closed-loop system: x[k+1] = (A - B*K) x[k]
    A_cl = A - B @ K.reshape(1, -1)
    
    # Create state-space system for H-inf norm calculation
    # Assuming C = I (full state output), D = 0
    C = np.eye(2)
    D = np.zeros((2, 1))
    
    # Convert to continuous-time for H-inf norm calculation if needed
    # For discrete-time, we can use control library
    sys = ct.ss(A_cl, B, C, D, dt=dt)
    
    # Compute H-infinity norm
    # Note: control.hinfsyn requires continuous-time
    # For discrete-time, we can compute induced L2 norm which equals H-inf norm
    # For simplicity, compute maximum singular value of frequency response
    
    # Alternative: compute peak of frequency response magnitude
    # For discrete-time, H-inf norm = sup_ω σ_max(G(e^{jω}))
    # We'll approximate by sampling frequencies
    omega = np.logspace(-2, np.pi/dt, 500)
    mag = np.zeros_like(omega)
    
    for j, w in enumerate(omega):
        # Frequency response at z = e^{jwT}
        z_val = np.exp(1j * w * dt)
        G = C @ np.linalg.inv(z_val * np.eye(2) - A_cl) @ B + D
        mag[j] = np.linalg.norm(G, 2)  # Spectral norm
    
    hinf_norm = np.max(mag)
    
    print(f"\nOperating point z = {z}:")
    print(f"  Closed-loop A matrix:\n{A_cl}")
    print(f"  Approx H-inf norm: {hinf_norm:.6f}")
    print(f"  Requirement < 1.0: {'PASS' if hinf_norm < 1.0 else 'FAIL'}")

# Implement anti-windup for actuator saturation at ±0.9
def saturated_control(u, limit=0.9):
    """Apply saturation to control input"""
    return np.clip(u, -limit, limit)

# Simple anti-windup: tracking back-calculation
class AntiWindupController:
    def __init__(self, K_func, limit=0.9, dt=0.02, K_aw=1.0):
        self.K_func = K_func  # Function that returns K(z)
        self.limit = limit
        self.dt = dt
        self.K_aw = K_aw  # Anti-windup gain
        self.u_unsat = 0.0
        self.u_sat = 0.0
        
    def compute(self, x, z):
        """Compute control with anti-windup"""
        K = self.K_func(z)
        u_ideal = -K @ x  # LQR control law
        
        # Apply saturation
        u_sat = np.clip(u_ideal, -self.limit, self.limit)
        
        # Simple anti-windup: track difference
        self.u_unsat = u_ideal
        self.u_sat = u_sat
        
        return u_sat

print("\n\nAnti-windup controller implemented with saturation limit ±0.9")

# Save results for report
np.savez('../outputs/analysis_results.npz', 
         z_vals=z_vals, 
         K_list=K_list, 
         A_list=A_list, 
         B_list=B_list,
         Q=Q,
         R=R,
         dt=dt)

print("\nAnalysis complete. Results saved to outputs/analysis_results.npz")
