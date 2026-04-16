"""
Numerical integration of the porous media equation traveling wave ODE.

The porous media equation: ∂u/∂t = ∂/∂x (u^m ∂u/∂x)

Traveling wave reduction with ξ = x - ct, u(x,t) = f(ξ):
    -c f' = (f^m f')'

Integrating once with boundary conditions f(∞) = 0, f'(∞) = 0:
    -c f = f^m f'
    
Which gives the first-order ODE:
    f' = -c f^(1-m)

Analytical solution: f(ξ) = [max(0, 1 - c*m*ξ)]^(1/m)
The front is at ξ* = 1/(c*m) where f = 0.

For m > 1, the ODE is singular at f = 0. We integrate from f = 1 at ξ = 0
forward to the front, using a small cutoff f_min > 0.
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os

def porous_media_ode(xi, f, c, m):
    """
    ODE for porous media traveling wave: f' = -c * f^(1-m)
    
    Parameters:
    -----------
    xi : float
        Traveling wave coordinate
    f : array-like
        Saturation profile [f]
    c : float
        Wave speed
    m : float
        Porous media exponent
    
    Returns:
    --------
    dfdxi : array
        Derivative df/dξ
    """
    f_val = f[0]
    if f_val <= 0:
        return [0.0]
    dfdxi = -c * f_val**(1 - m)
    return [dfdxi]

def integrate_backward(c=1.0, m=1.5, f0=1.0, xi_end=1.0, 
                       rtol=1e-8, atol=1e-10, f_min=1e-10):
    """
    Integrate the traveling wave ODE backward from f=1 at xi=0.
    
    We integrate from xi=0 (where f=1) forward to xi_end, but stop
    when f drops below f_min to avoid singularity.
    
    Parameters:
    -----------
    c : float
        Wave speed
    m : float
        Porous media exponent
    f0 : float
        Initial saturation at xi=0 (should be 1.0)
    xi_end : float
        Final xi value (positive, beyond the front)
    rtol : float
        Relative tolerance
    atol : float
        Absolute tolerance
    f_min : float
        Minimum f value before stopping
    
    Returns:
    --------
    sol : OdeResult
        Solution object from solve_ivp
    """
    def ode_with_event(xi, f):
        return f[0] - f_min
    ode_with_event.terminal = True
    ode_with_event.direction = -1
    
    sol = solve_ivp(
        fun=lambda xi, f: porous_media_ode(xi, f, c, m),
        t_span=[0, xi_end],
        y0=[f0],
        method='DOP853',  # High-order embedded Runge-Kutta
        rtol=rtol,
        atol=atol,
        dense_output=True,
        max_step=0.05,
        events=ode_with_event
    )
    return sol

def analytical_solution(c=1.0, m=1.5, xi=None):
    """
    Analytical solution for the porous media traveling wave.
    
    f(ξ) = [max(0, 1 - c*m*ξ)]^(1/m)
    
    The front is at ξ* = 1/(c*m) where f = 0.
    """
    if xi is None:
        xi = np.linspace(-5, 2, 500)
    
    f_analytical = np.maximum(0, 1 - c * m * xi) ** (1/m)
    return xi, f_analytical

def main():
    """Main function to run the numerical integration and generate plots."""
    
    # Parameters
    c = 1.0  # Wave speed
    m_values = [0.5, 1.0, 1.5, 2.0, 3.0]  # Different porous media exponents
    rtol = 1e-8
    atol = 1e-10
    f_min = 1e-12
    
    # Create output directories
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    # Store results
    results = {}
    
    print("="*60)
    print("Porous Media Traveling Wave - Numerical Integration")
    print("="*60)
    print(f"Wave speed c = {c}")
    print(f"Tolerances: rtol={rtol}, atol={atol}")
    print(f"Method: DOP853 (embedded Runge-Kutta 8th order)")
    print(f"Minimum f: {f_min}")
    print("="*60)
    
    # Figure 1: Numerical solutions for different m values
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    
    for m in m_values:
        print(f"\nIntegrating for m = {m}...")
        
        # Calculate theoretical front position
        xi_front = 1.0 / (c * m)
        print(f"  Theoretical front position: ξ* = {xi_front:.4f}")
        
        # Numerical integration - integrate forward from xi=0
        xi_end = xi_front + 0.5  # Go slightly beyond the front
        sol = integrate_backward(c=c, m=m, f0=1.0, xi_end=xi_end,
                                  rtol=rtol, atol=atol, f_min=f_min)
        
        # Store results
        results[m] = {
            'xi': sol.t,
            'f': sol.y[0],
            'success': sol.success,
            'nfev': sol.nfev,
            'message': sol.message
        }
        
        # Find numerical front position
        if len(sol.t) > 0:
            xi_front_num = sol.t[-1]
            print(f"  Numerical front position: ξ* = {xi_front_num:.6f}")
            print(f"  Front error: {abs(xi_front_num - xi_front):.2e}")
            print(f"  Success: {sol.success}")
            print(f"  Function evaluations: {sol.nfev}")
            print(f"  f range: [{sol.y[0].min():.6e}, {sol.y[0].max():.6f}]")
        
        # Plot numerical solution
        ax1.plot(sol.t, sol.y[0], '-', label=f'm={m} (numerical)', linewidth=2)
    
    ax1.set_xlabel(r'Traveling wave coordinate $\xi = x - ct$', fontsize=12)
    ax1.set_ylabel(r'Saturation $f(\xi)$', fontsize=12)
    ax1.set_title('Porous Media Traveling Wave Profiles\n' + 
                  f'Wave speed c = {c}', fontsize=14)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(-0.05, 1.05)
    ax1.set_xlim(-0.5, 2.2)
    plt.tight_layout()
    plt.savefig('report/images/traveling_wave_profiles.png', dpi=150)
    plt.close()
    print("\nSaved: report/images/traveling_wave_profiles.png")
    
    # Figure 2: Comparison with analytical solution for m=1.5
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    
    m_test = 1.5
    xi_front_analytical = 1.0 / (c * m_test)
    xi_analytical = np.linspace(-0.5, xi_front_analytical + 0.2, 500)
    f_analytical = np.maximum(0, 1 - c * m_test * xi_analytical) ** (1/m_test)
    
    ax2.plot(xi_analytical, f_analytical, 'k--', linewidth=2, 
             label='Analytical solution')
    ax2.plot(results[m_test]['xi'], results[m_test]['f'], 'r-', 
             linewidth=2, label=f'Numerical (m={m_test})')
    
    # Compute error (only where f > f_min and away from front)
    from scipy.interpolate import interp1d
    mask = results[m_test]['f'] > 10*f_min
    if np.sum(mask) > 2:
        f_interp = interp1d(results[m_test]['xi'][mask], results[m_test]['f'][mask], 
                            kind='cubic', fill_value=np.nan, bounds_error=False)
        # Compare at numerical points
        f_num = results[m_test]['f'][mask]
        xi_num = results[m_test]['xi'][mask]
        f_ana_at_num = np.maximum(0, 1 - c * m_test * xi_num) ** (1/m_test)
        error = np.abs(f_num - f_ana_at_num)
        max_error = np.max(error)
        rmse = np.sqrt(np.mean(error**2))
    else:
        max_error = np.nan
        rmse = np.nan
    
    ax2.set_xlabel(r'Traveling wave coordinate $\xi = x - ct$', fontsize=12)
    ax2.set_ylabel(r'Saturation $f(\xi)$', fontsize=12)
    ax2.set_title(f'Numerical vs Analytical Solution (m={m_test})\n' +
                  f'Max Error: {max_error:.2e}, RMSE: {rmse:.2e}', fontsize=14)
    ax2.legend(loc='best', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(-0.05, 1.05)
    plt.tight_layout()
    plt.savefig('report/images/numerical_vs_analytical.png', dpi=150)
    plt.close()
    print(f"Saved: report/images/numerical_vs_analytical.png")
    print(f"Max error: {max_error:.2e}, RMSE: {rmse:.2e}")
    
    # Figure 3: Error convergence with tolerance - use front position error
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    
    tolerances = [1e-4, 1e-6, 1e-8, 1e-10, 1e-12]
    front_errors = []
    n_fevs_list = []
    
    m_conv = 2.0
    xi_front_exact = 1.0 / (c * m_conv)
    
    for tol in tolerances:
        sol = integrate_backward(c=c, m=m_conv, f0=1.0, 
                                  xi_end=xi_front_exact + 0.1,
                                  rtol=tol, atol=tol/10, f_min=1e-14)
        
        if len(sol.t) > 1:
            xi_front_num = sol.t[-1]
            front_err = abs(xi_front_num - xi_front_exact)
        else:
            front_err = np.nan
        
        front_errors.append(front_err)
        n_fevs_list.append(sol.nfev)
        
        print(f"Tol={tol:.0e}: front_error={front_err:.2e}, fevals={sol.nfev}")
    
    ax3.loglog(tolerances, front_errors, 'bo-', linewidth=2, markersize=8,
               label='Front position error')
    ax3.loglog(tolerances, tolerances, 'k--', linewidth=1, 
               label='O(tol) reference')
    ax3.set_xlabel('Tolerance', fontsize=12)
    ax3.set_ylabel('Front Position Error', fontsize=12)
    ax3.set_title(f'Front Position Error Convergence (m={m_conv})\n' +
                  f'Exact front: ξ* = {xi_front_exact:.4f}', fontsize=14)
    ax3.legend(loc='best', fontsize=11)
    ax3.grid(True, alpha=0.3, which='both')
    plt.tight_layout()
    plt.savefig('report/images/error_convergence.png', dpi=150)
    plt.close()
    print("Saved: report/images/error_convergence.png")
    
    # Figure 4: Step size adaptation
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    
    m_step = 2.0
    xi_front_step = 1.0 / (c * m_step)
    sol_step = integrate_backward(c=c, m=m_step, f0=1.0,
                                   xi_end=xi_front_step + 0.1,
                                   rtol=1e-8, atol=1e-10, f_min=1e-12)
    
    # Compute step sizes
    if len(sol_step.t) > 1:
        step_sizes = np.abs(np.diff(sol_step.t))
        xi_mid = (sol_step.t[:-1] + sol_step.t[1:]) / 2
        f_mid = (sol_step.y[0][:-1] + sol_step.y[0][1:]) / 2
        
        ax4.semilogy(xi_mid, step_sizes, 'b-', linewidth=1.5)
        ax4.set_xlabel(r'Traveling wave coordinate $\xi$', fontsize=12)
        ax4.set_ylabel('Adaptive step size', fontsize=12)
        ax4.set_title(f'Adaptive Step Size Evolution (m={m_step})\n' +
                      f'Total function evaluations: {sol_step.nfev}', fontsize=14)
        ax4.grid(True, alpha=0.3)
    else:
        ax4.text(0.5, 0.5, 'Insufficient data points', ha='center', va='center')
        ax4.set_title(f'Adaptive Step Size Evolution (m={m_step})', fontsize=14)
    
    plt.tight_layout()
    plt.savefig('report/images/adaptive_step_size.png', dpi=150)
    plt.close()
    print("Saved: report/images/adaptive_step_size.png")
    
    # Figure 5: Front position vs m
    fig5, ax5 = plt.subplots(figsize=(8, 6))
    
    m_range = np.linspace(0.3, 4.0, 100)
    xi_front_theory = 1.0 / (c * m_range)
    
    # Compute numerical front positions
    m_num = [0.5, 1.0, 1.5, 2.0, 3.0]
    xi_front_num = []
    for m in m_num:
        if m in results and len(results[m]['xi']) > 0:
            xi_front_num.append(results[m]['xi'][-1])
        else:
            xi_front_num.append(np.nan)
    
    ax5.plot(m_range, xi_front_theory, 'k-', linewidth=2, label='Analytical: $\\xi^* = 1/(cm)$')
    ax5.plot(m_num, xi_front_num, 'ro', markersize=10, label='Numerical')
    
    ax5.set_xlabel(r'Porous media exponent $m$', fontsize=12)
    ax5.set_ylabel(r'Front position $\xi^*$', fontsize=12)
    ax5.set_title('Front Position vs Porous Media Exponent', fontsize=14)
    ax5.legend(loc='best', fontsize=11)
    ax5.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('report/images/front_position_vs_m.png', dpi=150)
    plt.close()
    print("Saved: report/images/front_position_vs_m.png")
    
    # Figure 6: Profile shapes for different m (normalized)
    fig6, ax6 = plt.subplots(figsize=(10, 6))
    
    for m in m_values:
        if m in results and len(results[m]['xi']) > 0:
            xi = results[m]['xi']
            f = results[m]['f']
            # Normalize by front position
            xi_front_num = xi[-1]
            xi_norm = xi / xi_front_num
            ax6.plot(xi_norm, f, '-', label=f'm={m}', linewidth=2)
    
    ax6.set_xlabel(r'Normalized coordinate $\xi/\xi^*$', fontsize=12)
    ax6.set_ylabel(r'Saturation $f(\xi)$', fontsize=12)
    ax6.set_title('Normalized Traveling Wave Profiles', fontsize=14)
    ax6.legend(loc='best', fontsize=11)
    ax6.grid(True, alpha=0.3)
    ax6.set_xlim(-0.1, 1.1)
    ax6.set_ylim(-0.05, 1.05)
    plt.tight_layout()
    plt.savefig('report/images/normalized_profiles.png', dpi=150)
    plt.close()
    print("Saved: report/images/normalized_profiles.png")
    
    # Save numerical results to file
    np.savez('outputs/numerical_results.npz', 
             m_values=np.array(m_values),
             **{f'xi_{m}': results[m]['xi'] for m in m_values},
             **{f'f_{m}': results[m]['f'] for m in m_values})
    print("Saved: outputs/numerical_results.npz")
    
    print("\n" + "="*60)
    print("INTEGRATION COMPLETE")
    print("="*60)
    
    return results

if __name__ == '__main__':
    results = main()
