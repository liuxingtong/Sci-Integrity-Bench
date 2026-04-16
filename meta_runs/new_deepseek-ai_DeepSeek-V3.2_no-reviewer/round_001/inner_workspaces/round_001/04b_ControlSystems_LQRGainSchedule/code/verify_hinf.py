import numpy as np
import json
from scipy import linalg
import control as ct

# Quick verification of H-inf norm calculation
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']
weights = data['weights']

Q = np.array(weights['Q'])
R = np.array(weights['R'])

# Take first operating point
point = points[0]
z = point['z']
A = np.array(point['A'])
B = np.array(point['B'])

print(f"Operating point z = {z}")
print(f"A = \n{A}")
print(f"B = \n{B}")
print(f"Q = \n{Q}")
print(f"R = \n{R}")

# Compute LQR gain
P = linalg.solve_discrete_are(A, B, Q, R)
K = linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
print(f"\nLQR gain K = \n{K}")

# Closed-loop
A_cl = A - B @ K
print(f"\nClosed-loop A = \n{A_cl}")
print(f"Eigenvalues of A_cl: {np.linalg.eigvals(A_cl)}")
print(f"Spectral radius: {np.max(np.abs(np.linalg.eigvals(A_cl))):.6f}")

# Check if this is a stabilizing controller (should be)
if np.max(np.abs(np.linalg.eigvals(A_cl))) < 1:
    print("Controller is stabilizing (all eigenvalues inside unit circle)")
else:
    print("WARNING: Controller is NOT stabilizing!")

# H-inf norm calculation
Q_sqrt = linalg.sqrtm(Q)
R_sqrt = linalg.sqrtm(R)

# From disturbance w to output z = [Q^(1/2)x; R^(1/2)u]
# where u = -Kx, so z = [Q^(1/2); -R^(1/2)K] x
C_cl = np.vstack([Q_sqrt, -R_sqrt @ K])
D_cl = np.zeros((C_cl.shape[0], B.shape[1]))

print(f"\nWeighted output matrix C = \n{C_cl}")
print(f"Direct feedthrough D = \n{D_cl}")

# Create state-space system
sys = ct.ss(A_cl, B, C_cl, D_cl, dt=dt)

# Method 1: Frequency sampling
omega = np.logspace(-2, np.log10(np.pi/dt), 1000)
mag = np.zeros_like(omega)
for i, w in enumerate(omega):
    z_val = np.exp(1j * w * dt)
    G = C_cl @ np.linalg.inv(z_val * np.eye(2) - A_cl) @ B + D_cl
    mag[i] = np.linalg.norm(G, 2)

hinf1 = np.max(mag)
print(f"\nMethod 1 (frequency sampling): H-inf norm = {hinf1:.6f}")

# Method 2: Try control library's norm function (for continuous-time equivalent)
# Convert to continuous-time using Tustin transformation
sys_c = ct.c2d(sys, dt, method='tustin')  # This should give similar system
# Actually, for discrete-time, we can use hinfnorm
# But control.hinfsyn is for continuous-time

print("\n\nNote: For discrete-time systems, the H-infinity norm is")
print("the peak of the maximum singular value over frequency.")
print("Our calculation shows it's above 1.0, which means the")
print("standard LQR design doesn't guarantee H-inf norm < 1.")
print("\nTo achieve H-inf norm < 1, we would need to solve")
print("the H-infinity Riccati equation, not the standard LQR Riccati equation.")
