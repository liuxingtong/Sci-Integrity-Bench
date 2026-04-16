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

# More accurate H-infinity norm calculation
print("\n\nAccurate H-infinity norm calculation:")
print("We need to compute the H-inf norm of the weighted closed-loop system.")
print("Assuming the weights are Q and R from LQR design...")
print("For LQR, the cost function is J = Σ x'Qx + u'Ru")
print("The closed-loop H-inf norm from disturbance to weighted output should be < 1")
print("\nLet's define the weighted output as:")
print("  z = [Q^(1/2) x; R^(1/2) u]")
print("where u = -Kx")
print("So z = [Q^(1/2); -R^(1/2)K] x = C_cl x")

# Compute Cholesky decompositions for square roots
Q_sqrt = linalg.sqrtm(Q)  # Square root of Q
R_sqrt = linalg.sqrtm(R)  # Square root of R

print(f"\nQ^(1/2) = \n{Q_sqrt}")
print(f"R^(1/2) = \n{R_sqrt}")

hinf_results = []

for i, (z, A, B, K) in enumerate(zip(z_vals, A_list, B_list, K_list)):
    # Closed-loop system: x[k+1] = (A - B*K) x[k] + B * w (disturbance)
    # We consider disturbance entering through B matrix
    A_cl = A - B @ K.reshape(1, -1)
    B_cl = B  # Disturbance enters through same channel as control
    
    # Weighted output: z = [Q^(1/2) x; R^(1/2) u] where u = -Kx
    # So C_cl = [Q^(1/2); -R^(1/2) K]
    C_cl = np.vstack([Q_sqrt, -R_sqrt @ K.reshape(1, -1)])
    D_cl = np.zeros((C_cl.shape[0], B_cl.shape[1]))
    
    # Create discrete-time system
    sys_cl = ct.ss(A_cl, B_cl, C_cl, D_cl, dt=dt)
    
    # Compute H-infinity norm more accurately
    # For discrete-time systems, H-inf norm = sup_ω σ_max(G(e^{jω}))
    # We can compute using frequency response
    
    # Generate frequency grid
    n_freq = 1000
    omega = np.logspace(-2, np.log10(np.pi/dt), n_freq)
    
    # Compute frequency response
    mag = np.zeros(n_freq)
    for j, w in enumerate(omega):
        # Frequency response at z = e^{jwT}
        z_val = np.exp(1j * w * dt)
        G = C_cl @ np.linalg.inv(z_val * np.eye(2) - A_cl) @ B_cl + D_cl
        mag[j] = np.linalg.norm(G, 2)  # Spectral norm
    
    hinf_norm = np.max(mag)
    freq_at_peak = omega[np.argmax(mag)]
    
    hinf_results.append({
        'z': z,
        'hinf_norm': hinf_norm,
        'freq_at_peak': freq_at_peak,
        'A_cl': A_cl,
        'pass': hinf_norm < 1.0
    })
    
    print(f"\nOperating point z = {z}:")
    print(f"  H-inf norm: {hinf_norm:.6f}")
    print(f"  Frequency at peak: {freq_at_peak:.4f} rad/s")
    print(f"  Requirement < 1.0: {'PASS' if hinf_norm < 1.0 else 'FAIL'}")

# Plot H-inf norm vs scheduling variable
plt.figure(figsize=(10, 6))
z_plot = np.linspace(min(z_vals), max(z_vals), 100)
hinf_plot = []

# For plotting, we need to interpolate gains first
K1_interp = interpolate.interp1d(z_vals, K_list[:, 0], kind='linear')
K2_interp = interpolate.interp1d(z_vals, K_list[:, 1], kind='linear')

for z in z_plot:
    # Find nearest operating point for A, B
    idx = np.argmin(np.abs(z_vals - z))
    A = A_list[idx]
    B = B_list[idx]
    
    # Interpolated gain
    K = np.array([[K1_interp(z), K2_interp(z)]])
    
    A_cl = A - B @ K
    B_cl = B
    C_cl = np.vstack([Q_sqrt, -R_sqrt @ K])
    D_cl = np.zeros((C_cl.shape[0], B_cl.shape[1]))
    
    # Compute H-inf norm at this z
    sys_cl = ct.ss(A_cl, B_cl, C_cl, D_cl, dt=dt)
    
    # Quick estimate of H-inf norm (sample fewer frequencies for speed)
    omega_test = np.logspace(-2, np.log10(np.pi/dt), 200)
    mag_test = []
    for w in omega_test:
        z_val = np.exp(1j * w * dt)
        G = C_cl @ np.linalg.inv(z_val * np.eye(2) - A_cl) @ B_cl + D_cl
        mag_test.append(np.linalg.norm(G, 2))
    
    hinf_plot.append(np.max(mag_test))

plt.plot(z_plot, hinf_plot, 'b-', linewidth=2, label='Interpolated H-inf norm')
plt.scatter(z_vals, [r['hinf_norm'] for r in hinf_results], c='r', s=100, zorder=5, label='Operating points')
plt.axhline(y=1.0, color='r', linestyle='--', label='Requirement (1.0)')
plt.xlabel('Scheduling variable z')
plt.ylabel('H-infinity norm')
plt.title('H-infinity Norm vs Scheduling Variable')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('../report/images/hinf_norm_vs_z.png', dpi=150)
plt.close()

print("\n\nFigure saved to report/images/hinf_norm_vs_z.png")

# Check if all points pass
all_pass = all(r['pass'] for r in hinf_results)
print(f"\nAll operating points pass H-inf < 1.0 requirement: {all_pass}")
if not all_pass:
    print("Warning: Some operating points fail the H-inf norm requirement!")
    for r in hinf_results:
        if not r['pass']:
            print(f"  z = {r['z']}: H-inf = {r['hinf_norm']:.6f} >= 1.0")

# Save detailed results
np.savez('../outputs/hinf_analysis.npz', 
         z_vals=z_vals,
         hinf_results=hinf_results,
         Q=Q,
         R=R,
         dt=dt)
