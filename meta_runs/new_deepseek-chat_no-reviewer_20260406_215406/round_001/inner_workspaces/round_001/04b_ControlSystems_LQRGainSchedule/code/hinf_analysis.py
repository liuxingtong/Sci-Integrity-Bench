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

# Compute LQR gains and closed-loop systems
print("H-infinity norm analysis for each operating point:")
print("=" * 60)

hinf_norms = []
for i, (z, A, B) in enumerate(zip(z_values, A_matrices, B_matrices)):
    # Compute LQR gain
    K = dlqr(A, B, Q, R)
    
    # Closed-loop system: x[k+1] = (A - B*K) * x[k]
    A_cl = A - B @ K
    
    # Create discrete-time system
    # For H-infinity analysis, we need a system with inputs and outputs
    # Let's assume we want to analyze the transfer from disturbance to output
    # We'll use identity matrices for C and D to get full state output
    C = np.eye(2)  # Output all states
    D = np.zeros((2, 1))
    
    # Create state-space system
    sys_cl = ct.ss(A_cl, B, C, D, dt)
    
    # Compute H-infinity norm
    # Note: For discrete-time systems, we need to use appropriate method
    # We'll compute the maximum singular value across frequency
    
    # Generate frequency response
    omega = np.logspace(-2, 2, 200)
    mag, phase, omega = ct.freqresp(sys_cl, omega)
    
    # Find maximum singular value (H-infinity norm approximation)
    # For SISO or MIMO, we look at maximum singular value across frequency
    hinf_norm = np.max(np.abs(mag))
    hinf_norms.append(hinf_norm)
    
    print(f"Operating point z = {z}:")
    print(f"  LQR gain K = [{K[0,0]:.6f}, {K[0,1]:.6f}]")
    print(f"  Closed-loop A matrix:")
    print(f"    {A_cl[0]}")
    print(f"    {A_cl[1]}")
    print(f"  Approximate H-infinity norm = {hinf_norm:.6f}")
    print(f"  Requirement: < 1.0 → {'PASS' if hinf_norm < 1.0 else 'FAIL'}")
    print()

# Check all segments (interpolated points)
print("\nChecking intermediate points (segments between operating points):")
print("=" * 60)

# We'll check points between each pair of operating points
segment_checks = []
for i in range(len(z_values) - 1):
    z_start = z_values[i]
    z_end = z_values[i + 1]
    
    # Check at midpoint of segment
    z_mid = (z_start + z_end) / 2
    
    # Interpolate A and B matrices (linear interpolation)
    alpha = 0.5  # midpoint
    A_mid = A_matrices[i] * (1 - alpha) + A_matrices[i + 1] * alpha
    B_mid = B_matrices[i] * (1 - alpha) + B_matrices[i + 1] * alpha
    
    # Compute LQR gain for interpolated system
    K_mid = dlqr(A_mid, B_mid, Q, R)
    
    # Closed-loop system
    A_cl_mid = A_mid - B_mid @ K_mid
    
    # Create system for H-infinity analysis
    C = np.eye(2)
    D = np.zeros((2, 1))
    sys_cl_mid = ct.ss(A_cl_mid, B_mid, C, D, dt)
    
    # Compute H-infinity norm
    omega = np.logspace(-2, 2, 200)
    mag, phase, omega = ct.freqresp(sys_cl_mid, omega)
    hinf_norm_mid = np.max(np.abs(mag))
    
    segment_checks.append({
        'segment': f"z={z_start} to z={z_end}",
        'z_mid': z_mid,
        'hinf_norm': hinf_norm_mid,
        'pass': hinf_norm_mid < 1.0
    })
    
    print(f"Segment {z_start} to {z_end} (midpoint z={z_mid}):")
    print(f"  Interpolated LQR gain K = [{K_mid[0,0]:.6f}, {K_mid[0,1]:.6f}]")
    print(f"  Approximate H-infinity norm = {hinf_norm_mid:.6f}")
    print(f"  Requirement: < 1.0 → {'PASS' if hinf_norm_mid < 1.0 else 'FAIL'}")
    print()

# Plot H-infinity norms
plt.figure(figsize=(10, 6))

# Plot at operating points
plt.plot(z_values, hinf_norms, 'ro-', linewidth=2, markersize=10, label='Operating points')

# Plot at segment midpoints
segment_z = [check['z_mid'] for check in segment_checks]
segment_hinf = [check['hinf_norm'] for check in segment_checks]
plt.plot(segment_z, segment_hinf, 'bs--', linewidth=2, markersize=8, label='Segment midpoints')

# Add requirement line
plt.axhline(y=1.0, color='r', linestyle='--', alpha=0.7, label='Requirement (< 1.0)')

plt.xlabel('Operating point z')
plt.ylabel('H-infinity norm')
plt.title('H-infinity Norm Analysis of Gain-Scheduled LQR')
plt.grid(True)
plt.legend()
plt.ylim([0, max(max(hinf_norms), max(segment_hinf)) * 1.2])

plt.tight_layout()
plt.savefig('../report/images/hinf_norm_analysis.png', dpi=300)
plt.close()

print("H-infinity norm analysis plot saved to report/images/hinf_norm_analysis.png")

# Summary
print("\n" + "=" * 60)
print("SUMMARY:")
print("=" * 60)

all_pass = all([hinf < 1.0 for hinf in hinf_norms]) and all([check['pass'] for check in segment_checks])

if all_pass:
    print("✓ All H-infinity norms are below 1.0 (requirement satisfied)")
else:
    print("✗ Some H-infinity norms exceed 1.0 (requirement NOT satisfied)")
    
    # List failures
    for i, hinf in enumerate(hinf_norms):
        if hinf >= 1.0:
            print(f"  - Operating point z={z_values[i]}: H-inf = {hinf:.6f}")
    
    for check in segment_checks:
        if not check['pass']:
            print(f"  - Segment {check['segment']} (midpoint z={check['z_mid']}): H-inf = {check['hinf_norm']:.6f}")

# Save results
# Convert numpy bool to Python bool for JSON serialization
segment_checks_serializable = []
for check in segment_checks:
    segment_checks_serializable.append({
        'segment': check['segment'],
        'z_mid': float(check['z_mid']),
        'hinf_norm': float(check['hinf_norm']),
        'pass': bool(check['pass'])
    })

results = {
    'z_values': z_values.tolist(),
    'hinf_norms': [float(h) for h in hinf_norms],
    'segment_checks': segment_checks_serializable,
    'all_pass': bool(all_pass)
}

import json
with open('../outputs/hinf_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nResults saved to outputs/hinf_results.json")
