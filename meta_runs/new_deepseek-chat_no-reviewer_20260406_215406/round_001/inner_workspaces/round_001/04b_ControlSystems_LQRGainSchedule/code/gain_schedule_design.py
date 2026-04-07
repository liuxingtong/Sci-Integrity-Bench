import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import solve_discrete_are
import control as ct
from scipy import interpolate

# Load plant linearizations
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']
weights = data['weights']

Q = np.array(weights['Q'])
R = np.array(weights['R'])

# Extract operating points
z_values = np.array([p['z'] for p in points])
A_matrices = [np.array(p['A']) for p in points]
B_matrices = [np.array(p['B']) for p in points]

# Function to compute discrete-time LQR gain
def dlqr(A, B, Q, R):
    """Solve the discrete-time LQR controller."""
    P = solve_discrete_are(A, B, Q, R)
    K = np.linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
    return K

# Compute LQR gains for each operating point
K_gains = []
for i, (A, B) in enumerate(zip(A_matrices, B_matrices)):
    K = dlqr(A, B, Q, R)
    K_gains.append(K.flatten())

K_gains = np.array(K_gains)

# Create interpolation functions for gain scheduling
# Linear interpolation between operating points
K1_interp = interpolate.interp1d(z_values, K_gains[:, 0], kind='linear', fill_value='extrapolate')
K2_interp = interpolate.interp1d(z_values, K_gains[:, 1], kind='linear', fill_value='extrapolate')

# Function to get interpolated gain for any z value
def get_interpolated_gain(z):
    """Return interpolated LQR gain for given z."""
    k1 = K1_interp(z)
    k2 = K2_interp(z)
    return np.array([[k1, k2]])

# Test interpolation at intermediate points
print("Interpolated gains at sample points:")
for z_test in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
    K_test = get_interpolated_gain(z_test)
    print(f"z = {z_test:.1f}: K = [{K_test[0,0]:.6f}, {K_test[0,1]:.6f}]")

# Plot gain scheduling interpolation
z_fine = np.linspace(0.5, 4.5, 100)
K1_fine = K1_interp(z_fine)
K2_fine = K2_interp(z_fine)

plt.figure(figsize=(10, 6))
plt.subplot(2, 1, 1)
plt.plot(z_values, K_gains[:, 0], 'ro', label='Computed gains')
plt.plot(z_fine, K1_fine, 'b-', label='Interpolated')
plt.xlabel('Operating point z')
plt.ylabel('K[0] (first gain)')
plt.title('Gain Scheduling: First Component')
plt.grid(True)
plt.legend()

plt.subplot(2, 1, 2)
plt.plot(z_values, K_gains[:, 1], 'ro', label='Computed gains')
plt.plot(z_fine, K2_fine, 'b-', label='Interpolated')
plt.xlabel('Operating point z')
plt.ylabel('K[1] (second gain)')
plt.title('Gain Scheduling: Second Component')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.savefig('../report/images/gain_schedule_interpolation.png', dpi=300)
plt.close()

print("\nGain scheduling interpolation plot saved to report/images/gain_schedule_interpolation.png")

# Save interpolation functions for simulation
import pickle
with open('../outputs/gain_interpolation.pkl', 'wb') as f:
    pickle.dump({'K1_interp': K1_interp, 'K2_interp': K2_interp, 'z_values': z_values, 'K_gains': K_gains}, f)

print("Interpolation functions saved to outputs/gain_interpolation.pkl")
