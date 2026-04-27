#!/usr/bin/env python3
"""
Porous Medium Equation - Traveling Wave Analysis

The porous medium equation (PME) is:
    u_t = (u^m)_xx

For a traveling wave solution u(x,t) = f(xi) where xi = x - c*t,
we substitute to get the traveling wave ODE:
    -c * f' = (f^m)'' = (m * f^(m-1) * f')'

Expanding:
    -c * f' = m*(m-1)*f^(m-2)*(f')^2 + m*f^(m-1)*f''

Rearranging for f'':
    f'' = [-c*f' - m*(m-1)*f^(m-2)*(f')^2] / [m*f^(m-1)]
    f'' = -c/(m*f^(m-1)) - (m-1)/f * (f')^2

This is a second-order ODE. We write it as a system:
    y[0] = f
    y[1] = f'
    y[0]' = y[1]
    y[1]' = -c/(m*y[0]^(m-1)) * y[1] - (m-1)/y[0] * y[1]^2

Boundary conditions for a saturation front:
    f(-inf) = 1  (fully saturated)
    f(+inf) = 0  (dry)

The wave speed c is determined by the Rankine-Hugoniot condition.
For the PME with m=2, the traveling wave connects f=1 to f=0.

Note: The solution has compact support - f=0 for xi > xi_0 (some finite point).
We integrate from the saturated side (f near 1) toward the dry side.
"""

import numpy as np
from scipy.integrate import solve_ivp, odeint
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import json

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# ============================================================
# Model Parameters
# ============================================================
m = 2          # PME exponent (m > 1 for slow diffusion)
c = 1.0        # Wave speed (positive, wave moves right)

print(f"Porous Medium Equation: u_t = (u^m)_xx")
print(f"Parameters: m = {m}, wave speed c = {c}")
print()

# ============================================================
# Traveling Wave ODE
# ============================================================
def pme_ode(xi, y, m, c):
    """
    Traveling wave ODE for the porous medium equation.
    
    System:
        y[0] = f(xi)     (saturation profile)
        y[1] = f'(xi)    (derivative)
    
    ODE:
        f'' = -c*f'/(m*f^(m-1)) - (m-1)*(f')^2/f
    
    Derived from: -c*f' = (m*f^(m-1)*f')'
    """
    f = y[0]
    fp = y[1]
    
    # Avoid division by zero (near the front where f -> 0)
    eps = 1e-10
    if f < eps:
        return [fp, 0.0]
    
    # f'' = -c*f'/(m*f^(m-1)) - (m-1)*(f')^2/f
    fpp = -c * fp / (m * f**(m-1)) - (m-1) * fp**2 / f
    
    return [fp, fpp]


# ============================================================
# Analytical Solution for m=2
# ============================================================
def analytical_solution_m2(xi, c=1.0):
    """
    For m=2, the PME traveling wave has an exact solution.
    
    The PME: u_t = (u^2)_xx
    Traveling wave: -c*f' = (2*f*f')' = 2*(f')^2 + 2*f*f''
    
    The exact solution is:
        f(xi) = max(0, (c/2) * (xi_0 - xi)) for xi < xi_0
        f(xi) = 0                             for xi >= xi_0
    
    where xi_0 is the front position.
    
    Verification: f = (c/2)*(xi_0 - xi)
        f' = -c/2
        f'' = 0
    
    Check ODE: -c*f' = 2*(f')^2 + 2*f*f''
        LHS: -c*(-c/2) = c^2/2
        RHS: 2*(c/2)^2 + 2*f*0 = c^2/2  ✓
    """
    xi_0 = 2.0 / c  # Front position (f=0 at xi=xi_0)
    f = np.maximum(0, (c/2) * (xi_0 - xi))
    return f


# ============================================================
# Numerical Integration
# ============================================================
print("=" * 60)
print("NUMERICAL INTEGRATION")
print("=" * 60)

# For m=2, analytical solution: f(xi) = (c/2)*(xi_0 - xi) for xi < xi_0
# At xi = -L (far left), f ≈ (c/2)*(xi_0 + L)
# We start integration from xi_start where f is close to 1

# Set up: f(xi_start) = f0, f'(xi_start) = -c/2 (from analytical)
xi_0 = 2.0 / c   # Front position for m=2
xi_start = xi_0 - 2.0/c  # Start where f = 1
f0_start = (c/2) * (xi_0 - xi_start)  # = 1.0
fp0_start = -c/2  # Analytical derivative

print(f"\nFor m={m}, c={c}:")
print(f"  Analytical front position: xi_0 = {xi_0:.4f}")
print(f"  Integration start: xi = {xi_start:.4f}")
print(f"  Initial condition: f({xi_start:.4f}) = {f0_start:.4f}")
print(f"  Initial derivative: f'({xi_start:.4f}) = {fp0_start:.4f}")

# Integration domain
xi_span = (xi_start, xi_0 + 0.5)  # Integrate past the front
xi_eval = np.linspace(xi_start, xi_0 + 0.5, 1000)

# Initial conditions
y0 = [f0_start, fp0_start]

# Solve using RK45 (Runge-Kutta 4th/5th order)
print("\nIntegrating with RK45 (Runge-Kutta 4th/5th order)...")
sol = solve_ivp(
    fun=lambda xi, y: pme_ode(xi, y, m, c),
    t_span=xi_span,
    y0=y0,
    method='RK45',
    t_eval=xi_eval,
    rtol=1e-8,
    atol=1e-10,
    dense_output=True
)

print(f"  Solver status: {sol.status} ({sol.message})")
print(f"  Number of function evaluations: {sol.nfev}")
print(f"  Number of steps: {len(sol.t)}")

# Extract solution
xi_num = sol.t
f_num = sol.y[0]
fp_num = sol.y[1]

# Clip negative values (compact support)
f_num_clipped = np.maximum(f_num, 0)

# ============================================================
# Analytical Solution for Comparison
# ============================================================
f_analytical = analytical_solution_m2(xi_eval, c)

# ============================================================
# RESIDUAL VERIFICATION
# ============================================================
print("\n" + "=" * 60)
print("RESIDUAL VERIFICATION")
print("=" * 60)

def compute_residual(xi, f, fp, m, c):
    """
    Compute the residual of the traveling wave ODE:
    R(xi) = -c*f' - (m*f^(m-1)*f')'
    
    Expanding:
    R(xi) = -c*f' - m*(m-1)*f^(m-2)*(f')^2 - m*f^(m-1)*f''
    
    We compute f'' from the ODE and check consistency.
    
    Alternative: use the integrated form.
    The ODE -c*f' = (m*f^(m-1)*f')' integrates to:
    -c*(f - f_L) = m*f^(m-1)*f' - [m*f_L^(m-1)*f'_L]
    
    For our case, we verify the ODE directly by computing
    the residual using numerical differentiation of the solution.
    """
    eps = 1e-10
    mask = f > eps
    
    # Compute f'' numerically from the solution
    fpp_numerical = np.gradient(fp, xi)
    
    # Compute residual: R = -c*fp - (m*(m-1)*f^(m-2)*fp^2 + m*f^(m-1)*fpp)
    residual = np.zeros_like(f)
    residual[mask] = (
        -c * fp[mask] 
        - m*(m-1) * f[mask]**(m-2) * fp[mask]**2 
        - m * f[mask]**(m-1) * fpp_numerical[mask]
    )
    
    return residual, fpp_numerical

# Compute residual
residual, fpp_num = compute_residual(xi_num, f_num, fp_num, m, c)

# Only consider interior points (away from boundaries)
interior_mask = (f_num > 0.01) & (f_num < 0.99)
residual_interior = residual[interior_mask]

print(f"\nODE Residual Analysis (interior region, 0.01 < f < 0.99):")
print(f"  Max |residual|: {np.max(np.abs(residual_interior)):.2e}")
print(f"  Mean |residual|: {np.mean(np.abs(residual_interior)):.2e}")
print(f"  RMS residual: {np.sqrt(np.mean(residual_interior**2)):.2e}")

# Also verify using the first integral
print("\nFirst Integral Verification:")
print("  The ODE -c*f' = (m*f^(m-1)*f')' has first integral:")
print("  I(xi) = m*f^(m-1)*f' + c*f = constant")

# Compute first integral
first_integral = m * f_num**(m-1) * fp_num + c * f_num
print(f"  I at xi_start: {first_integral[0]:.6f}")
print(f"  I at xi_end (before front): {first_integral[interior_mask][-1]:.6f}")
print(f"  Variation in I: {np.std(first_integral[interior_mask]):.2e}")
print(f"  Expected value: {m * f0_start**(m-1) * fp0_start + c * f0_start:.6f}")

# ============================================================
# Comparison with Analytical Solution
# ============================================================
print("\n" + "=" * 60)
print("COMPARISON WITH ANALYTICAL SOLUTION")
print("=" * 60)

# Interpolate numerical solution at analytical evaluation points
from scipy.interpolate import interp1d
f_interp = interp1d(xi_num, f_num_clipped, kind='cubic', fill_value=0, bounds_error=False)
f_num_at_eval = f_interp(xi_eval)

# Compute error
error = f_num_at_eval - f_analytical
mask_nonzero = f_analytical > 0.01

print(f"\nComparison with analytical solution (m=2):")
print(f"  Max |error|: {np.max(np.abs(error[mask_nonzero])):.2e}")
print(f"  Mean |error|: {np.mean(np.abs(error[mask_nonzero])):.2e}")
print(f"  RMS error: {np.sqrt(np.mean(error[mask_nonzero]**2)):.2e}")
print(f"  Relative RMS error: {np.sqrt(np.mean((error[mask_nonzero]/f_analytical[mask_nonzero])**2)):.2e}")

# ============================================================
# GENERAL m CASE: Shooting Method
# ============================================================
print("\n" + "=" * 60)
print("GENERAL m CASE (m=3): SHOOTING METHOD")
print("=" * 60)

m3 = 3
c3 = 1.0

# For general m, the traveling wave satisfies:
# -c*f' = (m*f^(m-1)*f')'
# Near the front (f -> 0+), the solution behaves as:
# f(xi) ~ (xi_0 - xi)^(1/(m-1)) * [c/(m*(m-1))]^(1/(m-1))
# This gives the correct behavior at the front.

# For m=3: f ~ sqrt((xi_0 - xi) * c/6)
# f' ~ -sqrt(c/6) / (2*sqrt(xi_0 - xi)) -> -inf as xi -> xi_0
# So we start from the front and integrate backward

print(f"\nFor m={m3}, c={c3}:")
print("  Near-front behavior: f ~ [(c/(m*(m-1))) * (xi_0 - xi)]^(1/(m-1))")

# Near-front expansion for m=3:
# f ~ sqrt(c/6 * (xi_0 - xi))
# f' ~ -sqrt(c/6) / (2*sqrt(xi_0 - xi))

def near_front_expansion(xi, xi_0, m, c, eps=1e-6):
    """Near-front expansion for the traveling wave."""
    delta = xi_0 - xi
    if delta <= 0:
        return 0.0, 0.0
    A = c / (m * (m-1))
    f = (A * delta)**(1/(m-1))
    fp = -(A**(1/(m-1))) / (m-1) * delta**(1/(m-1) - 1)
    return f, fp

# Start slightly before the front
delta_start = 0.01  # Small distance from front
xi_0_m3 = 2.0  # Assumed front position
xi_start_m3 = xi_0_m3 - delta_start

f_start_m3, fp_start_m3 = near_front_expansion(xi_start_m3, xi_0_m3, m3, c3)
print(f"  Starting at xi = {xi_start_m3:.4f} (delta = {delta_start})")
print(f"  f({xi_start_m3:.4f}) = {f_start_m3:.6f}")
print(f"  f'({xi_start_m3:.4f}) = {fp_start_m3:.6f}")

# Integrate backward (from front toward saturated region)
xi_span_m3 = (xi_start_m3, xi_start_m3 - 4.0)  # Integrate backward
xi_eval_m3 = np.linspace(xi_start_m3, xi_start_m3 - 4.0, 2000)

y0_m3 = [f_start_m3, fp_start_m3]

sol_m3 = solve_ivp(
    fun=lambda xi, y: pme_ode(xi, y, m3, c3),
    t_span=xi_span_m3,
    y0=y0_m3,
    method='RK45',
    t_eval=xi_eval_m3,
    rtol=1e-8,
    atol=1e-10
)

print(f"\n  Solver status: {sol_m3.status} ({sol_m3.message})")
print(f"  Number of function evaluations: {sol_m3.nfev}")

xi_m3 = sol_m3.t
f_m3 = sol_m3.y[0]
fp_m3 = sol_m3.y[1]

# Residual for m=3
residual_m3, _ = compute_residual(xi_m3, f_m3, fp_m3, m3, c3)
interior_mask_m3 = (f_m3 > 0.01) & (f_m3 < 0.99)
residual_interior_m3 = residual_m3[interior_mask_m3]

print(f"\n  ODE Residual (m=3, interior region):")
print(f"    Max |residual|: {np.max(np.abs(residual_interior_m3)):.2e}")
print(f"    Mean |residual|: {np.mean(np.abs(residual_interior_m3)):.2e}")
print(f"    RMS residual: {np.sqrt(np.mean(residual_interior_m3**2)):.2e}")

# First integral for m=3
first_integral_m3 = m3 * f_m3**(m3-1) * fp_m3 + c3 * f_m3
print(f"\n  First Integral (m=3):")
print(f"    I at start: {first_integral_m3[0]:.6f}")
print(f"    Variation: {np.std(first_integral_m3[interior_mask_m3]):.2e}")

# ============================================================
# SAVE RESULTS
# ============================================================
results = {
    'm2': {
        'xi': xi_num.tolist(),
        'f': f_num.tolist(),
        'fp': fp_num.tolist(),
        'residual': residual.tolist(),
        'first_integral': first_integral.tolist(),
        'max_residual_interior': float(np.max(np.abs(residual_interior))),
        'rms_residual_interior': float(np.sqrt(np.mean(residual_interior**2))),
        'max_error_vs_analytical': float(np.max(np.abs(error[mask_nonzero]))),
        'rms_error_vs_analytical': float(np.sqrt(np.mean(error[mask_nonzero]**2))),
    },
    'm3': {
        'xi': xi_m3.tolist(),
        'f': f_m3.tolist(),
        'fp': fp_m3.tolist(),
        'residual': residual_m3.tolist(),
        'first_integral': first_integral_m3.tolist(),
        'max_residual_interior': float(np.max(np.abs(residual_interior_m3))),
        'rms_residual_interior': float(np.sqrt(np.mean(residual_interior_m3**2))),
    }
}

with open('outputs/results.json', 'w') as f_out:
    json.dump(results, f_out, indent=2)

print("\nResults saved to outputs/results.json")

# ============================================================
# FIGURES
# ============================================================
print("\nGenerating figures...")

# Figure 1: Traveling wave profile for m=2
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('Porous Medium Equation: Traveling Wave Analysis', fontsize=14, fontweight='bold')

# Panel 1: Profile comparison
ax1 = axes[0, 0]
ax1.plot(xi_eval, f_analytical, 'b-', linewidth=2.5, label='Analytical (m=2)', zorder=3)
ax1.plot(xi_num, f_num_clipped, 'r--', linewidth=2, label='Numerical (RK45)', zorder=2)
ax1.axvline(x=xi_0, color='gray', linestyle=':', alpha=0.7, label=f'Front xi_0={xi_0:.2f}')
ax1.set_xlabel(r'$\xi = x - ct$', fontsize=12)
ax1.set_ylabel(r'$f(\xi)$', fontsize=12)
ax1.set_title(f'Traveling Wave Profile (m={m}, c={c})', fontsize=11)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xlim([xi_start - 0.1, xi_0 + 0.6])
ax1.set_ylim([-0.05, 1.1])

# Panel 2: Error vs analytical
ax2 = axes[0, 1]
ax2.semilogy(xi_eval[mask_nonzero], np.abs(error[mask_nonzero]) + 1e-16, 'g-', linewidth=2)
ax2.set_xlabel(r'$\xi$', fontsize=12)
ax2.set_ylabel(r'$|f_{num} - f_{exact}|$', fontsize=12)
ax2.set_title(f'Error vs Analytical Solution (m={m})', fontsize=11)
ax2.grid(True, alpha=0.3)
ax2.set_xlim([xi_start - 0.1, xi_0 - 0.05])

# Panel 3: ODE Residual
ax3 = axes[1, 0]
ax3.semilogy(xi_num[interior_mask], np.abs(residual[interior_mask]) + 1e-16, 'purple', linewidth=2)
ax3.set_xlabel(r'$\xi$', fontsize=12)
ax3.set_ylabel(r'$|R(\xi)|$', fontsize=12)
ax3.set_title(f'ODE Residual |R(xi)| (m={m})', fontsize=11)
ax3.grid(True, alpha=0.3)

# Panel 4: First integral conservation
ax4 = axes[1, 1]
ax4.plot(xi_num[interior_mask], first_integral[interior_mask], 'orange', linewidth=2)
ax4.set_xlabel(r'$\xi$', fontsize=12)
ax4.set_ylabel(r'$I(\xi) = m f^{m-1} f\prime + cf$', fontsize=12)
ax4.set_title(f'First Integral Conservation (m={m})', fontsize=11)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/traveling_wave_m2.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/traveling_wave_m2.png")

# Figure 2: m=3 solution
fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5))
fig2.suptitle(f'Porous Medium Equation: Traveling Wave (m={m3}, c={c3})', fontsize=13, fontweight='bold')

# Profile
ax = axes2[0]
ax.plot(xi_m3, f_m3, 'b-', linewidth=2.5)
ax.axvline(x=xi_0_m3, color='gray', linestyle=':', alpha=0.7, label=f'Front xi_0={xi_0_m3}')
ax.set_xlabel(r'$\xi$', fontsize=12)
ax.set_ylabel(r'$f(\xi)$', fontsize=12)
ax.set_title(f'Profile f(xi) (m={m3})', fontsize=11)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_ylim([-0.05, None])

# Residual
ax = axes2[1]
ax.semilogy(xi_m3[interior_mask_m3], np.abs(residual_m3[interior_mask_m3]) + 1e-16, 'purple', linewidth=2)
ax.set_xlabel(r'$\xi$', fontsize=12)
ax.set_ylabel(r'$|R(\xi)|$', fontsize=12)
ax.set_title(f'ODE Residual (m={m3})', fontsize=11)
ax.grid(True, alpha=0.3)

# First integral
ax = axes2[2]
ax.plot(xi_m3[interior_mask_m3], first_integral_m3[interior_mask_m3], 'orange', linewidth=2)
ax.set_xlabel(r'$\xi$', fontsize=12)
ax.set_ylabel(r'$I(\xi)$', fontsize=12)
ax.set_title(f'First Integral (m={m3})', fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/traveling_wave_m3.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/traveling_wave_m3.png")

# Figure 3: Phase portrait
fig3, axes3 = plt.subplots(1, 2, figsize=(12, 5))
fig3.suptitle('Phase Portraits: f vs f\' for Traveling Waves', fontsize=13, fontweight='bold')

# m=2 phase portrait
ax = axes3[0]
mask_pos_m2 = f_num > 0.001
ax.plot(f_num[mask_pos_m2], fp_num[mask_pos_m2], 'b-', linewidth=2.5, label='Numerical')
# Analytical: f' = -c/2 (constant for m=2)
f_range = np.linspace(0, 1, 100)
fp_analytical_m2 = -c/2 * np.ones_like(f_range)
ax.plot(f_range, fp_analytical_m2, 'r--', linewidth=2, label='Analytical (f\' = -c/2)')
ax.set_xlabel(r'$f$', fontsize=12)
ax.set_ylabel(r"$f'$", fontsize=12)
ax.set_title(f'Phase Portrait (m={m})', fontsize=11)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# m=3 phase portrait
ax = axes3[1]
mask_pos_m3 = f_m3 > 0.001
ax.plot(f_m3[mask_pos_m3], fp_m3[mask_pos_m3], 'g-', linewidth=2.5)
ax.set_xlabel(r'$f$', fontsize=12)
ax.set_ylabel(r"$f'$", fontsize=12)
ax.set_title(f'Phase Portrait (m={m3})', fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/phase_portraits.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/phase_portraits.png")

# Figure 4: Multiple wave speeds
fig4, axes4 = plt.subplots(1, 2, figsize=(12, 5))
fig4.suptitle('Effect of Wave Speed on Traveling Wave Profile (m=2)', fontsize=13, fontweight='bold')

colors = ['blue', 'green', 'red', 'purple', 'orange']
wave_speeds = [0.5, 1.0, 1.5, 2.0, 2.5]

ax = axes4[0]
for i, c_val in enumerate(wave_speeds):
    xi_0_c = 2.0 / c_val
    xi_start_c = xi_0_c - 2.0/c_val
    xi_eval_c = np.linspace(xi_start_c - 0.5, xi_0_c + 0.5, 500)
    f_c = analytical_solution_m2(xi_eval_c, c_val)
    # Shift so front is at xi=0
    ax.plot(xi_eval_c - xi_0_c, f_c, color=colors[i], linewidth=2, label=f'c={c_val}')

ax.set_xlabel(r'$\xi - \xi_0$ (shifted)', fontsize=12)
ax.set_ylabel(r'$f(\xi)$', fontsize=12)
ax.set_title('Profiles for Different Wave Speeds', fontsize=11)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xlim([-3, 1])
ax.set_ylim([-0.05, 1.5])

# Slope vs wave speed
ax = axes4[1]
c_range = np.linspace(0.1, 3.0, 100)
slope_m2 = -c_range / 2  # f' = -c/2 for m=2
ax.plot(c_range, np.abs(slope_m2), 'b-', linewidth=2.5)
ax.set_xlabel('Wave speed c', fontsize=12)
ax.set_ylabel(r"$|f'|$ (slope magnitude)", fontsize=12)
ax.set_title('Wave Slope vs Speed (m=2)', fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('report/images/wave_speed_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/wave_speed_comparison.png")

# Figure 5: Convergence study
print("\nRunning convergence study...")
tolerances = [1e-4, 1e-5, 1e-6, 1e-7, 1e-8]
max_errors = []
rms_errors = []

for tol in tolerances:
    sol_tol = solve_ivp(
        fun=lambda xi, y: pme_ode(xi, y, m, c),
        t_span=xi_span,
        y0=y0,
        method='RK45',
        t_eval=xi_eval,
        rtol=tol,
        atol=tol/100,
        dense_output=False
    )
    f_tol = np.maximum(sol_tol.y[0], 0)
    f_tol_interp = interp1d(sol_tol.t, f_tol, kind='cubic', fill_value=0, bounds_error=False)
    f_tol_at_eval = f_tol_interp(xi_eval)
    err = f_tol_at_eval - f_analytical
    max_errors.append(np.max(np.abs(err[mask_nonzero])))
    rms_errors.append(np.sqrt(np.mean(err[mask_nonzero]**2)))
    print(f"  tol={tol:.0e}: max_err={max_errors[-1]:.2e}, rms_err={rms_errors[-1]:.2e}")

fig5, ax5 = plt.subplots(figsize=(7, 5))
ax5.loglog(tolerances, max_errors, 'bo-', linewidth=2, markersize=8, label='Max error')
ax5.loglog(tolerances, rms_errors, 'rs-', linewidth=2, markersize=8, label='RMS error')
ax5.loglog(tolerances, tolerances, 'k--', alpha=0.5, label='y=tol (reference)')
ax5.set_xlabel('Solver tolerance (rtol)', fontsize=12)
ax5.set_ylabel('Error vs analytical solution', fontsize=12)
ax5.set_title('Convergence Study: RK45 Tolerance vs Error (m=2)', fontsize=11)
ax5.legend(fontsize=10)
ax5.grid(True, alpha=0.3, which='both')
plt.tight_layout()
plt.savefig('report/images/convergence_study.png', dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: report/images/convergence_study.png")

print("\n" + "=" * 60)
print("ALL COMPUTATIONS COMPLETE")
print("=" * 60)
