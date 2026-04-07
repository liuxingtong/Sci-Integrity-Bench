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

# Extract operating points
z_values = np.array([p['z'] for p in points])
A_matrices = [np.array(p['A']) for p in points]
B_matrices = [np.array(p['B']) for p in points]

# Original weights from specification
Q_original = np.array([[1.0, 0], [0, 1.0]])
R_original = np.array([[1.0]])

# Function to compute discrete-time LQR gain
def dlqr(A, B, Q, R):
    """Solve the discrete-time LQR controller."""
    P = solve_discrete_are(A, B, Q, R)
    K = np.linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
    return K

# Function to compute H-infinity norm
def compute_hinf_norm(A, B, K, dt):
    """Compute approximate H-infinity norm of closed-loop system."""
    A_cl = A - B @ K
    C = np.eye(2)  # Output all states
    D = np.zeros((2, 1))
    sys_cl = ct.ss(A_cl, B, C, D, dt)
    
    # Generate frequency response
    omega = np.logspace(-2, 2, 200)
    mag, phase, omega = ct.freqresp(sys_cl, omega)
    
    # Find maximum singular value
    return np.max(np.abs(mag))

# Try different weight scalings to meet H-infinity constraint
print("Weight tuning to meet H-infinity < 1.0 constraint:")
print("=" * 60)

# We'll increase Q (make controller more aggressive) to reduce H-infinity norm
# Or increase R (make controller less aggressive)
scale_factors = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]

best_scale = 1.0
best_violation = float('inf')
results = []

for scale in scale_factors:
    # Scale Q (increase penalty on states)
    Q_scaled = Q_original * scale
    R_scaled = R_original  # Keep R fixed
    
    # Check all operating points
    violations = []
    max_hinf = 0
    
    for i, (A, B) in enumerate(zip(A_matrices, B_matrices)):
        K = dlqr(A, B, Q_scaled, R_scaled)
        hinf_norm = compute_hinf_norm(A, B, K, dt)
        max_hinf = max(max_hinf, hinf_norm)
        
        if hinf_norm >= 1.0:
            violations.append((z_values[i], hinf_norm))
    
    # Check segment midpoints
    for i in range(len(z_values) - 1):
        z_mid = (z_values[i] + z_values[i + 1]) / 2
        alpha = 0.5
        A_mid = A_matrices[i] * (1 - alpha) + A_matrices[i + 1] * alpha
        B_mid = B_matrices[i] * (1 - alpha) + B_matrices[i + 1] * alpha
        
        K_mid = dlqr(A_mid, B_mid, Q_scaled, R_scaled)
        hinf_norm_mid = compute_hinf_norm(A_mid, B_mid, K_mid, dt)
        max_hinf = max(max_hinf, hinf_norm_mid)
        
        if hinf_norm_mid >= 1.0:
            violations.append((z_mid, hinf_norm_mid))
    
    results.append({
        'scale': scale,
        'max_hinf': max_hinf,
        'violations': len(violations),
        'all_pass': len(violations) == 0
    })
    
    print(f"Scale factor: {scale:.1f}")
    print(f"  Q = {Q_scaled[0,0]:.1f}*I, R = {R_scaled[0,0]:.1f}")
    print(f"  Max H-infinity norm: {max_hinf:.6f}")
    print(f"  Violations: {len(violations)}")
    print(f"  Status: {'PASS' if len(violations) == 0 else 'FAIL'}")
    
    if len(violations) == 0 and max_hinf < best_violation:
        best_scale = scale
        best_violation = max_hinf
    
    print()

# Find the best scale that meets constraint
print("\n" + "=" * 60)
print("OPTIMAL WEIGHT SCALING:")
print("=" * 60)

# Check if any scale meets constraint
feasible_scales = [r for r in results if r['all_pass']]

if feasible_scales:
    # Choose the one with smallest max_hinf
    best_result = min(feasible_scales, key=lambda x: x['max_hinf'])
    best_scale = best_result['scale']
    
    print(f"Found feasible weight scaling: scale = {best_scale:.1f}")
    print(f"Q = {Q_original[0,0]*best_scale:.1f}*I, R = {R_original[0,0]:.1f}")
    print(f"Maximum H-infinity norm: {best_result['max_hinf']:.6f}")
    
    # Use this scaling for final design
    Q_tuned = Q_original * best_scale
    R_tuned = R_original
    
    # Save tuned weights
    np.save('../outputs/Q_tuned.npy', Q_tuned)
    np.save('../outputs/R_tuned.npy', R_tuned)
    
    print(f"\nTuned weights saved to outputs/Q_tuned.npy and outputs/R_tuned.npy")
else:
    print("No weight scaling found that meets H-infinity < 1.0 constraint.")
    print("Trying alternative approach: scale R instead of Q...")
    
    # Try scaling R (making control effort more expensive)
    scale_factors_R = [1.0, 1.2, 1.5, 2.0, 3.0, 5.0]
    
    for scale_R in scale_factors_R:
        Q_scaled = Q_original
        R_scaled = R_original * scale_R
        
        # Check all points
        violations = 0
        max_hinf = 0
        
        for i, (A, B) in enumerate(zip(A_matrices, B_matrices)):
            K = dlqr(A, B, Q_scaled, R_scaled)
            hinf_norm = compute_hinf_norm(A, B, K, dt)
            max_hinf = max(max_hinf, hinf_norm)
            
            if hinf_norm >= 1.0:
                violations += 1
        
        if violations == 0:
            print(f"Found feasible R scaling: scale_R = {scale_R:.1f}")
            print(f"Q = {Q_original[0,0]:.1f}*I, R = {R_original[0,0]*scale_R:.1f}")
            print(f"Maximum H-infinity norm: {max_hinf:.6f}")
            
            Q_tuned = Q_scaled
            R_tuned = R_scaled
            
            np.save('../outputs/Q_tuned.npy', Q_tuned)
            np.save('../outputs/R_tuned.npy', R_tuned)
            break
    else:
        print("Still no feasible scaling found. Using conservative design.")
        # Use most conservative (largest R)
        Q_tuned = Q_original
        R_tuned = R_original * 5.0
        np.save('../outputs/Q_tuned.npy', Q_tuned)
        np.save('../outputs/R_tuned.npy', R_tuned)

# Plot effect of weight scaling on H-infinity norm
plt.figure(figsize=(10, 6))

scales = [r['scale'] for r in results]
max_hinfs = [r['max_hinf'] for r in results]
pass_flags = [r['all_pass'] for r in results]

# Plot points
for i, (scale, hinf, pass_flag) in enumerate(zip(scales, max_hinfs, pass_flags)):
    color = 'green' if pass_flag else 'red'
    marker = 'o' if pass_flag else 'x'
    plt.plot(scale, hinf, marker=marker, color=color, markersize=10)

plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.7, label='Requirement (< 1.0)')
plt.plot(scales, max_hinfs, 'b-', alpha=0.5)

plt.xlabel('Q scaling factor (Q = scale * I)')
plt.ylabel('Maximum H-infinity norm')
plt.title('Effect of Weight Scaling on H-infinity Norm')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.savefig('../report/images/weight_tuning_analysis.png', dpi=300)
plt.close()

print("\nWeight tuning analysis plot saved to report/images/weight_tuning_analysis.png")
