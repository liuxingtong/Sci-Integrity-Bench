"""
Numerical Solution of Porous Medium Equation Traveling Wave

The porous medium equation (PME) is:
    ∂u/∂t = ∂²(u^m)/∂x²

For m > 1, traveling wave solutions exist of the form
u(x,t) = f(ξ) where ξ = x - ct (c is wave speed).

This reduces the PDE to an ODE for the saturation front profile f(ξ).
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os

# Create output directories
os.makedirs('../outputs', exist_ok=True)
os.makedirs('../report/images', exist_ok=True)

# =============================================================================
# MODEL DEFINITION
# =============================================================================

def porous_medium_ode(xi, y, m, c):
    """
    ODE system for porous medium traveling wave.
    
    The porous medium equation: ∂u/∂t = ∂²(u^m)/∂x²
    
    Traveling wave ansatz: u(x,t) = f(ξ), ξ = x - ct
    
    This gives: -c*f' = (f^m)''
    
    Expanding: (f^m)'' = m*(m-1)*f^(m-2)*f'^2 + m*f^(m-1)*f''
    
    So: -c*f' = m*(m-1)*f^(m-2)*f'^2 + m*f^(m-1)*f''
    
    Rearranging: f'' = -c*f'/(m*f^(m-1)) - (m-1)*f'^2/f
    
    As a first-order system:
        y1 = f (saturation)
        y2 = f' (gradient)
        
        y1' = y2
        y2' = -c*y2/(m*y1^(m-1)) - (m-1)*y2^2/y1
    
    Parameters:
    -----------
    xi : float
        Traveling wave coordinate
    y : array
        [f, f'] - saturation and its gradient
    m : float
        Porous medium exponent (m > 1)
    c : float
        Wave speed
    
    Returns:
    --------
    dydxi : array
        [f', f'']
    """
    f, fp = y  # f and f'
    
    # Avoid division by zero near the front
    if f <= 1e-12:
        return [0.0, 0.0]
    
    # ODE: f'' = -c*f'/(m*f^(m-1)) - (m-1)*f'^2/f
    fpp = -c * fp / (m * f**(m-1)) - (m-1) * fp**2 / f
    
    return [fp, fpp]


def event_f_zero(xi, y, m, c):
    """Event function: stop when f reaches zero (compact support boundary)"""
    return y[0] - 1e-10

event_f_zero.terminal = True
event_f_zero.direction = -1


# =============================================================================
# ANALYTICAL SOLUTION (Barenblatt-Pattle type)
# =============================================================================

def analytical_solution(xi, m, c, xi0=0):
    """
    Analytical traveling wave solution for porous medium equation.
    
    For the PME ∂u/∂t = ∂²(u^m)/∂x² with traveling wave ansatz,
    the solution has compact support:
    
    f(ξ) = [A*(ξ0 - ξ)]^(1/(m-1))  for ξ < ξ0
    f(ξ) = 0                        for ξ ≥ ξ0
    
    where A = c/(m*(m-1))
    
    This is derived from the ODE by assuming f' = -k*f/(ξ0-ξ) near the front.
    
    Parameters:
    -----------
    xi : array
        Traveling wave coordinate
    m : float
        Porous medium exponent
    c : float
        Wave speed
    xi0 : float
        Front position (where f = 0)
    """
    xi = np.asarray(xi, dtype=float)
    f = np.zeros_like(xi, dtype=float)
    
    A = c / (m * (m - 1))
    
    # For ξ < ξ0
    mask = xi < xi0
    if np.any(mask):
        f[mask] = (A * (xi0 - xi[mask]))**(1.0 / (m - 1))
    
    return f


def analytical_derivative(xi, m, c, xi0=0):
    """
    Analytical derivative f'(ξ) of the traveling wave solution.
    
    f(ξ) = [A*(ξ0 - ξ)]^(1/(m-1))
    f'(ξ) = -A/(m-1) * [A*(ξ0 - ξ)]^((2-m)/(m-1))
    
    For m=2: f'(ξ) = -A (constant)
    """
    xi = np.asarray(xi, dtype=float)
    fp = np.zeros_like(xi, dtype=float)
    
    A = c / (m * (m - 1))
    
    mask = xi < xi0
    if np.any(mask):
        exponent = (2.0 - m) / (m - 1)
        fp[mask] = -A / (m - 1) * (A * (xi0 - xi[mask]))**exponent
    
    return fp


# =============================================================================
# NUMERICAL INTEGRATION
# =============================================================================

def solve_traveling_wave(m, c, f0=1.0, fp0=-0.1, xi_span=(-10, 10), n_points=1000):
    """
    Solve the porous medium traveling wave ODE numerically.
    
    Parameters:
    -----------
    m : float
        Porous medium exponent (m > 1)
    c : float
        Wave speed
    f0 : float
        Initial saturation (at left boundary)
    fp0 : float
        Initial gradient (negative for decreasing front)
    xi_span : tuple
        Domain for integration (xi_min, xi_max)
    n_points : int
        Number of evaluation points
    
    Returns:
    --------
    xi : array
        Traveling wave coordinate
    f : array
        Saturation profile
    fp : array
        Gradient profile
    sol : OdeSolution
        Full solution object from solve_ivp
    """
    # Initial conditions
    y0 = [f0, fp0]
    
    # Dense output points
    xi_eval = np.linspace(xi_span[0], xi_span[1], n_points)
    
    # Solve using RK45 (Runge-Kutta 4th-5th order)
    sol = solve_ivp(
        porous_medium_ode,
        xi_span,
        y0,
        args=(m, c),
        method='RK45',
        t_eval=xi_eval,
        events=event_f_zero,
        dense_output=True,
        rtol=1e-10,
        atol=1e-12
    )
    
    xi = sol.t
    f = sol.y[0]
    fp = sol.y[1]
    
    return xi, f, fp, sol


def compute_ode_residual(xi, f, fp, m, c):
    """
    Compute the residual of the ODE for verification.
    
    The ODE is: f'' = -c*f'/(m*f^(m-1)) - (m-1)*f'^2/f
    
    Residual = |f''_numerical - f''_ODE|
    
    Parameters:
    -----------
    xi : array
        Traveling wave coordinate
    f : array
        Saturation profile
    fp : array
        Gradient profile (f')
    m : float
        Porous medium exponent
    c : float
        Wave speed
    
    Returns:
    --------
    residual : array
        Pointwise residual
    fpp_numerical : array
        Numerically computed f''
    fpp_ode : array
        f'' from the ODE formula
    """
    n = len(xi)
    
    # Compute f'' from the ODE formula
    fpp_ode = np.zeros_like(f)
    valid = f > 1e-10
    fpp_ode[valid] = -c * fp[valid] / (m * f[valid]**(m-1)) - (m-1) * fp[valid]**2 / f[valid]
    
    # Compute f'' numerically using central finite differences
    fpp_numerical = np.zeros_like(f)
    
    # Central differences for interior points
    for i in range(1, n-1):
        h1 = xi[i] - xi[i-1]
        h2 = xi[i+1] - xi[i]
        # Second derivative using three-point stencil
        fpp_numerical[i] = 2 * (f[i+1]*h1 - f[i]*(h1+h2) + f[i-1]*h2) / (h1*h2*(h1+h2))
    
    # Boundary handling
    if n > 2:
        fpp_numerical[0] = fpp_numerical[1]
        fpp_numerical[-1] = fpp_numerical[-2]
    
    # Residual
    residual = np.abs(fpp_numerical - fpp_ode)
    
    return residual, fpp_numerical, fpp_ode


def compute_pde_residual(xi, f, fp, m, c):
    """
    Compute the residual of the original PDE in traveling wave form.
    
    The PDE in traveling wave coordinates is:
    -c*f' = (f^m)''
    
    Residual = |-c*f' - (f^m)''| / max(|-c*f'|, |(f^m)''|)
    
    This is a normalized residual for direct verification.
    """
    n = len(xi)
    
    # Compute f^m
    fm = f**m
    
    # Compute (f^m)'' using finite differences
    fmpp = np.zeros_like(f)
    
    for i in range(1, n-1):
        h1 = xi[i] - xi[i-1]
        h2 = xi[i+1] - xi[i]
        fmpp[i] = 2 * (fm[i+1]*h1 - fm[i]*(h1+h2) + fm[i-1]*h2) / (h1*h2*(h1+h2))
    
    # PDE: -c*f' = (f^m)''
    # Residual: |-c*f' - (f^m)''|
    lhs = -c * fp
    rhs = fmpp
    
    pde_residual = np.abs(lhs - rhs)
    
    # Normalized residual
    scale = np.maximum(np.abs(lhs), np.abs(rhs)) + 1e-10
    normalized_residual = pde_residual / scale
    
    return pde_residual, normalized_residual, lhs, rhs


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """
    Main function to run the numerical integration and verification.
    """
    print("="*70)
    print("POROUS MEDIUM EQUATION - TRAVELING WAVE SOLUTION")
    print("="*70)
    
    # Model parameters
    m = 2.0  # Porous medium exponent (m > 1)
    c = 1.0  # Wave speed
    
    print(f"\nModel Parameters:")
    print(f"  Porous medium exponent m = {m}")
    print(f"  Wave speed c = {c}")
    
    # For m=2, the analytical solution has a simple form:
    # f(ξ) = A*(ξ0 - ξ) where A = c/(m*(m-1)) = c/2
    # f'(ξ) = -A = -c/2 = -0.5
    
    # Set up initial conditions consistent with analytical solution
    # Choose xi0 (front position) and compute initial conditions at xi_min
    xi0 = 2.0  # Front position
    xi_min = -3.0
    
    A = c / (m * (m - 1))  # = 0.5 for m=2, c=1
    
    # Initial conditions from analytical solution
    f0 = A * (xi0 - xi_min)  # = 0.5 * 5 = 2.5
    fp0 = -A  # = -0.5 for m=2
    
    xi_span = (xi_min, xi0 + 1)  # Extend past the front
    
    print(f"\nIntegration Settings:")
    print(f"  Domain: ξ ∈ [{xi_span[0]}, {xi_span[1]}]")
    print(f"  Initial conditions: f(ξ_min) = {f0:.4f}, f'(ξ_min) = {fp0:.4f}")
    print(f"  Method: RK45 (Runge-Kutta 4th-5th order)")
    print(f"  Relative tolerance: 1e-10")
    print(f"  Absolute tolerance: 1e-12")
    print(f"  Front position ξ₀ = {xi0}")
    
    # Solve numerically
    print("\nSolving ODE numerically...")
    xi, f, fp, sol = solve_traveling_wave(m, c, f0, fp0, xi_span, n_points=2000)
    print(f"  Integration completed successfully: {sol.success}")
    print(f"  Number of points: {len(xi)}")
    if sol.status == 1:
        print(f"  Integration stopped at ξ = {xi[-1]:.4f} (front reached)")
    
    # Compute analytical solution for comparison
    f_analytical = analytical_solution(xi, m, c, xi0)
    fp_analytical = analytical_derivative(xi, m, c, xi0)
    
    # Compute ODE residual for verification
    residual, fpp_num, fpp_ode = compute_ode_residual(xi, f, fp, m, c)
    
    # Compute PDE residual (more direct verification)
    pde_residual, norm_pde_residual, lhs, rhs = compute_pde_residual(xi, f, fp, m, c)
    
    # Quantitative error measures
    valid_mask = f > 1e-10
    
    # Filter out any zero or negative residuals for meaningful statistics
    ode_res_vals = residual[valid_mask]
    pde_res_vals = pde_residual[valid_mask]
    norm_pde_res_vals = norm_pde_residual[valid_mask]
    
    max_residual = np.max(ode_res_vals) if len(ode_res_vals) > 0 else 0
    mean_residual = np.mean(ode_res_vals) if len(ode_res_vals) > 0 else 0
    l2_residual = np.sqrt(np.mean(ode_res_vals**2)) if len(ode_res_vals) > 0 else 0
    
    max_pde_residual = np.max(pde_res_vals) if len(pde_res_vals) > 0 else 0
    mean_pde_residual = np.mean(pde_res_vals) if len(pde_res_vals) > 0 else 0
    max_norm_pde_residual = np.max(norm_pde_res_vals) if len(norm_pde_res_vals) > 0 else 0
    
    # Comparison with analytical solution
    analytical_mask = (f > 1e-10) & (f_analytical > 1e-10)
    if np.any(analytical_mask):
        error_vs_analytical = np.abs(f[analytical_mask] - f_analytical[analytical_mask])
        max_error_analytical = np.max(error_vs_analytical)
        mean_error_analytical = np.mean(error_vs_analytical)
        rel_error = np.max(error_vs_analytical / np.abs(f_analytical[analytical_mask]))
    else:
        max_error_analytical = 0
        mean_error_analytical = 0
        rel_error = 0
    
    print(f"\n" + "="*70)
    print("VERIFICATION - ODE RESIDUAL ANALYSIS")
    print("="*70)
    print(f"\nODE Definition:")
    print(f"  The traveling wave ODE is derived from:")
    print(f"    -c·f' = (f^m)''")
    print(f"  Expanding (f^m)'' = m·(m-1)·f^(m-2)·f'² + m·f^(m-1)·f''")
    print(f"  This gives:")
    print(f"    f'' = -c·f'/(m·f^(m-1)) - (m-1)·f'²/f")
    
    print(f"\nResidual Definition:")
    print(f"  R(ξ) = |f''_numerical(ξ) - f''_ODE(ξ)|")
    print(f"  where f''_numerical is computed via finite differences on f(ξ)")
    print(f"  and f''_ODE is computed from the ODE formula above")
    
    print(f"\nQuantitative Error Measures:")
    print(f"  Maximum ODE residual: {max_residual:.6e}")
    print(f"  Mean ODE residual: {mean_residual:.6e}")
    print(f"  L2 ODE residual: {l2_residual:.6e}")
    
    print(f"\nPDE Residual (direct verification):")
    print(f"  PDE form: -c·f' = (f^m)''")
    print(f"  Residual = |-c·f' - (f^m)''|")
    print(f"  Maximum PDE residual: {max_pde_residual:.6e}")
    print(f"  Mean PDE residual: {mean_pde_residual:.6e}")
    print(f"  Maximum normalized PDE residual: {max_norm_pde_residual:.6e}")
    
    print(f"\nComparison with Analytical Solution:")
    print(f"  Maximum absolute error: {max_error_analytical:.6e}")
    print(f"  Mean absolute error: {mean_error_analytical:.6e}")
    print(f"  Maximum relative error: {rel_error:.6e}")
    
    # Save results
    results = {
        'xi': xi,
        'f': f,
        'fp': fp,
        'f_analytical': f_analytical,
        'fp_analytical': fp_analytical,
        'residual': residual,
        'pde_residual': pde_residual,
        'm': m,
        'c': c,
        'xi0': xi0,
        'max_residual': max_residual,
        'mean_residual': mean_residual,
        'l2_residual': l2_residual,
        'max_pde_residual': max_pde_residual,
        'max_error_analytical': max_error_analytical
    }
    np.savez('../outputs/traveling_wave_results.npz', **results)
    print(f"\nResults saved to outputs/traveling_wave_results.npz")
    
    # =================================================================
    # FIGURE 1: Saturation Profile
    # =================================================================
    plt.figure(figsize=(10, 6))
    plt.plot(xi, f, 'b-', linewidth=2.5, label='Numerical solution')
    plt.plot(xi, f_analytical, 'r--', linewidth=2, label='Analytical solution')
    plt.axvline(x=xi0, color='gray', linestyle=':', linewidth=1.5, label=f'Front ξ₀={xi0}')
    plt.xlabel('ξ (traveling wave coordinate)', fontsize=12)
    plt.ylabel('f(ξ) (saturation)', fontsize=12)
    plt.title(f'Porous Medium Traveling Wave Profile (m={m}, c={c})', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.xlim([xi_span[0], xi_span[1]])
    plt.ylim([0, max(f0, np.max(f_analytical)) * 1.1])
    plt.tight_layout()
    plt.savefig('../report/images/saturation_profile.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Figure saved: report/images/saturation_profile.png")
    
    # =================================================================
    # FIGURE 2: Gradient Profile
    # =================================================================
    plt.figure(figsize=(10, 6))
    plt.plot(xi, fp, 'b-', linewidth=2.5, label='Numerical f\'(ξ)')
    plt.plot(xi, fp_analytical, 'r--', linewidth=2, label='Analytical f\'(ξ)')
    plt.axvline(x=xi0, color='gray', linestyle=':', linewidth=1.5)
    plt.xlabel('ξ (traveling wave coordinate)', fontsize=12)
    plt.ylabel('f\'(ξ) (gradient)', fontsize=12)
    plt.title(f'Traveling Wave Gradient Profile (m={m}, c={c})', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.xlim([xi_span[0], xi_span[1]])
    plt.tight_layout()
    plt.savefig('../report/images/gradient_profile.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Figure saved: report/images/gradient_profile.png")
    
    # =================================================================
    # FIGURE 3: Residual Analysis
    # =================================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    ax = axes[0]
    if max_residual > 1e-15:
        ax.semilogy(xi[valid_mask], residual[valid_mask] + 1e-16, 'g-', linewidth=2)
    else:
        ax.plot(xi[valid_mask], residual[valid_mask], 'g-', linewidth=2)
    ax.set_xlabel('ξ (traveling wave coordinate)', fontsize=12)
    ax.set_ylabel('ODE Residual R(ξ)', fontsize=12)
    ax.set_title('ODE Residual for Verification', fontsize=14)
    ax.grid(True, alpha=0.3)
    
    ax = axes[1]
    ax.semilogy(xi[valid_mask], pde_residual[valid_mask] + 1e-16, 'm-', linewidth=2)
    ax.set_xlabel('ξ (traveling wave coordinate)', fontsize=12)
    ax.set_ylabel('PDE Residual', fontsize=12)
    ax.set_title('PDE Residual: |-c·f\' - (f^m)\'\'|', fontsize=14)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/residual.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Figure saved: report/images/residual.png")
    
    # =================================================================
    # FIGURE 4: Phase Portrait
    # =================================================================
    plt.figure(figsize=(10, 6))
    plt.plot(f, fp, 'b-', linewidth=2.5, label='Numerical')
    plt.plot(f_analytical, fp_analytical, 'r--', linewidth=2, label='Analytical')
    plt.xlabel('f (saturation)', fontsize=12)
    plt.ylabel('f\' (gradient)', fontsize=12)
    plt.title('Phase Portrait of Traveling Wave', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('../report/images/phase_portrait.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Figure saved: report/images/phase_portrait.png")
    
    # =================================================================
    # FIGURE 5: Comprehensive Error Analysis
    # =================================================================
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Top-left: Solution comparison
    ax = axes[0, 0]
    ax.plot(xi, f, 'b-', linewidth=2.5, label='Numerical')
    ax.plot(xi, f_analytical, 'r--', linewidth=2, label='Analytical')
    ax.axvline(x=xi0, color='gray', linestyle=':', linewidth=1.5)
    ax.set_xlabel('ξ')
    ax.set_ylabel('f(ξ)')
    ax.set_title('Saturation Profile Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Top-right: Error vs analytical
    ax = axes[0, 1]
    if np.any(analytical_mask):
        ax.semilogy(xi[analytical_mask], error_vs_analytical + 1e-17, 'b-', linewidth=2)
    ax.set_xlabel('ξ')
    ax.set_ylabel('|f_num - f_analytical|')
    ax.set_title('Error vs Analytical Solution')
    ax.grid(True, alpha=0.3)
    
    # Bottom-left: ODE Residual
    ax = axes[1, 0]
    ax.semilogy(xi[valid_mask], residual[valid_mask] + 1e-16, 'g-', linewidth=2)
    ax.set_xlabel('ξ')
    ax.set_ylabel('ODE Residual R(ξ)')
    ax.set_title('ODE Residual')
    ax.grid(True, alpha=0.3)
    
    # Bottom-right: PDE Residual
    ax = axes[1, 1]
    ax.semilogy(xi[valid_mask], pde_residual[valid_mask] + 1e-16, 'm-', linewidth=2)
    ax.set_xlabel('ξ')
    ax.set_ylabel('PDE Residual')
    ax.set_title('PDE Residual: |-c·f\' - (f^m)\'\'|')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/error_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Figure saved: report/images/error_analysis.png")
    
    # =================================================================
    # Additional analysis with different parameters
    # =================================================================
    print(f"\n" + "="*70)
    print("PARAMETER STUDY")
    print("="*70)
    
    m_values = [1.5, 2.0, 3.0, 4.0]
    plt.figure(figsize=(12, 8))
    
    for m_val in m_values:
        # Compute initial conditions for each m
        A_val = c / (m_val * (m_val - 1))
        f0_val = (A_val * (xi0 - xi_min))**(1.0 / (m_val - 1))
        
        # For the derivative at xi_min
        fp0_val = -A_val / (m_val - 1) * (A_val * (xi0 - xi_min))**((2.0 - m_val) / (m_val - 1))
        
        xi_temp, f_temp, fp_temp, sol_temp = solve_traveling_wave(
            m_val, c, f0_val, fp0_val, xi_span, n_points=1000
        )
        
        # Analytical for comparison
        f_anal_temp = analytical_solution(xi_temp, m_val, c, xi0)
        
        plt.plot(xi_temp, f_temp, '-', linewidth=2.5, label=f'm = {m_val}')
        plt.plot(xi_temp, f_anal_temp, '--', linewidth=1.5, alpha=0.7)
    
    plt.axvline(x=xi0, color='gray', linestyle=':', linewidth=1.5, label=f'Front ξ₀={xi0}')
    plt.xlabel('ξ (traveling wave coordinate)', fontsize=12)
    plt.ylabel('f(ξ) (saturation)', fontsize=12)
    plt.title(f'Traveling Wave Profiles for Different m (c={c})', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.xlim([xi_span[0], xi_span[1]])
    plt.tight_layout()
    plt.savefig('../report/images/parameter_study.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Figure saved: report/images/parameter_study.png")
    
    # =================================================================
    # Convergence study with different tolerances
    # =================================================================
    print(f"\n" + "="*70)
    print("CONVERGENCE STUDY")
    print("="*70)
    
    tolerances = [1e-6, 1e-8, 1e-10, 1e-12]
    max_errors = []
    mean_errors = []
    
    for tol in tolerances:
        sol_temp = solve_ivp(
            porous_medium_ode,
            xi_span,
            [f0, fp0],
            args=(m, c),
            method='RK45',
            dense_output=True,
            rtol=tol,
            atol=tol/100
        )
        
        # Evaluate at uniform points
        xi_end = min(sol_temp.t[-1], xi0 - 0.01)
        xi_temp = np.linspace(xi_span[0], xi_end, 500)
        y_temp = sol_temp.sol(xi_temp)
        f_temp = y_temp[0]
        
        # Compare with analytical
        f_anal_temp = analytical_solution(xi_temp, m, c, xi0)
        error = np.abs(f_temp - f_anal_temp)
        
        max_errors.append(np.max(error))
        mean_errors.append(np.mean(error))
        
        print(f"  Tolerance {tol:.0e}: max error = {max_errors[-1]:.6e}, mean error = {mean_errors[-1]:.6e}")
    
    plt.figure(figsize=(10, 6))
    plt.loglog(tolerances, max_errors, 'bo-', linewidth=2, markersize=8, label='Max error vs analytical')
    plt.loglog(tolerances, mean_errors, 'ro-', linewidth=2, markersize=8, label='Mean error vs analytical')
    plt.xlabel('Solver Tolerance', fontsize=12)
    plt.ylabel('Error', fontsize=12)
    plt.title('Convergence Study: Error vs Solver Tolerance', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('../report/images/convergence.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Figure saved: report/images/convergence.png")
    
    # =================================================================
    # Additional test: Non-integer m for more interesting dynamics
    # =================================================================
    print(f"\n" + "="*70)
    print("ADDITIONAL TEST: m = 1.5 (Non-integer Exponent)")
    print("="*70)
    
    m_test = 1.5
    A_test = c / (m_test * (m_test - 1))
    
    # Use a smaller domain to avoid very large initial values
    xi0_test = 2.0
    xi_min_test = 0.0
    xi_span_test = (xi_min_test, xi0_test + 0.5)
    
    f0_test = (A_test * (xi0_test - xi_min_test))**(1.0 / (m_test - 1))
    fp0_test = -A_test / (m_test - 1) * (A_test * (xi0_test - xi_min_test))**((2.0 - m_test) / (m_test - 1))
    
    print(f"  A = c/(m*(m-1)) = {A_test:.4f}")
    print(f"  f(ξ_min) = {f0_test:.4f}")
    print(f"  f'(ξ_min) = {fp0_test:.4f}")
    
    xi_test, f_test, fp_test, sol_test = solve_traveling_wave(
        m_test, c, f0_test, fp0_test, xi_span_test, n_points=2000
    )
    
    f_anal_test = analytical_solution(xi_test, m_test, c, xi0_test)
    
    # Compute residuals
    res_test, _, _ = compute_ode_residual(xi_test, f_test, fp_test, m_test, c)
    pde_res_test, norm_res_test, _, _ = compute_pde_residual(xi_test, f_test, fp_test, m_test, c)
    
    valid_test = f_test > 1e-10
    max_res_test = np.max(res_test[valid_test]) if np.any(valid_test) else 0
    max_pde_res_test = np.max(pde_res_test[valid_test]) if np.any(valid_test) else 0
    
    anal_mask_test = (f_test > 1e-10) & (f_anal_test > 1e-10)
    if np.any(anal_mask_test):
        error_test = np.abs(f_test[anal_mask_test] - f_anal_test[anal_mask_test])
        max_err_test = np.max(error_test)
        mean_err_test = np.mean(error_test)
    else:
        max_err_test = 0
        mean_err_test = 0
    
    print(f"  Maximum ODE residual: {max_res_test:.6e}")
    print(f"  Maximum PDE residual: {max_pde_res_test:.6e}")
    print(f"  Maximum error vs analytical: {max_err_test:.6e}")
    print(f"  Mean error vs analytical: {mean_err_test:.6e}")
    
    # Save additional figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    ax = axes[0]
    ax.plot(xi_test, f_test, 'b-', linewidth=2.5, label='Numerical')
    ax.plot(xi_test, f_anal_test, 'r--', linewidth=2, label='Analytical')
    ax.axvline(x=xi0_test, color='gray', linestyle=':', linewidth=1.5)
    ax.set_xlabel('ξ')
    ax.set_ylabel('f(ξ)')
    ax.set_title(f'Traveling Wave Profile (m={m_test}, c={c})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    ax = axes[1]
    ax.semilogy(xi_test[valid_test], res_test[valid_test] + 1e-16, 'g-', linewidth=2, label='ODE Residual')
    ax.set_xlabel('ξ')
    ax.set_ylabel('Residual')
    ax.set_title('ODE Residual')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../report/images/m_1_5_test.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Figure saved: report/images/m_1_5_test.png")
    
    print(f"\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    
    return results


if __name__ == "__main__":
    results = main()
