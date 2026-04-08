import numpy as np
import control as ct
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Load saved data
K_array = np.load('../outputs/K_matrices.npy')
z_values = np.load('../outputs/z_values.npy')

# Load plant linearizations
import json
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']
weights = data['weights']

Q = np.array(weights['Q'])
R = np.array(weights['R'])

# Create interpolation functions for gain scheduling
K1_interp = interp1d(z_values, K_array[:, 0], kind='linear', fill_value='extrapolate')
K2_interp = interp1d(z_values, K_array[:, 1], kind='linear', fill_value='extrapolate')

def get_scheduled_gain(z):
    """Get LQR gain for given scheduling parameter z"""
    k1 = K1_interp(z)
    k2 = K2_interp(z)
    return np.array([[k1, k2]])

# Define weighting functions for H-infinity analysis
# Simple weights as specified in requirements
W1 = ct.tf([1], [1, 0])  # Weight for performance
W2 = ct.tf([0.1], [1])   # Weight for control effort

print("Weighting functions:")
print(f"W1(s) = {W1}")
print(f"W2(s) = {W2}")
print()

# Analyze H-infinity norm for each operating point and interpolated points
n_segments = 20  # Analyze more points for smooth interpolation
z_analysis = np.linspace(z_values[0], z_values[-1], n_segments)

hinf_norms = []

for z in z_analysis:
    # Find nearest plant matrices (using interpolation)
    idx = np.searchsorted(z_values, z) - 1
    idx = max(0, min(len(z_values)-2, idx))
    
    z_low = z_values[idx]
    z_high = z_values[idx+1]
    alpha = (z - z_low) / (z_high - z_low)
    
    A_low = np.array(points[idx]['A'])
    B_low = np.array(points[idx]['B'])
    A_high = np.array(points[idx+1]['A'])
    B_high = np.array(points[idx+1]['B'])
    
    A = A_low + alpha * (A_high - A_low)
    B = B_low + alpha * (B_high - B_high)
    
    # Get scheduled gain
    K = get_scheduled_gain(z)
    
    # Closed-loop system: x(k+1) = (A - BK)x(k) + Bw(k)
    # y(k) = Cx(k) where C = I (full state feedback)
    A_cl = A - B @ K
    
    # Create discrete-time system
    sys_cl = ct.ss(A_cl, B, np.eye(2), np.zeros((2, 1)), dt)
    
    # For discrete-time systems, we can compute H-infinity norm directly
    # or convert to continuous using d2c
    try:
        # Try to compute H-infinity norm for discrete system
        # Convert to continuous for analysis
        sys_cl_cont = ct.d2c(sys_cl, method='tustin')
        hinf_norm = ct.hinfnorm(sys_cl_cont)[0]
    except:
        # Alternative: compute maximum singular value
        omega = np.logspace(-2, 2, 200)
        mag, phase, omega = ct.bode(sys_cl, omega, plot=False)
        hinf_norm = np.max(mag)
    
    hinf_norms.append(hinf_norm)
    
    print(f"z = {z:.2f}: H-infinity norm = {hinf_norm:.4f}")

# Check if all norms are below 1.0
max_norm = np.max(hinf_norms)
print(f"\nMaximum H-infinity norm: {max_norm:.4f}")
if max_norm < 1.0:
    print("✓ All H-infinity norms are below 1.0 (requirement satisfied)")
else:
    print(f"✗ H-infinity norm exceeds 1.0 at some points (max = {max_norm:.4f})")

# Plot H-infinity norms across operating range
plt.figure(figsize=(10, 6))
plt.plot(z_analysis, hinf_norms, 'b-o', linewidth=2, markersize=6)
plt.axhline(y=1.0, color='r', linestyle='--', linewidth=2, label='Requirement (1.0)')
plt.fill_between(z_analysis, 0, 1.0, alpha=0.2, color='green', label='Acceptable region')
plt.xlabel('Scheduling Parameter z')
plt.ylabel('H-infinity Norm')
plt.title('H-infinity Norm Analysis Across Operating Range')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('../report/images/hinf_norms.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nH-infinity analysis completed. Plot saved to ../report/images/hinf_norms.png")