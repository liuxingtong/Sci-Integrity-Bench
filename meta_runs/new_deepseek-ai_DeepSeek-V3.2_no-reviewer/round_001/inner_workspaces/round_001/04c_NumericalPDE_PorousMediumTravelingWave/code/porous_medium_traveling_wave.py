#!/usr/bin/env python3
"""
Numerical integration of porous medium traveling wave ODE.

The porous medium equation: ∂u/∂t = Δ(u^m) where m > 1.
Traveling wave ansatz: u(x,t) = f(ξ), ξ = x - ct.
This reduces to an ODE for f(ξ).

For 1D case: ∂u/∂t = ∂²(u^m)/∂x²
Substituting u(x,t) = f(ξ), ξ = x - ct:
-c f' = (f^m)''
Let g = f^m, then g'' + c f' = 0
But f = g^(1/m), so f' = (1/m) g^(1/m - 1) g'

Alternatively, we can write directly:
-c f' = m(m-1) f^{m-2} (f')^2 + m f^{m-1} f''

This is a second-order ODE. We can convert to a system of first-order ODEs:
Let y1 = f, y2 = f'
Then:
y1' = y2
y2' = [-c y2 - m(m-1) y1^{m-2} y2^2] / (m y1^{m-1})

Boundary conditions: typically f → 0 as ξ → ∞ and f → 1 as ξ → -∞
(or vice versa depending on wave direction).
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os


def porous_medium_ode(t, y, m, c):
    """
    ODE system for porous medium traveling wave.
    y = [f, f']
    t = ξ (traveling wave coordinate)
    """
    f, fp = y
    
    # Avoid division by zero for small f
    if f < 1e-12:
        f = 1e-12
    
    # Equations:
    # f' = fp
    # f'' = [-c fp - m(m-1) f^{m-2} fp^2] / (m f^{m-1})
    
    fpp_numerator = -c * fp - m * (m-1) * (f ** (m-2)) * (fp ** 2)
    fpp_denominator = m * (f ** (m-1))
    fpp = fpp_numerator / fpp_denominator
    
    return [fp, fpp]


def integrate_traveling_wave(m=2.0, c=1.0, f0=0.999, fp0=-0.1, xi_span=(-10, 10), 
                            rtol=1e-8, atol=1e-10, method='RK45'):
    """
    Integrate the traveling wave ODE.
    
    Parameters:
    -----------
    m : exponent in porous medium equation (m > 1)
    c : wave speed
    f0 : initial value of f at ξ = ξ_start
    fp0 : initial value of f' at ξ = ξ_start
    xi_span : tuple (ξ_start, ξ_end) for integration
    rtol, atol : tolerance parameters for solve_ivp
    method : integration method ('RK45', 'DOP853', etc.)
    
    Returns:
    --------
    sol : solution object from solve_ivp
    """
    
    # Initial conditions
    y0 = [f0, fp0]
    
    # Integrate
    sol = solve_ivp(
        lambda t, y: porous_medium_ode(t, y, m, c),
        xi_span,
        y0,
        method=method,
        rtol=rtol,
        atol=atol,
        dense_output=True
    )
    
    return sol


def analyze_solution(sol, m, c):
    """Analyze and plot the solution."""
    xi = sol.t
    f = sol.y[0]
    fp = sol.y[1]
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot f(ξ)
    ax = axes[0, 0]
    ax.plot(xi, f, 'b-', linewidth=2)
    ax.set_xlabel(r'$\xi = x - ct$', fontsize=12)
    ax.set_ylabel(r'$f(\xi)$', fontsize=12)
    ax.set_title(f'Traveling wave profile (m={m}, c={c})')
    ax.grid(True, alpha=0.3)
    
    # Plot phase portrait
    ax = axes[0, 1]
    ax.plot(f, fp, 'r-', linewidth=2)
    ax.set_xlabel(r'$f$', fontsize=12)
    ax.set_ylabel(r"$f'$", fontsize=12)
    ax.set_title('Phase portrait')
    ax.grid(True, alpha=0.3)
    
    # Plot derivative f'(ξ)
    ax = axes[1, 0]
    ax.plot(xi, fp, 'g-', linewidth=2)
    ax.set_xlabel(r'$\xi = x - ct$', fontsize=12)
    ax.set_ylabel(r"$f'(\xi)$", fontsize=12)
    ax.set_title("Derivative of profile")
    ax.grid(True, alpha=0.3)
    
    # Plot log-log of 1-f vs ξ to check asymptotic behavior
    ax = axes[1, 1]
    # Find where f < 1
    mask = f < 0.999
    if np.any(mask):
        ax.plot(xi[mask], 1 - f[mask], 'm-', linewidth=2)
        ax.set_xlabel(r'$\xi$', fontsize=12)
        ax.set_ylabel(r'$1 - f(\xi)$', fontsize=12)
        ax.set_title('Asymptotic approach to 1 (log scale)')
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def main():
    """Main function to run analysis."""
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('report/images', exist_ok=True)
    
    # Test parameters
    m_values = [2.0, 3.0, 1.5]
    c_values = [1.0, 2.0, 0.5]
    
    results = []
    
    for m in m_values:
        for c in c_values:
            print(f"\n=== Testing m={m}, c={c} ===")
            
            # Initial conditions: start near 1 with negative derivative
            # (wave propagating to the right)
            f0 = 0.999
            fp0 = -0.1
            
            # Adjust integration range based on wave speed
            xi_end = 20.0 / c if c > 0 else 20.0
            xi_span = (-5, xi_end)
            
            try:
                sol = integrate_traveling_wave(m=m, c=c, f0=f0, fp0=fp0, 
                                              xi_span=xi_span)
                
                print(f"  Integration successful: {sol.t.size} points")
                print(f"  f range: [{sol.y[0].min():.4f}, {sol.y[0].max():.4f}]")
                print(f"  f' range: [{sol.y[1].min():.4f}, {sol.y[1].max():.4f}]")
                
                # Analyze and plot
                fig = analyze_solution(sol, m, c)
                
                # Save figure
                fig_path = f'report/images/porous_wave_m{m}_c{c}.png'
                fig.savefig(fig_path, dpi=150, bbox_inches='tight')
                plt.close(fig)
                
                # Save data
                data_path = f'outputs/solution_m{m}_c{c}.npz'
                np.savez(data_path, xi=sol.t, f=sol.y[0], fp=sol.y[1], 
                        m=m, c=c, f0=f0, fp0=fp0)
                
                results.append({
                    'm': m,
                    'c': c,
                    'sol': sol,
                    'fig_path': fig_path,
                    'data_path': data_path
                })
                
            except Exception as e:
                print(f"  Integration failed: {e}")
    
    # Also test with DOP853 method for comparison
    print("\n=== Testing with DOP853 method ===")
    m_test, c_test = 2.0, 1.0
    sol_rk45 = integrate_traveling_wave(m=m_test, c=c_test, method='RK45')
    sol_dop853 = integrate_traveling_wave(m=m_test, c=c_test, method='DOP853')
    
    # Compare solutions
    fig_compare, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    ax1.plot(sol_rk45.t, sol_rk45.y[0], 'b-', label='RK45', alpha=0.7)
    ax1.plot(sol_dop853.t, sol_dop853.y[0], 'r--', label='DOP853', alpha=0.7)
    ax1.set_xlabel(r'$\xi$')
    ax1.set_ylabel(r'$f(\xi)$')
    ax1.set_title('Comparison of integration methods')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot difference
    # Interpolate to common grid for comparison
    xi_common = np.linspace(min(sol_rk45.t.min(), sol_dop853.t.min()),
                           max(sol_rk45.t.max(), sol_dop853.t.max()), 1000)
    f_rk45 = sol_rk45.sol(xi_common)[0]
    f_dop853 = sol_dop853.sol(xi_common)[0]
    
    ax2.plot(xi_common, np.abs(f_rk45 - f_dop853), 'k-')
    ax2.set_xlabel(r'$\xi$')
    ax2.set_ylabel('Absolute difference')
    ax2.set_title('Difference between RK45 and DOP853')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    fig_compare.savefig('report/images/method_comparison.png', dpi=150, bbox_inches='tight')
    plt.close(fig_compare)
    
    print("\n=== Analysis complete ===")
    print(f"Generated {len(results)} solution sets")
    print(f"Figures saved to report/images/")
    print(f"Data saved to outputs/")
    
    return results


if __name__ == "__main__":
    main()
