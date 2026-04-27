#!/usr/bin/env python3
"""
Additional verification and analysis for the porous medium traveling wave.
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os

os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

# ============================================================
# Parameters
# ============================================================
m = 2
c = 1.0

# ============================================================
# ODE System
# ============================================================
def pme_ode(xi, y, m, c):
    f, fp = y[0], y[1]
    eps = 1e-10
    if f < eps:
        return [fp, 0.0]
    fpp = -c * fp / (m * f**(m-1)) - (m-1) * fp**2 / f
    return [fp, fpp]

def analytical_m2(xi, c=1.0):
    xi_0 = 2.0 / c
    return np.maximum(0, (c/2) * (xi_0 - xi))

# ============================================================
# High-accuracy reference solution
# ============================================================
xi_0 = 2.0 / c
xi_start = 0.0
f0 = (c/2) * (xi_0 - xi_start)  # = 1.0
fp0 = -c/2

xi_span = (xi_start, xi_0 + 0.5)
xi_eval = np.linspace(xi_start, xi_0 + 0.5, 2000)

sol_ref = solve_ivp(
    fun=lambda xi, y: pme_ode(xi, y, m, c),
    t_span=xi_span,
    y0=[f0, fp0],
    method='RK45',
    t_eval=xi_eval,
    rtol=1e-10,
    atol=1e-12
)

xi_ref = sol_ref.t
f_ref = sol_ref.y[0]
fp_ref = sol_ref.y[1]

# ============================================================
# Detailed Residual Analysis
# ============================================================
print("DETAILED RESIDUAL ANALYSIS")
print("=" * 50)

# Method 1: Direct ODE residual using numerical differentiation
# R1 = -c*f' - (m*f^(m-1)*f')'
fpp_numerical = np.gradient(fp_ref, xi_ref)
eps = 1e-10
mask = f_ref > eps

R1 = np.zeros_like(f_ref)
R1[mask] = (
    -c * fp_ref[mask]
    - m*(m-1) * f_ref[mask]**(m-2) * fp_ref[mask]**2
    - m * f_ref[mask]**(m-1) * fpp_numerical[mask]
)

# Method 2: First integral conservation
# I(xi) = m*f^(m-1)*f' + c*f should be constant
I = m * f_ref**(m-1) * fp_ref + c * f_ref
I_expected = m * f0**(m-1) * fp0 + c * f0
I_residual = I - I_expected

# Method 3: Comparison with analytical
f_analytical = analytical_m2(xi_ref, c)
error_vs_analytical = f_ref - f_analytical

# Interior region
interior = (f_ref > 0.05) & (f_ref < 0.95)

print(f"\nMethod 1: Direct ODE Residual R(xi) = -c*f' - (m*f^(m-1)*f')'")
print(f"  Max |R| (interior): {np.max(np.abs(R1[interior])):.3e}")
print(f"  Mean |R| (interior): {np.mean(np.abs(R1[interior])):.3e}")
print(f"  RMS |R| (interior): {np.sqrt(np.mean(R1[interior]**2)):.3e}")

print(f"\nMethod 2: First Integral I(xi) = m*f^(m-1)*f' + c*f")
print(f"  Expected value: {I_expected:.6f}")
print(f"  Max |I - I_0| (interior): {np.max(np.abs(I_residual[interior])):.3e}")
print(f"  Relative variation: {np.max(np.abs(I_residual[interior]))/abs(I_expected):.3e}")

print(f"\nMethod 3: Error vs Analytical Solution (m=2)")
print(f"  Max |error| (interior): {np.max(np.abs(error_vs_analytical[interior])):.3e}")
print(f"  RMS error (interior): {np.sqrt(np.mean(error_vs_analytical[interior]**2)):.3e}")
print(f"  Relative RMS error: {np.sqrt(np.mean((error_vs_analytical[interior]/f_analytical[interior])**2)):.3e}")

# ============================================================
# Convergence Table
# ============================================================
print("\nCONVERGENCE TABLE")
print("=" * 50)
print(f"{'rtol':>10} {'Max Error':>12} {'RMS Error':>12} {'nfev':>8}")
print("-" * 45)

tolerances = [1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8, 1e-9]
conv_data = []

for tol in tolerances:
    sol_t = solve_ivp(
        fun=lambda xi, y: pme_ode(xi, y, m, c),
        t_span=xi_span,
        y0=[f0, fp0],
        method='RK45',
        t_eval=xi_eval,
        rtol=tol,
        atol=tol/100
    )
    f_t = np.maximum(sol_t.y[0], 0)
    err = f_t - f_analytical
    max_err = np.max(np.abs(err[interior]))
    rms_err = np.sqrt(np.mean(err[interior]**2))
    print(f"{tol:>10.0e} {max_err:>12.3e} {rms_err:>12.3e} {sol_t.nfev:>8d}")
    conv_data.append({'tol': tol, 'max_err': max_err, 'rms_err': rms_err, 'nfev': sol_t.nfev})

# ============================================================
# Multiple m values
# ============================================================
print("\nMULTIPLE m VALUES")
print("=" * 50)

m_values = [2, 3, 4, 5]
results_m = {}

for m_val in m_values:
    c_val = 1.0
    
    # Near-front expansion
    A = c_val / (m_val * (m_val - 1))
    delta_start = 0.001
    xi_0_val = 2.0
    xi_s = xi_0_val - delta_start
    f_s = (A * delta_start)**(1/(m_val-1))
    fp_s = -(A**(1/(m_val-1))) / (m_val-1) * delta_start**(1/(m_val-1) - 1)
    
    # Integrate backward
    xi_span_val = (xi_s, xi_s - 5.0)
    xi_eval_val = np.linspace(xi_s, xi_s - 5.0, 3000)
    
    sol_val = solve_ivp(
        fun=lambda xi, y: pme_ode(xi, y, m_val, c_val),
        t_span=xi_span_val,
        y0=[f_s, fp_s],
        method='RK45',
        t_eval=xi_eval_val,
        rtol=1e-8,
        atol=1e-10
    )
    
    xi_v = sol_val.t
    f_v = sol_val.y[0]
    fp_v = sol_val.y[1]
    
    # First integral
    I_v = m_val * f_v**(m_val-1) * fp_v + c_val * f_v
    interior_v = (f_v > 0.05) & (f_v < 0.95)
    
    if np.sum(interior_v) > 0:
        I_var = np.std(I_v[interior_v])
        I_mean = np.mean(I_v[interior_v])
        print(f"  m={m_val}: I_mean={I_mean:.4f}, I_std={I_var:.2e}, nfev={sol_val.nfev}")
    
    results_m[m_val] = {
        'xi': xi_v.tolist(),
        'f': f_v.tolist(),
        'fp': fp_v.tolist(),
        'I': I_v.tolist()
    }

# ============================================================
# FIGURE: Comprehensive verification plot
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Porous Medium Equation Traveling Wave: Comprehensive Verification', 
             fontsize=13, fontweight='bold')

# Panel 1: Profile + analytical
ax = axes[0, 0]
f_analytical_ref = analytical_m2(xi_ref, c)
ax.plot(xi_ref, f_analytical_ref, 'b-', linewidth=3, label='Analytical', alpha=0.7)
ax.plot(xi_ref, np.maximum(f_ref, 0), 'r--', linewidth=2, label='Numerical (RK45)')
ax.axvline(x=xi_0, color='gray', linestyle=':', alpha=0.7)
ax.fill_between(xi_ref, 0, np.maximum(f_ref, 0), alpha=0.1, color='red')
ax.set_xlabel(r'$\xi = x - ct$', fontsize=11)
ax.set_ylabel(r'$f(\xi)$', fontsize=11)
ax.set_title(f'Traveling Wave Profile (m={m}, c={c})', fontsize=10)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_xlim([xi_start - 0.1, xi_0 + 0.5])
ax.set_ylim([-0.05, 1.15])

# Panel 2: Error vs analytical
ax = axes[0, 1]
ax.semilogy(xi_ref[interior], np.abs(error_vs_analytical[interior]) + 1e-16, 
            'g-', linewidth=2)
ax.set_xlabel(r'$\xi$', fontsize=11)
ax.set_ylabel(r'$|f_{num} - f_{exact}|$', fontsize=11)
ax.set_title('Pointwise Error vs Analytical', fontsize=10)
ax.grid(True, alpha=0.3, which='both')
ax.text(0.05, 0.95, f'Max: {np.max(np.abs(error_vs_analytical[interior])):.2e}\nRMS: {np.sqrt(np.mean(error_vs_analytical[interior]**2)):.2e}',
        transform=ax.transAxes, verticalalignment='top', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Panel 3: ODE Residual
ax = axes[0, 2]
ax.semilogy(xi_ref[interior], np.abs(R1[interior]) + 1e-16, 'purple', linewidth=2)
ax.set_xlabel(r'$\xi$', fontsize=11)
ax.set_ylabel(r'$|R(\xi)|$', fontsize=11)
ax.set_title('ODE Residual |R(xi)|', fontsize=10)
ax.grid(True, alpha=0.3, which='both')
ax.text(0.05, 0.95, f'Max: {np.max(np.abs(R1[interior])):.2e}\nRMS: {np.sqrt(np.mean(R1[interior]**2)):.2e}',
        transform=ax.transAxes, verticalalignment='top', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Panel 4: First integral
ax = axes[1, 0]
ax.plot(xi_ref[interior], I[interior], 'orange', linewidth=2)
ax.axhline(y=I_expected, color='black', linestyle='--', alpha=0.7, label=f'Expected: {I_expected:.4f}')
ax.set_xlabel(r'$\xi$', fontsize=11)
ax.set_ylabel(r'$I(\xi) = mf^{m-1}f\prime + cf$', fontsize=11)
ax.set_title('First Integral Conservation', fontsize=10)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
ax.text(0.05, 0.05, f'Variation: {np.max(np.abs(I_residual[interior])):.2e}',
        transform=ax.transAxes, verticalalignment='bottom', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Panel 5: Multiple m values
ax = axes[1, 1]
colors_m = ['blue', 'green', 'red', 'purple']
for i, m_val in enumerate(m_values):
    xi_v = np.array(results_m[m_val]['xi'])
    f_v = np.array(results_m[m_val]['f'])
    # Shift so front is at xi=0
    front_idx = np.argmin(np.abs(f_v - 0.01))
    xi_shift = xi_v[front_idx] if front_idx < len(xi_v) else xi_v[-1]
    ax.plot(xi_v - xi_shift, np.maximum(f_v, 0), 
            color=colors_m[i], linewidth=2, label=f'm={m_val}')
ax.set_xlabel(r'$\xi - \xi_{front}$ (shifted)', fontsize=11)
ax.set_ylabel(r'$f(\xi)$', fontsize=11)
ax.set_title('Profiles for Different m Values', fontsize=10)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_xlim([-4, 0.5])
ax.set_ylim([-0.05, 1.5])

# Panel 6: Convergence
ax = axes[1, 2]
tols = [d['tol'] for d in conv_data]
max_errs = [d['max_err'] for d in conv_data]
rms_errs = [d['rms_err'] for d in conv_data]
ax.loglog(tols, max_errs, 'bo-', linewidth=2, markersize=7, label='Max error')
ax.loglog(tols, rms_errs, 'rs-', linewidth=2, markersize=7, label='RMS error')
ax.loglog(tols, tols, 'k--', alpha=0.5, label='y=tol')
ax.set_xlabel('Solver tolerance (rtol)', fontsize=11)
ax.set_ylabel('Error vs analytical', fontsize=11)
ax.set_title('Convergence Study (m=2)', fontsize=10)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, which='both')

plt.tight_layout()
plt.savefig('report/images/comprehensive_verification.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: report/images/comprehensive_verification.png")

# ============================================================
# FIGURE: Multiple m profiles (clean)
# ============================================================
fig2, axes2 = plt.subplots(1, 2, figsize=(12, 5))
fig2.suptitle('Porous Medium Traveling Waves for Different Nonlinearity Exponents', 
              fontsize=12, fontweight='bold')

ax = axes2[0]
for i, m_val in enumerate(m_values):
    xi_v = np.array(results_m[m_val]['xi'])
    f_v = np.array(results_m[m_val]['f'])
    # Find front position
    front_idx = np.argmin(np.abs(f_v - 0.005))
    xi_shift = xi_v[front_idx]
    mask_plot = f_v >= 0
    ax.plot(xi_v[mask_plot] - xi_shift, np.maximum(f_v[mask_plot], 0), 
            color=colors_m[i], linewidth=2.5, label=f'm={m_val}')
ax.set_xlabel(r'$\xi - \xi_{front}$', fontsize=12)
ax.set_ylabel(r'$f(\xi)$', fontsize=12)
ax.set_title('Saturation Profiles (shifted to common front)', fontsize=11)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
ax.set_xlim([-4, 0.3])
ax.set_ylim([-0.05, 1.5])

# Phase portraits
ax = axes2[1]
for i, m_val in enumerate(m_values):
    xi_v = np.array(results_m[m_val]['xi'])
    f_v = np.array(results_m[m_val]['f'])
    fp_v = np.array(results_m[m_val]['fp'])
    mask_pp = (f_v > 0.01) & (f_v < 1.2)
    ax.plot(f_v[mask_pp], fp_v[mask_pp], 
            color=colors_m[i], linewidth=2.5, label=f'm={m_val}')
ax.set_xlabel(r'$f$', fontsize=12)
ax.set_ylabel(r"$f'$", fontsize=12)
ax.set_title('Phase Portraits', fontsize=11)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
ax.set_xlim([-0.05, 1.3])

plt.tight_layout()
plt.savefig('report/images/multiple_m_profiles.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: report/images/multiple_m_profiles.png")

# ============================================================
# Save summary statistics
# ============================================================
summary = {
    'model': 'Porous Medium Equation u_t = (u^m)_xx',
    'traveling_wave_ode': '-c*f\' = (m*f^(m-1)*f\')\'',
    'method': 'RK45 (Runge-Kutta 4th/5th order)',
    'settings': {'rtol': 1e-10, 'atol': 1e-12},
    'verification': {
        'max_ode_residual': float(np.max(np.abs(R1[interior]))),
        'rms_ode_residual': float(np.sqrt(np.mean(R1[interior]**2))),
        'max_error_vs_analytical': float(np.max(np.abs(error_vs_analytical[interior]))),
        'rms_error_vs_analytical': float(np.sqrt(np.mean(error_vs_analytical[interior]**2))),
        'first_integral_variation': float(np.max(np.abs(I_residual[interior]))),
        'first_integral_relative_variation': float(np.max(np.abs(I_residual[interior]))/abs(I_expected))
    },
    'convergence_data': conv_data
}

with open('outputs/summary.json', 'w') as f_out:
    json.dump(summary, f_out, indent=2)

print("\nSaved: outputs/summary.json")
print("\nALL DONE!")
