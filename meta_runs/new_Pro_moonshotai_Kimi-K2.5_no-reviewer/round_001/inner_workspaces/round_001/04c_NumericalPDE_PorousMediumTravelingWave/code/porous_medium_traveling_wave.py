"""
Numerical solution of Porous Medium Equation (PME) traveling wave.

The PME is: u_t = (u^m * u_x)_x
Traveling wave ansatz: u(x,t) = f(ξ), ξ = x - ct

This yields the ODE:
-c f' = (f^m f')'

Integrating once:
-c f = f^m f' + C1

For a wave connecting u_L (left) to u_R (right) with c > 0,
the boundary conditions are:
f(-∞) = u_L, f(+∞) = u_R

For the classic Barenblatt-type solution with u_R = 0:
-c f = f^m f'

This gives: f' = -c * f^(1-m)

For m > 1, this has a compact support solution.
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# Physical parameters
m = 2.0  # Porous medium exponent (m > 1)
c = 1.0  # Wave speed

# For the PME traveling wave with u_R = 0, the ODE is:
# f' = -c * f^(1-m) for f > 0
# But this has singularity at f = 0.
# 
# Alternative formulation: Let g = f^m, then:
# f = g^(1/m), f' = (1/m) * g^(1/m - 1) * g'
# 
# From -c f = f^m f':
# -c g^(1/m) = g * (1/m) * g^(1/m - 1) * g'
# -c g^(1/m) = (1/m) * g^(1/m) * g'
# g' = -c * m

# So g(ξ) = g(0) - c*m*ξ for the active region
# This gives f(ξ) = (g(0) - c*m*ξ)^(1/m) for ξ < ξ_max
# where ξ_max = g(0)/(c*m)

# Let's verify this analytically and solve numerically

print("=" * 60)
print("Porous Medium Equation: Traveling Wave Solution")
print("=" * 60)
print(f"Parameters: m = {m}, c = {c}")
print()

# Analytical solution for compact support wave
# f(ξ) = [max(0, A - c*m*ξ)]^(1/m)
# where A = f(0)^m

A = 1.0  # Value of f(0)^m
xi_max = A / (c * m)
print(f"Analytical: Compact support ends at ξ_max = {xi_max:.6f}")
print(f"f(0) = {A**(1/m):.6f}")

# Define the ODE for numerical solution
# We use the form: f' = -c * f / f^m = -c * f^(1-m)
# But this is singular at f = 0.
# Better: use the integrated form and regularize

def pme_ode(xi, f):
    """
    ODE for PME traveling wave: f' = -c * f^(1-m)
    Regularized version to handle small f.
    """
    f_val = f[0]
    if f_val < 1e-10:
        return [0.0]  # At boundary of support
    df_dxi = -c * f_val**(1 - m)
    return [df_dxi]

def pme_ode_regularized(xi, f, epsilon=1e-8):
    """
    Regularized ODE: f' = -c * f / (f^m + epsilon)
    """
    f_val = f[0]
    df_dxi = -c * f_val / (f_val**m + epsilon)
    return [df_dxi]

# Solve with adaptive step integration
# Initial condition: f(0) = A^(1/m)
f0 = [A**(1/m)]

# Integration range
xi_span = (0, xi_max * 1.2)  # Go slightly beyond to see the zero region

print("\n" + "=" * 60)
print("Numerical Integration with solve_ivp (RK45)")
print("=" * 60)

# Method 1: Direct ODE with tight tolerances
sol1 = solve_ivp(
    pme_ode, 
    xi_span, 
    f0, 
    method='RK45',
    rtol=1e-8,
    atol=1e-10,
    dense_output=True,
    max_step=0.01
)

print(f"Method 1 (Direct ODE):")
print(f"  Number of steps: {len(sol1.t)}")
print(f"  Success: {sol1.success}")
print(f"  Final f value: {sol1.y[0, -1]:.10e}")

# Method 2: Regularized ODE
epsilon = 1e-8
sol2 = solve_ivp(
    lambda xi, f: pme_ode_regularized(xi, f, epsilon),
    xi_span, 
    f0, 
    method='RK45',
    rtol=1e-8,
    atol=1e-10,
    dense_output=True,
    max_step=0.01
)

print(f"\nMethod 2 (Regularized ODE, ε={epsilon}):")
print(f"  Number of steps: {len(sol2.t)}")
print(f"  Success: {sol2.success}")
print(f"  Final f value: {sol2.y[0, -1]:.10e}")

# Method 3: Higher order method (DOP853)
sol3 = solve_ivp(
    lambda xi, f: pme_ode_regularized(xi, f, epsilon),
    xi_span, 
    f0, 
    method='DOP853',
    rtol=1e-10,
    atol=1e-12,
    dense_output=True,
    max_step=0.005
)

print(f"\nMethod 3 (DOP853, tighter tolerances):")
print(f"  Number of steps: {len(sol3.t)}")
print(f"  Success: {sol3.success}")
print(f"  Final f value: {sol3.y[0, -1]:.10e}")

# Generate fine grid for plotting
xi_fine = np.linspace(xi_span[0], xi_span[1], 1000)

# Analytical solution
f_analytical = np.maximum(0, A - c * m * xi_fine)**(1/m)

# Numerical solutions
f_numerical_1 = sol1.sol(xi_fine)[0]
f_numerical_2 = sol2.sol(xi_fine)[0]
f_numerical_3 = sol3.sol(xi_fine)[0]

# Clip negative values to zero for physical interpretation
f_numerical_1 = np.maximum(0, f_numerical_1)
f_numerical_2 = np.maximum(0, f_numerical_2)
f_numerical_3 = np.maximum(0, f_numerical_3)

print("\n" + "=" * 60)
print("Error Analysis")
print("=" * 60)

# Compute errors (only where analytical solution is non-zero)
valid_mask = f_analytical > 1e-10
if np.any(valid_mask):
    err1 = np.abs(f_numerical_1[valid_mask] - f_analytical[valid_mask])
    err2 = np.abs(f_numerical_2[valid_mask] - f_analytical[valid_mask])
    err3 = np.abs(f_numerical_3[valid_mask] - f_analytical[valid_mask])
    
    print(f"Method 1 (RK45): Max error = {np.max(err1):.6e}, Mean error = {np.mean(err1):.6e}")
    print(f"Method 2 (RK45 reg): Max error = {np.max(err2):.6e}, Mean error = {np.mean(err2):.6e}")
    print(f"Method 3 (DOP853): Max error = {np.max(err3):.6e}, Mean error = {np.mean(err3):.6e}")

# Save results
results = {
    'xi': xi_fine,
    'f_analytical': f_analytical,
    'f_numerical_rk45': f_numerical_1,
    'f_numerical_reg': f_numerical_2,
    'f_numerical_dop853': f_numerical_3,
    'parameters': {'m': m, 'c': c, 'A': A}
}

np.savez('outputs/traveling_wave_results.npz', **results)
print("\nResults saved to outputs/traveling_wave_results.npz")

# Create visualizations
print("\n" + "=" * 60)
print("Generating Figures")
print("=" * 60)

# Figure 1: Comparison of solutions
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax1 = axes[0]
ax1.plot(xi_fine, f_analytical, 'k-', linewidth=2, label='Analytical', alpha=0.8)
ax1.plot(sol1.t, sol1.y[0], 'o', markersize=3, label=f'RK45 ({len(sol1.t)} steps)', alpha=0.7)
ax1.plot(sol2.t, sol2.y[0], 's', markersize=3, label=f'RK45 reg ({len(sol2.t)} steps)', alpha=0.7)
ax1.plot(sol3.t, sol3.y[0], '^', markersize=3, label=f'DOP853 ({len(sol3.t)} steps)', alpha=0.7)
ax1.axvline(x=xi_max, color='r', linestyle='--', alpha=0.5, label=f'Support boundary ξ={xi_max:.3f}')
ax1.set_xlabel(r'$\xi$', fontsize=12)
ax1.set_ylabel(r'$f(\xi)$', fontsize=12)
ax1.set_title(f'PME Traveling Wave (m={m}, c={c})', fontsize=12)
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.set_xlim([0, xi_max * 1.1])

ax2 = axes[1]
# Error plot
if np.any(valid_mask):
    ax2.semilogy(xi_fine[valid_mask], err1, '-', label='RK45 error', alpha=0.7)
    ax2.semilogy(xi_fine[valid_mask], err2, '-', label='RK45 reg error', alpha=0.7)
    ax2.semilogy(xi_fine[valid_mask], err3, '-', label='DOP853 error', alpha=0.7)
    ax2.axhline(y=1e-8, color='r', linestyle='--', alpha=0.5, label='rtol=1e-8')
    ax2.axhline(y=1e-10, color='orange', linestyle='--', alpha=0.5, label='atol=1e-10')
ax2.set_xlabel(r'$\xi$', fontsize=12)
ax2.set_ylabel('Absolute Error', fontsize=12)
ax2.set_title('Numerical Error Comparison', fontsize=12)
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure1_solution_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 1 saved: report/images/figure1_solution_comparison.png")

# Figure 2: Step size analysis
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax1 = axes[0]
# Compute step sizes
steps1 = np.diff(sol1.t)
steps2 = np.diff(sol2.t)
steps3 = np.diff(sol3.t)

ax1.semilogy(sol1.t[:-1], steps1, 'o-', markersize=2, label='RK45', alpha=0.7)
ax1.semilogy(sol2.t[:-1], steps2, 's-', markersize=2, label='RK45 reg', alpha=0.7)
ax1.semilogy(sol3.t[:-1], steps3, '^-', markersize=2, label='DOP853', alpha=0.7)
ax1.set_xlabel(r'$\xi$', fontsize=12)
ax1.set_ylabel('Step Size', fontsize=12)
ax1.set_title('Adaptive Step Size Evolution', fontsize=12)
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)

ax2 = axes[1]
# Local error estimate (from solver)
ax2.semilogy(sol1.t, np.abs(sol1.y[0] - (A - c*m*sol1.t)**(1/m) * (sol1.t < xi_max)), 
             'o', markersize=3, label='RK45 local error', alpha=0.7)
ax2.semilogy(sol3.t, np.abs(sol3.y[0] - (A - c*m*sol3.t)**(1/m) * (sol3.t < xi_max)), 
             '^', markersize=3, label='DOP853 local error', alpha=0.7)
ax2.set_xlabel(r'$\xi$', fontsize=12)
ax2.set_ylabel('Local Error', fontsize=12)
ax2.set_title('Local Error at Integration Points', fontsize=12)
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure2_step_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 2 saved: report/images/figure2_step_analysis.png")

# Figure 3: Phase portrait and derivative analysis
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax1 = axes[0]
# f' vs f (phase portrait)
f_vals = f_analytical[valid_mask]
df_analytical = -c * f_vals**(1-m)
df_numerical = np.gradient(f_numerical_3, xi_fine)[valid_mask]

ax1.plot(f_vals, df_analytical, 'k-', linewidth=2, label='Analytical df/dξ', alpha=0.8)
ax1.plot(f_vals[::10], df_numerical[::10], 'o', markersize=3, label='Numerical df/dξ', alpha=0.7)
ax1.set_xlabel(r'$f$', fontsize=12)
ax1.set_ylabel(r"$f'$", fontsize=12)
ax1.set_title('Phase Portrait: f\' vs f', fontsize=12)
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)

ax2 = axes[1]
# Convergence study with different tolerances
tolerances = [1e-4, 1e-6, 1e-8, 1e-10]
max_errors = []

for tol in tolerances:
    sol_test = solve_ivp(
        lambda xi, f: pme_ode_regularized(xi, f, epsilon),
        xi_span, 
        f0, 
        method='RK45',
        rtol=tol,
        atol=tol/100,
        dense_output=True
    )
    f_test = sol_test.sol(xi_fine)[0]
    f_test = np.maximum(0, f_test)
    if np.any(valid_mask):
        err = np.max(np.abs(f_test[valid_mask] - f_analytical[valid_mask]))
        max_errors.append(err)

ax2.loglog(tolerances, max_errors, 'o-', linewidth=2, markersize=8, label='Max error')
ax2.loglog(tolerances, tolerances, 'k--', alpha=0.5, label='y = rtol')
ax2.loglog(tolerances, [t/100 for t in tolerances], 'k:', alpha=0.5, label='y = atol')
ax2.set_xlabel('Tolerance (rtol)', fontsize=12)
ax2.set_ylabel('Maximum Error', fontsize=12)
ax2.set_title('Convergence Study: Error vs Tolerance', fontsize=12)
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure3_phase_convergence.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 3 saved: report/images/figure3_phase_convergence.png")

# Figure 4: Different m values
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

m_values = [1.5, 2.0, 3.0, 4.0]
colors = plt.cm.viridis(np.linspace(0, 1, len(m_values)))

ax1 = axes[0]
for i, m_test in enumerate(m_values):
    xi_max_test = A / (c * m_test)
    xi_test = np.linspace(0, xi_max_test * 1.1, 500)
    f_test = np.maximum(0, A - c * m_test * xi_test)**(1/m_test)
    ax1.plot(xi_test, f_test, color=colors[i], linewidth=2, 
             label=f'm = {m_test}, ξ_max = {xi_max_test:.3f}')

ax1.set_xlabel(r'$\xi$', fontsize=12)
ax1.set_ylabel(r'$f(\xi)$', fontsize=12)
ax1.set_title('Traveling Wave Profiles for Different m', fontsize=12)
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)

ax2 = axes[1]
# Different wave speeds
c_values = [0.5, 1.0, 2.0, 3.0]
colors2 = plt.cm.plasma(np.linspace(0, 1, len(c_values)))

for i, c_test in enumerate(c_values):
    xi_max_test = A / (c_test * m)
    xi_test = np.linspace(0, xi_max_test * 1.1, 500)
    f_test = np.maximum(0, A - c_test * m * xi_test)**(1/m)
    ax2.plot(xi_test, f_test, color=colors2[i], linewidth=2, 
             label=f'c = {c_test}, ξ_max = {xi_max_test:.3f}')

ax2.set_xlabel(r'$\xi$', fontsize=12)
ax2.set_ylabel(r'$f(\xi)$', fontsize=12)
ax2.set_title(f'Traveling Wave Profiles for Different c (m={m})', fontsize=12)
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/figure4_parameter_study.png', dpi=150, bbox_inches='tight')
plt.close()
print("Figure 4 saved: report/images/figure4_parameter_study.png")

print("\n" + "=" * 60)
print("All figures generated successfully!")
print("=" * 60)
