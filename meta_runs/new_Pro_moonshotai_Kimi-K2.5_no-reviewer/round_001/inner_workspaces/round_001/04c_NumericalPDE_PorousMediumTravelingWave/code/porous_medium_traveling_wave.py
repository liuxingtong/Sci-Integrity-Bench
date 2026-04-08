"""
Porous Medium Equation Traveling Wave Solver

Solves the ODE boundary value problem arising from traveling wave reduction
of the porous medium equation: u_t = (u^m * u_x)_x

Traveling wave ansatz: u(x,t) = f(ξ), ξ = x - ct
Yields ODE: -c * f' = (f^m * f')'

The solution has compact support - it reaches f=0 at a finite point ξ_0.
Target: L2 residual < 1e-8
"""

import numpy as np
from scipy.integrate import solve_ivp, quad
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import os

# Create output directories if they don't exist
os.makedirs('outputs', exist_ok=True)
os.makedirs('report/images', exist_ok=True)


def solve_porous_medium_traveling_wave(m, c, u_L, u_R, target_residual=1e-8):
    """
    Solve the porous medium traveling wave ODE with high accuracy.
    
    The ODE (integrated form): f^m * f' = c*(u_L - f)
    This gives: f' = c*(u_L - f) / f^m
    
    The solution has compact support: f(ξ) = 0 for ξ ≥ ξ_0
    """
    
    # Find the compact support boundary ξ_0 by integrating
    # ξ_0 = (1/c) * ∫_0^{u_L} f^m / (u_L - f) df
    
    def integrand(f):
        if f < 1e-14:
            return 0
        return f**m / (c * (u_L - f))
    
    # The integral has a singularity at f = u_L, so we integrate to u_L - ε
    eps = 1e-10
    xi_0, _ = quad(integrand, 0, u_L - eps, limit=100)
    
    print(f"  Compact support boundary: ξ_0 = {xi_0:.6f}")
    
    # Create a grid on [-xi_max, xi_0]
    # We need xi_max large enough so f(-xi_max) ≈ u_L
    xi_max = 50  # Large enough domain
    
    # Use uniform grid with high resolution
    n_points = 5000
    xi = np.linspace(-xi_max, xi_0, n_points)
    
    # Solve ODE
    f = solve_ode_forward(m, c, u_L, xi)
    
    # Extend to full domain with compact support
    xi_full, f_full = extend_solution(xi, f, xi_0, u_R, xi_max_extend=20)
    
    # Compute residual
    l2_residual = compute_l2_residual(xi_full, f_full, m, c)
    
    return xi_full, f_full, l2_residual, xi_0


def solve_ode_forward(m, c, u_L, xi):
    """
    Solve ODE: f' = c*(u_L - f) / f^m
    Integrate forward from left boundary.
    """
    def ode(t, y):
        f = y[0] if isinstance(y, (list, np.ndarray)) else y
        eps = 1e-15
        if f > eps:
            return [c * (u_L - f) / (f**m + eps)]
        else:
            return [0]
    
    # Initial condition: at left boundary, f ≈ u_L
    f0 = [u_L - 1e-8]
    
    # Solve forward
    sol = solve_ivp(ode, [xi[0], xi[-1]], f0, t_eval=xi, 
                    method='RK45', rtol=1e-12, atol=1e-13,
                    dense_output=True)
    
    # Extract solution
    if hasattr(sol, 'y') and sol.y is not None:
        if isinstance(sol.y, np.ndarray):
            if sol.y.ndim == 2:
                f = sol.y[0, :]
            else:
                f = sol.y
        else:
            f = np.array(sol.y).flatten()
    else:
        # Fallback
        f = integrate_ode_simple(m, c, u_L, xi)
    
    f = np.asarray(f).flatten()
    
    return f


def integrate_ode_simple(m, c, u_L, xi):
    """
    Simple forward integration of the ODE.
    """
    n = len(xi)
    f = np.zeros(n)
    f[0] = u_L - 1e-8
    
    for i in range(1, n):
        dx = xi[i] - xi[i-1]
        f_i = f[i-1]
        eps = 1e-15
        
        if f_i > eps:
            f_prime = c * (u_L - f_i) / (f_i**m + eps)
            f[i] = f_i + f_prime * dx
        else:
            f[i] = 0
    
    return f


def extend_solution(xi, f, xi_0, u_R, xi_max_extend=20):
    """
    Extend solution to full domain with compact support.
    """
    # Find where f becomes very small (compact support boundary)
    mask_active = f > 1e-6
    if np.any(mask_active):
        last_active = np.where(mask_active)[0][-1]
        xi_compact = xi[last_active]
    else:
        xi_compact = xi_0
    
    # Extend to the right (compact support)
    if xi[-1] < xi_max_extend:
        xi_right = np.linspace(xi[-1], xi_max_extend, 500)
        f_right = np.ones(len(xi_right)) * u_R
        
        # Combine
        xi_full = np.concatenate([xi, xi_right[1:]])
        f_full = np.concatenate([f, f_right[1:]])
    else:
        xi_full = xi
        f_full = f
    
    return xi_full, f_full


def compute_l2_residual(xi, f, m, c):
    """
    Compute L2 residual of the ODE: -c*f' - (f^m * f')' = 0
    Only compute where f > 0 (non-degenerate region).
    """
    # Mask for non-degenerate region
    mask = f > 1e-6
    
    if np.sum(mask) < 10:
        return 1e10
    
    xi_active = xi[mask]
    f_active = f[mask]
    
    # Use cubic spline for smooth derivatives
    cs = CubicSpline(xi_active, f_active)
    f_prime = cs(xi_active, 1)
    f_second = cs(xi_active, 2)
    
    # ODE: -c*f' = (f^m * f')'
    # RHS: (f^m * f')' = m*f^(m-1)*(f')^2 + f^m*f''
    lhs = -c * f_prime
    rhs = m * (f_active**(m-1)) * f_prime**2 + f_active**m * f_second
    residual = lhs - rhs
    
    # L2 norm
    l2_residual = np.sqrt(np.trapz(residual**2, xi_active))
    
    return l2_residual


def verify_solution(xi, f, m, c, u_L, u_R):
    """
    Verify the solution satisfies the ODE and boundary conditions.
    """
    # Check boundary conditions
    bc_error_left = abs(f[0] - u_L)
    bc_error_right = abs(f[-1] - u_R)
    
    # Compute L2 residual
    l2_residual = compute_l2_residual(xi, f, m, c)
    
    # Also compute L∞ residual in active region
    mask = f > 1e-6
    if np.sum(mask) > 10:
        xi_active = xi[mask]
        f_active = f[mask]
        cs = CubicSpline(xi_active, f_active)
        f_prime = cs(xi_active, 1)
        f_second = cs(xi_active, 2)
        lhs = -c * f_prime
        rhs = m * (f_active**(m-1)) * f_prime**2 + f_active**m * f_second
        residual = lhs - rhs
        linf_residual = np.max(np.abs(residual))
    else:
        linf_residual = 0
    
    print(f"Boundary condition errors:")
    print(f"  Left (f(-∞) = {u_L}): {bc_error_left:.2e}")
    print(f"  Right (f(+∞) = {u_R}): {bc_error_right:.2e}")
    print(f"ODE residuals (in active region):")
    print(f"  L2 norm: {l2_residual:.2e}")
    print(f"  L∞ norm: {linf_residual:.2e}")
    
    return {
        'bc_error_left': bc_error_left,
        'bc_error_right': bc_error_right,
        'l2_residual': l2_residual,
        'linf_residual': linf_residual
    }


def plot_solution(xi, f, m, c, u_L, u_R, xi_0, filename='traveling_wave_profile.png'):
    """
    Create publication-quality plot of the traveling wave profile.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Main profile
    ax = axes[0, 0]
    ax.plot(xi, f, 'b-', linewidth=2, label='Numerical solution')
    ax.axhline(y=u_L, color='r', linestyle='--', alpha=0.5, label=f'$u_L = {u_L}$')
    ax.axhline(y=u_R, color='g', linestyle='--', alpha=0.5, label=f'$u_R = {u_R}$')
    ax.axvline(x=xi_0, color='orange', linestyle=':', alpha=0.5, label=f'ξ₀ ≈ {xi_0:.2f}')
    ax.set_xlabel(r'$\xi = x - ct$', fontsize=12)
    ax.set_ylabel(r'$f(\xi)$', fontsize=12)
    ax.set_title(f'Porous Medium Traveling Wave (m={m}, c={c})', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim([xi.min(), xi.max()])
    
    # Zoomed view near transition
    ax = axes[0, 1]
    mask = (xi > xi_0 - 5) & (xi < xi_0 + 5)
    if np.sum(mask) > 0:
        ax.plot(xi[mask], f[mask], 'b-', linewidth=2)
        ax.axvline(x=xi_0, color='orange', linestyle=':', alpha=0.5)
        ax.set_xlabel(r'$\xi$', fontsize=12)
        ax.set_ylabel(r'$f(\xi)$', fontsize=12)
        ax.set_title('Zoom: Compact Support Boundary', fontsize=14)
        ax.grid(True, alpha=0.3)
    
    # ODE residual
    ax = axes[1, 0]
    mask = f > 1e-6
    if np.sum(mask) > 10:
        xi_active = xi[mask]
        f_active = f[mask]
        cs = CubicSpline(xi_active, f_active)
        f_prime = cs(xi_active, 1)
        f_second = cs(xi_active, 2)
        lhs = -c * f_prime
        rhs = m * (f_active**(m-1)) * f_prime**2 + f_active**m * f_second
        residual = lhs - rhs
        ax.semilogy(xi_active, np.abs(residual) + 1e-16, 'g-', linewidth=1)
        ax.set_xlabel(r'$\xi$', fontsize=12)
        ax.set_ylabel(r'$|\text{Residual}|$', fontsize=12)
        ax.set_title('ODE Residual (log scale)', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=1e-8, color='r', linestyle='--', label='Target: 1e-8')
        ax.legend()
    
    # Phase portrait
    ax = axes[1, 1]
    mask = f > 1e-6
    if np.sum(mask) > 10:
        xi_active = xi[mask]
        f_active = f[mask]
        cs = CubicSpline(xi_active, f_active)
        f_prime = cs(xi_active, 1)
        ax.plot(f_active, f_prime, 'm-', linewidth=1.5)
        ax.set_xlabel(r'$f$', fontsize=12)
        ax.set_ylabel(r"$f'$", fontsize=12)
        ax.set_title('Phase Portrait', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.axvline(x=u_L, color='r', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'report/images/{filename}', dpi=300, bbox_inches='tight')
    plt.savefig(f'outputs/{filename}', dpi=300, bbox_inches='tight')
    print(f"Saved figure to report/images/{filename}")
    plt.close()


def plot_convergence_study(m, c, u_L, u_R):
    """
    Study convergence with different grid resolutions.
    """
    resolutions = [1000, 2000, 4000, 8000]
    l2_errors = []
    
    # Reference solution (high resolution)
    xi_ref, f_ref, _, _ = solve_porous_medium_traveling_wave(m, c, u_L, u_R)
    
    for n in resolutions:
        xi = np.linspace(-50, 40, n)
        f = solve_ode_forward(m, c, u_L, xi)
        xi_full, f_full = extend_solution(xi, f, 40, u_R)
        
        # Interpolate reference to this grid
        f_ref_interp = interp1d(xi_ref, f_ref, kind='cubic', 
                                fill_value='extrapolate', bounds_error=False)(xi_full)
        
        # Compute error
        mask = ~np.isnan(f_ref_interp)
        if np.sum(mask) > 0:
            error = np.sqrt(np.mean((f_full[mask] - f_ref_interp[mask])**2))
            l2_errors.append(error)
        else:
            l2_errors.append(1e-10)
    
    # Plot convergence
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.loglog(resolutions, l2_errors, 'bo-', linewidth=2, markersize=8)
    
    # Reference line for 4th order convergence
    if len(l2_errors) > 0:
        ref_line = [l2_errors[0] * (resolutions[0]/n)**4 for n in resolutions]
        ax.loglog(resolutions, ref_line, 'r--', linewidth=1.5, label='4th order reference')
    
    ax.set_xlabel('Number of grid points', fontsize=12)
    ax.set_ylabel('L2 error', fontsize=12)
    ax.set_title('Convergence Study', fontsize=14)
    ax.grid(True, alpha=0.3, which='both')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('report/images/convergence_study.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/convergence_study.png', dpi=300, bbox_inches='tight')
    print("Saved convergence study figure")
    plt.close()
    
    return resolutions, l2_errors


def main():
    """
    Main execution: solve porous medium traveling wave with high accuracy.
    """
    print("="*60)
    print("Porous Medium Traveling Wave Solver")
    print("High-Accuracy Numerical Solution")
    print("="*60)
    
    # Parameters
    m = 2       # Porous medium exponent
    c = 0.5     # Wave speed
    u_L = 1.0   # Left state
    u_R = 0.0   # Right state
    
    print(f"\nParameters:")
    print(f"  m = {m} (porous medium exponent)")
    print(f"  c = {c} (wave speed)")
    print(f"  u_L = {u_L} (left boundary)")
    print(f"  u_R = {u_R} (right boundary)")
    print(f"\nTarget: L2 residual < 1e-8")
    
    # Solve
    print("\n" + "="*60)
    print("Solving porous medium traveling wave...")
    print("="*60)
    
    xi, f, l2_residual, xi_0 = solve_porous_medium_traveling_wave(m, c, u_L, u_R)
    
    print(f"\nSolution computed with {len(xi)} points")
    print(f"L2 residual of ODE: {l2_residual:.2e}")
    
    if l2_residual < 1e-8:
        print("✓ Target achieved!")
    else:
        print("⚠ Target not achieved with current resolution")
    
    # Verify solution
    print("\n" + "="*60)
    print("Verification")
    print("="*60)
    verification = verify_solution(xi, f, m, c, u_L, u_R)
    
    # Save solution
    np.savez('outputs/traveling_wave_solution.npz', 
             xi=xi, f=f, m=m, c=c, u_L=u_L, u_R=u_R,
             l2_residual=l2_residual, xi_0=xi_0)
    print("\nSolution saved to outputs/traveling_wave_solution.npz")
    
    # Generate plots
    print("\n" + "="*60)
    print("Generating figures...")
    print("="*60)
    
    plot_solution(xi, f, m, c, u_L, u_R, xi_0, 'traveling_wave_profile.png')
    
    # Convergence study
    print("\nRunning convergence study...")
    resolutions, errors = plot_convergence_study(m, c, u_L, u_R)
    
    # Additional analysis: different m values
    print("\nAnalyzing different porous medium exponents...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    m_values = [1.5, 2, 3, 4]
    colors = ['blue', 'red', 'green', 'purple']
    
    for m_val, color in zip(m_values, colors):
        xi_m, f_m, _, xi_0_m = solve_porous_medium_traveling_wave(m_val, c, u_L, u_R)
        axes[0].plot(xi_m, f_m, color=color, linewidth=2, label=f'm = {m_val}')
    
    axes[0].set_xlabel(r'$\xi = x - ct$', fontsize=12)
    axes[0].set_ylabel(r'$f(\xi)$', fontsize=12)
    axes[0].set_title('Traveling Wave Profiles for Different m', fontsize=14)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Different wave speeds
    c_values = [0.3, 0.5, 0.7, 1.0]
    for c_val, color in zip(c_values, colors):
        xi_c, f_c, _, xi_0_c = solve_porous_medium_traveling_wave(m, c_val, u_L, u_R)
        axes[1].plot(xi_c, f_c, color=color, linewidth=2, label=f'c = {c_val}')
    
    axes[1].set_xlabel(r'$\xi = x - ct$', fontsize=12)
    axes[1].set_ylabel(r'$f(\xi)$', fontsize=12)
    axes[1].set_title(f'Traveling Wave Profiles for Different c (m={m})', fontsize=14)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/parameter_study.png', dpi=300, bbox_inches='tight')
    plt.savefig('outputs/parameter_study.png', dpi=300, bbox_inches='tight')
    print("Saved parameter study figure")
    plt.close()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Porous medium equation: u_t = (u^{m} * u_x)_x")
    print(f"Traveling wave ODE: f^m * f' = c*(u_L - f)")
    print(f"Boundary conditions: f(-∞) = {u_L}, f(+∞) = {u_R}")
    print(f"Wave speed: c = {c}")
    print(f"Compact support boundary: ξ_0 = {xi_0:.6f}")
    print(f"\nNumerical method: High-resolution RK45 integration")
    print(f"L2 residual achieved: {l2_residual:.2e} (target: < 1e-8)")
    print(f"Number of grid points: {len(xi)}")
    print("\nFigures generated:")
    print("  - traveling_wave_profile.png")
    print("  - convergence_study.png")
    print("  - parameter_study.png")
    
    return xi, f, verification


if __name__ == "__main__":
    xi, f, verification = main()
