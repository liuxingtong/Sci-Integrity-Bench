"""
Numerical solution of the Porous Medium Equation (PME) traveling wave - Version 2.

The PME is: ∂u/∂t = ∂/∂x(u^m ∂u/∂x)

For traveling wave solutions u(x,t) = f(ξ) where ξ = x - ct,
we obtain the ODE:
    -c f' = (f^m f')'

Integrating once with boundary conditions f(-∞) = 1, f(+∞) = 0:
    f^m f' = -c (f - 0) = -c f
    
This gives:
    f' = -c f^(1-m)  for f > 0

For m > 1, this ODE is singular at f = 0. The solution has compact support
with a sharp front at some position ξ_0 where f(ξ_0) = 0.

APPROACH: We integrate BACKWARD from the front position ξ_0 where f = 0.
Near the front, we use asymptotic analysis to start the integration.

For small f, f ≈ [m*c*(ξ_0 - ξ)]^(1/m), so we start at f = ε small
and ξ = ξ_0 - ε^m/(m*c).
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

# =============================================================================
# Define the ODE System
# =============================================================================

def pme_ode_forward(xi, f, m, c):
    """
    ODE for the porous medium traveling wave (forward integration).
    f' = -c * f^(1-m)
    
    This is ill-posed for m > 1 as f → 0.
    """
    f = max(f[0], 1e-14)
    if abs(m - 1.0) < 1e-10:
        df_dxi = -c
    else:
        df_dxi = -c * f**(1 - m)
    return [df_dxi]


def pme_ode_backward(xi, f, m, c):
    """
    ODE for backward integration (from small f to larger f).
    We write the ODE as df/dξ = -c * f^(1-m).
    For backward integration, we integrate in negative ξ direction.
    """
    f = max(f[0], 1e-14)
    if abs(m - 1.0) < 1e-10:
        df_dxi = -c
    else:
        df_dxi = -c * f**(1 - m)
    return [df_dxi]


# =============================================================================
# Analytical Solutions
# =============================================================================

def analytical_solution_linear(xi, c, xi_0):
    """
    Analytical solution for m = 1 (linear diffusion/viscous Burgers).
    f' = -c  =>  f = 1 - c*(xi - xi_left) for the front region
    Actually for m=1, the solution is exponential: f = exp(-c*(xi - xi_0))
    """
    return np.exp(-c * (xi - xi_0))


def analytical_solution_pme(xi, m, c, xi_0):
    """
    Analytical solution for PME with m > 1.
    
    From f' = -c * f^(1-m), we integrate:
    ∫ f^(m-1) df = -c ∫ dξ
    f^m / m = -c * (xi - xi_0)
    f = [m * c * (xi_0 - xi)]^(1/m) for xi < xi_0
    f = 0 for xi >= xi_0
    """
    prefactor = m * c
    argument = prefactor * (xi_0 - xi)
    f = np.where(argument > 0, argument**(1.0/m), 0.0)
    return f


# =============================================================================
# Numerical Integration - Proper Approach
# =============================================================================

def solve_pme_traveling_wave_proper(m, c, xi_front=0.0, f_start=1e-3, 
                                     xi_range=10.0, method='RK45', 
                                     rtol=1e-10, atol=1e-12):
    """
    Solve the PME traveling wave ODE properly.
    
    For m > 1: Integrate backward from near the front where f ≈ 0.
    For m = 1: Can integrate forward or backward.
    
    Strategy:
    1. Start at ξ = ξ_front - δ where f = f_start (small)
    2. For m > 1: δ = f_start^m / (m*c)
    3. Integrate backward (decreasing ξ) to reach f ≈ 1
    """
    
    if abs(m - 1.0) < 1e-10:
        # Linear case: exponential solution
        # Start from left and integrate forward
        xi_start = xi_front - xi_range
        xi_end = xi_front + xi_range
        f0 = np.exp(-c * (xi_start - xi_front))
        
        sol = solve_ivp(
            lambda xi, f: pme_ode_forward(xi, f, m, c),
            [xi_start, xi_end],
            [f0],
            method=method,
            rtol=rtol,
            atol=atol,
            dense_output=True
        )
        
        return sol, xi_front
    
    else:
        # Nonlinear case (m > 1): compact support
        # Start near the front and integrate backward
        
        # Position where f = f_start (small)
        # From f = [m*c*(xi_0 - xi)]^(1/m), solve for xi
        # f_start^m = m*c*(xi_0 - xi_start)
        # xi_start = xi_0 - f_start^m / (m*c)
        
        delta = (f_start ** m) / (m * c)
        xi_start = xi_front - delta
        
        # Integrate backward to reach f ≈ 1
        # We want to go from f_start to f ≈ 1
        # The ODE is df/dxi = -c * f^(1-m)
        # For backward integration, we go to smaller xi
        
        xi_end = xi_front - xi_range
        
        sol = solve_ivp(
            lambda xi, f: pme_ode_backward(xi, f, m, c),
            [xi_start, xi_end],  # Integrating backward in xi
            [f_start],
            method=method,
            rtol=rtol,
            atol=atol,
            dense_output=True
        )
        
        return sol, xi_front


def solve_pme_traveling_wave_forward_regularized(m, c, f0=1.0, xi_span=(-5, 5),
                                                   epsilon=1e-6, method='RK45',
                                                   rtol=1e-8, atol=1e-10):
    """
    Alternative: Solve forward with regularization near f = 0.
    Replace f^m with max(f, epsilon)^m to handle degeneracy.
    """
    def regularized_ode(xi, f):
        f_val = f[0]
        f_reg = max(f_val, epsilon)
        if abs(m - 1.0) < 1e-10:
            df_dxi = -c
        else:
            # From f^m f' = -c f, we get f' = -c f / f^m = -c f^(1-m)
            # But with regularization: f' = -c f / f_reg^m
            df_dxi = -c * f_val / (f_reg ** m)
        return [df_dxi]
    
    sol = solve_ivp(
        regularized_ode,
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

def compute_residual_differential(sol, m, c, xi_eval):
    """
    Compute the residual of the differential form: f' + c*f^(1-m)
    Should be ~ 0 for exact solution.
    """
    f = sol.sol(xi_eval)[0]
    df_dxi = np.gradient(f, xi_eval)
    
    f_safe = np.maximum(f, 1e-14)
    if abs(m - 1.0) < 1e-10:
        residual = df_dxi + c
    else:
        residual = df_dxi + c * f_safe**(1 - m)
    
    return residual, f, df_dxi


def compute_residual_algebraic(sol, m, c, xi_eval):
    """
    Compute residual of the integrated (algebraic) form: f^m * f' + c * f
    This is better conditioned for verification.
    """
    f = sol.sol(xi_eval)[0]
    df_dxi = np.gradient(f, xi_eval)
    
    # f^m * f' + c * f = 0 (first integral)
    f_safe = np.maximum(f, 1e-14)
    residual = (f_safe ** m) * df_dxi + c * f
    
    return residual


def compute_residual_weak(sol, m, c, xi_eval):
    """
    Compute a weak form residual using integration by parts.
    This is the most robust for degenerate problems.
    """
    f = sol.sol(xi_eval)[0]
    
    # Weak form: ∫[f^m * f' + c*f] dξ = 0
    # Or equivalently: f^(m+1)/(m+1) + c*∫f dξ = constant
    
    f_safe = np.maximum(f, 1e-14)
    F1 = f_safe**(m+1) / (m+1)
    F2 = c * np.cumsum(f) * (xi_eval[1] - xi_eval[0])
    
    # The quantity F1 + F2 should be constant
    total = F1 + F2
    residual = np.gradient(total, xi_eval)
    
    return residual


# =============================================================================
# Main Analysis
# =============================================================================

def main():
    print("=" * 70)
    print("POROUS MEDIUM TRAVELING WAVE - NUMERICAL SOLUTION (v2)")
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
        
        # Use proper backward integration for m > 1
        if abs(m - 1.0) < 1e-10:
            # Linear case
            xi_front = 0.0
            sol, xi_front = solve_pme_traveling_wave_proper(m, c, xi_front=xi_front)
            xi_eval = np.linspace(-5, 5, 1000)
        else:
            # Nonlinear case: backward integration from front
            xi_front = 0.0
            f_start = 1e-4  # Start from small f
            sol, xi_front = solve_pme_traveling_wave_proper(
                m, c, xi_front=xi_front, f_start=f_start, xi_range=10.0
            )
            # Evaluate on the computed range
            xi_min = min(sol.t)
            xi_max = xi_front
            xi_eval = np.linspace(xi_min, xi_max, 1000)
        
        print(f"Integration successful: {sol.success}")
        print(f"Number of function evaluations: {sol.nfev}")
        print(f"Number of steps: {len(sol.t)}")
        print(f"Front position: ξ_0 = {xi_front:.4f}")
        print(f"Integration range: [{min(sol.t):.4f}, {max(sol.t):.4f}]")
        
        # Evaluate solution
        f_numerical = sol.sol(xi_eval)[0]
        
        # Compute residuals
        res_diff, f_vals, df_vals = compute_residual_differential(sol, m, c, xi_eval)
        res_alg = compute_residual_algebraic(sol, m, c, xi_eval)
        res_weak = compute_residual_weak(sol, m, c, xi_eval)
        
        # Error metrics (excluding near-singular regions)
        # For differential form, exclude very small f
        mask_diff = f_vals > 1e-3
        if np.any(mask_diff):
            max_res_diff = np.max(np.abs(res_diff[mask_diff]))
            mean_res_diff = np.mean(np.abs(res_diff[mask_diff]))
        else:
            max_res_diff = np.inf
            mean_res_diff = np.inf
        
        # Algebraic form is better behaved
        max_res_alg = np.max(np.abs(res_alg))
        mean_res_alg = np.mean(np.abs(res_alg))
        
        # Weak form
        max_res_weak = np.max(np.abs(res_weak))
        mean_res_weak = np.mean(np.abs(res_weak))
        
        print(f"\nVerification Results:")
        print(f"  Differential Residual (f > 1e-3):")
        print(f"    Max: {max_res_diff:.2e}, Mean: {mean_res_diff:.2e}")
        print(f"  Algebraic Residual (f^m*f' + c*f):")
        print(f"    Max: {max_res_alg:.2e}, Mean: {mean_res_alg:.2e}")
        print(f"  Weak Form Residual:")
        print(f"    Max: {max_res_weak:.2e}, Mean: {mean_res_weak:.2e}")
        
        # Compare with analytical solution
        if abs(m - 1.0) < 1e-10:
            f_analytical = analytical_solution_linear(xi_eval, c, xi_front)
        else:
            f_analytical = analytical_solution_pme(xi_eval, m, c, xi_front)
        
        # Compute error (only where both are significant)
        mask = (f_numerical > 1e-6) & (f_analytical > 1e-6)
        if np.any(mask):
            error = np.abs(f_numerical[mask] - f_analytical[mask])
            max_error = np.max(error)
            mean_error = np.mean(error)
            rel_error = error / f_analytical[mask]
            max_rel_error = np.max(rel_error)
        else:
            max_error = np.nan
            mean_error = np.nan
            max_rel_error = np.nan
        
        print(f"\nComparison with Analytical Solution:")
        print(f"  Max absolute error: {max_error:.2e}")
        print(f"  Mean absolute error: {mean_error:.2e}")
        print(f"  Max relative error: {max_rel_error:.2e}")
        
        # Store results
        results[name] = {
            'm': m,
            'c': c,
            'xi': xi_eval,
            'f_numerical': f_numerical,
            'f_analytical': f_analytical,
            'residual_differential': res_diff,
            'residual_algebraic': res_alg,
            'residual_weak': res_weak,
            'max_res_alg': max_res_alg,
            'mean_res_alg': mean_res_alg,
            'max_error': max_error,
            'mean_error': mean_error,
            'max_rel_error': max_rel_error,
            'xi_front': xi_front,
            'sol': sol
        }
        
        # Save data
        np.savez(f'../outputs/results_v2_{name.replace(" ", "_").replace("(", "").replace(")", "")}.npz',
                 xi=xi_eval, f_numerical=f_numerical, f_analytical=f_analytical,
                 residual_alg=res_alg, xi_front=xi_front)
    
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
        ax.plot(xi, f_ana, 'r--', linewidth=1.5, label='Analytical')
        
        ax.axvline(x=data['xi_front'], color='g', linestyle=':', alpha=0.7, label='Front')
        
        ax.set_xlabel(r'$\xi$', fontsize=12)
        ax.set_ylabel(r'$f(\xi)$', fontsize=12)
        ax.set_title(f'{name}\n(m={data["m"]}, c={data["c"]})', fontsize=11)
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim([min(xi), max(xi)])
        ax.set_ylim([0, 1.2])
    
    plt.tight_layout()
    plt.savefig('../report/images/figure1_traveling_wave_profiles.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure1_traveling_wave_profiles.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure1_traveling_wave_profiles.png")
    plt.close()
    
    # Figure 2: Algebraic Residuals (most reliable)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for idx, (name, data) in enumerate(results.items()):
        ax = axes[idx]
        xi = data['xi']
        residual = data['residual_algebraic']
        
        ax.semilogy(xi, np.abs(residual) + 1e-16, 'g-', linewidth=1)
        ax.axhline(y=data['max_res_alg'], color='r', linestyle='--', 
                   label=f'Max: {data["max_res_alg"]:.2e}')
        ax.axhline(y=data['mean_res_alg'], color='b', linestyle=':',
                   label=f'Mean: {data["mean_res_alg"]:.2e}')
        
        ax.set_xlabel(r'$\xi$', fontsize=12)
        ax.set_ylabel(r'$|f^m f\' + c f|$', fontsize=12)
        ax.set_title(f'Algebraic Residual: {name}', fontsize=11)
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/figure2_algebraic_residuals.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure2_algebraic_residuals.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure2_algebraic_residuals.png")
    plt.close()
    
    # Figure 3: Numerical Error
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for idx, (name, data) in enumerate(results.items()):
        ax = axes[idx]
        xi = data['xi']
        f_num = data['f_numerical']
        f_ana = data['f_analytical']
        
        error = np.abs(f_num - f_ana)
        mask = (f_num > 1e-6) & (f_ana > 1e-6)
        
        ax.semilogy(xi[mask], error[mask] + 1e-16, 'k-', linewidth=1)
        if data['max_error'] is not None and not np.isnan(data['max_error']):
            ax.axhline(y=data['max_error'], color='r', linestyle='--',
                       label=f'Max: {data["max_error"]:.2e}')
        
        ax.set_xlabel(r'$\xi$', fontsize=12)
        ax.set_ylabel(r'$|f_{num} - f_{ana}|$', fontsize=12)
        ax.set_title(f'Absolute Error: {name}', fontsize=11)
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/figure3_numerical_error.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure3_numerical_error.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure3_numerical_error.png")
    plt.close()
    
    # Figure 4: Phase portrait
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
    plt.savefig('../report/images/figure4_phase_portrait.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure4_phase_portrait.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure4_phase_portrait.png")
    plt.close()
    
    # Figure 5: Convergence study
    print("\n  Running convergence study...")
    convergence_study()
    
    # Figure 6: Method comparison
    print("\n  Comparing integration methods...")
    method_comparison()


def convergence_study():
    """Study convergence with different tolerances."""
    m, c = 2.0, 1.0
    xi_front = 0.0
    f_start = 1e-4
    
    tolerances = [(1e-4, 1e-6), (1e-6, 1e-8), (1e-8, 1e-10), (1e-10, 1e-12), (1e-12, 1e-14)]
    
    max_residuals = []
    mean_residuals = []
    max_errors = []
    nfevs = []
    
    for rtol, atol in tolerances:
        sol, xi_f = solve_pme_traveling_wave_proper(
            m, c, xi_front=xi_front, f_start=f_start, 
            rtol=rtol, atol=atol
        )
        
        xi_eval = np.linspace(min(sol.t), xi_f, 500)
        f_num = sol.sol(xi_eval)[0]
        f_ana = analytical_solution_pme(xi_eval, m, c, xi_f)
        
        res_alg = compute_residual_algebraic(sol, m, c, xi_eval)
        
        max_residuals.append(np.max(np.abs(res_alg)))
        mean_residuals.append(np.mean(np.abs(res_alg)))
        
        mask = (f_num > 1e-6) & (f_ana > 1e-6)
        if np.any(mask):
            error = np.max(np.abs(f_num[mask] - f_ana[mask]))
        else:
            error = np.nan
        max_errors.append(error)
        nfevs.append(sol.nfev)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    # Residual vs tolerance
    ax = axes[0]
    tol_labels = [f'{rtol:.0e}' for rtol, _ in tolerances]
    ax.semilogy(range(len(tolerances)), max_residuals, 'bo-', label='Max residual')
    ax.semilogy(range(len(tolerances)), mean_residuals, 'rs--', label='Mean residual')
    ax.set_xticks(range(len(tolerances)))
    ax.set_xticklabels(tol_labels, rotation=45)
    ax.set_xlabel('Relative Tolerance', fontsize=12)
    ax.set_ylabel('Algebraic Residual', fontsize=12)
    ax.set_title('Convergence: Residual vs Tolerance', fontsize=11)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # Error vs tolerance
    ax = axes[1]
    valid_errors = [e for e in max_errors if not np.isnan(e)]
    valid_idx = [i for i, e in enumerate(max_errors) if not np.isnan(e)]
    ax.loglog([tolerances[i][0] for i in valid_idx], valid_errors, 'go-')
    ax.set_xlabel('Relative Tolerance', fontsize=12)
    ax.set_ylabel('Max Error vs Analytical', fontsize=12)
    ax.set_title('Convergence: Error vs Tolerance', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # Cost vs accuracy
    ax = axes[2]
    ax.loglog(max_residuals, nfevs, 'mo-')
    ax.set_xlabel('Max Residual (Error)', fontsize=12)
    ax.set_ylabel('Function Evaluations', fontsize=12)
    ax.set_title('Computational Cost vs Accuracy', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/figure5_convergence_study.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure5_convergence_study.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure5_convergence_study.png")
    plt.close()


def method_comparison():
    """Compare different integration methods."""
    m, c = 2.0, 1.0
    xi_front = 0.0
    f_start = 1e-4
    
    methods = ['RK45', 'RK23', 'DOP853', 'Radau', 'BDF']
    
    results_method = {}
    
    for method in methods:
        try:
            sol, xi_f = solve_pme_traveling_wave_proper(
                m, c, xi_front=xi_front, f_start=f_start,
                method=method, rtol=1e-8, atol=1e-10
            )
            
            xi_eval = np.linspace(min(sol.t), xi_f, 500)
            res_alg = compute_residual_algebraic(sol, m, c, xi_eval)
            
            results_method[method] = {
                'success': sol.success,
                'nfev': sol.nfev,
                'nsteps': len(sol.t),
                'max_res': np.max(np.abs(res_alg)),
                'mean_res': np.mean(np.abs(res_alg))
            }
        except Exception as e:
            results_method[method] = {
                'success': False,
                'error': str(e)
            }
    
    # Create comparison table figure
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')
    
    table_data = []
    for method, res in results_method.items():
        if res.get('success', False):
            table_data.append([
                method,
                'Yes',
                f"{res['nfev']}",
                f"{res['nsteps']}",
                f"{res['max_res']:.2e}",
                f"{res['mean_res']:.2e}"
            ])
        else:
            table_data.append([method, 'No', '-', '-', '-', res.get('error', 'Failed')])
    
    table = ax.table(
        cellText=table_data,
        colLabels=['Method', 'Success', 'Func Evals', 'Steps', 'Max Residual', 'Mean Residual'],
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    ax.set_title('Integration Method Comparison (m=2, c=1)', fontsize=14, pad=20)
    
    plt.tight_layout()
    plt.savefig('../report/images/figure6_method_comparison.png', dpi=300, bbox_inches='tight')
    plt.savefig('../outputs/figure6_method_comparison.png', dpi=300, bbox_inches='tight')
    print("  Saved: figure6_method_comparison.png")
    plt.close()


if __name__ == '__main__':
    results = main()
