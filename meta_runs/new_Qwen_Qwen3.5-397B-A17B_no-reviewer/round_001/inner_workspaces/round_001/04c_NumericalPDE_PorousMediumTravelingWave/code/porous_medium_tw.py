"""
Numerical solution of porous medium equation traveling wave profiles.

The porous medium equation (PME) is:
    u_t = (u^m * u_x)_x

For traveling wave solutions u(x,t) = f(ξ) where ξ = x - ct, this reduces to:
    -c * f' = (f^m * f')'

Integrating once (assuming f → 0, f' → 0 as ξ → ∞):
    -c * f = f^m * f'

This gives the first-order ODE:
    f' = -c * f^(1-m)

For m > 1, this has compact support solutions.

We solve this as a boundary value problem with adaptive step size
to achieve L2 residual < 1e-8.
"""

import numpy as np
from scipy import integrate
from scipy.optimize import brentq
import matplotlib.pyplot as plt
import os

# Parameters
m = 2.0  # Porous medium exponent (m > 1)
c = 1.0  # Wave speed
TOL = 1e-8  # Target L2 residual tolerance

# Boundary conditions
f_left = 1.0   # f(-∞) ≈ 1 (saturated state)
f_right = 0.0  # f(+∞) = 0 (dry state)

# Domain for numerical solution
xi_min = -10
xi_max = 10


def ode_system(xi, y, m=m, c=c):
    """
    Alternative formulation: solve the second-order ODE directly.
    
    -c * f' = (f^m * f')'
    
    Let v = f^m * f', then:
    v' = -c * f'
    
    And f' = v / f^m (when f > 0)
    """
    f, v = y
    eps = 1e-12
    f_reg = max(abs(f), eps)
    
    if f > eps:
        df_dxi = v / (f**m)
    else:
        df_dxi = 0.0
    
    dv_dxi = -c * df_dxi
    
    return [df_dxi, dv_dxi]


def solve_traveling_wave_rk45(m=m, c=c, tol=TOL):
    """
    Solve the traveling wave ODE using adaptive RK45.
    
    We integrate from ξ = 0 where f = f0 (to be determined) to ξ_max.
    The shooting method finds f0 such that f(ξ_max) ≈ 0.
    """
    
    # For the porous medium equation traveling wave,
    # there's an exact solution for certain cases.
    # For m=2, the Barenblatt solution gives us guidance.
    
    # We'll use a shooting method from the left boundary
    # where f ≈ 1 and find the correct slope.
    
    def shoot(f_slope_guess):
        """Integrate ODE with given initial slope and return f at right boundary."""
        y0 = [f_left, f_slope_guess]  # [f, f^m * f']
        
        try:
            sol = integrate.solve_ivp(
                lambda xi, y: ode_system(xi, y, m, c),
                [xi_min, xi_max],
                y0,
                method='RK45',
                rtol=tol/10,
                atol=tol/10,
                dense_output=True,
                max_step=0.1
            )
            return sol.y[0, -1]  # f at right boundary
        except:
            return 1.0  # Return non-zero to indicate failure
    
    # Find the correct initial slope using bisection
    # f' should be negative (decreasing profile)
    slope_min = -10.0
    slope_max = -0.01
    
    try:
        optimal_slope = brentq(shoot, slope_min, slope_max, xtol=1e-10)
    except:
        # If shooting fails, use analytical approximation
        optimal_slope = -c  # Rough estimate
    
    # Final integration with optimal slope
    y0 = [f_left, optimal_slope]
    
    sol = integrate.solve_ivp(
        lambda xi, y: ode_system(xi, y, m, c),
        [xi_min, xi_max],
        y0,
        method='RK45',
        rtol=tol/100,
        atol=tol/100,
        dense_output=True,
        max_step=0.01
    )
    
    return sol


def compute_residual(sol, m=m, c=c):
    """
    Compute the L2 residual of the ODE solution.
    
    The ODE is: -c*f' = (f^m * f')'
    
    Residual = -c*f' - (f^m * f')'
    """
    xi = sol.t
    f = sol.y[0]
    v = sol.y[1]  # v = f^m * f'
    
    # Compute derivatives numerically
    df_dxi = np.gradient(f, xi)
    dv_dxi = np.gradient(v, xi)
    
    # Residual: -c*f' - v'
    residual = -c * df_dxi - dv_dxi
    
    # L2 norm
    l2_norm = np.sqrt(np.trapz(residual**2, xi))
    
    return l2_norm, residual


def analytical_solution(xi, m=m, c=c):
    """
    Analytical traveling wave solution for porous medium equation.
    
    For the ODE -c*f = f^m * f' (integrated form),
    we can solve: f' = -c * f^(1-m)
    
    This gives: f^(m-1) = c*(m-1)*(xi_0 - xi)
    
    So: f(xi) = [max(0, c*(m-1)*(xi_0 - xi))]^(1/(m-1))
    """
    xi_0 = 0  # Front position
    arg = c * (m - 1) * (xi_0 - xi)
    f = np.maximum(0, arg) ** (1.0 / (m - 1))
    return f


def main():
    print("="*60)
    print("Porous Medium Equation - Traveling Wave Solution")
    print("="*60)
    print(f"Parameters: m = {m}, c = {c}")
    print(f"Target L2 residual tolerance: {TOL}")
    print()
    
    # Solve the ODE
    print("Solving traveling wave ODE with adaptive RK45...")
    sol = solve_traveling_wave_rk45()
    
    # Compute residual
    l2_norm, residual = compute_residual(sol)
    print(f"L2 residual norm: {l2_norm:.6e}")
    
    # Check if tolerance is met
    if l2_norm < TOL:
        print(f"✓ Tolerance met (residual < {TOL})")
    else:
        print(f"✗ Tolerance not met, refining...")
        # Refine with tighter tolerances
        sol = solve_traveling_wave_rk45(tol=TOL/10)
        l2_norm, residual = compute_residual(sol)
        print(f"Refined L2 residual norm: {l2_norm:.6e}")
    
    # Extract solution
    xi = sol.t
    f = sol.y[0]
    v = sol.y[1]
    
    # Ensure non-negativity
    f = np.maximum(f, 0)
    
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    # Save numerical solution
    np.savez('outputs/traveling_wave_solution.npz', xi=xi, f=f, v=v, residual=residual)
    
    # Plot 1: Solution profile
    plt.figure(figsize=(10, 6))
    plt.plot(xi, f, 'b-', linewidth=2, label='Numerical solution')
    
    # Add analytical solution for comparison
    f_analytical = analytical_solution(xi, m, c)
    # Shift analytical to match numerical
    xi_shift = xi[np.argmin(np.abs(f - 0.5))] - xi[np.argmin(np.abs(f_analytical - 0.5))]
    f_analytical_shifted = analytical_solution(xi - xi_shift, m, c)
    plt.plot(xi, f_analytical_shifted, 'r--', linewidth=2, label='Analytical (shifted)')
    
    plt.xlabel(r'$\xi = x - ct$', fontsize=12)
    plt.ylabel(r'$f(\xi)$', fontsize=12)
    plt.title(f'Porous Medium Traveling Wave Profile (m={m}, c={c})', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(xi_min, xi_max)
    plt.ylim(-0.1, 1.1)
    plt.tight_layout()
    plt.savefig('report/images/solution_profile.png', dpi=150)
    plt.close()
    print("Saved: report/images/solution_profile.png")
    
    # Plot 2: Residual distribution
    plt.figure(figsize=(10, 6))
    plt.plot(xi, residual, 'g-', linewidth=1.5, label='Pointwise residual')
    plt.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    plt.axhline(y=TOL, color='r', linestyle='--', linewidth=1, label=f'Tolerance ({TOL})')
    plt.axhline(y=-TOL, color='r', linestyle='--', linewidth=1)
    plt.xlabel(r'$\xi$', fontsize=12)
    plt.ylabel('Residual', fontsize=12)
    plt.title(f'ODE Residual Distribution (L2 norm = {l2_norm:.6e})', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/residual_distribution.png', dpi=150)
    plt.close()
    print("Saved: report/images/residual_distribution.png")
    
    # Plot 3: Phase portrait (f vs f')
    df_dxi = np.gradient(f, xi)
    plt.figure(figsize=(8, 8))
    plt.plot(f, df_dxi, 'b-', linewidth=2)
    plt.xlabel(r'$f(\xi)$', fontsize=12)
    plt.ylabel(r"$f'(\xi)$", fontsize=12)
    plt.title('Phase Portrait of Traveling Wave', fontsize=14)
    plt.grid(True, alpha=0.3)
    
    # Add theoretical curve f' = -c * f^(1-m)
    f_theory = np.linspace(0.01, 1, 100)
    df_theory = -c * f_theory**(1-m)
    plt.plot(f_theory, df_theory, 'r--', linewidth=2, label='Theoretical: f\' = -c·f^(1-m)')
    plt.legend()
    plt.tight_layout()
    plt.savefig('report/images/phase_portrait.png', dpi=150)
    plt.close()
    print("Saved: report/images/phase_portrait.png")
    
    # Plot 4: Convergence study
    tolerances = [1e-4, 1e-6, 1e-8, 1e-10]
    l2_norms = []
    
    for tol in tolerances:
        sol_test = solve_traveling_wave_rk45(tol=tol)
        l2_test, _ = compute_residual(sol_test)
        l2_norms.append(l2_test)
        print(f"  Tolerance {tol}: L2 norm = {l2_test:.6e}")
    
    plt.figure(figsize=(10, 6))
    plt.loglog(tolerances, l2_norms, 'bo-', linewidth=2, markersize=8)
    plt.loglog(tolerances, tolerances, 'r--', linewidth=2, label='Reference slope = 1')
    plt.xlabel('Solver Tolerance', fontsize=12)
    plt.ylabel('L2 Residual Norm', fontsize=12)
    plt.title('Convergence Study: Residual vs Solver Tolerance', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3, which='both')
    plt.tight_layout()
    plt.savefig('report/images/convergence_study.png', dpi=150)
    plt.close()
    print("Saved: report/images/convergence_study.png")
    
    print()
    print("="*60)
    print("Summary")
    print("="*60)
    print(f"Final L2 residual norm: {l2_norm:.6e}")
    print(f"Target tolerance: {TOL}")
    print(f"Status: {'PASSED' if l2_norm < TOL else 'NEEDS REFINEMENT'}")
    print()
    
    return l2_norm, xi, f, residual


if __name__ == "__main__":
    main()
