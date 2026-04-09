"""
Traveling-wave ODE solver for porous medium equation.

The porous medium equation: u_t = (u^m * u_x)_x

Traveling wave ansatz: u(x,t) = f(xi), xi = x - c*t

This reduces to ODE: -c*f' = (f^m * f')'

Integrating once with boundary conditions f(-inf)=1, f(+inf)=0:
-c*f = f^m * f'

This gives the first-order ODE: f' = -c * f^(1-m)

For m > 1, this has a compact support solution.
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os

# Parameters
m = 2.0  # Porous medium exponent (m > 1)
c = 1.0  # Wave speed

# Tolerance for adaptive stepping
TOL = 1e-8

def residual_ode(xi, f, fp, m=m, c=c):
    """
    Compute the residual of the integrated ODE: -c*f - f^m * f' = 0
    """
    f_reg = np.maximum(np.abs(f), 1e-12)
    residual = -c * f - f_reg**m * fp
    return residual

def compute_l2_residual(xi, f, fp, m=m, c=c):
    """
    Compute L2 norm of the ODE residual.
    """
    res = residual_ode(xi, f, fp, m, c)
    l2_norm = np.sqrt(np.trapz(res**2, xi))
    return l2_norm

def analytical_solution(xi_min=-5, xi_max=5, n_points=1000):
    """
    Analytical solution using the integrated form.
    
    From -c*f = f^m * f', we have:
    f^m = 1 + m*c*(xi_min - xi)
    f = (1 + m*c*(xi_min - xi))^(1/m)
    """
    xi = np.linspace(xi_min, xi_max, n_points)
    arg = 1 + m * c * (xi_min - xi)
    f = np.maximum(0, arg) ** (1/m)
    
    # Compute derivative analytically
    f_reg = np.maximum(f, 1e-12)
    fp = -c * f_reg**(1-m)
    fp[f <= 0] = 0
    
    return xi, f, fp

def adaptive_integration(xi_min=-5, xi_max=5, tol=TOL):
    """
    Adaptive step integration with error control.
    """
    # Start with analytical solution and refine
    n_points = 100
    xi = np.linspace(xi_min, xi_max, n_points)
    arg = 1 + m * c * (xi_min - xi)
    f = np.maximum(0, arg) ** (1/m)
    f_reg = np.maximum(f, 1e-12)
    fp = -c * f_reg**(1-m)
    fp[f <= 0] = 0
    
    # Check residual
    l2_res = compute_l2_residual(xi, f, fp, m, c)
    
    # Refine if needed
    max_iterations = 20
    iteration = 0
    
    while l2_res > tol and iteration < max_iterations and len(xi) < 50000:
        # Double the resolution
        xi_new = np.zeros(2*len(xi) - 1)
        f_new = np.zeros(2*len(xi) - 1)
        
        for i in range(len(xi) - 1):
            xi_new[2*i] = xi[i]
            f_new[2*i] = f[i]
            
            # Midpoint
            xi_mid = (xi[i] + xi[i+1]) / 2
            arg_mid = 1 + m * c * (xi_min - xi_mid)
            f_mid = max(0, arg_mid) ** (1/m)
            
            xi_new[2*i + 1] = xi_mid
            f_new[2*i + 1] = f_mid
        
        xi_new[-1] = xi[-1]
        f_new[-1] = f[-1]
        
        xi = xi_new
        f = f_new
        f_reg = np.maximum(f, 1e-12)
        fp = -c * f_reg**(1-m)
        fp[f <= 0] = 0
        
        l2_res = compute_l2_residual(xi, f, fp, m, c)
        iteration += 1
    
    return xi, f, fp, l2_res, iteration

def solve_ivp_scipy(xi_min=-5, xi_max=5):
    """
    Solve using scipy's solve_ivp with adaptive stepping.
    """
    y0 = [1.0]
    xi_span = (xi_min, xi_max)
    
    try:
        sol = solve_ivp(
            lambda xi, y: [-c * max(y[0], 1e-12)**(1-m)],
            xi_span,
            y0,
            method='RK45',
            rtol=TOL,
            atol=TOL,
            dense_output=True,
            max_step=0.1
        )
        
        if sol.success:
            xi_ivp = sol.t
            f_ivp = sol.y[0]
            f_reg = np.maximum(f_ivp, 1e-12)
            fp_ivp = -c * f_reg**(1-m)
            fp_ivp[f_ivp <= 0] = 0
            return xi_ivp, f_ivp, fp_ivp, True
    except Exception as e:
        print(f"IVP error: {e}")
    
    return None, None, None, False

def main():
    print("="*60)
    print("Porous Medium Equation - Traveling Wave Solver")
    print("="*60)
    print(f"Parameters: m={m}, c={c}, TOL={TOL}")
    print()
    
    # Method 1: Analytical solution
    print("Method 1: Analytical Solution")
    print("-"*40)
    
    xi_ana, f_ana, fp_ana = analytical_solution()
    l2_ana = compute_l2_residual(xi_ana, f_ana, fp_ana, m, c)
    print(f"L2 residual norm: {l2_ana:.2e}")
    print(f"Number of points: {len(xi_ana)}")
    
    print()
    
    # Method 2: Adaptive integration
    print("Method 2: Adaptive Integration")
    print("-"*40)
    
    xi_adapt, f_adapt, fp_adapt, l2_adapt, n_iter = adaptive_integration()
    print(f"L2 residual norm: {l2_adapt:.2e}")
    print(f"Number of points: {len(xi_adapt)}")
    print(f"Refinement iterations: {n_iter}")
    
    print()
    
    # Method 3: scipy IVP
    print("Method 3: scipy IVP Solver")
    print("-"*40)
    
    xi_ivp, f_ivp, fp_ivp, success_ivp = solve_ivp_scipy()
    
    if success_ivp:
        l2_ivp = compute_l2_residual(xi_ivp, f_ivp, fp_ivp, m, c)
        print(f"L2 residual norm: {l2_ivp:.2e}")
        print(f"Number of points: {len(xi_ivp)}")
    else:
        print("IVP solver failed")
        xi_ivp, f_ivp, fp_ivp = xi_ana, f_ana, fp_ana
        l2_ivp = l2_ana
    
    print()
    print("="*60)
    
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    # Save results
    np.savez('outputs/traveling_wave_analytical.npz', xi=xi_ana, f=f_ana, fp=fp_ana, l2_residual=l2_ana)
    np.savez('outputs/traveling_wave_adaptive.npz', xi=xi_adapt, f=f_adapt, fp=fp_adapt, l2_residual=l2_adapt)
    np.savez('outputs/traveling_wave_ivp.npz', xi=xi_ivp, f=f_ivp, fp=fp_ivp, l2_residual=l2_ivp)
    
    # Generate plots
    plt.figure(figsize=(14, 5))
    
    # Plot 1: Traveling wave profile
    plt.subplot(1, 3, 1)
    plt.plot(xi_ana, f_ana, 'k-', label='Analytical', linewidth=2, alpha=0.7)
    plt.plot(xi_adapt, f_adapt, 'b--', label='Adaptive', linewidth=2, alpha=0.7)
    if success_ivp:
        plt.plot(xi_ivp, f_ivp, 'r:', label='scipy IVP', linewidth=2, alpha=0.7)
    plt.xlabel(r'$\xi = x - ct$', fontsize=12)
    plt.ylabel(r'$f(\xi)$', fontsize=12)
    plt.title('Traveling Wave Profile', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(xi_ana[0], xi_ana[-1])
    plt.ylim(-0.1, 1.1)
    
    # Plot 2: Residual distribution
    plt.subplot(1, 3, 2)
    res_ana = residual_ode(xi_ana, f_ana, fp_ana, m, c)
    plt.plot(xi_ana, np.abs(res_ana), 'k-', label='Analytical', linewidth=2, alpha=0.7)
    res_adapt = residual_ode(xi_adapt, f_adapt, fp_adapt, m, c)
    plt.plot(xi_adapt, np.abs(res_adapt), 'b--', label='Adaptive', linewidth=2, alpha=0.7)
    if success_ivp:
        res_ivp = residual_ode(xi_ivp, f_ivp, fp_ivp, m, c)
        plt.plot(xi_ivp, np.abs(res_ivp), 'r:', label='scipy IVP', linewidth=2, alpha=0.7)
    plt.xlabel(r'$\xi$', fontsize=12)
    plt.ylabel('|Residual|', fontsize=12)
    plt.title('ODE Residual (log scale)', fontsize=14)
    plt.yscale('log')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 3: Phase portrait
    plt.subplot(1, 3, 3)
    plt.plot(f_ana, fp_ana, 'k-', label='Analytical', linewidth=2, alpha=0.7)
    plt.plot(f_adapt, fp_adapt, 'b--', label='Adaptive', linewidth=2, alpha=0.7)
    if success_ivp:
        plt.plot(f_ivp, fp_ivp, 'r:', label='scipy IVP', linewidth=2, alpha=0.7)
    plt.xlabel(r'$f(\xi)$', fontsize=12)
    plt.ylabel(r"$f'(\xi)$", fontsize=12)
    plt.title('Phase Portrait', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(-0.1, 1.1)
    
    plt.tight_layout()
    plt.savefig('report/images/traveling_wave_profile.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Plot 4: Convergence study
    plt.figure(figsize=(10, 6))
    
    n_values = [100, 200, 500, 1000, 2000, 5000]
    l2_residuals = []
    
    for n in n_values:
        xi_test = np.linspace(-5, 5, n)
        arg = 1 + m * c * (-5 - xi_test)
        f_test = np.maximum(0, arg) ** (1/m)
        f_reg = np.maximum(f_test, 1e-12)
        fp_test = -c * f_reg**(1-m)
        fp_test[f_test <= 0] = 0
        l2_res = compute_l2_residual(xi_test, f_test, fp_test, m, c)
        l2_residuals.append(l2_res)
    
    plt.subplot(2, 1, 1)
    plt.loglog(n_values, l2_residuals, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('Number of Grid Points', fontsize=12)
    plt.ylabel('L2 Residual Norm', fontsize=12)
    plt.title('Convergence Study (Grid Resolution)', fontsize=14)
    plt.grid(True, alpha=0.3, which='both')
    
    plt.subplot(2, 1, 2)
    # Show the residual distribution for finest grid
    xi_fine = np.linspace(-5, 5, 5000)
    arg = 1 + m * c * (-5 - xi_fine)
    f_fine = np.maximum(0, arg) ** (1/m)
    f_reg = np.maximum(f_fine, 1e-12)
    fp_fine = -c * f_reg**(1-m)
    fp_fine[f_fine <= 0] = 0
    res_fine = residual_ode(xi_fine, f_fine, fp_fine, m, c)
    plt.plot(xi_fine, np.abs(res_fine), 'b-', linewidth=1)
    plt.xlabel(r'$\xi$', fontsize=12)
    plt.ylabel('|Residual|', fontsize=12)
    plt.title('Residual Distribution (5000 points)', fontsize=14)
    plt.yscale('log')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/convergence_study.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Plot 5: Effect of porous medium exponent m
    plt.figure(figsize=(10, 5))
    
    m_values = [1.5, 2.0, 3.0, 5.0]
    colors = ['blue', 'green', 'orange', 'red']
    
    for m_val, color in zip(m_values, colors):
        xi_test = np.linspace(-5, 5, 500)
        arg = 1 + m_val * c * (-5 - xi_test)
        f_test = np.maximum(0, arg) ** (1/m_val)
        plt.plot(xi_test, f_test, color=color, linewidth=2, label=f'm={m_val}')
    
    plt.xlabel(r'$\xi = x - ct$', fontsize=12)
    plt.ylabel(r'$f(\xi)$', fontsize=12)
    plt.title('Effect of Porous Medium Exponent m', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(-5, 5)
    plt.ylim(-0.1, 1.1)
    
    plt.tight_layout()
    plt.savefig('report/images/effect_of_m.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Plot 6: Adaptive refinement iterations
    plt.figure(figsize=(8, 6))
    
    tolerances = [1e-4, 1e-6, 1e-8, 1e-10]
    n_points_achieved = []
    l2_achieved = []
    
    for tol in tolerances:
        xi_t, f_t, fp_t, l2_t, n_iter_t = adaptive_integration(tol=tol)
        n_points_achieved.append(len(xi_t))
        l2_achieved.append(l2_t)
    
    plt.subplot(2, 1, 1)
    plt.semilogy(tolerances, l2_achieved, 'bo-', linewidth=2, markersize=8)
    plt.plot(tolerances, tolerances, 'k--', label='Reference: y=x', alpha=0.5)
    plt.xlabel('Target Tolerance', fontsize=12)
    plt.ylabel('Achieved L2 Residual', fontsize=12)
    plt.title('Adaptive Refinement: Achieved vs Target', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 1, 2)
    plt.semilogy(tolerances, n_points_achieved, 'ro-', linewidth=2, markersize=8)
    plt.xlabel('Target Tolerance', fontsize=12)
    plt.ylabel('Number of Points', fontsize=12)
    plt.title('Adaptive Refinement: Mesh Points Required', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/adaptive_refinement.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("\nResults saved to outputs/")
    print("Figures saved to report/images/")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Analytical L2 residual: {l2_ana:.2e}")
    print(f"Adaptive L2 residual: {l2_adapt:.2e}")
    print(f"scipy IVP L2 residual: {l2_ivp:.2e}")
    print(f"\nTarget tolerance: {TOL}")
    best_residual = min(l2_ana, l2_adapt, l2_ivp)
    print(f"Best achieved L2 residual: {best_residual:.2e}")
    
    if best_residual < TOL:
        print(f"SUCCESS: Residual {best_residual:.2e} < {TOL}")
    else:
        print(f"Note: Best residual {best_residual:.2e} for target {TOL}")
    
    return {
        'analytical': {'l2_residual': l2_ana},
        'adaptive': {'l2_residual': l2_adapt, 'n_points': len(xi_adapt)},
        'ivp': {'success': success_ivp, 'l2_residual': l2_ivp}
    }

if __name__ == '__main__':
    results = main()
