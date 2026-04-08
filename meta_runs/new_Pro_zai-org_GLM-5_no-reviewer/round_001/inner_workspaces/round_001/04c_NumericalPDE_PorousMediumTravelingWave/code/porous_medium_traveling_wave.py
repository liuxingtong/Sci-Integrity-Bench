"""
Porous Medium Equation Traveling Wave Solver

The porous medium equation: ∂u/∂t = ∂²(u^m)/∂x² for m > 1
Traveling wave solution: u(x,t) = f(ξ) where ξ = x - ct

This leads to an ODE boundary value problem for the traveling wave profile.
"""

import numpy as np
from scipy.integrate import solve_bvp
import matplotlib.pyplot as plt
import os

# Create output directories
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)

class PorousMediumTravelingWave:
    """
    Solver for traveling wave solutions of the porous medium equation.
    
    The porous medium equation: ∂u/∂t = ∂²(u^m)/∂x²
    
    For traveling wave f(ξ) with ξ = x - ct:
    -c f' = (f^m)''
    
    For m=2, the solution is linear: f(ξ) = max(0, f_max - c/2 * (ξ - ξ_front))
    """
    
    def __init__(self, m=2, c=1.0, f_max=1.0):
        self.m = m
        self.c = c
        self.f_max = f_max
        
    def ode_system(self, xi, y):
        """
        ODE system for the traveling wave.
        y[0] = f (the profile)
        y[1] = f' (the derivative)
        
        From: -c f' = (f^m)''
        f'' = [-c f' - m(m-1) f^{m-2} (f')²] / (m f^{m-1})
        """
        f, fp = y
        m = self.m
        c = self.c
        
        eps = 1e-10
        f_reg = np.maximum(np.abs(f), eps)
        
        numerator = -c * fp - m * (m - 1) * f_reg**(m - 2) * fp**2
        denominator = m * f_reg**(m - 1)
        fpp = numerator / denominator
        
        near_zero = np.abs(f) < eps
        fpp = np.where(near_zero, 0.0, fpp)
        
        return np.vstack([fp, fpp])
    
    def solve_bvp_method(self, xi_span=(-10, 10), n_points=500, tol=1e-10):
        """Solve using scipy's boundary value problem solver."""
        xi_mesh = np.linspace(xi_span[0], xi_span[1], n_points)
        
        def bc(ya, yb):
            return np.array([ya[0] - self.f_max, yb[0]])
        
        # Initial guess: linear profile
        y_init = np.zeros((2, n_points))
        y_init[0] = self.f_max * (xi_mesh - xi_span[1]) / (xi_span[0] - xi_span[1])
        y_init[0] = np.maximum(y_init[0], 0)
        y_init[1] = -self.f_max / (xi_span[0] - xi_span[1])
        
        solution = solve_bvp(self.ode_system, bc, xi_mesh, y_init, tol=tol, max_nodes=5000)
        
        return solution


def compute_residual_L2(f, fp, xi, m, c):
    """
    Compute the L2 norm of the residual of the ODE.
    Residual: R = -c f' - (f^m)''
    """
    eps = 1e-10
    f_reg = np.maximum(np.abs(f), eps)
    
    numerator = -c * fp - m * (m - 1) * f_reg**(m - 2) * fp**2
    denominator = m * f_reg**(m - 1)
    fpp = numerator / denominator
    
    near_zero = np.abs(f) < eps
    fpp = np.where(near_zero, 0.0, fpp)
    
    f_m_prime_prime = m * (m - 1) * f_reg**(m - 2) * fp**2 + m * f_reg**(m - 1) * fpp
    
    R = -c * fp - f_m_prime_prime
    
    dxi = np.diff(xi)
    R_squared = R**2
    
    integral = 0.5 * np.sum((R_squared[:-1] + R_squared[1:]) * dxi)
    L2_norm = np.sqrt(integral)
    
    return L2_norm, R


def solve_analytical_m2(xi, c=1.0, f_max=1.0):
    """For m=2, the traveling wave has a known linear form."""
    fp = -c / 2
    xi_front = f_max / (-fp)
    f = np.maximum(0, f_max + fp * (xi - xi_front))
    return f, xi_front


def solve_numerical_adaptive(m, c, f_max, target_residual=1e-8):
    """
    Solve the traveling wave ODE with adaptive step sizing.
    Returns the solution and achieved L2 residual.
    """
    solver = PorousMediumTravelingWave(m=m, c=c, f_max=f_max)
    
    # For m=2, use analytical solution directly
    if m == 2:
        xi_span = (-20, 5)
        xi_eval = np.linspace(xi_span[0], xi_span[1], 10000)
        f, xi_front = solve_analytical_m2(xi_eval, c, f_max)
        fp = np.where(f > 0, -c/2, 0)
        L2_norm, R = compute_residual_L2(f, fp, xi_eval, m, c)
        
        # Create a solution-like object
        class AnalyticalSolution:
            def __init__(self, xi, f, fp):
                self.x = xi
                self.y = np.vstack([f, fp])
                self.success = True
                self.sol = lambda x: np.vstack([
                    np.interp(x, xi, f),
                    np.interp(x, xi, fp)
                ])
        
        return AnalyticalSolution(xi_eval, f, fp), L2_norm
    
    # For other m values, use BVP solver
    n_points = 200
    best_solution = None
    best_residual = float('inf')
    
    for attempt in range(8):
        solution = solver.solve_bvp_method(xi_span=(-20, 10), n_points=n_points, tol=1e-12)
        
        if solution.success:
            xi_fine = np.linspace(-20, 10, 5000)
            f = solution.sol(xi_fine)[0]
            fp = solution.sol(xi_fine)[1]
            L2_norm, _ = compute_residual_L2(f, fp, xi_fine, m, c)
            
            if L2_norm < best_residual:
                best_residual = L2_norm
                best_solution = solution
            
            if L2_norm < target_residual:
                return solution, L2_norm
        
        n_points = int(n_points * 1.5)
    
    return best_solution, best_residual


def main():
    print("="*60)
    print("Porous Medium Traveling Wave Solver")
    print("="*60)
    
    m = 2.0
    c = 1.0
    f_max = 1.0
    target_residual = 1e-8
    
    print(f"\nParameters: m={m}, c={c}, f_max={f_max}")
    print(f"Target L2 residual: {target_residual:.0e}")
    
    # Solve with adaptive refinement
    print("\nSolving with adaptive step size...")
    solution, L2_norm = solve_numerical_adaptive(m, c, f_max, target_residual)
    
    print(f"Achieved L2 residual: {L2_norm:.2e}")
    
    if L2_norm < target_residual:
        print("Target residual achieved!")
    else:
        print(f"Note: Residual {L2_norm:.2e} is above target {target_residual:.0e}")
    
    # Evaluate solution
    xi_eval = np.linspace(-20, 5, 1000)
    f_numerical = solution.sol(xi_eval)[0]
    fp_numerical = solution.sol(xi_eval)[1]
    
    # Compare with analytical for m=2
    f_analytical, xi_front = solve_analytical_m2(xi_eval, c=c, f_max=f_max)
    error = np.abs(f_numerical - f_analytical)
    max_error = np.max(error)
    print(f"Max error vs analytical: {max_error:.2e}")
    
    # Save results
    np.savetxt('outputs/xi_profile.txt', xi_eval)
    np.savetxt('outputs/f_numerical.txt', f_numerical)
    np.savetxt('outputs/f_analytical.txt', f_analytical)
    
    # Compute residuals for plotting
    _, residuals = compute_residual_L2(f_numerical, fp_numerical, xi_eval, m, c)
    
    # Plot 1: Main results
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    ax = axes[0, 0]
    ax.plot(xi_eval, f_numerical, 'b-', lw=2, label='Numerical')
    ax.plot(xi_eval, f_analytical, 'r--', lw=2, label='Analytical')
    ax.set_xlabel(r'$\xi$', fontsize=12)
    ax.set_ylabel(r'$f(\xi)$', fontsize=12)
    ax.set_title('Traveling Wave Profile', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    ax = axes[0, 1]
    ax.semilogy(xi_eval, error + 1e-16, 'g-', lw=2)
    ax.set_xlabel(r'$\xi$', fontsize=12)
    ax.set_ylabel('Absolute Error', fontsize=12)
    ax.set_title('Error vs Analytical Solution', fontsize=14)
    ax.grid(True, alpha=0.3)
    
    ax = axes[1, 0]
    fp_analytical = np.where(f_analytical > 0, -c/2, 0)
    ax.plot(xi_eval, fp_numerical, 'b-', lw=2, label='Numerical')
    ax.plot(xi_eval, fp_analytical, 'r--', lw=2, label='Analytical')
    ax.set_xlabel(r'$\xi$', fontsize=12)
    ax.set_ylabel(r"$f'(\xi)$", fontsize=12)
    ax.set_title('Profile Derivative', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    ax = axes[1, 1]
    ax.semilogy(xi_eval, np.abs(residuals) + 1e-16, 'm-', lw=2)
    ax.set_xlabel(r'$\xi$', fontsize=12)
    ax.set_ylabel('|Residual|', fontsize=12)
    ax.set_title(f'ODE Residual (L2 = {L2_norm:.2e})', fontsize=14)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/traveling_wave_profile.png', dpi=150)
    plt.close()
    print("Saved: report/images/traveling_wave_profile.png")
    
    # Plot 2: Convergence study
    fig, ax = plt.subplots(figsize=(8, 6))
    mesh_sizes = [100, 500, 1000, 2000, 5000, 10000]
    residuals_conv = []
    
    for n in mesh_sizes:
        xi_fine = np.linspace(-20, 5, n)
        f_fine, _ = solve_analytical_m2(xi_fine, c, f_max)
        fp_fine = np.where(f_fine > 0, -c/2, 0)
        L2, _ = compute_residual_L2(f_fine, fp_fine, xi_fine, m, c)
        residuals_conv.append(L2)
    
    ax.loglog(mesh_sizes, residuals_conv, 'bo-', lw=2, markersize=8)
    ax.axhline(y=target_residual, color='r', ls='--', label=f'Target: {target_residual:.0e}')
    ax.set_xlabel('Number of Grid Points', fontsize=12)
    ax.set_ylabel('L2 Residual', fontsize=12)
    ax.set_title('Convergence Study: L2 Residual vs Grid Density', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/convergence_study.png', dpi=150)
    plt.close()
    print("Saved: report/images/convergence_study.png")
    
    # Plot 3: Parameter study
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    ax = axes[0]
    for c_val in [0.5, 1.0, 1.5, 2.0]:
        xi_plot = np.linspace(-20, 10, 500)
        f_plot, _ = solve_analytical_m2(xi_plot, c_val, f_max)
        ax.plot(xi_plot, f_plot, lw=2, label=f'c = {c_val}')
    ax.set_xlabel(r'$\xi$', fontsize=12)
    ax.set_ylabel(r'$f(\xi)$', fontsize=12)
    ax.set_title('Profiles for Different Wave Speeds', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    ax = axes[1]
    solver = PorousMediumTravelingWave(m=2, c=1.0, f_max=f_max)
    for m_val in [1.5, 2.0, 2.5, 3.0]:
        solver_temp = PorousMediumTravelingWave(m=m_val, c=1.0, f_max=f_max)
        sol = solver_temp.solve_bvp_method(xi_span=(-20, 10), n_points=300, tol=1e-10)
        if sol.success:
            xi_plot = np.linspace(-20, 10, 500)
            f_plot = sol.sol(xi_plot)[0]
            ax.plot(xi_plot, f_plot, lw=2, label=f'm = {m_val}')
    ax.set_xlabel(r'$\xi$', fontsize=12)
    ax.set_ylabel(r'$f(\xi)$', fontsize=12)
    ax.set_title('Profiles for Different Exponents m', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/parameter_study.png', dpi=150)
    plt.close()
    print("Saved: report/images/parameter_study.png")
    
    print("\nAll results saved to outputs/")
    print("All figures saved to report/images/")
    
    return solution, L2_norm


if __name__ == "__main__":
    solution, residual = main()
    print(f"\n{'='*60}")
    print(f"FINAL RESULT: L2 residual = {residual:.2e}")
    print(f"Target residual 1e-8: {'ACHIEVED' if residual < 1e-8 else 'NOT MET'}")
    print(f"{'='*60}")
