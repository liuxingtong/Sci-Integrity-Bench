import numpy as np
import json
from scipy import linalg
from scipy import interpolate

# Load data
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']
weights = data['weights']

Q = np.array(weights['Q'])
R = np.array(weights['R'])

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
    P = linalg.solve_discrete_are(A, B, Q, R)
    K = linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
    K_list.append(K)

z_vals = np.array(z_vals)
K_list = np.array(K_list).squeeze()  # Shape: (n_points, 2)

# Create interpolation functions for gain scheduling
K1_interp = interpolate.interp1d(z_vals, K_list[:, 0], kind='linear', fill_value='extrapolate')
K2_interp = interpolate.interp1d(z_vals, K_list[:, 1], kind='linear', fill_value='extrapolate')

def get_scheduled_gain(z):
    """Return interpolated gain K for scheduling variable z"""
    return np.array([[K1_interp(z), K2_interp(z)]])

# Test
x_test = np.array([0.5, -0.3])
z_test = 2.5
K_test = get_scheduled_gain(z_test)
print(f"K shape: {K_test.shape}")
print(f"K: {K_test}")
u_ideal_test = -K_test @ x_test
print(f"u_ideal shape: {u_ideal_test.shape}")
print(f"u_ideal: {u_ideal_test}")
print(f"u_ideal type: {type(u_ideal_test)}")
print(f"u_ideal.ndim: {u_ideal_test.ndim}")
print(f"u_ideal.size: {u_ideal_test.size}")
