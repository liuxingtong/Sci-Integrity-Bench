import json
import numpy as np
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
print(f"Number of operating points: {len(points)}")
print(f"Q matrix:\n{Q}")
print(f"R matrix:\n{R}")

# Extract operating points
z_values = [p['z'] for p in points]
A_matrices = [np.array(p['A']) for p in points]
B_matrices = [np.array(p['B']) for p in points]

print(f"\nOperating points (z): {z_values}")
print(f"\nSystem dimensions:")
print(f"A shape: {A_matrices[0].shape}")
print(f"B shape: {B_matrices[0].shape}")
print(f"Q shape: {Q.shape}")
print(f"R shape: {R.shape}")

# Function to compute discrete-time LQR gain
def dlqr(A, B, Q, R):
    """
    Solve the discrete-time LQR controller.
    Returns the optimal gain matrix K.
    """
    # Solve discrete-time algebraic Riccati equation
    P = solve_discrete_are(A, B, Q, R)
    
    # Compute optimal gain
    K = np.linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
    return K

# Compute LQR gains for each operating point
K_gains = []
for i, (A, B) in enumerate(zip(A_matrices, B_matrices)):
    K = dlqr(A, B, Q, R)
    K_gains.append(K)
    print(f"\nOperating point z={z_values[i]}:")
    print(f"A:\n{A}")
    print(f"B:\n{B}")
    print(f"LQR gain K: {K.flatten()}")

# Save gains for later use
K_array = np.array([K.flatten() for K in K_gains])
np.save('outputs/lqr_gains.npy', K_array)
np.save('outputs/z_values.npy', np.array(z_values))

print(f"\nLQR gains saved to outputs/lqr_gains.npy")

# Also save to main outputs directory for easy access
np.save('../outputs/lqr_gains.npy', K_array)
np.save('../outputs/z_values.npy', np.array(z_values))
