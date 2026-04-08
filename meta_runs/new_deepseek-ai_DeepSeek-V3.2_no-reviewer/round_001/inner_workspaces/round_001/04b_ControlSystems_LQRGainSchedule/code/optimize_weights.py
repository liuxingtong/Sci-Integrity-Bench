import numpy as np
import control as ct
from scipy.linalg import solve_discrete_are
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# Load plant linearizations
import json
with open('../data/plant_linearizations.json', 'r') as f:
    data = json.load(f)

dt = data['dt']
points = data['points']
weights = data['weights']

Q_default = np.array(weights['Q'])
R_default = np.array(weights['R'])

print(f"Default Q:\n{Q_default}")
print(f"Default R:\n{R_default}")
print()

# Function to compute H-infinity norm for given Q, R
def compute_max_hinf(Q, R):
    hinf_norms = []
    
    for point in points:
        A = np.array(point['A'])
        B = np.array(point['B'])
        
        # Solve LQR
        P = solve_discrete_are(A, B, Q, R)
        K = np.linalg.inv(B.T @ P @ B + R) @ B.T @ P @ A
        
        # Closed-loop system
        A_cl = A - B @ K
        sys_cl = ct.ss(A_cl, B, np.eye(2), np.zeros((2, 1)), dt)
        
        # Convert to continuous for H-infinity analysis
        try:
            sys_cl_cont = ct.d2c(sys_cl, method='tustin')
            hinf_norm = ct.hinfnorm(sys_cl_cont)[0]
        except:
            # Fallback: compute maximum gain
            omega = np.logspace(-2, 2, 100)
            mag, phase, omega = ct.bode(sys_cl, omega, plot=False)
            hinf_norm = np.max(mag)
        
        hinf_norms.append(hinf_norm)
    
    return np.max(hinf_norms), hinf_norms

# Objective function for optimization
def objective(x):
    # x = [q11, q22, r] (diagonal Q and scalar R)
    Q = np.diag([x[0], x[1]])
    R = np.array([[x[2]]])
    
    max_hinf, _ = compute_max_hinf(Q, R)
    
    # Penalty for exceeding 1.0
    penalty = 100 * max(0, max_hinf - 1.0)
    
    # Also minimize control effort (small R)
    control_effort = x[2]
    
    return penalty + 0.1 * control_effort

# Initial guess (close to default)
x0 = [1.0, 1.0, 1.0]

# Bounds: Q positive definite, R positive
bounds = [(0.1, 10.0), (0.1, 10.0), (0.1, 10.0)]

print("Optimizing weights to satisfy H-infinity constraint...")
result = minimize(objective, x0, bounds=bounds, method='SLSQP', 
                  options={'maxiter': 100, 'ftol': 1e-6})

print(f"Optimization status: {result.success}")
print(f"Message: {result.message}")
print(f"Optimal weights: Q_diag = [{result.x[0]:.4f}, {result.x[1]:.4f}], R = {result.x[2]:.4f}")

# Compute with optimal weights
Q_opt = np.diag([result.x[0], result.x[1]])
R_opt = np.array([[result.x[2]]])

max_hinf_opt, hinf_norms_opt = compute_max_hinf(Q_opt, R_opt)
print(f"\nMaximum H-infinity norm with optimal weights: {max_hinf_opt:.4f}")

# Compare with default
max_hinf_default, hinf_norms_default = compute_max_hinf(Q_default, R_default)
print(f"Maximum H-infinity norm with default weights: {max_hinf_default:.4f}")

# Design LQR controllers with optimal weights
K_matrices_opt = []
z_values = [p['z'] for p in points]

for point in points:
    A = np.array(point['A'])
    B = np.array(point['B'])
    
    P = solve_discrete_are(A, B, Q_opt, R_opt)
    K = np.linalg.inv(B.T @ P @ B + R_opt) @ B.T @ P @ A
    K_matrices_opt.append(K)
    
    # Check closed-loop stability
    A_cl = A - B @ K
    eigvals = np.linalg.eigvals(A_cl)
    max_eig = np.max(np.abs(eigvals))
    
    print(f"z={point['z']}: K = [{K[0,0]:.4f}, {K[0,1]:.4f}], max|eig| = {max_eig:.4f}")

# Save optimal weights and gains
np.save('../outputs/Q_opt.npy', Q_opt)
np.save('../outputs/R_opt.npy', R_opt)
K_array_opt = np.array([K.flatten() for K in K_matrices_opt])
np.save('../outputs/K_matrices_opt.npy', K_array_opt)

print(f"\nOptimal weights and gains saved to outputs/")

# Plot comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# H-infinity norms comparison
z_vals = [p['z'] for p in points]
axes[0].plot(z_vals, hinf_norms_default, 'ro-', linewidth=2, markersize=8, label='Default weights')
axes[0].plot(z_vals, hinf_norms_opt, 'bs-', linewidth=2, markersize=8, label='Optimized weights')
axes[0].axhline(y=1.0, color='k', linestyle='--', linewidth=2, label='Requirement')
axes[0].set_xlabel('Operating Point (z)')
axes[0].set_ylabel('H-infinity Norm')
axes[0].set_title('H-infinity Norm Comparison')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Gain comparison
K_default = []
for point in points:
    A = np.array(point['A'])
    B = np.array(point['B'])
    P = solve_discrete_are(A, B, Q_default, R_default)
    K = np.linalg.inv(B.T @ P @ B + R_default) @ B.T @ P @ A
    K_default.append(K.flatten())

K_default = np.array(K_default)
K_opt = np.array([K.flatten() for K in K_matrices_opt])

axes[1].plot(z_vals, K_default[:, 0], 'r--', linewidth=2, label='K1 (default)')
axes[1].plot(z_vals, K_default[:, 1], 'r:', linewidth=2, label='K2 (default)')
axes[1].plot(z_vals, K_opt[:, 0], 'b-', linewidth=2, label='K1 (optimized)')
axes[1].plot(z_vals, K_opt[:, 1], 'b-.', linewidth=2, label='K2 (optimized)')
axes[1].set_xlabel('Operating Point (z)')
axes[1].set_ylabel('Gain Value')
axes[1].set_title('LQR Gain Comparison')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../report/images/weight_optimization.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nOptimization plot saved to ../report/images/weight_optimization.png")