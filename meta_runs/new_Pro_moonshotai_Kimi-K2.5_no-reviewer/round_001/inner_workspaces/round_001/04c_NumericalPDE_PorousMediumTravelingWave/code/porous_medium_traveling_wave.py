"""
Numerical solution of the Porous Medium Equation (PME) traveling wave.

The PME is: ∂u/∂t = ∂/∂x(u^m ∂u/∂x)

For traveling wave solutions u(x,t) = f(ξ) where ξ = x - ct,
we obtain the ODE:
    -c f' = (f^m f')'

Integrating once:
    -c f = f^m f' + C1

For a saturation front connecting f(-∞) = 1 to f(+∞) = 0,
we set C1 = 0 and obtain:
    f' = -c f^(1-m)

For the classical case m > 1 (e.g., m = 2), this gives:
    f' = -c / f

Alternatively, for the pressure formulation with m = 1 (linear case):
    f' = -c (constant slope)

This script solves the general traveling wave ODE numerically
and verifies the solution against the analytical form.
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os

# Create output directories if they don't exist
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# =============================================================================
# Model Parameters
# =============================================================================
M = 2.0          # Porous medium exponent (m > 1 for degenerate diffusion)
C = 1.0          # Wave speed
F_LEFT = 1.0     # Left boundary condition (f → 1 as ξ → -∞)
F_RIGHT = 0.0    # Right boundary condition (f → 0 as ξ → +∞)

# =============================================================================
# Define the ODE System
# =============================================================================

def pme_ode(xi, f, m, c):
    """
    ODE for the porous medium traveling wave.
    
    From -c f = f^m f', we get:
        f' = -c * f / f^m = -c * f^(1-m)
    
    For f > 0. For the degenerate case (f = 0), we need special handling.
    """
    f = max(f[0], 1e-10)  # Avoid division by zero
    if m == 1:
        df_dxi = -c
    else:
        df_dxi = -c * f**(1 - m)
    return [df_dxi]


def pme_ode_with_regularization(xi, f, m, c, epsilon=1e-6):
    """
    Regularized ODE to handle the degenerate case near f = 0.
    Uses f_epsilon = max(f, epsilon) to avoid singularity.
    """
    f_reg = max(f[0], epsilon)
    if m == 1:
        df_dxi = -c
    else:
        df_dxi = -c * f_reg**(1 - m)
    return [df_dxi]


# =============================================================================
# Analytical Solution (for verification)
# =============================================================================

def analytical_solution(xi, m, c, xi_0):
    """
    Analytical solution for the traveling wave.
    
    For m > 1, integrating f' = -c * f^(1-m):
        f^m / m = -c * (xi - xi_0)
        f = [m * c * (xi_0 - xi)]^(1/m) for xi < xi_0
        f = 0 for xi >= xi_0
    
    This is the Barenblatt solution / self-similar solution form.
    """
    if m == 1:
        # Linear case: exponential decay
        return np.exp(-c * (xi - xi_0))
    else:
        # Degenerate case: compact support
        prefactor = m * c
        argument = prefactor * (xi_0 - xi)
        f = np.where(argument > 0, argument**(1/m), 0)
        return f


# =============================================================================
# Numerical Integration
# =============================================================================

def solve_traveling_wave(m, c, f0, xi_span, method='RK45', rtol=1e-8, atol=1e-10):
    """
    Solve the traveling wave ODE numerically.
    
    Parameters:
    -----------
    m : float
        Porous medium exponent
    c : float
        Wave speed
    f0 : float
        Initial condition f(xi_span[0]) = f0
    xi_span : tuple
        Integration interval (xi_start, xi_end)
    method : str
        Integration method for solve_ivp
    rtol, atol : float
        Relative and absolute tolerances
    
    Returns:
    --------
    sol : OdeSolution
        Solution object from solve_ivp
    """
    # Use regularized ODE for numerical stability
    sol = solve_ivp(
        lambda xi, f: pme_ode_with_regularization(xi, f, m, c),
        xi_span,
        [f0],
        method=method,
        rtol=rtol,
        atol=atol,
        dense_output=True
    )
    return sol


# =============================================================================
# Verification: Residual Calculation
# =============================================================================

def compute_residual(sol, m, c, xi_eval):
    """
    Compute the residual of the ODE: |f' + c * f^(1-m)|
    
    This verifies that the numerical solution satisfies the ODE.
    """
    f = sol.sol(xi_eval)[0]
    # Compute derivative numerically
    df_dxi = np.gradient(f, xi_eval)
    
    # ODE residual: f' + c * f^(1-m) should be ~ 0
    f_safe = np.maximum(f, 1e-10)
    residual = df_dxi + c * f_safe**(1 - m)
    
    return residual, f, df_dxi


def compute_algebraic_residual(sol, m, c, xi_eval):
    """
    Compute residual of the integrated form: |f^m * f' + c * f|
    
    This is an alternative verification using the first integral.
    """
    f = sol.sol(xi_eval)[0]
    df_dxi = np.gradient(f, xi_eval)
    
    # First integral: f^m * f' + c * f = 0
    residual = (f**m) * df_dxi + c * f
    
    return residual


# =============================================================================
# Main Analysis
# =============================================================================

def main():
    print("=" * 70)
    print("POROUS MEDIUM TRAVELING WAVE - NUMERICAL SOLUTION")
    print("=" * 70)
    
    # Test cases
    test_cases = [
        {'m': 1.0, 'c': 1.0, 'name': 'Linear (m=1)'},
        {'m': 2.0, 'c': 1.0, 'name': 'Quadratic (m=2)'},
        {'m': 3.0, 'c': 0.5, 'name': 'Cubic (m=3)'},
    ]
    
    results = {}
    
    for case in test_cases:
        m = case['m']
        c = case['c']
        name = case['name']
        
        print(f"\n{'='*70}")
        print(f"Case: {name}")
        print(f"Parameters: m = {m}, c = {c}")
        print(f"{'='*70}")
        
        # Integration settings
        xi_start = -5.0
        xi_end = 5.0
        f0 = 1.0  # Initial condition at xi_start
        
        # Solve numerically
        print(f"\nIntegrating ODE from ξ = {xi_start} to {xi_end}...")
        sol = solve_traveling_wave(m, c, f0, (xi_start, xi_end))
        
        print(f"Integration successful: {sol.success}")
        print(f"Number of function evaluations: {sol.nfev}")
        print(f"Number of steps: {len(sol.t)}")
        
        # Evaluate solution on fine grid
        xi_fine = np.linspace(xi_start, xi_end, 1000)
        f_numerical = sol.sol(xi_fine)[0]
        
        # Compute residuals for verification
        residual_ode, f_vals, df_vals = compute_residual(sol, m, c, xi_fine)
        residual_algebraic = compute_algebraic_residual(sol, m, c, xi_fine)
        
        # Error metrics
        max_residual_ode = np.max(np.abs(residual_ode))
        mean_residual_ode = np.mean(np.abs(residual_ode))
        max_residual_alg = np.max(np.abs(residual_algebraic))
        mean_residual_alg = np.mean(np.abs(residual_algebraic))
        
        print(f"\nVerification Results:")
        print(f"  ODE Residual (max): {max_residual_ode:.2e}")
        print(f"  ODE Residual (mean): {mean_residual_ode:.2e}")
        print(f"  Algebraic Residual (max): {max_residual_alg:.2e}")
        print(f"  Algebraic Residual (mean): {mean_residual_alg:.2e}")
        
        # Compare with analytical solution (if available)
        if m > 1:
            # Find the front position from numerical solution
            front_idx = np.where(f_numerical < 0.01)[0]
            if len(front_idx) > 0:
                xi_0_approx = xi_fine[front_idx[0]]
            else:
                xi_0_approx = xi_end
            
            f_analytical = analytical_solution(xi_fine, m, c, xi_0_approx)
            
            # Compute error
            error = np.abs(f_numerical - f_analytical)
            max_error = np.max(error)
            mean_error = np.mean(error)
            
            print(f"\nComparison with Analytical Solution:")
            print(f"  Approximate front position ξ_0 ≈ {xi_0_approx:.4f}")
            print(f"  Max error: {max_error:.2e}")
            print(f"  Mean error: {mean_error:.2e}")
        else:
            f_analytical = None
            max_error = None
            mean_error = None
        
        # Store results
        results[name] = {
            'm': m,
            'c': c,
            'xi': xi_fine,
            'f_numerical': f_numerical,
            'f_analytical': f_analytical,
            'residual_ode': residual_ode,
            'residual_algebraic': residual_algebraic,
            'max_residual_ode': max_residual_ode,
            'mean_residual_ode': mean_residual_ode,
            'max_error': max_error,
            'mean_error': mean_error,
            'sol': sol
        }
        
        # Save data
        np.savez(f'../outputs/results_{name.replace(" ", "_").replace("(", "").replace(")", "")}.npz',
                 xi=xi_fine, f_numerical=f_numerical, 
                 f_analytical=f_analytical if f_analytical is not None else np.zeros_like(xi_fine),
                 residual_ode=residual_ode, residual_algebraic=residual_algebraic)
    
    # Generate plots
    print("\n" + "=" * 70)
    print("GENERATING FIGURES")
    print("=" * 70)
    
    generate_figures(results)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    
    return results


def generate_figures(results):
    """Generate all figures for the report."""
    
    # Figure 1: Traveling wave profiles
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for idx, (name, data) in enumerate(results.items()):
        ax = axes[idx]
        xi = data['xi']
        f_num = data['f_numerical']
        f_ana = data['f_analytical']
        
        ax.plot(xi, f_num, 'b-', linewidth=2, label='Numerical')
        if f_ana is not None:
            ax.plot(xi, f_ana, 'r--', linewidth=1.5, label='Analytical')
        
        ax.set_xlabel(r'$\xi$', fontsize=12)
        ax.set_ylabel(r'$f(\xi)$', fontsize=12)
        ax.set_title(f'{name}\n(m={data["m"]}, c={data["c"]})', fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.set_xlim([-5, 5])
        ax.set_ylim([0, 1.2])
    
    plt.tight_layout()
    plt.savefig('../report/images/figure1_traveling_wave_profiles.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure1_traveling_wave_profiles.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure1_traveling_wave_profiles.png")
    plt.close()
    
    # Figure 2: ODE Residuals
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for idx, (name, data) in enumerate(results.items()):
        ax = axes[idx]
        xi = data['xi']
        residual = data['residual_ode']
        
        ax.semilogy(xi, np.abs(residual) + 1e-16, 'g-', linewidth=1)
        ax.axhline(y=data['max_residual_ode'], color='r', linestyle='--', 
                   label=f'Max: {data["max_residual_ode"]:.2e}')
        
        ax.set_xlabel(r'$\xi$', fontsize=12)
        ax.set_ylabel(r'$|\mathrm{Residual}|$', fontsize=12)
        ax.set_title(f'ODE Residual: {name}', fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/figure2_ode_residuals.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure2_ode_residuals.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure2_ode_residuals.png")
    plt.close()
    
    # Figure 3: Algebraic Residuals (First Integral)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for idx, (name, data) in enumerate(results.items()):
        ax = axes[idx]
        xi = data['xi']
        residual = data['residual_algebraic']
        
        ax.semilogy(xi, np.abs(residual) + 1e-16, 'm-', linewidth=1)
        max_res = np.max(np.abs(residual))
        ax.axhline(y=max_res, color='r', linestyle='--', 
                   label=f'Max: {max_res:.2e}')
        
        ax.set_xlabel(r'$\xi$', fontsize=12)
        ax.set_ylabel(r'$|f^m f\' + c f|$', fontsize=12)
        ax.set_title(f'Algebraic Residual: {name}', fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/figure3_algebraic_residuals.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure3_algebraic_residuals.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure3_algebraic_residuals.png")
    plt.close()
    
    # Figure 4: Comparison with analytical solution (for m > 1)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    cases_with_analytical = [(name, data) for name, data in results.items() 
                             if data['f_analytical'] is not None]
    
    for idx, (name, data) in enumerate(cases_with_analytical):
        ax = axes[idx]
        xi = data['xi']
        f_num = data['f_numerical']
        f_ana = data['f_analytical']
        error = np.abs(f_num - f_ana)
        
        ax.semilogy(xi, error + 1e-16, 'k-', linewidth=1)
        if data['max_error'] is not None:
            ax.axhline(y=data['max_error'], color='r', linestyle='--',
                       label=f'Max error: {data["max_error"]:.2e}')
        
        ax.set_xlabel(r'$\xi$', fontsize=12)
        ax.set_ylabel(r'$|f_{num} - f_{ana}|$', fontsize=12)
        ax.set_title(f'Numerical Error: {name}', fontsize=11)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/figure4_numerical_error.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure4_numerical_error.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure4_numerical_error.png")
    plt.close()
    
    # Figure 5: Phase portrait (f vs f')
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for idx, (name, data) in enumerate(results.items()):
        ax = axes[idx]
        xi = data['xi']
        f = data['f_numerical']
        df = np.gradient(f, xi)
        
        ax.plot(f, df, 'b-', linewidth=1.5)
        ax.set_xlabel(r'$f$', fontsize=12)
        ax.set_ylabel(r"$f'$", fontsize=12)
        ax.set_title(f'Phase Portrait: {name}', fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([0, 1.1])
    
    plt.tight_layout()
    plt.savefig('../report/images/figure5_phase_portrait.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure5_phase_portrait.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure5_phase_portrait.png")
    plt.close()
    
    # Figure 6: Convergence study
    print("\n  Running convergence study...")
    convergence_study()


def convergence_study():
    """Study convergence with different tolerances."""
    m, c = 2.0, 1.0
    xi_start, xi_end = -5.0, 5.0
    f0 = 1.0
    
    tolerances = [(1e-4, 1e-6), (1e-6, 1e-8), (1e-8, 1e-10), (1e-10, 1e-12)]
    
    max_residuals = []
    mean_residuals = []
    nfevs = []
    
    for rtol, atol in tolerances:
        sol = solve_traveling_wave(m, c, f0, (xi_start, xi_end), rtol=rtol, atol=atol)
        xi_eval = np.linspace(xi_start, xi_end, 1000)
        residual, _, _ = compute_residual(sol, m, c, xi_eval)
        
        max_residuals.append(np.max(np.abs(residual)))
        mean_residuals.append(np.mean(np.abs(residual)))
        nfevs.append(sol.nfev)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    # Residual vs tolerance
    ax = axes[0]
    tol_labels = [f'{rtol:.0e}' for rtol, _ in tolerances]
    ax.semilogy(range(len(tolerances)), max_residuals, 'bo-', label='Max residual')
    ax.semilogy(range(len(tolerances)), mean_residuals, 'rs--', label='Mean residual')
    ax.set_xticks(range(len(tolerances)))
    ax.set_xticklabels(tol_labels)
    ax.set_xlabel('Relative Tolerance', fontsize=12)
    ax.set_ylabel('Residual', fontsize=12)
    ax.set_title('Convergence Study: Residual vs Tolerance', fontsize=11)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # Cost vs accuracy
    ax = axes[1]
    ax.loglog(max_residuals, nfevs, 'go-')
    ax.set_xlabel('Max Residual (Error)', fontsize=12)
    ax.set_ylabel('Function Evaluations', fontsize=12)
    ax.set_title('Computational Cost vs Accuracy', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/figure6_convergence_study.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure6_convergence_study.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure6_convergence_study.png")
    plt.close()


if __name__ == '__main__':
    results = main()
