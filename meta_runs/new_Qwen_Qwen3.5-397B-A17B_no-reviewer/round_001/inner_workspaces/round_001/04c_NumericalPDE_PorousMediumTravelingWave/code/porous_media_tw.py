"""
Numerical solution of the porous media equation traveling wave ODE.

The porous media equation is:
    ∂u/∂t = ∂/∂x (u^m ∂u/∂x)

Using traveling wave coordinates ξ = x - ct, with u(x,t) = f(ξ), we get:
    -c f' = (f^m f')'

Integrating once (assuming f → 0 as ξ → ∞):
    -c f = f^m f'
    
This gives the first-order ODE:
    f' = -c f^(1-m)

For m > 1, this has compact support solutions (Barenblatt-type).

We solve this ODE numerically and verify the solution.
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# Parameters
m = 2.0  # Porous media exponent (m > 1 for finite speed propagation)
c = 1.0  # Wave speed
f0 = 1.0  # Initial saturation at ξ=0

# Front position from analytical solution
xi_front = f0**m / (m * c)  # = 0.5 for m=2, c=1, f0=1

def porous_media_ode(xi, f, m=m, c=c):
    """
    ODE for traveling wave profile of porous media equation.
    f' = -c * f^(1-m)
    
    We add small epsilon to avoid singularity at f=0
    """
    eps = 1e-12
    f_safe = np.maximum(np.abs(f), eps)
    return -c * f_safe**(1-m)

def solve_traveling_wave(f0=f0, xi_end=0.49, n_points=1000):
    """
    Solve the traveling wave ODE from ξ=0 to ξ=xi_end (before the front).
    
    We stop before ξ_front to avoid the singularity at f=0.
    
    Parameters:
    -----------
    f0 : float
        Initial saturation at ξ=0
    xi_end : float
        Maximum ξ value (should be < xi_front)
    n_points : int
        Number of points
    
    Returns:
    --------
    xi : array
        Spatial coordinate
    f : array
        Saturation profile
    """
    xi = np.linspace(0, xi_end, n_points)
    
    # Solve ODE
    sol = solve_ivp(
        lambda xi, f: porous_media_ode(xi, f, m, c),
        [0, xi_end],
        [f0],
        method='RK45',
        t_eval=xi,
        rtol=1e-10,
        atol=1e-12
    )
    
    return xi, sol.y[0]

def verify_solution(xi, f, m=m, c=c):
    """
    Verify that the numerical solution satisfies the ODE.
    
    Compute the residual: R = f' + c * f^(1-m)
    
    Returns:
    --------
    residual : array
        Pointwise residual
    residual_norm : float
        L2 norm of residual
    max_residual : float
        Maximum absolute residual
    """
    # Compute numerical derivative using uniform spacing
    dx = xi[1] - xi[0]  # Uniform grid spacing
    df_dxi = np.gradient(f, dx)
    
    # Compute ODE residual: f' + c * f^(1-m) = 0
    eps = 1e-12
    f_safe = np.maximum(np.abs(f), eps)
    rhs = -c * f_safe**(1-m)
    
    residual = df_dxi - rhs
    
    residual_norm = np.sqrt(np.mean(residual**2))
    max_residual = np.max(np.abs(residual))
    
    return residual, residual_norm, max_residual

def analytical_solution(xi, m=m, c=c, f0=f0):
    """
    Analytical solution for the porous media traveling wave.
    
    From f' = -c * f^(1-m), we get:
    f^m / m = -c * ξ + const
    
    With f(0) = f0:
    f(ξ) = [f0^m - m*c*ξ]^(1/m) for ξ < f0^m/(m*c)
    f(ξ) = 0 for ξ >= f0^m/(m*c)
    """
    xi_front = f0**m / (m * c)  # Front position where f=0
    
    f = np.zeros_like(xi)
    mask = xi < xi_front
    f[mask] = (f0**m - m * c * xi[mask])**(1/m)
    
    return f, xi_front

def main():
    xi_max_plot = 1.0  # For plotting
    
    print("="*60)
    print("Porous Media Equation - Traveling Wave Solution")
    print("="*60)
    print(f"Parameters: m = {m}, c = {c}, f0 = {f0}")
    print(f"Analytical front position: ξ_front = {xi_front:.6f}")
    print()
    
    # Solve numerically (stop before the singularity)
    xi_end = 0.49  # Just before ξ_front = 0.5
    xi, f_num = solve_traveling_wave(f0=f0, xi_end=xi_end, n_points=1000)
    
    # Get analytical solution on the same grid
    f_ana, xi_front_ana = analytical_solution(xi, m, c, f0)
    
    # Verify numerical solution
    residual, residual_norm, max_residual = verify_solution(xi, f_num, m, c)
    
    print("Verification Results:")
    print(f"  L2 norm of residual: {residual_norm:.6e}")
    print(f"  Max absolute residual: {max_residual:.6e}")
    print(f"  Front position (analytical): ξ_front = {xi_front_ana:.6f}")
    print()
    
    # Extend arrays for plotting (add the front and beyond)
    xi_full = np.linspace(0, xi_max_plot, 500)
    f_ana_full, _ = analytical_solution(xi_full, m, c, f0)
    
    # For numerical, append zeros after xi_end
    f_num_full = np.zeros_like(xi_full)
    for i, x in enumerate(xi_full):
        if x <= xi_end:
            # Interpolate
            f_num_full[i] = np.interp(x, xi, f_num)
        else:
            f_num_full[i] = 0
    
    # Plot results
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Numerical vs Analytical solution
    ax = axes[0, 0]
    ax.plot(xi_full, f_num_full, 'b-', linewidth=2, label='Numerical')
    ax.plot(xi_full, f_ana_full, 'r--', linewidth=2, label='Analytical')
    ax.axvline(xi_front_ana, color='k', linestyle=':', label=f'Front (ξ={xi_front_ana:.3f})')
    ax.set_xlabel('ξ (traveling wave coordinate)', fontsize=12)
    ax.set_ylabel('f(ξ) (saturation)', fontsize=12)
    ax.set_title('Traveling Wave Profile: Numerical vs Analytical', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, xi_max_plot])
    ax.set_ylim([0, 1.1])
    
    # Plot 2: Residual
    ax = axes[0, 1]
    ax.plot(xi, residual, 'g-', linewidth=1.5)
    ax.axhline(0, color='k', linestyle='-', linewidth=0.5)
    ax.set_xlabel('ξ (traveling wave coordinate)', fontsize=12)
    ax.set_ylabel('Residual: f\' + c·f^(1-m)', fontsize=12)
    ax.set_title(f'ODE Residual (L2={residual_norm:.2e})', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, xi_end])
    
    # Plot 3: Absolute error vs analytical
    ax = axes[1, 0]
    error = np.abs(f_num - f_ana)
    # Avoid log(0)
    error = np.maximum(error, 1e-16)
    ax.plot(xi, error, 'm-', linewidth=1.5)
    ax.set_xlabel('ξ (traveling wave coordinate)', fontsize=12)
    ax.set_ylabel('|f_num - f_ana|', fontsize=12)
    ax.set_title('Absolute Error vs Analytical Solution', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, xi_end])
    ax.set_yscale('log')
    
    # Plot 4: Phase portrait (f vs f')
    ax = axes[1, 1]
    dx = xi[1] - xi[0]
    df_dxi = np.gradient(f_num, dx)
    ax.plot(f_num, -df_dxi, 'b-', linewidth=1.5, label='Numerical f\'')
    
    # Theoretical: f' = -c * f^(1-m)
    f_theory = np.linspace(0.01, 1, 100)
    fp_theory = -c * f_theory**(1-m)
    ax.plot(f_theory, fp_theory, 'r--', linewidth=2, label='Theoretical: -c·f^(1-m)')
    
    ax.set_xlabel('f(ξ)', fontsize=12)
    ax.set_ylabel('-df/dξ', fontsize=12)
    ax.set_title('Phase Portrait', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('report/images/traveling_wave_solution.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("Figure saved to: report/images/traveling_wave_solution.png")
    
    # Additional test: convergence study
    print("\n" + "="*60)
    print("Convergence Study")
    print("="*60)
    
    n_points_list = [100, 200, 500, 1000, 2000]
    residuals_list = []
    
    for n in n_points_list:
        xi_test, f_test = solve_traveling_wave(f0=f0, xi_end=xi_end, n_points=n)
        _, res_norm, _ = verify_solution(xi_test, f_test, m, c)
        residuals_list.append(res_norm)
        print(f"  n={n:4d}: L2 residual = {res_norm:.6e}")
    
    # Plot convergence
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.loglog(n_points_list, residuals_list, 'bo-', linewidth=2, markersize=8)
    ax.set_xlabel('Number of points', fontsize=12)
    ax.set_ylabel('L2 Residual Norm', fontsize=12)
    ax.set_title('Convergence Study: Residual vs Grid Resolution', fontsize=14)
    ax.grid(True, alpha=0.3, which='both')
    
    # Add reference slope
    n_ref = np.array([100, 2000])
    slope = -1  # First-order convergence due to singularity
    ref_line = residuals_list[0] * (n_ref / n_points_list[0])**slope
    ax.loglog(n_ref, ref_line, 'r--', linewidth=1.5, label=f'Slope {slope}')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('report/images/convergence_study.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("\nFigure saved to: report/images/convergence_study.png")
    
    # Save numerical results
    np.savez('outputs/numerical_results.npz', 
             xi=xi, f_num=f_num, f_ana=f_ana, 
             residual=residual, xi_front=xi_front_ana,
             residual_norm=residual_norm, max_residual=max_residual)
    
    print("\nResults saved to: outputs/numerical_results.npz")
    
    return {
        'xi': xi,
        'f_num': f_num,
        'f_ana': f_ana,
        'residual': residual,
        'residual_norm': residual_norm,
        'max_residual': max_residual,
        'xi_front': xi_front_ana
    }

if __name__ == '__main__':
    results = main()
