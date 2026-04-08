import numpy as np
import json
import matplotlib.pyplot as plt
from scipy.linalg import solve_discrete_are
import control as ct

# Load plant linearizations
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']
weights = data['weights']

Q = np.array(weights['Q'])
R = np.array(weights['R'])

print(f"Sampling time dt = {dt}")
print(f"Q matrix:\n{Q}")
print(f"R matrix:\n{R}")
print(f"\nNumber of operating points: {len(points)}")

# Extract operating points
z_values = [p['z'] for p in points]
A_matrices = [np.array(p['A']) for p in points]
B_matrices = [np.array(p['B']) for p in points]

print(f"\nOperating points (z): {z_values}")

# Design LQR controllers for each operating point
K_matrices = []
for i, (A, B) in enumerate(zip(A_matrices, B_matrices)):
    print(f"\n--- Operating point z={z_values[i]} ---")
    print(f"A:\n{A}")
    print(f"B:\n{B}")
    
    # Solve discrete-time algebraic Riccati equation
    P = solve_discrete_are(A, B, Q, R)
    
    # Compute LQR gain: K = (B^T P B + R)^(-1) B^T P A
    K = np.linalg.inv(B.T @ P @ B + R) @ B.T @ P @ A
    K_matrices.append(K)
    
    print(f"LQR gain K: {K.flatten()}")
    
    # Check closed-loop stability
    A_cl = A - B @ K
    eigvals = np.linalg.eigvals(A_cl)
    print(f"Closed-loop eigenvalues: {eigvals}")
    print(f"Maximum eigenvalue magnitude: {np.max(np.abs(eigvals))}")
    
# Save K matrices for later use
K_array = np.array([K.flatten() for K in K_matrices])
np.save('../outputs/K_matrices.npy', K_array)
np.save('../outputs/z_values.npy', np.array(z_values))

print(f"\nK matrices saved to ../outputs/K_matrices.npy")
print(f"z values saved to ../outputs/z_values.npy")